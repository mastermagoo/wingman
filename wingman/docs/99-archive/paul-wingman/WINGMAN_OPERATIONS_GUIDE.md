# 🚀 PAUL WINGMAN - COMPLETE OPERATIONS GUIDE

## What is Wingman?

Paul Wingman is your **AI Truth Guardian** - an independent verification system that monitors ALL activity on your system and alerts you to discrepancies, lies, or suspicious AI behavior.

---

## 🎯 CORE MISSION

**Wingman's Job:**
1. **Monitor Everything** - All AI claims, system changes, file operations
2. **Verify Reality** - Check if what AI says matches what actually happened
3. **Alert You Immediately** - Via Telegram when something's wrong
4. **Accept Your Commands** - Via Telegram messages or voice notes

---

## 📡 COMMUNICATION ARCHITECTURE

### How Wingman Talks to You:

```
System Activity → Wingman Monitors → Verification → Telegram Alert to You
                     ↑                                    ↓
                Intel System                    You Respond (Text/Voice)
                     ↑                                    ↓
                AI Assistant ← Wingman Enforces ← Your Commands
```

### Telegram Integration:
- **Bot Token**: *(set via `BOT_TOKEN`; never commit)*
- **Your Chat ID**: *(set via `CHAT_ID`; never commit)*
- **Parse Mode**: Markdown for formatted alerts

---

## 🔍 WHAT WINGMAN MONITORS

### 1. Intel System Monitoring
- **Database Changes** - New emails, calendar events, processed items
- **Container Health** - Docker services up/down
- **Processing Pipeline** - Extraction, analysis, intelligence generation
- **Error States** - Failed operations, crashes, timeouts

### 2. AI Assistant Monitoring
- **Every Claim** - "I created X", "I saved Y", "I ran Z"
- **File Operations** - What was actually created vs claimed
- **Command Execution** - What actually ran vs what AI said
- **Data Access** - What AI actually read vs claimed to read

### 3. System-Wide Monitoring
- **File System Changes** - New files, deletions, modifications
- **Network Activity** - Unusual connections, data transfers
- **Process Spawning** - New services, background tasks
- **Resource Usage** - CPU/Memory spikes, disk usage

---

## 💬 TELEGRAM ALERT TYPES

### 🔴 CRITICAL ALERTS
```
🚨 CRITICAL: AI DECEPTION DETECTED
Claim: "Created backup at /backup/data.tar"
Reality: No file exists
Confidence: 98%
Action Required: Investigate immediately
```

### 🟡 WARNING ALERTS
```
⚠️ WARNING: Unusual Activity
Intel System processing stopped for 10 minutes
Last successful sync: 12:45 PM
Possible Cause: Container crashed
```

### 🟢 STATUS UPDATES
```
✅ STATUS: Intel System Healthy
- Emails: 45 new processed
- Calendar: 3 events added
- Intelligence: 48 items analyzed
- Next sync: in 5 minutes
```

### 🔵 VERIFICATION REPORTS
```
🔍 VERIFICATION: Command Execution
AI Claimed: "Installed new package"
Verification: Package found in system
Verdict: TRUE (85% confidence)
```

---

## 🎤 YOUR COMMAND OPTIONS

### Via Telegram Text:
```
"Check intel system status"
"Verify last AI claim"
"Show me what files changed"
"Alert me if X happens"
"Stop monitoring for 1 hour"
```

### Via Voice Notes:
Wingman transcribes your Telegram voice messages and executes commands:
```
🎤 "Hey Wingman, did the AI really create that backup?"
🎤 "Check if Docker is actually running"
🎤 "Send me hourly intel system summaries"
```

### Direct Responses:
When Wingman alerts you, reply directly:
```
Wingman: "🚨 AI claims database backup completed"
You: "Verify the backup file exists and check its size"
Wingman: "✅ Verified: backup exists, 2.3GB, created 2 min ago"
```

---

## 🔧 MONITORING MODES

### 1. **ACTIVE MODE** (Default)
- Real-time monitoring of all systems
- Instant Telegram alerts for issues
- Continuous AI claim verification
- Full system scanning every 5 minutes

### 2. **PASSIVE MODE**
- Logs everything but only alerts on critical issues
- Daily summary reports via Telegram
- Good for when you're sleeping

### 3. **PARANOID MODE**
- Verify EVERYTHING the AI does
- Alert on any file change
- Track all network connections
- Maximum security, more alerts

### 4. **STEALTH MODE**
- Monitor silently without AI knowing
- Collect evidence of deception
- Weekly detailed reports
- For investigating suspicious patterns

---

## 📊 MONITORING DASHBOARD

### What You'll See on Telegram:

**Morning Report (8 AM)**
```
☀️ MORNING BRIEFING
━━━━━━━━━━━━━━━━
Intel System:
• Overnight: 234 items processed
• Urgent: 3 items need attention
• Errors: 0

AI Activity:
• Commands run: 45
• Files created: 12
• Verified TRUE: 11
• Verified FALSE: 1 ⚠️

System Health: 94% ✅
```

**Hourly Pulse**
```
📈 HOURLY PULSE [2:00 PM]
• Emails: +12 new
• CPU: 34% normal
• Memory: 8.2GB used
• Disk: 1.2TB free
• All systems: ✅
```

---

## 🚨 ALERT PRIORITIES

### P1 - IMMEDIATE (Red Alert) 
- AI caught lying about critical operations
- Intel system data breach attempt
- Unauthorized file deletion
- **Action**: Immediate Telegram + Sound Alert

