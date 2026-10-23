from src import api, main as m


def fila(destino, tipo, precio, fecha="2026-10-23", mes="2026-11", pais="CO"):
    return {"fecha": fecha, "destino": destino, "ciudad": destino, "pais": pais, "pais_codigo": pais, "mes": mes,
            "tipo": tipo, "precio": precio, "aerolinea": "AV", "salida": mes + "-10", "regreso": "", "escalas": 0,
            "duracion_min": 60, "link": ""}


def test_meses_cambia_de_anio():
    from datetime import date
    assert api.meses(date(2026, 11, 5), 3) == ["2026-11", "2026-12", "2027-01"]


def test_normalizar_link_y_moneda():
    v = api.normalizar({"destination": "MIA", "price": 900000, "airline": "AV", "departure_at": "2026-12-01T10:00:00-05:00",
                        "transfers": 1, "link": "/search/BAQ0112MIA1?t=abc"}, False, "cop")
    assert v["destino"] == "MIA" and v["salida"] == "2026-12-01" and v["escalas"] == 1
    assert v["link"] == "https://www.aviasales.com/search/BAQ0112MIA1?t=abc&currency=cop"


def test_baja_requiere_historial_y_umbral():
    hist = [fila("MDE", "ida", p, fecha=f"2026-10-{d:02d}") for d, p in [(18, 200000), (19, 210000), (20, 205000), (21, 200000)]]
    hoy = [fila("MDE", "ida", 160000), fila("MDE", "ida", 170000, mes="2026-12")]
    alertas = m.bajas(hist, hoy, "2026-10-23", 0.15)
    assert len(alertas) == 1 and alertas[0][1]["precio"] == 160000
    assert m.bajas(hist, [fila("MDE", "ida", 190000)], "2026-10-23", 0.15) == []


def test_favoritos():
    cfg = {"favoritos": [{"destino": "ADZ", "tipo": "ida_y_vuelta", "precio_max": 600000}]}
    assert len(m.favoritos_baratos(cfg, [fila("ADZ", "ida_y_vuelta", 550000)])) == 1
    assert m.favoritos_baratos(cfg, [fila("ADZ", "ida_y_vuelta", 650000)]) == []


def test_favorito_no_repite_aviso():
    cfg = {"favoritos": [{"destino": "MDE", "tipo": "ida_y_vuelta", "precio_max": 300000}]}
    ayer = [fila("MDE", "ida_y_vuelta", 240000, fecha="2026-10-22")]
    assert m.favoritos_baratos(cfg, [fila("MDE", "ida_y_vuelta", 239000)], ayer) == []        # igual: no repite
    assert len(m.favoritos_baratos(cfg, [fila("MDE", "ida_y_vuelta", 220000)], ayer)) == 1    # bajó más: avisa
    caro = [fila("MDE", "ida_y_vuelta", 350000, fecha="2026-10-22")]
    assert len(m.favoritos_baratos(cfg, [fila("MDE", "ida_y_vuelta", 290000)], caro)) == 1    # recién entra al tope


def test_recolectar_combina_y_filtra_meses(monkeypatch):
    cfg = {"origen": "BAQ", "moneda": "cop", "meses_adelante": 2}
    def v(dest, fecha, precio, iv):
        return api.normalizar({"destination": dest, "price": precio, "departure_at": fecha}, iv, "cop")
    monkeypatch.setattr(api, "buscar_desde", lambda o, mes, iv, mon: [v("MDE", mes + "-15", 300000, iv)])
    monkeypatch.setattr(api, "buscar_a", lambda o, d, iv, mon: [v(d, "2026-11-20", 250000, iv), v(d, "2027-06-01", 100, iv)])
    monkeypatch.setattr(m, "lista_destinos", lambda cfg: ["MDE", "MAD"])
    filas = m.recolectar(cfg, "2026-10-23", {})
    claves = {(f["destino"], f["mes"], f["tipo"]): f["precio"] for f in filas}
    assert claves[("MDE", "2026-11", "ida")] == 250000          # se queda con el más barato
    assert ("MAD", "2026-11", "ida_y_vuelta") in claves
    assert not any(f["mes"] == "2027-06" for f in filas)        # fuera de los meses buscados
