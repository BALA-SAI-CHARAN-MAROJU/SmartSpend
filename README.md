# 💳 SmartSpend AI — Intelligent Personal Expense Tracker

**SmartSpend AI** is a production-grade, local-first personal finance platform built with Python, Streamlit, SQLite, and Scikit-Learn. It empowers users to track income and expenditures, manage multi-tiered category budgets, achieve savings goals, explore deep spending analytics, detect statistical anomalies, and forecast future expenditure using supervised machine learning.

---

## 🌟 Key Features

1. **Transaction Management & Monetary Integrity**
   - Full CRUD operations with instant search, multi-category filters, date ranges, and pagination.
   - **Zero floating-point rounding errors**: Monetary values are stored as integer minor units (mount_cents / paise) at the SQLite database layer.
   - Comprehensive support for Indian Rupee (₹) number formatting (12,34,567.89) and multi-currency configurations (USD, EUR, GBP, JPY).

2. **Multi-Tiered Budget Tracking**
   - Category-wise monthly and custom period budgets.
   - Dynamic threshold alerts with automated status flags:
     - 🟢 **Normal**: < 75% utilization
     - 🟡 **Warning**: 75% – 89.9%
     - 🟠 **Critical**: 90% – 99.9%
     - 🔴 **Exceeded**: >= 100%

3. **Savings Goals with Dynamic Run Rates**
   - Target tracking with live visual progress meters.
   - Calculates exact daily and monthly savings velocity required to achieve each goal on time.
   - Quick one-click milestone deposits.

4. **Spending Analytics & Continuous Trends**
   - Full temporal reindexing ensuring zero-spend days are correctly factored into running moving averages.
   - Interactive Plotly visualizations:
     - Daily cash-flow income vs. expense trends
     - Interactive category expense distribution donut charts
     - 12-month historical expenditure trajectory
     - Key financial KPIs (Savings Rate %, Daily Expense Averages, Net Savings)

5. **Machine Learning Spending Forecasts**
   - **Calendar Feature Engineering**: Extracts Day of Week, Day of Month, Weekend flags, 1-day lag, and 7-day / 14-day rolling historical averages.
   - **Chronological Time-Series Evaluation**: Strict 80/20 past-to-future temporal train/test split.
   - **Automated Baseline Comparison**: Evaluates **Ridge Regression** and **Random Forest Regressor** against an empirical 7-day Moving Average Baseline.
   - **Production Fallback Protection**: If training data is insufficient (< 14 days) or ML model validation error exceeds the baseline, the system automatically falls back to empirical averages with uncertainty boundary corridors.

6. **Smart Heuristic & Statistical Insights**
   - **Budget Alerts**: Real-time notifications for budgets nearing or exceeding thresholds.
   - **Spike Detection**: Flags categories experiencing spending spikes >= 40% over historical averages.
   - **IQR Anomaly Detection**: Uncovers statistical high-value outlier transactions using Interquartile Range analysis.
   - **Subscription Recurring Tally**: Detects and sums repeating monthly subscriptions.

7. **Privacy, Import/Export & Disaster Recovery**
   - **100% Local-First**: No data leaves your machine; no external API keys required.
   - **CSV Import/Export**: Robust column-mapping import parser with fingerprint duplicate detection (date + amount + category + description).
   - **SQLite Online Backups**: Instant zero-downtime database backups and restore mechanisms verified via PRAGMA integrity_check.

---

## 🏗️ Architecture & Project Structure

`
C:/FAI project/
├── app.py                      # Main application entry point & summary dashboard
├── config.py                   # Central configuration, categories, and ML constants
├── requirements.txt            # Project dependencies
├── models/
│   └── schemas.py              # Pydantic data models & integer unit conversion
├── database/
│   ├── connection.py           # Thread-safe SQLite connection factory with WAL mode
│   ├── initialization.py       # DDL schema definition & migration runner
│   ├── migrations.py           # Database migration runner
│   └── repositories.py         # Repository pattern for transactions, budgets, goals, settings
├── services/
│   ├── transaction_service.py  # Business logic & pagination for transactions
│   ├── budget_service.py       # Budget utilization calculations & threshold alerts
│   ├── savings_service.py      # Goal progress & daily/monthly run rates
│   ├── analytics_service.py    # Continuous trend analysis & category breakdowns
│   ├── prediction_service.py   # Machine learning pipeline, regression & baseline models
│   ├── insight_service.py      # Rule-based heuristics & IQR anomaly detection
│   ├── import_export_service.py# CSV parsing, duplicate deduplication, and export
│   ├── backup_service.py       # SQLite native online backup & restore
│   └── seed_service.py         # Realistic 90-day demonstration data generator
├── components/
│   ├── styles.py               # CSS fintech design tokens & Indian number formatting
│   ├── metric_cards.py         # Custom Streamlit KPI cards
│   ├── charts.py               # Interactive Plotly figures
│   ├── sidebar.py              # Global persistent navigation & metrics
│   └── transaction_forms.py    # Reusable add/edit forms
├── pages/
│   ├── 1_Overview.py           # Financial summary & cash flow overview
│   ├── 2_Transactions.py       # Transaction CRUD ledger with filtering & pagination
│   ├── 3_Budgets.py            # Budget manager & alert tracker
│   ├── 4_Spending_Analytics.py # Deep analytical charts & breakdowns
│   ├── 5_ML_Predictions.py     # Supervised ML forecasting & performance metrics
│   ├── 6_Smart_Insights.py     # Proactive alerts & anomaly reports
│   ├── 7_Savings_Goals.py      # Target savings goal planner
│   ├── 8_Import_Export.py      # CSV batch import & export
│   └── 9_Settings.py           # Preferences, demo data seed & backup management
└── tests/                      # Automated Pytest test suite
    ├── test_database.py
    ├── test_transactions.py
    ├── test_budgets.py
    ├── test_analytics.py
    ├── test_predictions.py
    └── test_import_export.py
`

---

## 🚀 Getting Started

### 1. Requirements
- Python 3.10+ (Tested on Python 3.14)
- Dependencies in 
equirements.txt

### 2. Running the Application
Launch the Streamlit web dashboard:

`ash
streamlit run app.py
`

Or with Python directly:
`ash
python -m streamlit run app.py
`

Access the application in your browser at http://localhost:8501.

### 3. Running the Test Suite
Execute the Pytest test suite:

`ash
pytest -q
`
All 13 unit tests will execute against isolated SQLite instances.