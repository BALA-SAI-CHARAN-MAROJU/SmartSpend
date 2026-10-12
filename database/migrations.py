from pathlib import Path
import sqlite3
from database.connection import get_connection

def run_migrations(db_path: Path | str | None = None) -> None:
    """Safe schema migrations framework for future schema evolution."""
    conn = get_connection(db_path)
    try:
        with conn:
            # Check applied migrations
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='schema_migrations'")
            if not cursor.fetchone():
                return
            cursor.execute("SELECT version FROM schema_migrations ORDER BY version")
            applied = {row[0] for row in cursor.fetchall()}
    finally:
        conn.close()
