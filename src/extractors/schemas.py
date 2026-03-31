"""Predefined JSON schemas for common document types."""

# Generic Form Schema
GENERIC_FORM_SCHEMA = {
    "type": "object",
    "title": "Generic Form",
    "description": "Generic schema for form field extraction",
    "properties": {
        "form_type": {
            "type": "string",
            "description": "Type or title of the form"
        },
        "form_number": {
            "type": "string",
            "description": "Form number or code"
        },
        "fields": {
            "type": "object",
            "description": "Extracted form fields as key-value pairs",
            "additionalProperties": {
                "type": "string"
            }
        },
        "checkboxes": {
            "type": "object",
            "description": "Checkbox states",
            "additionalProperties": {
                "type": "boolean"
            }
        },
        "signatures": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "label": {"type": "string"},
                    "present": {"type": "boolean"},
                    "name": {"type": "string"}
                }
            }
        },
        "stamps": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "type": {"type": "string"},
                    "date": {"type": "string"}
                }
            }
        },
        "dates": {
            "type": "object",
            "description": "All dates found in the form",
            "additionalProperties": {
                "type": "string"
            }
        },
        "confidence": {
            "type": "number",
            "minimum": 0,
            "maximum": 1
        }
    },
    "required": ["fields"]
}

# Table Schema (generic)
TABLE_SCHEMA = {
    "type": "object",
    "title": "Table Data",
    "description": "Generic schema for table extraction",
    "properties": {
        "headers": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Table column headers"
        },
        "rows": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": {"type": "string"}
            },
            "description": "Table rows as objects"
        },
        "table_title": {
            "type": "string",
            "description": "Table title or caption"
        },
        "notes": {
            "type": "string",
            "description": "Any notes or footnotes"
        },
        "row_count": {
            "type": "integer",
            "description": "Number of data rows"
        },
        "column_count": {
            "type": "integer",
            "description": "Number of columns"
        }
    },
    "required": ["headers", "rows"]
}


def get_schema(schema_name: str) -> dict:
    """
    Get a predefined schema by name.

    Args:
        schema_name: Name of the schema (generic_form, table)

    Returns:
        JSON schema dictionary

    Raises:
        ValueError: If schema name is not recognized
    """
    schemas = {
        "generic_form": GENERIC_FORM_SCHEMA,
        "table": TABLE_SCHEMA,
    }
    if schema_name not in schemas:
        raise ValueError(
            f"Unknown schema: '{schema_name}'. "
            f"Available schemas: {', '.join(schemas.keys())}. "
            f"For custom schemas, provide a path to a JSON schema file or pass a schema dict directly."
        )
    return schemas[schema_name]
