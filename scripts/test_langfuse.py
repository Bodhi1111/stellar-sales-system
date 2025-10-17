#!/usr/bin/env python3
"""
Test Langfuse connection and create a simple trace.
"""
import os
from config.settings import settings

# Set up Langfuse environment variables
if settings.LANGFUSE_PUBLIC_KEY and settings.LANGFUSE_SECRET_KEY:
    os.environ["LANGFUSE_PUBLIC_KEY"] = settings.LANGFUSE_PUBLIC_KEY
    os.environ["LANGFUSE_SECRET_KEY"] = settings.LANGFUSE_SECRET_KEY
    os.environ["LANGFUSE_HOST"] = settings.LANGFUSE_HOST
    
    print("✅ Langfuse Configuration:")
    print(f"   Host: {settings.LANGFUSE_HOST}")
    print(f"   Public Key: {settings.LANGFUSE_PUBLIC_KEY[:20]}...")
    print(f"   Secret Key: {settings.LANGFUSE_SECRET_KEY[:20]}...")
    
    # Test the connection
    try:
        from langfuse import Langfuse
        
        print("\n🔍 Testing connection to Langfuse...")
        
        # Initialize client (this will test the connection)
        langfuse = Langfuse(
            public_key=settings.LANGFUSE_PUBLIC_KEY,
            secret_key=settings.LANGFUSE_SECRET_KEY,
            host=settings.LANGFUSE_HOST
        )
        
        # Test by fetching projects (this will verify auth)
        langfuse.auth_check()
        
        print(f"✅ Successfully connected to Langfuse!")
        print(f"\n📊 View your traces at:")
        print(f"   {settings.LANGFUSE_HOST}")
        print(f"\n🎉 Ready to run your pipeline with full observability!")
        print(f"\n🚀 Next step:")
        print(f"   python orchestrator/pipeline_langfuse.py")
        
    except Exception as e:
        print(f"\n❌ Failed to connect to Langfuse: {e}")
        print("\n🔧 Troubleshooting:")
        print("   1. Check your API keys are correct")
        print("   2. Make sure you have internet connection")
        print("   3. Verify the project exists in Langfuse")
        import traceback
        traceback.print_exc()
        
else:
    print("❌ No Langfuse keys found in .env")
    print("\n📝 Add to .env file:")
    print("   LANGFUSE_PUBLIC_KEY=your_public_key")
    print("   LANGFUSE_SECRET_KEY=your_secret_key")
    print("   LANGFUSE_HOST=https://us.cloud.langfuse.com")

