import io
import streamlit as st
from datetime import date
import pandas as pd
from database.initialization import initialize_database
from database.repositories import SettingsRepository
from services.import_export_service import ImportExportService
from services.backup_service import BackupService
from components.styles import apply_custom_styles
from components.sidebar import render_sidebar
import config

st.set_page_config(page_title="SmartSpend AI - Import & Export", page_icon="💳", layout="wide")
initialize_database()
apply_custom_styles()
render_sidebar()

st.title("Data Import, Export & Backups")

import_export_service = ImportExportService()
backup_service = BackupService()

tab_import, tab_export, tab_backup = st.tabs(["📥 CSV Import", "📤 CSV Export", "💾 Database Backups"])

with tab_import:
    st.markdown("### Import Transactions from CSV")
    st.write("Upload statements or bank exports. SmartSpend AI maps fields, checks row validations, and flags suspected duplicates.")

    sample_csv = import_export_service.generate_csv_template()
    st.download_button(
        label="📄 Download Sample CSV Template",
        data=sample_csv,
        file_name="smartspend_sample_template.csv",
        mime="text/csv"
    )

    st.markdown("---")
    uploaded_file = st.file_uploader("Choose CSV file", type=["csv"])

    if uploaded_file is not None:
        content = uploaded_file.getvalue()
        df_preview = pd.read_csv(io.StringIO(content.decode("utf-8", errors="replace")))
        st.write("##### File Preview:")
        st.dataframe(df_preview.head(5), use_container_width=True)

        st.write("##### Column Mapping:")
        file_cols = list(df_preview.columns)
        
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1:
            date_col = st.selectbox("Date Column", file_cols, index=file_cols.index("date") if "date" in file_cols else 0)
            amount_col = st.selectbox("Amount Column", file_cols, index=file_cols.index("amount") if "amount" in file_cols else 0)
        with col_m2:
            type_col = st.selectbox("Type Column", file_cols, index=file_cols.index("type") if "type" in file_cols else 0)
            cat_col = st.selectbox("Category Column", file_cols, index=file_cols.index("category") if "category" in file_cols else 0)
        with col_m3:
            desc_col = st.selectbox("Description Column", ["None"] + file_cols, index=file_cols.index("description") + 1 if "description" in file_cols else 0)
            merchant_col = st.selectbox("Merchant Column", ["None"] + file_cols, index=file_cols.index("merchant") + 1 if "merchant" in file_cols else 0)
        with col_m4:
            pay_col = st.selectbox("Payment Method", ["None"] + file_cols, index=file_cols.index("payment_method") + 1 if "payment_method" in file_cols else 0)

        mapping = {
            "date": date_col,
            "amount": amount_col,
            "type": type_col,
            "category": cat_col,
        }
        if desc_col != "None": mapping["description"] = desc_col
        if merchant_col != "None": mapping["merchant"] = merchant_col
        if pay_col != "None": mapping["payment_method"] = pay_col

        if st.button("Validate & Process Records"):
            valid_recs, errors, dupes = import_export_service.parse_and_validate_csv(content, mapping)
            st.session_state["pending_import"] = valid_recs
            st.session_state["import_errors"] = errors
            st.session_state["import_dupes"] = dupes

        if "pending_import" in st.session_state:
            valid_recs = st.session_state["pending_import"]
            errors = st.session_state["import_errors"]
            dupes = st.session_state["import_dupes"]

            st.write(f"✅ **{len(valid_recs)} Valid Records Found**")
            if dupes:
                st.warning(f"⚠️ **{len(dupes)} Suspected Duplicate Records** matched against existing transactions.")
            if errors:
                st.error(f"❌ **{len(errors)} Row Validation Errors** encountered.")
                with st.expander("View Validation Errors"):
                    st.json(errors)

            if valid_recs:
                if st.button("Commit Import to Database", type="primary"):
                    imported_count = import_export_service.import_transactions(valid_recs)
                    st.success(f"Successfully imported {imported_count} transactions!")
                    del st.session_state["pending_import"]
                    st.rerun()

with tab_export:
    st.markdown("### Export Transactions")
    col_e1, col_e2, col_e3 = st.columns(3)
    with col_e1:
        exp_type = st.selectbox("Export Filter Type", ["All", "Expense", "Income"])
    with col_e2:
        exp_start = st.date_input("From Date", value=date.today() - pd.Timedelta(days=90))
    with col_e3:
        exp_end = st.date_input("To Date", value=date.today())

    if st.button("Generate Export CSV"):
        csv_data = import_export_service.export_transactions_csv(
            start_date=exp_start,
            end_date=exp_end,
            tx_type=exp_type.lower() if exp_type != "All" else None
        )
        st.download_button(
            label="💾 Download Filtered CSV",
            data=csv_data,
            file_name=f"smartspend_export_{date.today()}.csv",
            mime="text/csv"
        )

with tab_backup:
    st.markdown("### SQLite Database Backups & Restoration")
    st.write("Create safe, offline snapshot backups using SQLite's native backup API.")

    if st.button("📦 Create Instant Database Backup"):
        backup_path = backup_service.create_backup()
        st.success(f"Backup created successfully at: `{backup_path.name}`")

    st.markdown("---")
    st.markdown("### Available Backups")
    backups = list(config.BACKUPS_DIR.glob("*.db"))
    if not backups:
        st.info("No backups created yet.")
    else:
        for b in sorted(backups, reverse=True):
            b_col1, b_col2 = st.columns([3, 1])
            with b_col1:
                st.write(f"📁 **{b.name}** ({round(b.stat().st_size / 1024, 1)} KB)")
            with b_col2:
                if st.button("Restore This", key=f"restore_{b.name}"):
                    ok, msg = backup_service.restore_backup(b)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
