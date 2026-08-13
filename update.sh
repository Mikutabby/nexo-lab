#!/bin/bash
# 🔄 Nexo Quick Update — Script corto para actualizar
# Pegá esto en tu terminal:
# bash <(curl -fsSL https://raw.githubusercontent.com/Mikutabby/nexo-lab/master/update.sh)

set -euo pipefail

echo "🔄 Actualizando Nexo..."

# Backup rápido de memoria
BACKUP="/tmp/nexo-backup-$$"
mkdir -p "$BACKUP"
cp -r ~/.nexo-memory "$BACKUP/" 2>/dev/null || true
cp -r ~/.nexo "$BACKUP/" 2>/dev/null || true

# Actualizar repo
cd ~/nexo-lab 2>/dev/null || git clone https://github.com/Mikutabby/nexo-lab.git ~/nexo-lab
cd ~/nexo-lab
git pull origin main --quiet 2>/dev/null || git pull origin master --quiet 2>/dev/null || true

# Instalar scripts
chmod +x install.sh
bash install.sh --update 2>/dev/null || bash install.sh 2>/dev/null || true

# Restaurar memoria
cp -r "$BACKUP/.nexo-memory" ~/ 2>/dev/null || true
cp -r "$BACKUP/.nexo" ~/ 2>/dev/null || true
rm -rf "$BACKUP"

# Crear comando nexo-update para próximas veces
ln -sf ~/nexo-lab/nexo-update.sh ~/.local/bin/nexo-update 2>/dev/null || true

echo "✅ ¡Listo! Nexo actualizado."
echo "   Para actualizar en el futuro: nexo-update"
