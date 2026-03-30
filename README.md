# Agentic Document Extractor

End-to-end robust document extraction system using DPT (Document Pre-trained Transformer) architecture, designed specifically for Indian government and administrative documents.

## Features

- **Multi-language OCR**: Hindi and English text extraction with PaddleOCR
- **Layout Understanding**: Reading order prediction for multi-column documents
- **Vision-Based Analysis**: VLM-powered table, chart, and form extraction
- **Schema-Based Extraction**: JSON schema-driven field extraction with confidence scores
- **Visual Grounding**: Bounding box visualization for extracted values

## Supported Document Types

- Voter lists (Hindi + English mixed)
- Agent details forms
- Scanned PDF documents
- Image files (PNG, JPG, TIFF)
- DOCX files

## Installation

```bash
# Clone the repository
cd agentic_document_extractor

# Install dependencies
pip install -e .

# Set up environment variables
cp .env.example .env
# Edit .env and add your OpenAI API key
```

## Quick Start

### Python API

```python
from agentic_document_extractor import DocumentProcessor

# Initialize processor
processor = DocumentProcessor()

# Process a document
result = processor.process("path/to/voter_list.pdf")

# Extract structured data
voter_data = processor.extract_schema(result, schema_type="voter_list")
print(voter_data)
```

### CLI

```bash
# Process a single document
docextract process path/to/document.pdf --output result.json

# Extract with schema
docextract extract path/to/document.pdf --schema voter_list --output extracted.json

# Visualize layout
docextract visualize path/to/document.pdf --output layout.png
```

### Jupyter Notebook

```bash
jupyter notebook notebooks/demo.ipynb
```

## Project Structure

```
agentic_document_extractor/
├── src/
│   ├── core/           # OCR, layout detection, region processing
│   ├── agents/         # VLM tools, prompts, orchestrator
│   ├── extractors/     # Schema-based extraction
│   ├── utils/          # Visualization, document loaders
│   └── pipelines/      # End-to-end pipelines
├── cli/                # Command-line interface
├── notebooks/          # Interactive demos
├── tests/              # Unit and integration tests
├── examples/           # Sample schemas and outputs
└── configs/            # Configuration files
```

## Architecture

The system follows a hybrid agentic architecture:

1. **OCR Engine**: PaddleOCR with Hindi/English support
2. **Layout Detector**: Region type classification + reading order
3. **Agent Tools**: VLM-based table/form/stamp analysis
4. **Schema Extractor**: JSON schema-driven field extraction
5. **Pipeline Orchestrator**: End-to-end document processing

## Configuration

Edit `configs/default.yaml` to customize:

- OCR language settings
- VLM model selection
- Processing timeouts
- Output formats

## API Reference

### DocumentProcessor

Main class for document processing:

- `process(document_path)`: Process document, return regions
- `extract_schema(regions, schema_type)`: Extract structured data
- `visualize(document_path, output_path)`: Draw layout visualization

### Supported Schemas

- `voter_list`: Name, Age, Gender, Constituency, Serial No, Address
- `agent_details`: Name, ID, Contact, Area, Status

## Testing

```bash
# Run all tests
pytest tests/

# Run specific test
pytest tests/test_ocr.py -v
```

## License

MIT License

## Acknowledgments

Based on DeepLearning.AI course materials (L2, L4, L6, L8 notebooks) and LandingAI ADE framework.
