"""
Query Router - Intent Classification and Execution Planning

Routes queries to optimal retrieval strategies based on intent classification.
"""

from enum import Enum
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
import re


class QueryIntent(Enum):
    """Query intent types for routing"""
    FACT_LOOKUP = "fact_lookup"          # "What was the deal amount?"
    ENTITY_SEARCH = "entity_search"      # "Find meetings with John Doe"
    CONTEXT_QUESTION = "context"         # "Why did the client object?"
    COMPARISON = "comparison"            # "Compare Q1 vs Q2 performance"
    AGGREGATION = "aggregation"          # "What are common objections?"
    TEMPORAL = "temporal"                # "What happened in the last meeting?"


class QueryPlan(BaseModel):
    """Execution plan for a query"""
    intent: QueryIntent
    collections: List[str]
    retrieval_strategy: str
    top_k: int
    filters: Dict[str, Any]
    rerank: bool
    use_cache: bool
    metadata_boosts: Optional[Dict[str, Dict[str, float]]] = None


class QueryRouter:
    """
    Routes queries to optimal retrieval strategies based on intent.
    
    Example:
        router = QueryRouter()
        plan = await router.route("What was the deal amount?")
        # plan.intent = FACT_LOOKUP
        # plan.collections = ["chunks_detailed", "entities"]
        # plan.retrieval_strategy = "hybrid_keyword_heavy"
    """
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        self._init_intent_patterns()
    
    def _init_intent_patterns(self):
        """Initialize regex patterns for intent classification"""
        self.intent_patterns = {
            QueryIntent.FACT_LOOKUP: [
                r'what (is|was|were)',
                r'how much',
                r'how many',
                r'when (did|was)',
                r'who (is|was)',
                r'(price|cost|amount|fee)',
            ],
            QueryIntent.ENTITY_SEARCH: [
                r'find (meetings?|clients?|deals?)',
                r'show me (all|the)',
                r'list (all|the)',
                r'search for',
            ],
            QueryIntent.CONTEXT_QUESTION: [
                r'why (did|was)',
                r'how (did|was)',
                r'explain',
                r'describe',
                r'tell me about',
            ],
            QueryIntent.COMPARISON: [
                r'compare',
                r'difference between',
                r'vs',
                r'versus',
                r'better than',
            ],
            QueryIntent.AGGREGATION: [
                r'summarize',
                r'what are (the )?(main|common|top)',
                r'overview',
                r'trends',
                r'patterns',
            ],
            QueryIntent.TEMPORAL: [
                r'last (week|month|meeting)',
                r'recent',
                r'latest',
                r'history',
                r'timeline',
            ],
        }
    
    async def route(self, query: str, context: Dict = None) -> QueryPlan:
        """
        Analyze query and create execution plan.
        
        Args:
            query: User query string
            context: Optional context (transcript_id, user_role, etc.)
        
        Returns:
            QueryPlan with intent, collections, strategy, etc.
        """
        query_lower = query.lower()
        context = context or {}
        
        # Step 1: Classify intent
        intent = self._classify_intent(query_lower)
        
        # Step 2: Extract entities/filters from query
        filters = self._extract_filters(query_lower, context)
        
        # Step 3: Select collections based on intent
        collections = self._select_collections(intent, filters)
        
        # Step 4: Choose retrieval strategy
        strategy = self._select_strategy(intent)
        
        # Step 5: Determine top_k
        top_k = self._determine_top_k(intent, len(collections))
        
        # Step 6: Determine if reranking is needed
        rerank = self._should_rerank(intent)
        
        # Step 7: Check if caching is beneficial
        use_cache = self._should_cache(intent)
        
        # Step 8: Get metadata boosts
        metadata_boosts = self._get_metadata_boosts(intent, query_lower)
        
        return QueryPlan(
            intent=intent,
            collections=collections,
            retrieval_strategy=strategy,
            top_k=top_k,
            filters=filters,
            rerank=rerank,
            use_cache=use_cache,
            metadata_boosts=metadata_boosts
        )
    
    def _classify_intent(self, query: str) -> QueryIntent:
        """
        Classify query intent using pattern matching.
        
        Fallback to CONTEXT_QUESTION if no patterns match.
        """
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query):
                    return intent
        
        # Default fallback
        return QueryIntent.CONTEXT_QUESTION
    
    def _extract_filters(self, query: str, context: Dict) -> Dict[str, Any]:
        """
        Extract filters from query and context.
        
        Examples:
            "meetings with John" → {"entities_mentioned": ["John"]}
            "last week" → {"meeting_date": {"gte": "2025-10-17"}}
            "pricing objections" → {"conversation_phase": "Pricing", "contains_objection": True}
        """
        filters = {}
        
        # Add transcript_id from context if available
        if "transcript_id" in context:
            filters["transcript_id"] = context["transcript_id"]
        
        # Extract conversation phase
        phases = ["greeting", "discovery", "pricing", "objection", "closing"]
        for phase in phases:
            if phase in query:
                filters["conversation_phase"] = phase.capitalize()
        
        # Extract speaker role
        if "client" in query:
            filters["speaker_role"] = "Client"
        elif "agent" in query:
            filters["speaker_role"] = "Agent"
        
        # Detect pricing-related
        if any(kw in query for kw in ["price", "cost", "fee", "$", "dollar"]):
            filters["contains_pricing"] = True
        
        # Detect objection-related
        if any(kw in query for kw in ["objection", "concern", "pushback", "hesitant"]):
            filters["contains_objection"] = True
        
        # Extract sentiment
        if any(kw in query for kw in ["positive", "happy", "excited"]):
            filters["sentiment"] = {"gte": 0.3}
        elif any(kw in query for kw in ["negative", "unhappy", "frustrated"]):
            filters["sentiment"] = {"lte": -0.3}
        
        return filters
    
    def _select_collections(self, intent: QueryIntent, filters: Dict) -> List[str]:
        """Select which collections to query based on intent"""
        collection_map = {
            QueryIntent.FACT_LOOKUP: ["chunks_detailed", "entities"],
            QueryIntent.ENTITY_SEARCH: ["entities", "summaries"],
            QueryIntent.CONTEXT_QUESTION: ["chunks_contextual", "chunks_detailed"],
            QueryIntent.COMPARISON: ["summaries", "chunks_contextual"],
            QueryIntent.AGGREGATION: ["summaries", "chunks_contextual"],
            QueryIntent.TEMPORAL: ["chunks_contextual", "summaries"],
        }
        return collection_map.get(intent, ["chunks_contextual"])
    
    def _select_strategy(self, intent: QueryIntent) -> str:
        """Select retrieval strategy based on intent"""
        strategy_map = {
            QueryIntent.FACT_LOOKUP: "hybrid_keyword_heavy",      # 70% BM25, 30% vector
            QueryIntent.ENTITY_SEARCH: "structured_filter_first", # Filter then rank
            QueryIntent.CONTEXT_QUESTION: "dense_semantic",       # 100% vector
            QueryIntent.COMPARISON: "multi_query_fusion",         # Parallel queries
            QueryIntent.AGGREGATION: "hierarchical_summary",      # Top-down retrieval
            QueryIntent.TEMPORAL: "time_aware_window",           # Sliding window
        }
        return strategy_map.get(intent, "hybrid_balanced")
    
    def _determine_top_k(self, intent: QueryIntent, num_collections: int) -> int:
        """Determine how many results to retrieve"""
        base_k = {
            QueryIntent.FACT_LOOKUP: 5,
            QueryIntent.ENTITY_SEARCH: 10,
            QueryIntent.CONTEXT_QUESTION: 8,
            QueryIntent.COMPARISON: 15,
            QueryIntent.AGGREGATION: 20,
            QueryIntent.TEMPORAL: 12,
        }
        return base_k.get(intent, 10)
    
    def _should_rerank(self, intent: QueryIntent) -> bool:
        """Determine if reranking is beneficial for this intent"""
        # Rerank for context-heavy queries
        return intent in [
            QueryIntent.CONTEXT_QUESTION,
            QueryIntent.COMPARISON,
            QueryIntent.AGGREGATION
        ]
    
    def _should_cache(self, intent: QueryIntent) -> bool:
        """Determine if caching is beneficial for this intent"""
        # Cache fact lookups and entity searches (deterministic)
        return intent in [
            QueryIntent.FACT_LOOKUP,
            QueryIntent.ENTITY_SEARCH
        ]
    
    def _get_metadata_boosts(self, intent: QueryIntent, query: str) -> Optional[Dict]:
        """Get metadata-based score boosts for reranking"""
        if intent == QueryIntent.FACT_LOOKUP:
            # Boost chunks with pricing info if query mentions pricing
            if any(kw in query for kw in ["price", "cost", "fee"]):
                return {
                    "conversation_phase": {"Pricing": 1.5},
                    "contains_pricing": {True: 1.3}
                }
        
        elif intent == QueryIntent.CONTEXT_QUESTION:
            # Boost client responses
            return {
                "speaker_role": {"Client": 1.2}
            }
        
        return None
