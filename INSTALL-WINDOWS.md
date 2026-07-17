# 🪟 Nexo Ecosystem — Instalación en Windows

> Guía oficial para correr **Nexo** en una PC con Windows 10/11.
> Probado en: AMD Ryzen 5 5500 · 32 GB RAM · NVIDIA RTX 3050 (8 GB VRAM).

Nexo está hecho en **bash + systemd**, que es nativo de Linux. En Windows lo corremos
dentro de **WSL2** (Windows Subsystem for Linux) con Ubuntu. Una vez adentro, la
instalación es **idéntica a Linux**: un solo comando.

La RTX 3050 se usa automáticamente para inferencia GPU vía CUDA dentro de WSL2, así
que Ollama vuela igual que en Linux nativo.

---

## 🚀 Instalación rápida (3 pasos)

### Paso 1 — Instalar WSL2 + Ubuntu

Abrí **PowerShell como Administrador** (clic derecho → "Ejecutar como administrador")
y pegá esto:

```powershell
wsl --install
```

> Esto instala WSL2 y Ubuntu automáticamente. Pide reiniciar la PC una vez.

Después del reinicio, Ubuntu se abre solo y te pide crear un **usuario y contraseña**
(de Linux, no es tu cuenta de Windows). Anotala, la vas a usar poco.

### Paso 2 — Entrar a Ubuntu y clonar Nexo

En la terminal de Ubuntu (la que se abrió, o buscá "Ubuntu" en el menú inicio):

```bash
git clone https://github.com/Mikutabby/nexo-lab.git
cd nexo-lab
chmod +x install.sh
```

### Paso 3 — Instalar Nexo (igual que Linux)

```bash
./install.sh
```

¡Eso es todo! El instalador detecta el gestor de paquetes (apt, porque es Ubuntu),
instala todo y te ofrece **Ollama** para la IA local.

Al terminar, ejecutá `opencode` y ya tenés a Nexo disponible como agente.

---

## 🎮 Aprovechar la RTX 3050 (GPU)

Dentro de Ubuntu, Ollama usa la GPU automáticamente si los drivers están disponibles.
Para confirmarlo:

```bash
ollama pull qwen2.5:7b
ollama run qwen2.5:7b "decime hola"
```

Si querés ver que usa la GPU, instalá los drivers CUDA de NVIDIA para WSL:

```powershell
# En PowerShell (Windows, no Ubuntu):
winget install NVIDIA.CUDA --accept-package-agreements --accept-feature-agreements
```

Luego dentro de Ubuntu: `nvidia-smi` debe mostrar tu RTX 3050.

### Modelos recomendados para RTX 3050 (8 GB)

| Modelo | VRAM | Velocidad | Uso |
|---|---|---|---|
| `llama3.2:1b` | ~1 GB | Volador | Ultra liviano |
| `llama3.2:3b` | ~2 GB | Muy rápido | Charla diaria |
| **`qwen2.5:7b`** | ~4.5 GB | Bueno | Mejor razonamiento |
| `llama3.1:8b` | ~5 GB | Aceptable | Pesado pero capaz |

---

## 📦 Instalación modular (igual que Linux)

Cada componente se instala con un comando, dentro de Ubuntu:

```bash
./install.sh -c voz        # TTS + STT + Wake Word
./install.sh -c graph      # Knowledge Graph + memoria
./install.sh -c tools      # Tool Registry + Diary + Evaluator
./install.sh -c ollama     # Ollama + nomic-embed-text
./install.sh --list        # Ver todos los componentes
```

---

## 🖥️ Usar Nexo desde Windows (sin perderse en Ubuntu)

Para que sea cómodo, podés abrir la terminal de Nexo directamente desde Windows:

```powershell
# En PowerShell:
wsl -d Ubuntu -e bash -lic "opencode"
```

O creá un acceso directo en el escritorio con ese comando.

### TTS (voz) en Windows

El audio de Nexo suena **dentro de Ubuntu** pero se reproduce en tus parlantes de
Windows automáticamente (WSL2 redirige el audio por PulseAudio/pipewire).
Si no suena, dentro de Ubuntu ejecutá:

```bash
pulseaudio --start
```

---

## ⚠️ Solución de problemas

| Problema | Causa | Solución |
|----------|-------|----------|
| `wsl --install` dice "ya instalado" | WSL viejo | `wsl --update` y reiniciá |
| Ubuntu no arranca | Hyper-V desactivado | Activá "Plataforma de máquina virtual" en Features de Windows |
| Ollama no usa GPU | Falta driver CUDA | `winget install NVIDIA.CUDA` en PowerShell |
| `nvidia-smi` no aparece | Driver no instalado en Windows | Instalá GeForce Experience y los drivers de la RTX 3050 |
| El TTS no suena | PulseAudio caído | `pulseaudio --start` dentro de Ubuntu |
| `git clone` pide usuario | Querés pushear | Para instalar alcanza con clonar (es anónimo) |

---

## 💡 Notas

- **WSL2 no es una máquina virtual lenta**: comparte la RAM y CPU con Windows y la GPU
  vía CUDA. Rendimiento casi nativo para Ollama.
- Tu disco de Windows es accesible desde Ubuntu en `/mnt/c/`.
- Si formateás Windows, tu memoria de Nexo queda en el disco de WSL (`%LOCALAPPDATA%\Packages\...`).
  Hacé `~/nexo-lab/backup/migrar-miku.sh backup` para resguardarla.

---

*Creado por [mikuyasha](https://github.com/mikuyasha) con ❤️ y una Celeron (y ahora también en Ryzen + RTX 3050).*
