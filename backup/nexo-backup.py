#!/usr/bin/env python3
"""
nexo-backup.py — Backup y Restore del ecosistema Nexo
======================================================
Versión mejorada en Python con:
- Backup cifrado con GPG (AES256)
- Restore interactivo desde backup local o GitHub
- Política de retención configurable
- Mejor manejo de errores
- Soporte para cron (passphrase desde archivo)

Uso:
    nexo-backup.py                  → backup interactivo
    nexo-backup.py --cron           → backup automático
    nexo-backup.py --restore        → modo restore
    nexo-backup.py --list           → listar backups
    nexo-backup.py --help           → ayuda
"""

import os
import sys
import subprocess
import tarfile
import shutil
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Tuple

# ── Configuración ──────────────────────────────────────────────────────────
VERSION = "2.0"
NEXO_HOME = Path.home()
BACKUP_DIR = NEXO_HOME / "nexo-backups"
PASSFILE = NEXO_HOME / ".nexo-backup-pass"
GITHUB_REPO_FILE = NEXO_HOME / ".nexo-github-backup"
RETENTION_COUNT = 7

# Archivos a respaldar
INCLUDE = [
    ".nexo-memory",
    ".local/bin/nexo-*",
    ".opencode",
    ".config/opencode",
    ".face_embeddings.pkl",
    ".face_labels.pkl",
    ".face_model.yml",
    "backup/migrar.sh",
    ".local/bin/limpiar",
    ".local/bin/check-identity.sh",
    ".local/bin/face-recognize.py",
    ".local/bin/temp-monitor.sh",
    ".local/bin/temp-cancel.sh",
    ".local/bin/verify-secret.sh",
    ".local/bin/play-music",
    "config/crontab.example.txt",
    ".config/autostart/wallpaper-animado.desktop",
]

# Archivos del sistema (requieren sudo)
SYSTEM_FILES = [
    "/etc/sudoers.d/temp-monitor",
]

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
def run_cmd(cmd: List[str], input_data: Optional[bytes] = None, 
            check: bool = False) -> subprocess.CompletedProcess:
    """Ejecuta un comando y retorna el resultado."""
    try:
        return subprocess.run(
            cmd, input=input_data, capture_output=True, text=False
        )
    except Exception as e:
        warn(f"Error ejecutando {cmd[0]}: {e}")
        return subprocess.CompletedProcess(cmd, 1, b"", str(e).encode())

def check_gpg() -> bool:
    """Verifica que GPG esté instalado."""
    result = run_cmd(["gpg", "--version"])
    return result.returncode == 0

def get_passphrase_interactive() -> Optional[str]:
    """Solicita passphrase de forma interactiva."""
    import getpass
    
    info("Ingresá la passphrase para cifrar el backup.")
    info("La misma passphrase la vas a necesitar para restaurar.")
    info("La passphrase SOLO la sabés vos, yo nunca la guardo.")
    print()
    
    pass1 = getpass.getpass("🔑 Passphrase: ")
    pass2 = getpass.getpass("🔑 Repetir: ")
    
    if pass1 != pass2:
        err("Las passphrases no coinciden.")
        return None
    
    if not pass1:
        err("La passphrase no puede estar vacía.")
        return None
    
    return pass1

def get_passphrase_cron() -> Optional[str]:
    """Lee passphrase desde archivo (modo cron)."""
    if not PASSFILE.exists():
        err(f"Modo cron: no existe {PASSFILE}")
        info("Creá el archivo con tu passphrase y permisos 600:")
        info(f"  echo 'tu-passphrase' > {PASSFILE}")
        info(f"  chmod 600 {PASSFILE}")
        return None
    
    passphrase = PASSFILE.read_text().strip()
    if not passphrase:
        err(f"{PASSFILE} está vacío.")
        return None
    
    info(f"Passphrase leída de {PASSFILE}")
    return passphrase

