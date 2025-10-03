<!-- markdownlint-disable MD022 MD032 MD030 MD007 MD031 MD046 MD001 MD025 MD050 MD009 MD024 MD047 MD041 -->
# Playbook: SPRINT 02 - Building The Reasoning Engine

## Sprint Goal

To re-architect the orchestrator into an advanced, agentic reasoning engine. By the end of this sprint, the system will be able to receive a user request, create a dynamic plan, execute it using specialist agents as "tools," and perform cognitive self-correction. This sprint adapts the core concepts (Gatekeeper, Planner, Auditor, Router) from the "Agentic RAG" article.

---

### Epic 2.1: Upgrading the Agent's Memory (The State)

**Objective:** To enhance the `AgentState` to support the new cognitive processes. The state needs to track not just the data, but the agent's *thought process*—its plan, its actions, its verifications, and its final conclusion.

#### **Task 2.1.1: Evolve the `AgentState`**

* **Rationale:** Our current state is a simple data container. The new state will be the central nervous system of our reasoning loop, tracking every step of the agent's "thinking" from the initial query to the final response. This is essential for the new cognitive nodes to function.
* **File to Modify:** `orchestrator/state.py`
* **Step 1: Add the Code**
    * The following complete code should replace the existing content of `orchestrator/state.py`.

    ```python
from typing import TypedDict, List, Dict, Any, Optional
from pathlib import Path

class AgentState(TypedDict):
    """
    Represents the unified state for both the ingestion pipeline and the
    reasoning engine. It is designed for a gradual, backward-compatible
    migration to the new agentic architecture.
    """
    # --- Universal Fields ---
    file_path: Optional[Path]
    transcript_id: Optional[int]
    chunks: Optional[List[str]]

    # --- Ingestion & Legacy Fields (from Sprint 1) ---
    raw_text: Optional[str]
    structured_dialogue: Optional[List[Dict[str, Any]]]
    conversation_phases: Optional[List[Dict[str, Any]]] # RE-ADDED for compatibility
    extracted_data: Optional[Dict[str, Any]] # PRESERVED for backward compatibility
    crm_data: Optional[Dict[str, Any]]
    email_draft: Optional[str]
    social_content: Optional[Dict[str, Any]]
    coaching_feedback: Optional[Dict[str, Any]]
    db_save_status: Optional[Dict[str, Any]] # RE-ADDED for compatibility
    historian_status: Optional[Dict[str, Any]] # RE-ADDED for compatibility

    # --- Reasoning Engine & "Intelligence First" Fields ---
    original_request: Optional[str]
    extracted_entities: Optional[Dict[str, Any]] # NEW: From KnowledgeAnalyst
    plan: Optional[List[str]]
    intermediate_steps: Optional[List[Dict[str, Any]]]
    verification_history: Optional[List[Dict[str, Any]]]
    clarification_question: Optional[str]
    final_response: Optional[str]

---

### Epic 2.2: Building the Cognitive Nodes

**Objective:** To create a new suite of agents whose sole purpose is to provide the "thinking" capabilities for our reasoning loop. These agents do not process the transcript directly; they process the *state* of the problem itself.

#### **Task 2.2.1: Create the `GatekeeperAgent`**

* **Rationale:** A common failure point for AI systems is ambiguous user queries. The Gatekeeper acts as a "guard rail," checking if a request is specific enough to be answered with high precision. If not, it asks for clarification, mimicking an expert human who asks clarifying questions before starting work.
* **Step 1: Create the Agent File**
    * Create a new directory and file: `agents/gatekeeper/gatekeeper_agent.py`.
* **Step 2: Add the Code**
    * The following complete code should be placed in `agents/gatekeeper/gatekeeper_agent.py`.

    ```python
import json
import requests
from typing import Dict, Any

from agents.base_agent import BaseAgent
from config.settings import Settings # Keeping this import for consistency with other agents

