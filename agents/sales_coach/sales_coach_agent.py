import json
import requests
from typing import List, Dict, Any
from agents.base_agent import BaseAgent
from config.settings import Settings, settings

class SalesCoachAgent(BaseAgent):
    """
    This agent analyzes transcript chunks to provide sales coaching feedback.
    """
    def __init__(self, settings: Settings):
        super().__init__(settings)
        self.api_url = settings.OLLAMA_API_URL
        self.model_name = settings.LLM_MODEL_NAME

    def _construct_prompt(self, chunks: List[str]) -> str:
        """Constructs a prompt for the LLM to provide sales coaching."""
        full_text = "\\n---\\n".join(chunks)
        prompt = f"""
        You are an expert sales coach specializing in value-based selling for high-value services like Trust and Estate Planning.
        Analyze the following sales call transcript and provide concise, actionable feedback.

        1.  **Strengths:** What did the professional do well?
        2.  **Opportunities:** What is one key area for improvement?
        3.  **Suggestion:** Provide one concrete suggestion for next time.

        Provide your answer ONLY in JSON format with the keys "strengths", "opportunities", and "suggestion".

        Transcript:
        ---
        {full_text}
        ---

        JSON Output:
        """
        return prompt

    async def run(self, chunks: List[str]) -> Dict[str, Any]:
        print(f"👨‍🏫 SalesCoachAgent received {len(chunks)} chunks. Analyzing performance...")
        prompt = self._construct_prompt(chunks)
        payload = { "model": self.model_name, "prompt": prompt, "format": "json", "stream": False }

        try:
            response = requests.post(self.api_url, json=payload)
            response.raise_for_status()
            response_data = response.json()
            coaching_feedback = json.loads(response_data.get("response", "{}"))

            print(f"   LLM successfully generated coaching feedback.")
            return coaching_feedback

        except Exception as e:
            return {"error": str(e)}