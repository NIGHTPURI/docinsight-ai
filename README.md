# DocInsight AI

PDF 문서를 업로드하면 텍스트를 추출하고, AI를 활용해 요약 및 문서 기반 질문 응답을 제공하는 서비스입니다.

AI 기능은 OpenAI 모델 **API 연동**으로 구현했습니다. 모델을 직접 학습하거나 파인튜닝하지 않으며, embedding 검색·vector DB를 사용하는 RAG는 구현하지 않았습니다.

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
- 결과 저장 및 이미 생성된 요약 재사용

### 문서 질문 응답
- 문서 기반 질문
- AI 답변 생성
- 질문·답변 DB 저장과 이력 조회 API (현재 React UI에는 별도 이력 화면 없음)

### 문서 관리
- 문서 목록 조회
- 상세 조회
- 상태 관리

---

## 3. 아키텍처

```text
React → FastAPI Router
         ├─ PDF Service → 파일 저장 / PyMuPDF 텍스트 추출
         ├─ AI Service  → 문서 앞 12,000자 → OpenAI API
         └─ Repository → SQLAlchemy → SQLite (문서 / 요약 / 질문·답변)
```

업로드는 파일 저장·텍스트 추출·DB 저장을 수행합니다. 요약과 질문은 별도 요청으로 처리하며, 업로드 실패 시 저장한 파일을 정리합니다.

### 기술적 선택

- [Router](app/routers/documents.py) / [Service](app/services/ai_service.py) / [Repository](app/repositories/document_repository.py)를 나누어 HTTP 요청, 외부 API 호출, 데이터 저장의 책임을 구분했습니다.
- SQLite와 SQLAlchemy로 문서와 질문 이력을 영속화했습니다. 인메모리에서 DB로 변경한 과정은 [CHANGELOG](CHANGELOG.md)에 기록되어 있습니다.
- PyMuPDF로 PDF의 텍스트를 추출합니다. OCR 처리는 없으므로 텍스트 없는 스캔 문서는 처리하지 못합니다.
- 모델 입력은 추출한 텍스트의 앞 12,000자로 제한합니다. 간단한 입력 제한이며 긴 문서 전체에서 관련 부분을 검색하는 방식은 아닙니다.

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

```text
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
```

---

## 6. 검증 근거와 범위

구현 근거는 [문서 API](app/routers/documents.py), [PDF 처리](app/services/pdf_service.py), [AI 호출](app/services/ai_service.py), [DB 모델](app/models.py), [React UI](frontend/src/App.jsx)에서 확인할 수 있습니다. 자동 테스트와 평가 데이터셋·품질 지표는 저장소에 마련되어 있지 않습니다.

2026-10-01 문서 정리에서는 **실행 검증 미수행**입니다. 서버 시작, DB 변경, PDF 업로드, 유료 API 호출을 실행하지 않았습니다. 요약·답변의 정확도나 학습·검증·테스트 점수, Public / Private Leaderboard 성적을 제시하는 프로젝트가 아닙니다.

## 7. 실행 방법

Python 가상환경과 Node.js/npm이 필요합니다. 아래는 사용자가 로컬에서 실행할 절차이며, 요약·질문 요청은 문서 내용을 외부 API로 보내고 비용을 발생시킬 수 있습니다. 공개 가능한 샘플 문서로 확인하세요.

### Backend

저장소 루트에서 가상환경을 만든 뒤 운영체제에 맞게 활성화합니다.

```bash
python -m venv .venv
```

Linux / WSL / macOS:

```bash
source .venv/bin/activate
cp .env.example .env
```

Windows 명령 프롬프트:

```bat
.venv\Scripts\activate
copy .env.example .env
```

`.env`를 로컬에서 편집합니다. 모델명은 현재 코드의 기본 설정이며 사용 가능한 모델은 실행 환경에서 확인해야 합니다. 키를 README나 Git에 넣지 마세요.

```dotenv
OPENAI_API_KEY=your_api_key
MODEL_NAME=gpt-4.1-mini
UPLOAD_DIR=uploads
DATABASE_URL=sqlite:///./docinsight.db
```

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --reload-dir app
```

API 문서는 실행 후 `http://127.0.0.1:8000/docs`에서 확인합니다. 서버 시작 시 DB 테이블을 생성하며, 기본 `docinsight.db`와 `uploads/`에는 문서·질문·답변 및 업로드 파일이 저장됩니다. 사용 중 생긴 실제 데이터는 공유하거나 commit하지 마세요. 기존 DB 파일은 저장소에 포함되어 있으므로 로컬 실행 후 변경 여부를 확인해야 합니다.

---

### Frontend

별도 터미널에서 실행합니다.

```bash
cd frontend
npm install
npm run dev
```

Vite가 출력하는 로컬 주소를 엽니다. 현재 UI의 API 주소는 `http://127.0.0.1:8000`으로 지정되어 있습니다.

---

## 8. API

| Method | Path | 동작 |
|---|---|---|
| POST | `/documents/upload` | PDF 업로드·텍스트 추출·저장 |
| GET | `/documents` | 문서 목록 |
| GET | `/documents/{document_id}` | 문서 상세 |
| POST | `/documents/{document_id}/summarize` | 요약 생성 또는 기존 요약 반환 |
| POST | `/documents/{document_id}/ask` | 질문 응답과 이력 저장 |
| GET | `/documents/{document_id}/questions` | 저장된 질문·답변 이력 |

---

## 9. 한계

- OCR 없음
- 긴 문서 처리 제한: 앞 12,000자 이후의 내용은 모델 입력에 포함되지 않음
- 문서 기반 답변을 요구하는 prompt만 사용하므로 답변의 근거 일치·정확성을 보장하지 않음
- 인증과 업로드 파일 크기 제한 없음
- 외부 API 비용·장애에 의존하며 별도 비동기 작업 queue 없음
- 문서 삭제 API와 질문 이력 UI 개선은 향후 작업

---

## 10. 버전

현재: 0.2.0

자세한 내용은 [CHANGELOG.md](CHANGELOG.md)를 참고하세요. 현재 저장소에는 별도 라이선스 파일이 없습니다.
