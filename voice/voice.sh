#!/bin/bash
# Voice-to-text for OpenCode using Google Web Speech API

# Activar venv si existe
if [ -f "$HOME/.nexo-venv/bin/activate" ]; then
  . "$HOME/.nexo-venv/bin/activate"
fi

# Usage: ./voice.sh [language] [duration]
# Defaults: language=es-ES, duration=5

LANG="${1:-es-ES}"
DUR="${2:-5}"
OUTFILE="/tmp/opencode_voice.wav"

# Mapear código de idioma para Google
case "$LANG" in
    es|es-ES|es-*|spanish) GOOGLE_LANG="es-ES" ;;
    en|en-US|english) GOOGLE_LANG="en-US" ;;
    pt|pt-BR|portuguese) GOOGLE_LANG="pt-BR" ;;
    fr|french) GOOGLE_LANG="fr-FR" ;;
    de|german) GOOGLE_LANG="de-DE" ;;
    it|italian) GOOGLE_LANG="it-IT" ;;
    *) GOOGLE_LANG="$LANG" ;;
esac

echo "🎤 Grabando ${DUR}s..." >&2

# Asegurar PULSE_SERVER para systemd
export PULSE_SERVER="${PULSE_SERVER:-unix:/run/user/1000/pulse/native}"

# Método 1: parec + ffmpeg (PulseAudio nativo)
timeout "$DUR" parec --rate=16000 --channels=1 --format=s16le 2>/dev/null | \
    ffmpeg -y -f s16le -ar 16000 -ac 1 -i pipe:0 "$OUTFILE" 2>/dev/null

# Método 2: fallback rec (SoX)
if [ ! -s "$OUTFILE" ]; then
    rec -q -r 16000 -c 1 -b 16 "$OUTFILE" trim 0 "$DUR" 2>/dev/null
fi

# Método 3: fallback arecord (ALSA directo)
if [ ! -s "$OUTFILE" ]; then
    arecord -q -r 16000 -c 1 -f S16_LE -d "$DUR" "$OUTFILE" 2>/dev/null
fi

# Verificar
if [ ! -s "$OUTFILE" ]; then
    echo "ERROR: No hay audio"
    exit 1
fi

echo "🔄 Transcribiendo..." >&2

# VAD: detectar si hay voz usando webrtcvad
python3 -c "
import sys, json, wave, struct
try:
    import webrtcvad
    with wave.open('$OUTFILE', 'r') as wf:
        framerate = wf.getframerate()
        pcm = wf.readframes(wf.getnframes())
    vad = webrtcvad.Vad(3)
    frame_ms = 30
    frame_bytes = int(framerate * frame_ms / 1000) * 2
    speech = 0
    total = 0
    for i in range(0, len(pcm) - frame_bytes + 1, frame_bytes):
        if vad.is_speech(pcm[i:i+frame_bytes], framerate):
            speech += 1
        total += 1
    pct = (speech / total * 100) if total > 0 else 0
    print(json.dumps({'has_voice': pct >= 15, 'pct': round(pct, 1)}))
except Exception as e:
    print(json.dumps({'has_voice': True, 'pct': 50, 'error': str(e)}))
" > /tmp/vad_result.json 2>/dev/null

VAD_HAS_VOICE=$(python3 -c "import json; d=json.load(open('/tmp/vad_result.json')); print('true' if d['has_voice'] else 'false')" 2>/dev/null)
VAD_PCT=$(python3 -c "import json; d=json.load(open('/tmp/vad_result.json')); print(d['pct'])" 2>/dev/null)
echo "📊 VAD: voz=$VAD_HAS_VOICE ($VAD_PCT% frames)" >&2

if [ "$VAD_HAS_VOICE" != "true" ]; then
    echo "⏹️  Sin voz detectada, omitiendo API" >&2
    rm -f "$OUTFILE" /tmp/vad_result.json
    exit 0
fi

