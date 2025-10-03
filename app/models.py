#describe tables and fields of database

from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field

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
