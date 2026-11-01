import uuid
from pathlib import Path

import fitz
from fastapi import HTTPException, UploadFile

from app.config import settings


def display_filename(filename: str | None) -> str:
    return (filename or "document.pdf").replace("\\", "/").rsplit("/", 1)[-1][:255] or "document.pdf"


async def save_pdf_file(file: UploadFile) -> tuple[str, int]:
    directory = Path(settings.upload_dir)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{uuid.uuid4()}.pdf"
    size = 0
    try:
        with path.open("xb") as target:
            while chunk := await file.read(64 * 1024):
                size += len(chunk)
                if size > settings.max_upload_bytes:
                    raise HTTPException(status_code=413, detail="PDF 파일 크기가 업로드 한도를 초과했습니다.")
                target.write(chunk)
        return str(path), size
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def extract_text_from_pdf(file_path: str) -> str:
    try:
        with fitz.open(file_path) as doc:
            if not doc.is_pdf or doc.needs_pass:
                raise HTTPException(status_code=400, detail="암호화되지 않은 유효한 PDF가 필요합니다.")
            if len(doc) > settings.max_pdf_pages:
                raise HTTPException(status_code=413, detail="PDF 페이지 수가 처리 한도를 초과했습니다.")
            texts = []
            total = 0
            for page in doc:
                text = page.get_text()
                total += len(text) + 1
                if total > settings.max_document_chars:
                    raise HTTPException(status_code=413, detail="문서 텍스트가 처리 한도를 초과했습니다.")
                texts.append(text)
            return "\n".join(texts).strip()
    except (fitz.FileDataError, RuntimeError, ValueError):
        raise HTTPException(status_code=400, detail="PDF 파일을 읽을 수 없습니다.") from None
