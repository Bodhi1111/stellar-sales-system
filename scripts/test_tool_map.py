"""
Test script to verify tool_map works with all three tools (Epic 3.3)
"""
from orchestrator.graph import tool_map
import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


async def test_tool_map():
    """Test that all tools in tool_map are callable"""
    print("=" * 70)
    print("Testing Tool Map (Sprint 03, Epic 3.3)")
    print("=" * 70)

    print(f"\n📋 Tools in tool_map: {list(tool_map.keys())}")

    # Test each tool
    for tool_name, tool_agent in tool_map.items():
        print(f"\n🔧 Testing {tool_name}...")
        print(f"   Agent type: {type(tool_agent).__name__}")

        try:
            # Try calling with data dict (new interface)
            result = await tool_agent.run(data={"query": f"Test query for {tool_name}"})
            print(f"   ✅ Works with data dict interface")
            print(f"   Result type: {type(result)}")
        except TypeError as e:
            print(f"   ⚠️ Doesn't support data dict interface: {e}")
            print(f"   Note: Agent may need upgrade to standardized interface")
        except Exception as e:
            print(f"   ❌ Error: {e}")

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    tools_with_data_interface = []
    tools_needing_upgrade = []

    for tool_name, tool_agent in tool_map.items():
        try:
            result = await tool_agent.run(data={"query": "test"})
            tools_with_data_interface.append(tool_name)
        except:
            tools_needing_upgrade.append(tool_name)

    print(f"\n✅ Tools with data dict interface: {tools_with_data_interface}")
    if tools_needing_upgrade:
        print(f"⚠️ Tools needing interface upgrade: {tools_needing_upgrade}")
        print(
            f"   These agents need: async def run(self, data: Dict[str, Any]) -> Dict[str, Any]")

    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_tool_map())
