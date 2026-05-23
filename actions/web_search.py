"""
web_search.py — Búsqueda web para Nexo 2.0
Usa DuckDuckGo (sin API key). Fallback a Gemini si hay API key.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_MAX_RESULT_CHARS = 2000


def _base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


def _ddg_search(query: str, max_results: int = 3) -> list[dict]:
    try:
        from ddgs import DDGS
    except ImportError:
        from duckduckgo_search import DDGS

    results = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "title":   (r.get("title",  "") or "")[:120],
                    "snippet": (r.get("body",   "") or "")[:300],
                    "url":     (r.get("href",   "") or "")[:120],
                })
    except Exception as e:
        print(f"[WebSearch] DDG error: {e}")
    return results


def _format_results(query: str, results: list[dict]) -> str:
    if not results:
        return f"No encontré resultados para: {query}"

    lines = [f"Resultados para: {query}\n"]
    for i, r in enumerate(results, 1):
        if r.get("title"):   lines.append(f"{i}. {r['title']}")
        if r.get("snippet"): lines.append(f"   {r['snippet']}")
        if r.get("url"):     lines.append(f"   {r['url']}")
        lines.append("")
    text = "\n".join(lines).strip()
    if len(text) > _MAX_RESULT_CHARS:
        text = text[:_MAX_RESULT_CHARS] + "\n… [truncado]"
    return text


def web_search(query: str, max_results: int = 3) -> str:
    """
    Busca en la web usando DuckDuckGo.
    
    Args:
        query: Texto a buscar
        max_results: Máximo de resultados (default 3)
    
    Returns:
        str: Resultados formateados
    """
    if not query or not query.strip():
        return "¿Qué querés buscar?"

    query = query.strip()
    print(f"[WebSearch] 🔍 Buscando: {query}")

    results = _ddg_search(query, max_results=max_results)
    return _format_results(query, results)
