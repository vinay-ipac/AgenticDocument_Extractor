"""Tests for layout detector."""

import pytest
from PIL import Image

from agentic_document_extractor.core.layout_detector import LayoutDetector
from agentic_document_extractor.core.dataclasses import (
    LayoutRegion,
    DocumentLayout,
    RegionType,
    LayoutType,
    BoundingBox,
)


class TestLayoutDetector:
    """Test layout detector functionality."""

    @pytest.fixture
    def layout_detector(self):
        """Create layout detector instance."""
        return LayoutDetector(use_gpu=False, min_region_area=500)

    @pytest.fixture
    def sample_image(self):
        """Create a test image."""
        return Image.new("RGB", (800, 600), color="white")

    def test_initialization(self, layout_detector):
        """Test layout detector initialization."""
        assert layout_detector.use_gpu is False
        assert layout_detector.min_region_area == 500
        assert layout_detector._initialized is False

    def test_detect_returns_document_layout(self, layout_detector, sample_image):
        """Test that detection returns DocumentLayout."""
        layout = layout_detector.detect(sample_image)
        assert isinstance(layout, DocumentLayout)

    def test_document_layout_properties(self, layout_detector, sample_image):
        """Test DocumentLayout properties."""
        layout = layout_detector.detect(sample_image)
        assert layout.image_width == 800
        assert layout.image_height == 600
        assert layout.page_number == 1
        assert isinstance(layout.layout_type, LayoutType)

    def test_layout_has_regions(self, layout_detector, sample_image):
        """Test that layout contains regions."""
        layout = layout_detector.detect(sample_image)
        assert isinstance(layout.regions, list)
        # At least one region should exist (full image if nothing detected)
        assert len(layout.regions) >= 1

    def test_region_properties(self, layout_detector, sample_image):
        """Test LayoutRegion properties."""
        layout = layout_detector.detect(sample_image)
        for region in layout.regions:
            assert isinstance(region, LayoutRegion)
            assert hasattr(region, "id")
            assert hasattr(region, "region_type")
            assert hasattr(region, "bbox")
            assert hasattr(region, "reading_order")

    def test_reading_order_assigned(self, layout_detector, sample_image):
        """Test that reading order is assigned to regions."""
        layout = layout_detector.detect(sample_image)
        for i, region in enumerate(layout.regions):
            assert region.reading_order == i

    def test_get_regions_by_type(self, layout_detector, sample_image):
        """Test filtering regions by type."""
        layout = layout_detector.detect(sample_image)
        text_regions = layout.get_regions_by_type(RegionType.TEXT)
        assert isinstance(text_regions, list)

    def test_sort_by_reading_order(self, layout_detector, sample_image):
        """Test sorting regions by reading order."""
        layout = layout_detector.detect(sample_image)
        layout.sort_by_reading_order()
        # Verify order
        for i in range(len(layout.regions) - 1):
            assert layout.regions[i].reading_order <= layout.regions[i + 1].reading_order

    def test_layout_to_dict(self, layout_detector, sample_image):
        """Test DocumentLayout serialization."""
        layout = layout_detector.detect(sample_image)
        data = layout.to_dict()
        assert "document_path" in data
        assert "page_number" in data
        assert "image_width" in data
        assert "image_height" in data
        assert "regions" in data

    def test_layout_from_dict(self):
        """Test DocumentLayout deserialization."""
        data = {
            "document_path": "/test/doc.pdf",
            "page_number": 1,
            "image_width": 800,
            "image_height": 600,
            "layout_type": "single_column",
            "language": "en",
            "regions": [],
        }
        layout = DocumentLayout.from_dict(data)
        assert layout.document_path == "/test/doc.pdf"
        assert layout.image_width == 800
        assert layout.layout_type == LayoutType.SINGLE_COLUMN

    def test_add_region(self, layout_detector, sample_image):
        """Test adding regions to layout."""
        layout = layout_detector.detect(sample_image)
        initial_count = len(layout.regions)

        new_region = LayoutRegion(
            id="test_region",
            region_type=RegionType.TEXT,
            bbox=BoundingBox(0, 0, 100, 100),
            reading_order=999,
        )
        layout.add_region(new_region)

        assert len(layout.regions) == initial_count + 1

    def test_get_region_by_id(self, layout_detector, sample_image):
        """Test getting region by ID."""
        layout = layout_detector.detect(sample_image)
        if layout.regions:
            region = layout.regions[0]
            found = layout.get_region_by_id(region.id)
            assert found == region


class TestLayoutTypeDetection:
    """Test layout type detection."""

    @pytest.fixture
    def layout_detector(self):
        return LayoutDetector()

    def test_determine_layout_type_empty(self, layout_detector):
        """Test layout type with no regions."""
        layout_type = layout_detector._determine_layout_type([], 800)
        assert layout_type == LayoutType.SINGLE_COLUMN

    def test_determine_layout_type_single_column(self, layout_detector):
        """Test single column detection."""
        regions = [
            LayoutRegion(
                id=f"r{i}",
                region_type=RegionType.TEXT,
                bbox=BoundingBox(100, i * 100, 700, i * 100 + 50),
                reading_order=i,
            )
            for i in range(3)
        ]
        layout_type = layout_detector._determine_layout_type(regions, 800)
        assert layout_type == LayoutType.SINGLE_COLUMN
