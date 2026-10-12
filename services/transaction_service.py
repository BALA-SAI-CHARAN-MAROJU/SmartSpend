from pathlib import Path
from datetime import date
from typing import List, Optional, Tuple, Dict, Any
import pandas as pd
from models.schemas import Transaction, TransactionCreate, TransactionUpdate
from database.repositories import TransactionRepository
import config

class TransactionService:
    def __init__(self, db_path: Path | str | None = None):
        self.repo = TransactionRepository(db_path)

    def add_transaction(self, tx: TransactionCreate) -> int:
        return self.repo.add(tx)

    def update_transaction(self, tx: TransactionUpdate) -> bool:
        return self.repo.update(tx)

    def delete_transaction(self, tx_id: int) -> bool:
        return self.repo.delete(tx_id)

    def get_transaction(self, tx_id: int) -> Optional[Transaction]:
        return self.repo.get_by_id(tx_id)

    def get_transactions(
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
        return self.repo.list(
            start_date=start_date,
            end_date=end_date,
            tx_type=tx_type,
            category=category,
            payment_method=payment_method,
            search_query=search_query,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset
        )

    def count_transactions(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        tx_type: Optional[str] = None,
        category: Optional[str] = None,
        payment_method: Optional[str] = None,
        search_query: Optional[str] = None,
    ) -> int:
        return self.repo.count(
            start_date=start_date,
            end_date=end_date,
            tx_type=tx_type,
            category=category,
            payment_method=payment_method,
            search_query=search_query,
        )

    def get_as_dataframe(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        tx_type: Optional[str] = None
    ) -> pd.DataFrame:
        txs = self.get_transactions(start_date=start_date, end_date=end_date, tx_type=tx_type)
        if not txs:
            return pd.DataFrame(columns=[
                "id", "date", "type", "amount", "category", "description", "payment_method", "merchant"
            ])
        data = [
            {
                "id": t.id,
                "date": pd.to_datetime(t.transaction_date),
                "type": t.transaction_type,
                "amount": t.amount,
                "category": t.category,
                "description": t.description,
                "payment_method": t.payment_method,
                "merchant": t.merchant
            }
            for t in txs
        ]
        df = pd.DataFrame(data)
        return df.sort_values(by="date", ascending=True)

    def get_summary_metrics(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, float]:
        txs = self.get_transactions(start_date=start_date, end_date=end_date)
        total_income = sum(t.amount for t in txs if t.transaction_type == "income")
        total_expenses = sum(t.amount for t in txs if t.transaction_type == "expense")
        net_savings = total_income - total_expenses
        savings_rate = (net_savings / total_income * 100.0) if total_income > 0 else 0.0

        return {
            "total_income": round(total_income, 2),
            "total_expenses": round(total_expenses, 2),
            "net_savings": round(net_savings, 2),
            "savings_rate": round(savings_rate, 1),
            "transaction_count": len(txs)
        }
