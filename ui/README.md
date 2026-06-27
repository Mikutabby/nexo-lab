# 🔷 Nexo UI 2.0

**Interfaz visual tipo HUD para Nexo — el asistente del hogar.**

Widget de escritorio + Web App con animaciones estilo Iron Man, sincronizadas en tiempo real. Diseñado para ser liviano y funcional en hardware modesto.

![Nexo UI](https://img.shields.io/badge/version-2.0.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## ✨ Características

| Componente | Descripción |
|------------|-------------|
| **🖥️ HUD Principal** | Interfaz web completa con radar animado, info del sistema y panel de comandos |
| **📱 Mini Widget** | Versión miniatura sincronizada — se mueve con la interfaz principal |
| **📊 Conky Widget** | Widget de escritorio ultra-liviano (~5MB RAM) con info del sistema |
| **⚡ Tiempo Real** | WebSocket para actualizaciones en vivo sin recargar |
| **🎯 Comandos Rápidos** | Botones de acceso directo + input por teclado |
| **📋 Historial** | Registro de comandos y respuestas |
| **🔔 Estado Nexo** | Indicador visual: inactivo, escuchando, procesando, hablando |

## 🖼️ Vistas

### HUD Completo
```
┌─────────────┬──────────────────────┬─────────────┐
│  SISTEMA    │      ╭───╮           │  COMANDOS   │
│  CPU: 45%   │   ╭──┤ N ├──╮        │  [Hora] [Clima]
│  RAM: 60%   │   │  ╰───╯  │        │  [Estado] [Limpiar]
│  Temp: 52°C │   ╰─────────╯        │             │
│  Disco: 73% │   INACTIVO           │  HISTORIAL  │
│  Uptime: 2h │   > último comando   │  > cmd 1    │
└─────────────┴──────────────────────┴──────────────┘
```

### Mini Widget
```
┌──────────────────────────────────┐
│ NEXO                INACTIVO ●   │
│ CPU 45% ████░░  RAM 60% ██████░  │
│ TEMP 52°C █████░                 │
│ > último comando                 │
└──────────────────────────────────┘
```

## 📦 Requisitos

- **SO:** Linux (MX Linux, Ubuntu, Debian, etc.)
- **Python:** 3.8+
- **RAM:** ~50MB (web) + ~5MB (widget Conky)
- **Navegador:** Firefox, Chromium, Chrome
- **Dependencias:** `flask`, `conky`

## 🚀 Instalación

```bash
# 1. Clonar
git clone https://github.com/Mikutabby/nexo-ui.git
cd nexo-ui

# 2. Instalar
bash install.sh

# 3. Iniciar
nexo-ui start
```

O directamente:
```bash
curl -sSL https://raw.githubusercontent.com/Mikutabby/nexo-ui/main/install.sh | bash
```

## 🎮 Uso

```bash
nexo-ui start      # Iniciar todo (daemon + web + widget)
nexo-ui stop       # Detener todo
nexo-ui status     # Ver estado
nexo-ui open       # Abrir HUD en navegador
nexo-ui mini       # Abrir versión miniatura
nexo-ui web        # Solo web app
nexo-ui widget     # Solo widget Conky
nexo-ui daemon     # Controlar daemon de sincronización
```

### Acceso

| URL | Descripción |
|-----|-------------|
| `http://127.0.0.1:7070` | HUD principal |
| `http://127.0.0.1:7070/mini` | Versión miniatura |
| `http://127.0.0.1:7070/api/state` | Estado en JSON |
| `ws://127.0.0.1:7071` | WebSocket en tiempo real |

## 🏗️ Estructura del proyecto

```
nexo-ui/
├── install.sh                    # Instalador
├── README.md                     # Este archivo
├── requirements.txt              # Dependencias Python
├── LICENSE                       # MIT
├── config/
│   └── nexo-ui.json              # Configuración principal
├── conky/
│   ├── nexo-widget.conf          # Config del widget Conky
│   └── nexo-status.py            # Script de estado para Conky
├── sync/
│   └── nexo-ui-daemon.py         # Daemon de sincronización + WebSocket
└── web/
    ├── app.py                    # Flask web app
    ├── static/
    │   ├── css/hud.css           # Estilo HUD Iron Man
    │   └── js/hud.js             # Lógica de la interfaz
    └── templates/
        ├── index.html            # HUD principal
        └── mini.html             # Versión miniatura
```

## 🔧 Arquitectura

```
┌──────────────┐    WebSocket     ┌──────────────┐
│   Conky      │ ◄──── ws ────►   │  Web App     │
│   Widget     │                  │  Flask       │
│   (escritorio)│                  │  (navegador)  │
└──────┬───────┘                  └──────┬───────┘
       │                                 │
       │        ┌──────────────┐         │
       └───────►│  State JSON  │◄────────┘
                │  /tmp/nexo-  │
                │  ui-state    │
                └──────┬───────┘
                       │
                ┌──────▼───────┐
                │  Nexo Daemon │
                │  (sync)      │
                └──────────────┘
```

## 🤝 Integración con Nexo

Nexo UI es independiente pero se integra naturalmente con el ecosistema Nexo:

- **Estado**: detecta automáticamente si `nexo-wake` está activo
- **Comandos**: envía comandos vía API REST
- **TTS**: las respuestas pueden hablarse con `say.sh`
- **Widget**: muestra el estado actual de Nexo en tiempo real

## 📄 Licencia

MIT — ver [LICENSE](LICENSE)

---

*Built with 💙 for mikuyasha*
