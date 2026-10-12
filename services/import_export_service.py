import io
import csv
from pathlib import Path
from datetime import datetime, date
from typing import List, Dict, Any, Tuple
import pandas as pd
from models.schemas import TransactionCreate
from services.transaction_service import TransactionService
import config

class ImportExportService:
    def __init__(self, db_path: Path | str | None = None):
        self.tx_service = TransactionService(db_path)

    def generate_csv_template(self) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["date", "type", "amount", "category", "description", "payment_method", "merchant"])
        writer.writerow(["2026-03-01", "expense", "450.00", "Food", "Dinner with friends", "UPI", "Swiggy"])
        writer.writerow(["2026-03-02", "income", "75000.00", "Salary", "Monthly Salary Deposit", "Bank Transfer", "Employer Corp"])
        writer.writerow(["2026-03-05", "expense", "1200.00", "Groceries", "Weekly vegetables and fruits", "Credit Card", "Supermarket"])
        return output.getvalue()

    def parse_and_validate_csv(
        self,
        file_content: str | bytes,
        column_mapping: Dict[str, str]
    ) -> Tuple[List[TransactionCreate], List[Dict[str, Any]], List[Dict[str, Any]]]:
        if isinstance(file_content, bytes):
            file_content = file_content.decode("utf-8", errors="replace")

        df = pd.read_csv(io.StringIO(file_content))
        valid_records: List[TransactionCreate] = []
        errors: List[Dict[str, Any]] = []
        duplicates: List[Dict[str, Any]] = []

        inv_map = {v: k for k, v in column_mapping.items()}

        existing_txs = self.tx_service.get_transactions()
        existing_fps = {
            (t.transaction_date.isoformat(), t.transaction_type, round(t.amount, 2), t.category.lower())
            for t in existing_txs
        }

        for idx, row in df.iterrows():
            row_num = idx + 2
            row_dict = row.to_dict()

            try:
                raw_date = str(row_dict.get(inv_map.get("date", "date"), "")).strip()
                parsed_date = None
                for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y", "%Y/%m/%d"]:
                    try:
                        parsed_date = datetime.strptime(raw_date, fmt).date()
                        break
                    except ValueError:
                        continue
                if not parsed_date:
                    errors.append({"row": row_num, "error": f"Invalid date format '{raw_date}'"})
                    continue

                raw_type = str(row_dict.get(inv_map.get("type", "type"), "expense")).strip().lower()
                if raw_type not in ["income", "expense"]:
                    errors.append({"row": row_num, "error": f"Invalid transaction type '{raw_type}'. Must be income or expense."})
                    continue

                raw_amount = str(row_dict.get(inv_map.get("amount", "amount"), 0)).replace(",", "").strip()
                try:
                    amount_val = float(raw_amount)
                    if amount_val <= 0:
                        errors.append({"row": row_num, "error": "Amount must be strictly greater than 0."})
                        continue
                except ValueError:
                    errors.append({"row": row_num, "error": f"Invalid numeric amount '{raw_amount}'"})
                    continue

                raw_cat = str(row_dict.get(inv_map.get("category", "category"), "Other")).strip()
                if not raw_cat:
                    raw_cat = "Other"

                desc = str(row_dict.get(inv_map.get("description", "description"), "")).strip()
                if desc == "nan": desc = ""
                pay_method = str(row_dict.get(inv_map.get("payment_method", "payment_method"), "Other")).strip()
                if pay_method == "nan": pay_method = "Other"
                merchant = str(row_dict.get(inv_map.get("merchant", "merchant"), "")).strip()
                if merchant == "nan": merchant = ""

                fp = (parsed_date.isoformat(), raw_type, round(amount_val, 2), raw_cat.lower())
                if fp in existing_fps:
                    duplicates.append({
                        "row": row_num,
                        "date": parsed_date.isoformat(),
                        "amount": amount_val,
                        "category": raw_cat,
                        "description": desc,
                    })

                tx = TransactionCreate(
                    transaction_date=parsed_date,
                    transaction_type=raw_type,
                    amount=amount_val,
                    category=raw_cat,
                    description=desc,
                    payment_method=pay_method,
                    merchant=merchant
                )
                valid_records.append(tx)

            except Exception as e:
                errors.append({"row": row_num, "error": str(e)})

        return valid_records, errors, duplicates

    def import_transactions(self, records: List[TransactionCreate]) -> int:
        count = 0
        for r in records:
            self.tx_service.add_transaction(r)
            count += 1
        return count

    def export_transactions_csv(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        tx_type: Optional[str] = None
    ) -> str:
        txs = self.tx_service.get_transactions(start_date=start_date, end_date=end_date, tx_type=tx_type)
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "date", "type", "amount", "category", "description", "payment_method", "merchant", "created_at"])
        for t in txs:
            writer.writerow([
                t.id,
                t.transaction_date.isoformat(),
                t.transaction_type,
                f"{t.amount:.2f}",
                t.category,
                t.description,
                t.payment_method,
                t.merchant,
                t.created_at.isoformat()
            ])
        return output.getvalue()
