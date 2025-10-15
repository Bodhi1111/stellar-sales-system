from typing import Dict, Any
from pathlib import Path
from sqlalchemy.dialects.postgresql import insert
import asyncio

from agents.base_agent import BaseAgent
from config.settings import Settings
from core.database.postgres import db_manager
from core.database.models import Transcript
from core.database.baserow import BaserowManager


class PersistenceAgent(BaseAgent):
    """
    Handles the final persistence of all extracted and generated data into
    both PostgreSQL and Baserow databases. It uses the transcript_id (stored
    as external_id) to create or update the record, making the operation idempotent.
    """

    def __init__(self, settings: Settings):
        super().__init__(settings)
        self.baserow_manager = BaserowManager(settings)

    async def run(self, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Saves the complete, final record to the database.

        Args:
            data: Dict containing:
                - transcript_id: Unique identifier from transcript header
                - file_path: Path to the transcript file
                - chunks: List of text chunks
                - extracted_entities: Extracted data from KnowledgeAnalystAgent
                - social_content: Social media content
                - email_draft: Generated email
                - crm_data: CRM-ready data

        Returns:
            Dict with "persistence_status": "success" or "error"
        """
        if not data:
            return {"persistence_status": "error", "message": "No data provided."}

        transcript_id = data.get("transcript_id")
        if not transcript_id:
            return {"persistence_status": "error", "message": "Missing transcript_id for persistence."}

        file_path = data.get("file_path")
        if not file_path or not isinstance(file_path, Path):
            return {"persistence_status": "error", "message": "Invalid or missing file_path."}

        print(
            f"💾 PersistenceAgent: Saving final record for transcript ID {transcript_id}...")

        try:
            await db_manager.initialize()
            async with db_manager.session_context() as session:

                # Handle chunks (can be list of strings OR list of dicts with 'text' key)
                chunks = data.get("chunks", [])
                if chunks and isinstance(chunks[0], dict):
                    chunk_texts = [c.get('text', str(c)) for c in chunks]
                else:
                    chunk_texts = chunks

                upsert_data = {
                    "external_id": transcript_id,
                    "filename": file_path.name,
                    "full_text": "\n".join(chunk_texts) if chunk_texts else "",
                    "extracted_data": data.get("extracted_entities", {}),
                    "social_content": data.get("social_content", {}),
                    "email_draft": data.get("email_draft", ""),
                    # Now correctly included
                    "crm_data": data.get("crm_data", {})
                }

                stmt = insert(Transcript).values(upsert_data)

                # Define what to do on conflict (if the external_id already exists)
                update_dict = {
                    key: stmt.excluded[key] for key in upsert_data.keys() if key != 'external_id'}

                on_conflict_stmt = stmt.on_conflict_do_update(
                    index_elements=['external_id'],
                    set_=update_dict
                )

                await session.execute(on_conflict_stmt)
                await session.commit()

            print(
                f"   ✅ Successfully saved final record to PostgreSQL for transcript ID {transcript_id}.")

            # Launch Baserow sync in background (fire-and-forget, non-blocking)
            print(f"   🚀 Launching Baserow sync in background (non-blocking)...")
            asyncio.create_task(
                self._sync_to_baserow_background(data, transcript_id, file_path)
            )

            return {"persistence_status": "success"}

        except Exception as e:
            print(f"   ❌ ERROR in PersistenceAgent: {type(e).__name__}: {e}")
            return {"persistence_status": "error", "message": str(e)}

    async def _sync_to_baserow_background(self, data: Dict[str, Any], transcript_id: str, file_path: Path):
        """
        Background task for Baserow sync (fire-and-forget).
        Runs asynchronously without blocking the main pipeline.
        """
        try:
            # 1. Sync CRM data (clients, meetings, deals, etc.)
            crm_data = data.get("crm_data", {})
            if crm_data:
                baserow_result = await self.baserow_manager.sync_crm_data(crm_data, transcript_id)
                if baserow_result.get("status") == "success":
                    print(
                        f"   ✅ [Background] Successfully synced CRM data to Baserow for transcript ID {transcript_id}.")
                else:
                    print(
                        f"   ⚠️ [Background] Baserow CRM sync failed: {baserow_result.get('error')}")
            else:
                print(f"   ⚠️ [Background] No CRM data to sync to Baserow.")

            # 2. Sync Chunks (NEW: Parent-Child architecture)
            chunks_data = data.get("chunks_data", {})
            all_chunks = chunks_data.get("all_chunks", [])
            if all_chunks and file_path:
                chunks_result = await self.baserow_manager.sync_chunks(
                    chunks=all_chunks,
                    transcript_id=transcript_id,
                    transcript_filename=file_path.name
                )
                if chunks_result.get("status") == "success":
                    chunk_count = chunks_result.get("synced_count", 0)
                    print(
                        f"   ✅ [Background] Successfully synced {chunk_count} chunks to Baserow for transcript ID {transcript_id}.")
                else:
                    print(
                        f"   ⚠️ [Background] Baserow chunks sync failed: {chunks_result.get('error')}")
            else:
                print(f"   ⚠️ [Background] No chunks data to sync to Baserow.")

        except Exception as baserow_error:
            print(
                f"   ⚠️ [Background] Baserow sync failed (non-critical): {baserow_error}")
