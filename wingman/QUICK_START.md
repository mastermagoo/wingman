#0 Wingman PRD Deployment - Quick Start

**Purpose:** Quick reference for deploying `wingman-test` to `wingman-prd`

Updating existing guide instead of creating new version

---

## 🚀 Quick Deployment

### **1. Prepare Environment File**

```bash
cd /Volumes/Data/ai_projects/intel-system/wingman
cp env.prd.example .env.prd
# Edit .env.prd with production values:
# - DB_PASSWORD (secure password)
# - BOT_TOKEN (production bot token)
# - CHAT_ID (production chat ID)
```

### **2. Run Deployment**

```bash
./deploy_test_to_prd.sh
```

### **3. Verify Deployment**

```bash
# Check containers
docker ps --filter "name=wingman.*-prd"

# Check API health
curl http://localhost:5000/health

# Check logs
docker logs wingman-api-prd --tail 50
```

---

## 📋 Prerequisites

- ✅ `wingman-test` environment running and healthy
- ✅ `docker-compose.prd.yml` exists
- ✅ `.env.prd` configured with production values
- ✅ Production bot token and chat ID available

---

## 🔧 Configuration

### **Required .env.prd Values:**

```bash
DB_PASSWORD=<secure_production_password>
BOT_TOKEN=<production_telegram_bot_token>
CHAT_ID=<production_telegram_chat_id>
```

### **Optional .env.prd Values:**

```bash
API_PORT=5000              # Default: 5000
DB_PORT=5432               # Default: 5432
REDIS_PORT=6379            # Default: 6379
OLLAMA_PORT=11434          # Default: 11434
LOG_LEVEL=INFO             # Default: INFO
```

---

## 🛠️ Troubleshooting

### **Deployment Fails:**

1. **Check TEST environment:**
   ```bash
   docker ps --filter "name=wingman.*-test"
   curl http://localhost:8101/health
   ```

2. **Check logs:**
   ```bash
   tail -f /tmp/wingman_test_to_prd_*.log
   docker logs wingman-api-prd
   ```

3. **Force redeploy:**
   ```bash
   ./deploy_test_to_prd.sh --force
   ```

### **API Not Responding:**

```bash
# Check container status
docker ps --filter "name=wingman-api-prd"

# Check logs
docker logs wingman-api-prd --tail 100

# Restart API
docker restart wingman-api-prd
```

### **Database Issues:**

```bash
# Check database status
docker exec wingman-postgres-prd pg_isready -U wingman_prd

# Check database logs
docker logs wingman-postgres-prd --tail 50
```

---

## 📚 Full Documentation

See `DEPLOYMENT_PLAN.md` for complete deployment details.

## ✅ Mandatory Promotion Pipeline (DEV → TEST → PRD)

All Wingman security features must be implemented and verified in **DEV first**, then promoted to **TEST** for further testing, and only after explicit approval promoted to **PRD**.

### Phase 4 (Original) HITL bundle (DEV stage)

- **Bundle location (in this repo)**: `wingman/promotion_bundles/phase4_hitl_dev/`
- **Apply to MBP DEV repo**:

```bash
cd /Volumes/Data/ai_projects/intel-system/wingman/promotion_bundles/phase4_hitl_dev
./apply_to_dev_repo.sh /Users/mark/Projects/wingman-system-dev
```

- **DEV verification** (once DEV API is running):

```bash
API_URL=http://localhost:8002 python3 wingman/dev_e2e_phase4.py
```

### Phase 4 (Original) HITL bundle (TEST stage)

- **Bundle location (in this repo)**: `wingman/promotion_bundles/phase4_hitl_test/`
- **Apply to TEST working tree** (Mac Studio TEST):

```bash
cd /Volumes/Data/ai_projects/intel-system/wingman/promotion_bundles/phase4_hitl_test
./sync_to_test_repo.sh /path/to/wingman-test-working-tree
```

- **Configure TEST env file** (no secrets in git):
  - Copy `env.test.example` to `.env.test` in the same directory as `telegram_bot.py`
  - Set:
    - `BOT_TOKEN` (TEST bot token)
    - `CHAT_ID` (approval chat id)
    - `API_URL` (for host-run: `http://127.0.0.1:8101`, for docker: `http://wingman-api:8001`)

- **Acceptance test (TEST)**:
  - API `/health` responds
  - Telegram bot responds to `/pending`
  - Orchestrator blocks on approval and unblocks after `/approve <id>`

---

**Last Updated:** 2025-12-16



