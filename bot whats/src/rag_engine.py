import logging
import os

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from src.config import DEEPSEEK_API_BASE, DEEPSEEK_API_KEY, DEEPSEEK_MODEL

logger = logging.getLogger(__name__)

MD_PATH = "edital.md"

SYSTEM_PROMPT = (
    "Voce e um especialista em editais que explica de forma simples. "
    "Tom natural e direto, sem rodeios.\n\n"
    "REGRAS:\n"
    "1. Resumo: 2-3 frases com o essencial (programa, valor, prazo).\n"
    "2. Pergunta especifica: responda com os dados, nada alem.\n"
    "3. Nao use cumprimentos, despedidas. So 'Algo mais?' se couber.\n"
    "4. Se nao achar: 'Nao encontrei essa info no edital.'\n"
    "5. Nao invente. Baseie-se apenas no edital abaixo.\n"
)


class RAGEngine:
    def __init__(self) -> None:
        self.llm = ChatOpenAI(
            model=DEEPSEEK_MODEL,
            temperature=0.7,
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_API_BASE,
        )
        self._edital: str | None = None

    def _carregar_edital(self) -> str:
        if self._edital is None:
            path = MD_PATH
            if not os.path.exists(path):
                path = os.path.join(os.path.dirname(__file__), "..", MD_PATH)
            if not os.path.exists(path):
                raise FileNotFoundError(
                    f"Arquivo '{MD_PATH}' nao encontrado."
                )
            with open(path, encoding="utf-8") as f:
                self._edital = f.read()
        return self._edital

    async def ask(self, question: str, history: list[str] | None = None) -> str:
        try:
            edital = self._carregar_edital()

            historico_str = ""
            if history:
                historico_str = "\nHistorico da conversa:\n" + "\n".join(
                    f"- {m}" for m in history
                )

            human_prompt = (
                f"EDITAL COMPLETO:\n{edital}\n\n"
                f"{historico_str}\n"
                f"Pergunta do usuario:\n{question}\n\n"
                "Responda com base APENAS no edital acima."
            )

            messages = [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=human_prompt),
            ]

            response = await self.llm.ainvoke(messages)
            return response.content.strip()

        except Exception as e:
            logger.error(f"Erro no RAGEngine: {e}", exc_info=True)
            return (
                "Desculpe, ocorreu um erro ao processar sua pergunta. "
                "Tente novamente em alguns instantes!"
            )
