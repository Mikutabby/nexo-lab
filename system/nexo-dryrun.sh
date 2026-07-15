#!/bin/bash
# ============================================================================
# Nexo Dry-Run Helper — Ejecución segura de comandos destructivos
# ============================================================================
# Proporciona funciones para ejecutar comandos con dry-run, confirmación
# y logging de acciones destructivas.
#
# Uso:
#   source nexo-dryrun.sh
#   dry_run rm -rf /tmp/old_files
#   confirm_and_run "¿Eliminar archivos?" rm -rf /tmp/old_files
#
# Variables de entorno:
#   DRY_RUN=1        → Solo muestra comandos, no ejecuta
#   NON_INTERACTIVE=1 → Sin confirmaciones (para CI/CD)
#   NEXO_LOG_DIR     → Directorio de logs (default: ~/.nexo-memory/log)
# ============================================================================

# Configuración por defecto
: "${DRY_RUN:=0}"
: "${NON_INTERACTIVE:=0}"
: "${NEXO_LOG_DIR:=$HOME/.nexo-memory/log}"

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Funciones de output
_dry_info()  { echo -e "${BLUE}[DRY-RUN]${NC} $*"; }
_dry_ok()    { echo -e "${GREEN}[OK]${NC} $*"; }
_dry_warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
_dry_err()   { echo -e "${RED}[ERR]${NC} $*"; }
_dry_show()  { echo -e "${CYAN}[CMD]${NC} $*"; }

# ── Logging ────────────────────────────────────────────────────────────────
_dry_log() {
    local level="$1"
    local msg="$2"
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    mkdir -p "$NEXO_LOG_DIR" 2>/dev/null
    echo "[$timestamp] [$level] $msg" >> "$NEXO_LOG_DIR/dryrun.log" 2>/dev/null
}

# ── dry_run: Ejecuta un comando o lo muestra ───────────────────────────────
# Uso: dry_run <comando> [args...]
dry_run() {
    if [[ "$DRY_RUN" == "1" ]]; then
        _dry_show "DRY-RUN: $*"
        _dry_log "DRY_RUN" "$*"
        return 0
    fi
    
    # Ejecutar el comando real
    _dry_log "EXEC" "$*"
    "$@"
    local exit_code=$?
    
    if [[ $exit_code -eq 0 ]]; then
        _dry_ok "Ejecutado: $*"
    else
        _dry_err "Error $exit_code: $*"
    fi
    
    return $exit_code
}

# ── confirm_and_run: Pide confirmación antes de ejecutar ───────────────────
# Uso: confirm_and_run "¿Mensaje de confirmación?" <comando> [args...]
confirm_and_run() {
    local message="$1"
    shift
    
    if [[ "$DRY_RUN" == "1" ]]; then
        _dry_show "DRY-RUN: $*"
        _dry_info "Confirmación omitida (dry-run): $message"
        _dry_log "DRY_RUN" "$* (msg: $message)"
        return 0
    fi
    
    if [[ "$NON_INTERACTIVE" == "1" ]]; then
        _dry_warn "Modo no-interactivo: ejecutando sin confirmar: $message"
        _dry_log "AUTO" "$* (msg: $message)"
        "$@"
        return $?
    fi
    
    # Mostrar comando a ejecutar
    echo ""
    _dry_info "Acción a ejecutar:"
    _dry_show "$*"
    echo ""
    
    # Pedir confirmación
    echo -n -e "${YELLOW}¿$message? (s/N): ${NC}"
    read -r answer
    
    if [[ "$answer" =~ ^[sS]$ ]]; then
        _dry_log "CONFIRMED" "$*"
        "$@"
        local exit_code=$?
        if [[ $exit_code -eq 0 ]]; then
            _dry_ok "Ejecutado exitosamente"
        else
            _dry_err "Error durante ejecución: $exit_code"
        fi
        return $exit_code
    else
        _dry_warn "Cancelado por el usuario"
        _dry_log "CANCELLED" "$*"
        return 1
    fi
}

# ── destructive: Para comandos que borran/modifican datos ──────────────────
# Uso: destructive rm archivo.txt
# Muestra qué se va a borrar y pide confirmación
destructive() {
    local cmd="$1"
    shift
    
    case "$cmd" in
        rm|remove)
            if [[ "$DRY_RUN" == "1" ]]; then
                _dry_show "ELIMINARÍA: $*"
                for f in "$@"; do
                    if [[ -e "$f" ]]; then
                        local size
                        size=$(du -sh "$f" 2>/dev/null | cut -f1)
                        _dry_info "  → $f ($size)"
                    fi
                done
                _dry_log "DRY_RUN" "rm $*"
                return 0
            fi
            confirm_and_run "¿Eliminar estos archivos?" rm "$@"
            ;;
        mv|move)
            if [[ "$DRY_RUN" == "1" ]]; then
                _dry_show "MOVERÍA: $*"
                _dry_log "DRY_RUN" "mv $*"
                return 0
            fi
            confirm_and_run "¿Mover archivos?" mv "$@"
            ;;
        chmod|chown)
            if [[ "$DRY_RUN" == "1" ]]; then
                _dry_show "CAMBIARÍA PERMISOS: $cmd $*"
                _dry_log "DRY_RUN" "$cmd $*"
                return 0
            fi
            confirm_and_run "¿Cambiar permisos?" "$cmd" "$@"
            ;;
        *)
            # Para otros comandos, usar dry_run normal
            dry_run "$cmd" "$@"
            ;;
    esac
}

# ── summary: Resumen de lo que se hizo ─────────────────────────────────────
dry_summary() {
    if [[ -f "$NEXO_LOG_DIR/dryrun.log" ]]; then
        echo ""
        echo -e "${CYAN}━━━ RESUMEN DRY-RUN ━━━${NC}"
        
        local total
        total=$(wc -l < "$NEXO_LOG_DIR/dryrun.log")
        local dry_count
        dry_count=$(grep -c "DRY_RUN" "$NEXO_LOG_DIR/dryrun.log" 2>/dev/null || echo 0)
        local exec_count
        exec_count=$(grep -c "EXEC\|CONFIRMED" "$NEXO_LOG_DIR/dryrun.log" 2>/dev/null || echo 0)
        
        echo -e "  Total acciones: $total"
        echo -e "  ${GREEN}Ejecutadas: $exec_count${NC}"
        echo -e "  ${YELLOW}Dry-run (no ejecutadas): $dry_count${NC}"
        echo ""
        echo -e "  Log: $NEXO_LOG_DIR/dryrun.log"
    fi
}

# ── enable_dry_run: Activa modo dry-run ────────────────────────────────────
enable_dry_run() {
    DRY_RUN=1
    _dry_warn "Modo DRY-RUN activado — los comandos NO se ejecutarán"
}

# ── disable_dry_run: Desactiva modo dry-run ────────────────────────────────
disable_dry_run() {
    DRY_RUN=0
    _dry_ok "Modo DRY-RUN desactivado — los comandos SÍ se ejecutarán"
}

# Auto-cargar si se ejecuta directamente (no como source)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "Uso: source nexo-dryrun.sh"
    echo ""
    echo "Funciones disponibles:"
    echo "  dry_run <cmd>           Ejecuta o muestra (según DRY_RUN)"
    echo "  confirm_and_run <msg> <cmd>  Pide confirmación"
    echo "  destructive <cmd>       Para comandos destructivos (rm, mv, chmod)"
    echo "  enable_dry_run          Activa modo dry-run"
    echo "  disable_dry_run         Desactiva modo dry-run"
    echo "  dry_summary             Muestra resumen de acciones"
fi
