"""
StrategistAgent: Synthesizes final answers from intermediate steps.
Enhanced with LLMClient, context truncation, and DeepSeek-Coder optimization.
"""
from typing import Dict, Any, List

from agents.base_agent import BaseAgent
from config.settings import Settings
from core.llm_client import LLMClient


class StrategistAgent(BaseAgent):
    """
    The synthesis expert that connects disparate facts into coherent insights.

    Takes the intermediate steps from tool executions and weaves them together
    into a comprehensive, well-reasoned final answer to the user's original request.
    Acts as the "synthesis layer" that prevents disjointed, fragmented responses.
    """

    def __init__(self, settings: Settings):
        super().__init__(settings)
        self.llm_client = LLMClient(settings, timeout=120, max_retries=2)
        self.max_context_chars = 8000  # Prevent prompt overflow

    def _build_context_from_steps(self, steps: List[Dict[str, Any]]) -> str:
        """
        Builds a condensed context string from intermediate steps.
        Implements smart truncation to stay within token limits.

        Args:
            steps: List of dicts with 'tool_name' and 'tool_output'

        Returns:
            Formatted context string, truncated if necessary
        """
        context_parts = []
        total_chars = 0

        for i, step in enumerate(steps, 1):
            tool_name = step.get('tool_name', 'Unknown Tool')
            tool_output = step.get('tool_output', 'No output')

            # Convert output to string safely
            if isinstance(tool_output, dict):
                output_str = str(tool_output)
            elif isinstance(tool_output, str):
                output_str = tool_output
            else:
                output_str = str(tool_output)

            # Build step summary
            step_summary = f"STEP {i} - {tool_name}:\n{output_str}\n"
            step_chars = len(step_summary)

            # Check if adding this step would exceed limit
            if total_chars + step_chars > self.max_context_chars:
                remaining = self.max_context_chars - total_chars
                if remaining > 100:  # Only add if meaningful space left
                    truncated = output_str[:remaining - 50] + "... (truncated)"
                    context_parts.append(
                        f"STEP {i} - {tool_name}:\n{truncated}\n")
                break

            context_parts.append(step_summary)
            total_chars += step_chars

        return "\n".join(context_parts)

    async def run(self, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Synthesizes a final answer from intermediate tool execution steps.

        Args:
            data: Dict containing:
                - original_request: User's original query
                - intermediate_steps: List of tool execution results

        Returns:
            Dict with key "final_response": str (comprehensive answer)
        """
        print("🧠 StrategistAgent: Synthesizing final response...")

        # Input validation
        if not data or 'original_request' not in data or 'intermediate_steps' not in data:
            return {
                "final_response": "Error: Missing required data for synthesis (original_request or intermediate_steps)."
            }

        original_request = data['original_request']
        intermediate_steps = data['intermediate_steps']

        # Handle empty steps
        if not intermediate_steps:
            return {
                "final_response": f"I couldn't gather enough information to answer: {original_request}"
            }

        # Build context from steps with smart truncation
        context = self._build_context_from_steps(intermediate_steps)

        # DeepSeek-Coder optimized synthesis prompt
        prompt = f"""TASK: Synthesize a comprehensive answer from gathered information

USER'S ORIGINAL REQUEST:
"{original_request}"

INFORMATION GATHERED:
---
{context}
---

INSTRUCTIONS:
1. Analyze all the information gathered from the tools above
2. Connect the facts into a coherent narrative
3. Directly answer the user's original request
4. Be specific and cite relevant details from the gathered information
5. If information is incomplete, acknowledge what's missing
6. Keep the answer concise but complete (2-4 paragraphs max)

FINAL ANSWER:"""

        result = self.llm_client.generate(
            prompt=prompt,
            format_json=False,
            timeout=120
        )

        if not result["success"]:
            print(f"   ❌ LLM call failed: {result['error']}")
            return {
                "final_response": f"Error during synthesis: {result['error']}"
            }

        final_response = result["response"].strip()
        print(f"   ✅ Synthesized response ({len(final_response)} chars)")

        return {"final_response": final_response}
