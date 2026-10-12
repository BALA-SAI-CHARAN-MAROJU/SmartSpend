import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
ARTIFACTS_DIR = BASE_DIR / "artifacts"
BACKUPS_DIR = BASE_DIR / "backups"

DATA_DIR.mkdir(exist_ok=True)
ARTIFACTS_DIR.mkdir(exist_ok=True)
BACKUPS_DIR.mkdir(exist_ok=True)

DEFAULT_DB_PATH = DATA_DIR / "smartspend.db"

DEFAULT_CURRENCY = "INR"
CURRENCY_SYMBOLS = {
    "INR": "₹",
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
    "JPY": "¥",
}

DEFAULT_EXPENSE_CATEGORIES = [
    "Food & Dining",
    "Groceries",
    "Travel",
    "Transport",
    "Education",
    "Shopping", "Entertainment",
    "Gaming", "Health",
    "Bills", "Rent",
    "Personal Care", "Subscriptions",
    "Other",
]

DEFAULT_INCOME_CATEGORIES = [
    "Salary", "Allowance",
    "Freelance", "Scholarship",
    "Investment Income", "Other",
]

DEFAULT_PAYMENT_METHODS = [
    "UPI", "Credit Card",
    "Debit Card", "Bank Transfer",
    "Cash", "Other",
]

BUDGET_WARNING_THRESHOLD = 0.75
BUDGET_CRITICAL_THRESHOLD = 0.90
BUDGET_EXCEEDED_THRESHOLD = 1.00

MIN_DAYS_FOR_ML = 14
PREDICTION_DAYS_LOOKBACK = 90
RANDOM_SEED = 42
