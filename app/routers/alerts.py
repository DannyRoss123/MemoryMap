"""Simple alert acknowledgment endpoints."""

from typing import List, Optional

from fastapi import APIRouter, HTTPException
from sqlmodel import Session, select, SQLModel

from app.database import engine
from app.models import Alert, Person

router = APIRouter(tags=["alerts"])


class AlertUpdate(SQLModel):
    is_read: Optional[bool] = None


def _require_person(session: Session, person_id: int) -> Person:
    person = session.get(Person, person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found.")
    return person


@router.get("/caregivers/{caregiver_id}/alerts", response_model=List[Alert])
def list_alerts(caregiver_id: int, only_unread: bool = False, limit: int = 100):
    with Session(engine) as session:
        _require_person(session, caregiver_id)
        stmt = (
            select(Alert)
            .where(Alert.caregiver_id == caregiver_id)
            .order_by(Alert.created_at.desc())
        )
        if only_unread:
            stmt = stmt.where(Alert.is_read.is_(False))
        stmt = stmt.limit(limit)
        return session.exec(stmt).all()


@router.patch("/alerts/{alert_id}", response_model=Alert)
def update_alert(alert_id: int, payload: AlertUpdate):
    with Session(engine) as session:
        alert = session.get(Alert, alert_id)
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found.")

        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(alert, field, value)

        session.add(alert)
        session.commit()
        session.refresh(alert)
        return alert
