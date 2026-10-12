import streamlit as st
from datetime import date, timedelta
from database.initialization import initialize_database
from database.repositories import SettingsRepository
from services.savings_service import SavingsService
from models.schemas import SavingsGoalCreate
from components.styles import apply_custom_styles, format_currency
from components.sidebar import render_sidebar

st.set_page_config(page_title="SmartSpend AI - Savings Goals", page_icon="💳", layout="wide")
initialize_database()
apply_custom_styles()
render_sidebar()

st.title("Savings Goals Tracker")

settings_repo = SettingsRepository()
currency = settings_repo.get("currency", "INR")
savings_service = SavingsService()

with st.expander("🎯 Create New Savings Goal", expanded=False):
    with st.form("create_goal_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            goal_name = st.text_input("Goal Name", placeholder="e.g. Emergency Fund, Laptop, Vacation")
            target_amount = st.number_input("Target Amount", min_value=100.0, step=1000.0, format="%.2f")
            initial_amount = st.number_input("Starting Balance / Already Saved", min_value=0.0, step=500.0, format="%.2f")
        with col2:
            target_date = st.date_input("Target Completion Date", value=date.today() + timedelta(days=90))
            description = st.text_area("Description / Motivation", placeholder="Why are you saving for this?")

        submitted = st.form_submit_button("Create Goal", use_container_width=True)
        if submitted:
            if not goal_name.strip():
                st.error("Please enter a valid goal name.")
            else:
                try:
                    new_g = SavingsGoalCreate(
                        goal_name=goal_name,
                        target_amount=target_amount,
                        current_amount=initial_amount,
                        target_date=target_date,
                        description=description
                    )
                    savings_service.add_goal(new_g)
                    st.success(f"Goal '{goal_name}' created successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error creating goal: {e}")

st.markdown("---")

goals = savings_service.get_goals()
if not goals:
    st.info("No savings goals set yet. Create your first target above!")
else:
    for g in goals:
        with st.container():
            c1, c2, c3 = st.columns([2.5, 2, 1.5])
            with c1:
                status_icon = "🎉 COMPLETED" if g["is_completed"] else f"⏳ {g['days_remaining']} days left"
                st.markdown(f"### {g['goal_name']}")
                st.caption(f"{g['description'] or 'No description'} • Target Date: {g['target_date'].strftime('%d %b %Y')}")
            with c2:
                st.write(f"**Saved:** {format_currency(g['current_amount'], currency)} of {format_currency(g['target_amount'], currency)}")
                if not g["is_completed"] and g["days_remaining"] > 0:
                    st.caption(f"Required: **{format_currency(g['monthly_required'], currency)}/mo** ({format_currency(g['daily_required'], currency)}/day)")
                else:
                    st.caption(status_icon)
            with c3:
                add_contrib = st.number_input(f"+ Add Funds", min_value=0.0, step=500.0, key=f"contrib_val_{g['id']}", format="%.2f")
                col_b1, col_b2 = st.columns(2)
                with col_b1:
                    if st.button("Save", key=f"add_btn_{g['id']}"):
                        if add_contrib > 0:
                            savings_service.update_progress(g["id"], g["current_amount"] + add_contrib)
                            st.rerun()
                with col_b2:
                    if st.button("Delete", key=f"del_g_{g['id']}"):
                        savings_service.delete_goal(g["id"])
                        st.rerun()

            progress_ratio = min(1.0, max(0.0, g["progress_pct"] / 100.0))
            st.progress(progress_ratio)
            st.caption(f"Progress: **{g['progress_pct']}%** • Remaining: **{format_currency(g['remaining_amount'], currency)}**")
            st.divider()
