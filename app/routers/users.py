from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, get_owned_user
from ..models import User
from ..schemas import UserCreate, UserOut
from ..security import hash_password

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(body: UserCreate, db: Session = Depends(get_db)):
    # Sign-up. Stays public: you need an account before you can log in.
    email = body.email.strip().lower()  # so "Srikar@X.com" and "srikar@x.com" are one account
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(name=body.name, email=email, password_hash=hash_password(body.password))
    db.add(user)
    db.commit()
    db.refresh(user)  # pull DB-generated id + created_at back into the object
    return user


# Must be declared BEFORE /{user_id}, or FastAPI would try to read "me" as an int id.
@router.get("/me", response_model=UserOut)
def read_me(current: User = Depends(get_current_user)):
    return current


@router.get("/{user_id}", response_model=UserOut)
def get_user(user: User = Depends(get_owned_user)):
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user: User = Depends(get_owned_user), db: Session = Depends(get_db)):
    db.delete(user)
    db.commit()
