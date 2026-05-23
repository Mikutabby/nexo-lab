#!/bin/bash
# 🧠 Nexo Lab — Instalador automático
# Uso: ./install.sh [--help]
# Instala: ecosistema base (tools, graph, voice) + Nexo 2.0 (engine, UI, acciones)

set -o pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

info()  { echo -e "${BLUE}[INFO]${NC} $*"; }
ok()    { echo -e "${GREEN}[OK]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
err()   { echo -e "${RED}[ERR]${NC} $*"; }
header(){ echo -e "\n${CYAN}══ $* ══${NC}\n"; }

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BIN_DIR="$HOME/.local/bin"
OPENCODE_DIR="$HOME/.opencode"
AGENT_DIR="$OPENCODE_DIR/agents"
MEMORY_DIR="$HOME/.nexo-memory"
NEXO2_DIR="$HOME/nexo2"

echo ""
echo "========================================"
echo "  🧠 Nexo Lab — Instalación completa"
echo "  Ecosistema + Nexo 2.0"
echo "========================================"
echo ""

# ── Verificar SO ────────────────────────────────────────────────────────
if [[ "$(uname)" != "Linux" ]]; then
    err "Este instalador solo funciona en Linux"
    exit 1
fi

# ── Verificar source files ──────────────────────────────────────────────
header "Verificando archivos fuente"

MISSING_FILES=0
check_file() {
    if [[ ! -f "$1" ]]; then
        err "Falta archivo: $1"
        MISSING_FILES=$((MISSING_FILES + 1))
    fi
}

# Ecosistema base (system, tools, graph, voice, agent, backup)
for f in \
    "$SCRIPT_DIR/system/check-identity.sh" \
    "$SCRIPT_DIR/system/face-recognize.py" \
    "$SCRIPT_DIR/system/temp-monitor.sh" \
    "$SCRIPT_DIR/system/temp-cancel.sh" \
    "$SCRIPT_DIR/system/limpiar" \
    "$SCRIPT_DIR/system/falkon-rapido" \
    "$SCRIPT_DIR/system/nexo-harden" \
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
    check_file "$f"
done

# Nexo 2.0 (engine, acciones, UI)
for f in \
    "$SCRIPT_DIR/core/nexo_engine.py" \
    "$SCRIPT_DIR/core/model_router.py" \
    "$SCRIPT_DIR/core/prompt.txt" \
    "$SCRIPT_DIR/core/version.py" \
    "$SCRIPT_DIR/actions/web_search.py" \
    "$SCRIPT_DIR/actions/weather_report.py" \
    "$SCRIPT_DIR/actions/system_monitor.py" \
    "$SCRIPT_DIR/actions/spotify_control.py" \
    "$SCRIPT_DIR/actions/youtube_video.py" \
    "$SCRIPT_DIR/actions/file_controller.py" \
    "$SCRIPT_DIR/actions/reminder.py" \
    "$SCRIPT_DIR/actions/scheduler.py" \
    "$SCRIPT_DIR/actions/knowledge_base.py" \
    "$SCRIPT_DIR/actions/goals.py" \
    "$SCRIPT_DIR/actions/morning_brief.py" \
    "$SCRIPT_DIR/actions/user_profile.py" \
    "$SCRIPT_DIR/actions/smart_home.py" \
    "$SCRIPT_DIR/actions/browser_control.py" \
    "$SCRIPT_DIR/actions/ollama_provider.py" \
    "$SCRIPT_DIR/memory/memory_manager.py" \
    "$SCRIPT_DIR/ui/nexo_ui.py" \
    "$SCRIPT_DIR/ui/theme.py" \
    "$SCRIPT_DIR/server.py" \
    "$SCRIPT_DIR/main.py"; do
    check_file "$f"
done

if [[ $MISSING_FILES -gt 0 ]]; then
    err "Faltan $MISSING_FILES archivos. Asegurate de clonar el repo completo."
    err "Ejecutá: git clone https://github.com/Mikutabby/nexo-lab.git"
    exit 1
fi
ok "Todos los archivos fuente presentes ($MISSING_FILES ausentes)"

# ── Solicitar sudo password ─────────────────────────────────────────────
header "Acceso sudo"
echo -n "🔑 Ingresá tu contraseña sudo (se usará para servicios systemd): "
read -s SUDO_PASS
echo ""
if ! echo "$SUDO_PASS" | sudo -S -v 2>/dev/null; then
    err "Contraseña incorrecta"
    exit 1
fi
ok "Acceso sudo verificado"

# ── Crear directorios ──────────────────────────────────────────────────
header "Creando directorios"
mkdir -p "$BIN_DIR" "$AGENT_DIR" "$MEMORY_DIR" "$NEXO2_DIR"
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
header "Dependencias del sistema"
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
header "Dependencias Python"

# Dependencias base (ecosistema)
python3 -m pip install --quiet --user gtts edge-tts 2>/dev/null && \
    ok "gTTS, edge-tts instalados" || \
    warn "No se pudieron instalar gTTS/edge-tts — se usará espeak-ng local"

# Dependencias de Nexo 2.0
NEXO2_DEPS=("psutil" "requests" "duckduckgo-search" "pyperclip")
for dep in "${NEXO2_DEPS[@]}"; do
    python3 -m pip install --quiet --user "$dep" 2>/dev/null && \
        ok "$dep instalado" || \
        warn "No se pudo instalar $dep"
done

# PyQt6 para la UI gráfica
if python3 -c "from PyQt6.QtWidgets import QApplication" 2>/dev/null; then
    ok "PyQt6 ya instalado"
else
    warn "PyQt6 no detectado — la UI gráfica no estará disponible"
    echo -n "❓ ¿Querés instalar PyQt6? (s/N): "
    read -r INSTALL_PYQT
    if [[ "$INSTALL_PYQT" =~ ^[sS]$ ]]; then
        if [[ "$PKG_MANAGER" != "unknown" ]]; then
            echo "$SUDO_PASS" | sudo -S $INSTALL_CMD python3-pyqt6 python3-pyqt6.qtwebengine 2>/dev/null || \
            echo "$SUDO_PASS" | sudo -S $INSTALL_CMD pyqt6-dev-tools 2>/dev/null || \
            python3 -m pip install --quiet --user PyQt6 PyQt6-WebEngine 2>/dev/null && \
            ok "PyQt6 instalado" || \
            err "No se pudo instalar PyQt6 — instalá manualmente"
        else
            python3 -m pip install --quiet --user PyQt6 PyQt6-WebEngine 2>/dev/null && \
            ok "PyQt6 instalado" || \
            err "No se pudo instalar PyQt6"
        fi
    fi
fi

# Playwright para browser_control avanzado (opcional)
if python3 -c "from playwright.sync_api import sync_playwright" 2>/dev/null; then
    ok "Playwright ya instalado"
else
    warn "Playwright no detectado — browser_control avanzado no funcionará"
    echo -n "❓ ¿Querés instalar Playwright? (descarga ~300MB en navegadores) (s/N): "
    read -r INSTALL_PW
    if [[ "$INSTALL_PW" =~ ^[sS]$ ]]; then
        python3 -m pip install --quiet --user playwright 2>/dev/null && \
        python3 -m playwright install chromium 2>/dev/null && \
        ok "Playwright + Chromium instalados" || \
        warn "No se pudo instalar Playwright"
    fi
fi

# ── Piper TTS (local, rápido, sin depender de internet) ─────────────────
header "Piper TTS (local)"
if pip install --quiet --user --break-system-packages piper-tts 2>/dev/null; then
    ok "Piper TTS instalado"

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

# ── Copiar scripts del ecosistema ─────────────────────────────────────
header "Copiando scripts del ecosistema"

# system/
cp "$SCRIPT_DIR/system/check-identity.sh" "$BIN_DIR/"
cp "$SCRIPT_DIR/system/face-recognize.py" "$BIN_DIR/"
cp "$SCRIPT_DIR/system/temp-monitor.sh" "$BIN_DIR/"
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

# agent/ — reemplazar HOME en asistente.md
sed -e "s|HOME_PLACEHOLDER|$HOME|g" \
    "$SCRIPT_DIR/agent/asistente.md" > "$AGENT_DIR/asistente.md"

# backup
cp "$SCRIPT_DIR/backup/migrar-miku.sh" "$HOME/"

# Dar permisos de ejecución
find "$BIN_DIR" -maxdepth 1 -type f -exec chmod +x {} \;
chmod +x "$OPENCODE_DIR/say.sh" "$OPENCODE_DIR/voice.sh" 2>/dev/null || true
chmod +x "$HOME/migrar-miku.sh" 2>/dev/null || true

ok "Ecosistema base copiado"

# ── Instalar Nexo 2.0 ──────────────────────────────────────────────────
header "Instalando Nexo 2.0"

# Copiar archivos de nexo2 al directorio de destino
mkdir -p "$NEXO2_DIR/actions" "$NEXO2_DIR/core" "$NEXO2_DIR/memory" "$NEXO2_DIR/ui" "$NEXO2_DIR/config"

cp -r "$SCRIPT_DIR/actions/"* "$NEXO2_DIR/actions/"
cp -r "$SCRIPT_DIR/core/"* "$NEXO2_DIR/core/"
cp -r "$SCRIPT_DIR/memory/"* "$NEXO2_DIR/memory/"
cp -r "$SCRIPT_DIR/ui/"* "$NEXO2_DIR/ui/"
cp "$SCRIPT_DIR/server.py" "$NEXO2_DIR/"
cp "$SCRIPT_DIR/main.py" "$NEXO2_DIR/"
cp "$SCRIPT_DIR/.gitignore" "$NEXO2_DIR/" 2>/dev/null || true

# Crear launcher nexo2
cat > "$BIN_DIR/nexo2" << 'LAUNCHER'
#!/bin/bash
# 🧠 Nexo 2.0 — Launcher
NEXO_DIR="$HOME/nexo2"

case "${1:-cli}" in
    cli|shell)
        echo "🧠 Nexo 2.0 — Modo interactivo"
        cd "$NEXO_DIR" && python3 core/nexo_engine.py
        ;;
    gui|ui)
        echo "🖥️ Nexo 2.0 — Interfaz gráfica"
        cd "$NEXO_DIR" && python3 -c "
