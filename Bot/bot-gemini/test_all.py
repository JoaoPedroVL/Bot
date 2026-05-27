#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_imports():
    print("[1/6] Testando imports...")
    from src.config import GEMINI_API_KEY, GEMINI_MODEL, WHATSAPP_ACCESS_TOKEN, WHATSAPP_PHONE_NUMBER_ID
    assert GEMINI_API_KEY, "GEMINI_API_KEY vazio"
    assert GEMINI_MODEL == "gemini-2.5-flash"
    assert WHATSAPP_ACCESS_TOKEN, "WHATSAPP_ACCESS_TOKEN vazio"
    assert WHATSAPP_PHONE_NUMBER_ID, "WHATSAPP_PHONE_NUMBER_ID vazio"
    print("  OK\n")


def test_md_file():
    print("[2/6] Testando edital.md...")
    assert os.path.exists("edital.md"), "edital.md nao encontrado"
    size = os.path.getsize("edital.md")
    print(f"  edital.md encontrado ({size/1024:.0f} KB)\n")


def test_guias():
    print("[3/6] Testando imagens guias...")
    from src.rag_engine import _carregar_imagens, GUIAS_DIR, ANEXOS_DIR
    assert os.path.isdir(GUIAS_DIR), f"pasta '{GUIAS_DIR}' nao existe"
    guias = _carregar_imagens(GUIAS_DIR)
    assert len(guias) > 0, "nenhuma imagem guia encontrada"
    print(f"  {len(guias)} guia(s) carregada(s)")
    assert os.path.isdir(ANEXOS_DIR), f"pasta '{ANEXOS_DIR}' nao existe"
    anexos = _carregar_imagens(ANEXOS_DIR)
    assert len(anexos) > 0, "nenhuma imagem de anexo encontrada"
    print(f"  {len(anexos)} anexo(s) carregado(s)\n")


def test_rag_engine():
    print("[4/6] Testando RAG Engine...")
    import asyncio
    from src.rag_engine import RAGEngine

    async def _test():
        rag = RAGEngine()
        resp = await rag.ask("Resumo do edital?")
        assert resp and len(resp) > 10
        print(f"  Resposta: {resp[:80]}...")

    asyncio.run(_test())
    print("  OK\n")


def test_whatsapp_bot():
    print("[5/6] Testando WhatsAppBot...")
    from src.whatsapp_bot import WhatsAppBot
    bot = WhatsAppBot()
    assert bot.rag_engine is not None
    print("  OK\n")


def test_server():
    print("[6/6] Testando servidor...")
    from src.config import WEBHOOK_HOST, WEBHOOK_PORT
    assert WEBHOOK_HOST == "0.0.0.0"
    assert WEBHOOK_PORT == 8000
    import uvicorn
    import fastapi
    print("  OK\n")


def main():
    print("=" * 50)
    print("  EditalBot Gemini WhatsApp - Testes")
    print("=" * 50)
    test_imports()
    test_md_file()
    test_guias()
    test_rag_engine()
    test_whatsapp_bot()
    test_server()
    print("=" * 50)
    print("  TODOS OS TESTES PASSARAM!")
    print("=" * 50)


if __name__ == "__main__":
    main()
