#!/bin/bash
# ╔══════════════════════════════════════════════════════════════╗
# ║  NEXO UPDATE — Actualización segura del sistema (Arch)     ║
# ║  Solo lo necesario, sin sacrificar rendimiento              ║
# ║  Autor: Nexo para mikuyasha                                ║
# ╚══════════════════════════════════════════════════════════════╝

set -euo pipefail

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Config
LOG_DIR="/home/miku/.local/logs"
LOG_FILE="$LOG_DIR/nexo-update-$(date +%Y%m%d-%H%M%S).log"
LOCK_FILE="/tmp/nexo-update.lock"
DRY_RUN=false

# Paquetes NUNCA tocar (rendimiento/estabilidad)
SKIP_PKGS=(
    "linux"
    "linux-headers"
    "linux-lts"
    "linux-lts-headers"
    "mesa"
    "libglvnd"
    "xfce4"
    "xfce4-panel"
    "xfce4-session"
    "xfce4-settings"
    "xfdesktop"
    "wezterm"
    "opencode"
    "pipewire"
    "wireplumber"
    "pipewire-pulse"
    "pipewire-alsa"
    "pipewire-jack"
    "xorg-server"
    "xorg-xinit"
    "xorg-xrandr"
    "nvidia-utils"
)

# --- Funciones ---

log() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo -e "$msg" | tee -a "$LOG_FILE"
}

