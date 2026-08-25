"""
Módulo de base de datos para Tramitació
Maneja operacions SQLite específiques per al mòdul de Tramitació
"""

import sqlite3
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

from config import DB_FILENAME_TRAMITACIO
from utils import get_data_path
from core.base_database import BaseDatabase

logger = logging.getLogger(__name__)


class TramitacioDatabase(BaseDatabase):
    """Classe per gestionar la base de dades de Tramitació."""

    def __init__(self, db_path: Optional[Path] = None):
        """Inicialitza la connexió a la base de dades de Tramitació."""
        if db_path is None:
            db_path = get_data_path() / DB_FILENAME_TRAMITACIO
        super().__init__(db_path)

    def init_database(self):
        """Inicialitza les taules de la base de dades si no existeixen."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tramitacio (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    numero TEXT NOT NULL,
                    any INTEGER NOT NULL,
                    data TEXT NOT NULL,
                    info TEXT,
                    color TEXT DEFAULT '',
                    reminder_at TEXT DEFAULT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Migració: afegir columna reminder_at si no existeix
            try:
                cursor.execute(
                    "ALTER TABLE tramitacio ADD COLUMN reminder_at TEXT DEFAULT NULL"
                )
            except sqlite3.OperationalError:
                pass  # Ja existeix

            # Netejar duplicats abans de crear l'índex UNIQUE
            self._consolidate_duplicates(conn)

            # Crear índexs
            cursor.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_tramitacio_numero_any
                ON tramitacio(numero, any)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_tramitacio_any
                ON tramitacio(any)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_tramitacio_data
                ON tramitacio(data)
            """)

            logger.info("Taules e índexs de Tramitació creats/verificats")

    def _consolidate_duplicates(self, conn) -> int:
        """Consolida duplicats (numero, any) mantenint el registre més recent.
        La info de tots els duplicats es fusiona en un sol camp amb separador visual.
        Retorna quantitat de registres eliminats."""
        cursor = conn.cursor()
        # Trobar (numero, any) amb més d'un registre
        cursor.execute("""
            SELECT numero, any, COUNT(*) as cnt
            FROM tramitacio
            GROUP BY numero, any
            HAVING cnt > 1
        """)
        duplicats = cursor.fetchall()
        eliminats = 0
        for numero, any_val, _ in duplicats:
            # Seleccionar tots els registres d'aquest (numero, any) ordenats per updated_at DESC
            cursor.execute(
                "SELECT id, data, info, color, reminder_at, created_at, updated_at "
                "FROM tramitacio WHERE numero = ? AND any = ? ORDER BY updated_at DESC",
                (numero, any_val),
            )
            rows = cursor.fetchall()
            if len(rows) <= 1:
                continue
            # Mantenir el primer (més recent) i consolidar la info dels altres
            keep = rows[0]
            keep_id = keep["id"]
            # Consolidar info fusionant totes les info no buides
            consolidated_info = keep["info"] or ""
            for r in rows[1:]:
                if r["info"] and r["info"].strip():
                    consolidated_info = self._merge_info(consolidated_info, r["info"])
            # Actualitzar el registre mantingut amb info consolidada
            cursor.execute(
                "UPDATE tramitacio SET info = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (consolidated_info, keep_id),
            )
            # Eliminar els altres
            ids_to_delete = [r["id"] for r in rows[1:]]
            if ids_to_delete:
                placeholders = ",".join("?" * len(ids_to_delete))
                cursor.execute(
                    f"DELETE FROM tramitacio WHERE id IN ({placeholders})",
                    ids_to_delete,
                )
                eliminats += len(ids_to_delete)
        if eliminats:
            logger.info(f"Duplicats consolidats: {eliminats} registres eliminats")
        return eliminats

    # --- Operacions CRUD per Tramitació ---

    def create_tramit(
        self,
        numero: str,
        any: int,
        data: str,
        info: str = "",
        color: str = "",
        reminder_at: str = None,
    ) -> int:
        """Crea una nova tramitació i retorna el seu ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO tramitacio (numero, any, data, info, color, reminder_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (numero, any, data, info, color, reminder_at),
            )
            tramit_id = cursor.lastrowid
            logger.info(f"Tramitació creada amb ID: {tramit_id}")
            return tramit_id

    def get_tramit(self, tramit_id: int) -> Optional[Dict[str, Any]]:
        """Obté una tramitació per ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tramitacio WHERE id = ?", (tramit_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_tramit(
        self,
        tramit_id: int,
        numero: str,
        any: int,
        data: str,
        info: str,
        color: str = "",
        reminder_at: str = None,
    ) -> bool:
        """Actualitza una tramitació existent."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE tramitacio
                SET numero = ?, any = ?, data = ?, info = ?, color = ?, reminder_at = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """,
                (numero, any, data, info, color, reminder_at, tramit_id),
            )
            updated = cursor.rowcount > 0
            if updated:
                logger.info(f"Tramitació {tramit_id} actualitzada")
            return updated

    def update_color(self, tramit_id: int, color: str) -> bool:
        """Actualitza només el color d'una tramitació."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE tramitacio
                SET color = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """,
                (color, tramit_id),
            )
            updated = cursor.rowcount > 0
            if updated:
                logger.info(f"Color de tramitació {tramit_id} actualitzat a: {color}")
            return updated

    def delete_tramit(self, tramit_id: int) -> bool:
        """Elimina una tramitació."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tramitacio WHERE id = ?", (tramit_id,))
            deleted = cursor.rowcount > 0
            if deleted:
                logger.info(f"Tramitació {tramit_id} eliminada")
            return deleted

    def get_all_tramits(self, color_filter: str = None) -> List[Dict[str, Any]]:
        """Obté totes les tramitacions ordenades per data actualització."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if color_filter:
                cursor.execute(
                    "SELECT * FROM tramitacio WHERE color = ? ORDER BY updated_at DESC",
                    (color_filter,),
                )
            else:
                cursor.execute("SELECT * FROM tramitacio ORDER BY updated_at DESC")
            return [dict(row) for row in cursor.fetchall()]

    def search_tramits(
        self, numero: str = "", any: int = None, color_filter: str = None
    ) -> List[Dict[str, Any]]:
        """Cerca tramitacions per número i/o any i/o color."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM tramitacio WHERE 1=1"
            params = []

            if numero:
                query += " AND numero LIKE ? ESCAPE '\\'"
                # Escapar %, _ i \\ perquè es busquin literalment
                escaped = (
                    numero.replace("\\", "\\\\")
                    .replace("%", "\\%")
                    .replace("_", "\\_")
                )
                params.append(f"%{escaped}%")

            if any is not None:
                query += " AND any = ?"
                params.append(any)

            if color_filter:
                query += " AND color = ?"
                params.append(color_filter)

            query += " ORDER BY data DESC"

            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_tramit_by_numero_any(
        self, numero: str, any: int, exclude_id: int = None
    ) -> Optional[Dict[str, Any]]:
        """Obté una tramitació per número i any. Opcionalment exclou un ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if exclude_id is not None:
                cursor.execute(
                    "SELECT * FROM tramitacio WHERE numero = ? AND any = ? AND id != ?",
                    (numero, any, exclude_id),
                )
            else:
                cursor.execute(
                    "SELECT * FROM tramitacio WHERE numero = ? AND any = ?",
                    (numero, any),
                )
            row = cursor.fetchone()
            return dict(row) if row else None

    def upsert_tramit(
        self,
        numero: str,
        any: int,
        data: str,
        info: str = "",
        color: str = "",
        reminder_at: str = None,
    ) -> int:
        """Insereix o actualitza un tràmit segons número+any. Retorna l'ID.
        Si ja existeix, consolida la info: manté l'antiga i afegeix la nova després."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, info FROM tramitacio WHERE numero = ? AND any = ?",
                (numero, any),
            )
            existing = cursor.fetchone()
            if existing:
                existing_id, old_info = existing["id"], existing["info"] or ""
                # Consolidar info: mantenir l'antiga, afegir la nova després
                consolidated_info = self._merge_info(old_info, info)
                cursor.execute(
                    """
                    UPDATE tramitacio
                    SET data = ?, info = ?, color = ?, reminder_at = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """,
                    (data, consolidated_info, color, reminder_at, existing_id),
                )
                tramit_id = existing_id
                logger.info(f"Tramitació {tramit_id} actualitzada (upsert, info consolidada)")
            else:
                cursor.execute(
                    """
                    INSERT INTO tramitacio (numero, any, data, info, color, reminder_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (numero, any, data, info, color, reminder_at),
                )
                tramit_id = cursor.lastrowid
                logger.info(f"Tramitació creada amb ID: {tramit_id} (upsert)")
            return tramit_id

    def _merge_info(self, old_info: str, new_info: str) -> str:
        old_info = (old_info or "").strip()
        new_info = (new_info or "").strip()
        if not new_info:
            return ""
        if not old_info:
            return new_info
        if old_info == new_info:
            return old_info
        # Evita duplicar si new_info ja és l'últim bloc (cas després d'un merge previ)
        separator = "\n\n--- Dades noves ---\n\n"
        if separator in old_info:
            last_block = old_info.rsplit(separator, 1)[-1].strip()
            if last_block == new_info:
                return old_info
        return f"{old_info}{separator}{new_info}"

    # --- Consultes d'Alarmes ---

    def get_alarms(self, include_past: bool = False) -> List[Dict[str, Any]]:
        """Obté tots els tràmits amb alarma ordenats cronològicament.
        Per defecte només mostra els futurs. include_past=True mostra tot."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if include_past:
                cursor.execute(
                    """
                    SELECT * FROM tramitacio
                    WHERE reminder_at IS NOT NULL AND reminder_at != ''
                    ORDER BY reminder_at ASC
                """
                )
            else:
                cursor.execute(
                    """
                    SELECT * FROM tramitacio
                    WHERE reminder_at IS NOT NULL AND reminder_at != ''
                    AND reminder_at >= datetime('now', '-1 day')
                    ORDER BY reminder_at ASC
                """
                )
            return [dict(row) for row in cursor.fetchall()]

    # --- Operacions de Manteniment ---

    def rebuild_indexes(self) -> str:
        """Reconstrueix tots els índexs de la base de dades."""
        with self._get_connection() as conn:
            conn.execute("REINDEX")
            logger.info("Índexs reconstruïts")
            return "Índexs reconstruïts correctament"

    def update_statistics(self) -> str:
        """Actualitza les estadístiques de la base de dades per optimitzar consultes."""
        with self._get_connection() as conn:
            conn.execute("ANALYZE")
            logger.info("Estadístiques actualitzades")
            return "Estadístiques actualitzades correctament"

    def purge_old_records(self, days: int = 365) -> int:
        """Elimina registres anteriors a N dies. Retorna la quantitat eliminada."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                DELETE FROM tramitacio
                WHERE updated_at < datetime('now', ? || ' days')
                """,
                (f"-{days}",),
            )
            deleted = cursor.rowcount
            if deleted:
                logger.info(f"Purga: {deleted} registres eliminats (>{days} dies)")
            return deleted

    def vacuum(self) -> str:
        """Redueix l'espai no utilitzat de la base de dades."""
        with self._get_connection() as conn:
            conn.execute("VACUUM")
            logger.info("VACUUM completat")
            return "Base de dades optimitzada (VACUUM)"

    def get_database_stats(self) -> Dict[str, Any]:
        """Retorna estadístiques de la base de dades."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Nombre total de registres
            cursor.execute("SELECT COUNT(*) FROM tramitacio")
            total = cursor.fetchone()[0]
            # Registres per color
            cursor.execute(
                "SELECT color, COUNT(*) as cnt FROM tramitacio GROUP BY color ORDER BY cnt DESC"
            )
            by_color = {row["color"] or "(sense color)": row["cnt"] for row in cursor.fetchall()}
            # Registres per any
            cursor.execute(
                "SELECT any, COUNT(*) as cnt FROM tramitacio GROUP BY any ORDER BY any DESC"
            )
            by_year = {row["any"]: row["cnt"] for row in cursor.fetchall()}
            # Registres duplicats (si n'hi ha)
            cursor.execute(
                "SELECT COUNT(*) FROM ("
                "  SELECT numero, any FROM tramitacio GROUP BY numero, any HAVING COUNT(*) > 1"
                ")"
            )
            duplicates = cursor.fetchone()[0]
            # Mida del fitxer
            db_path = self.db_path
            size_bytes = db_path.stat().st_size if db_path.exists() else 0
            size_mb = size_bytes / (1024 * 1024)
            return {
                "total_records": total,
                "by_color": by_color,
                "by_year": by_year,
                "duplicates": duplicates,
                "file_size_mb": round(size_mb, 2),
            }
