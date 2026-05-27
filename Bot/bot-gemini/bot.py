#!/usr/bin/env python3
import base64
import logging
import sys

from fastapi import FastAPI, Request, HTTPException
import httpx
import uvicorn

from src.config import (
    WHATSAPP_ACCESS_TOKEN,
    WHATSAPP_API_BASE,
    WHATSAPP_PHONE_NUMBER_ID,
    WEBHOOK_HOST,
    WEBHOOK_PORT,
)
from src.whatsapp_bot import WhatsAppBot, _ULTIMO_ERRO

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

WEBHOOK_VERIFY_TOKEN = "meu_token_secreto_123"

app = FastAPI(title="EditalBot Gemini WhatsApp")
bot = WhatsAppBot()


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "phone_number_id": WHATSAPP_PHONE_NUMBER_ID,
        "api_base": WHATSAPP_API_BASE,
        "token_preview": WHATSAPP_ACCESS_TOKEN[:20] + "..." if WHATSAPP_ACCESS_TOKEN else "vazio",
        "ultimo_erro": _ULTIMO_ERRO,
    }


@app.get("/webhook")
async def verify_webhook(request: Request):
    params = dict(request.query_params)
    logger.info("Params recebidos: %s", params)
    hub_mode = params.get("hub.mode") or params.get("hub_mode")
    hub_token = params.get("hub.verify_token") or params.get("hub_verify_token")
    hub_challenge = params.get("hub.challenge") or params.get("hub_challenge")
    if hub_mode == "subscribe" and hub_token == WEBHOOK_VERIFY_TOKEN and hub_challenge:
        from fastapi.responses import PlainTextResponse
        return PlainTextResponse(hub_challenge, status_code=200)
    raise HTTPException(status_code=403, detail="Verification failed")


@app.post("/webhook")
async def webhook(request: Request):
    body = await request.json()
    logger.info("Webhook recebido: %s", body)

    try:
        entry = body["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]

        if "messages" not in value:
            return {"status": "ok"}

        for msg in value["messages"]:
            msg_type = msg.get("type")
            from_number = msg["from"]
            logger.info("Tipo: %s de %s", msg_type, from_number)

            if msg_type == "text":
                texto = msg["text"]["body"].strip()
                await bot.handle_incoming(from_number, texto)

            elif msg_type == "image":
                texto_caption = (msg.get("image", {}).get("caption") or "").strip()
                media_id = msg["image"]["id"]
                logger.info("Imagem recebida: %s | caption: %s", media_id, texto_caption)
                imagem_b64 = await bot._baixar_imagem(media_id)
                await bot.handle_incoming(
                    from_number,
                    texto_caption or "O que tem nessa imagem?",
                    imagem_b64=imagem_b64,
                )

            elif msg_type == "interactive":
                texto = (msg.get("interactive", {}).get("button_reply", {}).get("title")
                         or msg.get("interactive", {}).get("list_reply", {}).get("title")
                         or "")
                await bot.handle_incoming(from_number, texto)

            else:
                logger.info("Tipo nao tratado: %s", msg_type)

    except (KeyError, IndexError, TypeError) as e:
        logger.warning("Erro ao processar webhook: %s", e, exc_info=True)

    return {"status": "ok"}


def main() -> None:
    if not WHATSAPP_ACCESS_TOKEN:
        logger.error("WHATSAPP_ACCESS_TOKEN nao configurado!")
        sys.exit(1)
    if not WHATSAPP_PHONE_NUMBER_ID:
        logger.error("WHATSAPP_PHONE_NUMBER_ID nao configurado!")
        sys.exit(1)

    logger.info("Iniciando EditalBot Gemini WhatsApp em %s:%s", WEBHOOK_HOST, WEBHOOK_PORT)
    uvicorn.run(app, host=WEBHOOK_HOST, port=WEBHOOK_PORT)


if __name__ == "__main__":
    main()
