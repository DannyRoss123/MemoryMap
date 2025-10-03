#Routes for working with memories 

from fastapi import APIRouter, HTTPException
from sqlmodel import Session, select
from app.database import engine
from app.models import Memory

router = APIRouter(prefix="/memories", tags=["memories"])

@router.get("")
def list_memories(limit: int = 50, offset: int = 0):
    with Session(engine) as session:
        stmt = select(Memory).order_by(Memory.timestamp.desc()).limit(limit).offset(offset)
        return session.exec(stmt).all()

@router.post("", response_model=Memory)
def create_memory(mem: Memory):
    if not mem.title:
        raise HTTPException(422, "title required")
    with Session(engine) as session:
        session.add(mem)
        session.commit()
        session.refresh(mem)
        return mem

@router.get("/{mid}", response_model=Memory)
def get_memory(mid: int):
    with Session(engine) as session:
        obj = session.get(Memory, mid)
        if not obj:
            raise HTTPException(404, "Not found")
        return obj
