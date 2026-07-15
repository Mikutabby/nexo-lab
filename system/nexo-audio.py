#!/usr/bin/env python3
"""
nexo-audio.py — Diagnóstico de audio del sistema
==================================================
Versión mejorada en Python con:
- Verificación de PipeWire y WirePlumber
- Estado de dispositivos de audio
- Prueba de reproducción y micrófono
- Soluciones rápidas
- Mejor manejo de errores

Uso:
    nexo-audio.py              → diagnóstico completo
    nexo-audio.py --fix        → intentar reparar
    nexo-audio.py --help       → ayuda
"""

import os
import sys
import subprocess
import tempfile
from pathlib import Path
from typing import List, Tuple

# ── Configuración ──────────────────────────────────────────────────────────
VERSION = "2.0"
HOME = Path.home()
NEXO_DIR = HOME / "nexo-lab" / "nexo-lab"
SAY_SCRIPT = NEXO_DIR / "voice" / "say.sh"

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

def check_service(service_name: str) -> Tuple[bool, str]:
    """Verifica el estado de un servicio."""
    result = run_cmd(["systemctl", "--user", "status", service_name, "--no-pager", "-n", "3"])
    
    if result.returncode == 0:
        for line in result.stdout.split('\n'):
            if 'Active:' in line:
                return True, line.strip()
            if 'Main PID:' in line:
                return True, line.strip()
    
    return False, "No disponible"

def get_audio_devices() -> List[str]:
    """Obtiene la lista de dispositivos de audio."""
    result = run_cmd(["wpctl", "status"])
    
    if result.returncode == 0:
        devices = []
        in_audio = False
        for line in result.stdout.split('\n'):
            if 'Audio' in line:
                in_audio = True
                continue
            if 'Video' in line:
                in_audio = False
                continue
            if in_audio and line.strip():
                devices.append(line.strip())
        return devices
    
    return []

def get_volume() -> str:
    """Obtiene el volumen actual."""
    result = run_cmd(["wpctl", "get-volume", "52"])
    
    if result.returncode == 0:
        return result.stdout.strip()
    
    return "No disponible"

def is_muted() -> bool:
    """Verifica si el audio está muteado."""
    result = run_cmd(["pactl", "list", "sinks"])
    
    if result.returncode == 0:
        for line in result.stdout.split('\n'):
            if 'mute' in line.lower():
                return 'yes' in line.lower() or 'true' in line.lower()
    
    return False

def test_playback() -> bool:
    """Prueba la reproducción de audio."""
    if not SAY_SCRIPT.exists():
        warn("say.sh no encontrado")
        return False
    
    result = run_cmd([str(SAY_SCRIPT), "Prueba de audio"])
    return result.returncode == 0

def test_microphone() -> Tuple[bool, int]:
    """Prueba el micrófono."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        # Grabar 2 segundos
        result = run_cmd([
            "timeout", "2", "parec",
            "--rate=16000", "--channels=1", "--format=s16le"
        ])
        
        if result.returncode == 0 and len(result.stdout) > 1000:
            return True, len(result.stdout)
        
        return False, 0
    except Exception:
        return False, 0
    finally:
        Path(tmp_path).unlink(missing_ok=True)

def fix_audio() -> None:
    """Intenta reparar problemas de audio."""
    info("🔧 Intentando reparar audio...")
    
    # Reiniciar PipeWire
    info("Reiniciando PipeWire...")
    run_cmd(["systemctl", "--user", "restart", "pipewire"])
    
    # Reiniciar WirePlumber
    info("Reiniciando WirePlumber...")
    run_cmd(["systemctl", "--user", "restart", "wireplumber"])
    
    # Establecer volumen
    info("Estableciendo volumen a 80%...")
    run_cmd(["wpctl", "set-volume", "52", "0.8"])
    
    # Desmutear
    info("Desmutear audio...")
    run_cmd(["wpctl", "set-mute", "52", "0"])
    
    ok("Reparaciones aplicadas")

def show_help() -> None:
    """Muestra la ayuda."""
    print(f"""
╔══════════════════════════════════════════════╗
║   🔇 nexo-audio.py v{VERSION}                ║
║   Diagnóstico de audio del sistema          ║
╚══════════════════════════════════════════════╝

USO:
  nexo-audio.py              Diagnóstico completo
  nexo-audio.py --fix        Intentar reparar
  nexo-audio.py --help       Esta ayuda

COMPONENTES:
  - PipeWire
  - WirePlumber
  - Dispositivos de audio
  - Volumen y mute
  - Prueba de reproducción
  - Prueba de micrófono
""")

# ── Main ───────────────────────────────────────────────────────────────────
def main() -> int:
    args = sys.argv[1:]
    
    if "--help" in args or "-h" in args:
        show_help()
        return 0
    
    print()
    print("╔══════════════════════════════════════════════╗")
    print(f"║   🔇 NEXO AUDIO DIAGNÓSTICO v{VERSION}       ║")
    print("╚══════════════════════════════════════════════╝")
    print()
    
    # 1. Estado de PipeWire
    info("📡 PipeWire:")
    active, status = check_service("pipewire")
    if active:
        ok(status)
    else:
        warn(status)
    print()
    
    # 2. Estado de WirePlumber
    info("🔧 WirePlumber:")
    active, status = check_service("wireplumber")
    if active:
        ok(status)
    else:
        warn(status)
    print()
    
    # 3. Dispositivos de audio
    info("🔊 Dispositivos:")
    devices = get_audio_devices()
    if devices:
        for device in devices:
            print(f"  {device}")
    else:
        warn("No se encontraron dispositivos")
    print()
    
    # 4. Volumen actual
    info("🔊 Volumen:")
    volume = get_volume()
    print(f"  {volume}")
    print()
    
    # 5. Mute state
    info("🔇 Mudo:")
    muted = is_muted()
    if muted:
        warn("Audio muteado")
    else:
        ok("Audio no muteado")
    print()
    
    # 6. Prueba de reproducción
    info("▶️  Probando reproducción...")
    if test_playback():
        ok("Audio OK")
    else:
        err("Error en reproducción")
    print()
    
    # 7. Prueba de micrófono
    info("🎤 Probando micrófono (2s)...")
    mic_ok, size = test_microphone()
    if mic_ok:
        ok(f"Micrófono captura audio ({size} bytes)")
    else:
        err("No se pudo grabar")
    print()
    
    # 8. Soluciones rápidas
    info("🔧 Si hay problemas:")
    print("  systemctl --user restart pipewire wireplumber")
    print("  wpctl set-volume 52 0.8")
    print("  wpctl set-mute 52 0")
    
    # Modo fix
    if "--fix" in args:
        print()
        fix_audio()
    
    print()
    return 0

if __name__ == "__main__":
    sys.exit(main())
