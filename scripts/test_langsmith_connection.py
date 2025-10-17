#!/usr/bin/env python3
"""
Quick test to verify LangSmith connection works.
"""
import os
from config.settings import settings

# Set up LangSmith environment variables
if settings.LANGCHAIN_API_KEY:
    os.environ["LANGCHAIN_TRACING_V2"] = settings.LANGCHAIN_TRACING_V2
    os.environ["LANGCHAIN_ENDPOINT"] = settings.LANGCHAIN_ENDPOINT
    os.environ["LANGCHAIN_API_KEY"] = settings.LANGCHAIN_API_KEY
    os.environ["LANGCHAIN_PROJECT"] = settings.LANGCHAIN_PROJECT
    
    print("✅ LangSmith Configuration:")
    print(f"   Project: {settings.LANGCHAIN_PROJECT}")
    print(f"   Endpoint: {settings.LANGCHAIN_ENDPOINT}")
    print(f"   API Key: {settings.LANGCHAIN_API_KEY[:10]}...")
    print(f"   Tracing: {settings.LANGCHAIN_TRACING_V2}")
    
    # Test the connection
    try:
        from langsmith import Client
        client = Client()
        
        print("\n🔍 Testing connection to LangSmith...")
        
        # Try to get project info
        projects = list(client.list_projects(limit=1))
        print(f"✅ Successfully connected to LangSmith!")
        print(f"   Found {len(projects)} project(s)")
        
        print("\n📊 View your traces at:")
        print(f"   https://smith.langchain.com/")
        
    except Exception as e:
        print(f"\n❌ Failed to connect to LangSmith: {e}")
        print("\n🔧 Troubleshooting:")
        print("   1. Check your API key is correct")
        print("   2. Make sure you have internet connection")
        print("   3. Verify the API key hasn't expired")
        
else:
    print("❌ No LangSmith API key found in .env")
    print("\n📝 To set up LangSmith:")
    print("   1. Go to https://smith.langchain.com/")
    print("   2. Get your API key from Settings > API Keys")
    print("   3. Add to .env file:")
    print("      LANGCHAIN_API_KEY=your_key_here")

