from pathlib import Path
from datetime import date, timedelta
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from services.transaction_service import TransactionService
from services.budget_service import BudgetService

class InsightService:
    def __init__(self, db_path: Path | str | None = None):
        self.tx_service = TransactionService(db_path)
        self.budget_service = BudgetService(db_path)

    def generate_insights(self) -> List[Dict[str, Any]]:
        insights = []
        today = date.today()
        df = self.tx_service.get_as_dataframe(tx_type="expense")

        if df.empty:
            return [{
                "type": "info",
                "title": "Welcome to SmartSpend AI",
                "message": "Add your first transaction or import a statement to unlock intelligent spending analytics and alerts.",
                "importance": "low"
            }]

        budget_statuses = self.budget_service.get_budget_status(today)
        for b in budget_statuses:
            if b["alert_level"] == "exceeded":
                insights.append({
                    "type": "danger",
                    "title": f"Budget Exceeded: {b['category']}",
                    "message": f"You have spent {b['total_spent']:.2f} on {b['category']}, which is {b['utilization_pct']:.1f}% of your {b['budget_amount']:.2f} budget.",
                    "importance": "high"
                })
            elif b["alert_level"] == "critical":
                insights.append({
                    "type": "warning",
                    "title": f"Budget Critical: {b['category']}",
                    "message": f"You have reached {b['utilization_pct']:.1f}% of your budget for {b['category']} with {b['remaining']:.2f} remaining.",
                    "importance": "medium"
                })

        current_month_start = date(today.year, today.month, 1)
        curr_month_df = df[df["date"] >= pd.to_datetime(current_month_start)]
        prev_df = df[df["date"] < pd.to_datetime(current_month_start)]

        if not curr_month_df.empty and not prev_df.empty:
            curr_cat_spend = curr_month_df.groupby("category")["amount"].sum()
            num_prev_months = max(1, (current_month_start - df["date"].min().date()).days // 30)
            prev_cat_avg = prev_df.groupby("category")["amount"].sum() / num_prev_months

            for cat, curr_amount in curr_cat_spend.items():
                if cat in prev_cat_avg and prev_cat_avg[cat] > 0:
                    pct_diff = ((curr_amount - prev_cat_avg[cat]) / prev_cat_avg[cat]) * 100
                    if pct_diff >= 40.0 and curr_amount >= 500:
                        insights.append({
                            "type": "warning",
                            "title": f"Spending Spike in {cat}",
                            "message": f"{cat} spending this month ({curr_amount:.2f}) is {pct_diff:.1f}% higher than your historical monthly average ({prev_cat_avg[cat]:.2f}).",
                            "importance": "medium"
                        })

        if len(df) >= 15:
            q75, q25 = np.percentile(df["amount"], [75, 25])
            iqr = q75 - q25
            outlier_threshold = q75 + (2.5 * iqr)
            recent_outliers = df[(df["amount"] > outlier_threshold) & (df["date"] >= pd.to_datetime(today - timedelta(days=14)))]
            if not recent_outliers.empty:
                max_outlier = recent_outliers.sort_values(by="amount", ascending=False).iloc[0]
                insights.append({
                    "type": "info",
                    "title": "Unusually Large Expense Detected",
                    "message": f"A recent transaction of {max_outlier['amount']:.2f} for '{max_outlier['description'] or max_outlier['category']}' on {max_outlier['date'].strftime('%d %b %Y')} is significantly higher than your typical transactions.",
                    "importance": "low"
                })

        sub_df = df[df["category"].str.lower().isin(["subscriptions", "bills"])]
        if not sub_df.empty:
            total_subs = sub_df["amount"].sum()
            insights.append({
                "type": "info",
                "title": "Recurring Fixed Costs Summary",
                "message": f"You have logged {len(sub_df)} recurring expenses (Bills & Subscriptions) totaling {total_subs:.2f}.",
                "importance": "low"
            })

        latest_tx_date = df["date"].max().date()
        inactivity_days = (today - latest_tx_date).days
        if inactivity_days >= 5:
            insights.append({
                "type": "info",
                "title": "No Recent Expenses Logged",
                "message": f"You have not recorded any expenses in the last {inactivity_days} days. Keep your tracker updated to ensure accurate predictions.",
                "importance": "low"
            })

        return insights
