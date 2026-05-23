"""
youtube_video.py — YouTube para Nexo 2.0
Busca videos scrapeando resultados de YouTube y los abre en el navegador.
"""
from __future__ import annotations

import re
import subprocess
from urllib.parse import quote_plus

try:
    import requests
    _REQUESTS_OK = True
except ImportError:
    _REQUESTS_OK = False

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-AR,es;q=0.9",
}


def _open_url(url: str) -> bool:
    try:
        subprocess.Popen(["xdg-open", url])
        return True
    except Exception as e:
        print(f"[YouTube] open_url error: {e}")
        return False


def _scrape_first_video(query: str) -> str | None:
    """Busca un video en YouTube y devuelve la URL del primer resultado."""
    if not _REQUESTS_OK:
        return None

    search_url = (
        f"https://www.youtube.com/results"
        f"?search_query={quote_plus(query)}"
        f"&sp=EgIQAQ%3D%3D"  # filter: videos
    )

    try:
        r = requests.get(search_url, headers=HEADERS, timeout=10)
        video_ids = re.findall(r'"videoId":"([A-Za-z0-9_-]{11})"', r.text)

        seen = set()
        for vid in video_ids:
            if vid in seen:
                continue
            seen.add(vid)
            if f'/shorts/{vid}' in r.text:
                continue
            return f"https://www.youtube.com/watch?v={vid}"
    except Exception as e:
        print(f"[YouTube] Scrape error: {e}")

    return None


def search_and_play(query: str) -> str:
    """
    Busca un video en YouTube y lo abre en el navegador.
    
    Args:
        query: Texto a buscar (canción, video, tema, etc.)
    
    Returns:
        str: Mensaje con el resultado
    """
    if not query or not query.strip():
        return "¿Qué video querés ver?"

    if not _REQUESTS_OK:
        return "❌ Necesito 'requests'. Ejecutá: pip install requests"

    query = query.strip()
    print(f"[YouTube] 🔍 Buscando: {query}")

    url = _scrape_first_video(query)

    if url:
        _open_url(url)
        return f"▶ Abriendo: {query}"

    # Fallback: abrir búsqueda
    fallback = (
        f"https://www.youtube.com/results"
        f"?search_query={quote_plus(query)}"
    )
    _open_url(fallback)
    return f"🔍 Abrí búsqueda de YouTube para: {query}"


def get_video_info(url: str) -> str:
    """
    Obtiene información básica de un video de YouTube.
    
    Args:
        url: URL del video
    
    Returns:
        str: Info del video o mensaje de error
    """
    if not _REQUESTS_OK:
        return "❌ Necesito 'requests'."

    vid_match = re.search(r"(?:v=|\/v\/|youtu\.be\/|\/embed\/)([A-Za-z0-9_-]{11})", url)
    if not vid_match:
        return "URL de YouTube no válida."

    video_id = vid_match.group(1)
    try:
        r = requests.get(
            f"https://www.youtube.com/watch?v={video_id}",
            headers=HEADERS,
            timeout=12,
        )
        html = r.text
        info = {}

        patterns = [
            ("title",    r'"title":\{"runs":\[\{"text":"([^"]+)"'),
            ("channel",  r'"ownerChannelName":"([^"]+)"'),
            ("views",    r'"viewCount":"(\d+)"'),
        ]
        for key, pattern in patterns:
            match = re.search(pattern, html)
            if match:
                info[key] = match.group(1)

        if not info:
            return "No pude obtener información del video."

        parts = [f"{k.capitalize()}: {v}" for k, v in info.items()]
        return "\n".join(parts)
    except Exception as e:
        return f"Error obteniendo info del video: {e}"
