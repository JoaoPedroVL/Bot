import logging
import re
from typing import Awaitable, Callable

import httpx

from src.config import (
    WHATSAPP_ACCESS_TOKEN,
    WHATSAPP_API_BASE,
    WHATSAPP_PHONE_NUMBER_ID,
)
from src.rag_engine import RAGEngine

logger = logging.getLogger(__name__)

_ULTIMO_ERRO: str | None = None

_PALAVRAS_SAUDACAO = {
    "oi", "ola", "olá", "oie", "oii", "ooi", "hey", "bom", "boa",
    "dia", "tarde", "noite", "blz", "beleza", "td", "bem", "tudo",
    "fala", "opa", "iae", "eae", "eai", "aí", "saudações", "saudacoes",
    "hr", "hre", "hra", "obrigado", "obrigada", "brigado", "vlw",
    "valeu", "thanks", "thx", "tchau", "xau", "ate", "até", "logo",
    "sim", "nao", "não", "ok", "oks", "okay",
}


def _eh_saudacao(texto: str) -> bool:
    palavras = re.sub(r"[^\wà-üáéíóúâêôãõç]", " ", texto.lower()).split()
    if not palavras:
        return False
    return all(p in _PALAVRAS_SAUDACAO for p in palavras)


class WhatsAppBot:
    def __init__(self) -> None:
        self.rag_engine = RAGEngine()
        self._historico: dict[str, list[str]] = {}
        self._on_message_callback: Callable[[str, str], Awaitable[None]] | None = None

    def on_message(self, callback: Callable[[str, str], Awaitable[None]]) -> None:
        self._on_message_callback = callback

    async def send_message(self, to: str, text: str) -> None:
        global _ULTIMO_ERRO
        url = f"{WHATSAPP_API_BASE}/{WHATSAPP_PHONE_NUMBER_ID}/messages"

        logger.info(
            "Enviando mensagem para %s via %s",
            to, url,
        )

        headers = {
            "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": text},
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code != 200:
                _ULTIMO_ERRO = f"{resp.status_code}: {resp.text}"
                logger.error(
                    "Erro ao enviar mensagem para %s: %s %s",
                    to, resp.status_code, resp.text,
                )
            else:
                logger.info("Mensagem enviada com sucesso para %s", to)
                _ULTIMO_ERRO = None

    async def handle_incoming(self, from_number: str, user_text: str) -> None:
        if from_number not in self._historico:
            self._historico[from_number] = []

        if _eh_saudacao(user_text):
            await self.send_message(
                from_number,
                "Ola! Pergunte algo sobre o edital que eu respondo!",
            )
            return

        historico_recente = self._historico[from_number][-2:]

        answer = await self.rag_engine.ask(user_text, history=historico_recente)

        self._historico[from_number].append(user_text)
        self._historico[from_number].append(answer)
        self._historico[from_number] = self._historico[from_number][-6:]

        if len(self._historico[from_number]) <= 2:
            answer = "Ola! " + answer

        await self.send_message(from_number, answer)
