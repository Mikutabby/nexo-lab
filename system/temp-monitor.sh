#!/bin/bash
# temp-monitor.sh — Monitoreo de temperatura para cron
# Se ejecuta cada 2 minutos, verifica temperatura, y toma acción si es necesario

LOG_FILE="/home/miku/.nexo-memory/logs/temp.log"
mkdir -p "$(dirname "$LOG_FILE")"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

get_temp() {
    local temp=$(cat /sys/class/thermal/thermal_zone1/temp 2>/dev/null)
    if [ -n "$temp" ]; then
        echo $((temp / 1000))
    else
        echo "0"
    fi
}

get_temp_avg() {
    # Get average of last 5 readings
    if [ -f "$LOG_FILE" ]; then
        grep "Temperatura:" "$LOG_FILE" | tail -5 | grep -oP '\d+°C' | tr -d '°C' | awk '{sum+=$1; count++} END {if(count>0) print int(sum/count); else print 0}'
    else
        echo "0"
    fi
}

emergency_mode() {
    log "🚨 MODO EMERGENCIA: Temperatura crítica detectada"
    
    # Reducir frecuencia máxima (con sudo via PTY)
    for cpu in /sys/devices/system/cpu/cpu*/cpufreq/scaling_max_freq; do
        script -qc 'echo "0207" | sudo -S tee "'"$cpu"'" > /dev/null 2>&1' /dev/null
    done
    
    # Forzar powersave (con sudo via PTY)
    for cpu in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
        script -qc 'echo "0207" | sudo -S tee "'"$cpu"'" > /dev/null 2>&1' /dev/null
    done
    
    # Reducir prioridad de procesos pesados
    for pid in $(ps aux --sort=-%cpu | awk '$3 > 50 {print $2}' | head -5); do
        renice +19 $pid 2>/dev/null
    done
    
    log "✅ Optimizaciones de emergencia aplicadas"
}

warning_mode() {
    log "⚠️ ALERTA: Temperatura alta detectada"
    
    # Reducir prioridad de procesos pesados
    for pid in $(ps aux --sort=-%cpu | awk '$3 > 30 {print $2}' | head -3); do
        renice +15 $pid 2>/dev/null
    done
    
    log "✅ Optimizaciones de alerta aplicadas"
}

# Main
temp=$(get_temp)
avg=$(get_temp_avg)

log "Temperatura: ${temp}°C (promedio: ${avg}°C)"

if [ "$temp" -ge 80 ]; then
    emergency_mode
elif [ "$temp" -ge 70 ]; then
    warning_mode
fi

# Keep only last 1000 lines
if [ -f "$LOG_FILE" ]; then
    tail -1000 "$LOG_FILE" > "$LOG_FILE.tmp" && mv "$LOG_FILE.tmp" "$LOG_FILE"
fi
