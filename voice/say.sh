#!/bin/bash
# Text-to-Speech para OpenCode
# Usa múltiples motores TTS en orden de preferencia:
# 1. gTTS (Google TTS - rápido, buena calidad)
# 2. edge-tts (Microsoft Neural TTS - backup)
# 3. espeak-ng + MBROLA (voces de diphonemas)
# 4. espeak-ng (fallback por defecto)

# Idioma por defecto
LANG_DEFAULT="es"

# Umbral de timeout para TTS cloud (segundos)
# gTTS necesita ~5-12s en conexiones lentas, más playback
CLOUD_TIMEOUT=30

# Archivos temporales
TMPDIR="${XDG_RUNTIME_DIR:-/tmp}/opencode_tts"
mkdir -p "$TMPDIR"

# Velocidad: normal por defecto, slow con -s
SPEED="normal"

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
# al timeout del bash tool que mata la shell padre a los 30s.
play_detached() {
    local file="$1"
    setsid bash -c '
        f="$1"
        export PULSE_SERVER="unix:/run/user/1000/pulse/native"
        # Intentar multiples reproductores en orden de preferencia
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

# === INTENTAR 1: edge-tts (Microsoft Neural TTS) ===
try_edge_tts() {
    local text="$1"
    local lang="$2"
    local voice=""
    local outfile="$TMPDIR/edge_tts_$$.mp3"

    case "$lang" in
        es) voice="es-AR-ElenaNeural" ;;
        en) voice="en-US-JennyNeural" ;;
        *)  voice="es-AR-ElenaNeural" ;;
    esac

    # edge-tts con timeout - simple, sin SSML ni emociones
    local tag="$$"
    local textfile="$TMPDIR/edge_txt_$tag.txt"
    local scriptfile="$TMPDIR/edge_run_$tag.py"
    echo "$text" > "$textfile"
    cat > "$scriptfile" << PYSCRIPT
import asyncio, sys
with open("$textfile", "r") as f: txt = f.read()
import edge_tts
async def run():
    tts = edge_tts.Communicate(txt, "$voice")
    await tts.save("$outfile")
asyncio.run(run())
sys.exit(0)
PYSCRIPT
    timeout "$CLOUD_TIMEOUT" python3 "$scriptfile" 2>/dev/null && [ -s "$outfile" ] && {
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
    timeout "$CLOUD_TIMEOUT" python3 -c "
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

# === INTENTAR 3: espeak-ng + MBROLA ===
try_mbrola() {
    local text="$1"
    local lang="$2"
    local voice=""
    local outfile="$TMPDIR/mbrola_$$.wav"

    case "$lang" in
        es) voice="mb-es3" ;;   # Voz femenina española MBROLA
        en) voice="mb-us3" ;;   # Voz estadounidense MBROLA
        *)  voice="mb-es3" ;;
    esac

    # Configurar rutas si mbrola está disponible
    if command -v mbrola &>/dev/null || [ -x "$HOME/.local/bin/mbrola" ]; then
        export PATH="$HOME/.local/bin:$PATH"
        export XDG_DATA_DIRS="$HOME/.local/share:/usr/share/xfce4:$HOME/.local/share/flatpak/exports/share:/var/lib/flatpak/exports/share:/usr/local/share:/usr/share"
        
        espeak-ng -v "$voice" -w "$outfile" "$text" 2>/dev/null && [ -s "$outfile" ] && {
            play_detached "$outfile"
            return 0
        }
    fi
    rm -f "$outfile"
    return 1
}

# === INTENTAR 4: espeak-ng optimizado (fallback final) ===
try_espeak() {
    local text="$1"
    local lang="$2"
    local voice=""
    local outfile="$TMPDIR/espeak_$$.wav"

    case "$lang" in
        es) voice="es-419" ;;
        en) voice="en-us" ;;
        *)  voice="$lang" ;;
    esac

    local speed="155"
    [ "$SPEED" = "slow" ] && speed="110"
    espeak-ng -v "$voice" -s "$speed" -p 35 -P 65 -w "$outfile" "$text" 2>/dev/null && [ -s "$outfile" ] && {
        play_detached "$outfile"
        return 0
    }
    rm -f "$outfile"
    # Último recurso: espeak-ng directo sin archivo
    # También va con setsid para no bloquear
    setsid espeak-ng -v "$voice" -s "$speed" -p 35 -P 65 "$text" 2>/dev/null &
    return 0
}

# === EJECUCIÓN ===
# 1. gTTS primero (mejor calidad), timeout generoso para conexiones lentas
# 2. Si falla, espeak instantáneo como respaldo (sin edge-tts/mbrola, son lentos)
try_gtts "$SAY_TEXT" "$LANG" || {
    echo "⚠️ gTTS falló, usando espeak como respaldo" >&2
    try_espeak "$SAY_TEXT" "$LANG" || true
}

# Guardar texto hablado para echo detection (voice.sh lo usa)
echo "$SAY_TEXT" > /tmp/nexo-last-tts.txt

exit $?
