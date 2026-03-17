from pydantic import BaseModel


class UploadResponse(BaseModel):
    document_id: int
    filename: str
    extracted_text_length: int
    message: str


class SummaryResponse(BaseModel):
    document_id: int
    filename: str
    summary: str


class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    document_id: int
    question: str
    answer: str