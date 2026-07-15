#!/bin/bash
# 🧠 Nexo Lab — Instalador automático
# Uso: ./install.sh                    → Instala todo
#       ./install.sh --list            → Lista componentes disponibles
#       ./install.sh -c voz            → Instala solo el componente "voz"
#       ./install.sh -c graph          → Instala solo el componente "graph"
#       ./install.sh -c tools          → Instala solo el componente "tools"
#       ./install.sh -c sistema        → Instala solo el componente "sistema"
#       ./install.sh -c agente         → Instala solo el agente
#       ./install.sh -c config         → Instala solo la configuración
#       ./install.sh -c dependencias   → Instala solo dependencias
#       ./install.sh -c ollama         → Instala solo Ollama
#       ./install.sh -c memory         → Instala memoria avanzada
#       ./install.sh -c hermes         → Instala integración Hermes
#       ./install.sh -c skills         → Instala sistema de skills
#       ./install.sh -c brain          → Instala brain daemon
#       ./install.sh -c audio          → Instala diagnósticos de audio
#
# Cada componente es independiente y se puede instalar por separado.
# Ideal para instalación conversacional guiada por Nexo.

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
header(){ echo -e "\n${CYAN}━━━ $* ━━━${NC}\n"; }

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BIN_DIR="$HOME/.local/bin"
OPENCODE_DIR="$HOME/.opencode"
AGENT_DIR="$OPENCODE_DIR/agents"
MEMORY_DIR="$HOME/.nexo-memory"
# Requiere sudo sin contraseña — configurá: $USER ALL=(ALL) NOPASSWD: ALL

# ── Mostrar ayuda ──────────────────────────────────────────────────────────
show_help() {
    echo ""
    echo "🧠 Nexo Lab Installer — Instalación por componentes"
    echo ""
    echo "USO:"
    echo "  ./install.sh                   Instala TODO el ecosistema"
    echo "  ./install.sh -c <componente>   Instala solo un componente"
    echo "  ./install.sh --list            Lista componentes disponibles"
    echo "  ./install.sh --help            Muestra esta ayuda"
    echo ""
    echo "COMPONENTES:"
    echo "  dependencias   Dependencias del sistema (espeak-ng, python3, sqlite3, jq, etc)"
    echo "  voz            TTS (say.sh) + STT (voice.sh) + Wake Word"
    echo "  graph          Knowledge Graph (nexo-graph) + Memoria (nexo-memory)"
    echo "  tools          Tool Registry + Diary + Evaluator"
    echo "  sistema        Scripts del sistema (check-identity, temp-monitor, limpiar, etc)"
    echo "  agente         Archivo del agente (asistente.md) para OpenCode"
    echo "  config         Servicios systemd + sudoers + crontab"
    echo "  opencode       Instalación de OpenCode (AI coding agent)"
    echo "  ollama         Instalación de Ollama + modelo nomic-embed-text"
    echo "  memory         Memoria avanzada (organize, semantic-enhance, skill-creator)"
    echo "  hermes         Integración Hermes Agent (wrapper + OpenRouter)"
    echo "  skills         Sistema de skills/plugins"
    echo "  brain          Brain daemon + IA"
    echo "  audio          Diagnósticos de audio"
    echo ""
    echo "EJEMPLOS:"
    echo "  ./install.sh -c dependencias  # Solo dependencias"
    echo "  ./install.sh -c voz           # Solo TTS/STT"
    echo "  ./install.sh -c graph -c tools  # Múltiples componentes"
    echo ""
}

