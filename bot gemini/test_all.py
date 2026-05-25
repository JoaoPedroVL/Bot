#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_imports():
    print("[1/4] Testando imports...")
    from src.config import GEMINI_API_KEY, GEMINI_MODEL
    assert GEMINI_API_KEY, "GEMINI_API_KEY vazio"
    assert GEMINI_MODEL == "gemini-2.5-flash"
    print("  OK\n")


def test_md_file():
    print("[2/4] Testando edital.md...")
    from src.rag_engine import MD_PATH
    assert os.path.exists(MD_PATH), f"'{MD_PATH}' nao encontrado"
    size = os.path.getsize(MD_PATH)
    print(f"  edital.md encontrado ({size/1024:.0f} KB)\n")


def test_rag_engine():
    print("[3/4] Testando RAG Engine (Gemini)...")
    import asyncio
    from src.rag_engine import RAGEngine

    async def _test():
        rag = RAGEngine()
        resp = await rag.ask("Resumo do edital?")
        assert resp and len(resp) > 10
        print(f"  Resposta: {resp[:80]}...")

    asyncio.run(_test())
    print("  OK\n")


def test_langchain_gemini():
    print("[4/4] Testando langchain-google-genai...")
    from langchain_google_genai import ChatGoogleGenerativeAI
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key="test")
    assert llm
    print("  OK\n")


def main():
    print("=" * 50)
    print("  EditalBot Gemini - Suite de Testes")
    print("=" * 50)
    test_imports()
    test_md_file()
    test_rag_engine()
    test_langchain_gemini()
    print("=" * 50)
    print("  TODOS OS TESTES PASSARAM!")
    print("=" * 50)


if __name__ == "__main__":
    main()
