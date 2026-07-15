#!/bin/bash
# ============================================================================
# nexo-dryrun.sh — Wrapper para nexo-dryrun.py
# ============================================================================
# Wrapper en bash que mantiene compatibilidad con el script original
# mientras delega la lógica a la versión en Python.
#
# Uso:
#   source nexo-dryrun.sh        → cargar funciones
#   nexo-dryrun.py <comando>     → ejecutar comando
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/nexo-dryrun.py"

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
    echo "Error: nexo-dryrun.py no encontrado en $PYTHON_SCRIPT" >&2
    exit 1
fi

# Si se ejecuta directamente (no como source), mostrar ayuda
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "Uso: source nexo-dryrun.sh"
    echo ""
    echo "Funciones disponibles (via Python):"
    echo "  nexo-dryrun.py <cmd>           Ejecuta o muestra (según DRY_RUN)"
    echo "  nexo-dryrun.py --dry-run       Modo dry-run"
    echo "  nexo-dryrun.py --summary       Muestra resumen de acciones"
    echo ""
    echo "Para usar las funciones bash, source el script:"
    echo "  source $0"
fi
