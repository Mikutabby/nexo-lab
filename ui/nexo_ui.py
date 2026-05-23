#!/usr/bin/env python3
"""
nexo_ui.py — UI principal de Nexo 2.0
Basada en J.A.R.V.I.S v5.0 por Blazehue.
Versión ligera con widgets esenciales.
"""
from __future__ import annotations

import json
import math
import random
import subprocess
import sys
import time
from collections import deque
from datetime import datetime
from pathlib import Path

import psutil

from PyQt6.QtCore import (
    QEasingCurve, QPointF, QPropertyAnimation, QRectF, Qt, QTimer,
    pyqtSignal, QSize,
)
from PyQt6.QtGui import (
    QBrush, QColor, QFont, QPainter, QPainterPath, QPen, QRadialGradient,
    QKeySequence, QShortcut, QMouseEvent, QPixmap, QAction, QIcon,
)
from PyQt6.QtWidgets import (
    QApplication, QHBoxLayout, QLabel, QLineEdit, QMainWindow,
    QPushButton, QScrollArea, QSizePolicy, QVBoxLayout, QWidget,
    QFrame, QGraphicsOpacityEffect, QGraphicsDropShadowEffect,
    QSystemTrayIcon, QMenu, QTextEdit,
)

from .theme import _current as C, STATE_RGB, qcol, _hex_to_rgb, load_theme

# ── Config ─────────────────────────────────────────────────────────────────
APP_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = APP_DIR / "config"
_DEFAULT_W = 1280
_DEFAULT_H = 720
_MIN_W = 800
_MIN_H = 600


# ═══════════════════════════════════════════════════════════════════════════
# PARTICLE ORB — Esfera de partículas animada
# ═══════════════════════════════════════════════════════════════════════════
class Particle:
    TRAIL_LEN = 12

    def __init__(self, x: float, y: float, idx: int):
        self.x = x
        self.y = y
        self.tx = x
        self.ty = y
        self.vx = 0.0
        self.vy = 0.0
        self.idx = idx
        self.size = random.uniform(1.0, 2.6)
        self.phase = random.uniform(0.0, math.pi * 2)
        self.speed = random.uniform(0.12, 0.26)
        self.trail: deque[tuple[float, float]] = deque(maxlen=self.TRAIL_LEN)

    def update(self, tick: int, noise: float = 1.5):
        nx = math.sin(tick * 0.017 + self.phase) * noise
        ny = math.cos(tick * 0.013 + self.phase * 1.37) * noise
        dx = (self.tx + nx) - self.x
        dy = (self.ty + ny) - self.y
        self.vx = self.vx * 0.86 + dx * self.speed * 0.12
        self.vy = self.vy * 0.86 + dy * self.speed * 0.12
        self.trail.append((self.x, self.y))
        self.x += self.vx
        self.y += self.vy


