from pathlib import Path
from datetime import date, datetime
from typing import List, Optional, Tuple, Dict, Any
import sqlite3
from database.connection import get_connection
from models.schemas import (
    Transaction, TransactionCreate, TransactionUpdate,
    Budget, BudgetCreate,
    SavingsGoal, SavingsGoalCreate,
    cents_to_rupees, rupees_to_cents
)

class TransactionRepository:
    def __init__(self, db_path: Path | str | None = None):
        self.db_path = db_path

    def add(self, tx: TransactionCreate) -> int:
        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO transactions 
                    (transaction_date, transaction_type, amount_cents, category, description, payment_method, merchant, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
                    """,
                    (
                        tx.transaction_date.isoformat(),
                        tx.transaction_type,
                        tx.amount_cents,
                        tx.category,
                        tx.description or "",
                        tx.payment_method or "Other",
                        tx.merchant or "",
                    )
                )
                return cursor.lastrowid
        finally:
            conn.close()

    def update(self, tx: TransactionUpdate) -> bool:
        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE transactions
                    SET transaction_date = ?,
                        transaction_type = ?,
                        amount_cents = ?,
                        category = ?,
                        description = ?,
                        payment_method = ?,
                        merchant = ?,
                        updated_at = datetime('now')
                    WHERE id = ?
                    """,
                    (
                        tx.transaction_date.isoformat(),
                        tx.transaction_type,
                        tx.amount_cents,
                        tx.category,
                        tx.description or "",
                        tx.payment_method or "Other",
                        tx.merchant or "",
                        tx.id,
                    )
                )
                return cursor.rowcount > 0
        finally:
            conn.close()

    def delete(self, tx_id: int) -> bool:
        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM transactions WHERE id = ?", (tx_id,))
                return cursor.rowcount > 0
        finally:
            conn.close()

    def get_by_id(self, tx_id: int) -> Optional[Transaction]:
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM transactions WHERE id = ?", (tx_id,))
            row = cursor.fetchone()
            if row:
                return Transaction.from_row(row)
            return None
        finally:
            conn.close()

    def list(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        tx_type: Optional[str] = None,
        category: Optional[str] = None,
        payment_method: Optional[str] = None,
        search_query: Optional[str] = None,
        sort_by: str = "transaction_date",
        sort_order: str = "DESC",
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Transaction]:
        conn = get_connection(self.db_path)
        try:
            query = "SELECT * FROM transactions WHERE 1=1"
            params: list[Any] = []

            if start_date:
                query += " AND transaction_date >= ?"
                params.append(start_date.isoformat())
            if end_date:
                query += " AND transaction_date <= ?"
                params.append(end_date.isoformat())
            if tx_type and tx_type.lower() != "all":
                query += " AND transaction_type = ?"
                params.append(tx_type.lower())
            if category and category.lower() != "all":
                query += " AND category = ?"
                params.append(category)
            if payment_method and payment_method.lower() != "all":
                query += " AND payment_method = ?"
                params.append(payment_method)
            if search_query and search_query.strip():
                query += " AND (description LIKE ? OR merchant LIKE ?)"
                like_pat = f"%{search_query.strip()}%"
                params.extend([like_pat, like_pat])

            valid_cols = {"transaction_date", "amount_cents", "category", "created_at"}
            col = sort_by if sort_by in valid_cols else "transaction_date"
            order = "ASC" if sort_order.upper() == "ASC" else "DESC"
            query += f" ORDER BY {col} {order}, id DESC"

            if limit:
                query += " LIMIT ? OFFSET ?"
                params.extend([limit, offset])

            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [Transaction.from_row(row) for row in rows]
        finally:
            conn.close()

    def count(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        tx_type: Optional[str] = None,
        category: Optional[str] = None,
        payment_method: Optional[str] = None,
        search_query: Optional[str] = None,
    ) -> int:
        conn = get_connection(self.db_path)
        try:
            query = "SELECT COUNT(*) FROM transactions WHERE 1=1"
            params: list[Any] = []
            if start_date:
                query += " AND transaction_date >= ?"
                params.append(start_date.isoformat())
            if end_date:
                query += " AND transaction_date <= ?"
                params.append(end_date.isoformat())
            if tx_type and tx_type.lower() != "all":
                query += " AND transaction_type = ?"
                params.append(tx_type.lower())
            if category and category.lower() != "all":
                query += " AND category = ?"
                params.append(category)
            if payment_method and payment_method.lower() != "all":
                query += " AND payment_method = ?"
                params.append(payment_method)
            if search_query and search_query.strip():
                query += " AND (description LIKE ? OR merchant LIKE ?)"
                like_pat = f"%{search_query.strip()}%"
                params.extend([like_pat, like_pat])

            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchone()[0]
        finally:
            conn.close()

