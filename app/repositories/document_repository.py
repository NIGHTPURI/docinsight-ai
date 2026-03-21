from sqlalchemy.orm import Session

from app.models import Document, QuestionAnswer


def create_document(
    db: Session,
    *,
    filename: str,
    original_path: str,
    content_type: str | None,
    file_size: int | None,
    extracted_text: str,
) -> Document:
    document = Document(
        filename=filename,
        original_path=original_path,
        content_type=content_type,
        file_size=file_size,
        extracted_text=extracted_text,
        extracted_text_length=len(extracted_text),
        status="uploaded",
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


def get_document_by_id(db: Session, document_id: int) -> Document | None:
    return db.query(Document).filter(Document.id == document_id).first()


def list_documents(db: Session) -> list[Document]:
    return db.query(Document).order_by(Document.created_at.desc()).all()


def update_document_summary(db: Session, document: Document, summary: str) -> Document:
    document.summary = summary
    document.status = "summarized"
    db.commit()
    db.refresh(document)
    return document


def create_question_answer(
    db: Session,
    *,
    document_id: int,
    question: str,
    answer: str,
) -> QuestionAnswer:
    qa = QuestionAnswer(
        document_id=document_id,
        question=question,
        answer=answer,
    )
    db.add(qa)
    db.commit()
    db.refresh(qa)
    return qa


def list_question_answers_by_document_id(db: Session, document_id: int) -> list[QuestionAnswer]:
    return (
        db.query(QuestionAnswer)
        .filter(QuestionAnswer.document_id == document_id)
        .order_by(QuestionAnswer.created_at.desc())
        .all()
    )