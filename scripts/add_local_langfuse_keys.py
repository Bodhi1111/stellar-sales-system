#!/usr/bin/env python3
"""
Quick script to add LOCAL Langfuse API keys to .env
"""
from pathlib import Path

def update_env_file():
    print("🔑 Add Local Langfuse API Keys")
    print("=" * 50)
    print("\nGet these from: http://localhost:3000")
    print("  Settings → API Keys\n")
    
    public_key = input("Enter your Langfuse Public Key: ").strip()
    secret_key = input("Enter your Langfuse Secret Key: ").strip()
    
    if not public_key or not secret_key:
        print("❌ Both keys are required!")
        return
    
    env_path = Path(__file__).parent.parent / ".env"
    
    # Remove old Langfuse entries
    if env_path.exists():
        lines = env_path.read_text().splitlines()
        lines = [l for l in lines if not l.startswith("LANGFUSE_")]
        env_path.write_text("\n".join(lines) + "\n")
    
    # Add new keys
    with open(env_path, "a") as f:
        f.write("\n# Langfuse (Local Self-Hosted)\n")
        f.write(f"LANGFUSE_PUBLIC_KEY={public_key}\n")
        f.write(f"LANGFUSE_SECRET_KEY={secret_key}\n")
        f.write(f"LANGFUSE_HOST=http://localhost:3000\n")
    
    print("\n✅ Keys added to .env!")
    print("\n🚀 Next step:")
    print("   python orchestrator/pipeline_langfuse.py")
    print("\n📊 View traces at:")
    print("   http://localhost:3000")

if __name__ == "__main__":
    update_env_file()

