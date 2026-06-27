#!/bin/bash
# ============================================================================

# Activar venv si existe
if [ -f "$HOME/.nexo-venv/bin/activate" ]; then
  . "$HOME/.nexo-venv/bin/activate"
fi

# Nexo TTS v2 — Text-to-Speech con Piper + preprocessing de texto
# Inspirado en Jarvis (isair/jarvis) TTS system
# ============================================================================
# Habla texto usando el mejor motor disponible:
#   1. Piper TTS (offline, neural, buena calidad)
#   2. gTTS (Google WaveNet, cloud)
#   3. espeak-ng (fallback offline universal)
#
# Uso:
#   say.sh "texto"           → español
#   say.sh en "text"         → inglés
#   say.sh -s "texto lento"  → más lento
#   echo "texto" | say.sh    → pipe
# ============================================================================

set -euo pipefail

LANG_DEFAULT="es"
SPEED="normal"

# ─── MODELOS PIPER ───────────────────────────────────────────────────────────
PIPER_BIN="piper"
PIPER_VOICES_DIR="${HOME}/.local/share/piper-voices"
PIPER_BASE_URL="https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0"

# Voz español por defecto (medium, DaveFx)
PIPER_VOICE_ES_MODEL="es_ES-davefx-medium"
PIPER_VOICE_ES_URL="${PIPER_BASE_URL}/es/es_ES/davefx/medium/es_ES-davefx-medium"

# Voz inglés por defecto
PIPER_VOICE_EN_MODEL="en_GB-alan-medium"
PIPER_VOICE_EN_URL="${PIPER_BASE_URL}/en/en_GB/alan/medium/en_GB-alan-medium"

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
    RAW_TEXT="$*"
else
    RAW_TEXT=$(cat)
    LANG="$LANG_DEFAULT"
fi

[ -z "$RAW_TEXT" ] && exit 0

# ─── PREPROCESAMIENTO DE TEXTO (inspirado en Jarvis TTS) ─────────────────
# Escribe script Python a archivo temporal para evitar problemas de quoting
CLEAN_SCRIPT="/tmp/nexo-clean-text-$$.py"
cat > "$CLEAN_SCRIPT" << 'PYEOF'
import re, sys

text = sys.stdin.read().strip()
if not text:
    sys.exit(0)

# 1. Extraer URLs de markdown: [texto](url) -> texto (link a domain)
text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)',
    lambda m: f'Link a {m.group(1)}' if 'http' in m.group(2) else m.group(1), text)

# 2. URLs sueltas -> dominio legible (sin agregar .com si ya tiene TLD)
text = re.sub(r'https?://([^\s<>\[\]()]+)',
    lambda m: m.group(1).replace('www.', '').rstrip('/').split('/')[0] if '.' in m.group(1).split('/')[0] else m.group(1).split('/')[0] + '.com', text)

# 3. Bloques de codigo ``` ``` -> solo texto interior
text = re.sub(r'```\w*\n?([\s\S]*?)```', r'\1', text)

# 4. Codigo inline \x60x\x60 -> solo x
text = re.sub(r'\x60([^\x60]+)\x60', r'\1', text)

# 5. Negrita **x** / __x__ -> x
text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
text = re.sub(r'__([^_]+)__', r'\1', text)

# 6. Cursiva *x* / _x_ -> x (solo si no esta dentro de palabra)
text = re.sub(r'(?<!\*)\*([^*\s][^*]*?)\*(?!\*)', r'\1', text)
text = re.sub(r'(?<!\w)_([^_\n]+?)_(?!\w)', r'\1', text)

# 7. Tachado ~~x~~ -> x
text = re.sub(r'~~([^~]+)~~', r'\1', text)

# 8. Encabezados # -> quitarlos
text = re.sub(r'^\s*#{1,6}\s+', '', text, flags=re.MULTILINE)

# 9. Citas > -> quitarlas
text = re.sub(r'^\s*>\s?', '', text, flags=re.MULTILINE)

# 10. Listas -*+ -> quitarlas
text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)

# 11. Listas numeradas 1. 2) -> quitarlas
text = re.sub(r'^\s*\d+[.)]\s+', '', text, flags=re.MULTILINE)

# 12. HTML tags -> quitarlos
text = re.sub(r'<[^>]+>', '', text)

# 13. Lineas decorativas --- === -> quitarlas
text = re.sub(r'^\s*[-=]{3,}\s*$', '', text, flags=re.MULTILINE)

