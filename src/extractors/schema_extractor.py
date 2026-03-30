"""Schema-based data extractor."""

import json
import logging
import re
from typing import Optional, Union

from PIL import Image

from ..core.dataclasses import DocumentLayout, RegionType
from ..core.region_processor import RegionProcessor
from .schemas import get_schema, VOTER_LIST_SCHEMA, AGENT_DETAILS_SCHEMA

logger = logging.getLogger(__name__)


class SchemaExtractor:
    """
    Extract structured data using JSON schemas.

    Uses VLM to extract fields according to schema definitions.
    """

    def __init__(
        self,
        vlm_client,
        region_processor: Optional[RegionProcessor] = None,
        default_confidence_threshold: float = 0.5,
    ):
        """
        Initialize schema extractor.

        Args:
            vlm_client: OpenAI-compatible VLM client
            region_processor: RegionProcessor instance
            default_confidence_threshold: Minimum confidence for field inclusion
        """
        self.vlm_client = vlm_client
        self.region_processor = region_processor or RegionProcessor()
        self.confidence_threshold = default_confidence_threshold

    def extract(
        self,
        schema: Union[dict, str],
        image: Image.Image,
        layout: Optional[DocumentLayout] = None,
        context: str = "",
    ) -> dict:
        """
        Extract data according to schema.

        Args:
            schema: JSON schema dict or schema name string
            image: PIL Image of document
            layout: Optional DocumentLayout for context
            context: Additional context string

        Returns:
            Extracted data matching schema
        """
        # Get schema if name provided
        if isinstance(schema, str):
            schema = get_schema(schema)

        # Build prompt
        prompt = self._build_extraction_prompt(schema, context, layout)

        # Encode image
        image_b64 = self.region_processor.get_full_image_base64(image)

        try:
            response = self.vlm_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert document data extraction assistant. "
                            "Extract data from documents according to JSON schemas. "
                            "Return only valid JSON, no additional text. "
                            "Preserve original language (Hindi/English) for text values."
                        ),
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_b64}"
                                },
                            },
                            {"type": "text", "text": prompt},
                        ],
                    },
                ],
                max_tokens=3000,
                temperature=0.1,
            )

            result_text = response.choices[0].message.content
            return self._parse_result(result_text, schema)

        except Exception as e:
            logger.error(f"Schema extraction failed: {e}")
            return {"error": str(e), "schema_used": schema}

    def _build_extraction_prompt(
        self,
        schema: dict,
        context: str,
        layout: Optional[DocumentLayout],
    ) -> str:
        """Build extraction prompt."""
        prompt = """Extract data from this document according to the following JSON schema.

"""
        if context:
            prompt += f"Context: {context}\n\n"

        if layout:
            # Add layout context
            text_regions = []
            for region in layout.regions[:20]:  # Limit to first 20 regions
                if region.combined_text:
                    text_regions.append(
                        f"- [{region.region_type.value}] {region.combined_text[:200]}"
                    )
            if text_regions:
                prompt += "Detected text regions:\n" + "\n".join(text_regions) + "\n\n"

        prompt += "JSON Schema:\n"
        prompt += json.dumps(schema, indent=2)
        prompt += """

Instructions:
1. Extract all fields defined in the schema
2. Use null for fields that cannot be found
3. For arrays, extract all matching entries
4. Preserve original text in Hindi (Devanagari) or English
5. Standardize dates to YYYY-MM-DD format if possible
6. For numeric values, extract clean numbers without formatting
7. Include confidence scores (0-1) for extractions

Return ONLY valid JSON matching the schema structure."""

        return prompt

    def _parse_result(self, result_text: str, schema: dict) -> dict:
        """Parse extraction result."""
        result_text = result_text.strip()

        # Handle markdown code blocks
        for marker in ["```json", "```"]:
            if marker in result_text:
                start = result_text.find(marker) + len(marker)
                end = result_text.find("```", start)
                if end > start:
                    result_text = result_text[start:end].strip()
                    break

        # Try to parse JSON
        try:
            result = json.loads(result_text)
            # Add confidence if not present
            if "confidence" not in result:
                result["confidence"] = self._estimate_confidence(result_text)
            return result
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse error: {e}")
            # Try to extract JSON object
            match = re.search(r"\{[\s\S]*\}", result_text)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass

            return {
                "raw_response": result_text,
                "parse_error": str(e),
                "schema_used": schema,
            }

    def _estimate_confidence(self, result_text: str) -> float:
        """Estimate confidence from result."""
        # Simple heuristic based on response characteristics
        confidence = 0.7  # Base confidence

        # Increase for longer, detailed responses
        if len(result_text) > 500:
            confidence += 0.1

        # Decrease for error indicators
        if "error" in result_text.lower():
            confidence -= 0.2
        if "unable" in result_text.lower():
            confidence -= 0.1
        if "unclear" in result_text.lower():
            confidence -= 0.1

        return max(0.0, min(1.0, confidence))

    def extract_voter_list(
        self,
        image: Image.Image,
        layout: Optional[DocumentLayout] = None,
    ) -> dict:
        """
        Extract voter list using predefined schema.

        Args:
            image: PIL Image
            layout: Optional DocumentLayout

        Returns:
            Extracted voter data
        """
        return self.extract(
            schema=VOTER_LIST_SCHEMA,
            image=image,
            layout=layout,
            context="This is a voter list/electoral roll document. Extract all voter entries.",
        )

    def extract_agent_details(
        self,
        image: Image.Image,
        layout: Optional[DocumentLayout] = None,
    ) -> dict:
        """
        Extract agent details using predefined schema.

        Args:
            image: PIL Image
            layout: Optional DocumentLayout

        Returns:
            Extracted agent data
        """
        return self.extract(
            schema=AGENT_DETAILS_SCHEMA,
            image=image,
            layout=layout,
            context="This is an agent registration/details form. Extract agent information.",
        )

    def validate_extraction(
        self,
        extracted_data: dict,
        schema: dict,
    ) -> dict:
        """
        Validate extracted data against schema.

        Args:
            extracted_data: Extracted data
            schema: JSON schema

        Returns:
            Validation result with errors
        """
        errors = []

        # Check required fields
        required = schema.get("required", [])
        for field in required:
            if field not in extracted_data or extracted_data[field] is None:
                errors.append(f"Missing required field: {field}")

        # Validate field types
        properties = schema.get("properties", {})
        for field, value in extracted_data.items():
            if field in properties:
                prop_schema = properties[field]
                expected_type = prop_schema.get("type")

                if expected_type == "string" and value is not None and not isinstance(value, str):
                    errors.append(f"Field {field} should be string")
                elif expected_type == "integer" and value is not None and not isinstance(value, int):
                    errors.append(f"Field {field} should be integer")
                elif expected_type == "number" and value is not None and not isinstance(value, (int, float)):
                    errors.append(f"Field {field} should be number")
                elif expected_type == "array" and value is not None and not isinstance(value, list):
                    errors.append(f"Field {field} should be array")
                elif expected_type == "object" and value is not None and not isinstance(value, dict):
                    errors.append(f"Field {field} should be object")

                # Check enum values
                if "enum" in prop_schema and value not in prop_schema["enum"]:
                    errors.append(f"Field {field} value not in allowed values: {prop_schema['enum']}")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "extracted_data": extracted_data,
        }

    def extract_from_regions(
        self,
        schema: Union[dict, str],
        layout: DocumentLayout,
        image: Image.Image,
        target_region_types: Optional[list[RegionType]] = None,
    ) -> dict:
        """
        Extract data focusing on specific region types.

        Args:
            schema: JSON schema or name
            layout: DocumentLayout
            image: PIL Image
            target_region_types: Region types to focus on

        Returns:
            Extracted data
        """
        if isinstance(schema, str):
            schema = get_schema(schema)

        if target_region_types is None:
            target_region_types = [RegionType.TABLE, RegionType.FORM, RegionType.TEXT]

        # Get relevant regions
        relevant_regions = [
            r for r in layout.regions if r.region_type in target_region_types
        ]

        # Build context from relevant regions
        context_parts = []
        for region in relevant_regions:
            if region.combined_text:
                context_parts.append(f"[{region.region_type.value}]: {region.combined_text}")

        context = "\n\n".join(context_parts)

        return self.extract(
            schema=schema,
            image=image,
            layout=layout,
            context=context,
        )
