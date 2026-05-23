"""
🌐 Nexo 2.0 — Command Server HTTP

Recibe comandos vía HTTP POST y los procesa con NexoEngine.
Compatible con nexo-ui (web HUD) y cualquier cliente HTTP.

Endpoints:
  POST /command   — Envía un comando al engine
  GET  /status    — Estado actual del engine
  GET  /health    — Healthcheck
"""

import argparse
import json
import os
import sys
import threading
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_DIR))

STATE_FILE = "/tmp/nexo2-state.json"

_engine = None
_tts_enabled = True


def get_engine():
    global _engine
    if _engine is None:
        from core.nexo_engine import NexoEngine
        _engine = NexoEngine()
    return _engine


def write_state(**updates):
    """Escribe actualizaciones al state file compartido."""
    state = {}
    try:
        with open(STATE_FILE) as f:
            state = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    state.update(updates)
    state["timestamp"] = time.time()

    tmp = STATE_FILE + ".tmp"
    try:
        with open(tmp, "w") as f:
            json.dump(state, f, indent=2)
        os.rename(tmp, STATE_FILE)
    except Exception:
        pass


class CommandHandler(BaseHTTPRequestHandler):
    """Maneja las peticiones HTTP al servidor de comandos."""

    def do_POST(self):
        if self.path == "/command":
            self._handle_command()
        else:
            self._json_response(404, {"error": "Not found"})

    def do_GET(self):
        if self.path == "/status":
            self._handle_status()
        elif self.path == "/health":
            self._json_response(200, {"status": "ok", "app": "nexo2"})
        else:
            self._json_response(404, {"error": "Not found"})

    def _handle_command(self):
        """Recibe un comando, lo procesa y devuelve el resultado."""
        content_len = int(self.headers.get("Content-Length", 0))
        if content_len == 0:
            self._json_response(400, {"error": "Empty request body"})
            return

        body = self.rfile.read(content_len)
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self._json_response(400, {"error": "Invalid JSON"})
            return

        command = data.get("command", "").strip()
        if not command:
            self._json_response(400, {"error": "Empty command"})
            return

        # Actualizar estado: procesando
        write_state(nexo_status="thinking", last_command=command)

        # Procesar comando en thread separado
        def _process(cmd):
            engine = get_engine()
            try:
                response = engine.process_text(cmd)
                write_state(
                    nexo_status="idle",
                    last_command=cmd,
                    last_response=response,
                )
            except Exception as e:
                write_state(
                    nexo_status="error",
                    last_command=cmd,
                    last_response=f"Error: {e}",
                )

        thread = threading.Thread(target=_process, args=(command,), daemon=True)
        thread.start()

        self._json_response(200, {"status": "ok", "command": command})

    def _handle_status(self):
        """Devuelve el estado actual del engine."""
        engine = get_engine()
        status = engine.get_status()

        # Leer state file para info adicional
        try:
            with open(STATE_FILE) as f:
                state = json.load(f)
                status.update(state)
        except Exception:
            pass

        self._json_response(200, status)

    def _json_response(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def log_message(self, format, *args):
        """Silenciar logs del servidor."""
        pass


def start_server(engine, host="127.0.0.1", port=7072):
    """Inicia el servidor HTTP."""
    global _engine, _tts_enabled
    _engine = engine
    _tts_enabled = engine.tts_enabled

    print(f"🧠 Nexo 2.0 Command Server")
    print(f"   POST http://{host}:{port}/command")
    print(f"   GET  http://{host}:{port}/status")
    print(f"   GET  http://{host}:{port}/health")
    print(f"   State file: {STATE_FILE}")

    server = HTTPServer((host, port), CommandHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Servidor detenido")
        server.server_close()


def main():
    parser = argparse.ArgumentParser(description="Nexo 2.0 Command Server")
    parser.add_argument("--port", type=int, default=7072)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()

    engine = get_engine()
    start_server(engine, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
