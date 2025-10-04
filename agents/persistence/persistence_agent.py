import uuid
from pathlib import Path
from typing import Dict, Any, List
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient, models

from agents.base_agent import BaseAgent
from config.settings import Settings, settings
from core.database.postgres import db_manager
from core.database.models import Transcript

class PersistenceAgent(BaseAgent):
    """
    Handles all database persistence:
    1. Saves transcript metadata to PostgreSQL.
    2. Creates and saves vector embeddings to Qdrant.
    """
    def __init__(self, settings: Settings):
        super().__init__(settings)
        print("   Loading embedding model (this may take a moment)...")
        self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
        self.qdrant_client = QdrantClient(url=settings.QDRANT_URL)
        self.collection_name = "transcripts"
        self._ensure_qdrant_collection_exists()
        print("   Embedding model and Qdrant client ready.")

    def _ensure_qdrant_collection_exists(self):
        """Creates the Qdrant collection if it doesn't already exist."""
        try:
            self.qdrant_client.get_collection(collection_name=self.collection_name)
        except Exception:
            self.qdrant_client.recreate_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=self.embedding_model.get_sentence_embedding_dimension(),
                    distance=models.Distance.COSINE
                )
            )

    async def run(
        self, file_path: Path, chunks: List[str], crm_data: Dict[str, Any],
        social_content: Dict[str, Any], email_draft: str,
        coaching_feedback: Dict[str, Any] | None = None,
        transcript_id: str = None
    ):
        print(f"💾 PersistenceAgent saving data for: {file_path.name}")
        full_text = "\\n".join(chunks)

        # --- Save to PostgreSQL using upsert by external_id ---
        try:
            # Ensure database is initialized
            await db_manager.initialize()
            async with db_manager.session_context() as session:
                from sqlalchemy import select

                # Try to find existing record by external_id
                stmt = select(Transcript).where(Transcript.external_id == transcript_id)
                result = await session.execute(stmt)
                existing_transcript = result.scalar_one_or_none()

                if existing_transcript:
                    # Update existing record
                    print(f"   Updating existing transcript with external_id: {transcript_id}")
                    existing_transcript.filename = file_path.name
                    existing_transcript.full_text = full_text
                    existing_transcript.extracted_data = crm_data
                    existing_transcript.social_content = social_content
                    existing_transcript.email_draft = email_draft
                else:
                    # Create new record
                    print(f"   Creating new transcript with external_id: {transcript_id}")
                    new_transcript = Transcript(
                        external_id=transcript_id,
                        filename=file_path.name,
                        full_text=full_text,
                        extracted_data=crm_data,
                        social_content=social_content,
                        email_draft=email_draft
                    )
                    session.add(new_transcript)

                await session.commit()
            print(f"   ✅ Successfully saved transcript metadata to PostgreSQL (external_id: {transcript_id}).")
        except Exception as e:
            import traceback
            print(f"   ❌ ERROR: Failed to save to PostgreSQL: {str(e)}")
            print(f"   Traceback: {traceback.format_exc()}")
            return {"db_save_status": "postgres_error"}

        return {"db_save_status": "success"}