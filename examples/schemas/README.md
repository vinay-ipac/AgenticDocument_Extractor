# Custom Schema Guide

This directory contains example JSON schemas that demonstrate how to extract structured data from different document types using the Agentic Document Extractor.

## Overview

The Agentic Document Extractor is a **schema-driven system** — you define what data to extract by providing a JSON schema, and the system uses AI-powered analysis to extract that data from your documents. This approach is similar to landing.ai and other modern document AI platforms.

## Quick Start

### Using an Example Schema

```bash
# Extract invoice data using the example schema
docextract extract invoice.pdf --schema examples/schemas/invoice_schema.json --output data.json

# Extract receipt data
docextract extract receipt.pdf --schema examples/schemas/receipt_schema.json --output data.json

# Extract voter list data (Indian electoral documents)
docextract extract voter_list.pdf --schema examples/schemas/voter_list_schema.json --output data.json
```

### Using in Python

```python
from agentic_document_extractor import DocumentProcessor
import json

# Load custom schema
with open("examples/schemas/invoice_schema.json") as f:
    schema = json.load(f)

# Process document
processor = DocumentProcessor()
result = processor.process("invoice.pdf")

# Extract with schema
data = processor.extract_schema(result, schema)
print(json.dumps(data, indent=2))
```

## Schema Best Practices

Following landing.ai's approach, here are the best practices for creating effective extraction schemas:

### 1. Use Descriptive Field Names

**Good:**
```json
{
  "invoice_number": {"type": "string"},
  "invoice_date": {"type": "string"},
  "total_amount": {"type": "number"}
}
```

**Avoid:**
```json
{
  "inv_no": {"type": "string"},
  "date": {"type": "string"},
  "amt": {"type": "number"}
}
```

### 2. Specify Proper Data Types

JSON Schema supports these types:
- `string` — Text data
- `integer` — Whole numbers (no decimals)
- `number` — Numeric values (can include decimals)
- `boolean` — true/false values
- `array` — Lists of items
- `object` — Nested structures
- `null` — Explicitly null values

**Example:**
```json
{
  "properties": {
    "name": {"type": "string"},
    "age": {"type": "integer"},
    "price": {"type": "number"},
    "is_active": {"type": "boolean"},
    "tags": {"type": "array", "items": {"type": "string"}},
    "address": {"type": "object"}
  }
}
```

### 3. Use Nested Objects for Grouping

Group related fields together using nested objects:

```json
{
  "vendor": {
    "type": "object",
    "properties": {
      "name": {"type": "string"},
      "address": {"type": "string"},
      "phone": {"type": "string"}
    }
  },
  "customer": {
    "type": "object",
    "properties": {
      "name": {"type": "string"},
      "address": {"type": "string"}
    }
  }
}
```

### 4. Use Arrays for Repeating Data

For lists of items (like line items on an invoice), use arrays:

```json
{
  "line_items": {
    "type": "array",
    "description": "Items purchased",
    "items": {
      "type": "object",
      "properties": {
        "description": {"type": "string"},
        "quantity": {"type": "integer"},
        "unit_price": {"type": "number"},
        "total": {"type": "number"}
      }
    }
  }
}
```

### 5. Add Helpful Descriptions

Descriptions guide the AI extraction model:

```json
{
  "invoice_date": {
    "type": "string",
    "description": "Date when the invoice was issued (YYYY-MM-DD format)"
  },
  "due_date": {
    "type": "string",
    "description": "Payment due date (YYYY-MM-DD format)"
  }
}
```

### 6. Mark Required Fields

Specify which fields are mandatory:

```json
{
  "type": "object",
  "properties": {
    "invoice_number": {"type": "string"},
    "date": {"type": "string"},
    "total": {"type": "number"}
  },
  "required": ["invoice_number", "date", "total"]
}
```

### 7. Use Constraints Where Appropriate

Add validation constraints to improve extraction quality:

```json
{
  "age": {
    "type": "integer",
    "minimum": 0,
    "maximum": 150
  },
  "status": {
    "type": "string",
    "enum": ["pending", "approved", "rejected"]
  },
  "email": {
    "type": "string",
    "format": "email"
  },
  "phone": {
    "type": "string",
    "pattern": "^[0-9]{10}$"
  }
}
```

## Schema Template

