import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Tests use their own DB so they never touch demo data.
# Default = throwaway SQLite file; set TEST_DATABASE_URL to run against Postgres.
TEST_URL = os.getenv("TEST_DATABASE_URL", "sqlite:///./test.db")
# app.database refuses to import without DATABASE_URL; point it at the test DB when run outside Docker.
os.environ.setdefault("DATABASE_URL", TEST_URL)
# app.config refuses to import without SECRET_KEY; tests use a throwaway one.
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-used-anywhere-real")

from app.database import Base, get_db  # noqa: E402  (must come after the env setup above)
from app.main import app  # noqa: E402

engine = create_engine(TEST_URL, connect_args={"check_same_thread": False} if TEST_URL.startswith("sqlite") else {})
TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)

PASSWORD = "correct-horse-battery"


def signup_and_login(client, name, email, password=PASSWORD):
    """Create an account, log in, and return (user_json, auth_headers)."""
    r = client.post("/users", json={"name": name, "email": email, "password": password})
    assert r.status_code == 201, r.text
    t = client.post("/auth/login", data={"username": email, "password": password})
    assert t.status_code == 200, t.text
    return r.json(), {"Authorization": f"Bearer {t.json()['access_token']}"}


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
    # Logged-in user: every request this client makes now carries their token,
    # so the original tests below work unchanged apart from this fixture.
    u, headers = signup_and_login(client, "Aishwarya", "aish@example.com")
    client.headers.update(headers)
    return u
