from pathlib import Path
from typing import Dict

from fastapi import APIRouter, File, HTTPException, UploadFile
from app.config import settings
from app.schemas import SummaryResponse, UploadResponse
from app.services.ai_service import summarize_text
from app.services.pdf_service import extract_text_from_pdf
from app.schemas import AskRequest, AskResponse, SummaryResponse, UploadResponse
from app.services.ai_service import ask_about_document, summarize_text

router = APIRouter(prefix="/documents", tags=["documents"])

DOCUMENT_STORE: Dict[int, dict] = {}
CURRENT_ID = 1


@router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    global CURRENT_ID

    if not file.filename:
        raise HTTPException(status_code=400, detail="파일명이 없습니다.")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="PDF 파일만 업로드 가능합니다.")

    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    safe_filename = f"{CURRENT_ID}_{file.filename}"
    file_path = upload_dir / safe_filename

    try:
        content = await file.read()
        file_path.write_bytes(content)

        extracted_text = extract_text_from_pdf(str(file_path))
        if not extracted_text:
            raise HTTPException(status_code=400, detail="PDF에서 텍스트를 추출하지 못했습니다.")

        document_id = CURRENT_ID
        DOCUMENT_STORE[document_id] = {
            "id": document_id,
            "filename": file.filename,
            "saved_path": str(file_path),
            "text": extracted_text,
            "summary": None,
        }
        CURRENT_ID += 1

        return UploadResponse(
            document_id=document_id,
            filename=file.filename,
            extracted_text_length=len(extracted_text),
            message="업로드 및 텍스트 추출 완료",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"업로드 처리 중 오류가 발생했습니다: {str(e)}")


@router.post("/{document_id}/summarize", response_model=SummaryResponse)
def summarize_document(document_id: int):
    document = DOCUMENT_STORE.get(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다.")

    try:
        summary = summarize_text(document["text"])
        document["summary"] = summary

        return SummaryResponse(
            document_id=document_id,
            filename=document["filename"],
            summary=summary,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"요약 생성 중 오류가 발생했습니다: {str(e)}")


@router.get("/{document_id}")
def get_document(document_id: int):
    document = DOCUMENT_STORE.get(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다.")

    return {
        "document_id": document["id"],
        "filename": document["filename"],
        "summary": document["summary"],
        "text_preview": document["text"][:500],
    }

@router.post("/{document_id}/ask", response_model=AskResponse)
def ask_document(document_id: int, request: AskRequest):
    document = DOCUMENT_STORE.get(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다.")

    try:
        answer = ask_about_document(document["text"], request.question)

        return AskResponse(
            document_id=document_id,
            question=request.question,
            answer=answer,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"질문 처리 중 오류가 발생했습니다: {str(e)}")