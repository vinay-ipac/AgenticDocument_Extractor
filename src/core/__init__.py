"""Core components for document processing."""

from .dataclasses import OCRRegion, LayoutRegion, DocumentLayout
from .ocr_engine import OCREngine
from .layout_detector import LayoutDetector
from .region_processor import RegionProcessor

__all__ = [
    "OCRRegion",
    "LayoutRegion",
    "DocumentLayout",
    "OCREngine",
    "LayoutDetector",
    "RegionProcessor",
]
