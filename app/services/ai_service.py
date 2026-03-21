from openai import OpenAI

from app.config import settings

client = OpenAI(api_key=settings.openai_api_key)


def _limit_text(text: str, max_chars: int = 12000) -> str:
    return text[:max_chars]


def summarize_document(text: str) -> str:
    limited_text = _limit_text(text)

    response = client.chat.completions.create(
        model=settings.model_name,
        messages=[
            {
                "role": "system",
                "content": "당신은 문서를 간결하고 정확하게 요약하는 AI입니다."
            },
            {
                "role": "user",
                "content": f"다음 문서를 핵심 위주로 요약해 주세요.\n\n{limited_text}"
            }
        ],
        temperature=0.2,
    )

    return response.choices[0].message.content.strip()


def answer_question_about_document(text: str, question: str) -> str:
    limited_text = _limit_text(text)

    response = client.chat.completions.create(
        model=settings.model_name,
        messages=[
            {
                "role": "system",
                "content": "당신은 문서 내용을 기반으로만 답변하는 AI입니다. 문서에 없는 내용은 추측하지 마세요."
            },
            {
                "role": "user",
                "content": f"문서:\n{limited_text}\n\n질문:\n{question}"
            }
        ],
        temperature=0.2,
    )

    return response.choices[0].message.content.strip()