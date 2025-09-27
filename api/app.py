from fastapi import FastAPI, UploadFile, File, HTTPException
from pathlib import Path
import shutil

from orchestrator.pipeline import run_pipeline
from config.settings import settings

app = FastAPI(title="Stellar Sales System API")

@app.get("/")
async def root():
    """A simple endpoint to confirm the API is running."""
    return {"status": "ok", "message": "Welcome to the Stellar Sales System API!"}

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