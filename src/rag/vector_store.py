# src/rag/vector_store.py

import uuid
import numpy as np
import pandas as pd
import chromadb
from chromadb.config import Settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Collection names — one per document type
# Separating news and filings allows filtered searches:
# "search only SEC filings" or "search only recent news"
COLLECTION_NEWS    = "finsight_news"
COLLECTION_FILINGS = "finsight_filings"
COLLECTION_ALL     = "finsight_all"


class FinancialVectorStore:
    """
    ChromaDB-backed vector store for financial documents.

    Stores embedded chunks from:
        - News articles (from NewsAPI)
        - SEC filings (from EDGAR)

    Supports:
        - Filtered search by ticker, date, sentiment
        - Hybrid search (semantic + metadata filter)
        - Persistent storage — survives restarts

    Usage:
        store = FinancialVectorStore()
        store.add_news(texts, embeddings, metadatas)
        results = store.query("What revenue did Apple report?", ticker="AAPL")
    """

    def __init__(
        self,
        persist_dir:     str  = "data/embeddings",
        collection_name: str  = COLLECTION_ALL,
    ):
        """
        Initialize ChromaDB with persistent storage.

        ChromaDB stores data in persist_dir as SQLite + binary files.
        Data survives process restarts — you only embed documents once.

        Args:
            persist_dir:     directory for ChromaDB's persistent storage
            collection_name: which collection to use as default
        """
        logger.info(f"Initializing ChromaDB | persist_dir={persist_dir}")

        self.client = chromadb.PersistentClient(path=persist_dir)

        # Get or create the main collection
        # metadata hnsw:space sets the distance metric
        # cosine is correct for normalized embeddings from sentence-transformers
        self.collection = self.client.get_or_create_collection(
            name     = collection_name,
            metadata = {"hnsw:space": "cosine"},
        )

        logger.info(
            f"Vector store ready | "
            f"collection={collection_name} | "
            f"documents={self.collection.count()}"
        )


    def add_documents(
        self,
        texts:      list[str],
        embeddings: np.ndarray,
        metadatas:  list[dict],
        ids:        list[str] = None,
    ) -> int:
        """
        Add a batch of document chunks to the vector store.

        ChromaDB requires four parallel lists — all same length:
            ids[i]:         unique identifier for chunk i
            embeddings[i]:  embedding vector for chunk i
            documents[i]:   raw text of chunk i
            metadatas[i]:   metadata dict for chunk i

        Args:
            texts:      list of text chunks
            embeddings: numpy array of shape (n_chunks, embedding_dim)
            metadatas:  list of metadata dicts
            ids:        list of unique string IDs
                        auto-generated if None

        Returns:
            Number of documents successfully added
        """
        if not texts:
            logger.warning("add_documents called with empty texts list")
            return 0

        # Auto-generate UUIDs if no IDs provided
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in texts]

        # ChromaDB requires embeddings as list of lists, not numpy array
        embeddings_list = embeddings.tolist() if isinstance(embeddings, np.ndarray) \
                          else embeddings

        # Sanitize metadata — ChromaDB only accepts str, int, float, bool values
        # Lists and None will cause silent failures
        clean_metadatas = []
        for meta in metadatas:
            clean_meta = {}
            for k, v in meta.items():
                if isinstance(v, (str, int, float, bool)):
                    clean_meta[k] = v
                elif v is None:
                    clean_meta[k] = ""
                else:
                    clean_meta[k] = str(v)
            clean_metadatas.append(clean_meta)

        try:
            self.collection.add(
                ids        = ids,
                embeddings = embeddings_list,
                documents  = texts,
                metadatas  = clean_metadatas,
            )
            logger.info(f"Added {len(texts)} chunks to vector store")
            return len(texts)

        except Exception as e:
            logger.error(f"Failed to add documents to ChromaDB: {e}")
            raise


    def query(
        self,
        query_embedding: np.ndarray,
        top_k:           int   = 5,
        ticker:          str   = None,
        source_type:     str   = None,
        sentiment:       str   = None,
        date_from:       str   = None,
    ) -> dict:
        """
        Retrieve the top-k most semantically similar chunks.

        Supports optional metadata filters:
            ticker:      only return chunks about this stock
            source_type: "news" or "filing"
            sentiment:   "positive", "negative", or "neutral"
            date_from:   only return chunks from this date onwards
                         format: "YYYY-MM-DD"

        Why metadata filtering matters:
            Without it, a query about Apple might return chunks about
            Microsoft (if they were in a comparative article).
            Filtering by ticker ensures only AAPL documents are searched.

        Args:
            query_embedding: 1D numpy array from embedder.embed_query()
            top_k:           number of results to return
            ticker:          optional ticker filter e.g. "AAPL"
            source_type:     optional source filter
            sentiment:       optional sentiment filter
            date_from:       optional date filter

        Returns:
            ChromaDB query result dict with keys:
                documents:  list of lists of chunk texts
                metadatas:  list of lists of metadata dicts
                distances:  list of lists of similarity distances
                ids:        list of lists of chunk IDs
        """
        # Build WHERE clause for metadata filtering
        # ChromaDB uses MongoDB-style filter syntax
        where = self._build_where_clause(ticker, source_type, sentiment)

        collection_count = self.collection.count()
        if collection_count == 0:
            logger.warning("Vector store is empty — no documents to query")
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}

        query_params = {
            "query_embeddings": [query_embedding.tolist()],
            "n_results":        min(top_k, collection_count),
            "include":          ["documents", "metadatas", "distances"],
        }

        if where:
            query_params["where"] = where

        try:
            results = self.collection.query(**query_params)
            n_returned = len(results["documents"][0]) if results["documents"] else 0
            logger.info(f"Query returned {n_returned} chunks")
            return results

        except Exception as e:
            logger.error(f"ChromaDB query failed: {e}")
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}


    def _build_where_clause(
        self,
        ticker:      str = None,
        source_type: str = None,
        sentiment:   str = None,
    ) -> dict:
        """
        Build ChromaDB metadata filter clause.

        ChromaDB WHERE syntax:
            Single filter:   {"ticker": {"$eq": "AAPL"}}
            Multiple filters: {"$and": [{"ticker": {"$eq": "AAPL"}},
                                        {"sentiment_label": {"$eq": "positive"}}]}

        Args:
            ticker:      stock symbol filter
            source_type: "news" or "filing"
            sentiment:   "positive" / "negative" / "neutral"

        Returns:
            WHERE clause dict, or empty dict if no filters
        """
        conditions = []

        if ticker:
            conditions.append({"ticker": {"$eq": ticker}})

        if source_type:
            conditions.append({"source_type": {"$eq": source_type}})

        if sentiment:
            conditions.append({"sentiment_label": {"$eq": sentiment}})

        if not conditions:
            return {}
        elif len(conditions) == 1:
            return conditions[0]
        else:
            return {"$and": conditions}


    def format_results(self, raw_results: dict) -> list[dict]:
        """
        Convert raw ChromaDB query results into clean list of dicts.

        ChromaDB returns nested lists (designed for batch queries).
        We unwrap the outer list since we only send one query at a time.

        Args:
            raw_results: direct output from self.query()

        Returns:
            List of dicts with keys: text, metadata, distance, similarity
        """
        documents = raw_results.get("documents", [[]])[0]
        metadatas = raw_results.get("metadatas", [[]])[0]
        distances = raw_results.get("distances", [[]])[0]

        formatted = []
        for text, meta, dist in zip(documents, metadatas, distances):

            # ChromaDB cosine distance: 0.0 = identical, 2.0 = opposite
            # Convert to similarity: 1.0 = identical, 0.0 = unrelated
            similarity = round(1.0 - (dist / 2.0), 4)

            formatted.append({
                "text":       text,
                "metadata":   meta,
                "distance":   round(dist, 4),
                "similarity": similarity,
            })

        # Sort by similarity descending (most relevant first)
        formatted.sort(key=lambda x: x["similarity"], reverse=True)
        return formatted


    def upsert_documents(
        self,
        texts:      list[str],
        embeddings: np.ndarray,
        metadatas:  list[dict],
        ids:        list[str],
    ) -> int:
        """
        Add or update documents by ID.

        Use this instead of add_documents() when re-running the pipeline
        to avoid duplicate chunks. If a chunk ID already exists, it gets
        updated. If it doesn't exist, it gets inserted.

        Args:
            texts, embeddings, metadatas, ids: same as add_documents()

        Returns:
            Number of documents upserted
        """
        embeddings_list = embeddings.tolist() if isinstance(embeddings, np.ndarray) \
                          else embeddings

        clean_metadatas = []
        for meta in metadatas:
            clean_meta = {
                k: (v if isinstance(v, (str, int, float, bool)) else str(v or ""))
                for k, v in meta.items()
            }
            clean_metadatas.append(clean_meta)

        self.collection.upsert(
            ids        = ids,
            embeddings = embeddings_list,
            documents  = texts,
            metadatas  = clean_metadatas,
        )

        logger.info(f"Upserted {len(texts)} chunks")
        return len(texts)


    def delete_by_ticker(self, ticker: str) -> None:
        """
        Delete all chunks for a specific ticker.
        Useful when refreshing data for one stock without rebuilding
        the entire vector store.

        Args:
            ticker: stock symbol whose documents to delete
        """
        self.collection.delete(where={"ticker": {"$eq": ticker}})
        logger.info(f"Deleted all chunks for ticker={ticker}")


    def get_stats(self) -> dict:
        """
        Return summary statistics about the vector store.
        Shown in the dashboard sidebar.

        Returns:
            Dict with total_chunks, tickers, collection_name
        """
        total = self.collection.count()

        # Sample metadata to find unique tickers
        if total > 0:
            sample = self.collection.peek(min(100, total))
            tickers = list({
                m.get("ticker", "unknown")
                for m in sample["metadatas"]
            })
        else:
            tickers = []

        return {
            "total_chunks":    total,
            "tickers":         tickers,
            "collection_name": self.collection.name,
        }


    def count(self) -> int:
        """Return total number of chunks in the store."""
        return self.collection.count()