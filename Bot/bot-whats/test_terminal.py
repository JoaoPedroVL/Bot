#!/usr/bin/env python3
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.rag_engine import RAGEngine


async def main():
    rag = RAGEngine()
    historico = []

    print("=" * 50)
    print("  EditalBot - Modo Teste (Terminal)")
    print("  Digite 'sair' para encerrar")
    print("=" * 50)

    while True:
        pergunta = input("\n📝 Sua pergunta: ").strip()
        if pergunta.lower() in ("sair", "quit", "exit"):
            print("Encerrando...")
            break

        historico_recente = historico[-2:]
        resposta = await rag.ask(pergunta, history=historico_recente)

        historico.append(pergunta)
        historico.append(resposta)
        historico = historico[-6:]

        print(f"\n🤖 Resposta: {resposta}")


if __name__ == "__main__":
    asyncio.run(main())
