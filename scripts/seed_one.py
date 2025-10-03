from datetime import datetime, timedelta
from sqlmodel import Session
from app.database import engine, init_db
from app.models import Memory

def main():
    init_db()
    with Session(engine) as s:
        m = Memory(
            title="First Memory",
            note="Hello timeline!",
            image_url=None,
            occurred_at=datetime.utcnow() - timedelta(minutes=7),
        )
        s.add(m)
        s.commit()
        s.refresh(m)
        print("Inserted:", m)

if __name__ == "__main__":
    main()
