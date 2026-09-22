import enum
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint, Date, DateTime, Enum, ForeignKey, Numeric, String, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Category(str, enum.Enum):
    food = "food"
    transportation = "transportation"
    housing = "housing"
    entertainment = "entertainment"
    school = "school"
    other = "other"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # cascade: deleting a user deletes their goals/transactions (no orphans)
    goals: Mapped[list["Goal"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Goal(Base):
    __tablename__ = "goals"
    __table_args__ = (
        CheckConstraint("target_amount > 0", name="ck_goal_target_positive"),
        CheckConstraint("saved_amount >= 0", name="ck_goal_saved_nonneg"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    # Numeric, not float: money must be exact (0.1 + 0.2 != 0.3 in float)
    target_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    saved_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    deadline: Mapped[date | None] = mapped_column(Date, nullable=True)

    user: Mapped[User] = relationship(back_populates="goals")


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (CheckConstraint("amount > 0", name="ck_txn_amount_positive"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    category: Mapped[Category] = mapped_column(Enum(Category, name="category"))
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    occurred_on: Mapped[date] = mapped_column(Date, default=date.today)

    user: Mapped[User] = relationship(back_populates="transactions")
