"""Visualization utilities for document layouts and extractions."""

import logging
from pathlib import Path
from typing import Optional, Union

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from ..core.dataclasses import (
    DocumentLayout,
    LayoutRegion,
    OCRRegion,
    BoundingBox,
    RegionType,
)

logger = logging.getLogger(__name__)

# Color map for different region types
REGION_COLORS = {
    RegionType.TEXT: "#3498db",  # Blue
    RegionType.TABLE: "#2ecc71",  # Green
    RegionType.IMAGE: "#9b59b6",  # Purple
    RegionType.CHART: "#e67e22",  # Orange
    RegionType.FORM: "#1abc9c",  # Teal
    RegionType.STAMP: "#e74c3c",  # Red
    RegionType.HANDWRITING: "#f39c12",  # Yellow/Orange
    RegionType.HEADER: "#34495e",  # Dark blue
    RegionType.FOOTER: "#95a5a6",  # Gray
    RegionType.UNKNOWN: "#7f8c8d",  # Light gray
}

# Font sizes
FONT_SIZE_TITLE = 14
FONT_SIZE_LABEL = 10
FONT_SIZE_TEXT = 8


def get_font(size: int = FONT_SIZE_LABEL) -> ImageFont.FreeTypeFont:
    """Get a font with specified size."""
    try:
        # Try common font paths
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/TTF/DejaVuSans.ttf",
            "C:\\Windows\\Fonts\\arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
        ]
        for path in font_paths:
            try:
                return ImageFont.truetype(path, size)
            except (OSError, IOError):
                continue
    except Exception:
        pass

    # Fall back to default
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except Exception:
        return ImageFont.load_default()


def draw_bounding_box(
    image: Image.Image,
    bbox: BoundingBox,
    color: str = "#3498db",
    label: Optional[str] = None,
    fill: bool = False,
    line_width: int = 2,
) -> Image.Image:
    """
    Draw a bounding box on an image.

    Args:
        image: PIL Image to draw on
        bbox: BoundingBox to draw
        color: Box color (hex or name)
        label: Optional label text
        fill: Whether to fill the box
        line_width: Width of box lines

    Returns:
        Image with bounding box drawn
    """
    draw = ImageDraw.Draw(image)

    # Convert coordinates to integers
    coords = (
        int(bbox.x_min),
        int(bbox.y_min),
        int(bbox.x_max),
        int(bbox.y_max),
    )

    # Draw filled rectangle if requested
    if fill:
        # Convert hex to RGBA with alpha
        if color.startswith("#"):
            fill_color = tuple(int(color[i:i+2], 16) for i in (1, 3, 5)) + (50,)
        else:
            fill_color = (52, 152, 219, 50)  # Default blue with alpha
        draw.rectangle(coords, fill=fill_color)

    # Draw box outline
    draw.rectangle(coords, outline=color, width=line_width)

    # Draw label
    if label:
        font = get_font(FONT_SIZE_LABEL)
        # Get text size
        bbox_text = draw.textbbox((0, 0), label, font=font)
        text_width = bbox_text[2] - bbox_text[0]
        text_height = bbox_text[3] - bbox_text[1]

        # Draw label background
        label_y = max(0, int(bbox.y_min) - text_height - 4)
        draw.rectangle(
            (
                int(bbox.x_min),
                label_y,
                int(bbox.x_min) + text_width + 6,
                label_y + text_height + 4,
            ),
            fill=color,
        )

        # Draw label text
        draw.text(
            (int(bbox.x_min) + 3, label_y + 2),
            label,
            fill="white",
            font=font,
        )

    return image


