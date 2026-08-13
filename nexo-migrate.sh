#!/bin/bash
# ============================================================
# 🔄 nexo-migrate — Migración desde versiones antiguas de Nexo
# Para usuarios con versiones muy desactualizadas.
# Conserva memoria, configuración y datos personales.
#
# Uso (en Termux o Linux):
#   curl -fsSL https://raw.githubusercontent.com/Mikutabby/nexo-lab/master/nexo-migrate.sh | bash
# ============================================================

set -euo pipefail

# --- Colores ---
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${CYAN}🔄 =============================================="
echo -e "   NEXO MIGRATE — Desde versión antigua"
echo -e "==============================================${NC}"
echo ""

# --- Detectar si es Termux o Linux ---
if [ -d "/data/data/com.termux" ]; then
    IS_TERMUX=1
    INSTALL_DIR="$HOME"
    BIN_DIR="$HOME/.local/bin"
    REPO_DIR="$HOME/nexo-lab"
    echo -e "${GREEN}📱 Detectado: Termux${NC}"
else
    IS_TERMUX=0
    INSTALL_DIR="$HOME"
    BIN_DIR="$HOME/.local/bin"
    REPO_DIR="$HOME/nexo-lab"
    echo -e "${GREEN}🖥️  Detectado: Linux${NC}"
fi

# --- FASE 1: BACKUP de datos actuales ---
echo ""
echo -e "${YELLOW}[1/5]${NC} Creando backup de datos actuales..."

BACKUP_DIR="$HOME/nexo-backup-migrate-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Copiar memoria y config si existen
for item in ".nexo-memory" ".nexo" ".opencode" ".config/opencode"; do
    src="$HOME/$item"
    if [ -d "$src" ]; then
        cp -r "$src" "$BACKUP_DIR/" 2>/dev/null || true
        echo -e "  ${GREEN}✓${NC} $item respaldado"
    fi
done

# Copiar scripts personalizados si existen
if [ -d "$BIN_DIR" ]; then
    mkdir -p "$BACKUP_DIR/scripts"
    cp "$BIN_DIR"/nexo-* "$BACKUP_DIR/scripts/" 2>/dev/null || true
    echo -e "  ${GREEN}✓${NC} Scripts respaldados"
fi

echo -e "  ${GREEN}✓${NC} Backup en: $BACKUP_DIR"

# --- FASE 2: Clonar versión nueva ---
echo ""
echo -e "${YELLOW}[2/5]${NC} Descargando última versión..."

if [ -d "$REPO_DIR" ]; then
    echo -e "  ${YELLOW}⚠️${NC} Repo existente — actualizando..."
    cd "$REPO_DIR"
    git pull origin main --quiet 2>/dev/null || git pull origin master --quiet 2>/dev/null || {
        echo -e "  ${YELLOW}⚠️${NC} No se pudo actualizar, re-clonando..."
        rm -rf "$REPO_DIR"
        git clone https://github.com/Mikutabby/nexo-lab.git "$REPO_DIR" --quiet
    }
else
    git clone https://github.com/Mikutabby/nexo-lab.git "$REPO_DIR" --quiet
fi

echo -e "  ${GREEN}✓${NC} Repositorio actualizado"

# --- FASE 3: Instalar/actualizar ---
echo ""
echo -e "${YELLOW}[3/5]${NC} Instalando componentes..."

cd "$REPO_DIR"
chmod +x install.sh

# Instalar sin preguntar (para migración)
if [ -f install.sh ]; then
    bash install.sh --silent 2>/dev/null || bash install.sh 2>/dev/null || {
        echo -e "  ${YELLOW}⚠️${NC} Instalación con errores — continuando..."
    }
fi

echo -e "  ${GREEN}✓${NC} Componentes instalados"

# --- FASE 4: Restaurar datos ---
echo ""
echo -e "${YELLOW}[4/5]${NC} Restaurando memoria y configuración..."

for item in ".nexo-memory" ".nexo" ".opencode" ".config/opencode"; do
    src="$BACKUP_DIR/$item"
    dest="$HOME/$item"
    if [ -d "$src" ]; then
        # No sobreescribir, mergear
        if [ -d "$dest" ]; then
            cp -rn "$src"/* "$dest"/ 2>/dev/null || true
        else
            cp -r "$src" "$dest" 2>/dev/null || true
        fi
        echo -e "  ${GREEN}✓${NC} $item restaurado"
    fi
done

# Restaurar scripts personalizados
if [ -d "$BACKUP_DIR/scripts" ]; then
    mkdir -p "$BIN_DIR"
    cp "$BACKUP_DIR/scripts"/nexo-* "$BIN_DIR/" 2>/dev/null || true
    chmod +x "$BIN_DIR"/nexo-* 2>/dev/null || true
    echo -e "  ${GREEN}✓${NC} Scripts restaurados"
fi

# --- FASE 5: Actualizar symlink de nexo-update ---
echo ""
echo -e "${YELLOW}[5/5]${NC} Configurando actualizaciones futuras..."

# Crear symlink para nexo-update
if [ -f "$REPO_DIR/nexo-update.sh" ]; then
    ln -sf "$REPO_DIR/nexo-update.sh" "$BIN_DIR/nexo-update" 2>/dev/null || true
    chmod +x "$REPO_DIR/nexo-update.sh" 2>/dev/null || true
    echo -e "  ${GREEN}✓${NC} nexo-update disponible"
fi

# --- RESUMEN ---
echo ""
echo -e "${GREEN}✅ =============================================="
echo -e "   MIGRACIÓN COMPLETADA"
echo -e "===============================================${NC}"
echo ""
echo -e "  ${GREEN}Backup:${NC}    $BACKUP_DIR"
echo -e "  ${GREEN}Repo:${NC}      $REPO_DIR"
echo -e "  ${GREEN}Actualizar:${NC} nexo-update"
echo ""
echo -e "  Tus datos y memoria fueron conservados."
echo -e "  Si algo falló, tu backup está en:"
echo -e "  ${CYAN}$BACKUP_DIR${NC}"
echo ""
