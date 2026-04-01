import React, { useState, useEffect, useRef } from "react";
import { Loader2, AlertCircle, ZoomIn, ZoomOut } from "lucide-react";
import { api } from "@/api/client";
import { getRegionColor } from "@/lib/utils";
import type { LayoutRegion } from "@/types";
import { Button } from "@/components/ui/button";

interface DocumentViewerProps {
  documentId: string;
  page: number;
  onRegionClick?: (regionId: string) => void;
}

export function DocumentViewer({ documentId, page, onRegionClick }: DocumentViewerProps) {
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [regions, setRegions] = useState<LayoutRegion[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedRegionId, setSelectedRegionId] = useState<string | null>(null);
  const [zoom, setZoom] = useState(1);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });
  const containerRef = useRef<HTMLDivElement>(null);
  const imageRef = useRef<HTMLImageElement>(null);

  useEffect(() => {
    let mounted = true;

    const loadPageData = async () => {
      setIsLoading(true);
      setError(null);
      setSelectedRegionId(null);

      try {
        // Load image and regions in parallel
        const [imgUrl, regionsData] = await Promise.all([
          api.getPageImage(documentId, page),
          api.getRegions(documentId, page),
        ]);

        if (mounted) {
          setImageUrl(imgUrl);
          setRegions(regionsData.regions || []);
        }
      } catch (err) {
        if (mounted) {
          setError(err instanceof Error ? err.message : "Failed to load page");
        }
      } finally {
        if (mounted) {
          setIsLoading(false);
        }
      }
    };

    loadPageData();

    return () => {
      mounted = false;
      if (imageUrl) {
        URL.revokeObjectURL(imageUrl);
      }
    };
  }, [documentId, page]);

  const handleImageLoad = () => {
    if (imageRef.current) {
      setDimensions({
        width: imageRef.current.naturalWidth,
        height: imageRef.current.naturalHeight,
      });
    }
  };

  const handleRegionClick = (regionId: string) => {
    setSelectedRegionId(regionId);
    onRegionClick?.(regionId);
  };

  const handleZoomIn = () => {
    setZoom((prev) => Math.min(prev + 0.25, 3));
  };

  const handleZoomOut = () => {
    setZoom((prev) => Math.max(prev - 0.25, 0.5));
  };

  const handleResetZoom = () => {
    setZoom(1);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full p-6">
        <div className="flex items-center space-x-2 text-destructive">
          <AlertCircle className="h-5 w-5" />
          <span className="text-sm">{error}</span>
        </div>
      </div>
    );
  }

  if (!imageUrl) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-sm text-muted-foreground">No image available</p>
      </div>
    );
  }

  return (
    <div className="relative h-full flex flex-col">
      {/* Zoom Controls */}
      <div className="absolute top-4 right-4 z-10 flex space-x-2 bg-background/95 backdrop-blur rounded-md shadow-lg p-2">
        <Button variant="outline" size="sm" onClick={handleZoomOut} disabled={zoom <= 0.5}>
          <ZoomOut className="h-4 w-4" />
        </Button>
        <Button variant="outline" size="sm" onClick={handleResetZoom}>
          {Math.round(zoom * 100)}%
        </Button>
        <Button variant="outline" size="sm" onClick={handleZoomIn} disabled={zoom >= 3}>
          <ZoomIn className="h-4 w-4" />
        </Button>
      </div>

      {/* Scrollable Container */}
      <div ref={containerRef} className="flex-1 overflow-auto p-6">
        <div className="relative inline-block" style={{ transform: `scale(${zoom})`, transformOrigin: "top left" }}>
          {/* Page Image */}
          <img
            ref={imageRef}
            src={imageUrl}
            alt={`Page ${page}`}
            className="block max-w-full h-auto"
            onLoad={handleImageLoad}
          />

          {/* SVG Overlay for Regions */}
          {dimensions.width > 0 && (
            <svg
              className="absolute top-0 left-0 w-full h-full pointer-events-none"
              viewBox={`0 0 ${dimensions.width} ${dimensions.height}`}
              preserveAspectRatio="none"
            >
              {regions.map((region) => {
                const isSelected = region.id === selectedRegionId;
                const color = getRegionColor(region.region_type);

                return (
                  <g key={region.id}>
                    {/* Bounding Box */}
                    <rect
                      x={region.bbox.x_min}
                      y={region.bbox.y_min}
                      width={region.bbox.x_max - region.bbox.x_min}
                      height={region.bbox.y_max - region.bbox.y_min}
                      fill={isSelected ? color : "transparent"}
                      fillOpacity={isSelected ? 0.15 : 0}
                      stroke={color}
                      strokeWidth={isSelected ? 3 : 2}
                      strokeOpacity={isSelected ? 1 : 0.6}
                      className="pointer-events-auto cursor-pointer transition-all"
                      onClick={() => handleRegionClick(region.id)}
                      style={{ pointerEvents: "auto" }}
                    />

                    {/* Region Label */}
                    {isSelected && (
                      <text
                        x={region.bbox.x_min + 4}
                        y={region.bbox.y_min + 16}
                        fill={color}
                        fontSize="12"
                        fontWeight="bold"
                        className="pointer-events-none"
                      >
                        {region.region_type}
                      </text>
                    )}
                  </g>
                );
              })}
            </svg>
          )}
        </div>
      </div>
    </div>
  );
}
