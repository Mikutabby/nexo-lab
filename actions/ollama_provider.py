"""
ollama_provider.py — Ollama local LLM client for Nexo 2.0.
Adaptado de JARVIS para Linux.
"""
from __future__ import annotations

import json
import sys
import urllib.request
import urllib.error
from pathlib import Path

_DEFAULT_BASE_URL = "http://localhost:11434"
_DEFAULT_MODEL    = "qwen2:0.5b"
_TIMEOUT_PING     = 3
_TIMEOUT_CHAT     = 120  # timeout para modelos lentos en PC vieja


def _base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


def _get_config() -> dict:
    try:
        return json.loads((_base_dir() / "config" / "api_keys.json").read_text(encoding="utf-8"))
    except Exception:
        try:
            return json.loads((_base_dir() / "config" / "config.json").read_text(encoding="utf-8"))
        except Exception:
            return {}


def is_available() -> bool:
    cfg = _get_config()
    base = cfg.get("ollama_base_url", _DEFAULT_BASE_URL)
    try:
        req = urllib.request.Request(f"{base}/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=_TIMEOUT_PING):
            return True
    except Exception:
        return False


def list_models() -> list[str]:
    cfg = _get_config()
    base = cfg.get("ollama_base_url", _DEFAULT_BASE_URL)
    try:
        req = urllib.request.Request(f"{base}/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=_TIMEOUT_PING) as resp:
            data = json.loads(resp.read())
            return [m["name"] for m in data.get("models", [])]
    except Exception:
        return []


def get_chat_model() -> str:
    """Devuelve el primer modelo de chat disponible."""
    cfg = _get_config()
    model = cfg.get("ollama_model", _DEFAULT_MODEL)
    models = list_models()
    chat_models = [m for m in models if "embed" not in m.lower()]
    if chat_models:
        return chat_models[0]
    return model


def chat(prompt: str, system: str = "") -> str:
    """Envía un prompt a Ollama y devuelve la respuesta."""
    cfg = _get_config()
    base = cfg.get("ollama_base_url", _DEFAULT_BASE_URL)
    model = get_chat_model()

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "keep_alive": "30m",  # mantener modelo en RAM 30min
        "options": {
            "num_predict": 50,      # respuestas cortas (~10 palabras)
            "num_ctx": 256,         # contexto mínimo para acelerar
            "temperature": 0.7
        }
    }
    if system:
        payload["system"] = system

    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{base}/api/generate",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT_CHAT) as resp:
            result = json.loads(resp.read())
            return result.get("response", "").strip()
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Ollama HTTP Error {e.code}: {e.reason}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"Ollama no disponible en {base} — {e.reason}")
    except Exception as e:
        raise RuntimeError(f"Error con Ollama: {e}")


def pull_model(model_name: str) -> tuple[bool, str]:
    """Descarga un modelo de Ollama."""
    cfg = _get_config()
    base = cfg.get("ollama_base_url", _DEFAULT_BASE_URL)
    try:
        payload = json.dumps({"name": model_name, "stream": False}).encode()
        req = urllib.request.Request(
            f"{base}/api/pull",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=600) as resp:
            data = json.loads(resp.read())
            if data.get("status") == "success":
                return True, f"Modelo '{model_name}' descargado."
            return False, data.get("status", "Error")
    except Exception as e:
        return False, f"Error: {e}"
