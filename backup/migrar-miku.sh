#!/bin/bash
# ============================================================
# 🚀 Script de migración de miku - Backup y Restore
# ============================================================
# Uso:
#   ./migrar-miku.sh backup    → Crea el archivo miku-backup.tar.gz
#   ./migrar-miku.sh restore   → Restaura desde miku-backup.tar.gz
# ============================================================

set -e

BACKUP_FILE="$HOME/miku-backup.tar.gz"
RESTORE_DIR="$HOME"

backup() {
    echo "📦 Creando backup de miku..."
    
    # Verificar que existan los archivos clave
    local files=(
        "$HOME/.config/opencode/opencode.jsonc"
        "$HOME/.config/opencode/style.md"
        "$HOME/.opencode/agents/asistente.md"
        "$HOME/.opencode/say.sh"
        "$HOME/.opencode/voice.sh"
        "$HOME/.local/bin/check-identity.sh"
        "$HOME/.local/bin/face-recognize.py"
        "$HOME/.local/bin/temp-monitor.sh"
        "$HOME/.local/bin/temp-cancel.sh"
        "$HOME/.local/bin/limpiar"
    )
    
    for f in "${files[@]}"; do
        if [ ! -f "$f" ]; then
            echo "⚠️  CUIDADO: No existe $f"
        fi
    done

    # Crear el tar.gz incluyendo carpetas completas
    # También respalda los embeddings faciales si existen
    tar -czf "$BACKUP_FILE" \
        --exclude='node_modules' \
        -C "$HOME" \
        .config/opencode/opencode.jsonc \
        .config/opencode/style.md \
        .opencode/agents/ \
        .opencode/say.sh \
        .opencode/voice.sh \
        .local/bin/check-identity.sh \
        .local/bin/face-recognize.py \
        .local/bin/temp-monitor.sh \
        .local/bin/temp-cancel.sh \
        .local/bin/limpiar \
        .face_embeddings.pkl 2>/dev/null || true
    
    # Respaldar sudoers (pide contraseña si es necesario)
    if [ -f /etc/sudoers.d/temp-monitor ]; then
        if cp /etc/sudoers.d/temp-monitor "$HOME/temp-monitor.sudoers" 2>/dev/null; then
            tar -rf "$BACKUP_FILE" -C "$HOME" temp-monitor.sudoers 2>/dev/null
            rm "$HOME/temp-monitor.sudoers"
            echo "🔐 Incluido sudoers de temp-monitor"
        else
            echo "⚠️  No se pudo copiar /etc/sudoers.d/temp-monitor (ejecutar con sudo o copiar manual)"
        fi
    fi
    
    # Respaldar crontab
    crontab -l > "$HOME/miku-crontab.txt" 2>/dev/null || echo "# Sin crontab" > "$HOME/miku-crontab.txt"
    tar -rf "$BACKUP_FILE" -C "$HOME" miku-crontab.txt 2>/dev/null
    rm "$HOME/miku-crontab.txt"
    echo "⏰ Incluido crontab"
    
    echo ""
    echo "✅ Backup creado: $BACKUP_FILE"
    ls -lh "$BACKUP_FILE"
    
    # Detectar tamaño de embeddings
    if [ -f "$HOME/.face_embeddings.pkl" ]; then
        echo "   📸 Embeddings faciales incluidos"
    else
        echo "   ⚠️  No hay embeddings faciales (reconocimiento no entrenado)"
    fi
}

restore() {
    if [ ! -f "$BACKUP_FILE" ]; then
        echo "❌ No existe $BACKUP_FILE"
        echo "   Copiá el archivo a $HOME y ejecutá: $0 restore"
        exit 1
    fi
    
    echo "📂 Restaurando backup de miku..."
    echo ""
    
    # Extraer archivos
    tar -xzf "$BACKUP_FILE" -C "$RESTORE_DIR"
    
    echo "✅ Archivos restaurados en $RESTORE_DIR"
    echo ""
    
    # Listar lo que se restauró
    echo "📋 Archivos restaurados:"
    tar -tzf "$BACKUP_FILE" | while read -r line; do
        echo "   • $line"
    done
    
    echo ""
    echo "⚠️  COSAS QUE HACER A MANO EN LA PC NUEVA:"
    echo "   1. Instalar opencode (https://opencode.ai)"
    echo "   2. Restaurar sudoers:"
    echo "      sudo cp $HOME/temp-monitor.sudoers /etc/sudoers.d/temp-monitor"
    echo "      sudo chmod 440 /etc/sudoers.d/temp-monitor"
    echo "   3. Restaurar crontab:"
    echo "      crontab $HOME/miku-crontab.txt"
    echo "   4. Verificar que ~/.config/opencode/opencode.jsonc apunte a style.md"
    echo "   5. Instalar dependencias:"
    echo "      pip install opencv-python face-recognition numpy"
    echo "   6. Si tenés cámara, entrenar:"
    echo "      face-recognize.py train"
    echo ""
    echo "🎉 Bienvenido a la nueva PC, miku!"
}

# --- Main ---
case "${1:-}" in
    backup)
        backup
        ;;
    restore)
        restore
        ;;
    *)
        echo "Uso: $0 {backup|restore}"
        echo ""
        echo "  backup   → Crea $BACKUP_FILE con toda la configuración"
        echo "  restore  → Restaura desde $BACKUP_FILE"
        exit 1
        ;;
esac
