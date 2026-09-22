from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_user_or_404
from ..models import Goal, User
from ..schemas import GoalCreate, GoalOut, GoalUpdate

router = APIRouter(tags=["goals"])


def _get_goal_or_404(goal_id: int, db: Session) -> Goal:
    goal = db.get(Goal, goal_id)
    if goal is None:
        raise HTTPException(status_code=404, detail=f"Goal {goal_id} not found")
    return goal


@router.post("/users/{user_id}/goals", response_model=GoalOut, status_code=status.HTTP_201_CREATED)
def create_goal(body: GoalCreate, user: User = Depends(get_user_or_404), db: Session = Depends(get_db)):
    goal = Goal(user_id=user.id, **body.model_dump())
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


@router.get("/users/{user_id}/goals", response_model=list[GoalOut])
def list_goals(user: User = Depends(get_user_or_404), db: Session = Depends(get_db)):
    return db.scalars(select(Goal).where(Goal.user_id == user.id).order_by(Goal.id)).all()


@router.patch("/goals/{goal_id}", response_model=GoalOut)
def update_goal(goal_id: int, body: GoalUpdate, db: Session = Depends(get_db)):
    goal = _get_goal_or_404(goal_id, db)
    changes = body.model_dump(exclude_unset=True)  # only fields the client actually sent
    for field, value in changes.items():
        setattr(goal, field, value)
    if goal.saved_amount > goal.target_amount:
        raise HTTPException(status_code=422, detail="saved_amount cannot exceed target_amount")
    db.commit()
    db.refresh(goal)
    return goal


@router.delete("/goals/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(goal_id: int, db: Session = Depends(get_db)):
    db.delete(_get_goal_or_404(goal_id, db))
    db.commit()
