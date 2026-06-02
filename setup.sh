#!/usr/bin/env bash
# JARVIS Agent — Setup & Run Script
# Usage: bash setup.sh

set -e
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${CYAN}"
echo "  ░░░░░ JARVIS SETUP ░░░░░"
echo -e "${NC}"

# ── 1. Check Ollama ─────────────────────────────────────────────────
echo -e "${YELLOW}[1/4] Checking Ollama...${NC}"
if ! command -v ollama &> /dev/null; then
  echo "Ollama not found. Install from: https://ollama.com/download"
  exit 1
fi

echo "Pulling Mistral model (this may take a few minutes on first run)..."
ollama pull mistral

# ── 2. Python venv ───────────────────────────────────────────────────
echo -e "${YELLOW}[2/4] Setting up Python environment...${NC}"
cd agent
python3 -m venv .venv
source .venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo -e "${GREEN}✓ Python deps installed${NC}"

# ── 3. Create data dirs ──────────────────────────────────────────────
echo -e "${YELLOW}[3/4] Creating data directories...${NC}"
mkdir -p data/chroma
echo -e "${GREEN}✓ Data dirs ready${NC}"

# ── 4. Launch ────────────────────────────────────────────────────────
echo -e "${YELLOW}[4/4] Starting JARVIS agent...${NC}"
echo ""
echo -e "${GREEN}  Agent API: http://127.0.0.1:8765${NC}"
echo -e "${GREEN}  WebSocket: ws://127.0.0.1:8765/ws${NC}"
echo -e "${GREEN}  Health:    http://127.0.0.1:8765/health${NC}"
echo ""
echo -e "${CYAN}  Open ui/src/index.html in your browser to chat.${NC}"
echo -e "${CYAN}  (Tauri desktop build: cd .. && cargo tauri dev)${NC}"
echo ""

python main.py
