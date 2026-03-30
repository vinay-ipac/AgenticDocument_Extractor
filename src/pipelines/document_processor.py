"""End-to-end document processing pipeline."""

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Union

from PIL import Image

from ..core.dataclasses import DocumentLayout, RegionType
from ..core.ocr_engine import OCREngine
from ..core.layout_detector import LayoutDetector
from ..core.region_processor import RegionProcessor
from ..agents.orchestrator import AgentOrchestrator
from ..extractors.schema_extractor import SchemaExtractor
from ..utils.helpers import load_document, save_results_json, save_results_csv
from ..utils.visualization import draw_layout, generate_html_report

logger = logging.getLogger(__name__)


@dataclass
class ProcessingResult:
    """Result of document processing."""
    document_path: str
    page_count: int
    layouts: list[DocumentLayout] = field(default_factory=list)
    extractions: list[dict] = field(default_factory=list)
    analyses: list[dict] = field(default_factory=list)
    processing_time: float = 0.0
    images: list[Image.Image] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "document_path": self.document_path,
            "page_count": self.page_count,
            "layouts": [l.to_dict() for l in self.layouts],
            "extractions": self.extractions,
            "analyses": self.analyses,
            "processing_time": self.processing_time,
            "metadata": self.metadata,
            "errors": self.errors,
        }

    def save_json(self, output_path: Union[str, Path]) -> Path:
        """Save results to JSON."""
        return save_results_json(self.to_dict(), output_path)


