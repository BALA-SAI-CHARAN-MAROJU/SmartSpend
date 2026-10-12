from pathlib import Path
from datetime import date
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from services.transaction_service import TransactionService

class AnalyticsService:
    def __init__(self, db_path: Path | str | None = None):
        self.tx_service = TransactionService(db_path)

    def get_spending_by_category(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        tx_type: str = "expense"
    ) -> pd.DataFrame:
        df = self.tx_service.get_as_dataframe(start_date=start_date, end_date=end_date, tx_type=tx_type)
        if df.empty:
            return pd.DataFrame(columns=["category", "total_amount", "percentage", "count"])
        
        agg = df.groupby("category").agg(
            total_amount=("amount", "sum"),
            count=("id", "count")
        ).reset_index()
        total_sum = agg["total_amount"].sum()
        agg["percentage"] = (agg["total_amount"] / total_sum * 100.0) if total_sum > 0 else 0.0
        agg["total_amount"] = agg["total_amount"].round(2)
        agg["percentage"] = agg["percentage"].round(1)
        return agg.sort_values(by="total_amount", ascending=False)

    def get_daily_spending_trend(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> pd.DataFrame:
        df = self.tx_service.get_as_dataframe(start_date=start_date, end_date=end_date)
        if df.empty:
            return pd.DataFrame(columns=["date", "income", "expense", "net"])

        pivot = df.pivot_table(
            index="date",
            columns="type",
            values="amount",
            aggfunc="sum",
            fill_value=0.0
        ).reset_index()

        if "income" not in pivot.columns:
            pivot["income"] = 0.0
        if "expense" not in pivot.columns:
            pivot["expense"] = 0.0

        pivot = pivot.set_index("date").resample("D").sum().reset_index()
        pivot["net"] = (pivot["income"] - pivot["expense"]).round(2)
        pivot["income"] = pivot["income"].round(2)
        pivot["expense"] = pivot["expense"].round(2)
        return pivot

    def get_monthly_comparison(
        self,
        months: int = 6
    ) -> pd.DataFrame:
        df = self.tx_service.get_as_dataframe()
        if df.empty:
            return pd.DataFrame(columns=["year_month", "income", "expense", "net", "savings_rate"])

        df["year_month"] = df["date"].dt.to_period("M").astype(str)
        monthly = df.pivot_table(
            index="year_month",
            columns="type",
            values="amount",
            aggfunc="sum",
            fill_value=0.0
        ).reset_index()

        if "income" not in monthly.columns:
            monthly["income"] = 0.0
        if "expense" not in monthly.columns:
            monthly["expense"] = 0.0

        monthly["net"] = (monthly["income"] - monthly["expense"]).round(2)
        monthly["savings_rate"] = np.where(
            monthly["income"] > 0,
            (monthly["net"] / monthly["income"] * 100.0).round(1),
            0.0
        )
        return monthly.tail(months)

    def get_deep_analytics_metrics(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        df = self.tx_service.get_as_dataframe(start_date=start_date, end_date=end_date, tx_type="expense")
        if df.empty:
            return {
                "avg_daily_spend": 0.0,
                "highest_spend_day": None,
                "highest_spend_amount": 0.0,
                "total_expense": 0.0,
                "top_category": "None",
                "days_count": 0
            }

        daily = df.groupby("date")["amount"].sum()
        days_span = max(1, (df["date"].max() - df["date"].min()).days + 1)
        avg_daily = df["amount"].sum() / days_span
        max_idx = daily.idxmax()
        top_cat = df.groupby("category")["amount"].sum().idxmax()

        return {
            "avg_daily_spend": round(avg_daily, 2),
            "highest_spend_day": max_idx.strftime("%Y-%m-%d"),
            "highest_spend_amount": round(daily.max(), 2),
            "total_expense": round(df["amount"].sum(), 2),
            "top_category": top_cat,
            "days_count": days_span
        }
