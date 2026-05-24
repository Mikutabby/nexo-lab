#!/bin/bash
# Wallpaper animado con mpv
# Nexo - Asistente del hogar
# Método: mpv directo como ventana tipo DESKTOP

VIDEO="$HOME/Videos/wallpaper/fondo.mp4"
PIDFILE="/tmp/mpv-wallpaper.pid"

# Si no existe el video, salir
[ ! -f "$VIDEO" ] && exit 1

# Matar instancias previas
kill "$(cat "$PIDFILE" 2>/dev/null)" 2>/dev/null
sleep 1
pkill -f "mpv.*fondo-miku" 2>/dev/null
pkill -f "mpv.*fondo.mp4" 2>/dev/null

# Obtener resolución del monitor principal
RES=$(xrandr | grep ' connected' | awk '{print $3}' | head -1)
[ -z "$RES" ] && RES="1366x768"

# Matar el gestor de escritorio XFCE para que no tape el video
killall xfdesktop 2>/dev/null
sleep 1

# Exportar DISPLAY por si acaso
export DISPLAY=:0.0

# Lanzar mpv
mpv --loop --no-audio --no-osc --no-osd-bar --no-border \
    --really-quiet --vo=xv --keep-open \
    --geometry="${RES}+0+0" --title="fondo-miku" \
    --no-window-dragging \
    "$VIDEO" &
MPV_PID=$!
echo "$MPV_PID" > "$PIDFILE"

# Esperar 4 segundos a que la ventana se cree
sleep 4

# Buscar el WID: probar varios métodos
WID=""
for method in \
    "xdotool search --name 'fondo-miku' 2>/dev/null | head -1" \
    "xdotool search --class mpv 2>/dev/null | head -1" \
    "xwininfo -root -tree 2>/dev/null | grep '1366x768' | grep -v 'panel\|wrapper' | head -1 | awk '{print \$1}'"; do
    WID=$(eval "$method")
    [ -n "$WID" ] && break
done

if [ -n "$WID" ]; then
    # Configurar como ventana de escritorio (fondo real)
    xprop -id "$WID" -f _NET_WM_WINDOW_TYPE 32a \
        -set _NET_WM_WINDOW_TYPE '_NET_WM_WINDOW_TYPE_DESKTOP'
    xprop -id "$WID" -f _NET_WM_STATE 32a \
        -set _NET_WM_STATE '_NET_WM_STATE_BELOW, _NET_WM_STATE_SKIP_TASKBAR, _NET_WM_STATE_SKIP_PAGER'
fi

# Iniciar monitor de pausa en background
# Pausa el video cuando hay una ventana de aplicación activa
(
    PAUSADO=0
    while kill -0 "$MPV_PID" 2>/dev/null; do
        # Obtener ventana activa
        ACTIVE_WID=$(xdotool getactivewindow 2>/dev/null)
        
        if [ -n "$ACTIVE_WID" ] && [ "$ACTIVE_WID" != "$WID" ] && [ "$ACTIVE_WID" != "0" ]; then
            # Verificar que sea una ventana de aplicación (no del sistema)
            ACTIVE_CLASS=$(xprop -id "$ACTIVE_WID" WM_CLASS 2>/dev/null)
            case "$ACTIVE_CLASS" in
                *"xfce4-panel"*|*"Xfwm4"*|*"xfdesktop"*|*"plasmashell"*|*"wrapper"*)
                    # Ventana del sistema -> no pausar
                    ;;
                *)
                    # Aplicación -> pausar video
                    if [ "$PAUSADO" -eq 0 ]; then
                        kill -STOP "$MPV_PID" 2>/dev/null
                        PAUSADO=1
                    fi
                    ;;
            esac
        else
            # Sin ventana activa o es el wallpaper -> reanudar
            if [ "$PAUSADO" -eq 1 ]; then
                kill -CONT "$MPV_PID" 2>/dev/null
                PAUSADO=0
            fi
        fi
        
        sleep 2
    done
) &
echo "Wallpaper iniciado (PID: $MPV_PID)"
exit 0
