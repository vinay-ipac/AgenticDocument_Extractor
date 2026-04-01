"""Pydantic models for API request/response."""

from pydantic import BaseModel, Field
from typing import Any, Optional


class DocumentInfo(BaseModel):
    id: str
    filename: str
    status: str
    created_at: str
    page_count: int = 0
    processing_time: float = 0.0
    errors: list[str] = []


class DocumentListResponse(BaseModel):
    documents: list[DocumentInfo]


class UploadResponse(BaseModel):
    id: str
    filename: str
    status: str
    message: str


class ProcessRequest(BaseModel):
    dpi: int = Field(default=150, ge=72, le=600)
    language: str = Field(default="mixed", pattern="^(hi|en|mixed)$")
    max_pages: int = Field(default=100, ge=1, le=500)


class ParsingResponse(BaseModel):
    document_id: str
    page: int
    image_width: int
    image_height: int
    layout_type: str
    language: str
    regions: list[dict]
    region_count: int


class ExtractionRequest(BaseModel):
    schema_name: Optional[str] = None
    custom_schema: Optional[dict] = None


class ExtractionResponse(BaseModel):
    document_id: str
    page: int
    schema_used: str
    data: dict
    confidence: Optional[float] = None


class SchemaInfo(BaseModel):
    name: str
    title: str
    description: str
    required_fields: list[str] = []


class SchemaListResponse(BaseModel):
    schemas: list[SchemaInfo]


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
