# 🧠 Nexo Ecosystem

> Asistente autónomo para el hogar, hecho para correr en una PC modesta con Linux.  
> **Solo Linux** — requiere bash, systemd y PulseAudio.

Nexo es un ecosistema de scripts y configuraciones que transforman una PC Linux en un asistente del hogar con **memoria persistente**, **reconocimiento facial**, **control por voz**, **monitoreo del sistema** y **auto-aprendizaje**.

Creado originalmente para un Intel Celeron 847 con 4 GB de RAM — está optimizado para hardware modesto.

### 📋 Distribuciones soportadas
| Compatible | No compatible |
|:---|---:|
| Debian / Ubuntu / MX Linux | ❌ Windows |
| Fedora / RHEL / CentOS | ❌ macOS |
| Arch / Manjaro / EndeavourOS | ❌ BSD |
| Linux Mint / Pop!_OS / Zorin | ❌ ChromeOS |
| Cualquier distro con systemd + bash | Cualquier sistema sin systemd |

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

## 🖥️ Hecho para tu hardware

Nexo está creado para PCs modestas. No necesitas una GPU cara ni 16 GB de RAM.

| Componente | Mínimo | Recomendado |
|------------|--------|-------------|
| CPU | 2 cores @ 1.0 GHz | Intel Celeron 847 (1.1 GHz) |
| RAM | 2 GB | 4 GB |
| Disco | 10 GB libres | HDD 500 GB |
| GPU | Cualquier Intel HD | Intel HD Graphics 2000 |
| SO | Linux con systemd | MX Linux / XFCE |

### Optimizaciones incluidas
- **CPU**: governor `performance` + servicio systemd persistente
- **RAM**: zram con zstd, swappiness 10, vfs_cache_pressure 200
- **Disco**: noatime, scheduler BFQ, read-ahead 8 MB
- **Navegador**: Falkon Rápido (~44 MB RAM), Chromium eliminado por pesado
- **DNS**: Cloudflare 1.1.1.1 (~133 ms resolución)
- **Background**: sin animaciones, wallpaper estático
- **Inicio**: servicios innecesarios deshabilitados (~15s ahorrados)

---

## 🚀 Instalación rápida

```bash
git clone https://github.com/tu-usuario/nexo-ecosystem.git
cd nexo-ecosystem
chmod +x install.sh
./install.sh
```

El instalador te guiará por:
1. Copia de scripts a `~/.local/bin/`
2. Configuración del agente OpenCode
3. Instalación de dependencias (Python, espeak, etc.)
4. Configuración de servicios systemd
5. Inicialización del knowledge graph

### Dependencias opcionales
- **Ollama** — para embeddings semánticos, diary summariser y evaluator
- **Reconocimiento facial** — requiere OpenCV y face_recognition
- **gTTS / edge-tts** — para TTS por cloud (alternativa a espeak local)

---

## 📜 Licencia

MIT — hacé lo que quieras, pero si mejorás algo, mandá un PR ✨

---

*Creado por [mikuyasha](https://github.com/mikuyasha) con ❤️ y una Celeron.*
