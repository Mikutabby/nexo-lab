#!/usr/bin/env python3
"""
check-identity.py — Verificación de identidad
===============================================
Versión mejorada en Python con:
- Reconocimiento facial
- Almacenamiento de resultado con timestamp
- Mejor manejo de errores

Uso:
    check-identity.py              → verificar identidad
    check-identity.py --help       → ayuda
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

# ── Configuración ──────────────────────────────────────────────────────────
VERSION = "2.0"
HOME = Path.home()
IDENTITY_FILE = Path("/tmp/opencode-identity.json")
SCRIPT_DIR = HOME / ".local" / "bin"

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

def save_identity(identity: str) -> None:
    """Guarda la identidad con timestamp."""
    data = {
        "identity": identity,
        "timestamp": int(datetime.now().timestamp())
    }
    
    try:
        IDENTITY_FILE.write_text(json.dumps(data))
    except Exception as e:
        warn(f"Error guardando identidad: {e}")

def get_stored_identity() -> dict:
    """Obtiene la identidad almacenada."""
    if not IDENTITY_FILE.exists():
        return {"identity": "unknown", "timestamp": 0}
    
    try:
        return json.loads(IDENTITY_FILE.read_text())
    except Exception:
        return {"identity": "unknown", "timestamp": 0}

# ── Funciones principales ──────────────────────────────────────────────────
def check_identity() -> str:
    """Verifica quién está frente a la PC."""
    face_script = SCRIPT_DIR / "face-recognize.py"
    
    if not face_script.exists():
        warn("face-recognize.py no encontrado")
        return "unknown"
    
    result = run_cmd([str(face_script), "whoami"])
    
    if result.returncode != 0:
        warn(f"Error ejecutando face-recognize.py: {result.stderr}")
        return "unknown"
    
    # Obtener primera línea
    first_line = result.stdout.strip().split('\n')[0] if result.stdout.strip() else ""
    
    if first_line == "miku":
        return "miku"
    elif first_line == "unknown":
        return "unknown"
    elif first_line == "no_face":
        return "nobody"
    else:
        return "unknown"

def show_help() -> None:
    """Muestra la ayuda."""
    print(f"""
╔══════════════════════════════════════════════╗
║   👤 check-identity.py v{VERSION}            ║
║   Verificación de identidad                 ║
╚══════════════════════════════════════════════╝

USO:
  check-identity.py              Verificar identidad
  check-identity.py --help       Esta ayuda

SALIDA:
  - "miku"       → usuario conocido
  - "unknown"    → usuario desconocido
  - "nobody"     → nadie detectado

ARCHIVO DE ESTADO:
  {IDENTITY_FILE}
""")

# ── Main ───────────────────────────────────────────────────────────────────
def main() -> int:
    args = sys.argv[1:]
    
    if "--help" in args or "-h" in args:
        show_help()
        return 0
    
    # Verificar identidad
    identity = check_identity()
    
    # Guardar resultado
    save_identity(identity)
    
    # Imprimir resultado
    print(identity)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
