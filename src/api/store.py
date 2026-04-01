"""In-memory document store for the API."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from PIL import Image


class DocumentStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PARSED = "parsed"
    EXTRACTING = "extracting"
    COMPLETE = "complete"
    ERROR = "error"


@dataclass
class StoredDocument:
    id: str
    filename: str
    file_path: str
    status: DocumentStatus = DocumentStatus.UPLOADED
    created_at: str = ""
    page_count: int = 0
    images: list[Image.Image] = field(default_factory=list, repr=False)
    layouts: list[dict] = field(default_factory=list)
    extractions: list[dict] = field(default_factory=list)
    processing_time: float = 0.0
    errors: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()


class DocumentStore:
    """Thread-safe in-memory document store."""

    def __init__(self):
        self._documents: dict[str, StoredDocument] = {}

    def create(self, filename: str, file_path: str) -> StoredDocument:
        doc_id = uuid.uuid4().hex[:12]
        doc = StoredDocument(id=doc_id, filename=filename, file_path=file_path)
        self._documents[doc_id] = doc
        return doc

    def get(self, doc_id: str) -> Optional[StoredDocument]:
        return self._documents.get(doc_id)

    def list_all(self) -> list[StoredDocument]:
        return sorted(self._documents.values(), key=lambda d: d.created_at, reverse=True)

    def update_status(self, doc_id: str, status: DocumentStatus):
        doc = self._documents.get(doc_id)
        if doc:
            doc.status = status

    def delete(self, doc_id: str) -> bool:
        return self._documents.pop(doc_id, None) is not None


# Global singleton
store = DocumentStore()
