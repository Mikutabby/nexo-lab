#!/usr/bin/env python3
"""
nexo-daemon.py — Asistente de voz autónomo
============================================
Versión mejorada en Python con:
- Escucha, procesa y responde por voz
- Wake word detection
- Modo foreground y background
- Rotación de logs
- Mejor manejo de errores

Uso:
    nexo-daemon.py start      → iniciar en background
    nexo-daemon.py stop       → detener
    nexo-daemon.py status     → estado
    nexo-daemon.py foreground → ejecutar en primer plano
    nexo-daemon.py --help     → ayuda
"""

import os
import sys
import signal
import subprocess
import time
from pathlib import Path
from typing import Optional

# ── Configuración ──────────────────────────────────────────────────────────
VERSION = "2.0"
HOME = Path.home()

# Usar /dev/shm (RAM) en vez de /tmp (disco)
SHM_DIR = Path("/dev/shm/nexo-daemon")
try:
    SHM_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    SHM_DIR = Path("/tmp")

PIDFILE = SHM_DIR / "nexo-daemon.pid"
LOGFILE = SHM_DIR / "nexo-daemon.log"
VENV = HOME / ".nexo-venv"
NEXO_DIR = HOME / "nexo-lab" / "nexo-lab"
VOICE_SCRIPT = NEXO_DIR / "voice" / "voice.sh"
BRAIN_SCRIPT = NEXO_DIR / "brain" / "nexo-brain.py"
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

def log(message: str) -> None:
    """Registra mensaje en el log."""
    try:
        # Rotar log si es muy largo
        if LOGFILE.exists():
            lines = LOGFILE.read_text().count('\n')
            if lines > 1000:
                content = LOGFILE.read_text().split('\n')
                LOGFILE.write_text('\n'.join(content[-500:]))
        
        # Escribir log
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        with open(LOGFILE, "a") as f:
            f.write(f"[{timestamp}] {message}\n")
    except Exception:
        pass

def ensure_venv() -> None:
    """Activa el virtual environment si existe."""
    venv_activate = VENV / "bin" / "activate"
    if venv_activate.exists():
        try:
            # Esto no funciona directamente en Python, pero es una referencia
            pass
        except Exception:
            pass

def is_running() -> bool:
    """Verifica si el daemon está corriendo."""
    if not PIDFILE.exists():
        return False
    
    try:
        pid = int(PIDFILE.read_text().strip())
        os.kill(pid, 0)  # Verificar si el proceso existe
        return True
    except (ProcessLookupError, ValueError):
        return False

def get_pid() -> Optional[int]:
    """Obtiene el PID del daemon."""
    if not PIDFILE.exists():
        return None
    
    try:
        return int(PIDFILE.read_text().strip())
    except ValueError:
        return None

# ── Funciones principales ──────────────────────────────────────────────────
def cmd_foreground() -> None:
    """Ejecuta el daemon en primer plano."""
    ensure_venv()
    log("🔷 Nexo Daemon iniciado")
    
    print("🔷 Nexo Daemon — asistente de voz autónomo")
    print("   Decí 'nexo' seguido de tu comando")
    print(f"   Log: {LOGFILE}")
    print()
    
    while True:
        try:
            print("🎤 [Enter] para hablar, o escribí 'texto: <comando>' para teclear:")
            user_input = input().strip()
            
            if user_input:
                if user_input.lower().startswith("texto:"):
                    text = user_input[6:].strip()
                else:
                    text = user_input
            else:
                # Grabar audio
                result = run_cmd([str(VOICE_SCRIPT), "es", "5"])
                text = result.stdout.strip() if result.returncode == 0 else ""
            
            if text:
                print(f"📝 Tú: {text}")
                log(f"Comando: {text}")
                
                # Verificar wake word
                lower_text = text.lower()
                if "nexo" in lower_text:
                    # Extraer comando después de "nexo"
                    cmd = lower_text.split("nexo", 1)[1].strip()
                    if not cmd:
                        # Sin comando inline, grabar de nuevo
                        print("🎤 Decí tu comando...")
                        result = run_cmd([str(VOICE_SCRIPT), "es", "5"])
                        cmd = result.stdout.strip() if result.returncode == 0 else ""
                else:
                    cmd = text
                
                if cmd:
                    print(f"🤖 Procesando: {cmd}")
                    log(f"Procesando: {cmd}")
                    
                    # Ejecutar brain
                    result = run_cmd([sys.executable, str(BRAIN_SCRIPT), cmd])
                    response = result.stdout.strip() if result.returncode == 0 else "Error procesando comando"
                    
                    print(f"🤖 Nexo: {response}")
                    log(f"Respuesta: {response}")
            
            time.sleep(1)
            
        except KeyboardInterrupt:
            print()
            info("Daemon detenido")
            break
        except Exception as e:
            warn(f"Error: {e}")
            time.sleep(1)

def cmd_start() -> None:
    """Inicia el daemon en background."""
    if is_running():
        pid = get_pid()
        err(f"Nexo Daemon ya está corriendo (PID: {pid})")
        return
    
    info("Iniciando Nexo Daemon...")
    
    # Iniciar en background
    proc = subprocess.Popen(
        [sys.executable, str(Path(__file__)), "foreground"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True
    )
    
    # Guardar PID
    PIDFILE.write_text(str(proc.pid))
    
    ok(f"Nexo Daemon iniciado (PID: {proc.pid})")
    info("Decí 'nexo' seguido de tu comando")

def cmd_stop() -> None:
    """Detiene el daemon."""
    if not is_running():
        err("Nexo Daemon no está corriendo")
        return
    
    pid = get_pid()
    if pid:
        try:
            os.kill(pid, signal.SIGTERM)
            time.sleep(0.5)
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        except ProcessLookupError:
            pass
    
    PIDFILE.unlink(missing_ok=True)
    ok("Nexo Daemon detenido")

def cmd_status() -> None:
    """Muestra el estado del daemon."""
    if is_running():
        pid = get_pid()
        ok(f"Nexo Daemon: activo (PID: {pid})")
    else:
        info("Nexo Daemon: inactivo")

def show_help() -> None:
    """Muestra la ayuda."""
    print(f"""
╔══════════════════════════════════════════════╗
║   🔷 nexo-daemon.py v{VERSION}               ║
║   Asistente de voz autónomo                 ║
╚══════════════════════════════════════════════╝

USO:
  nexo-daemon.py start      Iniciar en background
  nexo-daemon.py stop       Detener
  nexo-daemon.py status     Mostrar estado
  nexo-daemon.py foreground Ejecutar en primer plano (debug)
  nexo-daemon.py --help     Esta ayuda

DESPUÉS DE INICIAR:
  Decí 'nexo' seguido de tu comando.
  Ej: 'nexo qué hora es', 'nexo abre firefox'

ARCHIVOS:
  PID: {PIDFILE}
  Log: {LOGFILE}
""")

# ── Main ───────────────────────────────────────────────────────────────────
def main() -> int:
    args = sys.argv[1:]
    
    if "--help" in args or "-h" in args:
        show_help()
        return 0
    
    if not args:
        show_help()
        return 0
    
    command = args[0]
    
    if command == "start":
        cmd_start()
    elif command == "stop":
        cmd_stop()
    elif command == "status":
        cmd_status()
    elif command == "foreground":
        cmd_foreground()
    else:
        err(f"Comando desconocido: {command}")
        show_help()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
