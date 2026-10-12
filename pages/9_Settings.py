import streamlit as st
from database.initialization import initialize_database
from database.repositories import SettingsRepository
from services.seed_service import seed_sample_dataset
from components.styles import apply_custom_styles
from components.sidebar import render_sidebar
import config

st.set_page_config(page_title="SmartSpend AI - Settings", page_icon="💳", layout="wide")
initialize_database()
apply_custom_styles()
render_sidebar()

st.title("Application Settings")

settings_repo = SettingsRepository()
curr_settings = settings_repo.get_all()

st.markdown("### Financial Preferences")
with st.form("settings_form"):
    currencies = list(config.CURRENCY_SYMBOLS.keys())
    active_curr = curr_settings.get("currency", "INR")
    curr_idx = currencies.index(active_curr) if active_curr in currencies else 0
    selected_currency = st.selectbox("Preferred Currency", currencies, index=curr_idx)

    st.caption("ℹ️ *Note: Changing currency updates display formatting and symbols. It does not alter your numerical transaction amounts.*")

    current_budget = float(curr_settings.get("monthly_budget", "50000"))
    monthly_budget = st.number_input("Global Monthly Spending Budget Limit", min_value=1000.0, value=current_budget, step=5000.0, format="%.2f")

    theme = st.selectbox("Appearance Theme", ["Light (Recommended)", "Dark"], index=0)

    save_btn = st.form_submit_button("Save Preferences", use_container_width=True)
    if save_btn:
        settings_repo.set("currency", selected_currency)
        settings_repo.set("monthly_budget", str(monthly_budget))
        settings_repo.set("theme", "light" if "Light" in theme else "dark")
        st.success("Settings saved successfully!")
        st.rerun()

st.markdown("---")

st.markdown("### Demo Dataset Generator")
st.write("Need instant data to test machine learning predictions, charts, and budget alerts?")

col_d1, col_d2 = st.columns([2, 1])
with col_d1:
    st.write("Generates 90 days of realistic multi-category personal financial data (recurring salary deposits, rent, groceries, weekend dining patterns, bills, and active budgets).")
with col_d2:
    if st.button("🚀 Load Realistic Demo Dataset", type="primary"):
        count = seed_sample_dataset()
        if count > 0:
            st.success(f"Successfully generated {count} realistic transactions, budgets, and savings goals!")
            st.rerun()
        else:
            st.info("Demo data already loaded or database already has existing transactions.")
