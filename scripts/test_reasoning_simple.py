"""
Test script with a simple, clear query.
"""
import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from orchestrator.state import AgentState
from orchestrator.graph import reasoning_app


async def test_simple_workflow():
    """Test with a simple clear query"""
    print("=" * 70)
    print("Testing Reasoning Workflow - Simple Query")
    print("=" * 70)

    # Very simple query
    test_query = "Draft a follow-up email for our last estate planning client"

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
    print("-" * 70)

    result = await reasoning_app.ainvoke(initial_state)

    print("\n" + "=" * 70)
    print("FINAL STATE")
    print("=" * 70)

    if result.get("clarification_question"):
        print(f"\n❓ Clarification: {result['clarification_question']}")

    if result.get("final_response"):
        print(f"\n🎯 FINAL ANSWER:")
        print(f"{result['final_response']}")

    if result.get("intermediate_steps"):
        print(f"\n🔧 Steps Executed: {len(result['intermediate_steps'])}")

    if result.get("verification_history"):
        avg_score = sum(v['confidence_score'] for v in result['verification_history']) / len(result['verification_history'])
        print(f"📊 Avg Confidence: {avg_score:.1f}/5")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(test_simple_workflow())
