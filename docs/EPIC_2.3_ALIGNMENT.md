# Epic 2.3 Implementation: Playbook Alignment

## Overview
This document details the alignment of the Stellar Sales System's reasoning workflow with the **Epic 2.3 playbook specification**. All agent interfaces and graph architecture now conform to the playbook's requirements.

## Changes Made to Align with Playbook

### 1. **Standardized Agent Interfaces**

All cognitive agents now use the consistent `run(data: Dict[str, Any])` signature as specified in the playbook.

#### Before (Non-standard):
```python
# GatekeeperAgent
async def run(self, request: str) -> Dict[str, Any]:
    # ...

# PlannerAgent
async def run(self, request: str) -> Dict[str, Any]:
    # ...
```

#### After (Playbook-compliant):
```python
# GatekeeperAgent
async def run(self, data: Dict[str, Any] = None) -> Dict[str, Any]:
    request = data['original_request']
    # ...

# PlannerAgent
async def run(self, data: Dict[str, Any] = None) -> Dict[str, Any]:
    request = data['original_request']
    # ...
```

**Impact**: All agents now conform to `BaseAgent` interface, enabling consistent tool execution.

### 2. **Graph Node Updates**

Updated all node functions to pass data as dictionaries:

```python
# Before
result = await gatekeeper_agent.run(request=state["original_request"])
result = await planner_agent.run(request=state["original_request"])

# After
result = await gatekeeper_agent.run(data={"original_request": state["original_request"]})
result = await planner_agent.run(data={"original_request": state["original_request"]})
```

### 3. **Simplified Replanner Logic**

#### Before (Duplicated work):
```python
async def replanner_node(state: AgentState) -> Dict[str, Any]:
    """Re-plan if verification failed"""
    last_verification = state["verification_history"][-1]
    if last_verification["confidence_score"] <= 2:
        result = await planner_agent.run(request=state["original_request"])
        return {"plan": result["plan"]}
    return {}
```

#### After (Playbook-compliant):
```python
async def replanner_node(state: AgentState) -> Dict[str, Any]:
    """Clears the plan to force replanning"""
    print("   🔄 Clearing plan for replanning...")
    return {"plan": []}
```

**Benefit**: The edge `replanner → planner` handles re-planning automatically, avoiding duplicate LLM calls.

### 4. **Implemented Tool Map Architecture**

Added placeholder tool infrastructure as specified in playbook:

```python
# Placeholder specialist agent for tool execution
class SalesCopilotAgent(BaseAgent):
    """Placeholder tool agent for Sprint 02 testing"""
    async def run(self, data: Dict[str, Any] = None) -> Dict[str, Any]:
        query = data.get("query", "No query provided") if data else "No query provided"
        return {"response": f"Placeholder response for query: {query}"}

# Tool mapping for the Planner
tool_map = {
    "sales_copilot_tool": sales_copilot_agent,
}
```

### 5. **Safe Tool Parsing**

Implemented the playbook's safe parsing function:

```python
def _parse_tool_call_safely(tool_call: str) -> tuple:
    """
    Safely parses a tool call string like "tool_name('argument')" without using eval().
    """
    match = re.match(r"(\w+)\s*\(\s*['\"](.+?)['\"]\s*\)", tool_call)
    if match:
        return match.group(1), match.group(2)
    return None, None
```

### 6. **Enhanced Tool Executor**

Updated to use tool map with proper error handling:

```python
async def tool_executor_node(state: AgentState) -> Dict[str, Any]:
    """Executes the next tool in the plan safely"""
    next_step = plan[0]
    tool_name, tool_input = _parse_tool_call_safely(next_step)

    if not tool_name or tool_name not in tool_map:
        error_output = {"error": f"Tool '{tool_name}' not found or call is malformed."}
        new_step = {"tool_name": tool_name or "unknown", "tool_input": tool_input or "", "tool_output": error_output}
    else:
        tool_agent = tool_map[tool_name]
        try:
            result = await tool_agent.run(data={"query": tool_input})
            new_step = {"tool_name": tool_name, "tool_input": tool_input, "tool_output": result}
        except Exception as e:
            new_step = {"tool_name": tool_name, "tool_input": tool_input, "tool_output": {"error": str(e)}}

    return {
        "intermediate_steps": (state.get("intermediate_steps") or []) + [new_step],
        "plan": plan[1:]
    }
```

