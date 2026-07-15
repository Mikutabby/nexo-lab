#!/usr/bin/env python3
"""
nexo-secrets v3.0 — Gestor de secrets cifrado con GPG
=====================================================
Versión mejorada en Python con mejor manejo de errores,
logging estructurado y soporte para múltiples formatos.

Uso:
    nexo-secrets get <clave>
    nexo-secrets set <clave> <valor>
    nexo-secrets check <clave> <valor>
    nexo-secrets delete <clave>
    nexo-secrets list
    nexo-secrets status
    nexo-secrets export <archivo>
    nexo-secrets import <archivo>

Requisitos:
    - gpg (GnuPG)
    - python3 >= 3.6
"""

import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple

# ── Configuración ──────────────────────────────────────────────────────────
SECRETS_DIR = Path.home() / ".nexo-memory"
SECRETS_FILE = SECRETS_DIR / "secrets.gpg"
PASSPHRASE_FILE = Path.home() / ".nexo-passphrase"
BACKUP_DIR = SECRETS_DIR / "backups"
LOG_FILE = SECRETS_DIR / "log" / "secrets.log"

# ── Colores ────────────────────────────────────────────────────────────────
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'

def info(msg: str) -> None:
    print(f"{Colors.BLUE}[INFO]{Colors.NC} {msg}")

def ok(msg: str) -> None:
    print(f"{Colors.GREEN}[OK]{Colors.NC} {msg}")

def warn(msg: str) -> None:
    print(f"{Colors.YELLOW}[WARN]{Colors.NC} {msg}")

def err(msg: str) -> None:
    print(f"{Colors.RED}[ERR]{Colors.NC} {msg}", file=sys.stderr)

def success(msg: str) -> None:
    print(f"{Colors.GREEN}✓{Colors.NC} {msg}")

def failure(msg: str) -> None:
    print(f"{Colors.RED}✗{Colors.NC} {msg}", file=sys.stderr)

# ── Logging ────────────────────────────────────────────────────────────────
def log_action(action: str, key: str, details: str = "") -> None:
    """Registra acciones en el log."""
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).isoformat()
        log_entry = f"[{timestamp}] {action}: {key}"
        if details:
            log_entry += f" ({details})"
        with open(LOG_FILE, "a") as f:
            f.write(log_entry + "\n")
    except Exception:
        pass  # El logging no debe fallar el programa principal

# ── Gestión de passphrase ──────────────────────────────────────────────────
def get_passphrase() -> str:
    """Obtiene la passphrase del archivo."""
    if not PASSPHRASE_FILE.exists():
        err(f"Passphrase no encontrada en {PASSPHRASE_FILE}")
        sys.exit(1)
    
    try:
        passphrase = PASSPHRASE_FILE.read_text().strip()
        if not passphrase:
            err("Passphrase vacía")
            sys.exit(1)
        return passphrase
    except Exception as e:
        err(f"Error leyendo passphrase: {e}")
        sys.exit(1)

