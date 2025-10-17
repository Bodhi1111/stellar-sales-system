#!/bin/bash
# Quick script to add Langfuse keys to .env

echo "🔍 Langfuse API Key Setup"
echo "=========================="
echo ""

# Prompt for keys
read -p "Enter your Langfuse Public Key: " PUBLIC_KEY
read -p "Enter your Langfuse Secret Key: " SECRET_KEY

# Add to .env
cat >> .env << EOF

# Langfuse (Open-Source Observability)
LANGFUSE_PUBLIC_KEY=$PUBLIC_KEY
LANGFUSE_SECRET_KEY=$SECRET_KEY
LANGFUSE_HOST=http://localhost:3000
EOF

echo ""
echo "✅ Langfuse keys added to .env"
echo ""
echo "🚀 Now run:"
echo "   python orchestrator/pipeline_langfuse.py"
echo ""
echo "📊 Then view traces at:"
echo "   http://localhost:3000"

