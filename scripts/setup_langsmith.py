#!/usr/bin/env python3
"""
Quick setup script to add LangSmith configuration to your .env file.
Run this after getting your LangSmith API key.
"""

from pathlib import Path
import sys


def setup_langsmith(api_key: str):
    """Add LangSmith configuration to .env file"""
    
    env_file = Path(__file__).parent.parent / ".env"
    
    if not env_file.exists():
        print("❌ .env file not found!")
        print("📝 Creating from template...")
        
        env_example = Path(__file__).parent.parent / "env.example"
        if env_example.exists():
            import shutil
            shutil.copy(env_example, env_file)
            print("✅ Created .env from env.example")
        else:
            print("❌ env.example not found either!")
            return False
    
    # Read current .env
    env_content = env_file.read_text()
    
    # Check if LangSmith is already configured
    if "LANGCHAIN_API_KEY=" in env_content and "your_langsmith_api_key_here" not in env_content:
        print("⚠️  LangSmith appears to be already configured")
        response = input("Do you want to update it? (y/n): ")
        if response.lower() != 'y':
            print("ℹ️  Keeping existing configuration")
            return True
    
    # Add or update LangSmith configuration
    langsmith_config = f"""
# ==============================================
# OBSERVABILITY & MONITORING
# ==============================================

# LangSmith (LangChain observability platform)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_API_KEY={api_key}
LANGCHAIN_PROJECT=stellar-sales-system
"""
    
    # Remove old config if present
    if "# OBSERVABILITY & MONITORING" in env_content:
        # Find the section and replace it
        lines = env_content.split('\n')
        new_lines = []
        skip = False
        
        for line in lines:
            if "# OBSERVABILITY & MONITORING" in line:
                skip = True
                continue
            elif skip and line.startswith("# ==="):
                skip = False
                new_lines.append(line)
            elif not skip:
                new_lines.append(line)
        
        env_content = '\n'.join(new_lines)
    
    # Add new config before OPTIONAL INTEGRATIONS section
    if "# OPTIONAL INTEGRATIONS" in env_content:
        env_content = env_content.replace(
            "# ==============================================\n# OPTIONAL INTEGRATIONS",
            langsmith_config.strip() + "\n\n# ==============================================\n# OPTIONAL INTEGRATIONS"
        )
    else:
        # Add at the end
        env_content += langsmith_config
    
    # Write back to file
    env_file.write_text(env_content)
    
    print("✅ LangSmith configuration added to .env")
    return True


def main():
    """Main entry point"""
    
    print("=" * 60)
    print("🔍 LangSmith Setup for Stellar Sales System")
    print("=" * 60)
    print()
    
    # Check if API key provided as argument
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
    else:
        # Prompt for API key
        print("📝 Enter your LangSmith API key")
        print("   (Get it from: https://smith.langchain.com/ → Settings → API Keys)")
        print()
        api_key = input("API Key: ").strip()
    
    if not api_key:
        print("❌ No API key provided")
        return
    
    if not api_key.startswith("ls__"):
        print("⚠️  Warning: LangSmith API keys usually start with 'ls__'")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            print("ℹ️  Cancelled")
            return
    
    # Set up LangSmith
    if setup_langsmith(api_key):
        print()
        print("=" * 60)
        print("✅ SETUP COMPLETE!")
        print("=" * 60)
        print()
        print("🚀 Next steps:")
        print()
        print("1. Test with a sample transcript:")
        print("   python orchestrator/pipeline.py")
        print()
        print("2. View your traces at:")
        print("   https://smith.langchain.com/")
        print()
        print("3. Set up file watching (optional):")
        print("   python scripts/watch_transcripts.py")
        print()
    else:
        print("❌ Setup failed")


if __name__ == "__main__":
    main()

