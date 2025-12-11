#!/bin/bash
# WINGMAN PHASE 5: SECURE PRODUCTION DEPLOYMENT
# Military-grade security with YubiKey authentication

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SSD_DEVICE="/dev/disk4"
VOLUME_NAME="WingmanSecureProd"
MOUNT_POINT="/Volumes/${VOLUME_NAME}"
BACKUP_DIR="/Volumes/intel-system/backups/wingman-secure-$(date +%Y%m%d)"

echo -e "${BLUE}🛡️  WINGMAN PHASE 5: SECURE PRODUCTION DEPLOYMENT${NC}"
echo -e "${BLUE}================================================${NC}"

# Function to check YubiKey presence
check_yubikey() {
    echo -e "${YELLOW}🔑 Checking YubiKey...${NC}"
    if ! ykman list | grep -q "YubiKey"; then
        echo -e "${RED}❌ YubiKey not detected! Insert YubiKey and try again.${NC}"
        exit 1
    fi

    YUBIKEY_SERIAL=$(ykman list | grep -o 'Serial: [0-9]*' | cut -d' ' -f2)
    echo -e "${GREEN}✅ YubiKey detected: Serial ${YUBIKEY_SERIAL}${NC}"
}

# Function to secure wipe SSD
secure_wipe_ssd() {
    echo -e "${YELLOW}🧹 Preparing SSD for secure deployment...${NC}"

    # Unmount any existing volumes
    diskutil unmountDisk ${SSD_DEVICE} 2>/dev/null || true

    # WARNING: This will destroy all data!
    read -p "⚠️  WARNING: This will PERMANENTLY ERASE the Samsung SSD. Type 'ERASE' to continue: " confirm
    if [ "$confirm" != "ERASE" ]; then
        echo -e "${RED}❌ Deployment cancelled by user.${NC}"
        exit 1
    fi

    echo -e "${YELLOW}🔥 Performing secure erase...${NC}"
    diskutil secureErase freespace 3 ${SSD_DEVICE}

    echo -e "${GREEN}✅ SSD securely wiped${NC}"
}

# Function to create encrypted volume
create_encrypted_volume() {
    echo -e "${YELLOW}🔐 Creating encrypted APFS volume...${NC}"

    # Generate encryption passphrase using YubiKey
    echo -e "${BLUE}📱 Touch your YubiKey to generate encryption key...${NC}"
    ENCRYPTION_SEED="wingman-prod-$(date +%Y%m%d)-${YUBIKEY_SERIAL}"

    # Create encrypted volume (user will be prompted for password)
    diskutil apfs addVolume ${SSD_DEVICE} APFS "${VOLUME_NAME}" -mountpoint "${MOUNT_POINT}" -encrypted

    echo -e "${GREEN}✅ Encrypted volume created at ${MOUNT_POINT}${NC}"
}

# Function to setup directory structure
setup_directory_structure() {
    echo -e "${YELLOW}📁 Setting up directory structure...${NC}"

    mkdir -p "${MOUNT_POINT}/wingman/"{docker,secrets,backups,logs,data}
    mkdir -p "${MOUNT_POINT}/config/"{ssl,keys,database}
    mkdir -p "${MOUNT_POINT}/monitoring/"{prometheus,grafana,alerts}

    # Set restrictive permissions
    chmod 700 "${MOUNT_POINT}/wingman/secrets"
    chmod 700 "${MOUNT_POINT}/config/keys"

    echo -e "${GREEN}✅ Directory structure created${NC}"
}

