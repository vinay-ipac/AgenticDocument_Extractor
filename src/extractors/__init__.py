"""Schema-based extractors."""

from .schemas import (
    GENERIC_FORM_SCHEMA,
    TABLE_SCHEMA,
    get_schema,
)
from .schema_extractor import SchemaExtractor

__all__ = [
    "GENERIC_FORM_SCHEMA",
    "TABLE_SCHEMA",
    "get_schema",
    "SchemaExtractor",
]
