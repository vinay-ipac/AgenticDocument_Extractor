"""Layout Detection with Reading Order prediction."""

import logging
import os
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

# Disable PaddlePaddle PIR to avoid oneDNN incompatibility on Windows.
os.environ.setdefault("FLAGS_enable_pir_api", "0")
os.environ.setdefault("FLAGS_enable_pir_in_executor", "0")
os.environ.setdefault("FLAGS_enable_pir_with_pt_in_dy2st", "0")
os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")


# Mapping from PaddleX layout detection labels to our RegionType
LAYOUT_LABEL_MAP = {
    "text": RegionType.TEXT,
    "title": RegionType.HEADER,
    "table": RegionType.TABLE,
    "figure": RegionType.IMAGE,
    "image": RegionType.IMAGE,
    "figure_caption": RegionType.TEXT,
    "table_caption": RegionType.TEXT,
    "formula": RegionType.TEXT,
    "equation": RegionType.TEXT,
    "stamp": RegionType.STAMP,
    "seal": RegionType.STAMP,
    "handwriting": RegionType.HANDWRITING,
    "form": RegionType.FORM,
    "header": RegionType.HEADER,
    "footer": RegionType.FOOTER,
    "reference": RegionType.TEXT,
    "abstract": RegionType.TEXT,
    "content": RegionType.TEXT,
    "list": RegionType.TEXT,
    "doc_title": RegionType.HEADER,
    "paragraph_title": RegionType.HEADER,
    "paragraph": RegionType.TEXT,
    "catalog": RegionType.TEXT,
    "chart": RegionType.CHART,
    "number": RegionType.TEXT,
    "algorithm": RegionType.TEXT,
    "code_block": RegionType.TEXT,
}


