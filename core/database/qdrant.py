from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient, models
from config.settings import settings

class QdrantManager:
    """
    Manages all interactions with the Qdrant vector database.
    """
    def __init__(self, settings):
        self.client = QdrantClient(url=settings.QDRANT_URL)
        self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
        self.collection_name = "transcripts"
        self._ensure_collection_exists()

    def _ensure_collection_exists(self):
        """Creates the Qdrant collection if it doesn't already exist."""
        try:
            self.client.get_collection(collection_name=self.collection_name)
        except Exception:
            self.client.recreate_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=self.embedding_model.get_sentence_embedding_dimension(),
                    distance=models.Distance.COSINE
                )
            )

    def search(self, query: str, limit: int = 3) -> list:
        """
        Takes a text query, creates an embedding, and searches Qdrant.
        """
        query_embedding = self.embedding_model.encode(query).tolist()

        search_results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=limit
        )
        return search_results

# Create a single, global instance for the app to use
qdrant_manager = QdrantManager(settings)