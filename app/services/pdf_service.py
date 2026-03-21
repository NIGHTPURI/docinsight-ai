import os
import uuid

import fitz
from fastapi import UploadFile

from app.config import settings


async def save_pdf_file(file: UploadFile) -> tuple[str, int]:
    os.makedirs(settings.upload_dir, exist_ok=True)

    unique_name = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(settings.upload_dir, unique_name)

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    return file_path, len(content)


def extract_text_from_pdf(file_path: str) -> str:
    doc = fitz.open(file_path)
    texts = []

    for page in doc:
        texts.append(page.get_text())

    doc.close()
    return "\n".join(texts).strip()