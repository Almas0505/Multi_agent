"""ChromaDB-backed vector store service."""

from __future__ import annotations

from datetime import date

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

    # ------------------------------------------------------------------
    # Phase 2: RAG integration methods
    # ------------------------------------------------------------------

    def store_analysis_results(self, ticker: str, state: dict) -> None:
        """Store agent analysis texts in the 'financial_analyses' ChromaDB collection.

        Creates documents from fundamentals, sentiment, and technical analysis_text
        fields in *state*, with metadata for future RAG retrieval.
        """
        today = date.today().isoformat()
        texts: list[str] = []
        metadatas: list[dict] = []

        agent_fields = [
            ("fundamentals_data", "fundamentals"),
            ("sentiment_data", "sentiment"),
            ("technical_data", "technical"),
            ("competitor_data", "competitor"),
            ("risk_data", "risk"),
        ]

        for state_key, agent_name in agent_fields:
            agent_data = state.get(state_key) or {}
            text = agent_data.get("analysis_text", "")
            if text:
                texts.append(text)
                metadatas.append({"ticker": ticker, "agent": agent_name, "date": today})

        if not texts:
            logger.warning(f"store_analysis_results: no analysis texts found for {ticker}")
            return

        client = self._get_client()
        if client is None:
            logger.warning("VectorStoreService: ChromaDB unavailable, skipping store_analysis_results.")
            return
        try:
            col = client.get_or_create_collection("financial_analyses")
            ids = [f"{ticker}_{metadatas[i]['agent']}_{today}_{i}" for i in range(len(texts))]
            col.add(documents=texts, metadatas=metadatas, ids=ids)
            logger.info(f"Stored {len(texts)} analysis documents for {ticker}")
        except Exception as exc:
            logger.error(f"VectorStoreService.store_analysis_results failed: {exc}")

    def search_similar_analyses(
        self, ticker: str, query: str, n_results: int = 3
    ) -> list[dict]:
        """Search the 'financial_analyses' collection for similar past analyses.

        Returns list of dicts: {text, ticker, date, agent}.
        Falls back to empty list if ChromaDB is unavailable.
        """
        client = self._get_client()
        if client is None:
            logger.warning("VectorStoreService: ChromaDB unavailable, returning empty results.")
            return []
        try:
            col = client.get_or_create_collection("financial_analyses")
            results = col.query(query_texts=[query], n_results=n_results)
            documents = results.get("documents", [[]])[0]
            metadatas_list = results.get("metadatas", [[]])[0]
            return [
                {
                    "text": doc,
                    "ticker": meta.get("ticker", ""),
                    "date": meta.get("date", ""),
                    "agent": meta.get("agent", ""),
                }
                for doc, meta in zip(documents, metadatas_list)
            ]
        except Exception as exc:
            logger.error(f"VectorStoreService.search_similar_analyses failed: {exc}")
            return []

    def store_news_articles(self, ticker: str, articles: list[dict]) -> None:
        """Store news headlines as documents in the 'financial_news' collection for RAG.

        Each article dict should contain at minimum a 'title' key.
        """
        if not articles:
            return

        today = date.today().isoformat()
        texts: list[str] = []
        metadatas: list[dict] = []

        for article in articles:
            title = article.get("title", "")
            if title:
                texts.append(title)
                metadatas.append(
                    {
                        "ticker": ticker,
                        "source": article.get("source", ""),
                        "date": article.get("published_at") or article.get("publishedAt") or today,
                    }
                )

        if not texts:
            return

        client = self._get_client()
        if client is None:
            logger.warning("VectorStoreService: ChromaDB unavailable, skipping store_news_articles.")
            return
        try:
            col = client.get_or_create_collection("financial_news")
            ids = [f"{ticker}_news_{today}_{i}" for i in range(len(texts))]
            col.add(documents=texts, metadatas=metadatas, ids=ids)
            logger.info(f"Stored {len(texts)} news articles for {ticker}")
        except Exception as exc:
            logger.error(f"VectorStoreService.store_news_articles failed: {exc}")
