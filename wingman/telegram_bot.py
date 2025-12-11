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
import telebot
from telebot import types
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

def load_config():
    """Load bot configuration from file"""
    if not CONFIG_PATH.exists():
        logger.error(f"Config file not found at {CONFIG_PATH}")
        logger.info(f"Please copy {TEMPLATE_PATH} to {CONFIG_PATH} and add your bot token")
        sys.exit(1)

    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)

# Load configuration
config = load_config()
bot = telebot.TeleBot(config['bot_token'])

# Initialize API client
api_url = config.get('api_url', 'http://localhost:8001')
api_client = WingmanAPIClient(api_url=api_url)
logger.info(f"Bot connected to API at {api_url}")

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

    # Build message
    message = f"🔍 *Verifying:* {claim_text}\n\n"
    message += f"{emoji} *VERDICT: {verdict}*\n\n"

    # Add details if available
    if result.get('details'):
        message += f"📋 *Details:*\n{result['details']}\n"

    # Add error message if verification failed
    if not result.get('success', True) and result.get('error'):
        message += f"\n⚠️ *Error:* {result['error']}"

    # Add files checked if available
    if result.get('files_checked'):
        message += "\n📁 *Files Checked:*\n"
        for file_info in result['files_checked']:
            file_emoji = '✅' if file_info['exists'] else '❌'
            message += f"  {file_emoji} {file_info['path']}\n"

    # Add processes checked if available
    if result.get('processes_checked'):
        message += "\n⚙️ *Processes Checked:*\n"
        for proc_info in result['processes_checked']:
            proc_emoji = '✅' if proc_info['running'] else '❌'
            message += f"  {proc_emoji} {proc_info['name']}\n"

    # Add AI analysis if this was an enhanced verification
    if result.get('ai_analysis'):
        ai = result['ai_analysis']
        message += f"\n🤖 *AI Analysis:*\n"
        message += f"  Type: {ai.get('claim_type', 'Unknown')}\n"
        if ai.get('entities'):
            message += f"  Entities: {', '.join(ai['entities'])}\n"
        message += f"  Confidence: {ai.get('confidence', 'UNKNOWN')}\n"

    return message

def format_stats_result(stats):
    """Format API stats for Telegram"""
    if not stats.get('success', True):
        return f"⚠️ *Error getting stats:* {stats.get('error', 'Unknown error')}"

    # Extract stats data
    stats_data = stats.get('stats', {})

    message = "📊 *Verification Statistics*\n\n"

    # Last 24 hours stats
    if stats_data.get('last_24h'):
        h24 = stats_data['last_24h']
        message += "*Last 24 Hours:*\n"
        message += f"Total: {h24.get('total', 0)} verifications\n"
        message += f"✅ TRUE: {h24.get('true', 0)}\n"
        message += f"❌ FALSE: {h24.get('false', 0)}\n"
        message += f"❓ UNVERIFIABLE: {h24.get('unverifiable', 0)}\n\n"

    # All time stats
    if stats_data.get('all_time'):
        all_time = stats_data['all_time']
        message += "*All Time:*\n"
        message += f"Total: {all_time.get('total', 0)} verifications\n"
        message += f"✅ TRUE: {all_time.get('true', 0)}\n"
        message += f"❌ FALSE: {all_time.get('false', 0)}\n"
        message += f"❓ UNVERIFIABLE: {all_time.get('unverifiable', 0)}\n"

    # Add false claim rate if available
    if stats_data.get('false_rate') is not None:
        message += f"\n📈 *False Claim Rate:* {stats_data['false_rate']:.1f}%"

    return message

def format_history_result(history):
    """Format API history for Telegram"""
    if not history.get('success', True):
        return f"⚠️ *Error getting history:* {history.get('error', 'Unknown error')}"

    verifications = history.get('verifications', [])

    if not verifications:
        return "📜 *Recent Verifications:*\n\nNo recent verifications found."

    message = "📜 *Recent Verifications:*\n\n"

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
        return f"🔴 *API Status:* Offline\n⚠️ Error: {status.get('error', 'Cannot connect to API')}"

    # Determine status emoji
    api_status = status.get('api_status', 'unknown')
    if api_status == 'healthy':
        status_emoji = '🟢'
        status_text = 'Online'
    else:
        status_emoji = '🔴'
        status_text = 'Issues'

    message = f"{status_emoji} *API Status:* {status_text}\n"

    # Database status
    db_status = status.get('database', 'unknown')
    if db_status == 'connected':
        message += "📊 *Database:* Connected\n"
    else:
        message += "📊 *Database:* Disconnected\n"

    # Response time
    if status.get('response_time'):
        message += f"⚡ *Response Time:* {status['response_time']:.0f}ms\n"

    # Version if available
    if status.get('version'):
        message += f"📦 *Version:* {status['version']}"

    return message

