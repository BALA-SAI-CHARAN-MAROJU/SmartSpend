import streamlit as st
from datetime import date, timedelta
from database.initialization import initialize_database
from database.repositories import SettingsRepository
from services.transaction_service import TransactionService
from components.styles import apply_custom_styles, format_currency
from components.sidebar import render_sidebar
from components.transaction_forms import render_add_transaction_form, render_edit_transaction_form
import config

st.set_page_config(page_title="SmartSpend AI - Transactions", page_icon="💳", layout="wide")
initialize_database()
apply_custom_styles()
render_sidebar()

st.title("Transaction Management")

settings_repo = SettingsRepository()
currency = settings_repo.get("currency", "INR")
tx_service = TransactionService()

with st.expander("➕ Add New Transaction", expanded=False):
    def handle_add_tx(new_tx):
        tx_id = tx_service.add_transaction(new_tx)
        st.success(f"Transaction #{tx_id} added successfully!")
        st.rerun()

    render_add_transaction_form(handle_add_tx)

st.markdown("---")

col1, col2, col3, col4 = st.columns([1.5, 1, 1, 1])
with col1:
    search_q = st.text_input("🔍 Search", placeholder="Description or merchant...")
with col2:
    filter_type = st.selectbox("Type", ["All", "Expense", "Income"])
with col3:
    all_cats = ["All"] + config.DEFAULT_EXPENSE_CATEGORIES + config.DEFAULT_INCOME_CATEGORIES
    filter_cat = st.selectbox("Category", list(dict.fromkeys(all_cats)))
with col4:
    filter_method = st.selectbox("Payment Method", ["All"] + config.DEFAULT_PAYMENT_METHODS)

col_d1, col_d2, col_d3 = st.columns([1, 1, 1])
with col_d1:
    filter_start = st.date_input("Start Date", value=date.today() - timedelta(days=90))
with col_d2:
    filter_end = st.date_input("End Date", value=date.today())
with col_d3:
    sort_option = st.selectbox("Sort By", ["Newest First", "Oldest First", "Highest Amount", "Lowest Amount"])

sort_map = {
    "Newest First": ("transaction_date", "DESC"),
    "Oldest First": ("transaction_date", "ASC"),
    "Highest Amount": ("amount_cents", "DESC"),
    "Lowest Amount": ("amount_cents", "ASC"),
}
sort_col, sort_ord = sort_map[sort_option]

PAGE_SIZE = 15
total_matching = tx_service.count_transactions(
    start_date=filter_start,
    end_date=filter_end,
    tx_type=filter_type.lower() if filter_type != "All" else None,
    category=filter_cat if filter_cat != "All" else None,
    payment_method=filter_method if filter_method != "All" else None,
    search_query=search_q
)

total_pages = max(1, (total_matching + PAGE_SIZE - 1) // PAGE_SIZE)
col_p1, col_p2 = st.columns([3, 1])
with col_p2:
    page_num = st.number_input(f"Page (of {total_pages})", min_value=1, max_value=total_pages, value=1, step=1)

offset = (page_num - 1) * PAGE_SIZE
txs = tx_service.get_transactions(
    start_date=filter_start,
    end_date=filter_end,
    tx_type=filter_type.lower() if filter_type != "All" else None,
    category=filter_cat if filter_cat != "All" else None,
    payment_method=filter_method if filter_method != "All" else None,
    search_query=search_q,
    sort_by=sort_col,
    sort_order=sort_ord,
    limit=PAGE_SIZE,
    offset=offset
)

st.caption(f"Showing {len(txs)} of {total_matching} records")

if not txs:
    st.info("No transactions match the selected filters.")
else:
    for tx in txs:
        with st.container():
            t_col1, t_col2, t_col3, t_col4, t_col5 = st.columns([1.2, 1.2, 2.5, 1.2, 1.2])
            with t_col1:
                st.write(f"**{tx.transaction_date.strftime('%d %b %Y')}**")
            with t_col2:
                badge_class = "badge-income" if tx.transaction_type == "income" else "badge-expense"
                st.markdown(f"<span class='{badge_class}'>{tx.category}</span>", unsafe_allow_html=True)
            with t_col3:
                desc = tx.description or "-"
                merch = f" • *{tx.merchant}*" if tx.merchant else ""
                st.write(f"{desc}{merch}")
            with t_col4:
                prefix = "+" if tx.transaction_type == "income" else "-"
                color = "#047857" if tx.transaction_type == "income" else "#b91c1c"
                st.markdown(f"<span style='color: {color}; font-weight: 700;'>{prefix}{format_currency(tx.amount, currency)}</span>", unsafe_allow_html=True)
            with t_col5:
                if st.button("Edit / Delete", key=f"edit_toggle_{tx.id}"):
                    st.session_state[f"active_edit_{tx.id}"] = not st.session_state.get(f"active_edit_{tx.id}", False)

            if st.session_state.get(f"active_edit_{tx.id}", False):
                with st.expander(f"Edit Transaction #{tx.id}", expanded=True):
                    def handle_update(updated_tx):
                        tx_service.update_transaction(updated_tx)
                        st.session_state[f"active_edit_{tx.id}"] = False
                        st.success("Updated successfully!")
                        st.rerun()

                    render_edit_transaction_form(tx, handle_update)

                    st.markdown("---")
                    st.markdown("##### Danger Zone")
                    del_conf = st.checkbox("Confirm permanent deletion", key=f"del_confirm_{tx.id}")
                    if del_conf:
                        if st.button("Delete Permanently", key=f"del_btn_{tx.id}", type="primary"):
                            tx_service.delete_transaction(tx.id)
                            st.session_state[f"active_edit_{tx.id}"] = False
                            st.success(f"Transaction #{tx.id} deleted.")
                            st.rerun()
            st.divider()
