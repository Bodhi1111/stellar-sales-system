"""
Test script for the aligned Epic 2.3 implementation.
Tests the complete reasoning workflow as specified in the playbook.
"""
import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from orchestrator.state import AgentState
from orchestrator.graph import reasoning_app


async def test_aligned_workflow():
    """Test the aligned Epic 2.3 implementation"""
    print("=" * 70)
    print("Testing Epic 2.3 Aligned Implementation")
    print("=" * 70)

    # Simple, clear query that won't trigger clarification
    test_query = "Find John Doe's sales transcript using sales_copilot_tool"

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
    print("RESULTS")
    print("=" * 70)

    if result.get("clarification_question"):
        print(f"\n❓ Clarification: {result['clarification_question']}")

    if result.get("plan"):
        print(f"\n📋 Plan State: {result['plan']}")

    if result.get("intermediate_steps"):
        print(f"\n🔧 Steps Executed: {len(result['intermediate_steps'])}")
        for i, step in enumerate(result['intermediate_steps'], 1):
            print(f"   {i}. {step['tool_name']}: {step.get('tool_output', {})}")

    if result.get("verification_history"):
        print(f"\n✅ Verifications:")
        for i, v in enumerate(result['verification_history'], 1):
            print(f"   Step {i}: Score {v['confidence_score']}/5 - {v['reasoning']}")

    if result.get("final_response"):
        print(f"\n🎯 Final Answer:")
        print(f"{result['final_response']}")
        print("\n✅ Complete workflow executed successfully!")
    else:
        print("\n⚠️ Workflow ended without final response (likely clarification needed)")

    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_aligned_workflow())
