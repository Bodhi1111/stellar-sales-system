"""
Test Reasoning Engine with RAG query.
"""
from orchestrator.graph import reasoning_app
from orchestrator.state import AgentState
import asyncio


async def test_rag_workflow():
    """Test with a query that should use RAG"""
    print("=" * 80)
    print("Testing Reasoning Engine with RAG Query")
    print("=" * 80)

    # Query that should trigger sales_copilot_tool (RAG)
    test_query = "What pricing concerns did the client raise in the most recent meeting?"

    initial_state: AgentState = {
        "original_request": test_query,
        "file_path": None,
        "transcript_id": None,
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

    if result.get("intermediate_steps"):
        print(f"\n🔧 Steps Executed: {len(result['intermediate_steps'])}")
        for i, step in enumerate(result['intermediate_steps'], 1):
            print(f"\n  Step {i}: {step['tool_name']}")
            print(f"    Input: {step['tool_input'][:100]}...")
            if 'error' in step.get('tool_output', {}):
                print(f"    ❌ Error: {step['tool_output']['error']}")
            else:
                output_str = str(step['tool_output'])[:200]
                print(f"    ✅ Output: {output_str}...")

    if result.get("verification_history"):
        avg_score = sum(v['confidence_score']
                        for v in result['verification_history']) / len(result['verification_history'])
        print(f"\n📊 Avg Confidence: {avg_score:.1f}/5")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(test_rag_workflow())
