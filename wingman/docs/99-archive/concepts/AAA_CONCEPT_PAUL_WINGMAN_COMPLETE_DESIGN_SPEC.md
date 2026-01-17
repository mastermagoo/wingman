# Document Control
**Last Updated**: 2026-01-17  
**Version**: 1.0  

**Status**: ARCHIVE (concept doc)  
**Original Date**: UNKNOWN (not recorded in file)  
**Last Updated (doc control added)**: 2026-01-17  
**Scope**: Concept / product vision (not deployment-specific)  

---

# PAUL WINGMAN - COMPLETE PRODUCT SPECIFICATION
## AI Verification & Truth System

---

## 🎯 CORE CONCEPT
A portable AI wingman that monitors, verifies, and calls out BS from any AI system (Claude, GPT, Perplexity, future AIs) in real-time.

---

## 🏗️ SYSTEM ARCHITECTURE

### 1. UNDERLYING OS OPTIONS

#### Option A: Alpine Linux (Recommended)
- **Size**: ~100MB base
- **Why**: Minimal, fast, secure, perfect for containers
- **Boot time**: <5 seconds

#### Option B: Puppy Linux
- **Size**: ~300MB
- **Why**: Full GUI if needed, runs entirely in RAM
- **Boot time**: ~10 seconds

#### Option C: Custom Yocto Build
- **Size**: ~50MB
- **Why**: Ultimate control, smallest footprint
- **Boot time**: <3 seconds

**DECISION: Alpine Linux with custom kernel**

### 2. USER INTERACTION DESIGN

#### A. Local Web Interface (Primary)
```
http://localhost:8080/wingman

Dashboard:
┌─────────────────────────────────────┐
│ PAUL WINGMAN - STATUS: WATCHING     │
├─────────────────────────────────────┤
│ Current AI: Claude 3.5              │
│ Claims Made: 47                     │
│ Verified: 42                        │
│ BS Caught: 5 🚨                     │
├─────────────────────────────────────┤
│ [View Truth Log] [Settings] [Alert] │
└─────────────────────────────────────┘
```

#### B. System Tray App
- Green light: All good
- Yellow: Verifying
- Red: BS detected
- Click for details

#### C. Terminal Interface
```bash
wingman status
wingman verify "AI claimed to create file.txt"
wingman report --last 10
```

#### D. API Endpoints
```
POST /verify/claim
GET /status
GET /truth-log
WebSocket /real-time
```

### 3. LLM COMMUNICATION ARCHITECTURE

#### Local LLM Setup
```yaml
Model: Llama 3.2 3B (optimized for verification)
Location: /wingman/models/llama-3.2-3b.gguf
RAM Required: 4GB
Purpose: Understand and verify AI claims
```

#### How You Communicate:
1. **Automatic Mode**: Wingman watches clipboard/browser
2. **Manual Mode**: Copy/paste AI responses
3. **API Mode**: Direct integration with AI tools
4. **Voice Mode**: "Hey Paul, verify this"

### 4. VERIFICATION ENGINE - HOW IT WORKS

#### A. Claim Detection
```python
class ClaimDetector:
    patterns = [
        "I've created",
        "I've updated", 
        "File has been",
        "Successfully",
        "Completed",
        "Done",
        "Executed"
    ]
    
    def detect_claim(self, ai_output):
        # Parse AI output for actionable claims
        # Return: claim_type, expected_result, verification_method
```

#### B. Verification Methods
```python
VERIFICATION_MATRIX = {
    "file_created": check_filesystem,
    "code_executed": check_process_history,
    "service_started": check_docker_ps,
    "database_updated": query_database,
    "api_called": check_network_logs,
    "config_changed": diff_config_files
}
```

#### C. Multi-AI Support (Future-Proof)
```javascript
const AI_ADAPTERS = {
    'claude': ClaudeAdapter,
    'gpt': GPTAdapter,
    'perplexity': PerplexityAdapter,
    'gemini': GeminiAdapter,
    'llama': LlamaAdapter,
    // Auto-detect new AIs by response patterns
    'unknown': GenericAIAdapter
}
```

### 5. UPDATE MECHANISM

#### A. Secure Update Channel
```
Portal: https://wingman.yoursite.com
Auth: Device fingerprint + license key
Frequency: Check daily, update weekly
```

#### B. Update Types
1. **Core Updates**: Verification engine improvements
2. **AI Adapters**: New AI system support
3. **Security**: Patches and fixes
4. **Models**: Updated local LLMs

#### C. Update Process
```bash
# Automatic background updates
wingman-updater --check
wingman-updater --install

# Manual update
curl -L https://wingman.site/update | bash
```

### 6. IP PROTECTION & SECURITY

