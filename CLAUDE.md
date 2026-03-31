# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Agentic Document Extractor — a generic, schema-driven document extraction system supporting any document type through custom JSON schemas. Combines PaddleOCR, PaddleX layout detection, GPT-4o VLM analysis, and JSON schema-driven extraction into a unified pipeline. Similar architecture to landing.ai's approach.

## Commands

```bash
# Install (editable)
pip install -e .
pip install -e ".[dev]"    # with dev deps (pytest, black, ruff)

# Run tests
pytest tests/                                    # all tests
pytest tests/test_ocr.py -v                      # single file
pytest tests/test_pipeline.py::TestDocumentProcessor -v  # single class
pytest tests/ -m "not slow"                      # skip slow tests
pytest tests/ -m integration                     # integration only

# Lint & format
black src/ tests/ cli/ --line-length 100
ruff check src/ tests/ cli/

# CLI (after pip install -e .)
docextract process doc.pdf --output results/
docextract extract doc.pdf --schema generic_form --output data.json
docextract extract invoice.pdf --schema examples/schemas/invoice_schema.json --output invoice.json
docextract visualize doc.pdf --output layout.png
docextract info --check-env
```

## Architecture

**Processing pipeline** (defined in `src/pipelines/document_processor.py`):

```
Document (PDF/Image/DOCX)
  → OCREngine         (src/core/ocr_engine.py)       – PaddleOCR, Hindi+English
  → LayoutDetector    (src/core/layout_detector.py)   – LayoutLMv3, region classification
  → RegionProcessor   (src/core/region_processor.py)  – crop, base64-encode for VLM
  → AgentOrchestrator (src/agents/orchestrator.py)    – LangChain agent with VLM tools
  → SchemaExtractor   (src/extractors/schema_extractor.py) – JSON schema → structured output
  → Output (JSON/CSV/HTML)
```

**Key design patterns:**
- **Lazy initialization**: VLM-dependent components (`AgentOrchestrator`, `SchemaExtractor`) are created only when first accessed via properties on `DocumentProcessor`. Core OCR/layout works without an OpenAI API key.
- **LRU caching**: `RegionProcessor` caches base64-encoded region crops (max 100) to avoid redundant VLM calls.
- **Error resilience**: Per-page error collection — a single page failure doesn't halt the pipeline. Errors accumulate in `ProcessingResult.errors`.
- **Fallback OCR**: If PaddleOCR is unavailable, falls back to Tesseract.

**Domain models** (`src/core/dataclasses.py`): `BoundingBox`, `OCRRegion`, `LayoutRegion`, `DocumentLayout`, `RegionType` enum, `LayoutType` enum. All support `to_dict()`/`from_dict()` serialization.

**Predefined extraction schemas** (`src/extractors/schemas.py`): `generic_form`, `table`. Custom schemas supported as JSON dicts or files. Example schemas in `examples/schemas/` (invoice, receipt, voter_list, agent_details).

**Agent tools** (`src/agents/tools.py`): VLM-powered tools for table, form, stamp, and chart analysis, orchestrated via LangChain's `create_tool_calling_agent`.

**CLI** (`src/cli/main.py`): Click-based with commands: `process`, `extract`, `visualize`, `info`. Schema-driven - works with any document type via custom schemas.

## Configuration

- Runtime config: `configs/default.yaml` (OCR langs, VLM model, DPI, agent iterations, output format)
- Environment: `.env` file — requires `OPENAI_API_KEY` for VLM features
- Python 3.9+ required

## Code Style

- **Black** formatter, line length 100
- **Ruff** linter: rules E, F, W, I, N, UP (ignores E501)
- Target Python versions: 3.9, 3.10, 3.11
- Use Pydantic dataclasses for domain models with `to_dict()`/`from_dict()` pattern
- Imports organized: stdlib → third-party → local (relative within `src/`)

## Schema-Driven Architecture

**V2** is generic and schema-driven:
- No hardcoded document types - all extraction via custom JSON schemas
- Users define schemas (following landing.ai best practices)
- Automatic CSV export for any array data
- Example schemas in `examples/schemas/` with comprehensive README

**Custom schema usage:**
```python
# Load from file
import json
with open("examples/schemas/invoice_schema.json") as f:
    schema = json.load(f)
data = processor.extract_schema(result, schema)

# Or define inline
schema = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "items": {"type": "array", "items": {"type": "object"}}
    }
}
data = processor.extract_schema(result, schema)
```

See `docs/SCHEMA_GUIDE.md` for detailed schema creation guide.
