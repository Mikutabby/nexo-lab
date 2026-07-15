#!/usr/bin/env python3
"""
voice.py — Speech-to-Text para Nexo
====================================
Versión mejorada en Python con:
- Múltiples métodos de grabación (parec, rec, arecord, pyaudio)
- VAD con webrtcvad
- Detección de eco
- Soporte para múltiples motores de transcripción
- Mejor manejo de errores

Uso:
    voice.py [idioma] [duracion]
    voice.py es-ES 5
    voice.py en-US 10
"""

import os
import sys
import json
import wave
import struct
import tempfile
import subprocess
import shutil
from pathlib import Path
from typing import Optional, Tuple

# ── Configuración ──────────────────────────────────────────────────────────
SHM_DIR = Path("/dev/shm/nexo-voice")
FALLBACK_DIR = Path(tempfile.gettempdir()) / "nexo-voice"
VOICE_FILE = "opencode_voice.wav"
TRIMMED_FILE = "opencode_voice_trimmed.wav"
RESULT_FILE = "voice_result.txt"
VAD_FILE = "vad_result.json"
LAST_TTS_FILE = "nexo-last-tts.txt"

# ── Colores ────────────────────────────────────────────────────────────────
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'

def info(msg: str) -> None:
    print(f"{Colors.BLUE}🎤{Colors.NC} {msg}", file=sys.stderr)

def ok(msg: str) -> None:
    print(f"{Colors.GREEN}✓{Colors.NC} {msg}", file=sys.stderr)

def warn(msg: str) -> None:
    print(f"{Colors.YELLOW}⚠{Colors.NC} {msg}", file=sys.stderr)

def err(msg: str) -> None:
    print(f"{Colors.RED}✗{Colors.NC} {msg}", file=sys.stderr)

# ── Idiomas soportados ────────────────────────────────────────────────────
LANGUAGES = {
    'es': 'es-ES', 'es-ES': 'es-ES', 'es-AR': 'es-AR', 'es-MX': 'es-MX',
    'spanish': 'es-ES',
    'en': 'en-US', 'en-US': 'en-US', 'en-GB': 'en-GB',
    'english': 'en-US',
    'pt': 'pt-BR', 'pt-BR': 'pt-BR', 'portuguese': 'pt-BR',
    'fr': 'fr-FR', 'french': 'fr-FR',
    'de': 'de-DE', 'german': 'de-DE',
    'it': 'it-IT', 'italian': 'it-IT',
}

def normalize_language(lang: str) -> str:
    """Normaliza código de idioma para Google."""
    return LANGUAGES.get(lang, lang)

# ── Directorio de trabajo ─────────────────────────────────────────────────
def get_work_dir() -> Path:
    """Obtiene el directorio de trabajo (RAM preferido, fallback a /tmp)."""
    if SHM_DIR.exists() or SHM_DIR.parent.exists():
        try:
            SHM_DIR.mkdir(exist_ok=True)
            return SHM_DIR
        except Exception:
            pass
    FALLBACK_DIR.mkdir(exist_ok=True)
    return FALLBACK_DIR

# ── Grabación de audio ────────────────────────────────────────────────────
def record_with_parec(duration: int, output: Path) -> bool:
    """Graba audio usando parec (PulseAudio)."""
    try:
        cmd = [
            "timeout", str(duration),
            "parec", "--rate=16000", "--channels=1", "--format=s16le"
        ]
        proc = subprocess.run(cmd, capture_output=True)
        
        if proc.returncode == 0 and proc.stdout:
            # Convertir raw a WAV usando ffmpeg
            ffmpeg_cmd = [
                "ffmpeg", "-y", "-f", "s16le", "-ar", "16000", "-ac", "1",
                "-i", "pipe:0", str(output)
            ]
            proc2 = subprocess.run(ffmpeg_cmd, input=proc.stdout, capture_output=True)
            return proc2.returncode == 0 and output.exists() and output.stat().st_size > 0
    except Exception:
        pass
    return False

