from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_user_or_404
from ..models import Category, Transaction, User
from ..schemas import CategoryTotal, SpendingSummary, TransactionCreate, TransactionOut

router = APIRouter(prefix="/users/{user_id}", tags=["transactions"])


@router.post("/transactions", response_model=TransactionOut, status_code=status.HTTP_201_CREATED)
def create_transaction(body: TransactionCreate, user: User = Depends(get_user_or_404), db: Session = Depends(get_db)):
    data = body.model_dump(exclude_none=True)  # let DB default fill occurred_on if omitted
    txn = Transaction(user_id=user.id, **data)
    db.add(txn)
    db.commit()
    db.refresh(txn)
    return txn


@router.get("/transactions", response_model=list[TransactionOut])
def list_transactions(
    user: User = Depends(get_user_or_404),
    db: Session = Depends(get_db),
    category: Category | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    stmt = select(Transaction).where(Transaction.user_id == user.id)
    if category:
        stmt = stmt.where(Transaction.category == category)
    stmt = stmt.order_by(Transaction.occurred_on.desc(), Transaction.id.desc()).limit(limit).offset(offset)
    return db.scalars(stmt).all()


@router.get("/spending-summary", response_model=SpendingSummary)
def spending_summary(
    user: User = Depends(get_user_or_404),
    db: Session = Depends(get_db),
    start: date | None = None,
    end: date | None = None,
):
    if start and end and start > end:
        raise HTTPException(status_code=422, detail="start must be on or before end")

    # SELECT category, SUM(amount), COUNT(*) FROM transactions
    # WHERE user_id = :id [AND date range] GROUP BY category
    stmt = (
        select(Transaction.category, func.sum(Transaction.amount), func.count(Transaction.id))
        .where(Transaction.user_id == user.id)
        .group_by(Transaction.category)
        .order_by(func.sum(Transaction.amount).desc())
    )
    if start:
        stmt = stmt.where(Transaction.occurred_on >= start)
    if end:
        stmt = stmt.where(Transaction.occurred_on <= end)

    rows = db.execute(stmt).all()
    by_cat = [CategoryTotal(category=c, total=Decimal(t).quantize(Decimal("0.01")), count=n) for c, t, n in rows]
    total = sum((r.total for r in by_cat), Decimal("0.00"))
    return SpendingSummary(user_id=user.id, start=start, end=end, by_category=by_cat, total_spending=total)
