#!/usr/bin/env python3
"""
Simple test to verify Langfuse connection and create a test trace.
"""
import os
from config.settings import settings

# Set environment variables
os.environ["LANGFUSE_PUBLIC_KEY"] = settings.LANGFUSE_PUBLIC_KEY
os.environ["LANGFUSE_SECRET_KEY"] = settings.LANGFUSE_SECRET_KEY
os.environ["LANGFUSE_HOST"] = settings.LANGFUSE_HOST

print(f"🔍 Testing Langfuse connection...")
print(f"   Host: {settings.LANGFUSE_HOST}")
print(f"   Public Key: {settings.LANGFUSE_PUBLIC_KEY[:20]}...")
print(f"   Secret Key: {settings.LANGFUSE_SECRET_KEY[:20]}...")

try:
    from langfuse.callback import CallbackHandler
    from langchain.schema import HumanMessage, AIMessage
    from langchain.llms.fake import FakeListLLM
    
    # Create handler
    handler = CallbackHandler()
    print(f"\n✅ Langfuse handler initialized")
    
    # Create a simple fake LLM call with the callback
    llm = FakeListLLM(responses=["Hello, this is a test response!"])
    
    # Make a call with the Langfuse callback
    result = llm.invoke("Test message", config={"callbacks": [handler]})
    
    print(f"✅ Test LLM call completed: {result}")
    
    # Flush to ensure trace is sent
    handler.flush()
    print(f"✅ Flushed trace to Langfuse")
    
    print(f"\n🎉 SUCCESS! Langfuse is working!")
    print(f"📊 Check your traces at: {settings.LANGFUSE_HOST}")
    print(f"   Look for a trace with 'FakeListLLM' in it")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    print(f"\n📋 Troubleshooting:")
    print(f"   1. Check that Langfuse is running: docker ps | grep langfuse")
    print(f"   2. Verify API keys match what's in Langfuse UI")
    print(f"   3. Check Langfuse logs: docker logs stellar_langfuse --tail 20")
    import traceback
    traceback.print_exc()

