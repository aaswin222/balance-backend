import os

# All secrets come from environment variables (Docker Compose loads them from .env).
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is not set. Copy .env.example to .env and fill it in.")

ALGORITHM = "HS256"  # HMAC-SHA256: the same secret signs and verifies the token
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
