"""
Test script for complete reasoning workflow without clarification.
"""
from orchestrator.graph import reasoning_app
from orchestrator.state import AgentState
import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


async def test_complete_workflow():
    """Test with a specific query that won't trigger clarification"""
    print("=" * 70)
    print("Testing Complete Reasoning Workflow")
    print("=" * 70)

    # More specific query
    test_query = "Show me the top 3 estate planning deals from the CRM with their revenue amounts"

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

    try:
        result = await reasoning_app.ainvoke(initial_state)

        print("\n" + "=" * 70)
        print("WORKFLOW RESULTS")
        print("=" * 70)

        if result.get("clarification_question"):
            print(f"\n❓ CLARIFICATION: {result['clarification_question']}")

        if result.get("plan"):
            print(f"\n📋 FINAL PLAN STATE:")
            for i, step in enumerate(result["plan"], 1):
                print(f"   {i}. {step}")

        if result.get("intermediate_steps"):
            print(f"\n🔧 EXECUTED STEPS ({len(result['intermediate_steps'])}):")
            for i, step in enumerate(result["intermediate_steps"], 1):
                tool_name = step.get("tool_name", "Unknown")
                output = step.get("tool_output", "No output")
                print(f"   {i}. {tool_name}: {output}")

        if result.get("verification_history"):
            print(
                f"\n✅ VERIFICATIONS ({len(result['verification_history'])}):")
            for i, v in enumerate(result["verification_history"], 1):
                print(
                    f"   Step {i}: {v['confidence_score']}/5 - {v['reasoning']}")

        if result.get("final_response"):
            print(f"\n🎯 FINAL RESPONSE:")
            print(f"   {result['final_response']}")
        else:
            print(f"\n⚠️ No final response generated")

        print("\n" + "=" * 70)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_complete_workflow())
