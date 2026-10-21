"""
Módulo de base de datos para JMEJCat
Maneja todas las operaciones con SQLite
"""

import logging
from pathlib import Path
from typing import Any, cast

from config import DB_FILENAME
from core.base_database import BaseDatabase
from utils import get_data_path

logger = logging.getLogger(__name__)


class Database(BaseDatabase):
    """Clase principal para manejar operaciones de base de datos."""

    def __init__(self, db_path: Path | None = None):
        """Inicializa la conexión a la base de datos."""
        if db_path is None:
            db_path = get_data_path() / DB_FILENAME
        super().__init__(db_path)

    def init_database(self) -> None:
        """Inicializa las tablas de la base de datos si no existen."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL CHECK(length(title) BETWEEN 1 AND 100),
                    request TEXT,
                    solution TEXT,
                    examples TEXT CHECK(examples IS NULL OR length(examples) <= 500),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS images (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    note_id INTEGER NOT NULL,
                    filename TEXT NOT NULL,
                    thumb_filename TEXT NOT NULL,
                    sort_order INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE CASCADE
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_notes_title
                ON notes(title)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_images_note
                ON images(note_id)
            """)

            logger.info("Tablas e índices creados/verificados")

    def _apply_migration(self, target_version: int) -> None:
        """Migració v2: afegeix CHECK constraints (validades prèviament a C:/varis/JMEJCat 0 violacions)."""
        if target_version == 2:
            # La taula ja existeix sense CHECK en instal·lacions antigues.
            # El CREATE IF NOT EXISTS no la modifica, però les noves instal·lacions
            # sí tindran els CHECK. Per a BD existents, validem i informem.
            try:
                with self._get_connection() as conn:
                    cur = conn.cursor()
                    cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='notes'")
                    row = cur.fetchone()
                    sql = row[0] if row else ""
                    if "CHECK" not in sql:
                        logger.info("Migració v2: notes sense CHECK (BD existent) — es manté compatibilitat; nous registres seran validats a nivell d'aplicació")
            except Exception as e:
                logger.warning(f"Migració v2 notes: {e}")
        else:
            super()._apply_migration(target_version)

    def _validate_note_fields(self, title: str, examples: str) -> None:
        """Valida camps abans d'inserir (mirall dels CHECK de la BD)."""
        if not (1 <= len(title) <= 100):
            raise ValueError(f"Títol ha de tenir 1-100 caràcters (actual {len(title)})")
        if examples is not None and len(examples) > 500:
            raise ValueError(f"Exemples màxim 500 caràcters (actual {len(examples)})")

    # --- Operaciones CRUD para notas ---

    def create_note(
        self, title: str, request: str = "", solution: str = "", examples: str = ""
    ) -> int:
        """Crea una nueva nota y devuelve su ID."""
        self._validate_note_fields(title, examples)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO notes (title, request, solution, examples)
                VALUES (?, ?, ?, ?)
            """,
                (title, request, solution, examples),
            )
            note_id = cast(int, cursor.lastrowid)
            logger.info(f"Nota creada con ID: {note_id}")
            return note_id

    def get_note(self, note_id: int) -> dict[str, Any] | None:
        """Obtiene una nota por su ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM notes WHERE id = ?", (note_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_note(
        self, note_id: int, title: str, request: str, solution: str, examples: str
    ) -> bool:
        """Actualiza una nota existente."""
        self._validate_note_fields(title, examples)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE notes
                SET title = ?, request = ?, solution = ?, examples = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """,
                (title, request, solution, examples, note_id),
            )
            updated = cast(int, cursor.rowcount) > 0
            if updated:
                logger.info(f"Nota {note_id} actualizada")
            return updated

    def delete_note(self, note_id: int) -> bool:
        """Elimina una nota y sus imágenes (CASCADE)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
            deleted = cast(int, cursor.rowcount) > 0
            if deleted:
                logger.info(f"Nota {note_id} eliminada")
            return deleted

    def get_all_notes(
        self, limit: int | None = 200, offset: int | None = 0
    ) -> list[dict[str, Any]]:
        """Obtiene todas las notas ordenadas por fecha de actualización.

        Args:
            limit: Nombre màxim de notes a retornar (None = sense límit).
            offset: Desplaçament per a paginació.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM notes ORDER BY updated_at DESC"
            params: list[Any] = []
            if limit is not None:
                query += " LIMIT ?"
                params.append(limit)
                if offset:
                    query += " OFFSET ?"
                    params.append(offset)
            elif offset:
                # SQLite requereix LIMIT quan hi ha OFFSET: -1 = sense límit
                query += " LIMIT -1 OFFSET ?"
                params.append(offset)
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def search_notes(
        self,
        query: str,
        fields: list[str] | None = None,
        limit: int | None = None,
        offset: int | None = 0,
    ) -> list[dict[str, Any]]:
        """Busca notes per camps (v4.0: unificat amb core/search.py).

        Args:
            query: text a cercar (parcial, literal amb ESCAPE).
            fields: columnes on cercar (per defecte SEARCH_FIELDS de config).
            limit: màxim resultats (None = sense límit).
            offset: desplaçament per paginació.
        """
        from config import SEARCH_FIELDS
        from core.search import like_param

        if fields is None:
            fields = list(SEARCH_FIELDS)
        # Columnes permeses (evita injecció via nom de columna)
        allowed = {"title", "request", "solution", "examples"}
        fields = [f for f in fields if f in allowed] or ["title"]
        search_term = like_param(query)
        where = " OR ".join(f"{f} LIKE ? ESCAPE '\\'" for f in fields)
        sql = f"SELECT * FROM notes WHERE ({where}) ORDER BY updated_at DESC"
        params: list[Any] = [search_term] * len(fields)
        if limit is not None:
            sql += " LIMIT ?"
            params.append(limit)
            if offset:
                sql += " OFFSET ?"
                params.append(offset)
        elif offset:
            sql += " LIMIT -1 OFFSET ?"
            params.append(offset)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]

    # --- Operaciones para imágenes ---

    def add_image(self, note_id: int, filename: str, thumb_filename: str) -> int:
        """Añade una imagen a una nota."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO images (note_id, filename, thumb_filename)
                VALUES (?, ?, ?)
            """,
                (note_id, filename, thumb_filename),
            )
            image_id = cast(int, cursor.lastrowid)
            logger.info(f"Imagen {image_id} añadida a nota {note_id}")
            return image_id

    def get_note_images(self, note_id: int) -> list[dict[str, Any]]:
        """Obtiene todas las imágenes de una nota."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM images
                WHERE note_id = ?
                ORDER BY sort_order, created_at
            """,
                (note_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def delete_image(self, image_id: int) -> bool:
        """Elimina una imagen por su ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM images WHERE id = ?", (image_id,))
            deleted = cast(int, cursor.rowcount) > 0
            if deleted:
                logger.info(f"Imagen {image_id} eliminada")
            return deleted

    def move_image_up(self, image_id: int, note_id: int) -> bool:
        """Mou una imatge una posició amunt. Retorna False si ja és la primera."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT id, sort_order FROM images
                WHERE note_id = ?
                ORDER BY sort_order, id
            """,
                (note_id,),
            )
            images = cursor.fetchall()

            if len(images) < 2:
                return False

            current_idx = None
            for i, img in enumerate(images):
                if img["id"] == image_id:
                    current_idx = i
                    break

            if current_idx is None or current_idx == 0:
                return False

            current_sort = current_idx
            prev_sort = current_idx - 1

            cursor.execute(
                "UPDATE images SET sort_order = ? WHERE id = ?",
                (current_sort, images[current_idx - 1]["id"]),
            )
            cursor.execute(
                "UPDATE images SET sort_order = ? WHERE id = ?", (prev_sort, image_id)
            )

            logger.info(f"Imatge {image_id} moguda amunt")
            return True

    def move_image_down(self, image_id: int, note_id: int) -> bool:
        """Mou una imatge una posició avall. Retorna False si ja és l'última."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT id, sort_order FROM images
                WHERE note_id = ?
                ORDER BY sort_order, id
            """,
                (note_id,),
            )
            images = cursor.fetchall()

            if len(images) < 2:
                return False

            current_idx = None
            for i, img in enumerate(images):
                if img["id"] == image_id:
                    current_idx = i
                    break

            if current_idx is None or current_idx == len(images) - 1:
                return False

            current_sort = current_idx
            next_sort = current_idx + 1

            cursor.execute(
                "UPDATE images SET sort_order = ? WHERE id = ?",
                (current_sort, images[current_idx + 1]["id"]),
            )
            cursor.execute(
                "UPDATE images SET sort_order = ? WHERE id = ?", (next_sort, image_id)
            )

            logger.info(f"Imatge {image_id} moguda avall")
            return True

    def get_stats(self) -> dict[str, Any]:
        """Obtiene estadísticas de la base de datos."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM notes")
            note_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM images")
            image_count = cursor.fetchone()[0]

            cursor.execute("""
                SELECT strftime('%Y-%m-%d', created_at) as date,
                       COUNT(*) as count
                FROM notes
                GROUP BY date
                ORDER BY date DESC
                LIMIT 7
            """)
            recent_activity = cursor.fetchall()

            return {
                "note_count": note_count,
                "image_count": image_count,
                "recent_activity": [dict(row) for row in recent_activity],
                "db_size": self.db_path.stat().st_size if self.db_path.exists() else 0,
            }