def draw_layout(
    layout: DocumentLayout,
    image: Optional[Image.Image] = None,
    image_path: Optional[str] = None,
    show_labels: bool = True,
    show_reading_order: bool = True,
    show_ocr: bool = False,
    output_path: Optional[Union[str, Path]] = None,
) -> Image.Image:
    """
    Draw layout visualization.

    Args:
        layout: DocumentLayout to visualize
        image: PIL Image background (optional)
        image_path: Path to image if not provided
        show_labels: Show region type labels
        show_reading_order: Show reading order numbers
        show_ocr: Show individual OCR regions
        output_path: Save result to this path

    Returns:
        Visualization image
    """
    # Load background image
    if image is None:
        if image_path:
            image = Image.open(image_path).convert("RGB")
        else:
            # Create blank canvas
            image = Image.new(
                "RGB",
                (layout.image_width, layout.image_height),
                color="white",
            )

    # Make a copy to draw on
    vis_image = image.copy()
    draw = ImageDraw.Draw(vis_image)

    # Draw each layout region
    for region in sorted(layout.regions, key=lambda r: r.reading_order):
        color = REGION_COLORS.get(region.region_type, "#7f8c8d")

        # Draw region box
        draw_bounding_box(
            vis_image,
            region.bbox,
            color=color,
            fill=True,
            line_width=2,
        )

        # Add label
        if show_labels:
            label = f"{region.region_type.value}"
            if show_reading_order:
                label = f"#{region.reading_order} {label}"

            font = get_font(FONT_SIZE_LABEL)
            bbox_text = draw.textbbox((0, 0), label, font=font)
            text_width = bbox_text[2] - bbox_text[0]
            text_height = bbox_text[3] - bbox_text[1]

            label_y = max(0, int(region.bbox.y_min) - text_height - 4)
            draw.rectangle(
                (
                    int(region.bbox.x_min),
                    label_y,
                    int(region.bbox.x_min) + text_width + 6,
                    label_y + text_height + 4,
                ),
                fill=color,
            )
            draw.text(
                (int(region.bbox.x_min) + 3, label_y + 2),
                label,
                fill="white",
                font=font,
            )

        # Draw OCR regions if requested
        if show_ocr and region.ocr_regions:
            for ocr in region.ocr_regions:
                draw_bounding_box(
                    vis_image,
                    ocr.bbox,
                    color="#f1c40f",  # Yellow for OCR
                    label=None,
                    line_width=1,
                )

    # Save if path provided
    if output_path:
        vis_image.save(output_path)
        logger.info(f"Saved layout visualization to {output_path}")

    return vis_image


def draw_bounding_boxes(
    image: Image.Image,
    regions: list[Union[LayoutRegion, OCRRegion]],
    color_map: Optional[dict] = None,
    show_text: bool = True,
    max_text_length: int = 50,
) -> Image.Image:
    """
    Draw bounding boxes for a list of regions.

    Args:
        image: PIL Image
        regions: List of regions with bbox attribute
        color_map: Custom color mapping
        show_text: Show region text content
        max_text_length: Maximum text length to display

    Returns:
        Image with bounding boxes
    """
    if color_map is None:
        color_map = REGION_COLORS

    vis_image = image.copy()
    draw = ImageDraw.Draw(vis_image)

    for i, region in enumerate(regions):
        # Get color
        if hasattr(region, "region_type"):
            color = color_map.get(region.region_type, "#3498db")
        else:
            color = "#3498db"  # Default blue

        # Draw box
        draw_bounding_box(
            vis_image,
            region.bbox,
            color=color,
            label=f"#{i}" if show_text else None,
            fill=True,
        )

        # Show text content
        if show_text:
            text = getattr(region, "text", "") or getattr(region, "combined_text", "")
            if text:
                # Truncate if too long
                if len(text) > max_text_length:
                    text = text[:max_text_length] + "..."

                # Replace newlines
                text = text.replace("\n", " ")

                font = get_font(FONT_SIZE_TEXT)
                text_y = int(region.bbox.y_max) + 2
                draw.text(
                    (int(region.bbox.x_min), text_y),
                    text,
                    fill="black",
                    font=font,
                )

    return vis_image


def create_comparison_view(
    original_image: Image.Image,
    layout: DocumentLayout,
    output_path: Optional[Union[str, Path]] = None,
) -> Image.Image:
    """
    Create side-by-side comparison of original and layout visualization.

    Args:
        original_image: Original document image
        layout: DocumentLayout
        output_path: Optional save path

    Returns:
        Comparison image
    """
    # Create visualization
    vis_image = draw_layout(layout, image=original_image, show_labels=True)

    # Ensure same size
    if vis_image.size != original_image.size:
        vis_image = vis_image.resize(original_image.size, Image.Resampling.LANCZOS)

    # Create side-by-side
    total_width = original_image.width * 2
    total_height = max(original_image.height, vis_image.height)

    comparison = Image.new("RGB", (total_width, total_height), color="white")
    comparison.paste(original_image, (0, 0))
    comparison.paste(vis_image, (original_image.width, 0))

    # Add labels
    draw = ImageDraw.Draw(comparison)
    font = get_font(FONT_SIZE_TITLE)

    draw.text((10, 10), "Original", fill="black", font=font)
    draw.text((original_image.width + 10, 10), "Layout Detected", fill="black", font=font)

    # Save if requested
    if output_path:
        comparison.save(output_path)
        logger.info(f"Saved comparison view to {output_path}")

    return comparison


