from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import Base, engine
from .routes.videos import router as videos_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Fourthuman VideoQC API",
    description="Video intake, automated quality checks and human review workflow.",
    version="1.0.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(videos_router)

@app.get("/health")
def health():
    return {"status": "ok", "service": "Fourthuman VideoQC"}
