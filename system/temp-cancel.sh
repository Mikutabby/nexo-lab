#!/bin/bash
# Cancela el apagado por temperatura
# Se puede ejecutar con: temp-cancel

echo "SUDO_PASS_PLACEHOLDER" | sudo -S systemctl cancel 2>/dev/null
echo "SUDO_PASS_PLACEHOLDER" | sudo -S rtcwake -m disable 2>/dev/null
echo "SUDO_PASS_PLACEHOLDER" | sudo -S sh -c 'echo 0 > /sys/class/rtc/rtc0/wakealarm' 2>/dev/null
rm -f /tmp/temp-monitor-cooldown /tmp/temp-monitor-status

TEMP=$(cat /sys/class/thermal/thermal_zone1/temp 2>/dev/null | awk '{printf "%.1f°C", $1/1000}')
echo "✅ Apagado cancelado. Temperatura actual: ${TEMP:-desconocida}"
spd-say "Apagado cancelado" 2>/dev/null || true
