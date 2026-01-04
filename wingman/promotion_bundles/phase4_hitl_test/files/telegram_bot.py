#!/usr/bin/env python3
"""
Wingman Telegram Bot - API Integration Version
Provides verification services via Telegram commands using Wingman API
Worker 4B - Phase 4 Integration
"""
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import re
try:
    import telebot  # pyTelegramBotAPI
    from telebot import types
    from telebot.apihelper import ApiTelegramException
except ModuleNotFoundError as e:
    print("Error: Telegram dependency missing.")
    print("Install it in your current Python environment with:")
    print("  pip install pyTelegramBotAPI")
    raise
import logging

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

from bot_api_client import WingmanAPIClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load configuration
CONFIG_PATH = Path(__file__).parent / 'bot_config.json'
TEMPLATE_PATH = Path(__file__).parent / 'bot_config.json.template'

def _load_env_file(path: Path) -> bool:
    """
    Minimal .env loader (no dependencies).
    - Only sets vars that are not already set in the environment.
    - Ignores blank lines and comments.
    """
    try:
        if not path.exists() or not path.is_file():
            return False
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            if not k:
                continue
            if os.getenv(k) is None:
                os.environ[k] = v
        return True
    except Exception as e:
        logger.warning(f"Failed to load env file {path}: {e}")
        return False

def _bootstrap_env():
    """
    Load DEV/TEST/PRD-style env files automatically so operators don't have to export tokens repeatedly.
    Precedence (first found wins per var):
      - .env (common)
      - .env.dev (DEV)
      - .env.test (TEST)
      - .env.prd (PRD)
    """
    base = Path(__file__).parent
    loaded = []
    for name in [".env", ".env.dev", ".env.test", ".env.prd"]:
        p = base / name
        if _load_env_file(p):
            loaded.append(name)

    # Help operators: template file is not auto-loaded.
    if (base / "env.dev.example").exists() and not (base / ".env.dev").exists():
        logger.warning("Found env.dev.example but .env.dev is missing. Copy it: cp env.dev.example .env.dev")
    if (base / "env.test.example").exists() and not (base / ".env.test").exists():
        logger.warning("Found env.test.example but .env.test is missing. Copy it: cp env.test.example .env.test")

    if loaded:
        logger.info(f"Loaded environment variables from: {', '.join(loaded)}")

def _normalize_bot_token(raw: str) -> str:
    """
    Accept only a valid Telegram bot token form: "<digits>:<non-space-non-colon>".
    If raw contains extra text (e.g., pasted commands, URLs like .../bot<TOKEN>/sendMessage),
    extract the first matching token safely.
    """
    # Important: terminals often inject whitespace/newlines when pasting.
    # Telegram tokens must not contain whitespace, so strip ALL whitespace first.
    s = re.sub(r"\s+", "", (raw or ""))
    if not s:
        return ""
    # Fast path: already looks like "id:secret" with exactly one colon and no whitespace
    if s.count(":") == 1 and not any(c.isspace() for c in s):
        left, right = s.split(":", 1)
        if left.isdigit() and right and ":" not in right:
            return s
    # Extract the first plausible token substring
    m = re.search(r"(\d+:[^\s:]+)", s)
    if m:
        return m.group(1).strip()
    return s

