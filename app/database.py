import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Docker Compose injects this; the hostname "db" is the Postgres service name.
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+psycopg2://balance:balance@localhost:5432/balance"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    # One session per request, always closed -> no leaked connections.
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
