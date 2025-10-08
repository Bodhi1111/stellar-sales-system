import json
import requests
from typing import List, Dict, Any
from agents.base_agent import BaseAgent
from config.settings import Settings, settings


class SocialAgent(BaseAgent):
    """
    This agent analyzes transcript chunks to find social media content.
    """

    def __init__(self, settings: Settings):
        super().__init__(settings)
        self.api_url = settings.OLLAMA_API_URL
        self.model_name = settings.LLM_MODEL_NAME

    def _construct_prompt(self, chunks: List[str]) -> str:
        """Constructs a prompt for the LLM to find quotable content."""
        full_text = "\\n---\\n".join(chunks)
        prompt = f"""
        You are a social media expert for a Trust and Estate Planning firm.
        Your task is to analyze the transcript below and identify up to 3 short, powerful, and emotionally resonant quotes or "micro-stories" that could be used as testimonials or marketing content.

        - The quotes should be concise (1-3 sentences).
        - They should highlight a problem, a solution, or a feeling of relief.
        - Extract content directly from the transcript.

        Provide your answer ONLY in JSON format with a single key "social_posts", which is a list of strings. For example: {{"social_posts": ["Quote 1...", "Quote 2..."]}}

        Transcript:
        ---
        {full_text}
        ---

        JSON Output:
        """
        return prompt

    async def run(self, chunks: List[str]) -> Dict[str, Any]:
        print(
            f"📱 SocialAgent received {len(chunks)} chunks. Searching for content...")
        prompt = self._construct_prompt(chunks)
        payload = {"model": self.model_name, "prompt": prompt,
                   "format": "json", "stream": False}

        try:
            response = requests.post(self.api_url, json=payload)
            response.raise_for_status()
            response_data = response.json()
            social_content = json.loads(response_data.get("response", "{}"))

            print(
                f"   LLM successfully found social content: {social_content}")
            return social_content

        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
        except json.JSONDecodeError:
            return {"error": "Invalid JSON response"}
