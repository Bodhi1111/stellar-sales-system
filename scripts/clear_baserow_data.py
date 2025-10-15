#!/usr/bin/env python3
"""
Clear all test data from Baserow tables while preserving table structure and fields.
"""
import requests
from config.settings import settings

BASEROW_TOKEN = settings.BASEROW_TOKEN
BASEROW_URL = settings.BASEROW_URL

# All Baserow table IDs
TABLES = {
    704: "Clients",
    705: "Meetings",
    706: "Deals",
    707: "Communications",
    708: "Sales Coaching",
    709: "Chunks"
}

def delete_all_rows(table_id: int, table_name: str):
    """Delete all rows from a Baserow table."""
    headers = {"Authorization": f"Token {BASEROW_TOKEN}"}

    # Get total count first
    response = requests.get(
        f"{BASEROW_URL}/api/database/rows/table/{table_id}/?size=1",
        headers=headers
    )

    if response.status_code != 200:
        print(f"❌ Failed to fetch rows from {table_name}: {response.text}")
        return

    data = response.json()
    row_count = data['count']

    print(f"\n📋 {table_name} (Table {table_id}): {row_count} rows")

    if row_count == 0:
        print(f"   ✅ Already empty")
        return

    # Delete all rows using pagination
    deleted = 0
    page_size = 200

    while deleted < row_count:
        # Fetch next page of rows
        response = requests.get(
            f"{BASEROW_URL}/api/database/rows/table/{table_id}/?size={page_size}",
            headers=headers
        )

        if response.status_code != 200:
            print(f"   ⚠️  Failed to fetch page: {response.text}")
            break

        rows = response.json()['results']

        if not rows:
            break

        # Delete each row in the page
        for row in rows:
            delete_response = requests.delete(
                f"{BASEROW_URL}/api/database/rows/table/{table_id}/{row['id']}/",
                headers=headers
            )

            if delete_response.status_code == 204:
                deleted += 1
                if deleted % 100 == 0:
                    print(f"   ... {deleted}/{row_count} rows deleted")
            else:
                print(f"   ⚠️  Failed to delete row {row['id']}: {delete_response.text}")

    print(f"   ✅ Deleted {deleted}/{row_count} rows")

if __name__ == "__main__":
    print("=" * 80)
    print("🧹 CLEARING ALL BASEROW TEST DATA")
    print("=" * 80)
    print("\n⚠️  This will delete ALL rows from the following tables:")
    for table_id, table_name in TABLES.items():
        print(f"   - {table_name} (Table {table_id})")

    print("\n⚠️  Table structures and field definitions will be preserved.")

    confirm = input("\nType 'YES' to confirm deletion: ")

    if confirm != "YES":
        print("❌ Cancelled")
        exit(0)

    print("\n🚀 Starting deletion...\n")

    for table_id, table_name in TABLES.items():
        delete_all_rows(table_id, table_name)

    print("\n" + "=" * 80)
    print("✅ ALL TEST DATA CLEARED")
    print("=" * 80)