# 14. Emojis -> descriptivos basicos
emoji_map = {
    '\u2705': 'check, ',
    '\u274c': 'error, ',
    '\u26a0\ufe0f': 'advertencia, ',
    '\U0001f525': 'caliente, ',
    '\U0001f3b5': 'musica, ',
    '\U0001f3b6': 'musica, ',
    '\U0001f534': 'rojo, ',
    '\U0001f7e2': 'verde, ',
    '\u26a1': 'rayo, ',
    '\U0001f4a1': 'idea, ',
    '\U0001f527': 'herramienta, ',
    '\U0001f680': 'lanzamiento, ',
    '\U0001f4cb': 'lista, ',
    '\u2b50': 'estrella, ',
    '\U0001f512': 'candado, ',
    '\U0001f464': 'usuario, ',
}
for emoji, replacement in emoji_map.items():
    text = text.replace(emoji, replacement)

# 15. Lineas vacias multiples -> una sola
text = re.sub(r'\n{3,}', '\n\n', text)

print(text.strip())
PYEOF

SAY_TEXT=$(printf '%s' "$RAW_TEXT" | python3 "$CLEAN_SCRIPT" 2>/dev/null || true)
rm -f "$CLEAN_SCRIPT"
[ -z "$SAY_TEXT" ] && SAY_TEXT="$RAW_TEXT"

# ─── DESCARGA DE MODELO PIPER (si no existe) ────────────────────────────────
ensure_piper_model() {
    local lang="$1"
    local model_name="" model_url=""

    case "$lang" in
        es) model_name="$PIPER_VOICE_ES_MODEL"; model_url="$PIPER_VOICE_ES_URL" ;;
        en) model_name="$PIPER_VOICE_EN_MODEL"; model_url="$PIPER_VOICE_EN_URL" ;;
        *)  return 1 ;;
    esac

    local model_path="${PIPER_VOICES_DIR}/${model_name}.onnx"
    local json_path="${PIPER_VOICES_DIR}/${model_name}.onnx.json"

    if [ -f "$model_path" ] && [ -f "$json_path" ]; then
        echo "$model_path"
        return 0
    fi

    # Descargar modelo
    mkdir -p "$PIPER_VOICES_DIR"
    echo "Descargando voz Piper: ${model_name} (~60MB)..." >&2

    for suffix in ".onnx" ".onnx.json"; do
        local target="${PIPER_VOICES_DIR}/${model_name}${suffix}"
        local url="${model_url}${suffix}"
        if [ ! -f "$target" ]; then
            wget -q --show-progress -O "$target" "$url" 2>&1 || {
                rm -f "$target" 2>/dev/null
                return 1
            }
        fi
    done

    echo "Voz descargada: ${model_name}" >&2
    echo "$model_path"
}

# ─── 1. PIPER TTS (offline, neural) ─────────────────────────────────────────
case "$SPEED" in
    slow) LENGTH_SCALE="1.3" ;;
    *)    LENGTH_SCALE="1.0" ;;
esac

PIPER_MODEL_PATH=""
PIPER_MODEL_PATH=$(ensure_piper_model "$LANG" 2>/dev/null) || true

if [ -n "$PIPER_MODEL_PATH" ] && command -v "$PIPER_BIN" &>/dev/null; then
    echo "$SAY_TEXT" | "$PIPER_BIN" \
        --model "$PIPER_MODEL_PATH" \
        --output-raw \
        --length-scale "$LENGTH_SCALE" 2>/dev/null | \
        aplay -r 22050 -f S16_LE -c 1 -q 2>/dev/null && {
        echo "$SAY_TEXT" > /tmp/nexo-last-tts.txt
        exit 0
    }
fi

# ─── 2. gTTS (Google WaveNet, cloud) ────────────────────────────────────────
OUT_FILE="/tmp/nexo-tts-$$.mp3"

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

if [ -s "$OUT_FILE" ]; then
    mpg123 --no-gapless -q "$OUT_FILE" 2>/dev/null
    rm -f "$OUT_FILE"
    echo "$SAY_TEXT" > /tmp/nexo-last-tts.txt
    exit 0
fi
rm -f "$OUT_FILE"

# ─── 3. FALLBACK: espeak-ng ────────────────────────────────────────────────
case "$LANG" in
    es) VOICE="es-419" ;;
    en) VOICE="en-us" ;;
    *)  VOICE="$LANG"  ;;
esac

case "$SPEED" in
    slow) SPEED_VAL="120" ;;
    *)    SPEED_VAL="155" ;;
esac

espeak-ng -v "$VOICE" -s "$SPEED_VAL" "$SAY_TEXT" 2>/dev/null

echo "$SAY_TEXT" > /tmp/nexo-last-tts.txt
