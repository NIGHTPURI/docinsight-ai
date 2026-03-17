# DocInsight AI

PDF 문서를 업로드하면 텍스트를 추출하고, LLM을 활용해 핵심 내용을 요약하며 문서 기반 질문에 답변하는 AI 서비스입니다.

---

## 개발 배경

긴 문서를 빠르게 이해하기 어렵다는 문제를 해결하기 위해 이 프로젝트를 시작했습니다.  
특히 단순 요약을 넘어, 문서 내용을 기반으로 정보를 활용할 수 있는 AI 서비스 구조를 목표로 설계했습니다.

---

## 주요 기능

- PDF 파일 업로드
- PDF 텍스트 추출 (PyMuPDF)
- LLM 기반 문서 요약
- 문서 기반 질문 응답 (Q&A)
- React 기반 웹 인터페이스 제공

---

## 기술 스택

### Backend
- Python
- FastAPI
- OpenAI API (LLM)
- PyMuPDF
- Pydantic

### Frontend
- React (Vite)
- Fetch API

---

## 시스템 구조

사용자 (웹)
→ React 프론트엔드
→ FastAPI 서버
→ PDF 텍스트 추출
→ LLM 호출 (요약 / 질문 응답)
→ 결과 반환

---

## API 명세

### 1. 문서 업로드
POST /documents/upload  
PDF 파일 업로드 및 텍스트 추출

---

### 2. 문서 요약
POST /documents/{document_id}/summarize  
문서 내용을 기반으로 AI 요약 생성

---

### 3. 문서 조회
GET /documents/{document_id}  
문서 정보 및 요약 결과 조회

---

### 4. 문서 기반 질문 응답
POST /documents/{document_id}/ask  

요청 예시:
```json
{
  "question": "이 문서의 핵심 내용은 무엇인가요?"
}