from core.nexo_engine import NexoEngine
from ui.nexo_ui import launch_ui
engine = NexoEngine()
launch_ui(engine=engine)
"
        ;;
    server)
        echo "🌐 Nexo 2.0 — Servidor HTTP"
        cd "$NEXO_DIR" && python3 core/nexo_engine.py --daemon --port "${2:-7072}"
        ;;
    command|-c)
        shift
        cd "$NEXO_DIR" && python3 core/nexo_engine.py -c "$*"
        ;;
    status)
        curl -s http://127.0.0.1:7072/status 2>/dev/null | python3 -m json.tool 2>/dev/null || echo "❌ Nexo 2.0 server no está corriendo"
        ;;
    help|--help|-h)
        echo "🧠 Nexo 2.0 — Asistente del Hogar"
        echo ""
        echo "Uso:"
        echo "  nexo2                  Modo CLI interactivo"
        echo "  nexo2 gui|ui           Interfaz gráfica PyQt6"
        echo "  nexo2 server [puerto]  Iniciar servidor HTTP"
        echo "  nexo2 -c <comando>     Ejecutar un comando"
        echo "  nexo2 status           Estado del servidor"
        echo "  nexo2 help             Esta ayuda"
        ;;
    *)
        echo "Uso: nexo2 {cli|gui|server|command|status|help}"
        ;;
