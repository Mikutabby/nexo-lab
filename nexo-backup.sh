#!/bin/bash
# ═══════════════════════════════════════════════════════════
# nexo-backup.sh — Backup cifrado del ecosistema Nexo
# ═══════════════════════════════════════════════════════════
# 
# USO:
#   nexo-backup.sh              → interactivo (pide passphrase)
#   nexo-backup.sh --cron       → lee passphrase de ~/.nexo-backup-pass
#   nexo-backup.sh --restore    → modo restore
#   nexo-backup.sh --help       → ayuda
#
# La passphrase SOLO la sabe miku. Nunca está en mi configuración.
# ═══════════════════════════════════════════════════════════

# NOTA: No usar set -e para evitar que errores menores maten el script
# El manejo de errores se hace explícitamente donde es necesario

VERSION="1.1"
NEXO_HOME="$HOME"
BACKUP_DIR="$NEXO_HOME/nexo-backups"
RESTORE_SCRIPT="$NEXO_HOME/.local/bin/nexo-restore.sh"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_FILE="nexo-ecosystem-$TIMESTAMP.tar.gz"
BACKUP_PATH="$BACKUP_DIR/$BACKUP_FILE"
ENCRYPTED_FILE="$BACKUP_PATH.gpg"
PASSFILE="$NEXO_HOME/.nexo-backup-pass"

# Política de retención: mantener solo los últimos N backups
RETENTION_COUNT=7

# Archivos a respaldar
INCLUDE=(
    "$NEXO_HOME/.nexo-memory"
    "$NEXO_HOME/.local/bin/nexo-"
    "$NEXO_HOME/.opencode"
    "$NEXO_HOME/.config/opencode"
    "$NEXO_HOME/.face_embeddings.pkl"
    "$NEXO_HOME/.face_labels.pkl"
    "$NEXO_HOME/.face_model.yml"
    "$NEXO_HOME/migrar-miku.sh"
    "$NEXO_HOME/.local/bin/limpiar"
    "$NEXO_HOME/.local/bin/check-identity.sh"
    "$NEXO_HOME/.local/bin/face-recognize.py"
    "$NEXO_HOME/.local/bin/temp-monitor.sh"
    "$NEXO_HOME/.local/bin/temp-cancel.sh"
    "$NEXO_HOME/.local/bin/verify-secret.sh"
    "$NEXO_HOME/.local/bin/play-music"
    "$NEXO_HOME/miku-crontab.txt"
    "/etc/sudoers.d/temp-monitor"
    "$NEXO_HOME/.config/autostart/wallpaper-animado.desktop"
)

# Ayuda
if [[ "$1" == "--help" ]]; then
    echo "╔══════════════════════════════════════════════╗"
    echo "║   🔐 nexo-backup.sh v$VERSION              ║"
    echo "║   Backup cifrado del ecosistema Nexo       ║"
    echo "╚══════════════════════════════════════════════╝"
    echo ""
    echo "USO:"
    echo "  nexo-backup.sh              Backup interactivo (te pide passphrase)"
    echo "  nexo-backup.sh --cron       Backup automático (usa ~/.nexo-backup-pass)"
    echo "  nexo-backup.sh --restore    Restaurar desde backup"
    echo "  nexo-backup.sh --list       Listar backups disponibles"
    echo "  nexo-backup.sh --help       Esta ayuda"
    echo ""
    echo "📁 Backups guardados en: $BACKUP_DIR"
    echo "🔐 Cifrado GPG simétrico (AES256)"
    echo ""
    echo "⚠️  La passphrase SOLO la sabe miku."
    echo "   Para cron: crear $PASSFILE con permisos 600"
    exit 0
fi

