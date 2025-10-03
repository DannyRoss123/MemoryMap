##Entry point for API 

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import init_db
from app.routers import health, memories

app = FastAPI(title="MemoryMap (Day 1)")

# allow same-origin local usage; expand later if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# serve /static for the tiny frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
def _startup():
    init_db()

app.include_router(health.router)
app.include_router(memories.router)