esac
LAUNCHER
chmod +x "$BIN_DIR/nexo2"
ok "Nexo 2.0 instalado en $NEXO2_DIR"

# ── Inicializar Knowledge Graph ────────────────────────────────────────
header "Inicializando Knowledge Graph"
"$BIN_DIR/nexo-graph" init 2>/dev/null || true
ok "Knowledge Graph inicializado"

# ── Configurar servicios systemd ────────────────────────────────────────
header "Servicios systemd"

# CPU Performance
echo "$SUDO_PASS" | sudo -S cp "$SCRIPT_DIR/config/cpu-performance.service" /etc/systemd/system/ 2>/dev/null
echo "$SUDO_PASS" | sudo -S systemctl daemon-reload 2>/dev/null
echo "$SUDO_PASS" | sudo -S systemctl enable cpu-performance.service 2>/dev/null
echo "$SUDO_PASS" | sudo -S systemctl start cpu-performance.service 2>/dev/null && \
    ok "Servicio CPU Performance configurado" || \
    warn "No se pudo configurar CPU Performance (posiblemente no soportado)"

# Sudoers para Nexo (reemplazar USERNAME por el usuario real)
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
header "Verificación final"

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

# Verificar Nexo 2.0
if command -v nexo2 &>/dev/null; then
    ok "nexo2 launcher listo"
