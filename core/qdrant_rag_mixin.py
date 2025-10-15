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
        """
        Hybrid search with Parent-Child retrieval:
        1. Search child chunks (speaker turns) via BM25 + Vector
        2. Fetch parent chunks (phase segments) for matched children
        3. Return parent context for LLM
        """

        matched_child_chunks = []

        # Multi-query vector search on CHILD CHUNKS only
        for query in queries:
            query_vector = self.embedder_model.encode(query, show_progress_bar=False).tolist()

            # Search only embedded chunks (child chunks)
            vector_results = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=Filter(
                    must=[
                        FieldCondition(key="transcript_id", match=MatchValue(value=transcript_id)),
                        FieldCondition(key="is_embedded", match=MatchValue(value=True))  # Only child chunks
                    ]
                ),
                limit=top_k,
                with_payload=True,
                score_threshold=0.15
            )

            matched_child_chunks.extend(vector_results)

        if not matched_child_chunks:
            print(f"   ℹ️ No child chunks matched for queries")
            return []

        # Get unique parent_ids from matched children
        parent_ids = set()
        for result in matched_child_chunks:
            parent_id = result.payload.get("parent_id")
            if parent_id:
                parent_ids.add(parent_id)

        print(f"   ✅ Found {len(matched_child_chunks)} child chunks")
        print(f"   🔗 Fetching {len(parent_ids)} parent chunks for context")

        # Fetch parent chunks by chunk_id
        parent_chunks = []
        for parent_id in parent_ids:
            try:
                # Retrieve parent by chunk_id
                parent_results = self.qdrant_client.scroll(
                    collection_name=self.collection_name,
                    scroll_filter=Filter(
                        must=[FieldCondition(key="chunk_id", match=MatchValue(value=parent_id))]
                    ),
                    limit=1,
                    with_payload=True
                )

                if parent_results[0]:
                    parent_chunks.append(parent_results[0][0])

            except Exception as e:
                print(f"   ⚠️ Warning: Could not fetch parent {parent_id}: {e}")
                continue

        # Return parent chunk texts (broader context for LLM)
        final_chunks = []

        # Always include header for metadata context
        try:
            header_results = self.qdrant_client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(key="transcript_id", match=MatchValue(value=transcript_id)),
                        FieldCondition(key="chunk_type", match=MatchValue(value="header"))
                    ]
                ),
                limit=1,
                with_payload=True
            )
            if header_results[0]:
                final_chunks.append(header_results[0][0].payload["text"])
        except Exception:
            pass

        # Add parent chunks (conversation phase segments)
        for parent in parent_chunks[:top_k]:
            final_chunks.append(parent.payload["text"])

        print(f"   📄 Returning {len(final_chunks)} chunks (1 header + {len(final_chunks)-1} parents)")

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
