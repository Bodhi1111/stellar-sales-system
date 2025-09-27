import json
import requests
from typing import List, Dict, Any
from agents.base_agent import BaseAgent
from config.settings import Settings, settings

class StructuringAgent(BaseAgent):
    """
    Analyzes a structured dialogue to identify distinct conversation phases.
    """
    def __init__(self, settings: Settings):
        super().__init__(settings)
        self.api_url = settings.OLLAMA_API_URL
        self.model_name = settings.LLM_MODEL_NAME

    def _format_dialogue_for_prompt(self, dialogue: List[Dict[str, Any]]) -> str:
        """Formats the structured dialogue into a simple text block."""
        return "\\n".join([f"[{turn['timestamp']}] {turn['speaker']}: {turn['text']}" for turn in dialogue])

    def _construct_prompt(self, formatted_dialogue: str) -> str:
        """Constructs a prompt for the LLM to identify conversation phases."""
        phase_list = [
            "greeting", "introduction", "client's motivation for the meeting", "agenda", "about us", 
            "client's goals", "client's estate details", "compare will versus trust", 
            "revocable living trust structure", "additional estate planning documents", 
            "our additional benefits", "comparing price", "closing", "objection/rebuttal", 
            "price negotiation", "scheduling client meeting", "collecting money", "ending meeting"
        ]

        # Using simple string concatenation to build the prompt to avoid formatting errors.
        prompt = "You are an expert meeting analyst. Your task is to segment the following transcript into its logical phases.\n"
        prompt += "Read the entire transcript, which includes timestamps and speakers.\n"
        prompt += "Identify the starting timestamp for each phase of the conversation you find from the provided list.\n\n"
        prompt += "Here is the list of possible phases:\n" + ", ".join(phase_list) + "\n\n"
        prompt += "RULES:\n"
        prompt += "- Only use phases from the provided list.\n"
        prompt += "- Associate each identified phase with the timestamp where it begins.\n"
        prompt += "- It is okay if not all phases are present in every transcript.\n\n"
        prompt += "Provide your answer ONLY in JSON format, as a list of objects, where each object has a \"phase\" and a \"start_timestamp\".\n"
        prompt += "Example Format:\n"
        prompt += '[\\n  {"phase": "greeting", "start_timestamp": "00:00:05"},\\n  {"phase": "agenda", "start_timestamp": "00:02:15"}\\n]\\n\\n'
        prompt += "Transcript:\\n---\\n"
        prompt += formatted_dialogue
        prompt += "\\n---\\n\\nJSON Output:"

        return prompt

    async def run(self, structured_dialogue: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        print("🏗️ StructuringAgent received dialogue. Identifying phases...")
        formatted_dialogue = self._format_dialogue_for_prompt(structured_dialogue)
        prompt = self._construct_prompt(formatted_dialogue)
        payload = { "model": self.model_name, "prompt": prompt, "format": "json", "stream": False }

        try:
            response = requests.post(self.api_url, json=payload)
            response.raise_for_status()
            response_data = response.json()
            phases = json.loads(response_data.get("response", "[]"))
            print(f"   Successfully identified {len(phases)} phases.")
            return phases
        except Exception as e:
            print(f"   ❌ ERROR: An unexpected error occurred during phase identification: {e}")
            return []