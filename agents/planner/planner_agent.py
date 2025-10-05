"""
PlannerAgent: Creates step-by-step execution plans using specialist agents as tools.
Enhanced with LLMClient for robust error handling and DeepSeek-Coder optimization.
"""
import re
from typing import Dict, Any, List

from agents.base_agent import BaseAgent
from config.settings import Settings
from core.llm_client import LLMClient


class PlannerAgent(BaseAgent):
    """
    The strategic brain that decomposes user requests into step-by-step plans.

    Each step in the plan is a call to a specialist agent acting as a "tool".
    This structured approach prevents monolithic attempts at complex questions
    and enables sophisticated multi-step reasoning.
    """

    def __init__(self, settings: Settings):
        super().__init__(settings)
        self.llm_client = LLMClient(settings, timeout=90, max_retries=2)

        # Whitelist of valid tools to prevent hallucinated/invalid tool calls
        self.valid_tools = {"sales_copilot_tool", "crm_tool", "email_tool"}

    def _get_tool_descriptions(self) -> str:
        """Returns the list of tools the planner can choose from."""
        return """AVAILABLE TOOLS:
- sales_copilot_tool(query: str): Expert at retrieving information from the knowledge base (transcripts, emails, Neo4j graph). Use for questions about specific facts, summaries, or past events.
- crm_tool(query: str): Expert at analyzing and summarizing data from the CRM. Use for questions about deal outcomes, client history, and sales performance metrics.
- email_tool(query: str): Expert at drafting and analyzing sales emails. Use for requests to generate new emails or find examples of past emails."""

    def _parse_plan_safely(self, plan_str: str) -> List[str]:
        """
        Safely parses the LLM's string output into a list of tool calls
        without using eval(). Validates tool names against whitelist.

        Args:
            plan_str: Raw LLM output containing tool calls

        Returns:
            List of validated tool call strings, always ending with "FINISH"
        """
        print(f"   → Parsing plan: {plan_str[:100]}...")
        plan = []

        # Improved regex to capture tool name and its argument (single or double quotes)
        pattern = r"(\w+)\s*\(\s*['\"](.+?)['\"]\s*\)"
        matches = re.findall(pattern, plan_str)

        for tool_name, argument in matches:
            if tool_name in self.valid_tools:
                # Reconstruct the tool call with consistent formatting
                plan.append(f"{tool_name}('{argument}')")
            else:
                print(f"   ⚠️ Skipping invalid tool: {tool_name}")

        # Always ensure the plan ends with "FINISH"
        if "FINISH" in plan_str.upper() or not plan:
            plan.append("FINISH")

        return plan

    async def run(self, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Creates a step-by-step execution plan for the user's request.

        Args:
            data: Dict containing:
                - original_request: The user's original query

        Returns:
            Dict with key "plan": List of tool calls ending with "FINISH"
        """
        print("🗺️ PlannerAgent: Creating execution plan...")

        # Extract request from data dict
        if not data or 'original_request' not in data:
            return {"plan": ["FINISH"]}

        request = data['original_request']

        # Escape quotes in request
        safe_request = request.replace("'", "\\'")
        tool_descriptions = self._get_tool_descriptions()

        # Optimized prompt for DeepSeek-Coder with clear structure
        prompt = f"""TASK: Create a step-by-step plan to answer a user request

{tool_descriptions}

INSTRUCTIONS:
1. Analyze the user's request
2. Create a plan using ONLY the available tools above
3. Each step must be a tool call in this exact format: tool_name('argument')
4. The final step must ALWAYS be 'FINISH'
5. Keep the plan minimal - only use tools that are necessary

OUTPUT FORMAT:
Return a Python list of strings.
Example: ["sales_copilot_tool('Find transcripts about estate planning')", "FINISH"]

USER REQUEST: "{safe_request}"

PLAN (as Python list):"""

        result = self.llm_client.generate(
            prompt=prompt,
            format_json=False,
            timeout=90
        )

        if not result["success"]:
            print(f"   ❌ LLM call failed: {result['error']}")
            return {"plan": ["FINISH"]}

        plan_str = result["response"]

        # Use safe parsing to extract and validate tool calls
        plan = self._parse_plan_safely(plan_str)

        print(f"   ✅ Generated plan with {len(plan)} steps")
        for i, step in enumerate(plan, 1):
            print(f"      {i}. {step}")

        return {"plan": plan}
