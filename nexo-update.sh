#!/bin/bash
# ============================================================
# 🔄 nexo-update — Actualización selectiva de Nexo
# Solo aplica mejoras/fixes sin reinstalar todo.
# No sobreescribe configuraciones del usuario.
#
# Uso:
#   nexo-update              → Actualizar con últimos cambios
#   nexo-update --check      → Solo mostrar qué cambiaría
#   nexo-update --force      → Forzar actualización
#   nexo-update --version    → Mostrar versión actual
# ============================================================

set -euo pipefail

# --- Config ---
REPO_URL="https://github.com/Mikutabby/nexo-lab.git"
REPO_DIR="$HOME/nexo-lab"
LOCAL_DIR="$HOME/.local/bin"
MEMORY_DIR="$HOME/.nexo-memory"
VERSION_FILE="$MEMORY_DIR/nexo-version.txt"

# Detectar rama remota (main o master)
detect_remote_branch() {
    cd "$REPO_DIR" 2>/dev/null || return
    if git rev-parse --verify origin/main &>/dev/null; then
        echo "main"
    elif git rev-parse --verify origin/master &>/dev/null; then
        echo "master"
    else
        echo "main"
    fi
}
REMOTE_BRANCH=$(detect_remote_branch)

# --- Colores ---
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
DIM='\033[2m'
NC='\033[0m'

# --- Helpers ---
log() { echo -e "${CYAN}[update]${NC} $1"; }
ok()  { echo -e "  ${GREEN}✓${NC} $1"; }
warn(){ echo -e "  ${YELLOW}⚠️${NC} $1"; }
err() { echo -e "  ${RED}❌${NC} $1"; }

# ============================================================
# FASE 1: VERIFICAR ESTADO
# ============================================================
echo -e "${CYAN}🔄 =============================================="
echo -e "   NEXO UPDATE — Actualización Selectiva"
echo -e "==============================================${NC}"
echo ""

if [ ! -d "$REPO_DIR/.git" ]; then
    err "No se encontró el repositorio nexo-lab en $REPO_DIR"
    echo "  Instalalo primero con: bash ~/nexo-lab/install.sh"
    exit 1
fi

# ============================================================
# FASE 2: OBTENER ÚLTIMOS CAMBIOS
# ============================================================
log "Obteniendo últimos cambios de GitHub..."

cd "$REPO_DIR"

# Guardar estado actual
OLD_COMMIT=$(git rev-parse HEAD 2>/dev/null || echo "unknown")

# Fetch + pull
git fetch origin "$REMOTE_BRANCH" --quiet 2>/dev/null || {
    err "No se pudo conectar a GitHub. ¿Tenés internet?"
    exit 1
}

NEW_COMMIT=$(git rev-parse "origin/$REMOTE_BRANCH" 2>/dev/null || echo "unknown")

if [ "$OLD_COMMIT" = "$NEW_COMMIT" ]; then
    ok "Ya estás actualizado. No hay cambios nuevos."
    exit 0
fi

# ============================================================
# FASE 3: MOSTRAR CAMBIOS
# ============================================================
echo ""
log "Cambios detectados:"
echo ""

# Obtener archivos modificados
CHANGED_FILES=$(git diff --name-only "$OLD_COMMIT".."$NEW_COMMIT" 2>/dev/null || git diff --name-only HEAD..origin/main 2>/dev/null || echo "")
ADDED_FILES=$(git diff --name-only --diff-filter=A "$OLD_COMMIT".."$NEW_COMMIT" 2>/dev/null || echo "")
DELETED_FILES=$(git diff --name-only --diff-filter=D "$OLD_COMMIT".."$NEW_COMMIT" 2>/dev/null || echo "")

# Contar cambios
CHANGED_COUNT=$(echo "$CHANGED_FILES" | grep -c . 2>/dev/null || echo "0")
ADDED_COUNT=$(echo "$ADDED_FILES" | grep -c . 2>/dev/null || echo "0")
DELETED_COUNT=$(echo "$DELETED_FILES" | grep -c . 2>/dev/null || echo "0")

echo -e "  ${GREEN}Modificados:${NC} $CHANGED_COUNT archivos"
echo -e "  ${CYAN}Agregados:${NC}   $ADDED_COUNT archivos"
echo -e "  ${RED}Eliminados:${NC}  $DELETED_COUNT archivos"

if [ "${1:-}" = "--check" ]; then
    echo ""
    log "Modo check — no se aplican cambios"
    echo ""
    if [ -n "$CHANGED_FILES" ]; then
        echo "Archivos que se actualizarían:"
        echo "$CHANGED_FILES" | while read -r f; do
            [ -n "$f" ] && echo -e "  ${YELLOW}M${NC}  $f"
        done
    fi
    if [ -n "$ADDED_FILES" ]; then
        echo "$ADDED_FILES" | while read -r f; do
            [ -n "$f" ] && echo -e "  ${GREEN}A${NC}  $f"
        done
    fi
    exit 0
fi

