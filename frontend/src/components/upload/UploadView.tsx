import React, { useState, useCallback } from "react";
import { Upload, FileText, Loader2, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/api/client";
import type { DocumentInfo, SSEEvent } from "@/types";
import { cn } from "@/lib/utils";

interface UploadViewProps {
  onDocumentProcessed: (doc: DocumentInfo) => void;
}

interface ProcessingOptions {
  dpi: number;
  language: string;
  max_pages: number;
}

interface ProgressState {
  stage: string;
  message: string;
  percentage: number;
}

const ACCEPTED_FILE_TYPES = [
  "application/pdf",
  "image/png",
  "image/jpeg",
  "image/jpg",
  "image/tiff",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
];

const ACCEPTED_EXTENSIONS = ".pdf,.png,.jpg,.jpeg,.tiff,.docx";

export function UploadView({ onDocumentProcessed }: UploadViewProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [uploadedDocId, setUploadedDocId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState<ProgressState | null>(null);
  const [options, setOptions] = useState<ProcessingOptions>({
    dpi: 150,
    language: "mixed",
    max_pages: 100,
  });

  const validateFile = useCallback((file: File): boolean => {
    if (!ACCEPTED_FILE_TYPES.includes(file.type) && !file.name.match(/\.(pdf|png|jpe?g|tiff|docx)$/i)) {
      setError("Invalid file type. Please upload a PDF, image, or DOCX file.");
      return false;
    }

    if (file.size > 50 * 1024 * 1024) {
      setError("File too large. Maximum size is 50MB.");
      return false;
    }

    return true;
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      setError(null);

      const files = Array.from(e.dataTransfer.files);
      if (files.length > 0) {
        const file = files[0];
        if (validateFile(file)) {
          setSelectedFile(file);
        }
      }
    },
    [validateFile]
  );

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setError(null);
      const files = e.target.files;
      if (files && files.length > 0) {
        const file = files[0];
        if (validateFile(file)) {
          setSelectedFile(file);
        }
      }
    },
    [validateFile]
  );

  const handleUpload = useCallback(async () => {
    if (!selectedFile) return;

    setError(null);
    setIsUploading(true);

    try {
      const result = await api.uploadDocument(selectedFile);
      setUploadedDocId(result.id);
      setIsUploading(false);

      // Immediately start processing
      handleProcess(result.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
      setIsUploading(false);
    }
  }, [selectedFile]);

  const handleProcess = useCallback(
    (docId: string) => {
      setIsProcessing(true);
      setProgress({ stage: "loading", message: "Starting processing...", percentage: 0 });

      const cleanup = api.processDocument(
        docId,
        options,
        (event: SSEEvent) => {
          if (event.type === "status") {
            setProgress({
              stage: event.data.stage || "processing",
              message: event.data.message || "Processing...",
              percentage: 0,
            });
          } else if (event.type === "progress") {
            setProgress({
              stage: event.data.stage || "processing",
              message: event.data.message || "Processing...",
              percentage: event.data.percentage || 0,
            });
          } else if (event.type === "complete") {
            setProgress({
              stage: "done",
              message: "Processing complete",
              percentage: 100,
            });
          }
        },
        (err) => {
          setError(err.message);
          setIsProcessing(false);
          setProgress(null);
        },
        async () => {
          setIsProcessing(false);
          setProgress(null);

          // Fetch completed document info
          try {
            const docInfo = await api.getDocument(docId);
            onDocumentProcessed(docInfo);
          } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to load document");
          }
        }
      );

      return cleanup;
    },
    [options, onDocumentProcessed]
  );

  const handleReset = useCallback(() => {
    setSelectedFile(null);
    setUploadedDocId(null);
    setError(null);
    setProgress(null);
  }, []);

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Upload Document</CardTitle>
          <CardDescription>
            Upload a document for OCR processing and structured data extraction
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Dropzone */}
          <div
            className={cn(
              "border-2 border-dashed rounded-lg p-12 text-center transition-colors cursor-pointer",
              isDragging
                ? "border-primary bg-primary/5"
                : "border-muted-foreground/25 hover:border-primary/50",
              isUploading || isProcessing ? "pointer-events-none opacity-50" : ""
            )}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => document.getElementById("file-input")?.click()}
          >
            <input
              id="file-input"
              type="file"
              accept={ACCEPTED_EXTENSIONS}
              className="hidden"
              onChange={handleFileSelect}
              disabled={isUploading || isProcessing}
            />

            <div className="flex flex-col items-center space-y-4">
              <div className="rounded-full bg-primary/10 p-4">
                <Upload className="h-8 w-8 text-primary" />
              </div>

              {selectedFile ? (
                <div className="space-y-2">
                  <div className="flex items-center space-x-2 text-sm">
                    <FileText className="h-4 w-4" />
                    <span className="font-medium">{selectedFile.name}</span>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
              ) : (
                <>
                  <div>
                    <p className="text-sm font-medium">Drop your document here, or click to browse</p>
                    <p className="text-xs text-muted-foreground mt-1">
                      Supports PDF, PNG, JPEG, TIFF, DOCX (max 50MB)
                    </p>
                  </div>
                </>
              )}
            </div>
          </div>

          {/* Processing Options */}
          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">DPI</label>
              <select
                className="w-full px-3 py-2 border rounded-md text-sm"
                value={options.dpi}
                onChange={(e) => setOptions({ ...options, dpi: parseInt(e.target.value) })}
                disabled={isUploading || isProcessing}
              >
                <option value="150">150 (Fast)</option>
                <option value="300">300 (Standard)</option>
                <option value="600">600 (High Quality)</option>
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Language</label>
              <select
                className="w-full px-3 py-2 border rounded-md text-sm"
                value={options.language}
                onChange={(e) => setOptions({ ...options, language: e.target.value })}
                disabled={isUploading || isProcessing}
              >
                <option value="mixed">Mixed (Hindi + English)</option>
                <option value="en">English</option>
                <option value="hi">Hindi</option>
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Max Pages</label>
              <input
                type="number"
                className="w-full px-3 py-2 border rounded-md text-sm"
                value={options.max_pages}
                onChange={(e) => setOptions({ ...options, max_pages: parseInt(e.target.value) || 100 })}
                min="1"
                max="1000"
                disabled={isUploading || isProcessing}
              />
            </div>
          </div>

          {/* Error Display */}
          {error && (
            <div className="flex items-center space-x-2 p-3 rounded-md bg-destructive/10 text-destructive text-sm">
              <AlertCircle className="h-4 w-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Progress Display */}
          {isProcessing && progress && (
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium">{progress.message}</span>
                {progress.percentage > 0 && (
                  <span className="text-muted-foreground">{progress.percentage}%</span>
                )}
              </div>
              <div className="h-2 bg-muted rounded-full overflow-hidden">
                <div
                  className="h-full bg-primary transition-all duration-300"
                  style={{ width: `${progress.percentage}%` }}
                />
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex space-x-3">
            {selectedFile && !uploadedDocId && (
              <Button onClick={handleUpload} disabled={isUploading || isProcessing} className="flex-1">
                {isUploading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Uploading...
                  </>
                ) : (
                  <>
                    <Upload className="mr-2 h-4 w-4" />
                    Upload & Process
                  </>
                )}
              </Button>
            )}

            {(selectedFile || error) && !isProcessing && (
              <Button variant="outline" onClick={handleReset}>
                Clear
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
