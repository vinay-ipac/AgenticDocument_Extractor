"""Core components for document processing."""

import os

# Disable PaddlePaddle PIR to avoid oneDNN incompatibility on Windows.
# Must be set BEFORE any paddle import throughout the application.
os.environ.setdefault("FLAGS_enable_pir_api", "0")
os.environ.setdefault("FLAGS_enable_pir_in_executor", "0")
os.environ.setdefault("FLAGS_enable_pir_with_pt_in_dy2st", "0")
os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")

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