banner() {
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║          🔒 NEXO UPDATE — Actualización Segura         ║"
    echo "║          Solo lo necesario. Sin perder rendimiento.     ║"
    echo "║          Arch Linux / pacman                            ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

check_lock() {
    if [ -f "$LOCK_FILE" ]; then
        local pid
        pid=$(cat "$LOCK_FILE" 2>/dev/null || echo "")
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            echo -e "${RED}❌ Ya hay una actualización en curso (PID: $pid)${NC}"
            exit 1
        fi
        rm -f "$LOCK_FILE"
    fi
    echo $$ > "$LOCK_FILE"
    trap 'rm -f "$LOCK_FILE"' EXIT
}

check_root() {
    if [ "$EUID" -eq 0 ]; then
        echo -e "${RED}❌ No ejecutes esto como root. Usa: nexo-update${NC}"
        exit 1
    fi
}

check_system() {
    log "📊 Verificando estado del sistema..."
    
    # RAM disponible
    local ram_avail
    ram_avail=$(awk '/MemAvailable/ {printf "%.0f", $2/1024}' /proc/meminfo)
    if [ "$ram_avail" -lt 500 ]; then
        echo -e "${YELLOW}⚠️  RAM baja: ${ram_avail}MB disponible. Podría ser lento.${NC}"
    fi
    
    # Disco
    local disk_pct
    disk_pct=$(df / | awk 'NR==2 {gsub(/%/,"",$5); print $5}')
    if [ "$disk_pct" -gt 90 ]; then
        echo -e "${RED}❌ Disco al ${disk_pct}%. Libera espacio antes de actualizar.${NC}"
        exit 1
    fi
    log "   RAM: ${ram_avail}MB | Disco: ${disk_pct}% usado"
    
    # Conexión
    if ! ping -c 1 -W 3 1.1.1.1 &>/dev/null; then
        echo -e "${RED}❌ Sin conexión a internet${NC}"
        exit 1
    fi
    log "   ✅ Internet OK"
}

is_skipped() {
    local pkg="$1"
    for skip in "${SKIP_PKGS[@]}"; do
        if [[ "$pkg" == "$skip" || "$pkg" == "$skip"* ]]; then
            return 0
        fi
    done
    return 1
}

show_plan() {
    log "📋 Plan de actualización:"
    echo ""
    
    # Sync primero
    sudo pacman -Sy --quiet 2>/dev/null
    
    # Contar actualizaciones disponibles
    local updates
    updates=$(pacman -Qu 2>/dev/null | wc -l)
    log "   📦 Actualizaciones disponibles: $updates"
    
    # Contar protegidas
    local skipped=0
    local to_update=()
    while IFS= read -r line; do
        local pkg
        pkg=$(echo "$line" | awk '{print $1}')
        if is_skipped "$pkg"; then
            skipped=$((skipped + 1))
        else
            to_update+=("$pkg")
        fi
    done < <(pacman -Qu 2>/dev/null)
    
    if [ "$skipped" -gt 0 ]; then
        log "   🛡️  Paquetes protegidos (NO se tocarán): $skipped"
    fi
    log "   ⬆️  Se actualizarán: ${#to_update[@]} paquetes"
    
    if [ "${#to_update[@]}" -gt 0 ]; then
        echo ""
        log "   Paquetes a actualizar:"
        for pkg in "${to_update[@]}"; do
            log "     • $pkg"
        done
    fi
    
    echo ""
}

do_update() {
    local start_time
    start_time=$(date +%s)
    
    log "🔄 Iniciando actualización..."
    echo ""
    
    # 1. Sincronizar bases de datos
    log "1/4 📥 Sincronizando bases de datos..."
    sudo pacman -Sy --noconfirm 2>&1 | tee -a "$LOG_FILE"
    
    # 2. Construir lista de paquetes a actualizar (excluyendo protegidos)
    log "2/4 📋 Construyendo lista de actualización..."
    
    local update_list=()
    while IFS= read -r line; do
        local pkg
        pkg=$(echo "$line" | awk '{print $1}')
        if ! is_skipped "$pkg"; then
            update_list+=("$pkg")
        fi
    done < <(pacman -Qu 2>/dev/null)
    
    if [ "${#update_list[@]}" -eq 0 ]; then
        log "   ✅ Todo actualizado, nada que hacer"
        return 0
    fi
    
    log "   Actualizando ${#update_list[@]} paquetes..."
    
    # 3. Instalar actualizaciones
    log "3/4 ⬆️  Instalando actualizaciones..."
    sudo pacman -S --noconfirm --needed "${update_list[@]}" 2>&1 | tee -a "$LOG_FILE" || {
        log "⚠️  Algunas actualizaciones fallaron, revisando..."
    }
    
    # 4. Limpiar caché de paquetes viejos (mantener últimos 2)
    log "4/4 🧹 Limpiando caché..."
    sudo pacman -Sc --noconfirm 2>&1 | tee -a "$LOG_FILE" || true
    
    # Limpiar paquetes huérfanos
    local orphans
    orphans=$(pacman -Qdtq 2>/dev/null || true)
    if [ -n "$orphans" ]; then
        log "   🗑️  Eliminando paquetes huérfanos..."
        echo "$orphans" | sudo pacman -Rs --noconfirm - 2>&1 | tee -a "$LOG_FILE" || true
    fi
    
    local end_time
    end_time=$(date +%s)
    local duration=$(( end_time - start_time ))
    local minutes=$(( duration / 60 ))
    local seconds=$(( duration % 60 ))
    
    echo ""
    log "✅ Actualización completada en ${minutes}m ${seconds}s"
}

show_summary() {
    echo ""
    echo -e "${CYAN}══════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}📊 RESUMEN DE ACTUALIZACIÓN${NC}"
    echo -e "${CYAN}══════════════════════════════════════════════════════════${NC}"
    
    local remaining
    remaining=$(pacman -Qu 2>/dev/null | wc -l)
    
    if [ "$remaining" -eq 0 ]; then
        echo -e "${GREEN}✅ Sistema completamente actualizado${NC}"
    else
        echo -e "${YELLOW}⚠️  Quedan $remaining paquetes por actualizar (protegidos o con dependencias)${NC}"
    fi
    
    echo -e "   📝 Log guardado en: $LOG_FILE"
    echo ""
}

usage() {
    echo "Uso: nexo-update [opciones]"
    echo ""
    echo "Opciones:"
    echo "  --dry-run    Solo mostrar qué se actualizaría (sin instalar)"
    echo "  --help       Mostrar esta ayuda"
    echo ""
    echo "Ejemplos:"
    echo "  nexo-update              # Actualización segura normal"
    echo "  nexo-update --dry-run    # Ver qué se actualizaría"
    echo ""
}

main() {
    while [ $# -gt 0 ]; do
        case "$1" in
            --dry-run) DRY_RUN=true ;;
            --help|-h) usage; exit 0 ;;
            *) echo "Opción desconocida: $1"; usage; exit 1 ;;
        esac
        shift
    done
    
    mkdir -p "$LOG_DIR"
    banner
    check_root
    check_lock
    check_system
    
    if [ "$DRY_RUN" = true ]; then
        log "🔍 Modo dry-run: solo mostrando cambios"
        show_plan
        exit 0
    fi
    
    show_plan
    
    echo -e "${YELLOW}¿Continuar con la actualización? (s/N):${NC} "
    read -r answer
    if [[ ! "$answer" =~ ^[sS]$ ]]; then
        log "❌ Cancelado por el usuario"
        exit 0
    fi
    
    echo ""
    do_update
    show_summary
    
    log "🏁 Proceso finalizado"
}

main "$@"