# ============================================================
# FASE 4: APLICAR CAMBIOS SELECTIVAMENTE
# ============================================================
echo ""
log "Aplicando actualizaciones..."

# Hacer pull (con rebase para mantener historial limpio)
git pull origin "$REMOTE_BRANCH" --rebase --quiet 2>/dev/null || {
    # Si rebase falla, intentar merge
    git pull origin "$REMOTE_BRANCH" --quiet 2>/dev/null || {
        err "Error al hacer pull"
        exit 1
    }
}

ok "Repositorio actualizado"

# ============================================================
# FASE 5: COPIAR SCRIPTS ACTUALIZADOS
# ============================================================
log "Copiando scripts actualizados..."

COPIED=0

# Scripts que van a ~/.local/bin/
SCRIPTS_TO_UPDATE=(
    "graph/nexo-graph"
    "graph/nexo-graph-core"
    "graph/nexo-memory"
    "tools/nexo-tools"
    "tools/nexo-diary"
    "tools/nexo-evaluate"
    "tools/nexo-wake"
    "voice/nexo-wake"
    "voice/say.sh"
    "voice/voice.sh"
    "system/temp-monitor.sh"
    "system/temp-cancel.sh"
    "system/check-identity.sh"
    "system/face-recognize.py"
    "system/limpiar"
    "brain/nexo-brain.py"
)

for script in "${SCRIPTS_TO_UPDATE[@]}"; do
    src="$REPO_DIR/$script"
    if [ -f "$src" ]; then
        basename=$(basename "$script")
        # Buscar en ubicaciones conocidas
        for dest_dir in "$LOCAL_DIR" "$LOCAL_DIR/nexo-lab"; do
            dest="$dest_dir/$basename"
            if [ -f "$dest" ] || [ "$dest_dir" = "$LOCAL_DIR" ]; then
                # No sobreescribir si es idéntico
                if ! diff -q "$src" "$dest" &>/dev/null 2>&1; then
                    cp "$src" "$dest"
                    chmod +x "$dest" 2>/dev/null || true
                    ok "Actualizado: $basename"
                    COPIED=$((COPIED + 1))
                fi
                break
            fi
        done
    fi
done

# Copiar también los wrappers de Python (brain, etc)
for wrapper in brain/nexo-brain.py; do
    src="$REPO_DIR/$wrapper"
    if [ -f "$src" ]; then
        dest="$LOCAL_DIR/nexo-brain.py"
        if ! diff -q "$src" "$dest" &>/dev/null 2>&1; then
            cp "$src" "$dest"
            chmod +x "$dest"
            ok "Actualizado: nexo-brain.py"
            COPIED=$((COPIED + 1))
        fi
    fi
done

# Copiar install.sh actualizado
if [ -f "$REPO_DIR/install.sh" ]; then
    dest="$REPO_DIR/install.sh"
    chmod +x "$dest"
fi

ok "Scripts: $COPIED archivos actualizados"

# ============================================================
# FASE 6: EJECUTAR MIGRACIONES SI EXISTEN
# ============================================================
if [ -d "$REPO_DIR/system/migrations" ]; then
    log "Buscando migraciones..."
    for migration in "$REPO_DIR/system/migrations/"*.sh; do
        [ -f "$migration" ] || continue
        mig_name=$(basename "$migration" .sh)
        
        # Verificar si ya se ejecutó
        if [ -f "$MEMORY_DIR/migrations/$mig_name.done" ]; then
            continue
        fi
        
        log "Ejecutando migración: $mig_name"
        if bash "$migration" 2>/dev/null; then
            mkdir -p "$MEMORY_DIR/migrations"
            touch "$MEMORY_DIR/migrations/$mig_name.done"
            ok "Migración completada: $mig_name"
        else
            warn "Migración falló: $mig_name (no crítico)"
        fi
    done
fi

# ============================================================
# FASE 7: ACTUALIZAR VERSION
# ============================================================
COMMIT_SHORT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
COMMIT_DATE=$(git log -1 --format="%ci" 2>/dev/null || date)
mkdir -p "$MEMORY_DIR"
cat > "$VERSION_FILE" << EOF
version: $COMMIT_SHORT
date: $COMMIT_DATE
updated: $(date -Iseconds)
EOF

ok "Versión: $COMMIT_SHORT"

# ============================================================
# FASE 8: RESUMEN
# ============================================================
echo ""
echo -e "${GREEN}✅ =============================================="
echo -e "   ACTUALIZACIÓN COMPLETADA"
echo -e "===============================================${NC}"
echo ""
echo -e "  ${GREEN}Scripts:${NC}     $COPIED archivos actualizados"
echo -e "  ${GREEN}Repositorio:${NC}  $COMMIT_SHORT"
echo -e "  ${GREEN}Fecha:${NC}        $COMMIT_DATE"
echo ""
echo -e "${DIM}  Para ver cambios: cd ~/nexo-lab && git log --oneline${NC}"
echo -e "${DIM}  Para ver diff:    cd ~/nexo-lab && git diff HEAD~1${NC}"
echo ""
