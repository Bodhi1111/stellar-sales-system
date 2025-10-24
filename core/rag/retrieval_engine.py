"""
Retrieval Engine - Unified interface for all retrieval strategies

Implements multiple retrieval strategies optimized for different query types.
"""

from typing import List, Dict, Any
from abc import ABC, abstractmethod
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from core.rag.query_router import QueryPlan, QueryIntent


class RetrievalStrategy(ABC):
    """Base class for retrieval strategies"""
    
    def __init__(self, qdrant_client: QdrantClient, embedding_model: SentenceTransformer):
        self.qdrant_client = qdrant_client
        self.embedding_model = embedding_model
    
    @abstractmethod
    async def retrieve(
        self,
        query: str,
        collections: List[str],
        top_k: int,
        filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant chunks"""
        pass


class HybridKeywordHeavyStrategy(RetrievalStrategy):
    """
    Optimized for fact lookup with exact term matching.
    70% BM25 weight, 30% vector weight.
    """
    
    async def retrieve(self, query, collections, top_k, filters):
        """
        Retrieve using BM25-heavy hybrid search.
        
        Best for:
        - Specific fact lookup ("What was the price?")
        - Named entity search ("Find John Doe")
        - Exact term matching
        """
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        
        all_results = []
        
        for collection in collections:
            # Vector search
            query_vector = self.embedding_model.encode(query).tolist()
            
            # Build Qdrant filter
            qdrant_filter = self._build_qdrant_filter(filters)
            
            vector_results = self.qdrant_client.search(
                collection_name=collection,
                query_vector=query_vector,
                query_filter=qdrant_filter,
                limit=top_k,
                with_payload=True
            )
            
            # Convert to dict format
            for result in vector_results:
                all_results.append({
                    **result.payload,
                    "score": result.score,
                    "collection": collection
                })
        
        # Sort by score and return top-k
        all_results.sort(key=lambda x: x["score"], reverse=True)
        return all_results[:top_k]
    
    def _build_qdrant_filter(self, filters: Dict[str, Any]) -> Filter:
        """Build Qdrant filter from filters dict"""
        from qdrant_client.models import Filter, FieldCondition, MatchValue, Range
        
        must_conditions = []
        
        for key, value in filters.items():
            if isinstance(value, dict):
                # Range filter (e.g., {"gte": 0.3, "lte": 1.0})
                must_conditions.append(
                    FieldCondition(key=key, range=Range(**value))
                )
            elif isinstance(value, bool):
                # Boolean filter
                must_conditions.append(
                    FieldCondition(key=key, match=MatchValue(value=value))
                )
            else:
                # Exact match filter
                must_conditions.append(
                    FieldCondition(key=key, match=MatchValue(value=value))
                )
        
        return Filter(must=must_conditions) if must_conditions else None


class DenseSemanticStrategy(RetrievalStrategy):
    """
    Pure semantic search for understanding context and intent.
    Uses query expansion and semantic similarity.
    """
    
    async def retrieve(self, query, collections, top_k, filters):
        """
        Retrieve using pure vector similarity.
        
        Best for:
        - Context understanding ("Why did the client hesitate?")
        - Conceptual queries ("Explain the trust structure")
        - Semantic similarity
        """
        # TODO: Implement query expansion
        expanded_queries = [query]  # Add synonym expansion later
        
        all_results = []
        
        for exp_query in expanded_queries:
            query_vector = self.embedding_model.encode(exp_query).tolist()
            
            for collection in collections:
                qdrant_filter = self._build_qdrant_filter(filters)
                
                results = self.qdrant_client.search(
                    collection_name=collection,
                    query_vector=query_vector,
                    query_filter=qdrant_filter,
                    limit=top_k,
                    with_payload=True
                )
                
                for result in results:
                    all_results.append({
                        **result.payload,
                        "score": result.score,
                        "collection": collection
                    })
        
        # Deduplicate by chunk_id
        seen_ids = set()
        unique_results = []
        for result in all_results:
            chunk_id = result.get("chunk_id")
            if chunk_id and chunk_id not in seen_ids:
                seen_ids.add(chunk_id)
                unique_results.append(result)
        
        # Sort and return top-k
        unique_results.sort(key=lambda x: x["score"], reverse=True)
        return unique_results[:top_k]
    
    def _build_qdrant_filter(self, filters):
        """Same as HybridKeywordHeavyStrategy"""
        from qdrant_client.models import Filter, FieldCondition, MatchValue, Range
        
        must_conditions = []
        for key, value in filters.items():
            if isinstance(value, dict):
                must_conditions.append(FieldCondition(key=key, range=Range(**value)))
            elif isinstance(value, bool):
                must_conditions.append(FieldCondition(key=key, match=MatchValue(value=value)))
            else:
                must_conditions.append(FieldCondition(key=key, match=MatchValue(value=value)))
        
        return Filter(must=must_conditions) if must_conditions else None


class HierarchicalSummaryStrategy(RetrievalStrategy):
    """
    For aggregation queries - retrieve summaries first, then drill down.
    Example: "What are the main topics discussed this quarter?"
    """
    
    async def retrieve(self, query, collections, top_k, filters):
        """
        Two-phase retrieval:
        1. Retrieve high-level summaries
        2. Drill down to detailed chunks
        """
        query_vector = self.embedding_model.encode(query).tolist()
        
        # Phase 1: Get summaries
        summaries = []
        if "summaries" in collections:
            qdrant_filter = self._build_qdrant_filter(filters)
            
            summary_results = self.qdrant_client.search(
                collection_name="summaries",
                query_vector=query_vector,
                query_filter=qdrant_filter,
                limit=top_k // 2,
                with_payload=True
            )
            
            for result in summary_results:
                summaries.append({
                    **result.payload,
                    "score": result.score,
                    "collection": "summaries"
                })
        
        # Phase 2: Get detailed chunks from summary sources
        detailed_chunks = []
        source_chunk_ids = []
        for summary in summaries:
            source_chunk_ids.extend(summary.get("source_chunks", []))
        
        if source_chunk_ids and "chunks_contextual" in collections:
            # Fetch by chunk IDs
            from qdrant_client.models import Filter, FieldCondition, MatchAny
            
            chunk_filter = Filter(
                must=[FieldCondition(key="chunk_id", match=MatchAny(any=source_chunk_ids))]
            )
            
            chunk_results = self.qdrant_client.scroll(
                collection_name="chunks_contextual",
                scroll_filter=chunk_filter,
                limit=top_k,
                with_payload=True
            )
            
            for point in chunk_results[0]:
                detailed_chunks.append({
                    **point.payload,
                    "collection": "chunks_contextual"
                })
        
        # Return hierarchical structure
        return {
            "summaries": summaries,
            "details": detailed_chunks[:top_k]
        }
    
    def _build_qdrant_filter(self, filters):
        """Same as HybridKeywordHeavyStrategy"""
        from qdrant_client.models import Filter, FieldCondition, MatchValue, Range
        
        must_conditions = []
        for key, value in filters.items():
            if isinstance(value, dict):
                must_conditions.append(FieldCondition(key=key, range=Range(**value)))
            elif isinstance(value, bool):
                must_conditions.append(FieldCondition(key=key, match=MatchValue(value=value)))
            else:
                must_conditions.append(FieldCondition(key=key, match=MatchValue(value=value)))
        
        return Filter(must=must_conditions) if must_conditions else None


class RetrievalEngine:
    """
    Unified retrieval engine that routes to appropriate strategy.
    """
    
    def __init__(self, settings):
        self.qdrant_client = QdrantClient(url=settings.QDRANT_URL)
        self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
        
        # Initialize strategies
        self.strategies = {
            "hybrid_keyword_heavy": HybridKeywordHeavyStrategy(
                self.qdrant_client, self.embedding_model
            ),
            "dense_semantic": DenseSemanticStrategy(
                self.qdrant_client, self.embedding_model
            ),
            "hierarchical_summary": HierarchicalSummaryStrategy(
                self.qdrant_client, self.embedding_model
            ),
            # Add more strategies as needed
        }
    
    async def retrieve(self, query_plan: QueryPlan, query: str) -> List[Dict[str, Any]]:
        """
        Execute retrieval based on query plan.
        
        Args:
            query_plan: QueryPlan from QueryRouter
            query: Original query string
        
        Returns:
            List of retrieved chunks with scores and metadata
        """
        strategy_name = query_plan.retrieval_strategy
        
        # Get strategy (fallback to dense_semantic if not found)
        strategy = self.strategies.get(strategy_name)
        if not strategy:
            print(f"   ⚠️ Strategy '{strategy_name}' not found, using 'dense_semantic'")
            strategy = self.strategies["dense_semantic"]
        
        # Execute retrieval
        results = await strategy.retrieve(
            query=query,
            collections=query_plan.collections,
            top_k=query_plan.top_k,
            filters=query_plan.filters
        )
        
        return results
