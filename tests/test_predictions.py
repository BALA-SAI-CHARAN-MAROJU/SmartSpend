import tempfile
from pathlib import Path
from datetime import date, timedelta
import pytest
from database.initialization import initialize_database
from models.schemas import TransactionCreate
from services.prediction_service import PredictionService
from services.transaction_service import TransactionService

@pytest.fixture
def temp_pred_env():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        temp_db = Path(f.name)
    initialize_database(temp_db)
    p_service = PredictionService(temp_db)
    tx_service = TransactionService(temp_db)
    yield p_service, tx_service, temp_db
    if temp_db.exists():
        temp_db.unlink()

def test_sparse_data_graceful_fallback(temp_pred_env):
    p_service, tx_service, _ = temp_pred_env
    today = date.today()
    for j in range(3):
        tx_service.add_transaction(TransactionCreate(
            transaction_date=today - timedelta(days=j),
            transaction_type="expense",
            amount=500.0,
            category="Food"
        ))

    res = p_service.predict_current_month_expenditure()
    assert res["status"] in ["insufficient_data", "fallback_provisional"]
    assert "projected_total" in res
    assert res["projected_total"] >= 0

def test_ml_pipeline_with_sufficient_history(temp_pred_env):
    p_service, tx_service, _ = temp_pred_env
    today = date.today()
    for i in range(30):
        tx_service.add_transaction(TransactionCreate(
            transaction_date=today - timedelta(days=30 - i),
            transaction_type="expense",
            amount=400.0 + (i % 5) * 50.0,
            category="Food"
        ))

    eval_res = p_service.evaluate_models()
    assert eval_res["status"] == "success"
    assert "baseline_mae" in eval_res
    assert "ridge_mae" in eval_res
    assert "rf_mae" in eval_res

    pred = p_service.predict_current_month_expenditure()
    assert pred["projected_total"] > 0
    assert len(pred["daily_forecasts"]) == pred["remaining_days"]