def load_config():
    """
    Load bot configuration (env-first, file-fallback).

    Env vars (recommended for TEST/PRD):
      - BOT_TOKEN
      - API_URL (default: http://localhost:8001)
      - CHAT_ID (optional: restrict bot to a specific chat)
      - ALLOWED_USERS (optional: comma-separated Telegram user IDs)
    """
    cfg = {}
    token_source = "unknown"
    allow_file_config = (os.getenv("WINGMAN_ALLOW_FILE_CONFIG", "").strip() == "1")

    # Optional file fallback for DEV convenience
    if allow_file_config and CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, 'r') as f:
                cfg = json.load(f) or {}
        except Exception as e:
            logger.warning(f"Failed to read {CONFIG_PATH}: {e}")

    # Env overrides (env-first)
    env_token_raw = (os.getenv("BOT_TOKEN") or "").strip()
    if env_token_raw:
        token_source = "env"
        cfg["bot_token"] = _normalize_bot_token(env_token_raw)
    else:
        if allow_file_config:
            token_source = "file"
            cfg["bot_token"] = _normalize_bot_token(cfg.get("bot_token", ""))
        else:
            logger.error("BOT_TOKEN env var is required (file fallback disabled).")
            logger.error("Fix: set BOT_TOKEN in this shell before starting the bot.")
            logger.error("If you *must* use bot_config.json temporarily, set WINGMAN_ALLOW_FILE_CONFIG=1.")
            sys.exit(1)

    env_api_url = (os.getenv("API_URL") or "").strip()
    if env_api_url:
        cfg["api_url"] = env_api_url
    else:
        if allow_file_config and cfg.get("api_url"):
            cfg["api_url"] = str(cfg.get("api_url")).strip()
        else:
            # DEV-safe default to avoid repeating http://localhost:8001 mistakes
            cfg["api_url"] = "http://localhost:8002"
            logger.warning("API_URL not set; defaulting to http://localhost:8002 (DEV). Set API_URL to override.")

    cfg["chat_id"] = os.getenv("CHAT_ID", str(cfg.get("chat_id", ""))).strip()

    allowed_users_env = os.getenv("ALLOWED_USERS", "").strip()
    if allowed_users_env:
        cfg["allowed_users"] = [u.strip() for u in allowed_users_env.split(",") if u.strip()]

    if not cfg.get("bot_token"):
        logger.error("BOT_TOKEN is required (set env BOT_TOKEN or provide bot_config.json)")
        sys.exit(1)

    cfg["_token_source"] = token_source
    return cfg

# Auto-load env file(s) before reading config so BOT_TOKEN/API_URL/CHAT_ID are available.
_bootstrap_env()

# Load configuration
config = load_config()

# Safe diagnostics (no token leakage)
_tok = config.get("bot_token", "") or ""
_colon_count = _tok.count(":")
if _colon_count != 1:
    logger.error(f"BOT_TOKEN looks invalid (colon_count={_colon_count}, length={len(_tok)}).")
    logger.error("Fix: ensure wingman/.env.dev contains BOT_TOKEN=<digits>:<secret> (no quotes/brackets), then restart bot.")
    sys.exit(1)

bot = telebot.TeleBot(config['bot_token'])

# Initialize API client
api_url = config.get('api_url', 'http://localhost:8001')
api_client = WingmanAPIClient(api_url=api_url)
logger.info(f"Bot connected to API at {api_url}")


def _is_allowed(message) -> bool:
    """Optional security guardrails for bot usage."""
    # Restrict to a single chat if CHAT_ID provided
    chat_id = (config.get("chat_id") or "").strip()
    if chat_id:
        try:
            if str(message.chat.id) != str(chat_id):
                return False
        except Exception:
            return False

    # Restrict to allowed users if configured
    allowed = config.get("allowed_users") or []
    if allowed:
        try:
            return str(message.from_user.id) in {str(x) for x in allowed}
        except Exception:
            return False

    return True


def _deny(message, reason: str = "Not authorized"):
    chat_id = (config.get("chat_id") or "").strip()
    hint = ""
    if chat_id:
        hint = f"\n\nAllowed chat_id: {chat_id}\nThis chat_id: {message.chat.id}\nTip: if you're in a group, try /pending@robowing_bot or update CHAT_ID to the group chat id."
    # Plain text (no Markdown) to avoid Telegram entity parsing errors.
    bot.reply_to(message, f"⛔ {reason}{hint}")
    logger.warning(f"Denied bot command from user={getattr(message.from_user,'id',None)} chat={getattr(message.chat,'id',None)}: {reason}")

