from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..schemas import Token
from ..security import DUMMY_HASH, create_access_token, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # OAuth2's standard form calls the field "username"; in Balance it's the email.
    user = db.scalar(select(User).where(User.email == form.username.strip().lower()))

    # Always run a hash check (against a dummy if the email is unknown) so the response
    # time doesn't reveal whether an email is registered.
    password_ok = verify_password(form.password, user.password_hash if user else DUMMY_HASH)

    if user is None or not password_ok:
        # Same message for "no such email" and "wrong password" on purpose.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(access_token=create_access_token(user.id), user_id=user.id)
