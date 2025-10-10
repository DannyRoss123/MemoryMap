"""Seed demo data for caregiver dashboard exploration."""

from datetime import datetime, timedelta
from typing import Optional

from sqlmodel import Session, select

from app.database import engine, init_db
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


def get_person_by_email(session: Session, email: Optional[str]) -> Optional[Person]:
    if not email:
        return None
    return session.exec(select(Person).where(Person.email == email)).first()


def ensure_person(
    session: Session,
    *,
    role: RoleEnum,
    name: str,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    avatar_url: Optional[str] = None,
) -> Person:
    person = get_person_by_email(session, email)
    if not person:
        person = Person(
            role=role,
            name=name,
            email=email,
            phone=phone,
            avatar_url=avatar_url,
        )
        session.add(person)
        session.commit()
        session.refresh(person)
    return person


def ensure_circle_link(
    session: Session,
    *,
    client_id: int,
    member_id: int,
    role: LinkRoleEnum,
    relationship: Optional[str] = None,
    can_edit: bool = False,
    notify: bool = False,
) -> CircleLink:
    link = session.exec(
        select(CircleLink).where(
            CircleLink.client_id == client_id,
            CircleLink.member_id == member_id,
        )
    ).first()

    if not link:
        link = CircleLink(
            client_id=client_id,
            member_id=member_id,
            role=role,
            relationship=relationship,
            can_edit=can_edit,
            notify=notify,
        )
        session.add(link)
    else:
        link.role = role
        link.relationship = relationship or link.relationship
        link.can_edit = can_edit
        link.notify = notify
        session.add(link)

    session.commit()
    session.refresh(link)
    return link


def seed():
    init_db()
    now = datetime.utcnow()

    with Session(engine) as session:
        caregiver = ensure_person(
            session,
            role=RoleEnum.caregiver,
            name="Dana Rivera",
            email="dana.caregiver@example.com",
            phone="+1-555-900-1111",
        )

        client_alex = ensure_person(
            session,
            role=RoleEnum.user,
            name="Alex Kim",
            email="alex.kim@example.com",
            phone="+1-555-200-1111",
            avatar_url=None,
        )
        client_alex.location = "Home suite - Room 204"
        session.add(client_alex)

        client_maria = ensure_person(
            session,
            role=RoleEnum.user,
            name="Maria Gonzales",
            email="maria.gonzales@example.com",
            phone="+1-555-200-2222",
            avatar_url=None,
        )
        client_maria.location = "Sunrise Assisted Living - Room 18B"
        session.add(client_maria)
        session.commit()

        family_sarah = ensure_person(
            session,
            role=RoleEnum.family,
            name="Sarah Kim",
            email="sarah.kim@example.com",
            phone="+1-555-440-3322",
        )

        family_omar = ensure_person(
            session,
            role=RoleEnum.family,
            name="Omar Gonzales",
            email="omar.gonzales@example.com",
            phone="+1-555-440-2211",
        )

        ensure_circle_link(
            session,
            client_id=client_alex.id,
            member_id=caregiver.id,
            role=LinkRoleEnum.primary_caregiver,
            relationship="Primary caregiver",
            can_edit=True,
            notify=True,
        )
        ensure_circle_link(
            session,
            client_id=client_maria.id,
            member_id=caregiver.id,
            role=LinkRoleEnum.caregiver,
            relationship="Visiting nurse",
            can_edit=True,
            notify=True,
        )
        ensure_circle_link(
            session,
            client_id=client_alex.id,
            member_id=family_sarah.id,
            role=LinkRoleEnum.family,
            relationship="Daughter",
            can_edit=False,
            notify=True,
        )
        ensure_circle_link(
            session,
            client_id=client_maria.id,
            member_id=family_omar.id,
            role=LinkRoleEnum.family,
            relationship="Nephew",
            can_edit=False,
            notify=True,
        )

        # Sample tasks
        if not session.exec(select(Task)).first():
            tasks = [
                Task(
                    user_id=client_alex.id,
                    assigned_by=caregiver.id,
                    title="Medication – morning vitamins",
                    description="Ensure Alex takes Vitamin D and B12.",
                    due_at=now + timedelta(hours=2),
                    status="open",
                ),
                Task(
                    user_id=client_maria.id,
                    assigned_by=caregiver.id,
                    title="Physiotherapy check-in",
                    description="Call Maria to confirm she did her stretching routine.",
                    due_at=now + timedelta(days=1),
                    status="open",
                ),
                Task(
                    user_id=client_alex.id,
                    assigned_by=caregiver.id,
                    title="Grocery restock",
                    description="Review pantry list after lunch.",
                    due_at=now - timedelta(hours=3),
                    status="missed",
                ),
            ]
            session.add_all(tasks)
            session.commit()

        # Sample check-ins
        if not session.exec(select(CheckIn)).first():
            checkins = [
                CheckIn(
                    user_id=client_alex.id,
                    by="caregiver",
                    mood="ok",
                    hydration="ok",
                    sleep_hours=7.5,
                    notes="Alex slept well and had breakfast.",
                    created_at=now - timedelta(hours=4),
                ),
                CheckIn(
                    user_id=client_maria.id,
                    by="family",
                    mood="happy",
                    hydration="high",
                    sleep_hours=8.0,
                    notes="Feeling energized after morning walk.",
                    created_at=now - timedelta(days=1, hours=1),
                ),
            ]
            session.add_all(checkins)
            session.commit()

        # Sample alerts
        if not session.exec(select(Alert)).first():
            alerts = [
                Alert(
                    user_id=client_alex.id,
                    caregiver_id=caregiver.id,
                    kind="missed_task",
                    message="Alex did not confirm the grocery restock.",
                    created_at=now - timedelta(hours=2),
                ),
                Alert(
                    user_id=client_maria.id,
                    caregiver_id=caregiver.id,
                    kind="custom",
                    message="Maria noted some knee discomfort yesterday.",
                    created_at=now - timedelta(days=1, hours=3),
                    is_read=True,
                ),
            ]
            session.add_all(alerts)
            session.commit()

        # Sample memory (global for now, until user_id is added)
        if not session.exec(select(Memory)).first():
            session.add(
                Memory(
                    title="Picnic in the park",
                    note="Alex and Dana enjoyed a sunny afternoon at the park.",
                    image_url=None,
                    occurred_at=now - timedelta(days=3),
                )
            )
            session.commit()

        print("Seeded caregiver demo data.")
        print(f"Caregiver ID: {caregiver.id}")
        print(f"Client IDs: {[client_alex.id, client_maria.id]}")
        print(f"Family contact IDs: {[family_sarah.id, family_omar.id]}")


if __name__ == "__main__":
    seed()
