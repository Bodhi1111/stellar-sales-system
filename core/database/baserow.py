"""
BaserowManager - Handles all Baserow CRM operations
Syncs CRM data from PostgreSQL to Baserow for human-friendly interface

Uses baserow-client library with procedural API (not OOP table objects)
"""

import json
import requests
from typing import Dict, Any, Optional, List
from baserow.client import BaserowClient
from baserow.filter import Filter, FilterMode, FilterType
from config.settings import Settings


class BaserowManager:
    """
    Manages Baserow CRM database operations using baserow-client library.

    Architecture:
    - All tables use external_id (transcript_id from header) as primary key
    - Tables link via external_id matching (not Baserow link fields)
    - Uses procedural API: client.list_database_table_rows(table_id), etc.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = BaserowClient(url=settings.BASEROW_URL, token=settings.BASEROW_TOKEN)

        # Store table IDs for API calls (procedural API requires table_id parameter)
        self.clients_table_id = settings.BASEROW_CLIENTS_ID
        self.meetings_table_id = settings.BASEROW_MEETINGS_ID
        self.deals_table_id = settings.BASEROW_DEALS_ID
        self.communications_table_id = settings.BASEROW_COMMUNICATIONS_ID
        self.sales_coaching_table_id = settings.BASEROW_SALES_COACHING_ID

        # Initialize field name → field ID mappings for all tables
        # This is required because baserow-client needs field IDs (field_6790) not names (external_id)
        print("📋 Initializing Baserow field mappings...")
        self.clients_field_map = self._get_field_mapping(self.clients_table_id)
        self.meetings_field_map = self._get_field_mapping(self.meetings_table_id)
        self.deals_field_map = self._get_field_mapping(self.deals_table_id)
        self.communications_field_map = self._get_field_mapping(self.communications_table_id)
        self.sales_coaching_field_map = self._get_field_mapping(self.sales_coaching_table_id)
        print(f"   ✅ Field mappings loaded for 5 tables")

    async def sync_crm_data(self, crm_data: Dict[str, Any], transcript_id: str) -> Dict[str, Any]:
        """
        Main sync method - called by PersistenceAgent after PostgreSQL save.

        Args:
            crm_data: Complete CRM data from CRMAgent
            transcript_id: External ID from transcript header

        Returns:
            Dict with sync status
        """
        print(f"📊 BaserowManager: Syncing data for transcript {transcript_id}...")

        try:
            # Convert transcript_id to integer for Baserow (number field)
            external_id = int(transcript_id) if transcript_id.isdigit() else hash(transcript_id) % 10**8

            # Step 1: Upsert Client
            client_row = await self._upsert_client(crm_data, external_id)
            print(f"   ✅ Client synced: {client_row.get('client_name')} (external_id: {external_id})")

            # Step 2: Upsert Meeting
            meeting_row = await self._upsert_meeting(crm_data, external_id)
            print(f"   ✅ Meeting synced (external_id: {external_id})")

            # Step 3: Upsert Deal
            deal_row = await self._upsert_deal(crm_data, external_id)
            print(f"   ✅ Deal synced (external_id: {external_id})")

            # Step 4: Upsert Communication
            comm_row = await self._upsert_communication(crm_data, external_id)
            print(f"   ✅ Communication synced (external_id: {external_id})")

            # Step 5: Upsert Sales Coaching
            coaching_row = await self._upsert_sales_coaching(crm_data, external_id)
            print(f"   ✅ Sales Coaching synced (external_id: {external_id})")

            return {
                "status": "success",
                "external_id": external_id
            }

        except Exception as e:
            print(f"   ❌ Baserow sync failed: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "failed", "error": str(e)}

    def _get_field_mapping(self, table_id: int) -> Dict[str, str]:
        """
        Fetch field metadata from Baserow and create name → ID mapping.

        Uses REST API because baserow-client.list_database_table_fields() has deserialization issues.

        Returns:
            Dict mapping field names to field IDs, e.g. {"external_id": "field_6790", ...}
        """
        try:
            headers = {"Authorization": f"Token {self.settings.BASEROW_TOKEN}"}
            response = requests.get(
                f"{self.settings.BASEROW_URL}/api/database/fields/table/{table_id}/",
                headers=headers
            )
            response.raise_for_status()
            fields = response.json()

            # Create mapping: field_name → field_id
            return {field['name']: f"field_{field['id']}" for field in fields}
        except Exception as e:
            print(f"   ⚠️ Warning: Could not fetch field mapping for table {table_id}: {e}")
            return {}

    def _transform_to_field_ids(self, data: Dict[str, Any], field_map: Dict[str, str]) -> Dict[str, Any]:
        """
        Transform record data from field names to field IDs.

        Args:
            data: Record with field names as keys, e.g. {"external_id": 123, "client_name": "John"}
            field_map: Mapping from field names to IDs, e.g. {"external_id": "field_6790", ...}

        Returns:
            Record with field IDs as keys, e.g. {"field_6790": 123, "field_6791": "John"}
        """
        transformed = {}
        for field_name, value in data.items():
            field_id = field_map.get(field_name)
            if field_id:
                transformed[field_id] = value
            else:
                print(f"   ⚠️ Warning: Field '{field_name}' not found in Baserow schema, skipping")
        return transformed

    def _find_row_by_external_id(self, table_id: int, external_id: int) -> Optional[Dict[str, Any]]:
        """Find existing row by external_id using baserow-client API"""
        try:
            # Use Filter to search by external_id
            filter_obj = Filter(
                field="external_id",
                filter=FilterMode.equal,  # FilterMode.equal, not FilterType.EQUAL
                value=external_id  # Can be int, no need to convert to string
            )

            # list_database_table_rows returns a Page object
            result = self.client.list_database_table_rows(
                table_id=table_id,
                filter=[filter_obj]  # 'filter' not 'filters'
            )

            # Page object has .results attribute
            rows = result.results if hasattr(result, 'results') else result
            return rows[0] if rows else None
        except Exception as e:
            print(f"   Warning: Could not search for existing row: {e}")
            return None

    async def _upsert_client(self, crm_data: Dict[str, Any], external_id: int) -> Dict[str, Any]:
        """Upsert client using procedural API"""
        client_data = {
            "external_id": external_id,
            "client_name": crm_data.get("client_name", crm_data.get("customer_name", "Unknown")),
            "email": crm_data.get("client_email", crm_data.get("email", "")),
            "marital_status": crm_data.get("marital_status", ""),
            "children_count": int(crm_data.get("children_count", 0)),
            "estate_value": int(crm_data.get("estate_value", 0)),
            "real_estate_count": int(crm_data.get("real_estate_count", 0)),
            "crm_json": json.dumps(crm_data, indent=2)
        }

        # Transform field names to field IDs
        client_data_with_ids = self._transform_to_field_ids(client_data, self.clients_field_map)

        existing_row = self._find_row_by_external_id(self.clients_table_id, external_id)

        if existing_row:
            # Update existing row
            return self.client.update_database_table_row(
                table_id=self.clients_table_id,
                row_id=existing_row['id'],
                record=client_data_with_ids
            )
        else:
            # Create new row
            return self.client.create_database_table_row(
                table_id=self.clients_table_id,
                record=client_data_with_ids
            )

    async def _upsert_meeting(self, crm_data: Dict[str, Any], external_id: int) -> Dict[str, Any]:
        """Upsert meeting using procedural API"""
        # Map outcome to Baserow options
        outcome = crm_data.get("outcome", "Pending")
        meeting_outcome_map = {
            "Won": "Won",
            "Lost": "Lost",
            "Pending": "Follow-up",
            "Follow-up Scheduled": "Follow-up",
            "Needs More Info": "Follow-up"
        }
        meeting_outcome = meeting_outcome_map.get(outcome, "Follow-up")

        meeting_data = {
            "external_id": external_id,
            "client_external_id": external_id,
            "meeting_date": crm_data.get("meeting_date", ""),
            "transcript_filename": crm_data.get("transcript_filename", ""),
            "summary": crm_data.get("transcript_summary", ""),
            "meeting_outcome": meeting_outcome
        }

        # Transform field names to field IDs
        meeting_data_with_ids = self._transform_to_field_ids(meeting_data, self.meetings_field_map)

        existing_row = self._find_row_by_external_id(self.meetings_table_id, external_id)

        if existing_row:
            return self.client.update_database_table_row(
                table_id=self.meetings_table_id,
                row_id=existing_row['id'],
                record=meeting_data_with_ids
            )
        else:
            return self.client.create_database_table_row(
                table_id=self.meetings_table_id,
                record=meeting_data_with_ids
            )

    async def _upsert_deal(self, crm_data: Dict[str, Any], external_id: int) -> Dict[str, Any]:
        """Upsert deal using procedural API"""
        # Parse products and objections
        products_str = crm_data.get("product_discussed", "")
        products = []
        if "Estate Planning" in products_str:
            products.append("Estate Planning")
        if "Trust" in products_str or "Sub-trust" in products_str:
            products.append("Sub-trusts")
        if "LLC" in products_str:
            products.append("LLC")

        objections_str = crm_data.get("objections_raised", "")
        objections = []
        if "price" in objections_str.lower() or "cost" in objections_str.lower():
            objections.append("Price")
        if "timing" in objections_str.lower():
            objections.append("Timing")
        if "spouse" in objections_str.lower():
            objections.append("Spouse")

        deal_data = {
            "external_id": external_id,
            "client_id": external_id,
            "meeting_id": external_id,
            "products_discussed": products,
            "deal_amount": float(crm_data.get("deal", 0)),
            "deposit_amount": float(crm_data.get("deposit", 0)),
            "next_action": crm_data.get("action_items", ""),
            "objections": objections
        }

        # Transform field names to field IDs
        deal_data_with_ids = self._transform_to_field_ids(deal_data, self.deals_field_map)

        existing_row = self._find_row_by_external_id(self.deals_table_id, external_id)

        if existing_row:
            return self.client.update_database_table_row(
                table_id=self.deals_table_id,
                row_id=existing_row['id'],
                record=deal_data_with_ids
            )
        else:
            return self.client.create_database_table_row(
                table_id=self.deals_table_id,
                record=deal_data_with_ids
            )

    async def _upsert_communication(self, crm_data: Dict[str, Any], external_id: int) -> Dict[str, Any]:
        """Upsert communication using procedural API"""
        social_content = crm_data.get("social_opportunities", {})
        if isinstance(social_content, str):
            social_text = social_content
        else:
            social_text = social_content.get("social_media_quote", crm_data.get("social_media_quote", ""))

        comm_data = {
            "external_id": external_id,
            "client_id": external_id,
            "meeting_id": external_id,
            "follow_up_email_draft": crm_data.get("follow_up_email_draft", crm_data.get("email_draft", "")),
            "facebook_social_media_post": social_text,
            "instagram_social_media_post": social_text,
            "linkedin_social_media_post": social_text,
            "client_quotes": crm_data.get("social_media_quote", "")
        }

        # Transform field names to field IDs
        comm_data_with_ids = self._transform_to_field_ids(comm_data, self.communications_field_map)

        existing_row = self._find_row_by_external_id(self.communications_table_id, external_id)

        if existing_row:
            return self.client.update_database_table_row(
                table_id=self.communications_table_id,
                row_id=existing_row['id'],
                record=comm_data_with_ids
            )
        else:
            return self.client.create_database_table_row(
                table_id=self.communications_table_id,
                record=comm_data_with_ids
            )

    async def _upsert_sales_coaching(self, crm_data: Dict[str, Any], external_id: int) -> Dict[str, Any]:
        """Upsert sales coaching using procedural API"""
        coaching_opportunities = crm_data.get("coaching_opportunities", "")
        if isinstance(coaching_opportunities, dict):
            coaching_opportunities = str(coaching_opportunities)

        coaching_data = {
            "external_id": external_id,
            "objection_rebuttals": coaching_opportunities,
            "question_based_selling_opportunities": coaching_opportunities
        }

        # Transform field names to field IDs
        coaching_data_with_ids = self._transform_to_field_ids(coaching_data, self.sales_coaching_field_map)

        existing_row = self._find_row_by_external_id(self.sales_coaching_table_id, external_id)

        if existing_row:
            return self.client.update_database_table_row(
                table_id=self.sales_coaching_table_id,
                row_id=existing_row['id'],
                record=coaching_data_with_ids
            )
        else:
            return self.client.create_database_table_row(
                table_id=self.sales_coaching_table_id,
                record=coaching_data_with_ids
            )

    # === Query Methods for CRM Tool Agent (use procedural API) ===

    async def query_clients(self, filters: Optional[List[Filter]] = None) -> List[Dict[str, Any]]:
        """Query clients table"""
        return self.client.list_database_table_rows(
            table_id=self.clients_table_id,
            filters=filters or []
        )

    async def query_meetings(self, filters: Optional[List[Filter]] = None) -> List[Dict[str, Any]]:
        """Query meetings table"""
        return self.client.list_database_table_rows(
            table_id=self.meetings_table_id,
            filters=filters or []
        )

    async def query_deals(self, filters: Optional[List[Filter]] = None) -> List[Dict[str, Any]]:
        """Query deals table"""
        return self.client.list_database_table_rows(
            table_id=self.deals_table_id,
            filters=filters or []
        )

    async def query_communications(self, filters: Optional[List[Filter]] = None) -> List[Dict[str, Any]]:
        """Query communications table"""
        return self.client.list_database_table_rows(
            table_id=self.communications_table_id,
            filters=filters or []
        )

    async def query_sales_coaching(self, filters: Optional[List[Filter]] = None) -> List[Dict[str, Any]]:
        """Query sales coaching table"""
        return self.client.list_database_table_rows(
            table_id=self.sales_coaching_table_id,
            filters=filters or []
        )
