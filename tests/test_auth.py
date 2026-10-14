"""Login / password tests (added in Exercise 5)."""
from sqlalchemy import select

from app.models import User
from app.security import create_access_token

from .conftest import PASSWORD, TestingSession, signup_and_login


def test_signup_never_returns_password(client):
    r = client.post("/users", json={"name": "Srikar", "email": "srikar@example.com", "password": PASSWORD})
    assert r.status_code == 201
    body = r.json()
    assert "password" not in body and "password_hash" not in body


def test_password_is_hashed_in_database(client):
    signup_and_login(client, "Srikar", "srikar@example.com")
    with TestingSession() as db:
        stored = db.scalar(select(User.password_hash).where(User.email == "srikar@example.com"))
    assert stored != PASSWORD
    assert stored.startswith("$argon2")  # Argon2 hash format, includes its own salt


def test_short_password_rejected(client):
    r = client.post("/users", json={"name": "S", "email": "s@example.com", "password": "short"})
    assert r.status_code == 422


def test_login_returns_token(client):
    client.post("/users", json={"name": "Srikar", "email": "srikar@example.com", "password": PASSWORD})
    r = client.post("/auth/login", data={"username": "srikar@example.com", "password": PASSWORD})
    assert r.status_code == 200
    assert r.json()["token_type"] == "bearer" and r.json()["access_token"]


def test_login_email_is_case_insensitive(client):
    client.post("/users", json={"name": "Srikar", "email": "Srikar@Example.com", "password": PASSWORD})
    r = client.post("/auth/login", data={"username": "srikar@example.com", "password": PASSWORD})
    assert r.status_code == 200


def test_wrong_password_401(client):
    client.post("/users", json={"name": "Srikar", "email": "srikar@example.com", "password": PASSWORD})
    r = client.post("/auth/login", data={"username": "srikar@example.com", "password": "wrong-password"})
    assert r.status_code == 401


def test_unknown_email_gets_same_401_as_wrong_password(client):
    client.post("/users", json={"name": "Srikar", "email": "srikar@example.com", "password": PASSWORD})
    wrong_pw = client.post("/auth/login", data={"username": "srikar@example.com", "password": "nope-nope"})
    no_user = client.post("/auth/login", data={"username": "ghost@example.com", "password": "nope-nope"})
    assert wrong_pw.status_code == no_user.status_code == 401
    assert wrong_pw.json() == no_user.json()  # doesn't reveal which emails exist


def test_me_requires_token(client):
    assert client.get("/users/me").status_code == 401


def test_me_returns_logged_in_user(client):
    u, headers = signup_and_login(client, "Srikar", "srikar@example.com")
    r = client.get("/users/me", headers=headers)
    assert r.status_code == 200 and r.json()["id"] == u["id"]


def test_garbage_token_401(client):
    r = client.get("/users/me", headers={"Authorization": "Bearer not.a.real.token"})
    assert r.status_code == 401


def test_expired_token_401(client):
    u, _ = signup_and_login(client, "Srikar", "srikar@example.com")
    expired = create_access_token(u["id"], expires_minutes=-1)
    r = client.get("/users/me", headers={"Authorization": f"Bearer {expired}"})
    assert r.status_code == 401


def test_token_signed_with_other_key_401(client):
    import jwt
    u, _ = signup_and_login(client, "Srikar", "srikar@example.com")
    forged = jwt.encode({"sub": str(u["id"])}, "attacker-key", algorithm="HS256")
    r = client.get("/users/me", headers={"Authorization": f"Bearer {forged}"})
    assert r.status_code == 401
