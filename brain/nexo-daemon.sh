#!/bin/bash
# 🔷 Nexo Daemon — Asistente de voz autónomo
# Escucha, procesa y responde por voz sin necesidad de opencode.
#
# Uso:
#   nexo-daemon start      → Iniciar en background
#   nexo-daemon stop       → Detener
#   nexo-daemon status     → Estado
#   nexo-daemon foreground → Ejecutar en primer plano (modo debug)

PIDFILE="/tmp/nexo-daemon.pid"
LOGFILE="/tmp/nexo-daemon.log"
VENV="$HOME/.nexo-venv"
NEXO_DIR="$HOME/nexo-lab/nexo-lab"
VOICE_SCRIPT="$NEXO_DIR/voice/voice.sh"
BRAIN_SCRIPT="$NEXO_DIR/brain/nexo-brain.py"
SAY_SCRIPT="$NEXO_DIR/voice/say.sh"

log() {
    echo "[$(date '+%H:%M:%S')] $*" >> "$LOGFILE"
}

ensure_venv() {
    if [ -f "$VENV/bin/activate" ]; then
        . "$VENV/bin/activate"
    fi
}

cmd_foreground() {
    ensure_venv
    log "🔷 Nexo Daemon iniciado"
    echo "🔷 Nexo Daemon — asistente de voz autónomo"
    echo "   Decí 'nexo' seguido de tu comando"
    echo "   Log: $LOGFILE"
    echo ""

    while true; do
        echo "🎤 [Enter] para hablar, o escribí 'texto: <comando>' para teclear:"
        read -t 0.5 -r INPUT 2>/dev/null || true
        if [ -n "$INPUT" ]; then
            if echo "$INPUT" | grep -qi "^texto:"; then
                TEXT=$(echo "$INPUT" | sed 's/^texto://i' | sed 's/^[[:space:]]*//')
            else
                TEXT="$INPUT"
            fi
        else
            TEXT=$(bash "$VOICE_SCRIPT" es 5 2>/dev/null)
        fi
        if [ -n "$TEXT" ]; then
            echo "📝 Tú: $TEXT"
            log "Comando: $TEXT"

            # Verificar wake word
            LOWER=$(echo "$TEXT" | tr '[:upper:]' '[:lower:]')
            if echo "$LOWER" | grep -q "nexo"; then
                # Extraer comando después de "nexo"
                CMD=$(echo "$LOWER" | sed 's/.*nexo//' | sed 's/^[[:space:]]*//')
                if [ -z "$CMD" ]; then
                    # Sin comando inline, grabar de nuevo
                    echo "🎤 Decí tu comando..."
                    CMD=$(bash "$VOICE_SCRIPT" es 5 2>/dev/null)
                fi
            else
                CMD="$TEXT"
            fi

            if [ -n "$CMD" ]; then
                echo "🤖 Procesando: $CMD"
                log "Procesando: $CMD"
                RESPONSE=$(python3 "$BRAIN_SCRIPT" "$CMD" 2>/dev/null)
                echo "🤖 Nexo: $RESPONSE"
                log "Respuesta: $RESPONSE"
            fi
        fi
        sleep 1
    done
}

cmd_daemon() {
    case "${1:-start}" in
        start)
            if [ -f "$PIDFILE" ] && kill -0 $(cat "$PIDFILE") 2>/dev/null; then
                echo "❌ Nexo Daemon ya está corriendo (PID: $(cat $PIDFILE))"
                exit 1
            fi
            echo "🔷 Iniciando Nexo Daemon..."
            nohup "$0" foreground > /dev/null 2>&1 &
            echo $! > "$PIDFILE"
            echo "✅ Nexo Daemon iniciado (PID: $!)"
            echo "   Decí 'nexo' seguido de tu comando"
            ;;
        stop)
            if [ ! -f "$PIDFILE" ]; then
                echo "❌ Nexo Daemon no está corriendo"
                exit 1
            fi
            kill $(cat "$PIDFILE") 2>/dev/null
            rm -f "$PIDFILE"
            echo "✅ Nexo Daemon detenido"
            ;;
        status)
            if [ -f "$PIDFILE" ] && kill -0 $(cat "$PIDFILE") 2>/dev/null; then
                echo "🔷 Nexo Daemon: activo (PID: $(cat $PIDFILE))"
            else
                echo "🔷 Nexo Daemon: inactivo"
            fi
            ;;
        *)
            echo "Uso: $0 {start|stop|status|foreground}"
            ;;
    esac
}

case "${1:-help}" in
    start|stop|status)
        cmd_daemon "$1"
        ;;
    foreground)
        cmd_foreground
        ;;
    *)
        echo "🔷 Nexo Daemon — Asistente de voz autónomo"
        echo ""
        echo "Uso: $0 <comando>"
        echo "  start      Iniciar en background"
        echo "  stop       Detener"
        echo "  status     Mostrar estado"
        echo "  foreground Ejecutar en primer plano (debug)"
        echo ""
        echo "Después de iniciar, decí 'nexo' seguido de tu comando."
        echo "Ej: 'nexo qué hora es', 'nexo abre firefox'"
        ;;
esac
