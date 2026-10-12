from pathlib import Path
import sqlite3
import config
from database.connection import get_connection

INITIAL_SCHEMA = """
-- Schema migration tracker
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Transactions table storing monetary values in integer minor units (amount_cents)
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_date TEXT NOT NULL,
    transaction_type TEXT NOT NULL CHECK(transaction_type IN ('income', 'expense')),
    amount_cents INTEGER NOT NULL CHECK(amount_cents > 0),
    category TEXT NOT NULL,
    description TEXT DEFAULT '',
    payment_method TEXT DEFAULT 'Other',
    merchant TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(transaction_date);
CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(transaction_type);
CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category);
CREATE INDEX IF NOT EXISTS idx_transactions_date_type ON transactions(transaction_date, transaction_type);

-- Budgets table
CREATE TABLE IF NOT EXISTS budgets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    budget_amount_cents INTEGER NOT NULL CHECK(budget_amount_cents > 0),
    period_type TEXT NOT NULL DEFAULT 'monthly',
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(category, period_type, start_date, end_date)
);

CREATE INDEX IF NOT EXISTS idx_budgets_dates ON budgets(start_date, end_date);

-- Savings goals table
CREATE TABLE IF NOT EXISTS savings_goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    goal_name TEXT NOT NULL,
    target_amount_cents INTEGER NOT NULL CHECK(target_amount_cents > 0),
    current_amount_cents INTEGER NOT NULL DEFAULT 0 CHECK(current_amount_cents >= 0),
    target_date TEXT NOT NULL,
    description TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Application settings key-value store
CREATE TABLE IF NOT EXISTS app_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Custom Categories
CREATE TABLE IF NOT EXISTS custom_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    category_type TEXT NOT NULL CHECK(category_type IN ('income', 'expense')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

def initialize_database(db_path: Path | str | None = None) -> None:
    """Initializes SQLite database tables and default configuration if not present."""
    conn = get_connection(db_path)
    try:
        with conn:
            conn.executescript(INITIAL_SCHEMA)
            
            # Default settings
            default_settings = [
                ("currency", config.DEFAULT_CURRENCY),
                ("monthly_budget", "50000"),  # Default ₹50,000 monthly budget
                ("theme", "light"),
                ("first_day_of_week", "Monday"),
                ("date_format", "DD/MM/YYYY"),
            ]
            for key, val in default_settings:
                conn.execute(
                    "INSERT OR IGNORE INTO app_settings (key, value) VALUES (?, ?)",
                    (key, val)
                )

            # Record version 1 migration
            conn.execute("INSERT OR IGNORE INTO schema_migrations (version) VALUES (1)")
    finally:
        conn.close()

if __name__ == "__main__":
    initialize_database()
    print("Database initialized successfully.")
