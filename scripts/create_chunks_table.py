#!/usr/bin/env python3
"""
Create Chunks table in Baserow for parent-child chunk metadata storage.

This table stores all chunks (header, parent, child) with rich metadata for:
- Human annotation and correction of sales_stage, topics, intent, sentiment
- Surgical filtering during retrieval
- Data quality audits and improvements

NOTE: This script requires manual table creation in Baserow UI due to API limitations.
      It will guide you through the process and generate the field schema.
"""

import requests
import json
from config.settings import settings

BASEROW_URL = settings.BASEROW_URL
BASEROW_TOKEN = settings.BASEROW_TOKEN
DATABASE_ID = settings.BASEROW_DATABASE_ID


def create_chunks_table():
    """
    Generate instructions for creating Chunks table in Baserow.

    Due to API limitations with table creation, this will:
    1. List the required table structure
    2. Provide manual steps for creation
    3. Show how to add fields via API once table exists
    """

    print("📋 Chunks Table Schema for Baserow")
    print("=" * 60)
    print(f"\nDue to API limitations, please create the table manually:")
    print(f"\n1. Open Baserow at {BASEROW_URL}")
    print(f"2. Navigate to Database ID {DATABASE_ID}")
    print(f"3. Click '+ Add table' and name it 'Chunks'")
    print(f"4. Note the Table ID that appears in the URL")
    print(f"5. Run this script again with --table-id <ID> to add fields\n")
    print("=" * 60)

    print("\n📝 Field Schema:")
    print("-" * 60)

    # Step 2: Define fields
    # Baserow creates default fields (Name), we'll add our custom fields

    fields = [
        # Core identifiers
        {"name": "chunk_id", "type": "text"},
        {"name": "parent_id", "type": "text"},
        {"name": "chunk_type", "type": "single_select", "select_options": [
            {"value": "header", "color": "blue"},
            {"value": "parent", "color": "green"},
            {"value": "child", "color": "orange"}
        ]},
        {"name": "external_id", "type": "number", "number_decimal_places": 0},
        {"name": "transcript_filename", "type": "text"},

        # Content
        {"name": "text", "type": "long_text"},

        # Speaker metadata (child chunks only)
        {"name": "speaker_name", "type": "text"},
        {"name": "start_time", "type": "number", "number_decimal_places": 1},
        {"name": "end_time", "type": "number", "number_decimal_places": 1},

        # Sales metadata (human editable!)
        {"name": "sales_stage", "type": "single_select", "select_options": [
            {"value": "Discovery", "color": "blue"},
            {"value": "Demo", "color": "green"},
            {"value": "Objection Handling", "color": "red"},
            {"value": "Closing", "color": "yellow"},
            {"value": "Unknown", "color": "light-gray"}
        ]},
        {"name": "conversation_phase", "type": "text"},
        {"name": "detected_topics", "type": "long_text"},

        # Semantic NLP metadata (human editable!)
        {"name": "intent", "type": "single_select", "select_options": [
            {"value": "question", "color": "blue"},
            {"value": "statement", "color": "green"},
            {"value": "objection", "color": "red"},
            {"value": "agreement", "color": "yellow"},
            {"value": "proposal", "color": "orange"},
            {"value": "clarification", "color": "light-blue"}
        ]},
        {"name": "sentiment", "type": "single_select", "select_options": [
            {"value": "positive", "color": "green"},
            {"value": "neutral", "color": "light-gray"},
            {"value": "negative", "color": "red"},
            {"value": "concerned", "color": "orange"},
            {"value": "excited", "color": "yellow"}
        ]},
        {"name": "discourse_marker", "type": "single_select", "select_options": [
            {"value": "transition", "color": "blue"},
            {"value": "confirmation", "color": "green"},
            {"value": "hedge", "color": "orange"},
            {"value": "emphasis", "color": "red"},
            {"value": "none", "color": "light-gray"}
        ]},
        {"name": "contains_entity", "type": "boolean"},

        # Parent chunk metadata
        {"name": "turn_count", "type": "number", "number_decimal_places": 0},
        {"name": "speaker_balance", "type": "number", "number_decimal_places": 2},

        # Timestamps
        {"name": "timestamp_start", "type": "text"},
        {"name": "timestamp_end", "type": "text"},
    ]

    # Step 3: Add fields to table
    print(f"   📝 Adding {len(fields)} custom fields...")

    for field in fields:
        # Prepare field payload
        field_payload = {
            "name": field["name"],
            "type": field["type"]
        }

        # Add type-specific options
        if field["type"] == "single_select" and "select_options" in field:
            field_payload["select_options"] = field["select_options"]
        elif field["type"] == "number":
            field_payload["number_decimal_places"] = field.get("number_decimal_places", 0)

        response = requests.post(
            f"{BASEROW_URL}/api/database/fields/table/{table_id}/",
            headers=headers,
            json=field_payload
        )

        if response.status_code in [200, 201]:
            field_data = response.json()
            print(f"      ✅ Added field: {field['name']} (field_{field_data['id']})")
        else:
            print(f"      ❌ Failed to add field {field['name']}: {response.status_code}")
            print(f"         Response: {response.text}")

    print(f"\n✅ Chunks table created successfully!")
    print(f"   Table ID: {table_id}")
    print(f"   Add this to your .env file:")
    print(f"   BASEROW_CHUNKS_ID={table_id}")

    return table_id


if __name__ == "__main__":
    create_chunks_table()
