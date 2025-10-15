#!/usr/bin/env python3
"""
Recreate Qdrant collection with new BGE embedding model dimensions.

BAAI/bge-base-en-v1.5 produces 768-dimensional vectors (vs 384 for MiniLM).
This requires recreating the collection.
"""

from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer
from config.settings import settings

def main():
    print("🔄 Updating Qdrant collection for BGE embeddings...")
    print(f"   Model: {settings.EMBEDDING_MODEL_NAME}")
    print(f"   Qdrant: {settings.QDRANT_URL}")

    # Initialize clients
    qdrant_client = QdrantClient(url=settings.QDRANT_URL)
    embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)

    vector_size = embedding_model.get_sentence_embedding_dimension()
    print(f"   Vector dimensions: {vector_size}")

    collection_name = "transcripts"

    # Check if collection exists
    try:
        existing = qdrant_client.get_collection(collection_name)
        print(f"\n⚠️  Collection '{collection_name}' exists with {existing.vectors_count} vectors")
        print(f"   Existing vector size: {existing.config.params.vectors.size}")

        if existing.config.params.vectors.size == vector_size:
            print(f"   ✅ Vector dimensions already match. No update needed.")
            return

        print(f"\n🗑️  Deleting old collection (vector size mismatch)...")
        qdrant_client.delete_collection(collection_name)
        print(f"   ✅ Deleted old collection")

    except Exception as e:
        print(f"   ℹ️  Collection doesn't exist yet")

    # Create new collection
    print(f"\n📦 Creating new collection with vector size {vector_size}...")
    qdrant_client.create_collection(
        collection_name=collection_name,
        vectors_config=models.VectorParams(
            size=vector_size,
            distance=models.Distance.COSINE
        )
    )

    print(f"   ✅ Collection '{collection_name}' created successfully!")
    print(f"\n🎯 Ready to embed transcripts with BGE model")
    print(f"   Next: Run ./venv/bin/python scripts/test_nelson_diaz.py")

if __name__ == "__main__":
    main()
