# 🧠 Nexo Ecosystem

[![English](https://img.shields.io/badge/lang-English-blue)](README.en.md)

> Asistente autónomo para el hogar con **memoria persistente** — se acuerda de todo lo que hacés.  
> **Linux nativo** o **Windows vía WSL2** — requiere bash, systemd y PulseAudio.

Nexo es un ecosistema de scripts y configuraciones que transforman una PC Linux en un asistente del hogar con **memoria persistente**, **reconocimiento facial**, **control por voz**, **monitoreo del sistema** y **auto-aprendizaje**.

### 🧠 Memoria que no se pierde

Todo lo que hablás con Nexo, lo que configurás, lo que aprende — **lo recuerda entre sesiones**. Usa un Knowledge Graph en SQLite con embeddings semánticos (Ollama + nomic-embed-text) que entiende el *significado* de las cosas, no solo palabras clave.

Y si migrás de PC o formateás, el script `migrar-miku.sh` (incluido en el repo) respalda **toda la memoria** — conversaciones, preferencias, aprendizajes — para que Nexo no olvide nada. ➡️ [Ver backup](backup/migrar-miku.sh)

Creado originalmente para un Intel Celeron 847 con 4 GB de RAM — está optimizado para **cualquier hardware**, desde una netbook vieja hasta un Ryzen 9.

### 📋 Distribuciones soportadas
| Compatible | No compatible |
|:---|---:|
| Debian / Ubuntu / MX Linux | ❌ macOS |
| Fedora / RHEL / CentOS | ❌ BSD |
| Arch / Manjaro / EndeavourOS | ❌ ChromeOS (sin Linux) |
| Linux Mint / Pop!_OS / Zorin | Cualquier sistema sin systemd |
| **Windows 10/11 vía WSL2 + Ubuntu** | |
| Cualquier distro con systemd + bash | |

> 🪟 **¿Tenés Windows?** Mirá **[INSTALL-WINDOWS.md](INSTALL-WINDOWS.md)** — se instala igual de fácil que Linux con un solo comando dentro de WSL2, y la GPU (RTX 3050, etc.) se usa automáticamente para Ollama.

---

## 📦 Componentes

### 🤖 Agente (`agent/`)
- **asistente.md** — Personalidad y reglas de Nexo. Archivo de agente para OpenCode que define cómo piensa, habla y actúa.

### 🎤 Voz (`voice/`)
- **say.sh** — Text-to-Speech multi-motor: gTTS (Google), edge-tts (Microsoft), MBROLA, espeak-ng. Fallback automático.
- **voice.sh** — Speech-to-Text con VAD (Voice Activity Detection) + echo detection. Usa Google Web Speech API.

### 🧠 Memoria (`graph/`)
- **nexo-graph** — Knowledge Graph en SQLite con 3 ramas (user, directives, world). Búsqueda por keywords + Jaccard similarity + embeddings semánticos (Ollama + nomic-embed-text).
- **nexo-memory** — Sistema de auto-aprendizaje y memoria persistente. Guarda facts, hábitos, errores y mejoras automáticamente.

### 🔧 Herramientas (`tools/`)
- **nexo-tools** — Tool Registry. Registra, busca y ejecuta herramientas personalizadas desde el knowledge graph.
- **nexo-diary** — Diary Summariser. Resume las interacciones del día usando Ollama y guarda en el grafo.
- **nexo-evaluate** — Evaluator. Verifica completitud de tareas usando IA local.
- **nexo-wake** — Wake Word Detection. Escucha la palabra "Nexo" y activa comandos por voz. Soporta fuzzy match con difflib.

### 🧠 Memoria Avanzada (`memory/`)
- **nexo-memory-organize** — Organiza hechos en 11 categorías automáticamente.
- **nexo-semantic-enhance** — Genera embeddings TF-IDF y búsqueda semántica ligera.
- **nexo-skill-creator** — Crea skills automáticamente desde trayectorias de tareas.
- **nexo-memory-enhance** — Agrega tablas de mejora (conversation_summaries, learned_patterns, auto_skills).

### 🤖 Hermes Integration (`hermes/`)
- **hermes** — Wrapper para Hermes Agent con OpenRouter.
- **nexo-hermes-integration** — Script de demostración de integración.

### 🔌 Skills System (`skills/`)
- **nexo-skill** — Gestor de skills (listar, info, ejecutar, crear).
- **nexo-skill-creator** — Crea skills automáticamente desde tareas.

### 🧠 Brain (`brain/`)
- **nexo-brain.py** — Brain daemon con IA para razonamiento avanzado.
- **nexo-daemon.sh** — Daemon del brain para procesamiento en background.

### 🎵 Audio (`system/`)
- **nexo-audio-diagnostico.sh** — Diagnósticos completos de audio del sistema.

### ⚙️ Sistema (`system/`)
- **check-identity.sh** / **face-recognize.py** — Reconocimiento facial para verificar quién está usando la PC.
- **temp-monitor.sh** / **temp-cancel.sh** — Monitoreo de temperatura con apagado automático si supera 80°C.
- **limpiar** — Limpiador del sistema (cache APT, thumbnails, logs, papelera, RAM).
- **falkon-rapido** — Navegador web ultra-ligero basado en Falkon (~44 MB RAM reales).

### 🗂️ Config (`config/`)
- **cpu-performance.service** — Servicio systemd que fija el governor de CPU en `performance`.
- **sudoers.temp-monitor** — Regla sudoers para apagado automático sin contraseña.
- **miku-crontab.txt** — Crontab del sistema.

### 💿 Backup (`backup/`)
- **migrar-miku.sh** — Script de backup y restore completo del ecosistema.

---

## 🖥️ Funciona en cualquier PC

Nexo está creado para **cualquier PC con Linux** — desde una netbook vieja (Celeron, Atom) hasta un ultrabook moderno (Core i7, Ryzen 7).  
No necesitas una GPU cara ni 16 GB de RAM. Mientras corra Linux con systemd, Nexo funciona.

| Componente | Mínimo | Recomendado |
|------------|--------|-------------|
| CPU | Cualquier x86_64 de 2+ cores | Intel Core / AMD Ryzen (cualquier generación) |
| RAM | 2 GB | 4 GB o más |
| Disco | 5 GB libres | 20 GB libres o más |
| GPU | Cualquier integrada o dedicada | La que tengas — Nexo apenas usa GPU |
| SO | Linux con systemd + bash | MX Linux, Ubuntu, Debian, Fedora, Arch… |

### Optimizaciones incluidas
- **CPU**: governor `performance` + servicio systemd persistente
- **RAM**: zram con zstd, swappiness 10, vfs_cache_pressure 200
- **Disco**: noatime, scheduler BFQ, read-ahead 8 MB
- **DNS**: Cloudflare 1.1.1.1 (~133 ms resolución)
- **Background**: sin animaciones, wallpaper estático
- **Inicio**: servicios innecesarios deshabilitados (~15s ahorrados)

---

## 🚀 Instalación rápida

### Opción 1: Clonar con Git (recomendado)

```bash
git clone https://github.com/Mikutabby/nexo-lab.git
cd nexo-lab
chmod +x install.sh
./install.sh
```

> **Nota:** El repo es **público** — `git clone` no pide usuario ni contraseña.  
> Si GitHub te pide credenciales, es porque estás intentando hacer `git push` (escribir cambios).  
> Para solo instalar, clonar es anónimo y automático. ✅

### Opción 2: Descargar ZIP (sin Git)

Si no tenés Git o preferís bajarlo manual:

```bash
wget https://github.com/Mikutabby/nexo-lab/archive/refs/heads/main.zip
unzip main.zip
cd nexo-lab-main
chmod +x install.sh
./install.sh
```

### Opción 3: Desde tu PC

Si ya lo tenés clonado o descargado, directamente:

```bash
cd nexo-lab
chmod +x install.sh
./install.sh
```

### Opción 4: Instalación por conversación (con Nexo) 🗣️

**El instalador ya incluye OpenCode automáticamente.** Cloná, ejecutá y listo:

```bash
git clone https://github.com/Mikutabby/nexo-lab.git
cd nexo-lab
chmod +x install.sh
./install.sh
```

Al finalizar, ejecutá `opencode` y ya vas a tener a Nexo disponible como agente.

Nexo **sabe instalar cada componente por separado**. Solo decile qué querés:

| Decile a Nexo... | Y él instala... |
|---|---|
| "instalame las **dependencias**" | Paquetes base del sistema |
| "quiero **voz**" | TTS + STT + Wake Word |
| "poneme la **memoria**" | Knowledge Graph + memoria persistente |
| "instalame las **herramientas**" | Tool Registry, Diary, Evaluator |
| "copiame los **scripts**" | Scripts del sistema (face, temp, limpiar) |
| "cargame el **agente**" | Archivo asistente.md |
| "configurame el **sistema**" | Systemd + sudoers + crontab |
| "instalame **ollama**" | IA local |
| "poneme la **memoria avanzada**" | organize, semantic-enhance, skill-creator |
| "conectame **hermes**" | Hermes Agent + OpenRouter |
| "instalame los **skills**" | Sistema de plugins |
| "activame el **brain**" | Brain daemon + IA |
| "revisame el **audio**" | Diagnósticos de audio |
| "haceme el **completo**" | Todo el ecosistema |
| "**respaldame**" | Backup completo |

Cada componente se instala con un solo comando:
```bash
./install.sh -c <componente>
```

> 💡 El instalador soporta instalación **modular**: `-c voz`, `-c graph`, `-c tools`, `-c memory`, `-c hermes`, `-c skills`, `-c brain`, `-c audio`, etc.
> Usá `./install.sh --list` para ver todos los componentes disponibles.

---

## 🔄 Actualizar Nexo

Para actualizar sin reinstalar todo:

```bash
nexo-update
```

Esto **solo aplica los fixes y mejoras** sin sobreescribir tus configuraciones personales.

### Opciones

| Comando | Qué hace |
|---------|----------|
| `nexo-update` | Actualiza con los últimos cambios |
| `nexo-update --check` | Muestra qué cambiaría (sin aplicar) |
| `nexo-update --force` | Fuerza la actualización |
| `nexo-update --version` | Muestra la versión actual |

### Qué se actualiza

- ✅ Scripts en `~/.local/bin/` (graph, memory, tools, brain, voice, etc.)
- ✅ Migraciones automáticas si las hay
- ❌ **NO** toca configuraciones del usuario
- ❌ **NO** reinstala dependencias del sistema
- ❌ **NO** sobreescribe `~/.nexo-memory/` (tu memoria persistente)

> 💡 **Para usuarios de Termux:** Si Nexo te dice cosas raras, pedile a miku que te pase los scripts actualizados, o cloná el repo y ejecutá `./install.sh`

### Instalación modular por componentes

El instalador ahora soporta **instalación por componentes individuales** con la flag `-c`:

```bash
# Ver componentes disponibles
./install.sh --list

# Instalar solo un componente
./install.sh -c voz
./install.sh -c graph
./install.sh -c tools

# Instalar múltiples componentes
./install.sh -c dependencias -c sistema -c config

# Instalar todo (por defecto)
./install.sh
```

### ¿Qué hace el instalador completo?

1. **Instala OpenCode** automáticamente (AI coding agent donde vive Nexo)
2. Verifica que tengas acceso **sudo sin contraseña** (si no, te indica cómo configurarlo)
3. Detecta tu gestor de paquetes (apt, dnf, pacman, zypper)
4. Instala dependencias del sistema (espeak-ng, python3, sqlite3, jq, curl)
5. Instala dependencias Python (gTTS, edge-tts para TTS por cloud)
6. Copia todos los scripts a `~/.local/bin/`
7. Configura el Knowledge Graph (memoria persistente)
8. Activa el servicio de rendimiento CPU (governor `performance`)
9. Configura sudoers para el monitor de temperatura
10. Instala el crontab del sistema
11. Te ofrece instalar **Ollama** para funciones avanzadas (embeddings, diary, evaluator)

### 📦 Dependencias opcionales

| Dependencia | Para qué sirve | Cómo instalarla |
|-------------|---------------|-----------------|
| **Ollama** | Embeddings semánticos, diary, evaluator | El instalador te lo ofrece automáticamente |
| **OpenCV + face_recognition** | Reconocimiento facial | `pip install --user opencv-python face_recognition` |
| **gTTS / edge-tts** | TTS por cloud (voz más natural) | El instalador las instala automáticamente |

### ⚠️ Solución de problemas comunes

| Problema | Causa | Solución |
|----------|-------|----------|
| `git clone` pide usuario/contraseña | Querés pushear o tenés un credential helper configurado | Usá la Opción 2 (ZIP) o configurá SSH |
| `sudo: contraseña incorrecta` | No tenés sudo sin contraseña configurado | Ejecutá `bash ~/nexo-lab/setup-sudo.sh` para configurarlo |
| Ollama no se instala | No tenés curl o el script falló | Instalalo manual: `curl -fsSL https://ollama.com/install.sh \| sh` |
| El TTS no suena | PulseAudio no está corriendo | Revisá `pulseaudio --start` o tu configuración de audio |
| `face-recognize.py` no funciona | Falta OpenCV | `pip install --user opencv-python face_recognition` |

---

## 📜 Licencia

MIT — hacé lo que quieras, pero si mejorás algo, mandá un PR ✨

---

*Creado por [mikuyasha](https://github.com/mikuyasha) con ❤️ y una Celeron.*
