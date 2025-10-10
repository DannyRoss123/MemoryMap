"""Task management endpoints for caregiver workflows."""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from sqlmodel import Session, select, SQLModel

from app.database import engine
from app.models import Task, Person

router = APIRouter(tags=["tasks"])


class TaskCreate(SQLModel):
    assigned_by: int
    title: str
    description: Optional[str] = None
    due_at: Optional[datetime] = None
    repeat: Optional[str] = None
    status: Optional[str] = None


class TaskUpdate(SQLModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_at: Optional[datetime] = None
    repeat: Optional[str] = None
    status: Optional[str] = None


def _require_person(session: Session, person_id: int) -> Person:
    person = session.get(Person, person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found.")
    return person


@router.post("/users/{user_id}/tasks", response_model=Task)
def create_task(user_id: int, payload: TaskCreate):
    with Session(engine) as session:
        _require_person(session, user_id)
        _require_person(session, payload.assigned_by)

        status = payload.status or "open"
        task = Task(
            user_id=user_id,
            assigned_by=payload.assigned_by,
            title=payload.title,
            description=payload.description,
            due_at=payload.due_at,
            repeat=payload.repeat,
            status=status,
        )
        session.add(task)
        session.commit()
        session.refresh(task)
        return task


@router.get("/users/{user_id}/tasks", response_model=List[Task])
def list_tasks(user_id: int, status: Optional[str] = None, limit: int = 100):
    with Session(engine) as session:
        _require_person(session, user_id)
        stmt = select(Task).where(Task.user_id == user_id).order_by(Task.created_at.desc())
        if status:
            stmt = stmt.where(Task.status == status)
        stmt = stmt.limit(limit)
        return session.exec(stmt).all()


@router.patch("/tasks/{task_id}", response_model=Task)
def update_task(task_id: int, payload: TaskUpdate):
    with Session(engine) as session:
        task = session.get(Task, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found.")

        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(task, field, value)

        session.add(task)
        session.commit()
        session.refresh(task)
        return task
