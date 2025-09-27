import json
import requests
from typing import List, Dict, Any

from agents.base_agent import BaseAgent
from config.settings import Settings, settings
from core.database.qdrant import qdrant_manager

class SalesCopilotAgent(BaseAgent):
    """
    This agent answers questions by performing RAG over all saved transcripts.
    """
    def __init__(self, settings: Settings):
        super().__init__(settings)
        self.api_url = settings.OLLAMA_API_URL
        self.model_name = settings.LLM_MODEL_NAME

    def _get_historical_context(self, query: str) -> str:
        """Searches Qdrant for historical context related to the user's query."""
        print(f"   Searching Qdrant for context related to: '{query}'")
        search_results = qdrant_manager.search(query=query, limit=5)

        context = "\\n---\\n".join([result.payload['text'] for result in search_results])
        return context

    def _construct_prompt(self, query: str, context: str) -> str:
        """Constructs a prompt for the LLM to answer a question with context."""
        prompt = f"""
        You are an expert sales copilot. Based ONLY on the provided Context from past sales calls, answer the User's Question.
        If the context is empty or does not contain the answer, say 'I could not find an answer in the transcripts.'

        Context:
        ---
        {context}
        ---
        User's Question: {query}

        Answer:
        """
        return prompt

    async def run(self, query: str) -> str:
        print(f"🤖 SalesCopilotAgent received query: '{query}'")

        # 1. Retrieve historical context
        context = self._get_historical_context(query)

        # 2. Construct the prompt
        prompt = self._construct_prompt(query, context)

        # 3. Call the LLM
        payload = {"model": self.model_name, "prompt": prompt, "stream": False}

        try:
            response = requests.post(self.api_url, json=payload)
            response.raise_for_status()
            final_answer = response.json().get("response", "Error: No response from LLM.").strip()
        except Exception as e:
            final_answer = f"Error communicating with LLM: {e}"

        print(f"   Generated final answer.")
        return final_answer