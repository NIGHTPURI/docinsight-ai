from datetime import datetime
from pydantic import BaseModel


class DocumentUploadResponse(BaseModel):
    document_id: int
    filename: str
    extracted_text_length: int
    message: str


class DocumentSummaryResponse(BaseModel):
    document_id: int
    filename: str
    summary: str


class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    document_id: int
    question: str
    answer: str


class DocumentDetailResponse(BaseModel):
    id: int
    filename: str
    extracted_text_length: int
    summary: str | None
    status: str
    created_at: datetime
    updated_at: datetime


class DocumentListItemResponse(BaseModel):
    id: int
    filename: str
    status: str
    extracted_text_length: int
    created_at: datetime


class QuestionAnswerItemResponse(BaseModel):
    id: int
    question: str
    answer: str
    created_at: datetime