# ── Backup ─────────────────────────────────────────────────────────────────
def create_backup(passphrase: str, cron_mode: bool = False) -> bool:
    """Crea un backup cifrado del ecosistema Nexo."""
    
    print()
    print("╔══════════════════════════════════════════════╗")
    print(f"║   🔐 Nexo Backup v{VERSION}                  ║")
    print("╚══════════════════════════════════════════════╝")
    print()
    
    # Crear directorio de backups
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    
    # Timestamp
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_name = f"nexo-ecosystem-{timestamp}.tar.gz"
    backup_path = BACKUP_DIR / backup_name
    encrypted_path = BACKUP_DIR / f"{backup_name}.gpg"
    
    info("Creando backup...")
    
    # Crear lista de archivos
    filelist = []
    
    for pattern in INCLUDE:
        # Expandir glob para nexo-*
        if "*" in pattern:
            full_path = NEXO_HOME / pattern
            parent = full_path.parent
            if parent.exists():
                for f in parent.glob(full_path.name):
                    if f.exists():
                        rel = f.relative_to(NEXO_HOME)
                        filelist.append(str(rel))
        else:
            full_path = NEXO_HOME / pattern
            if full_path.exists():
                rel = full_path.relative_to(NEXO_HOME)
                filelist.append(str(rel))
    
    # Archivos del sistema (copiar temporalmente)
    for sys_file in SYSTEM_FILES:
        if os.path.exists(sys_file):
            try:
                dest = NEXO_HOME / "backup-sudoers-temp-monitor"
                subprocess.run(["sudo", "cp", sys_file, str(dest)], 
                             capture_output=True)
                filelist.append("backup-sudoers-temp-monitor")
            except Exception:
                warn(f"No se pudo copiar {sys_file}")
    
    # Quitar duplicados
    filelist = list(set(filelist))
    
    info(f"Archivos a respaldar: {len(filelist)}")
    info("Creando tarball...")
    
    # Crear tarball
    try:
        with tarfile.open(str(backup_path), "w:gz") as tar:
            for item in filelist:
                full_path = NEXO_HOME / item
                if full_path.exists():
                    tar.add(str(full_path), arcname=item)
    except Exception as e:
        warn(f"Error creando tarball: {e}")
        return False
    
    # Cifrar con GPG
    info("Cifrando con GPG (AES256)...")
    
    try:
        cmd = [
            "gpg", "--batch", "--yes",
            "--passphrase-fd", "0",
            "--symmetric", "--cipher-algo", "AES256",
            "-o", str(encrypted_path), str(backup_path)
        ]
        
        result = subprocess.run(
            cmd, input=passphrase.encode(),
            capture_output=True
        )
        
        if result.returncode != 0:
            err("Error al cifrar con GPG")
            backup_path.unlink(missing_ok=True)
            return False
            
    except Exception as e:
        err(f"Error al cifrar: {e}")
        backup_path.unlink(missing_ok=True)
        return False
    
    # Borrar temporal sin cifrar
    backup_path.unlink(missing_ok=True)
    
    # Limpiar sudoers temporal
    sudoers_temp = NEXO_HOME / "backup-sudoers-temp-monitor"
    if sudoers_temp.exists():
        sudoers_temp.unlink()
    
    size = encrypted_path.stat().st_size
    size_str = f"{size / 1024:.1f} KB" if size < 1024*1024 else f"{size / (1024*1024):.1f} MB"
    
    print()
    ok(f"Backup completado:")
    info(f"📁 {encrypted_path}")
    info(f"📦 Tamaño: {size_str}")
    info("🔐 Cifrado GPG AES256")
    
    # Subir a GitHub (opcional)
    if GITHUB_REPO_FILE.exists():
        upload_to_github(encrypted_path, timestamp)
    
    # Limpiar backups antiguos
    cleanup_old_backups()
    
    # Registrar timestamp
    (NEXO_HOME / ".nexo-last-backup").write_text(str(int(datetime.now().timestamp())))
    
    print()
    info("💡 Tip: Guardá esta passphrase en un lugar seguro.")
    info("   Sin ella, NO se puede restaurar el backup.")
    
    return True

