"""Daily wellness check-in endpoints."""

from typing import List, Optional

from fastapi import APIRouter, HTTPException
from sqlmodel import Session, select, SQLModel

from app.database import engine
from app.models import CheckIn, Person

router = APIRouter(tags=["checkins"])


class CheckInCreate(SQLModel):
    by: Optional[str] = "caregiver"
    mood: Optional[str] = None
    sleep_hours: Optional[float] = None
    hydration: Optional[str] = None
    notes: Optional[str] = None


def _require_person(session: Session, person_id: int) -> Person:
    person = session.get(Person, person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found.")
    return person


@router.post("/users/{user_id}/checkins", response_model=CheckIn)
def create_checkin(user_id: int, payload: CheckInCreate):
    with Session(engine) as session:
        _require_person(session, user_id)
        checkin = CheckIn(
            user_id=user_id,
            by=payload.by or "caregiver",
            mood=payload.mood,
            sleep_hours=payload.sleep_hours,
            hydration=payload.hydration,
            notes=payload.notes,
        )
        session.add(checkin)
        session.commit()
        session.refresh(checkin)
        return checkin


@router.get("/users/{user_id}/checkins", response_model=List[CheckIn])
def list_checkins(user_id: int, limit: int = 30):
    with Session(engine) as session:
        _require_person(session, user_id)
        stmt = (
            select(CheckIn)
            .where(CheckIn.user_id == user_id)
            .order_by(CheckIn.created_at.desc())
            .limit(limit)
        )
        return session.exec(stmt).all()
