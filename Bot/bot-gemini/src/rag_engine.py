import base64
import logging
import os
import re

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from src.config import GEMINI_API_KEY, GEMINI_MODEL
from src.vector_store import get_vector_store

logger = logging.getLogger(__name__)

GUIAS_DIR = "guias"
ANEXOS_DIR = "anexos"

SYSTEM_PROMPT = (
    "Voce e um assistente que ajuda pessoas a entenderem editais "
    "e usarem sistemas passo a passo.\n\n"
    "REGRAS:\n"
    "1. Voce recebe trechos do edital, imagens de exemplo (guias) "
    "com setas e indicacoes, e talvez uma imagem do usuario.\n"
    "2. Use as guias como referencia visual para explicar "
    "onde clicar, o que preencher, qual o proximo passo.\n"
    "3. Se o usuario mandou print, compare com as guias e "
    "explique em que parte ele esta e o que fazer.\n"
    "4. Se perguntarem sobre um anexo, responda com o que tem "
    "na imagem do anexo.\n"
    "5. Resposta simples e direta, como se fosse um colega "
    "ajudando. Nao invente se nao estiver no edital ou nas guias.\n"
    "6. Baseie-se APENAS nos trechos do edital e nas imagens fornecidas.\n"
)


def _imagem_para_base64(caminho: str) -> str:
    with open(caminho, "rb") as f:
        return base64.b64encode(f.read()).decode()


def _carregar_imagens(pasta: str) -> list[dict]:
    imagens = []
    if not os.path.isdir(pasta):
        return imagens
    ext_validas = (".png", ".jpg", ".jpeg", ".gif", ".webp")
    for nome in sorted(os.listdir(pasta)):
        if nome.lower().endswith(ext_validas):
            caminho = os.path.join(pasta, nome)
            b64 = _imagem_para_base64(caminho)
            mime = "image/png" if nome.lower().endswith(".png") else "image/jpeg"
            imagens.append({
                "type": "image_url",
                "image_url": {"url": f"data:{mime};base64,{b64}"},
                "_arquivo": caminho,
                "_nome": nome,
            })
    return imagens


def _extrair_numero_anexo(pergunta: str) -> int | None:
    match = re.search(r"(?:anexo|annex)\s*(?:de\s*numero\s*)?(\d+)", pergunta.lower())
    if match:
        return int(match.group(1))
    match_romano = re.search(
        r"(?:anexo|annex)\s+(I|II|III|IV|V|VI|VII|VIII|IX|X)", pergunta, re.IGNORECASE,
    )
    if match_romano:
        romanos = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5,
                   "VI": 6, "VII": 7, "VIII": 8, "IX": 9, "X": 10}
        return romanos.get(match_romano.group(1).upper())
    return None


def _achar_anexo(numero: int) -> str | None:
    if not os.path.isdir(ANEXOS_DIR):
        return None
    for nome in os.listdir(ANEXOS_DIR):
        if nome.lower().endswith((".png", ".jpg", ".jpeg")):
            if re.match(rf"anexo{numero}\.", nome, re.IGNORECASE):
                return os.path.join(ANEXOS_DIR, nome)
    return None


class RAGEngine:
    def __init__(self) -> None:
        self.vector_store = get_vector_store()
        self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 6})
        self.llm = ChatGoogleGenerativeAI(
            model=GEMINI_MODEL,
            temperature=0.7,
            api_key=GEMINI_API_KEY,
        )
        self._guias: list[dict] | None = None
        self._anexos: list[dict] | None = None

    def _get_anexo_imagem(self, numero: int) -> str | None:
        if self._anexos is None:
            self._anexos = _carregar_imagens(ANEXOS_DIR)
        for img in self._anexos:
            nome = img["_nome"].lower()
            if re.match(rf"anexo{numero}(?!\d)", nome):
                return img["image_url"]["url"]
            if re.match(rf"anexo{numero}continuacao", nome):
                return img["image_url"]["url"]
        return None

    async def ask(
        self,
        question: str,
        history: list[str] | None = None,
        imagem_usuario: str | None = None,
    ) -> str:
        try:
            docs = await self.retriever.ainvoke(question)
            if not docs:
                return "Nao encontrei essa informacao no edital."

            if self._guias is None:
                self._guias = _carregar_imagens(GUIAS_DIR)

            context = "\n\n---\n\n".join(doc.page_content for doc in docs)

            historico_str = ""
            if history:
                historico_str = "\nHistorico da conversa:\n" + "\n".join(
                    f"- {m}" for m in history
                )

            texto = (
                f"Trechos do edital:\n{context}\n\n"
                f"{historico_str}\n"
                f"Pergunta do usuario:\n{question}\n\n"
                "Responda com base APENAS nos trechos acima e nas imagens."
            )

            conteudo: list[dict] = [{"type": "text", "text": texto}]
            conteudo.extend(self._guias)
            if imagem_usuario:
                conteudo.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{imagem_usuario}"},
                })

            messages = [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=conteudo),
            ]

            response = await self.llm.ainvoke(messages)
            return response.content.strip()

        except Exception as e:
            logger.error(f"Erro no RAGEngine: {e}", exc_info=True)
            return "Desculpe, ocorreu um erro ao processar sua pergunta."
