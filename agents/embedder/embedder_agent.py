# This is the new, enhanced code for agents/embedder/embedder_agent.py

import uuid
from typing import List, Dict, Any
from datetime import datetime # NEW IMPORT
from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer

from agents.base_agent import BaseAgent
from config.settings import Settings

class EmbedderAgent(BaseAgent):
    """
    This agent's sole responsibility is to take raw text chunks, generate
    vector embeddings, and store them in the Qdrant vector database.
    It forms the core of the system's semantic memory.
    """
    def __init__(self, settings: Settings):
        super().__init__(settings)
        self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
        self.qdrant_client = QdrantClient(url=settings.QDRANT_URL)
        self.collection_name = "transcripts"
        self._ensure_qdrant_collection_exists()

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

    async def run(self, chunks: List[str], transcript_id: str) -> Dict[str, Any]:
        """
        Generates embeddings for a list of text chunks and upserts them into Qdrant.
        """
        print(f"🧠 EmbedderAgent: Generating {len(chunks)} embeddings for transcript ID {transcript_id}...")

        try:
            embeddings = self.embedding_model.encode(
                chunks, convert_to_tensor=False, show_progress_bar=False
            ).tolist()

            payloads = [
                {
                    "transcript_id": transcript_id,
                    "chunk_index": i,
                    "text": chunk,
                    "doc_type": "transcript_chunk",
                    "word_count": len(chunk.split()),
                    "created_at": datetime.now().isoformat()
                } for i, chunk in enumerate(chunks)
            ]

            # --- SUPERIOR SOLUTION: Create DETERMINISTIC UUIDs ---
            # This creates a compliant UUID that is the same every time for a given chunk.
            deterministic_ids = [
                str(uuid.uuid5(uuid.NAMESPACE_DNS, f"transcript_{transcript_id}_chunk_{i}"))
                for i, _ in enumerate(chunks)
            ]

            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=models.Batch(
                    ids=deterministic_ids,
                    vectors=embeddings,
                    payloads=payloads
                ),
                wait=True
            )

            print(f"   ✅ Successfully saved {len(chunks)} embeddings to Qdrant.")
            return {"embedding_status": "success", "vector_count": len(chunks)}

        except Exception as e:
            print(f"   ❌ ERROR in EmbedderAgent: {type(e).__name__}: {e}")
            return {"embedding_status": "error", "error_message": str(e)}
