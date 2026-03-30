"""Document loading and processing helpers."""

import csv
import json
import logging
from pathlib import Path
from typing import Optional, Union

from PIL import Image

logger = logging.getLogger(__name__)


def image_to_pil(source: Union[str, Path, Image.Image, bytes]) -> Image.Image:
    """
    Convert various image sources to PIL Image.

    Args:
        source: File path, PIL Image, bytes, or numpy array

    Returns:
        PIL Image in RGB mode
    """
    if isinstance(source, Image.Image):
        return source.convert("RGB")
    elif isinstance(source, (str, Path)):
        return Image.open(source).convert("RGB")
    elif isinstance(source, bytes):
        from io import BytesIO
        return Image.open(BytesIO(source)).convert("RGB")
    elif hasattr(source, "numpy"):
        # Handle numpy arrays
        import numpy as np
        arr = source.numpy() if hasattr(source, "numpy") else source
        if len(arr.shape) == 3 and arr.shape[2] == 3:
            # Assume BGR (OpenCV)
            arr = arr[:, :, ::-1]
        return Image.fromarray(arr).convert("RGB")
    else:
        raise ValueError(f"Unsupported image source type: {type(source)}")


def pdf_to_images(
    pdf_path: Union[str, Path],
    dpi: int = 150,
    pages: Optional[list[int]] = None,
) -> list[Image.Image]:
    """
    Convert PDF pages to images.

    Args:
        pdf_path: Path to PDF file
        dpi: Output image DPI
        pages: List of page numbers (0-indexed), None for all

    Returns:
        List of PIL Images
    """
    try:
        import fitz  # PyMuPDF

        pdf_path = Path(pdf_path)
        doc = fitz.open(pdf_path)

        # Determine which pages to process
        if pages is None:
            page_numbers = list(range(len(doc)))
        else:
            page_numbers = [p for p in pages if 0 <= p < len(doc)]

        images = []
        for page_num in page_numbers:
            page = doc[page_num]
            # Render page to image
            mat = fitz.Matrix(dpi / 72, dpi / 72)
            pix = page.get_pixmap(matrix=mat)

            # Convert to PIL Image
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            images.append(img)

        doc.close()

        logger.info(f"Converted {len(images)} pages from {pdf_path.name}")
        return images

    except ImportError:
        logger.error("PyMuPDF not installed. Install with: pip install PyMuPDF")
        raise
    except Exception as e:
        logger.error(f"Failed to convert PDF: {e}")
        raise


def docx_to_images(
    docx_path: Union[str, Path],
    dpi: int = 150,
) -> list[Image.Image]:
    """
    Convert DOCX document to images.

    Note: This converts each paragraph/section to an image.
    For complex layouts, consider saving as PDF first.

    Args:
        docx_path: Path to DOCX file
        dpi: Output image DPI

    Returns:
        List of PIL Images
    """
    try:
        from docx import Document
        from docx2image import docx_to_image  # Optional dependency

        docx_path = Path(docx_path)
        doc = Document(docx_path)

        images = []

        # Try docx2image first
        try:
            for i, para in enumerate(doc.paragraphs):
                if para.text.strip():
                    img = docx_to_image(docx_path, i)
                    if img:
                        images.append(img)
        except Exception:
            # Fallback: render whole document
            logger.info("Using fallback DOCX rendering")
            import fitz  # PyMuPDF can open DOCX

            doc = fitz.open(docx_path)
            for page_num in range(len(doc)):
                page = doc[page_num]
                mat = fitz.Matrix(dpi / 72, dpi / 72)
                pix = page.get_pixmap(matrix=mat)
                img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
                images.append(img)
            doc.close()

        logger.info(f"Converted {len(images)} sections from {docx_path.name}")
        return images

    except ImportError:
        logger.error("python-docx not installed. Install with: pip install python-docx")
        raise
    except Exception as e:
        logger.error(f"Failed to convert DOCX: {e}")
        raise


def load_document(
    document_path: Union[str, Path],
    dpi: int = 150,
    pages: Optional[list[int]] = None,
) -> list[Image.Image]:
    """
    Load a document (PDF, DOCX, or image) as images.

    Args:
        document_path: Path to document
        dpi: Output DPI for conversions
        pages: Specific pages for PDFs

    Returns:
        List of PIL Images
    """
    document_path = Path(document_path)

    if not document_path.exists():
        raise FileNotFoundError(f"Document not found: {document_path}")

    suffix = document_path.suffix.lower()

    if suffix in (".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".gif"):
        return [image_to_pil(document_path)]
    elif suffix == ".pdf":
        return pdf_to_images(document_path, dpi, pages)
    elif suffix == ".docx":
        return docx_to_images(document_path, dpi)
    else:
        # Try to open as image
        try:
            return [image_to_pil(document_path)]
        except Exception:
            raise ValueError(f"Unsupported document format: {suffix}")


def save_results_json(
    results: dict,
    output_path: Union[str, Path],
    indent: int = 2,
) -> Path:
    """
    Save results to JSON file.

    Args:
        results: Results dictionary
        output_path: Output file path
        indent: JSON indentation

    Returns:
        Output path
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=indent, ensure_ascii=False)

    logger.info(f"Saved results to {output_path}")
    return output_path


def save_results_csv(
    data: list[dict],
    output_path: Union[str, Path],
    fieldnames: Optional[list[str]] = None,
) -> Path:
    """
    Save extracted data to CSV file.

    Args:
        data: List of dictionaries (e.g., voter records)
        output_path: Output file path
        fieldnames: Column names (auto-detected if not provided)

    Returns:
        Output path
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not data:
        logger.warning("No data to save to CSV")
        output_path.touch()
        return output_path

    # Auto-detect fieldnames
    if fieldnames is None:
        fieldnames = list(data[0].keys())

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(data)

    logger.info(f"Saved {len(data)} records to {output_path}")
    return output_path


def extract_text_from_layout(layout) -> str:
    """
    Extract combined text from layout in reading order.

    Args:
        layout: DocumentLayout

    Returns:
        Combined text string
    """
    texts = []
    for region in sorted(layout.regions, key=lambda r: r.reading_order):
        if region.combined_text:
            texts.append(region.combined_text)
    return "\n\n".join(texts)


def count_regions_by_type(layout) -> dict:
    """
    Count regions by type.

    Args:
        layout: DocumentLayout

    Returns:
        Dictionary mapping region types to counts
    """
    from ..core.dataclasses import RegionType

    counts = {}
    for region in layout.regions:
        rt = region.region_type
        counts[rt] = counts.get(rt, 0) + 1
    return counts


def get_page_dimensions(images: list[Image.Image]) -> tuple:
    """
    Get consistent page dimensions from images.

    Args:
        images: List of PIL Images

    Returns:
        (width, height) tuple using max dimensions
    """
    if not images:
        return (0, 0)

    max_width = max(img.width for img in images)
    max_height = max(img.height for img in images)

    return (max_width, max_height)
