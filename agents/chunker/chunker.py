import sys
from pathlib import Path
from langchain.text_splitter import RecursiveCharacterTextSplitter

from agents.base_agent import BaseAgent
from config.settings import settings


class ChunkerAgent(BaseAgent):
    """
    This agent takes a file path, reads the text, and splits it into chunks.
    """

    def __init__(self, settings):
        super().__init__(settings)
        # Initialize the text splitter once
        # Optimized for vector embeddings: 200-500 tokens (150-300 words)
        # Target: ~350 tokens = ~1400 characters (assuming 4 chars per token)
        # Rationale:
        #   - Smaller chunks = more granular semantic search
        #   - Better retrieval precision for RAG queries
        #   - Knowledge Analyst will query vectors, not process chunks directly
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1400,     # ~350 tokens, optimal for embedding coherence
            chunk_overlap=140,   # 10% overlap to maintain context at boundaries
        )

    async def run(self, file_path: Path):
        print(f"📦 ChunkerAgent received file: {file_path}")
        try:
            content = file_path.read_text(encoding='utf-8')
            print(f"   Successfully read {len(content)} characters.")

            # Use the text splitter to create chunks
            chunks = self.text_splitter.split_text(content)

            print(f"   Split text into {len(chunks)} chunks.")
            if chunks:
                print(f"   First chunk: '{chunks[0]}...'")

            return chunks

        except FileNotFoundError:
            print(f"   ❌ ERROR: File not found at {file_path}")
        except Exception as e:
            print(f"   ❌ ERROR: An unexpected error occurred: {e}")


# This block allows us to test the agent by running the file directly
if __name__ == "__main__":
    import asyncio
    if len(sys.argv) > 1:
        file_to_chunk = Path(sys.argv[1])

        async def main():
            agent = ChunkerAgent(settings)
            await agent.run(file_path=file_to_chunk)
        asyncio.run(main())
    else:
        print("Usage: python agents/chunker/chunker.py <path_to_file>")
