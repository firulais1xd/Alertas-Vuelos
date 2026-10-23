"""Genera la página web estática (carpeta sitio/) que publica GitHub Pages."""
import json
from collections import defaultdict
from pathlib import Path

PLANTILLA = Path(__file__).with_name("plantilla.html")


def generar(historial, hoy, cfg, destino: Path):
    hoy_filas = [r for r in historial if r["fecha"] == hoy]
    # Por destino: lo más barato hoy (ida e ida y vuelta) y el mejor precio por mes
    destinos = {}
    for r in hoy_filas:
        d = destinos.setdefault(r["destino"], {"codigo": r["destino"], "ciudad": r["ciudad"], "pais": r["pais"],
                                               "nacional": r["pais_codigo"] == "CO", "ida": None, "ida_y_vuelta": None,
                                               "meses": {}})
        actual = d[r["tipo"]]
        if actual is None or r["precio"] < actual["precio"]:
            d[r["tipo"]] = _corto(r)
        d["meses"].setdefault(r["mes"], {})[r["tipo"]] = round(r["precio"])

    # Historial: mínimo diario por destino y tipo
    hist = defaultdict(lambda: defaultdict(dict))
    for r in historial:
        dia = hist[r["destino"]][r["tipo"]]
        dia[r["fecha"]] = min(dia.get(r["fecha"], float("inf")), round(r["precio"]))

    datos = {
        "hoy": hoy,
        "origen": cfg["origen"],
        "destinos": sorted(destinos.values(), key=lambda d: (d["ida_y_vuelta"] or d["ida"] or {"precio": 9e12})["precio"]),
        "historia": {k: {t: sorted(v.items()) for t, v in tipos.items()} for k, tipos in hist.items()},
        "dias": len({r["fecha"] for r in historial}),
    }
    js = json.dumps(datos, ensure_ascii=False).replace("</", "<\\/")
    destino.mkdir(exist_ok=True)
    (destino / "index.html").write_text(PLANTILLA.read_text(encoding="utf-8").replace("__DATOS__", js), encoding="utf-8")


def _corto(r):
    return {k: r[k] for k in ("precio", "aerolinea", "salida", "regreso", "escalas", "link")} | {"precio": round(r["precio"])}
