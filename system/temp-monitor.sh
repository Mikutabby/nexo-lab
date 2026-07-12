#!/bin/bash
# Monitor de temperatura - avisa por parlantes y apaga si es crítico
# Cancelar apagado: rm -f /tmp/temp-monitor-cooldown && sudo rtcwake -m disable

NEXO_VERSION="2.0"

case "${1:-}" in
  --help|-h) head -5 "$0" | grep -E "^# " | sed 's/^# //'; exit 0 ;;
  --version|-v) echo "Nexo Temp Monitor v${NEXO_VERSION}"; exit 0 ;;
esac

WARN=75       # Alerta temprana (solo avisa)
CRIT=80       # Shutdown
COOLDOWN=480  # 8 minutos
LOG_TAG="temp-monitor"
STATUS_FILE="/tmp/temp-monitor-status"

# Leer temperatura
TEMP=""
if [ -f /sys/class/thermal/thermal_zone1/temp ]; then
    TEMP=$(awk '{printf "%d", $1/1000}' /sys/class/thermal/thermal_zone1/temp)
elif [ -f /sys/class/thermal/thermal_zone0/temp ]; then
    TEMP=$(awk '{printf "%d", $1/1000}' /sys/class/thermal/thermal_zone0/temp)
fi

if [ -z "$TEMP" ]; then
    TEMP=$(sensors 2>/dev/null | grep "Package id 0:" | grep -oP '[+-]?\d+\.\d+°C' | head -1 | tr -d '+°C' | awk -F. '{print $1}')
fi

[ -z "$TEMP" ] && exit 1

echo "$TEMP" > "$STATUS_FILE"
logger -t "$LOG_TAG" "${TEMP}°C"

# ---- PRE-ALERTA (solo aviso, sin apagar) ----
if [ "$TEMP" -ge "$WARN" ] && [ "$TEMP" -lt "$CRIT" ]; then
    logger -t "$LOG_TAG" "⚠️  Precaución: ${TEMP}°C"
    notify-send -u critical -t 6000 \
        "🔥 Temperatura: ${TEMP}°C" \
        "Cuidado, se está calentando." 2>/dev/null || true
    spd-say "Cuidado, la temperatura está en ${TEMP} grados" 2>/dev/null || true
    exit 0
fi

# ---- CRÍTICO ----
if [ "$TEMP" -ge "$CRIT" ]; then
    # Si ya estamos en cooldown, no repetir
    if [ -f /tmp/temp-monitor-cooldown ]; then
        exit 0
    fi

    logger -t "$LOG_TAG" "¡CRÍTICO! ${TEMP}°C"

    # Hablar por los parlantes
    spd-say "ATENCIÓN. Temperatura crítica: ${TEMP} grados. El sistema se apagará en dos minutos. Decí no para cancelar." 2>/dev/null || true

    notify-send -u critical -t 12000 \
        "🔥🔥 CRÍTICO: ${TEMP}°C" \
        "Apagado en 2 minutos.\nGuardá tu trabajo.\nCancelar: rm -f /tmp/temp-monitor-cooldown" 2>/dev/null || true

    wall "🔥  TEMPERATURA CRÍTICA: ${TEMP}°C
⏳  Apagado en 2 minutos. Guardá tu trabajo.
✋  Decí NO para cancelar."

    touch /tmp/temp-monitor-cooldown

    # Esperar 1 minuto
    sleep 60

    # Si cancelaron, salir
    if [ ! -f /tmp/temp-monitor-cooldown ]; then
        logger -t "$LOG_TAG" "Apagado cancelado por el usuario"
        spd-say "Apagado cancelado" 2>/dev/null || true
        exit 0
    fi

    # Segundo aviso
    spd-say "Un minuto restante. Guardá tu trabajo." 2>/dev/null || true
    notify-send -u critical -t 8000 \
        "⏳ 1 minuto restante" \
        "Apagado en 60 segundos." 2>/dev/null || true
    wall "⏳  1 minuto para el apagado."

    sleep 30

    if [ ! -f /tmp/temp-monitor-cooldown ]; then
        logger -t "$LOG_TAG" "Apagado cancelado por el usuario"
        spd-say "Apagado cancelado" 2>/dev/null || true
        exit 0
    fi

    # Tercer aviso
    spd-say "Treinta segundos. Último aviso." 2>/dev/null || true
    notify-send -u critical -t 8000 \
        "⏳ 30 segundos" \
        "Último aviso." 2>/dev/null || true
    wall "⏳  30 segundos."

    sleep 30

    if [ ! -f /tmp/temp-monitor-cooldown ]; then
        logger -t "$LOG_TAG" "Apagado cancelado por el usuario"
        spd-say "Apagado cancelado" 2>/dev/null || true
        exit 0
    fi

    # Apagar y programar reinicio
    spd-say "Apagando sistema" 2>/dev/null || true
    sudo /sbin/rtcwake -m off -s "$COOLDOWN"
    sudo /usr/bin/systemctl poweroff
fi