def format_verification_result(result, claim_text):
    """Format API verification result for Telegram"""
    # Determine verdict emoji and text
    verdict = result.get('verdict', 'ERROR')

    if verdict == 'TRUE':
        emoji = '✅'
    elif verdict == 'FALSE':
        emoji = '❌'
    elif verdict == 'UNVERIFIABLE':
        emoji = '❓'
    else:
        emoji = '⚠️'

    # Build message (plain text; avoid Markdown entity parsing issues)
    message = f"🔍 Verifying: {claim_text}\n\n"
    message += f"{emoji} VERDICT: {verdict}\n\n"

    # Add details if available
    if result.get('details'):
        message += f"📋 Details:\n{result['details']}\n"

    # Add error message if verification failed
    if not result.get('success', True) and result.get('error'):
        message += f"\n⚠️ Error: {result['error']}"

    # Add files checked if available
    if result.get('files_checked'):
        message += "\n📁 Files Checked:\n"
        for file_info in result['files_checked']:
            file_emoji = '✅' if file_info['exists'] else '❌'
            message += f"  {file_emoji} {file_info['path']}\n"

    # Add processes checked if available
    if result.get('processes_checked'):
        message += "\n⚙️ Processes Checked:\n"
        for proc_info in result['processes_checked']:
            proc_emoji = '✅' if proc_info['running'] else '❌'
            message += f"  {proc_emoji} {proc_info['name']}\n"

    # Add AI analysis if this was an enhanced verification
    if result.get('ai_analysis'):
        ai = result['ai_analysis']
        message += f"\n🤖 AI Analysis:\n"
        message += f"  Type: {ai.get('claim_type', 'Unknown')}\n"
        if ai.get('entities'):
            message += f"  Entities: {', '.join(ai['entities'])}\n"
        message += f"  Confidence: {ai.get('confidence', 'UNKNOWN')}\n"

    return message

def format_stats_result(stats):
    """Format API stats for Telegram"""
    if not stats.get('success', True):
        return f"⚠️ Error getting stats: {stats.get('error', 'Unknown error')}"

    # Extract stats data
    stats_data = stats.get('stats', {})

    message = "📊 Verification Statistics\n\n"

    # Last 24 hours stats
    if stats_data.get('last_24h'):
        h24 = stats_data['last_24h']
        message += "Last 24 Hours:\n"
        message += f"Total: {h24.get('total', 0)} verifications\n"
        message += f"✅ TRUE: {h24.get('true', 0)}\n"
        message += f"❌ FALSE: {h24.get('false', 0)}\n"
        message += f"❓ UNVERIFIABLE: {h24.get('unverifiable', 0)}\n\n"

    # All time stats
    if stats_data.get('all_time'):
        all_time = stats_data['all_time']
        message += "All Time:\n"
        message += f"Total: {all_time.get('total', 0)} verifications\n"
        message += f"✅ TRUE: {all_time.get('true', 0)}\n"
        message += f"❌ FALSE: {all_time.get('false', 0)}\n"
        message += f"❓ UNVERIFIABLE: {all_time.get('unverifiable', 0)}\n"

    # Add false claim rate if available
    if stats_data.get('false_rate') is not None:
        message += f"\n📈 False Claim Rate: {stats_data['false_rate']:.1f}%"

    return message

def format_history_result(history):
    """Format API history for Telegram"""
    if not history.get('success', True):
        return f"⚠️ Error getting history: {history.get('error', 'Unknown error')}"

    verifications = history.get('verifications', [])

    if not verifications:
        return "📜 Recent Verifications:\n\nNo recent verifications found."

    message = "📜 Recent Verifications:\n\n"

    for i, entry in enumerate(verifications[:5], 1):
        # Determine emoji based on verdict
        verdict = entry.get('verdict', 'UNKNOWN')
        if verdict == 'TRUE':
            emoji = '✅'
        elif verdict == 'FALSE':
            emoji = '❌'
        elif verdict == 'UNVERIFIABLE':
            emoji = '❓'
        else:
            emoji = '⚠️'

        # Format claim (truncate if too long)
        claim = entry.get('claim', 'Unknown claim')
        if len(claim) > 50:
            claim = claim[:47] + "..."

        # Format timestamp
        timestamp = entry.get('timestamp')
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp)
                time_ago = datetime.now() - dt
                if time_ago.total_seconds() < 60:
                    time_str = "just now"
                elif time_ago.total_seconds() < 3600:
                    minutes = int(time_ago.total_seconds() / 60)
                    time_str = f"{minutes} minute{'s' if minutes != 1 else ''} ago"
                elif time_ago.total_seconds() < 86400:
                    hours = int(time_ago.total_seconds() / 3600)
                    time_str = f"{hours} hour{'s' if hours != 1 else ''} ago"
                else:
                    days = int(time_ago.total_seconds() / 86400)
                    time_str = f"{days} day{'s' if days != 1 else ''} ago"
            except:
                time_str = "Unknown time"
        else:
            time_str = "Unknown time"

        message += f"{i}. {emoji} \"{claim}\"\n"
        message += f"   Time: {time_str}\n\n"

    return message

