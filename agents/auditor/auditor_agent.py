"""
AuditorAgent: Verifies specialist tool outputs for quality and relevance.
Enhanced with LLMClient, Pydantic validation, and DeepSeek-Coder optimization.
"""
import json
from typing import Dict, Any
from pydantic import BaseModel, Field, ValidationError

from agents.base_agent import BaseAgent
from config.settings import Settings
from core.llm_client import LLMClient


class VerificationResult(BaseModel):
    """Structured output for the Auditor's verification."""
    confidence_score: int = Field(
        description="Score from 1-5 on confidence in the tool output",
        ge=1,
        le=5
    )
    reasoning: str = Field(
        description="Brief reasoning for the confidence score"
    )


class AuditorAgent(BaseAgent):
    """
    Audits specialist tool outputs against the original request to ensure
    relevance and quality. Enables self-correction through verification scores.

    Acts as a "skeptic" providing critical second opinion on all tool outputs,
    preventing the system from blindly trusting potentially low-quality responses.
    """

    def __init__(self, settings: Settings):
        super().__init__(settings)
        self.llm_client = LLMClient(settings, timeout=75, max_retries=2)

    async def run(self, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Audits a tool's output for quality and relevance.

        Args:
            data: Dict containing:
                - original_request: User's query
                - last_step: Dict with 'tool_name' and 'tool_output'

        Returns:
            Dict with:
                - confidence_score: int (1-5)
                - reasoning: str
        """
        print("🕵️ AuditorAgent: Verifying tool output...")

        # Input validation
        if not data or 'original_request' not in data or 'last_step' not in data:
            return {
                "confidence_score": 1,
                "reasoning": "Missing required input data for audit."
            }

        original_request = data['original_request']
        last_step = data['last_step']
        tool_name = last_step.get('tool_name', 'Unknown Tool')
        tool_output = last_step.get('tool_output', 'No output')

        # Safely serialize tool output for the prompt
        try:
            tool_output_str = json.dumps(
                tool_output, ensure_ascii=False, indent=2)
        except Exception:
            tool_output_str = str(tool_output)

        # Truncate if too long
        if len(tool_output_str) > 2000:
            tool_output_str = tool_output_str[:2000] + "\n... (truncated)"

        # Optimized prompt for DeepSeek-Coder with explicit JSON schema
        prompt = f"""TASK: Audit a specialist tool's output for quality and relevance

USER'S ORIGINAL REQUEST:
"{original_request}"

TOOL CALLED:
{tool_name}

TOOL'S OUTPUT:
---
{tool_output_str}
---

AUDIT CHECKLIST:
1. RELEVANCE: Is this output directly relevant and helpful for the user's request?
2. ACCURACY: Does the output appear factually consistent and logical?
3. COMPLETENESS: Does it adequately address the request?

INSTRUCTIONS:
Provide a confidence score from 1 (poor/irrelevant) to 5 (excellent/highly relevant).

OUTPUT (valid JSON only):
{{
  "confidence_score": <1-5>,
  "reasoning": "Brief explanation for the score"
}}"""

        result = self.llm_client.generate_json(
            prompt=prompt,
            timeout=75
        )

        if not result["success"]:
            print(f"   ❌ LLM call failed: {result['error']}")
            return {
                "confidence_score": 2,
                "reasoning": f"Audit request failed: {result['error']}"
            }

        try:
            # Validate using Pydantic model
            verification = VerificationResult(**result["data"])
            print(f"   ✅ Audit Score: {verification.confidence_score}/5")
            print(f"      Reasoning: {verification.reasoning}")
            return verification.dict()

        except ValidationError as e:
            print(f"   ❌ Validation error: {e}")
            return {
                "confidence_score": 2,
                "reasoning": f"Audit response validation failed: {e}"
            }
