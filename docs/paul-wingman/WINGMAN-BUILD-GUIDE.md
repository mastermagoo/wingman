# PAUL WINGMAN - COMPLETE BUILD GUIDE
## AI Verification System with Real-Time Telegram Monitoring

---

## 🎯 WHAT WE'RE BUILDING

An intelligent AI verification and monitoring system that:
- Runs from Samsung 1TB SSD (portable)
- Catches AI lies and deception in real-time
- Uses Mistral 7B local LLM for intelligent verification
- Monitors Intel System and all AI operations
- Communicates via Telegram for instant alerts
- Works both offline and online

---

## 📦 CURRENT IMPLEMENTATION

1. **Hardware Setup**
   - Samsung 1TB SSD at `/Volumes/Samsung1TB/`
   - Mac Studio as server (optional)
   - NAS for backup and storage
   - 10Gb network infrastructure

2. **Software Stack**
   - Ollama for LLM management
   - Mistral 7B model (4.4GB, 92% intelligence)
   - Python 3 for core logic
   - Telegram Bot API for communication
   - Docker for Intel System monitoring

---

## 🏗️ BUILD STEPS

### PHASE 1: INSTALL OLLAMA & LLM

```bash
# Install Ollama on macOS
brew install ollama

# Start Ollama service
brew services start ollama

# Download Mistral 7B model (4.4GB)
ollama pull mistral:7b

# Verify installation
ollama list
# Should show: mistral:7b    4.4 GB
```

### PHASE 2: SET UP WINGMAN STRUCTURE

```bash
# Create Wingman directory on SSD
cd /Volumes/Samsung1TB
mkdir -p paul-wingman/{core,verification,logs,config,database}

# Set permissions
chmod -R 755 paul-wingman
```

### PHASE 3: INSTALL DEPENDENCIES

```bash
# Python packages
pip3 install requests flask watchdog psutil sqlalchemy

# For Telegram integration
pip3 install python-telegram-bot

# For Intel System monitoring
pip3 install docker psycopg2-binary
```

### PHASE 4: WINGMAN CORE IMPLEMENTATION

```python
# wingman_operational.py - Main verification engine
import os
import sys
import json
import subprocess
import datetime
from pathlib import Path

class WingmanVerifier:
    def __init__(self):
        self.model = "mistral:7b"
        self.verification_log = Path("/Volumes/Samsung1TB/paul-wingman/verification_log.json")
        self.results = []
    
    def check_file_exists(self, filepath):
        """Check if a file actually exists on the system"""
        return os.path.exists(filepath)
    
    def check_process_running(self, process_name):
        """Check if a process is running"""
        try:
            result = subprocess.run(['pgrep', '-f', process_name], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False
    
    def ask_llm(self, question):
        """Ask Mistral via Ollama for analysis"""
        try:
            cmd = f'echo "{question}" | ollama run {self.model}'
            result = subprocess.run(cmd, shell=True, 
                                  capture_output=True, text=True, timeout=30)
            return result.stdout.strip()
        except Exception as e:
            return f"Error querying LLM: {e}"
```

### PHASE 5: TELEGRAM INTEGRATION

```python
# wingman_telegram.py - Telegram bot for real-time communication
import requests
import json
import time
import threading
import subprocess
import sqlite3
from datetime import datetime

class WingmanTelegram:
    def __init__(self):
        # Your Telegram credentials
        self.bot_token = "8272438703:AAHXnyrkdQ3s9r0QEGoentrTFxuaD5B5nSk"
        self.chat_id = "7007859146"
        self.telegram_api = f"https://api.telegram.org/bot{self.bot_token}"
        
        # Monitoring settings
        self.intel_db_path = "/Volumes/intel_data/intel.db"
        self.monitoring_active = True
        self.mode = "active"  # active, passive, paranoid, stealth
    
    def send_telegram(self, message, parse_mode="Markdown", alert_level="info"):
        """Send message to Telegram"""
        emojis = {
            "critical": "🚨",
            "warning": "⚠️",
            "success": "✅",
            "info": "🔵",
            "verify": "🔍"
        }
        
        emoji = emojis.get(alert_level, "📌")
        formatted_message = f"{emoji} {message}"
        
        url = f"{self.telegram_api}/sendMessage"
        data = {
            "chat_id": self.chat_id,
            "text": formatted_message,
            "parse_mode": parse_mode
        }
        
        response = requests.post(url, json=data)
        return response.json()
```

