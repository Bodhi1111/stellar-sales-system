#!/usr/bin/env python3
"""
Complete diagnostic for Langfuse connectivity.
Tests: Docker → Langfuse → Python SDK → LangChain
"""
import os
import sys
import requests
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import settings

print("=" * 70)
print("🔍 LANGFUSE DIAGNOSTIC REPORT")
print("=" * 70)

# Set environment variables
os.environ["LANGFUSE_PUBLIC_KEY"] = settings.LANGFUSE_PUBLIC_KEY
os.environ["LANGFUSE_SECRET_KEY"] = settings.LANGFUSE_SECRET_KEY
os.environ["LANGFUSE_HOST"] = settings.LANGFUSE_HOST

print(f"\n📋 Configuration:")
print(f"   Host: {settings.LANGFUSE_HOST}")
print(f"   Public Key: {settings.LANGFUSE_PUBLIC_KEY}")
print(f"   Secret Key: {settings.LANGFUSE_SECRET_KEY}")

# Test 1: Docker connectivity
print(f"\n{'='*70}")
print("TEST 1: Docker Container Running")
print("=" * 70)
try:
    import subprocess
    result = subprocess.run(
        ["docker", "ps", "--filter", "name=stellar_langfuse", "--format", "{{.Names}}\t{{.Status}}"],
        capture_output=True,
        text=True
    )
    if "stellar_langfuse" in result.stdout:
        print(f"✅ Docker container running")
        print(f"   {result.stdout.strip()}")
    else:
        print(f"❌ Docker container not found!")
        print(f"   Run: docker-compose -f docker-compose.langfuse.yml up -d")
except Exception as e:
    print(f"❌ Docker check failed: {e}")

# Test 2: HTTP connectivity to Langfuse
print(f"\n{'='*70}")
print("TEST 2: HTTP Connection to Langfuse")
print("=" * 70)
try:
    response = requests.get(f"{settings.LANGFUSE_HOST}/api/public/health", timeout=5)
    if response.status_code == 200:
        print(f"✅ Langfuse HTTP endpoint reachable")
        print(f"   Status: {response.status_code}")
    else:
        print(f"⚠️  Langfuse responded with status: {response.status_code}")
except Exception as e:
    print(f"❌ Cannot reach Langfuse: {e}")
    print(f"   Make sure Docker container is running")

# Test 3: API Authentication
print(f"\n{'='*70}")
print("TEST 3: API Key Authentication")
print("=" * 70)
try:
    import base64
    
    # Create Basic Auth header
    credentials = f"{settings.LANGFUSE_PUBLIC_KEY}:{settings.LANGFUSE_SECRET_KEY}"
    encoded = base64.b64encode(credentials.encode()).decode()
    headers = {
        "Authorization": f"Basic {encoded}",
        "Content-Type": "application/json"
    }
    
    # Try to create a trace via API
    trace_data = {
        "name": "diagnostic-test-trace",
        "metadata": {"test": "diagnostic"}
    }
    
    response = requests.post(
        f"{settings.LANGFUSE_HOST}/api/public/traces",
        headers=headers,
        json=trace_data,
        timeout=5
    )
    
    if response.status_code in [200, 201]:
        print(f"✅ API authentication successful!")
        print(f"   Created test trace via REST API")
        print(f"   Trace ID: {response.json().get('id', 'N/A')}")
    else:
        print(f"❌ API authentication failed!")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
        print(f"\n   🔑 Your API keys may be incorrect.")
        print(f"   Please regenerate them at: {settings.LANGFUSE_HOST}")
except Exception as e:
    print(f"❌ API test failed: {e}")

# Test 4: Python SDK
print(f"\n{'='*70}")
print("TEST 4: Langfuse Python SDK")
print("=" * 70)
try:
    from langfuse import Langfuse
    
    client = Langfuse(
        public_key=settings.LANGFUSE_PUBLIC_KEY,
        secret_key=settings.LANGFUSE_SECRET_KEY,
        host=settings.LANGFUSE_HOST
    )
    
    # Create a generation (simple trace)
    generation = client.generation(
        name="sdk-test",
        metadata={"test": "python-sdk"},
        input="test input",
        output="test output"
    )
    
    # Flush to send
    client.flush()
    
    print(f"✅ Python SDK working!")
    print(f"   Created generation via SDK")
    
except Exception as e:
    print(f"❌ Python SDK failed: {e}")
    import traceback
    traceback.print_exc()

# Test 5: LangChain Callback
print(f"\n{'='*70}")
print("TEST 5: LangChain Callback Integration")
print("=" * 70)
try:
    from langfuse.callback import CallbackHandler
    
    handler = CallbackHandler()
    print(f"✅ CallbackHandler initialized")
    
    # Try with a fake LLM
    try:
        from langchain_core.messages import HumanMessage
        from langchain_core.language_models import FakeListChatModel
        
        llm = FakeListChatModel(responses=["test response from fake LLM"])
        
        response = llm.invoke(
            [HumanMessage(content="Hello test")],
            config={"callbacks": [handler]}
        )
        
        handler.flush()
        
        print(f"✅ LangChain callback executed!")
        print(f"   Response: {response}")
        
    except ImportError:
        print(f"⚠️  Could not test with FakeListChatModel")
        print(f"   LangChain Core may need to be updated")
        
except Exception as e:
    print(f"❌ LangChain callback failed: {e}")
    import traceback
    traceback.print_exc()

# Summary
print(f"\n{'='*70}")
print("📊 DIAGNOSTIC SUMMARY")
print("=" * 70)
print(f"""
✅ If all tests passed, traces should appear at:
   {settings.LANGFUSE_HOST}/project/cmgu23980006gahrcduruaw/traces

❌ If API authentication failed:
   1. Go to {settings.LANGFUSE_HOST}
   2. Settings → API Keys
   3. Delete old keys and create new ones
   4. Update .env file with new keys

🔧 If still not working:
   1. Check Docker logs: docker logs stellar_langfuse --tail 50
   2. Restart Langfuse: docker restart stellar_langfuse
   3. Verify API keys match in Langfuse UI
""")

