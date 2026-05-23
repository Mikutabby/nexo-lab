"""
weather_report.py — Clima para Nexo 2.0
Obtiene datos via Open-Meteo (sin API key).
Geocodifica con Nominatim (sin API key).
"""
from __future__ import annotations

import datetime

try:
    import requests as _requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False

_WMO_MAP: dict[int, tuple[str, str]] = {
    0:  ("Despejado",          "☀"),
    1:  ("Mayormente despejado","🌤"),
    2:  ("Parcialmente nublado","⛅"),
    3:  ("Nublado",            "☁"),
    45: ("Niebla",             "🌫"),
    48: ("Escarcha",           "🌫"),
    51: ("Llovizna leve",      "🌦"),
    53: ("Llovizna moderada",  "🌦"),
    55: ("Llovizna intensa",   "🌧"),
    61: ("Lluvia leve",        "🌧"),
    63: ("Lluvia moderada",    "🌧"),
    65: ("Lluvia fuerte",      "🌧"),
    71: ("Nevada leve",        "❄"),
    73: ("Nevada moderada",    "❄"),
    75: ("Nevada intensa",     "❄"),
    77: ("Granizo",            "🌨"),
    80: ("Chaparrón leve",     "🌦"),
    81: ("Chaparrón moderado", "🌧"),
    82: ("Chaparrón violento", "⛈"),
    85: ("Nevada leve",        "🌨"),
    86: ("Nevada fuerte",      "🌨"),
    95: ("Tormenta",           "⛈"),
    96: ("Tormenta con granizo","⛈"),
    99: ("Tormenta fuerte",    "⛈"),
}

_HEADERS = {"User-Agent": "Nexo/2.0 (weather)"}


def _geocode(city: str) -> tuple[float, float, str] | None:
    try:
        url = "https://nominatim.openstreetmap.org/search"
        r = _requests.get(
            url,
            params={"q": city, "format": "json", "limit": 1, "accept-language": "es"},
            headers=_HEADERS,
            timeout=8,
        )
        data = r.json()
        if not data:
            return None
        item = data[0]
        return float(item["lat"]), float(item["lon"]), item["display_name"]
    except Exception as e:
        print(f"[Weather] Geocode error: {e}")
        return None


def _fetch_weather(lat: float, lon: float) -> dict | None:
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        r = _requests.get(
            url,
            params={
                "latitude":    lat,
                "longitude":   lon,
                "current":     "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m",
                "daily":       "temperature_2m_max,temperature_2m_min,weather_code",
                "timezone":    "auto",
                "forecast_days": 4,
            },
            headers=_HEADERS,
            timeout=10,
        )
        return r.json()
    except Exception as e:
        print(f"[Weather] Open-Meteo error: {e}")
        return None


def weather_report(city: str) -> str:
    """
    Obtiene el clima actual para una ciudad.
    
    Args:
        city: Nombre de la ciudad
    
    Returns:
        str: Reporte del clima
    """
    if not city or not city.strip():
        return "Decime la ciudad para consultar el clima."

    city = city.strip()

    if not _HAS_REQUESTS:
        return "❌ Necesito 'requests'. Ejecutá: pip install requests"

    print(f"[Weather] Consultando clima para: {city}")

    geo = _geocode(city)
    if not geo:
        return f"No pude encontrar la ubicación de '{city}'."

    lat, lon, display_name = geo
    short_name = display_name.split(",")[0].strip()
    print(f"[Weather] Ubicación: {short_name} ({lat:.3f}, {lon:.3f})")

    data = _fetch_weather(lat, lon)
    if not data or "current" not in data:
        return f"No pude obtener datos del clima para {city}."

    cur   = data["current"]
    temp  = cur.get("temperature_2m", "?")
    feels = cur.get("apparent_temperature", "?")
    humid = cur.get("relative_humidity_2m", "?")
    wind  = cur.get("wind_speed_10m", "?")
    code  = int(cur.get("weather_code", 0))
    desc, icon = _WMO_MAP.get(code, ("Desconocido", "🌡"))

    def _fmt(v, unit): return f"{v:.0f}{unit}" if isinstance(v, (int, float)) else f"{v}{unit}"
    temp_str  = _fmt(temp,  "°C")
    feels_str = _fmt(feels, "°C")
    wind_str  = _fmt(wind,  " km/h")

    # Pronóstico próximos días
    forecast_parts = []
    daily = data.get("daily", {})
    times = daily.get("time", [])
    t_max = daily.get("temperature_2m_max", [])
    t_min = daily.get("temperature_2m_min", [])
    d_cod = daily.get("weather_code", [])
    day_names = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
    for i in range(min(4, len(times))):
        try:
            dt = datetime.date.fromisoformat(times[i])
            dn = day_names[dt.weekday()]
            dc = int(d_cod[i]) if i < len(d_cod) else 0
            di = _WMO_MAP.get(dc, ("?", "🌤"))[1]
            mx = _fmt(t_max[i], "°") if i < len(t_max) and isinstance(t_max[i], (int, float)) else "?"
            mn = _fmt(t_min[i], "°") if i < len(t_min) and isinstance(t_min[i], (int, float)) else "?"
            forecast_parts.append(f"{dn}:{di}{mx}/{mn}")
        except Exception:
            pass
    forecast_str = " | ".join(forecast_parts) if forecast_parts else ""

    msg = (
        f"Clima en {short_name}: {desc} {icon}, {temp_str} "
        f"(sensación {feels_str}). Humedad {humid}%, viento {wind_str}."
    )
    if forecast_str:
        msg += f"\nPronóstico: {forecast_str}"

    return msg
