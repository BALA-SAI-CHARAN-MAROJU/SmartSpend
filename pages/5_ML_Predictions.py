import streamlit as st
import pandas as pd
from database.initialization import initialize_database
from database.repositories import SettingsRepository
from services.prediction_service import PredictionService
from components.styles import apply_custom_styles, format_currency
from components.metric_cards import render_metric_card, render_text_metric_card
from components.charts import create_forecast_chart
from components.sidebar import render_sidebar

st.set_page_config(page_title="SmartSpend AI - ML Predictions", page_icon="💳", layout="wide")
initialize_database()
apply_custom_styles()
render_sidebar()

st.title("Machine Learning Spending Forecast")
st.caption("Empirical time-series expenditure prediction with automated baseline comparison.")

settings_repo = SettingsRepository()
currency = settings_repo.get("currency", "INR")
monthly_budget = float(settings_repo.get("monthly_budget", "50000"))

pred_service = PredictionService()
result = pred_service.predict_current_month_expenditure()
eval_res = result.get("eval_res", {})

if result.get("status") == "insufficient_data":
    st.warning("⚠️ Insufficient historical data for full machine learning model training.")
    st.info(result.get("message", "Need at least 14 days of expense history."))
else:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_metric_card("Spent So Far This Month", result["actual_spent_so_far"], currency=currency, subtext=f"Day 1 to {result['elapsed_days']}")
    with col2:
        render_metric_card("Forecasted (Remaining Days)", result["forecast_remaining"], currency=currency, subtext=f"Next {result['remaining_days']} days")
    with col3:
        render_metric_card("Projected Total Month Spend", result["projected_total"], currency=currency, subtext=f"Model: {result['model_used']}")
    with col4:
        diff = monthly_budget - result["projected_total"]
        if diff >= 0:
            render_metric_card("Expected Budget Surplus", diff, currency=currency, subtext="Within Budget")
        else:
            render_metric_card("Expected Overspend", abs(diff), currency=currency, subtext="Exceeds Budget")

    st.markdown("---")

    st.markdown("### Daily Forecast with Uncertainty Bounds")
    recent_history = eval_res.get("data", pd.DataFrame()).tail(30)
    st.plotly_chart(create_forecast_chart(result["daily_forecasts"], recent_history), use_container_width=True)

    st.markdown("### Model Benchmark & Evaluation")
    if eval_res.get("status") == "success":
        eval_cols = st.columns(3)
        with eval_cols[0]:
            st.metric(
                "Baseline (7-Day MA) MAE",
                format_currency(eval_res["baseline_mae"], currency),
                help="Mean Absolute Error of simple 7-day moving average"
            )
        with eval_cols[1]:
            st.metric(
                "Ridge Regression MAE",
                format_currency(eval_res["ridge_mae"], currency),
                help="L2 regularized linear model with lag & calendar features"
            )
        with eval_cols[2]:
            st.metric(
                "Random Forest MAE",
                format_currency(eval_res["rf_mae"], currency),
                help="Non-linear ensemble trees regressor"
            )

        st.info(
            f"🏆 **Selected Model**: **{result['model_used']}**.\n\n"
            f"Chronological holdout validation: trained on {eval_res['train_days']} historical days and tested on {eval_res['test_days']} unseen days. "
            f"If ML models perform worse than the empirical baseline, the system automatically falls back to the baseline."
        )
    else:
        st.info("Using provisional baseline average as dataset is growing.")

    with st.expander("📅 View Detailed Daily Forecast Values"):
        forecast_df = pd.DataFrame(result["daily_forecasts"])
        if not forecast_df.empty:
            forecast_df["predicted_spend"] = forecast_df["predicted_spend"].apply(lambda x: format_currency(x, currency))
            forecast_df["lower_bound"] = forecast_df["lower_bound"].apply(lambda x: format_currency(x, currency))
            forecast_df["upper_bound"] = forecast_df["upper_bound"].apply(lambda x: format_currency(x, currency))
            forecast_df.columns = ["Date", "Forecasted Spend", "Lower Bound (-MAE)", "Upper Bound (+MAE)"]
            st.dataframe(forecast_df, use_container_width=True, hide_index=True)
