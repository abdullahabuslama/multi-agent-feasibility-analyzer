"""Long-term memory: the company knowledge base stored in Qdrant.

Documents are turned into vectors (lists of numbers that capture meaning)
by a Sentence Transformers model and saved in a Qdrant collection. A search
finds the passages whose meaning is closest to the question.

Where the data lives:
- `QDRANT_URL` empty  -> local mode, saved in the `QDRANT_PATH` folder.
  Only one process can open that folder at a time: stop the API before
  running the ingest command.
- `QDRANT_URL` set    -> a Qdrant server (Docker or Qdrant Cloud).
"""

import atexit
from functools import lru_cache

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from config.settings import get_settings

EMPTY_STORE_MESSAGE = (
    "The company knowledge base is empty. "
    "Run `python -m src.memory.ingest --rebuild` first."
)


def get_retriever(k: int = 4) -> VectorStoreRetriever:
    """A retriever that returns the `k` passages closest to a query."""
    if not get_client().collection_exists(_collection_name()):
        raise RuntimeError(EMPTY_STORE_MESSAGE)
    return _vector_store().as_retriever(search_kwargs={"k": k})


def add_documents(documents: list[Document], ids: list[str] | None = None) -> None:
    """Store documents. Passing the same ids again replaces the old copies."""
    _ensure_collection()
    _vector_store().add_documents(documents, ids=ids)


def reset_collection() -> None:
    """Delete every stored document."""
    client = get_client()
    if client.collection_exists(_collection_name()):
        client.delete_collection(_collection_name())


@lru_cache
def get_client() -> QdrantClient:
    # Created once and shared: in local mode a second client would fail
    # because the storage folder is locked by the first one.
    settings = get_settings()
    if settings.qdrant_url:
        client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key or None)
    else:
        client = QdrantClient(path=str(settings.qdrant_path))
    # Close while Python is still running; closing during shutdown prints errors.
    atexit.register(client.close)
    return client


@lru_cache
def get_embeddings() -> Embeddings:
    # Imported here because loading the model is slow; only pay for it when used.
    from langchain_huggingface import HuggingFaceEmbeddings

    return HuggingFaceEmbeddings(model_name=get_settings().embedding_model)


def _vector_store() -> QdrantVectorStore:
    return QdrantVectorStore(
        client=get_client(),
        collection_name=_collection_name(),
        embedding=get_embeddings(),
    )


def _ensure_collection() -> None:
    client = get_client()
    if client.collection_exists(_collection_name()):
        return
    vector_size = len(get_embeddings().embed_query("size probe"))
    client.create_collection(
        _collection_name(),
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
    )


def _collection_name() -> str:
    return get_settings().qdrant_collection
