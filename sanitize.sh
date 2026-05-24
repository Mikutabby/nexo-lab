#!/bin/bash
# 🧼 Nexo Sanitize — Escanea y limpia datos sensibles del repositorio
# Uso:
#   ./sanitize.sh scan      → Busca datos sensibles (solo reporta)
#   ./sanitize.sh clean     → Reemplaza datos sensibles con placeholders
#   ./sanitize.sh install   → Instala el pre-commit hook en .git/hooks/
#   ./sanitize.sh check     → Para usar como pre-commit hook (exit 1 si hay algo)

set -e

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
HOOK_DIR="$REPO_DIR/.githooks"
HOOK_TARGET="$REPO_DIR/.git/hooks/pre-commit"

# ─── Patrones de datos sensibles ────────────────────────────────────────────

# Contraseñas en texto plano: "password: 1234", "contraseña: xyz", "pass: xyz"
# También detecta "Password sudo de miku: 0207" (palabra + hasta 30 chars + valor)
PASSWORD_PATTERN='(password|contraseña|passwd|pass).{0,30}[:=][ \t]*[0-9a-zA-Z_\-\.]{4,}'

# IPs privadas
PRIVATE_IP_PATTERN='(^|[^0-9])(192\.168\.[0-9]{1,3}\.[0-9]{1,3}|10\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}|172\.(1[6-9]|2[0-9]|3[0-1])\.[0-9]{1,3}\.[0-9]{1,3})([^0-9]|$)'

# MAC addresses
MAC_PATTERN='([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})'

# Tokens / API keys
TOKEN_PATTERN='(sk-[a-zA-Z0-9]{20,}|ghp_[a-zA-Z0-9]{36,}|api[_-]?key[=: \t]+[a-zA-Z0-9_\-\.]{8,}|token[=: \t]+[a-zA-Z0-9_\-\.]{8,})'

# Nombres de dispositivos específicos del hogar (datos de red local)
DEVICE_PATTERN='(Miku-casa|Miku-vivo|Miku-root)'

# ─── Archivos a ignorar ────────────────────────────────────────────────────
IGNORE_PATTERNS=(
    '.git/'
    '__pycache__/'
    '*.pyc'
    '*.swp'
    '*.swo'
    '.DS_Store'
    'venv/'
    'node_modules/'
    '*.db'
    '*.pkl'
    '*.log'
    'sanitize.sh'  # no escanearse a sí mismo
)

