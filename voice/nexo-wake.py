#!/usr/bin/env python3
"""
nexo-wake.py — Detección de wake word "nexo"
=============================================
Versión mejorada en Python con:
- Detección de wake word "nexo"
- Modo loop, once y daemon
- VAD (Voice Activity Detection)
- Sensibilidad ajustable
- Uso de RAM en lugar de disco
- Mejor manejo de errores

Uso:
    nexo-wake.py                    → modo loop
    nexo-wake.py once               → escuchar una vez
    nexo-wake.py daemon start|stop  → modo daemon
    nexo-wake.py sensitivity <0-1>  → ajustar sensibilidad
    nexo-wake.py --help             → ayuda
"""

import os
import sys
import signal
import subprocess
import time
import struct
import math
from pathlib import Path
from typing import Optional

# ── Configuración ──────────────────────────────────────────────────────────
VERSION = "2.0"
HOME = Path.home()
PIDFILE = Path("/tmp/nexo-wake.pid")
LOGFILE = Path("/tmp/nexo-wake.log")
SENSITIVITY = 0.6
DURATION = 2

# Usar tmpfs si existe, sino /tmp
if Path("/dev/shm").exists() and os.access("/dev/shm", os.W_OK):
    TEMP_BASE = Path("/dev/shm")
elif Path("/run").exists() and os.access("/run", os.W_OK):
    TEMP_BASE = Path("/run")
else:
    TEMP_BASE = Path("/tmp")

# ── Colores ────────────────────────────────────────────────────────────────
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'

def info(msg: str) -> None:
    print(f"{Colors.BLUE}ℹ️  {Colors.NC} {msg}")

def ok(msg: str) -> None:
    print(f"{Colors.GREEN}✅{Colors.NC} {msg}")

def warn(msg: str) -> None:
    print(f"{Colors.YELLOW}⚠️  {Colors.NC} {msg}")

def err(msg: str) -> None:
    print(f"{Colors.RED}❌{Colors.NC} {msg}")

# ── Utilidades ─────────────────────────────────────────────────────────────
def run_cmd(cmd: list, check: bool = False) -> subprocess.CompletedProcess:
    """Ejecuta un comando y retorna el resultado."""
    try:
        return subprocess.run(cmd, capture_output=True, text=True)
    except Exception as e:
        warn(f"Error ejecutando {cmd[0]}: {e}")
        return subprocess.CompletedProcess(cmd, 1, "", str(e))

def log(message: str) -> None:
    """Registra mensaje en el log."""
    try:
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        with open(LOGFILE, "a") as f:
            f.write(f"[{timestamp}] {message}\n")
    except Exception:
        pass

def check_wake_word(text: str) -> bool:
    """Verifica si el texto contiene la wake word 'nexo'."""
    lower_text = text.lower()
    
    # 1. Exact match
    if "nexo" in lower_text:
        return True
    
    # 2. Fuzzy match (difflib)
    try:
        import difflib
        targets = ['nexo', 'neco', 'nejo', 'necho', 'neto', 'deco', 'mecso']
        words = lower_text.split()
        
        for word in words:
            for target in targets:
                ratio = difflib.SequenceMatcher(None, word, target).ratio()
                if ratio >= SENSITIVITY:
                    return True
    except Exception:
        pass
    
    return False