class LayoutDetector:
    """
    Layout detection with reading order prediction.

    Uses PaddleX layout analysis model (PP-DocLayoutV3) for layout detection
    and spatial heuristics for reading order.
    """

    def __init__(
        self,
        layout_model_name: str = "PP-DocLayoutV3",
        reading_order_model_name: str = "microsoft/layoutlmv3-base",
        use_gpu: bool = False,
        min_region_area: float = 500.0,
        layout_threshold: float = 0.3,
    ):
        """
        Initialize layout detector.

        Args:
            layout_model_name: PaddleX layout model name
            reading_order_model_name: HuggingFace model for reading order
            use_gpu: Whether to use GPU
            min_region_area: Minimum area for a region to be considered
            layout_threshold: Confidence threshold for layout detection
        """
        self.layout_model_name = layout_model_name
        self.reading_order_model_name = reading_order_model_name
        self.use_gpu = use_gpu
        self.min_region_area = min_region_area
        self.layout_threshold = layout_threshold
        self._layout_model = None
        self._reading_order_model = None
        self._initialized = False

    def _initialize(self):
        """Lazy initialization of models."""
        if self._initialized:
            return

        # Initialize PaddleX layout analysis model
        try:
            import paddlex

            logger.info(f"Initializing PaddleX layout model: {self.layout_model_name}")
            self._layout_model = paddlex.create_model(self.layout_model_name)
            logger.info("PaddleX layout model initialized")

        except Exception as e:
            logger.warning(f"Failed to initialize PaddleX layout model: {e}")
            self._layout_model = None

        # Try to initialize LayoutLM for reading order (optional)
        try:
            from transformers import AutoModel, AutoTokenizer

            logger.info(f"Loading reading order model: {self.reading_order_model_name}")
            self._reading_order_tokenizer = AutoTokenizer.from_pretrained(
                self.reading_order_model_name,
                trust_remote_code=True,
            )
            self._reading_order_model = AutoModel.from_pretrained(
                self.reading_order_model_name,
                trust_remote_code=True,
            )
            logger.info("Reading order model initialized")
        except Exception as e:
            logger.info(f"Reading order model not available ({e}), using spatial heuristics")
            self._reading_order_model = None

        self._initialized = True

    def _detect_layout_with_paddlex(
        self, image: Image.Image, save_visualization: Optional[Union[str, Path]] = None
    ) -> list[dict]:
        """
        Detect layout using PaddleX layout analysis model.

        Args:
            image: PIL Image
            save_visualization: Optional path to save the PaddleX visualization

        Returns:
            List of layout regions with type, bbox, and score
        """
        if self._layout_model is None:
            return []

        try:
            cv2_image = np.array(image)
            if len(cv2_image.shape) == 3 and cv2_image.shape[2] == 3:
                cv2_image = cv2_image[:, :, ::-1]  # RGB to BGR

            # PaddleX model.predict() returns a generator of LayoutAnalysisResult
            raw_results = list(self._layout_model.predict(cv2_image))

            # Save PaddleX visualization if requested
            if save_visualization:
                self._save_layout_image(raw_results, save_visualization)

            regions = []
            for result in raw_results:
                # LayoutAnalysisResult is dict-like with "boxes" key
                boxes = result.get("boxes", []) if hasattr(result, 'get') else result["boxes"]

                for box_info in boxes:
                    label = box_info.get("label", "unknown").lower()
                    coordinate = box_info.get("coordinate", [])
                    score = box_info.get("score", 0.0)

                    if score < self.layout_threshold:
                        continue

                    if len(coordinate) >= 4:
                        x_min, y_min, x_max, y_max = coordinate[:4]
                    else:
                        continue

                    # Also check for 'order' key from the layout model
                    reading_order = box_info.get("order", None)

                    regions.append({
                        "type": label,
                        "bbox": (float(x_min), float(y_min), float(x_max), float(y_max)),
                        "score": float(score),
                        "reading_order": reading_order,
                    })

            logger.info(f"PaddleX layout detection found {len(regions)} regions")
            return regions

        except Exception as e:
            logger.error(f"PaddleX layout detection failed: {e}")
            return []

    def _save_layout_image(self, results: list, output_path: Union[str, Path]):
        """
        Save the layout detection visualization from PaddleX.

        Args:
            results: PaddleX layout analysis results
            output_path: Path to save the visualization
        """
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            for result in results:
                if hasattr(result, 'img'):
                    img_dict = result.img
                    # img_dict typically has "res" key with the visualization
                    for key, vis_img in img_dict.items():
                        if isinstance(vis_img, Image.Image):
                            vis_img.save(output_path)
                            logger.info(f"Saved layout detection image to {output_path}")
                            return
                        elif isinstance(vis_img, np.ndarray):
                            pil_img = Image.fromarray(
                                vis_img[:, :, ::-1] if len(vis_img.shape) == 3 and vis_img.shape[-1] == 3 else vis_img
                            )
                            pil_img.save(output_path)
                            logger.info(f"Saved layout detection image to {output_path}")
                            return
        except Exception as e:
            logger.warning(f"Failed to save layout detection image: {e}")

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

        # Check if any regions already have reading order from layout model
        has_model_order = any(
            r.metadata.get("model_reading_order") is not None for r in regions
        )
        if has_model_order:
            # Use model-provided order
            sorted_regions = sorted(
                regions,
                key=lambda r: (r.metadata.get("model_reading_order", 999), r.bbox.y_min),
            )
            for i, region in enumerate(sorted_regions):
                region.reading_order = i
            return sorted_regions

        if self._reading_order_model is not None:
            try:
                # Use LayoutLM-based reading order
                sorted_regions = sorted(regions, key=lambda r: (
                    r.bbox.y_min // 50 * 50,  # Group by rows (50px buckets)
                    r.bbox.x_min
                ))
                for i, region in enumerate(sorted_regions):
                    region.reading_order = i
                return sorted_regions
            except Exception as e:
                logger.error(f"Reading order prediction failed: {e}")

        # Fallback: sort by y-coordinate (top to bottom), then x (left to right)
        logger.info("Using spatial heuristic reading order (top-to-bottom, left-to-right)")
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
        if not ocr_regions:
            return [region]

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

        region.metadata["table_rows"] = len(rows)
        region.metadata["table_cells"] = len(ocr_regions)

        return [region]

    def detect(
        self,
        image_source: Union[str, Path, Image.Image, np.ndarray],
        ocr_regions: Optional[list[OCRRegion]] = None,
        save_visualization: Optional[Union[str, Path]] = None,
    ) -> DocumentLayout:
        """
        Detect layout and assign reading order.

        Args:
            image_source: Image file path, PIL Image, or numpy array
            ocr_regions: Optional pre-extracted OCR regions
            save_visualization: Optional path to save layout visualization image

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

        # Detect layout regions using PaddleX (also saves visualization if requested)
        layout_regions_raw = self._detect_layout_with_paddlex(
            image, save_visualization=save_visualization
        )

        # Create LayoutRegion objects
        layout_regions = []
        for i, raw in enumerate(layout_regions_raw):
            x_min, y_min, x_max, y_max = raw["bbox"]
            area = (x_max - x_min) * (y_max - y_min)

            if area < self.min_region_area:
                continue

            region_type_str = raw["type"].lower()
            region_type = LAYOUT_LABEL_MAP.get(region_type_str, RegionType.UNKNOWN)

            # Check for specific types
            if "table" in region_type_str:
                region_type = RegionType.TABLE
            elif "stamp" in region_type_str or "seal" in region_type_str:
                region_type = RegionType.STAMP
            elif "handwriting" in region_type_str:
                region_type = RegionType.HANDWRITING
            elif "chart" in region_type_str:
                region_type = RegionType.CHART

            metadata = {}
            if raw.get("reading_order") is not None:
                metadata["model_reading_order"] = raw["reading_order"]

            layout_region = LayoutRegion(
                id=f"layout_{uuid.uuid4().hex[:8]}",
                region_type=region_type,
                bbox=BoundingBox(
                    x_min=x_min,
                    y_min=y_min,
                    x_max=x_max,
                    y_max=y_max,
                ),
                reading_order=i,
                confidence=raw["score"],
                metadata=metadata,
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
