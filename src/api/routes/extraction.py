"""Schema extraction routes."""

import json
import logging
from pathlib import Path
import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

from ..models import (
    ExtractionRequest,
    ExtractionResponse,
    SchemaInfo,
    SchemaListResponse,
)
from ..store import DocumentStatus, store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/extraction", tags=["extraction"])


@router.post("/{doc_id}/{page}", response_model=ExtractionResponse)
async def extract_with_schema(doc_id: str, page: int, request: ExtractionRequest):
    """Run schema-based extraction on a page."""
    doc = store.get(doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")

    if doc.status not in (DocumentStatus.PARSED, DocumentStatus.COMPLETE):
        raise HTTPException(400, f"Document not yet parsed (status: {doc.status.value})")

    if page >= len(doc.layouts):
        raise HTTPException(404, f"Page {page} not found")

    if page >= len(doc.images):
        raise HTTPException(400, "Page image not available")

    # Resolve schema
    schema = None
    schema_name = "custom"

    logger.info(f"Extraction request: schema_name={request.schema_name}, custom_schema={'present' if request.custom_schema else 'none'}")

    if request.schema_name:
        try:
            from ...extractors.schemas import get_schema
            schema = get_schema(request.schema_name)
            schema_name = request.schema_name
        except ValueError as e:
            raise HTTPException(400, str(e))
    elif request.custom_schema:
        schema = request.custom_schema
        schema_name = request.custom_schema.get("title", "custom")
    else:
        raise HTTPException(
            400,
            f"Provide either schema_name or custom_schema. Received: schema_name={request.schema_name}, custom_schema={request.custom_schema}"
        )

    # Run extraction
    try:
        store.update_status(doc_id, DocumentStatus.EXTRACTING)

        from ...core.dataclasses import DocumentLayout
        from ...extractors.schema_extractor import SchemaExtractor
        from openai import OpenAI

        vlm_client = OpenAI(api_key=api_key)
        extractor = SchemaExtractor(vlm_client=vlm_client)

        layout_dict = doc.layouts[page]
        layout = DocumentLayout.from_dict(layout_dict)
        image = doc.images[page]

        result = extractor.extract(
            schema=schema,
            image=image,
            layout=layout,
        )

        # Store extraction
        extraction_record = {
            "page": page,
            "schema": schema_name,
            "data": result,
        }
        doc.extractions.append(extraction_record)
        store.update_status(doc_id, DocumentStatus.COMPLETE)

        return ExtractionResponse(
            document_id=doc_id,
            page=page,
            schema_used=schema_name,
            data=result,
            confidence=result.get("confidence") if isinstance(result, dict) else None,
        )

    except Exception as e:
        logger.exception("Extraction failed")
        doc.errors.append(f"Extraction error: {str(e)}")
        store.update_status(doc_id, DocumentStatus.PARSED)
        raise HTTPException(500, f"Extraction failed: {str(e)}")


@router.get("/schemas", response_model=SchemaListResponse)
async def list_schemas():
    """List available predefined schemas."""
    from ...extractors.schemas import GENERIC_FORM_SCHEMA, TABLE_SCHEMA

    schemas = [
        SchemaInfo(
            name="generic_form",
            title=GENERIC_FORM_SCHEMA.get("title", "Generic Form"),
            description=GENERIC_FORM_SCHEMA.get("description", ""),
            required_fields=GENERIC_FORM_SCHEMA.get("required", []),
        ),
        SchemaInfo(
            name="table",
            title=TABLE_SCHEMA.get("title", "Table Data"),
            description=TABLE_SCHEMA.get("description", ""),
            required_fields=TABLE_SCHEMA.get("required", []),
        ),
    ]

    # Load example schemas
    examples_dir = Path(__file__).parent.parent.parent.parent / "examples" / "schemas"
    if examples_dir.exists():
        for schema_file in examples_dir.glob("*.json"):
            try:
                with open(schema_file) as f:
                    s = json.load(f)
                schemas.append(
                    SchemaInfo(
                        name=schema_file.stem,
                        title=s.get("title", schema_file.stem),
                        description=s.get("description", ""),
                        required_fields=s.get("required", []),
                    )
                )
            except Exception:
                pass

    return SchemaListResponse(schemas=schemas)


@router.get("/schemas/{schema_name}")
async def get_schema_detail(schema_name: str):
    """Get full schema definition."""
    try:
        from ...extractors.schemas import get_schema
        return get_schema(schema_name)
    except ValueError:
        pass

    # Check example schemas
    examples_dir = Path(__file__).parent.parent.parent.parent / "examples" / "schemas"
    schema_file = examples_dir / f"{schema_name}.json"
    if schema_file.exists():
        with open(schema_file) as f:
            return json.load(f)

    raise HTTPException(404, f"Schema '{schema_name}' not found")


@router.post("/validate")
async def validate_schema(schema: dict):
    """Validate a custom JSON schema."""
    errors = []

    if not isinstance(schema, dict):
        errors.append("Schema must be a JSON object")
    elif "properties" not in schema and "type" not in schema:
        errors.append("Schema should have 'properties' or 'type' field")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "schema": schema,
    }


@router.get("/{doc_id}/results")
async def get_extraction_results(doc_id: str):
    """Get all extraction results for a document."""
    doc = store.get(doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")

    return {"document_id": doc_id, "extractions": doc.extractions}


@router.get("/{doc_id}/{page}/export/json")
async def export_json(doc_id: str, page: int):
    """Export extraction results as JSON file."""
    doc = store.get(doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")

    page_extractions = [e for e in doc.extractions if e.get("page") == page]
    if not page_extractions:
        raise HTTPException(404, "No extraction results for this page")

    data = page_extractions[-1].get("data", {})
    content = json.dumps(data, indent=2, ensure_ascii=False)

    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={doc.filename}_page{page}.json"},
    )