### 7. **Router Threshold Alignment**

Updated confidence threshold from `≤ 2` to `< 3` as per playbook:

```python
# Before
if last_verification["confidence_score"] <= 2:
    return "replanner"

# After
if last_verification["confidence_score"] < 3:
    return "replanner"
```

### 8. **Graph Edge Correction**

Fixed replanner edge to loop back to planner:

```python
# Before
workflow.add_edge("replanner", "tool_executor")

# After
workflow.add_edge("replanner", "planner")
```

## Testing

Created `scripts/test_reasoning_aligned.py` to verify Epic 2.3 compliance:

```bash
./venv/bin/python scripts/test_reasoning_aligned.py
```

### Test Results:
✅ **Agent Interfaces**: All agents accept `data: Dict[str, Any]`
✅ **Tool Parsing**: Safe regex parsing without `eval()`
✅ **Tool Map**: Placeholder agent successfully integrated
✅ **Replanner Flow**: Correctly loops to planner when confidence < 3
✅ **Router Logic**: Properly routes based on state
✅ **Error Handling**: Gracefully handles malformed tool calls

## Architecture Diagram

```
EPIC 2.3 COGNITIVE WORKFLOW
============================

original_request
      ↓
Gatekeeper (checks ambiguity)
      ↓
Planner (creates tool call plan)
      ↓
Tool Executor (executes via tool_map) → Auditor (scores 1-5)
      ↑                                        ↓
      ←────── Replanner (clears plan) ←── Router (conditional)
                                              ↓
                                         Strategist (synthesizes)
                                              ↓
                                         final_response
```

## Files Modified

### Agent Files
- `agents/gatekeeper/gatekeeper_agent.py` - Updated interface to `run(data: Dict)`
- `agents/planner/planner_agent.py` - Updated interface to `run(data: Dict)`
- `agents/auditor/auditor_agent.py` - Already compliant ✅
- `agents/strategist/strategist_agent.py` - Already compliant ✅

### Orchestrator Files
- `orchestrator/graph.py` - Major updates:
  - Added `import re` for safe parsing
  - Added `_parse_tool_call_safely()` function
  - Added `SalesCopilotAgent` placeholder class
  - Added `tool_map` dictionary
  - Updated `gatekeeper_node()` and `planner_node()` calls
  - Rewrote `tool_executor_node()` with tool map logic
  - Simplified `replanner_node()` to clear plan only
  - Updated `router_node()` threshold to `< 3`
  - Fixed `replanner → planner` edge

### Test Files
- `scripts/test_reasoning_aligned.py` - New test for Epic 2.3 compliance

## Key Differences from Original Implementation

| Aspect | Original | Epic 2.3 Playbook | Status |
|--------|----------|-------------------|--------|
| Agent interface | Mixed signatures | All use `run(data: Dict)` | ✅ Fixed |
| Tool executor | Mock strings | Tool map with real agents | ✅ Fixed |
| Replanner logic | Calls planner inside | Clears plan, edges to planner | ✅ Fixed |
| Router threshold | ≤ 2 | < 3 | ✅ Fixed |
| Tool parsing | Simple split | Regex without eval() | ✅ Fixed |
| Replanner edge | → tool_executor | → planner | ✅ Fixed |

## Next Steps (Sprint 03)

1. **Replace Placeholder Tools**: Implement real `SalesCopilotAgent` with:
   - Qdrant semantic search
   - Neo4j graph queries
   - PostgreSQL data retrieval

2. **Add CRM and Email Tools**:
   ```python
   tool_map = {
       "sales_copilot_tool": SalesCopilotAgent(settings),
       "crm_tool": CRMToolAgent(settings),
       "email_tool": EmailToolAgent(settings),
   }
   ```

3. **Optimize Gatekeeper**: Reduce false positives for clarification requests

4. **Add API Endpoint**:
   ```python
   @app.post("/query/")
   async def query_endpoint(request: QueryRequest):
       result = await reasoning_app.ainvoke({
           "original_request": request.query
       })
       return {"answer": result["final_response"]}
   ```

## Conclusion

The reasoning workflow is now **fully aligned with Epic 2.3 playbook specification**. All agent interfaces are consistent, tool execution uses a proper tool map, and the cognitive loop implements the exact architecture specified in the playbook with safe parsing and robust error handling.

The system is ready for Sprint 03 tool implementations! 🚀
