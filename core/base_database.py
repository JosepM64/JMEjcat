"""
Base database class with shared connection management.
"""

import logging
import sqlite3
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

logger = logging.getLogger(__name__)


class BaseDatabase:
    """Base class for database connections with WAL and foreign keys.

    La connexió és compartida entre threads (check_same_thread=False),
    protegida per un Lock per evitar problemes de concurrència.
    Inclou sistema de migracions versionades (taula schema_version).
    """

    def __init__(self, db_path: Path):
        """Initialize database connection."""
        self.db_path = db_path
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        # Esperar fins 5s si la BD està bloquejada per un altre thread/procés
        self._conn.execute("PRAGMA busy_timeout=5000")
        self._ensure_schema_version_table()
        self.init_database()
        self.migrate()
        logger.info(f"Database initialized at: {db_path}")

    # --- Migracions versionades (2.10) ---

    def _ensure_schema_version_table(self) -> None:
        """Crea la taula schema_version si no existeix."""
        try:
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY
                )
            """)
            self._conn.commit()
        except Exception as e:
            logger.warning(f"No s'ha pogut crear schema_version: {e}")

    def _get_schema_version(self) -> int:
        """Retorna la versió actual de l'esquema (0 si no existeix)."""
        try:
            cur = self._conn.execute("SELECT version FROM schema_version ORDER BY version DESC LIMIT 1")
            row = cur.fetchone()
            return int(row[0]) if row else 0
        except Exception:
            return 0

    def _set_schema_version(self, version: int) -> None:
        """Desa la versió de l'esquema."""
        try:
            self._conn.execute("DELETE FROM schema_version")
            self._conn.execute("INSERT INTO schema_version (version) VALUES (?)", (version,))
            self._conn.commit()
        except Exception as e:
            logger.warning(f"No s'ha pogut desar schema_version {version}: {e}")

    def migrate(self) -> None:
        """Sistema de migracions versionades.

        Compara la versió actual (schema_version) amb la desitjada
        (config.DB_VERSION) i aplica migracions incrementals.
        Les subclasses poden sobreescriure _apply_migration().
        """
        try:
            from config import DB_VERSION as target_version
        except ImportError:
            target_version = 1
        current = self._get_schema_version()
        if current == 0:
            # Primera inicialització: establir directament a target
            self._set_schema_version(target_version)
            logger.info(f"schema_version inicialitzat a {target_version} per {self.db_path.name}")
            return
        if current >= target_version:
            return
        logger.info(f"Migració {self.db_path.name}: {current} -> {target_version}")
        for v in range(current + 1, target_version + 1):
            try:
                self._apply_migration(v)
                self._set_schema_version(v)
                logger.info(f"Migració a v{v} completada per {self.db_path.name}")
            except Exception as e:
                logger.error(f"Error en migració a v{v} per {self.db_path.name}: {e}")
                raise

    def _apply_migration(self, target_version: int) -> None:
        """Aplica una migració incremental. Sobre-escriure a subclasses.

        Args:
            target_version: versió destí (ex. 2 vol dir migrar de 1 a 2).
        """
        # Base no fa res; subclasses implementen lògica específica
        logger.info(f"Cap migració específica per v{target_version} a {self.__class__.__name__}")

    def close(self) -> None:
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
    def _get_connection(self) -> Iterator[sqlite3.Connection]:
        """Context manager for operations (reuses persistent connection).

        Thread-safe: serialitza l'accés amb un Lock perquè la connexió
        és compartida entre fils (UI, exportadors, etc.).
        """
        with self._lock:
            try:
                yield self._conn
                self._conn.commit()
            except Exception as e:
                self._conn.rollback()
                raise e

    def init_database(self) -> None:
        """Initialize database tables. Override in subclasses."""
        pass