# Listar backups
if [[ "$1" == "--list" ]]; then
    echo "📦 Backups disponibles en $BACKUP_DIR:"
    echo ""
    if [[ -d "$BACKUP_DIR" ]]; then
        ls -lh "$BACKUP_DIR"/*.gpg 2>/dev/null || echo "  (no hay backups aún)"
    else
        echo "  (no hay backups aún)"
    fi
    exit 0
fi

# ─── MODO RESTORE ────────────────────────────────────
if [[ "$1" == "--restore" ]]; then
    echo "🔓 MODO RESTORE"
    echo "Seleccioná un backup para restaurar:"
    echo ""

    if [[ ! -d "$BACKUP_DIR" ]]; then
        echo "❌ No hay directorio de backups en $BACKUP_DIR"
        exit 1
    fi

    mapfile -t FILES < <(ls -t "$BACKUP_DIR"/*.gpg 2>/dev/null)
    if [[ ${#FILES[@]} -eq 0 ]]; then
        echo "❌ No hay backups disponibles."
        exit 1
    fi

    echo "  #  FECHA              TAMAÑO"
    echo "  ─────────────────────────────────"
    for i in "${!FILES[@]}"; do
        BASENAME=$(basename "${FILES[$i]}" .tar.gz.gpg)
        BASENAME=$(basename "$BASENAME" .gpg)
        if [[ "$BASENAME" == "latest-backup" ]]; then
            FECHA="Último backup    "
        else
            FECHA=$(echo "$BASENAME" | sed 's/nexo-ecosystem-//')
        fi
        TAM=$(du -h "${FILES[$i]}" | cut -f1)
        printf "  %-2d  %s  %s\n" $((i+1)) "$FECHA" "$TAM"
    done
    
    echo ""
    read -p "➜ Elegí número (o 0 para cancelar): " CHOICE </dev/tty
    if [[ "$CHOICE" == "0" || -z "$CHOICE" ]]; then
        echo "Cancelado."
        exit 0
    fi

    SELECTED="${FILES[$((CHOICE-1))]}"
    if [[ -z "$SELECTED" ]]; then
        echo "❌ Opción inválida."
        exit 1
    fi

    echo ""
    echo "🔐 Descifrando backup..."
    echo "(ingresá la passphrase del backup)"
    echo ""

    DECRYPTED="${SELECTED%.gpg}"
    if [[ -f "$NEXO_HOME/.nexo-backup-pass" && "$2" == "--cron" ]]; then
        PASSPHRASE=$(cat "$NEXO_HOME/.nexo-backup-pass")
        echo "$PASSPHRASE" | gpg --batch --yes --passphrase-fd 0 -d -o "$DECRYPTED" "$SELECTED" 2>/dev/null
    else
        gpg -d -o "$DECRYPTED" "$SELECTED"
    fi

    if [[ $? -ne 0 ]]; then
        echo "❌ Passphrase incorrecta o error al descifrar."
        rm -f "$DECRYPTED"
        exit 1
    fi
    echo "✅ Backup descifrado."

    echo ""
    echo "⚠️  Esto va a SOBREESCRIBIR los archivos actuales."
    read -p "➜ ¿Restaurar ahora? (s/N): " CONFIRM </dev/tty
    if [[ "$CONFIRM" != "s" && "$CONFIRM" != "S" ]]; then
        echo "Cancelado. El backup descifrado queda en: $DECRYPTED"
        exit 0
    fi

    echo "🔄 Restaurando..."
    tar -xzf "$DECRYPTED" -C "$NEXO_HOME" 2>/dev/null || sudo tar -xzf "$DECRYPTED" -C "$NEXO_HOME"

    # Restaurar sudoers si existe
    if [[ -f "$NEXO_HOME/backup-sudoers-temp-monitor" ]]; then
        sudo cp "$NEXO_HOME/backup-sudoers-temp-monitor" /etc/sudoers.d/temp-monitor
        sudo chmod 440 /etc/sudoers.d/temp-monitor
        rm -f "$NEXO_HOME/backup-sudoers-temp-monitor"
    fi

    echo "✅ Restauración completada."
    echo "🔄 Te recomiendo reiniciar la terminal o ejecutar: exec bash"
    rm -f "$DECRYPTED"
    exit 0
fi

# ─── MODO BACKUP ─────────────────────────────────────

echo "╔══════════════════════════════════════════════╗"
echo "║   🔐 Nexo Backup v$VERSION                  ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# Crear directorio de backups
mkdir -p "$BACKUP_DIR"

# Obtener passphrase
if [[ "$1" == "--cron" ]]; then
    # Modo cron: leer del archivo seguro
    if [[ ! -f "$PASSFILE" ]]; then
        echo "❌ Modo cron: no existe $PASSFILE"
        echo "   Creá el archivo con tu passphrase y permisos 600:"
        echo "   echo 'tu-passphrase' > $PASSFILE"
        echo "   chmod 600 $PASSFILE"
        exit 1
    fi
    PASSPHRASE=$(cat "$PASSFILE")
    if [[ -z "$PASSPHRASE" ]]; then
        echo "❌ $PASSFILE está vacío."
        exit 1
    fi
    echo "🔑 Passphrase leída de $PASSFILE"
else
    # Modo interactivo
    echo "🔐 Ingresá la passphrase para cifrar el backup."
    echo "   (la misma passphrase la vas a necesitar para restaurar)"
    echo "   La passphrase SOLO la sabés vos, yo nunca la guardo."
    echo ""
    read -s -p "➜ Passphrase: " PASSPHRASE </dev/tty
    echo ""
    read -s -p "➜ Repetir: " PASSPHRASE2 </dev/tty
    echo ""
    if [[ "$PASSPHRASE" != "$PASSPHRASE2" ]]; then
        echo "❌ Las passphrases no coinciden."
        exit 1
    fi
    if [[ -z "$PASSPHRASE" ]]; then
        echo "❌ La passphrase no puede estar vacía."
        exit 1
    fi
fi

echo ""
echo "📦 Creando backup..."

# Crear lista de archivos existentes
FILELIST=$(mktemp)
for item in "${INCLUDE[@]}"; do
    if [[ -e "$item" || -L "$item" ]]; then
        # Eliminar el prefijo $NEXO_HOME/ para rutas relativas
        rel="${item#$NEXO_HOME/}"
        if [[ "$rel" == "$item" ]]; then
            # Es una ruta absoluta fuera de home (ej: /etc/sudoers.d)
            # La agregamos como backup especial
            if [[ -f "$item" ]] && sudo cp "$item" "$NEXO_HOME/backup-sudoers-temp-monitor" 2>/dev/null; then
                echo "backup-sudoers-temp-monitor" >> "$FILELIST"
            fi
        else
            echo "$rel" >> "$FILELIST"
        fi
    fi
done

# También respaldar archivos que coincidan con globs de nexo-
for f in "$NEXO_HOME/.local/bin/nexo-"*; do
    if [[ -f "$f" ]]; then
        rel="${f#$NEXO_HOME/}"
        echo "$rel" >> "$FILELIST"
    fi
done

# Quitar duplicados
sort -u "$FILELIST" -o "$FILELIST"

echo "   Archivos a respaldar: $(wc -l < "$FILELIST")"
echo "   Creando tarball..."

# Crear tar
if ! tar czf "$BACKUP_PATH" \
    --exclude=".nexo-memory/venv" \
    --exclude=".opencode/node_modules" \
    --exclude=".opencode/bin/opencode" \
    -C "$NEXO_HOME" --files-from "$FILELIST" 2>&1; then
    echo "⚠️  Error al crear el tarball, pero continuando..."
fi
rm -f "$FILELIST"

# Cifrar con GPG
echo "   Cifrando con GPG (AES256)..."

if [[ "$1" == "--cron" ]]; then
    echo "$PASSPHRASE" | gpg --batch --yes --passphrase-fd 0 \
        --symmetric --cipher-algo AES256 \
        -o "$ENCRYPTED_FILE" "$BACKUP_PATH" 2>/dev/null
else
    echo "$PASSPHRASE" | gpg --batch --yes --passphrase-fd 0 \
        --symmetric --cipher-algo AES256 \
        -o "$ENCRYPTED_FILE" "$BACKUP_PATH"
fi

# Borrar temporal sin cifrar
rm -f "$BACKUP_PATH"

# Limpiar backup de sudoers
rm -f "$NEXO_HOME/backup-sudoers-temp-monitor"

SIZE=$(du -h "$ENCRYPTED_FILE" | cut -f1)
echo ""
echo "✅ Backup completado:"
echo "   📁 $ENCRYPTED_FILE"
echo "   📦 Tamaño: $SIZE"
echo "   🔐 Cifrado GPG AES256"
echo ""

# ─── Subir a GitHub (opcional) ─────────────────────
if [[ -f "$NEXO_HOME/.nexo-github-backup" ]]; then
    echo "☁️  Subiendo a GitHub..."
    REPO=$(cat "$NEXO_HOME/.nexo-github-backup")
    cd "$BACKUP_DIR" || { echo "⚠️  No se pudo entrar a $BACKUP_DIR"; continue; }
    
    # Inicializar git si no existe
    if [[ ! -d ".git" ]]; then
        git init 2>/dev/null
        git branch -M main 2>/dev/null
    fi
    
    # Configurar remote
    git remote remove origin 2>/dev/null || true
    git remote add origin "$REPO" 2>/dev/null
    
    # Asegurar rama main
    CURRENT_BRANCH=$(git branch --show-current 2>/dev/null)
    if [[ "$CURRENT_BRANCH" != "main" ]]; then
        git branch -M main 2>/dev/null || true
    fi
    
    # Copiar y commitear backup
    cp "$ENCRYPTED_FILE" "latest-backup.gpg"
    git add "latest-backup.gpg" 2>/dev/null
    
    # Hacer commit (con --allow-empty si no hay cambios nuevos)
    git diff --cached --quiet 2>/dev/null || git commit -m "Backup $TIMESTAMP" 2>/dev/null
    
    # Push forzado a main
    if git push -f origin main 2>/dev/null; then
        echo "✅ Subido a GitHub: $REPO"
    else
        echo "⚠️  No se pudo subir a GitHub (probá con 'gh auth setup-git' primero)"
    fi
fi

# ─── Limpieza de backups antiguos ──────────────
echo "🧹 Limpiando backups antiguos (reteniendo últimos $RETENTION_COUNT)..."
REMOVED=0
while true; do
    COUNT=$(ls -1 "$BACKUP_DIR"/nexo-ecosystem-*.tar.gz.gpg 2>/dev/null | wc -l)
    if [[ "$COUNT" -le "$RETENTION_COUNT" ]]; then
        break
    fi
    OLDEST=$(ls -t "$BACKUP_DIR"/nexo-ecosystem-*.tar.gz.gpg 2>/dev/null | tail -1)
    if [[ -n "$OLDEST" ]]; then
        rm -f "$OLDEST"
        REMOVED=$((REMOVED + 1))
    else
        break
    fi
done
if [[ "$REMOVED" -gt 0 ]]; then
    echo "   Eliminados $REMOVED backup(s) antiguo(s)"
fi

echo "💡 Tip: Guardá esta passphrase en un lugar seguro."
echo "   Sin ella, NO se puede restaurar el backup."
echo ""

# Registrar timestamp del último backup
date +%s > "$NEXO_HOME/.nexo-last-backup"
