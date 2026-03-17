from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.documents import router as documents_router

app = FastAPI(
    title="DocInsight AI",
    description="PDF 문서 업로드 후 텍스트 추출 및 AI 요약을 제공하는 서비스",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents_router)


@app.get("/")
def read_root():
    return {
        "message": "DocInsight AI 서버가 실행 중입니다.",
        "docs_url": "/docs",
    }