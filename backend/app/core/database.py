from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def init_db() -> None:
    """Creates database schema and performs schema migrations for SQLite."""
    Base.metadata.create_all(bind=engine)
    if "sqlite" in settings.DATABASE_URL:
        with engine.connect() as conn:
            try:
                result = conn.execute(text("PRAGMA table_info(audit_events)"))
                columns = [row[1] for row in result.fetchall()]
                if columns and "merchant_id" not in columns:
                    conn.execute(text("ALTER TABLE audit_events ADD COLUMN merchant_id VARCHAR(64) DEFAULT 'default'"))
                    conn.commit()
            except Exception:
                pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
