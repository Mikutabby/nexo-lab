#!/bin/bash
# ============================================================================
# Nexo TTS — Text-to-Speech
# ============================================================================
# Habla el texto en máximo 5 segundos con la mejor calidad posible.
#
# Prioridad:
#   1. gTTS (Google WaveNet) — voz natural, ~1.5s
#   2. espeak-ng directo     — fallback universal, ~0.03s
#
# Uso:
#   say.sh "texto"           → español
#   say.sh en "text"         → inglés
#   say.sh -s "texto lento"  → más lento
#   echo "texto" | say.sh    → pipe
# ============================================================================

LANG_DEFAULT="es"
SPEED="normal"

# ─── VOCES DE RESPALDO ──────────────────────────────────────────────────────
VOICE_ES="es-419"
VOICE_EN="en-us"

# ─── Parseo de argumentos ──────────────────────────────────────────────────
if [ $# -gt 0 ]; then
    case "$1" in
        es|en) LANG="$1"; shift ;;
        -s)    SPEED="slow"; LANG="$LANG_DEFAULT"; shift ;;
        *)     LANG="$LANG_DEFAULT" ;;
    esac
    while [ $# -gt 0 ]; do
        case "$1" in
            -s) SPEED="slow"; shift ;;
            *)  break ;;
        esac
    done
    SAY_TEXT="$*"
else
    SAY_TEXT=$(cat)
    LANG="$LANG_DEFAULT"
fi

[ -z "$SAY_TEXT" ] && exit 0

case "$SPEED" in
    slow) SPEED_VAL="120" ;;
    *)    SPEED_VAL="155" ;;
esac

OUT_FILE="/tmp/nexo-tts-$$.mp3"

# ─── 1. gTTS: generar audio con Google WaveNet ─────────────────────────────
# Escribir texto a archivo para evitar problemas con caracteres especiales
printf '%s' "$SAY_TEXT" > /tmp/nexo-tts-texto.txt

python3 -c "
import sys
try:
    from gtts import gTTS
    with open('/tmp/nexo-tts-texto.txt') as f:
        txt = f.read()
    if not txt.strip():
        sys.exit(1)
    tts = gTTS(txt, lang='$LANG')
    tts.save('$OUT_FILE')
    sys.exit(0)
except Exception:
    sys.exit(1)
" 2>/dev/null

rm -f /tmp/nexo-tts-texto.txt

# Si generó el archivo, reproducirlo
if [ -s "$OUT_FILE" ]; then
    mpg123 --no-gapless -q "$OUT_FILE" 2>/dev/null
    rm -f "$OUT_FILE"
    echo "$SAY_TEXT" > /tmp/nexo-last-tts.txt
    exit 0
fi
rm -f "$OUT_FILE"

# ─── 2. FALLBACK: espeak-ng (sin internet, o si gTTS falló) ────────────────
case "$LANG" in
    es) VOICE="$VOICE_ES" ;;
    en) VOICE="$VOICE_EN" ;;
    *)  VOICE="$LANG"     ;;
esac

espeak-ng -v "$VOICE" -s "$SPEED_VAL" "$SAY_TEXT" 2>/dev/null

echo "$SAY_TEXT" > /tmp/nexo-last-tts.txt
