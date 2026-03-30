"""Agent Orchestrator for coordinating document analysis."""

import json
import logging
from typing import Optional, Union

from PIL import Image

from ..core.dataclasses import DocumentLayout, LayoutRegion, RegionType
from ..core.region_processor import RegionProcessor
from .tools import create_vlm_tools
from .prompts import SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Orchestrates VLM-based document analysis using LangChain agents.

    Coordinates tools for table, form, stamp, and chart analysis.
    """

    def __init__(
        self,
        vlm_client,
        region_processor: Optional[RegionProcessor] = None,
        verbose: bool = True,
        max_iterations: int = 10,
    ):
        """
        Initialize the orchestrator.

        Args:
            vlm_client: OpenAI-compatible VLM client
            region_processor: RegionProcessor instance (created if not provided)
            verbose: Enable verbose logging
            max_iterations: Maximum agent iterations
        """
        self.vlm_client = vlm_client
        self.region_processor = region_processor or RegionProcessor()
        self.verbose = verbose
        self.max_iterations = max_iterations
        self._agent = None
        self._current_image: Optional[Image.Image] = None
        self._current_layout: Optional[DocumentLayout] = None

    def _create_agent(self, document_context: str, language: str):
        """
        Create LangChain agent with tools.

        Args:
            document_context: Context about the document
            language: Document language
        """
        try:
            from langchain.agents import create_tool_calling_agent, AgentExecutor
            from langchain_core.prompts import ChatPromptTemplate
            from langchain_openai import ChatOpenAI

            # Create tools
            tools = create_vlm_tools(
                self.vlm_client,
                self.region_processor,
                self._current_image,
                self._current_layout.regions if self._current_layout else [],
                document_context,
                language,
            )

            # Create prompt
            prompt = ChatPromptTemplate.from_messages([
                ("system", SYSTEM_PROMPT),
                ("human", "{input}"),
                ("ai", "{agent_scratchpad}"),
            ])

            # Create LLM
            llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0,
                max_tokens=2000,
            )

            # Create agent
            agent = create_tool_calling_agent(llm, tools, prompt)

            # Create executor
            self._agent = AgentExecutor(
                agent=agent,
                tools=tools,
                verbose=self.verbose,
                max_iterations=self.max_iterations,
                handle_parsing_errors=True,
            )

            logger.info("Created LangChain agent executor")

        except ImportError as e:
            logger.warning(f"LangChain not available, using direct tool calls: {e}")
            self._agent = None

    def _direct_tool_execution(
        self,
        tool_name: str,
        region_id: str,
    ) -> dict:
        """
        Execute a tool directly without LangChain.

        Args:
            tool_name: Name of the tool to use
            region_id: ID of the region to analyze

        Returns:
            Tool result
        """
        # Find region
        region = None
        for r in self._current_layout.regions:
            if r.id == region_id:
                region = r
                break

        if region is None:
            return {"error": f"Region {region_id} not found"}

        # Create appropriate tool
        from .tools import (
            AnalyzeTable,
            AnalyzeTableHindi,
            AnalyzeForm,
            AnalyzeStamp,
            AnalyzeChart,
        )

        tool_map = {
            "analyze_table": AnalyzeTable,
            "analyze_table_hindi": AnalyzeTableHindi,
            "analyze_form": AnalyzeForm,
            "analyze_stamp": AnalyzeStamp,
            "analyze_chart": AnalyzeChart,
        }

        tool_class = tool_map.get(tool_name)
        if tool_class is None:
            return {"error": f"Unknown tool: {tool_name}"}

        # Determine if Hindi should be used
        use_hindi = (
            tool_name == "analyze_table_hindi"
            or (region.region_type == RegionType.TABLE and self._current_layout.language == "hi")
        )

        tool = tool_class(
            self.vlm_client,
            self.region_processor,
            self._current_image,
            "",  # document_context
            self._current_layout.language if self._current_layout else "en",
        )
        tool._regions = self._current_layout.regions

        if tool_name in ("analyze_table", "analyze_table_hindi"):
            return tool._run(region_id, use_hindi=use_hindi)
        else:
            return tool._run(region_id)

    def analyze_regions(
        self,
        layout: DocumentLayout,
        image: Image.Image,
        region_types: Optional[list[RegionType]] = None,
        region_ids: Optional[list[str]] = None,
    ) -> dict:
        """
        Analyze specified regions in the document.

        Args:
            layout: DocumentLayout with regions
            image: PIL Image of the document
            region_types: Types of regions to analyze (default: TABLE, FORM, STAMP, CHART)
            region_ids: Specific region IDs to analyze (overrides region_types)

        Returns:
            Dictionary mapping region IDs to analysis results
        """
        self._current_image = image
        self._current_layout = layout

        # Determine which regions to analyze
        if region_ids:
            regions_to_analyze = [
                r for r in layout.regions if r.id in region_ids
            ]
        else:
            if region_types is None:
                region_types = [
                    RegionType.TABLE,
                    RegionType.FORM,
                    RegionType.STAMP,
                    RegionType.CHART,
                    RegionType.HANDWRITING,
                ]
            regions_to_analyze = [
                r for r in layout.regions if r.region_type in region_types
            ]

        if not regions_to_analyze:
            logger.info("No regions to analyze")
            return {}

        logger.info(f"Analyzing {len(regions_to_analyze)} regions")

        results = {}

        for region in regions_to_analyze:
            logger.info(f"Analyzing region {region.id} (type: {region.region_type.value})")

            # Determine appropriate tool
            tool_name = self._get_tool_for_region(region)

            try:
                if self._agent is not None:
                    # Use LangChain agent
                    result = self._invoke_agent(
                        f"Analyze region {region.id} using {tool_name}",
                        layout.language,
                    )
                else:
                    # Direct execution
                    result = self._direct_tool_execution(tool_name, region.id)

                results[region.id] = {
                    "region_type": region.region_type.value,
                    "reading_order": region.reading_order,
                    "analysis": result,
                }

            except Exception as e:
                logger.error(f"Failed to analyze region {region.id}: {e}")
                results[region.id] = {
                    "region_type": region.region_type.value,
                    "error": str(e),
                }

        return results

    def _get_tool_for_region(self, region: LayoutRegion) -> str:
        """Get appropriate tool name for a region type."""
        tool_map = {
            RegionType.TABLE: "analyze_table",
            RegionType.FORM: "analyze_form",
            RegionType.STAMP: "analyze_stamp",
            RegionType.CHART: "analyze_chart",
            RegionType.HANDWRITING: "analyze_form",
        }
        return tool_map.get(region.region_type, "analyze_form")

    def _invoke_agent(self, query: str, language: str) -> dict:
        """
        Invoke the LangChain agent.

        Args:
            query: User query
            language: Document language

        Returns:
            Agent response
        """
        if self._agent is None:
            raise RuntimeError("Agent not initialized")

        response = self._agent.invoke({
            "input": query,
        })

        return response.get("output", response)

    def extract_with_schema(
        self,
        layout: DocumentLayout,
        image: Image.Image,
        schema: dict,
    ) -> dict:
        """
        Extract data according to a JSON schema.

        Args:
            layout: DocumentLayout
            image: PIL Image
            schema: JSON schema defining expected fields

        Returns:
            Extracted data matching schema
        """
        self._current_image = image
        self._current_layout = layout

        # Create prompt for schema-based extraction
        schema_prompt = self._create_schema_prompt(schema)

        # Process full image
        full_b64 = self.region_processor.get_full_image_base64(image)

        try:
            response = self.vlm_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a document data extraction assistant. Extract data according to the provided schema.\n\nSchema:\n{json.dumps(schema, indent=2)}",
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/png;base64,{full_b64}"},
                            },
                            {"type": "text", "text": schema_prompt},
                        ],
                    },
                ],
                max_tokens=2000,
                temperature=0,
            )

            result_text = response.choices[0].message.content
            return self._parse_extraction_result(result_text, schema)

        except Exception as e:
            logger.error(f"Schema-based extraction failed: {e}")
            return {"error": str(e), "schema": schema}

    def _create_schema_prompt(self, schema: dict) -> str:
        """Create prompt for schema-based extraction."""
        prompt = """Extract the following fields from this document.

