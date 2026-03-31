"""Tests for document processing pipeline."""

import pytest
from pathlib import Path
from PIL import Image
from unittest.mock import Mock, patch

from agentic_document_extractor.pipelines.document_processor import (
    DocumentProcessor,
    ProcessingResult,
)
from agentic_document_extractor.core.dataclasses import RegionType

from agentic_document_extractor.utils.helpers import load_document

class TestProcessingResult:
    """Test ProcessingResult dataclass."""

    def test_creation(self):
        """Test ProcessingResult creation."""
        result = ProcessingResult(
            document_path="test.pdf",
            page_count=1,
        )
        assert result.document_path == "test.pdf"
        assert result.page_count == 1
        assert result.processing_time == 0.0
        assert result.errors == []

    def test_to_dict(self):
        """Test ProcessingResult serialization."""
        result = ProcessingResult(
            document_path="test.pdf",
            page_count=2,
            processing_time=1.5,
        )
        data = result.to_dict()
        assert data["document_path"] == "test.pdf"
        assert data["page_count"] == 2
        assert data["processing_time"] == 1.5

    def test_save_json(self, tmp_path):
        """Test saving results to JSON."""
        result = ProcessingResult(
            document_path="test.pdf",
            page_count=1,
        )
        output_path = tmp_path / "results.json"
        result.save_json(output_path)
        assert output_path.exists()


class TestDocumentProcessor:
    """Test DocumentProcessor pipeline."""

    @pytest.fixture
    def processor(self):
        """Create DocumentProcessor instance."""
        return DocumentProcessor(
            ocr_languages=("en",),
            use_gpu=False,
            verbose=False,
            max_pages=10,
        )

    @pytest.fixture
    def sample_image(self):
        """Create test image."""
        return Image.new("RGB", (800, 600), color="white")

    def test_initialization(self, processor):
        """Test DocumentProcessor initialization."""
        assert processor.ocr_languages == ("en",)
        assert processor.use_gpu is False
        assert processor.max_pages == 10

    def test_process_image(self, processor, sample_image):
        """Test processing a PIL Image."""
        result = processor.process(sample_image, analyze_regions=False)
        assert isinstance(result, ProcessingResult)
        assert result.page_count == 1
        assert len(result.layouts) == 1

    def test_process_returns_result(self, processor, sample_image):
        """Test that process returns ProcessingResult."""
        result = processor.process(sample_image, analyze_regions=False)
        assert hasattr(result, "document_path")
        assert hasattr(result, "page_count")
        assert hasattr(result, "layouts")
        assert hasattr(result, "processing_time")

    def test_process_multiple_images(self, processor, sample_image):
        """Test processing multiple images."""
        images = [sample_image, sample_image]
        result = processor.process(images, analyze_regions=False)
        assert result.page_count == 2
        assert len(result.layouts) == 2

    def test_process_respects_max_pages(self, sample_image):
        """Test that max_pages is respected."""
        processor = DocumentProcessor(max_pages=2)
        images = [sample_image] * 5
        result = processor.process(images, analyze_regions=False)
        assert result.page_count <= 2

    def test_layout_detected(self, processor, sample_image):
        """Test that layout is detected."""
        result = processor.process(sample_image, analyze_regions=False)
        assert len(result.layouts) > 0
        layout = result.layouts[0]
        assert len(layout.regions) > 0

    def test_processing_time_recorded(self, processor, sample_image):
        """Test that processing time is recorded."""
        result = processor.process(sample_image, analyze_regions=False)
        assert result.processing_time > 0

    @patch("agentic_document_extractor.pipelines.document_processor.load_document")
    def test_process_from_path(self, mock_load, processor, sample_image):
        """Test processing from file path."""
        mock_load.return_value = [sample_image]

        result = processor.process("test.pdf", analyze_regions=False)
        assert result.page_count == 1
        mock_load.assert_called_once()


class TestDocumentProcessorExtraction:
    """Test extraction functionality."""

    @pytest.fixture
    def processor(self):
        """Create processor without VLM (for basic tests)."""
        return DocumentProcessor(
            ocr_languages=("en",),
            verbose=False,
        )

    @pytest.fixture
    def sample_image(self):
        return Image.new("RGB", (800, 600), color="white")

    def test_extract_schema_without_vlm(self):
        """Test schema extraction without VLM."""
        from unittest.mock import Mock

        # Mock the OpenAI client and its response
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content='{"fields": {}}'))]
        mock_vlm = Mock()
        mock_vlm.chat.completions.create.return_value = mock_response

        processor = DocumentProcessor(vlm_client=mock_vlm)

        # Create a minimal result with proper layout mock
        from PIL import Image
        mock_layout = Mock()
        mock_layout.regions = []  # Empty regions list

        result = ProcessingResult(
            document_path="test.pdf",
            page_count=1,
            images=[Image.new("RGB", (400, 400))],
            layouts=[mock_layout]
        )

        # Use valid schema name or dict
        extraction = processor.extract_schema(result, "generic_form")
        assert extraction is not None
        assert isinstance(extraction, dict)

    def test_visualize(self, processor, sample_image, tmp_path):
        """Test visualization generation."""
        result = processor.process(sample_image, analyze_regions=False)

        output_path = tmp_path / "layout.png"
        path = processor.visualize(result, tmp_path)
        assert path.exists()

    def test_generate_report(self, processor, sample_image, tmp_path):
        """Test report generation."""
        result = processor.process(sample_image, analyze_regions=False)

        generated = processor.generate_report(result, tmp_path)
        assert "json" in generated
        assert generated["json"].exists()


class TestRegionTypeFiltering:
    """Test region type filtering in processing."""

    @pytest.fixture
    def processor(self):
        return DocumentProcessor(verbose=False)

    @pytest.fixture
    def sample_image(self):
        return Image.new("RGB", (800, 600), color="white")

    def test_analyze_specific_region_types(self, processor, sample_image):
        """Test analyzing specific region types."""
        result = processor.process(
            sample_image,
            analyze_regions=True,
            region_types=[RegionType.TABLE],
        )
        # Should complete without error
        assert isinstance(result, ProcessingResult)


class TestDocumentLoading:
    """Test document loading functionality."""

    def test_load_image_file(self):
        """Test loading an image file."""
        from agentic_document_extractor.utils.helpers import load_document

        # Create a test image
        img = Image.new("RGB", (100, 100), color="red")
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            img.save(f.name)
            temp_path = f.name

        try:
            images = load_document(temp_path)
            assert len(images) == 1
            assert images[0].size == (100, 100)
        finally:
            os.unlink(temp_path)

    def test_load_nonexistent_file(self):
        """Test loading nonexistent file raises error."""
        from agentic_document_extractor.utils.helpers import load_document

        with pytest.raises(FileNotFoundError):
            load_document("nonexistent.pdf")

    def test_load_unsupported_format(self, tmp_path):
        """Test loading unsupported file format."""
        # ✅ CREATE a temp file with unsupported extension
        unsupported_file = tmp_path / "document.txt"
        unsupported_file.write_text("Some text")
        
        # ✅ Now test that it raises appropriate error
        with pytest.raises((FileNotFoundError, ValueError)) as exc_info:    
            load_document(str(unsupported_file))
        
        # Verify it's format error, not file not found
        assert "supported" in str(exc_info.value).lower() or "format" in str(exc_info.value).lower()