def detect_voice(raw_file: Path) -> bool:
    """Detecta si hay voz en el archivo raw PCM."""
    if not raw_file.exists() or raw_file.stat().st_size == 0:
        return False
    
    try:
        with open(raw_file, 'rb') as f:
            data = f.read()
        
        # Dividir en frames de 30ms (480 samples a 16kHz)
        frame_size = 480  # 30ms
        frames = [data[i:i+frame_size*2] for i in range(0, len(data), frame_size*2)]
        
        if not frames:
            return False
        
        # Calcular RMS de cada frame, contar frames con voz
        voice_frames = 0
        for frame in frames:
            if len(frame) < frame_size * 2:
                continue
            samples = struct.unpack('<' + 'h' * (len(frame)//2), frame)
            rms = math.sqrt(sum(s*s for s in samples) / len(samples)) if samples else 0
            if rms > 300:  # Threshold de silencio
                voice_frames += 1
        
        # Si más del 10% de los frames tienen voz, hay actividad
        return voice_frames > max(1, len(frames) * 0.1)
        
    except Exception:
        return False

def record_and_check() -> tuple[bool, str]:
    """Graba audio y verifica si hay wake word."""
    raw_file = TEMP_BASE / f"nexo-wake-raw-{os.getpid()}.raw"
    wav_file = TEMP_BASE / f"nexo-wake-{os.getpid()}.wav"
    
    try:
        # 1. Capturar audio RAW
        result = run_cmd([
            "timeout", str(DURATION), "parec",
            "--rate=16000", "--channels=1", "--format=s16le"
        ])
        
        if result.returncode == 0 and result.stdout:
            raw_file.write_bytes(result.stdout.encode() if isinstance(result.stdout, str) else result.stdout)
        else:
            # Fallback: rec (SoX) directo a WAV
            run_cmd([
                "rec", "-q", "-r", "16000", "-c", "1", "-b", "16",
                str(wav_file), "trim", "0", str(DURATION)
            ])
        
        # 2. VAD: detectar si hay voz
        has_voice = False
        
        if raw_file.exists() and raw_file.stat().st_size > 0:
            has_voice = detect_voice(raw_file)
            raw_file.unlink(missing_ok=True)
        elif wav_file.exists() and wav_file.stat().st_size > 5000:
            has_voice = True
        
        if not has_voice:
            wav_file.unlink(missing_ok=True)
            return False, ""
        
        # 3. Convertir raw a WAV si es necesario
        if not wav_file.exists() and raw_file.exists():
            run_cmd([
                "ffmpeg", "-y", "-f", "s16le", "-ar", "16000", "-ac", "1",
                "-i", str(raw_file), str(wav_file)
            ])
        
        if not wav_file.exists() or wav_file.stat().st_size == 0:
            wav_file.unlink(missing_ok=True)
            return False, ""
        
        # 4. Transcribir
        result = run_cmd([
            sys.executable, "-c", f"""
import speech_recognition as sr
r = sr.Recognizer()
with sr.WavFile('{wav_file}') as source:
    r.adjust_for_ambient_noise(source, duration=0.3)
    audio = r.record(source)
try:
    text = r.recognize_google(audio, language='es-ES')
    print(text)
except:
    pass
"""
        ])
        
        wav_file.unlink(missing_ok=True)
        
        text = result.stdout.strip()
        if not text:
            return False, ""
        
        return check_wake_word(text), text
        
    except Exception as e:
        raw_file.unlink(missing_ok=True)
        wav_file.unlink(missing_ok=True)
        return False, ""

def cmd_once() -> int:
    """Escucha una vez."""
    info(f"🎤 Escuchando... ({DURATION}s)")
    
    found, text = record_and_check()
    
    if text:
        info(f"📝 Transcripción: {text}")
    
    if found:
        ok(f"Wake word detectada: '{text}'")
        print(text)
        return 0
    else:
        err("No se detectó wake word")
        return 1

def cmd_loop() -> None:
    """Modo loop continuo."""
    info("🔊 Nexo Wake — Modo loop (sin escritura a disco)")
    info(f"   Escuchando cada {DURATION}s...")
    info(f"   Wake word: 'nexo' (sensibilidad: {SENSITIVITY})")
    info(f"   Temp: {TEMP_BASE} (RAM-based)")
    info(f"   PID: {os.getpid()}")
    print()
    
    while True:
        try:
            found, text = record_and_check()
            
            if found and text:
                log(f"🎤 Wake word: {text}")
                ok(f"Wake word detectada: {text}")
                
                # Extraer comando después de "nexo"
                command = text.lower().replace("nexo", "").strip()
                
                if command:
                    log(f"🗣️ Comando: {command}")
                    info(f"🗣️ Procesando: {command}")
                else:
                    log("⏳ Esperando comando completo...")
                    info("⏳ Hablá tu comando...")
            
            time.sleep(0.5)
            
        except KeyboardInterrupt:
            print()
            info("Daemon detenido")
            break

def cmd_daemon(action: str) -> None:
    """Modo daemon."""
    if action == "start":
        if PIDFILE.exists():
            try:
                pid = int(PIDFILE.read_text().strip())
                os.kill(pid, 0)
                err(f"nexo-wake ya está corriendo (PID: {pid})")
                return
            except (ProcessLookupError, ValueError):
                pass
        
        info("Iniciando nexo-wake daemon...")
        
        proc = subprocess.Popen(
            [sys.executable, str(Path(__file__)), "loop"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        
        PIDFILE.write_text(str(proc.pid))
        ok(f"Daemon iniciado (PID: {proc.pid})")
        
    elif action == "stop":
        if not PIDFILE.exists():
            err("nexo-wake no está corriendo")
            return
        
        try:
            pid = int(PIDFILE.read_text().strip())
            os.kill(pid, signal.SIGTERM)
            time.sleep(0.5)
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        except ProcessLookupError:
            pass
        
        PIDFILE.unlink(missing_ok=True)
        ok("Daemon detenido")
        
    elif action == "status":
        if PIDFILE.exists():
            try:
                pid = int(PIDFILE.read_text().strip())
                os.kill(pid, 0)
                ok(f"nexo-wake: activo (PID: {pid})")
                return
            except (ProcessLookupError, ValueError):
                pass
        
        info("nexo-wake: inactivo")
        
    else:
        err(f"Uso: nexo-wake daemon start|stop|status")

def show_help() -> None:
    """Muestra la ayuda."""
    print(f"""
╔══════════════════════════════════════════════╗
║   🔊 nexo-wake.py v{VERSION}                 ║
║   Detección de wake word "nexo"             ║
╚══════════════════════════════════════════════╝

USO:
  nexo-wake.py                    Modo loop (escucha continua)
  nexo-wake.py once               Escucha una vez
  nexo-wake.py daemon start|stop  Modo daemon
  nexo-wake.py sensitivity <0-1>  Ajustar sensibilidad
  nexo-wake.py --help             Esta ayuda

CONFIGURACIÓN:
  Sensibilidad: {SENSITIVITY}
  Duración: {DURATION}s
  Temp: {TEMP_BASE} (RAM-based)
""")

# ── Main ───────────────────────────────────────────────────────────────────
def main() -> int:
    args = sys.argv[1:]
    
    if "--help" in args or "-h" in args:
        show_help()
        return 0
    
    if not args:
        cmd_loop()
        return 0
    
    command = args[0]
    
    if command in ["once", "one-shot"]:
        return cmd_once()
    elif command in ["loop", "listen"]:
        cmd_loop()
    elif command == "daemon":
        if len(args) < 2:
            err("Uso: nexo-wake.py daemon start|stop|status")
            return 1
        cmd_daemon(args[1])
    elif command in ["sensitivity", "sens"]:
        if len(args) < 2:
            info(f"Sensibilidad actual: {SENSITIVITY}")
        else:
            try:
                SENSITIVITY = float(args[1])
                ok(f"Sensibilidad ajustada a: {SENSITIVITY}")
            except ValueError:
                err("Valor inválido")
                return 1
    else:
        cmd_loop()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