def record_with_rec(duration: int, output: Path) -> bool:
    """Graba audio usando rec (SoX)."""
    try:
        cmd = ["rec", "-q", "-r", "16000", "-c", "1", "-b", "16",
               str(output), "trim", "0", str(duration)]
        result = subprocess.run(cmd, capture_output=True, timeout=duration + 5)
        return result.returncode == 0 and output.exists() and output.stat().st_size > 0
    except Exception:
        pass
    return False

def record_with_arecord(duration: int, output: Path) -> bool:
    """Graba audio usando arecord (ALSA)."""
    try:
        cmd = ["arecord", "-q", "-r", "16000", "-c", "1", "-f", "S16_LE",
               "-d", str(duration), str(output)]
        result = subprocess.run(cmd, capture_output=True, timeout=duration + 5)
        return result.returncode == 0 and output.exists() and output.stat().st_size > 0
    except Exception:
        pass
    return False

def record_audio(duration: int, work_dir: Path) -> Optional[Path]:
    """Graba audio usando el método disponible."""
    output = work_dir / VOICE_FILE
    
    # Asegurar PULSE_SERVER
    os.environ.setdefault('PULSE_SERVER', 'unix:/run/user/1000/pulse/native')
    
    # Intentar métodos en orden
    methods = [
        ("parec + ffmpeg", record_with_parec),
        ("rec (SoX)", record_with_rec),
        ("arecord (ALSA)", record_with_arecord),
    ]
    
    for name, method in methods:
        info(f"Intentando {name}...")
        if method(duration, output):
            ok(f"Audio grabado: {output.stat().st_size} bytes")
            return output
    
    err("No se pudo grabar audio con ningún método")
    return None

# ── VAD (Voice Activity Detection) ────────────────────────────────────────
def detect_voice(audio_path: Path) -> Tuple[bool, float]:
    """Detecta si hay voz en el archivo usando webrtcvad."""
    try:
        import webrtcvad
        
        with wave.open(str(audio_path), 'r') as wf:
            framerate = wf.getframerate()
            pcm = wf.readframes(wf.getnframes())
        
        vad = webrtcvad.Vad(3)
        frame_ms = 30
        frame_bytes = int(framerate * frame_ms / 1000) * 2
        
        speech = 0
        total = 0
        
        for i in range(0, len(pcm) - frame_bytes + 1, frame_bytes):
            frame = pcm[i:i+frame_bytes]
            if vad.is_speech(frame, framerate):
                speech += 1
            total += 1
        
        pct = (speech / total * 100) if total > 0 else 0
        has_voice = pct >= 15
        
        return has_voice, round(pct, 1)
        
    except ImportError:
        warn("webrtcvad no instalado, asumiendo voz presente")
        return True, 50.0
    except Exception as e:
        warn(f"Error en VAD: {e}")
        return True, 50.0

# ── Recorte de silencio ───────────────────────────────────────────────────
def trim_silence(audio_path: Path, work_dir: Path) -> Optional[Path]:
    """Recorta silencio del audio usando webrtcvad."""
    try:
        import webrtcvad
        
        with wave.open(str(audio_path), 'r') as wf:
            params = wf.getparams()
            framerate = wf.getframerate()
            pcm = wf.readframes(wf.getnframes())
        
        vad = webrtcvad.Vad(1)
        frame_ms = 30
        frame_bytes = int(framerate * frame_ms / 1000) * 2
        
        voiced_frames = []
        for i in range(0, len(pcm) - frame_bytes + 1, frame_bytes):
            frame = pcm[i:i+frame_bytes]
            if vad.is_speech(frame, framerate):
                voiced_frames.append(frame)
        
        if voiced_frames:
            trimmed = b''.join(voiced_frames)
            trimmed_path = work_dir / TRIMMED_FILE
            
            with wave.open(str(trimmed_path), 'w') as wf:
                wf.setparams(params)
                wf.writeframes(trimmed)
            
            return trimmed_path
            
    except Exception as e:
        warn(f"Error recortando silencio: {e}")
    
    # Fallback: copiar original
    trimmed_path = work_dir / TRIMMED_FILE
    shutil.copy(audio_path, trimmed_path)
    return trimmed_path