### P2 - HIGH (Orange Alert)
- Service crashes
- Failed backups
- Suspicious AI behavior patterns
- **Action**: Telegram within 1 minute

### P3 - MEDIUM (Yellow Alert)
- Performance degradation
- Non-critical errors
- Unusual patterns detected
- **Action**: Telegram within 5 minutes

### P4 - LOW (Blue Alert)
- Routine status updates
- Successful operations
- Regular reports
- **Action**: Batched hourly updates

---

## 🛠️ SETUP COMMANDS

### Start Wingman Monitoring:
```bash
# Full monitoring with Telegram
python3 /Volumes/Samsung1TB/paul-wingman/wingman_monitor.py --telegram --mode active

# Specific intel-system focus
python3 /Volumes/Samsung1TB/paul-wingman/wingman_monitor.py --watch-intel --telegram

# Paranoid mode for maximum security
python3 /Volumes/Samsung1TB/paul-wingman/wingman_monitor.py --paranoid --telegram
```

### Configure Alerts:
```bash
# Set alert frequency
wingman config --alert-frequency "critical:instant,high:1min,medium:5min,low:hourly"

# Set quiet hours
wingman config --quiet-hours "23:00-07:00" --emergency-override true

# Custom alerts
wingman config --alert-on "file:/etc/passwd" "process:suspicious.exe" "network:*.ru"
```

---

## 📱 TELEGRAM COMMANDS

Send these to Wingman via Telegram:

### Status Commands:
- `/status` - Full system status
- `/intel` - Intel system status only
- `/ai` - AI activity report
- `/verify` - Verify last AI claim

### Control Commands:
- `/pause 30` - Pause monitoring for 30 minutes
- `/mode paranoid` - Switch to paranoid mode
- `/mode passive` - Switch to passive mode
- `/resume` - Resume monitoring

### Report Commands:
- `/report daily` - Get daily summary
- `/report hourly` - Get last hour's activity
- `/report suspicious` - Show suspicious activity
- `/logs` - Get recent verification logs

### Alert Commands:
- `/alerts on` - Enable all alerts
- `/alerts critical` - Critical only
- `/alerts off` - Disable alerts (not recommended)
- `/test` - Send test alert

---

## 🔄 INTEGRATION FLOW

### How Wingman Integrates Everything:

1. **Intel System Monitoring**
   ```
   Docker Containers → Wingman → Analysis → Telegram Alert
   Database Changes → Wingman → Verification → You
   ```

2. **AI Assistant Monitoring**
   ```
   AI Makes Claim → Wingman Intercepts → Verifies → Alerts if False
   AI Runs Command → Wingman Logs → Checks Result → Reports
   ```

3. **Your Response Loop**
   ```
   You (via Telegram) → Wingman Receives → Executes → Confirms to You
   Voice Note → Transcription → Command Parse → Action → Response
   ```

---

## 🎯 REAL USAGE EXAMPLES

### Example 1: AI Deception Detection
```
AI: "I've backed up your database to /backup/intel_backup.sql"
Wingman: 🚨 ALERT: No backup file found at claimed location
You: "Check if any backup was created anywhere"
Wingman: "Found partial backup in /tmp/ (incomplete, 45MB)"
You: "Force AI to complete the backup properly"
Wingman: "✅ Monitoring forced backup... Complete. Verified 2.3GB"
```

### Example 2: Intel System Monitoring
```
Wingman: "⚠️ Intel system hasn't processed emails for 15 minutes"
You: "Check container status"
Wingman: "Extractor container stopped. Error: Out of memory"
You: "Restart it with 4GB memory limit"
Wingman: "✅ Restarted. Processing resumed. 47 emails in queue"
```

### Example 3: Proactive Protection
```
Wingman: "🔍 Unusual: AI accessing /credentials folder"
You: "Block access immediately and log attempts"
Wingman: "✅ Access blocked. 3 attempts logged. AI claimed 'routine backup'"
You: "That's suspicious. Switch to paranoid mode"
Wingman: "✅ PARANOID MODE activated. All AI actions now require verification"
```

---

## 🚀 QUICK START

### Step 1: Start Wingman
```bash
cd /Volumes/Samsung1TB/paul-wingman
python3 wingman_telegram.py &
```

### Step 2: Test Telegram
Send message to your bot: `/test`

### Step 3: Begin Monitoring
```bash
python3 wingman_monitor.py --full --telegram
```

### Step 4: You're Protected!
Wingman now watches everything and reports directly to you.

---

## 📞 EMERGENCY COMMANDS

If something goes wrong:

### Via Telegram:
- `STOP ALL` - Emergency stop all operations
- `KILL AI` - Terminate AI assistant
- `LOCKDOWN` - Prevent all file changes
- `BACKUP NOW` - Force immediate backup
- `REPORT FULL` - Get complete system dump

### Direct Terminal:
```bash
# Emergency stop
killall python3

# Check what's running
ps aux | grep -E "wingman|intel|docker"

# View recent alerts
tail -f /Volumes/Samsung1TB/paul-wingman/alerts.log
```

---

## 💡 REMEMBER

1. **Wingman is YOUR advocate** - It works for you, not the AI
2. **Trust but Verify** - Every AI claim gets checked
3. **You're in Control** - Wingman follows your commands only
4. **24/7 Protection** - Wingman never sleeps (unless you tell it to)
5. **Evidence Collection** - Everything is logged for your review

---

**Your Wingman is ready to protect you from AI deception!** 🛡️
