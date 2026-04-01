# Document Extraction Dashboard

A professional web UI for document parsing (OCR + layout detection) and schema-based extraction.

## Features

- **Upload & Process**: Drag-drop documents (PDF, images, DOCX) with real-time processing progress
- **Document Viewer**: Interactive page viewer with region overlays (colored by type)
- **Parsing Panel**: View detected regions, OCR text, reading order, and confidence scores
- **Extraction Panel**: Schema-based extraction with predefined schemas or custom JSON schemas
- **Export**: Download extraction results as JSON

## Tech Stack

**Backend**: FastAPI + Python
- OCR: PaddleOCR (Hindi + English)
- Layout: PaddleX PP-DocLayoutV3
- Extraction: GPT-4o-mini VLM

**Frontend**: React + Vite + TypeScript + Tailwind CSS

## Quick Start

### 1. Install Backend Dependencies

```bash
cd agentic_document_extractor
pip install -e .
pip install fastapi uvicorn python-multipart
```

Make sure you have an OpenAI API key in your environment:
```bash
export OPENAI_API_KEY=sk-...
```

### 2. Install Frontend Dependencies

```bash
cd frontend
npm install
```

### 3. Development Mode

**Terminal 1 - Start Backend:**
```bash
python -m src.api.main
# Backend runs on http://localhost:8000
```

**Terminal 2 - Start Frontend:**
```bash
cd frontend
npm run dev
# Frontend runs on http://localhost:5173
```

Open http://localhost:5173 in your browser.

### 4. Production Build

```bash
# Build frontend
cd frontend
npm run build

# Start backend (serves built frontend)
cd ..
python -m src.api.main
# Access dashboard at http://localhost:8000
```

## API Endpoints

### Documents
- `POST /api/documents/upload` - Upload a document
- `POST /api/documents/{id}/process` - Process document (SSE stream)
- `GET /api/documents/{id}` - Get document status
- `GET /api/documents/{id}/image/{page}` - Get page image
- `GET /api/documents/` - List all documents
- `DELETE /api/documents/{id}` - Delete document

### Parsing
- `GET /api/parsing/{id}/{page}` - Get parsing results (layout + regions)
- `GET /api/parsing/{id}/{page}/regions` - Get all regions with OCR text

### Extraction
- `POST /api/extraction/{id}/{page}` - Run schema extraction
- `GET /api/extraction/schemas` - List available schemas
- `GET /api/extraction/schemas/{name}` - Get schema definition
- `POST /api/extraction/validate` - Validate custom schema
- `GET /api/extraction/{id}/{page}/export/json` - Export as JSON

## Architecture

```
Upload → OCR (PaddleOCR) → Layout Detection (PaddleX) → VLM Extraction (GPT-4o-mini)
                ↓                    ↓                          ↓
            OCR Regions        Layout Regions            Structured JSON
```

## Region Types & Colors

| Type | Color | Description |
|------|-------|-------------|
| text | Blue (#3498db) | Regular text content |
| table | Green (#2ecc71) | Tabular data |
| image | Purple (#9b59b6) | Images/photos |
| chart | Orange (#e67e22) | Charts/graphs |
| form | Teal (#1abc9c) | Form fields |
| stamp | Red (#e74c3c) | Stamps/seals |
| handwriting | Yellow (#f39c12) | Handwritten text |

## Predefined Schemas

- **generic_form**: Extract form fields, checkboxes, stamps, signatures
- **table**: Extract table headers and rows
- **Custom**: Define your own JSON schema

See `examples/schemas/` for example custom schemas (invoice, receipt, voter_list, etc.).

## Troubleshooting

**Backend fails to start:**
- Ensure PaddlePaddle is installed: `pip install paddlepaddle paddleocr`
- Check OPENAI_API_KEY is set

**Frontend fails to connect:**
- Verify backend is running on port 8000
- Check CORS settings in `src/api/main.py`

**Processing fails:**
- Check backend logs for OCR/layout errors
- Ensure document format is supported (PDF, PNG, JPG, TIFF, DOCX)

**Extraction fails:**
- Verify OPENAI_API_KEY is valid
- Check schema is valid JSON
- Review backend logs for VLM errors

## License

Same as parent project.