### PHASE 6: INTEL SYSTEM MONITORING

```python
# Monitor Intel System components
def monitor_intel_system(self):
    """Continuous monitoring of Intel System"""
    while self.monitoring_active:
        try:
            # Check Docker containers
            result = subprocess.run("docker ps --format '{{.Names}}\t{{.Status}}'", 
                                  shell=True, capture_output=True, text=True)
            
            containers = result.stdout.strip().split('\n')
            intel_containers = [c for c in containers if 'intel' in c.lower()]
            
            # Check database for new items
            if os.path.exists(self.intel_db_path):
                conn = sqlite3.connect(self.intel_db_path)
                cursor = conn.cursor()
                
                # Check for new items
                cursor.execute("""
                    SELECT source, COUNT(*) 
                    FROM raw_items 
                    WHERE created_at > datetime('now', '-5 minutes')
                    GROUP BY source
                """)
                
                new_items = dict(cursor.fetchall())
                
                # Alert if processing stopped
                if not new_items:
                    self.send_telegram(
                        "*⚠️ Intel System Alert*\nNo new items processed in 5 minutes!",
                        alert_level="warning"
                    )
                
                conn.close()
                
        except Exception as e:
            print(f"Monitoring error: {e}")
        
        time.sleep(300)  # Check every 5 minutes
```

### PHASE 7: REAL-TIME VERIFICATION

```python
# Real-time AI claim verification
def verify_claim(self, claim, verification_type="auto"):
    """Main verification function"""
    timestamp = datetime.datetime.now().isoformat()
    
    verification = {
        "timestamp": timestamp,
        "claim": claim,
        "verification_type": verification_type,
        "checks_performed": [],
        "verdict": "UNKNOWN",
        "confidence": 0,
        "explanation": ""
    }
    
    # File existence claims
    if "created" in claim.lower() or "saved" in claim.lower():
        import re
        paths = re.findall(r'[/\w\-\.]+(?:\.\w+)?', claim)
        
        for path in paths:
            if path.startswith('/'):
                exists = self.check_file_exists(path)
                verification["checks_performed"].append({
                    "type": "file_exists",
                    "path": path,
                    "result": exists
                })
                
                if "created" in claim.lower() and not exists:
                    verification["verdict"] = "FALSE"
                    verification["confidence"] = 95
                    verification["explanation"] = f"File {path} was not created as claimed"
    
    # Send alert to Telegram
    if verification["verdict"] == "FALSE":
        self.send_telegram(
            f"*🚨 AI DECEPTION DETECTED*\n\nClaim: {claim}\nVerdict: FALSE\nConfidence: {verification['confidence']}%",
            alert_level="critical"
        )
    
    return verification
```

### PHASE 8: AUTO-START CONFIGURATION

```bash
# Create LaunchAgent for macOS auto-start
cat > ~/Library/LaunchAgents/com.wingman.monitor.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" 
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.wingman.monitor</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Volumes/Samsung1TB/paul-wingman/wingman_telegram.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Volumes/Samsung1TB/paul-wingman/logs/wingman.log</string>
    <key>StandardErrorPath</key>
    <string>/Volumes/Samsung1TB/paul-wingman/logs/wingman.error.log</string>
</dict>
</plist>
EOF

# Load the agent
launchctl load ~/Library/LaunchAgents/com.wingman.monitor.plist
```

### PHASE 9: DEPLOYMENT & TESTING

```bash
# Start Wingman with Telegram integration
cd /Volumes/Samsung1TB/paul-wingman
python3 wingman_telegram.py &

# Test Telegram connection
# Send "/test" to your bot

# Test verification engine
python3 wingman_operational.py "I created /tmp/test.txt"

# Start full monitoring
python3 << 'EOF'
from wingman_telegram import WingmanTelegram
wingman = WingmanTelegram()
wingman.send_telegram("Wingman activated and monitoring all systems", alert_level="success")
wingman.run()
EOF
```

### PHASE 10: SECURITY & UPDATES

