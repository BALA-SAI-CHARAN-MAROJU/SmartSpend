from pathlib import Path
from datetime import date, timedelta, datetime
import calendar
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from services.transaction_service import TransactionService
import config

class PredictionService:
    def __init__(self, db_path: Path | str | None = None):
        self.tx_service = TransactionService(db_path)

    def prepare_daily_dataset(self) -> pd.DataFrame:
        df = self.tx_service.get_as_dataframe(tx_type="expense")
        if df.empty or len(df) < 5:
            return pd.DataFrame()

        df["date"] = pd.to_datetime(df["date"]).dt.normalize()
        daily = df.groupby("date")["amount"].sum().reset_index()

        full_idx = pd.date_range(start=daily["date"].min(), end=daily["date"].max(), freq="D")
        daily = daily.set_index("date").reindex(full_idx, fill_value=0.0).reset_index()
        daily.columns = ["date", "amount"]

        daily["day_of_week"] = daily["date"].dt.dayofweek
        daily["day_of_month"] = daily["date"].dt.day
        daily["is_weekend"] = daily["day_of_week"].isin([5, 6]).astype(int)
        
        daily["lag_1"] = daily["amount"].shift(1).fillna(daily["amount"].mean())
        daily["roll_7_mean"] = daily["amount"].shift(1).rolling(window=7, min_periods=1).mean().fillna(daily["amount"].mean())
        daily["roll_14_mean"] = daily["amount"].shift(1).rolling(window=14, min_periods=1).mean().fillna(daily["amount"].mean())

        return daily

    def evaluate_models(self) -> Dict[str, Any]:
        data = self.prepare_daily_dataset()
        if len(data) < config.MIN_DAYS_FOR_ML:
            return {
                "status": "insufficient_data",
                "days_count": len(data),
                "min_days_required": config.MIN_DAYS_FOR_ML,
                "message": f"Only {len(data)} continuous days available. Need at least {config.MIN_DAYS_FOR_ML} days to train ML models."
            }

        feature_cols = ["day_of_week", "day_of_month", "is_weekend", "lag_1", "roll_7_mean", "roll_14_mean"]
        
        split_idx = int(len(data) * 0.8)
        if (len(data) - split_idx) < 3:
            split_idx = len(data) - 3

        train = data.iloc[:split_idx]
        test = data.iloc[split_idx:]

        X_train, y_train = train[feature_cols], train["amount"]
        X_test, y_test = test[feature_cols], test["amount"]

        # 1. Baseline
        baseline_pred = np.full(len(test), train["amount"].tail(7).mean())
        baseline_mae = mean_absolute_error(y_test, baseline_pred)
        baseline_rmse = np.sqrt(mean_squared_error(y_test, baseline_pred))

        # 2. Ridge
        ridge = Ridge(alpha=1.0, random_state=config.RANDOM_SEED)
        ridge.fit(X_train, y_train)
        ridge_pred = np.clip(ridge.predict(X_test), 0, None)
        ridge_mae = mean_absolute_error(y_test, ridge_pred)
        ridge_rmse = np.sqrt(mean_squared_error(y_test, ridge_pred))

        # 3. Random Forest
        rf = RandomForestRegressor(n_estimators=50, max_depth=5, random_state=config.RANDOM_SEED)
        rf.fit(X_train, y_train)
        rf_pred = np.clip(rf.predict(X_test), 0, None)
        rf_mae = mean_absolute_error(y_test, rf_pred)
        rf_rmse = np.sqrt(mean_squared_error(y_test, rf_pred))

        candidates = [
            ("Baseline (7-Day Average)", baseline_mae, baseline_rmse, None),
            ("Ridge Regression", ridge_mae, ridge_rmse, ridge),
            ("Random Forest Regressor", rf_mae, rf_rmse, rf),
        ]
        candidates.sort(key=lambda x: x[1])

        best_name, best_mae, best_rmse, best_model = candidates[0]
        use_ml = (best_model is not None) and (best_mae < baseline_mae)

        return {
            "status": "success",
            "days_count": len(data),
            "train_days": len(train),
            "test_days": len(test),
            "baseline_mae": round(baseline_mae, 2),
            "baseline_rmse": round(baseline_rmse, 2),
            "ridge_mae": round(ridge_mae, 2),
            "ridge_rmse": round(ridge_rmse, 2),
            "rf_mae": round(rf_mae, 2),
            "rf_rmse": round(rf_rmse, 2),
            "champion_model_name": best_name if use_ml else "Baseline (Moving Average)",
            "use_ml": use_ml,
            "best_mae": round(best_mae if use_ml else baseline_mae, 2),
            "model_obj": best_model if use_ml else None,
            "feature_cols": feature_cols,
            "data": data
        }

    def predict_current_month_expenditure(self) -> Dict[str, Any]:
        today = date.today()
        first_day_of_month = date(today.year, today.month, 1)
        _, num_days_in_month = calendar.monthrange(today.year, today.month)
        last_day_of_month = date(today.year, today.month, num_days_in_month)
        elapsed_days = today.day
        remaining_days = num_days_in_month - elapsed_days

        month_txs = self.tx_service.get_transactions(
            start_date=first_day_of_month,
            end_date=today,
            tx_type="expense"
        )
        actual_spent_so_far = sum(t.amount for t in month_txs)

        eval_res = self.evaluate_models()

        if eval_res.get("status") == "insufficient_data":
            avg_daily = (actual_spent_so_far / max(1, elapsed_days)) if actual_spent_so_far > 0 else 0.0
            forecast_remaining = avg_daily * remaining_days
            projected_total = actual_spent_so_far + forecast_remaining

            return {
                "status": "fallback_provisional",
                "model_used": "Provisional Daily Average Baseline",
                "actual_spent_so_far": round(actual_spent_so_far, 2),
                "forecast_remaining": round(forecast_remaining, 2),
                "projected_total": round(projected_total, 2),
                "elapsed_days": elapsed_days,
                "remaining_days": remaining_days,
                "days_in_month": num_days_in_month,
                "eval_res": eval_res,
                "daily_forecasts": [
                    {
                        "date": (today + timedelta(days=i + 1)).strftime("%Y-%m-%d"),
                        "predicted_spend": round(avg_daily, 2),
                        "lower_bound": round(max(0, avg_daily * 0.7), 2),
                        "upper_bound": round(avg_daily * 1.3, 2),
                    }
                    for i in range(remaining_days)
                ]
            }

        data = eval_res["data"]
        model = eval_res["model_obj"]
        use_ml = eval_res["use_ml"]
        feature_cols = eval_res["feature_cols"]

        daily_forecasts = []
        forecast_sum = 0.0

        current_lag1 = data["amount"].iloc[-1] if not data.empty else 0.0
        recent_amounts = list(data["amount"].tail(14)) if not data.empty else [0.0]

        for i in range(remaining_days):
            forecast_date = today + timedelta(days=i + 1)
            dow = forecast_date.weekday()
            dom = forecast_date.day
            is_wknd = 1 if dow in [5, 6] else 0
            roll_7 = np.mean(recent_amounts[-7:]) if len(recent_amounts) >= 7 else np.mean(recent_amounts)
            roll_14 = np.mean(recent_amounts[-14:]) if len(recent_amounts) >= 14 else np.mean(recent_amounts)

            if use_ml and model is not None:
                feat_df = pd.DataFrame([{
                    "day_of_week": dow,
                    "day_of_month": dom,
                    "is_weekend": is_wknd,
                    "lag_1": current_lag1,
                    "roll_7_mean": roll_7,
                    "roll_14_mean": roll_14,
                }])[feature_cols]
                pred_val = float(np.clip(model.predict(feat_df)[0], 0, None))
            else:
                pred_val = float(max(0.0, roll_7))

            mae_uncertainty = eval_res.get("best_mae", 50.0)
            daily_forecasts.append({
                "date": forecast_date.strftime("%Y-%m-%d"),
                "predicted_spend": round(pred_val, 2),
                "lower_bound": round(max(0.0, pred_val - mae_uncertainty), 2),
                "upper_bound": round(pred_val + mae_uncertainty, 2),
            })
            forecast_sum += pred_val
            current_lag1 = pred_val
            recent_amounts.append(pred_val)

        projected_total = actual_spent_so_far + forecast_sum

        return {
            "status": "success",
            "model_used": eval_res["champion_model_name"],
            "actual_spent_so_far": round(actual_spent_so_far, 2),
            "forecast_remaining": round(forecast_sum, 2),
            "projected_total": round(projected_total, 2),
            "elapsed_days": elapsed_days,
            "remaining_days": remaining_days,
            "days_in_month": num_days_in_month,
            "eval_res": eval_res,
            "daily_forecasts": daily_forecasts
        }
