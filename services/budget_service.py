from pathlib import Path
from datetime import date
from typing import List, Dict, Any, Optional
from database.repositories import BudgetRepository, TransactionRepository
from models.schemas import Budget, BudgetCreate, cents_to_rupees, rupees_to_cents
import config

class BudgetService:
    def __init__(self, db_path: Path | str | None = None):
        self.budget_repo = BudgetRepository(db_path)
        self.tx_repo = TransactionRepository(db_path)

    def set_budget(self, budget_create: BudgetCreate) -> int:
        return self.budget_repo.add(budget_create)

    def delete_budget(self, budget_id: int) -> bool:
        return self.budget_repo.delete(budget_id)

    def get_budgets(self) -> List[Budget]:
        return self.budget_repo.list_all()

    def get_budget_status(self, current_date: Optional[date] = None) -> List[Dict[str, Any]]:
        today = current_date or date.today()
        active_budgets = self.budget_repo.list_active(today)
        statuses = []

        for b in active_budgets:
            txs = self.tx_repo.list(
                start_date=b.start_date,
                end_date=b.end_date,
                tx_type="expense",
                category=b.category if b.category.lower() != "overall" else None
            )
            total_spent = sum(t.amount for t in txs)
            remaining = b.budget_amount - total_spent
            utilization_pct = (total_spent / b.budget_amount * 100.0) if b.budget_amount > 0 else 0.0

            if utilization_pct >= 100.0:
                alert_level = "exceeded"
            elif utilization_pct >= config.BUDGET_CRITICAL_THRESHOLD * 100:
                alert_level = "critical"
            elif utilization_pct >= config.BUDGET_WARNING_THRESHOLD * 100:
                alert_level = "warning"
            else:
                alert_level = "normal"

            statuses.append({
                "budget_id": b.id,
                "category": b.category,
                "period_type": b.period_type,
                "start_date": b.start_date,
                "end_date": b.end_date,
                "budget_amount": b.budget_amount,
                "total_spent": round(total_spent, 2),
                "remaining": round(remaining, 2),
                "utilization_pct": round(utilization_pct, 1),
                "alert_level": alert_level,
                "transaction_count": len(txs)
            })

        return statuses
