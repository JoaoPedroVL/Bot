#!/usr/bin/env python3
import asyncio
import base64
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.rag_engine import RAGEngine


async def main():
    rag = RAGEngine()
    historico = []

    print("=" * 50)
    print("  EditalBot Gemini - Modo Teste (Terminal)")
    print("  Digite 'sair' para encerrar")
    print("  Para enviar imagem:")
    print("    caminho/da/imagem.jpg | sua pergunta")
    print("=" * 50)

    while True:
        entrada = input("\nSua pergunta: ").strip()
        if entrada.lower() in ("sair", "quit", "exit"):
            print("Encerrando...")
            break

        imagem_b64 = None
        pergunta = entrada

        if "|" in entrada:
            caminho_img = entrada.split("|", 1)[0].strip()
            pergunta = entrada.split("|", 1)[1].strip()
            if os.path.exists(caminho_img):
                with open(caminho_img, "rb") as f:
                    imagem_b64 = base64.b64encode(f.read()).decode()
                print(f"  Imagem carregada: {caminho_img}")
            else:
                print(f"  Arquivo nao encontrado: {caminho_img}")

        historico_recente = historico[-2:]
        resposta = await rag.ask(
            pergunta,
            history=historico_recente,
            imagem_usuario=imagem_b64,
        )

        historico.append(pergunta)
        historico.append(resposta)
        historico = historico[-6:]

        print(f"\nResposta: {resposta}")


if __name__ == "__main__":
    asyncio.run(main())
