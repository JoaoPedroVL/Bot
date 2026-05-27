import base64
import logging
import mimetypes
import os
import random
import re

import httpx

from src.config import (
    WHATSAPP_ACCESS_TOKEN,
    WHATSAPP_API_BASE,
    WHATSAPP_PHONE_NUMBER_ID,
)
from src.rag_engine import RAGEngine, _extrair_numero_anexo, _achar_anexo

logger = logging.getLogger(__name__)

_ULTIMO_ERRO: str | None = None


def _quebrar_texto(texto: str, max_len: int = 500) -> list[str]:
    if len(texto) <= max_len:
        return [texto]
    partes = []
    while texto:
        if len(texto) <= max_len:
            partes.append(texto.strip())
            break
        corte = texto.rfind(". ", 0, max_len)
        if corte == -1 or corte < max_len // 2:
            corte = texto.rfind("\n", 0, max_len)
        if corte == -1 or corte < max_len // 2:
            corte = texto.rfind(" ", 0, max_len)
        if corte == -1 or corte < max_len // 2:
            corte = max_len
        partes.append(texto[:corte + 1].strip())
        texto = texto[corte + 1:]
    return partes


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


async def _enviar_imagem_whatsapp(to: str, caminho_arquivo: str) -> None:
    global _ULTIMO_ERRO
    upload_url = f"{WHATSAPP_API_BASE}/{WHATSAPP_PHONE_NUMBER_ID}/media"

    mime = mimetypes.guess_type(caminho_arquivo)[0] or "image/png"
    nome = os.path.basename(caminho_arquivo)

    headers_upload = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
    }
    with open(caminho_arquivo, "rb") as f:
        files = {
            "file": (nome, f, mime),
            "messaging_product": (None, "whatsapp"),
            "type": (None, mime),
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(upload_url, headers=headers_upload, files=files)
            if resp.status_code not in (200, 201):
                _ULTIMO_ERRO = f"Upload: {resp.status_code} {resp.text}"
                logger.error("Erro no upload da imagem: %s", _ULTIMO_ERRO)
                return
            media_id = resp.json().get("id")

    msg_url = f"{WHATSAPP_API_BASE}/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "image",
        "image": {"id": media_id},
    }
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(msg_url, json=payload, headers=headers)
        if resp.status_code != 200:
            _ULTIMO_ERRO = f"{resp.status_code}: {resp.text}"
            logger.error("Erro ao enviar imagem: %s %s", resp.status_code, resp.text)
        else:
            _ULTIMO_ERRO = None


class WhatsAppBot:
    def __init__(self) -> None:
        self.rag_engine = RAGEngine()
        self._historico: dict[str, list[str]] = {}

    async def _baixar_imagem(self, media_id: str) -> str | None:
        url = f"{WHATSAPP_API_BASE}/{media_id}"
        headers = {"Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}"}
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code != 200:
                logger.error("Erro ao obter URL da midia: %s", resp.text)
                return None
            data = resp.json()
            image_url = data.get("url")
            if not image_url:
                logger.error("URL da imagem nao encontrada")
                return None
            img_resp = await client.get(image_url, headers=headers)
            if img_resp.status_code != 200:
                logger.error("Erro ao baixar imagem: %s", img_resp.status_code)
                return None
            return base64.b64encode(img_resp.content).decode()

    async def send_message(self, to: str, text: str) -> None:
        global _ULTIMO_ERRO
        url = f"{WHATSAPP_API_BASE}/{WHATSAPP_PHONE_NUMBER_ID}/messages"
        partes = _quebrar_texto(text, 500)
        for parte in partes:
            headers = {
                "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
                "Content-Type": "application/json",
            }
            payload = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "text",
                "text": {"body": parte},
            }
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json=payload, headers=headers)
                if resp.status_code != 200:
                    _ULTIMO_ERRO = f"{resp.status_code}: {resp.text}"
                    logger.error("Erro ao enviar: %s %s", resp.status_code, resp.text)
                else:
                    _ULTIMO_ERRO = None

    async def handle_incoming(
        self, from_number: str, user_text: str, imagem_b64: str | None = None,
    ) -> None:
        if from_number not in self._historico:
            self._historico[from_number] = []

        if not imagem_b64 and _eh_saudacao(user_text):
            await self.send_message(
                from_number, random.choice([
                    "Ola! Me pergunte algo sobre o edital.",
                    "Fala ai! Pode perguntar sobre o edital.",
                    "Oi! O que voce quer saber sobre o edital?",
                ]),
            )
            return

        num_anexo = _extrair_numero_anexo(user_text)
        if num_anexo is not None:
            caminho = _achar_anexo(num_anexo)
            if caminho:
                await self.send_message(
                    from_number,
                    f"Aqui esta o anexo {num_anexo}:",
                )
                await _enviar_imagem_whatsapp(from_number, caminho)
                return
            else:
                await self.send_message(
                    from_number,
                    f"Nao achei a imagem do anexo {num_anexo} na pasta.",
                )
                return

        historico_recente = self._historico[from_number][-2:]
        answer = await self.rag_engine.ask(
            user_text,
            history=historico_recente,
            imagem_usuario=imagem_b64,
        )

        self._historico[from_number].append(user_text)
        self._historico[from_number].append(answer)
        self._historico[from_number] = self._historico[from_number][-6:]

        if len(self._historico[from_number]) <= 2:
            answer = "Ola! " + answer

        await self.send_message(from_number, answer)
