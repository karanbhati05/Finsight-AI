# src/rag/embedder.py
import os
os.environ["USE_TF"] = "0"
os.environ["USE_TORCH"] = "1"
import numpy as np
import pandas as pd
from pathlib import Path
from sentence_transformers import SentenceTransformer
from src.utils.logger import get_logger
from src.utils.helpers import chunk_text

logger = get_logger(__name__)

# all-MiniLM-L6-v2: small (80MB), fast, strong performance on semantic similarity
# Produces 384-dimensional embeddings
# Better alternatives for production: all-mpnet-base-v2 (768-dim, slower, more accurate)
DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


class DocumentEmbedder:
    """
    Converts text documents into dense vector embeddings for semantic search.

    Core concept:
        Two sentences with similar meaning will have similar embedding vectors
        even if they use completely different words.

        "Apple posted record quarterly revenue" and
        "iPhone maker exceeded earnings expectations" will be
        close together in embedding space.

        This is what enables the RAG chatbot to find relevant documents
        even when the user's question uses different phrasing than the documents.

    Usage:
        embedder = DocumentEmbedder()
        embedding = embedder.embed_query("What was Apple's revenue?")
        # Returns a 384-dimensional numpy array
    """

    def __init__(self, model_name: str = DEFAULT_MODEL):
        """
        Load sentence transformer model.
        First run downloads ~80MB, cached after that.

        Args:
            model_name: HuggingFace sentence-transformers model
        """
        logger.info(f"Loading embedding model: {model_name}")
        self.model      = SentenceTransformer(model_name)
        self.model_name = model_name
        self.dim        = self.model.get_sentence_embedding_dimension()
        logger.info(f"Embedder ready | model={model_name} | dim={self.dim}")


    def embed_documents(
        self,
        texts:      list[str],
        batch_size: int = 64,
        show_progress: bool = True,
    ) -> np.ndarray:
        """
        Embed a list of document chunks into vectors.

        Args:
            texts:         list of text strings to embed
            batch_size:    how many texts to process at once
                           64 is efficient for CPU; 256+ for GPU
            show_progress: show tqdm progress bar

        Returns:
            numpy array of shape (len(texts), embedding_dim)
            e.g. (1000, 384) for 1000 chunks with MiniLM
        """
        if not texts:
            return np.array([])

        # Filter empty strings — they produce degenerate embeddings
        valid_texts    = [t if t and t.strip() else "empty document" for t in texts]

        logger.info(f"Embedding {len(valid_texts)} chunks...")

        embeddings = self.model.encode(
            valid_texts,
            batch_size      = batch_size,
            show_progress_bar = show_progress,
            convert_to_numpy  = True,
            normalize_embeddings = True,  # L2 normalize for cosine similarity
        )

        logger.info(f"Embeddings shape: {embeddings.shape}")
        return embeddings


    def embed_query(self, query: str) -> np.ndarray:
        """
        Embed a single query string for retrieval.

        Must use the same normalization as embed_documents()
        so similarity scores are comparable.

        Args:
            query: user's natural language question

        Returns:
            1D numpy array of shape (embedding_dim,)
        """
        if not query or not query.strip():
            # Return zero vector for empty queries
            return np.zeros(self.dim)

        embedding = self.model.encode(
            [query],
            convert_to_numpy     = True,
            normalize_embeddings = True,
        )
        return embedding[0]    # return 1D array, not (1, dim)


    def embed_dataframe(
        self,
        df:             pd.DataFrame,
        text_col:       str   = "content",
        chunk_size:     int   = 512,
        overlap:        int   = 50,
        metadata_cols:  list  = None,
    ) -> tuple[list[str], np.ndarray, list[dict]]:
        """
        Embed all documents in a DataFrame, with chunking for long texts.

        This is the main function called by build_vector_store.py.
        It handles the full pipeline:
            1. Iterate over each document in the DataFrame
            2. Chunk long documents into overlapping segments
            3. Embed all chunks
            4. Create metadata dicts for each chunk (for ChromaDB)

        Why return (texts, embeddings, metadatas) as a tuple?
            ChromaDB's add() method needs all three aligned:
            texts[i], embeddings[i], and metadatas[i] must all refer
            to the same chunk.

        Args:
            df:            DataFrame with document text
            text_col:      column containing document text
            chunk_size:    words per chunk
            overlap:       word overlap between chunks
            metadata_cols: list of columns to include in metadata
                           (stored alongside embeddings in ChromaDB)

        Returns:
            Tuple of (chunk_texts, embeddings_array, metadatas_list)
        """
        if metadata_cols is None:
            metadata_cols = ["ticker", "source", "published_at", "url", "sentiment_label"]

        all_texts     = []
        all_metadatas = []
        all_ids       = []

        logger.info(f"Processing {len(df)} documents for embedding...")

        for idx, row in df.iterrows():
            text = str(row.get(text_col, "") or "")
            if not text.strip():
                continue

            # Split document into overlapping chunks
            chunks = chunk_text(text, chunk_size=chunk_size, overlap=overlap)

            for chunk_idx, chunk in enumerate(chunks):
                if not chunk.strip():
                    continue

                # Unique ID for this chunk — needed by ChromaDB
                doc_id = f"doc_{idx}_chunk_{chunk_idx}"

                # Metadata stored alongside the embedding
                # Used for filtering queries e.g. "only search AAPL documents"
                meta = {}
                for col in metadata_cols:
                    val = row.get(col, "")
                    # ChromaDB requires string/int/float metadata values
                    meta[col] = str(val) if val is not None else ""

                # Add chunk position metadata — useful for ordering retrieved chunks
                meta["chunk_idx"]   = chunk_idx
                meta["doc_row_idx"] = int(idx)

                all_texts.append(chunk)
                all_metadatas.append(meta)
                all_ids.append(doc_id)

        if not all_texts:
            logger.warning("No valid text chunks found for embedding")
            return [], np.array([]), []

        logger.info(f"Total chunks to embed: {len(all_texts)}")

        # Embed all chunks in one batch
        embeddings = self.embed_documents(all_texts)

        return all_texts, embeddings, all_metadatas


    def compute_similarity(
        self,
        query_embedding:    np.ndarray,
        document_embeddings: np.ndarray,
    ) -> np.ndarray:
        """
        Compute cosine similarity between a query and all document embeddings.

        Because we used normalize_embeddings=True, vectors have unit length.
        For unit vectors: cosine_similarity = dot_product
        This makes similarity computation a simple matrix multiplication.

        Args:
            query_embedding:     1D array of shape (dim,)
            document_embeddings: 2D array of shape (n_docs, dim)

        Returns:
            1D array of similarity scores, shape (n_docs,)
            Scores range from 0.0 (unrelated) to 1.0 (identical)
        """
        # Dot product of normalized vectors = cosine similarity
        similarities = document_embeddings @ query_embedding
        return similarities


    def find_most_similar(
        self,
        query:               str,
        texts:               list[str],
        document_embeddings: np.ndarray,
        top_k:               int = 5,
    ) -> list[dict]:
        """
        Find the top-k most similar texts to a query.

        Lightweight alternative to ChromaDB for small document sets
        or quick experimentation in notebooks.

        Args:
            query:               question string
            texts:               list of document strings (same order as embeddings)
            document_embeddings: pre-computed embeddings array
            top_k:               number of results to return

        Returns:
            List of dicts with 'text', 'score', 'rank' sorted by similarity
        """
        query_emb     = self.embed_query(query)
        similarities  = self.compute_similarity(query_emb, document_embeddings)

        # Get indices of top-k highest scores
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for rank, idx in enumerate(top_indices):
            results.append({
                "rank":  rank + 1,
                "score": round(float(similarities[idx]), 4),
                "text":  texts[idx],
            })

        return results