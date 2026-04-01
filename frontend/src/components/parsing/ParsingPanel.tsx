import React, { useState, useEffect } from "react";
import { Loader2, AlertCircle, FileText, Search } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api } from "@/api/client";
import { getRegionColor } from "@/lib/utils";
import type { ParsingResponse, LayoutRegion } from "@/types";
import { cn } from "@/lib/utils";

interface ParsingPanelProps {
  documentId: string;
  page: number;
  selectedRegionId: string | null;
  onRegionSelect: (regionId: string | null) => void;
}

export function ParsingPanel({
  documentId,
  page,
  selectedRegionId,
  onRegionSelect,
}: ParsingPanelProps) {
  const [parsing, setParsing] = useState<ParsingResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    let mounted = true;

    const loadParsing = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const data = await api.getParsing(documentId, page);
        if (mounted) {
          setParsing(data);
        }
      } catch (err) {
        if (mounted) {
          setError(err instanceof Error ? err.message : "Failed to load parsing data");
        }
      } finally {
        if (mounted) {
          setIsLoading(false);
        }
      }
    };

    loadParsing();

    return () => {
      mounted = false;
    };
  }, [documentId, page]);

  const selectedRegion = parsing?.regions.find((r) => r.id === selectedRegionId);

  const filteredRegions = parsing?.regions.filter((region) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      region.region_type.toLowerCase().includes(query) ||
      region.combined_text?.toLowerCase().includes(query) ||
      region.id.toLowerCase().includes(query)
    );
  });

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

  if (!parsing) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-sm text-muted-foreground">No parsing data available</p>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Stats Header */}
      <div className="border-b p-4 space-y-3">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-xs text-muted-foreground">Layout Type</p>
            <p className="text-sm font-medium">{parsing.layout_type}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Language</p>
            <p className="text-sm font-medium">{parsing.language}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Regions</p>
            <p className="text-sm font-medium">{parsing.region_count}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Dimensions</p>
            <p className="text-sm font-medium">
              {parsing.image_width} × {parsing.image_height}
            </p>
          </div>
        </div>

        {/* Search Bar */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search regions..."
            className="w-full pl-9 pr-3 py-2 text-sm border rounded-md"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      </div>

      {/* Region List */}
      <div className="flex-1 overflow-auto p-4 space-y-2">
        {filteredRegions && filteredRegions.length > 0 ? (
          filteredRegions.map((region) => (
            <RegionCard
              key={region.id}
              region={region}
              isSelected={region.id === selectedRegionId}
              onClick={() => onRegionSelect(region.id === selectedRegionId ? null : region.id)}
            />
          ))
        ) : (
          <div className="flex items-center justify-center py-8 text-sm text-muted-foreground">
            No regions found
          </div>
        )}
      </div>

      {/* Selected Region Inspector */}
      {selectedRegion && (
        <div className="border-t p-4 space-y-3 bg-muted/30">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold">Region Details</h3>
            <Badge
              style={{
                backgroundColor: getRegionColor(selectedRegion.region_type),
                color: "white",
              }}
            >
              {selectedRegion.region_type}
            </Badge>
          </div>

          <div className="space-y-2 text-xs">
            <div>
              <span className="text-muted-foreground">ID:</span>{" "}
              <span className="font-mono">{selectedRegion.id}</span>
            </div>
            <div>
              <span className="text-muted-foreground">Reading Order:</span>{" "}
              {selectedRegion.reading_order}
            </div>
            <div>
              <span className="text-muted-foreground">Confidence:</span>{" "}
              {(selectedRegion.confidence * 100).toFixed(1)}%
            </div>
            <div>
              <span className="text-muted-foreground">OCR Regions:</span>{" "}
              {selectedRegion.ocr_regions.length}
            </div>
            {selectedRegion.combined_text && (
              <div>
                <span className="text-muted-foreground">Text Length:</span>{" "}
                {selectedRegion.combined_text.length} chars
              </div>
            )}
          </div>

          {selectedRegion.combined_text && (
            <div className="pt-2">
              <p className="text-xs text-muted-foreground mb-1">Extracted Text:</p>
              <div className="max-h-32 overflow-auto text-xs bg-background rounded p-2 border">
                {selectedRegion.combined_text}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

interface RegionCardProps {
  region: LayoutRegion;
  isSelected: boolean;
  onClick: () => void;
}

function RegionCard({ region, isSelected, onClick }: RegionCardProps) {
  const color = getRegionColor(region.region_type);

  return (
    <button
      className={cn(
        "w-full text-left p-3 rounded-md border transition-colors",
        isSelected
          ? "border-primary bg-primary/5 shadow-sm"
          : "border-muted hover:border-primary/50 hover:bg-muted/50"
      )}
      onClick={onClick}
    >
      <div className="flex items-start justify-between mb-2">
        <Badge
          variant="outline"
          style={{
            borderColor: color,
            color: color,
          }}
        >
          {region.region_type}
        </Badge>
        <span className="text-xs text-muted-foreground">#{region.reading_order}</span>
      </div>

      <div className="text-xs text-muted-foreground mb-1">
        <FileText className="inline h-3 w-3 mr-1" />
        {region.ocr_regions.length} OCR region{region.ocr_regions.length !== 1 ? "s" : ""}
        {" • "}
        {(region.confidence * 100).toFixed(0)}% confidence
      </div>

      {region.combined_text && (
        <p className="text-xs line-clamp-2 mt-2">{region.combined_text}</p>
      )}
    </button>
  );
}
