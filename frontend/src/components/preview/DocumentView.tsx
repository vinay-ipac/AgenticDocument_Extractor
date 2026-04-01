import React, { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { DocumentViewer } from "./DocumentViewer";
import { ParsingPanel } from "@/components/parsing/ParsingPanel";
import { ExtractionPanel } from "@/components/extraction/ExtractionPanel";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";

interface DocumentViewProps {
  documentId: string;
  pageCount: number;
  currentPage: number;
  onPageChange: (page: number) => void;
}

export function DocumentView({
  documentId,
  pageCount,
  currentPage,
  onPageChange,
}: DocumentViewProps) {
  const [selectedRegionId, setSelectedRegionId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<string>("parsing");

  const handleRegionClick = (regionId: string) => {
    setSelectedRegionId(regionId);
    setActiveTab("parsing");
  };

  const handlePreviousPage = () => {
    if (currentPage > 1) {
      onPageChange(currentPage - 1);
      setSelectedRegionId(null);
    }
  };

  const handleNextPage = () => {
    if (currentPage < pageCount) {
      onPageChange(currentPage + 1);
      setSelectedRegionId(null);
    }
  };

  return (
    <div className="flex h-screen">
      {/* Left Panel - Document Viewer */}
      <div className="flex-1 flex flex-col border-r bg-muted/5">
        <div className="flex-1 overflow-hidden">
          <DocumentViewer
            documentId={documentId}
            page={currentPage}
            onRegionClick={handleRegionClick}
          />
        </div>

        {/* Page Navigation */}
        <div className="border-t bg-background p-4">
          <div className="flex items-center justify-between">
            <Button
              variant="outline"
              size="sm"
              onClick={handlePreviousPage}
              disabled={currentPage <= 1}
            >
              <ChevronLeft className="h-4 w-4 mr-1" />
              Previous
            </Button>

            <div className="text-sm font-medium">
              Page {currentPage} of {pageCount}
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={handleNextPage}
              disabled={currentPage >= pageCount}
            >
              Next
              <ChevronRight className="h-4 w-4 ml-1" />
            </Button>
          </div>
        </div>
      </div>

      {/* Right Panel - Parsing & Extraction Tabs */}
      <div className="w-[480px] flex flex-col bg-background">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col">
          <div className="border-b px-4 pt-4">
            <TabsList className="w-full">
              <TabsTrigger value="parsing" className="flex-1">
                Parsing
              </TabsTrigger>
              <TabsTrigger value="extraction" className="flex-1">
                Extraction
              </TabsTrigger>
            </TabsList>
          </div>

          <div className="flex-1 overflow-hidden">
            <TabsContent value="parsing" className="h-full m-0 p-0">
              <ParsingPanel
                documentId={documentId}
                page={currentPage}
                selectedRegionId={selectedRegionId}
                onRegionSelect={setSelectedRegionId}
              />
            </TabsContent>

            <TabsContent value="extraction" className="h-full m-0 p-0">
              <ExtractionPanel documentId={documentId} page={currentPage} />
            </TabsContent>
          </div>
        </Tabs>
      </div>
    </div>
  );
}
