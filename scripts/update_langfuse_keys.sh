#!/bin/bash
# Quick script to update Langfuse keys in .env

echo "🔑 Update Langfuse API Keys"
echo "============================"
echo ""
echo "Get your keys from: http://localhost:3000"
echo "  Settings → API Keys → Create new API keys"
echo ""

read -p "Enter your NEW Public Key (pk-lf-...): " PUBLIC_KEY
read -p "Enter your NEW Secret Key (sk-lf-...): " SECRET_KEY

# Remove old Langfuse entries
grep -v "LANGFUSE" .env > .env.tmp && mv .env.tmp .env

# Add new keys
cat >> .env << EOF

# Langfuse (Local Self-Hosted Observability)
LANGFUSE_PUBLIC_KEY=$PUBLIC_KEY
LANGFUSE_SECRET_KEY=$SECRET_KEY
LANGFUSE_HOST=http://localhost:3000
EOF

echo ""
echo "✅ Keys updated in .env!"
echo ""
echo "🧪 Now test the connection:"
echo "   python scripts/diagnose_langfuse.py"

