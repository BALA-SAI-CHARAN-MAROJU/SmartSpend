import shutil
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Tuple
import config

class BackupService:
    def __init__(self, db_path: Path | str | None = None):
        self.db_path = Path(db_path) if db_path else config.DEFAULT_DB_PATH
        self.backup_dir = config.BACKUPS_DIR

    def create_backup(self) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"smartspend_backup_{timestamp}.db"
        
        src_conn = sqlite3.connect(str(self.db_path))
        dst_conn = sqlite3.connect(str(backup_file))
        try:
            with dst_conn:
                src_conn.backup(dst_conn)
        finally:
            src_conn.close()
            dst_conn.close()

        return backup_file

    def restore_backup(self, backup_file_path: Path | str) -> Tuple[bool, str]:
        src = Path(backup_file_path)
        if not src.exists():
            return False, f"Backup file {src} does not exist."

        try:
            test_conn = sqlite3.connect(str(src))
            cursor = test_conn.cursor()
            cursor.execute("PRAGMA integrity_check;")
            res = cursor.fetchone()
            if not res or res[0] != "ok":
                test_conn.close()
                return False, "Backup file failed SQLite integrity check."
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='transactions'")
            if not cursor.fetchone():
                test_conn.close()
                return False, "Backup is missing essential 'transactions' table."
            test_conn.close()

            src_conn = sqlite3.connect(str(src))
            dst_conn = sqlite3.connect(str(self.db_path))
            try:
                with dst_conn:
                    src_conn.backup(dst_conn)
            finally:
                src_conn.close()
                dst_conn.close()

            return True, "Database successfully restored from backup."
        except Exception as e:
            return False, f"Failed to restore backup: {str(e)}"
