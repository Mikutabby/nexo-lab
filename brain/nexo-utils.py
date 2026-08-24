#!/usr/bin/env python3
"""
🔧 Nexo Utils — Módulo compartido de utilidades.
Funciones comunes para todos los scripts de Nexo.
"""

import json
from pathlib import Path
from datetime import datetime, timezone

# Paths
NEXO_MEMORY = Path.home() / ".nexo-memory"
NEXO_LOGS = NEXO_MEMORY / "logs"
NEXO_GRAPH_DB = NEXO_MEMORY / "graph-v2.db"

# Ensure directories exist
NEXO_MEMORY.mkdir(parents=True, exist_ok=True)
NEXO_LOGS.mkdir(parents=True, exist_ok=True)

def load_json(file_path, default=None):
    """Load a JSON file, return default if not exists."""
    if file_path.exists():
        with open(file_path) as f:
            return json.load(f)
    return default if default is not None else {}

def save_json(file_path, data):
    """Save data to a JSON file."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def now_iso():
    """Return current time as ISO string."""
    return datetime.now(timezone.utc).isoformat()

def log_message(message, log_file="general.log"):
    """Write a message to a log file."""
    log_path = NEXO_LOGS / log_file
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(log_path, "a") as f:
        f.write(f"[{timestamp}] {message}\n")

def get_temp():
    """Get current CPU temperature."""
    try:
        with open('/sys/class/thermal/thermal_zone1/temp') as f:
            return int(f.read().strip()) // 1000
    except:
        return 0

def get_disk_usage():
    """Get disk usage percentage."""
    import subprocess
    result = subprocess.run(['df', '/'], capture_output=True, text=True)
    lines = result.stdout.strip().split('\n')
    if len(lines) > 1:
        return int(lines[1].split()[4].rstrip('%'))
    return 0

def get_memory_info():
    """Get memory info as dict with total, used, free, percent."""
    import subprocess
    result = subprocess.run(['free'], capture_output=True, text=True)
    for line in result.stdout.split('\n'):
        if line.startswith('Mem:'):
            parts = line.split()
            total = int(parts[1])
            free = int(parts[6])
            used = total - free
            return {
                'total': total,
                'used': used,
                'free': free,
                'percent': int(used / total * 100)
            }
    return {'total': 0, 'used': 0, 'free': 0, 'percent': 0}

def run_command(cmd, timeout=30):
    """Run a shell command and return output."""
    import subprocess
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, shell=isinstance(cmd, str)
        )
        return result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return "❌ Timeout"
    except Exception as e:
        return f"❌ Error: {e}"
