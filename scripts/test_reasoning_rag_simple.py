"""
Test Reasoning Engine with direct RAG query (sales_copilot_tool).
"""
from orchestrator.graph import reasoning_app
from orchestrator.state import AgentState
import asyncio


async def test_rag_workflow():
    """Test with a query that should use RAG via sales_copilot_tool"""
    print("=" * 80)
    print("Testing Reasoning Engine - Direct RAG Query")
    print("=" * 80)

    # Direct query about transcript content (should use sales_copilot_tool)
    test_query = "Tell me about any pricing objections or concerns mentioned in the transcripts"

    initial_state: AgentState = {
        "original_request": test_query,
        "file_path": None,
        "transcript_id": None,  # Will auto-select most recent
        "chunks": None,
        "raw_text": None,
        "structured_dialogue": None,
        "conversation_phases": None,
        "extracted_data": None,
        "crm_data": None,
        "email_draft": None,
        "social_content": None,
        "coaching_feedback": None,
        "db_save_status": None,
        "historian_status": None,
        "extracted_entities": None,
        "plan": None,
        "intermediate_steps": None,
        "verification_history": None,
        "clarification_question": None,
        "final_response": None
    }

    print(f"\n📝 Query: {test_query}\n")
    print("-" * 80)

    result = await reasoning_app.ainvoke(initial_state)

    print("\n" + "=" * 80)
    print("FINAL RESULT")
    print("=" * 80)

    if result.get("clarification_question"):
        print(f"\n❓ Clarification: {result['clarification_question']}")

    if result.get("final_response"):
        print(f"\n🎯 FINAL ANSWER:")
        print(f"{result['final_response']}")
        print()

    if result.get("intermediate_steps"):
        print(f"\n🔧 Steps Executed: {len(result['intermediate_steps'])}")
        for i, step in enumerate(result['intermediate_steps'], 1):
            print(f"\n  Step {i}: {step['tool_name']}")
            print(f"    Input: {step['tool_input'][:80]}...")

            tool_output = step.get('tool_output', {})
            if isinstance(tool_output, dict):
                if 'error' in tool_output:
                    print(f"    ❌ Error: {tool_output['error']}")
                elif 'response' in tool_output:
                    response = tool_output['response']
                    if isinstance(response, dict) and 'results' in response:
                        results = response['results']
                        print(f"    ✅ Retrieved: {len(results)} results")
                        if results and len(results) > 0:
                            first_result = results[0]
                            if isinstance(first_result, dict) and 'text' in first_result:
                                print(f"    📄 Sample: {first_result['text'][:150]}...")
                    else:
                        print(f"    ✅ Output: {str(response)[:150]}...")
            else:
                print(f"    ✅ Output: {str(tool_output)[:150]}...")

    if result.get("verification_history"):
        print(f"\n📊 Verification History:")
        for i, v in enumerate(result['verification_history'], 1):
            print(f"  {i}. Score: {v['confidence_score']}/5 - {v.get('reasoning', '')[:80]}...")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(test_rag_workflow())
