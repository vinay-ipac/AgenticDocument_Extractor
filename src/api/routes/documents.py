"""Document upload and processing routes."""

import asyncio
import io
import json
import logging
import shutil
import tempfile
import time
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, HTTPException, UploadFile, Query
from fastapi.responses import StreamingResponse, Response

from ..models import (
    DocumentInfo,
    DocumentListResponse,
    ErrorResponse,
    ProcessRequest,
    UploadResponse,
)
from ..store import DocumentStatus, store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/documents", tags=["documents"])

# Temp directory for uploaded files
UPLOAD_DIR = Path(tempfile.gettempdir()) / "docextract_uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"}


@router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """Upload a document for processing."""
    if not file.filename:
        raise HTTPException(400, "No filename provided")

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            400,
            f"Unsupported file type: {ext}. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Save uploaded file
    doc = store.create(filename=file.filename, file_path="")
    save_path = UPLOAD_DIR / f"{doc.id}{ext}"
    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    doc.file_path = str(save_path)

    return UploadResponse(
        id=doc.id,
        filename=file.filename,
        status=doc.status.value,
        message="Document uploaded successfully",
    )


@router.post("/{doc_id}/process")
async def process_document(
    doc_id: str,
    dpi: int = Query(default=150, ge=72, le=600),
    language: str = Query(default="mixed"),
    max_pages: int = Query(default=100, ge=1, le=500),
):
    """Process a document with OCR and layout detection. Returns SSE stream."""
    doc = store.get(doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")

    if doc.status == DocumentStatus.PROCESSING:
        raise HTTPException(409, "Document is already being processed")

    async def event_stream():
        import os
        os.environ.setdefault("FLAGS_enable_pir_api", "0")
        os.environ.setdefault("FLAGS_enable_pir_in_executor", "0")
        os.environ.setdefault("FLAGS_enable_pir_with_pt_in_dy2st", "0")

        store.update_status(doc_id, DocumentStatus.PROCESSING)

        try:
            yield _sse_event("status", {"step": "loading", "message": "Loading document..."})
            await asyncio.sleep(0)

            from ...utils.helpers import load_document
            lang_tuple = ("hi", "en") if language == "mixed" else (language,)
            images = load_document(doc.file_path, dpi=dpi)

            if len(images) > max_pages:
                images = images[:max_pages]

            doc.images = images
            doc.page_count = len(images)

            yield _sse_event("status", {
                "step": "loaded",
                "message": f"Loaded {len(images)} page(s)",
                "page_count": len(images),
            })
            await asyncio.sleep(0)

            # OCR
            yield _sse_event("status", {"step": "ocr", "message": "Running OCR..."})
            await asyncio.sleep(0)

            from ...core.ocr_engine import OCREngine
            ocr_engine = OCREngine(languages=lang_tuple, use_gpu=False, show_log=False)

            all_ocr_regions = []
            for i, image in enumerate(images):
                ocr_regions = ocr_engine.extract(image)
                all_ocr_regions.append(ocr_regions)
                yield _sse_event("progress", {
                    "step": "ocr",
                    "page": i + 1,
                    "total": len(images),
                    "regions": len(ocr_regions),
                })
                await asyncio.sleep(0)

            # Layout detection
            yield _sse_event("status", {"step": "layout", "message": "Detecting layout..."})
            await asyncio.sleep(0)

            from ...core.layout_detector import LayoutDetector
            layout_detector = LayoutDetector(use_gpu=False)

            layouts = []
            for i, (image, ocr_regions) in enumerate(zip(images, all_ocr_regions)):
                layout = layout_detector.detect(image, ocr_regions=ocr_regions)
                layout.page_number = i + 1
                layouts.append(layout)
                yield _sse_event("progress", {
                    "step": "layout",
                    "page": i + 1,
                    "total": len(images),
                    "regions": len(layout.regions),
                })
                await asyncio.sleep(0)

            # Store results
            doc.layouts = [l.to_dict() for l in layouts]
            doc.status = DocumentStatus.PARSED

            total_regions = sum(len(l.regions) for l in layouts)
            yield _sse_event("complete", {
                "step": "done",
                "message": "Processing complete",
                "page_count": len(images),
                "total_regions": total_regions,
            })

        except Exception as e:
            logger.exception("Processing failed")
            doc.errors.append(str(e))
            store.update_status(doc_id, DocumentStatus.ERROR)
            yield _sse_event("error", {"message": str(e)})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/{doc_id}", response_model=DocumentInfo)
async def get_document(doc_id: str):
    """Get document status and metadata."""
    doc = store.get(doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")

    return DocumentInfo(
        id=doc.id,
        filename=doc.filename,
        status=doc.status.value,
        created_at=doc.created_at,
        page_count=doc.page_count,
        processing_time=doc.processing_time,
        errors=doc.errors,
    )


@router.get("/{doc_id}/image/{page}")
async def get_page_image(doc_id: str, page: int = 0):
    """Get a page image as PNG."""
    doc = store.get(doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    if page >= len(doc.images):
        raise HTTPException(404, f"Page {page} not found (document has {len(doc.images)} pages)")

    buf = io.BytesIO()
    doc.images[page].save(buf, format="PNG")
    buf.seek(0)
    return Response(content=buf.read(), media_type="image/png")


@router.get("/", response_model=DocumentListResponse)
async def list_documents():
    """List all uploaded documents."""
    docs = store.list_all()
    return DocumentListResponse(
        documents=[
            DocumentInfo(
                id=d.id,
                filename=d.filename,
                status=d.status.value,
                created_at=d.created_at,
                page_count=d.page_count,
                processing_time=d.processing_time,
                errors=d.errors,
            )
            for d in docs
        ]
    )


@router.delete("/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a document."""
    doc = store.get(doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")

    # Clean up file
    try:
        Path(doc.file_path).unlink(missing_ok=True)
    except Exception:
        pass

    store.delete(doc_id)
    return {"message": "Document deleted"}


def _sse_event(event_type: str, data: dict) -> str:
    """Format an SSE event."""
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
