#!/usr/bin/env python3
"""
🔷 Nexo UI — Daemon de sincronización
Gestiona el estado compartido entre Conky, Web UI y Nexo.
Lee info del sistema cada N segundos y la publica via WebSocket.
"""

import argparse
import asyncio
import json
import logging
import os
import signal
import socket
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# ── Config ─────────────────────────────────────────────────────────────────
STATE_FILE = "/tmp/nexo-ui-state.json"
PID_FILE = "/tmp/nexo-ui-daemon.pid"
CONFIG_FILE = os.path.expanduser("~/.config/nexo-ui/nexo-ui.json")
WS_PORT = 7071
UPDATE_INTERVAL = 2.0  # segundos

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(message)s",
    handlers=[
        logging.FileHandler("/tmp/nexo-ui-daemon.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("nexo-ui")


# ── Estado por defecto ─────────────────────────────────────────────────────
DEFAULT_STATE = {
    "nexo_status": "idle",
    "last_command": "",
    "last_response": "",
    "cpu": 0,
    "ram": 0,
    "temp": 0,
    "disk": 0,
    "uptime": "",
    "active_processes": 0,
    "hostname": socket.gethostname(),
    "timestamp": 0,
    "widget_pos": {"x": 0, "y": 0},
    "theme": "dark",
    "nexo_active": False,
    "session_start": datetime.now().isoformat(),
}


# ── Sistema: leer info ────────────────────────────────────────────────────
def read_cpu():
    """Lee porcentaje de CPU promedio."""
    try:
        with open("/proc/stat") as f:
            line = f.readline().strip().split()
        if len(line) >= 5:
            user, nice, system, idle = int(line[1]), int(line[2]), int(line[3]), int(line[4])
            total = user + nice + system + idle
            # Primera lectura
            if not hasattr(read_cpu, "_prev"):
                read_cpu._prev = (total, idle)
                return 0
            prev_total, prev_idle = read_cpu._prev
            diff_total = total - prev_total
            diff_idle = idle - prev_idle
            read_cpu._prev = (total, idle)
            if diff_total > 0:
                return round(100 * (diff_total - diff_idle) / diff_total, 1)
        return 0
    except Exception:
        return 0


def read_ram():
    """Lee porcentaje de RAM usado."""
    try:
        with open("/proc/meminfo") as f:
            data = f.read()
        lines = {l.split(":")[0].strip(): int(l.split(":")[1].strip().split()[0])
                 for l in data.split("\n") if ":" in l and l.strip()}
        total = lines.get("MemTotal", 1)
        available = lines.get("MemAvailable", 0)
        return round(100 * (total - available) / total, 1) if total else 0
    except Exception:
        return 0


def read_temp():
    """Lee temperatura de la CPU."""
    paths = [
        "/sys/class/thermal/thermal_zone0/temp",
        "/sys/class/thermal/thermal_zone1/temp",
        "/sys/class/thermal/thermal_zone2/temp",
    ]
    for p in paths:
        try:
            with open(p) as f:
                val = int(f.read().strip()) // 1000
                return val
        except Exception:
            continue
    return 0


def read_disk():
    """Lee porcentaje de disco usado en /."""
    try:
        st = os.statvfs("/")
        used = (st.f_blocks - st.f_bfree) * st.f_frsize
        total = st.f_blocks * st.f_frsize
        return round(100 * used / total, 1) if total else 0
    except Exception:
        return 0


def read_uptime():
    """Lee tiempo de actividad del sistema."""
    try:
        with open("/proc/uptime") as f:
            uptime_sec = float(f.read().strip().split()[0])
        hours = int(uptime_sec // 3600)
        minutes = int((uptime_sec % 3600) // 60)
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"
    except Exception:
        return "0m"


def read_processes():
    """Cuenta procesos activos."""
    try:
        return len(os.listdir("/proc")) - 2  # menos . y ..
    except Exception:
        return 0


def read_nexo_status():
    """Detecta si Nexo está activo (por PID file u otros indicadores)."""
    pid_file = "/tmp/nexo-wake.pid"
    if os.path.exists(pid_file):
        try:
            with open(pid_file) as f:
                pid = int(f.read().strip())
            os.kill(pid, 0)
            return True, "listening"
        except (ProcessLookupError, ValueError, OSError):
            os.remove(pid_file)
    # Verificar si say.sh se ejecutó recientemente (TTS activo)
    tts_log = "/tmp/nexo-wake.log"
    if os.path.exists(tts_log):
        try:
            mtime = os.path.getmtime(tts_log)
            if time.time() - mtime < 30:
                return True, "speaking"
        except Exception:
            pass
    return False, "idle"


def read_state():
    """Lee el estado actual desde el archivo JSON."""
    global DEFAULT_STATE
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return dict(DEFAULT_STATE)


def write_state(state):
    """Escribe el estado al archivo JSON."""
    state["timestamp"] = time.time()
    # Escribir atómicamente
    tmp = STATE_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f, indent=2)
    os.rename(tmp, STATE_FILE)


def update_system_state():
    """Actualiza el estado con info fresca del sistema."""
    state = read_state()
    state["cpu"] = read_cpu()
    state["ram"] = read_ram()
    state["temp"] = read_temp()
    state["disk"] = read_disk()
    state["uptime"] = read_uptime()
    state["active_processes"] = read_processes()
    nexo_active, nexo_status = read_nexo_status()
    state["nexo_active"] = nexo_active
    if nexo_status != "idle":
        state["nexo_status"] = nexo_status
    state["timestamp"] = time.time()
    write_state(state)
    return state


# ── WebSocket Server ──────────────────────────────────────────────────────
class WebSocketStateBroadcast:
    """Servidor WebSocket mínimo para broadcast de estado en tiempo real."""

    def __init__(self, host="127.0.0.1", port=WS_PORT):
        self.host = host
        self.port = port
        self.clients = set()

    async def handler(self, reader, writer):
        """Maneja una conexión WebSocket."""
        # Handshake HTTP -> WebSocket
        try:
            request = (await reader.read(1024)).decode()
            if "Upgrade: websocket" not in request and "upgrade: websocket" not in request.lower():
                writer.close()
                return

            # Extraer key para handshake
            import hashlib, base64
            key = ""
            for line in request.split("\r\n"):
                if "Sec-WebSocket-Key" in line:
                    key = line.split(":")[1].strip()
                    break

            if not key:
                writer.close()
                return

            accept = base64.b64encode(
                hashlib.sha1((key + "258EAFA5-E914-47DA-95CA-5AB5C5E46B1F").encode()).digest()
            ).decode()

            response = (
                "HTTP/1.1 101 Switching Protocols\r\n"
                "Upgrade: websocket\r\n"
                "Connection: Upgrade\r\n"
                f"Sec-WebSocket-Accept: {accept}\r\n"
                "\r\n"
            )
            writer.write(response.encode())
            await writer.drain()

            # Agregar cliente
            self.clients.add(writer)
            log.info(f"WebSocket cliente conectado ({len(self.clients)} total)")

            # Mantener conexión viva
            try:
                while True:
                    await asyncio.sleep(30)
                    # Ping frame
                    try:
                        writer.write(b"\x89\x00")
                        await writer.drain()
                    except Exception:
                        break
            except (ConnectionResetError, BrokenPipeError):
                pass
            finally:
                self.clients.discard(writer)
                try:
                    writer.close()
                except Exception:
                    pass
                log.info(f"WebSocket cliente desconectado ({len(self.clients)} total)")

        except Exception as e:
            log.debug(f"Error en WebSocket: {e}")
            self.clients.discard(writer)

    async def broadcast(self, data):
        """Envía datos JSON a todos los clientes conectados."""
        if not self.clients:
            return
        message = json.dumps({"type": "state_update", "data": data})
        # Empaquetar en frame WebSocket
        frame = self._encode_frame(message.encode())
        dead = set()
        for writer in self.clients:
            try:
                writer.write(frame)
                await writer.drain()
            except Exception:
                dead.add(writer)
        self.clients -= dead

    @staticmethod
    def _encode_frame(payload):
        """Codifica un payload en un frame WebSocket (texto, sin enmascarar)."""
        frame = bytearray()
        frame.append(0x81)  # FIN + opcode texto
        length = len(payload)
        if length < 126:
            frame.append(length)
        elif length < 65536:
            frame.append(126)
            frame.extend(length.to_bytes(2, "big"))
        else:
            frame.append(127)
            frame.extend(length.to_bytes(8, "big"))
        frame.extend(payload)
        return bytes(frame)

    async def start_server(self):
        server = await asyncio.start_server(self.handler, self.host, self.port)
        log.info(f"WebSocket server en ws://{self.host}:{self.port}")
        async with server:
            await server.serve_forever()


# ── Daemon ────────────────────────────────────────────────────────────────
async def async_main():
    """Punto de entrada asíncrono principal."""
    ws_server = WebSocketStateBroadcast()
    log.info(f"🔷 Nexo UI Daemon iniciado (PID: {os.getpid()})")
    # Primera actualización inmediata
    state = update_system_state()
    await ws_server.broadcast(state)

    async def loop():
        while True:
            await asyncio.sleep(UPDATE_INTERVAL)
            state = update_system_state()
            await ws_server.broadcast(state)

    await asyncio.gather(
        loop(),
        ws_server.start_server(),
    )


# ── Daemon ────────────────────────────────────────────────────────────────
def daemonize():
    """Fork y desacople completo."""
    pid = os.fork()
    if pid > 0:
        # Padre: guardar PID y salir
        with open(PID_FILE, "w") as f:
            f.write(str(pid))
        print(pid)
        sys.exit(0)

    # Hijo
    os.setsid()
    signal.signal(signal.SIGHUP, signal.SIG_IGN)
    with open(os.devnull, "r") as nul:
        os.dup2(nul.fileno(), 0)
    # Redirigir salida al log
    sys.stdout = open("/tmp/nexo-ui-daemon.log", "a")
    sys.stderr = open("/tmp/nexo-ui-daemon.log", "a")
    os.chdir("/")

    # Iniciar event loop
    asyncio.run(async_main())


def main():
    parser = argparse.ArgumentParser(description="Nexo UI — Daemon de sincronización")
    parser.add_argument("command", nargs="?", default="start",
                        choices=["start", "stop", "restart", "status", "foreground"],
                        help="Comando (defecto: start)")
    args = parser.parse_args()

    if args.command == "status":
        if os.path.exists(PID_FILE):
            try:
                with open(PID_FILE) as f:
                    pid = int(f.read().strip())
                os.kill(pid, 0)
                print(f"🔷 Nexo UI Daemon: activo (PID: {pid})")
                return 0
            except (ProcessLookupError, ValueError):
                os.remove(PID_FILE)
        print("🔷 Nexo UI Daemon: inactivo")
        return 1

    elif args.command == "stop":
        if not os.path.exists(PID_FILE):
            print("❌ Nexo UI Daemon no está corriendo")
            return 1
        try:
            with open(PID_FILE) as f:
                pid = int(f.read().strip())
            os.kill(pid, signal.SIGTERM)
            os.remove(PID_FILE)
            print("✅ Nexo UI Daemon detenido")
        except ProcessLookupError:
            os.remove(PID_FILE)
            print("✅ Nexo UI Daemon detenido (PID no existía)")
        except Exception as e:
            print(f"❌ Error: {e}")
            return 1
        return 0

    elif args.command == "foreground":
        asyncio.run(async_main())

    else:  # start
        if os.path.exists(PID_FILE):
            try:
                with open(PID_FILE) as f:
                    pid = int(f.read().strip())
                os.kill(pid, 0)
                print(f"❌ Ya está corriendo (PID: {pid})")
                return 1
            except (ProcessLookupError, ValueError):
                os.remove(PID_FILE)
        pid = daemonize()
        print(f"✅ Nexo UI Daemon iniciado (PID: {pid})")
        return 0


if __name__ == "__main__":
    sys.exit(main())
