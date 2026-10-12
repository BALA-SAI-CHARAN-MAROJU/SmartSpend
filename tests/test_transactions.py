import tempfile
from pathlib import Path
from datetime import date, timedelta
import pytest
from database.initialization import initialize_database
from models.schemas import TransactionCreate, TransactionUpdate
from services.transaction_service import TransactionService

@pytest.fixture
def temp_service():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        temp_db = Path(f.name)
    initialize_database(temp_db)
    service = TransactionService(temp_db)
    yield service
    if temp_db.exists():
        temp_db.unlink()

def test_add_and_retrieve_transaction(temp_service):
    tx = TransactionCreate(
        transaction_date=date.today(),
        transaction_type="expense",
        amount=125.50,
        category="Food",
        description="Lunch at cafe",
        payment_method="UPI",
        merchant="Cafe Coffee Day"
    )
    tx_id = temp_service.add_transaction(tx)
    assert tx_id > 0

    fetched = temp_service.get_transaction(tx_id)
    assert fetched is not None
    assert fetched.amount == 125.50
    assert fetched.category == "Food"
    assert fetched.amount_cents == 12550

def test_update_transaction(temp_service):
    tx_id = temp_service.add_transaction(TransactionCreate(
        transaction_date=date.today(),
        transaction_type="expense",
        amount=50.0,
        category="Transport",
        description="Bus fare",
        payment_method="Cash"
    ))
    
    updated = temp_service.update_transaction(TransactionUpdate(
        id=tx_id,
        transaction_date=date.today(),
        transaction_type="expense",
        amount=65.0,
        category="Transport",
        description="Metro fare",
        payment_method="UPI"
    ))
    assert updated is True

    fetched = temp_service.get_transaction(tx_id)
    assert fetched.amount == 65.0
    assert fetched.description == "Metro fare"

def test_delete_transaction(temp_service):
    tx_id = temp_service.add_transaction(TransactionCreate(
        transaction_date=date.today(),
        transaction_type="income",
        amount=5000.0,
        category="Salary"
    ))
    assert temp_service.delete_transaction(tx_id) is True
    assert temp_service.get_transaction(tx_id) is None

def test_summary_metrics(temp_service):
    temp_service.add_transaction(TransactionCreate(
        transaction_date=date.today(),
        transaction_type="income",
        amount=10000.0,
        category="Salary"
    ))
    temp_service.add_transaction(TransactionCreate(
        transaction_date=date.today(),
        transaction_type="expense",
        amount=2500.0,
        category="Food"
    ))

    metrics = temp_service.get_summary_metrics()
    assert metrics["total_income"] == 10000.0
    assert metrics["total_expenses"] == 2500.0
    assert metrics["net_savings"] == 7500.0
    assert metrics["savings_rate"] == 75.0
    assert metrics["transaction_count"] == 2
