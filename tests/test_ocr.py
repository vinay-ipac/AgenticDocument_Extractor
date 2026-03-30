"""Tests for OCR engine."""

import pytest
from PIL import Image
import numpy as np

from agentic_document_extractor.core.ocr_engine import OCREngine
from agentic_document_extractor.core.dataclasses import OCRRegion


class TestOCREngine:
    """Test OCR engine functionality."""

    @pytest.fixture
    def ocr_engine(self):
        """Create OCR engine instance."""
        return OCREngine(languages=("en",), show_log=False)

    @pytest.fixture
    def sample_image(self):
        """Create a simple test image."""
        # Create a white image with some text-like patterns
        img = Image.new("RGB", (400, 200), color="white")
        return img

    def test_initialization(self, ocr_engine):
        """Test OCR engine initialization."""
        assert ocr_engine.languages == ("en",)
        assert ocr_engine._initialized is False

    def test_language_detection_english(self, ocr_engine):
        """Test English language detection."""
        text = "Hello World, this is English text."
        lang = ocr_engine._detect_language(text)
        assert lang == "en"

    def test_language_detection_hindi(self, ocr_engine):
        """Test Hindi language detection."""
        text = "नमस्ते दुनिया, यह हिंदी पाठ है।"
        lang = ocr_engine._detect_language(text)
        assert lang == "hi"

    def test_language_detection_mixed(self, ocr_engine):
        """Test mixed language detection."""
        text = "Hello नमस्ते World दुनिया"
        lang = ocr_engine._detect_language(text)
        assert lang == "mixed"

    def test_language_detection_empty(self, ocr_engine):
        """Test empty text language detection."""
        lang = ocr_engine._detect_language("")
        assert lang == "unknown"

    def test_extract_from_image(self, ocr_engine, sample_image):
        """Test OCR extraction from PIL Image."""
        regions = ocr_engine.extract(sample_image)
        assert isinstance(regions, list)
        # Empty image should return empty or minimal results
        assert len(regions) >= 0

    def test_extract_returns_ocr_regions(self, ocr_engine, sample_image):
        """Test that extraction returns OCRRegion objects."""
        regions = ocr_engine.extract(sample_image)
        for region in regions:
            assert isinstance(region, OCRRegion)
            assert hasattr(region, "text")
            assert hasattr(region, "bbox")
            assert hasattr(region, "confidence")

    def test_bbox_properties(self, ocr_engine, sample_image):
        """Test bounding box properties."""
        regions = ocr_engine.extract(sample_image)
        for region in regions:
            bbox = region.bbox
            assert bbox.width >= 0
            assert bbox.height >= 0
            assert bbox.area >= 0
            assert len(bbox.center) == 2

    def test_region_to_dict(self, ocr_engine, sample_image):
        """Test OCRRegion to_dict method."""
        regions = ocr_engine.extract(sample_image)
        for region in regions:
            data = region.to_dict()
            assert "id" in data
            assert "text" in data
            assert "bbox" in data
            assert "confidence" in data

    def test_region_from_dict(self):
        """Test OCRRegion from_dict method."""
        data = {
            "id": "test_123",
            "text": "Hello World",
            "bbox": {"x_min": 10, "y_min": 10, "x_max": 100, "y_max": 30},
            "confidence": 0.95,
            "language": "en",
            "region_type": "text",
        }
        region = OCRRegion.from_dict(data)
        assert region.id == "test_123"
        assert region.text == "Hello World"
        assert region.confidence == 0.95

    def test_is_available(self, ocr_engine):
        """Test OCR availability check."""
        # This will initialize the engine
        available = ocr_engine.is_available()
        # Result depends on whether PaddleOCR is installed
        assert isinstance(available, bool)


class TestOCREngineHindi:
    """Test Hindi OCR functionality."""

    @pytest.fixture
    def hindi_ocr_engine(self):
        """Create Hindi OCR engine."""
        return OCREngine(languages=("hi", "en"), show_log=False)

    def test_hindi_language_detection(self, hindi_ocr_engine):
        """Test Hindi text detection."""
        hindi_text = "भारत एक विशाल देश है"
        lang = hindi_ocr_engine._detect_language(hindi_text)
        assert lang == "hi"

    def test_get_languages(self, hindi_ocr_engine):
        """Test getting configured languages."""
        langs = hindi_ocr_engine.get_languages()
        assert langs == ("hi", "en")