should_ignore() {
    local file="$1"
    for pattern in "${IGNORE_PATTERNS[@]}"; do
        # Si el patrón contiene un /, comparar como ruta
        if [[ "$pattern" == */* ]]; then
            if [[ "$file" == *"$pattern"* ]]; then
                return 0
            fi
        else
            # Patrón glob simple
            local basename="${file##*/}"
            if [[ "$basename" == $pattern ]]; then
                return 0
            fi
        fi
    done
    return 1
}

# ─── Colores ────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

info()  { echo -e "${CYAN}[INFO]${NC} $1"; }
ok()    { echo -e "${GREEN}[OK]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
err()   { echo -e "${RED}[ERROR]${NC} $1"; }

# ─── Escaneo ────────────────────────────────────────────────────────────────
scan() {
    local mode="${1:-report}"  # report | clean
    local found=0
    local findings=()
    local files_to_fix=()

    info "Escaneando $REPO_DIR en busca de datos sensibles..."
    echo ""

    # Buscar archivos (excluyendo .git y binarios)
    while IFS= read -r -d '' file; do
        should_ignore "$file" && continue

        local content
        content=$(cat "$file" 2>/dev/null) || continue

        local line_num=0
        while IFS= read -r line; do
            line_num=$((line_num + 1))

            # Verificar cada patrón
            if [[ "$line" =~ $PASSWORD_PATTERN ]]; then
                # Falso positivo: no si es documentación genérica como "no password"
                local lower="${line,,}"
                if [[ "$lower" == *"sin contraseña"* || "$lower" == *"no necesita contraseña"* || "$lower" == *"no password"* || "$lower" == *"nopasswd"* ]]; then
                    continue
                fi
                found=1
                local match="${BASH_REMATCH[0]}"
                warn "🔑 Password: $file:$line_num → $match"
                findings+=("password|$file|$line_num|$match")
                files_to_fix+=("$file")
            fi

            if [[ "$line" =~ $PRIVATE_IP_PATTERN ]]; then
                found=1
                local match="${BASH_REMATCH[2]}"
                warn "🌐 IP privada: $file:$line_num → $match"
                findings+=("ip|$file|$line_num|$match")
                files_to_fix+=("$file")
            fi

            if [[ "$line" =~ $MAC_PATTERN ]]; then
                found=1
                local match="${BASH_REMATCH[0]}"
                warn "📡 MAC: $file:$line_num → $match"
                findings+=("mac|$file|$line_num|$match")
                files_to_fix+=("$file")
            fi

            if [[ "$line" =~ $TOKEN_PATTERN ]]; then
                found=1
                local match="${BASH_REMATCH[0]}"
                warn "🔐 Token: $file:$line_num → ${match:0:15}..."
                findings+=("token|$file|$line_num|$match")
                files_to_fix+=("$file")
            fi

            if [[ "$line" =~ $DEVICE_PATTERN ]]; then
                found=1
                local match="${BASH_REMATCH[0]}"
                warn "📱 Dispositivo: $file:$line_num → $match"
                findings+=("device|$file|$line_num|$match")
                files_to_fix+=("$file")
            fi

        done < "$file"

    done < <(find "$REPO_DIR" -type f -not -path '*/.git/*' -print0)

    echo ""
    if [ "$found" -eq 1 ]; then
        err "Se encontraron $found datos sensibles"
        if [ "$mode" = "clean" ]; then
            clean_files "${files_to_fix[@]}"
        fi
        return 1
    else
        ok "No se encontraron datos sensibles"
        return 0
    fi
}

# ─── Limpieza ────────────────────────────────────────────────────────────────
clean_files() {
    local files=("$@")
    # Obtener lista única
    mapfile -t unique < <(printf "%s\n" "${files[@]}" | sort -u)

    warn "Se limpiarán ${#unique[@]} archivo(s):"
    for f in "${unique[@]}"; do
        local rel="${f#$REPO_DIR/}"
        echo "   - $rel"
    done

    echo ""
    info "Modo clean: reemplazando datos sensibles con placeholders..."
    echo ""

    # Para cada archivo, reemplazar patrones con placeholders
    for file in "${unique[@]}"; do
        local cleaned=0
        local tmpfile=$(mktemp)

        while IFS= read -r line || [ -n "$line" ]; do
            local original="$line"

            # Reemplazar contraseñas (pero no documentación)
            if [[ "$line" =~ $PASSWORD_PATTERN ]]; then
                local lower="${line,,}"
                if [[ "$lower" != *"sin contraseña"* && "$lower" != *"no necesita"* && "$lower" != *"no password"* && "$lower" != *"nopasswd"* ]]; then
                    # Reemplazar el valor después de : o =
                    line=$(echo "$line" | sed -E 's/(password[=: \t]+)[0-9a-zA-Z_\-\.]{4,}/\1PLACEHOLDER_PASSWORD/gI')
                    line=$(echo "$line" | sed -E 's/(contraseña[=: \t]+)[0-9a-zA-Z_\-\.]{4,}/\1PLACEHOLDER_PASSWORD/gI')
                    line=$(echo "$line" | sed -E 's/(pass[=: \t]+)[0-9a-zA-Z_\-\.]{4,}/\1PLACEHOLDER_PASSWORD/gI')
                    line=$(echo "$line" | sed -E 's/(passwd[=: \t]+)[0-9a-zA-Z_\-\.]{4,}/\1PLACEHOLDER_PASSWORD/gI')
                fi
            fi

            # Reemplazar IPs privadas
            line=$(echo "$line" | sed -E 's/(192\.168\.[0-9]{1,3}\.[0-9]{1,3})/PLACEHOLDER_IP/g')
            line=$(echo "$line" | sed -E 's/(10\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})/PLACEHOLDER_IP/g')
            line=$(echo "$line" | sed -E 's/(172\.(1[6-9]|2[0-9]|3[0-1])\.[0-9]{1,3}\.[0-9]{1,3})/PLACEHOLDER_IP/g')

            # Reemplazar MACs
            line=$(echo "$line" | sed -E 's/([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})/PLACEHOLDER_MAC/g')

            # Reemplazar dispositivos específicos
            line=$(echo "$line" | sed -E 's/Miku-casa/PLACEHOLDER_DEVICE/g')
            line=$(echo "$line" | sed -E 's/Miku-vivo/PLACEHOLDER_DEVICE/g')
            line=$(echo "$line" | sed -E 's/Miku-root/PLACEHOLDER_DEVICE/g')

            if [ "$line" != "$original" ]; then
                cleaned=$((cleaned + 1))
            fi
            echo "$line" >> "$tmpfile"
        done < "$file"

        if [ "$cleaned" -gt 0 ]; then
            cp "$tmpfile" "$file"
            ok "🧼 $cleaned reemplazos en ${file#$REPO_DIR/}"
        fi
        rm -f "$tmpfile"
    done

    echo ""
    ok "Limpieza completada. Revisá los cambios con 'git diff' antes de commit."
}

# ─── Instalar pre-commit hook ───────────────────────────────────────────────
install_hook() {
    mkdir -p "$HOOK_DIR"

    local hook_script="$HOOK_DIR/pre-commit"

    cat > "$hook_script" << 'HOOK'
#!/bin/bash
# Nexo pre-commit hook — Evita commits con datos sensibles
set -e

REPO_DIR="$(git rev-parse --show-toplevel)"
echo "🧼 Nexo Sanitize: revisando datos sensibles antes del commit..."

# Ejecutar sanitize en modo check
"$REPO_DIR/sanitize.sh" check
RESULT=$?

if [ "$RESULT" -ne 0 ]; then
    echo ""
    echo "❌ COMMIT RECHAZADO: se encontraron datos sensibles."
    echo "   Ejecutá './sanitize.sh clean' para limpiarlos,"
    echo "   o './sanitize.sh scan' para ver exactamente qué hay."
    echo ""
    echo "   Si es un falso positivo, usá 'git commit --no-verify' para saltar."
    exit 1
fi

echo "✅ Check sanitize pasado — todo limpio"
HOOK

    chmod +x "$hook_script"
    ok "Pre-commit hook creado en $hook_script"

    # Copiar a .git/hooks/ si existe el directorio .git
    if [ -d "$REPO_DIR/.git/hooks" ]; then
        cp "$hook_script" "$REPO_DIR/.git/hooks/pre-commit"
        chmod +x "$REPO_DIR/.git/hooks/pre-commit"
        ok "Hook instalado en .git/hooks/pre-commit"
    else
        warn "No hay directorio .git. Para instalar: cp .githooks/pre-commit .git/hooks/pre-commit"
    fi

    # Sugerir git config para hooks global
    echo ""
    info "Para activar los hooks automáticamente al clonar:"
    echo "   git config core.hooksPath .githooks"
    echo "   (Agregá esta línea al install.sh si querés que sea automático)"
}

# ─── MAIN ───────────────────────────────────────────────────────────────────
case "${1:-scan}" in
    scan)
        scan report
        ;;
    clean)
        scan clean
        ;;
    check)
        # Modo silencioso para pre-commit hook
        scan report > /dev/null 2>&1
        ;;
    install)
        install_hook
        ;;
    *)
        echo "🧼 Nexo Sanitize — Protegé tu privacidad en el repo"
        echo ""
        echo "Uso:"
        echo "  ./sanitize.sh scan     → Buscar datos sensibles (solo reporta)"
        echo "  ./sanitize.sh clean    → Buscar y reemplazar con placeholders"
        echo "  ./sanitize.sh install  → Instalar pre-commit hook"
        echo "  ./sanitize.sh check    → Para hooks (exit 1 si hay algo)"
        echo ""
        exit 1
        ;;
esac