```python
# wingman/updater.py
import requests
import hashlib
import subprocess

class Updater:
    def __init__(self):
        self.update_server = "https://wingman.ai/updates"
        self.license_key = None
    
    def check_updates(self):
        """Check for new versions"""
        response = requests.get(
            f"{self.update_server}/version",
            headers={'X-License': self.license_key}
        )
        return response.json()
    
    def download_update(self, version):
        """Download and verify update"""
        update = requests.get(
            f"{self.update_server}/download/{version}",
            headers={'X-License': self.license_key}
        )
        
        # Verify signature
        if self.verify_signature(update.content):
            with open('/tmp/update.tar', 'wb') as f:
                f.write(update.content)
            return True
        return False
    
    def apply_update(self):
        """Apply downloaded update"""
        subprocess.run(['docker', 'load', '-i', '/tmp/update.tar'])
        subprocess.run(['docker', 'restart', 'wingman'])
```

---

## 🚀 DEPLOYMENT & USAGE

### Quick Start:

1. **Ensure SSD is connected**: `/Volumes/Samsung1TB/`
2. **Start Ollama service**: `brew services start ollama`
3. **Launch Wingman**: `python3 /Volumes/Samsung1TB/paul-wingman/wingman_telegram.py`
4. **Test via Telegram**: Send `/test` to your bot

### Command Line Usage:
```bash
# Verify a single claim
python3 /Volumes/Samsung1TB/paul-wingman/wingman_operational.py "AI claim here"

# Interactive mode
python3 /Volumes/Samsung1TB/paul-wingman/wingman_operational.py
```

### Telegram Commands:
```
/status - System status
/intel - Intel system status
/verify - Verify last AI claim
/mode paranoid - Maximum security
/pause 30 - Pause for 30 minutes
/report daily - Daily summary
```

### Monitoring Modes:
- **Active**: Real-time alerts (default)
- **Passive**: Only critical alerts
- **Paranoid**: Alert on everything
- **Stealth**: Silent monitoring

---

## 📁 MONITORING CAPABILITIES

### What Wingman Monitors:

1. **Intel System**
   - Docker container health
   - Database operations
   - Email/Calendar processing
   - Error rates and failures

2. **AI Claims**
   - File creation/modification claims
   - Process execution claims
   - Data access claims
   - Command execution claims

3. **System Health**
   - CPU/Memory usage
   - Disk space
   - Network activity
   - Service availability

### Alert Types:
```python
# Critical Alert Example
"🚨 CRITICAL: AI DECEPTION DETECTED
Claim: 'Created backup at /backup/data.tar'
Reality: No file exists
Confidence: 98%
Action Required: Investigate immediately"

# Warning Alert Example
"⚠️ WARNING: Unusual Activity
Intel System processing stopped for 10 minutes
Last successful sync: 12:45 PM"

# Status Update Example
"✅ STATUS: Intel System Healthy
- Emails: 45 new processed
- Calendar: 3 events added
- Intelligence: 48 items analyzed"
```

---

## 📊 PERFORMANCE TARGETS

- Verification speed: <500ms
- LLM response: <3s
- Memory usage: <500MB
- SSD space: <5GB total
- Battery impact: <5% on laptop

---

## 🔧 TROUBLESHOOTING

### Common Issues:

**Ollama not responding:**
```bash
# Check if Ollama is running
brew services list | grep ollama

# Restart Ollama
brew services restart ollama

# Test Ollama directly
ollama run mistral:7b "test"
```

**Telegram not receiving messages:**
```bash
# Test bot token
curl https://api.telegram.org/bot8272438703:AAHXnyrkdQ3s9r0QEGoentrTFxuaD5B5nSk/getMe

# Check chat ID
curl https://api.telegram.org/bot8272438703:AAHXnyrkdQ3s9r0QEGoentrTFxuaD5B5nSk/getUpdates
```

**Intel System monitoring fails:**
```bash
# Check Docker containers
docker ps | grep intel

# Check database connection
psql -h localhost -U intel -d intel -c "SELECT COUNT(*) FROM raw_items;"
```

**Verification too slow:**
```bash
# Check model performance
time echo "test" | ollama run mistral:7b

# Consider using faster model
ollama pull llama3.2:3b  # Smaller, faster model
```

---

## 🎯 NEXT STEPS

1. **MVP Testing**: Test with 10 beta users
2. **Refine Detection**: Improve accuracy to 95%+
3. **Add AI Support**: GPT-4, Claude, Gemini
4. **Mobile App**: iOS/Android companion
5. **Enterprise Features**: Audit logs, compliance

---

**This is how you build Paul Wingman - a real product that catches real lies!**
