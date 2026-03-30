"""VLM-based analysis tools for document regions."""

import json
import logging
from typing import Optional

from langchain_core.tools import BaseTool

from ..core.dataclasses import LayoutRegion, RegionType
from .prompts import (
    TABLE_ANALYSIS_PROMPT,
    TABLE_HINDI_PROMPT,
    FORM_ANALYSIS_PROMPT,
    STAMP_ANALYSIS_PROMPT,
    CHART_ANALYSIS_PROMPT,
)

logger = logging.getLogger(__name__)


class VLMToolMixin:
    """Mixin for VLM-based tools."""

    def __init__(self, vlm_client, region_processor, image, document_context: str = "", language: str = "en"):
        """
        Initialize VLM tool.

        Args:
            vlm_client: OpenAI-compatible VLM client
            region_processor: RegionProcessor instance
            image: PIL Image of the full document
            document_context: Context about the document
            language: Primary document language
        """
        self.vlm_client = vlm_client
        self.region_processor = region_processor
        self.image = image
        self.document_context = document_context
        self.language = language

    def _call_vlm(self, prompt: str, region_b64: str, max_tokens: int = 2000) -> str:
        """
        Call VLM with image and prompt.

        Args:
            prompt: Text prompt
            region_b64: Base64 encoded region image
            max_tokens: Maximum tokens in response

        Returns:
            VLM response text
        """
        content = [
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{region_b64}"},
            },
            {"type": "text", "text": prompt},
        ]

        response = self.vlm_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": content,
                }
            ],
            max_tokens=max_tokens,
        )

        return response.choices[0].message.content

    def _parse_json_response(self, response: str) -> dict:
        """
        Parse JSON from VLM response.

        Args:
            response: VLM response text

        Returns:
            Parsed JSON dict
        """
        # Try to extract JSON from response
        response = response.strip()

        # Handle markdown code blocks
        if "```json" in response:
            start = response.find("```json") + 7
            end = response.find("```", start)
            response = response[start:end].strip()
        elif "```" in response:
            start = response.find("```") + 3
            end = response.find("```", start)
            response = response[start:end].strip()

        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON: {e}")
            # Try to find JSON in the response
            start_brace = response.find("{")
            end_brace = response.rfind("}") + 1
            if start_brace >= 0 and end_brace > start_brace:
                json_str = response[start_brace:end_brace]
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    pass

            # Return partial result
            return {"raw_response": response, "parse_error": str(e)}


class AnalyzeTable(VLMToolMixin, BaseTool):
    """Tool for analyzing tables in documents."""

    name: str = "analyze_table"
    description: str = "Analyze a table region and extract structured row-column data"

    def __init__(self, vlm_client, region_processor, image, document_context: str = "", language: str = "en"):
        super().__init__(vlm_client, region_processor, image, document_context, language)
        self.args_schema = None  # Dynamic schema

    def _run(self, region_id: str, use_hindi: bool = False) -> dict:
        """
        Analyze a table region.

        Args:
            region_id: ID of the layout region to analyze
            use_hindi: Whether to use Hindi prompt

        Returns:
            Extracted table data as JSON
        """
        # Find region
        region = self._get_region(region_id)
        if region is None:
            return {"error": f"Region {region_id} not found"}

        # Process region
        region_b64 = self.region_processor.process_region(self.image, region)

        # Select prompt based on language
        if use_hindi or self.language == "hi":
            prompt = TABLE_HINDI_PROMPT
        else:
            prompt = TABLE_ANALYSIS_PROMPT

        # Call VLM
        response = self._call_vlm(prompt, region_b64)

        # Parse response
        result = self._parse_json_response(response)
        result["region_id"] = region_id
        result["region_type"] = "table"

        logger.info(f"Analyzed table region {region_id}")
        return result

    def _get_region(self, region_id: str) -> Optional[LayoutRegion]:
        """Get region by ID from document context."""
        # This will be set by the orchestrator
        if hasattr(self, "_regions"):
            for region in self._regions:
                if region.id == region_id:
                    return region
        return None


class AnalyzeTableHindi(VLMToolMixin, BaseTool):
    """Tool for analyzing Hindi tables in documents."""

    name: str = "analyze_table_hindi"
    description: str = "Analyze a Hindi table region and extract structured data (uses Hindi prompts)"

    def __init__(self, vlm_client, region_processor, image, document_context: str = "", language: str = "hi"):
        super().__init__(vlm_client, region_processor, image, document_context, language)
        self.args_schema = None

    def _run(self, region_id: str) -> dict:
        """
        Analyze a Hindi table region.

        Args:
            region_id: ID of the layout region to analyze

        Returns:
            Extracted table data as JSON
        """
        # Use the same implementation as AnalyzeTable but force Hindi
        table_tool = AnalyzeTable(
            self.vlm_client,
            self.region_processor,
            self.image,
            self.document_context,
            "hi",
        )
        table_tool._regions = getattr(self, "_regions", [])
        return table_tool._run(region_id, use_hindi=True)


