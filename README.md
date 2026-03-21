# DocInsight AI

PDF 문서를 업로드하면 텍스트를 추출하고, AI를 활용해 요약 및 문서 기반 질문 응답을 제공하는 서비스입니다.

---

## 1. 프로젝트 개요

DocInsight AI는 긴 문서를 빠르게 이해하기 어려운 문제를 해결하기 위해 만든 AI 기반 문서 분석 서비스입니다.

다음 기능을 하나의 시스템으로 구현합니다.

- PDF 업로드
- 텍스트 추출
- AI 요약
- 문서 기반 질문 응답
- DB 저장 및 관리
- React UI

---

## 2. 주요 기능

### 문서 업로드
- PDF 업로드
- 텍스트 추출
- DB 저장

### 문서 요약
- 핵심 내용 요약
- 결과 저장

### 문서 질문 응답
- 문서 기반 질문
- AI 답변 생성

### 문서 관리
- 문서 목록 조회
- 상세 조회
- 상태 관리

---

## 3. 아키텍처

Browser → React → FastAPI → PDF 처리 → OpenAI → DB

---

## 4. 기술 스택

Backend:
- Python
- FastAPI
- SQLAlchemy
- PyMuPDF
- OpenAI

Frontend:
- React
- Vite

Database:
- SQLite

---

## 5. 프로젝트 구조

docinsight-ai/
├─ app/
│  ├─ main.py
│  ├─ config.py
│  ├─ database.py
│  ├─ dependencies.py
│  ├─ models.py
│  ├─ schemas.py
│  ├─ routers/
│  │   └─ documents.py
│  ├─ services/
│  │   ├─ pdf_service.py
│  │   └─ ai_service.py
│  └─ repositories/
│      └─ document_repository.py
├─ frontend/
├─ uploads/
├─ requirements.txt
├─ README.md
└─ CHANGELOG.md

---

## 6. 실행 방법

### Backend

python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

.env

OPENAI_API_KEY=your_api_key
MODEL_NAME=gpt-4.1-mini
UPLOAD_DIR=uploads
DATABASE_URL=sqlite:///./docinsight.db

실행

uvicorn app.main:app --reload --reload-dir app

---

### Frontend

cd frontend
npm install
npm run dev

---

## 7. API

- POST /documents/upload
- GET /documents
- GET /documents/{id}
- POST /documents/{id}/summarize
- POST /documents/{id}/ask

---

## 8. 설계

- Router / Service / Repository 분리
- DB 기반 상태 관리
- API 중심 구조

---

## 9. 한계

- OCR 없음
- 긴 문서 처리 제한
- 인증 없음

---

## 10. 버전

현재: 0.2.0

자세한 내용은 CHANGELOG.md 참고