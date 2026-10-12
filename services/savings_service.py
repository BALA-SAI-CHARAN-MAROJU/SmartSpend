from pathlib import Path
from datetime import date
from typing import List, Dict, Any, Optional
from database.repositories import SavingsGoalRepository
from models.schemas import SavingsGoal, SavingsGoalCreate

class SavingsService:
    def __init__(self, db_path: Path | str | None = None):
        self.repo = SavingsGoalRepository(db_path)

    def add_goal(self, goal: SavingsGoalCreate) -> int:
        return self.repo.add(goal)

    def update_progress(self, goal_id: int, new_amount: float) -> bool:
        return self.repo.update_progress(goal_id, new_amount)

    def update_goal(self, goal_id: int, goal_name: str, target_amount: float, target_date: date, description: str) -> bool:
        return self.repo.update_goal(goal_id, goal_name, target_amount, target_date, description)

    def delete_goal(self, goal_id: int) -> bool:
        return self.repo.delete(goal_id)

    def get_goals(self) -> List[Dict[str, Any]]:
        raw_goals = self.repo.list_all()
        today = date.today()
        results = []

        for g in raw_goals:
            progress_pct = (g.current_amount / g.target_amount * 100.0) if g.target_amount > 0 else 0.0
            remaining_amount = max(0.0, g.target_amount - g.current_amount)
            days_remaining = (g.target_date - today).days

            if days_remaining > 0 and remaining_amount > 0:
                daily_required = remaining_amount / days_remaining
                monthly_required = daily_required * 30.4
            else:
                daily_required = 0.0
                monthly_required = 0.0

            is_completed = g.current_amount >= g.target_amount

            results.append({
                "id": g.id,
                "goal_name": g.goal_name,
                "target_amount": g.target_amount,
                "current_amount": g.current_amount,
                "remaining_amount": round(remaining_amount, 2),
                "target_date": g.target_date,
                "description": g.description,
                "progress_pct": min(100.0, round(progress_pct, 1)),
                "days_remaining": days_remaining,
                "daily_required": round(daily_required, 2),
                "monthly_required": round(monthly_required, 2),
                "is_completed": is_completed,
            })

        return results
