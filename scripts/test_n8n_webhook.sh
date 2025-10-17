#!/bin/bash
# Quick test script for N8N webhook trigger

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Default test file
TEST_FILE="${PROJECT_ROOT}/data/transcripts/test_sprint01.txt"

# Check if file exists
if [ ! -f "$TEST_FILE" ]; then
    echo "❌ Test file not found: $TEST_FILE"
    exit 1
fi

echo "🧪 Testing N8N Webhook Trigger"
echo "================================"
echo ""
echo "Test file: $(basename "$TEST_FILE")"
echo "File size: $(du -h "$TEST_FILE" | cut -f1)"
echo ""

# Activate venv if it exists
if [ -d "${PROJECT_ROOT}/venv" ]; then
    source "${PROJECT_ROOT}/venv/bin/activate"
fi

# Run trigger script
python3 "${SCRIPT_DIR}/trigger_n8n_workflow.py" --file "$TEST_FILE"

echo ""
echo "✅ Test complete!"
echo ""
echo "📊 To view results:"
echo "   - N8N UI:      http://localhost:5678"
echo "   - Qdrant:      http://localhost:6333/dashboard"
echo "   - Baserow CRM: http://localhost:8080"
echo ""
