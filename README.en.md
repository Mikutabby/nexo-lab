# Nexo Ecosystem

> Autonomous home assistant with **persistent memory** — it remembers everything you configure.  
> **Linux only** — requires bash, systemd, and PulseAudio.

Nexo is an ecosystem of scripts and configurations that turn a Linux PC into a home assistant with **persistent memory**, **facial recognition**, **voice control**, **system monitoring**, and **self-learning**.

### Memory that doesn't forget

Everything you configure with Nexo, everything it learns — **it remembers between sessions**. It uses a Knowledge Graph in SQLite with semantic embeddings (Ollama + nomic-embed-text) that understands the *meaning* of things, not just keywords.

And if you migrate to a new PC or reinstall, the `migrar-miku.sh` script (included in the repo) backs up **all memory** — conversations, preferences, learnings — so Nexo doesn't forget anything. ➡️ [View backup](backup/migrar-miku.sh)

Originally created for an Intel Celeron 847 with 4 GB of RAM — optimized for **any hardware**, from an old netbook to a Ryzen 9.

### Supported distributions
| Compatible | Not compatible |
|:---|---:|
| Debian / Ubuntu / MX Linux | ❌ Windows |
| Fedora / RHEL / CentOS | ❌ macOS |
| Arch / Manjaro / EndeavourOS | ❌ BSD |
| Linux Mint / Pop!_OS / Zorin | ❌ ChromeOS |
| Any distro with systemd + bash | Any system without systemd |

---

## Components

### Agent (`agent/`)
- **asistente.md** — Nexo's personality and rules. OpenCode agent file that defines how it thinks, speaks, and acts.

### Voice (`voice/`)
- **say.sh** — Multi-engine Text-to-Speech: gTTS (Google), edge-tts (Microsoft), MBROLA, espeak-ng. Automatic fallback.
- **voice.sh** — Speech-to-Text with VAD (Voice Activity Detection) + echo detection. Uses Google Web Speech API.

### Memory (`graph/`)
- **nexo-graph** — Knowledge Graph in SQLite with 3 branches (user, directives, world). Search by keywords + Jaccard similarity + semantic embeddings (Ollama + nomic-embed-text).
- **nexo-memory** — Self-learning system and persistent memory. Automatically saves facts, habits, errors, and improvements.

### Tools (`tools/`)
- **nexo-tools** — Tool Registry. Register, search, and execute custom tools from the knowledge graph.
- **nexo-diary** — Diary Summariser. Summarizes daily interactions using Ollama and saves to the graph.
- **nexo-evaluate** — Evaluator. Verifies task completion using local AI.
- **nexo-wake** — Wake Word Detection. Listens for the word "Nexo" and activates voice commands. Supports fuzzy match with difflib.

### Advanced Memory (`memory/`)
- **nexo-memory-organize** — Organizes facts into 11 categories automatically.
- **nexo-semantic-enhance** — Generates TF-IDF embeddings and lightweight semantic search.
- **nexo-skill-creator** — Creates skills automatically from task trajectories.
- **nexo-memory-enhance** — Adds enhancement tables (conversation_summaries, learned_patterns, auto_skills).

### Hermes Integration (`hermes/`)
- **hermes** — Wrapper for Hermes Agent with OpenRouter.
- **nexo-hermes-integration** — Integration demo script.

### Skills System (`skills/`)
- **nexo-skill** — Skill manager (list, info, execute, create).
- **nexo-skill-creator** — Creates skills automatically from tasks.

### Brain (`brain/`)
- **nexo-brain.py** — Brain daemon with AI for advanced reasoning.
- **nexo-daemon.sh** — Brain daemon for background processing.

### Audio (`system/`)
- **nexo-audio-diagnostico.sh** — Complete system audio diagnostics.

### System (`system/`)
- **check-identity.sh** / **face-recognize.py** — Facial recognition to verify who's using the PC.
- **temp-monitor.sh** / **temp-cancel.sh** — Temperature monitoring with automatic shutdown if it exceeds 80°C.
- **limpiar** — System cleaner (APT cache, thumbnails, logs, trash, RAM).
- **falkon-rapido** — Ultra-lightweight web browser based on Falkon (~44 MB real RAM).

### Config (`config/`)
- **cpu-performance.service** — systemd service that sets CPU governor to `performance`.
- **sudoers.temp-monitor** — sudoers rule for automatic shutdown without password.
- **miku-crontab.txt** — System crontab.

### Backup (`backup/`)
- **migrar-miku.sh** — Complete backup and restore script for the ecosystem.

---

## Works on any PC

Nexo is built for **any Linux PC** — from an old netbook (Celeron, Atom) to a modern ultrabook (Core i7, Ryzen 7).  
You don't need an expensive GPU or 16 GB of RAM. As long as it runs Linux with systemd, Nexo works.

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | Any x86_64 with 2+ cores | Intel Core / AMD Ryzen (any generation) |
| RAM | 2 GB | 4 GB or more |
| Disk | 5 GB free | 20 GB free or more |
| GPU | Any integrated or dedicated | Whatever you have — Nexo barely uses GPU |
| OS | Linux with systemd + bash | MX Linux, Ubuntu, Debian, Fedora, Arch… |

