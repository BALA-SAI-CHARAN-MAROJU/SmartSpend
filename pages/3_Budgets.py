import streamlit as st
from datetime import date, timedelta
from database.initialization import initialize_database
from database.repositories import SettingsRepository
from services.budget_service import BudgetService
from models.schemas import BudgetCreate
from components.styles import apply_custom_styles, format_currency
from components.sidebar import render_sidebar
import config

st.set_page_config(page_title="SmartSpend AI - Budgets", page_icon="💳", layout="wide")
initialize_database()
apply_custom_styles()
render_sidebar()

st.title("Budget Management")

settings_repo = SettingsRepository()
currency = settings_repo.get("currency", "INR")
budget_service = BudgetService()

with st.expander("➕ Set Category Budget", expanded=False):
    with st.form("create_budget_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            category = st.selectbox("Category", config.DEFAULT_EXPENSE_CATEGORIES + ["Overall"])
            budget_amount = st.number_input("Budget Limit", min_value=100.0, step=500.0, format="%.2f")
        with col2:
            period_type = st.selectbox("Period Type", ["monthly", "custom"])
            today = date.today()
            if period_type == "monthly":
                start_date = date(today.year, today.month, 1)
                if today.month == 12:
                    end_date = date(today.year + 1, 1, 1) - timedelta(days=1)
                else:
                    end_date = date(today.year, today.month + 1, 1) - timedelta(days=1)
                st.caption(f"Active window: {start_date} to {end_date}")
            else:
                c_d1, c_d2 = st.columns(2)
                start_date = c_d1.date_input("Start Date", value=today)
                end_date = c_d2.date_input("End Date", value=today + timedelta(days=30))

        submitted = st.form_submit_button("Save Budget", use_container_width=True)
        if submitted:
            try:
                b_create = BudgetCreate(
                    category=category,
                    budget_amount=budget_amount,
                    period_type=period_type,
                    start_date=start_date,
                    end_date=end_date
                )
                budget_service.set_budget(b_create)
                st.success(f"Budget for '{category}' set to {format_currency(budget_amount, currency)}!")
                st.rerun()
            except Exception as e:
                st.error(f"Error saving budget: {e}")

st.markdown("---")

st.markdown("### Active Budgets & Threshold Utilization")
statuses = budget_service.get_budget_status()

if not statuses:
    st.info("No active budgets found. Click 'Set Category Budget' above to establish spending limits.")
else:
    for b in statuses:
        alert_badge = ""
        if b["alert_level"] == "exceeded":
            alert_badge = "🚨 EXCEEDED"
        elif b["alert_level"] == "critical":
            alert_badge = "⚠️ CRITICAL (>90%)"
        elif b["alert_level"] == "warning":
            alert_badge = "⚡ WARNING (>75%)"

        with st.container():
            c1, c2, c3, c4 = st.columns([2, 1.5, 1.5, 1])
            with c1:
                st.markdown(f"#### {b['category']} {alert_badge}")
                st.caption(f"Period: {b['start_date']} to {b['end_date']}")
            with c2:
                st.write(f"**Spent:** {format_currency(b['total_spent'], currency)}")
                st.caption(f"{b['transaction_count']} transactions")
            with c3:
                st.write(f"**Limit:** {format_currency(b['budget_amount'], currency)}")
                rem_color = "#047857" if b['remaining'] >= 0 else "#b91c1c"
                st.markdown(f"<span style='color: {rem_color}; font-size: 0.85rem;'>Remaining: {format_currency(b['remaining'], currency)}</span>", unsafe_allow_html=True)
            with c4:
                if st.button("Delete", key=f"del_budget_{b['budget_id']}"):
                    budget_service.delete_budget(b['budget_id'])
                    st.rerun()

            pct = min(1.0, max(0.0, b["utilization_pct"] / 100.0))
            st.progress(pct)
            st.caption(f"Utilization: **{b['utilization_pct']}%**")
            st.divider()