Here's a basic template to start with:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "title": "Your Document Type",
  "description": "Brief description of what this schema extracts",
  "properties": {
    "field_name": {
      "type": "string",
      "description": "What this field represents"
    },
    "another_field": {
      "type": "integer",
      "description": "Numeric field description"
    },
    "nested_data": {
      "type": "object",
      "description": "Group of related fields",
      "properties": {
        "sub_field_1": {"type": "string"},
        "sub_field_2": {"type": "number"}
      }
    },
    "repeating_items": {
      "type": "array",
      "description": "List of items",
      "items": {
        "type": "object",
        "properties": {
          "item_name": {"type": "string"},
          "item_value": {"type": "number"}
        }
      }
    }
  },
  "required": ["field_name"]
}
```

## Example Schemas in This Directory

### invoice_schema.json
Professional invoice extraction schema demonstrating:
- Nested objects (vendor, customer)
- Arrays (line_items)
- Proper data types (number for prices, integer for quantity)
- Enum constraints (currency)
- Comprehensive required fields

Use for: Commercial invoices, purchase orders, billing statements

### receipt_schema.json
Receipt extraction schema showing:
- Simple merchant information
- Transaction timestamp fields
- Item arrays with quantity/price
- Payment method enum
- Pattern validation (card last 4 digits)

Use for: Point-of-sale receipts, purchase confirmations

### voter_list_schema.json
Electoral roll extraction (India-specific):
- Voter array with comprehensive fields
- Metadata object for document-level info
- Multi-language field descriptions (English + Hindi)
- Confidence scoring

Use for: Indian electoral documents, voter registration forms

### agent_details_schema.json
Agent registration form extraction:
- Personal and contact information
- Location data (area, district, state)
- Status tracking with enums
- Date fields for validity tracking

Use for: Agent registration forms, representative details

## Creating Your Own Schema

1. **Identify the document type** — What kind of document are you extracting from?
2. **List the fields** — What information do you need to extract?
3. **Group related fields** — Use nested objects for logical groupings
4. **Determine data types** — String, number, integer, boolean, array, object
5. **Add descriptions** — Help the AI understand what each field means
6. **Mark required fields** — Which fields are mandatory?
7. **Add constraints** — Enums, patterns, min/max values where appropriate
8. **Test and iterate** — Run extraction on sample documents and refine

## Advanced Topics

### Multi-Language Support

Include language hints in descriptions for better extraction from multilingual documents:

```json
{
  "name": {
    "type": "string",
    "description": "Voter name (नाम)"
  }
}
```

### Confidence Scores

Include confidence fields to track extraction quality:

```json
{
  "confidence": {
    "type": "number",
    "minimum": 0,
    "maximum": 1,
    "description": "Confidence score for this extraction"
  }
}
```

### Additional Properties

Allow flexible fields for unexpected data:

```json
{
  "type": "object",
  "properties": {
    "known_field_1": {"type": "string"},
    "known_field_2": {"type": "number"}
  },
  "additionalProperties": true
}
```

Or explicitly define additional property types:

```json
{
  "fields": {
    "type": "object",
    "description": "Dynamic form fields",
    "additionalProperties": {"type": "string"}
  }
}
```

## Troubleshooting

### Extraction returns empty or partial data
- Check field descriptions are clear and specific
- Ensure data types match document content
- Try adding more context in descriptions
- Verify document quality (OCR accuracy, layout detection)

### Wrong data type extracted
- Be explicit about types (use `integer` not `number` for whole numbers)
- Add format hints in descriptions (e.g., "YYYY-MM-DD format")
- Use enum constraints to limit valid values

### Array data not extracted
- Ensure array structure is clear in schema
- Add description explaining what the array contains
- Check if the document has clear repeating patterns

### Nested objects not working
- Simplify nesting depth (max 2-3 levels recommended)
- Use clear descriptions at each level
- Consider flattening very deep structures

## Resources

- [JSON Schema Specification](https://json-schema.org/)
- [Understanding JSON Schema](https://json-schema.org/understanding-json-schema/)
- [Landing.ai Documentation](https://landing.ai/docs)
- [Project Documentation](../../README.md)

## Need Help?

If you're stuck creating a schema:
1. Look at the example schemas in this directory
2. Start with the template above
3. Test with a single document first
4. Iterate based on extraction results
5. Open an issue on GitHub for support
