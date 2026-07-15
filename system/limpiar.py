#!/usr/bin/env python3
"""
limpiar.py — Limpiador automático del sistema
===============================================
Versión mejorada en Python con:
- Limpieza de cache de APT
- Limpieza de miniaturas
- Limpieza de logs del sistema
- Limpieza de cache de navegadores
- Limpieza de papelera
- Limpieza de archivos temporales
- Liberación de RAM
- Mejor manejo de errores

Uso:
    limpiar.py              → limpieza completa
    limpiar.py --dry-run    → mostrar qué se limpiaría
    limpiar.py --help       → ayuda
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from typing import List, Tuple

# ── Configuración ──────────────────────────────────────────────────────────
VERSION = "2.0"
HOME = Path.home()

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
def run_cmd(cmd: List[str], check: bool = False) -> subprocess.CompletedProcess:
    """Ejecuta un comando y retorna el resultado."""
    try:
        return subprocess.run(cmd, capture_output=True, text=True)
    except Exception as e:
        warn(f"Error ejecutando {cmd[0]}: {e}")
        return subprocess.CompletedProcess(cmd, 1, "", str(e))

def get_size_str(size_bytes: int) -> str:
    """Convierte bytes a string legible."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

def get_dir_size(path: Path) -> int:
    """Obtiene el tamaño total de un directorio."""
    total = 0
    try:
        for item in path.rglob("*"):
            if item.is_file():
                total += item.stat().st_size
    except Exception:
        pass
    return total

# ── Funciones de limpieza ──────────────────────────────────────────────────
def clean_apt_cache(dry_run: bool = False) -> Tuple[bool, str]:
    """Limpia la cache de APT."""
    info("Cache de APT...")
    
    if dry_run:
        # Calcular tamaño de cache
        cache_dir = Path("/var/cache/apt/archives")
        if cache_dir.exists():
            size = get_dir_size(cache_dir)
            return True, f"Se limpiarían {get_size_str(size)}"
        return True, "No se encontró cache de APT"
    
    result = run_cmd(["sudo", "apt-get", "autoremove", "--purge", "-y"])
    if result.returncode == 0:
        ok("autoremove completado")
    else:
        warn("autoremove requiere sudo")
    
    result = run_cmd(["sudo", "apt-get", "autoclean", "-y"])
    if result.returncode == 0:
        ok("autoclean completado")
    else:
        warn("autoclean requiere sudo")
    
    return True, "Cache de APT limpiada"

def clean_thumbnails(dry_run: bool = False) -> Tuple[bool, str]:
    """Limpia las miniaturas viejas."""
    info("Miniaturas...")
    
    thumbnails_dir = HOME / ".cache" / "thumbnails"
    if not thumbnails_dir.exists():
        return True, "No hay directorio de miniaturas"
    
    if dry_run:
        size = get_dir_size(thumbnails_dir)
        return True, f"Se limpiarían {get_size_str(size)}"
    
    try:
        shutil.rmtree(thumbnails_dir)
        thumbnails_dir.mkdir()
        ok("Miniaturas limpiadas")
        return True, "Miniaturas limpiadas"
    except Exception as e:
        warn(f"Error limpiando miniaturas: {e}")
        return False, str(e)

def clean_journal_logs(dry_run: bool = False) -> Tuple[bool, str]:
    """Limpia los logs viejos del journal."""
    info("Logs del sistema (journal)...")
    
    if dry_run:
        # Calcular tamaño del journal
        result = run_cmd(["journalctl", "--disk-usage"])
        if result.returncode == 0:
            return True, f"Se limpiarían: {result.stdout.strip()}"
        return True, "No se pudo calcular tamaño del journal"
    
    result = run_cmd(["sudo", "journalctl", "--vacuum-time=3d"])
    if result.returncode == 0:
        ok("Journal limpiado")
        return True, "Journal limpiado"
    else:
        warn("Journal requiere sudo")
        return False, "Journal requiere sudo"

def clean_browser_cache(dry_run: bool = False) -> Tuple[bool, str]:
    """Limpia la cache de navegadores."""
    info("Cache de navegadores...")
    
    browser_dirs = [
        HOME / ".cache" / "mozilla" / "firefox",
        HOME / ".cache" / "chromium",
        HOME / ".cache" / "google-chrome",
    ]
    
    total_size = 0
    for browser_dir in browser_dirs:
        if browser_dir.exists():
            total_size += get_dir_size(browser_dir)
    
    if dry_run:
        return True, f"Se limpiarían {get_size_str(total_size)}"
    
    # Firefox
    for pattern in [
        HOME / ".cache" / "mozilla" / "firefox" / "*" / "cache2",
        HOME / ".cache" / "mozilla" / "firefox" / "*" / "startupCache",
    ]:
        for cache_dir in HOME.glob(str(pattern.parent.name)):
            cache_path = cache_dir / pattern.name
            if cache_path.exists():
                shutil.rmtree(cache_path, ignore_errors=True)
    
    # Chromium
    chromium_dir = HOME / ".cache" / "chromium"
    if chromium_dir.exists():
        shutil.rmtree(chromium_dir, ignore_errors=True)
    
    # Chrome
    chrome_dir = HOME / ".cache" / "google-chrome"
    if chrome_dir.exists():
        shutil.rmtree(chrome_dir, ignore_errors=True)
    
    ok("Cache de navegadores limpiada")
    return True, "Cache de navegadores limpiada"

