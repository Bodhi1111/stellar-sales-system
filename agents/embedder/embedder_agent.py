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

    async def run(self, chunks: List[Any], transcript_id: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generates embeddings for chunks and upserts them into Qdrant with RICH metadata.

        NEW ARCHITECTURE: Chunks are now dictionaries with embedded metadata:
        {
            "text": str,
            "chunk_type": "header" | "dialogue",
            "conversation_phase": str,
            "speakers": List[str],
            "timestamp_start": str,
            "timestamp_end": str
        }

        Args:
            chunks: List of chunk dictionaries (NEW) or text strings (backward compat)
            transcript_id: Unique identifier for the transcript
            metadata: Optional global metadata
        """
        print(
            f"🧠 EmbedderAgent: Generating {len(chunks)} embeddings for transcript ID {transcript_id}...")

        try:
            # Extract text from chunks (handle both dict and string formats)
            chunk_texts = []
            chunk_metadata_list = []

            for i, chunk in enumerate(chunks):
                if isinstance(chunk, dict):
                    # NEW: Chunk with embedded metadata
                    chunk_texts.append(chunk["text"])
                    chunk_metadata_list.append(chunk)
                else:
                    # BACKWARD COMPAT: Plain text chunk
                    chunk_texts.append(chunk)
                    chunk_metadata_list.append({
                        "text": chunk,
                        "chunk_type": "unknown",
                        "conversation_phase": None,
                        "speakers": []
                    })

            # Batch encode all chunks at once (optimized for SentenceTransformer)
            embeddings = self.embedding_model.encode(
                chunk_texts,
                convert_to_tensor=False,
                show_progress_bar=False,
                batch_size=32  # Process 32 chunks at a time
            ).tolist()

            # NEW: Create payloads with RICH metadata from each chunk
            payloads = []
            for i, chunk_meta in enumerate(chunk_metadata_list):
                payload = {
                    "transcript_id": transcript_id,
                    "chunk_index": i,
                    "text": chunk_meta.get("text", chunk_texts[i]),
                    "doc_type": chunk_meta.get("chunk_type", "transcript_chunk"),
                    "word_count": len(chunk_texts[i].split()),
                    "created_at": datetime.now().isoformat(),

                    # RICH METADATA from ChunkerAgent (enables targeted retrieval)
                    "conversation_phase": chunk_meta.get("conversation_phase"),
                    "speakers": chunk_meta.get("speakers", []),
                    "timestamp_start": chunk_meta.get("timestamp_start"),
                    "timestamp_end": chunk_meta.get("timestamp_end"),

                    # SEMANTIC NLP METADATA from StructuringAgent → ParserAgent → ChunkerAgent
                    "dominant_intent": chunk_meta.get("dominant_intent"),
                    "dominant_sentiment": chunk_meta.get("dominant_sentiment"),
                    "contains_entities": chunk_meta.get("contains_entities", False),
                    "discourse_markers": chunk_meta.get("discourse_markers", []),

                    # ENHANCED METADATA from Semantic Chunker (enables advanced filtering)
                    "turn_count": chunk_meta.get("turn_count", 0),
                    "speaker_balance": chunk_meta.get("speaker_balance", 0.5),
                    "question_count": chunk_meta.get("question_count", 0),
                    "objection_count": chunk_meta.get("objection_count", 0),
                    "has_objections": chunk_meta.get("has_objections", False),

                    # Global metadata (will be populated by Knowledge Analyst later)
                    "client_name": metadata.get("client_name", "") if metadata else "",
                    "meeting_date": metadata.get("meeting_date", "") if metadata else ""
                }
                payloads.append(payload)

            # Count chunks with phase metadata
            chunks_with_phases = sum(1 for p in payloads if p["conversation_phase"])
            if chunks_with_phases > 0:
                print(f"   ✅ {chunks_with_phases}/{len(payloads)} chunks have conversation_phase metadata")

            # Count chunks with semantic NLP metadata
            chunks_with_intent = sum(1 for p in payloads if p["dominant_intent"])
            chunks_with_sentiment = sum(1 for p in payloads if p["dominant_sentiment"])
            if chunks_with_intent > 0 or chunks_with_sentiment > 0:
                print(f"   🧠 {chunks_with_intent}/{len(payloads)} chunks have intent metadata")
                print(f"   🧠 {chunks_with_sentiment}/{len(payloads)} chunks have sentiment metadata")

            # --- SUPERIOR SOLUTION: Create DETERMINISTIC UUIDs ---
            # This creates a compliant UUID that is the same every time for a given chunk.
            deterministic_ids = [
                str(uuid.uuid5(uuid.NAMESPACE_DNS,
                    f"transcript_{transcript_id}_chunk_{i}"))
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

            print(
                f"   ✅ Successfully saved {len(chunks)} embeddings to Qdrant.")
            return {"embedding_status": "success", "vector_count": len(chunks)}

        except Exception as e:
            print(f"   ❌ ERROR in EmbedderAgent: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return {"embedding_status": "error", "error_message": str(e)}
