"""Tests for VLM tools."""

import pytest
from unittest.mock import Mock, MagicMock
from PIL import Image

from agentic_document_extractor.agents.tools import (
    AnalyzeTable,
    AnalyzeTableHindi,
    AnalyzeForm,
    AnalyzeStamp,
    AnalyzeChart,
    create_vlm_tools,
)
from agentic_document_extractor.core.dataclasses import LayoutRegion, BoundingBox, RegionType
from agentic_document_extractor.core.region_processor import RegionProcessor


class MockVLMClient:
    """Mock VLM client for testing."""

    def __init__(self, response_text='{"test": "result"}'):
        self.response_text = response_text
        self.chat = Mock()
        self.chat.completions = Mock()

    def create_response(self, **kwargs):
        """Create a mock response."""
        response = Mock()
        choice = Mock()
        choice.message = Mock()
        choice.message.content = self.response_text
        response.choices = [choice]
        return response


class TestAnalyzeTable:
    """Test AnalyzeTable tool."""

    @pytest.fixture
    def mock_client(self):
        """Create mock VLM client."""
        client = MockVLMClient()
        client.chat.completions.create = Mock(
            return_value=client.create_response()
        )
        return client

    @pytest.fixture
    def sample_image(self):
        """Create test image."""
        return Image.new("RGB", (400, 400), color="white")

    @pytest.fixture
    def region_processor(self):
        """Create region processor."""
        return RegionProcessor()

    @pytest.fixture
    def table_region(self):
        """Create a table region."""
        return LayoutRegion(
            id="table_1",
            region_type=RegionType.TABLE,
            bbox=BoundingBox(50, 50, 350, 350),
            reading_order=1,
        )

    def test_analyze_table_initialization(self, mock_client, region_processor, sample_image):
        """Test AnalyzeTable initialization."""
        tool = AnalyzeTable(mock_client, region_processor, sample_image)
        assert tool.name == "analyze_table"
        assert tool.description != ""

    def test_analyze_table_runs(self, mock_client, region_processor, sample_image, table_region):
        """Test AnalyzeTable execution."""
        tool = AnalyzeTable(mock_client, region_processor, sample_image)
        tool._regions = [table_region]

        result = tool._run("table_1")
        assert isinstance(result, dict)
        assert "region_id" in result
        assert result["region_id"] == "table_1"

    def test_analyze_table_region_not_found(self, mock_client, region_processor, sample_image):
        """Test AnalyzeTable with invalid region."""
        tool = AnalyzeTable(mock_client, region_processor, sample_image)
        tool._regions = []

        result = tool._run("nonexistent")
        assert "error" in result

    def test_analyze_table_parses_json(self, mock_client, region_processor, sample_image, table_region):
        """Test JSON parsing in response."""
        json_response = '{"headers": ["Name", "Age"], "rows": [{"Name": "John", "Age": "30"}]}'
        mock_client.response_text = json_response
        mock_client.chat.completions.create = Mock(
            return_value=mock_client.create_response()
        )

        tool = AnalyzeTable(mock_client, region_processor, sample_image)
        tool._regions = [table_region]

        result = tool._run("table_1")
        assert "headers" in result.get("analysis", result) or "headers" in result


class TestAnalyzeForm:
    """Test AnalyzeForm tool."""

    @pytest.fixture
    def mock_client(self):
        client = MockVLMClient()
        client.chat.completions.create = Mock(
            return_value=client.create_response()
        )
        return client

    @pytest.fixture
    def sample_image(self):
        return Image.new("RGB", (400, 600), color="white")

    @pytest.fixture
    def form_region(self):
        return LayoutRegion(
            id="form_1",
            region_type=RegionType.FORM,
            bbox=BoundingBox(50, 50, 350, 550),
            reading_order=1,
        )

    def test_analyze_form_runs(self, mock_client, region_processor, sample_image, form_region):
        """Test AnalyzeForm execution."""
        from agentic_document_extractor.core.region_processor import RegionProcessor
        region_processor = RegionProcessor()

        tool = AnalyzeForm(mock_client, region_processor, sample_image)
        tool._regions = [form_region]

        result = tool._run("form_1")
        assert isinstance(result, dict)
        assert result["region_id"] == "form_1"
        assert result["region_type"] == "form"


