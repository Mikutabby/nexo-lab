#!/bin/bash
# setup-sudo.sh — Configura sudo sin contraseña para el usuario actual
# Uso: bash setup-sudo.sh
# Te va a pedir la contraseña UNA sola vez

set -e

USER_NAME=$(whoami)
SUDOERS_FILE="/etc/sudoers.d/${USER_NAME}-nopasswd"

echo "🔧 Configurando sudo sin contraseña para: $USER_NAME"
echo ""

if sudo -n true 2>/dev/null; then
    echo "✅ Ya tenés sudo sin contraseña. No hace nada."
    exit 0
fi

echo "🔑 Te va a pedir la contraseña UNA vez..."
echo ""

echo "${USER_NAME} ALL=(ALL) NOPASSWD: ALL" | sudo tee "$SUDOERS_FILE" > /dev/null
sudo chmod 440 "$SUDOERS_FILE"

if sudo -n true 2>/dev/null; then
    echo ""
    echo "✅ ¡Listo! sudo sin contraseña configurado."
    echo "   Archivo: $SUDOERS_FILE"
else
    echo ""
    echo "❌ Algo salió mal. Verificá la contraseña e intentá de nuevo."
    exit 1
fi
