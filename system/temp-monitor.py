#!/usr/bin/env python3
"""
temp-monitor.py — Monitor de temperatura del sistema
=====================================================
Versión mejorada en Python con:
- Monitoreo continuo de temperatura
- Alertas por parlantes y notificaciones
- Apagado automático en caso crítico
- Cancelación de apagado
- Mejor manejo de errores

Uso:
    temp-monitor.py              → monitoreo continuo
    temp-monitor.py --once       → una sola lectura
    temp-monitor.py --cancel     → cancelar apagado
    temp-monitor.py --status     → ver estado actual
    temp-monitor.py --help       → ayuda
"""

import os
import sys
import time
import subprocess
from pathlib import Path
from typing import Optional

# ── Configuración ──────────────────────────────────────────────────────────
VERSION = "2.0"
WARN_TEMP = 75      # Alerta temprana
CRIT_TEMP = 80      # Shutdown
COOLDOWN = 480      # 8 minutos en segundos
LOG_TAG = "temp-monitor"
STATUS_FILE = Path("/tmp/temp-monitor-status")
COOLDOWN_FILE = Path("/tmp/temp-monitor-cooldown")

# ── Colores ────────────────────────────────────────────────────────────────
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'

def info(msg: str) -> None:
    print(f"{Colors.BLUE}ℹ️  {Colors.NC} {msg}")

def ok(msg: str) -> None:
    print(f"{Colors.GREEN}✅{Colors.NC} {msg}")

def warn(msg: str) -> None:
    print(f"{Colors.YELLOW}⚠️  {Colors.NC} {msg}")

def err(msg: str) -> None:
    print(f"{Colors.RED}❌{Colors.NC} {msg}")

# ── Utilidades ─────────────────────────────────────────────────────────────
def run_cmd(cmd: List[str], check: bool = False) -> subprocess.CompletedProcess:
    """Ejecuta un comando y retorna el resultado."""
    try:
        return subprocess.run(cmd, capture_output=True, text=True)
    except Exception as e:
        warn(f"Error ejecutando {cmd[0]}: {e}")
        return subprocess.CompletedProcess(cmd, 1, "", str(e))

def read_temperature() -> Optional[int]:
    """Lee la temperatura del sistema."""
    # Intentar thermal_zone1
    thermal1 = Path("/sys/class/thermal/thermal_zone1/temp")
    if thermal1.exists():
        try:
            temp_raw = thermal1.read_text().strip()
            return int(temp_raw) // 1000
        except Exception:
            pass
    
    # Intentar thermal_zone0
    thermal0 = Path("/sys/class/thermal/thermal_zone0/temp")
    if thermal0.exists():
        try:
            temp_raw = thermal0.read_text().strip()
            return int(temp_raw) // 1000
        except Exception:
            pass
    
    # Intentar con sensors
    try:
        result = run_cmd(["sensors"])
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if "Package id 0:" in line:
                    # Extraer temperatura
                    import re
                    match = re.search(r'([+-]?\d+\.\d+)°C', line)
                    if match:
                        return int(float(match.group(1)))
    except Exception:
        pass
    
    return None

def send_notification(title: str, body: str, urgency: str = "critical", timeout: int = 6000) -> None:
    """Envía una notificación."""
    try:
        subprocess.run(
            ["notify-send", "-u", urgency, "-t", str(timeout), title, body],
            capture_output=True
        )
    except Exception:
        pass

def speak(text: str) -> None:
    """Habla por los parlantes."""
    try:
        subprocess.run(["spd-say", text], capture_output=True)
    except Exception:
        pass

def wall(message: str) -> None:
    """Envía mensaje a todos los usuarios."""
    try:
        subprocess.run(["wall", message], capture_output=True)
    except Exception:
        pass

def log(level: str, message: str) -> None:
    """Registra en el log del sistema."""
    try:
        subprocess.run(
            ["logger", "-t", LOG_TAG, f"[{level}] {message}"],
            capture_output=True
        )
    except Exception:
        pass

