import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .database import get_db
from .models import User
from .security import decode_access_token

# Tells FastAPI (and the /docs "Authorize" button) that tokens come from POST /auth/login
# and are sent back as:  Authorization: Bearer <token>
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

CREDENTIALS_ERROR = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    # Missing header -> oauth2_scheme itself returns 401 before we get here.
    try:
        user_id = decode_access_token(token)
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise CREDENTIALS_ERROR  # expired, tampered, wrong key, or malformed
    user = db.get(User, user_id)
    if user is None:
        raise CREDENTIALS_ERROR  # token is valid but the account was deleted
    return user


def get_owned_user(user_id: int, current: User = Depends(get_current_user)) -> User:
    """Used by every /users/{user_id}/... route. Replaces the old get_user_or_404:
    instead of trusting whatever id is in the URL, the id must be the logged-in user's own."""
    if user_id != current.id:
        # 403 for any id that isn't yours, whether or not it exists,
        # so the API can't be used to probe which user ids are real.
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only access your own data")
    return current
