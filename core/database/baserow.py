"""
BaserowManager - Handles all Baserow CRM operations
Syncs CRM data from PostgreSQL to Baserow for human-friendly interface

Uses baserow-client library with procedural API (not OOP table objects)
"""

import json
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime
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
        self.client = BaserowClient(
            url=settings.BASEROW_URL, token=settings.BASEROW_TOKEN)

        # Store table IDs for API calls (procedural API requires table_id parameter)
        self.clients_table_id = settings.BASEROW_CLIENTS_ID
        self.meetings_table_id = settings.BASEROW_MEETINGS_ID
        self.deals_table_id = settings.BASEROW_DEALS_ID
        self.communications_table_id = settings.BASEROW_COMMUNICATIONS_ID
        self.sales_coaching_table_id = settings.BASEROW_SALES_COACHING_ID
        self.chunks_table_id = settings.BASEROW_CHUNKS_ID  # NEW: Parent-child chunks

        # Initialize field name → field ID mappings for all tables
        # This is required because baserow-client needs field IDs (field_6790) not names (external_id)
        print("📋 Initializing Baserow field mappings...")
        self.clients_field_map = self._get_field_mapping(self.clients_table_id)
        self.meetings_field_map = self._get_field_mapping(
            self.meetings_table_id)
        self.deals_field_map = self._get_field_mapping(self.deals_table_id)
        self.communications_field_map = self._get_field_mapping(
            self.communications_table_id)
        self.sales_coaching_field_map = self._get_field_mapping(
            self.sales_coaching_table_id)
        self.chunks_field_map = self._get_field_mapping(self.chunks_table_id)  # NEW
        print(f"   ✅ Field mappings loaded for 6 tables")

    async def sync_crm_data(self, crm_data: Dict[str, Any], transcript_id: str) -> Dict[str, Any]:
        """
        Main sync method - called by PersistenceAgent after PostgreSQL save.

        Args:
            crm_data: Complete CRM data from CRMAgent
            transcript_id: External ID from transcript header

        Returns:
            Dict with sync status
        """
        print(
            f"📊 BaserowManager: Syncing data for transcript {transcript_id}...")

        try:
            # Convert transcript_id to integer for Baserow (number field)
            external_id = int(transcript_id) if transcript_id.isdigit(
            ) else hash(transcript_id) % 10**8

            # Step 1: Upsert Client
            client_row = await self._upsert_client(crm_data, external_id)
            print(
                f"   ✅ Client synced: {client_row.get('client_name')} (external_id: {external_id})")

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
            print(
                f"   ⚠️ Warning: Could not fetch field mapping for table {table_id}: {e}")
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
                print(
                    f"   ⚠️ Warning: Field '{field_name}' not found in Baserow schema, skipping")
        return transformed

    def _find_row_by_external_id(self, table_id: int, external_id: int, field_map: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """
        Find existing row by external_id using baserow-client API.

        CRITICAL: baserow-client Filter requires field ID (e.g., "field_6790") not field name (e.g., "external_id")
        """
        print(
            f"   🔍 DEBUG: Searching for existing row in table {table_id} with external_id={external_id}")

        try:
            # Get the field ID for "external_id" from the field mapping
            external_id_field_id = field_map.get("external_id")
            if not external_id_field_id:
                print(
                    f"      ❌ ERROR: 'external_id' field not found in field mapping for table {table_id}")
                return None

            # Use Filter with FIELD ID (not field name)
            filter_obj = Filter(
                field=external_id_field_id,  # FIXED: Use field ID like "field_6790"
                filter=FilterMode.equal,
                value=external_id
            )
            print(
                f"      📋 Filter object created: field='{external_id_field_id}', filter=FilterMode.equal, value={external_id}")

            # list_database_table_rows returns a Page object
            print(f"      🌐 Calling list_database_table_rows with filter parameter...")
            result = self.client.list_database_table_rows(
                table_id=table_id,
                filter=[filter_obj]
            )
            print(f"      ✅ API call succeeded, result type: {type(result)}")

            # Page object has .results attribute
            rows = result.results if hasattr(result, 'results') else result
            print(f"      📊 Rows found: {len(rows) if rows else 0}")

            if rows:
                print(
                    f"      ✅ Found existing row with ID: {rows[0].get('id', 'N/A')}, external_id: {rows[0].get('external_id', 'N/A')}")
                return rows[0]
            else:
                print(
                    f"      ℹ️ No existing row found with external_id={external_id}")
                return None

        except Exception as e:
            print(
                f"      ❌ ERROR in _find_row_by_external_id: {type(e).__name__}: {e}")
            import traceback
            print(f"      📍 Stack trace:")
            traceback.print_exc()
            return None

    def _parse_date_to_iso8601(self, date_str: str) -> str:
        """
        Parse various date formats and convert to ISO 8601 with timezone (YYYY-MM-DDThh:mm:ssZ)

        Handles:
        - "October 03, 2025 at 15:30" (natural language from LLM)
        - "2025-10-03" (YYYY-MM-DD)
        - "2025-10-03T15:30:00Z" (already ISO 8601)
        - Empty string
        """
        print(f"      🔍 DATE PARSER INPUT: '{date_str}'")

        if not date_str or date_str.strip() == "":
            print(f"      ✅ DATE PARSER OUTPUT: '' (empty input)")
            return ""

        try:
            # Try parsing as ISO 8601 first (already in correct format)
            if "T" in date_str and ("Z" in date_str or "+" in date_str or date_str.count("-") > 2):
                print(f"      ✅ DATE PARSER OUTPUT: '{date_str}' (already ISO 8601)")
                return date_str

            # Try parsing YYYY-MM-DD format (date only)
            if len(date_str) == 10 and date_str.count("-") == 2:
                result = f"{date_str}T00:00:00Z"
                print(f"      ✅ DATE PARSER OUTPUT: '{result}' (from YYYY-MM-DD)")
                return result

            # Try parsing YYYY-MM-DDTHH:MM:SS format (without Z)
            if "T" in date_str and len(date_str) == 19:
                result = f"{date_str}Z"
                print(f"      ✅ DATE PARSER OUTPUT: '{result}' (added Z to ISO timestamp)")
                return result

            # Try parsing natural language format like "October 03, 2025 at 15:30"
            # Common LLM output patterns
            formats_to_try = [
                "%Y-%m-%dT%H:%M:%S",   # 2025-10-03T15:30:00 (ISO without Z)
                "%B %d, %Y at %H:%M",  # October 03, 2025 at 15:30
                "%B %d, %Y",           # October 03, 2025
                "%Y-%m-%d %H:%M:%S",   # 2025-10-03 15:30:00
                "%Y-%m-%d %H:%M",      # 2025-10-03 15:30
                "%m/%d/%Y",            # 10/03/2025
                "%d/%m/%Y",            # 03/10/2025
            ]

            for fmt in formats_to_try:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    result = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
                    print(f"      ✅ DATE PARSER OUTPUT: '{result}' (matched format: {fmt})")
                    return result
                except ValueError:
                    continue

            # If all parsing attempts fail, return empty string
            print(f"      ⚠️ WARNING: Could not parse date '{date_str}', returning empty string")
            return ""

        except Exception as e:
            print(f"      ❌ ERROR parsing date '{date_str}': {e}")
            return ""

    async def _upsert_client(self, crm_data: Dict[str, Any], external_id: int) -> Dict[str, Any]:
        """Upsert client using procedural API"""
        print(f"   👤 UPSERT CLIENT: external_id={external_id}")

        client_data = {
            "external_id": external_id,
            "client_name": crm_data.get("client_name", crm_data.get("customer_name", "Unknown")),
            "children_count": int(crm_data.get("children_count", 0)),
            "estate_value": int(crm_data.get("estate_value", 0)),
            "real_estate_count": int(crm_data.get("real_estate_count", 0)),
            "crm_json": json.dumps(crm_data, indent=2)
        }

        # Only include email if it has a valid value (Baserow email field rejects empty strings)
        email = crm_data.get("client_email", crm_data.get("email"))
        print(f"      📧 DEBUG: Email from CRM: '{email}'")
        if email and email.strip() and '@' in email:
            client_data["email"] = email
            print(f"      ✅ Email will be synced: {email}")
        else:
            print(f"      ⚠️ Email validation failed or empty: '{email}'")

        # Only include marital_status if it has a valid value (Baserow select fields reject empty strings)
        marital_status = crm_data.get("marital_status", "")
        if marital_status and marital_status.strip():
            client_data["marital_status"] = marital_status

        # Transform field names to field IDs
        client_data_with_ids = self._transform_to_field_ids(
            client_data, self.clients_field_map)
        print(
            f"      📝 Transformed {len(client_data_with_ids)} fields to field IDs")

        existing_row = self._find_row_by_external_id(
            self.clients_table_id, external_id, self.clients_field_map)

        if existing_row:
            # Update existing row
            print(
                f"      🔄 UPDATE path: Updating existing row ID {existing_row['id']}")
            result = self.client.update_database_table_row(
                table_id=self.clients_table_id,
                row_id=existing_row['id'],
                record=client_data_with_ids
            )
            print(f"      ✅ Update completed for row ID {existing_row['id']}")
            return result
        else:
            # Create new row
            print(
                f"      ✨ CREATE path: Creating new row with external_id={external_id}")
            result = self.client.create_database_table_row(
                table_id=self.clients_table_id,
                record=client_data_with_ids
            )
            print(
                f"      ✅ Create completed, new row ID: {result.get('id', 'N/A')}")
            return result

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

        # Format meeting_date for Baserow (ISO 8601 with timezone)
        # Combine meeting_date and meeting_time from header metadata for full timestamp
        meeting_date_raw = crm_data.get("meeting_date", "")
        meeting_time_raw = crm_data.get("meeting_time", "")
        meeting_date_formatted = ""

        if meeting_date_raw:
            # If we have both date and time, combine them into full ISO 8601 timestamp
            if meeting_time_raw:
                combined_datetime = f"{meeting_date_raw}T{meeting_time_raw}"
                meeting_date_formatted = self._parse_date_to_iso8601(combined_datetime)
            else:
                meeting_date_formatted = self._parse_date_to_iso8601(meeting_date_raw)

        # Generate transcript_filename from meeting_title (meeting_title + ".txt")
        meeting_title = crm_data.get("meeting_title", "")
        transcript_filename = f"{meeting_title}.txt" if meeting_title else crm_data.get("transcript_filename", "unknown.txt")

        meeting_data = {
            "external_id": external_id,
            "client_external_id": external_id,
            "client_name": crm_data.get("client_name", crm_data.get("customer_name", "")),
            "transcript_filename": transcript_filename,
            "meeting_title": meeting_title,  # NEW: Add meeting_title field
            "sales_rep": "J. Vaughan",  # NEW: Add sales_rep (currently only J. Vaughan)
            "duration_minutes": int(round(crm_data.get("duration_minutes", 0))),  # NEW: Add duration from header (rounded to integer)
            "summary": crm_data.get("transcript_summary", ""),
            "meeting_outcome": meeting_outcome
        }

        # Only include meeting_date if we have a valid ISO 8601 datetime
        # Baserow datetime fields reject empty strings
        if meeting_date_formatted and meeting_date_formatted.strip():
            meeting_data["meeting_date"] = meeting_date_formatted

        # Transform field names to field IDs
        meeting_data_with_ids = self._transform_to_field_ids(
            meeting_data, self.meetings_field_map)

        existing_row = self._find_row_by_external_id(
            self.meetings_table_id, external_id, self.meetings_field_map)

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
        print(f"   💰 UPSERT DEAL: external_id={external_id}")
        print(f"      🔍 DEBUG: deal={crm_data.get('deal', 'MISSING')}, deposit={crm_data.get('deposit', 'MISSING')}")

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

        # Format close_date if deal is Won
        close_date_raw = crm_data.get("close_date", "")
        close_date_formatted = ""
        if close_date_raw:
            close_date_iso = self._parse_date_to_iso8601(close_date_raw)
            # Baserow date field requires YYYY-MM-DD only (no time component)
            close_date_formatted = close_date_iso.split('T')[0] if close_date_iso else ""

        deal_amount = float(crm_data.get("deal", 0))
        deposit_amount = float(crm_data.get("deposit", 0))

        print(f"      💵 Parsed: deal_amount={deal_amount}, deposit_amount={deposit_amount}")

        # Map outcome to stage field
        outcome_to_stage_map = {
            "Won": "Closed Won",
            "Lost": "Closed Lost",
            "Follow-up Scheduled": "Follow up",
            "Pending": "Follow up",
            "Needs More Info": "Follow up"
        }
        stage = outcome_to_stage_map.get(crm_data.get("outcome", ""), "Follow up")

        deal_data = {
            "external_id": external_id,
            "client_id": external_id,
            "meeting_id": external_id,
            "client_name": crm_data.get("client_name", crm_data.get("customer_name", "")),
            # REMOVED: "stage" field - doesn't exist in Baserow schema (use meeting_outcome in Meetings table instead)
            "products_discussed": products,
            "deal_amount": deal_amount,
            "deposit_amount": deposit_amount,
            "win_probability": float(crm_data.get("win_probability", 0.5)),  # Win probability (0.0 to 1.0)
            "next_action": crm_data.get("action_items", ""),
            "objections": objections
        }

        # Only include close_date if we have a valid YYYY-MM-DD date
        if close_date_formatted and close_date_formatted.strip():
            deal_data["close_date"] = close_date_formatted

        # Transform field names to field IDs
        deal_data_with_ids = self._transform_to_field_ids(
            deal_data, self.deals_field_map)

        existing_row = self._find_row_by_external_id(
            self.deals_table_id, external_id, self.deals_field_map)

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
            social_text = social_content.get(
                "social_media_quote", crm_data.get("social_media_quote", ""))

        comm_data = {
            "external_id": external_id,
            "client_id": external_id,
            "meeting_id": external_id,
            "client_name": crm_data.get("client_name", crm_data.get("customer_name", "")),
            "follow_up_email_draft": crm_data.get("follow_up_email_draft", crm_data.get("email_draft", "")),
            "facebook_social_media_post": social_text,
            "instagram_social_media_post": social_text,
            "linkedin_social_media_post": social_text,
            "client_quotes": crm_data.get("social_media_quote", "")
        }

        # Transform field names to field IDs
        comm_data_with_ids = self._transform_to_field_ids(
            comm_data, self.communications_field_map)

        existing_row = self._find_row_by_external_id(
            self.communications_table_id, external_id, self.communications_field_map)

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
            "client_name": crm_data.get("client_name", crm_data.get("customer_name", "")),
            "objection_rebuttals": coaching_opportunities,
            "question_based_selling_opportunities": coaching_opportunities
        }

        # Transform field names to field IDs
        coaching_data_with_ids = self._transform_to_field_ids(
            coaching_data, self.sales_coaching_field_map)

        existing_row = self._find_row_by_external_id(
            self.sales_coaching_table_id, external_id, self.sales_coaching_field_map)

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

    # === Chunks Table Methods (Parent-Child Architecture) ===

    async def sync_chunks(self, chunks: List[Dict[str, Any]], transcript_id: str, transcript_filename: str) -> Dict[str, Any]:
        """
        Sync all chunks (header, parent, child) to Baserow Chunks table.

        This enables human-in-the-loop annotation and correction of:
        - sales_stage (Discovery/Demo/Objection Handling/Closing)
        - detected_topics (add missing, remove irrelevant)
        - intent, sentiment, discourse_marker

        Args:
            chunks: List of all chunks (from ChunkerAgent.run()['all_chunks'])
            transcript_id: External ID from header
            transcript_filename: Source filename for reference

        Returns:
            Dict with sync status and chunk count
        """
        print(f"📦 BaserowManager: Syncing {len(chunks)} chunks to Baserow...")

        try:
            external_id = int(transcript_id) if transcript_id.isdigit() else hash(transcript_id) % 10**8

            synced_count = 0
            for chunk in chunks:
                await self._upsert_chunk(chunk, external_id, transcript_filename)
                synced_count += 1

            print(f"   ✅ Synced {synced_count} chunks to Baserow (external_id: {external_id})")
            return {"status": "success", "synced_count": synced_count}

        except Exception as e:
            print(f"   ❌ Chunk sync failed: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "failed", "error": str(e)}

    async def _upsert_chunk(self, chunk: Dict[str, Any], external_id: int, transcript_filename: str) -> Dict[str, Any]:
        """
        Upsert individual chunk to Baserow.

        Uses chunk_id as unique identifier (chunks are never updated, only created).
        """
        # Prepare chunk data for Baserow
        chunk_data = {
            "chunk_id": chunk.get("chunk_id"),
            "parent_id": chunk.get("parent_id") or "",  # Empty string if None
            "chunk_type": chunk.get("chunk_type"),
            "external_id": external_id,
            "transcript_filename": transcript_filename,
            "text": chunk.get("text", ""),
            "speaker_name": chunk.get("speaker_name") or "",
            "start_time": float(chunk.get("start_time", 0.0)),
            "end_time": float(chunk.get("end_time", 0.0)),
            "conversation_phase": chunk.get("conversation_phase") or "",
            "timestamp_start": chunk.get("timestamp_start") or chunk.get("timestamp") or "",
            "timestamp_end": chunk.get("timestamp_end") or ""
        }

        # Baserow valid values for single_select fields
        VALID_SALES_STAGES = {
            "Setting up for meeting", "Assistant Intro Rep", "Greeting", "Client Motivation",
            "Set Meeting Agenda", "Establish Credibility", "Discovery", "Compare Options",
            "Present Solution", "Pricing", "Objection Handling", "Closing", "Unknown"
        }
        VALID_INTENTS = {"question", "statement", "objection", "agreement", "proposal", "clarification"}
        VALID_SENTIMENTS = {"positive", "neutral", "concerned", "excited"}  # NOTE: No "negative"
        VALID_DISCOURSE_MARKERS = {"transition", "confirmation", "hedge", "emphasis", "none"}

        # Add optional fields (only if not None/empty AND valid)
        sales_stage = chunk.get("sales_stage")
        if sales_stage and sales_stage in VALID_SALES_STAGES:
            chunk_data["sales_stage"] = sales_stage
        elif sales_stage:
            # Invalid value, use Unknown
            chunk_data["sales_stage"] = "Unknown"

        if chunk.get("detected_topics"):
            # Convert list to JSON string for storage
            topics = chunk.get("detected_topics")
            if isinstance(topics, list):
                chunk_data["detected_topics"] = json.dumps(topics)
            else:
                chunk_data["detected_topics"] = str(topics)

        intent = chunk.get("intent")
        if intent and intent in VALID_INTENTS:
            chunk_data["intent"] = intent

        sentiment = chunk.get("sentiment")
        if sentiment == "negative":
            # Map "negative" to "concerned" (Baserow doesn't have "negative")
            chunk_data["sentiment"] = "concerned"
        elif sentiment and sentiment in VALID_SENTIMENTS:
            chunk_data["sentiment"] = sentiment

        discourse_marker = chunk.get("discourse_marker")
        if discourse_marker and discourse_marker in VALID_DISCOURSE_MARKERS:
            chunk_data["discourse_marker"] = discourse_marker

        if chunk.get("contains_entity") is not None:
            chunk_data["contains_entity"] = bool(chunk.get("contains_entity"))

        if chunk.get("turn_count") is not None:
            chunk_data["turn_count"] = int(chunk.get("turn_count", 0))

        if chunk.get("speaker_balance") is not None:
            chunk_data["speaker_balance"] = float(chunk.get("speaker_balance", 0.0))

        # Transform to field IDs
        chunk_data_with_ids = self._transform_to_field_ids(chunk_data, self.chunks_field_map)

        # Check if chunk already exists (by chunk_id)
        existing_row = self._find_chunk_by_id(chunk.get("chunk_id"))

        if existing_row:
            # Update existing chunk
            return self.client.update_database_table_row(
                table_id=self.chunks_table_id,
                row_id=existing_row['id'],
                record=chunk_data_with_ids
            )
        else:
            # Create new chunk
            try:
                return self.client.create_database_table_row(
                    table_id=self.chunks_table_id,
                    record=chunk_data_with_ids
                )
            except Exception as e:
                print(f"      ❌ DEBUG: Failed to create chunk")
                print(f"         chunk_type: {chunk.get('chunk_type')}")
                print(f"         sales_stage: {chunk.get('sales_stage')}")
                print(f"         intent: {chunk.get('intent')}")
                print(f"         sentiment: {chunk.get('sentiment')}")
                print(f"         discourse_marker: {chunk.get('discourse_marker')}")
                print(f"         chunk_data_with_ids: {str(chunk_data_with_ids)[:300]}")
                print(f"         Error: {str(e)}")
                raise

    def _find_chunk_by_id(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        """
        Find existing chunk by chunk_id (UUID).

        Returns existing row or None.
        """
        if not chunk_id:
            return None

        try:
            chunk_id_field_id = self.chunks_field_map.get("chunk_id")
            if not chunk_id_field_id:
                return None

            filter_obj = Filter(
                field=chunk_id_field_id,
                filter=FilterMode.equal,
                value=chunk_id
            )

            result = self.client.list_database_table_rows(
                table_id=self.chunks_table_id,
                filter=[filter_obj]
            )

            rows = result.results if hasattr(result, 'results') else result
            return rows[0] if rows else None

        except Exception:
            return None
