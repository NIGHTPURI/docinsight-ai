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