def format_api_status(status):
    """Format API status for Telegram"""
    if not status.get('success'):
        return f"🔴 API Status: Offline\n⚠️ Error: {status.get('error', 'Cannot connect to API')}"

    # Determine status emoji
    api_status = status.get('api_status', 'unknown')
    if api_status == 'healthy':
        status_emoji = '🟢'
        status_text = 'Online'
    else:
        status_emoji = '🔴'
        status_text = 'Issues'

    message = f"{status_emoji} API Status: {status_text}\n"

    # Database status
    db_status = status.get('database', 'unknown')
    if db_status == 'connected':
        message += "📊 Database: Connected\n"
    else:
        message += "📊 Database: Disconnected\n"

    # Response time
    if status.get('response_time'):
        message += f"⚡ Response Time: {status['response_time']:.0f}ms\n"

    # Version if available
    if status.get('version'):
        message += f"📦 Version: {status['version']}"

    return message

@bot.message_handler(commands=['start', 'help'])
def send_help(message):
    """Handle /help and /start commands"""
    if not _is_allowed(message):
        return _deny(message)
    help_text = """
🤖 *Wingman Verification Bot*

I verify AI-generated claims by checking actual system state through the Wingman API.

*Commands:*
/verify `[claim]` - Simple verification
/verify\\_enhanced `[claim]` - With AI analysis
/stats - Recent verification stats
/history - Show recent verifications
/api\\_status - Check API health
/pending - List pending approvals (Phase 4)
/approve `<id>` `[note]` - Approve a request (Phase 4)
/reject `<id>` `[note]` - Reject a request (Phase 4)
/help - Show this message

*Examples:*
/verify I created /tmp/test.txt
/verify\\_enhanced Docker is running on port 8080
/pending
/approve 6b0c... Looks good
/reject 6b0c... Too risky

*How it works:*
• Simple: Checks files and processes directly
• Enhanced: Uses AI to understand claim first
• All verifications go through the Wingman API
"""
    bot.reply_to(message, help_text)
    logger.info(f"Help sent to user {message.from_user.id}")


@bot.message_handler(commands=["chatid", "whoami"])
def chatid_command(message):
    """Debug / operator convenience: show current chat_id and user_id."""
    # Intentionally allowed even if chat restriction is enabled, so operator can discover IDs.
    user = getattr(message, "from_user", None)
    username = getattr(user, "username", "") if user else ""
    uid = getattr(user, "id", "") if user else ""
    cid = getattr(message.chat, "id", "")
    # Plain text to avoid Telegram Markdown entity parsing issues.
    text = (
        "Wingman Chat/Identity\n\n"
        f"- chat_id: {cid}\n"
        f"- user_id: {uid}\n"
        f"- username: {username}\n"
        "\nIf you want to lock the bot to this chat, set CHAT_ID to the chat_id above."
    )
    bot.reply_to(message, text)

@bot.message_handler(commands=['verify'])
def verify_command(message):
    """Handle /verify command for simple verification via API"""
    if not _is_allowed(message):
        return _deny(message)
    # Extract claim text
    claim_text = message.text[8:].strip()  # Remove '/verify ' prefix

    if not claim_text:
        bot.reply_to(message, "⚠️ Please provide a claim to verify\n\nExample: /verify I created backup.tar")
        return

    # Check claim length
    if len(claim_text) > config.get('max_claim_length', 500):
        bot.reply_to(message, "⚠️ Claim too long. Please keep it under 500 characters.")
        return

    # Send typing indicator
    bot.send_chat_action(message.chat.id, 'typing')

    try:
        # Call API for verification
        result = api_client.verify_claim(claim_text, use_enhanced=False)

        # Format and send result
        response = format_verification_result(result, claim_text)
        bot.reply_to(message, response)

        logger.info(f"Verification completed for user {message.from_user.id}: {result.get('verdict', 'UNKNOWN')}")

    except Exception as e:
        logger.error(f"Error in verification: {str(e)}")
        bot.reply_to(message, f"❌ Error during verification: {str(e)}")

