import streamlit as st
from datetime import date, timedelta
from database.initialization import initialize_database
from database.repositories import SettingsRepository
from services.analytics_service import AnalyticsService
from components.styles import apply_custom_styles, format_currency
from components.metric_cards import render_metric_card, render_text_metric_card
from components.charts import (
    create_income_expense_trend_chart,
    create_category_pie_chart,
    create_monthly_comparison_chart
)
from components.sidebar import render_sidebar

st.set_page_config(page_title="SmartSpend AI - Analytics", page_icon="💳", layout="wide")
initialize_database()
apply_custom_styles()
render_sidebar()

st.title("Spending Analytics")

settings_repo = SettingsRepository()
currency = settings_repo.get("currency", "INR")
analytics_service = AnalyticsService()

col1, col2 = st.columns([1, 2])
with col1:
    preset = st.selectbox("Timeframe", ["Last 90 Days", "This Month", "Last 30 Days", "This Year", "All Time"])

today = date.today()
if preset == "Last 90 Days":
    start_d, end_d = today - timedelta(days=90), today
elif preset == "This Month":
    start_d, end_d = date(today.year, today.month, 1), today
elif preset == "Last 30 Days":
    start_d, end_d = today - timedelta(days=30), today
elif preset == "This Year":
    start_d, end_d = date(today.year, 1, 1), today
else:
    start_d, end_d = None, None

deep_metrics = analytics_service.get_deep_analytics_metrics(start_date=start_d, end_date=end_d)

m1, m2, m3, m4 = st.columns(4)
with m1:
    render_metric_card("Avg Daily Spending", deep_metrics["avg_daily_spend"], currency=currency)
with m2:
    render_metric_card("Highest Spending Day", deep_metrics["highest_spend_amount"], currency=currency, subtext=f"{deep_metrics['highest_spend_day'] or 'N/A'}")
with m3:
    render_text_metric_card("Top Category", deep_metrics["top_category"], subtext="Highest volume")
with m4:
    render_metric_card("Total Expenses", deep_metrics["total_expense"], currency=currency, subtext=f"Over {deep_metrics['days_count']} days")

st.markdown("---")

st.markdown("### Monthly Financial Trajectory")
monthly_df = analytics_service.get_monthly_comparison(months=12)
if not monthly_df.empty:
    st.plotly_chart(create_monthly_comparison_chart(monthly_df), use_container_width=True)
else:
    st.info("Insufficient data for monthly comparison.")

col_c1, col_c2 = st.columns([1.2, 1])
with col_c1:
    st.markdown("### Daily Cash Flow Trend")
    trend_df = analytics_service.get_daily_spending_trend(start_date=start_d, end_date=end_d)
    st.plotly_chart(create_income_expense_trend_chart(trend_df), use_container_width=True)

with col_c2:
    st.markdown("### Category Proportions")
    cat_df = analytics_service.get_spending_by_category(start_date=start_d, end_date=end_d)
    st.plotly_chart(create_category_pie_chart(cat_df), use_container_width=True)

if not cat_df.empty:
    st.markdown("### Detailed Category Breakdown")
    cat_display = cat_df.copy()
    cat_display["total_amount"] = cat_display["total_amount"].apply(lambda x: format_currency(x, currency))
    cat_display.columns = ["Category", "Total Spent", "Share (%)", "Transaction Count"]
    st.dataframe(cat_display, use_container_width=True, hide_index=True)