def upload_to_github(backup_path: Path, timestamp: str) -> None:
    """Sube el backup a GitHub."""
    info("☁️  Subiendo a GitHub...")
    
    repo = GITHUB_REPO_FILE.read_text().strip()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Clonar repo
        result = run_cmd(["git", "clone", repo, tmpdir])
        if result.returncode != 0:
            warn("No se pudo clonar el repo de GitHub")
            return
        
        # Copiar backup
        dest = Path(tmpdir) / "latest-backup.gpg"
        shutil.copy2(backup_path, dest)
        
        # Commit y push
        os.chdir(tmpdir)
        run_cmd(["git", "add", "latest-backup.gpg"])
        run_cmd(["git", "commit", "-m", f"Backup {timestamp}"])
        result = run_cmd(["git", "push", "-f", "origin", "main"])
        
        if result.returncode == 0:
            ok(f"Subido a GitHub: {repo}")
        else:
            warn("No se pudo subir a GitHub")

def cleanup_old_backups() -> None:
    """Elimina backups antiguos según la política de retención."""
    info(f"🧹 Limpiando backups antiguos (reteniendo últimos {RETENTION_COUNT})...")
    
    backups = sorted(BACKUP_DIR.glob("nexo-ecosystem-*.tar.gz.gpg"), 
                    key=lambda p: p.stat().st_mtime, reverse=True)
    
    removed = 0
    for backup in backups[RETENTION_COUNT:]:
        backup.unlink()
        removed += 1
    
    if removed > 0:
        info(f"   Eliminados {removed} backup(s) antiguo(s)")

# ── Restore ────────────────────────────────────────────────────────────────
def list_backups() -> List[Path]:
    """Lista backups disponibles."""
    if not BACKUP_DIR.exists():
        return []
    
    return sorted(BACKUP_DIR.glob("*.gpg"), 
                 key=lambda p: p.stat().st_mtime, reverse=True)

def show_backup_list(backups: List[Path]) -> None:
    """Muestra la lista de backups."""
    print()
    info("📦 Backups disponibles:")
    print()
    print("  #  FECHA              TAMAÑO")
    print("  ─────────────────────────────────")
    
    for i, backup in enumerate(backups):
        name = backup.stem.replace(".tar.gz", "")
        if name == "latest-backup":
            fecha = "Último backup    "
        else:
            # Extraer fecha del nombre (nexo-ecosystem-YYYYMMDD-HHMMSS)
            parts = name.split("-")
            if len(parts) >= 5:
                # nexo-ecosystem-YYYYMMDD-HHMMSS -> YYYYMMDD-HHMMSS
                fecha = f"{parts[2]}-{parts[3]}"
            else:
                fecha = name
        
        size = backup.stat().st_size
        size_str = f"{size / 1024:.1f}KB" if size < 1024*1024 else f"{size / (1024*1024):.1f}MB"
        
        print(f"  {i+1:2d}  {fecha}  {size_str}")

