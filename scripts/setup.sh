#!/usr/bin/env bash
# GestureHub Local Development Setup Script
set -euo pipefail

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()    { echo -e "${CYAN}[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

echo -e "${CYAN}"
echo "  ╔══════════════════════════════╗"
echo "  ║   GestureHub Setup Script    ║"
echo "  ╚══════════════════════════════╝"
echo -e "${NC}"

# ── Check prerequisites ────────────────────────────────────────────────
info "Checking prerequisites..."

command -v node >/dev/null 2>&1 || error "Node.js not found. Install from https://nodejs.org (>=18)"
command -v npm  >/dev/null 2>&1 || error "npm not found."

NODE_MAJOR=$(node -e "process.stdout.write(process.version.split('.')[0].slice(1))")
if (( NODE_MAJOR < 18 )); then
  error "Node.js >= 18 required. Found: $(node --version)"
fi

success "Node.js $(node --version), npm $(npm --version)"

# ── Backend setup ──────────────────────────────────────────────────────
info "Installing backend dependencies..."
cd "$(dirname "$0")/../backend"
npm install
success "Backend dependencies installed"

# ── Create .env ────────────────────────────────────────────────────────
if [[ ! -f .env ]]; then
  cp .env.example .env
  # Generate a random JWT secret
  if command -v openssl >/dev/null 2>&1; then
    SECRET=$(openssl rand -hex 32)
    # Cross-platform sed (Linux: sed -i, macOS: sed -i '')
    if sed --version 2>/dev/null | grep -q GNU; then
      sed -i "s/gesturehub-secret-change-in-production/$SECRET/" .env
    else
      sed -i '' "s/gesturehub-secret-change-in-production/$SECRET/" .env
    fi
    success "Generated random JWT_SECRET in backend/.env"
  else
    warn "openssl not found — please set JWT_SECRET manually in backend/.env"
  fi
else
  warn "backend/.env already exists, skipping"
fi

# ── Frontend setup ─────────────────────────────────────────────────────
info "Installing frontend dependencies..."
cd ../frontend
npm install
success "Frontend dependencies installed"

if [[ ! -f .env ]]; then
  cat > .env <<'EOF'
VITE_API_URL=/api
VITE_SOCKET_URL=
EOF
  success "Created frontend/.env"
fi

# ── Done ───────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}══════════════════════════════════════════${NC}"
echo -e "${GREEN}  Setup complete! Start GestureHub with:${NC}"
echo ""
echo -e "  ${CYAN}Terminal 1 (Backend):${NC}"
echo "    cd backend && npm run dev"
echo ""
echo -e "  ${CYAN}Terminal 2 (Frontend):${NC}"
echo "    cd frontend && npm run dev"
echo ""
echo -e "  ${CYAN}Or use Docker Compose:${NC}"
echo "    docker compose up --build"
echo -e "${GREEN}══════════════════════════════════════════${NC}"
