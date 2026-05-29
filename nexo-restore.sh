#!/bin/bash
# ═══════════════════════════════════════════════════════════
# nexo-restore.sh — Restaurador de emergencia de Nexo
# ═══════════════════════════════════════════════════════════
#
# Este script es AUTÓNOMO y está diseñado para:
#   1. Descargar el último backup desde GitHub
#   2. Descifrarlo con tu passphrase
#   3. Restaurar todo el ecosistema Nexo
#
# USO:
#   curl -fsSL https://raw.githubusercontent.com/Mikutabby/nexo-lab/main/nexo-restore.sh | bash
#   ~~~~~~~~~~~ O ~~~~~~~~~~~~
#   nexo-restore.sh              → restaurar desde backup local
#   nexo-restore.sh --github     → descargar y restaurar desde GitHub
#   nexo-restore.sh --help       → ayuda
#
# ⚠️  REQUISITOS: bash, gpg, tar, git (para --github)
# ═══════════════════════════════════════════════════════════

VERSION="1.0"
NEXO_HOME="$HOME"
BACKUP_DIR="$NEXO_HOME/nexo-backups"
GITHUB_REPO_FILE="$NEXO_HOME/.nexo-github-backup"

echo "╔══════════════════════════════════════════════╗"
echo "║   🔓 Nexo Restore v$VERSION                 ║"
echo "║   Restaurador de emergencia del ecosistema  ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# Ayuda
if [[ "$1" == "--help" ]]; then
    echo "USO:"
    echo "  nexo-restore.sh                   Restaurar desde backup local"
    echo "  nexo-restore.sh --github          Descargar y restaurar desde GitHub"
    echo "  nexo-restore.sh --github <url>    Usar repo específico"
    echo "  nexo-restore.sh --help            Esta ayuda"
    echo ""
    echo "📁 Busca backups en: $BACKUP_DIR"
    echo "☁️  GitHub: url guardada en $GITHUB_REPO_FILE"
    exit 0
fi

# Verificar requisitos
for cmd in gpg tar; do
    if ! command -v "$cmd" &>/dev/null; then
        echo "❌ $cmd no está instalado. Instalalo primero."
        exit 1
    fi
done