def clean_trash(dry_run: bool = False) -> Tuple[bool, str]:
    """Limpia la papelera."""
    info("Papelera...")
    
    trash_dir = HOME / ".local" / "share" / "Trash"
    if not trash_dir.exists():
        return True, "No hay papelera"
    
    if dry_run:
        size = get_dir_size(trash_dir)
        return True, f"Se limpiarían {get_size_str(size)}"
    
    try:
        shutil.rmtree(trash_dir)
        trash_dir.mkdir(parents=True)
        ok("Papelera limpiada")
        return True, "Papelera limpiada"
    except Exception as e:
        warn(f"Error limpiando papelera: {e}")
        return False, str(e)

def clean_temp_files(dry_run: bool = False) -> Tuple[bool, str]:
    """Limpia archivos temporales viejos."""
    info("Archivos temporales (/tmp)...")
    
    tmp_dir = Path("/tmp")
    if not tmp_dir.exists():
        return True, "No hay directorio /tmp"
    
    # Calcular archivos viejos (>7 días)
    import time
    cutoff = time.time() - (7 * 24 * 3600)
    old_files = []
    
    try:
        for item in tmp_dir.rglob("*"):
            if item.is_file() and item.stat().st_mtime < cutoff:
                old_files.append(item)
    except Exception:
        pass
    
    if dry_run:
        total_size = sum(f.stat().st_size for f in old_files)
        return True, f"Se limpiarían {len(old_files)} archivos ({get_size_str(total_size)})"
    
    cleaned = 0
    for f in old_files:
        try:
            f.unlink()
            cleaned += 1
        except Exception:
            pass
    
    ok(f"Archivos temporales limpiados: {cleaned}")
    return True, f"{cleaned} archivos temporales limpiados"

def free_ram(dry_run: bool = False) -> Tuple[bool, str]:
    """Libera RAM (cache de páginas)."""
    info("Liberando RAM...")
    
    if dry_run:
        return True, "Se liberaría caché de páginas"
    
    # Sync
    run_cmd(["sync"])
    
    # Drop caches
    result = run_cmd(["sudo", "tee", "/proc/sys/vm/drop_caches"])
    if result.returncode == 0:
        ok("RAM liberada")
        return True, "RAM liberada"
    else:
        warn("Liberación de RAM requiere sudo")
        return False, "Requiere sudo"

def show_memory_usage() -> None:
    """Muestra el uso de memoria."""
    result = run_cmd(["free", "-h"])
    if result.returncode == 0:
        for line in result.stdout.split('\n'):
            if 'Mem:' in line:
                parts = line.split()
                print(f"\n📊 Uso de memoria:")
                print(f"   Total: {parts[1]}")
                print(f"   Usada: {parts[2]}")
                print(f"   Libre: {parts[3]}")
                print(f"   Cache: {parts[5]}")
                break

# ── Main ───────────────────────────────────────────────────────────────────
def main() -> int:
    args = sys.argv[1:]
    dry_run = "--dry-run" in args
    
    if "--help" in args or "-h" in args:
        print(f"""
╔══════════════════════════════════════════════╗
║   🧹 limpiar.py v{VERSION}                   ║
║   Limpiador automático del sistema          ║
╚══════════════════════════════════════════════╝

USO:
  limpiar.py              Limpieza completa
  limpiar.py --dry-run    Mostrar qué se limpiaría
  limpiar.py --help       Esta ayuda

LIMPIEZA:
  1. Cache de APT
  2. Miniaturas viejas
  3. Logs del sistema (journal)
  4. Cache de navegadores
  5. Papelera
  6. Archivos temporales (+7 días)
  7. Liberar RAM
""")
        return 0
    
    print()
    print("╔══════════════════════════════════════════════╗")
    print(f"║   🧹 LIMPIADOR AUTOMÁTICO v{VERSION}         ║")
    print("╚══════════════════════════════════════════════╝")
    print()
    
    if dry_run:
        info("🔍 Modo dry-run: mostrando qué se limpiaría")
        print()
    
    # Ejecutar limpiezas
    clean_apt_cache(dry_run)
    clean_thumbnails(dry_run)
    clean_journal_logs(dry_run)
    clean_browser_cache(dry_run)
    clean_trash(dry_run)
    clean_temp_files(dry_run)
    free_ram(dry_run)
    
    print()
    print("╔══════════════════════════════════════════════╗")
    print("║   ✅ LIMPIEZA COMPLETADA                    ║")
    print("╚══════════════════════════════════════════════╝")
    
    show_memory_usage()
    print()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
