import json
import requests
from typing import List, Dict, Any
from agents.base_agent import BaseAgent
from config.settings import settings

class ExtractorAgent(BaseAgent):
    """
    This agent takes text chunks and uses an LLM to extract information.
    """
    def __init__(self, settings):
        super().__init__(settings)
        self.api_url = settings.OLLAMA_API_URL
        self.model_name = settings.LLM_MODEL_NAME

    def _construct_prompt(self, chunks: List[str]) -> str:
        """Constructs a prompt for the LLM from the text chunks."""
        full_text = "\\n---\\n".join(chunks)
        prompt = f"""
        You are an expert sales analyst. Read the following sales call transcript and extract the specified information.
        Provide your answer ONLY in JSON format with the following keys: "customer_name", "main_objection", "action_items".

        Transcript:
        ---
        {full_text}
        ---

        JSON Output:
        """
        return prompt

    async def run(self, chunks: List[str]) -> Dict[str, Any]:
        print(f"🕵️ ExtractorAgent received {len(chunks)} chunks. Contacting LLM...")

        prompt = self._construct_prompt(chunks)

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "format": "json", # Ask Ollama to guarantee JSON output
            "stream": False
        }

        try:
            # Send the prompt to the Ollama API
            response = requests.post(self.api_url, json=payload)
            response.raise_for_status() # Raise an exception for bad status codes

            # The response from Ollama is a JSON string, so we parse it twice
            response_data = response.json()
            extracted_data = json.loads(response_data.get("response", "{}"))

            print(f"   LLM successfully extracted data: {extracted_data}")
            return extracted_data

        except requests.exceptions.RequestException as e:
            print(f"   ❌ ERROR: Could not connect to Ollama API: {e}")
            return {"error": str(e)}
        except json.JSONDecodeError:
            print(f"   ❌ ERROR: Failed to parse JSON response from LLM.")
            return {"error": "Invalid JSON response"}