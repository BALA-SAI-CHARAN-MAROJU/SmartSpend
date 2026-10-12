import streamlit as st
from datetime import date
from models.schemas import TransactionCreate, TransactionUpdate
import config

def render_add_transaction_form(on_submit_callback):
    with st.form("add_transaction_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            tx_type = st.selectbox("Transaction Type", ["expense", "income"], format_func=lambda x: x.capitalize())
            amount = st.number_input("Amount", min_value=0.01, step=10.0, format="%.2f")
            tx_date = st.date_input("Date", value=date.today())
        
        with col2:
            cats = config.DEFAULT_EXPENSE_CATEGORIES if tx_type == "expense" else config.DEFAULT_INCOME_CATEGORIES
            category = st.selectbox("Category", cats)
            payment_method = st.selectbox("Payment Method", config.DEFAULT_PAYMENT_METHODS)
            merchant = st.text_input("Merchant / Payee (Optional)", placeholder="e.g. Swiggy, Amazon, Employer")

        description = st.text_input("Description / Notes", placeholder="e.g. Dinner with team, Groceries")

        submitted = st.form_submit_button("Add Transaction", use_container_width=True)
        if submitted:
            if amount <= 0:
                st.error("Amount must be greater than zero.")
                return
            new_tx = TransactionCreate(
                transaction_date=tx_date,
                transaction_type=tx_type,
                amount=amount,
                category=category,
                description=description,
                payment_method=payment_method,
                merchant=merchant
            )
            on_submit_callback(new_tx)

def render_edit_transaction_form(tx, on_update_callback):
    with st.form(f"edit_tx_{tx.id}"):
        col1, col2 = st.columns(2)
        with col1:
            tx_type = st.selectbox(
                "Transaction Type",
                ["expense", "income"],
                index=0 if tx.transaction_type == "expense" else 1,
                format_func=lambda x: x.capitalize()
            )
            amount = st.number_input("Amount", min_value=0.01, value=float(tx.amount), step=10.0, format="%.2f")
            tx_date = st.date_input("Date", value=tx.transaction_date)

        with col2:
            cats = config.DEFAULT_EXPENSE_CATEGORIES if tx_type == "expense" else config.DEFAULT_INCOME_CATEGORIES
            cat_idx = cats.index(tx.category) if tx.category in cats else 0
            category = st.selectbox("Category", cats, index=cat_idx)
            pay_idx = config.DEFAULT_PAYMENT_METHODS.index(tx.payment_method) if tx.payment_method in config.DEFAULT_PAYMENT_METHODS else 0
            payment_method = st.selectbox("Payment Method", config.DEFAULT_PAYMENT_METHODS, index=pay_idx)
            merchant = st.text_input("Merchant", value=tx.merchant or "")

        description = st.text_input("Description", value=tx.description or "")

        submitted = st.form_submit_button("Save Changes", use_container_width=True)
        if submitted:
            updated_tx = TransactionUpdate(
                id=tx.id,
                transaction_date=tx_date,
                transaction_type=tx_type,
                amount=amount,
                category=category,
                description=description,
                payment_method=payment_method,
                merchant=merchant
            )
            on_update_callback(updated_tx)
