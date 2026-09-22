import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

# Tests use their own DB so they never touch demo data.
# Default = throwaway SQLite file; set TEST_DATABASE_URL to run against Postgres.
TEST_URL = os.getenv("TEST_DATABASE_URL", "sqlite:///./test.db")
engine = create_engine(TEST_URL, connect_args={"check_same_thread": False} if TEST_URL.startswith("sqlite") else {})
TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@pytest.fixture()
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)  # fresh schema per test = no cross-test leakage

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture()
def user(client):
    r = client.post("/users", json={"name": "Aishwarya", "email": "aish@example.com"})
    return r.json()