@bot.message_handler(commands=['verify_enhanced'])
def verify_enhanced_command(message):
    """Handle /verify_enhanced command for AI-enhanced verification via API"""
    if not _is_allowed(message):
        return _deny(message)
    # Extract claim text
    claim_text = message.text[16:].strip()  # Remove '/verify_enhanced ' prefix

    if not claim_text:
        bot.reply_to(message, "⚠️ Please provide a claim to verify\n\nExample: /verify_enhanced Docker is running")
        return

    # Check if enhanced mode is enabled
    if not config.get('enable_enhanced', True):
        bot.reply_to(message, "⚠️ Enhanced verification is currently disabled")
        return

    # Check claim length
    if len(claim_text) > config.get('max_claim_length', 500):
        bot.reply_to(message, "⚠️ Claim too long. Please keep it under 500 characters.")
        return

    # Send typing indicator
    bot.send_chat_action(message.chat.id, 'typing')

    try:
        # Call API for enhanced verification
        result = api_client.verify_claim(claim_text, use_enhanced=True)

        # Format and send result
        response = format_verification_result(result, claim_text)
        bot.reply_to(message, response)

        logger.info(f"Enhanced verification completed for user {message.from_user.id}: {result.get('verdict', 'UNKNOWN')}")

    except Exception as e:
        logger.error(f"Error in enhanced verification: {str(e)}")
        bot.reply_to(message, f"❌ Error during enhanced verification: {str(e)}")

@bot.message_handler(commands=['stats'])
def stats_command(message):
    """Handle /stats command to show verification statistics from API"""
    if not _is_allowed(message):
        return _deny(message)
    # Send typing indicator
    bot.send_chat_action(message.chat.id, 'typing')

    try:
        # Get stats from API
        stats = api_client.get_stats('24h')

        # Format and send result
        response = format_stats_result(stats)
        bot.reply_to(message, response)

        logger.info(f"Stats sent to user {message.from_user.id}")

    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        bot.reply_to(message, f"❌ Error getting statistics: {str(e)}")

@bot.message_handler(commands=['history'])
def history_command(message):
    """Handle /history command to show recent verifications from API"""
    if not _is_allowed(message):
        return _deny(message)
    # Send typing indicator
    bot.send_chat_action(message.chat.id, 'typing')

    try:
        # Get history from API
        history = api_client.get_history(limit=5)

        # Format and send result
        response = format_history_result(history)
        bot.reply_to(message, response)

        logger.info(f"History sent to user {message.from_user.id}")

    except Exception as e:
        logger.error(f"Error getting history: {str(e)}")
        bot.reply_to(message, f"❌ Error getting history: {str(e)}")

@bot.message_handler(commands=['api_status'])
def api_status_command(message):
    """Handle /api_status command to check API health"""
    if not _is_allowed(message):
        return _deny(message)
    # Send typing indicator
    bot.send_chat_action(message.chat.id, 'typing')

    try:
        # Get API status
        status = api_client.get_api_status()

        # Format and send result
        response = format_api_status(status)
        bot.reply_to(message, response)

        logger.info(f"API status sent to user {message.from_user.id}")

    except Exception as e:
        logger.error(f"Error checking API status: {str(e)}")
        bot.reply_to(message, f"❌ Error checking API status: {str(e)}")

# Catch-all should NOT swallow commands like /pending.
@bot.message_handler(func=lambda message: not (getattr(message, "text", "") or "").startswith("/"))
def handle_other_messages(message):
    """Handle non-command messages"""
    if not _is_allowed(message):
        return _deny(message)
    bot.reply_to(message,
                 "💡 Tip: Use /help to see available commands\n\n"
                 "To verify a claim, use:\n"
                 "/verify [your claim here]")


def _format_pending_approvals(pending: list) -> str:
    if not pending:
        return "✅ No pending approvals."
    lines = ["🧾 Pending Approvals (oldest first)\n"]
    for item in pending[:10]:
        rid = item.get("request_id", "")
        risk = item.get("risk_level", "")
        worker_id = item.get("worker_id", "")
        task_name = item.get("task_name", "")
        created = item.get("created_at", "")
        short_id = rid.split("-")[0] if rid else ""
        lines.append(f"- {short_id} | {risk} | worker={worker_id} | {task_name} | {created}")
    lines.append("\nUse /approve <id> [note] or /reject <id> [note] (full UUID or short prefix).")
    return "\n".join(lines)


