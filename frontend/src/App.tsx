import { useState } from "react";
import { FileText } from "lucide-react";
import { UploadView } from "./components/upload/UploadView";
import { DocumentView } from "./components/preview/DocumentView";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import type { DocumentInfo } from "./types";

function App() {
  const [currentDocument, setCurrentDocument] = useState<DocumentInfo | null>(null);
  const [currentPage, setCurrentPage] = useState(0);
  const [activeTab, setActiveTab] = useState("upload");

  const handleDocumentProcessed = (doc: DocumentInfo) => {
    setCurrentDocument(doc);
    setCurrentPage(0);
    setActiveTab("document");
  };

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b">
        <div className="container mx-auto px-4 py-4 flex items-center gap-3">
          <FileText className="w-8 h-8 text-primary" />
          <div>
            <h1 className="text-2xl font-bold">Document Extraction Dashboard</h1>
            <p className="text-sm text-muted-foreground">
              OCR, Layout Detection & Schema-based Extraction
            </p>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-6">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            <TabsTrigger value="upload">Upload & Process</TabsTrigger>
            <TabsTrigger value="document" disabled={!currentDocument}>
              Document View
            </TabsTrigger>
          </TabsList>

          <TabsContent value="upload" className="mt-6">
            <UploadView onDocumentProcessed={handleDocumentProcessed} />
          </TabsContent>

          <TabsContent value="document" className="mt-6">
            {currentDocument && (
              <DocumentView
                documentId={currentDocument.id}
                pageCount={currentDocument.page_count}
                currentPage={currentPage}
                onPageChange={setCurrentPage}
              />
            )}
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}

export default App;
