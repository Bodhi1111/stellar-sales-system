#!/bin/bash
# Fix N8N Workflow URLs for Docker Networking
# This script directly updates the n8n SQLite database to fix localhost URLs

set -e

echo "🔧 Fixing N8N workflow URLs for Docker networking..."

# Stop n8n container to safely modify database
echo "📦 Stopping n8n container..."
docker stop stellar_n8n

# Wait for container to fully stop
sleep 2

# Backup the database
echo "💾 Creating database backup..."
docker cp stellar_n8n:/home/node/.n8n/database.sqlite /tmp/n8n_database_backup_$(date +%Y%m%d_%H%M%S).sqlite

# Create SQL update script
cat > /tmp/fix_n8n_urls.sql <<'EOF'
-- Fix Qdrant URLs (localhost:6333 -> stellar_qdrant:6333)
UPDATE workflow_entity
SET nodes = REPLACE(nodes, 'http://localhost:6333/', 'http://stellar_qdrant:6333/')
WHERE nodes LIKE '%localhost:6333%';

-- Fix Baserow URLs (localhost:8080 -> baserow:80)
UPDATE workflow_entity
SET nodes = REPLACE(nodes, 'http://localhost:8080/', 'http://baserow:80/')
WHERE nodes LIKE '%localhost:8080%';

-- Verify changes
SELECT
    name,
    CASE
        WHEN nodes LIKE '%stellar_qdrant:6333%' THEN 'Qdrant: FIXED ✓'
        WHEN nodes LIKE '%localhost:6333%' THEN 'Qdrant: NEEDS FIX ✗'
        ELSE 'Qdrant: N/A'
    END as qdrant_status,
    CASE
        WHEN nodes LIKE '%baserow:80%' THEN 'Baserow: FIXED ✓'
        WHEN nodes LIKE '%localhost:8080%' THEN 'Baserow: NEEDS FIX ✗'
        ELSE 'Baserow: N/A'
    END as baserow_status
FROM workflow_entity
WHERE name = 'Stellar Sales System';
EOF

echo "🔍 Applying URL fixes to database..."

# Copy SQL script into container
docker cp /tmp/fix_n8n_urls.sql stellar_n8n:/tmp/fix_n8n_urls.sql

# Execute SQL script
docker start stellar_n8n
sleep 3
docker exec stellar_n8n sqlite3 /home/node/.n8n/database.sqlite < /tmp/fix_n8n_urls.sql

echo "✅ URLs fixed!"
echo ""
echo "📊 Verification:"
docker exec stellar_n8n sqlite3 /home/node/.n8n/database.sqlite "SELECT name FROM workflow_entity WHERE nodes LIKE '%stellar_qdrant:6333%' AND name = 'Stellar Sales System';" | grep -q "Stellar" && echo "  ✓ Qdrant URLs updated" || echo "  ✗ Qdrant URLs NOT updated"
docker exec stellar_n8n sqlite3 /home/node/.n8n/database.sqlite "SELECT name FROM workflow_entity WHERE nodes LIKE '%baserow:80%' AND name = 'Stellar Sales System';" | grep -q "Stellar" && echo "  ✓ Baserow URLs updated" || echo "  ✗ Baserow URLs NOT updated"

echo ""
echo "🔄 Restarting n8n container to apply changes..."
docker restart stellar_n8n

echo ""
echo "✨ Done! The workflow should now work correctly."
echo "   Open n8n at http://localhost:5678 and test the workflow."