class GatekeeperAgent(BaseAgent):
    """
    Checks if a user's request is specific enough to be answered,
    or if it's too ambiguous and requires clarification.
    """
    def __init__(self, settings: Settings):
        super().__init__(settings)
        self.api_url = settings.OLLAMA_API_URL
        self.model_name = settings.LLM_MODEL_NAME

    async def run(self, request: str) -> Dict[str, Any]:
        print("🧐 GatekeeperAgent: Checking for ambiguity...")

        # ENHANCEMENT: Escape quotes to prevent prompt issues
        safe_request = request.replace('"', '\\"')

        prompt = f"""
        You are an expert at identifying ambiguity in user requests for a sales analysis system.
        A specific request asks for a number, a date, a named risk, a client name, or a comparison.
        An ambiguous request is open-ended (e.g., 'How are sales going?').

        If the request is ambiguous, formulate a single, polite question to the user that would provide the necessary clarification. Otherwise, respond with only the word "OK".

        User Request: "{safe_request}"
        Response:
        """
        payload = {"model": self.model_name, "prompt": prompt, "stream": False}

        try:
            response = requests.post(self.api_url, json=payload)
            response.raise_for_status() # Check for HTTP errors (4xx or 5xx)

            llm_response = response.json().get("response", "").strip()

            # ENHANCEMENT: Case-insensitive check for robustness
            if llm_response.upper() == "OK":
                print("   - Request is specific. Proceeding.")
                return {"clarification_question": None}
            else:
                print("   - Request is ambiguous. Generating clarification question.")
                return {"clarification_question": llm_response}

        # ENHANCEMENT: More specific error handling
        except requests.RequestException as e:
            print(f"   ❌ ERROR: LLM API request failed: {e}")
            # In case of a network error, we assume the request is OK to not block the pipeline.
            return {"clarification_question": None}
        except Exception as e:
            print(f"   ❌ ERROR: Unexpected error in GatekeeperAgent: {e}")
            return {"clarification_question": None}

#### **Task 2.2.2: Create the `PlannerAgent`**

* **Rationale:** This agent is the strategic brain. It decomposes a user's request into a logical, step-by-step plan. Each step in the plan will be a call to one of our specialist agents (who will act as "tools"). This structured approach prevents the system from making a single, monolithic attempt to answer a complex question.
* **Step 1: Create the Agent File**
    * Create a new directory and file: `agents/planner/planner_agent.py`.
* **Step 2: Add the Code**
    * The following complete code should be placed in `agents/planner/planner_agent.py`.

    ```python
import json
import re
import requests
from typing import Dict, Any, List

from agents.base_agent import BaseAgent
from config.settings import Settings

class PlannerAgent(BaseAgent):
    """
    This agent is the strategic brain. It creates a step-by-step plan
    to answer a user's request by selecting from available "tools".
    """
    def __init__(self, settings: Settings):
        super().__init__(settings)
        self.api_url = settings.OLLAMA_API_URL
        self.model_name = settings.LLM_MODEL_NAME
        # Whitelist of valid tools to prevent hallucinated/invalid tool calls
        self.valid_tools = {"sales_copilot_tool", "crm_tool", "email_tool"}

    def _get_tool_descriptions(self) -> str:
        """Returns the list of tools the planner can choose from."""
        return """
        - sales_copilot_tool(query: str): Expert at retrieving information from the knowledge base (transcripts, emails, etc.). Use for questions about specific facts, summaries, or past events.
        - crm_tool(query: str): Expert at analyzing and summarizing data from the CRM. Use for questions about deal outcomes, client history, and sales performance metrics.
        - email_tool(query: str): Expert at drafting and analyzing sales emails. Use for requests to generate new emails or find examples of past emails.
        """

    def _parse_plan_safely(self, plan_str: str) -> List[str]:
        """
        Safely parses the LLM's string output into a list of tool calls
        without using the dangerous eval(). It also validates the tool names.
        """
        print(f"   - Safely parsing LLM plan string: {plan_str}")
        plan = []
        # Improved regex to capture tool name and its single-quoted argument
        pattern = r"(\w+)\s*\(\s*'(.*?)'\s*\)"
        matches = re.findall(pattern, plan_str)

        for tool_name, argument in matches:
            if tool_name in self.valid_tools:
                # Reconstruct the tool call to ensure consistent formatting
                plan.append(f"{tool_name}('{argument}')")
            else:
                print(f"   ⚠️ Skipping invalid tool call found in plan: {tool_name}")

        # Always ensure the plan ends with "FINISH"
        if "FINISH" in plan_str or not plan:
            plan.append("FINISH")

        return plan

    async def run(self, request: str) -> Dict[str, Any]:
        print("🗺️ PlannerAgent: Creating a plan...")
        safe_request = request.replace("'", "\\'") # Escape single quotes for the argument
        tool_descriptions = self._get_tool_descriptions()

        prompt = f"""
        You are a master planner agent. Your task is to create a step-by-step plan to answer the user's request by intelligently selecting from the available tools.

        **Available Tools:**
        {tool_descriptions}

        **Instructions:**
        1. Analyze the user's request.
        2. Create a clear, step-by-step plan. Each step must be a call to one of the available tools.
        3. The final step in your plan must ALWAYS be 'FINISH'.

        **Output Format:**
        Return the plan as a Python-parseable list of strings.
        Example: ["sales_copilot_tool('Find transcripts where the main objection was about price')", "FINISH"]

        ---
        User Request: "{safe_request}"
        Plan:
        """
        payload = {"model": self.model_name, "prompt": prompt, "stream": False}

        try:
            response = requests.post(self.api_url, json=payload)
            response.raise_for_status()

            plan_str = response.json().get("response", "[]")
            
            # CRITICAL: Use the safe parsing method
            plan = self._parse_plan_safely(plan_str)

            print(f"   - Generated Plan: {plan}")
            return {"plan": plan}

        except requests.RequestException as e:
            print(f"   ❌ ERROR: LLM API request failed: {e}")
            return {"plan": ["FINISH"]}
        except Exception as e:
            print(f"   ❌ ERROR in PlannerAgent: {e}")
            return {"plan": ["FINISH"]}

---
#### **Task 2.2.3: Create the `AuditorAgent` (for Self-Correction)**

* **Rationale:** A basic agent trusts its tools blindly. An advanced agent is a skeptic. The Auditor acts as a critical "second opinion." After a specialist agent (acting as a tool) runs, its output is passed to the Auditor to be validated against the original request. If the output is low-quality or irrelevant, this check allows our system to self-correct by looping back to the Planner to try a new approach.
* **Step 1: Create the Agent File**
    * Create a new directory and file: `agents/auditor/auditor_agent.py`.
* **Step 2: Define the Verification Structure (Pydantic)**
    * At the top of the new file, we will define a Pydantic model. This forces the Auditor LLM to return a structured, reliable score and reasoning, which is essential for our router's logic.

* **Step 3: Add the Code**
    * The following complete code should be placed in `agents/auditor/auditor_agent.py`.

    ```python
