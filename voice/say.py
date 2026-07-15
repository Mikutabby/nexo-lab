#!/usr/bin/env python3
"""
say.py — Text-to-Speech para Nexo
==================================
Versión mejorada en Python con:
- Múltiples motores: Piper (offline), gTTS (cloud), espeak-ng (fallback)
- Preprocesamiento de texto (markdown, URLs, emojis)
- Soporte multi-idioma
- Velocidad adjustable
- Mejor manejo de errores

Uso:
    say.py "texto"           → español
    say.py en "text"         → inglés
    say.py -s "texto lento"  → más lento
    echo "texto" | say.py    → pipe
"""

import os
import sys
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

# ── Configuración ──────────────────────────────────────────────────────────
SHM_DIR = Path("/dev/shm/nexo-tts")
FALLBACK_DIR = Path(tempfile.gettempdir()) / "nexo-tts"

# Piper
PIPER_BIN = "piper"
PIPER_VOICES_DIR = Path.home() / ".local" / "share" / "piper-voices"
PIPER_BASE_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0"
PIPER_VOICES = {
    'es': ('es_ES-davefx-medium', f"{PIPER_BASE_URL}/es/es_ES/davefx/medium/es_ES-davefx-medium"),
    'en': ('en_GB-alan-medium', f"{PIPER_BASE_URL}/en/en_GB/alan/medium/en_GB-alan-medium"),
}

# ── Colores ────────────────────────────────────────────────────────────────
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'

def info(msg: str) -> None:
    print(f"{Colors.BLUE}🔊{Colors.NC} {msg}", file=sys.stderr)

def ok(msg: str) -> None:
    print(f"{Colors.GREEN}✓{Colors.NC} {msg}", file=sys.stderr)

def warn(msg: str) -> None:
    print(f"{Colors.YELLOW}⚠{Colors.NC} {msg}", file=sys.stderr)

def err(msg: str) -> None:
    print(f"{Colors.RED}✗{Colors.NC} {msg}", file=sys.stderr)

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

# ── Preprocesamiento de texto ─────────────────────────────────────────────
def clean_text(text: str) -> str:
    """Limpia texto markdown y formatea para TTS."""
    if not text.strip():
        return ""
    
    # 1. URLs de markdown: [texto](url) -> texto
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', 
        lambda m: f'Link a {m.group(1)}' if 'http' in m.group(2) else m.group(1), text)
    
    # 2. URLs sueltas -> dominio legible
    text = re.sub(r'https?://([^\s<>\[\]()]+)',
        lambda m: m.group(1).replace('www.', '').rstrip('/').split('/')[0] 
        if '.' in m.group(1).split('/')[0] else m.group(1).split('/')[0] + '.com', text)
    
    # 3. Bloques de codigo -> solo texto interior
    text = re.sub(r'```\w*\n?([\s\S]*?)```', r'\1', text)
    
    # 4. Codigo inline -> solo texto
    text = re.sub(r'`([^`]+)`', r'\1', text)
    
    # 5. Negrita -> texto
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'__([^_]+)__', r'\1', text)
    
    # 6. Cursiva -> texto
    text = re.sub(r'(?<!\*)\*([^*\s][^*]*?)\*(?!\*)', r'\1', text)
    text = re.sub(r'(?<!\w)_([^_\n]+?)_(?!\w)', r'\1', text)
    
    # 7. Tachado -> texto
    text = re.sub(r'~~([^~]+)~~', r'\1', text)
    
    # 8. Encabezados -> quitar
    text = re.sub(r'^\s*#{1,6}\s+', '', text, flags=re.MULTILINE)
    
    # 9. Citas -> quitar
    text = re.sub(r'^\s*>\s?', '', text, flags=re.MULTILINE)
    
    # 10. Listas -> quitar
    text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+[.)]\s+', '', text, flags=re.MULTILINE)
    
    # 11. HTML tags -> quitar
    text = re.sub(r'<[^>]+>', '', text)
    
    # 12. Lineas decorativas -> quitar
    text = re.sub(r'^\s*[-=]{3,}\s*$', '', text, flags=re.MULTILINE)
    
    # 13. Emojis -> descriptivos
    emoji_map = {
        '✅': 'check, ', '❌': 'error, ', '⚠️': 'advertencia, ',
        '🔥': 'caliente, ', '🎵': 'musica, ', '🎶': 'musica, ',
        '🔴': 'rojo, ', '🟢': 'verde, ', '⚡': 'rayo, ',
        '💡': 'idea, ', '🔧': 'herramienta, ', '🚀': 'lanzamiento, ',
        '📋': 'lista, ', '⭐': 'estrella, ', '🔒': 'candado, ',
        '👤': 'usuario, ',
    }
    for emoji, replacement in emoji_map.items():
        text = text.replace(emoji, replacement)
    
    # 14. Lineas vacias multiples -> una sola
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()