class BudgetRepository:
    def __init__(self, db_path: Path | str | None = None):
        self.db_path = db_path

    def add(self, budget: BudgetCreate) -> int:
        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO budgets 
                    (category, budget_amount_cents, period_type, start_date, end_date, created_at)
                    VALUES (?, ?, ?, ?, ?, datetime('now'))
                    """,
                    (
                        budget.category,
                        budget.budget_amount_cents,
                        budget.period_type,
                        budget.start_date.isoformat(),
                        budget.end_date.isoformat(),
                    )
                )
                return cursor.lastrowid
        finally:
            conn.close()

    def update(self, budget_id: int, budget_amount: float) -> bool:
        cents = rupees_to_cents(budget_amount)
        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE budgets SET budget_amount_cents = ? WHERE id = ?",
                    (cents, budget_id)
                )
                return cursor.rowcount > 0
        finally:
            conn.close()

    def delete(self, budget_id: int) -> bool:
        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM budgets WHERE id = ?", (budget_id,))
                return cursor.rowcount > 0
        finally:
            conn.close()

    def list_active(self, current_date: Optional[date] = None) -> List[Budget]:
        d = current_date or date.today()
        d_str = d.isoformat()
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM budgets 
                WHERE start_date <= ? AND end_date >= ?
                ORDER BY category ASC
                """,
                (d_str, d_str)
            )
            return [Budget.from_row(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def list_all(self) -> List[Budget]:
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM budgets ORDER BY start_date DESC, category ASC")
            return [Budget.from_row(row) for row in cursor.fetchall()]
        finally:
            conn.close()

class SavingsGoalRepository:
    def __init__(self, db_path: Path | str | None = None):
        self.db_path = db_path

    def add(self, goal: SavingsGoalCreate) -> int:
        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO savings_goals
                    (goal_name, target_amount_cents, current_amount_cents, target_date, description, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))
                    """,
                    (
                        goal.goal_name,
                        goal.target_amount_cents,
                        goal.current_amount_cents,
                        goal.target_date.isoformat(),
                        goal.description or "",
                    )
                )
                return cursor.lastrowid
        finally:
            conn.close()

    def update_progress(self, goal_id: int, new_current_amount: float) -> bool:
        cents = rupees_to_cents(new_current_amount)
        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE savings_goals
                    SET current_amount_cents = ?, updated_at = datetime('now')
                    WHERE id = ?
                    """,
                    (cents, goal_id)
                )
                return cursor.rowcount > 0
        finally:
            conn.close()

    def update_goal(self, goal_id: int, goal_name: str, target_amount: float, target_date: date, description: str) -> bool:
        target_cents = rupees_to_cents(target_amount)
        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE savings_goals
                    SET goal_name = ?, target_amount_cents = ?, target_date = ?, description = ?, updated_at = datetime('now')
                    WHERE id = ?
                    """,
                    (goal_name, target_cents, target_date.isoformat(), description, goal_id)
                )
                return cursor.rowcount > 0
        finally:
            conn.close()

    def delete(self, goal_id: int) -> bool:
        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM savings_goals WHERE id = ?", (goal_id,))
                return cursor.rowcount > 0
        finally:
            conn.close()

    def list_all(self) -> List[SavingsGoal]:
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM savings_goals ORDER BY target_date ASC")
            return [SavingsGoal.from_row(row) for row in cursor.fetchall()]
        finally:
            conn.close()

class SettingsRepository:
    def __init__(self, db_path: Path | str | None = None):
        self.db_path = db_path

    def get(self, key: str, default: str = "") -> str:
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM app_settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row[0] if row else default
        finally:
            conn.close()

    def set(self, key: str, value: str) -> None:
        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO app_settings (key, value, updated_at) 
                    VALUES (?, ?, datetime('now'))
                    ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
                    """,
                    (key, value)
                )
        finally:
            conn.close()

    def get_all(self) -> Dict[str, str]:
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM app_settings")
            return {row[0]: row[1] for row in cursor.fetchall()}
        finally:
            conn.close()
