#!/usr/bin/env bash
# GestureHub VPS Deployment Script
# Usage: ./scripts/deploy-vps.sh <user@vps-host> [domain]
set -euo pipefail

GREEN='\033[0;32m'; CYAN='\033[0;36m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info()    { echo -e "${CYAN}[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

SSH_TARGET="${1:-}"
DOMAIN="${2:-harshhpatil.in}"
REPO_DIR="/opt/gesturehub"

[[ -z "$SSH_TARGET" ]] && error "Usage: $0 <user@vps-host> [domain]"

command -v ssh  >/dev/null || error "ssh not found"
command -v rsync >/dev/null || error "rsync not found"

info "Deploying GestureHub to $SSH_TARGET (domain: $DOMAIN)"

# ── 1. Sync files ──────────────────────────────────────────────────────
info "Syncing project files..."
rsync -avz --exclude='node_modules' --exclude='.git' --exclude='dist' \
  --exclude='*.db' --exclude='.env' \
  "$(dirname "$0")/../" "${SSH_TARGET}:${REPO_DIR}/"
success "Files synced"

# ── 2. Remote setup ────────────────────────────────────────────────────
ssh "$SSH_TARGET" bash <<REMOTE
set -e

cd $REPO_DIR

# Install Docker if needed
if ! command -v docker &>/dev/null; then
  echo "[Remote] Installing Docker..."
  curl -fsSL https://get.docker.com | sh
  usermod -aG docker \$USER
fi

if ! command -v docker-compose &>/dev/null && ! docker compose version &>/dev/null 2>&1; then
  echo "[Remote] Installing Docker Compose plugin..."
  apt-get install -y docker-compose-plugin
fi

# Create .env if missing
if [[ ! -f backend/.env ]]; then
  cp backend/.env.example backend/.env
  SECRET=\$(openssl rand -hex 32)
  sed -i "s/gesturehub-secret-change-in-production/\$SECRET/" backend/.env
  echo "[Remote] Created backend/.env"
fi

# Always update CORS_ORIGIN to match domain
sed -i "s|CORS_ORIGIN=.*|CORS_ORIGIN=https://$DOMAIN|" backend/.env

# Stop old containers
docker compose down || true

# Build and start
docker compose build --no-cache
docker compose up -d

echo "[Remote] Containers started"
docker compose ps
REMOTE

success "Deployment complete!"

# ── 3. SSL with Let's Encrypt ──────────────────────────────────────────
if [[ "$DOMAIN" != "localhost" ]]; then
  info "Setting up SSL for $DOMAIN..."
  ssh "$SSH_TARGET" bash <<SSLSCRIPT
if ! command -v certbot &>/dev/null; then
  apt-get install -y certbot
fi
certbot certonly --standalone -d $DOMAIN --non-interactive --agree-tos -m admin@$DOMAIN || true
SSLSCRIPT
  success "SSL certificate configured (check certbot output)"
fi

echo ""
echo -e "${GREEN}══════════════════════════════════════════════${NC}"
echo -e "${GREEN}  GestureHub deployed to https://$DOMAIN${NC}"
echo -e "${GREEN}══════════════════════════════════════════════${NC}"
