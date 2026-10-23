"""Envío de mensajes a Telegram.

Secretos del repositorio (Settings › Secrets and variables › Actions):
  TELEGRAM_TOKEN    token que entrega @BotFather
  TELEGRAM_CHAT_ID  tu chat. Si falta, se detecta solo con el último mensaje que le escribiste al bot,
                    y el bot te responde con el número para que lo guardes.
"""
import os

import requests

API = "https://api.telegram.org/bot{token}/{metodo}"
LIMITE = 4000


def _chat_desde_mensajes(token: str) -> str | None:
    r = requests.get(API.format(token=token, metodo="getUpdates"), timeout=20).json()
    for upd in reversed(r.get("result", [])):
        msg = upd.get("message") or upd.get("edited_message") or {}
        chat = msg.get("chat", {}).get("id")
        if chat:
            return str(chat)
    return None


def enviar(texto: str) -> bool:
    token = os.getenv("TELEGRAM_TOKEN", "").strip()
    if not token:
        print("ℹ️  Sin TELEGRAM_TOKEN: no se envía nada a Telegram. Mensaje:\n" + texto)
        return False
    chat = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    aviso_chat = False
    if not chat:
        chat = _chat_desde_mensajes(token)
        if not chat:
            print("⚠️  No encuentro tu chat: abre tu bot en Telegram, escríbele 'hola' y vuelve a ejecutar.")
            return False
        aviso_chat = True

    partes = _partir(texto)
    if aviso_chat:
        partes.append(
            f"🔑 Tu chat ID es <code>{chat}</code>.\n"
            "Guárdalo en GitHub como secreto <b>TELEGRAM_CHAT_ID</b> para que los avisos lleguen siempre."
        )
    ok = True
    for parte in partes:
        r = requests.post(API.format(token=token, metodo="sendMessage"), timeout=20, data={
            "chat_id": chat, "text": parte, "parse_mode": "HTML", "disable_web_page_preview": "true",
        })
        if not r.ok:
            print(f"⚠️  Telegram respondió {r.status_code}: {r.text[:300]}")
            ok = False
    return ok


def _partir(texto: str) -> list[str]:
    partes, actual = [], ""
    for linea in texto.split("\n"):
        if len(actual) + len(linea) + 1 > LIMITE:
            partes.append(actual)
            actual = ""
        actual += linea + "\n"
    if actual.strip():
        partes.append(actual)
    return partes
