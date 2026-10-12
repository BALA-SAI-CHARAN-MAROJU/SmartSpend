import tempfile
import sqlite3
from pathlib import Path
from datetime import date
import pytest
from database.initialization import initialize_database
from database.connection import get_connection
from database.repositories import SettingsRepository

def test_database_initialization():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        temp_db = Path(f.name)
    try:
        initialize_database(temp_db)
        conn = get_connection(temp_db)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        assert "transactions" in tables
        assert "budgets" in tables
        assert "savings_goals" in tables
        assert "app_settings" in tables
        assert "schema_migrations" in tables

        settings_repo = SettingsRepository(temp_db)
        assert settings_repo.get("currency") == "INR"
        assert settings_repo.get("theme") == "light"
        conn.close()
    finally:
        if temp_db.exists():
            temp_db.unlink()

def test_data_persistence_across_reconnects():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        temp_db = Path(f.name)
    try:
        initialize_database(temp_db)
        settings_repo = SettingsRepository(temp_db)
        settings_repo.set("custom_key", "persisted_value")

        repo2 = SettingsRepository(temp_db)
        assert repo2.get("custom_key") == "persisted_value"
    finally:
        if temp_db.exists():
            temp_db.unlink()
