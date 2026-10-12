import streamlit as st
from database.repositories import SettingsRepository
from services.transaction_service import TransactionService

def render_sidebar():
    with st.sidebar:
        st.markdown("## 💳 **SmartSpend AI**")
        st.markdown("<p style='font-size: 0.85rem; color: #6b7280;'>Intelligent Personal Expense Tracker</p>", unsafe_allow_html=True)
        st.divider()

        settings_repo = SettingsRepository()
        curr = settings_repo.get("currency", "INR")
        st.caption(f"Active Currency: **{curr}**")

        tx_service = TransactionService()
        count = tx_service.count_transactions()
        st.caption(f"Total Transactions: **{count}**")

        st.divider()
        st.markdown("<div style='font-size: 0.75rem; color: #9ca3af;'>100% Local & Private • Zero Cloud Leak</div>", unsafe_allow_html=True)
