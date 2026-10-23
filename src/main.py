"""Busca los vuelos más baratos desde Barranquilla, guarda el historial, avisa por Telegram y genera la página.

Uso:  python -m src.main            (normal)
      RESUMEN=1 python -m src.main  (fuerza el resumen semanal)
"""
import csv
import json
import os
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

from . import api, sitio, telegram

RAIZ = Path(__file__).resolve().parent.parent
CSV = RAIZ / "data" / "vuelos.csv"
CIUDADES = RAIZ / "data" / "ciudades.json"
COLUMNAS = ["fecha", "destino", "ciudad", "pais", "pais_codigo", "mes", "tipo", "precio", "aerolinea",
            "salida", "regreso", "escalas", "duracion_min", "link"]
BOGOTA = timezone(timedelta(hours=-5))
DIAS_HABITUAL = 30
TIPO = {"ida": "solo ida", "ida_y_vuelta": "ida y vuelta"}


def pesos(x: float) -> str:
    return "$" + f"{x:,.0f}".replace(",", ".")


def cargar_ciudades():
    """Nombres de ciudades: se descargan una vez y se guardan en data/ciudades.json."""
    if CIUDADES.exists() and CIUDADES.stat().st_size > 1000:
        return json.loads(CIUDADES.read_text(encoding="utf-8"))
    c = api.ciudades()
    if c:
        CIUDADES.parent.mkdir(exist_ok=True)
        CIUDADES.write_text(json.dumps(c, ensure_ascii=False), encoding="utf-8")
    return c


def recolectar(cfg, hoy: str, ciudades: dict):
    """El vuelo más barato por (destino, mes, tipo)."""
    mejores = {}
    for mes in api.meses(datetime.fromisoformat(hoy).date(), cfg["meses_adelante"]):
        for ida_y_vuelta in (False, True):
            vuelos = api.buscar_desde(cfg["origen"], mes, ida_y_vuelta, cfg["moneda"])
            print(f"{mes} {'ida y vuelta' if ida_y_vuelta else 'solo ida'}: {len(vuelos)} vuelos")
            for v in vuelos:
                if not v["destino"] or v["precio"] <= 0 or v["destino"] == cfg["origen"] or v["salida"] < hoy:
                    continue
                clave = (v["destino"], mes, v["tipo"])
                if clave not in mejores or v["precio"] < mejores[clave]["precio"]:
                    c = ciudades.get(v["destino"], {})
                    mejores[clave] = {"fecha": hoy, "mes": mes, "ciudad": c.get("nombre", v["destino"]),
                                      "pais": c.get("pais", ""), "pais_codigo": c.get("pais_codigo", ""), **v}
    return list(mejores.values())


def leer_historial():
    if not CSV.exists():
        return []
    with open(CSV, encoding="utf-8", newline="") as f:
        filas = list(csv.DictReader(f))
    for r in filas:
        r["precio"] = float(r["precio"])
        r["escalas"] = int(r["escalas"] or 0)
        r["duracion_min"] = int(r["duracion_min"] or 0)
    return filas


def guardar(historial):
    CSV.parent.mkdir(exist_ok=True)
    with open(CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNAS)
        w.writeheader()
        for r in sorted(historial, key=lambda r: (r["fecha"], r["destino"], r["tipo"], r["mes"])):
            w.writerow({k: r[k] for k in COLUMNAS})


def minimo_por_ruta(filas):
    """(destino, tipo) -> fila más barata entre todos los meses."""
    out = {}
    for r in filas:
        k = (r["destino"], r["tipo"])
        if k not in out or r["precio"] < out[k]["precio"]:
            out[k] = r
    return out


def bajas(historial, hoy_filas, hoy, baja_minima):
    desde = (datetime.fromisoformat(hoy) - timedelta(days=DIAS_HABITUAL)).date().isoformat()
    por_dia = defaultdict(lambda: defaultdict(lambda: float("inf")))
    for r in historial:
        if desde <= r["fecha"] < hoy:
            k = (r["destino"], r["tipo"])
            por_dia[k][r["fecha"]] = min(por_dia[k][r["fecha"]], r["precio"])
    alertas = []
    for k, r in minimo_por_ruta(hoy_filas).items():
        dias = list(por_dia.get(k, {}).values())
        if len(dias) < 3:
            continue
        habitual = statistics.median(dias)
        cambio = r["precio"] / habitual - 1
        if cambio <= -baja_minima:
            alertas.append((cambio, r, habitual))
    return sorted(alertas, key=lambda a: a[0])


