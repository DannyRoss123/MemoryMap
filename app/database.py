##Initial Database setup 

from sqlmodel import SQLModel, create_engine
import os
from dotenv import load_dotenv

load_dotenv()
#using sqllite right now for simplicity
DB_URL = os.getenv("DB_URL", "sqlite:///./memorymap.db")
engine = create_engine(DB_URL, echo=False)

def init_db():
    SQLModel.metadata.create_all(engine)
