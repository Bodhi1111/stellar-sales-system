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
        coaching_feedback: Dict[str, Any] | None = None
    ):
        print(f"💾 PersistenceAgent saving data for: {file_path.name}")
        full_text = "\\n".join(chunks)
        transcript_id = None

        # --- Save to PostgreSQL ---
        try:
            # Ensure database is initialized
            await db_manager.initialize()
            async with db_manager.session_context() as session:
                new_transcript = Transcript(
                    filename=file_path.name, full_text=full_text,
                    extracted_data=crm_data, social_content=social_content,
                    email_draft=email_draft
                )
                session.add(new_transcript)
                await session.commit()
                transcript_id = new_transcript.id
            print(f"   ✅ Successfully saved transcript metadata to PostgreSQL (ID: {transcript_id}).")
        except Exception as e:
            import traceback
            print(f"   ❌ ERROR: Failed to save to PostgreSQL: {str(e)}")
            print(f"   Traceback: {traceback.format_exc()}")
            return {"db_save_status": "postgres_error"}

        # --- Create and Save Embeddings to Qdrant ---
        if transcript_id and chunks:
            try:
                print(f"   Creating {len(chunks)} embeddings for Qdrant...")
                embeddings = self.embedding_model.encode(chunks).tolist()

                self.qdrant_client.upsert(
                    collection_name=self.collection_name,
                    points=models.Batch(
                        ids=[str(uuid.uuid4()) for _ in chunks],
                        vectors=embeddings,
                        payloads=[
                            {"transcript_id": transcript_id, "text": chunk} for chunk in chunks
                        ]
                    )
                )
                print(f"   ✅ Successfully saved {len(chunks)} embeddings to Qdrant.")
            except Exception as e:
                print(f"   ❌ ERROR: Failed to save embeddings to Qdrant: {e}")
                return {"db_save_status": "qdrant_error"}

        return {"db_save_status": "success"}