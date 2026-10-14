import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Docker Compose builds this from .env; the hostname "db" is the Postgres service name.
# No fallback with a password in it: if it's missing, fail loudly instead.
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set. Copy .env.example to .env and run via docker compose.")

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