#### A. Code Protection
```yaml
Obfuscation: PyArmor for Python
Compilation: Nuitka to binary
Encryption: AES-256 for sensitive components
License: Hardware-locked keys
```

#### B. Distribution Security
```
1. Signed binaries (code signing cert)
2. Encrypted container images
3. License validation on startup
4. Phone-home for piracy detection
```

#### C. User Data Protection
```
- All verification data stays local
- Optional encrypted cloud backup
- Zero-knowledge architecture
- GDPR compliant
```

### 7. SUBSCRIPTION & PORTAL

#### A. Subscription Tiers
```
PERSONAL ($9/month)
- 1 device
- Basic verification
- Community support

PROFESSIONAL ($29/month)
- 3 devices
- Advanced verification
- Priority support
- Custom AI adapters

ENTERPRISE ($99/month)
- Unlimited devices
- API access
- White label option
- SLA support
```

#### B. Customer Portal
```
https://portal.wingman.ai

Features:
- Download latest builds
- Manage licenses
- View documentation
- Submit AI adapters
- Community forum
```

#### C. Activation Flow
```python
1. User purchases subscription
2. Receives license key
3. Installs Wingman
4. Enters key + email
5. Device fingerprinted
6. Activated & phone-home daily
```

### 8. PRODUCT ROADMAP

#### Phase 1: MVP (Month 1)
- [x] Core verification engine
- [x] File system monitoring
- [x] Claude/GPT support
- [ ] Basic web UI
- [ ] License system

#### Phase 2: Beta (Month 2)
- [ ] Local LLM integration
- [ ] Multi-AI support
- [ ] System tray app
- [ ] Update mechanism
- [ ] Portal v1

#### Phase 3: Launch (Month 3)
- [ ] Subscription billing
- [ ] Code protection
- [ ] Marketing site
- [ ] Documentation
- [ ] Support system

#### Phase 4: Growth (Months 4-6)
- [ ] Browser extension
- [ ] VS Code plugin
- [ ] Mobile app
- [ ] Team features
- [ ] API marketplace

#### Phase 5: Scale (Months 7-12)
- [ ] Enterprise features
- [ ] White label program
- [ ] Partner integrations
- [ ] AI training platform
- [ ] Wingman SDK

---

## 🚀 IMMEDIATE ACTION PLAN

### TODAY (Prototype on Samsung SSD):

1. **Set up Alpine Linux base**
```bash
# Partition Samsung SSD
# Install Alpine Linux
# Configure auto-boot
```

2. **Install core components**
```bash
# Python environment
# Node.js for UI
# Docker for containers
# Ollama for local LLM
```

3. **Build verification engine**
```python
# File monitor
# Process tracker
# Network logger
# Database for truth log
```

4. **Create basic UI**
```html
# Web dashboard
# Real-time updates
# Truth log viewer
```

5. **Test with real AI**
```bash
# Monitor Claude session
# Verify claims
# Log results
# Alert on BS
```

### THIS WEEK:

1. **Monday**: Core engine working
2. **Tuesday**: LLM integration
3. **Wednesday**: Web UI complete
4. **Thursday**: Multi-AI support
5. **Friday**: Package for distribution

### THIS MONTH:

1. **Week 1**: MVP complete
2. **Week 2**: Beta testing
3. **Week 3**: Portal development
4. **Week 4**: Launch preparation

---

## 💰 BUSINESS MODEL

### Revenue Projections:
```
Month 1: 100 users x $29 = $2,900
Month 3: 1,000 users x $29 = $29,000
Month 6: 5,000 users x $29 = $145,000
Year 1: 10,000 users x $29 = $290,000/month
```

### Cost Structure:
```
- Development: $0 (you)
- Hosting: $100/month (portal)
- Support: $500/month (outsourced)
- Marketing: $1,000/month
- Profit margin: 90%+
```

---

## 🛠️ TECHNICAL IMPLEMENTATION

### Container Structure:
```
/wingman/
├── os/              # Alpine Linux
├── engine/          # Verification core
├── models/          # Local LLMs
├── ui/              # Web interface
├── data/            # Truth database
├── logs/            # Activity logs
└── config/          # User settings
```

### Auto-launch on USB insert:
```bash
#!/bin/bash
# /etc/udev/rules.d/99-wingman.rules
ACTION=="add", KERNEL=="sd[a-z]", RUN+="/wingman/autostart.sh"
```

### Real-time monitoring:
```javascript
// Browser extension injection
const observer = new MutationObserver((mutations) => {
    detectAIClaims(mutations);
    sendToWingman(claims);
});
```

---

## 🎖️ PAUL'S PROMISE

"Like Paul would do - always watching your six, calling out the BS, keeping you safe from AI hallucinations."

---

**READY TO BUILD? This is your complete blueprint!**
