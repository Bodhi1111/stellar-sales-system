"""
Diagnostic test to isolate Baserow filter functionality issue
Tests multiple approaches to see which one actually works
"""
import requests
from config.settings import settings
from baserow.filter import Filter, FilterMode
from baserow.client import BaserowClient
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_baserow_filter_approaches():
    """Test different approaches to filtering Baserow data"""
    print("=" * 70)
    print("BASEROW FILTER DIAGNOSTIC TEST")
    print("=" * 70)

    client = BaserowClient(url=settings.BASEROW_URL,
                           token=settings.BASEROW_TOKEN)
    table_id = settings.BASEROW_CLIENTS_ID

    # We know this external_id does NOT exist in the database
    nonexistent_id = 99999999
    # We know this external_id DOES exist (from previous test)
    existing_id = 83116306

    print(f"\n📊 Testing against Clients table (ID: {table_id})")
    print(f"   Searching for NONEXISTENT external_id: {nonexistent_id}")
    print(f"   Searching for EXISTING external_id: {existing_id}")
    print()

    # ============================================================
    # APPROACH 1: Current implementation (filter parameter)
    # ============================================================
    print("=" * 70)
    print("APPROACH 1: Using 'filter' parameter (CURRENT)")
    print("=" * 70)

    try:
        filter_obj = Filter(field="external_id",
                            filter=FilterMode.equal, value=nonexistent_id)
        result = client.list_database_table_rows(
            table_id=table_id, filter=[filter_obj])
        rows = result.results if hasattr(result, 'results') else result
        print(f"✅ API call succeeded")
        print(
            f"📊 Rows returned for NONEXISTENT ID {nonexistent_id}: {len(rows)}")
        print(f"   Expected: 0 rows")
        print(
            f"   Result: {'❌ FAIL - Filter not working!' if len(rows) > 0 else '✅ PASS'}")
    except Exception as e:
        print(f"❌ Error: {e}")

    print()

    try:
        filter_obj = Filter(field="external_id",
                            filter=FilterMode.equal, value=existing_id)
        result = client.list_database_table_rows(
            table_id=table_id, filter=[filter_obj])
        rows = result.results if hasattr(result, 'results') else result
        print(f"✅ API call succeeded")
        print(f"📊 Rows returned for EXISTING ID {existing_id}: {len(rows)}")
        print(f"   Expected: 1 row")
        print(f"   Result: {'✅ PASS' if len(rows) == 1 else '❌ FAIL'}")
    except Exception as e:
        print(f"❌ Error: {e}")

    # ============================================================
    # APPROACH 2: Try 'filters' parameter (plural)
    # ============================================================
    print("\n" + "=" * 70)
    print("APPROACH 2: Using 'filters' parameter (PLURAL)")
    print("=" * 70)

    try:
        filter_obj = Filter(field="external_id",
                            filter=FilterMode.equal, value=nonexistent_id)
        result = client.list_database_table_rows(
            table_id=table_id, filters=[filter_obj])
        rows = result.results if hasattr(result, 'results') else result
        print(f"✅ API call succeeded")
        print(
            f"📊 Rows returned for NONEXISTENT ID {nonexistent_id}: {len(rows)}")
        print(f"   Expected: 0 rows")
        print(
            f"   Result: {'❌ FAIL - Filter not working!' if len(rows) > 0 else '✅ PASS'}")
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")

    # ============================================================
    # APPROACH 3: Direct REST API with query parameters
    # ============================================================
    print("\n" + "=" * 70)
    print("APPROACH 3: Direct REST API with query parameters")
    print("=" * 70)

    try:
        headers = {"Authorization": f"Token {settings.BASEROW_TOKEN}"}
        url = f"{settings.BASEROW_URL}/api/database/rows/table/{table_id}/?user_field_names=true&filter__external_id__equal={nonexistent_id}"
        print(f"🌐 URL: {url}")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        print(f"✅ API call succeeded")
        print(
            f"📊 Rows returned for NONEXISTENT ID {nonexistent_id}: {data['count']}")
        print(f"   Expected: 0 rows")
        print(
            f"   Result: {'❌ FAIL' if data['count'] > 0 else '✅ PASS - REST API filter works!'}")
    except Exception as e:
        print(f"❌ Error: {e}")

    print()

    try:
        headers = {"Authorization": f"Token {settings.BASEROW_TOKEN}"}
        url = f"{settings.BASEROW_URL}/api/database/rows/table/{table_id}/?user_field_names=true&filter__external_id__equal={existing_id}"
        print(f"🌐 URL: {url}")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        print(f"✅ API call succeeded")
        print(
            f"📊 Rows returned for EXISTING ID {existing_id}: {data['count']}")
        print(f"   Expected: 1 row")
        if data['count'] == 1:
            print(f"   Row ID: {data['results'][0]['id']}")
            print(f"   external_id: {data['results'][0]['external_id']}")
        print(
            f"   Result: {'✅ PASS - REST API filter works!' if data['count'] == 1 else '❌ FAIL'}")
    except Exception as e:
        print(f"❌ Error: {e}")

    # ============================================================
    # APPROACH 4: Use field ID instead of field name
    # ============================================================
    print("\n" + "=" * 70)
    print("APPROACH 4: Using field ID instead of field name")
    print("=" * 70)

    # Get field mapping
    try:
        headers = {"Authorization": f"Token {settings.BASEROW_TOKEN}"}
        response = requests.get(
            f"{settings.BASEROW_URL}/api/database/fields/table/{table_id}/",
            headers=headers
        )
        response.raise_for_status()
        fields = response.json()
        field_map = {field['name']: f"field_{field['id']}" for field in fields}
        external_id_field_id = field_map.get("external_id")

        print(f"📋 Field ID for 'external_id': {external_id_field_id}")

        if external_id_field_id:
            filter_obj = Filter(field=external_id_field_id,
                                filter=FilterMode.equal, value=nonexistent_id)
            result = client.list_database_table_rows(
                table_id=table_id, filter=[filter_obj])
            rows = result.results if hasattr(result, 'results') else result
            print(f"✅ API call succeeded")
            print(
                f"📊 Rows returned for NONEXISTENT ID {nonexistent_id}: {len(rows)}")
            print(f"   Expected: 0 rows")
            print(
                f"   Result: {'❌ FAIL' if len(rows) > 0 else '✅ PASS - Field ID works!'}")
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")

    print("\n" + "=" * 70)
    print("DIAGNOSTIC TEST COMPLETE")
    print("=" * 70)
    print("\nℹ️ Review the results above to identify which approach works correctly.")


if __name__ == "__main__":
    test_baserow_filter_approaches()
