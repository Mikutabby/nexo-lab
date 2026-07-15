#!/usr/bin/env python3
"""
nexo-dryrun.py — Ejecución segura de comandos destructivos
==========================================================
Versión mejorada en Python con:
- Ejecución segura de comandos
- Modo dry-run
- Confirmación antes de ejecutar
- Logging de acciones
- Mejor manejo de errores

Uso:
    nexo-dryrun.py <comando> [args...]     → ejecutar comando
    nexo-dryrun.py --dry-run <comando>     → modo dry-run
    nexo-dryrun.py --summary               → mostrar resumen
    nexo-dryrun.py --help                  → ayuda
"""

import os
import sys
import subprocess
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Optional

# ── Configuración ──────────────────────────────────────────────────────────
VERSION = "2.0"
HOME = Path.home()
LOG_DIR = HOME / ".nexo-memory" / "log"
LOG_FILE = LOG_DIR / "dryrun.log"

# Variables de entorno
DRY_RUN = os.environ.get("DRY_RUN", "0") == "1"
NON_INTERACTIVE = os.environ.get("NON_INTERACTIVE", "0") == "1"

# ── Colores ────────────────────────────────────────────────────────────────
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'

def info(msg: str) -> None:
    print(f"{Colors.BLUE}[DRY-RUN]{Colors.NC} {msg}")

def ok(msg: str) -> None:
    print(f"{Colors.GREEN}[OK]{Colors.NC} {msg}")

def warn(msg: str) -> None:
    print(f"{Colors.YELLOW}[WARN]{Colors.NC} {msg}")

def err(msg: str) -> None:
    print(f"{Colors.RED}[ERR]{Colors.NC} {msg}")

def show(msg: str) -> None:
    print(f"{Colors.CYAN}[CMD]{Colors.NC} {msg}")

