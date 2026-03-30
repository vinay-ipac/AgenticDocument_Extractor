"""Predefined JSON schemas for common document types."""

# Voter List Schema
VOTER_LIST_SCHEMA = {
    "type": "object",
    "title": "Voter List",
    "description": "Schema for extracting voter information from electoral rolls",
    "properties": {
        "voters": {
            "type": "array",
            "description": "List of voters extracted from the document",
            "items": {
                "type": "object",
                "properties": {
                    "serial_number": {
                        "type": "string",
                        "description": "Voter serial number in the list (क्रमांक)"
                    },
                    "name": {
                        "type": "string",
                        "description": "Voter name (नाम)"
                    },
                    "father_name": {
                        "type": "string",
                        "description": "Father's or husband's name"
                    },
                    "age": {
                        "type": "integer",
                        "description": "Voter age in years (आयु)"
                    },
                    "gender": {
                        "type": "string",
                        "enum": ["Male", "Female", "Other"],
                        "description": "Voter gender (लिंग)"
                    },
                    "address": {
                        "type": "string",
                        "description": "Voter address including village/locality (पता/गांव)"
                    },
                    "constituency": {
                        "type": "string",
                        "description": "Assembly constituency (निर्वाचन क्षेत्र)"
                    },
                    "assembly_constituency_no": {
                        "type": "integer",
                        "description": "Assembly constituency number"
                    },
                    "part_no": {
                        "type": "string",
                        "description": "Part number of electoral roll"
                    },
                    "epic_no": {
                        "type": "string",
                        "description": "EPIC (Electoral Photo Identity Card) number"
                    },
                    "date_of_birth": {
                        "type": "string",
                        "description": "Date of birth if available"
                    },
                    "confidence": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 1,
                        "description": "Confidence score for this extraction"
                    }
                },
                "required": ["name"]
            }
        },
        "metadata": {
            "type": "object",
            "properties": {
                "total_voters": {
                    "type": "integer",
                    "description": "Total number of voters in the list"
                },
                "constituency_name": {
                    "type": "string",
                    "description": "Name of the constituency"
                },
                "part_number": {
                    "type": "string",
                    "description": "Part number of the electoral roll"
                },
                "year": {
                    "type": "string",
                    "description": "Year of the electoral roll"
                },
                "language": {
                    "type": "string",
                    "description": "Primary language of the document"
                }
            }
        },
        "extraction_notes": {
            "type": "string",
            "description": "Any notes about the extraction quality or issues"
        }
    },
    "required": ["voters"]
}

# Agent Details Schema
AGENT_DETAILS_SCHEMA = {
    "type": "object",
    "title": "Agent Details",
    "description": "Schema for extracting agent registration details",
    "properties": {
        "agent_name": {
            "type": "string",
            "description": "Full name of the agent (एजेंट का नाम)"
        },
        "agent_id": {
            "type": "string",
            "description": "Unique agent identifier (एजेंट आईडी)"
        },
        "contact_number": {
            "type": "string",
            "description": "Contact phone number (संपर्क नंबर)"
        },
        "alternate_contact": {
            "type": "string",
            "description": "Alternate contact number"
        },
        "email": {
            "type": "string",
            "format": "email",
            "description": "Email address"
        },
        "area": {
            "type": "string",
            "description": "Assigned area or location (क्षेत्र)"
        },
        "district": {
            "type": "string",
            "description": "District name"
        },
        "state": {
            "type": "string",
            "description": "State name"
        },
        "pin_code": {
            "type": "string",
            "description": "PIN code"
        },
        "status": {
            "type": "string",
            "enum": ["Active", "Inactive", "Pending", "Suspended"],
            "description": "Current agent status (स्थिति)"
        },
        "registration_date": {
            "type": "string",
            "description": "Date of registration (पंजीकरण तिथि)"
        },
        "valid_until": {
            "type": "string",
            "description": "Validity end date"
        },
        "supervisor_name": {
            "type": "string",
            "description": "Name of supervising officer"
        },
        "office_address": {
            "type": "string",
            "description": "Office address"
        },
        "confidence": {
            "type": "number",
            "minimum": 0,
            "maximum": 1,
            "description": "Overall confidence score"
        },
        "additional_info": {
            "type": "object",
            "description": "Any additional fields found in the form"
        }
    },
    "required": ["agent_name"]
}

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
        schema_name: Name of the schema

    Returns:
        JSON schema dictionary
    """
    schemas = {
        "voter_list": VOTER_LIST_SCHEMA,
        "agent_details": AGENT_DETAILS_SCHEMA,
        "generic_form": GENERIC_FORM_SCHEMA,
        "table": TABLE_SCHEMA,
    }
    return schemas.get(schema_name, GENERIC_FORM_SCHEMA)
