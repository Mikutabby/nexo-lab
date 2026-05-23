"""
🧠 Nexo 2.0 — Engine principal
================================
Orquestador que procesa comandos, rutea tools y gestiona la memoria.

Arquitectura:
  1. Recibe texto del usuario
  2. Detecta intención (Ollama/Gemini → tool call o respuesta directa)
  3. Ejecuta la tool correspondiente
  4. Devuelve respuesta (texto + TTS opcional)

Basado en JARVIS (Blazehue) pero adaptado para Linux + Ollama.
"""

import json
import os
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional

# Asegurar path del proyecto
APP_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(APP_DIR))

# ── Config ─────────────────────────────────────────────────────────────────
CONFIG_PATH = APP_DIR / "config" / "config.json"
PROMPT_PATH = APP_DIR / "core" / "prompt.txt"

def load_config() -> dict:
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}

def save_config(cfg: dict):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2), encoding="utf-8")

def load_system_prompt() -> str:
    try:
        return PROMPT_PATH.read_text(encoding="utf-8")
    except Exception:
        return "Eres Nexo, un asistente AI eficiente y con personalidad. Responde en español."


class ToolExecutor:
    """
    Ejecuta tools por nombre.
    Cada tool recibe (parameters: dict, response: any, player: any) y devuelve str.
    Adaptado del main.py de JARVIS.
    """

    def __init__(self, nexo: 'NexoEngine'):
        self.nexo = nexo

    async def execute(self, name: str, args: dict) -> str:
        """Ejecuta una tool por nombre y devuelve resultado en texto."""
        import asyncio
        loop = asyncio.get_event_loop()

        result = "Done."

        try:
            if name == "web_search":
                from actions.web_search import web_search as _ws
                query = args.get("query", "") if isinstance(args, dict) else str(args)
                r = await loop.run_in_executor(None, lambda: _ws(query))
                result = r or "Búsqueda completada."

            elif name == "weather_report":
                from actions.weather_report import weather_report as _wr
                city = args.get("city", "") if isinstance(args, dict) else str(args)
                r = await loop.run_in_executor(None, lambda: _wr(city))
                result = r or "Clima entregado."

            elif name == "system_monitor":
                from actions.system_monitor import system_monitor as _sm
                r = await loop.run_in_executor(None, lambda: _sm(parameters=args, player=self.nexo))
                result = r or "Monitor listo."

            elif name == "spotify_control":
                from actions.spotify_control import spotify_control as _sc
                r = await loop.run_in_executor(None, lambda: _sc(parameters=args, player=self.nexo))
                result = r or "Spotify listo."

            elif name == "youtube_video":
                from actions.youtube_video import youtube_video as _yv
                r = await loop.run_in_executor(None, lambda: _yv(parameters=args, response=None, player=self.nexo))
                result = r or "YouTube listo."

            elif name == "file_controller":
                from actions.file_controller import file_controller as _fc
                r = await loop.run_in_executor(None, lambda: _fc(parameters=args, player=self.nexo))
                result = r or "Archivo procesado."

            elif name == "reminder":
                from actions.reminder import reminder as _rem
                r = await loop.run_in_executor(None, lambda: _rem(parameters=args, response=None, player=self.nexo))
                result = r or "Recordatorio listo."

            elif name == "scheduler":
                from actions.scheduler import scheduler as _sched
                r = await loop.run_in_executor(None, lambda: _sched(parameters=args, player=self.nexo, speak=self.nexo.say))
                result = r or "Tarea programada."

            elif name == "knowledge_base":
                from actions.knowledge_base import knowledge_base as _kb
                r = await loop.run_in_executor(None, lambda: _kb(parameters=args, player=self.nexo))
                result = r or "Base de conocimiento lista."

            elif name == "goals":
                from actions.goals import goals as _gl
                r = await loop.run_in_executor(None, lambda: _gl(parameters=args, player=self.nexo))
                result = r or "Objetivos listos."

            elif name == "morning_brief":
                from actions.morning_brief import morning_brief as _mb
                r = await loop.run_in_executor(None, lambda: _mb(parameters=args, player=self.nexo))
                result = r or "Aquí está tu informe del día."

            elif name == "user_profile":
                from actions.user_profile import user_profile as _up
                r = await loop.run_in_executor(None, lambda: _up(parameters=args, player=self.nexo))
                result = r or "Perfil listo."

            elif name == "smart_home":
                from actions.smart_home import smart_home as _sh
                r = await loop.run_in_executor(None, lambda: _sh(parameters=args, player=self.nexo))
                result = r or "Hogar listo."

            elif name == "browser_control":
                from actions.browser_control import browser_control as _bc
                r = await loop.run_in_executor(None, lambda: _bc(parameters=args, player=self.nexo))
                result = r or "Navegador listo."

            elif name == "save_memory":
                from memory.memory_manager import remember as _mem_save
                cat = args.get("category", "notes")
                key = args.get("key", "")
                val = args.get("value", "")
                if key and val:
                    _mem_save(key, val, cat)
                    result = f"Recordado: {cat}/{key}"
                else:
                    result = "Faltan key/value para guardar en memoria."

            else:
                result = f"Tool desconocida: {name}"

        except Exception as e:
            result = f"Error en tool '{name}': {e}"
            traceback.print_exc()

        return result


