from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_user_or_404
from ..models import User
from ..schemas import UserCreate, UserOut

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(body: UserCreate, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.email == body.email)):
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(**body.model_dump())
    db.add(user)
    db.commit()
    db.refresh(user)  # pull DB-generated id + created_at back into the object
    return user


@router.get("/{user_id}", response_model=UserOut)
def get_user(user: User = Depends(get_user_or_404)):
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user: User = Depends(get_user_or_404), db: Session = Depends(get_db)):
    db.delete(user)
    db.commit()