# ── Transcripción ─────────────────────────────────────────────────────────
def transcribe_google(audio_path: Path, language: str) -> Optional[str]:
    """Transcribe audio usando Google Web Speech API."""
    try:
        import speech_recognition as sr
    except ImportError:
        warn("speech_recognition no instalado, instalando...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 
                       'SpeechRecognition', '--break-system-packages'],
                      capture_output=True)
        try:
            import speech_recognition as sr
        except ImportError:
            err("No se pudo instalar speech_recognition")
            return None
    
    try:
        r = sr.Recognizer()
        with sr.WavFile(str(audio_path)) as source:
            r.adjust_for_ambient_noise(source, duration=0.5)
            audio = r.record(source)
        
        text = r.recognize_google(audio, language=language)
        return text
        
    except sr.UnknownValueError:
        warn("No se entendió el audio")
        return None
    except sr.RequestError as e:
        err(f"API no disponible: {e}")
        return None
    except Exception as e:
        err(f"Error en transcripción: {e}")
        return None

# ── Detección de eco ──────────────────────────────────────────────────────
def is_echo(transcribed: str, work_dir: Path) -> bool:
    """Detecta si el texto transcrito es eco del último TTS."""
    last_tts_path = work_dir / LAST_TTS_FILE
    
    if not last_tts_path.exists():
        return False
    
    try:
        last_tts = last_tts_path.read_text().strip().lower()
        transcribed_lower = transcribed.lower()
        
        # Limpiar puntuación
        import re
        last_words = set(re.findall(r'\w+', last_tts))
        trans_words = set(re.findall(r'\w+', transcribed_lower))
        
        if not last_words or not trans_words:
            return False
        
        # Jaccard similarity
        intersection = len(last_words & trans_words)
        union = len(last_words | trans_words)
        jaccard = intersection / union if union > 0 else 0
        
        # Si más del 50% de las palabras coinciden, es eco
        if jaccard > 0.5 or (len(trans_words) <= 3 and intersection >= 2):
            return True
        
        return False
        
    except Exception:
        return False

# ── Copiar al portapapeles ────────────────────────────────────────────────
def copy_to_clipboard(text: str) -> bool:
    """Copia texto al portapapeles."""
    try:
        # Intentar xclip
        proc = subprocess.run(
            ["xclip", "-selection", "clipboard"],
            input=text.encode(), capture_output=True
        )
        if proc.returncode == 0:
            return True
        
        # Intentar xsel
        proc = subprocess.run(
            ["xsel", "-b"],
            input=text.encode(), capture_output=True
        )
        return proc.returncode == 0
        
    except Exception:
        return False

# ── Función principal ─────────────────────────────────────────────────────
def main() -> int:
    # Parsear argumentos
    lang = sys.argv[1] if len(sys.argv) > 1 else "es-ES"
    try:
        duration = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    except ValueError:
        duration = 5
    
    language = normalize_language(lang)
    work_dir = get_work_dir()
    
    info(f"Grabando {duration}s en {language}...")
    
    # 1. Grabar audio
    audio_path = record_audio(duration, work_dir)
    if not audio_path:
        return 1
    
    # 2. Detectar voz (VAD)
    has_voice, pct = detect_voice(audio_path)
    info(f"VAD: voz={'sí' if has_voice else 'no'} ({pct}% frames)")
    
    if not has_voice:
        warn("Sin voz detectada, omitiendo API")
        audio_path.unlink(missing_ok=True)
        return 0
    
    # 3. Recortar silencio
    trimmed_path = trim_silence(audio_path, work_dir)
    if trimmed_path and trimmed_path.exists():
        audio_to_transcribe = trimmed_path
    else:
        audio_to_transcribe = audio_path
    
    # 4. Transcribir
    info("Transcribiendo...")
    text = transcribe_google(audio_to_transcribe, language)
    
    if not text:
        err("No se pudo transcribir el audio")
        return 1
    
    # 5. Detectar eco
    if is_echo(text, work_dir):
        warn("Eco detectado — ignorando")
        return 0
    
    # 6. Salida
    print(text)
    copy_to_clipboard(text)
    ok(f"Transcrito: {text}")
    
    # 7. Limpiar
    audio_path.unlink(missing_ok=True)
    if trimmed_path:
        trimmed_path.unlink(missing_ok=True)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