### Included optimizations
- **CPU**: `performance` governor + persistent systemd service
- **RAM**: zram with zstd, swappiness 10, vfs_cache_pressure 200
- **Disk**: noatime, BFQ scheduler, 8 MB read-ahead
- **DNS**: Cloudflare 1.1.1.1 (~133 ms resolution)
- **Background**: no animations, static wallpaper
- **Boot**: unnecessary services disabled (~15s saved)

---

## Quick installation

### Option 1: Clone with Git (recommended)

```bash
git clone https://github.com/Mikutabby/nexo-lab.git
cd nexo-lab
chmod +x install.sh
./install.sh
```

> **Note:** The repo is **public** — `git clone` doesn't ask for username or password.  
> If GitHub asks for credentials, it's because you're trying to `git push` (write changes).  
> For installation only, cloning is anonymous and automatic. ✅

### Option 2: Download ZIP (no Git)

If you don't have Git or prefer to download manually:

```bash
wget https://github.com/Mikutabby/nexo-lab/archive/refs/heads/main.zip
unzip main.zip
cd nexo-lab-main
chmod +x install.sh
./install.sh
```

### Option 3: From your PC

If you already have it cloned or downloaded:

```bash
cd nexo-lab
chmod +x install.sh
./install.sh
```

### Option 4: Conversational installation (with Nexo) 🗣️

**The installer now includes OpenCode automatically.** Clone, run, and you're done:

```bash
git clone https://github.com/Mikutabby/nexo-lab.git
cd nexo-lab
chmod +x install.sh
./install.sh
```

When finished, run `opencode` and Nexo will be available as an agent.

Nexo **knows how to install each component separately**. Just tell it what you want:

| Tell Nexo... | And it installs... |
|---|---|
| "install **dependencies**" | Base system packages |
| "I want **voice**" | TTS + STT + Wake Word |
| "set up **memory**" | Knowledge Graph + persistent memory |
| "install **tools**" | Tool Registry, Diary, Evaluator |
| "copy the **scripts**" | System scripts (face, temp, clean) |
| "load the **agent**" | asistente.md file |
| "configure the **system**" | systemd + sudoers + crontab |
| "install **ollama**" | Local AI |
| "set up **advanced memory**" | organize, semantic-enhance, skill-creator |
| "connect **hermes**" | Hermes Agent + OpenRouter |
| "install **skills**" | Plugin system |
| "activate the **brain**" | Brain daemon + AI |
| "check **audio**" | Audio diagnostics |
| "install **everything**" | The complete ecosystem |
| "**backup**" | Complete backup |

Each component installs with a single command:
```bash
./install.sh -c <component>
```

> 💡 The installer supports **modular installation**: `-c voz`, `-c graph`, `-c tools`, `-c memory`, `-c hermes`, `-c skills`, `-c brain`, `-c audio`, etc.
> Use `./install.sh --list` to see all available components.

---

### Modular installation by components

The installer now supports **individual component installation** with the `-c` flag:

```bash
# View available components
./install.sh --list

# Install a single component
./install.sh -c voz
./install.sh -c graph
./install.sh -c tools

# Install multiple components
./install.sh -c dependencias -c sistema -c config

# Install everything (default)
./install.sh
```

### What does the complete installer do?

1. **Installs OpenCode** automatically (AI coding agent where Nexo lives)
2. Verifies you have **passwordless sudo** access (if not, it tells you how to configure it)
3. Detects your package manager (apt, dnf, pacman, zypper)
4. Installs system dependencies (espeak-ng, python3, sqlite3, jq, curl)
5. Installs Python dependencies (gTTS, edge-tts for cloud TTS)
6. Copies all scripts to `~/.local/bin/`
7. Configures the Knowledge Graph (persistent memory)
8. Enables the CPU performance service (governor `performance`)
9. Configures sudoers for the temperature monitor
10. Installs the system crontab
11. Offers to install **Ollama** for advanced features (embeddings, diary, evaluator)

### Optional dependencies

| Dependency | What it's for | How to install |
|------------|---------------|----------------|
| **Ollama** | Semantic embeddings, diary, evaluator | The installer offers it automatically |
| **OpenCV + face_recognition** | Facial recognition | `pip install --user opencv-python face_recognition` |
| **gTTS / edge-tts** | Cloud TTS (more natural voice) | The installer installs them automatically |

### Common troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `git clone` asks for username/password | You're trying to push or have a credential helper configured | Use Option 2 (ZIP) or configure SSH |
| `sudo: incorrect password` | You don't have passwordless sudo configured | Run `bash ~/nexo-lab/setup-sudo.sh` to configure it |
| Ollama doesn't install | You don't have curl or the script failed | Install manually: `curl -fsSL https://ollama.com/install.sh \| sh` |
| TTS doesn't play | PulseAudio isn't running | Check `pulseaudio --start` or your audio configuration |
| `face-recognize.py` doesn't work | OpenCV is missing | `pip install --user opencv-python face_recognition` |

---

## License

MIT — do whatever you want, but if you improve something, send a PR ✨

---

*Created by [mikuyasha](https://github.com/Mikutabby) with ❤️ and a Celeron.*