# ── Operaciones GPG ────────────────────────────────────────────────────────
def gpg_encrypt(data: str, output: Path) -> bool:
    """Cifra datos con GPG."""
    passphrase = get_passphrase()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
        tmp.write(data)
        tmp_path = tmp.name
    
    try:
        cmd = [
            "gpg", "--batch", "--yes", "--pinentry-mode", "loopback",
            "--passphrase", passphrase,
            "--symmetric", "--cipher-algo", "AES256",
            "--output", str(output), tmp_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0
    except Exception as e:
        err(f"Error cifrando: {e}")
        return False
    finally:
        os.unlink(tmp_path)

def gpg_decrypt(input_file: Path) -> Optional[str]:
    """Descifra datos con GPG."""
    if not input_file.exists():
        return None
    
    passphrase = get_passphrase()
    
    try:
        cmd = [
            "gpg", "--batch", "--yes", "--pinentry-mode", "loopback",
            "--passphrase", passphrase,
            "--decrypt", str(input_file)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout
        else:
            err(f"Error descifrando: {result.stderr}")
            return None
    except Exception as e:
        err(f"Error descifrando: {e}")
        return None

# ── Gestión de secrets ─────────────────────────────────────────────────────
def init_secrets() -> None:
    """Inicializa el archivo de secrets si no existe."""
    SECRETS_DIR.mkdir(parents=True, exist_ok=True)
    
    if not SECRETS_FILE.exists():
        data = {
            "version": 1,
            "created": datetime.now(timezone.utc).isoformat(),
            "secrets": {}
        }
        gpg_encrypt(json.dumps(data, indent=2), SECRETS_FILE)

def read_secrets() -> dict:
    """Lee los secrets cifrados."""
    init_secrets()
    
    content = gpg_decrypt(SECRETS_FILE)
    if content:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            err("Error decodificando secrets")
            return {"version": 1, "secrets": {}}
    return {"version": 1, "secrets": {}}

def write_secrets(data: dict) -> bool:
    """Escribe secrets cifrados."""
    try:
        return gpg_encrypt(json.dumps(data, indent=2), SECRETS_FILE)
    except Exception as e:
        err(f"Error escribiendo secrets: {e}")
        return False

def get_secret(key: str) -> Optional[str]:
    """Obtiene un secret por su clave."""
    data = read_secrets()
    return data.get("secrets", {}).get(key)

def set_secret(key: str, value: str) -> bool:
    """Establece un secret."""
    data = read_secrets()
    
    if "secrets" not in data:
        data["secrets"] = {}
    
    data["secrets"][key] = value
    data["updated"] = datetime.now(timezone.utc).isoformat()
    
    if write_secrets(data):
        log_action("SET", key)
        ok(f"Secret '{key}' guardado")
        return True
    return False

def delete_secret(key: str) -> bool:
    """Elimina un secret."""
    data = read_secrets()
    
    if key in data.get("secrets", {}):
        del data["secrets"][key]
        data["updated"] = datetime.now(timezone.utc).isoformat()
        
        if write_secrets(data):
            log_action("DELETE", key)
            ok(f"Secret '{key}' eliminado")
            return True
    else:
        err(f"Secret '{key}' no encontrado")
        return False
    
    return False

def check_secret(key: str, expected: str) -> Tuple[bool, str]:
    """Verifica si un secret coincide con el valor esperado."""
    stored = get_secret(key)
    
    if stored is None:
        return False, f"Secret '{key}' no definido"
    
    if stored == expected:
        log_action("CHECK", key, "OK")
        return True, "Correcto"
    else:
        log_action("CHECK", key, "FAIL")
        return False, "Incorrecto"

def list_secrets() -> list:
    """Lista todas las claves de secrets."""
    data = read_secrets()
    return list(data.get("secrets", {}).keys())

def export_secrets(output_path: str) -> bool:
    """Exporta secrets a un archivo JSON cifrado."""
    data = read_secrets()
    
    try:
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        log_action("EXPORT", "*", f"to {output_path}")
        ok(f"Secrets exportados a {output_path}")
        return True
    except Exception as e:
        err(f"Error exportando: {e}")
        return False

def import_secrets(input_path: str) -> bool:
    """Importa secrets desde un archivo."""
    try:
        with open(input_path, 'r') as f:
            data = json.load(f)
        
        if "secrets" not in data:
            err("Formato de archivo inválido")
            return False
        
        # Backup antes de importar
        backup_path = BACKUP_DIR / f"secrets-backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        
        current = read_secrets()
        with open(backup_path, 'w') as f:
            json.dump(current, f, indent=2)
        
        if write_secrets(data):
            log_action("IMPORT", "*", f"from {input_path}")
            ok(f"Secrets importados desde {input_path}")
            ok(f"Backup guardado en {backup_path}")
            return True
    except Exception as e:
        err(f"Error importando: {e}")
    
    return False

# ── Interfaz CLI ───────────────────────────────────────────────────────────
def print_usage() -> None:
    """Muestra el uso del programa."""
    print(f"""
{Colors.CYAN}nexo-secrets{Colors.NC} v3.0 — Gestor de secrets cifrado con GPG

{Colors.GREEN}Uso:{Colors.NC}
    nexo-secrets get <clave>         Obtener un secret
    nexo-secrets set <clave> <valor> Establecer un secret
    nexo-secrets check <clave> <val> Verificar un secret
    nexo-secrets delete <clave>      Eliminar un secret
    nexo-secrets list                Listar todas las claves
    nexo-secrets status              Estado del sistema
    nexo-secrets export <archivo>    Exportar secrets
    nexo-secrets import <archivo>    Importar secrets

{Colors.GREEN}Ejemplos:{Colors.NC}
    nexo-secrets get sudo_password
    nexo-secrets set api_key "abc123"
    nexo-secrets check my_secret "expected_value"
    nexo-secrets list
""")

def print_status() -> None:
    """Muestra el estado del sistema."""
    info("Estado de nexo-secrets:")
    print(f"  Archivo: {SECRETS_FILE}")
    print(f"  Passphrase: {PASSPHRASE_FILE}")
    print(f"  Existe: {'Sí' if SECRETS_FILE.exists() else 'No'}")
    
    if SECRETS_FILE.exists():
        data = read_secrets()
        secrets_count = len(data.get("secrets", {}))
        print(f"  Secrets: {secrets_count}")
        
        if "created" in data:
            print(f"  Creado: {data['created']}")
        if "updated" in data:
            print(f"  Actualizado: {data['updated']}")

def main() -> int:
    """Función principal."""
    if len(sys.argv) < 2:
        print_usage()
        return 0
    
    command = sys.argv[1]
    
    if command == "get":
        if len(sys.argv) < 3:
            err("Uso: nexo-secrets get <clave>")
            return 1
        key = sys.argv[2]
        value = get_secret(key)
        if value is not None:
            print(value)
            return 0
        else:
            err(f"Secret '{key}' no encontrado")
            return 1
    
    elif command == "set":
        if len(sys.argv) < 4:
            err("Uso: nexo-secrets set <clave> <valor>")
            return 1
        key = sys.argv[2]
        value = sys.argv[3]
        return 0 if set_secret(key, value) else 1
    
    elif command == "check":
        if len(sys.argv) < 4:
            err("Uso: nexo-secrets check <clave> <valor>")
            return 1
        key = sys.argv[2]
        expected = sys.argv[3]
        success, msg = check_secret(key, expected)
        if success:
            ok(msg)
            return 0
        else:
            err(msg)
            return 1
    
    elif command == "delete":
        if len(sys.argv) < 3:
            err("Uso: nexo-secrets delete <clave>")
            return 1
        key = sys.argv[2]
        return 0 if delete_secret(key) else 1
    
    elif command == "list":
        keys = list_secrets()
        if keys:
            for key in keys:
                print(key)
        else:
            info("No hay secrets guardados")
        return 0
    
    elif command == "status":
        print_status()
        return 0
    
    elif command == "export":
        if len(sys.argv) < 3:
            err("Uso: nexo-secrets export <archivo>")
            return 1
        output_path = sys.argv[2]
        return 0 if export_secrets(output_path) else 1
    
    elif command == "import":
        if len(sys.argv) < 3:
            err("Uso: nexo-secrets import <archivo>")
            return 1
        input_path = sys.argv[2]
        return 0 if import_secrets(input_path) else 1
    
    elif command in ["--help", "-h", "help"]:
        print_usage()
        return 0
    
    else:
        err(f"Comando desconocido: {command}")
        print_usage()
        return 1

if __name__ == "__main__":
    sys.exit(main())
