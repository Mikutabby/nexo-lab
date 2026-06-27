#!/bin/bash
# 🔷 Nexo UI — Instalador
# Interfaz visual estilo HUD con widget de escritorio y web app.

set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; NC='\033[0m'
info()  { echo -e "${BLUE}[INFO]${NC} $*"; }
ok()    { echo -e "${GREEN}[OK]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
err()   { echo -e "${RED}[ERR]${NC} $*"; }
title() { echo -e "\n${CYAN}━━━ $* ━━━${NC}"; }

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
INSTALL_DIR="$HOME/.local/share/nexo-ui"
BIN_DIR="$HOME/.local/bin"
CONFIG_DIR="$HOME/.config/nexo-ui"
STATE_FILE="/tmp/nexo-ui-state.json"

echo ""
echo "============================================"
echo "  🔷 Nexo UI 2.0 — Instalador"
echo "============================================"
echo ""

# ── Verificar OS ────────────────────────────────────────
if [ ! -f /etc/os-release ]; then
    err "Sistema no soportado (se requiere Linux)"
    exit 1
fi
ok "Sistema: $(grep PRETTY_NAME /etc/os-release | cut -d= -f2 | tr -d '\"')"

# ── Instalar dependencias ──────────────────────────────
title "Dependencias del sistema"

DEPS="python3 python3-pip conky"
MISSING=""
for dep in $DEPS; do
    if ! command -v $dep &>/dev/null; then
        MISSING="$MISSING $dep"
    fi
done

if [ -n "$MISSING" ]; then
    info "Instalando:$MISSING"
    sudo apt-get update -qq && sudo apt-get install -y -qq $MISSING
    ok "Dependencias instaladas"
else
    ok "Todas las dependencias del sistema están presentes"
fi

# ── Instalar pip packages ──────────────────────────────
title "Dependencias Python"

pip install --break-system-packages -q flask 2>/dev/null || pip install -q flask
ok "Flask instalado"

# ── Crear directorios ──────────────────────────────────
title "Estructura del proyecto"

mkdir -p "$INSTALL_DIR" "$BIN_DIR" "$CONFIG_DIR"
ok "Directorios creados en $INSTALL_DIR"

# ── Copiar archivos ────────────────────────────────────
title "Copiando archivos"

cp -r "$SCRIPT_DIR/web" "$INSTALL_DIR/"
cp -r "$SCRIPT_DIR/sync" "$INSTALL_DIR/"
cp -r "$SCRIPT_DIR/conky" "$INSTALL_DIR/"
cp "$SCRIPT_DIR/config/nexo-ui.json" "$CONFIG_DIR/"
ok "Archivos copiados"

# ── Crear lanzadores ──────────────────────────────────
title "Lanzadores"

# nexo-ui-web
cat > "$BIN_DIR/nexo-ui-web" << 'EOF'
#!/bin/bash
cd "$HOME/.local/share/nexo-ui/web"
exec python3 app.py "$@"
EOF
chmod +x "$BIN_DIR/nexo-ui-web"

# nexo-ui-daemon
cat > "$BIN_DIR/nexo-ui-daemon" << 'EOF'
#!/bin/bash
exec python3 "$HOME/.local/share/nexo-ui/sync/nexo-ui-daemon.py" "$@"
EOF
chmod +x "$BIN_DIR/nexo-ui-daemon"

# nexo-ui-widget
cat > "$BIN_DIR/nexo-ui-widget" << 'EOF'
#!/bin/bash
exec conky -c "$HOME/.local/share/nexo-ui/conky/nexo-widget.conf"
EOF
chmod +x "$BIN_DIR/nexo-ui-widget"

# nexo-ui (todo en uno)
cat > "$BIN_DIR/nexo-ui" << 'EOF'
#!/bin/bash
# 🔷 Nexo UI — Control unificado
CMD="${1:-help}"
case "$CMD" in
    start)
        echo "🔷 Iniciando Nexo UI..."
        nexo-ui-daemon start
        sleep 1
        nexo-ui-web --port 7070 &
        sleep 1
        nexo-ui-widget &
        echo "✅ Nexo UI activo"
        echo "   Web: http://127.0.0.1:7070"
        echo "   Mini: http://127.0.0.1:7070/mini"
        echo "   Widget: Conky en escritorio"
        ;;
    stop)
        echo "🔷 Deteniendo Nexo UI..."
        kill $(pgrep -f "nexo-ui-daemon") 2>/dev/null || true
        kill $(pgrep -f "app.py.*7070") 2>/dev/null || true
        kill $(pgrep -f "nexo-widget.conf") 2>/dev/null || true
        nexo-ui-daemon stop 2>/dev/null || true
        echo "✅ Nexo UI detenido"
        ;;
    status)
        echo "🔷 Nexo UI — Estado:"
        nexo-ui-daemon status 2>/dev/null || echo "  Daemon: inactivo"
        pgrep -f "app.py.*7070" >/dev/null && echo "  Web App: activa" || echo "  Web App: inactiva"
        pgrep -f "nexo-widget.conf" >/dev/null && echo "  Widget: activo" || echo "  Widget: inactivo"
        ;;
    web)
        nexo-ui-web --port 7070 "$@"
        ;;
    widget)
        nexo-ui-widget
        ;;
    daemon)
        shift
        nexo-ui-daemon "$@"
        ;;
    open)
        xdg-open "http://127.0.0.1:7070" 2>/dev/null || sensible-browser "http://127.0.0.1:7070" 2>/dev/null || echo "Abrí http://127.0.0.1:7070 en tu navegador"
        ;;
    mini)
        xdg-open "http://127.0.0.1:7070/mini" 2>/dev/null || sensible-browser "http://127.0.0.1:7070/mini" 2>/dev/null || echo "Abrí http://127.0.0.1:7070/mini en tu navegador"
        ;;
    help|--help|-h)
        echo "Uso: nexo-ui <comando>"
        echo ""
        echo "  start    Iniciar todo (daemon + web + widget)"
        echo "  stop     Detener todo"
        echo "  status   Mostrar estado"
        echo "  web      Iniciar solo web app"
        echo "  widget   Iniciar solo widget Conky"
        echo "  daemon   Controlar daemon (start|stop|status)"
        echo "  open     Abrir interfaz en navegador"
        echo "  mini     Abrir versión miniatura"
        ;;
    *)
        echo "Comando desconocido: $CMD"
        echo "Usá: nexo-ui help"
        ;;
