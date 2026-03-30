"""Region Processor for cropping and encoding."""

import base64
import hashlib
import logging
from io import BytesIO
from pathlib import Path
from typing import Optional, Union

import numpy as np
from PIL import Image

from .dataclasses import LayoutRegion, OCRRegion, BoundingBox

logger = logging.getLogger(__name__)


class RegionProcessor:
    """
    Process document regions for VLM analysis.

    Handles cropping, encoding, and caching of regions.
    """

    def __init__(
        self,
        padding: int = 10,
        cache_enabled: bool = True,
        max_cache_size: int = 100,
        output_format: str = "PNG",
        quality: int = 95,
    ):
        """
        Initialize region processor.

        Args:
            padding: Padding around cropped regions in pixels
            cache_enabled: Whether to cache processed regions
            max_cache_size: Maximum number of cached regions
            output_format: Image output format (PNG, JPEG, WEBP)
            quality: JPEG/WEBP quality (1-100)
        """
        self.padding = padding
        self.cache_enabled = cache_enabled
        self.max_cache_size = max_cache_size
        self.output_format = output_format
        self.quality = quality
        self._cache: dict[str, bytes] = {}
        self._cache_order: list[str] = []

    def _get_cache_key(
        self,
        image_hash: str,
        bbox: BoundingBox,
        padding: int,
    ) -> str:
        """Generate cache key for a cropped region."""
        key_string = f"{image_hash}:{bbox.to_tuple()}:{padding}"
        return hashlib.md5(key_string.encode()).hexdigest()

    def _compute_image_hash(self, image: Image.Image) -> str:
        """Compute hash of image for caching."""
        img_bytes = image.tobytes()
        return hashlib.md5(img_bytes).hexdigest()

    def _evict_if_needed(self):
        """Evict oldest cache entries if needed."""
        while len(self._cache) >= self.max_cache_size and self._cache_order:
            oldest_key = self._cache_order.pop(0)
            self._cache.pop(oldest_key, None)

    def crop_region(
        self,
        image: Image.Image,
        bbox: BoundingBox,
        padding: Optional[int] = None,
    ) -> Image.Image:
        """
        Crop a region from an image with padding.

        Args:
            image: Source image
            bbox: Bounding box to crop
            padding: Optional override for padding

        Returns:
            Cropped PIL Image
        """
        if padding is None:
            padding = self.padding

        # Apply padding
        x_min = max(0, int(bbox.x_min - padding))
        y_min = max(0, int(bbox.y_min - padding))
        x_max = min(image.width, int(bbox.x_max + padding))
        y_max = min(image.height, int(bbox.y_max + padding))

        # Crop
        cropped = image.crop((x_min, y_min, x_max, y_max))

        logger.debug(
            f"Cropped region: ({x_min}, {y_min}) to ({x_max}, {y_max}), "
            f"size: {cropped.size}"
        )

        return cropped

    def encode_to_base64(
        self,
        image: Image.Image,
        format: Optional[str] = None,
        quality: Optional[int] = None,
    ) -> str:
        """
        Encode image to base64 string.

        Args:
            image: PIL Image to encode
            format: Output format (overrides default)
            quality: Quality setting (overrides default)

        Returns:
            Base64 encoded string (without data URI prefix)
        """
        if format is None:
            format = self.output_format
        if quality is None:
            quality = self.quality

        buffer = BytesIO()

        # Handle formats that don't support transparency
        if format.upper() in ("JPEG", "JPG"):
            if image.mode in ("RGBA", "LA", "P"):
                image = image.convert("RGB")
            image.save(buffer, format="JPEG", quality=quality, optimize=True)
        elif format.upper() == "WEBP":
            if image.mode in ("RGBA", "LA", "P"):
                image = image.convert("RGB")
            image.save(buffer, format="WEBP", quality=quality)
        else:
            image.save(buffer, format="PNG", optimize=True)

        buffer.seek(0)
        return base64.b64encode(buffer.read()).decode("utf-8")

    def process_region(
        self,
        image: Image.Image,
        region: Union[LayoutRegion, OCRRegion],
        use_cache: bool = True,
    ) -> str:
        """
        Process a region for VLM analysis.

        Args:
            image: Source image
            region: Region to process
            use_cache: Whether to use caching

        Returns:
            Base64 encoded cropped region
        """
        # Get bounding box
        if isinstance(region, LayoutRegion):
            bbox = region.bbox
            region_id = region.id
        elif isinstance(region, OCRRegion):
            bbox = region.bbox
            region_id = region.id
        else:
            raise ValueError(f"Unknown region type: {type(region)}")

        # Check cache
        if use_cache and self.cache_enabled:
            image_hash = self._compute_image_hash(image)
            cache_key = self._get_cache_key(image_hash, bbox, self.padding)

            if cache_key in self._cache:
                logger.debug(f"Cache hit for region {region_id}")
                return self._cache[cache_key]

        # Crop and encode
        cropped = self.crop_region(image, bbox)
        encoded = self.encode_to_base64(cropped)

        # Cache result
        if use_cache and self.cache_enabled:
            self._evict_if_needed()
            self._cache[cache_key] = encoded
            self._cache_order.append(cache_key)
            logger.debug(f"Cached region {region_id}")

        return encoded

    def process_all_regions(
        self,
        image: Image.Image,
        regions: list[Union[LayoutRegion, OCRRegion]],
        use_cache: bool = True,
    ) -> dict[str, str]:
        """
        Process multiple regions.

        Args:
            image: Source image
            regions: List of regions to process
            use_cache: Whether to use caching

        Returns:
            Dictionary mapping region IDs to base64 strings
        """
        results = {}
        for region in regions:
            results[region.id] = self.process_region(
                image, region, use_cache=use_cache
            )
        return results

    def get_full_image_base64(
        self,
        image: Image.Image,
        format: Optional[str] = None,
        quality: Optional[int] = None,
    ) -> str:
        """
        Encode full image to base64.

        Args:
            image: PIL Image
            format: Output format
            quality: Quality setting

        Returns:
            Base64 encoded string
        """
        return self.encode_to_base64(image, format=format, quality=quality)

    def create_vlm_payload(
        self,
        image: Image.Image,
        region: Union[LayoutRegion, OCRRegion],
        prompt: str,
        include_full_image: bool = False,
    ) -> dict:
        """
        Create a payload for VLM API calls.

        Args:
            image: Source image
            region: Region to analyze
            prompt: Prompt for VLM
            include_full_image: Whether to include full image

        Returns:
            Dictionary suitable for VLM API
        """
        region_b64 = self.process_region(image, region)

        content = []

        if include_full_image:
            full_b64 = self.get_full_image_base64(image)
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{full_b64}"},
            })

        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{region_b64}"},
        })

        content.append({"type": "text", "text": prompt})

        return {"content": content}

    def clear_cache(self):
        """Clear the region cache."""
        self._cache.clear()
        self._cache_order.clear()
        logger.info("Region cache cleared")

    def get_cache_stats(self) -> dict:
        """Get cache statistics."""
        total_size = sum(len(v) for v in self._cache.values())
        return {
            "entries": len(self._cache),
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
        }

    def load_image(self, source: Union[str, Path, np.ndarray, Image.Image]) -> Image.Image:
        """
        Load image from various sources.

        Args:
            source: File path, numpy array, or PIL Image

        Returns:
            PIL Image in RGB mode
        """
        if isinstance(source, (str, Path)):
            return Image.open(source).convert("RGB")
        elif isinstance(source, np.ndarray):
            if len(source.shape) == 3 and source.shape[2] == 3:
                # Assume BGR (OpenCV format)
                source = source[:, :, ::-1]
            return Image.fromarray(source).convert("RGB")
        elif isinstance(source, Image.Image):
            return source.convert("RGB")
        else:
            raise ValueError(f"Unsupported image source type: {type(source)}")
