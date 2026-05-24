# 🧠 Nexo Ecosystem — Asistente del Hogar

## 📋 Índice

1. [Arquitectura](#arquitectura)
2. [Estructura de directorios](#estructura-de-directorios)
3. [Proyectos](#proyectos)
4. [Scripts del sistema](#scripts-del-sistema)
5. [Servicios](#servicios)
6. [Flujo de datos](#flujo-de-datos)
7. [Para desarrolladores](#para-desarrolladores)

---

## Arquitectura

```
Usuario
   │
   ├─► OpenCode (CLI/chat) ──► asistente.md (Nexo AI) ──► bash/python tools
   │
   ├─► nexo2 (CLI/GUI/Server) ──► nexo_engine.py ──► 15+ acciones
   │                                                   │
   │                                                   ├─► browser_control.py
   │                                                   ├─► file_controller.py
   │                                                   ├─► spotify_control.py
   │                                                   ├─► weather_report.py
   │                                                   ├─► web_search.py
   │                                                   ├─► youtube_video.py
   │                                                   ├─► scheduler.py
   │                                                   ├─► reminder.py
   │                                                   ├─► smart_home.py
   │                                                   ├─► system_monitor.py
   │                                                   ├─► knowledge_base.py
   │                                                   ├─► goals.py
   │                                                   ├─► user_profile.py
   │                                                   ├─► morning_brief.py
   │                                                   └─► ollama_provider.py
   │
   ├─► nexo-app (server HTTP, puerto 7072) ──► engine.py (versión anterior)
   │
   ├─► TTS (say.sh) ──► gTTS (Google) ──► espeak-ng (fallback)
   │
   ├─► STT (voice.sh) ──► graba micrófono ──► Google Speech API
   │
   ├─► Reconocimiento facial (face-recognize.py) ──► check-identity.sh
   │
   ├─► Monitor temperatura (temp-monitor.sh) ──► cron cada 2min
   │
   ├─► Memoria persistente (nexo-memory / nexo-graph) ──► SQLite
   │
   └─► Wake word (nexo-wake) ──► escucha "Nexo"
```

---

## Estructura de directorios

```
~/
├── nexo2/                          ★ PROYECTO PRINCIPAL (git)
│   ├── README.md                   Esta documentación
│   ├── VERSION                     v2.0.0
│   ├── LICENSE                     MIT
│   ├── main.py                     Entry point
│   ├── server.py                   HTTP server (puerto 7072)
│   ├── install.sh                  Instalador completo
│   │
│   ├── agent/                      Personalidad del asistente
│   │   ├── asistente.md            Prompt del agente (copia)
│   │   └── style-local.md          Instrucciones de estilo
│   │
│   ├── core/                       ★ MOTOR PRINCIPAL
│   │   ├── nexo_engine.py          Orquestador (keywords + Ollama)
│   │   ├── model_router.py         Ruteo a modelos Ollama
│   │   ├── prompt.txt              System prompt JARVIS v2.1
│   │   └── version.py              Versión
│   │
│   ├── actions/                    ★ 15 ACCIONES
│   │   ├── browser_control.py      Control de navegador (Playwright)
│   │   ├── file_controller.py      Operaciones con archivos
│   │   ├── smart_home.py           Hogar inteligente (MQTT)
│   │   ├── spotify_control.py      Control de Spotify
│   │   ├── system_monitor.py       Monitor del sistema
│   │   ├── scheduler.py            Planificador de tareas
│   │   ├── knowledge_base.py       Base de conocimiento
│   │   ├── goals.py                Seguimiento de objetivos
│   │   ├── morning_brief.py        Resumen matutino
│   │   ├── user_profile.py         Perfil de usuario
│   │   ├── weather_report.py       Clima (Open-Meteo)
│   │   ├── youtube_video.py        YouTube search/play
│   │   ├── reminder.py             Recordatorios
│   │   ├── web_search.py           Búsqueda web (DDGS)
│   │   └── ollama_provider.py      Cliente Ollama
│   │
│   ├── memory/                     Memoria
│   │   └── memory_manager.py       Gestor de memoria
│   │
│   ├── graph/                      ★ SISTEMA DE MEMORIA
│   │   ├── nexo-graph              Knowledge Graph (SQLite + embeddings)
│   │   └── nexo-memory             Memoria persistente (bash)
│   │
│   ├── tools/                      Utilidades
│   │   ├── nexo-diary              Resumidor diario (Ollama)
│   │   ├── nexo-evaluate           Evaluador de tareas
│   │   ├── nexo-tools              Registro de herramientas
│   │   └── nexo-wake               Detección de wake word
│   │
│   ├── voice/                      Voz
│   │   ├── say.sh                  TTS → gTTS → espeak-ng
│   │   └── voice.sh                STT → Google Speech API
│   │
│   ├── ui/                         Interfaz gráfica
│   │   ├── nexo_ui.py              PyQt6 (ParticleOrb + widgets)
│   │   └── theme.py                Temas de color
│   │
│   ├── system/                     Scripts del sistema (copias)
│   │   ├── check-identity.sh       Reconocimiento facial
│   │   ├── face-recognize.py       Entrenamiento/detección facial
│   │   ├── temp-monitor.sh         Monitor temperatura
│   │   ├── temp-cancel.sh          Cancelar apagado
│   │   ├── limpiar                 Limpieza del sistema
│   │   ├── falkon-rapido           Lanzador rápido Falkon
│   │   ├── suspender               Suspender PC
│   │   ├── desbloquear             Desbloquear pantalla
│   │   ├── dar_internet            Compartir internet
│   │   ├── nexo-keepalive          Mantener modelo en RAM
│   │   ├── wallpaper-animado.sh    Fondo de pantalla animado
│   │   └── jp.py                   Procesador JSON
│   │
│   ├── backup/
│   │   └── migrar-miku.sh          Backup/restore del ecosistema
│   │
│   ├── config/                     Configuración
│   │   ├── config.json             Config principal
│   │   ├── api_keys.json           API keys
│   │   ├── knowledge_base.json     Base de conocimiento
│   │   ├── miku-crontab.txt        Cron para temp-monitor
│   │   └── ...                     Servicios systemd, sudoers, etc.
│   │
│   ├── assets/                     (vacío - para assets futuros)
│   └── .git/                       Repositorio GitHub
│
├── .opencode/                      ★ CONFIGURACIÓN DE OPENCODE
│   ├── bin/opencode                Binario de OpenCode
│   ├── agents/asistente.md         ★ Personalidad activa de Nexo
│   ├── say.sh                      TTS (copia vivida)
│   ├── voice.sh                    STT (copia vivida)
│   └── node_modules/               Dependencias npm
│
├── .config/opencode/               Config de OpenCode
│   ├── opencode.jsonc              Config principal
│   ├── style.md                    Estilo base
│   ├── style-local.md              Estilo local
│   └── node_modules/               Dependencias npm
│
├── .local/bin/                     ★ SCRIPTS EJECUTABLES (en PATH)
│   ├── nexo2                       Lanzador Nexo 2.0
│   ├── nexo-graph                  Knowledge Graph
│   ├── nexo-memory                 Memoria persistente
│   ├── nexo-diary                  Resumidor diario
│   ├── nexo-evaluate               Evaluador
│   ├── nexo-tools                  Lanzador de herramientas
│   ├── nexo-wake                   Wake word
│   ├── nexo-keepalive              Keepalive Ollama
│   ├── nexo-ui*                    UI wrappers
│   ├── check-identity.sh           Reconocimiento facial
│   ├── face-recognize.py           Face train/identify
│   ├── temp-monitor.sh             Temperatura
│   ├── temp-cancel.sh              Cancelar apagado
│   ├── limpiar                     Limpieza sistema
│   ├── falkon-rapido               Falkon rápido
│   ├── suspender / desbloquear     Utilidades
│   ├── dar_internet                Compartir red
│   ├── wallpaper-animado.sh        Wallpaper
│   └── jp.py                       JSON processor
│
├── nexo-app/                       ★ PROYECTO ANTERIOR (aún activo)
│   ├── server.py                   HTTP server corriendo en :7072
│   ├── main.py                     Entry point CLI
│   ├── nexo-app.sh                 Lanzador
│   ├── core/                       Motor (engine.py, brain.py, etc.)
│   ├── memory/                     Memoria (bridge)
│   ├── tools/                      Herramientas (registry, system, etc.)
│   └── voice/                      TTS/STT
│
├── .nexo-memory/                   ★ DATOS DE MEMORIA
│   ├── memory.json                 Memoria en JSON
│   ├── graph.db                    Knowledge Graph (SQLite)
│   ├── interactions.json           Interacciones recientes
│   ├── log/*.log                   Logs diarios
│   └── learned/                    Datos de aprendizaje
│
├── .nexo-voice/                    Datos de entrenamiento de voz
│   └── recordings/*.wav            12 muestras de voz
│
├── miku-eco/                       ★ PROYECTO ANTERIOR (hogar)
│   └── .local/bin/miku-eco/        Automatización del hogar
│
├── respaldo-nexo-20260522/         Backup completo (260 MB)
│
└── miku-backup.tar.gz              Backup comprimido (53 MB)
```

---

## Proyectos

### 🏆 nexo2 (PRINCIPAL — activo)
| Aspecto | Detalle |
|---------|---------|
| **Directorio** | `~/nexo2/` |
| **Git** | `github.com/Mikutabby/nexo-lab` (rama `main`) |
| **Estado** | En desarrollo activo |
| **Motor** | `core/nexo_engine.py` — keywords + Ollama fallback |
| **UI** | PyQt6 (`ui/nexo_ui.py`) + HTTP server (`server.py`) |
| **Acciones** | 15 módulos en `actions/` |
| **Instalación** | `bash install.sh` |

### 🔶 nexo-app (ANTERIOR — aún corriendo)
| Aspecto | Detalle |
|---------|---------|
| **Directorio** | `~/nexo-app/` |
| **Git** | No trackeado |
| **Estado** | Servidor HTTP activo en puerto 7072 (PID 133986) |
| **Motor** | `core/engine.py` + `core/brain.py` |
| **Nota** | Versión previa a nexo2. Mantenida por compatibilidad. El servidor HTTP seguirá funcionando hasta que nexo2 lo reemplace. |

### 🏠 miku-eco (ANTERIOR — inactivo)
| Aspecto | Detalle |
|---------|---------|
| **Directorio** | `~/.local/bin/miku-eco/` |
| **Servicio** | `miku-eco.service` (systemd, desactivado) |
| **Estado** | Inactivo. Código mantenido como referencia. |
| **Función** | Automatización del hogar (TV LG, presencia, voz) |

---

## Scripts del sistema

| Script | Ruta viva | Función |
|--------|-----------|---------|
| `say.sh` | `~/.opencode/` y `~/nexo2/voice/` | Text-to-Speech (gTTS → espeak-ng) |
| `voice.sh` | `~/.opencode/` y `~/nexo2/voice/` | Speech-to-Text (Google Speech API) |
| `check-identity.sh` | `~/.local/bin/` | Reconoce quién está frente a la PC |
| `face-recognize.py` | `~/.local/bin/` | Entrena/identifica rostros |
| `temp-monitor.sh` | `~/.local/bin/` | Monitorea temperatura (cron cada 2min) |
| `temp-cancel.sh` | `~/.local/bin/` | Cancela apagado por temperatura |
| `limpiar` | `~/.local/bin/` | Limpieza del sistema |
| `nexo-graph` | `~/.local/bin/` | Knowledge Graph (SQLite + embeddings) |
| `nexo-memory` | `~/.local/bin/` | Memoria persistente |
| `nexo-diary` | `~/.local/bin/` | Resumen diario |
| `nexo-evaluate` | `~/.local/bin/` | Evaluador de tareas |
| `nexo-tools` | `~/.local/bin/` | Registro de herramientas |
| `nexo-wake` | `~/.local/bin/` | Wake word detection |
| `nexo-keepalive` | `~/.local/bin/` | Mantiene modelo Ollama en RAM |
| `nexo2` | `~/.local/bin/` | Lanzador de Nexo 2.0 |

> **Nota:** `~/.local/bin/` es la fuente de verdad para scripts ejecutables. `~/nexo2/system/`, `~/nexo2/graph/`, `~/nexo2/tools/` y `~/nexo2/voice/` son **copias sincronizadas** para el repositorio git.

---

## Servicios

| Servicio | Tipo | Estado | Función |
|----------|------|--------|---------|
| `nexo-keepalive.service` | user | ✅ Activo | Mantiene smollm2:135m en RAM |
| `nexo-wakeword.service` | user | ❌ Inactivo | Escucha "Nexo" (deshabilitado) |
| `miku-eco.service` | system | ❌ Inactivo | Hogar inteligente (anterior) |
| `nexo-app/server.py` | user (PID 133986) | ✅ Activo | Servidor HTTP puerto 7072 |

### Crontab
```
0 * * * *  nexo-memory learn             → Aprendizaje automático cada hora
*/2 * * * * temp-monitor.sh              → Monitor temperatura cada 2 minutos
```

---

## Flujo de datos

```
                    ┌──────────────┐
                    │   Usuario    │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        OpenCode       nexo2 CLI    nexo2 GUI
        (chat)        (terminal)   (PyQt6)
              │            │            │
              └─────┬──────┘────────────┘
                    ▼
           nexo_engine.py
                    │
          ┌─────────┼─────────┐
          ▼         ▼         ▼
    keywords    acciones   Ollama
    (instant)   (15 mod.)  (fallback)
          │         │         │
          └─────────┼─────────┘
                    ▼
              Respuesta
                    │
          ┌─────────┼─────────┐
          ▼         ▼         ▼
       say.sh    voice.sh   face-recog
       (TTS)     (STT)      (identidad)
          │         │         │
          ▼         ▼         ▼
       parlante  micrófono  cámara
```

---

## Para desarrolladores

### ¿Por qué hay 3 proyectos?

1. **nexo2** — Reescritura moderna. 15 acciones modulares, PyQt6 UI, keywords + Ollama. Es el futuro.
2. **nexo-app** — Versión anterior con engine.py/brain.py. El server HTTP sigue activo en :7072.
3. **miku-eco** — Proyecto de hogar inteligente separado, inactivo.

### Live code vs git code

- **`~/.local/bin/`** contiene los scripts **reales** que ejecuta cron, systemd y el PATH.
- **`~/nexo2/`** es el proyecto git. Las subcarpetas `system/`, `graph/`, `tools/`, `voice/` contienen **copias** sincronizadas de los scripts de `~/.local/bin/`.
- **Regla:** si modificás un script en `~/.local/bin/`, copialo a `~/nexo2/` para mantener el git actualizado.

### Cómo empezar a desarrollar

```bash
# 1. Clonar
git clone https://github.com/Mikutabby/nexo-lab ~/nexo2

# 2. Probar motor
nexo2 -c "ayuda"                    # CLI modo comando
nexo2                                # CLI interactivo
nexo2 gui                            # Interfaz gráfica

# 3. Probar acciones individuales
cd ~/nexo2 && python3 -c "
from actions.weather_report import get_weather
print(get_weather('Buenos Aires'))
"

# 4. Servidor HTTP
nexo2 server                         # Puerto 7072
curl http://127.0.0.1:7072/status    # Ver estado

# 5. Instalación completa
bash ~/nexo2/install.sh
```

### Dependencias clave

| Dependencia | Para qué |
|-------------|----------|
| Python 3.12+ | Todo el ecosistema |
| PyQt6 6.9+ | UI gráfica (ParticleOrb) |
| Ollama | LLM local (smollm2:135m) |
| espeak-ng / mbrola | TTS fallback |
| gTTS | TTS Google WaveNet |
| google-speech | STT |
| Playwright | Browser control |
| opencv-python | Face recognition |
| SQLite3 | Knowledge Graph |

### Notas importantes

- **Smollm2:135m** genera a ~0.1 tok/s en este hardware (Celeron 847). Por eso se priorizan keywords.
- **Ollama timeout:** 8s, context: 256 tokens.
- **TTS:** gTTS (~1.5s) con fallback a espeak-ng (~0.03s).
- **El motor usa keywords primero** — si el comando coincide con una keyword, se ejecuta al instante sin LLM.
- **Para probar cambios:** editá el archivo y ejecutalo directamente. No necesitás reiniciar nada.