# ── Listar componentes ─────────────────────────────────────────────────────
list_components() {
    header "COMPONENTES DISPONIBLES"
    echo -e "  ${GREEN}dependencias${NC}  Dependencias base del sistema"
    echo -e "  ${GREEN}voz${NC}           TTS + STT + Wake Word"
    echo -e "  ${GREEN}graph${NC}         Knowledge Graph + Memoria persistente"
    echo -e "  ${GREEN}tools${NC}         Tool Registry + Diary + Evaluator"
    echo -e "  ${GREEN}sistema${NC}       Scripts del sistema (face, temp, limpiar, etc)"
    echo -e "  ${GREEN}agente${NC}        Archivo asistente.md para OpenCode"
    echo -e "  ${GREEN}config${NC}        Systemd + sudoers + crontab"
    echo -e "  ${GREEN}opencode${NC}      OpenCode (AI coding agent)"
    echo -e "  ${GREEN}ollama${NC}        Ollama + modelo nomic-embed-text"
    echo -e "  ${GREEN}memory${NC}        Memoria avanzada (organize, semantic, skill-creator)"
    echo -e "  ${GREEN}hermes${NC}        Hermes Agent wrapper + integración"
    echo -e "  ${GREEN}skills${NC}        Sistema de skills/plugins"
    echo -e "  ${GREEN}brain${NC}         Brain daemon + IA"
    echo -e "  ${GREEN}audio${NC}         Diagnósticos de audio"
    echo -e "  ${GREEN}todo${NC}          Instalar todo (por defecto)"
    echo ""
}

# ── Verificar sudo sin contraseña ──────────────────────────────────────────
HAS_SUDO=0
check_sudo() {
    if sudo -n true 2>/dev/null; then
        HAS_SUDO=1
        ok "Acceso sudo verificado"
    else
        HAS_SUDO=0
        warn "Sin sudo sin contraseña — se saltarán componentes que lo necesiten"
        warn "Para configurarlo: sudo bash -c 'echo \"miku ALL=(ALL) NOPASSWD: ALL\" > /etc/sudoers.d/miku-nopasswd && chmod 440 /etc/sudoers.d/miku-nopasswd'"
    fi
}

# Wrapper para ejecutar comandos sudo
run_sudo() {
    sudo "$@"
}

# ── Verificar archivos fuente ──────────────────────────────────────────────
verify_files() {
    local missing=0
    for f in "$@"; do
        if [[ ! -f "$f" ]]; then
            err "Falta archivo: $f"
            missing=$((missing + 1))
        fi
    done
    if [[ $missing -gt 0 ]]; then
        err "Faltan $missing archivos. Asegurate de clonar el repo completo."
        exit 1
    fi
    ok "Archivos fuente verificados"
}

# ── Crear directorios ──────────────────────────────────────────────────────
create_dirs() {
    mkdir -p "$BIN_DIR" "$AGENT_DIR" "$MEMORY_DIR"
    ok "Directorios creados"
}

# ── Detectar gestor de paquetes ────────────────────────────────────────────
detect_pkg_manager() {
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
    info "Gestor de paquetes detectado: ${PKG_MANAGER:-ninguno}"
}

# ═══════════════════════════════════════════════════════════════════════════
# COMPONENTES DE INSTALACIÓN
# ═══════════════════════════════════════════════════════════════════════════

