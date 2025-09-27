import json
import requests
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import semantic_search

from agents.base_agent import BaseAgent
from config.settings import Settings, settings

class ExtractorAgent(BaseAgent):
    """
    This agent uses a two-step "Local RAG" process to extract information.
    """
    def __init__(self, settings: Settings):
        super().__init__(settings)
        self.api_url = settings.OLLAMA_API_URL
        self.model_name = settings.LLM_MODEL_NAME
        # This agent now needs its own embedding model for in-memory search
        self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)

    def _get_relevant_context(self, query: str, chunks: List[str], top_k: int = 2) -> str:
        """Performs in-memory semantic search to find the most relevant chunks."""
        query_embedding = self.embedding_model.encode(query)
        chunk_embeddings = self.embedding_model.encode(chunks)

        hits = semantic_search(query_embedding, chunk_embeddings, top_k=top_k)
        # We take the first list of hits for our single query
        context_chunks = [chunks[hit['corpus_id']] for hit in hits[0]]
        return "\\n---\\n".join(context_chunks)

    async def run(self, chunks: List[str]) -> Dict[str, Any]:
        print(f"🕵️ ExtractorAgent starting enriched extraction on {len(chunks)} chunks...")

        questions = {
            "customer_name": "What is the customer's full name?",
            "main_objection": "What is the customer's main objection or primary concern?",
            "action_items": "What are the specific next steps or action items discussed?"
        }

        extracted_data = {}

        for key, question in questions.items():
            print(f"   -> Finding context for: '{key}'")
            context = self._get_relevant_context(question, chunks)

            prompt = f"""Based ONLY on the following Context, answer the Question. If the context does not contain the answer, say 'Not found in context'.
            Context:
            ---
            {context}
            ---
            Question: {question}
            Answer:"""

            payload = {"model": self.model_name, "prompt": prompt, "stream": False}

            try:
                response = requests.post(self.api_url, json=payload)
                response.raise_for_status()
                answer = response.json().get("response", "").strip()
                extracted_data[key] = answer
            except Exception:
                extracted_data[key] = "Error during extraction."

        print(f"   Enriched extraction complete: {extracted_data}")
        return extracted_data