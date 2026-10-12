import tempfile
from pathlib import Path
from datetime import date, timedelta
import pytest
from database.initialization import initialize_database
from models.schemas import TransactionCreate
from services.analytics_service import AnalyticsService
from services.transaction_service import TransactionService

@pytest.fixture
def temp_analytics_env():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        temp_db = Path(f.name)
    initialize_database(temp_db)
    a_service = AnalyticsService(temp_db)
    tx_service = TransactionService(temp_db)
    yield a_service, tx_service, temp_db
    if temp_db.exists():
        temp_db.unlink()

def test_category_breakdown_and_math_reconciliation(temp_analytics_env):
    a_service, tx_service, _ = temp_analytics_env
    today = date.today()

    tx_service.add_transaction(TransactionCreate(
        transaction_date=today,
        transaction_type="expense",
        amount=300.0,
        category="Food"
    ))
    tx_service.add_transaction(TransactionCreate(
        transaction_date=today,
        transaction_type="expense",
        amount=700.0,
        category="Food"
    ))
    tx_service.add_transaction(TransactionCreate(
        transaction_date=today,
        transaction_type="expense",
        amount=1000.0,
        category="Rent"
    ))

    cat_df = a_service.get_spending_by_category()
    assert not cat_df.empty
    assert cat_df["total_amount"].sum() == 2000.0

    food_row = cat_df[cat_df["category"] == "Food"].iloc[0]
    assert food_row["total_amount"] == 1000.0
    assert food_row["percentage"] == 50.0

def test_empty_dataset_handling(temp_analytics_env):
    a_service, _, _ = temp_analytics_env
    cat_df = a_service.get_spending_by_category()
    assert cat_df.empty

    trend_df = a_service.get_daily_spending_trend()
    assert trend_df.empty

    metrics = a_service.get_deep_analytics_metrics()
    assert metrics["avg_daily_spend"] == 0.0
