"""OCR Engine with Hindi and English support."""

import base64
import logging
from io import BytesIO
from pathlib import Path
from typing import Optional, Union
import uuid

import numpy as np
from PIL import Image

from .dataclasses import OCRRegion, BoundingBox, RegionType

logger = logging.getLogger(__name__)


class OCREngine:
    """
    OCR Engine supporting Hindi and English text extraction.

    Uses PaddleOCR as primary engine with Tesseract fallback.
    """

    def __init__(
        self,
        languages: tuple = ("hi", "en"),
        use_gpu: bool = False,
        show_log: bool = False,
        det_db_thresh: float = 0.3,
        det_db_box_thresh: float = 0.5,
    ):
        """
        Initialize OCR engine.

        Args:
            languages: Tuple of language codes (e.g., ("hi", "en"))
            use_gpu: Whether to use GPU acceleration
            show_log: Whether to show PaddleOCR logs
            det_db_thresh: Detection threshold
            det_db_box_thresh: Box detection threshold
        """
        self.languages = languages
        self.use_gpu = use_gpu
        self._ocr = None
        self._det_db_thresh = det_db_thresh
        self._det_db_box_thresh = det_db_box_thresh
        self._show_log = show_log
        self._initialized = False

    def _initialize(self):
        """Lazy initialization of PaddleOCR."""
        if self._initialized:
            return

        try:
            import os
            os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")
            from paddleocr import PaddleOCR

            # PaddleOCR accepts a single language code. For mixed Hindi/English
            # documents, use "hi" — the Hindi model handles Latin script too.
            if "hi" in self.languages:
                ocr_lang = "hi"
            elif "en" in self.languages:
                ocr_lang = "en"
            else:
                ocr_lang = self.languages[0]

            logger.info(f"Initializing PaddleOCR with language: {ocr_lang}")
            # PaddleOCR 3.x API — old params like use_gpu, show_log,
            # use_angle_cls, page_num are removed.
            self._ocr = PaddleOCR(
                lang=ocr_lang,
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False,
                text_det_thresh=self._det_db_thresh,
                text_det_box_thresh=self._det_db_box_thresh,
            )
            self._initialized = True
            logger.info("PaddleOCR initialized successfully")

        except Exception as e:
            logger.warning(f"PaddleOCR not available ({e}), falling back to Tesseract")
            self._ocr = None
            self._initialized = True

    def _detect_language(self, text: str) -> str:
        """
        Detect language of extracted text.

        Args:
            text: Extracted text

        Returns:
            Language code ('hi' for Hindi, 'en' for English, 'mixed' for both)
        """
        # Hindi Unicode range
        hindi_chars = set(
            chr(i)
            for i in range(0x0900, 0x097F)  # Devanagari
        )

        if not text.strip():
            return "unknown"

        text_chars = set(text)
        hindi_count = len(text_chars & hindi_chars)
        total_alpha = sum(1 for c in text if c.isalpha())

        if total_alpha == 0:
            return "unknown"

        hindi_ratio = hindi_count / total_alpha if total_alpha > 0 else 0

        if hindi_ratio > 0.3:
            return "hi"
        elif hindi_ratio > 0.1:
            return "mixed"
        else:
            return "en"

    def _pil_to_cv2(self, pil_image: Image.Image) -> np.ndarray:
        """Convert PIL image to OpenCV format."""
        import cv2
        img_array = np.array(pil_image)
        # PIL is RGB, OpenCV expects BGR
        if len(img_array.shape) == 3 and img_array.shape[2] == 3:
            img_array = img_array[:, :, ::-1]
        return img_array

    def _process_paddle_result(self, result, image_width: int, image_height: int) -> list[OCRRegion]:
        """
        Process PaddleOCR result into OCRRegion objects.

        Args:
            result: PaddleOCR result tuple (boxes, texts, scores)
            image_width: Original image width
            image_height: Original image height

        Returns:
            List of OCRRegion objects
        """
        regions = []

        if result is None or len(result) == 0:
            return regions

        # PaddleOCR returns: (boxes, texts, scores)
        boxes = result[0] if len(result) > 0 else []
        texts = result[1] if len(result) > 1 else []
        scores = result[2] if len(result) > 2 else []

        for i, (box, text, score) in enumerate(zip(boxes, texts, scores)):
            if text is None or text.strip() == "":
                continue

            # Normalize coordinates if needed
            box = np.array(box)
            if box.max() > 1.0:
                # Absolute coordinates
                x_min = float(np.min(box[:, 0]))
                x_max = float(np.max(box[:, 0]))
                y_min = float(np.min(box[:, 1]))
                y_max = float(np.max(box[:, 1]))
            else:
                # Normalized coordinates
                x_min = float(np.min(box[:, 0]) * image_width)
                x_max = float(np.max(box[:, 0]) * image_width)
                y_min = float(np.min(box[:, 1]) * image_height)
                y_max = float(np.max(box[:, 1]) * image_height)

            # Ensure coordinates are within bounds
            x_min = max(0, min(x_min, image_width))
            x_max = max(0, min(x_max, image_width))
            y_min = max(0, min(y_min, image_height))
            y_max = max(0, min(y_max, image_height))

            language = self._detect_language(text)

            region = OCRRegion(
                id=f"ocr_{uuid.uuid4().hex[:8]}",
                text=text.strip(),
                bbox=BoundingBox(
                    x_min=x_min,
                    y_min=y_min,
                    x_max=x_max,
                    y_max=y_max,
                ),
                confidence=float(score),
                language=language,
                region_type=RegionType.TEXT,
            )
            regions.append(region)

        return regions

    def _process_tesseract_result(
        self, image: Image.Image, image_width: int, image_height: int
    ) -> list[OCRRegion]:
        """
        Fallback Tesseract OCR processing.

        Args:
            image: PIL Image
            image_width: Image width
            image_height: Image height

        Returns:
            List of OCRRegion objects
        """
        try:
            import pytesseract
            from pytesseract import Output

            logger.info("Using Tesseract OCR fallback")

            # Get detailed output with bounding boxes
            data = pytesseract.image_to_data(
                image,
                output_type=Output.DICT,
                lang="hin+eng",  # Tesseract language codes
            )

            regions = []
            n_boxes = len(data["level"])

            for i in range(n_boxes):
                text = data["text"][i].strip()
                if not text:
                    continue

                x = data["left"][i]
                y = data["top"][i]
                w = data["width"][i]
                h = data["height"][i]
                conf = data["conf"][i]

                # Skip low confidence results
                if conf < 30:
                    continue

                language = self._detect_language(text)

                region = OCRRegion(
                    id=f"ocr_{uuid.uuid4().hex[:8]}",
                    text=text,
                    bbox=BoundingBox(
                        x_min=float(x),
                        y_min=float(y),
                        x_max=float(x + w),
                        y_max=float(y + h),
                    ),
                    confidence=conf / 100.0,
                    language=language,
                    region_type=RegionType.TEXT,
                )
                regions.append(region)

            return regions

        except Exception as e:
            logger.error(f"Tesseract OCR failed: {e}")
            return []

    def extract(
        self,
        image_source: Union[str, Path, Image.Image, np.ndarray],
        force_tesseract: bool = False,
    ) -> list[OCRRegion]:
        """
        Extract text from an image.

        Args:
            image_source: Image file path, PIL Image, or numpy array
            force_tesseract: Force use of Tesseract instead of PaddleOCR

        Returns:
            List of OCRRegion objects
        """
        self._initialize()

        # Load image
        if isinstance(image_source, (str, Path)):
            image = Image.open(image_source).convert("RGB")
        elif isinstance(image_source, np.ndarray):
            image = Image.fromarray(image_source)
        elif isinstance(image_source, Image.Image):
            image = image_source.convert("RGB")
        else:
            raise ValueError(f"Unsupported image type: {type(image_source)}")

        image_width, image_height = image.size

        # Try PaddleOCR first (unless forced to use Tesseract)
        if not force_tesseract and self._ocr is not None:
            try:
                import cv2
                cv2_image = self._pil_to_cv2(image)
                result = self._ocr.ocr(cv2_image, cls=True)

                # Flatten result if nested
                if result and len(result) == 1 and isinstance(result[0], list):
                    result = result[0]

                regions = self._process_paddle_result(result, image_width, image_height)

                if regions:
                    logger.info(f"Extracted {len(regions)} text regions with PaddleOCR")
                    return regions

            except Exception as e:
                logger.warning(f"PaddleOCR failed: {e}, falling back to Tesseract")

        # Fallback to Tesseract
        regions = self._process_tesseract_result(image, image_width, image_height)
        logger.info(f"Extracted {len(regions)} text regions with Tesseract")
        return regions

    def extract_from_base64(self, base64_string: str) -> list[OCRRegion]:
        """
        Extract text from a base64-encoded image.

        Args:
            base64_string: Base64-encoded image string

        Returns:
            List of OCRRegion objects
        """
        # Remove data URI prefix if present
        if "," in base64_string:
            base64_string = base64_string.split(",", 1)[1]

        image_data = base64.b64decode(base64_string)
        image = Image.open(BytesIO(image_data))
        return self.extract(image)

    def get_languages(self) -> tuple:
        """Get configured languages."""
        return self.languages

    def is_available(self) -> bool:
        """Check if OCR engine is available."""
        self._initialize()
        return self._ocr is not None
