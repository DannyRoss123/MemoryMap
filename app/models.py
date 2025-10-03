#describe tables and fields of database

from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field

class Memory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    body: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
