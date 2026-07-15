#!/bin/bash
# ============================================================================
# nexo-backup.sh — Wrapper para nexo-backup.py
# ============================================================================
# Wrapper en bash que mantiene compatibilidad con el script original
# mientras delega la lógica a la versión en Python.
#
# Uso:
#   nexo-backup.sh              → backup interactivo
#   nexo-backup.sh --cron       → backup automático
#   nexo-backup.sh --restore    → modo restore
#   nexo-backup.sh --list       → listar backups
#   nexo-backup.sh --help       → ayuda
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/nexo-backup.py"

# Activar venv si existe
if [ -f "$HOME/.nexo-venv/bin/activate" ]; then
    . "$HOME/.nexo-venv/bin/activate"
fi

# Verificar que Python está disponible
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 no encontrado" >&2
    exit 1
fi

# Verificar que el script Python existe
if [[ ! -f "$PYTHON_SCRIPT" ]]; then
    echo "Error: nexo-backup.py no encontrado en $PYTHON_SCRIPT" >&2
    exit 1
fi

# Ejecutar el script Python con todos los argumentos
exec python3 "$PYTHON_SCRIPT" "$@"
