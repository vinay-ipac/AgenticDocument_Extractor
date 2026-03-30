"""
Agentic Document Extractor - End-to-end document extraction using DPT architecture.

This package provides tools for extracting structured data from Indian government
and administrative documents, with support for Hindi and English languages.

Example usage:
    from agentic_document_extractor import DocumentProcessor

    processor = DocumentProcessor()
    result = processor.process("voter_list.pdf")
    voters = processor.extract_voter_list(result)
"""

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
    VOTER_LIST_SCHEMA,
    AGENT_DETAILS_SCHEMA,
    GENERIC_FORM_SCHEMA,
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
    "VOTER_LIST_SCHEMA",
    "AGENT_DETAILS_SCHEMA",
    "GENERIC_FORM_SCHEMA",
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
