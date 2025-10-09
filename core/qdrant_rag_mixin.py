"""
Qdrant RAG Mixin - Shared Hybrid Search Capabilities for All Agents

Provides every agent with semantic, multi-dimensional context from Qdrant.
Uses hybrid search (BM25 + Vector + RRF) for optimal retrieval.
"""

from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer
from core.hybrid_search import HybridSearchEngine


class QdrantRAGMixin:
    """
    Mixin class that gives any agent RAG capabilities with Qdrant.

    Usage:
        class MyAgent(BaseAgent, QdrantRAGMixin):
            def __init__(self, settings):
                super().__init__(settings)
                self._init_qdrant_rag(settings)

            async def run(self, transcript_id):
                chunks = await self.retrieve_chunks(transcript_id, ["query1", "query2"])
                # Use chunks for LLM context
    """

    def _init_qdrant_rag(
        self,
        settings,
        collection_name: str = "transcripts",
        embedder_model_name: Optional[str] = None
    ):
        """Initialize Qdrant RAG components"""
        self.qdrant_client = QdrantClient(url=settings.QDRANT_URL)
        self.collection_name = collection_name

        # Initialize embedder for vector search
        model_name = embedder_model_name or settings.EMBEDDING_MODEL_NAME
        self.embedder_model = SentenceTransformer(model_name)

        # Initialize hybrid search engine
        self.hybrid_search = HybridSearchEngine()

        print(f"   ✅ Initialized Qdrant RAG: {collection_name} collection")

    async def retrieve_chunks(
        self,
        transcript_id: str,
        queries: List[str],
        top_k: int = 10,
        use_hybrid: bool = True,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        Retrieve relevant chunks using hybrid search (BM25 + Vector + RRF).

        Args:
            transcript_id: Transcript to query
            queries: List of query strings (e.g., ["client info", "pricing"])
            top_k: Number of chunks to return
            use_hybrid: If True, use hybrid search; if False, vector-only
            metadata_filter: Optional filters (e.g., {"conversation_phase": "pricing"})

        Returns:
            List of chunk texts ranked by relevance
        """
        try:
            if use_hybrid:
                return await self._retrieve_hybrid(transcript_id, queries, top_k, metadata_filter)
            else:
                return await self._retrieve_vector_only(transcript_id, queries, top_k, metadata_filter)
        except Exception as e:
            print(f"   ⚠️ Warning: RAG retrieval failed: {e}")
            return []

    async def _retrieve_hybrid(
        self,
        transcript_id: str,
        queries: List[str],
        top_k: int,
        metadata_filter: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Hybrid search: BM25 + Vector + RRF fusion"""

        # Fetch ALL chunks for this transcript
        all_chunks_results = self.qdrant_client.scroll(
            collection_name=self.collection_name,
            scroll_filter=Filter(
                must=[FieldCondition(key="transcript_id", match=MatchValue(value=transcript_id))]
            ),
            limit=100,
            with_payload=True
        )

        all_chunks = all_chunks_results[0]
        if not all_chunks:
            return []

        # Sort by chunk_index for consistent BM25 indexing
        all_chunks_sorted = sorted(all_chunks, key=lambda x: x.payload.get('chunk_index', 0))
        chunk_payloads = [c.payload for c in all_chunks_sorted]

        # Index in BM25
        self.hybrid_search.index_chunks(chunk_payloads)

        # Multi-query hybrid retrieval
        hybrid_chunk_indices = set()

        for query in queries:
            # Vector search
            query_vector = self.embedder_model.encode(query, show_progress_bar=False).tolist()
            vector_results = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=Filter(
                    must=[FieldCondition(key="transcript_id", match=MatchValue(value=transcript_id))]
                ),
                limit=top_k,
                with_payload=True,
                score_threshold=0.15
            )

            # Format vector results
            vector_results_formatted = [
                (r.payload["chunk_index"], r.score)
                for r in vector_results
            ]

            # Hybrid search with RRF fusion
            fused_indices = self.hybrid_search.hybrid_search(
                query=query,
                vector_results=vector_results_formatted,
                top_k=5,
                bm25_weight=0.4,  # 40% keyword
                vector_weight=0.6  # 60% semantic
            )

            hybrid_chunk_indices.update(fused_indices)

        # Always include header chunk (index 0) for metadata
        hybrid_chunk_indices.add(0)

        # Retrieve full text for selected chunks
        final_chunks = []
        for chunk_idx in sorted(hybrid_chunk_indices)[:top_k]:
            chunk_data = self.hybrid_search.get_chunk_by_index(chunk_idx)
            if chunk_data:
                final_chunks.append(chunk_data["text"])

        return final_chunks

    async def _retrieve_vector_only(
        self,
        transcript_id: str,
        queries: List[str],
        top_k: int,
        metadata_filter: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Vector-only retrieval (fallback if hybrid fails)"""

        all_retrieved_chunks = []
        chunk_ids = set()

        for query in queries:
            query_vector = self.embedder_model.encode(query, show_progress_bar=False).tolist()

            # Build filter
            filter_conditions = [
                FieldCondition(key="transcript_id", match=MatchValue(value=transcript_id))
            ]

            if metadata_filter:
                for key, value in metadata_filter.items():
                    filter_conditions.append(
                        FieldCondition(key=key, match=MatchValue(value=value))
                    )

            results = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=Filter(must=filter_conditions),
                limit=5,
                with_payload=True,
                score_threshold=0.2
            )

            for result in results:
                chunk_id = result.payload.get("chunk_index", -1)
                if chunk_id not in chunk_ids:
                    all_retrieved_chunks.append(result.payload["text"])
                    chunk_ids.add(chunk_id)

        return all_retrieved_chunks[:top_k]

    def get_chunk_count(self, transcript_id: str) -> int:
        """Get total number of chunks for a transcript"""
        try:
            results = self.qdrant_client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[FieldCondition(key="transcript_id", match=MatchValue(value=transcript_id))]
                ),
                limit=1,
                with_payload=False
            )
            return len(results[0]) if results[0] else 0
        except Exception:
            return 0
