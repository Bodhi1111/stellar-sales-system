#!/usr/bin/env python3
"""
Add missing fields to Baserow Chunks table.
"""

import requests
from config.settings import settings

BASEROW_URL = settings.BASEROW_URL
BASEROW_TOKEN = settings.BASEROW_TOKEN
CHUNKS_TABLE_ID = settings.BASEROW_CHUNKS_ID

headers = {"Authorization": f"Token {BASEROW_TOKEN}", "Content-Type": "application/json"}

# Define all required fields for Chunks table
fields_to_add = [
    {"name": "text", "type": "long_text"},
    {"name": "speaker_name", "type": "text"},
    {"name": "start_time", "type": "number", "number_decimal_places": 1},
    {"name": "end_time", "type": "number", "number_decimal_places": 1},
    {"name": "sales_stage", "type": "single_select", "select_options": [
        {"value": "Discovery", "color": "blue"},
        {"value": "Demo", "color": "green"},
        {"value": "Objection Handling", "color": "red"},
        {"value": "Closing", "color": "yellow"},
        {"value": "Unknown", "color": "light-gray"}
    ]},
    {"name": "conversation_phase", "type": "text"},
    {"name": "detected_topics", "type": "long_text"},
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
    {"name": "turn_count", "type": "number", "number_decimal_places": 0},
    {"name": "speaker_balance", "type": "number", "number_decimal_places": 2},
    {"name": "timestamp_start", "type": "text"},
    {"name": "timestamp_end", "type": "text"},
]

print(f"📋 Adding {len(fields_to_add)} fields to Chunks table (ID: {CHUNKS_TABLE_ID})...\n")

added_count = 0
for field in fields_to_add:
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
        f"{BASEROW_URL}/api/database/fields/table/{CHUNKS_TABLE_ID}/",
        headers=headers,
        json=field_payload
    )

    if response.status_code in [200, 201]:
        field_data = response.json()
        print(f"   ✅ Added: {field['name']:25} (field_{field_data['id']})")
        added_count += 1
    else:
        print(f"   ❌ Failed: {field['name']:25} - {response.status_code}")
        print(f"      Response: {response.text[:100]}")

print(f"\n✅ Added {added_count}/{len(fields_to_add)} fields successfully!")
print(f"\n🔄 Restart the pipeline to use the new field mappings.")