def favoritos_baratos(cfg, hoy_filas):
    mins = minimo_por_ruta(hoy_filas)
    out = []
    for f in cfg.get("favoritos") or []:
        r = mins.get((f["destino"], f["tipo"]))
        if r and r["precio"] <= f["precio_max"]:
            out.append((r, f["precio_max"]))
    return out


MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


def fecha_corta(iso: str) -> str:
    if not iso:
        return ""
    a, m, d = iso.split("-")
    return f"{int(d)} {MESES[int(m) - 1]}" + ("" if a == str(datetime.now(BOGOTA).year) else f" {a}")


def linea(r):
    fechas = fecha_corta(r["salida"]) + (f" → {fecha_corta(r['regreso'])}" if r["regreso"] else "")
    lugar = r["ciudad"] if not r["pais"] or r["pais"] == r["ciudad"] else f"{r['ciudad']} ({r['pais']})"
    escalas = "directo" if r["escalas"] == 0 else f"{r['escalas']} escala{'s' if r['escalas'] > 1 else ''}"
    enlace = f" <a href=\"{r['link']}\">ver</a>" if r["link"] else ""
    return f"{lugar} — <b>{pesos(r['precio'])}</b> {TIPO[r['tipo']]}, {fechas}, {r['aerolinea']}, {escalas}{enlace}"


def mensaje_alertas(alertas, favs, origen):
    partes = []
    if favs:
        partes.append(f"🎯 <b>Tus destinos favoritos en precio objetivo</b> (desde {origen})")
        partes += [f"• {linea(r)} (tu tope: {pesos(tope)})" for r, tope in favs]
    if alertas:
        partes.append(f"\n✈️ <b>Bajaron de precio</b> (desde {origen})")
        partes += [f"• {linea(r)} <b>{c:+.0%}</b> vs. {pesos(h)}" for c, r, h in alertas[:15]]
    return "\n".join(partes).strip()


def mensaje_resumen(hoy_filas, cfg, url):
    mins = list(minimo_por_ruta(hoy_filas).values())
    n = cfg.get("top_resumen", 10)
    nac = sorted([r for r in mins if r["pais_codigo"] == "CO" and r["tipo"] == "ida_y_vuelta"], key=lambda r: r["precio"])[:5]
    intl = sorted([r for r in mins if r["pais_codigo"] != "CO" and r["tipo"] == "ida_y_vuelta"], key=lambda r: r["precio"])[:n]
    lineas = [f"🇨🇴 <b>Nacionales más baratos desde {cfg['origen']}</b> (ida y vuelta)"]
    lineas += [f"{i}. {linea(r)}" for i, r in enumerate(nac, 1)] or ["(sin datos)"]
    lineas.append(f"\n🌎 <b>Internacionales más baratos</b> (ida y vuelta)")
    lineas += [f"{i}. {linea(r)}" for i, r in enumerate(intl, 1)] or ["(sin datos)"]
    lineas.append("\nℹ️ Precios de búsquedas recientes en Aviasales; confírmalos en el enlace.")
    if url:
        lineas.append(f"📊 <a href=\"{url}\">Ver todos los destinos y el historial</a>")
    return "\n".join(lineas)


def url_pagina():
    repo = os.getenv("GITHUB_REPOSITORY", "")
    if "/" not in repo:
        return ""
    dueno, nombre = repo.split("/", 1)
    return f"https://{dueno.lower()}.github.io/{nombre}/"


def main():
    with open(RAIZ / "config" / "config.yml", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    ahora = datetime.now(BOGOTA)
    hoy = ahora.date().isoformat()

    ciudades = cargar_ciudades()
    hoy_filas = recolectar(cfg, hoy, ciudades)
    historial = [r for r in leer_historial() if r["fecha"] != hoy]
    alertas = bajas(historial, hoy_filas, hoy, cfg["baja_minima"])
    favs = favoritos_baratos(cfg, hoy_filas)
    historial += hoy_filas
    guardar(historial)
    sitio.generar(historial, hoy, cfg, RAIZ / "sitio")

    destinos = len({r["destino"] for r in hoy_filas})
    print(f"Listo: {len(hoy_filas)} precios, {destinos} destinos, {len(alertas)} bajas, {len(favs)} favoritos en precio.")
    if not hoy_filas:
        telegram.enviar("⚠️ <b>Alertas de vuelos</b>: hoy la API no devolvió vuelos. Revisa el registro de GitHub Actions.")
        sys.exit(1)

    if alertas or favs:
        telegram.enviar(mensaje_alertas(alertas, favs, cfg["origen"]))
    resumen = os.getenv("RESUMEN", "").lower() in ("1", "true", "si", "sí")
    if resumen or ahora.weekday() == 0:
        telegram.enviar(mensaje_resumen(hoy_filas, cfg, url_pagina()))


if __name__ == "__main__":
    main()
