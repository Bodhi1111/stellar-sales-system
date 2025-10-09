"""
Hybrid Search - BM25 + Vector Search with RRF Fusion

Combines keyword-based search (BM25) with semantic vector search for optimal retrieval.
Uses Reciprocal Rank Fusion (RRF) to merge results from both methods.

Best Practices:
- BM25: Captures exact term matches (names, IDs, specific keywords)
- Vector: Captures semantic similarity (concepts, paraphrases)
- RRF: Combines rankings without needing score normalization
- Metadata filtering: Both methods respect conversation_phase, intent filters

Expected improvement: 50% → 75-85% extraction accuracy
"""

from typing import List, Dict, Any, Tuple
from rank_bm25 import BM25Okapi
import numpy as np


class HybridSearchEngine:
    """
    Combines BM25 keyword search with vector semantic search using RRF fusion.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75, rrf_k: int = 60):
        """
        Initialize hybrid search engine.

        Args:
            k1: BM25 term frequency saturation parameter (default: 1.5)
            b: BM25 length normalization parameter (default: 0.75)
            rrf_k: RRF constant for rank fusion (default: 60)
        """
        self.k1 = k1
        self.b = b
        self.rrf_k = rrf_k
        self.bm25_index = None
        self.corpus_chunks = []  # Store chunk texts for BM25
        self.chunk_metadata = []  # Store full chunk metadata

    def index_chunks(self, chunks: List[Dict[str, Any]]):
        """
        Index chunks for BM25 keyword search.

        Args:
            chunks: List of chunk dictionaries with 'text' and metadata fields
        """
        # Extract texts and tokenize
        self.corpus_chunks = []
        self.chunk_metadata = []

        for chunk in chunks:
            text = chunk.get('text', '')
            self.corpus_chunks.append(text)
            self.chunk_metadata.append(chunk)

        # Tokenize corpus (simple whitespace + lowercase)
        tokenized_corpus = [self._tokenize(text) for text in self.corpus_chunks]

        # Create BM25 index
        self.bm25_index = BM25Okapi(
            tokenized_corpus,
            k1=self.k1,
            b=self.b
        )

        print(f"   ✅ BM25 index created for {len(self.corpus_chunks)} chunks")

    def _tokenize(self, text: str) -> List[str]:
        """
        Simple tokenization: lowercase + split on whitespace.

        Note: For production, consider more sophisticated tokenization
        (stemming, stopword removal, etc.)
        """
        return text.lower().split()

    def search_bm25(
        self,
        query: str,
        top_k: int = 10,
        metadata_filter: Dict[str, Any] = None
    ) -> List[Tuple[int, float]]:
        """
        BM25 keyword search.

        Args:
            query: Search query string
            top_k: Number of top results to return
            metadata_filter: Optional filter (e.g., {"conversation_phase": "pricing"})

        Returns:
            List of (chunk_index, score) tuples
        """
        if self.bm25_index is None:
            return []

        # Tokenize query
        tokenized_query = self._tokenize(query)

        # Get BM25 scores
        scores = self.bm25_index.get_scores(tokenized_query)

        # Apply metadata filter if provided
        if metadata_filter:
            filtered_indices = self._apply_metadata_filter(metadata_filter)
            # Zero out scores for chunks that don't match filter
            scores = np.array([
                score if i in filtered_indices else 0
                for i, score in enumerate(scores)
            ])

        # Get top-k indices
        top_indices = np.argsort(scores)[::-1][:top_k]

        # Return (index, score) tuples for non-zero scores
        results = [
            (int(idx), float(scores[idx]))
            for idx in top_indices
            if scores[idx] > 0
        ]

        return results

    def _apply_metadata_filter(self, metadata_filter: Dict[str, Any]) -> List[int]:
        """
        Filter chunks by metadata criteria.

        Args:
            metadata_filter: Dictionary of metadata conditions

        Returns:
            List of chunk indices that match the filter
        """
        matching_indices = []

        for i, chunk_meta in enumerate(self.chunk_metadata):
            match = True
            for key, value in metadata_filter.items():
                chunk_value = chunk_meta.get(key)

                if isinstance(value, list):
                    # Match if chunk value is in the list
                    if chunk_value not in value:
                        match = False
                        break
                else:
                    # Exact match
                    if chunk_value != value:
                        match = False
                        break

            if match:
                matching_indices.append(i)

        return matching_indices

    def rrf_fusion(
        self,
        bm25_results: List[Tuple[int, float]],
        vector_results: List[Tuple[int, float]],
        bm25_weight: float = 0.5,
        vector_weight: float = 0.5
    ) -> List[Tuple[int, float]]:
        """
        Reciprocal Rank Fusion (RRF) to combine BM25 and vector search results.

        RRF Formula: score(chunk) = Σ [weight / (k + rank(chunk))]

        Args:
            bm25_results: List of (chunk_index, score) from BM25
            vector_results: List of (chunk_index, score) from vector search
            bm25_weight: Weight for BM25 results (default: 0.5)
            vector_weight: Weight for vector results (default: 0.5)

        Returns:
            Fused list of (chunk_index, rrf_score) sorted by score
        """
        rrf_scores = {}

        # Process BM25 results
        for rank, (chunk_idx, _) in enumerate(bm25_results):
            rrf_scores[chunk_idx] = rrf_scores.get(chunk_idx, 0) + \
                                     bm25_weight / (self.rrf_k + rank + 1)

        # Process vector results
        for rank, (chunk_idx, _) in enumerate(vector_results):
            rrf_scores[chunk_idx] = rrf_scores.get(chunk_idx, 0) + \
                                     vector_weight / (self.rrf_k + rank + 1)

        # Sort by RRF score
        fused_results = sorted(
            rrf_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return fused_results

    def hybrid_search(
        self,
        query: str,
        vector_results: List[Tuple[int, float]],
        top_k: int = 10,
        bm25_weight: float = 0.4,
        vector_weight: float = 0.6,
        metadata_filter: Dict[str, Any] = None
    ) -> List[int]:
        """
        Hybrid search combining BM25 and vector search with RRF fusion.

        Args:
            query: Search query string
            vector_results: Vector search results as (chunk_index, score) tuples
            top_k: Number of final results to return
            bm25_weight: Weight for keyword search (default: 0.4)
            vector_weight: Weight for semantic search (default: 0.6)
            metadata_filter: Optional metadata filter

        Returns:
            List of chunk indices ranked by hybrid score
        """
        # BM25 keyword search
        bm25_results = self.search_bm25(
            query,
            top_k=top_k * 2,  # Retrieve more for fusion
            metadata_filter=metadata_filter
        )

        # RRF fusion
        fused_results = self.rrf_fusion(
            bm25_results,
            vector_results,
            bm25_weight=bm25_weight,
            vector_weight=vector_weight
        )

        # Return top-k chunk indices
        return [chunk_idx for chunk_idx, score in fused_results[:top_k]]

    def get_chunk_by_index(self, index: int) -> Dict[str, Any]:
        """Get full chunk metadata by index"""
        if 0 <= index < len(self.chunk_metadata):
            return self.chunk_metadata[index]
        return None
