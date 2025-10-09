#!/usr/bin/env python3
"""Check select fields in all Baserow tables."""
import requests
import json

BASEROW_URL = "http://localhost:8080"
TOKEN = "6TElBEHaafiG4nmajttcnaN7TZEIioi7"

tables = {
    704: "Clients",
    705: "Meetings",
    706: "Deals",
    707: "Communications",
    708: "Sales Coaching"
}

for table_id, table_name in tables.items():
    print(f"\n=== {table_name} (Table {table_id}) ===")
    response = requests.get(
        f"{BASEROW_URL}/api/database/fields/table/{table_id}/",
        headers={"Authorization": f"Token {TOKEN}"}
    )
    fields = response.json()

    select_fields = [f for f in fields if 'select' in f.get('type', '')]
    if select_fields:
        for field in select_fields:
            print(f"  - {field['name']}: {field['type']}")
    else:
        print("  (no select fields)")
