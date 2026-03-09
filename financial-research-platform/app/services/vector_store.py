"""ChromaDB-backed vector store service."""

from __future__ import annotations

from loguru import logger

try:
    import chromadb  # type: ignore
    _CHROMA_AVAILABLE = True
except ImportError:  # pragma: no cover
    _CHROMA_AVAILABLE = False

from app.config import settings


class VectorStoreService:
    """Store and retrieve text embeddings using ChromaDB."""

    def __init__(self) -> None:
        self._client = None

    def _get_client(self):
        if not _CHROMA_AVAILABLE:
            return None
        if self._client is None:
            try:
                self._client = chromadb.HttpClient(
                    host=settings.CHROMA_HOST,
                    port=settings.CHROMA_PORT,
                )
            except Exception as exc:
                logger.warning(f"ChromaDB connection failed: {exc}")
                self._client = None
        return self._client

    def add_documents(
        self,
        texts: list[str],
        metadatas: list[dict],
        collection: str = "financial_research",
    ) -> None:
        """Add *texts* with associated *metadatas* to the named collection."""
        client = self._get_client()
        if client is None:
            logger.warning("VectorStoreService: ChromaDB unavailable, skipping add_documents.")
            return
        try:
            col = client.get_or_create_collection(collection)
            ids = [f"doc_{i}" for i in range(len(texts))]
            col.add(documents=texts, metadatas=metadatas, ids=ids)
        except Exception as exc:
            logger.error(f"VectorStoreService.add_documents failed: {exc}")

    def search(
        self,
        query: str,
        collection: str = "financial_research",
        n_results: int = 5,
    ) -> list[dict]:
        """Search the collection for documents similar to *query*."""
        client = self._get_client()
        if client is None:
            logger.warning("VectorStoreService: ChromaDB unavailable, returning empty results.")
            return []
        try:
            col = client.get_or_create_collection(collection)
            results = col.query(query_texts=[query], n_results=n_results)
            documents = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            return [
                {"text": doc, "metadata": meta}
                for doc, meta in zip(documents, metadatas)
            ]
        except Exception as exc:
            logger.error(f"VectorStoreService.search failed: {exc}")
            return []
