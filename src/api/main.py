"""FastAPI application for Document Extraction Dashboard."""

import os
import logging
from pathlib import Path

# PIR flags must be set before any paddle import
os.environ.setdefault("FLAGS_enable_pir_api", "0")
os.environ.setdefault("FLAGS_enable_pir_in_executor", "0")
os.environ.setdefault("FLAGS_enable_pir_with_pt_in_dy2st", "0")
os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .routes import documents, parsing, extraction

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

app = FastAPI(
    title="Document Extraction Dashboard API",
    version="0.1.0",
    description="API for document parsing and schema-based extraction",
)

# CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(documents.router)
app.include_router(parsing.router)
app.include_router(extraction.router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}


# Serve frontend build if it exists
frontend_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")


def main():
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[str(Path(__file__).parent.parent)],
    )


if __name__ == "__main__":
    main()
