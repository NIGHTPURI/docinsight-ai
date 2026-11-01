from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.dependencies import get_db
from app.repositories.document_repository import (
    create_document,
    create_question_answer,
    get_document_by_id,
    list_documents,
    list_question_answers_by_document_id,
    update_document_summary,
)
from app.schemas import (
    AskRequest,
    AskResponse,
    DocumentDetailResponse,
    DocumentListItemResponse,
    DocumentSummaryResponse,
    DocumentUploadResponse,
    QuestionAnswerItemResponse,
    SearchResponse,
)
from app.services.ai_service import answer_question_about_document, summarize_document, SUMMARY_MAX_CHARS
from app.services.pdf_service import extract_text_from_pdf, save_pdf_file, display_filename
from app.services.retrieval_service import retrieve_sources, format_context

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="PDF 파일만 업로드할 수 있습니다.")

    saved_path = None

    try:
        saved_path, file_size = await save_pdf_file(file)
        extracted_text = await run_in_threadpool(extract_text_from_pdf, saved_path)

        if not extracted_text.strip():
            raise HTTPException(status_code=400, detail="PDF에서 추출된 텍스트가 없습니다.")

        document = await run_in_threadpool(
            create_document,
            db,
            filename=display_filename(file.filename),
            original_path=saved_path,
            content_type=file.content_type,
            file_size=file_size,
            extracted_text=extracted_text,
        )

        return DocumentUploadResponse(
            document_id=document.id,
            filename=document.filename,
            extracted_text_length=document.extracted_text_length,
            message="업로드 및 텍스트 추출 완료",
        )
    except BaseException:
        try:
            db.rollback()
        finally:
            if saved_path:
                Path(saved_path).unlink(missing_ok=True)
        raise


@router.get("", response_model=list[DocumentListItemResponse])
def get_documents(db: Session = Depends(get_db)):
    documents = list_documents(db)
    return [
        DocumentListItemResponse(
            id=doc.id,
            filename=doc.filename,
            status=doc.status,
            extracted_text_length=doc.extracted_text_length,
            created_at=doc.created_at,
        )
        for doc in documents
    ]


@router.get("/{document_id}", response_model=DocumentDetailResponse)
def get_document(document_id: int, db: Session = Depends(get_db)):
    document = get_document_by_id(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다.")

    return DocumentDetailResponse(
        id=document.id,
        filename=document.filename,
        extracted_text_length=document.extracted_text_length,
        summary=document.summary,
        status=document.status,
        created_at=document.created_at,
        updated_at=document.updated_at,
    )


@router.post("/{document_id}/summarize", response_model=DocumentSummaryResponse)
def summarize_document_api(document_id: int, db: Session = Depends(get_db)):
    document = get_document_by_id(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다.")

    if document.summary:
        return DocumentSummaryResponse(
            document_id=document.id,
            filename=document.filename,
            summary=document.summary,
            source_chars=min(len(document.extracted_text), SUMMARY_MAX_CHARS),
            total_chars=len(document.extracted_text),
            truncated=len(document.extracted_text) > SUMMARY_MAX_CHARS,
        )

    summary = summarize_document(document.extracted_text)
    updated_document = update_document_summary(db, document, summary)

    return DocumentSummaryResponse(
        document_id=updated_document.id,
        filename=updated_document.filename,
        summary=updated_document.summary,
        source_chars=min(len(document.extracted_text), SUMMARY_MAX_CHARS),
        total_chars=len(document.extracted_text),
        truncated=len(document.extracted_text) > SUMMARY_MAX_CHARS,
    )


@router.post("/{document_id}/search", response_model=SearchResponse)
def search_document(document_id: int, request: AskRequest, db: Session = Depends(get_db)):
    document = get_document_by_id(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다.")
    sources = retrieve_sources(document.extracted_text, request.question)
    return SearchResponse(document_id=document_id, question=request.question,
                          sources=[source.to_dict() for source in sources])


@router.post("/{document_id}/ask", response_model=AskResponse)
def ask_document(
    document_id: int,
    request: AskRequest,
    db: Session = Depends(get_db),
):
    document = get_document_by_id(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다.")

    sources = retrieve_sources(document.extracted_text, request.question)
    if sources:
        answer = answer_question_about_document(format_context(sources), request.question)
    else:
        answer = "질문과 관련된 문서 구간을 찾지 못했습니다. 문서에 사용된 단어로 질문을 바꿔 주세요."

    create_question_answer(
        db,
        document_id=document.id,
        question=request.question,
        answer=answer,
    )

    return AskResponse(
        document_id=document.id,
        question=request.question,
        answer=answer,
        sources=[source.to_dict() for source in sources],
        answer_status="generated" if sources else "no_evidence",
    )


@router.get("/{document_id}/questions", response_model=list[QuestionAnswerItemResponse])
def get_document_questions(document_id: int, db: Session = Depends(get_db)):
    document = get_document_by_id(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다.")

    qas = list_question_answers_by_document_id(db, document_id)
    return [
        QuestionAnswerItemResponse(
            id=qa.id,
            question=qa.question,
            answer=qa.answer,
            created_at=qa.created_at,
        )
        for qa in qas
    ]