@bot.message_handler(commands=['start', 'help'])
def send_help(message):
    """Handle /help and /start commands"""
    help_text = """
🤖 *Wingman Verification Bot*

I verify AI-generated claims by checking actual system state through the Wingman API.

*Commands:*
/verify `[claim]` - Simple verification
/verify\\_enhanced `[claim]` - With AI analysis
/stats - Recent verification stats
/history - Show recent verifications
/api\\_status - Check API health
/help - Show this message

*Examples:*
/verify I created /tmp/test.txt
/verify\\_enhanced Docker is running on port 8080

*How it works:*
• Simple: Checks files and processes directly
• Enhanced: Uses AI to understand claim first
• All verifications go through the Wingman API
"""
    bot.reply_to(message, help_text, parse_mode='Markdown')
    logger.info(f"Help sent to user {message.from_user.id}")

@bot.message_handler(commands=['verify'])
def verify_command(message):
    """Handle /verify command for simple verification via API"""
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
        bot.reply_to(message, response, parse_mode='Markdown')

        logger.info(f"Verification completed for user {message.from_user.id}: {result.get('verdict', 'UNKNOWN')}")

    except Exception as e:
        logger.error(f"Error in verification: {str(e)}")
        bot.reply_to(message, f"❌ Error during verification: {str(e)}")

@bot.message_handler(commands=['verify_enhanced'])
def verify_enhanced_command(message):
    """Handle /verify_enhanced command for AI-enhanced verification via API"""
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
        bot.reply_to(message, response, parse_mode='Markdown')

        logger.info(f"Enhanced verification completed for user {message.from_user.id}: {result.get('verdict', 'UNKNOWN')}")

    except Exception as e:
        logger.error(f"Error in enhanced verification: {str(e)}")
        bot.reply_to(message, f"❌ Error during enhanced verification: {str(e)}")

@bot.message_handler(commands=['stats'])
def stats_command(message):
    """Handle /stats command to show verification statistics from API"""
    # Send typing indicator
    bot.send_chat_action(message.chat.id, 'typing')

    try:
        # Get stats from API
        stats = api_client.get_stats('24h')

        # Format and send result
        response = format_stats_result(stats)
        bot.reply_to(message, response, parse_mode='Markdown')

        logger.info(f"Stats sent to user {message.from_user.id}")

    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        bot.reply_to(message, f"❌ Error getting statistics: {str(e)}")

@bot.message_handler(commands=['history'])
def history_command(message):
    """Handle /history command to show recent verifications from API"""
    # Send typing indicator
    bot.send_chat_action(message.chat.id, 'typing')

    try:
        # Get history from API
        history = api_client.get_history(limit=5)

        # Format and send result
        response = format_history_result(history)
        bot.reply_to(message, response, parse_mode='Markdown')

        logger.info(f"History sent to user {message.from_user.id}")

    except Exception as e:
        logger.error(f"Error getting history: {str(e)}")
        bot.reply_to(message, f"❌ Error getting history: {str(e)}")

@bot.message_handler(commands=['api_status'])
def api_status_command(message):
    """Handle /api_status command to check API health"""
    # Send typing indicator
    bot.send_chat_action(message.chat.id, 'typing')

    try:
        # Get API status
        status = api_client.get_api_status()

        # Format and send result
        response = format_api_status(status)
        bot.reply_to(message, response, parse_mode='Markdown')

        logger.info(f"API status sent to user {message.from_user.id}")

    except Exception as e:
        logger.error(f"Error checking API status: {str(e)}")
        bot.reply_to(message, f"❌ Error checking API status: {str(e)}")

@bot.message_handler(func=lambda message: True)
def handle_other_messages(message):
    """Handle non-command messages"""
    bot.reply_to(message,
                 "💡 *Tip:* Use /help to see available commands\n\n"
                 "To verify a claim, use:\n"
                 "/verify [your claim here]",
                 parse_mode='Markdown')

def main():
    """Main function to run the bot"""
    logger.info("Starting Wingman Telegram Bot (API Integration)...")
    logger.info(f"Bot configuration loaded from {CONFIG_PATH}")
    logger.info(f"Connected to API at {api_url}")

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