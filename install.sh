#!/bin/bash
# 🧠 Nexo Lab — Instalador automático
# Uso: ./install.sh [--help]

set -o pipefail

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
echo "  🧠 Nexo Lab Installer"
echo "========================================"
echo ""

# ── Verificar SO ────────────────────────────────────────────────────────
if [[ "$(uname)" != "Linux" ]]; then
    err "Este instalador solo funciona en Linux"
    exit 1
fi

# ── Verificar source files ──────────────────────────────────────────────
info "Verificando archivos fuente..."
MISSING_FILES=0
for f in \
    "$SCRIPT_DIR/system/check-identity.sh" \
    "$SCRIPT_DIR/system/face-recognize.py" \
    "$SCRIPT_DIR/system/temp-monitor.sh" \
    "$SCRIPT_DIR/system/temp-cancel.sh" \
    "$SCRIPT_DIR/system/limpiar" \
    "$SCRIPT_DIR/system/falkon-rapido" \
    "$SCRIPT_DIR/graph/nexo-graph" \
    "$SCRIPT_DIR/graph/nexo-memory" \
    "$SCRIPT_DIR/tools/nexo-tools" \
    "$SCRIPT_DIR/tools/nexo-diary" \
    "$SCRIPT_DIR/tools/nexo-evaluate" \
    "$SCRIPT_DIR/tools/nexo-wake" \
    "$SCRIPT_DIR/voice/say.sh" \
    "$SCRIPT_DIR/voice/voice.sh" \
    "$SCRIPT_DIR/agent/asistente.md" \
    "$SCRIPT_DIR/backup/migrar-miku.sh" \
    "$SCRIPT_DIR/config/cpu-performance.service" \
    "$SCRIPT_DIR/config/sudoers.temp-monitor" \
    "$SCRIPT_DIR/config/miku-crontab.txt"; do
    if [[ ! -f "$f" ]]; then
        err "Falta archivo: $f"
        MISSING_FILES=$((MISSING_FILES + 1))
    fi
done
if [[ $MISSING_FILES -gt 0 ]]; then
    err "Faltan $MISSING_FILES archivos. Asegurate de clonar el repo completo."
    exit 1
fi
ok "Todos los archivos fuente presentes"

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

# ── Detectar gestor de paquetes ──────────────────────────────────────────
if command -v apt &>/dev/null; then
    PKG_MANAGER="apt"
    INSTALL_CMD="apt install -y"
elif command -v dnf &>/dev/null; then
    PKG_MANAGER="dnf"
    INSTALL_CMD="dnf install -y"
elif command -v pacman &>/dev/null; then
    PKG_MANAGER="pacman"
    INSTALL_CMD="pacman -S --noconfirm"
elif command -v zypper &>/dev/null; then
    PKG_MANAGER="zypper"
    INSTALL_CMD="zypper install -y"
else
    PKG_MANAGER="unknown"
    INSTALL_CMD=""
fi

# ── Instalar dependencias del sistema ────────────────────────────────────
info "Instalando dependencias del sistema..."
if [[ "$PKG_MANAGER" == "apt" ]]; then
    echo "$SUDO_PASS" | sudo -S apt update -qq 2>/dev/null
    echo "$SUDO_PASS" | sudo -S $INSTALL_CMD espeak-ng mpg123 python3 python3-pip jq sqlite3 curl 2>/dev/null
    ok "Dependencias de sistema instaladas"
elif [[ -n "$INSTALL_CMD" ]]; then
    warn "Dependencias no instaladas automáticamente. Ejecutá:"
    warn "  sudo $INSTALL_CMD espeak-ng mpg123 python3 python3-pip jq sqlite3 curl"
else
    warn "Gestor de paquetes no detectado. Instalá manualmente: espeak-ng, python3, pip, jq, sqlite3, curl"
fi

# ── Instalar dependencias Python ─────────────────────────────────────────
info "Instalando dependencias Python..."
python3 -m pip install --quiet --user gtts edge-tts 2>/dev/null && \
    ok "Dependencias Python instaladas (gTTS, edge-tts)" || \
    warn "No se pudieron instalar gTTS/edge-tts — se usará espeak-ng local"