def _resolve_request_id(prefix: str) -> str:
    """
    Resolve a short request_id prefix to a full UUID deterministically.

    Safety rule: NEVER approve/reject the wrong request.
    - If prefix matches exactly one pending request -> return that full id.
    - If it matches zero -> return original (could be a full UUID).
    - If it matches more than one -> return empty string (caller must error).
    """
    pref = (prefix or "").strip().lower()
    if not pref:
        return ""

    pending = api_client.list_pending_approvals(limit=200)
    if not pending.get("success", True):
        return ""

    matches = []
    for item in pending.get("pending", []):
        rid_full = (item.get("request_id") or "")
        rid = rid_full.lower()
        if rid.startswith(pref):
            matches.append(rid_full)

    if len(matches) == 1:
        return matches[0]
    if len(matches) == 0:
        # Possibly a full UUID; let API handle it.
        return prefix.strip()
    # Ambiguous prefix
    return ""


@bot.message_handler(commands=["pending"])
def pending_command(message):
    """Phase 4: show pending approval queue."""
    if not _is_allowed(message):
        return _deny(message)
    bot.send_chat_action(message.chat.id, 'typing')
    res = api_client.list_pending_approvals(limit=20)
    if not res.get("success", True):
        return bot.reply_to(message, f"⚠️ Error: {res.get('error','Unknown error')}")
    text = _format_pending_approvals(res.get("pending", []))
    bot.reply_to(message, text)

@bot.message_handler(commands=["show"])
def show_command(message):
    """Phase 4: show details for a specific approval id/prefix."""
    if not _is_allowed(message):
        return _deny(message)
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return bot.reply_to(message, "Usage: /show <id-prefix-or-uuid>")
    rid = _resolve_request_id(parts[1].strip())
    if not rid:
        return bot.reply_to(message, "⚠️ Ambiguous or unavailable id. Use a longer prefix or full UUID.")
    bot.send_chat_action(message.chat.id, 'typing')
    res = api_client.get_approval(rid)
    if not res.get("success", True):
        return bot.reply_to(message, f"⚠️ Error: {res.get('error','Unknown error')}")
    a = res.get("approval", {}) or {}
    text = (
        "Approval Details\n\n"
        f"- request_id: {a.get('request_id','')}\n"
        f"- status: {a.get('status','')}\n"
        f"- risk: {a.get('risk_level','')} ({a.get('risk_reason','')})\n"
        f"- worker_id: {a.get('worker_id','')}\n"
        f"- task_name: {a.get('task_name','')}\n"
        f"- created_at: {a.get('created_at','')}\n"
        f"- decided_by: {a.get('decided_by','')}\n"
        f"- decided_at: {a.get('decided_at','')}\n"
        f"- note: {a.get('decision_note','')}\n"
    )
    bot.reply_to(message, text)


@bot.message_handler(commands=["clear_pending"])
def clear_pending_command(message):
    """Phase 4: bulk reject all pending approvals (requires CONFIRM)."""
    if not _is_allowed(message):
        return _deny(message)
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2 or parts[1].strip().upper() != "CONFIRM":
        return bot.reply_to(message, "⚠️ Usage: /clear_pending CONFIRM\nThis will reject ALL pending approvals.")
    bot.send_chat_action(message.chat.id, 'typing')
    pending = api_client.list_pending_approvals(limit=200)
    if not pending.get("success", True):
        return bot.reply_to(message, f"⚠️ Error: {pending.get('error','Unknown error')}")
    items = pending.get("pending", []) or []
    if not items:
        return bot.reply_to(message, "✅ No pending approvals to clear.")
    ok = 0
    for item in items:
        rid = item.get("request_id") or ""
        if not rid:
            continue
        r = api_client.reject(rid, decided_by=f"{getattr(message.from_user,'username','') or ''}({message.from_user.id})", note="bulk clear")
        if r.get("success", True):
            ok += 1
    bot.reply_to(message, f"🧹 Cleared pending approvals: {ok}/{len(items)} rejected.")


