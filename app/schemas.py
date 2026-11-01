from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class DocumentUploadResponse(BaseModel):
    document_id: int
    filename: str
    extracted_text_length: int
    message: str


class DocumentSummaryResponse(BaseModel):
    document_id: int
    filename: str
    summary: str
    source_chars: int
    total_chars: int
    truncated: bool


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("질문을 입력해 주세요.")
        return value


class SourceExcerptResponse(BaseModel):
    source_id: str
    start_char: int
    end_char: int
    text: str


class AskResponse(BaseModel):
    document_id: int
    question: str
    answer: str
    sources: list[SourceExcerptResponse]
    answer_status: str


class SearchResponse(BaseModel):
    document_id: int
    question: str
    sources: list[SourceExcerptResponse]


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