# ── Piper TTS (local, rápido, sin depender de internet) ─────────────────
info "Instalando Piper TTS..."
if pip install --quiet --user --break-system-packages piper-tts 2>/dev/null; then
    ok "Piper TTS instalado"
    
    # Descargar voces
    PIPER_VOICES_DIR="$HOME/.local/share/piper-voices"
    mkdir -p "$PIPER_VOICES_DIR"
    
    info "Descargando voces Piper (español + inglés)..."
    
    # Español
    if [ ! -f "$PIPER_VOICES_DIR/es_ES-davefx-medium.onnx" ]; then
        curl -sL "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/davefx/medium/es_ES-davefx-medium.onnx?download=true" \
            -o "$PIPER_VOICES_DIR/es_ES-davefx-medium.onnx" &
        curl -sL "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/davefx/medium/es_ES-davefx-medium.onnx.json?download=true" \
            -o "$PIPER_VOICES_DIR/es_ES-davefx-medium.onnx.json" &
    fi
    
    # Inglés
    if [ ! -f "$PIPER_VOICES_DIR/en_US-lessac-medium.onnx" ]; then
        curl -sL "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx?download=true" \
            -o "$PIPER_VOICES_DIR/en_US-lessac-medium.onnx" &
        curl -sL "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json?download=true" \
            -o "$PIPER_VOICES_DIR/en_US-lessac-medium.onnx.json" &
    fi
    
    wait
    ok "Voces Piper descargadas (español + inglés)"
else
    warn "No se pudo instalar Piper TTS — se usará gTTS cloud + espeak como respaldo"
fi

# ── Copiar scripts ─────────────────────────────────────────────────────
info "Copiando scripts..."

# system/
cp "$SCRIPT_DIR/system/check-identity.sh" "$BIN_DIR/"
cp "$SCRIPT_DIR/system/face-recognize.py" "$BIN_DIR/"
cp "$SCRIPT_DIR/system/temp-monitor.sh" "$BIN_DIR/"
# temp-cancel.sh: ya no necesita password (usa sudoers NOPASSWD)
cp "$SCRIPT_DIR/system/temp-cancel.sh" "$BIN_DIR/"
cp "$SCRIPT_DIR/system/nexo-harden" "$BIN_DIR/"
cp "$SCRIPT_DIR/system/limpiar" "$BIN_DIR/"
cp "$SCRIPT_DIR/system/falkon-rapido" "$BIN_DIR/"

# graph/
cp "$SCRIPT_DIR/graph/nexo-graph" "$BIN_DIR/"
cp "$SCRIPT_DIR/graph/nexo-memory" "$BIN_DIR/"

# tools/
cp "$SCRIPT_DIR/tools/nexo-tools" "$BIN_DIR/"
cp "$SCRIPT_DIR/tools/nexo-diary" "$BIN_DIR/"
cp "$SCRIPT_DIR/tools/nexo-evaluate" "$BIN_DIR/"
# nexo-wake: reemplazar HOME placeholder
sed "s|HOME_PLACEHOLDER|$HOME|g" "$SCRIPT_DIR/tools/nexo-wake" > "$BIN_DIR/nexo-wake"

# voice/
cp "$SCRIPT_DIR/voice/say.sh" "$OPENCODE_DIR/"
cp "$SCRIPT_DIR/voice/voice.sh" "$OPENCODE_DIR/"

# agent/ — reemplazar HOME en asistente.md (ya no necesita password — usa sudoers NOPASSWD)
sed -e "s|HOME_PLACEHOLDER|$HOME|g" \
    "$SCRIPT_DIR/agent/asistente.md" > "$AGENT_DIR/asistente.md"

# backup
cp "$SCRIPT_DIR/backup/migrar-miku.sh" "$HOME/"

# Dar permisos de ejecución (solo a archivos, no directorios)
find "$BIN_DIR" -maxdepth 1 -type f -exec chmod +x {} \;
chmod +x "$OPENCODE_DIR/say.sh" "$OPENCODE_DIR/voice.sh" 2>/dev/null || true
ok "Scripts copiados y ejecutables"

# ── Inicializar Knowledge Graph ────────────────────────────────────────
info "Inicializando Knowledge Graph..."
"$BIN_DIR/nexo-graph" init 2>/dev/null || true
ok "Knowledge Graph inicializado"

# ── Configurar servicios systemd ────────────────────────────────────────
info "Configurando servicios systemd..."

# CPU Performance
echo "$SUDO_PASS" | sudo -S cp "$SCRIPT_DIR/config/cpu-performance.service" /etc/systemd/system/ 2>/dev/null
echo "$SUDO_PASS" | sudo -S systemctl daemon-reload 2>/dev/null
echo "$SUDO_PASS" | sudo -S systemctl enable cpu-performance.service 2>/dev/null
echo "$SUDO_PASS" | sudo -S systemctl start cpu-performance.service 2>/dev/null && \
    ok "Servicio CPU Performance configurado" || \
    warn "No se pudo configurar CPU Performance (posiblemente no soportado)"

