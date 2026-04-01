"""Parsing results routes."""

import logging

from fastapi import APIRouter, HTTPException

from ..models import ParsingResponse
from ..store import DocumentStatus, store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/parsing", tags=["parsing"])


@router.get("/{doc_id}/{page}", response_model=ParsingResponse)
async def get_parsing_results(doc_id: str, page: int = 0):
    """Get parsing results (layout + regions) for a page."""
    doc = store.get(doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")

    if doc.status not in (DocumentStatus.PARSED, DocumentStatus.COMPLETE):
        raise HTTPException(400, f"Document not yet parsed (status: {doc.status.value})")

    if page >= len(doc.layouts):
        raise HTTPException(404, f"Page {page} not found")

    layout = doc.layouts[page]

    return ParsingResponse(
        document_id=doc_id,
        page=page,
        image_width=layout.get("image_width", 0),
        image_height=layout.get("image_height", 0),
        layout_type=layout.get("layout_type", "unknown"),
        language=layout.get("language", "mixed"),
        regions=layout.get("regions", []),
        region_count=len(layout.get("regions", [])),
    )


@router.get("/{doc_id}/{page}/regions")
async def get_regions(doc_id: str, page: int = 0):
    """Get all regions with OCR text for a page."""
    doc = store.get(doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")

    if doc.status not in (DocumentStatus.PARSED, DocumentStatus.COMPLETE):
        raise HTTPException(400, f"Document not yet parsed (status: {doc.status.value})")

    if page >= len(doc.layouts):
        raise HTTPException(404, f"Page {page} not found")

    layout = doc.layouts[page]
    regions = layout.get("regions", [])

    # Enrich with combined text
    enriched = []
    for r in regions:
        ocr_texts = [ocr.get("text", "") for ocr in r.get("ocr_regions", [])]
        enriched.append({
            **r,
            "combined_text": " ".join(t for t in ocr_texts if t.strip()),
        })

    return {"document_id": doc_id, "page": page, "regions": enriched}