fi

# ── Verificar Ollama (opcional) ─────────────────────────────────────────
if command -v ollama &>/dev/null; then
    ok "Ollama detectado"
else
    warn "Ollama no detectado — los embeddings semánticos y algunas funciones no funcionarán"
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

# ── Security Hardening (opcional) ──────────────────────────────────────
echo ""
echo -n "🛡️  ¿Querés aplicar hardening de seguridad? (firewall, kernel, SSH) (s/N): "
read -r RUN_HARDEN
if [[ "$RUN_HARDEN" =~ ^[sS]$ ]]; then
    info "Aplicando security hardening..."
    echo "$SUDO_PASS" | sudo -S "$BIN_DIR/nexo-harden" --apply 2>/dev/null && \
        ok "Security hardening aplicado" || \
        warn "No se pudo aplicar hardening (ejecutá manual: sudo nexo-harden --apply)"
fi

# ── Probar TTS ──────────────────────────────────────────────────────────
info "Probando TTS..."
if timeout 5 espeak-ng "Hola, soy Nexo" 2>/dev/null; then
    ok "TTS funciona (espeak-ng)"
else
    warn "TTS no funciona — revisá espeak-ng o PulseAudio"
fi

# ── Resumen final ───────────────────────────────────────────────────────
echo ""
echo "========================================"
echo "  ✅ Nexo Lab instalado correctamente"
echo "========================================"
echo ""
echo "  📍 Scripts:        $BIN_DIR/"
echo "  🧠 Memoria:        $MEMORY_DIR/"
echo "  🤖 Agente:         $AGENT_DIR/asistente.md"
echo "  🎤 Voz:            $OPENCODE_DIR/"
echo "  🧠 Nexo 2.0:       $NEXO2_DIR/"
echo ""
echo "  📌 Ecosistema base:"
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
echo "  📌 Nexo 2.0 (asistente conversacional):"
echo "     nexo2           — Modo CLI interactivo"
echo "     nexo2 gui       — Interfaz gráfica (PyQt6)"
echo "     nexo2 server    — Servidor HTTP (puerto 7072)"
echo "     nexo2 -c cmd    — Ejecutar comando directo"
echo ""
echo "  💡 Comandos rápidos de Nexo 2.0:"
echo "     hora | clima [ciudad] | buscá [consulta]"
echo "     abrí [url] | poné [video] | objetivos"
echo "     tareas programadas | luces | mi perfil"
echo ""
echo "  📖 README: $SCRIPT_DIR/README.md"
echo "  🌐 GitHub: https://github.com/Mikutabby/nexo-lab"
echo ""
