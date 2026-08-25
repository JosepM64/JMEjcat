"""
Base database class with shared connection management.
"""

import sqlite3
import logging
from pathlib import Path
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class BaseDatabase:
    """Base class for database connections with WAL and foreign keys."""

    def __init__(self, db_path: Path):
        """Initialize database connection."""
        self.db_path = db_path
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self.init_database()
        logger.info(f"Database initialized at: {db_path}")

    def close(self):
        """Close the database connection."""
        try:
            if hasattr(self, "_conn") and self._conn:
                self._conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                self._conn.commit()
                self._conn.close()
                logger.info("Database connection closed (WAL checkpoint done)")
        except Exception as e:
            logger.warning(f"Error closing database connection: {e}")

    @contextmanager
    def _get_connection(self):
        """Context manager for operations (reuses persistent connection)."""
        try:
            yield self._conn
            self._conn.commit()
        except Exception as e:
            self._conn.rollback()
            raise e

    def init_database(self):
        """Initialize database tables. Override in subclasses."""
        pass
