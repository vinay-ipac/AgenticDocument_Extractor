"""
Agentic Document Extractor - End-to-end document extraction using DPT architecture.

This package provides a generic, schema-driven system for extracting structured data
from any document type using custom JSON schemas.

Example usage:
    from agentic_document_extractor import DocumentProcessor

    processor = DocumentProcessor()
    result = processor.process("document.pdf")
    data = processor.extract_schema(result, "generic_form")
"""

import os

# Disable PaddlePaddle PIR to avoid oneDNN incompatibility on Windows.
# Must be set BEFORE any paddle import throughout the application.
os.environ.setdefault("FLAGS_enable_pir_api", "0")
os.environ.setdefault("FLAGS_enable_pir_in_executor", "0")
os.environ.setdefault("FLAGS_enable_pir_with_pt_in_dy2st", "0")
os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")

from .pipelines.document_processor import DocumentProcessor, ProcessingResult
from .core.dataclasses import (
    OCRRegion,
    LayoutRegion,
    DocumentLayout,
    BoundingBox,
    RegionType,
    LayoutType,
)
from .core.ocr_engine import OCREngine
from .core.layout_detector import LayoutDetector
from .core.region_processor import RegionProcessor
from .agents.orchestrator import AgentOrchestrator
from .extractors.schema_extractor import SchemaExtractor
from .extractors.schemas import (
    GENERIC_FORM_SCHEMA,
    TABLE_SCHEMA,
    get_schema,
)
from .utils.helpers import (
    load_document,
    pdf_to_images,
    save_results_json,
    save_results_csv,
)
from .utils.visualization import draw_layout, create_comparison_view

__version__ = "0.1.0"
__author__ = "IPAC"

__all__ = [
    # Version
    "__version__",
    # Main processor
    "DocumentProcessor",
    "ProcessingResult",
    # Core components
    "OCREngine",
    "LayoutDetector",
    "RegionProcessor",
    # Agent
    "AgentOrchestrator",
    # Extractors
    "SchemaExtractor",
    # Schemas
    "GENERIC_FORM_SCHEMA",
    "TABLE_SCHEMA",
    "get_schema",
    # Data classes
    "OCRRegion",
    "LayoutRegion",
    "DocumentLayout",
    "BoundingBox",
    "RegionType",
    "LayoutType",
    # Utilities
    "load_document",
    "pdf_to_images",
    "save_results_json",
    "save_results_csv",
    "draw_layout",
    "create_comparison_view",
]
