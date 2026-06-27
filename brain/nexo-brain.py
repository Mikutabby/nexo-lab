#!/usr/bin/env python3
"""
🧠 Nexo Brain — Procesador de comandos con personalidad.
Usa el knowledge graph para contexto y responde con voz.
Sin Ollama: procesa comandos comunes directamente + IA remota opcional.
"""

import json
import os
import random
import re
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path

MEMORY_DIR = Path.home() / ".nexo-memory"
DB_PATH = MEMORY_DIR / "graph.db"
MEMORY_JSON = MEMORY_DIR / "memory.json"
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "")

SALUDOS = [
    "Dime, miku",
    "Aquí estoy, ¿qué necesitas?",
    "¿En qué puedo ayudarte?",
    "Te escucho, miku",
    "Dime qué necesitas",
]

RESPUESTAS_NO_ENTIENDO = [
    "No entendí bien, ¿podrías repetirlo?",
    "No sé cómo hacer eso todavía. ¿Qué más?",
    "Eso no lo tengo programado. Decime otra cosa.",
]

BRAIN_REPLIES = [
    "Entendido.",
    "Listo.",
    "Hecho.",
    "Procesado.",
    "Como digas, miku.",
    "Ahí va.",
]


def load_memory():
    if MEMORY_JSON.exists():
        with open(MEMORY_JSON) as f:
            return json.load(f)
    return {}


def load_graph_context():
    if not DB_PATH.exists():
        return ""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT name, data, branch FROM memory_nodes WHERE id NOT IN ('root','user','directives','world') AND data != '' ORDER BY access_count DESC LIMIT 20"
        ).fetchall()
        conn.close()
        parts = []
        for r in rows:
            parts.append(f"[{r['branch']}] {r['name']}: {r['data'][:200]}")
        return "\n".join(parts)
    except Exception:
        return ""