# ── Logging ────────────────────────────────────────────────────────────────
def setup_logging() -> None:
    """Configura el logging."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        filename=str(LOG_FILE),
        level=logging.INFO,
        format='[%(asctime)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def log_action(level: str, message: str) -> None:
    """Registra una acción en el log."""
    try:
        logging.log(getattr(logging, level, logging.INFO), message)
    except Exception:
        pass

# ── Funciones principales ──────────────────────────────────────────────────
def run_command(cmd: List[str], dry_run: bool = False) -> int:
    """Ejecuta un comando o lo muestra en modo dry-run."""
    if dry_run:
        show(f"DRY-RUN: {' '.join(cmd)}")
        log_action("INFO", f"DRY_RUN: {' '.join(cmd)}")
        return 0
    
    # Ejecutar el comando real
    log_action("INFO", f"EXEC: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd)
        
        if result.returncode == 0:
            ok(f"Ejecutado: {' '.join(cmd)}")
        else:
            err(f"Error {result.returncode}: {' '.join(cmd)}")
        
        return result.returncode
        
    except Exception as e:
        err(f"Error ejecutando: {e}")
        return 1

def confirm_and_run(message: str, cmd: List[str], dry_run: bool = False) -> int:
    """Pide confirmación antes de ejecutar un comando."""
    if dry_run:
        show(f"DRY-RUN: {' '.join(cmd)}")
        info(f"Confirmación omitida (dry-run): {message}")
        log_action("INFO", f"DRY_RUN: {' '.join(cmd)} (msg: {message})")
        return 0
    
    if NON_INTERACTIVE:
        warn(f"Modo no-interactivo: ejecutando sin confirmar: {message}")
        log_action("WARNING", f"AUTO: {' '.join(cmd)} (msg: {message})")
        return run_command(cmd)
    
    # Mostrar comando a ejecutar
    print()
    info("Acción a ejecutar:")
    show(f"{' '.join(cmd)}")
    print()
    
    # Pedir confirmación
    try:
        answer = input(f"{YELLOW}¿{message}? (s/N): {Colors.NC}").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return 1
    
    if answer in ['s', 'si', 'sí']:
        log_action("INFO", f"CONFIRMED: {' '.join(cmd)}")
        result = run_command(cmd)
        
        if result == 0:
            ok("Ejecutado exitosamente")
        else:
            err(f"Error durante ejecución: {result}")
        
        return result
    else:
        warn("Cancelado por el usuario")
        log_action("WARNING", f"CANCELLED: {' '.join(cmd)}")
        return 1

def destructive(cmd_type: str, args: List[str], dry_run: bool = False) -> int:
    """Para comandos destructivos (rm, mv, chmod)."""
    if cmd_type in ['rm', 'remove']:
        if dry_run:
            show(f"ELIMINARÍA: {' '.join(args)}")
            
            for f in args:
                path = Path(f)
                if path.exists():
                    size = path.stat().st_size
                    size_str = f"{size / 1024:.1f}KB" if size < 1024*1024 else f"{size / (1024*1024):.1f}MB"
                    info(f"  → {f} ({size_str})")
            
            log_action("INFO", f"DRY_RUN: rm {' '.join(args)}")
            return 0
        
        return confirm_and_run("¿Eliminar estos archivos?", ["rm"] + args)
    
    elif cmd_type in ['mv', 'move']:
        if dry_run:
            show(f"MOVERÍA: {' '.join(args)}")
            log_action("INFO", f"DRY_RUN: mv {' '.join(args)}")
            return 0
        
        return confirm_and_run("¿Mover archivos?", ["mv"] + args)
    
    elif cmd_type in ['chmod', 'chown']:
        if dry_run:
            show(f"CAMBIARÍA PERMISOS: {cmd_type} {' '.join(args)}")
            log_action("INFO", f"DRY_RUN: {cmd_type} {' '.join(args)}")
            return 0
        
        return confirm_and_run("¿Cambiar permisos?", [cmd_type] + args)
    
    else:
        return run_command([cmd_type] + args, dry_run)

def show_summary() -> None:
    """Muestra un resumen de las acciones realizadas."""
    if not LOG_FILE.exists():
        info("No hay acciones registradas")
        return
    
    print()
    print(f"{Colors.CYAN}━━━ RESUMEN DRY-RUN ━━━{Colors.NC}")
    
    content = LOG_FILE.read_text()
    lines = content.strip().split('\n')
    
    total = len(lines)
    dry_count = sum(1 for line in lines if 'DRY_RUN' in line)
    exec_count = sum(1 for line in lines if 'EXEC' in line or 'CONFIRMED' in line)
    
    print(f"  Total acciones: {total}")
    print(f"  {Colors.GREEN}Ejecutadas: {exec_count}{Colors.NC}")
    print(f"  {Colors.YELLOW}Dry-run (no ejecutadas): {dry_count}{Colors.NC}")
    print()
    print(f"  Log: {LOG_FILE}")

def show_help() -> None:
    """Muestra la ayuda."""
    print(f"""
╔══════════════════════════════════════════════╗
║   🔒 nexo-dryrun.py v{VERSION}               ║
║   Ejecución segura de comandos              ║
╚══════════════════════════════════════════════╝

USO:
  nexo-dryrun.py <comando> [args...]     Ejecutar comando
  nexo-dryrun.py --dry-run <comando>     Modo dry-run
  nexo-dryrun.py --summary               Mostrar resumen
  nexo-dryrun.py --help                  Esta ayuda

VARIABLES DE ENTORNO:
  DRY_RUN=1        Solo muestra comandos, no ejecuta
  NON_INTERACTIVE=1 Sin confirmaciones (para CI/CD)

EJEMPLOS:
  DRY_RUN=1 nexo-dryrun.py rm -rf /tmp/old
  nexo-dryrun.py --summary
""")

# ── Main ───────────────────────────────────────────────────────────────────
def main() -> int:
    args = sys.argv[1:]
    
    # Configurar logging
    setup_logging()
    
    # Argumentos especiales
    if "--help" in args or "-h" in args:
        show_help()
        return 0
    
    if "--summary" in args:
        show_summary()
        return 0
    
    # Verificar si hay comandos
    if not args:
        show_help()
        return 0
    
    # Modo dry-run global
    global DRY_RUN
    if "--dry-run" in args:
        DRY_RUN = True
        args.remove("--dry-run")
    
    if not args:
        show_help()
        return 0
    
    # Ejecutar comando
    cmd = args[0]
    cmd_args = args[1:]
    
    return run_command([cmd] + cmd_args, DRY_RUN)

if __name__ == "__main__":
    sys.exit(main())
