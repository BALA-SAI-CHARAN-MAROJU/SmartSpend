import streamlit as st
from database.initialization import initialize_database
from database.repositories import SettingsRepository
from services.transaction_service import TransactionService
from services.analytics_service import AnalyticsService
from components.styles import apply_custom_styles, format_currency
from components.sidebar import render_sidebar
from components.metric_cards import render_metric_card
from components.charts import create_income_expense_trend_chart, create_category_pie_chart

st.set_page_config(
    page_title="SmartSpend AI - Intelligent Expense Tracker",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded"
)

initialize_database()
apply_custom_styles()
render_sidebar()

st.title("SmartSpend AI 💳")
st.markdown("##### Intelligent, Local-First Personal Finance Dashboard")

settings_repo = SettingsRepository()
currency = settings_repo.get("currency", "INR")
monthly_budget_setting = float(settings_repo.get("monthly_budget", "50000"))

tx_service = TransactionService()
analytics_service = AnalyticsService()

metrics = tx_service.get_summary_metrics()

if metrics["transaction_count"] == 0:
    st.info("👋 Welcome to **SmartSpend AI**! No transactions recorded yet.")
    st.markdown("""
        **Get started right away:**
        - Navigate to **Transactions** in the sidebar to add your first expense or income.
        - Or head over to **Settings** to load a realistic 90-day demo dataset for testing machine learning forecasts and analytics.
    """)
else:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_metric_card("Total Income (All-Time)", metrics["total_income"], currency=currency)
    with col2:
        render_metric_card("Total Expenses (All-Time)", metrics["total_expenses"], currency=currency)
    with col3:
        render_metric_card("Net Savings", metrics["net_savings"], currency=currency, subtext=f"Savings Rate: {metrics['savings_rate']}%")
    with col4:
        render_metric_card("Configured Monthly Budget", monthly_budget_setting, currency=currency, subtext="Global limit")

    st.markdown("---")

    c1, c2 = st.columns([1.3, 1])
    with c1:
        st.markdown("### Cash Flow Trend")
        trend_df = analytics_service.get_daily_spending_trend()
        st.plotly_chart(create_income_expense_trend_chart(trend_df), use_container_width=True)
    with c2:
        st.markdown("### Expense Breakdown")
        cat_df = analytics_service.get_spending_by_category()
        st.plotly_chart(create_category_pie_chart(cat_df), use_container_width=True)

    st.markdown("---")
    st.markdown("### Quick Navigation")
    nav1, nav2, nav3, nav4 = st.columns(4)
    with nav1:
        st.markdown("**📊 Overview & Analytics**\nExplore daily trends, monthly summaries, and category shares in *Overview* and *Spending Analytics*.")
    with nav2:
        st.markdown("**🤖 ML Predictions**\nForecast end-of-month expenditure using regression models compared with rolling baselines in *ML Predictions*.")
    with nav3:
        st.markdown("**🎯 Budgets & Goals**\nSet category limits with 75%/90%/100% alerts in *Budgets* and plan targets in *Savings Goals*.")
    with nav4:
        st.markdown("**📥 Import & Backup**\nImport bank statements, download templates, and export offline SQLite backups in *Import & Export*.")
