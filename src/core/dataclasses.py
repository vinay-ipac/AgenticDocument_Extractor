"""Data classes for document processing."""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class RegionType(str, Enum):
    """Types of document regions."""
    TEXT = "text"
    TABLE = "table"
    IMAGE = "image"
    CHART = "chart"
    FORM = "form"
    STAMP = "stamp"
    HANDWRITING = "handwriting"
    HEADER = "header"
    FOOTER = "footer"
    UNKNOWN = "unknown"


class LayoutType(str, Enum):
    """Layout types for reading order."""
    SINGLE_COLUMN = "single_column"
    MULTI_COLUMN = "multi_column"
    TABLE_GRID = "table_grid"
    FREE_FORM = "free_form"


@dataclass
class BoundingBox:
    """Bounding box coordinates."""
    x_min: float
    y_min: float
    x_max: float
    y_max: float

    @property
    def width(self) -> float:
        return self.x_max - self.x_min

    @property
    def height(self) -> float:
        return self.y_max - self.y_min

    @property
    def area(self) -> float:
        return self.width * self.height

    @property
    def center(self) -> tuple:
        return ((self.x_min + self.x_max) / 2, (self.y_min + self.y_max) / 2)

    def to_tuple(self) -> tuple:
        return (self.x_min, self.y_min, self.x_max, self.y_max)

    def to_dict(self) -> dict:
        return {
            "x_min": self.x_min,
            "y_min": self.y_min,
            "x_max": self.x_max,
            "y_max": self.y_max,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BoundingBox":
        return cls(
            x_min=data["x_min"],
            y_min=data["y_min"],
            x_max=data["x_max"],
            y_max=data["y_max"],
        )


@dataclass
class OCRRegion:
    """OCR result for a detected text region."""
    id: str
    text: str
    bbox: BoundingBox
    confidence: float
    language: str = "en"
    region_type: RegionType = RegionType.TEXT
    parent_id: Optional[str] = None
    children_ids: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "text": self.text,
            "bbox": self.bbox.to_dict(),
            "confidence": self.confidence,
            "language": self.language,
            "region_type": self.region_type.value,
            "parent_id": self.parent_id,
            "children_ids": self.children_ids,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "OCRRegion":
        return cls(
            id=data["id"],
            text=data["text"],
            bbox=BoundingBox.from_dict(data["bbox"]),
            confidence=data["confidence"],
            language=data.get("language", "en"),
            region_type=RegionType(data.get("region_type", "text")),
            parent_id=data.get("parent_id"),
            children_ids=data.get("children_ids", []),
            metadata=data.get("metadata", {}),
        )


@dataclass
class LayoutRegion:
    """Layout region with reading order information."""
    id: str
    region_type: RegionType
    bbox: BoundingBox
    reading_order: int
    confidence: float = 1.0
    ocr_regions: list = field(default_factory=list)
    sub_regions: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def add_ocr_region(self, ocr_region: OCRRegion):
        """Add an OCR region to this layout region."""
        self.ocr_regions.append(ocr_region)
        ocr_region.parent_id = self.id

    @property
    def children_ids(self) -> list:
        return [r.id for r in self.ocr_regions]

    @property
    def combined_text(self) -> str:
        """Get combined text from all OCR regions in reading order."""
        sorted_regions = sorted(self.ocr_regions, key=lambda r: r.bbox.y_min)
        return " ".join(r.text for r in sorted_regions if r.text.strip())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "region_type": self.region_type.value,
            "bbox": self.bbox.to_dict(),
            "reading_order": self.reading_order,
            "confidence": self.confidence,
            "ocr_regions": [r.to_dict() for r in self.ocr_regions],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LayoutRegion":
        region = cls(
            id=data["id"],
            region_type=RegionType(data["region_type"]),
            bbox=BoundingBox.from_dict(data["bbox"]),
            reading_order=data["reading_order"],
            confidence=data.get("confidence", 1.0),
            metadata=data.get("metadata", {}),
        )
        region.ocr_regions = [OCRRegion.from_dict(r) for r in data.get("ocr_regions", [])]
        return region


@dataclass
class DocumentLayout:
    """Complete document layout with all regions."""
    document_path: str
    page_number: int
    image_width: int
    image_height: int
    layout_type: LayoutType = LayoutType.SINGLE_COLUMN
    regions: list = field(default_factory=list)
    language: str = "mixed"
    metadata: dict = field(default_factory=dict)

    def add_region(self, region: LayoutRegion):
        """Add a layout region."""
        self.regions.append(region)

    def get_regions_by_type(self, region_type: RegionType) -> list:
        """Get all regions of a specific type."""
        return [r for r in self.regions if r.region_type == region_type]

    def get_region_by_id(self, region_id: str) -> Optional[LayoutRegion]:
        """Get a region by its ID."""
        for region in self.regions:
            if region.id == region_id:
                return region
            if region.id == region_id:
                return region
        return None

    def sort_by_reading_order(self):
        """Sort regions by reading order."""
        self.regions.sort(key=lambda r: r.reading_order)

    def to_dict(self) -> dict:
        return {
            "document_path": self.document_path,
            "page_number": self.page_number,
            "image_width": self.image_width,
            "image_height": self.image_height,
            "layout_type": self.layout_type.value,
            "language": self.language,
            "regions": [r.to_dict() for r in self.regions],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DocumentLayout":
        layout = cls(
            document_path=data["document_path"],
            page_number=data["page_number"],
            image_width=data["image_width"],
            image_height=data["image_height"],
            layout_type=LayoutType(data.get("layout_type", "single_column")),
            language=data.get("language", "mixed"),
            metadata=data.get("metadata", {}),
        )
        layout.regions = [LayoutRegion.from_dict(r) for r in data.get("regions", [])]
        return layout
