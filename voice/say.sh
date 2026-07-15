#!/bin/bash
# ============================================================================
# say.sh — Wrapper para say.py
# ============================================================================
# Wrapper en bash que mantiene compatibilidad con el script original
# mientras delega la lógica a la versión en Python.
#
# Uso:
#   say.sh "texto"           → español
#   say.sh en "text"         → inglés
#   say.sh -s "texto lento"  → más lento
#   echo "texto" | say.sh    → pipe
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/say.py"

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
    echo "Error: say.py no encontrado en $PYTHON_SCRIPT" >&2
    exit 1
fi

# Ejecutar el script Python con todos los argumentos
exec python3 "$PYTHON_SCRIPT" "$@"