@bot.message_handler(commands=["approve"])
def approve_command(message):
    """Phase 4: approve a request id."""
    if not _is_allowed(message):
        return _deny(message)
    parts = message.text.split(maxsplit=2)
    if len(parts) < 2:
        return bot.reply_to(message, "Usage: /approve <id> [note]")
    requested = parts[1].strip()
    rid = _resolve_request_id(requested)
    if not rid:
        return bot.reply_to(
            message,
            "⚠️ Ambiguous or unavailable request id. Please paste the full UUID (or a longer unique prefix).\n"
            "Tip: run /pending and copy the full request_id if needed."
        )
    if rid.lower().startswith(requested.lower()) is False and "-" not in requested:
        return bot.reply_to(
            message,
            f"⚠️ Safety stop: resolved id doesn't match requested prefix.\nRequested: {requested}\nResolved: {rid}\n"
            "Please try again with a longer prefix/full UUID."
        )
    note = parts[2] if len(parts) >= 3 else ""
    decided_by = f"{getattr(message.from_user, 'username', '') or ''}({message.from_user.id})"
    bot.send_chat_action(message.chat.id, 'typing')
    res = api_client.approve(rid, decided_by=decided_by, note=note)
    if not res.get("success", True):
        return bot.reply_to(message, f"⚠️ Error: {res.get('error','Unknown error')}")
    approval = res.get("approval", {})
    bot.reply_to(message, f"✅ Approved {approval.get('request_id','')}")


@bot.message_handler(commands=["reject"])
def reject_command(message):
    """Phase 4: reject a request id."""
    if not _is_allowed(message):
        return _deny(message)
    parts = message.text.split(maxsplit=2)
    if len(parts) < 2:
        return bot.reply_to(message, "Usage: /reject <id> [note]")
    requested = parts[1].strip()
    rid = _resolve_request_id(requested)
    if not rid:
        return bot.reply_to(
            message,
            "⚠️ Ambiguous or unavailable request id. Please paste the full UUID (or a longer unique prefix).\n"
            "Tip: run /pending and copy the full request_id if needed."
        )
    if rid.lower().startswith(requested.lower()) is False and "-" not in requested:
        return bot.reply_to(
            message,
            f"⚠️ Safety stop: resolved id doesn't match requested prefix.\nRequested: {requested}\nResolved: {rid}\n"
            "Please try again with a longer prefix/full UUID."
        )
    note = parts[2] if len(parts) >= 3 else ""
    decided_by = f"{getattr(message.from_user, 'username', '') or ''}({message.from_user.id})"
    bot.send_chat_action(message.chat.id, 'typing')
    res = api_client.reject(rid, decided_by=decided_by, note=note)
    if not res.get("success", True):
        return bot.reply_to(message, f"⚠️ Error: {res.get('error','Unknown error')}")
    approval = res.get("approval", {})
    bot.reply_to(message, f"🛑 Rejected {approval.get('request_id','')}")

def main():
    """Main function to run the bot"""
    logger.info("Starting Wingman Telegram Bot (API Integration)...")
    logger.info(f"Bot configuration loaded from {CONFIG_PATH}")
    logger.info(f"Connected to API at {api_url}")
    logger.info(f"Telegram token source: {config.get('_token_source', 'unknown')}")
    if config.get("_token_source") == "file":
        logger.warning("BOT_TOKEN env var not set; using token from bot_config.json (may be stale).")

    # Fail-fast if Telegram token is unauthorized (avoid infinite noisy retries)
    try:
        _me = bot.get_me()
        logger.info(f"Telegram bot authorized as: @{getattr(_me, 'username', 'unknown')}")
    except ApiTelegramException as e:
        # 401 Unauthorized -> wrong/expired token
        if getattr(e, "error_code", None) == 401:
            logger.error("Telegram API returned 401 Unauthorized. BOT_TOKEN is invalid/expired or for the wrong bot.")
            logger.error("Fix: set BOT_TOKEN to the exact token from BotFather for the intended bot.")
            return
        logger.error(f"Telegram API error during getMe(): {e}")
        return
    except Exception as e:
        logger.error(f"Telegram auth preflight failed: {e}")
        return

    # Check API health on startup
    if api_client.health_check():
        logger.info("✅ API is healthy and responding")
    else:
        logger.warning("⚠️ API is not responding - bot will retry on each request")

    # Check for allowed users restriction
    if config.get('allowed_users'):
        logger.info(f"Bot restricted to users: {config['allowed_users']}")
    else:
        logger.info("Bot accepting messages from all users")

    # Check for chat restriction
    if config.get("chat_id"):
        logger.info(f"Bot restricted to chat_id: {config['chat_id']}")

    # Start polling
    try:
        logger.info("Bot is polling for messages...")
        bot.infinity_polling()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {str(e)}")
        raise

if __name__ == "__main__":
    main()