Return your response as valid JSON matching this structure:
"""
        prompt += json.dumps(schema, indent=2)
        prompt += """

Instructions:
- Return only the JSON, no additional text
- Use null for fields that cannot be found
- Include confidence scores where applicable
- Preserve original language (Hindi/English) for text values
"""
        return prompt

    def _parse_extraction_result(self, result_text: str, schema: dict) -> dict:
        """Parse extraction result into structured format."""
        result_text = result_text.strip()

        # Handle markdown code blocks
        if "```json" in result_text:
            start = result_text.find("```json") + 7
            end = result_text.find("```", start)
            result_text = result_text[start:end].strip()
        elif "```" in result_text:
            start = result_text.find("```") + 3
            end = result_text.find("```", start)
            result_text = result_text[start:end].strip()

        try:
            return json.loads(result_text)
        except json.JSONDecodeError:
            # Try to find JSON in response
            start_brace = result_text.find("{")
            end_brace = result_text.rfind("}") + 1
            if start_brace >= 0 and end_brace > start_brace:
                try:
                    return json.loads(result_text[start_brace:end_brace])
                except json.JSONDecodeError:
                    pass

            return {"raw_response": result_text, "parse_error": "Failed to parse JSON"}

    def summarize_document(
        self,
        layout: DocumentLayout,
        image: Image.Image,
    ) -> dict:
        """
        Generate a summary of the document.

        Args:
            layout: DocumentLayout
            image: PIL Image

        Returns:
            Document summary
        """
        self._current_image = image
        self._current_layout = layout

        # Process full image
        full_b64 = self.region_processor.get_full_image_base64(image)

        # Create context from layout
        region_summary = []
        for region in layout.regions:
            region_summary.append(
                f"- {region.region_type.value} (order {region.reading_order}): "
                f"{region.combined_text[:100]}..." if region.combined_text else ""
            )

        context = "\n".join(region_summary)

        try:
            response = self.vlm_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a document analysis assistant. Summarize the document's content and structure.",
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/png;base64,{full_b64}"},
                            },
                            {
                                "type": "text",
                                "text": f"""Summarize this document.

Document structure:
{context}

Include in your summary:
1. Document type (voter list, form, report, etc.)
2. Main content/subject
3. Language(s) used
4. Key sections or fields
5. Any notable features (stamps, signatures, tables)

Return as JSON:
{{
    "document_type": "",
    "subject": "",
    "languages": [],
    "key_sections": [],
    "notable_features": [],
    "page_count_estimate": 1
}}
""",
                            },
                        ],
                    },
                ],
                max_tokens=1500,
                temperature=0.3,
            )

            result_text = response.choices[0].message.content
            return self._parse_extraction_result(result_text, {})

        except Exception as e:
            logger.error(f"Document summarization failed: {e}")
            return {"error": str(e)}
