#!/bin/bash
# ============================================================================
# nexo-daemon.sh — Wrapper para nexo-daemon.py
# ============================================================================
# Wrapper en bash que mantiene compatibilidad con el script original
# mientras delega la lógica a la versión en Python.
#
# Uso:
#   nexo-daemon.sh start      → iniciar en background
#   nexo-daemon.sh stop       → detener
#   nexo-daemon.sh status     → estado
#   nexo-daemon.sh foreground → ejecutar en primer plano
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/nexo-daemon.py"

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
    echo "Error: nexo-daemon.py no encontrado en $PYTHON_SCRIPT" >&2
    exit 1
fi

# Ejecutar el script Python con todos los argumentos
exec python3 "$PYTHON_SCRIPT" "$@"
