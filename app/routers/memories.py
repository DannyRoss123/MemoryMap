#Routes for working with memories 
from typing import List
from datetime import datetime
from fastapi import APIRouter, HTTPException
from sqlmodel import Session, select
from app.database import engine
from app.models import Memory

router = APIRouter(prefix="/memories", tags=["memories"])

def _parse_iso_datetime(value):
    """
    Accept strings like '2025-10-02T22:19:00Z' or '...+00:00' and return datetime.
    If already a datetime, return as-is.
    """
    if isinstance(value, str):
        value = value.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(value)
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"Invalid occurred_at: {value}") from e
    return value

@router.get("", response_model=List[Memory])
def list_memories(limit: int = 200, offset: int = 0):
    with Session(engine) as session:
        stmt = (
            select(Memory)
            .order_by(Memory.occurred_at.desc(), Memory.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return session.exec(stmt).all()

@router.post("", response_model=Memory)
def create_memory(mem: Memory):
    if not mem.title:
        raise HTTPException(422, "title required")

    # Ensure datetime type for SQLite
    mem.occurred_at = _parse_iso_datetime(mem.occurred_at)

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

@router.put("/{mid}", response_model=Memory)
def update_memory(mid: int, payload: Memory):
    with Session(engine) as session:
        obj = session.get(Memory, mid)
        if not obj:
            raise HTTPException(404, "Not found")

        # Coerce occurred_at on update, too
        payload.occurred_at = _parse_iso_datetime(payload.occurred_at)

        obj.title = payload.title
        obj.note = payload.note
        obj.image_url = payload.image_url
        obj.occurred_at = payload.occurred_at

        session.add(obj)
        session.commit()
        session.refresh(obj)
        return obj

@router.delete("/{mid}")
def delete_memory(mid: int):
    with Session(engine) as session:
        obj = session.get(Memory, mid)
        if not obj:
            raise HTTPException(404, "Not found")
        session.delete(obj)
        session.commit()
        return {"ok": True}