# ── 1. Dependencias del sistema ────────────────────────────────────────────
install_deps() {
    header "DEPENDENCIAS DEL SISTEMA"
    check_sudo
    detect_pkg_manager

    if [[ $HAS_SUDO -eq 0 ]]; then
        warn "Saltando instalación de paquetes del sistema (necesita sudo)"
        warn "Instalá manualmente: espeak-ng, python3, jq, sqlite3, curl"
    elif [[ "$PKG_MANAGER" == "apt" ]]; then
        run_sudo apt update -qq 2>/dev/null
        run_sudo "$INSTALL_CMD" espeak-ng mpg123 python3 python3-pip jq sqlite3 curl 2>/dev/null
        ok "Dependencias de sistema instaladas (apt)"
    elif [[ -n "$INSTALL_CMD" ]]; then
        warn "Instalando con $PKG_MANAGER... (puede pedir confirmación)"
        run_sudo "$INSTALL_CMD" espeak-ng mpg123 python3 python3-pip jq sqlite3 curl 2>/dev/null
    else
        warn "Gestor de paquetes no detectado. Instalá manualmente:"
        warn "  espeak-ng, python3, pip, jq, sqlite3, curl, mpg123"
    fi

    # Dependencias Python
    info "Instalando dependencias Python..."
    python3 -m pip install --quiet --user gtts edge-tts 2>/dev/null && \
        ok "Dependencias Python instaladas (gTTS, edge-tts)" || \
        warn "No se pudieron instalar gTTS/edge-tts — se usará espeak-ng local"

    # Piper TTS
    info "Instalando Piper TTS..."
    if pip install --quiet --user --break-system-packages piper-tts 2>/dev/null; then
        ok "Piper TTS instalado"
        local PIPER_DIR="$HOME/.local/share/piper-voices"
        mkdir -p "$PIPER_DIR"
        info "Descargando voces Piper..."
        [[ ! -f "$PIPER_DIR/es_ES-davefx-medium.onnx" ]] && \
            curl -sL "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/davefx/medium/es_ES-davefx-medium.onnx?download=true" -o "$PIPER_DIR/es_ES-davefx-medium.onnx" &
        [[ ! -f "$PIPER_DIR/es_ES-davefx-medium.onnx.json" ]] && \
            curl -sL "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/davefx/medium/es_ES-davefx-medium.onnx.json?download=true" -o "$PIPER_DIR/es_ES-davefx-medium.onnx.json" &
        [[ ! -f "$PIPER_DIR/en_US-lessac-medium.onnx" ]] && \
            curl -sL "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx?download=true" -o "$PIPER_DIR/en_US-lessac-medium.onnx" &
        [[ ! -f "$PIPER_DIR/en_US-lessac-medium.onnx.json" ]] && \
            curl -sL "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json?download=true" -o "$PIPER_DIR/en_US-lessac-medium.onnx.json" &
        wait
        ok "Voces Piper descargadas"
    else
        warn "No se pudo instalar Piper TTS — se usará gTTS cloud + espeak"
    fi

    ok "Componente 'dependencias' instalado"
}

# ── 2. Voz (TTS + STT) ─────────────────────────────────────────────────────
install_voice() {
    header "VOZ (TTS + STT)"
    create_dirs
    verify_files \
        "$SCRIPT_DIR/voice/say.sh" \
        "$SCRIPT_DIR/voice/voice.sh"

    cp "$SCRIPT_DIR/voice/say.sh" "$OPENCODE_DIR/"
    cp "$SCRIPT_DIR/voice/voice.sh" "$OPENCODE_DIR/"
    chmod +x "$OPENCODE_DIR/say.sh" "$OPENCODE_DIR/voice.sh"

    # nexo-wake: wake word detector
    if [[ -f "$SCRIPT_DIR/voice/nexo-wake" ]]; then
        cp "$SCRIPT_DIR/voice/nexo-wake" "$BIN_DIR/"
        chmod +x "$BIN_DIR/nexo-wake"
        ok "Wake word detector instalado"
    fi

    # Verificar TTS
    if command -v espeak-ng &>/dev/null; then
        ok "espeak-ng disponible para TTS"
    else
        warn "espeak-ng no instalado — el TTS por defecto no funcionará"
    fi

    ok "Componente 'voz' instalado en $OPENCODE_DIR/"
}

# ── 3. Knowledge Graph + Memoria ──────────────────────────────────────────
install_graph() {
    header "KNOWLEDGE GRAPH + MEMORIA"
    create_dirs
    verify_files \
        "$SCRIPT_DIR/graph/nexo-graph" \
        "$SCRIPT_DIR/graph/nexo-memory"

    cp "$SCRIPT_DIR/graph/nexo-graph" "$BIN_DIR/"
    cp "$SCRIPT_DIR/graph/nexo-memory" "$BIN_DIR/"
    chmod +x "$BIN_DIR/nexo-graph" "$BIN_DIR/nexo-memory"

    # Inicializar graph
    "$BIN_DIR/nexo-graph" init 2>/dev/null || true
    ok "Knowledge Graph inicializado"

    ok "Componente 'graph' instalado"
}

