#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_imports():
    print("[1/5] Testando imports...")
    from src.config import (
        WHATSAPP_ACCESS_TOKEN, WHATSAPP_PHONE_NUMBER_ID,
        WHATSAPP_VERIFY_TOKEN, DEEPSEEK_API_KEY,
    )
    assert WHATSAPP_ACCESS_TOKEN, "WHATSAPP_ACCESS_TOKEN vazio"
    assert WHATSAPP_PHONE_NUMBER_ID, "WHATSAPP_PHONE_NUMBER_ID vazio"
    assert WHATSAPP_VERIFY_TOKEN, "WHATSAPP_VERIFY_TOKEN vazio"
    assert DEEPSEEK_API_KEY, "DEEPSEEK_API_KEY vazio"
    print("  OK\n")


def test_md_file():
    print("[2/5] Testando edital.md...")
    from src.rag_engine import MD_PATH
    assert os.path.exists(MD_PATH), f"'{MD_PATH}' nao encontrado"
    size = os.path.getsize(MD_PATH)
    print(f"  edital.md encontrado ({size/1024:.0f} KB)\n")


def test_rag_engine():
    print("[3/5] Testando RAG Engine...")
    import asyncio
    from src.rag_engine import RAGEngine

    async def _test():
        rag = RAGEngine()
        resp = await rag.ask("Resumo do edital?")
        assert resp and len(resp) > 10
        print(f"  Resposta: {resp[:100]}...")

    asyncio.run(_test())
    print("  OK\n")


def test_whatsapp_bot():
    print("[4/5] Testando WhatsAppBot...")
    from src.whatsapp_bot import WhatsAppBot
    bot = WhatsAppBot()
    assert bot.rag_engine is not None
    print("  OK\n")


def test_server_start():
    print("[5/5] Testando startup do servidor...")
    from src.config import WEBHOOK_HOST, WEBHOOK_PORT
    assert WEBHOOK_HOST == "0.0.0.0"
    assert WEBHOOK_PORT == 8000
    import uvicorn
    import fastapi
    print(f"  FastAPI v{fastapi.__version__}, Uvicorn pronto\n")


def main():
    print("=" * 50)
    print("  EditalBot WhatsApp - Suite de Testes")
    print("=" * 50)
    test_imports()
    test_md_file()
    test_rag_engine()
    test_whatsapp_bot()
    test_server_start()
    print("=" * 50)
    print("  TODOS OS TESTES PASSARAM!")
    print("=" * 50)


if __name__ == "__main__":
    main()