# Recortar silencio usando webrtcvad
python3 -c "
import sys, wave, struct, json
try:
    import webrtcvad
    with wave.open('$OUTFILE', 'r') as wf:
        params = wf.getparams()
        framerate = wf.getframerate()
        pcm = wf.readframes(wf.getnframes())
    vad = webrtcvad.Vad(1)
    frame_ms = 30
    frame_bytes = int(framerate * frame_ms / 1000) * 2
    # Encontrar inicio y fin de voz
    voiced_frames = []
    for i in range(0, len(pcm) - frame_bytes + 1, frame_bytes):
        frame = pcm[i:i+frame_bytes]
        if vad.is_speech(frame, framerate):
            voiced_frames.append(frame)
    if voiced_frames:
        trimmed = b''.join(voiced_frames)
        with wave.open('/tmp/opencode_voice_trimmed.wav', 'w') as wf:
            wf.setparams(params)
            wf.writeframes(trimmed)
except Exception:
    # Si falla, copiar original
    import shutil
    shutil.copy('$OUTFILE', '/tmp/opencode_voice_trimmed.wav')
" 2>/dev/null

if [ -s "/tmp/opencode_voice_trimmed.wav" ]; then
    OUTFILE_ORIG="$OUTFILE"
    OUTFILE="/tmp/opencode_voice_trimmed.wav"
fi

# Usar Python speech_recognition
python3 -c "
import sys
try:
    import speech_recognition as sr
except ImportError:
    import subprocess
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'SpeechRecognition', '--break-system-packages'])
    import speech_recognition as sr

r = sr.Recognizer()
with sr.WavFile('$OUTFILE') as source:
    r.adjust_for_ambient_noise(source, duration=0.5)
    audio = r.record(source)

try:
    text = r.recognize_google(audio, language='$GOOGLE_LANG')
    # stdout: solo el texto (para pipelines)
    print(text)
    # stderr: metadata
    print(f'TEXTO:{text}', file=sys.stderr)
except sr.UnknownValueError:
    print('ERROR:No se entendió el audio', file=sys.stderr)
except sr.RequestError as e:
    print(f'ERROR:API no disponible - {e}')
except Exception as e:
    print(f'ERROR:{e}')
" > /tmp/voice_result.txt 2>/dev/null

RESULT=$(cat /tmp/voice_result.txt 2>/dev/null)

if echo "$RESULT" | grep -q "^TEXTO:"; then
    TEXT=$(echo "$RESULT" | sed 's/^TEXTO://')
    
    # === ECHO DETECTION ===
    # Comparar con el último texto hablado por TTS para evitar loops
    if [[ -f /tmp/nexo-last-tts.txt ]]; then
        LAST_TTS=$(cat /tmp/nexo-last-tts.txt | tr '[:upper:]' '[:lower:]' | sed 's/[^a-záéíóúñ0-9 ]//g')
        TRANS_TTS=$(echo "$TEXT" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-záéíóúñ0-9 ]//g')
        
        # Jaccard similarity entre palabras del TTS y lo transcrito
        python3 -c "
import sys
last = '''$LAST_TTS'''.split()
trans = '''$TRANS_TTS'''.split()
if not last or not trans:
    sys.exit(0)
set_a = set(last)
set_b = set(trans)
inter = len(set_a & set_b)
union = len(set_a | set_b)
jaccard = inter / union if union > 0 else 0
# Si más del 50% de las palabras coinciden, es eco
if jaccard > 0.5 or (len(trans) <= 3 and inter >= 2):
    print('ECHO')
else:
    print('OK')
" 2>/dev/null | grep -q "ECHO" && {
        echo "🔇 Eco detectado — ignorando" >&2
        rm -f "$OUTFILE" "$OUTFILE_ORIG" /tmp/opencode_voice_trimmed.wav /tmp/voice_result.txt /tmp/vad_result.json
        exit 0
    }
    fi
    
    echo "$TEXT"
    echo -n "$TEXT" | xclip -selection clipboard 2>/dev/null || \
    echo -n "$TEXT" | xsel -b 2>/dev/null
elif echo "$RESULT" | grep -q "^ERROR:"; then
    echo "❌ $(echo "$RESULT" | sed 's/^ERROR://')" >&2
    exit 1
fi

# Limpiar
rm -f "$OUTFILE" "$OUTFILE_ORIG" /tmp/opencode_voice_trimmed.wav /tmp/voice_result.txt /tmp/vad_result.json
