#!/bin/bash
# check-identity.sh - Verifica quién está frente a la PC usando reconocimiento facial
# Almacena el resultado en /tmp/opencode-identity.json
# Uso: check-identity.sh  -> imprime "miku", "unknown" o "nobody"

IDENTITY_FILE="/tmp/opencode-identity.json"
SCRIPT_DIR="/home/miku/.local/bin"

# Ejecutar reconocimiento facial
RESULT=$(python3 "$SCRIPT_DIR/face-recognize.py" whoami 2>&1)
EXIT_CODE=$?

# La primera línea del output es el estado: "miku", "unknown" o "no_face"
FIRST_LINE=$(echo "$RESULT" | head -1)

case "$FIRST_LINE" in
    miku)
        IDENTITY="miku"
        echo "miku"
        ;;
    unknown)
        IDENTITY="unknown"
        echo "unknown"
        ;;
    no_face)
        IDENTITY="nobody"
        echo "nobody"
        ;;
    *)
        # Fallback: si por alguna razón no se puede determinar
        IDENTITY="unknown"
        echo "unknown"
        ;;
esac

# Guardar identidad con timestamp
cat > "$IDENTITY_FILE" <<EOF
{"identity":"$IDENTITY","timestamp":$(date +%s)}
EOF

exit 0
