#!/usr/bin/env python3
"""
temp-cancel.py — Cancelar apagado por temperatura
==================================================
Versión mejorada en Python con:
- Cancelación de apagado programado
- Limpieza de archivos de estado
- Información de temperatura actual
- Mejor manejo de errores

Uso:
    temp-cancel.py              → cancelar apagado
    temp-cancel.py --help       → ayuda
"""

import os
import sys
import subprocess
from pathlib import Path

# ── Configuración ──────────────────────────────────────────────────────────
VERSION = "2.0"
COOLDOWN_FILE = Path("/tmp/temp-monitor-cooldown")
STATUS_FILE = Path("/tmp/temp-monitor-status")

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

def read_temperature() -> str:
    """Lee la temperatura actual."""
    thermal1 = Path("/sys/class/thermal/thermal_zone1/temp")
    thermal0 = Path("/sys/class/thermal/thermal_zone0/temp")
    
    for thermal_file in [thermal1, thermal0]:
        if thermal_file.exists():
            try:
                temp_raw = thermal_file.read_text().strip()
                temp = int(temp_raw) / 1000
                return f"{temp:.1f}°C"
            except Exception:
                pass
    
    return "desconocida"

def speak(text: str) -> None:
    """Habla por los parlantes."""
    try:
        subprocess.run(["spd-say", text], capture_output=True)
    except Exception:
        pass

def show_help() -> None:
    """Muestra la ayuda."""
    print(f"""
╔══════════════════════════════════════════════╗
║   🛑 temp-cancel.py v{VERSION}               ║
║   Cancelar apagado por temperatura          ║
╚══════════════════════════════════════════════╝

USO:
  temp-cancel.py              Cancelar apagado
  temp-cancel.py --help       Esta ayuda

DESCRIPCIÓN:
  Cancela un apagado programado por temperatura
  y limpia los archivos de estado.
""")

# ── Main ───────────────────────────────────────────────────────────────────
def main() -> int:
    args = sys.argv[1:]
    
    if "--help" in args or "-h" in args:
        show_help()
        return 0
    
    # Cancelar apagado
    info("Cancelando apagado programado...")
    
    # Cancelar rtcwake
    run_cmd(["sudo", "rtcwake", "-m", "disable"])
    
    # Limpiar wakealarm
    try:
        with open("/sys/class/rtc/rtc0/wakealarm", "w") as f:
            f.write("0")
    except Exception:
        pass
    
    # Eliminar archivos de estado
    COOLDOWN_FILE.unlink(missing_ok=True)
    STATUS_FILE.unlink(missing_ok=True)
    
    # Obtener temperatura actual
    temp = read_temperature()
    
    ok(f"Apagado cancelado. Temperatura actual: {temp}")
    speak("Apagado cancelado")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