esac
EOF
chmod +x "$BIN_DIR/nexo-ui"

# nexo-voice (atajo rápido)
if [ -f "$HOME/.local/bin/voice.sh" ]; then
    ln -sf "$HOME/.local/bin/voice.sh" "$BIN_DIR/nexo-voice" 2>/dev/null || true
fi

ok "Lanzadores creados en $BIN_DIR"

# ── Estado inicial ─────────────────────────────────────
title "Estado inicial"

if [ ! -f "$STATE_FILE" ]; then
    python3 -c "
import json, socket
default = {
    'nexo_status': 'idle',
    'last_command': '',
    'last_response': '',
    'cpu': 0, 'ram': 0, 'temp': 0, 'disk': 0,
    'uptime': '0m', 'active_processes': 0,
    'hostname': socket.gethostname(),
    'timestamp': 0, 'nexo_active': False,
    'theme': 'dark'
}
with open('$STATE_FILE', 'w') as f:
    json.dump(default, f, indent=2)
" 2>/dev/null
    ok "Estado inicial creado"
fi

# ── Verificar PATH ─────────────────────────────────────
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    warn "$HOME/.local/bin no está en PATH"
    echo "   Agregá esto a tu ~/.bashrc:"
    echo "   export PATH=\"\$HOME/.local/bin:\$PATH\""
fi

# ── Resumen final ──────────────────────────────────────
echo ""
echo "============================================"
echo "  ✅ Nexo UI 2.0 instalado"
echo "============================================"
echo ""
echo "  Para iniciar:"
echo "    nexo-ui start"
echo ""
echo "  Para abrir interfaz:"
echo "    nexo-ui open      (HUD completo)"
echo "    nexo-ui mini      (Versión miniatura)"
echo ""
echo "  Web app:  http://127.0.0.1:7070"
echo "  Mini:     http://127.0.0.1:7070/mini"
echo ""
echo "  Para más información:"
echo "    nexo-ui help"
echo ""
