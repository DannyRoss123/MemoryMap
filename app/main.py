##Entry point for API 
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import init_db
from app.routers import (
    health,
    memories,
    upload,
    caregivers,
    tasks,
    checkins,
    alerts,
)

app = FastAPI(title="MemoryMap")

# CORS (adjust if you use a different origin)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static site + uploads
app.mount("/static", StaticFiles(directory="static"), name="static")
Path("uploads").mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.on_event("startup")
def _startup():
    init_db()

# Routes
app.include_router(health.router)
app.include_router(memories.router)
app.include_router(upload.router)
app.include_router(caregivers.router)
app.include_router(tasks.router)
app.include_router(checkins.router)
app.include_router(alerts.router)
