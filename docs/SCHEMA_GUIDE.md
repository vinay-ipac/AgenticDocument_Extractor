# Schema Creation Guide

This guide provides comprehensive documentation for creating custom JSON schemas for document extraction with the Agentic Document Extractor.

## Table of Contents

- [Introduction](#introduction)
- [JSON Schema Basics](#json-schema-basics)
- [Schema-Driven Extraction](#schema-driven-extraction)
- [Field Types and Usage](#field-types-and-usage)
- [Nested Structures](#nested-structures)
- [Arrays and Repeating Data](#arrays-and-repeating-data)
- [Best Practices](#best-practices)
- [Validation and Constraints](#validation-and-constraints)
- [Common Patterns](#common-patterns)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)

## Introduction

The Agentic Document Extractor uses a **schema-driven approach** similar to landing.ai and other modern document AI platforms. Instead of hardcoding extraction logic for specific document types, you define what data to extract using standard JSON Schema, and the system handles the extraction automatically.

### Why Schema-Driven?

1. **Flexibility** — Extract from any document type without code changes
2. **Standardization** — Uses JSON Schema (widely adopted standard)
3. **AI-Powered** — Leverages VLM (Vision-Language Models) for intelligent extraction
4. **Type Safety** — Strong typing ensures data quality
5. **Maintainability** — Schemas are declarative and easy to understand

## JSON Schema Basics

JSON Schema is a vocabulary that allows you to annotate and validate JSON documents. Our system uses JSON Schema Draft 7.

### Minimal Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "field_name": {
      "type": "string"
    }
  }
}
```

### Schema Structure

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",  // Schema version
  "type": "object",                                        // Root type
  "title": "Document Title",                               // Human-readable title
  "description": "What this schema extracts",              // Schema purpose
  "properties": {                                          // Field definitions
    "field1": {...},
    "field2": {...}
  },
  "required": ["field1"]                                   // Mandatory fields
}
```

## Schema-Driven Extraction

### How It Works

1. **Define Schema** — Create a JSON schema describing the data structure
2. **Process Document** — System performs OCR and layout detection
3. **AI Analysis** — VLM analyzes document using schema as context
4. **Extract Data** — System returns structured JSON matching your schema
5. **Validate** — Output conforms to schema types and constraints

### Loading Schemas

**From File (CLI):**
```bash
docextract extract document.pdf --schema my_schema.json --output data.json
```

**From File (Python):**
```python
import json
from agentic_document_extractor import DocumentProcessor

with open("my_schema.json") as f:
    schema = json.load(f)

processor = DocumentProcessor()
result = processor.process("document.pdf")
data = processor.extract_schema(result, schema)
```

**Inline (Python):**
```python
schema = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "date": {"type": "string"}
    }
}

data = processor.extract_schema(result, schema)
```

## Field Types and Usage

### String

Text data of any length.

```json
{
  "name": {
    "type": "string",
    "description": "Person's full name"
  },
  "email": {
    "type": "string",
    "format": "email",
    "description": "Email address"
  }
}
```

**Use for:** Names, addresses, descriptions, IDs, dates (as text)

### Integer

Whole numbers without decimals.

```json
{
  "age": {
    "type": "integer",
    "description": "Age in years",
    "minimum": 0,
    "maximum": 150
  },
  "quantity": {
    "type": "integer",
    "description": "Number of items",
    "minimum": 1
  }
}
```

**Use for:** Counts, quantities, ages, years

### Number

Numeric values that can include decimals.

```json
{
  "price": {
    "type": "number",
    "description": "Item price",
    "minimum": 0
  },
  "tax_rate": {
    "type": "number",
    "description": "Tax rate as percentage (e.g., 18 for 18%)",
    "minimum": 0,
    "maximum": 100
  }
}
```

**Use for:** Prices, percentages, measurements, ratings

### Boolean

True/false values.

```json
{
  "is_paid": {
    "type": "boolean",
    "description": "Whether the invoice has been paid"
  },
  "urgent": {
    "type": "boolean",
    "description": "Urgent delivery required"
  }
}
```

**Use for:** Yes/no questions, checkboxes, flags

### Array

Lists of items (homogeneous or heterogeneous).

```json
{
  "tags": {
    "type": "array",
    "description": "Document tags",
    "items": {
      "type": "string"
    }
  }
}
```

**Use for:** Lists, repeated items, collections

### Object

Nested structures (maps/dictionaries).

```json
{
  "address": {
    "type": "object",
    "description": "Mailing address",
    "properties": {
      "street": {"type": "string"},
      "city": {"type": "string"},
      "postal_code": {"type": "string"}
    }
  }
}
```

**Use for:** Grouped fields, nested data, complex structures

## Nested Structures

### When to Use Nesting

Use nested objects to group logically related fields:

```json
{
  "vendor": {
    "type": "object",
    "description": "Vendor information",
    "properties": {
      "name": {"type": "string", "description": "Vendor name"},
      "tax_id": {"type": "string", "description": "Tax ID number"},
      "contact": {
        "type": "object",
        "description": "Contact details",
        "properties": {
          "phone": {"type": "string"},
          "email": {"type": "string"}
        }
      }
    },
    "required": ["name"]
  }
}
```

### Nesting Best Practices

1. **Limit depth** — Max 2-3 levels recommended
2. **Logical grouping** — Group related fields only
3. **Clear descriptions** — Describe the purpose of each level
4. **Consider flattening** — Deep nesting can reduce extraction accuracy

**Good nesting:**
```json
{
  "customer": {
    "type": "object",
    "properties": {
      "name": {"type": "string"},
      "email": {"type": "string"}
    }
  }
}
```

**Over-nested (avoid):**
```json
{
  "document": {
    "type": "object",
    "properties": {
      "metadata": {
        "type": "object",
        "properties": {
          "author": {
            "type": "object",
            "properties": {
              "details": {
                "type": "object",
                "properties": {
                  "name": {"type": "string"}
                }
              }
            }
          }
        }
      }
    }
  }
}
```

## Arrays and Repeating Data

### Simple Arrays

Arrays of primitive types:

```json
{
  "categories": {
    "type": "array",
    "description": "Product categories",
    "items": {
      "type": "string"
    }
  }
}
```

**Example output:**
```json
{
  "categories": ["Electronics", "Computing", "Accessories"]
}
```

### Object Arrays

Arrays of complex objects (most common pattern):

```json
{
  "line_items": {
    "type": "array",
    "description": "Invoice line items",
    "items": {
      "type": "object",
      "properties": {
        "description": {"type": "string"},
        "quantity": {"type": "integer"},
        "unit_price": {"type": "number"},
        "total": {"type": "number"}
      },
      "required": ["description", "quantity", "total"]
    }
  }
}
```

**Example output:**
```json
{
  "line_items": [
    {
      "description": "Widget A",
      "quantity": 10,
      "unit_price": 5.99,
      "total": 59.90
    },
    {
      "description": "Widget B",
      "quantity": 5,
      "unit_price": 12.50,
      "total": 62.50
    }
  ]
}
```

### Array Constraints

Control array size:

```json
{
  "items": {
    "type": "array",
    "minItems": 1,
    "maxItems": 100,
    "items": {"type": "string"}
  }
}
```

## Best Practices

### 1. Descriptive Field Names

Use clear, self-documenting names:

✅ **Good:**
- `invoice_number`
- `customer_name`
- `total_amount`
- `transaction_date`

❌ **Avoid:**
- `inv_no`
- `cust`
- `amt`
- `date` (too generic)

### 2. Comprehensive Descriptions

Add helpful descriptions to guide the AI:

```json
{
  "invoice_date": {
    "type": "string",
    "description": "Date when the invoice was issued in YYYY-MM-DD format"
  }
}
```

### 3. Appropriate Types

Match types to data:

```json
{
  "age": {"type": "integer"},           // Not "string"
  "price": {"type": "number"},          // Not "string"
  "is_active": {"type": "boolean"},     // Not "string"
  "date": {"type": "string"}            // OK as ISO date string
}
```

### 4. Required Fields

Mark essential fields as required:

```json
{
  "type": "object",
  "properties": {
    "invoice_number": {"type": "string"},
    "date": {"type": "string"},
    "total": {"type": "number"},
    "notes": {"type": "string"}
  },
  "required": ["invoice_number", "date", "total"]
}
```

### 5. Validation Constraints

Add constraints where appropriate:

```json
{
  "quantity": {
    "type": "integer",
    "minimum": 1,
    "maximum": 9999
  },
  "email": {
    "type": "string",
    "format": "email"
  },
  "status": {
    "type": "string",
    "enum": ["draft", "pending", "approved", "rejected"]
  }
}
```

## Validation and Constraints

### Numeric Constraints

```json
{
  "age": {
    "type": "integer",
    "minimum": 0,
    "maximum": 150,
    "exclusiveMinimum": false,
    "exclusiveMaximum": false
  },
  "discount": {
    "type": "number",
    "minimum": 0,
    "maximum": 100,
    "multipleOf": 0.01
  }
}
```

### String Constraints

```json
{
  "postal_code": {
    "type": "string",
    "pattern": "^[0-9]{5}(-[0-9]{4})?$",
    "minLength": 5,
    "maxLength": 10
  },
  "email": {
    "type": "string",
    "format": "email"
  }
}
```

### Enum Constraints

Limit to specific values:

```json
{
  "status": {
    "type": "string",
    "enum": ["active", "inactive", "pending", "suspended"]
  },
  "priority": {
    "type": "string",
    "enum": ["low", "medium", "high", "urgent"]
  }
}
```

### Format Hints

JSON Schema supports these formats:
- `date-time` — ISO 8601 date-time
- `date` — ISO 8601 date
- `time` — ISO 8601 time
- `email` — Email address
- `uri` — URI/URL
- `uuid` — UUID

```json
{
  "created_at": {
    "type": "string",
    "format": "date-time"
  },
  "website": {
    "type": "string",
    "format": "uri"
  }
}
```

## Common Patterns

### Invoice/Bill Pattern

```json
{
  "type": "object",
  "properties": {
    "document_number": {"type": "string"},
    "date": {"type": "string"},
    "vendor": {
      "type": "object",
      "properties": {
        "name": {"type": "string"},
        "address": {"type": "string"}
      }
    },
    "line_items": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "description": {"type": "string"},
          "quantity": {"type": "integer"},
          "price": {"type": "number"}
        }
      }
    },
    "total": {"type": "number"}
  }
}
```

### Form Pattern

```json
{
  "type": "object",
  "properties": {
    "form_type": {"type": "string"},
    "applicant": {
      "type": "object",
      "properties": {
        "name": {"type": "string"},
        "email": {"type": "string"},
        "phone": {"type": "string"}
      }
    },
    "responses": {
      "type": "object",
      "additionalProperties": {"type": "string"}
    }
  }
}
```

### Table Pattern

```json
{
  "type": "object",
  "properties": {
    "records": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {"type": "string"},
          "name": {"type": "string"},
          "value": {"type": "number"}
        }
      }
    }
  }
}
```

## Examples

See the `examples/schemas/` directory for complete, real-world schema examples:
- **invoice_schema.json** — Commercial invoices
- **receipt_schema.json** — Purchase receipts
- **voter_list_schema.json** — Electoral rolls
- **agent_details_schema.json** — Agent registration forms

## Troubleshooting

### Problem: Extraction returns empty data

**Solutions:**
- Add more descriptive field descriptions
- Simplify field names
- Check document quality (OCR/layout detection)
- Verify schema syntax is valid JSON

### Problem: Wrong data type extracted

**Solutions:**
- Be explicit about types (use `integer` not `number` for whole numbers)
- Add format hints (e.g., "YYYY-MM-DD format")
- Use enum to constrain values
- Add validation constraints (min/max)

### Problem: Array not populating

**Solutions:**
- Ensure clear description of array purpose
- Check if document has repeating patterns
- Verify array item schema is correct
- Consider if data is actually array-like in document

### Problem: Nested data not extracted

**Solutions:**
- Reduce nesting depth
- Simplify structure
- Add descriptions at each nesting level
- Consider flattening into top-level fields

### Problem: Partial extraction

**Solutions:**
- Mark critical fields as required
- Add more context in descriptions
- Check if document contains all expected data
- Review extraction errors in output

## Resources

- [JSON Schema Official Site](https://json-schema.org/)
- [Understanding JSON Schema](https://json-schema.org/understanding-json-schema/)
- [JSON Schema Validator](https://www.jsonschemavalidator.net/)
- [Example Schemas](../examples/schemas/)
- [Project README](../README.md)

## Getting Help

If you need assistance:
1. Review the example schemas in `examples/schemas/`
2. Check the troubleshooting section above
3. Validate your schema at jsonschemavalidator.net
4. Open an issue on GitHub with:
   - Your schema
   - Sample document (if possible)
   - Expected vs actual output