# ── Piper TTS ──────────────────────────────────────────────────────────────
def ensure_piper_model(lang: str) -> Optional[Path]:
    """Asegura que el modelo Piper exista, descargándolo si es necesario."""
    if lang not in PIPER_VOICES:
        return None
    
    model_name, model_url = PIPER_VOICES[lang]
    model_path = PIPER_VOICES_DIR / f"{model_name}.onnx"
    json_path = PIPER_VOICES_DIR / f"{model_name}.onnx.json"
    
    if model_path.exists() and json_path.exists():
        return model_path
    
    # Descargar modelo
    PIPER_VOICES_DIR.mkdir(parents=True, exist_ok=True)
    info(f"Descargando voz Piper: {model_name} (~60MB)...")
    
    for suffix in [".onnx", ".onnx.json"]:
        target = PIPER_VOICES_DIR / f"{model_name}{suffix}"
        url = f"{model_url}{suffix}"
        if not target.exists():
            try:
                subprocess.run(
                    ["wget", "-q", "--show-progress", "-O", str(target), url],
                    check=True, capture_output=True
                )
            except Exception as e:
                err(f"Error descargando {suffix}: {e}")
                target.unlink(missing_ok=True)
                return None
    
    ok(f"Voz descargada: {model_name}")
    return model_path

def speak_piper(text: str, lang: str, speed: str) -> bool:
    """Habla usando Piper TTS (offline, neural)."""
    model_path = ensure_piper_model(lang)
    if not model_path:
        return False
    
    try:
        length_scale = "1.3" if speed == "slow" else "1.0"
        work_dir = get_work_dir()
        wav_file = work_dir / "piper-output.wav"
        text_file = work_dir / "piper-input.txt"
        
        # Escribir texto a archivo temporal
        text_file.write_text(text)
        
        # Piper genera WAV desde archivo
        piper_cmd = [
            PIPER_BIN,
            "--model", str(model_path),
            "--input_file", str(text_file),
            "--output_file", str(wav_file),
            "--length-scale", length_scale
        ]
        
        # Ejecutar Piper
        piper_proc = subprocess.run(
            piper_cmd, capture_output=True
        )
        
        # Limpiar archivo temporal
        text_file.unlink(missing_ok=True)
        
        if piper_proc.returncode != 0 or not wav_file.exists():
            return False
        
        # Reproducir WAV con aplay
        aplay_proc = subprocess.run(
            ["aplay", str(wav_file)],
            capture_output=True
        )
        
        wav_file.unlink(missing_ok=True)
        return aplay_proc.returncode == 0
        
    except Exception as e:
        warn(f"Error con Piper: {e}")
        return False

# ── gTTS ───────────────────────────────────────────────────────────────────
def speak_gtts(text: str, lang: str) -> bool:
    """Habla usando gTTS (Google WaveNet, cloud)."""
    try:
        from gtts import gTTS
    except ImportError:
        warn("gTTS no instalado, instalando...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'gTTS'],
                      capture_output=True)
        try:
            from gtts import gTTS
        except ImportError:
            return False
    
    try:
        work_dir = get_work_dir()
        out_file = work_dir / "nexo-tts.mp3"
        
        tts = gTTS(text, lang=lang)
        tts.save(str(out_file))
        
        # Reproducir con mpg123
        result = subprocess.run(
            ["mpg123", "--no-gapless", "-q", str(out_file)],
            capture_output=True
        )
        
        out_file.unlink(missing_ok=True)
        return result.returncode == 0
        
    except Exception as e:
        warn(f"Error con gTTS: {e}")
        return False

# ── espeak-ng ──────────────────────────────────────────────────────────────
def speak_espeak(text: str, lang: str, speed: str) -> bool:
    """Habla usando espeak-ng (fallback offline)."""
    voice_map = {'es': 'es-419', 'en': 'en-us'}
    voice = voice_map.get(lang, lang)
    speed_val = "120" if speed == "slow" else "155"
    
    try:
        result = subprocess.run(
            ["espeak-ng", "-v", voice, "-s", speed_val, text],
            capture_output=True
        )
        return result.returncode == 0
    except Exception:
        return False

# ── Guardar último TTS ────────────────────────────────────────────────────
def save_last_tts(text: str, work_dir: Path) -> None:
    """Guarda el último texto hablado para detección de eco."""
    try:
        last_tts_file = work_dir / "nexo-last-tts.txt"
        last_tts_file.write_text(text)
    except Exception:
        pass

# ── Función principal ─────────────────────────────────────────────────────
def main() -> int:
    # Activar venv si existe
    venv_path = Path.home() / ".nexo-venv" / "bin" / "activate"
    if venv_path.exists():
        try:
            subprocess.run(["bash", "-c", f"source {venv_path}"], capture_output=True)
        except Exception:
            pass
    
    # Parsear argumentos
    lang = "es"
    speed = "normal"
    text_parts = []
    
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg in ['es', 'en']:
            lang = arg
        elif arg == '-s':
            speed = "slow"
        else:
            text_parts.append(arg)
        i += 1
    
    # Leer de stdin si no hay texto
    if text_parts:
        raw_text = ' '.join(text_parts)
    else:
        raw_text = sys.stdin.read().strip()
    
    if not raw_text:
        return 0
    
    # Preprocesar texto
    text = clean_text(raw_text)
    if not text:
        text = raw_text
    
    work_dir = get_work_dir()
    
    # Intentar motores en orden
    info(f"Hablando en {lang}...")
    
    # 1. Piper (offline, neural)
    if speak_piper(text, lang, speed):
        save_last_tts(text, work_dir)
        ok("Piper TTS")
        return 0
    
    # 2. gTTS (cloud)
    if speak_gtts(text, lang):
        save_last_tts(text, work_dir)
        ok("gTTS")
        return 0
    
    # 3. espeak-ng (fallback)
    if speak_espeak(text, lang, speed):
        save_last_tts(text, work_dir)
        ok("espeak-ng")
        return 0
    
    err("No se pudo reproducir audio con ningún motor")
    return 1

if __name__ == "__main__":
    sys.exit(main())