class NexoEngine:
    """
    Motor principal de Nexo 2.0.
    """

    def __init__(self):
        self.config = load_config()
        self.app_dir = APP_DIR
        self.data_dir = Path(self.config.get("data_dir", str(APP_DIR / ".data")))
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Inicializar memoria
        self._init_memory()

        # Inicializar tool executor
        self.tool_executor = ToolExecutor(self)

        # Estado
        self.running = False
        self.last_activity = datetime.now()
        self.context_history: list[dict] = []

        # TTS
        self.tts_enabled = self.config.get("tts_enabled", True)
        self._say_script = os.path.expanduser("~/.opencode/say.sh")

        print(f"🧠 Nexo 2.0 — Inicializado")
        print(f"   Config: {CONFIG_PATH}")

    def _init_memory(self):
        """Inicializa el sistema de memoria."""
        # Asegurar que memory_manager usa nuestro data_dir
        try:
            from memory.memory_manager import load_memory, save_memory, update_memory
            self.memory_load = load_memory
            self.memory_save = save_memory
            self.memory_update = update_memory
            # Cargar memoria al inicio
            self.memory = self.memory_load()
            print(f"   Memoria cargada: {len(self.memory)} categorías")
        except Exception as e:
            print(f"   ⚠️ Memoria no disponible: {e}")
            self.memory_load = lambda: {}
            self.memory_save = lambda x: None
            self.memory_update = lambda x: {}
            self.memory = {}

    # ── TTS ─────────────────────────────────────────────────────────

    def say(self, text: str):
        """Envía texto a TTS."""
        if not text or not self.tts_enabled:
            return
        try:
            import subprocess
            subprocess.Popen(
                ["bash", self._say_script, text],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            pass

    # ── Procesamiento ───────────────────────────────────────────────

    def process_text(self, text: str) -> str:
        """
        Procesa un texto de entrada y devuelve la respuesta.
        """
        text = text.strip()
        if not text:
            return "¿Decime?"

        self.last_activity = datetime.now()
        text_lower = text.lower()

        # ── Comandos del sistema ──
        if text_lower in ("salir", "exit", "chau", "adiós", "hasta luego"):
            return "¡Hasta luego miku!"

        if text_lower in ("ayuda", "help", "comandos", "qué sabes hacer", "qué haces", "que sabes hacer"):
            return self._show_help()

        # ── Intentar con keywords primero (rápido) ──
        keyword_result = self._keyword_fallback(text)
        if keyword_result:
            return keyword_result

        # ── Si no matcheó keywords, intentar con Ollama ──
        if self.config.get("ollama_enabled", True):
            ollama_response = self._try_ollama(text)
            if ollama_response:
                return ollama_response

        return "No entendí bien. Probá con 'ayuda' para ver qué sé hacer."

    def _try_ollama(self, text: str) -> Optional[str]:
        """Intenta procesar con Ollama con timeout corto."""
        from concurrent.futures import ThreadPoolExecutor, TimeoutError

        def _do_ollama():
            from actions.ollama_provider import chat as ollama_chat, is_available
            from memory.memory_manager import format_memory_for_prompt

            if not is_available():
                return None

            memory = self.memory_load()
            memory_context = format_memory_for_prompt(memory)

            system = load_system_prompt()
            if memory_context:
                system += f"\n\n{memory_context}"

            full_prompt = f"{system}\n\nUsuario: {text}\nNexo:"
            return ollama_chat(full_prompt)

        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(_do_ollama)
                response = future.result(timeout=30)  # timeout 30s
                return response
        except TimeoutError:
            print("⚠️ Ollama timeout (30s)")
        except Exception as e:
            print(f"⚠️ Ollama error: {e}")
        return None

    def _keyword_fallback(self, text: str) -> Optional[str]:
        """Fallback por keywords + actions."""
        text_lower = text.lower()

        # ── Saludos ──
        if any(w in text_lower for w in ["hola", "buenas", "qué tal", "que tal", "hey"]):
            return "¡Hola miku! ¿En qué andamos?"

        if "gracias" in text_lower or "graciass" in text_lower:
            return "¡Para eso estoy! Cuando quieras."

        if any(w in text_lower for w in ["quién sos", "quien sos", "tu nombre", "cómo te llamas"]):
            return "Soy Nexo 2.0, tu asistente del hogar. Creado por miku."

        # ── Hora ──
        if any(w in text_lower for w in ["hora", "que hora", "qué hora"]):
            ahora = datetime.now().strftime("%H:%M")
            return f"Son las {ahora}."

        # ── Temperatura ──
        if any(w in text_lower for w in ["temperatura", "calor"]):
            try:
                temp = open("/sys/class/thermal/thermal_zone1/temp").read().strip()
                temp_c = round(int(temp) / 1000, 1)
                return f"La temperatura del CPU es de {temp_c}°C."
            except:
                return "No pude leer la temperatura del sistema."

        # ── Sistema ──
        if any(w in text_lower for w in ["cpu", "sistema", "pc", "computador", "rendimiento"]):
            import psutil
            cpu = psutil.cpu_percent()
            ram = psutil.virtual_memory().percent
            return f"CPU al {cpu}%, RAM al {ram}%. Todo en orden."

        # ── Clima ──
        if any(w in text_lower for w in ["clima", "clima en", "clima de", "tiempo en", "tiempo de", "qué temperatura hace"]):
            # Extraer ciudad: "clima Bogotá", "clima en Bogotá", etc.
            ciudad = text
            for prefix in ["clima en ", "clima de ", "tiempo en ", "tiempo de ", "qué temperatura hace en ", "qué temperatura hace en ", "clima "]:
                if prefix in text_lower:
                    ciudad = text[text_lower.index(prefix) + len(prefix):].strip()
                    break
            if ciudad and ciudad.lower() in ("clima", "tiempo", ""):
                ciudad = "Bogotá"  # default
            if ciudad:
                from actions.weather_report import weather_report
                return weather_report(ciudad)
            return "Decime qué ciudad para consultar el clima."

        # ── Búsqueda web ──
        if any(w in text_lower[:10] for w in ["buscá", "busca", "googleá", "googlea", "investigá", "investiga"]):
            query = text
            for prefix in ["buscá ", "busca ", "googleá ", "googlea ", "investigá ", "investiga "]:
                if prefix in text_lower:
                    query = text[text_lower.index(prefix) + len(prefix):].strip()
                    break
            if query and query.lower() not in ("buscá", "busca", "googleá", "googlea", ""):
                from actions.web_search import web_search
                return web_search(query)
            return "¿Qué querés que busque?"

        # ── Listar archivos ──
        is_list_cmd = any(w in text_lower for w in
            ["listá archivos", "lista archivos", "qué hay en", "mostrame", "archivos en"])
        is_list_simple = text_lower in ("listá", "lista", "archivos", "archivo")
        if is_list_cmd or is_list_simple:
            from actions.file_controller import list_files as _list_files
            path = "home"
            for prefix in ["qué hay en ", "mostrame ", "archivos en ",
                           "listá archivos ", "lista archivos ", "listá ", "lista "]:
                if text_lower.startswith(prefix):
                    p = text[len(prefix):].strip()
                    if p and p.lower() not in ("archivos", "archivo", "carpeta", "directorio"):
                        path = p
                    break
            return _list_files(path)

        # ── Base de conocimiento (guardar) — ANTES que recordatorios genéricos ──
        if any(w in text_lower for w in ["recordá que", "aprendé que", "guarda esto", "anotá"]):
            from actions.knowledge_base import kb_add
            content = text
            for prefix in ["recordá que ", "aprendé que ", "guarda esto: ", "anotá: ", "anotá ", "guarda esto "]:
                if text_lower.startswith(prefix):
                    content = text[len(prefix):].strip()
                    break
            if content and len(content) > 5:
                return kb_add(content[:60], content)
            return "¿Qué querás que recuerde?"

        # ── Recordatorios ──
        if any(w in text_lower for w in ["recordá", "recuerda", "recordatorio", "acordate"]):
            return (
                "Para crear un recordatorio decime: "
                "'recordá [mensaje] el [YYYY-MM-DD] a las [HH:MM]'. "
                "Ej: 'recordá reunión el 2026-05-25 a las 15:00'"
            )

        # ── Navegador / Abrir páginas (ANTES que YouTube para evitar conflicto) ──
        if any(w in text_lower for w in ["abrí ", "abri ", "abre ", "abrir ",
                                          "navegador", "página", "pagina",
                                          "andá a", "anda a", "chrome", "firefox"]):
            import webbrowser
            url = text
            for prefix in ["abrí ", "abri ", "abre ", "abrir ", "navegador ", "andá a ", "anda a ",
                           "página ", "pagina ", "chrome ", "firefox "]:
                if text_lower.startswith(prefix):
                    url = text[len(prefix):].strip()
                    break
            # Si solo dijo "navegador", "chrome", etc sin URL
            if url.lower() in ("abrí", "abri", "abre", "abrir", "navegador", "página", "pagina",
                               "chrome", "firefox", "andá a", "anda a"):
                return "¿Qué página querés abrir? Decí: 'abrí youtube.com'"
            # Si tiene punto, asumir URL
            if "." in url and " " not in url:
                if not url.startswith("http"):
                    url = "https://" + url
                webbrowser.open(url)
                return f"Abriendo {url}"
            else:
                # Sin punto: buscar en Google
                from actions.web_search import web_search
                return web_search(url)

        # ── YouTube ──
        if any(w in text_lower for w in ["youtube", "video", "poné", "poné video", "mira", "mirá"]):
            from actions.youtube_video import search_and_play
            query = text
            for prefix in ["poné video ", "poné ", "mirá ", "mira ", "youtube ", "video "]:
                if text_lower.startswith(prefix):
                    query = text[len(prefix):].strip()
                    break
            # Si es solo "youtube" o "video", pedir query
            if query.lower() in ("youtube", "video", "poné", "mirá", "mira"):
                return "¿Qué video querés ver? Decí: 'poné [nombre del video]'"
            if query != text or any(w in text_lower for w in ["poné", "mirá", "mira"]):  # tenía prefijo
                return search_and_play(query)
            # Si solo dijo "youtube" sin más contexto
            return "¿Qué querés ver en YouTube?"

        # ── Spotify (comandos que no necesitan decir "spotify") ──
        if any(w in text_lower for w in ["qué suena", "que suena", "siguiente", "próxima canción"]):
            from actions.spotify_control import spotify
            if "siguiente" in text_lower or "próxima" in text_lower:
                return spotify("next")
            return spotify("current")

        # ── Spotify ──
        if any(w in text_lower for w in ["spotify", "música", "musica", "canción", "cancion"]):
            from actions.spotify_control import spotify
            if any(w in text_lower for w in ["poné", "pon", "poné música", "pon musica"]):
                query = text
                for prefix in ["poné música ", "pon música ", "poné ", "pon "]:
                    if text_lower.startswith(prefix):
                        query = text[len(prefix):].strip()
                        break
                if query.lower() in ("spotify", "música", "musica", "poné", "pon", ""):
                    return "¿Qué canción querés escuchar?"
                return spotify("play", query)
            if any(w in text_lower for w in ["pausa", "pará", "para", "stop"]):
                return spotify("pause")
            return (
                "Comandos Spotify:\n"
                "  'poné [canción]' — buscar y reproducir\n"
                "  'siguiente' / 'pausa' / 'qué suena'"
            )

        # ── Base de conocimiento (buscar) ──
        if any(w in text_lower for w in ["qué sabes de", "qué sabés de", "buscá en memoria", "buscá en tu memoria"]):
            from actions.knowledge_base import kb_search
            query = text
            for prefix in ["qué sabes de ", "qué sabés de ", "buscá en memoria ", "buscá en tu memoria "]:
                if text_lower.startswith(prefix):
                    query = text[len(prefix):].strip()
                    break
            if query and query not in ("qué sabes de", "qué sabés de", ""):
                return kb_search(query)
            return "¿Sobre qué querés que busque en mi memoria?"

        # ── Morning Brief ──
        if any(w in text_lower for w in ["informe matutino", "resumen del día", "resumen del dia",
                                          "morning brief", "qué hay de nuevo", "que hay de nuevo"]):
            from actions.morning_brief import morning_brief as _mb
            return _mb(parameters={"force": True}, player=None) or "Aquí está tu informe del día."

        # ── Tareas programadas (scheduler) ──
        if any(w in text_lower for w in ["tareas programadas", "lista de tareas", "mostrar tareas",
                                          "ver tareas", "listá tareas", "lista tareas", "scheduler"]):
            from actions.scheduler import scheduler as _sched
            return _sched(parameters={"action": "list"})

        # ── Objetivos / Metas ──
        if any(w in text_lower for w in ["objetivos", "mis objetivos", "metas", "mis metas",
                                          "listá objetivos", "lista objetivos"]):
            from actions.goals import goals as _gl
            return _gl(parameters={"action": "list"})

        # ── Perfil de usuario ──
        if any(w in text_lower for w in ["mi perfil", "mostrá perfil", "mostra perfil",
                                          "mis preferencias", "mis datos"]):
            from actions.user_profile import user_profile as _up
            return _up(parameters={"action": "view"})

        # ── Hogar inteligente (smart home) ──
        if any(w in text_lower for w in ["luces", "hogar", "casa inteligente", "smart home",
                                          "dispositivos", "encendé la luz", "apagá la luz"]):
            from actions.smart_home import smart_home as _sh
            # Comandos rápidos de encender/apagar
            if any(w in text_lower for w in ["encendé", "encende", "prende", "prender"]):
                device = text.lower().replace("encendé","").replace("encende","").replace("prende","").replace("prender","")
                device = device.replace("la luz","").replace("las luces","").replace("la","").replace("el","").strip()
                return _sh(parameters={"action": "on", "device": device or "sala"})
            if any(w in text_lower for w in ["apagá", "apaga", "apagar"]):
                device = text.lower().replace("apagá","").replace("apaga","").replace("apagar","")
                device = device.replace("la luz","").replace("las luces","").replace("la","").replace("el","").strip()
                return _sh(parameters={"action": "off", "device": device or "sala"})
            return _sh(parameters={"action": "list"})

        return None  # No matcheó → que intente Ollama

    def _show_help(self) -> str:
        """Muestra los comandos disponibles."""
        return (
            "🧠 Nexo 2.0 — Comandos disponibles\n"
            "══════════════════════════════════\n\n"
            "💬 hola / quién sos / gracias\n"
            "🕐 hora\n"
            "🌡️ temperatura\n"
            "💻 cpu / sistema\n"
            "🌤️ clima [ciudad]\n"
            "🔍 buscá [consulta]\n"
            "📁 listá archivos [carpeta]\n"
            "⏰ recordá [mensaje] el [fecha]\n"
            "▶️ poné [video/canción]\n"
            "🧠 recordá que [cosa]\n"
            "📖 qué sabes de [tema]\n"
            "🎵 Spotify: poné, pausa, siguiente\n"
            "📋 tareas programadas / scheduler\n"
            "🎯 objetivos / metas\n"
            "👤 mi perfil\n"
            "🏠 luces / hogar (encendé/apagá)\n"
            "🌐 abrí [URL o búsqueda]\n"
            "📰 informe matutino\n"
            "❓ ayuda\n\n"
            "💡 Sin conexión a IA. Usá 'buscá' para buscar en internet."
        )

    def get_status(self) -> dict:
        return {
            "version": self.config.get("version", "2.0.0"),
            "running": self.running,
            "tts_enabled": self.tts_enabled,
            "last_activity": self.last_activity.isoformat(),
        }

    # ── CLI ─────────────────────────────────────────────────────────

    def start_cli(self):
        """Inicia el loop interactivo por CLI."""
        self.running = True
        print("\n" + "=" * 50)
        print("  🧠 Nexo 2.0 — Asistente del Hogar")
        print("  Escribe 'salir' para terminar")
        print("=" * 50 + "\n")

        self.say("¡Hola miku! Nexo 2.0 está listo.")

        try:
            while self.running:
                try:
                    user_input = input("\n👤 Tú: ").strip()
                    if not user_input:
                        continue

                    response = self.process_text(user_input)
                    print(f"\n🤖 Nexo: {response}")

                    if response.startswith("¡Hasta luego"):
                        break

                except KeyboardInterrupt:
                    print()
                    self.say("Hasta luego miku.")
                    break
                except EOFError:
                    break
                except Exception as e:
                    print(f"⚠️ Error: {e}")

        finally:
            self.running = False


# ── Entry point ────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="🧠 Nexo 2.0")
    parser.add_argument("-c", "--command", type=str, help="Ejecutar un comando")
    parser.add_argument("--daemon", action="store_true", help="Modo servidor")
    parser.add_argument("--port", type=int, default=7072, help="Puerto del servidor")
    parser.add_argument("--verbose", "-v", action="store_true", help="Modo verbose")
    args = parser.parse_args()

    nexo = NexoEngine()

    if args.command:
        response = nexo.process_text(args.command)
        print(response)
    elif args.daemon:
        print("📡 Modo servidor — puerto", args.port)
        from server import start_server
        start_server(nexo, port=args.port)
    else:
        nexo.start_cli()


if __name__ == "__main__":
    main()
