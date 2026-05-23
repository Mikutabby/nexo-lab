# 🧠 Nexo Ecosystem

> Asistente autónomo para el hogar con **memoria persistente** — se acuerda de todo lo que hacés.  
> **Solo Linux** — requiere bash, systemd y PulseAudio.

Nexo es un ecosistema de scripts y configuraciones que transforman una PC Linux en un asistente del hogar con **memoria persistente**, **reconocimiento facial**, **control por voz**, **monitoreo del sistema** y **auto-aprendizaje**.

### 🧠 Memoria que no se pierde

Todo lo que hablás con Nexo, lo que configurás, lo que aprende — **lo recuerda entre sesiones**. Usa un Knowledge Graph en SQLite con embeddings semánticos (Ollama + nomic-embed-text) que entiende el *significado* de las cosas, no solo palabras clave.

Y si migrás de PC o formateás, el script `migrar-miku.sh` (incluido en el repo) respalda **toda la memoria** — conversaciones, preferencias, aprendizajes — para que Nexo no olvide nada. ➡️ [Ver backup](backup/migrar-miku.sh)

Creado originalmente para un Intel Celeron 847 con 4 GB de RAM — está optimizado para **cualquier hardware**, desde una netbook vieja hasta un Ryzen 9.

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

---

### ¿Qué hace el instalador?

1. Pide tu contraseña **sudo** (para instalar dependencias y configurar servicios)
2. Detecta tu gestor de paquetes (apt, dnf, pacman, zypper)
3. Instala dependencias del sistema (espeak-ng, python3, sqlite3, jq, curl)
4. Instala dependencias Python (gTTS, edge-tts para TTS por cloud)
5. Copia todos los scripts a `~/.local/bin/`
6. Configura el Knowledge Graph (memoria persistente)
7. Activa el servicio de rendimiento CPU (governor `performance`)
8. Configura sudoers para el monitor de temperatura
9. Instala el crontab del sistema
10. Te ofrece instalar **Ollama** para funciones avanzadas (embeddings, diary, evaluator)

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
| `sudo: contraseña incorrecta` | Escribiste mal la contraseña | Ejecutá de nuevo el instalador con cuidado |
| Ollama no se instala | No tenés curl o el script falló | Instalalo manual: `curl -fsSL https://ollama.com/install.sh \| sh` |
| El TTS no suena | PulseAudio no está corriendo | Revisá `pulseaudio --start` o tu configuración de audio |
| `face-recognize.py` no funciona | Falta OpenCV | `pip install --user opencv-python face_recognition` |

---

## 📜 Licencia

MIT — hacé lo que quieras, pero si mejorás algo, mandá un PR ✨

---

*Creado por [mikuyasha](https://github.com/mikuyasha) con ❤️ y una Celeron.*
