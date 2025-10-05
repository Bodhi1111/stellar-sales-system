"""
GatekeeperAgent: Checks for query ambiguity and requests clarification if needed.
Enhanced with LLMClient for robust error handling and DeepSeek-Coder optimization.
"""
from typing import Dict, Any

from agents.base_agent import BaseAgent
from config.settings import Settings
from core.llm_client import LLMClient


class GatekeeperAgent(BaseAgent):
    """
    Checks if a user's request is specific enough to be answered,
    or if it's too ambiguous and requires clarification.

    Acts as a "guard rail" to prevent the system from attempting to answer
    poorly-defined queries, mimicking how an expert human would ask for
    clarification before starting complex work.
    """

    def __init__(self, settings: Settings):
        super().__init__(settings)
        self.llm_client = LLMClient(settings, timeout=60, max_retries=2)

    async def run(self, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyzes a user request for ambiguity.

        Args:
            data: Dict containing:
                - original_request: The user's original query

        Returns:
            Dict with key "clarification_question":
            - None if request is specific enough
            - A clarifying question string if request is ambiguous
        """
        print("🧐 GatekeeperAgent: Checking for ambiguity...")

        # Extract request from data dict
        if not data or 'original_request' not in data:
            return {"clarification_question": "Error: No request provided."}

        request = data['original_request']

        # Escape quotes to prevent prompt injection
        safe_request = request.replace('"', '\\"')

        # Optimized prompt for DeepSeek-Coder with clear structure
        prompt = f"""TASK: Determine if a sales analysis request is specific or ambiguous

RULES:
- SPECIFIC request: asks for a number, date, named entity, client name, or comparison
  Examples: "How many deals closed in Q4?", "What is John Doe's estate value?", "Show me Robin's objections"
- AMBIGUOUS request: open-ended, vague, or missing critical details
  Examples: "How are sales going?", "Tell me about clients", "What's happening?"

INSTRUCTIONS:
1. Read the user request below
2. If SPECIFIC: respond with only the word "OK"
3. If AMBIGUOUS: generate ONE polite clarifying question

USER REQUEST: "{safe_request}"

RESPONSE:"""

        result = self.llm_client.generate(
            prompt=prompt,
            format_json=False,
            timeout=60
        )

        if not result["success"]:
            print(f"   ❌ LLM call failed: {result['error']}")
            # Fail open: assume request is OK to not block pipeline
            return {"clarification_question": None}

        llm_response = result["response"].strip()

        # Case-insensitive check for "OK"
        if llm_response.upper() == "OK":
            print("   ✅ Request is specific. Proceeding.")
            return {"clarification_question": None}
        else:
            print(f"   ⚠️ Request is ambiguous. Clarification needed.")
            print(f"      Question: {llm_response}")
            return {"clarification_question": llm_response}
