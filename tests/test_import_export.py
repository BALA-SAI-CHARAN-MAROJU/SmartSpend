import tempfile
from pathlib import Path
from datetime import date
import pytest
from database.initialization import initialize_database
from models.schemas import TransactionCreate
from services.import_export_service import ImportExportService
from services.backup_service import BackupService
from services.transaction_service import TransactionService

@pytest.fixture
def temp_io_env():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        temp_db = Path(f.name)
    initialize_database(temp_db)
    io = ImportExportService(temp_db)
    tx = TransactionService(temp_db)
    bk = BackupService(temp_db)
    yield io, tx, bk, temp_db
    if temp_db.exists():
        temp_db.unlink()

def test_csv_import_validation_and_duplicate_detection(temp_io_env):
    io_svc, tx_svc, _, _ = temp_io_env

    tx_svc.add_transaction(TransactionCreate(
        transaction_date=date(2026, 3, 1),
        transaction_type="expense",
        amount=500.0,
        category="Food",
        description="Cafe"
    ))

    csv_data = """date,type,amount,category,description
2026-03-01,expense,500.00,Food,Cafe
2026-03-02,expense,800.00,Shopping,Shoes
invalid-date,expense,100.00,Food,Snack
"""
    mapping = {"date": "date", "type": "type", "amount": "amount", "category": "category", "description": "description"}
    valid, errors, dupes = io_svc.parse_and_validate_csv(csv_data, mapping)

    assert len(valid) == 2
    assert len(dupes) == 1
    assert len(errors) == 1

    imported_count = io_svc.import_transactions(valid)
    assert imported_count == 2

def test_database_backup_and_restore(temp_io_env):
    _, tx_svc, backup_svc, temp_db = temp_io_env

    tx_svc.add_transaction(TransactionCreate(
        transaction_date=date.today(),
        transaction_type="income",
        amount=100000.0,
        category="Salary"
    ))

    backup_path = backup_svc.create_backup()
    assert backup_path.exists()

    txs = tx_svc.get_transactions()
    for t in txs:
        tx_svc.delete_transaction(t.id)
    assert tx_svc.count_transactions() == 0

    ok, msg = backup_svc.restore_backup(backup_path)
    assert ok is True
    assert tx_svc.count_transactions() == 1

    if backup_path.exists():
        backup_path.unlink()
