"""Endpoints that power caregiver dashboards."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Literal, Set

from fastapi import APIRouter, HTTPException
from sqlmodel import Session, select, SQLModel, Field

from app.database import engine
from app.models import (
    Person,
    RoleEnum,
    CircleLink,
    LinkRoleEnum,
    Task,
    CheckIn,
    Alert,
    Memory,
)

router = APIRouter(prefix="/caregivers", tags=["caregivers"])


class ContactSummary(SQLModel):
    person: Person
    role: LinkRoleEnum
    relationship: Optional[str] = None
    can_edit: bool = False
    notify: bool = False


class ClientSummary(SQLModel):
    client: Person
    caregiver_role: LinkRoleEnum
    relationship: Optional[str] = None
    can_edit: bool = False
    notify: bool = False
    family: List[ContactSummary] = Field(default_factory=list)


class FeedItem(SQLModel):
    kind: Literal["memory", "task", "checkin", "alert"]
    source_id: int
    user_id: Optional[int] = None
    timestamp: datetime
    title: Optional[str] = None
    summary: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)


CAREGIVER_ROLES = {LinkRoleEnum.primary_caregiver, LinkRoleEnum.caregiver}
CONTACT_ROLES = {LinkRoleEnum.family, LinkRoleEnum.friend}


def _require_caregiver(session: Session, caregiver_id: int) -> Person:
    caregiver = session.get(Person, caregiver_id)
    if not caregiver or caregiver.role != RoleEnum.caregiver:
        raise HTTPException(status_code=404, detail="Caregiver not found.")
    return caregiver


def _caregiver_links(session: Session, caregiver_id: int) -> List[CircleLink]:
    stmt = select(CircleLink).where(
        CircleLink.member_id == caregiver_id,
        CircleLink.role.in_(CAREGIVER_ROLES),
    )
    return session.exec(stmt).all()


@router.get("/{caregiver_id}/profile", response_model=Person)
def get_profile(caregiver_id: int):
    with Session(engine) as session:
        return _require_caregiver(session, caregiver_id)


@router.get("/{caregiver_id}/clients", response_model=List[ClientSummary])
def list_clients(caregiver_id: int):
    with Session(engine) as session:
        caregiver = _require_caregiver(session, caregiver_id)
        links = _caregiver_links(session, caregiver.id)
        if not links:
            return []

        client_ids = {link.client_id for link in links}
        clients = session.exec(select(Person).where(Person.id.in_(client_ids))).all()
        client_map = {p.id: p for p in clients}

        results: List[ClientSummary] = []
        for link in links:
            client = client_map.get(link.client_id)
            if not client:
                continue

            # Fetch family/friends for this client
            contact_links = session.exec(
                select(CircleLink).where(
                    CircleLink.client_id == link.client_id,
                    CircleLink.member_id != caregiver.id,
                    CircleLink.role.in_(CONTACT_ROLES),
                )
            ).all()

            member_ids: Set[int] = {cl.member_id for cl in contact_links}
            members = (
                session.exec(select(Person).where(Person.id.in_(member_ids))).all()
                if member_ids
                else []
            )
            member_map = {m.id: m for m in members}

            family_contacts = [
                ContactSummary(
                    person=member_map[cl.member_id],
                    role=cl.role,
                    relationship=cl.relationship,
                    can_edit=cl.can_edit,
                    notify=cl.notify,
                )
                for cl in contact_links
                if cl.member_id in member_map
            ]

            results.append(
                ClientSummary(
                    client=client,
                    caregiver_role=link.role,
                    relationship=link.relationship,
                    can_edit=link.can_edit,
                    notify=link.notify,
                    family=family_contacts,
                )
            )
        return results


@router.get("/{caregiver_id}/updates", response_model=List[FeedItem])
def list_updates(caregiver_id: int, limit: int = 50):
    with Session(engine) as session:
        caregiver = _require_caregiver(session, caregiver_id)
        links = _caregiver_links(session, caregiver.id)
        if not links:
            return []

        client_ids = [link.client_id for link in links]
        now = datetime.utcnow()
        feed: List[FeedItem] = []

        # Tasks: include open/missed items
        task_stmt = (
            select(Task)
            .where(Task.user_id.in_(client_ids))
            .where(Task.status.in_(["open", "missed"]))
        )
        for task in session.exec(task_stmt):
            summary = task.description
            if task.due_at and task.due_at < now and task.status == "open":
                summary = (summary or "") + (" " if summary else "") + "Overdue."
            feed.append(
                FeedItem(
                    kind="task",
                    source_id=task.id,
                    user_id=task.user_id,
                    timestamp=task.due_at or task.created_at,
                    title=task.title,
                    summary=summary,
                    data=task.model_dump(),
                )
            )

        # Check-ins
        checkin_stmt = select(CheckIn).where(CheckIn.user_id.in_(client_ids))
        for checkin in session.exec(checkin_stmt):
            feed.append(
                FeedItem(
                    kind="checkin",
                    source_id=checkin.id,
                    user_id=checkin.user_id,
                    timestamp=checkin.created_at,
                    title=f"Check-in ({checkin.by})",
                    summary=checkin.notes,
                    data=checkin.model_dump(),
                )
            )

        # Alerts
        alert_stmt = select(Alert).where(Alert.caregiver_id == caregiver.id)
        for alert in session.exec(alert_stmt):
            feed.append(
                FeedItem(
                    kind="alert",
                    source_id=alert.id,
                    user_id=alert.user_id,
                    timestamp=alert.created_at,
                    title=alert.kind,
                    summary=alert.message,
                    data=alert.model_dump(),
                )
            )

        # Memories (best effort - Memory currently has no client scope)
        if hasattr(Memory, "user_id"):
            memory_stmt = select(Memory).where(Memory.user_id.in_(client_ids))
        else:
            memory_stmt = select(Memory)
        for memory in session.exec(memory_stmt):
            feed.append(
                FeedItem(
                    kind="memory",
                    source_id=memory.id,
                    user_id=getattr(memory, "user_id", None),
                    timestamp=memory.created_at,
                    title=memory.title,
                    summary=memory.note,
                    data=memory.model_dump(),
                )
            )

        feed.sort(key=lambda item: item.timestamp, reverse=True)
        return feed[:limit]


@router.post("/{caregiver_id}/links", response_model=ClientSummary)
def add_link(
    caregiver_id: int,
    client_id: int,
    relationship: Optional[str] = None,
    role: LinkRoleEnum = LinkRoleEnum.caregiver,
    can_edit: bool = False,
    notify: bool = False,
):
    with Session(engine) as session:
        caregiver = _require_caregiver(session, caregiver_id)
        client = session.get(Person, client_id)
        if not client or client.role != RoleEnum.user:
            raise HTTPException(status_code=404, detail="Client not found.")

        existing = session.exec(
            select(CircleLink).where(
                CircleLink.client_id == client_id,
                CircleLink.member_id == caregiver.id,
            )
        ).first()

        if existing:
            existing.relationship = relationship or existing.relationship
            existing.role = role
            existing.can_edit = can_edit
            existing.notify = notify
            link = existing
        else:
            link = CircleLink(
                client_id=client_id,
                member_id=caregiver.id,
                role=role,
                relationship=relationship,
                can_edit=can_edit,
                notify=notify,
            )
            session.add(link)

        session.commit()
        session.refresh(link)

        return ClientSummary(
            client=client,
            caregiver_role=link.role,
            relationship=link.relationship,
            can_edit=link.can_edit,
            notify=link.notify,
            family=[],
        )
