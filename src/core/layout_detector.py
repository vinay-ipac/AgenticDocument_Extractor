"""Layout Detection with Reading Order prediction."""

import logging
import uuid
from pathlib import Path
from typing import Optional, Union

import numpy as np
from PIL import Image

from .dataclasses import (
    LayoutRegion,
    OCRRegion,
    BoundingBox,
    RegionType,
    LayoutType,
    DocumentLayout,
)

logger = logging.getLogger(__name__)


# Mapping from PaddleOCR layout types to our RegionType
LAYOUT_TYPE_MAP = {
    "text": RegionType.TEXT,
    "title": RegionType.HEADER,
    "table": RegionType.TABLE,
    "figure": RegionType.IMAGE,
    "figure_caption": RegionType.TEXT,
    "table_caption": RegionType.TEXT,
    "formula": RegionType.TEXT,
    "equation": RegionType.TEXT,
    "stamp": RegionType.STAMP,
    "seal": RegionType.STAMP,
    "handwriting": RegionType.HANDWRITING,
    "form": RegionType.FORM,
}


class LayoutDetector:
    """
    Layout detection with reading order prediction.

    Uses PaddleOCR for layout detection and LayoutLMv3 for reading order.
    """

    def __init__(
        self,
        model_name: str = "layoutlmv3-base",
        use_gpu: bool = False,
        min_region_area: float = 1000.0,
    ):
        """
        Initialize layout detector.

        Args:
            model_name: LayoutLM model name for reading order
            use_gpu: Whether to use GPU
            min_region_area: Minimum area for a region to be considered
        """
        self.model_name = model_name
        self.use_gpu = use_gpu
        self.min_region_area = min_region_area
        self._layout_model = None
        self._reading_order_model = None
        self._initialized = False

    def _initialize(self):
        """Lazy initialization of models."""
        if self._initialized:
            return

        # Initialize PaddleOCR layout detection
        try:
            from paddleocr import PaddleOCR

            logger.info("Initializing PaddleOCR layout detection")
            self._layout_model = PaddleOCR(
                lang="en",
                use_gpu=self.use_gpu,
                show_log=False,
                use_angle_cls=False,
                det=False,  # Disable text detection, use layout only
                rec=False,  # Disable recognition
                layout=True,  # Enable layout analysis
            )
            logger.info("PaddleOCR layout model initialized")

        except Exception as e:
            logger.warning(f"Failed to initialize layout model: {e}")
            self._layout_model = None

        # Try to initialize LayoutLM for reading order
        try:
            from transformers import AutoModelForTokenClassification, AutoTokenizer

            logger.info(f"Loading LayoutLM model: {self.model_name}")
            self._reading_order_tokenizer = AutoTokenizer.from_pretrained(
                self.model_name, trust_remote_code=True
            )
            self._reading_order_model = AutoModelForTokenClassification.from_pretrained(
                self.model_name, trust_remote_code=True
            )
            logger.info("LayoutLM reading order model initialized")

        except Exception as e:
            logger.warning(f"Failed to load LayoutLM model: {e}")
            self._reading_order_model = None

        self._initialized = True

    def _detect_layout_with_paddle(self, image: Image.Image) -> list[dict]:
        """
        Detect layout using PaddleOCR.

        Args:
            image: PIL Image

        Returns:
            List of layout regions with type and bbox
        """
        if self._layout_model is None:
            return []

        try:
            import cv2
            cv2_image = np.array(image)
            if len(cv2_image.shape) == 3:
                cv2_image = cv2_image[:, :, ::-1]  # RGB to BGR

            result = self._layout_model.ocr(cv2_image, cls=False)

            regions = []
            if result:
                # Result format: [(box, (type, score)), ...]
                for item in result[0] if isinstance(result[0], list) else result:
                    if len(item) >= 2:
                        box = item[0]
                        layout_info = item[1]

                        if isinstance(layout_info, tuple) and len(layout_info) >= 2:
                            layout_type_str = layout_info[0]
                            score = layout_info[1]
                        else:
                            layout_type_str = str(layout_info)
                            score = 1.0

                        # Convert box to coordinates
                        box = np.array(box)
                        x_min = float(np.min(box[:, 0]))
                        x_max = float(np.max(box[:, 0]))
                        y_min = float(np.min(box[:, 1]))
                        y_max = float(np.max(box[:, 1]))

                        regions.append({
                            "type": layout_type_str,
                            "bbox": (x_min, y_min, x_max, y_max),
                            "score": float(score),
                        })

            return regions

        except Exception as e:
            logger.error(f"PaddleOCR layout detection failed: {e}")
            return []

    def _predict_reading_order(
        self, regions: list[LayoutRegion], image: Image.Image
    ) -> list[LayoutRegion]:
        """
        Predict reading order for regions.

        Args:
            regions: List of LayoutRegion objects
            image: Original image

        Returns:
            Regions with assigned reading order
        """
        if not regions:
            return regions

        if self._reading_order_model is None:
            # Fallback: sort by y-coordinate (top to bottom)
            logger.info("Using fallback reading order (top-to-bottom)")
            sorted_regions = sorted(regions, key=lambda r: (r.bbox.y_min, r.bbox.x_min))
            for i, region in enumerate(sorted_regions):
                region.reading_order = i
            return sorted_regions

        try:
            # Use LayoutLM for reading order prediction
            # This is a simplified implementation
            # Full implementation would require proper tokenization of layout

            # For now, use a heuristic based on position
            # LayoutLM would provide better multi-column handling
            sorted_regions = sorted(regions, key=lambda r: (
                r.bbox.y_min // 50 * 50,  # Group by rows (50px buckets)
                r.bbox.x_min
            ))

            for i, region in enumerate(sorted_regions):
                region.reading_order = i

            return sorted_regions

        except Exception as e:
            logger.error(f"Reading order prediction failed: {e}")
            # Fallback to simple sorting
            sorted_regions = sorted(regions, key=lambda r: (r.bbox.y_min, r.bbox.x_min))
            for i, region in enumerate(sorted_regions):
                region.reading_order = i
            return sorted_regions

    def _detect_table_grid(self, region: LayoutRegion, ocr_regions: list[OCRRegion]) -> list[LayoutRegion]:
        """
        Detect table grid structure within a table region.

        Args:
            region: Table LayoutRegion
            ocr_regions: OCR regions within the table

        Returns:
            Sub-regions for table cells
        """
        # Simple grid detection based on OCR region positions
        if not ocr_regions:
            return [region]

        # Find unique row and column positions
        y_positions = sorted(set(r.bbox.y_min for r in ocr_regions))
        x_positions = sorted(set(r.bbox.x_min for r in ocr_regions))

        # Group into rows (within 10px tolerance)
        rows = []
        current_row = []
        last_y = None

        for ocr in sorted(ocr_regions, key=lambda r: r.bbox.y_min):
            if last_y is None or abs(ocr.bbox.y_min - last_y) > 10:
                if current_row:
                    rows.append(current_row)
                current_row = [ocr]
            else:
                current_row.append(ocr)
            last_y = ocr.bbox.y_min

        if current_row:
            rows.append(current_row)

        # Update region metadata with grid info
        region.metadata["table_rows"] = len(rows)
        region.metadata["table_cells"] = len(ocr_regions)

        return [region]

    def detect(
        self,
        image_source: Union[str, Path, Image.Image, np.ndarray],
        ocr_regions: Optional[list[OCRRegion]] = None,
    ) -> DocumentLayout:
        """
        Detect layout and assign reading order.

        Args:
            image_source: Image file path, PIL Image, or numpy array
            ocr_regions: Optional pre-extracted OCR regions

        Returns:
            DocumentLayout with detected regions
        """
        self._initialize()

        # Load image
        if isinstance(image_source, (str, Path)):
            image = Image.open(image_source).convert("RGB")
            image_path = str(image_source)
        elif isinstance(image_source, np.ndarray):
            image = Image.fromarray(image_source)
            image_path = "<numpy_array>"
        elif isinstance(image_source, Image.Image):
            image = image_source.convert("RGB")
            image_path = "<pil_image>"
        else:
            raise ValueError(f"Unsupported image type: {type(image_source)}")

        image_width, image_height = image.size

        # Detect layout regions
        layout_regions_raw = self._detect_layout_with_paddle(image)

        # Create LayoutRegion objects
        layout_regions = []
        for i, raw in enumerate(layout_regions_raw):
            x_min, y_min, x_max, y_max = raw["bbox"]
            area = (x_max - x_min) * (y_max - y_min)

            if area < self.min_region_area:
                continue

            region_type_str = raw["type"].lower()
            region_type = LAYOUT_TYPE_MAP.get(region_type_str, RegionType.UNKNOWN)

            # Check for specific types
            if "table" in region_type_str:
                region_type = RegionType.TABLE
            elif "stamp" in region_type_str or "seal" in region_type_str:
                region_type = RegionType.STAMP
            elif "handwriting" in region_type_str:
                region_type = RegionType.HANDWRITING

            layout_region = LayoutRegion(
                id=f"layout_{uuid.uuid4().hex[:8]}",
                region_type=region_type,
                bbox=BoundingBox(
                    x_min=x_min,
                    y_min=y_min,
                    x_max=x_max,
                    y_max=y_max,
                ),
                reading_order=i,  # Will be reassigned
                confidence=raw["score"],
            )
            layout_regions.append(layout_region)

        # If no layout detected, create a single region for the whole image
        if not layout_regions:
            layout_regions = [
                LayoutRegion(
                    id=f"layout_{uuid.uuid4().hex[:8]}",
                    region_type=RegionType.TEXT,
                    bbox=BoundingBox(
                        x_min=0,
                        y_min=0,
                        x_max=image_width,
                        y_max=image_height,
                    ),
                    reading_order=0,
                    confidence=1.0,
                )
            ]

        # Assign OCR regions to layout regions
        if ocr_regions:
            for ocr in ocr_regions:
                for layout in layout_regions:
                    if self._region_contains(layout.bbox, ocr.bbox):
                        layout.add_ocr_region(ocr)
                        break

        # Predict reading order
        layout_regions = self._predict_reading_order(layout_regions, image)

        # Detect table grids
        for layout in layout_regions:
            if layout.region_type == RegionType.TABLE and layout.ocr_regions:
                self._detect_table_grid(layout, layout.ocr_regions)

        # Determine layout type
        layout_type = self._determine_layout_type(layout_regions, image_width)

        # Create DocumentLayout
        doc_layout = DocumentLayout(
            document_path=image_path,
            page_number=1,
            image_width=image_width,
            image_height=image_height,
            layout_type=layout_type,
            regions=layout_regions,
        )

        # Detect language
        doc_layout.language = self._detect_document_language(ocr_regions or [])

        logger.info(
            f"Detected {len(layout_regions)} layout regions, "
            f"type: {layout_type.value}, language: {doc_layout.language}"
        )

        return doc_layout

    def _region_contains(self, outer: BoundingBox, inner: BoundingBox) -> bool:
        """Check if outer region contains inner region (with tolerance)."""
        tolerance = 10
        return (
            outer.x_min - tolerance <= inner.x_min <= outer.x_max + tolerance
            and outer.y_min - tolerance <= inner.y_min <= outer.y_max + tolerance
        )

    def _determine_layout_type(
        self, regions: list[LayoutRegion], image_width: int
    ) -> LayoutType:
        """Determine overall layout type."""
        if not regions:
            return LayoutType.SINGLE_COLUMN

        # Check for table grid
        table_regions = [r for r in regions if r.region_type == RegionType.TABLE]
        if len(table_regions) > len(regions) / 2:
            return LayoutType.TABLE_GRID

        # Check for multi-column
        x_centers = [r.bbox.center[0] for r in regions]
        if x_centers:
            left_regions = [r for r in regions if r.bbox.center[0] < image_width / 3]
            right_regions = [r for r in regions if r.bbox.center[0] > 2 * image_width / 3]

            if left_regions and right_regions:
                # Check for vertical overlap
                for left in left_regions:
                    for right in right_regions:
                        if self._regions_overlap_vertically(left, right):
                            return LayoutType.MULTI_COLUMN

        return LayoutType.SINGLE_COLUMN

    def _regions_overlap_vertically(self, r1: LayoutRegion, r2: LayoutRegion) -> bool:
        """Check if two regions overlap vertically."""
        return not (
            r1.bbox.y_max < r2.bbox.y_min or r2.bbox.y_max < r1.bbox.y_min
        )

    def _detect_document_language(self, ocr_regions: list[OCRRegion]) -> str:
        """Detect primary language of document."""
        if not ocr_regions:
            return "unknown"

        lang_counts = {}
        for region in ocr_regions:
            lang = region.language
            lang_counts[lang] = lang_counts.get(lang, 0) + 1

        if not lang_counts:
            return "unknown"

        primary_lang = max(lang_counts, key=lang_counts.get)

        # Check for mixed
        total = sum(lang_counts.values())
        if lang_counts.get("hi", 0) > 0 and lang_counts.get("en", 0) > 0:
            hi_ratio = lang_counts["hi"] / total
            en_ratio = lang_counts["en"] / total
            if hi_ratio > 0.2 and en_ratio > 0.2:
                return "mixed"

        return primary_lang
