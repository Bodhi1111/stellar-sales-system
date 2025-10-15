# This is the new, enhanced code for agents/embedder/embedder_agent.py

import uuid
from typing import List, Dict, Any
from datetime import datetime  # NEW IMPORT
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
        self.embedding_model = SentenceTransformer(
            settings.EMBEDDING_MODEL_NAME)
        self.qdrant_client = QdrantClient(url=settings.QDRANT_URL)
        self.collection_name = "transcripts"
        self._ensure_qdrant_collection_exists()

    def _ensure_qdrant_collection_exists(self):
        """Creates the Qdrant collection if it doesn't already exist."""
        try:
            self.qdrant_client.get_collection(
                collection_name=self.collection_name)
        except Exception:
            self.qdrant_client.recreate_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=self.embedding_model.get_sentence_embedding_dimension(),
                    distance=models.Distance.COSINE
                )
            )

    async def run(
        self,
        child_chunks: List[Dict[str, Any]] = None,
        parent_chunks: List[Dict[str, Any]] = None,
        header_chunk: Dict[str, Any] = None,
        transcript_id: str = None,
        metadata: Dict[str, Any] = None,
        # Backward compatibility parameters
        chunks: List[Any] = None
    ) -> Dict[str, Any]:
        """
        Parent-Child Embedding Architecture:

        1. CHILD CHUNKS (speaker turns): Embedded and indexed for retrieval
        2. PARENT CHUNKS (phase segments): Stored in payload only (NO embedding)
        3. HEADER CHUNK: Stored in payload only (NO embedding)

        All chunks have chunk_id (UUID) and parent_id for linking.

        Args:
            child_chunks: Speaker-turn chunks to embed
            parent_chunks: Phase segment chunks (stored, not embedded)
            header_chunk: Header metadata chunk (stored, not embedded)
            transcript_id: Unique identifier for the transcript
            metadata: Optional global metadata (client_name, meeting_date)
            chunks: DEPRECATED - for backward compatibility
        """
        # Backward compatibility
        if chunks and not child_chunks:
            print("   ⚠️ Using deprecated 'chunks' parameter")
            return await self._run_legacy(chunks, transcript_id, metadata)

        if not child_chunks:
            print("   ⚠️ No child chunks to embed.")
            return {"embedding_status": "success", "vector_count": 0}

        print(f"🧠 EmbedderAgent: Parent-Child architecture")
        print(f"   - {len(child_chunks)} child chunks (speaker turns) to EMBED")
        print(f"   - {len(parent_chunks) if parent_chunks else 0} parent chunks (phase segments) to STORE")
        print(f"   - Header chunk: {'yes' if header_chunk else 'no'}")

        try:
            all_points = []

            # 1. Embed CHILD CHUNKS (speaker turns)
            child_texts = [c["text"] for c in child_chunks]
            child_embeddings = self.embedding_model.encode(
                child_texts,
                convert_to_tensor=False,
                show_progress_bar=False,
                batch_size=32
            ).tolist()

            for chunk, embedding in zip(child_chunks, child_embeddings):
                payload = self._create_payload(chunk, transcript_id, metadata, is_embedded=True)
                all_points.append(models.PointStruct(
                    id=chunk["chunk_id"],  # Use chunk's UUID
                    vector=embedding,
                    payload=payload
                ))

            print(f"   ✅ Embedded {len(child_chunks)} child chunks")

            # 2. Store PARENT CHUNKS (no embedding, zero vector)
            if parent_chunks:
                zero_vector = [0.0] * self.embedding_model.get_sentence_embedding_dimension()
                for chunk in parent_chunks:
                    payload = self._create_payload(chunk, transcript_id, metadata, is_embedded=False)
                    all_points.append(models.PointStruct(
                        id=chunk["chunk_id"],  # Use chunk's UUID
                        vector=zero_vector,  # Zero vector (not searchable)
                        payload=payload
                    ))
                print(f"   ✅ Stored {len(parent_chunks)} parent chunks (no embedding)")

            # 3. Store HEADER CHUNK (no embedding, zero vector)
            if header_chunk:
                zero_vector = [0.0] * self.embedding_model.get_sentence_embedding_dimension()
                payload = self._create_payload(header_chunk, transcript_id, metadata, is_embedded=False)
                all_points.append(models.PointStruct(
                    id=header_chunk["chunk_id"],
                    vector=zero_vector,
                    payload=payload
                ))
                print(f"   ✅ Stored header chunk (no embedding)")

            # Upsert all points to Qdrant
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=all_points,
                wait=True
            )

            print(f"   ✅ Successfully saved {len(all_points)} points to Qdrant")
            return {
                "embedding_status": "success",
                "child_count": len(child_chunks),
                "parent_count": len(parent_chunks) if parent_chunks else 0,
                "total_points": len(all_points)
            }

        except Exception as e:
            print(f"   ❌ ERROR in EmbedderAgent: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return {"embedding_status": "error", "error_message": str(e)}

    def _create_payload(
        self,
        chunk: Dict[str, Any],
        transcript_id: str,
        metadata: Dict[str, Any],
        is_embedded: bool
    ) -> Dict[str, Any]:
        """Create Qdrant payload from chunk with parent-child metadata."""
        payload = {
            # Parent-Child architecture fields
            "chunk_id": chunk.get("chunk_id"),
            "parent_id": chunk.get("parent_id"),
            "chunk_type": chunk.get("chunk_type"),  # "header", "parent", "child"
            "is_embedded": is_embedded,  # True for children, False for parents/header

            # Core fields
            "transcript_id": transcript_id,
            "text": chunk.get("text", ""),
            "word_count": len(chunk.get("text", "").split()),
            "created_at": datetime.now().isoformat(),

            # Speaker metadata (child chunks only)
            "speaker_name": chunk.get("speaker_name"),
            "start_time": chunk.get("start_time"),
            "end_time": chunk.get("end_time"),

            # Sales metadata
            "sales_stage": chunk.get("sales_stage"),
            "conversation_phase": chunk.get("conversation_phase"),
            "detected_topics": chunk.get("detected_topics", []),

            # Semantic NLP metadata (child chunks)
            "intent": chunk.get("intent"),
            "sentiment": chunk.get("sentiment"),
            "discourse_marker": chunk.get("discourse_marker"),
            "contains_entity": chunk.get("contains_entity", False),

            # Parent chunk metadata
            "turn_count": chunk.get("turn_count"),
            "speaker_balance": chunk.get("speaker_balance"),

            # Global metadata
            "client_name": metadata.get("client_name", "") if metadata else "",
            "meeting_date": metadata.get("meeting_date", "") if metadata else ""
        }

        return payload

    async def _run_legacy(self, chunks: List[Any], transcript_id: str, metadata: Dict[str, Any] = None):
        """Backward compatibility for old chunk format."""
        print(f"   ⚠️ Running in legacy mode (deprecated)")
        # Convert old format to child chunks
        child_chunks = []
        for i, chunk in enumerate(chunks):
            if isinstance(chunk, dict):
                chunk_data = chunk.copy()
                if "chunk_id" not in chunk_data:
                    chunk_data["chunk_id"] = str(uuid.uuid4())
                child_chunks.append(chunk_data)
            else:
                child_chunks.append({
                    "chunk_id": str(uuid.uuid4()),
                    "parent_id": None,
                    "chunk_type": "child",
                    "text": chunk
                })

        return await self.run(
            child_chunks=child_chunks,
            parent_chunks=None,
            header_chunk=None,
            transcript_id=transcript_id,
            metadata=metadata
        )