# ── Funciones principales ──────────────────────────────────────────────────
def check_temperature() -> int:
    """Verifica la temperatura y toma acciones si es necesario."""
    temp = read_temperature()
    
    if temp is None:
        err("No se pudo leer la temperatura")
        return 1
    
    # Guardar estado
    STATUS_FILE.write_text(str(temp))
    log("INFO", f"{temp}°C")
    
    # Pre-alerta
    if WARN_TEMP <= temp < CRIT_TEMP:
        log("WARN", f"Precaución: {temp}°C")
        send_notification(
            f"🔥 Temperatura: {temp}°C",
            "Cuidado, se está calentando."
        )
        speak(f"Cuidado, la temperatura está en {temp} grados")
        return 0
    
    # Crítico
    if temp >= CRIT_TEMP:
        # Si ya estamos en cooldown, no repetir
        if COOLDOWN_FILE.exists():
            return 0
        
        log("CRIT", f"¡CRÍTICO! {temp}°C")
        
        # Hablar por los parlantes
        speak(
            f"ATENCIÓN. Temperatura crítica: {temp} grados. "
            f"El sistema se apagará en dos minutos. Decí no para cancelar."
        )
        
        send_notification(
            f"🔥🔥 CRÍTICO: {temp}°C",
            "Apagado en 2 minutos.\nGuardá tu trabajo.\nCancelar: rm -f /tmp/temp-monitor-cooldown",
            timeout=12000
        )
        
        wall(
            f"🔥  TEMPERATURA CRÍTICA: {temp}°C\n"
            f"⏳  Apagado en 2 minutos. Guardá tu trabajo.\n"
            f"✋  Decí NO para cancelar."
        )
        
        COOLDOWN_FILE.touch()
        
        # Esperar 1 minuto
        time.sleep(60)
        
        # Si cancelaron, salir
        if not COOLDOWN_FILE.exists():
            log("INFO", "Apagado cancelado por el usuario")
            speak("Apagado cancelado")
            return 0
        
        # Segundo aviso
        speak("Un minuto restante. Guardá tu trabajo.")
        send_notification(
            "⏳ 1 minuto restante",
            "Apagado en 60 segundos.",
            timeout=8000
        )
        wall("⏳  1 minuto para el apagado.")
        
        time.sleep(30)
        
        if not COOLDOWN_FILE.exists():
            log("INFO", "Apagado cancelado por el usuario")
            speak("Apagado cancelado")
            return 0
        
        # Tercer aviso
        speak("Treinta segundos. Último aviso.")
        send_notification(
            "⏳ 30 segundos",
            "Último aviso.",
            timeout=8000
        )
        wall("⏳  30 segundos.")
        
        time.sleep(30)
        
        if not COOLDOWN_FILE.exists():
            log("INFO", "Apagado cancelado por el usuario")
            speak("Apagado cancelado")
            return 0
        
        # Apagar y programar reinicio
        speak("Apagando sistema")
        run_cmd(["sudo", "/sbin/rtcwake", "-m", "off", "-s", str(COOLDOWN)])
        run_cmd(["sudo", "/usr/bin/systemctl", "poweroff"])
    
    return 0

def cancel_shutdown() -> None:
    """Cancela un apagado programado."""
    if COOLDOWN_FILE.exists():
        COOLDOWN_FILE.unlink()
        run_cmd(["sudo", "rtcwake", "-m", "disable"])
        ok("Apagado cancelado")
        speak("Apagado cancelado")
    else:
        info("No hay apagado programado")

def show_status() -> None:
    """Muestra el estado actual del monitor."""
    temp = read_temperature()
    
    if temp is None:
        err("No se pudo leer la temperatura")
        return
    
    print()
    info("🌡️  Estado del monitor de temperatura:")
    print()
    print(f"  🌡️  Temperatura actual: {temp}°C")
    print(f"  ⚠️  Umbral de alerta: {WARN_TEMP}°C")
    print(f"  🔥 Umbral crítico: {CRIT_TEMP}°C")
    
    if COOLDOWN_FILE.exists():
        print()
        warn("⚠️  Hay un apagado programado en curso")
        info("   Para cancelar: python3 temp-monitor.py --cancel")
    
    print()

def show_help() -> None:
    """Muestra la ayuda."""
    print(f"""
╔══════════════════════════════════════════════╗
║   🌡️  temp-monitor.py v{VERSION}              ║
║   Monitor de temperatura del sistema        ║
╚══════════════════════════════════════════════╝

USO:
  temp-monitor.py              Monitoreo continuo
  temp-monitor.py --once       Una sola lectura
  temp-monitor.py --cancel     Cancelar apagado
  temp-monitor.py --status     Ver estado actual
  temp-monitor.py --help       Esta ayuda

CONFIGURACIÓN:
  ⚠️  Alerta: {WARN_TEMP}°C
  🔥 Crítico: {CRIT_TEMP}°C
  ⏳ Cooldown: {COOLDOWN}s ({COOLDOWN//60} min)

NOTAS:
  - Ejecutar con cron cada 2 minutos
  - Cancelar apagado: python3 temp-monitor.py --cancel
  - Estado: /tmp/temp-monitor-status
""")

# ── Main ───────────────────────────────────────────────────────────────────
def main() -> int:
    args = sys.argv[1:]
    
    if "--help" in args or "-h" in args:
        show_help()
        return 0
    
    if "--version" in args or "-v" in args:
        print(f"Nexo Temp Monitor v{VERSION}")
        return 0
    
    if "--cancel" in args:
        cancel_shutdown()
        return 0
    
    if "--status" in args:
        show_status()
        return 0
    
    if "--once" in args:
        return check_temperature()
    
    # Modo continuo
    info("🔄 Iniciando monitoreo de temperatura...")
    info(f"   ⚠️  Alerta: {WARN_TEMP}°C")
    info(f"   🔥 Crítico: {CRIT_TEMP}°C")
    info("   Presioná Ctrl+C para salir")
    print()
    
    try:
        while True:
            check_temperature()
            time.sleep(120)  # 2 minutos
    except KeyboardInterrupt:
        print()
        info("Monitoreo detenido")
        return 0

if __name__ == "__main__":
    sys.exit(main())
