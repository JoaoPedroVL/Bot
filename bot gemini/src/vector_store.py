import logging
import os
import shutil

from langchain_chroma import Chroma
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.config import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    EMBEDDING_MODEL,
    PDF_PATH,
    VECTOR_DB_DIR,
)

logger = logging.getLogger(__name__)


def _get_embeddings() -> FastEmbedEmbeddings:
    return FastEmbedEmbeddings(model_name=EMBEDDING_MODEL)


def get_vector_store() -> Chroma:
    embeddings = _get_embeddings()
    return Chroma(
        persist_directory=VECTOR_DB_DIR,
        embedding_function=embeddings,
        collection_metadata={"hnsw:space": "cosine"},
    )


def process_pdf() -> int:
    if not os.path.exists(PDF_PATH):
        raise FileNotFoundError(
            f"Arquivo '{PDF_PATH}' nao encontrado na raiz do projeto."
        )

    if os.path.exists(VECTOR_DB_DIR):
        shutil.rmtree(VECTOR_DB_DIR)
        logger.info("Banco vetorial anterior removido.")

    logger.info("Carregando PDF...")
    loader = PyMuPDFLoader(PDF_PATH)
    documents = loader.load()
    logger.info(f"PDF carregado: {len(documents)} pagina(s).")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ".", " ", ""],
        length_function=len,
    )
    chunks = text_splitter.split_documents(documents)
    logger.info(f"Texto dividido em {len(chunks)} chunks.")

    embeddings = _get_embeddings()

    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=VECTOR_DB_DIR,
        collection_metadata={"hnsw:space": "cosine"},
    )
    logger.info(f"Chunks indexados no banco vetorial em '{VECTOR_DB_DIR}'.")

    return len(chunks)
