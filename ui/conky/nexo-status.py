#!/usr/bin/env python3
"""Devuelve el estado de Nexo con color para Conky."""
import json, os, sys

try:
    with open("/tmp/nexo-ui-state.json") as f:
        s = json.load(f)
    status = s.get("nexo_status", "idle")
    nexos = {
        "idle": "${color4}◦ Inactivo${color}",
        "listening": "${color3}◦ Escuchando...${color}",
        "thinking": "${color5}◦ Pensando...${color}",
        "speaking": "${color1}◦ Hablando${color}",
        "error": "${color2}◦ Error${color}",
    }
    print(nexos.get(status, "${color4}◦ ${color}" + status))
except Exception:
    print("${color4}◦ Desconectado${color}")
