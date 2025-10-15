from fastapi import FastAPI, UploadFile, File, HTTPException
from pathlib import Path
import shutil
from typing import List
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

from orchestrator.pipeline import run_pipeline
from config.settings import settings

app = FastAPI(title="Stellar Sales System API")

# Initialize embedding model once at startup
embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)


class EmbeddingRequest(BaseModel):
    text: str


class EmbeddingResponse(BaseModel):
    embedding: List[float]
    dimension: int

@app.get("/")
async def root():
    """A simple endpoint to confirm the API is running."""
    return {"status": "ok", "message": "Welcome to the Stellar Sales System API!"}

@app.post("/embeddings", response_model=EmbeddingResponse)
async def generate_embedding(request: EmbeddingRequest):
    """
    Generate vector embedding for the given text using BAAI/bge-base-en-v1.5.
    This endpoint is used by N8N workflow for RAG chunking.
    """
    try:
        embedding = embedding_model.encode(
            request.text,
            convert_to_tensor=False,
            show_progress_bar=False
        ).tolist()

        return EmbeddingResponse(
            embedding=embedding,
            dimension=len(embedding)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Embedding generation failed: {str(e)}"
        )


@app.post("/upload_transcript/")
async def upload_transcript(file: UploadFile = File(...)):
    """
    Endpoint to upload and process a new transcript file.
    """
    save_path = settings.BASE_DIR / "data" / "transcripts" / file.filename

    try:
        # Save the uploaded file to disk
        with save_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Run our existing pipeline with the new file path
        await run_pipeline(file_path=save_path)

        return {
            "status": "success",
            "filename": file.filename,
            "message": "File uploaded and processed successfully."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")