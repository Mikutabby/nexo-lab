#!/usr/bin/env python3
"""
🔷 Nexo UI — Web App
Interfaz visual estilo HUD con animaciones, WebSocket en tiempo real,
y versión miniatura sincronizada.
"""

import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_from_directory

# ── Config ─────────────────────────────────────────────────────────────────
STATE_FILE = "/tmp/nexo-ui-state.json"
SYNC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sync")
sys.path.insert(0, SYNC_DIR)

app = Flask(__name__, static_folder="static")


# ── API REST ───────────────────────────────────────────────────────────────
@app.route("/")
def index():
    """Página principal: HUD completo."""
    return render_template("index.html")


@app.route("/mini")
def mini():
    """Versión miniatura sincronizada."""
    return render_template("mini.html")


@app.route("/api/state")
def api_state():
    """Devuelve el estado actual en JSON."""
    try:
        with open(STATE_FILE) as f:
            data = json.load(f)
        return jsonify(data)
    except (FileNotFoundError, json.JSONDecodeError):
        return jsonify({
            "nexo_status": "idle",
            "cpu": 0,
            "ram": 0,
            "temp": 0,
            "error": "state_file_not_found"
        })


@app.route("/api/command", methods=["POST"])
def api_command():
    """Recibe un comando y lo ejecuta en Nexo."""
    data = request.get_json(silent=True) or {}
    command = data.get("command", "").strip()
    if not command:
        return jsonify({"status": "error", "message": "Comando vacío"})

    # Actualizar estado
    state = _read_state()
    state["last_command"] = command
    state["nexo_status"] = "thinking"
    _write_state(state)

    # Ejecutar en thread separado
    def _execute(cmd):
        try:
            result = subprocess.run(
                ["python3", "-c", f"""
import subprocess as sp
try:
    r = sp.run(['bash', '-c', 'echo "Comando recibido: {cmd}"'], capture_output=True, text=True, timeout=30)
    print(r.stdout)
except Exception as e:
    print(f'Error: {{e}}')
"""],
                capture_output=True, text=True, timeout=30
            )
            output = result.stdout.strip() or "Comando ejecutado"
            s = _read_state()
            s["last_response"] = output
            s["nexo_status"] = "idle"
            _write_state(s)
        except Exception as e:
            s = _read_state()
            s["last_response"] = f"Error: {e}"
            s["nexo_status"] = "error"
            _write_state(s)

    thread = threading.Thread(target=_execute, args=(command,), daemon=True)
    thread.start()

    return jsonify({"status": "ok", "command": command})


@app.route("/api/nexo/status")
def api_nexo_status():
    """Endpoint específico para el estado de Nexo."""
    state = _read_state()
    return jsonify({
        "status": state.get("nexo_status", "idle"),
        "active": state.get("nexo_active", False),
        "last_command": state.get("last_command", ""),
        "last_response": state.get("last_response", ""),
    })


# ── Helpers ────────────────────────────────────────────────────────────────
def _read_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _write_state(state):
    tmp = STATE_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f, indent=2)
    os.rename(tmp, STATE_FILE)


# ── Main ───────────────────────────────────────────────────────────────────
def main():
    import argparse
    parser = argparse.ArgumentParser(description="Nexo UI — Web App")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=7070)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    print(f"🔷 Nexo UI Web — http://{args.host}:{args.port}")
    print(f"   Mini: http://{args.host}:{args.port}/mini")
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