class AnalyzeForm(VLMToolMixin, BaseTool):
    """Tool for analyzing forms in documents."""

    name: str = "analyze_form"
    description: str = "Analyze a form region and extract field-value pairs"

    def __init__(self, vlm_client, region_processor, image, document_context: str = "", language: str = "en"):
        super().__init__(vlm_client, region_processor, image, document_context, language)
        self.args_schema = None

    def _run(self, region_id: str) -> dict:
        """
        Analyze a form region.

        Args:
            region_id: ID of the layout region to analyze

        Returns:
            Extracted form data as JSON
        """
        region = self._get_region(region_id)
        if region is None:
            return {"error": f"Region {region_id} not found"}

        region_b64 = self.region_processor.process_region(self.image, region)
        response = self._call_vlm(FORM_ANALYSIS_PROMPT, region_b64)
        result = self._parse_json_response(response)
        result["region_id"] = region_id
        result["region_type"] = "form"

        logger.info(f"Analyzed form region {region_id}")
        return result

    def _get_region(self, region_id: str) -> Optional[LayoutRegion]:
        if hasattr(self, "_regions"):
            for region in self._regions:
                if region.id == region_id:
                    return region
        return None


class AnalyzeStamp(VLMToolMixin, BaseTool):
    """Tool for analyzing stamps and seals on documents."""

    name: str = "analyze_stamp"
    description: str = "Analyze a stamp or seal region and extract text/metadata"

    def __init__(self, vlm_client, region_processor, image, document_context: str = "", language: str = "en"):
        super().__init__(vlm_client, region_processor, image, document_context, language)
        self.args_schema = None

    def _run(self, region_id: str) -> dict:
        """
        Analyze a stamp/seal region.

        Args:
            region_id: ID of the layout region to analyze

        Returns:
            Extracted stamp data as JSON
        """
        region = self._get_region(region_id)
        if region is None:
            return {"error": f"Region {region_id} not found"}

        region_b64 = self.region_processor.process_region(self.image, region)
        response = self._call_vlm(STAMP_ANALYSIS_PROMPT, region_b64, max_tokens=500)
        result = self._parse_json_response(response)
        result["region_id"] = region_id
        result["region_type"] = "stamp"

        logger.info(f"Analyzed stamp region {region_id}")
        return result

    def _get_region(self, region_id: str) -> Optional[LayoutRegion]:
        if hasattr(self, "_regions"):
            for region in self._regions:
                if region.id == region_id:
                    return region
        return None


class AnalyzeChart(VLMToolMixin, BaseTool):
    """Tool for analyzing charts and graphs in documents."""

    name: str = "analyze_chart"
    description: str = "Analyze a chart or graph region and extract data points"

    def __init__(self, vlm_client, region_processor, image, document_context: str = "", language: str = "en"):
        super().__init__(vlm_client, region_processor, image, document_context, language)
        self.args_schema = None

    def _run(self, region_id: str) -> dict:
        """
        Analyze a chart/graph region.

        Args:
            region_id: ID of the layout region to analyze

        Returns:
            Extracted chart data as JSON
        """
        region = self._get_region(region_id)
        if region is None:
            return {"error": f"Region {region_id} not found"}

        region_b64 = self.region_processor.process_region(self.image, region)
        response = self._call_vlm(CHART_ANALYSIS_PROMPT, region_b64)
        result = self._parse_json_response(response)
        result["region_id"] = region_id
        result["region_type"] = "chart"

        logger.info(f"Analyzed chart region {region_id}")
        return result

    def _get_region(self, region_id: str) -> Optional[LayoutRegion]:
        if hasattr(self, "_regions"):
            for region in self._regions:
                if region.id == region_id:
                    return region
        return None


def create_vlm_tools(
    vlm_client,
    region_processor,
    image,
    regions: list,
    document_context: str = "",
    language: str = "en",
) -> list:
    """
    Create VLM tools with context.

    Args:
        vlm_client: OpenAI VLM client
        region_processor: RegionProcessor instance
        image: PIL Image of document
        regions: List of LayoutRegion objects
        document_context: Document context string
        language: Document language

    Returns:
        List of configured tool instances
    """
    tools = [
        AnalyzeTable(vlm_client, region_processor, image, document_context, language),
        AnalyzeTableHindi(vlm_client, region_processor, image, document_context, language),
        AnalyzeForm(vlm_client, region_processor, image, document_context, language),
        AnalyzeStamp(vlm_client, region_processor, image, document_context, language),
        AnalyzeChart(vlm_client, region_processor, image, document_context, language),
    ]

    # Set regions on all tools
    for tool in tools:
        tool._regions = regions

    return tools