# ── 4. Herramientas (tools) ────────────────────────────────────────────────
install_tools() {
    header "HERRAMIENTAS (tools)"
    create_dirs
    verify_files \
        "$SCRIPT_DIR/tools/nexo-tools" \
        "$SCRIPT_DIR/tools/nexo-diary" \
        "$SCRIPT_DIR/tools/nexo-evaluate" \
        "$SCRIPT_DIR/tools/nexo-wake"

    cp "$SCRIPT_DIR/tools/nexo-tools" "$BIN_DIR/"
    cp "$SCRIPT_DIR/tools/nexo-diary" "$BIN_DIR/"
    cp "$SCRIPT_DIR/tools/nexo-evaluate" "$BIN_DIR/"

    # nexo-wake: reemplazar HOME placeholder
    sed "s|HOME_PLACEHOLDER|$HOME|g" "$SCRIPT_DIR/tools/nexo-wake" > "$BIN_DIR/nexo-wake"

    chmod +x "$BIN_DIR/nexo-tools" "$BIN_DIR/nexo-diary" \
            "$BIN_DIR/nexo-evaluate" "$BIN_DIR/nexo-wake"

    ok "Componente 'tools' instalado"
}

# ── 5. Sistema (scripts del sistema) ──────────────────────────────────────
install_system() {
    header "SCRIPTS DEL SISTEMA"
    create_dirs
    verify_files \
        "$SCRIPT_DIR/system/check-identity.sh" \
        "$SCRIPT_DIR/system/face-recognize.py" \
        "$SCRIPT_DIR/system/temp-monitor.sh" \
        "$SCRIPT_DIR/system/temp-cancel.sh" \
        "$SCRIPT_DIR/system/limpiar" \
        "$SCRIPT_DIR/system/falkon-rapido" \
        "$SCRIPT_DIR/system/nexo-harden"

    cp "$SCRIPT_DIR/system/check-identity.sh" "$BIN_DIR/"
    cp "$SCRIPT_DIR/system/face-recognize.py" "$BIN_DIR/"
    cp "$SCRIPT_DIR/system/temp-monitor.sh" "$BIN_DIR/"
    cp "$SCRIPT_DIR/system/temp-cancel.sh" "$BIN_DIR/"
    cp "$SCRIPT_DIR/system/nexo-harden" "$BIN_DIR/"
    cp "$SCRIPT_DIR/system/limpiar" "$BIN_DIR/"
    cp "$SCRIPT_DIR/system/falkon-rapido" "$BIN_DIR/"
    chmod +x "$BIN_DIR"/*

    ok "Componente 'sistema' instalado"
}

# ── 6. Agente (asistente.md) ──────────────────────────────────────────────
install_agent() {
    header "AGENTE (asistente.md)"
    create_dirs
    verify_files "$SCRIPT_DIR/agent/asistente.md"

    # Reemplazar HOME_PLACEHOLDER
    sed -e "s|HOME_PLACEHOLDER|$HOME|g" \
        "$SCRIPT_DIR/agent/asistente.md" > "$AGENT_DIR/asistente.md"

    ok "Agente instalado en $AGENT_DIR/asistente.md"
}

# ── 7. Configuración (systemd + sudoers + crontab) ────────────────────────
install_config() {
    header "CONFIGURACIÓN DEL SISTEMA"
    check_sudo
    verify_files \
        "$SCRIPT_DIR/config/cpu-performance.service" \
        "$SCRIPT_DIR/config/sudoers.temp-monitor" \
        "$SCRIPT_DIR/config/miku-crontab.txt"

    if [[ $HAS_SUDO -eq 0 ]]; then
        warn "Sin sudo — no se pueden configurar servicios systemd, sudoers ni crontab"
        warn "Ejecutá después: bash setup-sudo.sh && ./install.sh -c config"
        return 0
    fi

    # CPU Performance
    run_sudo cp "$SCRIPT_DIR/config/cpu-performance.service" /etc/systemd/system/ 2>/dev/null
    run_sudo systemctl daemon-reload 2>/dev/null
    run_sudo systemctl enable cpu-performance.service 2>/dev/null
    run_sudo systemctl start cpu-performance.service 2>/dev/null && \
        ok "Servicio CPU Performance configurado" || \
        warn "No se pudo configurar CPU Performance"

    # Sudoers
    sed "s/USERNAME/$USER/g" "$SCRIPT_DIR/config/sudoers.temp-monitor" | \
        run_sudo tee /etc/sudoers.d/temp-monitor >/dev/null 2>&1
    run_sudo chmod 440 /etc/sudoers.d/temp-monitor 2>/dev/null && \
        ok "Sudoers configurado" || \
        warn "No se pudo configurar sudoers"

    # Crontab
    if [[ -f "$SCRIPT_DIR/config/miku-crontab.txt" ]]; then
        sed "s|\$HOME|$HOME|g" "$SCRIPT_DIR/config/miku-crontab.txt" | crontab - 2>/dev/null && \
            ok "Crontab configurado" || \
            warn "No se pudo configurar crontab"
    fi

    ok "Componente 'config' instalado"
}

# ── 8. Ollama (opcional) ──────────────────────────────────────────────────
install_ollama() {
    header "OLLAMA (IA local)"

    if command -v ollama &>/dev/null; then
        ok "Ollama ya está instalado"
    else
        info "Instalando Ollama..."
        if command -v curl &>/dev/null; then
            curl -fsSL https://ollama.com/install.sh | sh 2>&1 || {
                warn "Fallo la instalación de Ollama"
                return 1
            }
        else
            err "curl no está instalado. Instalá curl primero."
            return 1
        fi
    fi

    if command -v ollama &>/dev/null; then
        info "Descargando modelo nomic-embed-text..."
        ollama pull nomic-embed-text 2>&1 &
        ok "Ollama instalado. nomic-embed-text descargándose en background"
    fi
}

# ── 9. OpenCode ────────────────────────────────────────────────────────────
install_opencode() {
    header "OPENCODE (AI Coding Agent)"

    local OC_INSTALLED=0

    # Verificar si ya está instalado
    if command -v opencode &>/dev/null || [[ -f "$HOME/.opencode/bin/opencode" ]]; then
        OC_INSTALLED=1
    fi

    if [[ $OC_INSTALLED -eq 0 ]]; then
        # No está instalado → instalar
        info "OpenCode no encontrado. Instalando automáticamente..."

        if ! command -v curl &>/dev/null; then
            err "curl no está instalado. Instalá curl primero."
            return 1
        fi

        # Intentar instalación oficial
        info "Descargando desde opencode.ai..."
        if curl -fsSL https://opencode.ai/install -o /tmp/opencode-install.sh 2>/dev/null && \
           bash /tmp/opencode-install.sh --no-modify-path 2>&1; then
            ok "OpenCode instalado correctamente"
            rm -f /tmp/opencode-install.sh
        else
            warn "Instalador oficial falló. Intentando descarga directa..."
            install_opencode_manual
        fi

        # Verificar que se instaló
        if [[ -f "$HOME/.opencode/bin/opencode" ]]; then
            export PATH="$HOME/.opencode/bin:$PATH"
            ok "OpenCode disponible en ~/.opencode/bin/"
        else
            err "No se pudo instalar OpenCode"
            return 1
        fi
    else
        ok "OpenCode ya está instalado"
    fi

    # Configurar para Nexo (siempre, tanto si se instaló como si ya existía)
    configure_opencode
}

# Instalación manual de OpenCode
install_opencode_manual() {
    info "Descarga manual de OpenCode..."

    local ARCH OS
    ARCH=$(uname -m)
    OS=$(uname -s | tr '[:upper:]' '[:lower:]')

    case "$ARCH" in
        x86_64)  ARCH="amd64" ;;
        aarch64) ARCH="arm64" ;;
        armv7l)  ARCH="armv7" ;;
    esac

    local URL="https://github.com/opencode-ai/opencode/releases/latest/download/opencode-${OS}-${ARCH}"
    mkdir -p "$HOME/.opencode/bin"

    if curl -fsSL "$URL" -o "$HOME/.opencode/bin/opencode" 2>/dev/null; then
        chmod +x "$HOME/.opencode/bin/opencode"
        ok "Binario descargado manualmente"
    else
        err "No se pudo descargar opencode"
        return 1
    fi
}

# Configurar OpenCode para Nexo
configure_opencode() {
    local OC_DIR="$HOME/.opencode"
    local AGENTS_DIR="$OC_DIR/agents"
    local CONFIG_FILE="$OC_DIR/opencode.json"
    local STYLE_FILE="$OC_DIR/agents/style-local.md"

    mkdir -p "$AGENTS_DIR"

    info "Configurando OpenCode para Nexo..."

    # 1. Agente asistente.md
    if [[ -f "$SCRIPT_DIR/agent/asistente.md" ]]; then
        cp "$SCRIPT_DIR/agent/asistente.md" "$AGENTS_DIR/"
        ok "Agente: asistente.md"
    fi

    # 2. Configuración opencode.json
    if [[ -f "$SCRIPT_DIR/config/opencode.jsonc" ]]; then
        cp "$SCRIPT_DIR/config/opencode.jsonc" "$CONFIG_FILE"
        ok "Config: opencode.json"
    fi

    # 3. style-local.md (necesario para el agente)
    if [[ ! -f "$STYLE_FILE" ]]; then
        cat > "$STYLE_FILE" << 'STYLE_EOF'
# Style Local — Nexo

## Identidad
- Nombre: Nexo
- Creador: mikuyasha (miku)
- Rol: Asistente autónomo del hogar Linux

## Comportamiento
- Hablar siempre antes de ejecutar cualquier acción
- Respuestas cortas y conversacionales (1-3 oraciones)
- Modo relajado por defecto, serio para código/debug
- Aprender y adaptarse de cada interacción
- Nunca omitir el paso de hablar primero

## Permisos
- bash: allow
- read: allow
- edit: allow
- write: allow
- glob: allow
- grep: allow
STYLE_EOF
        ok "Config: style-local.md"
    fi

    # 4. PATH en bashrc
    if ! grep -q '.opencode/bin' "$HOME/.bashrc" 2>/dev/null; then
        echo '' >> "$HOME/.bashrc"
        echo '# OpenCode' >> "$HOME/.bashrc"
        # shellcheck disable=SC2016
        echo 'export PATH="$HOME/.opencode/bin:$PATH"' >> "$HOME/.bashrc"
        ok "PATH: agregado a ~/.bashrc"
    fi

    ok "OpenCode configurado para Nexo"
    info "Ejecutá 'source ~/.bashrc' para usar opencode"
}

# ── 10. Memoria Avanzada ─────────────────────────────────────────────────
install_memory() {
    header "MEMORIA AVANZADA"
    create_dirs
    verify_files \
        "$SCRIPT_DIR/memory/nexo-memory-organize" \
        "$SCRIPT_DIR/memory/nexo-semantic-enhance"

    cp "$SCRIPT_DIR/memory/"* "$BIN_DIR/"
    chmod +x "$BIN_DIR/nexo-memory-"* "$BIN_DIR/nexo-skill-creator" 2>/dev/null

    # Generar embeddings iniciales
    info "Generando embeddings iniciales..."
    "$BIN_DIR/nexo-semantic-enhance" 2>/dev/null && \
        ok "Embeddings generados" || \
        warn "No se pudieron generar embeddings — ejecutá nexo-semantic-enhance después"

    ok "Componente 'memory' instalado"
}

# ── 11. Hermes Integration ────────────────────────────────────────────────
install_hermes() {
    header "HERMES AGENT INTEGRATION"
    create_dirs

    # Wrapper
    if [[ -f "$SCRIPT_DIR/hermes/hermes" ]]; then
        cp "$SCRIPT_DIR/hermes/hermes" "$BIN_DIR/"
        chmod +x "$BIN_DIR/hermes"
        ok "Hermes wrapper instalado"
    fi

    # Config
    mkdir -p "$HOME/.hermes"
    if [[ -f "$SCRIPT_DIR/hermes/hermes" ]] && [[ ! -f "$HOME/.hermes/config.yaml" ]]; then
        warn "Configurá Hermes manualmente: hermes setup"
    fi

    ok "Componente 'hermes' instalado"
}

# ── 12. Skills System ─────────────────────────────────────────────────────
install_skills() {
    header "SKILLS SYSTEM"
    create_dirs
    verify_files \
        "$SCRIPT_DIR/skills/nexo-skill"

    cp "$SCRIPT_DIR/skills/nexo-skill" "$BIN_DIR/"
    cp "$SCRIPT_DIR/skills/nexo-skill-creator" "$BIN_DIR/" 2>/dev/null
    chmod +x "$BIN_DIR/nexo-skill" "$BIN_DIR/nexo-skill-creator" 2>/dev/null

    # Crear directorio de skills
    mkdir -p "$HOME/.nexo-skills"

    ok "Componente 'skills' instalado"
}

# ── 13. Brain (Daemon + IA) ───────────────────────────────────────────────
install_brain() {
    header "BRAIN (DAEMON + IA)"
    create_dirs
    verify_files \
        "$SCRIPT_DIR/brain/nexo-brain.py" \
        "$SCRIPT_DIR/brain/nexo-daemon.sh"

    cp "$SCRIPT_DIR/brain/nexo-brain.py" "$BIN_DIR/"
    cp "$SCRIPT_DIR/brain/nexo-daemon.sh" "$BIN_DIR/"
    chmod +x "$BIN_DIR/nexo-brain.py" "$BIN_DIR/nexo-daemon.sh"

    ok "Componente 'brain' instalado"
}

# ── 14. Audio Diagnostics ─────────────────────────────────────────────────
install_audio() {
    header "AUDIO DIAGNOSTICS"
    create_dirs

    if [[ -f "$SCRIPT_DIR/system/nexo-audio-diagnostico.sh" ]]; then
        cp "$SCRIPT_DIR/system/nexo-audio-diagnostico.sh" "$BIN_DIR/"
        chmod +x "$BIN_DIR/nexo-audio-diagnostico.sh"
        ok "Audio diagnostics instalado"
    fi

    ok "Componente 'audio' instalado"
}

# ── Instalar TODO ──────────────────────────────────────────────────────────
install_all() {
    header "INSTALACIÓN COMPLETA"
    echo "Se instalará el ecosistema Nexo completo."
    echo ""

    install_opencode
    install_deps
    install_voice
    install_graph
    install_tools
    install_system
    install_agent
    install_config
    install_memory
    install_hermes
    install_skills
    install_brain
    install_audio

    # Backup
    verify_files "$SCRIPT_DIR/backup/migrar-miku.sh" 2>/dev/null
    cp "$SCRIPT_DIR/backup/migrar-miku.sh" "$HOME/" 2>/dev/null
    chmod +x "$HOME/migrar-miku.sh" 2>/dev/null

    # Verificar dependencias
    header "VERIFICACIÓN FINAL"
    local deps_missing=""
    for cmd in python3 jq sqlite3 espeak-ng; do
        command -v "$cmd" &>/dev/null || deps_missing="$deps_missing $cmd"
    done
    [[ -n "$deps_missing" ]] && warn "Faltan:$deps_missing" || ok "Todas las dependencias presentes"

    # TTS test
    if timeout 3 espeak-ng "Hola" 2>/dev/null; then
        ok "TTS funciona"
    else
        warn "TTS no funciona — revisá PulseAudio"
    fi

    # Preguntar por Ollama
    echo ""
    echo -n "❓ ¿Querés instalar Ollama para funciones avanzadas? (s/N): "
    read -r INSTALL_OLLAMA_ANS
    [[ "$INSTALL_OLLAMA_ANS" =~ ^[sS]$ ]] && install_ollama

    header "✅ ECOSISTEMA NEXO INSTALADO"
    echo "   📍 Scripts:    $BIN_DIR/"
    echo "   🧠 Memoria:    $MEMORY_DIR/"
    echo "   🤖 Agente:     $AGENT_DIR/asistente.md"
    echo "   🎤 Voz:        $OPENCODE_DIR/"
    echo ""
    echo "   Comandos: nexo-graph, nexo-memory, nexo-tools, nexo-diary,"
    echo "             nexo-evaluate, nexo-wake, nexo-skill, nexo-skill-creator,"
    echo "             nexo-memory-organize, nexo-semantic-enhance,"
    echo "             nexo-brain, nexo-daemon, hermes,"
    echo "             limpiar, face-recognize, temp-monitor, nexo-harden"
    echo ""
    echo "   🔄 Backup:     ~/migrar-miku.sh"
    echo "   🌐 GitHub:     https://github.com/Mikutabby/nexo-lab"
    echo ""
}

# ═══════════════════════════════════════════════════════════════════════════
# PARSING DE ARGUMENTOS
# ═══════════════════════════════════════════════════════════════════════════

# Si no hay argumentos, instalar todo
if [[ $# -eq 0 ]]; then
    install_all
    exit 0
fi

COMPONENTS=()
while [[ $# -gt 0 ]]; do
    case "$1" in
        --help|-h)
            show_help
            exit 0
            ;;
        --list|-l)
            list_components
            exit 0
            ;;
        --component|-c)
            shift
            if [[ -z "$1" || "$1" == -* ]]; then
                err "Falta el nombre del componente después de $1"
                exit 1
            fi
            COMPONENTS+=("$1")
            shift
            ;;
        *)
            err "Opción desconocida: $1"
            echo "Usá --help para ver las opciones disponibles"
            exit 1
            ;;
    esac
done

# Si no se especificaron componentes después del parsing
if [[ ${#COMPONENTS[@]} -eq 0 ]]; then
    err "No se especificaron componentes. Usá -c <componente>"
    echo "Componentes: dependencias, voz, graph, tools, sistema, agente, config, opencode, ollama, memory, hermes, skills, brain, audio"
    exit 1
fi

# Instalar cada componente
INSTALLED=0
for comp in "${COMPONENTS[@]}"; do
    case "$comp" in
        todo|all|completo)
            install_all
            INSTALLED=$((INSTALLED + 1))
            ;;
        dependencias|deps|dep|dependencia)
            install_deps
            INSTALLED=$((INSTALLED + 1))
            ;;
        voice|voz)
            install_voice
            INSTALLED=$((INSTALLED + 1))
            ;;
        graph|grafo|memoria|mem)
            install_graph
            INSTALLED=$((INSTALLED + 1))
            ;;
        tools|herramientas|tool)
            install_tools
            INSTALLED=$((INSTALLED + 1))
            ;;
        sistema|system)
            install_system
            INSTALLED=$((INSTALLED + 1))
            ;;
        agente|agent)
            install_agent
            INSTALLED=$((INSTALLED + 1))
            ;;
        config|configuración|configuracion)
            install_config
            INSTALLED=$((INSTALLED + 1))
            ;;
        opencode|oc)
            install_opencode
            INSTALLED=$((INSTALLED + 1))
            ;;
        ollama)
            install_ollama
            INSTALLED=$((INSTALLED + 1))
            ;;
        memory|memoria-avanzada)
            install_memory
            INSTALLED=$((INSTALLED + 1))
            ;;
        hermes)
            install_hermes
            INSTALLED=$((INSTALLED + 1))
            ;;
        skills|plugins)
            install_skills
            INSTALLED=$((INSTALLED + 1))
            ;;
        brain|cerebro)
            install_brain
            INSTALLED=$((INSTALLED + 1))
            ;;
        audio|sonido)
            install_audio
            INSTALLED=$((INSTALLED + 1))
            ;;
        *)
            err "Componente desconocido: $comp"
            echo "Usá --list para ver los componentes disponibles"
            exit 1
            ;;
    esac
done

echo ""
if [[ $INSTALLED -gt 0 ]]; then
    ok "Instalación completada ($INSTALLED componente/s)"
    echo "Ejecutá 'source ~/.bashrc' o reiniciá la terminal para usar los comandos nuevos."
fi
