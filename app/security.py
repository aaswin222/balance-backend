from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from .config import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, SECRET_KEY

# Argon2 is the current OWASP-recommended password hash. Each hash has its own random salt,
# so two users with the same password still get different hashes.
password_hash = PasswordHash.recommended()

# Used when the email doesn't exist, so a wrong email takes as long as a wrong password
# (otherwise response time would reveal which emails are registered).
DUMMY_HASH = password_hash.hash("dummy-password-for-timing")


def hash_password(plain: str) -> str:
    return password_hash.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return password_hash.verify(plain, hashed)


def create_access_token(user_id: int, expires_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),  # "subject" = who this token belongs to
        "iat": now,           # issued at
        "exp": now + timedelta(minutes=expires_minutes),  # PyJWT rejects it after this
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> int:
    """Return the user id inside a valid token. Raises jwt.InvalidTokenError if the token
    is expired, tampered with, or signed with a different key."""
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    return int(payload["sub"])
