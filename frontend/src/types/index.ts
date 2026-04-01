export interface BoundingBox {
  x_min: number;
  y_min: number;
  x_max: number;
  y_max: number;
}

export interface OCRRegion {
  id: string;
  text: string;
  bbox: BoundingBox;
  confidence: number;
  language: string;
  region_type: string;
}

export interface LayoutRegion {
  id: string;
  region_type: string;
  bbox: BoundingBox;
  reading_order: number;
  confidence: number;
  ocr_regions: OCRRegion[];
  combined_text?: string;
  metadata?: Record<string, any>;
}

export interface DocumentLayout {
  document_path: string;
  page_number: number;
  image_width: number;
  image_height: number;
  layout_type: string;
  language: string;
  regions: LayoutRegion[];
  metadata?: Record<string, any>;
}

export interface DocumentInfo {
  id: string;
  filename: string;
  status: string;
  created_at: string;
  page_count: number;
  processing_time: number;
  errors: string[];
}

export interface ParsingResponse {
  document_id: string;
  page: number;
  image_width: number;
  image_height: number;
  layout_type: string;
  language: string;
  regions: LayoutRegion[];
  region_count: number;
}

export interface SchemaInfo {
  name: string;
  title: string;
  description: string;
  required_fields: string[];
}

export interface ExtractionResult {
  document_id: string;
  page: number;
  schema_used: string;
  data: Record<string, any>;
  confidence?: number;
}

export interface SSEEvent {
  type: string;
  data: any;
}

export type ProcessingStep =
  | "loading"
  | "loaded"
  | "ocr"
  | "layout"
  | "done"
  | "error";