# This is the new, FINALIZED code for agents/auditor/auditor_agent.py

import json
import requests
from typing import Dict, Any
from pydantic import BaseModel, Field, ValidationError

from agents.base_agent import BaseAgent
from config.settings import Settings

class VerificationResult(BaseModel):
    """Structured output for the Auditor node's verification."""
    confidence_score: int = Field(description="Score from 1-5 on confidence", ge=1, le=5)
    reasoning: str = Field(description="Brief reasoning for the confidence score.")

class AuditorAgent(BaseAgent):
    """
    Audits specialist tool output against the original request to ensure
    relevance and quality. This enables the system to self-correct.
    """
    def __init__(self, settings: Settings):
        super().__init__(settings)
        self.api_url = settings.OLLAMA_API_URL
        self.model_name = settings.LLM_MODEL_NAME

    async def run(self, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Runs the audit verification on a tool's output.
        Expects a dictionary with 'original_request' and 'last_step'.
        """
        print("🕵️ AuditorAgent: Verifying the last tool output...")

        # --- ENHANCEMENT: Input Validation ---
        if not data or 'original_request' not in data or 'last_step' not in data:
            return {"confidence_score": 1, "reasoning": "Missing required input data for audit."}
        
        original_request = data['original_request']
        last_step = data['last_step']
        tool_name = last_step.get('tool_name', 'Unknown Tool')
        tool_output = last_step.get('tool_output', 'No output')

        # Safely serialize tool output for the prompt
        try:
            tool_output_str = json.dumps(tool_output, ensure_ascii=False, indent=2)
        except Exception:
            tool_output_str = str(tool_output)

        prompt = f"""
        You are a meticulous fact-checker and auditor. Given the user's original request and the output from a specialist tool, audit the output for quality and relevance.

        **User's Original Request:**
        "{original_request}"

        **Tool Called:**
        {tool_name}

        **Tool's Output:**
        ---
        {tool_output_str[:2000]}
        ---

        **Audit Checklist:**
        1. **Relevance:** Is this output directly relevant and helpful for the user's request?
        2. **Accuracy:** Does the output appear factually consistent and logical?

        Provide a confidence score from 1 (not relevant/correct) to 5 (highly relevant/correct).
        Respond ONLY with a valid JSON object in this exact format:
        {{
            "confidence_score": <1-5>,
            "reasoning": "Your brief reasoning here."
        }}
        """
        # Note: Removed "format": "json" for better compatibility with local LLMs
        payload = {"model": self.model_name, "prompt": prompt, "stream": False}

        try:
            response = requests.post(self.api_url, json=payload)
            response.raise_for_status()
            response_text = response.json().get("response", "{}")

            # --- ENHANCEMENT: Robust JSON parsing ---
            json_match = response_text[response_text.find('{'):response_text.rfind('}')+1]
            result_dict = json.loads(json_match)
            
            verification = VerificationResult(**result_dict)
            print(f"   - Audit Confidence Score: {verification.confidence_score}/5")
            return verification.dict()

        except (json.JSONDecodeError, ValidationError) as e:
            print(f"   ❌ ERROR: Failed to parse or validate LLM response: {e}")
            return {"confidence_score": 2, "reasoning": f"Audit response was malformed: {e}"}
        except requests.RequestException as e:
            print(f"   ❌ ERROR: LLM API request failed: {e}")
            return {"confidence_score": 3, "reasoning": "Audit request failed due to network error."}
        except Exception as e:
            print(f"   ❌ ERROR: Unexpected error in AuditorAgent: {e}")
            return {"confidence_score": 1, "reasoning": f"An unexpected error occurred: {e}"}

#### **Task 2.2.4: Create the `StrategistAgent` (for Synthesis)**

* **Rationale:** This is the final and most advanced cognitive step. After the plan is complete and all information has been gathered, a basic agent would simply list the facts. The Strategist goes further. It synthesizes the information into a single, coherent answer and attempts to **connect the dots**, generating novel insights or hypotheses based on the combined data. This is the primary value-add of the entire reasoning engine.
* **Step 1: Create the Agent File**
    * Create a new directory and file: `agents/strategist/strategist_agent.py`.
* **Step 2: Add the Code**
    * The following complete code should be placed in `agents/strategist/strategist_agent.py`.

    ```python
# This is the new, FINALIZED code for agents/strategist/strategist_agent.py

import json
import requests
from typing import Dict, Any, List

from agents.base_agent import BaseAgent
from config.settings import Settings

class StrategistAgent(BaseAgent):
    """
    This agent acts as the final synthesizer. It takes all the verified
    information from the tool execution steps and constructs a comprehensive
    final response, aiming to generate novel insights by connecting disparate facts.
    """
    def __init__(self, settings: Settings):
        super().__init__(settings)
        self.api_url = settings.OLLAMA_API_URL
        self.model_name = settings.LLM_MODEL_NAME
        self.max_context_chars = 8000 # Safety limit for the LLM context

    async def run(self, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Synthesizes a final answer from intermediate tool execution steps.
        Expects a dictionary with 'original_request' and 'intermediate_steps'.
        """
        print("✍️ StrategistAgent: Synthesizing the final answer...")

        # --- ENHANCEMENT: Input Validation ---
        if not data or 'original_request' not in data or 'intermediate_steps' not in data:
            return {"final_response": "Error: Missing required data for synthesis."}
        
        original_request = data['original_request']
        intermediate_steps = data['intermediate_steps']

        # --- ENHANCEMENT: Build context safely with truncation ---
        context_parts = []
        total_chars = 0
        for step in intermediate_steps:
            try:
                output_str = json.dumps(step.get('tool_output', 'No output'), indent=2, ensure_ascii=False)
            except TypeError:
                output_str = str(step.get('tool_output', 'No output'))

            step_text = (
                f"Step: Calling tool `{step.get('tool_name', 'N/A')}` with input `{step.get('tool_input', 'N/A')}`\n"
                f"Observed Output:\n{output_str}"
            )

            if total_chars + len(step_text) > self.max_context_chars:
                context_parts.append("... [additional steps truncated due to context limit]")
                break
            
            context_parts.append(step_text)
            total_chars += len(step_text)

        context = "\n\n---\n\n".join(context_parts)

        prompt = f"""
        You are an expert financial analyst acting as a strategist. Your task is to synthesize a comprehensive, final answer to the user's request based on the context provided by your specialist agents.

        **User's Original Request:**
        {original_request}

        **Context from Specialist Agents:**
        ---
        {context}
        ---

        **Instructions:**
        1.  Carefully review the context from all tool outputs.
        2.  Construct a clear, well-written, and accurate final answer.
        3.  **Connect the Dots (Causal Inference):** Do not just list the facts. Analyze the combined information to find connections and correlations.
        4.  **Frame as a Hypothesis:** Clearly state connections as data-grounded hypotheses.

        Final Answer:
        """
        payload = {"model": self.model_name, "prompt": prompt, "stream": False}

        try:
            response = requests.post(self.api_url, json=payload)
            response.raise_for_status()
            final_answer = response.json().get("response", "Could not generate a final answer.")
            print("   - Generated final answer with causal inference.")
            return {"final_response": final_answer}
        except requests.RequestException as e:
            print(f"   ❌ ERROR: LLM API request failed: {e}")
            return {"final_response": f"An error occurred during final synthesis: {e}"}
        except Exception as e:
            print(f"   ❌ ERROR: Unexpected error in StrategistAgent: {e}")
            return {"final_response": f"An unexpected error occurred: {e}"}

---

### Epic 2.3: Building the Cognitive Workflow

**Objective:** To completely re-architect the `orchestrator/graph.py` file. We will transform it from a linear pipeline into an advanced, cyclical graph that enables dynamic planning, execution, and self-correction. This new structure is the "reasoning engine" itself.

#### **Task 2.3.1: Re-Architect the Orchestrator Graph**

* **Rationale:** This is the culmination of Sprint 2. We are wiring together all the new cognitive agents (`Gatekeeper`, `Planner`, `Auditor`, `Strategist`) with a new `ToolExecutor` node and a conditional `Router`. This architecture allows the system to think, plan, act, and verify in a loop, rather than just processing data in a straight line.
* **File to Modify:** `orchestrator/graph.py`
* **Step 1: Add the Code**
    * The following complete code should replace the existing content of `orchestrator/graph.py`. This is a complete overhaul and represents the new heart of the Stellar Sales System.

    ```python
### Epic 2.3: Building the Cognitive Workflow

**Objective:** To design the final, production-ready `StateGraph` in the `orchestrator/graph.py` file. This new graph will correctly and securely implement the full reasoning engine, including the cognitive loop for planning, execution, verification, and self-correction.

#### **Task 2.3.1: Implement the Master Reasoning Workflow**

* **Rationale:** This is the culmination of Sprint 2. We are wiring together all the new cognitive agents using best practices. This implementation avoids the dangerous `eval()` function, uses a pure router function with a dedicated `replanner` node for state changes, correctly handles all `BaseAgent` interfaces, and includes robust error handling.
* **File to Modify:** `orchestrator/graph.py`
* **Step 1: Add the Code**
    * The following complete code should replace the existing content of `orchestrator/graph.py`. This is the final, secure, and robust version of the reasoning engine.

    ```python
    from langgraph.graph import StateGraph, END
    from typing import Dict, Any
    import re

    from orchestrator.state import AgentState
    from config.settings import settings

    # --- Import all cognitive agents ---
    from agents.gatekeeper.gatekeeper_agent import GatekeeperAgent
    from agents.planner.planner_agent import PlannerAgent
    from agents.auditor.auditor_agent import AuditorAgent
    from agents.strategist.strategist_agent import StrategistAgent

    # --- Import specialist agents that will act as "tools" ---
    # In Sprint 3, we will replace this with the real, upgraded agent.
    from agents.base_agent import BaseAgent
    class SalesCopilotAgent(BaseAgent):
        async def run(self, data: Dict[str, Any] = None) -> Dict[str, Any]:
            print(f"--- (Placeholder) SalesCopilot called with: {data} ---")
            return {"response": "Placeholder response from SalesCopilot."}

    # --- Initialize ALL agents ---
    gatekeeper_agent = GatekeeperAgent(settings)
    planner_agent = PlannerAgent(settings)
    auditor_agent = AuditorAgent(settings)
    strategist_agent = StrategistAgent(settings)
    sales_copilot_agent = SalesCopilotAgent(settings)

    # --- Tool Mapping for the Planner ---
    tool_map = {
        "sales_copilot_tool": sales_copilot_agent,
    }

    # --- Define the Cognitive Nodes for the Graph ---

    async def gatekeeper_node(state: AgentState) -> Dict[str, Any]:
        """First node: Checks for ambiguity."""
        result = await gatekeeper_agent.run(data={"original_request": state["original_request"]})
        return {"clarification_question": result.get("clarification_question")}

    async def planner_node(state: AgentState) -> Dict[str, Any]:
        """Generates the step-by-step plan."""
        result = await planner_agent.run(data={"original_request": state["original_request"]})
        return {"plan": result.get("plan", ["FINISH"])}

    def _parse_tool_call_safely(tool_call: str) -> tuple[str, str]:
        """Safely parses a tool call string like "tool_name('argument')" without using eval()."""
        match = re.match(r"(\w+)\s*\(\s*['\"](.*?)['\"]\s*\)", tool_call)
        if match:
            return match.group(1), match.group(2)
        return None, None

    async def tool_executor_node(state: AgentState) -> Dict[str, Any]:
        """Executes the next tool in the plan safely."""
        print("🛠️ ToolExecutorNode: Executing the next step...")
        plan = state.get("plan", [])
        next_step = plan[0]
        tool_name, tool_input = _parse_tool_call_safely(next_step)

        if not tool_name or tool_name not in tool_map:
            error_output = {"error": f"Tool '{tool_name}' not found or call is malformed."}
            new_step = {"tool_name": tool_name or "unknown", "tool_input": tool_input or "", "tool_output": error_output}
        else:
            tool_agent = tool_map[tool_name]
            try:
                # All tools now conform to the same run(data) signature
                result = await tool_agent.run(data={"query": tool_input})
                new_step = {"tool_name": tool_name, "tool_input": tool_input, "tool_output": result}
            except Exception as e:
                new_step = {"tool_name": tool_name, "tool_input": tool_input, "tool_output": {"error": str(e)}}

        return {
            "intermediate_steps": state.get("intermediate_steps", []) + [new_step],
            "plan": plan[1:]
        }

    async def auditor_node(state: AgentState) -> Dict[str, Any]:
        """Verifies the output of the last tool."""
        last_step = state["intermediate_steps"][-1]
        result = await auditor_agent.run(data={"original_request": state["original_request"], "last_step": last_step})
        return {"verification_history": state.get("verification_history", []) + [result]}

    async def strategist_node(state: AgentState) -> Dict[str, Any]:
        """Synthesizes the final response."""
        result = await strategist_agent.run(data={"original_request": state["original_request"], "intermediate_steps": state["intermediate_steps"]})
        return {"final_response": result.get("final_response")}

    async def replanner_node(state: AgentState) -> Dict[str, Any]:
        """Node to clear a failed plan, forcing a new plan to be created."""
        print("   - Verification failed. Clearing plan for replanning.")
        return {"plan": []}

    # --- Define the Conditional Router ---

    def router_node(state: AgentState) -> str:
        """The central decision-maker. This is a pure function and does not modify state."""
        print("🚦 RouterNode: Deciding next step...")

        if state.get("clarification_question"):
            return END

        verification_history = state.get("verification_history", [])
        if verification_history:
            last_verification = verification_history[-1]
            if last_verification.get("confidence_score", 0) < 3:
                return "replanner"

        if not state.get("plan") or state["plan"][0] == "FINISH":
            return "strategist"

        return "tool_executor"

    # --- Construct the Graph ---
    def create_reasoning_workflow():
        workflow = StateGraph(AgentState)

        workflow.add_node("gatekeeper", gatekeeper_node)
        workflow.add_node("planner", planner_node)
        workflow.add_node("tool_executor", tool_executor_node)
        workflow.add_node("auditor", auditor_node)
        workflow.add_node("strategist", strategist_node)
        workflow.add_node("replanner", replanner_node)

        workflow.set_entry_point("gatekeeper")

        workflow.add_edge("gatekeeper", "planner")
        workflow.add_edge("planner", "tool_executor")
        workflow.add_edge("tool_executor", "auditor")
        workflow.add_edge("strategist", END)
        workflow.add_edge("replanner", "planner") # After clearing the plan, go back to the planner

        workflow.add_conditional_edges(
            "auditor",
            router_node,
            {
                "replanner": "replanner",
                "strategist": "strategist",
                "tool_executor": "tool_executor",
                END: END
            }
        )

        return workflow.compile()

    app = create_reasoning_workflow()
    ```
---