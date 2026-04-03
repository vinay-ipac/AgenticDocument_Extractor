import type {
  DocumentInfo,
  ParsingResponse,
  SchemaInfo,
  ExtractionResult,
  SSEEvent,
} from "@/types";

const API_BASE = "/api";

class APIError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "APIError";
    this.status = status;
  }
}

async function fetchJSON<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${url}`, options);

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new APIError(
      response.status,
      errorData.error || errorData.detail || response.statusText
    );
  }

  return response.json();
}

export const api = {
  // Documents
  async uploadDocument(file: File): Promise<{ id: string; filename: string; status: string; message: string }> {
    const formData = new FormData();
    formData.append("file", file);

    return fetchJSON("/documents/upload", {
      method: "POST",
      body: formData,
    });
  },

  async listDocuments(): Promise<{ documents: DocumentInfo[] }> {
    return fetchJSON("/documents/");
  },

  async getDocument(docId: string): Promise<DocumentInfo> {
    return fetchJSON(`/documents/${docId}`);
  },

  async deleteDocument(docId: string): Promise<{ message: string }> {
    return fetchJSON(`/documents/${docId}`, { method: "DELETE" });
  },

  async getPageImage(docId: string, page: number): Promise<string> {
    const response = await fetch(`${API_BASE}/documents/${docId}/image/${page}`);
    if (!response.ok) throw new Error("Failed to fetch page image");
    const blob = await response.blob();
    return URL.createObjectURL(blob);
  },

  // Processing (SSE)
  processDocument(
    docId: string,
    options: {
      dpi?: number;
      language?: string;
      max_pages?: number;
    },
    onEvent: (event: SSEEvent) => void,
    onError: (error: Error) => void,
    onComplete: () => void
  ): () => void {
    const params = new URLSearchParams({
      dpi: String(options.dpi || 150),
      language: options.language || "mixed",
      max_pages: String(options.max_pages || 100),
    });

    const eventSource = new EventSource(
      `${API_BASE}/documents/${docId}/process?${params}`
    );

    eventSource.addEventListener("status", (e) => {
      onEvent({ type: "status", data: JSON.parse(e.data) });
    });

    eventSource.addEventListener("progress", (e) => {
      onEvent({ type: "progress", data: JSON.parse(e.data) });
    });

    eventSource.addEventListener("complete", (e) => {
      onEvent({ type: "complete", data: JSON.parse(e.data) });
      eventSource.close();
      onComplete();
    });

    eventSource.addEventListener("error", (e) => {
      const data = (e as MessageEvent).data ? JSON.parse((e as MessageEvent).data) : {};
      onError(new Error(data.message || "Processing failed"));
      eventSource.close();
    });

    eventSource.onerror = () => {
      if (eventSource.readyState === EventSource.CLOSED) {
        eventSource.close();
      }
    };

    return () => eventSource.close();
  },

  // Parsing
  async getParsing(docId: string, page: number): Promise<ParsingResponse> {
    return fetchJSON(`/parsing/${docId}/${page}`);
  },

  async getRegions(docId: string, page: number): Promise<{ document_id: string; page: number; regions: any[] }> {
    return fetchJSON(`/parsing/${docId}/${page}/regions`);
  },

  // Extraction
  async extractWithSchema(
    docId: string,
    page: number,
    schemaName?: string,
    customSchema?: any
  ): Promise<ExtractionResult> {
    const body: any = {};
    if (schemaName) body.schema_name = schemaName;
    if (customSchema) body.custom_schema = customSchema;

    return fetchJSON(`/extraction/${docId}/${page}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  },

  async listSchemas(): Promise<{ schemas: SchemaInfo[] }> {
    return fetchJSON("/extraction/schemas");
  },

  async getSchema(schemaName: string): Promise<any> {
    return fetchJSON(`/extraction/schemas/${schemaName}`);
  },

  async validateSchema(schema: any): Promise<{ valid: boolean; errors: string[] }> {
    return fetchJSON("/extraction/validate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(schema),
    });
  },

  async exportJSON(docId: string, page: number): Promise<Blob> {
    const response = await fetch(`${API_BASE}/extraction/${docId}/${page}/export/json`);
    if (!response.ok) throw new Error("Failed to export JSON");
    return response.blob();
  },

  // Health
  async health(): Promise<{ status: string; version: string }> {
    return fetchJSON("/health");
  },
};

export { APIError };
