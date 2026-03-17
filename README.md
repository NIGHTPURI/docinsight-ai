# DocInsight AI

PDF 문서를 업로드하면 텍스트를 추출하고, LLM을 활용해 핵심 내용을 요약하는 AI 백엔드 서비스입니다.

---

## 개발 배경

긴 문서를 빠르게 이해하기 어렵다는 문제를 해결하기 위해 이 프로젝트를 시작했습니다.  
특히 단순 요약이 아닌, 문서 내용을 기반으로 정보를 활용할 수 있는 AI 서비스 구조를 목표로 설계했습니다.

---

## 주요 기능

- PDF 파일 업로드
- PDF 텍스트 추출 (PyMuPDF)
- LLM 기반 문서 요약
- 문서 정보 조회 API 제공

---

## 기술 스택

- Backend: Python, FastAPI
- AI: OpenAI API (LLM)
- PDF 처리: PyMuPDF
- 환경 관리: Pydantic Settings
- 서버 실행: Uvicorn

---

## 시스템 구조

사용자  
→ PDF 업로드  
→ FastAPI 서버  
→ 텍스트 추출  
→ LLM 요약 요청  
→ 결과 반환  

---

## API 명세

### 1. 문서 업로드
POST /documents/upload  
PDF 파일 업로드 및 텍스트 추출

### 2. 문서 요약
POST /documents/{document_id}/summarize  
문서 내용을 기반으로 AI 요약 생성

### 3. 문서 조회
GET /documents/{document_id}  
문서 정보 및 요약 결과 조회

---

## 실행 방법

1. 가상환경 생성
python -m venv .venv

2. 가상환경 활성화
.venv\Scripts\activate

3. 패키지 설치
pip install -r requirements.txt

4. 환경 변수 설정 (.env 파일 생성)
OPENAI_API_KEY=your_api_key  
MODEL_NAME=gpt-4.1-mini  
UPLOAD_DIR=uploads  

5. 서버 실행
uvicorn app.main:app --reload

6. API 테스트
http://127.0.0.1:8000/docs

---

## 설계 포인트

- PDF 처리, AI 호출, API 로직을 서비스 단위로 분리
- FastAPI 기반으로 REST API 구조 설계
- 추후 문서 기반 질의응답(RAG) 확장이 가능하도록 구조 설계

---

## 한계 및 개선 방향

- 현재 인메모리 저장 구조 → DB 연동 필요
- 긴 문서 처리 시 chunking 전략 개선 필요
- 문서 기반 질의응답 기능 추가 가능
- 사용자 인증 및 문서 관리 기능 확장 가능

---

## 프로젝트 요약

DocInsight AI는 문서 이해를 자동화하기 위한 AI 기반 백엔드 서비스로  
PDF 처리와 LLM 연동을 통해 실무형 AI 서비스 구조를 구현하는 데 초점을 맞춘 프로젝트입니다.