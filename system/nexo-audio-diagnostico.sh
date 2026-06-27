#!/bin/bash
# 🔇 Nexo Audio Diagnóstico
# Revisa y repara el audio del sistema

echo "🔇 Nexo Audio Diagnóstico"
echo "========================="
echo ""

# 1. Estado de PipeWire
echo "📡 PipeWire:"
systemctl --user status pipewire --no-pager -n 3 2>/dev/null | grep -E "Active|Main PID"
echo ""

# 2. Estado de WirePlumber
echo "🔧 WirePlumber:"
systemctl --user status wireplumber --no-pager -n 3 2>/dev/null | grep -E "Active|Main PID"
echo ""

# 3. Dispositivos de audio
echo "🔊 Dispositivos:"
wpctl status 2>/dev/null | grep -A 20 "^Audio" | grep -v "^Video"
echo ""

# 4. Volumen actual
echo "🔊 Volumen:"
wpctl get-volume 52 2>/dev/null || echo "  No se pudo obtener volumen"
echo ""

# 5. Mute state
echo "🔇 Mudo:"
pactl list sinks 2>/dev/null | grep -i mute | head -1 || pw-cli info 52 2>/dev/null | grep mute | head -1
echo ""

# 6. Prueba de reproducción
echo "▶️  Probando reproducción..."
if bash "$HOME/nexo-lab/nexo-lab/voice/say.sh" "Prueba de audio" 2>/dev/null; then
    echo "  ✅ Audio OK"
else
    echo "  ❌ Error en reproducción"
fi
echo ""

# 7. Prueba de micrófono
echo "🎤 Probando micrófono (2s)..."
if timeout 2 parec --rate=16000 --channels=1 --format=s16le 2>/dev/null | ffmpeg -y -f s16le -ar 16000 -ac 1 -i pipe:0 /tmp/nexo-test-mic.wav 2>/dev/null; then
    SIZE=$(stat -c%s /tmp/nexo-test-mic.wav 2>/dev/null || echo 0)
    if [ "$SIZE" -gt 1000 ]; then
        echo "  ✅ Micrófono captura audio ($SIZE bytes)"
    else
        echo "  ❌ Micrófono no captura suficiente audio"
    fi
else
    echo "  ❌ No se pudo grabar"
fi
rm -f /tmp/nexo-test-mic.wav
echo ""

# 8. Soluciones rápidas
echo "🔧 Si hay problemas:"
echo "  systemctl --user restart pipewire wireplumber"
echo "  wpctl set-volume 52 0.8"
echo "  wpctl set-mute 52 0"