# ─── MODO GITHUB ────────────────────────────────────
if [[ "$1" == "--github" ]]; then
    echo "☁️  Modo GitHub"
    echo ""

    REPO="${2:-}"
    if [[ -z "$REPO" ]]; then
        if [[ -f "$GITHUB_REPO_FILE" ]]; then
            REPO=$(cat "$GITHUB_REPO_FILE")
            echo "📖 Leyendo repo de $GITHUB_REPO_FILE"
        else
            echo "No hay repo configurado."
            read -p "➜ URL del repo GitHub (ej: git@github.com:user/repo.git): " REPO
            if [[ -z "$REPO" ]]; then
                echo "Cancelado."
                exit 1
            fi
        fi
    fi

    echo "➜ Repo: $REPO"
    echo ""
    echo "📥 Clonando repo de backups..."
    
    TMPDIR=$(mktemp -d)
    if git clone "$REPO" "$TMPDIR" 2>/dev/null; then
        echo "✅ Repo clonado."
        BACKUP_FILE=$(ls -t "$TMPDIR"/*.gpg 2>/dev/null | head -1)
        if [[ -z "$BACKUP_FILE" ]]; then
            BACKUP_FILE=$(ls -t "$TMPDIR"/latest-backup.gpg 2>/dev/null | head -1)
        fi
        if [[ -z "$BACKUP_FILE" ]]; then
            echo "❌ No se encontró backup en el repo."
            rm -rf "$TMPDIR"
            exit 1
        fi
        echo "📦 Backup encontrado: $(basename "$BACKUP_FILE")"
        cp "$BACKUP_FILE" "$BACKUP_DIR/$(basename "$BACKUP_FILE")"
        rm -rf "$TMPDIR"
        SELECTED="$BACKUP_DIR/$(basename "$BACKUP_FILE")"
    else
        echo "❌ No se pudo clonar el repo."
        echo "   Verificá:"
        echo "   - Que tengas acceso al repo"
        echo "   - Que git esté configurado"
        exit 1
    fi
else
    # ─── MODO LOCAL ──────────────────────────────────
    if [[ ! -d "$BACKUP_DIR" ]]; then
        echo "❌ No hay directorio de backups en $BACKUP_DIR"
        echo ""
        echo "💡 Opciones:"
        echo "   1. Creá backups con: nexo-backup.sh"
        echo "   2. Usá --github para descargar desde GitHub"
        exit 1
    fi

    mapfile -t FILES < <(ls -t "$BACKUP_DIR"/*.gpg 2>/dev/null)
    if [[ ${#FILES[@]} -eq 0 ]]; then
        echo "❌ No hay backups en $BACKUP_DIR"
        exit 1
    fi

    echo "📦 Backups disponibles:"
    echo ""
    echo "  #  FECHA              TAMAÑO"
    echo "  ─────────────────────────────────"
    for i in "${!FILES[@]}"; do
        BASENAME=$(basename "${FILES[$i]}" .tar.gz.gpg)
        FECHA=$(echo "$BASENAME" | sed 's/nexo-ecosystem-//')
        TAM=$(du -h "${FILES[$i]}" | cut -f1)
        printf "  %-2d  %s  %s\n" $((i+1)) "$FECHA" "$TAM"
    done

    echo ""
    read -p "➜ Elegí número (o 0 para cancelar): " CHOICE
    if [[ "$CHOICE" == "0" || -z "$CHOICE" ]]; then
        echo "Cancelado."
        exit 0
    fi

    SELECTED="${FILES[$((CHOICE-1))]}"
    if [[ -z "$SELECTED" ]]; then
        echo "❌ Opción inválida."
        exit 1
    fi
fi

# ─── DESCIFRAR ──────────────────────────────────────
echo ""
echo "🔐 Descifrando backup..."
echo "   (ingresá la passphrase que usaste al crear el backup)"
echo ""

DECRYPTED="${SELECTED%.gpg}"

if gpg -d -o "$DECRYPTED" "$SELECTED"; then
    echo "✅ Backup descifrado correctamente."
else
    echo ""
    echo "❌ Error al descifrar."
    echo "   Posibles causas:"
    echo "   - Passphrase incorrecta"
    echo "   - Backup corrupto"
    echo "   - GPG no compatible"
    rm -f "$DECRYPTED"
    exit 1
fi

# ─── RESTAURAR ──────────────────────────────────────
echo ""
echo "⚠️  ESTO VA A SOBREESCRIBIR ARCHIVOS ACTUALES"
echo "   Se van a restaurar:"
echo ""
tar tzf "$DECRYPTED" 2>/dev/null | head -30
echo "... y más archivos."
echo ""

read -p "➜ ¿Restaurar ahora? (s/N): " CONFIRM
if [[ "$CONFIRM" != "s" && "$CONFIRM" != "S" ]]; then
    echo "Cancelado."
    echo "El backup descifrado queda en: $DECRYPTED"
    exit 0
fi

echo ""
echo "🔄 Restaurando..."

# Extraer
if tar -xzf "$DECRYPTED" -C "$NEXO_HOME" 2>/dev/null; then
    echo "✅ Archivos restaurados en $NEXO_HOME"
else
    # Intentar con sudo (para archivos del sistema)
    echo "⚠️  Intentando con sudo para archivos del sistema..."
    sudo tar -xzf "$DECRYPTED" -C "$NEXO_HOME"
    echo "✅ Archivos restaurados (con sudo)"
fi

# Restaurar sudoers si existe en el backup
if [[ -f "$NEXO_HOME/backup-sudoers-temp-monitor" ]]; then
    echo "🔧 Restaurando sudoers..."
    sudo cp "$NEXO_HOME/backup-sudoers-temp-monitor" /etc/sudoers.d/temp-monitor
    sudo chmod 440 /etc/sudoers.d/temp-monitor
    rm -f "$NEXO_HOME/backup-sudoers-temp-monitor"
    echo "✅ sudoers restaurado"
fi

# Corregir permisos de scripts
echo "🔧 Corrigiendo permisos..."
chmod +x "$NEXO_HOME/.local/bin/nexo-"* 2>/dev/null || true
chmod +x "$NEXO_HOME/.local/bin/limpiar" 2>/dev/null || true
chmod +x "$NEXO_HOME/migrar-miku.sh" 2>/dev/null || true
echo "✅ Permisos corregidos"

rm -f "$DECRYPTED"

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║   ✅ RESTAURACIÓN COMPLETADA                ║"
echo "╚══════════════════════════════════════════════╝"
echo ""
echo "📋 Resumen:"
echo "   • Memoria persistente  → restaurada"
echo "   • Knowledge graph      → restaurado"
echo "   • Scripts Nexo         → restaurados"
echo "   • Configuración        → restaurada"
echo "   • Embeddings faciales  → restaurados"
echo "   • Sudoers              → restaurado"
echo ""
echo "🔄 Reiniciá la terminal o ejecutá: exec bash"
echo "🎉 Bienvenido de vuelta a Nexo."
