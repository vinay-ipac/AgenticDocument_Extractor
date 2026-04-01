import React, { useState, useEffect } from "react";
import { Loader2, AlertCircle, Download, Eye, FileJson, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/api/client";
import type { SchemaInfo, ExtractionResult } from "@/types";

interface ExtractionPanelProps {
  documentId: string;
  page: number;
}

export function ExtractionPanel({ documentId, page }: ExtractionPanelProps) {
  const [schemas, setSchemas] = useState<SchemaInfo[]>([]);
  const [selectedSchema, setSelectedSchema] = useState<string>("");
  const [customSchema, setCustomSchema] = useState<string>("");
  const [useCustomSchema, setUseCustomSchema] = useState(false);
  const [isLoadingSchemas, setIsLoadingSchemas] = useState(true);
  const [isExtracting, setIsExtracting] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [extractionResult, setExtractionResult] = useState<ExtractionResult | null>(null);
  const [viewMode, setViewMode] = useState<"tree" | "raw">("tree");

  useEffect(() => {
    let mounted = true;

    const loadSchemas = async () => {
      setIsLoadingSchemas(true);
      setError(null);

      try {
        const data = await api.listSchemas();
        if (mounted) {
          setSchemas(data.schemas);
          if (data.schemas.length > 0) {
            setSelectedSchema(data.schemas[0].name);
          }
        }
      } catch (err) {
        if (mounted) {
          setError(err instanceof Error ? err.message : "Failed to load schemas");
        }
      } finally {
        if (mounted) {
          setIsLoadingSchemas(false);
        }
      }
    };

    loadSchemas();

    return () => {
      mounted = false;
    };
  }, []);

  const handleExtract = async () => {
    setIsExtracting(true);
    setError(null);
    setExtractionResult(null);

    try {
      let schema = undefined;

      if (useCustomSchema) {
        // Validate and parse custom schema
        try {
          schema = JSON.parse(customSchema);
        } catch (err) {
          throw new Error("Invalid JSON in custom schema");
        }
      }

      const result = await api.extractWithSchema(
        documentId,
        page,
        useCustomSchema ? undefined : selectedSchema,
        schema
      );

      setExtractionResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Extraction failed");
    } finally {
      setIsExtracting(false);
    }
  };

  const handleExport = async () => {
    if (!extractionResult) return;

    setIsExporting(true);
    setError(null);

    try {
      const blob = await api.exportJSON(documentId, page);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${documentId}_page${page}_extraction.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Export failed");
    } finally {
      setIsExporting(false);
    }
  };

  const handleLoadSchemaTemplate = async () => {
    if (!selectedSchema) return;

    try {
      const schema = await api.getSchema(selectedSchema);
      setCustomSchema(JSON.stringify(schema, null, 2));
      setUseCustomSchema(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load schema template");
    }
  };

  if (isLoadingSchemas) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Schema Selector */}
      <div className="border-b p-4 space-y-4">
        <div className="flex items-center space-x-2">
          <input
            type="checkbox"
            id="use-custom"
            checked={useCustomSchema}
            onChange={(e) => setUseCustomSchema(e.target.checked)}
            className="h-4 w-4"
          />
          <label htmlFor="use-custom" className="text-sm font-medium">
            Use Custom Schema
          </label>
        </div>

        {!useCustomSchema ? (
          <div className="space-y-2">
            <label className="text-sm font-medium">Select Schema</label>
            <select
              className="w-full px-3 py-2 border rounded-md text-sm"
              value={selectedSchema}
              onChange={(e) => setSelectedSchema(e.target.value)}
            >
              {schemas.map((schema) => (
                <option key={schema.name} value={schema.name}>
                  {schema.title}
                </option>
              ))}
            </select>
            {selectedSchema && schemas.find((s) => s.name === selectedSchema) && (
              <p className="text-xs text-muted-foreground">
                {schemas.find((s) => s.name === selectedSchema)?.description}
              </p>
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={handleLoadSchemaTemplate}
              className="w-full"
            >
              <FileJson className="h-4 w-4 mr-2" />
              Load as Template
            </Button>
          </div>
        ) : (
          <div className="space-y-2">
            <label className="text-sm font-medium">Custom JSON Schema</label>
            <textarea
              className="w-full px-3 py-2 border rounded-md text-xs font-mono min-h-[200px]"
              value={customSchema}
              onChange={(e) => setCustomSchema(e.target.value)}
              placeholder='{\n  "type": "object",\n  "properties": {\n    "field": {\n      "type": "string"\n    }\n  }\n}'
            />
          </div>
        )}

        <Button onClick={handleExtract} disabled={isExtracting} className="w-full">
          {isExtracting ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Extracting...
            </>
          ) : (
            <>
              <Sparkles className="mr-2 h-4 w-4" />
              Extract Data
            </>
          )}
        </Button>
      </div>

      {/* Error Display */}
      {error && (
        <div className="flex items-center space-x-2 p-4 border-b bg-destructive/10 text-destructive text-sm">
          <AlertCircle className="h-4 w-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Results */}
      {extractionResult && (
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Results Header */}
          <div className="border-b p-4 space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold">Extraction Results</h3>
              <div className="flex items-center space-x-2">
                <Button
                  variant={viewMode === "tree" ? "default" : "outline"}
                  size="sm"
                  onClick={() => setViewMode("tree")}
                >
                  <Eye className="h-4 w-4" />
                </Button>
                <Button
                  variant={viewMode === "raw" ? "default" : "outline"}
                  size="sm"
                  onClick={() => setViewMode("raw")}
                >
                  <FileJson className="h-4 w-4" />
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleExport}
                  disabled={isExporting}
                >
                  {isExporting ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Download className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2 text-xs">
              <div>
                <span className="text-muted-foreground">Schema:</span>{" "}
                <span className="font-medium">{extractionResult.schema_used}</span>
              </div>
              {extractionResult.confidence !== undefined && (
                <div>
                  <span className="text-muted-foreground">Confidence:</span>{" "}
                  <span className="font-medium">
                    {(extractionResult.confidence * 100).toFixed(1)}%
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Results Content */}
          <div className="flex-1 overflow-auto p-4">
            {viewMode === "tree" ? (
              <JsonTreeView data={extractionResult.data} />
            ) : (
              <pre className="text-xs font-mono whitespace-pre-wrap break-words">
                {JSON.stringify(extractionResult.data, null, 2)}
              </pre>
            )}
          </div>
        </div>
      )}

      {/* Empty State */}
      {!extractionResult && !error && (
        <div className="flex-1 flex items-center justify-center p-6">
          <div className="text-center space-y-2">
            <Sparkles className="h-12 w-12 mx-auto text-muted-foreground/50" />
            <p className="text-sm text-muted-foreground">
              Select a schema and click Extract to begin
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

interface JsonTreeViewProps {
  data: any;
  level?: number;
}

function JsonTreeView({ data, level = 0 }: JsonTreeViewProps) {
  const [expandedKeys, setExpandedKeys] = useState<Set<string>>(new Set());

  const toggleKey = (key: string) => {
    const newExpanded = new Set(expandedKeys);
    if (newExpanded.has(key)) {
      newExpanded.delete(key);
    } else {
      newExpanded.add(key);
    }
    setExpandedKeys(newExpanded);
  };

  const renderValue = (value: any, key: string, path: string): React.ReactNode => {
    const fullPath = path ? `${path}.${key}` : key;

    if (value === null) {
      return <span className="text-muted-foreground italic">null</span>;
    }

    if (typeof value === "boolean") {
      return <span className="text-blue-600">{value.toString()}</span>;
    }

    if (typeof value === "number") {
      return <span className="text-green-600">{value}</span>;
    }

    if (typeof value === "string") {
      return <span className="text-orange-600">"{value}"</span>;
    }

    if (Array.isArray(value)) {
      const isExpanded = expandedKeys.has(fullPath);
      return (
        <div>
          <button
            onClick={() => toggleKey(fullPath)}
            className="text-muted-foreground hover:text-foreground"
          >
            {isExpanded ? "▼" : "▶"} [{value.length}]
          </button>
          {isExpanded && (
            <div className="ml-4 border-l pl-2 mt-1">
              {value.map((item, index) => (
                <div key={index} className="py-0.5">
                  <span className="text-muted-foreground">{index}:</span>{" "}
                  {renderValue(item, index.toString(), fullPath)}
                </div>
              ))}
            </div>
          )}
        </div>
      );
    }

    if (typeof value === "object") {
      const isExpanded = expandedKeys.has(fullPath);
      const keys = Object.keys(value);
      return (
        <div>
          <button
            onClick={() => toggleKey(fullPath)}
            className="text-muted-foreground hover:text-foreground"
          >
            {isExpanded ? "▼" : "▶"} {"{"}
            {keys.length}
            {"}"}
          </button>
          {isExpanded && (
            <div className="ml-4 border-l pl-2 mt-1">
              {keys.map((k) => (
                <div key={k} className="py-0.5">
                  <span className="text-purple-600 font-medium">{k}:</span>{" "}
                  {renderValue(value[k], k, fullPath)}
                </div>
              ))}
            </div>
          )}
        </div>
      );
    }

    return <span>{String(value)}</span>;
  };

  if (typeof data !== "object" || data === null) {
    return <div className="text-xs font-mono">{renderValue(data, "", "")}</div>;
  }

  return (
    <div className="text-xs font-mono space-y-1">
      {Object.keys(data).map((key) => (
        <div key={key}>
          <span className="text-purple-600 font-medium">{key}:</span>{" "}
          {renderValue(data[key], key, "")}
        </div>
      ))}
    </div>
  );
}
