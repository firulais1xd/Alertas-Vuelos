# Historial de cambios

La entrada más reciente va arriba. Cada entrada tiene:

- **Motivo:** por qué se hizo el cambio.
- **Cambios:** qué se modificó y en qué archivos.
- **Cómo verificar:** qué debería notarse.

Los commits automáticos "Vuelos del AAAA-MM-DD" solo actualizan `data/` y no se documentan aquí.

---

## v0.2.1 — 2026-10-23

**Motivo:** el bot de Telegram no enviaba mensajes, y desde fuera no se podía saber por qué (los registros de Actions no estaban accesibles).

**Cambios:**
- `src/telegram.py`: registra el resultado de cada envío: si hay token, si se detectó el chat, cuántos mensajes tenía el bot en su bandeja, cuántos se enviaron y los errores que devolvió Telegram. No guarda el token ni el número de chat.
- `src/main.py`: ese registro queda en la sección `"telegram"` de `data/diagnostico.json`.

**Cómo verificar:** después de una ejecución, `data/diagnostico.json` muestra el estado de Telegram.

---

## v0.2.0 — 2026-10-23

**Motivo:** la primera ejecución real funcionó (Medellín a $239.260 y Bogotá a $242.143 ida y vuelta), pero solo trajo 14 destinos, porque cada consulta a la API devuelve pocos resultados. Además, el aviso de favoritos se habría repetido todos los días.

**Cambios:**
- `src/api.py`: cada mes y tipo de vuelo se consulta de 4 formas (mercado Colombia o global, ordenado por precio o por ruta) y los resultados se combinan, quedándose con el más barato por destino.
- `src/main.py`: se escribe `data/diagnostico.json` con cuántos resultados dio cada forma de consulta, para medir la cobertura y quitar las que no aporten.
- `src/main.py`: el aviso de un favorito solo se envía la primera vez que baja de tu tope, o si después baja otro 2 % o más.
- `tests/test_vuelos.py`: prueba de que el aviso de favoritos no se repite.

**Cómo verificar:** `data/diagnostico.json` debería mostrar más de 14 destinos, y el bot no debería repetir el aviso de Medellín si el precio sigue igual.

---

## v0.1.0 — 2026-10-23

**Motivo:** primera versión. Vigilar los precios de vuelos desde Barranquilla a cualquier destino, recibir alertas por Telegram y ver una página con historial.

**Cambios:**
- `src/api.py`: consulta `prices_for_dates` de Travelpayouts desde BAQ sin destino fijo, por mes, en solo ida y en ida y vuelta, en COP. Los códigos de aerolínea se muestran con su nombre, y los de ciudad con su nombre en español (datos públicos de Travelpayouts).
  - La API Self-Service de Amadeus se descartó porque cerró en julio de 2026.
- `src/main.py`:
  - Guarda el vuelo más barato por destino, mes y tipo, y descarta fechas ya pasadas.
  - Avisa de bajas de 15 % o más frente a la mediana de 30 días, y de favoritos por debajo de su precio objetivo.
  - Los lunes envía el top de destinos nacionales e internacionales.
- `config/config.yml`: origen, meses hacia adelante, umbral y favoritos iniciales (Medellín, San Andrés, Miami, Madrid, Cancún).
- `src/sitio.py` y `src/plantilla.html`: página con la lista de destinos (filtros, búsqueda, enlace al vuelo) y gráficas por mes de salida e historial. Funciona en celular y en modo oscuro.
- `src/telegram.py`: el mismo módulo del comparador de mercado, con detección automática del chat ID.
- `.github/workflows/diario.yml`: se ejecuta todos los días a las 7:43 a. m. (hora de Colombia), guarda el historial y publica en GitHub Pages.
- `tests/test_vuelos.py`: pruebas de meses, enlaces, bajas de precio y favoritos.

**Cómo verificar:** después de guardar el secreto `TRAVELPAYOUTS_TOKEN`, ejecuta *Actions › Vuelos diarios › Run workflow*. El registro muestra cuántos vuelos hay por mes, y la página lista los destinos.