def select_backup(backups: List[Path]) -> Optional[Path]:
    """Permite al usuario seleccionar un backup."""
    show_backup_list(backups)
    
    print()
    try:
        choice = input("➜ Elegí número (o 0 para cancelar): ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return None
    
    if choice == "0" or not choice:
        info("Cancelado.")
        return None
    
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(backups):
            return backups[idx]
    except ValueError:
        pass
    
    err("Opción inválida.")
    return None

def decrypt_backup(backup_path: Path, passphrase: str) -> Optional[Path]:
    """Descifra un backup."""
    decrypted_path = backup_path.with_suffix('')  # Quitar .gpg
    
    info("Descifrando backup...")
    
    cmd = [
        "gpg", "--batch", "--yes",
        "--passphrase-fd", "0",
        "-d", "-o", str(decrypted_path), str(backup_path)
    ]
    
    result = subprocess.run(
        cmd, input=passphrase.encode(),
        capture_output=True
    )
    
    if result.returncode != 0:
        err("Passphrase incorrecta o error al descifrar.")
        decrypted_path.unlink(missing_ok=True)
        return None
    
    ok("Backup descifrado correctamente.")
    return decrypted_path

def restore_backup(decrypted_path: Path) -> bool:
    """Restaura un backup descifrado."""
    print()
    warn("ESTO VA A SOBREESCRIBIR ARCHIVOS ACTUALES")
    info("Se van a restaurar:")
    print()
    
    # Mostrar contenido
    try:
        with tarfile.open(str(decrypted_path), "r:gz") as tar:
            members = tar.getnames()[:30]
            for m in members:
                print(f"  • {m}")
            if len(tar.getnames()) > 30:
                print("  ... y más archivos.")
    except Exception as e:
        warn(f"No se pudo listar contenido: {e}")
    
    print()
    try:
        confirm = input("➜ ¿Restaurar ahora? (s/N): ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return False
    
    if confirm != 's':
        info("Cancelado.")
        info(f"El backup descifrado queda en: {decrypted_path}")
        return False
    
    print()
    info("🔄 Restaurando...")
    
    # Extraer
    try:
        with tarfile.open(str(decrypted_path), "r:gz") as tar:
            tar.extractall(path=str(NEXO_HOME))
        ok("Archivos restaurados")
    except Exception as e:
        warn(f"Error extrayendo: {e}")
        info("Intentando con sudo...")
        result = run_cmd(["sudo", "tar", "xzf", str(decrypted_path), 
                         "-C", str(NEXO_HOME)])
        if result.returncode != 0:
            err("No se pudo restaurar")
            return False
        ok("Archivos restaurados (con sudo)")
    
    # Restaurar sudoers
    sudoers_temp = NEXO_HOME / "backup-sudoers-temp-monitor"
    if sudoers_temp.exists():
        info("Restaurando sudoers...")
        run_cmd(["sudo", "cp", str(sudoers_temp), "/etc/sudoers.d/temp-monitor"])
        run_cmd(["sudo", "chmod", "440", "/etc/sudoers.d/temp-monitor"])
        sudoers_temp.unlink()
        ok("sudoers restaurado")
    
    # Corregir permisos
    info("Corrigiendo permisos...")
    nexo_bin = NEXO_HOME / ".local" / "bin"
    for script in nexo_bin.glob("nexo-*"):
        script.chmod(0o755)
    
    limpiar = NEXO_HOME / ".local" / "bin" / "limpiar"
    if limpiar.exists():
        limpiar.chmod(0o755)
    
    migrar = NEXO_HOME / "backup" / "migrar.sh"
    if migrar.exists():
        migrar.chmod(0o755)
    
    ok("Permisos corregidos")
    
    # Limpiar
    decrypted_path.unlink(missing_ok=True)
    
    print()
    print("╔══════════════════════════════════════════════╗")
    print("║   ✅ RESTAURACIÓN COMPLETADA                ║")
    print("╚══════════════════════════════════════════════╝")
    print()
    info("📋 Resumen:")
    info("   • Memoria persistente  → restaurada")
    info("   • Knowledge graph      → restaurado")
    info("   • Scripts Nexo         → restaurados")
    info("   • Configuración        → restaurada")
    info("   • Embeddings faciales  → restaurados")
    info("   • Sudoers              → restaurado")
    print()
    info("🔄 Reiniciá la terminal o ejecutá: exec bash")
    info("🎉 Bienvenido de vuelta a Nexo.")
    
    return True

def restore_from_github(repo_url: Optional[str] = None) -> bool:
    """Descarga y restaura desde GitHub."""
    info("☁️  Modo GitHub")
    print()
    
    # Obtener repo
    if repo_url:
        repo = repo_url
    elif GITHUB_REPO_FILE.exists():
        repo = GITHUB_REPO_FILE.read_text().strip()
        info(f"Leyendo repo de {GITHUB_REPO_FILE}")
    else:
        repo = input("➜ URL del repo GitHub: ").strip()
        if not repo:
            info("Cancelado.")
            return False
    
    info(f"➜ Repo: {repo}")
    print()
    info("📥 Clonando repo de backups...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        result = run_cmd(["git", "clone", repo, tmpdir])
        if result.returncode != 0:
            err("No se pudo clonar el repo.")
            info("Verificá:")
            info("  - Que tengas acceso al repo")
            info("  - Que git esté configurado")
            return False
        
        ok("Repo clonado.")
        
        # Buscar backup
        tmpdir_path = Path(tmpdir)
        backups = list(tmpdir_path.glob("*.gpg"))
        
        if not backups:
            latest = tmpdir_path / "latest-backup.gpg"
            if latest.exists():
                backups = [latest]
        
        if not backups:
            err("No se encontró backup en el repo.")
            return False
        
        # Usar el más reciente
        backup = max(backups, key=lambda p: p.stat().st_mtime)
        info(f"📦 Backup encontrado: {backup.name}")
        
        # Copiar a directorio local
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        dest = BACKUP_DIR / backup.name
        shutil.copy2(backup, dest)
        
        # Seleccionar passphrase
        if PASSFILE.exists():
            passphrase = PASSFILE.read_text().strip()
        else:
            passphrase = get_passphrase_interactive()
            if not passphrase:
                return False
        
        # Descifrar y restaurar
        decrypted = decrypt_backup(dest, passphrase)
        if decrypted:
            return restore_backup(decrypted)
        
        return False

def restore_interactive() -> bool:
    """Restore interactivo desde backup local."""
    backups = list_backups()
    
    if not backups:
        err(f"No hay backups en {BACKUP_DIR}")
        info("💡 Opciones:")
        info("   1. Creá backups con: nexo-backup.py")
        info("   2. Usá --github para descargar desde GitHub")
        return False
    
    selected = select_backup(backups)
    if not selected:
        return False
    
    # Seleccionar passphrase
    if PASSFILE.exists():
        passphrase = PASSFILE.read_text().strip()
    else:
        passphrase = get_passphrase_interactive()
        if not passphrase:
            return False
    
    decrypted = decrypt_backup(selected, passphrase)
    if decrypted:
        return restore_backup(decrypted)
    
    return False

# ── Ayuda ──────────────────────────────────────────────────────────────────
def show_help() -> None:
    """Muestra la ayuda."""
    print(f"""
╔══════════════════════════════════════════════╗
║   🔐 nexo-backup.py v{VERSION}              ║
║   Backup y Restore del ecosistema Nexo      ║
╚══════════════════════════════════════════════╝

USO:
  nexo-backup.py              Backup interactivo (te pide passphrase)
  nexo-backup.py --cron       Backup automático (usa ~/.nexo-backup-pass)
  nexo-backup.py --restore    Restaurar desde backup local
  nexo-backup.py --github     Descargar y restaurar desde GitHub
  nexo-backup.py --list       Listar backups disponibles
  nexo-backup.py --help       Esta ayuda

📁 Backups guardados en: {BACKUP_DIR}
🔐 Cifrado GPG simétrico (AES256)

La passphrase SOLO la sabe el usuario.
   Para cron: crear {PASSFILE} con permisos 600
""")

# ── Main ───────────────────────────────────────────────────────────────────
def main() -> int:
    args = sys.argv[1:]
    
    # Verificar GPG
    if not check_gpg():
        err("GPG no está instalado. Instalalo primero.")
        return 1
    
    # Parsear argumentos
    if "--help" in args or "-h" in args:
        show_help()
        return 0
    
    if "--list" in args:
        backups = list_backups()
        if backups:
            show_backup_list(backups)
        else:
            info("No hay backups disponibles.")
        return 0
    
    if "--restore" in args:
        return 0 if restore_interactive() else 1
    
    if "--github" in args:
        idx = args.index("--github")
        repo = args[idx + 1] if idx + 1 < len(args) else None
        return 0 if restore_from_github(repo) else 1
    
    # Modo backup
    cron_mode = "--cron" in args
    
    if cron_mode:
        passphrase = get_passphrase_cron()
    else:
        passphrase = get_passphrase_interactive()
    
    if not passphrase:
        return 1
    
    return 0 if create_backup(passphrase, cron_mode) else 1

if __name__ == "__main__":
    sys.exit(main())
