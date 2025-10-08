"""
Test script for the Reasoning Engine workflow (Sprint 02).
Tests: Gatekeeper → Planner → Tool Executor → Auditor → Router → Strategist
"""
from orchestrator.graph import reasoning_app
from orchestrator.state import AgentState
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


async def test_reasoning_workflow():
    """Test the complete reasoning engine with a sample query"""
    print("=" * 70)
    print("Testing Reasoning Engine Workflow (Sprint 02)")
    print("=" * 70)

    # Test query
    test_query = "What sales opportunities exist in our recent transcripts related to estate planning?"

    # Initialize state
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
        # Run the reasoning workflow
        result = await reasoning_app.ainvoke(initial_state)

        print("\n" + "=" * 70)
        print("WORKFLOW RESULTS")
        print("=" * 70)

        # Display clarification if needed
        if result.get("clarification_question"):
            print(f"\n❓ CLARIFICATION NEEDED:")
            print(f"   {result['clarification_question']}")

        # Display plan if created
        if result.get("plan"):
            print(f"\n📋 EXECUTION PLAN:")
            for i, step in enumerate(result["plan"], 1):
                print(f"   {i}. {step}")

        # Display intermediate steps
        if result.get("intermediate_steps"):
            print(f"\n🔧 EXECUTED STEPS:")
            for i, step in enumerate(result["intermediate_steps"], 1):
                tool_name = step.get("tool_name", "Unknown")
                output = step.get("tool_output", "No output")
                print(f"   {i}. {tool_name}")
                print(f"      Output: {output[:100]}..." if len(
                    str(output)) > 100 else f"      Output: {output}")

        # Display verification history
        if result.get("verification_history"):
            print(f"\n✅ VERIFICATION SCORES:")
            for i, verification in enumerate(result["verification_history"], 1):
                score = verification.get("confidence_score", "N/A")
                reasoning = verification.get("reasoning", "No reasoning")
                print(f"   Step {i}: {score}/5 - {reasoning}")

        # Display final response
        if result.get("final_response"):
            print(f"\n🎯 FINAL ANSWER:")
            print(f"   {result['final_response']}")

        print("\n" + "=" * 70)
        print("✅ Reasoning workflow completed successfully!")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ Error during reasoning workflow: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_reasoning_workflow())
