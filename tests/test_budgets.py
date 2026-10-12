import tempfile
from pathlib import Path
from datetime import date, timedelta
import pytest
from database.initialization import initialize_database
from models.schemas import BudgetCreate, TransactionCreate
from services.budget_service import BudgetService
from services.transaction_service import TransactionService

@pytest.fixture
def temp_budget_env():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        temp_db = Path(f.name)
    initialize_database(temp_db)
    b_service = BudgetService(temp_db)
    tx_service = TransactionService(temp_db)
    yield b_service, tx_service, temp_db
    if temp_db.exists():
        temp_db.unlink()

def test_budget_threshold_alerts(temp_budget_env):
    b_service, tx_service, _ = temp_budget_env
    today = date.today()
    start_d = today - timedelta(days=10)
    end_d = today + timedelta(days=20)

    b_id = b_service.set_budget(BudgetCreate(
        category="Groceries",
        budget_amount=1000.0,
        period_type="monthly",
        start_date=start_d,
        end_date=end_d
    ))
    assert b_id > 0

    tx_service.add_transaction(TransactionCreate(
        transaction_date=today,
        transaction_type="expense",
        amount=500.0,
        category="Groceries"
    ))
    statuses = b_service.get_budget_status(today)
    assert len(statuses) == 1
    assert statuses[0]["alert_level"] == "normal"
    assert statuses[0]["utilization_pct"] == 50.0

    tx_service.add_transaction(TransactionCreate(
        transaction_date=today,
        transaction_type="expense",
        amount=300.0,
        category="Groceries"
    ))
    statuses = b_service.get_budget_status(today)
    assert statuses[0]["alert_level"] == "warning"
    assert statuses[0]["utilization_pct"] == 80.0

    tx_service.add_transaction(TransactionCreate(
        transaction_date=today,
        transaction_type="expense",
        amount=150.0,
        category="Groceries"
    ))
    statuses = b_service.get_budget_status(today)
    assert statuses[0]["alert_level"] == "critical"

    tx_service.add_transaction(TransactionCreate(
        transaction_date=today,
        transaction_type="expense",
        amount=100.0,
        category="Groceries"
    ))
    statuses = b_service.get_budget_status(today)
    assert statuses[0]["alert_level"] == "exceeded"
