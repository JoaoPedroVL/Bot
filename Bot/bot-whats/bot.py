#!/usr/bin/env python3
import logging
import sys

from fastapi import FastAPI, Request, HTTPException
import uvicorn

from src.config import (
    WHATSAPP_ACCESS_TOKEN,
    WHATSAPP_PHONE_NUMBER_ID,
    WHATSAPP_VERIFY_TOKEN,
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

app = FastAPI(title="EditalBot WhatsApp")
bot = WhatsAppBot()


@app.get("/health")
async def health():
    from src.config import WHATSAPP_PHONE_NUMBER_ID, WHATSAPP_API_BASE
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
        logger.info("Value: %s", value)

        if "messages" not in value:
            logger.info("Sem mensagens, apenas status update")
            return {"status": "ok"}

        for msg in value["messages"]:
            msg_type = msg.get("type")
            logger.info("Tipo da mensagem: %s", msg_type)

            if msg_type == "text":
                from_number = msg["from"]
                text = msg["text"]["body"].strip()
                logger.info("Mensagem de %s: %s", from_number, text)
                await bot.handle_incoming(from_number, text)
            elif msg_type == "interactive":
                from_number = msg["from"]
                text = msg.get("interactive", {}).get("button_reply", {}).get("title", "")
                if not text:
                    text = msg.get("interactive", {}).get("list_reply", {}).get("title", "")
                logger.info("Mensagem interativa de %s: %s", from_number, text)
                await bot.handle_incoming(from_number, text)
            else:
                logger.info("Tipo nao tratado: %s", msg_type)

    except (KeyError, IndexError, TypeError) as e:
        logger.warning("Erro ao processar webhook: %s", e, exc_info=True)

    return {"status": "ok"}


def main() -> None:
    if not WHATSAPP_ACCESS_TOKEN:
        logger.error(
            "WHATSAPP_ACCESS_TOKEN nao configurado!\n"
            "1. Copie .env.example para .env\n"
            "2. Preencha suas credenciais\n"
            "3. Execute novamente."
        )
        sys.exit(1)

    if not WHATSAPP_PHONE_NUMBER_ID:
        logger.error(
            "WHATSAPP_PHONE_NUMBER_ID nao configurado!\n"
            "Preencha no .env com o ID do numero de telefone do WhatsApp."
        )
        sys.exit(1)

    logger.info(
        "Iniciando EditalBot WhatsApp em %s:%s",
        WEBHOOK_HOST, WEBHOOK_PORT,
    )
    uvicorn.run(app, host=WEBHOOK_HOST, port=WEBHOOK_PORT)


if __name__ == "__main__":
    main()
