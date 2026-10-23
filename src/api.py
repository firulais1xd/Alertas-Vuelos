"""Consulta de precios en la API de Travelpayouts (Aviasales).

Los precios vienen de búsquedas recientes de otros usuarios (últimas 48 h), no son una cotización en vivo:
sirven para detectar tendencias y ofertas, y el precio final se confirma al abrir el enlace.
"""
import os
import time
from datetime import date

import requests

BASE = "https://api.travelpayouts.com"
WEB = "https://www.aviasales.com"

AEROLINEAS = {
    "AV": "Avianca", "LA": "LATAM", "4C": "LATAM", "CM": "Copa", "JA": "JetSMART", "P5": "Wingo", "9R": "Satena",
    "VE": "Clic", "AA": "American", "UA": "United", "DL": "Delta", "NK": "Spirit", "B6": "JetBlue",
    "IB": "Iberia", "UX": "Air Europa", "AF": "Air France", "KL": "KLM", "LH": "Lufthansa", "TK": "Turkish",
    "AM": "Aeroméxico", "VB": "Viva Aerobus", "Y4": "Volaris", "H2": "Sky", "G3": "Gol", "AR": "Aerolíneas Argentinas",
    "TP": "TAP", "BA": "British Airways", "AC": "Air Canada", "F9": "Frontier", "WN": "Southwest", "AS": "Alaska",
    "V0": "Conviasa", "ES": "Estelar", "DM": "Arajet", "QL": "Laser", "EK": "Emirates", "CX": "Cathay",
}


def _get(ruta: str, **params):
    token = os.getenv("TRAVELPAYOUTS_TOKEN", "").strip()
    if not token:
        raise SystemExit("Falta el secreto TRAVELPAYOUTS_TOKEN (Settings › Secrets and variables › Actions).")
    for intento in range(3):
        try:
            r = requests.get(BASE + ruta, params=params, timeout=40,
                             headers={"X-Access-Token": token, "Accept-Encoding": "gzip, deflate"})
            if r.status_code == 401:
                raise SystemExit("El token de Travelpayouts no es válido (HTTP 401). Revisa el secreto TRAVELPAYOUTS_TOKEN.")
            if r.ok:
                return r.json()
            print(f"   HTTP {r.status_code}: {r.text[:200]}")
        except requests.RequestException as e:
            print(f"   error de red: {e}")
        time.sleep(3 * (intento + 1))
    return None


def meses(desde: date, cantidad: int) -> list[str]:
    y, m = desde.year, desde.month
    out = []
    for _ in range(cantidad):
        out.append(f"{y}-{m:02d}")
        m += 1
        if m > 12:
            y, m = y + 1, 1
    return out


def buscar_desde(origen: str, mes: str, ida_y_vuelta: bool, moneda: str) -> list[dict]:
    """Vuelos más baratos desde `origen` a cualquier destino, saliendo en `mes` (AAAA-MM)."""
    datos = _get("/aviasales/v3/prices_for_dates", origin=origen, departure_at=mes,
                 one_way=str(not ida_y_vuelta).lower(), sorting="price", direct="false",
                 currency=moneda, limit=1000, market="co")
    return [normalizar(v, ida_y_vuelta, moneda) for v in (datos or {}).get("data", [])]


def normalizar(v: dict, ida_y_vuelta: bool, moneda: str) -> dict:
    link = v.get("link") or ""
    return {
        "destino": v.get("destination", ""),
        "tipo": "ida_y_vuelta" if ida_y_vuelta else "ida",
        "precio": float(v.get("price") or 0),
        "aerolinea": AEROLINEAS.get(v.get("airline", ""), v.get("airline", "")),
        "salida": (v.get("departure_at") or "")[:10],
        "regreso": (v.get("return_at") or "")[:10],
        "escalas": int(v.get("transfers") or 0) + int(v.get("return_transfers") or 0),
        "duracion_min": int(v.get("duration") or v.get("duration_to") or 0),
        "link": (WEB + link + ("&" if "?" in link else "?") + f"currency={moneda}") if link else "",
    }


def ciudades() -> dict[str, dict]:
    """Código IATA de ciudad -> {nombre, pais_codigo}. Datos públicos, no requieren token."""
    try:
        cs = requests.get(BASE + "/data/es/cities.json", timeout=60).json()
        ps = {p["code"]: p.get("name") or p["code"] for p in requests.get(BASE + "/data/es/countries.json", timeout=60).json()}
    except Exception as e:
        print(f"⚠️  No se pudieron cargar nombres de ciudades: {e}")
        return {}
    return {c["code"]: {"nombre": c.get("name") or c["code"], "pais_codigo": c.get("country_code", ""),
                        "pais": ps.get(c.get("country_code", ""), c.get("country_code", ""))} for c in cs}
