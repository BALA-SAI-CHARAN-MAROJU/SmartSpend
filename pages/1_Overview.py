import streamlit as st
from datetime import date, timedelta
from database.initialization import initialize_database
from database.repositories import SettingsRepository
from services.transaction_service import TransactionService
from services.analytics_service import AnalyticsService
from services.budget_service import BudgetService
from components.styles import apply_custom_styles, format_currency
from components.metric_cards import render_metric_card, render_text_metric_card
from components.charts import create_income_expense_trend_chart, create_category_pie_chart
from components.sidebar import render_sidebar

st.set_page_config(page_title="SmartSpend AI - Overview", page_icon="💳", layout="wide")
initialize_database()
apply_custom_styles()
render_sidebar()

st.title("Financial Overview")

settings_repo = SettingsRepository()
currency = settings_repo.get("currency", "INR")
monthly_budget_setting = float(settings_repo.get("monthly_budget", "50000"))

tx_service = TransactionService()
analytics_service = AnalyticsService()
budget_service = BudgetService()

col_f1, col_f2 = st.columns([1, 2])
with col_f1:
    range_option = st.selectbox(
        "Date Filter",
        ["This Month", "This Week", "Last Month", "Last 3 Months", "This Year", "Custom Range"]
    )

today = date.today()
if range_option == "This Week":
    start_d = today - timedelta(days=today.weekday())
    end_d = today
elif range_option == "This Month":
    start_d = date(today.year, today.month, 1)
    end_d = today
elif range_option == "Last Month":
    first_this_month = date(today.year, today.month, 1)
    end_d = first_this_month - timedelta(days=1)
    start_d = date(end_d.year, end_d.month, 1)
elif range_option == "Last 3 Months":
    start_d = today - timedelta(days=90)
    end_d = today
elif range_option == "This Year":
    start_d = date(today.year, 1, 1)
    end_d = today
else:
    with col_f2:
        c1, c2 = st.columns(2)
        start_d = c1.date_input("Start Date", value=today - timedelta(days=30))
        end_d = c2.date_input("End Date", value=today)

metrics = tx_service.get_summary_metrics(start_date=start_d, end_date=end_d)

if metrics["transaction_count"] == 0:
    st.info("👋 Welcome to **SmartSpend AI**! No transactions recorded in this period yet.")
    st.markdown("Go to **Transactions** to add your first expense or **Settings** to load sample data for instant demonstration.")
else:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_metric_card("Total Income", metrics["total_income"], currency=currency, subtext=f"{range_option}")
    with col2:
        render_metric_card("Total Expenses", metrics["total_expenses"], currency=currency, subtext=f"{range_option}")
    with col3:
        render_metric_card("Net Savings", metrics["net_savings"], currency=currency, subtext=f"Rate: {metrics['savings_rate']}%")
    with col4:
        curr_month_start = date(today.year, today.month, 1)
        curr_month_txs = tx_service.get_transactions(start_date=curr_month_start, end_date=today, tx_type="expense")
        curr_month_spent = sum(t.amount for t in curr_month_txs)
        remaining_budget = monthly_budget_setting - curr_month_spent
        render_metric_card("Remaining Budget", remaining_budget, currency=currency, subtext=f"Limit: {format_currency(monthly_budget_setting, currency)}")

    st.markdown("---")

    chart_col1, chart_col2 = st.columns([1.2, 1])
    with chart_col1:
        daily_trend = analytics_service.get_daily_spending_trend(start_date=start_d, end_date=end_d)
        st.plotly_chart(create_income_expense_trend_chart(daily_trend), use_container_width=True)

    with chart_col2:
        cat_df = analytics_service.get_spending_by_category(start_date=start_d, end_date=end_d)
        st.plotly_chart(create_category_pie_chart(cat_df), use_container_width=True)

    st.markdown("### Recent Transactions")
    recent_txs = tx_service.get_transactions(limit=8)
    if recent_txs:
        table_data = [
            {
                "Date": t.transaction_date.strftime("%d %b %Y"),
                "Type": t.transaction_type.capitalize(),
                "Category": t.category,
                "Description": t.description,
                "Merchant": t.merchant,
                "Method": t.payment_method,
                "Amount": format_currency(t.amount, currency)
            }
            for t in recent_txs
        ]
        st.dataframe(table_data, use_container_width=True, hide_index=True)