class ParticleOrb(QWidget):
    N = 130
    _MORPH_DURATION = 25

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)
        self.setMinimumSize(80, 80)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMouseTracking(True)

        self._state = "INITIATING"
        self._tick = 0
        self._audio = 0.0
        self._blink = True
        self._btick = 0
        self._cx = 0.0
        self._cy = 0.0
        self._R = 0.0
        self._particles: list[Particle] = []
        self._static_tgts: list[tuple] | None = None
        self._prev_tgts: list[tuple] | None = None
        self._transition_ticks = 0

        self._cur_r, self._cur_g, self._cur_b = 0.0, 212.0, 255.0
        self._col_spd = 0.15

        self._mx = 0.0
        self._my = 0.0
        self._mforce = 0.0
        self._mattract = False

        self._tmr = QTimer(self)
        self._tmr.timeout.connect(self._step)
        self._tmr.start(16)

    def _ensure(self):
        W, H = self.width(), self.height()
        if W < 20 or H < 20:
            return
        self._cx = W / 2.0
        self._cy = H / 2.0
        self._R = min(W, H) * 0.38
        if not self._particles:
            for i in range(self.N):
                a = random.uniform(0, math.pi * 2)
                r = random.uniform(0, self._R * 0.08)
                self._particles.append(Particle(
                    self._cx + r * math.cos(a),
                    self._cy + r * math.sin(a), i))

    def mousePressEvent(self, event: QMouseEvent):
        pos = event.position()
        self._mx, self._my = pos.x(), pos.y()
        self._mforce = 1.0
        self._mattract = (event.button() == Qt.MouseButton.RightButton)

    def mouseMoveEvent(self, event: QMouseEvent):
        pos = event.position()
        self._mx, self._my = pos.x(), pos.y()
        if event.buttons() & (Qt.MouseButton.LeftButton | Qt.MouseButton.RightButton):
            self._mforce = min(1.0, self._mforce + 0.08)
            self._mattract = bool(event.buttons() & Qt.MouseButton.RightButton)

    def _f_sphere(self):
        g = math.pi * (3 - math.sqrt(5))
        pts = []
        for i in range(self.N):
            y = 1 - (i / (self.N - 1)) * 2
            r = math.sqrt(max(0.0, 1 - y * y))
            th = g * i
            x = r * math.cos(th)
            z = r * math.sin(th)
            d = (z + 1.65) / 2.65
            pts.append((self._cx + x * self._R * d, self._cy + y * self._R * 0.88 * d))
        return pts

    def _f_vortex(self):
        rot = self._tick * 0.042
        pts = []
        for i in range(self.N):
            t = i / self.N
            arm = i % 3
            a = t * 10 * math.pi + rot + arm * (math.pi * 2 / 3)
            r = self._R * (0.05 + 0.92 * (t ** 0.5)) * 0.88
            pts.append((self._cx + r * math.cos(a), self._cy + r * math.sin(a) * 0.62))
        return pts

    def _f_rings(self):
        RINGS = 7
        per = max(1, self.N // RINGS)
        al = self._audio
        rot = self._tick * 0.008
        pulse = math.sin(self._tick * 0.05) * 0.12
        pts = []
        for i in range(self.N):
            ring = min(i // per, RINGS - 1)
            pos = i % per
            a = (pos / per) * 2 * math.pi + ring * 0.6 + rot
            r = self._R * (ring + 1) / RINGS * (0.65 + 0.38 * al + pulse)
            pts.append((self._cx + r * math.cos(a), self._cy + r * math.sin(a) * 0.78))
        return pts

    def _f_helix(self):
        rot = self._tick * 0.022
        pts = []
        for i in range(self.N):
            t = i / self.N
            y = (t - 0.5) * self._R * 2.1
            phase = t * 6 * math.pi + rot
            strand = i % 3
            s = strand * (math.pi * 2 / 3)
            x = self._R * 0.35 * math.cos(phase + s)
            pts.append((self._cx + x, self._cy + y))
        return pts

    def _f_collapse(self):
        g = math.pi * (3 - math.sqrt(5))
        pts = []
        for i in range(self.N):
            a = g * i
            r = self._R * 0.07 * (i / self.N)
            pts.append((self._cx + r * math.cos(a), self._cy + r * math.sin(a)))
        return pts

    def _f_grid(self):
        COLS = int(math.sqrt(self.N * 1.7)) + 1
        ROWS = (self.N + COLS - 1) // COLS
        gw = self._R * 1.75 / COLS
        gh = gw * 0.88
        ox = self._cx - COLS * gw / 2
        oy = self._cy - ROWS * gh / 2
        pts = []
        for i in range(self.N):
            row = i // COLS
            col = i % COLS
            hx = (row % 2) * gw * 0.5
            pts.append((ox + col * gw + hx, oy + row * gh))
        return pts

    def _f_bars(self):
        BARS = 14
        per = max(1, self.N // BARS)
        bw = self._R * 1.75 / BARS
        pts = []
        for i in range(self.N):
            b = min(i // per, BARS - 1)
            pos = i % per
            x = self._cx + (b - BARS / 2 + 0.5) * bw
            h = self._R * 0.88 * abs(math.sin(self._tick * 0.07 + b * 0.8))
            y = self._cy + h * (1 - 2 * pos / per)
            pts.append((x, y))
        return pts

    def _f_star(self):
        ARMS = 8
        per = max(1, self.N // ARMS)
        rot = self._tick * 0.022
        pts = []
        for i in range(self.N):
            arm = i // per
            pos = i % per
            t = pos / per
            a = (arm / ARMS) * 2 * math.pi + rot + math.sin(t * 6) * 0.28
            r = self._R * (0.08 + 0.92 * t)
            pts.append((self._cx + r * math.cos(a), self._cy + r * math.sin(a) * 0.88))
        return pts

    def _f_nebula(self):
        g = math.pi * (3 - math.sqrt(5))
        pts = []
        for i in range(self.N):
            t = i / self.N
            a = g * i
            r = self._R * (0.06 + 0.74 * (math.sin(t * math.pi)) ** 1.5)
            swirl = t * 4 * math.pi * math.sin(self._tick * 0.014)
            pts.append((self._cx + r * math.cos(a + swirl), self._cy + r * math.sin(a + swirl) * 0.85))
        return pts

    def _f_pulse(self):
        g = math.pi * (3 - math.sqrt(5))
        amp = 0.85 + 0.22 * math.sin(self._tick * 0.20)
        pts = []
        for i in range(self.N):
            y = 1 - (i / (self.N - 1)) * 2
            r = math.sqrt(max(0.0, 1 - y * y))
            th = g * i
            x = r * math.cos(th)
            z = r * math.sin(th)
            d = (z + 1.65) / 2.65
            pts.append((self._cx + x * self._R * d * amp, self._cy + y * self._R * 0.88 * d * amp))
        return pts

    def _f_wave(self):
        LINES = 9
        per = max(1, self.N // LINES)
        scan = (self._tick * 0.04) % (math.pi * 2)
        pts = []
        for i in range(self.N):
            line = min(i // per, LINES - 1)
            pos = i % per
            t = pos / per
            x = self._cx + (t - 0.5) * self._R * 1.8
            y = self._cy + (line - LINES / 2 + 0.5) * self._R * 0.22
            y += math.sin(t * math.pi * 3 + scan + line * 0.7) * self._R * 0.12
            pts.append((x, y))
        return pts

    def _f_orbit(self):
        RINGS = 5
        per = max(1, self.N // RINGS)
        pts = []
        for i in range(self.N):
            ring = min(i // per, RINGS - 1)
            pos = i % per
            spd = 0.025 + ring * 0.012
            a = (pos / per) * 2 * math.pi + self._tick * spd
            r = self._R * (0.22 + ring * 0.16)
            tilt = 0.25 + ring * 0.18
            pts.append((self._cx + r * math.cos(a), self._cy + r * math.sin(a) * tilt))
        return pts

    def _f_success(self):
        PETALS = 8
        per = max(1, self.N // PETALS)
        rot = self._tick * 0.010
        pts = []
        for i in range(self.N):
            pet = min(i // per, PETALS - 1)
            pos = i % per
            t = pos / per
            a = (pet / PETALS) * 2 * math.pi + rot
            r = self._R * 0.85 * math.sin(t * math.pi)
            pts.append((self._cx + r * math.cos(a), self._cy + r * math.sin(a) * 0.9))
        return pts

    def _f_tornado(self):
        rot = self._tick * 0.055
        pts = []
        for i in range(self.N):
            t = i / self.N
            y = (t - 0.5) * self._R * 2.0
            taper = 0.08 + (1 - t) * 0.90
            a = t * 14 * math.pi + rot
            r = self._R * taper
            pts.append((self._cx + r * math.cos(a), self._cy + y))
        return pts

    def _f_breathing(self):
        g = math.pi * (3 - math.sqrt(5))
        scale = 0.65 + 0.35 * (0.5 + 0.5 * math.sin(self._tick * 0.025))
        pts = []
        for i in range(self.N):
            y = 1 - (i / (self.N - 1)) * 2
            r = math.sqrt(max(0.0, 1 - y * y))
            th = g * i
            x = r * math.cos(th)
            z = r * math.sin(th)
            d = (z + 1.65) / 2.65
            pts.append((self._cx + x * self._R * d * scale, self._cy + y * self._R * 0.88 * d * scale))
        return pts

    def _f_comet(self):
        rot = self._tick * 0.018
        TAIL = self.N
        pts = []
        for i in range(TAIL):
            t = i / TAIL
            a = rot - t * 1.8
            r = self._R * (0.50 + 0.40 * math.cos(t * math.pi))
            ell = 0.55
            pts.append((self._cx + r * math.cos(a), self._cy + r * math.sin(a) * ell))
        return pts

    def _f_matrix(self):
        COLS = 12
        per = max(1, self.N // COLS)
        cw = self._R * 1.80 / COLS
        pts = []
        for i in range(self.N):
            col = i // per
            pos = i % per
            x = self._cx + (col - COLS / 2 + 0.5) * cw
            spd = 0.04 + (col % 3) * 0.015
            y = self._cy + self._R * ((pos / per + self._tick * spd) % 2 - 1)
            pts.append((x, y))
        return pts

    def _targets(self):
        s = self._state
        if s == "THINKING": return self._f_vortex()
        elif s == "SPEAKING": return self._f_rings()
        elif s == "PROCESSING": return self._f_helix()
        elif s == "MUTED": return self._f_collapse()
        elif s in ("WORK", "WORKING"): return self._f_grid()
        elif s in ("MUSIC", "PLAYING"): return self._f_bars()
        elif s in ("GAMING", "GAME"): return self._f_star()
        elif s == "INITIATING": return self._f_nebula()
        elif s == "ALERT": return self._f_pulse()
        elif s == "SEARCHING": return self._f_wave()
        elif s == "LOADING": return self._f_orbit()
        elif s == "SUCCESS": return self._f_success()
        elif s == "IDLE": return self._f_comet()
        elif s == "BREATHING": return self._f_breathing()
        else: return self._f_sphere()

    def _targets_morphed(self):
        new_tgts = self._targets()
        if (self._transition_ticks > 0 and self._prev_tgts
                and len(self._prev_tgts) == len(new_tgts)):
            self._transition_ticks -= 1
            t = 1.0 - (self._transition_ticks / self._MORPH_DURATION)
            t = t * t * (3.0 - 2.0 * t)
            return [(p[0] * (1 - t) + n[0] * t, p[1] * (1 - t) + n[1] * t)
                    for p, n in zip(self._prev_tgts, new_tgts)]
        return new_tgts

    def _step(self):
        if not self.isVisible() or self.width() < 20 or self.height() < 20:
            return
        self._ensure()
        self._tick += 1

        tr, tg, tb = STATE_RGB.get(self._state, (0, 212, 255))
        self._cur_r += (tr - self._cur_r) * self._col_spd
        self._cur_g += (tg - self._cur_g) * self._col_spd
        self._cur_b += (tb - self._cur_b) * self._col_spd

        self._btick += 1
        if self._btick >= 26:
            self._blink = not self._blink
            self._btick = 0

        DYNAMIC = {"THINKING", "SPEAKING", "PROCESSING", "MUSIC", "PLAYING",
                   "GAMING", "GAME", "WORK", "WORKING", "SEARCHING", "LOADING",
                   "ALERT", "BREATHING"}
        if self._state in DYNAMIC or self._transition_ticks > 0:
            tgts = self._targets_morphed()
        else:
            if self._static_tgts is None:
                self._static_tgts = self._targets()
            tgts = self._static_tgts

        for i, p in enumerate(self._particles):
            if i < len(tgts):
                p.tx, p.ty = tgts[i]

        noise = {
            "THINKING": 0.5, "SPEAKING": 1.0 + self._audio * 3.5,
            "LISTENING": 2.6, "MUTED": 0.10, "PROCESSING": 0.40,
            "GAMING": 1.8, "GAME": 1.8, "MUSIC": 0.85, "PLAYING": 0.85,
            "WORK": 0.22, "WORKING": 0.22, "INITIATING": 1.4, "ALERT": 2.0,
            "SEARCHING": 1.0, "LOADING": 0.50, "SUCCESS": 0.9, "IDLE": 0.4,
            "BREATHING": 0.3,
        }.get(self._state, 2.0)

        if self._mforce > 0.01:
            self._mforce *= 0.94
            for p in self._particles:
                dx, dy = self._mx - p.x, self._my - p.y
                d = math.hypot(dx, dy) + 1.0
                f = self._mforce * 90.0 / (d * d * 0.006 + 60.0)
                if self._mattract:
                    p.vx += (dx / d) * f
                    p.vy += (dy / d) * f
                else:
                    p.vx -= (dx / d) * f
                    p.vy -= (dy / d) * f

        for p in self._particles:
            p.update(self._tick, noise)

        self.update()
        is_dynamic = self._state in DYNAMIC or self._mforce > 0.01 or self._transition_ticks > 0
        self._tmr.setInterval(16 if is_dynamic else 33)

    def set_state(self, state: str):
        new = state.upper()
        if new == self._state:
            return
        self._prev_tgts = [(p.x, p.y) for p in self._particles] if self._particles else None
        self._state = new
        self._static_tgts = None
        self._transition_ticks = self._MORPH_DURATION

    def set_audio(self, level: float):
        self._audio = max(0.0, min(1.0, level))

    def _rgb(self):
        return (int(self._cur_r), int(self._cur_g), int(self._cur_b))

    def paintEvent(self, _):
        if not self._particles:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        W, H = self.width(), self.height()
        cx, cy = self._cx or W / 2, self._cy or H / 2
        R = self._R or min(W, H) * 0.38
        cr, cg, cb = self._rgb()
        al = self._audio

        p.fillRect(self.rect(), QColor(5, 12, 20))

        # Center glow
        gr = R * (1.20 + al * 0.30)
        glow = QRadialGradient(cx, cy, gr)
        glow.setColorAt(0.0, QColor(cr, cg, cb, int(22 + al * 38)))
        glow.setColorAt(0.55, QColor(cr, cg, cb, int(7 + al * 14)))
        glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setBrush(QBrush(glow))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QRectF(cx - gr, cy - gr, gr * 2, gr * 2))

        # Connection lines
        DYNAMIC = {"THINKING", "SPEAKING", "PROCESSING", "MUSIC", "PLAYING",
                   "GAMING", "GAME", "WORK", "WORKING", "SEARCHING", "LOADING",
                   "ALERT", "BREATHING"}
        state = self._state
        MAX_D = 82.0 if state in DYNAMIC else 55.0
        step = 1 if state in DYNAMIC else 2
        parts = self._particles
        for i in range(0, len(parts), step):
            pi = parts[i]
            for j in range(i + 1, min(i + 20, len(parts))):
                pj = parts[j]
                d = math.hypot(pi.x - pj.x, pi.y - pj.y)
                if d < MAX_D:
                    t_ = 1 - d / MAX_D
                    a_ = int(t_ ** 1.7 * 72)
                    pw = 0.22 + t_ * 0.9
                    p.setPen(QPen(QColor(cr, cg, cb, a_), pw))
                    p.drawLine(QPointF(pi.x, pi.y), QPointF(pj.x, pj.y))

        # Trails
        p.setPen(Qt.PenStyle.NoPen)
        for part in parts:
            trail = list(part.trail)
            n = len(trail)
            for k in range(1, n):
                t_ = k / n
                a_ = int(t_ ** 1.3 * 100)
                pw = 0.22 + t_ * 1.7
                p.setPen(QPen(QColor(cr, cg, cb, a_), pw))
                p.drawLine(QPointF(trail[k - 1][0], trail[k - 1][1]),
                           QPointF(trail[k][0], trail[k][1]))

            s = part.size * (1.0 + al * 0.5)
            rg = QRadialGradient(part.x, part.y, s * 2.6)
            rg.setColorAt(0.0, QColor(215, 248, 255, 230))
            rg.setColorAt(0.35, QColor(cr, cg, cb, 190))
            rg.setColorAt(1.0, QColor(cr, cg, cb, 0))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(rg))
            p.drawEllipse(QPointF(part.x, part.y), s * 2.6, s * 2.6)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._cx = self.width() / 2.0
        self._cy = self.height() / 2.0
        self._R = min(self.width(), self.height()) * 0.38
        self._static_tgts = None


# ═══════════════════════════════════════════════════════════════════════════
# DRAGGABLE WIDGET — Widget flotante
# ═══════════════════════════════════════════════════════════════════════════
class DraggableWidget(QFrame):
    closed = pyqtSignal(object)

    def __init__(self, title: str, icon: str, accent: str = "",
                 closeable: bool = True, parent=None):
        super().__init__(parent)
        self.setObjectName("DraggableWidget")
        self._accent = accent or C.get("PRI", "#00d4ff")
        self._drag_pos = None

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(36)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(0, 0, 0, 180))
        self.setGraphicsEffect(shadow)
        self.setStyleSheet(f"""
            QFrame#DraggableWidget {{
                background: {C.get("PANEL", "#070f18")};
                border: 1px solid {C.get("BORDER", "#0d2540")};
                border-radius: 20px;
            }}
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header
        self._hdr = QWidget()
        self._hdr.setFixedHeight(40)
        self._hdr.setCursor(Qt.CursorShape.SizeAllCursor)
        self._hdr.setStyleSheet(f"""
            background: #000000;
            border-top-left-radius: 20px;
            border-top-right-radius: 20px;
            border-bottom: 1px solid {C.get("BORDER", "#0d2540")};
        """)
        hl = QHBoxLayout(self._hdr)
        hl.setContentsMargins(14, 0, 10, 0)
        hl.setSpacing(7)

        dot = QLabel("●")
        dot.setFont(QFont("Segoe UI", 7))
        dot.setStyleSheet(f"color: {self._accent}; background: transparent; border: none;")
        hl.addWidget(dot)

        ico = QLabel(icon)
        ico.setFont(QFont("Arial", 12))
        ico.setStyleSheet(f"color: {self._accent}; background: transparent; border: none;")
        hl.addWidget(ico)

        tl = QLabel(title)
        tl.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        tl.setStyleSheet("color: #ffffff; background: transparent; border: none;")
        hl.addWidget(tl)
        hl.addStretch()

        if closeable:
            cb = QPushButton("✕")
            cb.setFixedSize(20, 20)
            cb.setFont(QFont("Segoe UI", 8))
            cb.setCursor(Qt.CursorShape.PointingHandCursor)
            cb.setStyleSheet(f"""
                QPushButton {{ background: transparent; color: #555555;
                    border: none; border-radius: 10px; }}
                QPushButton:hover {{ color: #ff3355; background: rgba(255,51,85,0.18); }}
            """)
            cb.clicked.connect(self._on_close)
            hl.addWidget(cb)

        root.addWidget(self._hdr)
        self._body = QVBoxLayout()
        self._body.setContentsMargins(10, 6, 10, 10)
        self._body.setSpacing(5)
        root.addLayout(self._body, stretch=1)

    def _on_close(self):
        self.hide()
        self.closed.emit(self)

    def mousePressEvent(self, event: QMouseEvent):
        if (event.button() == Qt.MouseButton.LeftButton
                and self._hdr.geometry().contains(event.pos())):
            gp = event.globalPosition()
            self._drag_pos = QPoint(int(gp.x()) - self.x(), int(gp.y()) - self.y())
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._drag_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            gp = event.globalPosition()
            nx = int(gp.x()) - self._drag_pos.x()
            ny = int(gp.y()) - self._drag_pos.y()
            if self.parent():
                nx = max(0, min(nx, self.parent().width() - self.width()))
                ny = max(0, min(ny, self.parent().height() - self.height()))
            self.move(nx, ny)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_pos = None
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def show_animated(self):
        self.show()
        self.raise_()
        eff = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(eff)
        anim = QPropertyAnimation(eff, b"opacity", self)
        anim.setDuration(150)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)

    def hide_animated(self):
        eff = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(eff)
        anim = QPropertyAnimation(eff, b"opacity", self)
        anim.setDuration(120)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.Type.InCubic)
        anim.finished.connect(self.hide)
        anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)


# ═══════════════════════════════════════════════════════════════════════════
# METRIC BAR — Barra animada de métricas
# ═══════════════════════════════════════════════════════════════════════════
class MetricBar(QWidget):
    def __init__(self, label: str, unit: str = "%", color: str = "", parent=None):
        super().__init__(parent)
        self._label = label
        self._unit = unit
        self._color = color or C.get("PRI", "#00d4ff")
        self._value = 0.0
        self._text = "0"
        self._anim = 0.0
        self.setFixedHeight(30)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        tmr = QTimer(self)
        tmr.timeout.connect(self._animate)
        tmr.start(24)

    def set_value(self, pct: float, text: str):
        self._value = max(0.0, min(100.0, pct))
        self._text = text.split()[0] if text else "0"

    def _animate(self):
        self._anim += (self._value - self._anim) * 0.18
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        W, H = self.width(), self.height()
        v = self._anim
        col = qcol(C.get("RED", "#ff3355")) if v > 85 else qcol(C.get("ACC", "#ff6600")) if v > 65 else qcol(self._color)

        p.setFont(QFont("Segoe UI", 8))
        p.setPen(QPen(qcol(C.get("TEXT_DIM", "#2e6070")), 1))
        p.drawText(QRectF(0, 0, W * 0.55, 20),
                   Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self._label)

        p.setFont(QFont("Consolas", 8, QFont.Weight.Bold))
        p.setPen(QPen(col, 1))
        p.drawText(QRectF(W * 0.40, 0, W * 0.60, 20),
                   Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, self._text)

        by, bh = 24, 3
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(qcol("#060f1a", 180)))
        p.drawRoundedRect(QRectF(0, by, W, bh), 1.5, 1.5)

        fw = W * (v / 100.0)
        if fw > 0.5:
            p.setBrush(QBrush(col))
            p.drawRoundedRect(QRectF(0, by, fw, bh), 1.5, 1.5)


# ═══════════════════════════════════════════════════════════════════════════
# CLOCK WIDGET — Reloj
# ═══════════════════════════════════════════════════════════════════════════
class ClockWidget(DraggableWidget):
    def __init__(self, parent=None):
        super().__init__("RELOJ", "◷", C.get("PRI", "#00d4ff"), closeable=True, parent=parent)
        self.resize(200, 130)

        self._time = QLabel("00:00:00")
        self._time.setFont(QFont("Consolas", 22, QFont.Weight.Bold))
        self._time.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._time.setStyleSheet(f"color: {C.get('PRI', '#00d4ff')}; background: transparent;")
        self._body.addWidget(self._time)

        self._date = QLabel("")
        self._date.setFont(QFont("Segoe UI", 9))
        self._date.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._date.setStyleSheet(f"color: {C.get('TEXT_DIM', '#2e6070')}; background: transparent;")
        self._body.addWidget(self._date)

        tmr = QTimer(self)
        tmr.timeout.connect(self._tick)
        tmr.start(1000)
        self._tick()

    def _tick(self):
        now = datetime.now()
        dias = ["LUN", "MAR", "MIÉ", "JUE", "VIE", "SÁB", "DOM"]
        self._time.setText(now.strftime("%H:%M:%S"))
        self._date.setText(f"{dias[now.weekday()]}  {now.strftime('%d/%m/%Y')}")


# ═══════════════════════════════════════════════════════════════════════════
# SYSTEM WIDGET — Monitor de sistema
# ═══════════════════════════════════════════════════════════════════════════
class SystemWidget(DraggableWidget):
    def __init__(self, parent=None):
        super().__init__("SISTEMA", "⚡", C.get("GREEN", "#00ff88"), closeable=True, parent=parent)
        self.resize(250, 175)

        self._gauges: dict[str, MetricBar] = {}
        for label, unit, color in [
            ("CPU", "%", C.get("PRI", "#00d4ff")),
            ("RAM", "%", C.get("GREEN", "#00ff88")),
            ("TEMP", "°C", C.get("ACC", "#ff6600")),
        ]:
            g = MetricBar(label, unit, color)
            self._gauges[label] = g
            self._body.addWidget(g)

        tmr = QTimer(self)
        tmr.timeout.connect(self._update)
        tmr.start(2000)
        self._update()

    def _update(self):
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory().percent
        temp = -1.0
        try:
            ts = psutil.sensors_temperatures()
            for name in ["coretemp", "k10temp", "cpu_thermal", "acpitz"]:
                if name in ts and ts[name]:
                    temp = ts[name][0].current
                    break
        except Exception:
            pass
        # Fallback: leer thermal_zone
        if temp < 0:
            try:
                temp = int(open("/sys/class/thermal/thermal_zone1/temp").read().strip()) / 1000
            except Exception:
                temp = 0

        self._gauges["CPU"].set_value(cpu, f"{cpu:.0f}%")
        self._gauges["RAM"].set_value(mem, f"{mem:.0f}%")
        self._gauges["TEMP"].set_value(min(temp, 100) if temp >= 0 else 0,
                                        f"{temp:.0f}°" if temp >= 0 else "N/A")


# ═══════════════════════════════════════════════════════════════════════════
# TRANSCRIPT AREA — Texto de transcripción
# ═══════════════════════════════════════════════════════════════════════════
class TranscriptArea(QWidget):
    _chunk = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background: rgba(3,10,18,200); border-top: 1px solid rgba(13,37,66,0.5);")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 10, 24, 10)
        lay.setSpacing(0)

        self._lbl = QLabel("")
        self._lbl.setFont(QFont("Segoe UI", 13))
        self._lbl.setWordWrap(True)
        self._lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self._lbl.setStyleSheet("color: #ffffff; background: transparent;")
        self._lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        lay.addWidget(self._lbl)

        self._full = ""
        self._chunk.connect(self._on_chunk)
        self._eff = QGraphicsOpacityEffect(self._lbl)
        self._eff.setOpacity(1.0)
        self._lbl.setGraphicsEffect(self._eff)

    def append_text(self, chunk: str):
        self._chunk.emit(chunk)

    def _on_chunk(self, chunk: str):
        if chunk == "__clear__":
            self._full = ""
            self._lbl.setText("")
            anim = QPropertyAnimation(self._eff, b"opacity", self)
            anim.setDuration(80)
            anim.setStartValue(1.0)
            anim.setEndValue(0.0)
            anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
            return
        if not self._full:
            self._eff.setOpacity(0.0)
            anim = QPropertyAnimation(self._eff, b"opacity", self)
            anim.setDuration(100)
            anim.setStartValue(0.0)
            anim.setEndValue(1.0)
            anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
        if self._full and chunk:
            _P = set('.,;:!?¿¡…\n')
            if not self._full[-1].isspace() and not chunk[0].isspace() and chunk[0] not in _P:
                chunk = " " + chunk
        self._full += chunk
        self._lbl.setText(self._full)

    def set_text(self, text: str):
        self._full = text
        self._lbl.setText(text)

    def clear(self):
        self.append_text("__clear__")


# ═══════════════════════════════════════════════════════════════════════════
# MAIN WINDOW — Ventana principal
# ═══════════════════════════════════════════════════════════════════════════
class NexoMainWindow(QMainWindow):
    command_sent = pyqtSignal(str)

    def __init__(self, engine=None):
        super().__init__()
        self._engine = engine
        self.setWindowTitle("Nexo 2.0")
        self.setMinimumSize(_MIN_W, _MIN_H)
        self.resize(_DEFAULT_W, _DEFAULT_H)

        scr = QApplication.primaryScreen().availableGeometry()
        self.move((scr.width() - _DEFAULT_W) // 2, (scr.height() - _DEFAULT_H) // 2)

        # Central widget
        central = QWidget()
        central.setStyleSheet(f"background:{C.get('BG', '#050c14')};")
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Orb area (crear primero para que los widgets flotantes tengan parent)
        self._orb_area = QWidget()
        self._orb_area.setStyleSheet("background: transparent;")
        root.addWidget(self._orb_area, stretch=1)

        # Floating widgets (crear ANTES que header, porque header los referencia)
        self._clock_w = ClockWidget(self._orb_area)
        self._system_w = SystemWidget(self._orb_area)
        for w in [self._clock_w, self._system_w]:
            w.hide()
            w.closed.connect(self._on_widget_closed)

        # Header (usa self._clock_w y self._system_w para los toggles)
        self._hdr = self._build_header()
        root.addWidget(self._hdr, stretch=0)

        # Input strip
        self._input_strip = self._build_input()
        root.addWidget(self._input_strip, stretch=0)

        # Orb
        self.orb = ParticleOrb(self._orb_area)

        # Transcript
        self._transcript = TranscriptArea(self._orb_area)

        # Timer for layout
        QTimer.singleShot(0, self._safe_relayout)
        QTimer.singleShot(120, self._safe_relayout)

        # Shortcuts
        QShortcut(QKeySequence("F11"), self).activated.connect(self._toggle_fs)
        QShortcut(QKeySequence("Escape"), self).activated.connect(lambda: self._input.setFocus())

        # Engine command signal
        self.command_sent.connect(self._on_command)

    def _build_header(self):
        hdr = QWidget()
        hdr.setFixedHeight(40)
        hdr.setStyleSheet(f"background: #000000; border-bottom: 1px solid {C.get('BORDER', '#0d2540')};")
        lay = QHBoxLayout(hdr)
        lay.setContentsMargins(16, 0, 16, 0)

        title = QLabel("◆  NEXO 2.0")
        title.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {C.get('PRI', '#00d4ff')}; letter-spacing: 3px; background: transparent;")
        lay.addWidget(title)
        lay.addStretch()

        self._status_lbl = QLabel("● LISTO")
        self._status_lbl.setFont(QFont("Segoe UI", 8))
        self._status_lbl.setStyleSheet(f"color: {C.get('TEXT_DIM', '#2e6070')}; background: transparent;")
        lay.addWidget(self._status_lbl)

        sep = QLabel("|")
        sep.setStyleSheet(f"color: {C.get('BORDER', '#0d2540')}; padding: 0 8px; background: transparent;")
        lay.addWidget(sep)

        # Widget toggles
        for name, w in [("⏱", self._clock_w), ("⚡", self._system_w)]:
            btn = QPushButton(name)
            btn.setFixedSize(30, 24)
            btn.setFont(QFont("Arial", 12))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{ background: transparent; color: {C.get('TEXT_DIM', '#2e6070')};
                    border: 1px solid {C.get('BORDER', '#0d2540')}; border-radius: 4px; }}
                QPushButton:hover {{ color: {C.get('PRI', '#00d4ff')};
                    border: 1px solid {C.get('PRI', '#00d4ff')}; }}
            """)
            btn.clicked.connect(lambda checked, w=w: self._toggle_widget(w))
            lay.addWidget(btn)

        return hdr

    def _build_input(self):
        strip = QWidget()
        strip.setFixedHeight(60)
        strip.setStyleSheet(f"background: #000000; border-top: 1px solid {C.get('BORDER', '#0d2540')};")
        lay = QHBoxLayout(strip)
        lay.setContentsMargins(16, 8, 16, 8)

        self._input = QLineEdit()
        self._input.setFont(QFont("Segoe UI", 11))
        self._input.setPlaceholderText("Escribí un comando…")
        self._input.setStyleSheet(f"""
            QLineEdit {{
                background: {C.get('PANEL', '#070f18')}; color: {C.get('TEXT', '#7aeeff')};
                border: 1px solid {C.get('BORDER', '#0d2540')};
                border-radius: 8px; padding: 8px 14px;
                selection-background-color: {C.get('BORDER_A', '#1a5070')};
            }}
            QLineEdit:focus {{ border: 1px solid {C.get('PRI', '#00d4ff')}; }}
        """)
        self._input.returnPressed.connect(self._send_command)
        lay.addWidget(self._input, stretch=1)

        send_btn = QPushButton("▶")
        send_btn.setFixedSize(36, 36)
        send_btn.setFont(QFont("Arial", 14))
        send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        send_btn.setStyleSheet(f"""
            QPushButton {{
                background: {C.get('PRI_DIM', '#005f77')}; color: {C.get('PRI', '#00d4ff')};
                border: none; border-radius: 18px;
            }}
            QPushButton:hover {{ background: {C.get('PRI', '#00d4ff')}; color: #000000; }}
        """)
        send_btn.clicked.connect(self._send_command)
        lay.addWidget(send_btn)

        return strip

    def _send_command(self):
        text = self._input.text().strip()
        if not text:
            return
        self._input.clear()
        self._transcript.set_text(f"👤 {text}")
        self.command_sent.emit(text)

    def _on_command(self, text: str):
        if self._engine:
            self.orb.set_state("THINKING")
            try:
                response = self._engine.process_text(text)
                self._transcript.set_text(f"🤖 {response}")
                self.orb.set_state("LISTENING")
            except Exception as e:
                self._transcript.set_text(f"⚠️ Error: {e}")
                self.orb.set_state("ALERT")
                QTimer.singleShot(3000, lambda: self.orb.set_state("LISTENING"))

    def _toggle_widget(self, widget):
        if widget.isVisible():
            widget.hide_animated()
        else:
            self._position_widget(widget)
            widget.show_animated()

    def _position_widget(self, widget):
        """Posiciona widget en un lugar visible."""
        ow = widget.width()
        oh = widget.height()
        used_positions = {(w.x(), w.y()) for w in [self._clock_w, self._system_w] if w.isVisible() and w != widget}

        # Buscar posición libre
        for row in range(3):
            for col in range(3):
                x = 20 + col * (ow + 20)
                y = 80 + row * (oh + 20)
                if (x, y) not in used_positions:
                    widget.move(x, y)
                    return
        widget.move(20, 80)

    def _toggle_fs(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def _on_widget_closed(self, widget):
        pass  # already hidden by widget's close

    def _safe_relayout(self):
        """Re-posiciona orb y transcript después de resize."""
        if not self._orb_area:
            return
        wa = self._orb_area
        W, H = wa.width(), wa.height()
        if W < 100 or H < 100:
            return

        # Orb ocupa toda el área
        self.orb.setGeometry(0, 0, W, H)

        # Transcript en la parte inferior
        t_h = min(90, H // 6)
        self._transcript.setGeometry(0, H - t_h, W, t_h)
        self._transcript.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        QTimer.singleShot(50, self._safe_relayout)

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(50, self._safe_relayout)

    def set_status(self, text: str):
        self._status_lbl.setText(text)

    def set_engine(self, engine):
        self._engine = engine


# ═══════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════
def launch_ui(engine=None):
    """Lanza la interfaz gráfica de Nexo 2.0."""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Cargar fuente Bonne (para efectos visuales)
    try:
        from PyQt6.QtGui import QFontDatabase
        QFontDatabase.addApplicationFont(str(APP_DIR / "assets" / "Bonne.ttf"))
    except Exception:
        pass

    win = NexoMainWindow(engine=engine)
    win.show()
    win.orb.set_state("LISTENING")
    win.set_status("● ESCUCHANDO")

    try:
        exit_code = app.exec()
    except KeyboardInterrupt:
        exit_code = 0

    return exit_code


if __name__ == "__main__":
    sys.exit(launch_ui())