class TestAnalyzeStamp:
    """Test AnalyzeStamp tool."""

    @pytest.fixture
    def mock_client(self):
        client = MockVLMClient()
        client.chat.completions.create = Mock(
            return_value=client.create_response()
        )
        return client

    @pytest.fixture
    def sample_image(self):
        return Image.new("RGB", (400, 400), color="white")

    @pytest.fixture
    def stamp_region(self):
        return LayoutRegion(
            id="stamp_1",
            region_type=RegionType.STAMP,
            bbox=BoundingBox(150, 150, 250, 250),
            reading_order=1,
        )

    def test_analyze_stamp_runs(self, mock_client, sample_image, stamp_region):
        """Test AnalyzeStamp execution."""
        from agentic_document_extractor.core.region_processor import RegionProcessor
        region_processor = RegionProcessor()

        tool = AnalyzeStamp(mock_client, region_processor, sample_image)
        tool._regions = [stamp_region]

        result = tool._run("stamp_1")
        assert isinstance(result, dict)
        assert result["region_type"] == "stamp"


class TestAnalyzeChart:
    """Test AnalyzeChart tool."""

    @pytest.fixture
    def mock_client(self):
        client = MockVLMClient()
        client.chat.completions.create = Mock(
            return_value=client.create_response()
        )
        return client

    @pytest.fixture
    def sample_image(self):
        return Image.new("RGB", (500, 400), color="white")

    @pytest.fixture
    def chart_region(self):
        return LayoutRegion(
            id="chart_1",
            region_type=RegionType.CHART,
            bbox=BoundingBox(50, 50, 450, 350),
            reading_order=1,
        )

    def test_analyze_chart_runs(self, mock_client, sample_image, chart_region):
        """Test AnalyzeChart execution."""
        from agentic_document_extractor.core.region_processor import RegionProcessor
        region_processor = RegionProcessor()

        tool = AnalyzeChart(mock_client, region_processor, sample_image)
        tool._regions = [chart_region]

        result = tool._run("chart_1")
        assert isinstance(result, dict)
        assert result["region_type"] == "chart"


class TestCreateVLMTools:
    """Test VLM tools creation."""

    @pytest.fixture
    def mock_client(self):
        return MockVLMClient()

    @pytest.fixture
    def sample_image(self):
        return Image.new("RGB", (400, 400), color="white")

    @pytest.fixture
    def regions(self):
        return [
            LayoutRegion(
                id="table_1",
                region_type=RegionType.TABLE,
                bbox=BoundingBox(50, 50, 350, 350),
                reading_order=1,
            )
        ]

    def test_create_vlm_tools_returns_list(self, mock_client, sample_image, regions):
        """Test that create_vlm_tools returns a list."""
        from agentic_document_extractor.core.region_processor import RegionProcessor
        region_processor = RegionProcessor()

        tools = create_vlm_tools(mock_client, region_processor, sample_image, regions)
        assert isinstance(tools, list)
        assert len(tools) == 5  # 5 tools created

    def test_create_vlm_tools_has_all_tools(self, mock_client, sample_image, regions):
        """Test that all expected tools are created."""
        from agentic_document_extractor.core.region_processor import RegionProcessor
        region_processor = RegionProcessor()

        tools = create_vlm_tools(mock_client, region_processor, sample_image, regions)
        tool_names = [t.name for t in tools]

        assert "analyze_table" in tool_names
        assert "analyze_table_hindi" in tool_names
        assert "analyze_form" in tool_names
        assert "analyze_stamp" in tool_names
        assert "analyze_chart" in tool_names
