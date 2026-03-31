# Agentic Document Extractor

A generic, schema-driven document extraction system that uses AI-powered vision and OCR to extract structured data from any document type.

## Features

- **Schema-Driven**: Extract any data structure using custom JSON schemas
- **Multi-language OCR**: Hindi and English text extraction with PaddleOCR
- **Layout Understanding**: Automatic region detection and reading order prediction
- **Vision-Based Analysis**: VLM-powered table, chart, and form extraction
- **Confidence Scoring**: Built-in quality metrics for extracted data
- **Visual Grounding**: Bounding box visualization for extracted values
- **CSV Export**: Automatic CSV generation for array data

## Supported Document Types

Through custom JSON schemas, extract from any document including:

- Invoices and receipts
- Forms and applications
- Tables and spreadsheets
- Charts and graphs
- Government documents (voter lists, agent forms, etc.)
- Scanned PDFs
- Images (PNG, JPG, TIFF)
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
import json

# Initialize processor
processor = DocumentProcessor()

# Process a document
result = processor.process("document.pdf")

# Extract with predefined generic schema
form_data = processor.extract_schema(result, "generic_form")
print(json.dumps(form_data, indent=2))

# Extract with custom schema
custom_schema = {
    "type": "object",
    "properties": {
        "document_title": {"type": "string"},
        "date": {"type": "string"},
        "total_amount": {"type": "number"},
        "line_items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "description": {"type": "string"},
                    "amount": {"type": "number"}
                }
            }
        }
    }
}
data = processor.extract_schema(result, custom_schema)

# Or load schema from file
with open("examples/schemas/invoice_schema.json") as f:
    schema = json.load(f)
invoice_data = processor.extract_schema(result, schema)
```

### CLI

```bash
# Process a document
docextract process document.pdf --output results/

# Extract with predefined generic schema
docextract extract document.pdf --schema generic_form --output data.json

# Extract with custom schema file
docextract extract invoice.pdf --schema examples/schemas/invoice_schema.json --output invoice_data.json

# Extract table data
docextract extract table.pdf --schema table --output table_data.json

# Visualize layout detection
docextract visualize document.pdf --output layout.png

# Check environment setup
docextract info --check-env
```

### Jupyter Notebook

```bash
jupyter notebook notebooks/demo.ipynb
```

## Creating Custom Schemas

Define what to extract using standard JSON Schema:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "invoice_number": {
      "type": "string",
      "description": "Unique invoice identifier"
    },
    "date": {
      "type": "string",
      "description": "Invoice date in YYYY-MM-DD format"
    },
    "vendor": {
      "type": "object",
      "description": "Vendor information",
      "properties": {
        "name": {"type": "string"},
        "address": {"type": "string"}
      }
    },
    "line_items": {
      "type": "array",
      "description": "Invoice line items",
      "items": {
        "type": "object",
        "properties": {
          "description": {"type": "string"},
          "quantity": {"type": "integer"},
          "price": {"type": "number"},
          "total": {"type": "number"}
        }
      }
    },
    "total_amount": {
      "type": "number",
      "description": "Final total amount"
    }
  },
  "required": ["invoice_number", "date", "total_amount"]
}
```

### Schema Best Practices

Following [landing.ai](https://landing.ai) best practices:

1. **Descriptive field names**: Use clear, self-documenting names
2. **Proper data types**: String, integer, number, boolean, array, object
3. **Nested objects**: Group related fields together
4. **Arrays for repeating data**: Use arrays for lists of items
5. **Helpful descriptions**: Guide the AI with clear descriptions
6. **Mark required fields**: Specify which fields are mandatory
7. **Add constraints**: Use enums, min/max, patterns where appropriate

See [examples/schemas/README.md](examples/schemas/README.md) for detailed guidance and examples.

## Example Schemas

Pre-built schemas for common document types:

- **invoice_schema.json** - Commercial invoices with line items
- **receipt_schema.json** - Purchase receipts
- **voter_list_schema.json** - Indian electoral rolls (example)
- **agent_details_schema.json** - Agent registration forms (example)

All schemas are in `examples/schemas/` directory.

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
│   └── schemas/        # Example JSON schemas
├── docs/               # Documentation
│   ├── SCHEMA_GUIDE.md         # Schema creation guide
│   └── MIGRATION_V1_TO_V2.md   # Migration guide
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

```python
processor = DocumentProcessor(
    verbose=False,           # Enable verbose logging
    use_gpu=False,          # Use GPU for OCR (if available)
)

# Process document (OCR + layout detection)
result = processor.process(
    document="path/to/doc.pdf",
    analyze_regions=True,    # Enable VLM analysis
    layout_output_dir=None,  # Save layout images
)

# Extract structured data with schema
data = processor.extract_schema(
    result=result,
    schema="generic_form",   # Or dict, or file path
    page=0                   # Page number (0-indexed)
)

# Visualize layout
processor.visualize(
    document="path/to/doc.pdf",
    output_path="layout.png"
)
```

### Predefined Schemas

Built-in generic schemas:

- **generic_form**: Extract form fields, checkboxes, signatures, stamps
- **table**: Extract table headers, rows, and metadata

Custom schemas can be:
- Python dictionaries
- JSON files
- Loaded from `examples/schemas/`

## CSV Export

Array fields are automatically exported to CSV:

```python
# Schema with array field
schema = {
    "type": "object",
    "properties": {
        "customers": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "email": {"type": "string"}
                }
            }
        }
    }
}

# Process with generate_report
result = processor.process("document.pdf")
processor.generate_report(result, "output/")

# Creates: output/customers_page_1.csv
```

## Testing

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_ocr.py -v

# Run specific test class
pytest tests/test_pipeline.py::TestDocumentProcessor -v

# Skip slow tests
pytest tests/ -m "not slow"
```

## Documentation

- [Schema Creation Guide](docs/SCHEMA_GUIDE.md) - Comprehensive guide to creating custom schemas
- [Migration Guide](docs/MIGRATION_V1_TO_V2.md) - Upgrading from V1 (voter-list-specific) to V2 (generic)
- [Example Schemas](examples/schemas/README.md) - Example schemas with explanations

## Troubleshooting

### Common Issues

**OCR not working:**
- Ensure PaddlePaddle and PaddleOCR are installed
- Check if GPU is required: `use_gpu=False` for CPU-only systems

**Schema extraction returns empty data:**
- Add more descriptive field descriptions
- Check document quality (OCR accuracy, layout detection)
- Verify schema syntax is valid JSON

**VLM features not available:**
- Set `OPENAI_API_KEY` in `.env` file
- Core OCR/layout works without API key

## License

MIT License

## Acknowledgments

Based on [DeepLearning.AI](https://www.deeplearning.ai/) course materials and [LandingAI](https://landing.ai) ADE framework. Schema-driven approach inspired by landing.ai's document AI platform.

## Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check documentation in `docs/`
- Review example schemas in `examples/schemas/`
