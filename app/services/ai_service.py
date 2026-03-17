from openai import OpenAI
from app.config import settings


client = OpenAI(api_key=settings.openai_api_key)


def summarize_text(text: str) -> str:
    if not text or not text.strip():
        raise ValueError("요약할 텍스트가 비어 있습니다.")

    shortened_text = text[:3000]

    prompt = f"""
다음 문서를 한국어로 간결하게 요약해 주세요.

조건:
1. 핵심 주제를 먼저 한 문장으로 설명
2. 주요 내용을 자연스럽게 정리
3. 너무 길지 않게 작성
4. 문서에 없는 내용은 추측하지 말 것

문서:
{shortened_text}
""".strip()

    response = client.responses.create(
        model=settings.model_name,
        input=prompt,
    )

    return response.output_text.strip()

def ask_about_document(document_text: str, question: str) -> str:
    if not document_text or not document_text.strip():
        raise ValueError("문서 텍스트가 비어 있습니다.")

    if not question or not question.strip():
        raise ValueError("질문이 비어 있습니다.")

    shortened_text = document_text[:12000]

    prompt = f"""
다음 문서를 바탕으로 사용자의 질문에 한국어로 답변해 주세요.

조건:
1. 반드시 제공된 문서 내용만 근거로 답변할 것
2. 문서에 없는 내용은 추측하지 말 것
3. 답변은 간결하지만 충분히 이해 가능하게 작성할 것

문서:
{shortened_text}

질문:
{question}
""".strip()

    response = client.responses.create(
        model=settings.model_name,
        input=prompt,
    )

    return response.output_text.strip()