# Sudoers para Nexo (reemplazar USERNAME por el usuario real)
# Permite comandos sudo sin contraseña: rtcwake, poweroff, cpupower, services
sed "s/USERNAME/$USER/g" "$SCRIPT_DIR/config/sudoers.temp-monitor" | \
    echo "$SUDO_PASS" | sudo -S tee /etc/sudoers.d/temp-monitor >/dev/null 2>&1
echo "$SUDO_PASS" | sudo -S chmod 440 /etc/sudoers.d/temp-monitor 2>/dev/null && \
    ok "Sudoers para temp-monitor configurado" || \
    warn "No se pudo configurar sudoers para temp-monitor"

# Crontab (expandir $HOME antes de instalar)
if [[ -f "$SCRIPT_DIR/config/miku-crontab.txt" ]]; then
    sed "s|\$HOME|$HOME|g" "$SCRIPT_DIR/config/miku-crontab.txt" | crontab - 2>/dev/null && \
        ok "Crontab configurado" || \
        warn "No se pudo configurar crontab"
fi

# ── Verificar dependencias ──────────────────────────────────────────────
info "Verificando dependencias..."

DEPS_MISSING=""
for cmd in python3 jq sqlite3 espeak-ng; do
    if ! command -v "$cmd" &>/dev/null; then
        DEPS_MISSING="$DEPS_MISSING $cmd"
    fi
done

if [[ -n "$DEPS_MISSING" ]]; then
    warn "Faltan dependencias:$DEPS_MISSING"
else
    ok "Todas las dependencias básicas presentes"
fi

# ── Verificar Ollama (opcional) ─────────────────────────────────────────
if command -v ollama &>/dev/null; then
    ok "Ollama detectado"
else
    warn "Ollama no detectado — los embeddings semánticos y diary no funcionarán"
    warn "Instalá Ollama: curl -fsSL https://ollama.com/install.sh | sh"
    echo ""
    echo -n "❓ ¿Querés instalar Ollama ahora? (s/N): "
    read -r INSTALL_OLLAMA
    if [[ "$INSTALL_OLLAMA" =~ ^[sS]$ ]]; then
        info "Instalando Ollama..."
        curl -fsSL https://ollama.com/install.sh | sh 2>&1 || warn "Fallo la instalación de Ollama"
        if command -v ollama &>/dev/null; then
            ollama pull nomic-embed-text 2>/dev/null &
            ok "Ollama instalado. nomic-embed-text descargándose en background"
        fi
    fi
fi

# ── Ofrecer Security Hardening ──────────────────────────────────────────
echo ""
echo -n "🛡️  ¿Querés aplicar hardening de seguridad? (firewall, kernel, SSH) (s/N): "
read -r RUN_HARDEN
if [[ "$RUN_HARDEN" =~ ^[sS]$ ]]; then
    info "Aplicando security hardening..."
    echo "$SUDO_PASS" | sudo -S "$BIN_DIR/nexo-harden" --apply 2>/dev/null && \
        ok "Security hardening aplicado" || \
        warn "No se pudo aplicar hardening (ejecutá manual: sudo nexo-harden --apply)"
fi

# ── Verificar TTS ────────────────────────────────────────────────────────
info "Probando TTS..."
if timeout 5 espeak-ng "Hola" 2>/dev/null; then
    ok "TTS funciona (espeak-ng)"
else
    warn "TTS no funciona — revisá espeak-ng o PulseAudio"
fi

echo ""
echo "========================================"
echo "  ✅ Nexo Lab instalado"
echo "========================================"
echo ""
echo "   📍 Scripts:    $BIN_DIR/"
echo "   🧠 Memoria:    $MEMORY_DIR/"
echo "   🤖 Agente:     $AGENT_DIR/asistente.md"
echo "   🎤 Voz:        $OPENCODE_DIR/"
echo ""
echo "   Comandos disponibles:"
echo "     nexo-graph      — Knowledge Graph (3 ramas + embeddings)"
echo "     nexo-memory     — Memoria persistente + auto-aprendizaje"
echo "     nexo-tools      — Tool Registry"
echo "     nexo-diary      — Diary Summariser (Ollama)"
echo "     nexo-evaluate   — Evaluator (Ollama)"
echo "     nexo-wake       — Wake Word Detection"
echo "     limpiar         — Limpiador del sistema"
echo "     face-recognize  — Reconocimiento facial"
echo "     temp-monitor    — Monitor de temperatura"
echo "     nexo-harden     — 🛡️ Security Hardening"
echo ""
echo "   📖 README: $SCRIPT_DIR/README.md"
echo "   🌐 GitHub: https://github.com/Mikutabby/nexo-lab"
echo ""