def create_extraction_visualization(
    image: Image.Image,
    extracted_data: dict,
    region_mappings: Optional[dict] = None,
    output_path: Optional[Union[str, Path]] = None,
) -> Image.Image:
    """
    Create visualization showing extracted fields.

    Args:
        image: Document image
        extracted_data: Extracted data dictionary
        region_mappings: Mapping of fields to region IDs
        output_path: Optional save path

    Returns:
        Visualization image
    """
    vis_image = image.copy()
    draw = ImageDraw.Draw(vis_image)

    # Draw extraction highlights
    if region_mappings:
        for field_name, region_id in region_mappings.items():
            # Would need to look up region by ID
            # For now, just show the field name
            pass

    # Add extraction summary overlay
    summary_lines = ["Extracted Fields:"]
    for key, value in extracted_data.items():
        if key not in ("confidence", "notes", "error"):
            if isinstance(value, str):
                summary_lines.append(f"  {key}: {value[:40]}...")
            elif isinstance(value, list):
                summary_lines.append(f"  {key}: {len(value)} items")

    # Draw summary box
    font = get_font(FONT_SIZE_LABEL)
    line_height = 16
    box_height = len(summary_lines) * line_height + 20
    box_width = 300

    draw.rectangle(
        (10, image.height - box_height - 10, 10 + box_width, image.height - 10),
        fill="rgba(255, 255, 255, 200)",
        outline="black",
    )

    for i, line in enumerate(summary_lines):
        draw.text(
            (20, image.height - box_height + 5 + i * line_height),
            line,
            fill="black",
            font=font,
        )

    if output_path:
        vis_image.save(output_path)

    return vis_image


def generate_html_report(
    layout: DocumentLayout,
    extracted_data: dict,
    output_path: Union[str, Path],
    image_base64: Optional[str] = None,
) -> str:
    """
    Generate an HTML report of extraction results.

    Args:
        layout: DocumentLayout
        extracted_data: Extracted data
        output_path: Output HTML file path
        image_base64: Optional base64 image

    Returns:
        HTML content
    """
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Document Extraction Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
        .field {{ margin: 10px 0; }}
        .field-label {{ font-weight: bold; color: #333; }}
        .field-value {{ color: #666; margin-left: 10px; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
        .confidence {{ color: #888; font-size: 0.9em; }}
    </style>
</head>
<body>
    <h1>Document Extraction Report</h1>

    <div class="section">
        <h2>Document Info</h2>
        <p>Type: {layout.layout_type.value}</p>
        <p>Language: {layout.language}</p>
        <p>Regions: {len(layout.regions)}</p>
    </div>
"""

    # Add image if provided
    if image_base64:
        html += f"""
    <div class="section">
        <h2>Document Image</h2>
        <img src="data:image/png;base64,{image_base64}" style="max-width: 100%; height: auto;" />
    </div>
"""

    # Add extracted data
    html += """
    <div class="section">
        <h2>Extracted Data</h2>
"""

    for key, value in extracted_data.items():
        if isinstance(value, dict):
            html += f"        <div class='field'><span class='field-label'>{key}:</span></div>\n"
            for k, v in value.items():
                html += f"        <div class='field'><span class='field-value'>  {k}: {v}</span></div>\n"
        elif isinstance(value, list):
            html += f"        <div class='field'><span class='field-label'>{key}:</span> ({len(value)} items)</div>\n"
            if value and isinstance(value[0], dict):
                # Render as table
                html += "        <table>\n"
                headers = list(value[0].keys())
                html += "            <tr>" + "".join(f"<th>{h}</th>" for h in headers) + "</tr>\n"
                for item in value[:10]:  # Limit to 10 rows
                    html += "            <tr>" + "".join(f"<td>{item.get(h, '')}</td>" for h in headers) + "</tr>\n"
                html += "        </table>\n"
        else:
            html += f"        <div class='field'><span class='field-label'>{key}:</span> <span class='field-value'>{value}</span></div>\n"

    html += """
    </div>
</body>
</html>
"""

    # Write to file
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html)

    logger.info(f"Generated HTML report: {output_path}")
    return html
