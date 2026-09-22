from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from .models import Category


# ---------- Users ----------
class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: EmailStr
    created_at: datetime


# ---------- Goals ----------
class GoalCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    target_amount: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    saved_amount: Decimal = Field(default=Decimal("0"), ge=0, max_digits=10, decimal_places=2)
    deadline: date | None = None

    @model_validator(mode="after")
    def saved_not_over_target(self):
        if self.saved_amount > self.target_amount:
            raise ValueError("saved_amount cannot exceed target_amount")
        return self


class GoalUpdate(BaseModel):
    # All optional -> PATCH semantics (only send what changes)
    name: str | None = Field(default=None, min_length=1, max_length=100)
    target_amount: Decimal | None = Field(default=None, gt=0, max_digits=10, decimal_places=2)
    saved_amount: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    deadline: date | None = None


class GoalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    name: str
    target_amount: Decimal
    saved_amount: Decimal
    deadline: date | None
    progress_pct: float = 0.0

    @model_validator(mode="after")
    def compute_progress(self):
        self.progress_pct = round(float(self.saved_amount / self.target_amount * 100), 1)
        return self


# ---------- Transactions ----------
class TransactionCreate(BaseModel):
    amount: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    category: Category
    description: str | None = Field(default=None, max_length=255)
    occurred_on: date | None = None


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    amount: Decimal
    category: Category
    description: str | None
    occurred_on: date


# ---------- Summary ----------
class CategoryTotal(BaseModel):
    category: Category
    total: Decimal
    count: int


class SpendingSummary(BaseModel):
    user_id: int
    start: date | None
    end: date | None
    by_category: list[CategoryTotal]
    total_spending: Decimal
