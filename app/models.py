#describe tables and fields of database

from typing import Optional
from enum import Enum
from datetime import datetime
from sqlmodel import SQLModel, Field


class RoleEnum(str, Enum):
    user = "user"
    caregiver = "caregiver"
    family = "family"
    admin = "admin"


class LinkRoleEnum(str, Enum):
    primary_caregiver = "primary_caregiver"
    caregiver = "caregiver"
    family = "family"
    friend = "friend"


class Person(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    role: RoleEnum = Field(default=RoleEnum.user)
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CircleLink(SQLModel, table=True):
    """Connects a client to someone in their circle (caregivers, family, friends)."""

    id: Optional[int] = Field(default=None, primary_key=True)
    client_id: int = Field(foreign_key="person.id")
    member_id: int = Field(foreign_key="person.id")
    role: LinkRoleEnum = Field(default=LinkRoleEnum.caregiver)
    relationship: Optional[str] = None
    can_edit: bool = Field(default=False)
    notify: bool = Field(default=False)

class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="person.id")
    assigned_by: int = Field(foreign_key="person.id")
    title: str
    description: Optional[str] = None
    due_at: Optional[datetime] = None
    repeat: Optional[str] = None  # none|daily|weekly
    status: str = Field(default="open")  # open|done|missed
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CheckIn(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="person.id")
    by: str = Field(default="caregiver")
    mood: Optional[str] = None  # happy|ok|sad
    sleep_hours: Optional[float] = None
    hydration: Optional[str] = None  # low|ok|high
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Alert(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="person.id")
    caregiver_id: int = Field(foreign_key="person.id")
    kind: str  # inactivity|missed_task|custom
    message: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_read: bool = Field(default=False)

class Memory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    # Content
    title: str
    note: Optional[str] = None
    image_url: Optional[str] = None  # e.g., "/uploads/xxxx.jpg"

    # When it happened (client-provided)
    occurred_at: datetime = Field(default_factory=datetime.utcnow)

    # When the record was created (server-side)
    created_at: datetime = Field(default_factory=datetime.utcnow)
