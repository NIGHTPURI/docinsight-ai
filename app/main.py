from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.database import Base, engine
from app.config import settings
from app.routers.documents import router as documents_router
from app.upload_limit import UploadLimitMiddleware

@asynccontextmanager
async def lifespan(app):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title="DocInsight AI", lifespan=lifespan)
app.add_middleware(UploadLimitMiddleware, max_body_bytes=settings.max_upload_bytes + 64 * 1024)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents_router)


@app.get("/")
def root():
    return {"message": "DocInsight AI API is running"}