class DocumentProcessor:
    """
    End-to-end document processing pipeline.

    Orchestrates OCR, layout detection, analysis, and extraction.
    """

    def __init__(
        self,
        vlm_client=None,
        ocr_languages: tuple = ("hi", "en"),
        use_gpu: bool = False,
        verbose: bool = True,
        ocr_padding: int = 10,
        max_pages: int = 100,
        dpi: int = 150,
    ):
        """
        Initialize document processor.

        Args:
            vlm_client: OpenAI VLM client (created if not provided)
            ocr_languages: OCR language tuple
            use_gpu: Use GPU acceleration
            verbose: Enable verbose logging
            ocr_padding: Padding for OCR regions
            max_pages: Maximum pages to process
            dpi: DPI for document conversion
        """
        self.ocr_languages = ocr_languages
        self.use_gpu = use_gpu
        self.verbose = verbose
        self.ocr_padding = ocr_padding
        self.max_pages = max_pages
        self.dpi = dpi

        # Initialize components
        self.ocr_engine = OCREngine(
            languages=ocr_languages,
            use_gpu=use_gpu,
            show_log=verbose,
        )

        self.layout_detector = LayoutDetector(use_gpu=use_gpu)
        self.region_processor = RegionProcessor(padding=ocr_padding)

        # Lazy initialization for VLM-dependent components
        self._vlm_client = vlm_client
        self._orchestrator = None
        self._schema_extractor = None

    @property
    def vlm_client(self):
        """Get or create VLM client."""
        if self._vlm_client is None:
            try:
                from openai import OpenAI
                self._vlm_client = OpenAI()
            except ImportError:
                logger.warning("OpenAI not installed. VLM features disabled.")
                return None
        return self._vlm_client

    @property
    def orchestrator(self) -> Optional[AgentOrchestrator]:
        """Get or create orchestrator."""
        if self._orchestrator is None and self.vlm_client:
            self._orchestrator = AgentOrchestrator(
                vlm_client=self.vlm_client,
                region_processor=self.region_processor,
                verbose=self.verbose,
            )
        return self._orchestrator

    @property
    def schema_extractor(self) -> Optional[SchemaExtractor]:
        """Get or create schema extractor."""
        if self._schema_extractor is None and self.vlm_client:
            self._schema_extractor = SchemaExtractor(
                vlm_client=self.vlm_client,
                region_processor=self.region_processor,
            )
        return self._schema_extractor

    def process(
        self,
        document: Union[str, Path, Image.Image, list[Image.Image]],
        analyze_regions: bool = True,
        region_types: Optional[list[RegionType]] = None,
        layout_output_dir: Optional[Union[str, Path]] = None,
    ) -> ProcessingResult:
        """
        Process a document through the full pipeline.

        Args:
            document: Document path, image, or list of images
            analyze_regions: Whether to analyze regions with VLM
            region_types: Types of regions to analyze
            layout_output_dir: Optional directory to save layout detection images

        Returns:
            ProcessingResult with all outputs
        """
        start_time = time.time()
        errors = []

        # Load document
        try:
            if isinstance(document, (str, Path)):
                images = load_document(document, dpi=self.dpi)
                document_path = str(document)
            elif isinstance(document, Image.Image):
                images = [document]
                document_path = "<image>"
            elif isinstance(document, list):
                images = document
                document_path = "<images>"
            else:
                raise ValueError(f"Unsupported document type: {type(document)}")

            # Limit pages
            if len(images) > self.max_pages:
                logger.warning(f"Limiting to {self.max_pages} pages")
                images = images[:self.max_pages]

        except Exception as e:
            logger.error(f"Failed to load document: {e}")
            return ProcessingResult(
                document_path=str(document) if hasattr(document, "__str__") else "<unknown>",
                page_count=0,
                errors=[str(e)],
            )

        # Prepare layout output directory
        if layout_output_dir:
            layout_output_dir = Path(layout_output_dir)
            layout_output_dir.mkdir(parents=True, exist_ok=True)

        layouts = []
        analyses = []

        # Process each page
        for i, image in enumerate(images):
            logger.info(f"Processing page {i + 1}/{len(images)}")

            try:
                # Step 1: OCR
                ocr_regions = self.ocr_engine.extract(image)
                logger.info(f"  Extracted {len(ocr_regions)} OCR regions")

                # Step 2: Layout detection
                layout_vis_path = None
                if layout_output_dir:
                    layout_vis_path = str(layout_output_dir / f"layout_page_{i + 1}.png")

                layout = self.layout_detector.detect(
                    image,
                    ocr_regions=ocr_regions,
                    save_visualization=layout_vis_path,
                )
                layout.page_number = i + 1
                layouts.append(layout)
                logger.info(f"  Detected {len(layout.regions)} layout regions")

                # Step 2b: Also save our own visualization with region labels and reading order
                if layout_output_dir:
                    try:
                        vis_path = layout_output_dir / f"layout_annotated_page_{i + 1}.png"
                        draw_layout(
                            layout=layout,
                            image=image,
                            output_path=vis_path,
                            show_labels=True,
                            show_reading_order=True,
                            show_ocr=True,
                        )
                        logger.info(f"  Saved annotated layout to {vis_path}")
                    except Exception as e:
                        logger.warning(f"  Failed to save annotated layout: {e}")

                # Step 3: Region analysis (optional)
                if analyze_regions and self.orchestrator:
                    analysis = self.orchestrator.analyze_regions(
                        layout=layout,
                        image=image,
                        region_types=region_types,
                    )
                    if analysis:
                        analyses.append({
                            "page": i + 1,
                            "analysis": analysis,
                        })
                        logger.info(f"  Analyzed {len(analysis)} regions")

            except Exception as e:
                error_msg = f"Page {i + 1}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)

        processing_time = time.time() - start_time

        result = ProcessingResult(
            document_path=document_path,
            page_count=len(images),
            layouts=layouts,
            analyses=analyses,
            processing_time=processing_time,
            images=images,  # Always store for downstream extraction/visualization
            errors=errors,
        )

        logger.info(
            f"Processed {document_path} in {processing_time:.2f}s, "
            f"{len(layouts)} pages, {len(errors)} errors"
        )

        return result

    def extract_schema(
        self,
        result: ProcessingResult,
        schema: Union[dict, str],
        page: int = 0,
    ) -> dict:
        """
        Extract data using a schema from processed results.

        Args:
            result: ProcessingResult from process()
            schema: JSON schema or schema name
            page: Page index (0-based)

        Returns:
            Extracted data
        """
        if not self.schema_extractor:
            logger.error("Schema extractor not available (VLM client missing)")
            return {"error": "VLM client not configured"}

        # Layout is optional — VLM can extract from the image alone
        layout = result.layouts[page] if page < len(result.layouts) else None
        image = result.images[page] if page < len(result.images) else None

        if image is None:
            # Reload image if not stored
            image = Image.open(result.document_path)

        extraction = self.schema_extractor.extract(
            schema=schema,
            image=image,
            layout=layout,
        )

        result.extractions.append({
            "page": page + 1,
            "schema": schema if isinstance(schema, str) else schema.get("title", "custom"),
            "data": extraction,
        })

        return extraction

    def extract_voter_list(
        self,
        result: ProcessingResult,
        page: int = 0,
    ) -> dict:
        """Extract voter list data."""
        from ..extractors.schemas import VOTER_LIST_SCHEMA
        return self.extract_schema(result, VOTER_LIST_SCHEMA, page)

    def extract_agent_details(
        self,
        result: ProcessingResult,
        page: int = 0,
    ) -> dict:
        """Extract agent details."""
        from ..extractors.schemas import AGENT_DETAILS_SCHEMA
        return self.extract_schema(result, AGENT_DETAILS_SCHEMA, page)

    def visualize(
        self,
        result: ProcessingResult,
        output_dir: Union[str, Path],
        page: int = 0,
    ) -> Path:
        """
        Create visualization of processed results.

        Args:
            result: ProcessingResult
            output_dir: Output directory
            page: Page index

        Returns:
            Path to visualization
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        if page >= len(result.layouts):
            raise ValueError(f"Page {page} not found")

        layout = result.layouts[page]
        image = result.images[page] if page < len(result.images) else None

        output_path = output_dir / f"layout_page_{page + 1}.png"

        draw_layout(
            layout=layout,
            image=image,
            output_path=output_path,
            show_labels=True,
            show_reading_order=True,
        )

        return output_path

    def generate_report(
        self,
        result: ProcessingResult,
        output_dir: Union[str, Path],
    ) -> dict:
        """
        Generate comprehensive report files.

        Args:
            result: ProcessingResult
            output_dir: Output directory

        Returns:
            Dictionary of generated file paths
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        generated = {}

        # JSON results
        json_path = output_dir / "results.json"
        result.save_json(json_path)
        generated["json"] = json_path

        # HTML report
        if result.layouts:
            html_path = output_dir / "report.html"
            from ..core.region_processor import RegionProcessor
            rp = RegionProcessor()
            image_b64 = rp.get_full_image_base64(result.images[0]) if result.images else None

            generate_html_report(
                layout=result.layouts[0],
                extracted_data=result.extractions[0] if result.extractions else {},
                output_path=html_path,
                image_base64=image_b64,
            )
            generated["html"] = html_path

        # CSV exports for voter data
        if result.extractions:
            for i, ext in enumerate(result.extractions):
                if "data" in ext and "voters" in ext.get("data", {}):
                    voters = ext["data"]["voters"]
                    if voters:
                        csv_path = output_dir / f"voters_page_{ext['page']}.csv"
                        save_results_csv(voters, csv_path)
                        generated[f"csv_page_{ext['page']}"] = csv_path

        logger.info(f"Generated report files in {output_dir}")
        return generated

    def process_and_extract(
        self,
        document: Union[str, Path],
        schema: Optional[Union[dict, str]] = None,
        output_dir: Optional[Union[str, Path]] = None,
        analyze_regions: bool = True,
    ) -> ProcessingResult:
        """
        Process document and optionally extract with schema.

        Args:
            document: Document path
            schema: Optional schema for extraction
            output_dir: Optional output directory for results
            analyze_regions: Whether to analyze regions

        Returns:
            ProcessingResult
        """
        # Process document
        result = self.process(document, analyze_regions=analyze_regions)

        # Extract with schema if provided
        if schema and self.schema_extractor:
            extraction = self.extract_schema(result, schema)
            result.extractions.append({"schema": schema, "data": extraction})

        # Generate outputs if directory specified
        if output_dir:
            self.generate_report(result, output_dir)

        return result
