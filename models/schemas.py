from datetime import datetime, date
from decimal import Decimal
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator

def rupees_to_cents(amount: float | Decimal | int) -> int:
    return int(round(float(amount) * 100))

def cents_to_rupees(cents: int) -> float:
    return round(cents / 100.0, 2)

class TransactionBase(BaseModel):
    transaction_date: date
    transaction_type: Literal["income", "expense"]
    amount: float = Field(gt=0, description="Amount in major currency unit")
    category: str = Field(min_length=1, max_length=100)
    description: Optional[str] = Field(default="", max_length=500)
    payment_method: str = Field(default="UPI", max_length=50)
    merchant: Optional[str] = Field(default="", max_length=100)

    @field_validator("description", "merchant", mode="before")
    @classmethod
    def default_empty_str(cls, v):
        return v if v is not None else ""

    @property
    def amount_cents(self) -> int:
        return rupees_to_cents(self.amount)

class TransactionCreate(TransactionBase):
    pass

class TransactionUpdate(TransactionBase):
    id: int

class Transaction(TransactionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_row(cls, row) -> "Transaction":
        return cls(
            id=row["id"],
            transaction_date=datetime.strptime(row["transaction_date"], "%Y-%m-%d").date()
            if isinstance(row["transaction_date"], str) else row["transaction_date"],
            transaction_type=row["transaction_type"],
            amount=cents_to_rupees(row["amount_cents"]),
            category=row["category"],
            description=row["description"] or "",
            payment_method=row["payment_method"] or "Other",
            merchant=row["merchant"] or "",
            created_at=datetime.fromisoformat(row["created_at"]) if isinstance(row["created_at"], str) else row["created_at"],
            updated_at=datetime.fromisoformat(row["updated_at"]) if isinstance(row["updated_at"], str) else row["updated_at"],
        )

class BudgetBase(BaseModel):
    category: str = Field(min_length=1, max_length=100)
    budget_amount: float = Field(gt=0)
    period_type: Literal["monthly", "custom"] = "monthly"
    start_date: date
    end_date: date

    @property
    def budget_amount_cents(self) -> int:
        return rupees_to_cents(self.budget_amount)

class BudgetCreate(BudgetBase):
    pass

class Budget(BudgetBase):
    id: int
    created_at: datetime

    @classmethod
    def from_row(cls, row) -> "Budget":
        return cls(
            id=row["id"],
            category=row["category"],
            budget_amount=cents_to_rupees(row["budget_amount_cents"]),
            period_type=row["period_type"],
            start_date=datetime.strptime(row["start_date"], "%Y-%m-%d").date()
            if isinstance(row["start_date"], str) else row["start_date"],
            end_date=datetime.strptime(row["end_date"], "%Y-%m-%d").date()
            if isinstance(row["end_date"], str) else row["end_date"],
            created_at=datetime.fromisoformat(row["created_at"]) if isinstance(row["created_at"], str) else row["created_at"],
        )

class SavingsGoalBase(BaseModel):
    goal_name: str = Field(min_length=1, max_length=150)
    target_amount: float = Field(gt=0)
    current_amount: float = Field(ge=0, default=0.0)
    target_date: date
    description: Optional[str] = Field(default="", max_length=500)

    @field_validator("description", mode="before")
    @classmethod
    def default_desc(cls, v):
        return v if v is not None else ""

    @property
    def target_amount_cents(self) -> int:
        return rupees_to_cents(self.target_amount)

    @property
    def current_amount_cents(self) -> int:
        return rupees_to_cents(self.current_amount)

class SavingsGoalCreate(SavingsGoalBase):
    pass

class SavingsGoal(SavingsGoalBase):
    id: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_row(cls, row) -> "SavingsGoal":
        return cls(
            id=row["id"],
            goal_name=row["goal_name"],
            target_amount=cents_to_rupees(row["target_amount_cents"]),
            current_amount=cents_to_rupees(row["current_amount_cents"]),
            target_date=datetime.strptime(row["target_date"], "%Y-%m-%d").date()
            if isinstance(row["target_date"], str) else row["target_date"],
            description=row["description"] or "",
            created_at=datetime.fromisoformat(row["created_at"]) if isinstance(row["created_at"], str) else row["created_at"],
            updated_at=datetime.fromisoformat(row["updated_at"]) if isinstance(row["updated_at"], str) else row["updated_at"],
        )

class AppSetting(BaseModel):
    key: str
    value: str
