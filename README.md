# ✈️ Alertas de Vuelos — desde Barranquilla

Busca cada día los vuelos más baratos **desde Barranquilla (BAQ) a cualquier destino** para los próximos 6 meses. Te avisa por **Telegram** cuando una ruta baja de precio y publica una **página** con todos los destinos, el precio por mes y el historial.

Todo corre gratis en GitHub Actions.

## Qué hace

- **Todos los días a las 7:43 a. m.** consulta la API de Travelpayouts (Aviasales): vuelos de solo ida y de ida y vuelta, para cada uno de los próximos 6 meses.
- Guarda el vuelo más barato por destino, mes y tipo en [`data/vuelos.csv`](data/vuelos.csv).
- **Telegram:**
  - 🎯 Aviso cuando uno de tus **destinos favoritos** está por debajo del precio que pusiste en [`config/config.yml`](config/config.yml).
  - ✈️ Aviso cuando una ruta **baja 15 % o más** frente a su precio habitual (mediana de 30 días; se necesitan al menos 3 días de historial).
  - Los **lunes** (o cuando lo ejecutas a mano): los 5 destinos nacionales y los 10 internacionales más baratos.
- **Página web:** `https://firulais1xd.github.io/Alertas-Vuelos/`. Permite filtrar entre nacionales e internacionales y entre ida o ida y vuelta, buscar por ciudad y ver gráficas por mes y el historial.

## Configuración (una sola vez, desde el teléfono)

1. **Token de Travelpayouts:** crea una cuenta gratis en travelpayouts.com y copia tu token desde la sección *API*.
2. **Secretos:** en el repo, ve a *Settings › Secrets and variables › Actions › New repository secret*.
   - `TRAVELPAYOUTS_TOKEN`: el token del paso 1.
   - `TELEGRAM_TOKEN`: el token de tu bot (el mismo del comparador de mercado).
   - `TELEGRAM_CHAT_ID`: tu número de chat (el bot te lo envía en la primera ejecución).
3. **Página web:** en *Settings › Pages › Source*, elige **GitHub Actions**.
4. **Primera ejecución:** en *Actions › Vuelos diarios › Run workflow*.

## Personalizar

En `config/config.yml` puedes cambiar:
- `favoritos`: destinos y el precio máximo que pagarías.
- `meses_adelante`: cuántos meses hacia adelante buscar.
- `baja_minima`: qué tanto debe bajar un precio para avisarte (0.15 = 15 %).

## Limitaciones importantes

- Los precios vienen de **búsquedas recientes de otros usuarios** en Aviasales (últimas 48 horas), no de una cotización en vivo. Sirven para detectar tendencias y ofertas, pero **el precio final se confirma al abrir el enlace**.
- Las rutas poco buscadas pueden no aparecer algunos días.
- No incluye equipaje ni tasas adicionales que cobre la aerolínea.

## Estructura

```
config/config.yml     Origen, meses, favoritos y umbrales
src/api.py            Consulta a Travelpayouts y nombres de ciudades
src/main.py           Recolecta, guarda, detecta bajas y avisa
src/sitio.py          Genera la página web
src/telegram.py       Envía los mensajes
data/vuelos.csv       Historial (se actualiza solo)
```

Historial de cambios: [CHANGELOG.md](CHANGELOG.md)
