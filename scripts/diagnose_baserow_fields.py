"""
Diagnostic Script: Query Baserow API to identify field mapping mismatches

This script:
1. Fetches actual field names from Baserow for all tables
2. Compares with field names used in BaserowManager code
3. Identifies mismatches causing "Field not found" warnings
4. Generates a fix report

Usage:
    python scripts/diagnose_baserow_fields.py
"""

import os
import requests
from dotenv import load_dotenv
from typing import Dict, List

# Load environment
load_dotenv()

BASEROW_URL = os.getenv("BASEROW_URL", "http://localhost:8080")
BASEROW_TOKEN = os.getenv("BASEROW_TOKEN")

# Table IDs
TABLES = {
    "Clients": int(os.getenv("BASEROW_CLIENTS_ID", 704)),
    "Meetings": int(os.getenv("BASEROW_MEETINGS_ID", 705)),
    "Deals": int(os.getenv("BASEROW_DEALS_ID", 706)),
    "Communications": int(os.getenv("BASEROW_COMMUNICATIONS_ID", 707)),
    "Sales Coaching": int(os.getenv("BASEROW_SALES_COACHING_ID", 708)),
    "Chunks": int(os.getenv("BASEROW_CHUNKS_ID", 709)),
}

# Fields used in code (from baserow.py analysis)
CODE_FIELDS = {
    "Clients": [
        "external_id", "client_name", "email", "children_count",
        "estate_value", "real_estate_count", "marital_status", "crm_json"
    ],
    "Meetings": [
        "external_id", "client_external_id", "client_name", "transcript_filename",
        "meeting_title", "sales_rep", "duration_minutes", "summary",
        "meeting_outcome", "meeting_date"
    ],
    "Deals": [
        "external_id", "client_id", "meeting_id", "client_name", "stage",
        "products_discussed", "deal_amount", "deposit_amount", "win_probability",
        "next_action", "objections", "close_date"
    ],
    "Communications": [
        "external_id", "client_id", "meeting_id", "client_name",
        "follow_up_email_draft", "facebook_social_media_post",
        "instagram_social_media_post", "linkedin_social_media_post",
        "client_quotes"
    ],
    "Sales Coaching": [
        "external_id", "client_name", "objection_rebuttals",
        "question_based_selling_opportunities"
    ],
}


def fetch_table_fields(table_id: int) -> Dict[str, str]:
    """
    Fetch field names and IDs from Baserow API.

    Returns:
        Dict mapping field_name → field_id
    """
    try:
        headers = {"Authorization": f"Token {BASEROW_TOKEN}"}
        response = requests.get(
            f"{BASEROW_URL}/api/database/fields/table/{table_id}/",
            headers=headers
        )
        response.raise_for_status()
        fields = response.json()

        return {field['name']: f"field_{field['id']}" for field in fields}
    except Exception as e:
        print(f"   ❌ Error fetching fields for table {table_id}: {e}")
        return {}


def main():
    print("=" * 80)
    print("BASEROW FIELD MAPPING DIAGNOSTIC")
    print("=" * 80)

    if not BASEROW_TOKEN:
        print("\n❌ ERROR: BASEROW_TOKEN not found in .env")
        print("   Please add your Baserow API token to .env file")
        return

    all_mismatches = []

    for table_name, table_id in TABLES.items():
        if table_name not in CODE_FIELDS:
            continue  # Skip Chunks table (not in comparison)

        print(f"\n{'=' * 80}")
        print(f"TABLE: {table_name} (ID: {table_id})")
        print(f"{'=' * 80}")

        # Fetch actual Baserow fields
        baserow_fields = fetch_table_fields(table_id)
        if not baserow_fields:
            print("   ⚠️  Could not fetch fields from Baserow")
            continue

        print(f"\n✅ Baserow Fields ({len(baserow_fields)}):")
        for name, field_id in sorted(baserow_fields.items()):
            print(f"   - {name:40s} → {field_id}")

        # Fields used in code
        code_fields = CODE_FIELDS[table_name]
        print(f"\n📝 Code References ({len(code_fields)}):")
        for field in sorted(code_fields):
            print(f"   - {field}")

        # Find mismatches
        mismatches = []
        for code_field in code_fields:
            if code_field not in baserow_fields:
                mismatches.append(code_field)

        if mismatches:
            print(f"\n🔴 MISMATCHES FOUND ({len(mismatches)}):")
            for field in mismatches:
                print(f"   ❌ '{field}' - used in code but NOT in Baserow schema")
                all_mismatches.append((table_name, field))
        else:
            print(f"\n✅ No mismatches - all code fields exist in Baserow")

        # Find extra fields
        extra = [f for f in baserow_fields if f not in code_fields]
        if extra:
            print(f"\n📌 Extra Fields in Baserow (not used in code):")
            for field in extra:
                print(f"   • {field}")

    # Summary
    print(f"\n{'=' * 80}")
    print("SUMMARY")
    print(f"{'=' * 80}")

    if all_mismatches:
        print(f"\n🔴 Found {len(all_mismatches)} field mapping issues:")
        for table, field in all_mismatches:
            print(f"   - {table:20s} → {field}")

        print(f"\n💡 RECOMMENDED FIXES:")
        print(f"   1. Update code to use correct Baserow field names")
        print(f"   2. OR add missing fields to Baserow schema")
        print(f"   3. Check GEORGE_PADRON_EVALUATION_REPORT.md for known issues")
    else:
        print(f"\n✅ No field mapping issues found!")
        print(f"   All code field references match Baserow schema")

    print(f"\n{'=' * 80}")


if __name__ == "__main__":
    main()
