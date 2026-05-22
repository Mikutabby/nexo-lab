#!/bin/bash
# 🧠 Nexo Ecosystem — Instalador automático
# Uso: ./install.sh [--help]

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info()  { echo -e "${BLUE}[INFO]${NC} $*"; }
ok()    { echo -e "${GREEN}[OK]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
err()   { echo -e "${RED}[ERR]${NC} $*"; }

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BIN_DIR="$HOME/.local/bin"
OPENCODE_DIR="$HOME/.opencode"
AGENT_DIR="$OPENCODE_DIR/agents"
MEMORY_DIR="$HOME/.nexo-memory"

echo ""
echo "========================================"
echo "  🧠 Nexo Ecosystem Installer"
echo "========================================"
echo ""

# ── Verificar SO ────────────────────────────────────────────────────────
if [[ "$(uname)" != "Linux" ]]; then
    err "Este instalador solo funciona en Linux"
    exit 1
fi

# ── Solicitar sudo password ─────────────────────────────────────────────
echo -n "🔑 Ingresá tu contraseña sudo (se usará para servicios systemd): "
read -s SUDO_PASS
echo ""
if ! echo "$SUDO_PASS" | sudo -S -v 2>/dev/null; then
    err "Contraseña incorrecta"
    exit 1
fi
ok "Acceso sudo verificado"
echo ""

# ── Crear directorios ──────────────────────────────────────────────────
info "Creando directorios..."
mkdir -p "$BIN_DIR" "$AGENT_DIR" "$MEMORY_DIR"
ok "Directorios creados"

# ── Copiar scripts ─────────────────────────────────────────────────────
info "Copiando scripts..."

# system/
cp "$SCRIPT_DIR/system/check-identity.sh" "$BIN_DIR/"
cp "$SCRIPT_DIR/system/face-recognize.py" "$BIN_DIR/"
cp "$SCRIPT_DIR/system/temp-monitor.sh" "$BIN_DIR/"
sed "s/\$SUDO_PASS/$SUDO_PASS/g" "$SCRIPT_DIR/system/temp-cancel.sh" > "$BIN_DIR/temp-cancel.sh"
cp "$SCRIPT_DIR/system/limpiar" "$BIN_DIR/"
cp "$SCRIPT_DIR/system/falkon-rapido" "$BIN_DIR/"

# graph/
cp "$SCRIPT_DIR/graph/nexo-graph" "$BIN_DIR/"
cp "$SCRIPT_DIR/graph/nexo-memory" "$BIN_DIR/"

# tools/
cp "$SCRIPT_DIR/tools/nexo-tools" "$BIN_DIR/"
cp "$SCRIPT_DIR/tools/nexo-diary" "$BIN_DIR/"
cp "$SCRIPT_DIR/tools/nexo-evaluate" "$BIN_DIR/"
sed "s|\$HOME|$HOME|g" "$SCRIPT_DIR/tools/nexo-wake" > "$BIN_DIR/nexo-wake"

# voice/
cp "$SCRIPT_DIR/voice/say.sh" "$OPENCODE_DIR/"
cp "$SCRIPT_DIR/voice/voice.sh" "$OPENCODE_DIR/"

# agent/
sed -e "s/\*\*TU_PASSWORD\*\*/$SUDO_PASS/g" \
    -e "s|\\\$HOME|$HOME|g" \
    "$SCRIPT_DIR/agent/asistente.md" > "$AGENT_DIR/asistente.md"

# backup
cp "$SCRIPT_DIR/backup/migrar-miku.sh" "$HOME/"

chmod +x "$BIN_DIR"/* "$OPENCODE_DIR/say.sh" "$OPENCODE_DIR/voice.sh"
ok "Scripts copiados y ejecutables"

# ── Inicializar Knowledge Graph ────────────────────────────────────────
info "Inicializando Knowledge Graph..."
"$BIN_DIR/nexo-graph" init 2>/dev/null || true
ok "Knowledge Graph inicializado"

# ── Configurar servicios systemd ────────────────────────────────────────
info "Configurando servicios systemd..."

# CPU Performance
cp "$SCRIPT_DIR/config/cpu-performance.service" /tmp/cpu-performance.service
echo "$SUDO_PASS" | sudo -S cp /tmp/cpu-performance.service /etc/systemd/system/ 2>/dev/null
echo "$SUDO_PASS" | sudo -S systemctl daemon-reload 2>/dev/null
echo "$SUDO_PASS" | sudo -S systemctl enable cpu-performance.service 2>/dev/null
echo "$SUDO_PASS" | sudo -S systemctl start cpu-performance.service 2>/dev/null
ok "Servicio CPU Performance configurado"

# Sudoers para temp-monitor
TEMP_SUDOERS="/tmp/nexo-temp-sudoers"
sed "s/\$SUDO_PASS/$SUDO_PASS/g" "$SCRIPT_DIR/config/sudoers.temp-monitor" > "$TEMP_SUDOERS"
echo "$SUDO_PASS" | sudo -S cp "$TEMP_SUDOERS" /etc/sudoers.d/temp-monitor 2>/dev/null
echo "$SUDO_PASS" | sudo -S chmod 440 /etc/sudoers.d/temp-monitor 2>/dev/null
ok "Sudoers para temp-monitor configurado"

# Crontab
crontab "$SCRIPT_DIR/config/miku-crontab.txt" 2>/dev/null || true
ok "Crontab configurado"

# ── Verificar dependencias ──────────────────────────────────────────────
info "Verificando dependencias..."

DEPS_MISSING=""
for cmd in python3 jq sqlite3; do
    if ! command -v "$cmd" &>/dev/null; then
        DEPS_MISSING="$DEPS_MISSING $cmd"
    fi
done

if [[ -n "$DEPS_MISSING" ]]; then
    warn "Faltan dependencias:$DEPS_MISSING"
    warn "Instalálas con: sudo apt install$DEPS_MISSING"
else
    ok "Todas las dependencias básicas presentes"
fi

# ── Verificar Ollama (opcional) ─────────────────────────────────────────
if command -v ollama &>/dev/null; then
    ok "Ollama detectado"
else
    warn "Ollama no detectado — los embeddings semánticos y diary no funcionarán"
    warn "Instalá Ollama: curl -fsSL https://ollama.com/install.sh | sh"
fi

echo ""
echo "========================================"
echo "  ✅ Nexo Ecosystem instalado"
echo "========================================"
echo ""
echo "   📍 Scripts:    $BIN_DIR/"
echo "   🧠 Memoria:    $MEMORY_DIR/"
echo "   🤖 Agente:     $AGENT_DIR/asistente.md"
echo "   🎤 Voz:        $OPENCODE_DIR/"
echo ""
echo "   Comandos disponibles:"
echo "     nexo-graph      — Knowledge Graph"
echo "     nexo-memory     — Memoria persistente"
echo "     nexo-tools      — Tool Registry"
echo "     nexo-diary      — Diary Summariser"
echo "     nexo-evaluate   — Evaluator"
echo "     nexo-wake       — Wake Word Detection"
echo "     limpiar         — Limpiador del sistema"
echo "     face-recognize  — Reconocimiento facial"
echo "     temp-monitor    — Monitor de temperatura"
echo ""
echo "   📖 README: $SCRIPT_DIR/README.md"
echo ""
