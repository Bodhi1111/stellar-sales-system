import json
import requests
from typing import Dict, Any
from agents.base_agent import BaseAgent
from config.settings import Settings, settings


class EmailAgent(BaseAgent):
    """
    This agent takes extracted data and drafts a follow-up email.
    """

    def __init__(self, settings: Settings):
        super().__init__(settings)
        self.api_url = settings.OLLAMA_API_URL
        self.model_name = settings.LLM_MODEL_NAME

    def _construct_prompt(self, extracted_data: Dict[str, Any]) -> str:
        """Constructs a prompt for the LLM to draft an email."""
        customer_name = extracted_data.get("customer_name", "Valued Client")
        action_items = extracted_data.get(
            "action_items", "our recent discussion.")

        prompt = f"""
        You are a helpful assistant for a Trust and Estate Planning firm.
        Your task is to draft a brief, professional follow-up email to a potential client.
        The email should be friendly and confirm the next steps based on the provided notes.

        Client Name: {customer_name}
        Action Items from transcript: {action_items}

        Draft the email now.
        """
        return prompt

    async def run(self, extracted_data: Dict[str, Any]) -> str:
        print(f"📧 EmailAgent received data: {extracted_data}")
        prompt = self._construct_prompt(extracted_data)

        payload = {"model": self.model_name, "prompt": prompt, "stream": False}

        try:
            response = requests.post(self.api_url, json=payload)
            response.raise_for_status()

            response_data = response.json()
            email_draft = response_data.get(
                "response", "Could not generate email draft.")

            print(f"   LLM successfully drafted email.")
            return email_draft

        except requests.exceptions.RequestException as e:
            return f"Error: Could not connect to LLM. {e}"