def get_system_info():
    info = {}
    try:
        with open("/proc/loadavg") as f:
            info["load"] = f.read().strip().split()[0]
    except Exception:
        info["load"] = "?"
    try:
        with open("/proc/uptime") as f:
            secs = float(f.read().strip().split()[0])
            h, m = int(secs // 3600), int((secs % 3600) // 60)
            info["uptime"] = f"{h}h {m}m"
    except Exception:
        info["uptime"] = "?"
    try:
        with open("/proc/meminfo") as f:
            data = f.read()
        for line in data.split("\n"):
            if "MemTotal" in line:
                kb = int(line.split()[1])
                info["ram_total"] = f"{kb // 1024}MB"
            elif "MemAvailable" in line:
                kb = int(line.split()[1])
                info["ram_avail"] = f"{kb // 1024}MB"
    except Exception:
        pass
    info["hostname"] = os.uname().nodename
    return info


def get_time_response():
    now = datetime.now()
    return f"Son las {now.hour} con {now.minute} minutos del {now.day} de {now.month}."


def weather_response():
    clima_file = MEMORY_DIR / "hogar" / "clima_cache.json"
    if clima_file.exists():
        try:
            with open(clima_file) as f:
                data = json.load(f)
            auto = data.get("__auto__", {})
            if auto.get("texto"):
                return auto["texto"]
        except Exception:
            pass
    return "No tengo datos del clima guardados."


def get_user_name(memory):
    return memory.get("user", {}).get("name", "miku")


def process_command(text, memory, context, system_info):
    lower = text.lower().strip()

    if re.search(r'\b(hola|hey|oye|nexo)\b', lower) and not any(cmd in lower for cmd in
                                                                  ["hora", "clima", "temperatura", "estado",
                                                                   "sistema", "abre", "abri", "abrir",
                                                                   "busca", "diario", "limpiar", "memoria",
                                                                   "quien", "quién", "como", "cómo", "eres"]):
        return random.choice(SALUDOS)

    if re.search(r'\b(hora|qué hora|que hora|tiempo)\b', lower):
        return get_time_response()

    if re.search(r'\b(clima|temperatura|frío|calor|frío|caliente)\b', lower):
        return weather_response()

    if re.search(r'\b(estado|sistema|como esta|cómo está|rendimiento|cpu|ram|memoria)\b', lower):
        si = system_info
        return (f"CPU load: {si.get('load', '?')}. "
                f"RAM: {si.get('ram_avail', '?')} disponible de {si.get('ram_total', '?')}. "
                f"Uptime: {si.get('uptime', '?')}.")

    if re.search(r'\b(quien eres|quién eres|que eres|qué eres|como te llamas|cómo te llamas|presentate)\b', lower):
        name = memory.get("nexo", {}).get("name", "Nexo")
        creator = memory.get("nexo", {}).get("creator", "mikuyasha")
        return f"Soy {name}, tu asistente del hogar. Fui creado por {creator} para ayudarte con tu PC."

    if re.search(r'\b(gracias|thanks|thank)\b', lower):
        return random.choice(
            ["De nada, miku.", "Para eso estoy.", "Cuando quieras.", "Un placer."])

    if re.search(r'\b(diario|resumen|hoy que hicimos|qué hicimos)\b', lower):
        log_dir = MEMORY_DIR / "log"
        if log_dir.exists():
            logs = list(log_dir.glob("*.log"))
            if logs:
                today = datetime.now().strftime("%Y-%m-%d")
                today_log = log_dir / f"{today}.log"
                if today_log.exists():
                    count = len(today_log.read_text().strip().split("\n"))
                    return f"Hoy tengo {count} interacciones registradas."
                return f"Tengo {len(logs)} días de interacciones guardadas."
            return "No tengo interacciones registradas."
        return "No hay diario disponible."

    if re.search(r'\b(abre|abri|abrir|abrime|abrí)\b', lower):
        app_match = re.search(r'(?:abre|abri|abrir|abrime|abrí)\s+(.+)', lower)
        if app_match:
            app = app_match.group(1).strip()
            apps = {
                "firefox": "firefox",
                "navegador": "firefox",
                "terminal": "xfce4-terminal",
                "consola": "xfce4-terminal",
                "explorador": "thunar",
                "archivos": "thunar",
                "music": "audacious",
                "musica": "audacious",
                "editor": "mousepad",
                "notas": "mousepad",
            }
            cmd = apps.get(app, app)
            try:
                subprocess.Popen([cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return f"Abriendo {app}."
            except Exception:
                return f"No pude abrir {app}."
        return "¿Qué querés que abra?"

    if re.search(r'\b(limpiar|limpia|basura|temp)\b', lower):
        try:
            subprocess.run(["rm", "-rf", "/tmp/*"], shell=True, timeout=10)
            return "Temporal limpiado."
        except Exception:
            return "No pude limpiar el temporal."

    if re.search(r'\b(memoria|recuerda|que sabes|qué sabes|que recuerdas|qué recuerdas)\b', lower):
        mem = memory
        facts = mem.get("user", {}).get("facts", [])
        if facts:
            fact = random.choice(facts)
            return f"Recuerdo: {fact}"
        if context:
            lines = context.strip().split("\n")
            if lines:
                return f"Tengo {len(lines)} datos en mi knowledge graph."
        return "No tengo mucha memoria todavía."

    if re.search(r'\b(red|dispositivos|wifi|router|ip)\b', lower):
        devices = memory.get("network", {}).get("devices", {})
        if devices:
            names = [d.get("name", ip) for ip, d in devices.items()]
            return f"Tengo {len(devices)} dispositivos en la red: {', '.join(names)}."
        return "No hay dispositivos registrados."

    if re.search(r'\b(apagar|shutdown|apaga|off)\b', lower):
        return "No puedo apagar el sistema por seguridad. Tenés que hacerlo manual."

    if re.search(r'\b(ollama|ia|inteligencia|modelo)\b', lower):
        return "Esta PC no puede correr Ollama localmente. Si conectás un servidor con IA, podré responder mejor."

    return None


def speak(text):
    say_script = Path.home() / "nexo-lab" / "nexo-lab" / "voice" / "say.sh"
    if say_script.exists():
        try:
            subprocess.run(["bash", str(say_script), text], timeout=30)
        except Exception:
            pass


def main():
    text = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else sys.stdin.read().strip()

    if not text:
        print("❌ Uso: nexo-brain <comando> | echo 'comando' | nexo-brain")
        sys.exit(1)

    memory = load_memory()
    context = load_graph_context()
    system_info = get_system_info()

    response = process_command(text, memory, context, system_info)

    if response:
        print(response)
        speak(response)
    else:
        fallback = random.choice(RESPUESTAS_NO_ENTIENDO)
        print(fallback)
        speak(fallback)


if __name__ == "__main__":
    main()
