# Reglas del repositorio

- **Cada cambio que se suba a GitHub debe documentarse en `CHANGELOG.md`**, en una entrada nueva arriba del todo con el formato `## vX.Y.Z — AAAA-MM-DD` y las secciones Motivo, Cambios (indicando los archivos) y Cómo verificar. La documentación va **en el mismo commit** que el cambio.
  - Versión: Z para correcciones, Y para funciones nuevas, X para cambios grandes.
  - Los commits automáticos "Vuelos del …" (solo `data/`) no se documentan.
- Antes de subir: `python -m pytest -q tests` debe pasar.
- Nunca escribir tokens en el código ni en la conversación: van como secretos de GitHub (`TRAVELPAYOUTS_TOKEN`, `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID`).
- Los mensajes de commit van en español y describen el cambio.
- Idioma del código, la página y la documentación: español. Origen: Barranquilla (BAQ).
