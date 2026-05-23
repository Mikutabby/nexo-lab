#!/bin/bash
# Text-to-Speech para OpenCode
# Usa múltiples motores TTS en orden de preferencia:
# 1. Piper TTS (local, rápido, sin depender de internet) 🏆
# 2. gTTS (Google TTS - cloud, backup)
# 3. espeak-ng (fallback universal)

# Idioma por defecto
LANG_DEFAULT="es"

# Archivos temporales
TMPDIR="${XDG_RUNTIME_DIR:-/tmp}/opencode_tts"
mkdir -p "$TMPDIR"

# Velocidad: normal por defecto, slow con -s
SPEED="normal"

# Ruta de Piper
PIPER_BIN="$HOME/.local/bin/piper"
PIPER_VOICES="$HOME/.local/share/piper-voices"

# Determinar idioma y texto
if [ $# -gt 0 ]; then
    case "$1" in
        es|en)
            LANG="$1"
            shift
            ;;
        -s)
            SPEED="slow"
            LANG="$LANG_DEFAULT"
            shift
            ;;
        *)
            LANG="$LANG_DEFAULT"
            ;;
    esac
    # Flags adicionales después del primero
    while [ $# -gt 0 ]; do
        case "$1" in
            -s)
                SPEED="slow"
                shift
                ;;
            *)
                break
                ;;
        esac
    done
    SAY_TEXT="$*"
else
    SAY_TEXT=$(cat)
    LANG="$LANG_DEFAULT"
fi

[ -z "$SAY_TEXT" ] && exit 0

# Limpiar texto (quitar comillas que puedan interferir)
SAY_TEXT=$(echo "$SAY_TEXT" | sed "s/['\"]//g")

# Reproducir audio en proceso desacoplado (setsid) para que sobreviva
# al timeout del bash tool que mata la shell padre.
play_detached() {
    local file="$1"
    setsid bash -c '
        f="$1"
        export PULSE_SERVER="unix:/run/user/1000/pulse/native"
        case "$f" in
            *.mp3)
                mpg123 --no-gapless -o pulse --quiet "$f" 2>/dev/null || \
                play -q "$f" 2>/dev/null || \
                paplay "$f" 2>/dev/null
                ;;
            *.wav)
                aplay -q "$f" 2>/dev/null || \
                play -q "$f" 2>/dev/null || \
                paplay "$f" 2>/dev/null
                ;;
        esac
        rm -f "$f"
    ' _ "$file" &
}

# === INTENTAR 1: Piper TTS (local, rápido) ===
try_piper() {
    local text="$1"
    local lang="$2"
    local voice_model=""

    # Seleccionar voz según idioma
    case "$lang" in
        es) voice_model="$PIPER_VOICES/es_ES-davefx-medium.onnx" ;;
        en) voice_model="$PIPER_VOICES/en_US-lessac-medium.onnx" ;;
        *)  voice_model="$PIPER_VOICES/es_ES-davefx-medium.onnx" ;;
    esac

    # Verificar que Piper y la voz existen
    [ -x "$PIPER_BIN" ] || return 1
    [ -f "$voice_model" ] || return 1

    local outfile="$TMPDIR/piper_$$.wav"

    # Piper no necesita timeout — es local
    echo "$text" | "$PIPER_BIN" \
        --model "$voice_model" \
        --output-file "$outfile" 2>/dev/null && [ -s "$outfile" ] && {
        play_detached "$outfile"
        return 0
    }
    rm -f "$outfile"
    return 1
}

# === INTENTAR 2: gTTS (Google TTS) ===
try_gtts() {
    local text="$1"
    local lang="$2"
    local outfile="$TMPDIR/gtts_$$.mp3"

    echo "$text" > "$TMPDIR/gtts_text_$$.txt"

    # gTDS timeout: si la conexión es lenta, esperar hasta 20s
    timeout 20 python3 -c "
import sys
try:
    from gtts import gTTS
    with open('$TMPDIR/gtts_text_$$.txt', 'r') as f:
        txt = f.read()
    tts = gTTS(txt, lang='$lang')
    tts.save('$outfile')
    sys.exit(0)
except Exception as e:
    sys.exit(1)
" 2>/dev/null && [ -s "$outfile" ] && {
    play_detached "$outfile"
    return 0
}
    rm -f "$outfile"
    return 1
}

# === INTENTAR 3: espeak-ng (fallback final) ===
try_espeak() {
    local text="$1"
    local lang="$2"
    local voice=""

    case "$lang" in
        es) voice="es-419" ;;
        en) voice="en-us" ;;
        *)  voice="$lang" ;;
    esac

    local speed="155"
    [ "$SPEED" = "slow" ] && speed="110"
    # Directo: sin archivo intermedio, arranca al toque (~100ms)
    setsid espeak-ng -v "$voice" -s "$speed" -p 35 -P 65 "$text" 2>/dev/null &
    return 0
}

# === DESCARGAR VOZ DE PIPER (si falta) ===
ensure_piper_voice() {
    local lang="$1"
    local voice_model=""
    local voice_url=""
    local voice_json_url=""

    case "$lang" in
        es)
            voice_model="$PIPER_VOICES/es_ES-davefx-medium.onnx"
            voice_url="https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/davefx/medium/es_ES-davefx-medium.onnx?download=true"
            voice_json_url="https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/davefx/medium/es_ES-davefx-medium.onnx.json?download=true"
            ;;
        en)
            voice_model="$PIPER_VOICES/en_US-lessac-medium.onnx"
            voice_url="https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx?download=true"
            voice_json_url="https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json?download=true"
            ;;
    esac

    if [ -x "$PIPER_BIN" ] && [ ! -f "$voice_model" ]; then
        echo "⚠️ Descargando voz Piper para $lang..." >&2
        mkdir -p "$PIPER_VOICES"
        curl -sL "$voice_url" -o "$voice_model" &
        curl -sL "$voice_json_url" -o "${voice_model}.json" &
        wait
        echo "✅ Voz Piper descargada" >&2
    fi
}

# === EJECUCIÓN ===
# Prioridad: velocidad ante todo.
# ⚡ espeak-ng directo (local, rápido, ~100ms para empezar a hablar)
# ❌ NO usamos Piper TTS ni gTTS — en PCs lentas tardan +15s en generar
try_espeak "$SAY_TEXT" "$LANG" || true

# Guardar texto hablado para echo detection (voice.sh lo usa)
echo "$SAY_TEXT" > /tmp/nexo-last-tts.txt

exit $?