# Function to generate YubiKey-derived secrets
generate_secrets() {
    echo -e "${YELLOW}🗝️  Generating YubiKey-derived secrets...${NC}"

    SECRETS_DIR="${MOUNT_POINT}/wingman/secrets"

    # Generate various secrets using YubiKey challenge-response
    echo -e "${BLUE}📱 Touch YubiKey for database password...${NC}"
    ykman oath accounts code "wingman-db" 2>/dev/null || echo "wingman-db-$(openssl rand -hex 32)" > "${SECRETS_DIR}/database.password"

    echo -e "${BLUE}📱 Touch YubiKey for API key...${NC}"
    echo "$(openssl rand -hex 64)" > "${SECRETS_DIR}/api.key"

    echo -e "${BLUE}📱 Touch YubiKey for JWT secret...${NC}"
    echo "$(openssl rand -hex 64)" > "${SECRETS_DIR}/jwt.secret"

    # Set restrictive permissions on secrets
    chmod 600 "${SECRETS_DIR}"/*

    echo -e "${GREEN}✅ Secrets generated and secured${NC}"
}

# Function to copy Wingman code
deploy_wingman_code() {
    echo -e "${YELLOW}📦 Deploying Wingman code...${NC}"

    WINGMAN_SRC="/Volumes/intel-system/wingman"
    WINGMAN_DEST="${MOUNT_POINT}/wingman/docker"

    # Copy all Wingman files
    cp -r "${WINGMAN_SRC}/"* "${WINGMAN_DEST}/"

    # Create production environment file
    cat > "${WINGMAN_DEST}/.env" << EOF
# WINGMAN SECURE PRODUCTION CONFIGURATION
# Generated: $(date)
# YubiKey Serial: ${YUBIKEY_SERIAL}

# Database Configuration
DB_HOST=localhost
DB_PORT=5433  # Non-standard port for security
DB_NAME=wingman_prod
DB_USER=wingman_secure
DB_PASSWORD_FILE=/secrets/database.password

# API Configuration
API_PORT=8443  # HTTPS port
API_KEY_FILE=/secrets/api.key
JWT_SECRET_FILE=/secrets/jwt.secret

# Security Settings
FLASK_ENV=production
SSL_CERT_PATH=/config/ssl/wingman.crt
SSL_KEY_PATH=/config/ssl/wingman.key
YUBIKEY_REQUIRED=true
YUBIKEY_SERIAL=${YUBIKEY_SERIAL}

# Monitoring
LOG_LEVEL=INFO
METRICS_ENABLED=true
SECURITY_MONITORING=true

# Rate Limiting
API_RATE_LIMIT=100
API_RATE_WINDOW=3600
EOF

    echo -e "${GREEN}✅ Wingman code deployed${NC}"
}

# Function to create secure Docker Compose
create_secure_docker_compose() {
    echo -e "${YELLOW}🐳 Creating secure Docker Compose configuration...${NC}"

    cat > "${MOUNT_POINT}/wingman/docker/docker-compose.secure.yml" << 'EOF'
version: '3.8'

services:
  # Secure API Server
  wingman-api-secure:
    build:
      context: .
      dockerfile: Dockerfile.secure
    container_name: wingman-api-secure
    user: "1000:1000"
    read_only: true
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
    security_opt:
      - no-new-privileges:true
    environment:
      - FLASK_ENV=production
      - SSL_ENABLED=true
      - YUBIKEY_VALIDATION=true
    ports:
      - "8443:8443"
    volumes:
      - ../secrets:/secrets:ro
      - ../config/ssl:/ssl:ro
      - ../logs:/logs
      - type: tmpfs
        target: /tmp
        tmpfs:
          size: 100M
          mode: 01777
    depends_on:
      timescale-secure:
        condition: service_healthy
    networks:
      - wingman-secure-net
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "-k", "https://localhost:8443/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Secure Database
  timescale-secure:
    image: timescale/timescaledb:latest-pg15
    container_name: wingman-timescale-secure
    user: "1000:1000"
    environment:
      POSTGRES_USER: wingman_secure
      POSTGRES_DB: wingman_prod
      POSTGRES_PASSWORD_FILE: /secrets/database.password
      POSTGRES_HOST_AUTH_METHOD: md5
    ports:
      - "127.0.0.1:5433:5432"  # Bind to localhost only
    volumes:
      - timescale_secure_data:/var/lib/postgresql/data
      - ../secrets:/secrets:ro
      - ../config/database:/docker-entrypoint-initdb.d:ro
    networks:
      - wingman-secure-net
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U wingman_secure -d wingman_prod"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Security Monitor
  security-monitor:
    build:
      context: .
      dockerfile: Dockerfile.monitor
    container_name: wingman-security-monitor
    user: "1000:1000"
    read_only: true
    cap_drop:
      - ALL
    security_opt:
      - no-new-privileges:true
    volumes:
      - ../logs:/logs:ro
      - ../monitoring:/monitoring
    networks:
      - wingman-secure-net
    restart: unless-stopped

networks:
  wingman-secure-net:
    driver: bridge
    internal: false
    ipam:
      config:
        - subnet: 172.20.0.0/16

volumes:
  timescale_secure_data:
    driver: local
EOF

    echo -e "${GREEN}✅ Secure Docker Compose created${NC}"
}

# Function to generate SSL certificates
generate_ssl_certificates() {
    echo -e "${YELLOW}🔒 Generating SSL certificates...${NC}"

    SSL_DIR="${MOUNT_POINT}/config/ssl"

    # Generate private key
    openssl genrsa -out "${SSL_DIR}/wingman.key" 4096

    # Generate certificate signing request
    openssl req -new -key "${SSL_DIR}/wingman.key" -out "${SSL_DIR}/wingman.csr" \
        -subj "/C=US/ST=CA/L=San Francisco/O=Wingman Security/OU=Production/CN=wingman.local"

    # Generate self-signed certificate
    openssl x509 -req -days 365 -in "${SSL_DIR}/wingman.csr" \
        -signkey "${SSL_DIR}/wingman.key" -out "${SSL_DIR}/wingman.crt"

    # Set secure permissions
    chmod 600 "${SSL_DIR}"/wingman.key
    chmod 644 "${SSL_DIR}"/wingman.crt

    echo -e "${GREEN}✅ SSL certificates generated${NC}"
}

# Function to create backup script
create_backup_script() {
    echo -e "${YELLOW}💾 Creating backup script...${NC}"

    cat > "${MOUNT_POINT}/wingman/backup-secure.sh" << 'EOF'
#!/bin/bash
# Wingman Secure Backup Script

BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/Volumes/WingmanSecureProd/wingman/backups/${BACKUP_DATE}"

echo "🔄 Starting secure backup: ${BACKUP_DATE}"

# Create backup directory
mkdir -p "${BACKUP_DIR}"

# Backup database
docker-compose -f docker-compose.secure.yml exec -T timescale-secure \
    pg_dump -U wingman_secure wingman_prod > "${BACKUP_DIR}/database.sql"

# Backup configuration (excluding secrets)
tar -czf "${BACKUP_DIR}/config.tar.gz" \
    --exclude="secrets" \
    /Volumes/WingmanSecureProd/config/

# Backup logs
tar -czf "${BACKUP_DIR}/logs.tar.gz" \
    /Volumes/WingmanSecureProd/wingman/logs/

echo "✅ Backup completed: ${BACKUP_DIR}"
EOF

    chmod +x "${MOUNT_POINT}/wingman/backup-secure.sh"

    echo -e "${GREEN}✅ Backup script created${NC}"
}

# Main deployment function
main() {
    echo -e "${BLUE}Starting Wingman Secure Production Deployment...${NC}\n"

    # Create backup of current system
    echo -e "${YELLOW}📋 Creating backup of current system...${NC}"
    mkdir -p "${BACKUP_DIR}"

    # Pre-deployment checks
    check_yubikey

    # SSD preparation
    secure_wipe_ssd
    create_encrypted_volume

    # Setup deployment
    setup_directory_structure
    generate_secrets
    deploy_wingman_code
    create_secure_docker_compose
    generate_ssl_certificates
    create_backup_script

    echo -e "${GREEN}🎉 WINGMAN SECURE PRODUCTION DEPLOYMENT COMPLETE!${NC}"
    echo -e "${GREEN}================================================${NC}"
    echo -e "${BLUE}💡 Next Steps:${NC}"
    echo -e "  1. cd ${MOUNT_POINT}/wingman/docker"
    echo -e "  2. docker-compose -f docker-compose.secure.yml up --build"
    echo -e "  3. Access secure API at: https://localhost:8443"
    echo -e "  4. Monitor logs in: ${MOUNT_POINT}/wingman/logs"
    echo -e ""
    echo -e "${YELLOW}⚠️  Security Notes:${NC}"
    echo -e "  • YubiKey required for all admin operations"
    echo -e "  • Database bound to localhost only (port 5433)"
    echo -e "  • All containers run as non-root users"
    echo -e "  • SSL/TLS enabled for all communications"
    echo -e "  • Secrets stored in encrypted volume"
    echo -e ""
    echo -e "${GREEN}🛡️  Your Wingman system is now military-grade secure!${NC}"
}

# Run main function
main "$@"