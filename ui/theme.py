"""
theme.py — Temas de color para Nexo 2.0 UI
"""
from __future__ import annotations

THEMES: dict[str, dict] = {
    "cyan": {
        "NAME": "Nexo Cyan", "PRI": "#00d4ff", "PRI_DIM": "#005f77",
        "BG": "#050c14", "GRID": "#0a1620", "PANEL": "#070f18",
        "BORDER": "#0d2540", "BORDER_A": "#1a5070",
        "TEXT": "#7aeeff", "TEXT_DIM": "#2e6070", "TEXT_MED": "#4aaccf",
    },
    "green": {
        "NAME": "Matrix Green", "PRI": "#00ff88", "PRI_DIM": "#006633",
        "BG": "#040e08", "GRID": "#081a10", "PANEL": "#061208",
        "BORDER": "#0a2a18", "BORDER_A": "#155a30",
        "TEXT": "#7affcc", "TEXT_DIM": "#1f5535", "TEXT_MED": "#3aaa77",
    },
    "purple": {
        "NAME": "Quantum Purple", "PRI": "#a855f7", "PRI_DIM": "#5b21b6",
        "BG": "#07030f", "GRID": "#0f0618", "PANEL": "#0a0412",
        "BORDER": "#2d1b69", "BORDER_A": "#4c1d95",
        "TEXT": "#c084fc", "TEXT_DIM": "#3b2062", "TEXT_MED": "#8b5cf6",
    },
    "gold": {
        "NAME": "Amber Gold", "PRI": "#f59e0b", "PRI_DIM": "#78350f",
        "BG": "#0c0a00", "GRID": "#1a1400", "PANEL": "#100c00",
        "BORDER": "#292524", "BORDER_A": "#57534e",
        "TEXT": "#fde68a", "TEXT_DIM": "#57430c", "TEXT_MED": "#d97706",
    },
}

STATE_RGB: dict[str, tuple[int, int, int]] = {
    "LISTENING":   (0,   212, 255),
    "IDLE":        (0,   180, 255),
    "INITIATING":  (0,   100, 180),
    "THINKING":    (60,  130, 255),
    "SPEAKING":    (120, 240, 255),
    "PROCESSING":  (130,  70, 255),
    "MUTED":       (40,   60,  80),
    "MUSIC":       (255,  45, 200),
    "ALERT":       (255,  60,  60),
    "SUCCESS":     (0,   255, 136),
    "SEARCHING":   (80,  200, 255),
    "LOADING":     (40,  120, 255),
    "BREATHING":   (0,   212, 255),
}


def load_theme(name: str = "cyan") -> dict:
    """Carga un tema y lo devuelve."""
    t = THEMES.get(name, THEMES["cyan"]).copy()
    return t


def apply_theme(theme: dict):
    """Aplica el theme al módulo."""
    global _current
    _current = theme.copy()
    _refresh_state_rgb()


_current = THEMES["cyan"].copy()


def _refresh_state_rgb():
    """Actualiza colores de estado desde el tema actual."""
    from .theme import _current as c
    import math
    pr, pg, pb = _hex_to_rgb(c.get("PRI", "#00d4ff"))
    dr, dg, db = _hex_to_rgb(c.get("PRI_DIM", "#005f77"))
    STATE_RGB.update({
        "LISTENING": (pr, pg, pb),
        "IDLE": (_dim(pr, 0.84), _dim(pg, 0.84), _dim(pb, 0.84)),
        "INITIATING": (dr, dg, db),
        "SPEAKING": (min(255, pr + 40), min(255, pg + 20), min(255, pb)),
        "BREATHING": (pr, pg, pb),
    })


def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _dim(v: int, f: float) -> int:
    return max(0, min(255, int(v * f)))


def qcol(h: str, a: int = 255):
    from PyQt6.QtGui import QColor
    c = QColor(h)
    c.setAlpha(a)
    return c
