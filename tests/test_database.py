"""
Smoke tests per a `database.py` (Notes).

Cobreix:
- Schema (taules i índexs creats)
- CRUD bàsic (create / get / update / delete)
- Cerca amb ESCAPE (%, _ literals)
- Stats
- Re-inicialització idempotent
"""

import pytest


class TestSchema:
    """L'schema es crea correctament."""

    def test_notes_table_exists(self, notes_db):
        rows = notes_db._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='notes'"
        ).fetchall()
        assert len(rows) == 1

    def test_images_table_exists(self, notes_db):
        rows = notes_db._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='images'"
        ).fetchall()
        assert len(rows) == 1

    def test_title_index_exists(self, notes_db):
        rows = notes_db._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_notes_title'"
        ).fetchall()
        assert len(rows) == 1

    def test_wal_mode_enabled(self, notes_db):
        mode = notes_db._conn.execute("PRAGMA journal_mode").fetchone()[0]
        assert mode.lower() == "wal"

    def test_foreign_keys_enabled(self, notes_db):
        fk = notes_db._conn.execute("PRAGMA foreign_keys").fetchone()[0]
        assert fk == 1

    def test_reinit_is_idempotent(self, notes_db):
        """Re-executar init_database no ha de fallar ni duplicar taules."""
        notes_db.init_database()
        notes_db.init_database()
        rows = notes_db._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='notes'"
        ).fetchall()
        assert len(rows) == 1


class TestNotesCRUD:
    """CRUD bàsic de notes."""

    def test_create_and_get_note(self, notes_db):
        nid = notes_db.create_note("Títol test", "Petició", "Solució", "Exemples")
        note = notes_db.get_note(nid)
        assert note is not None
        assert note["title"] == "Títol test"
        assert note["request"] == "Petició"
        assert note["solution"] == "Solució"
        assert note["examples"] == "Exemples"

    def test_create_note_with_empty_fields(self, notes_db):
        nid = notes_db.create_note("Només títol")
        note = notes_db.get_note(nid)
        assert note["title"] == "Només títol"
        assert note["request"] in (None, "")
        assert note["solution"] in (None, "")
        assert note["examples"] in (None, "")

    def test_update_note(self, notes_db):
        nid = notes_db.create_note("Original")
        ok = notes_db.update_note(nid, "Modificat", "R2", "S2", "E2")
        assert ok is True
        note = notes_db.get_note(nid)
        assert note["title"] == "Modificat"

    def test_update_nonexistent_returns_false(self, notes_db):
        ok = notes_db.update_note(99999, "x", "x", "x", "x")
        assert ok is False

    def test_delete_note(self, notes_db):
        nid = notes_db.create_note("Per esborrar")
        ok = notes_db.delete_note(nid)
        assert ok is True
        assert notes_db.get_note(nid) is None

    def test_delete_nonexistent_returns_false(self, notes_db):
        assert notes_db.delete_note(99999) is False

    def test_get_all_notes_sorted_by_updated_at(self, notes_db):
        a = notes_db.create_note("A")
        b = notes_db.create_note("B")
        c = notes_db.create_note("C")
        # Force update on A per posar-la primera
        notes_db.update_note(a, "A-mod", "x", "x", "x")
        notes = notes_db.get_all_notes()
        ids = [n["id"] for n in notes]
        assert ids[0] == a  # la modificada ha de ser la primera
        assert set(ids) == {a, b, c}


class TestSearch:
    """Cerca de notes — fix v3.55 (ESCAPE literal)."""

    def test_search_substring(self, notes_db):
        notes_db.create_note("apagat de llum")
        notes_db.create_note("encesa del llum")
        notes_db.create_note("altres coses")
        results = notes_db.search_notes("llum")
        titles = [n["title"] for n in results]
        assert "apagat de llum" in titles
        assert "encesa del llum" in titles
        assert "altres coses" not in titles

    def test_search_empty_returns_all(self, notes_db):
        notes_db.create_note("A")
        notes_db.create_note("B")
        results = notes_db.search_notes("")
        assert len(results) == 2

    def test_search_literal_percent(self, notes_db):
        """v3.55: % s'ha de cercar literalment, no com a comodí SQL."""
        notes_db.create_note("10% descompte")
        notes_db.create_note("altres coses")
        results = notes_db.search_notes("%")
        # Només la que conté '%' literalment
        titles = [n["title"] for n in results]
        assert "10% descompte" in titles
        assert "altres coses" not in titles

    def test_search_literal_underscore(self, notes_db):
        notes_db.create_note("foo_bar baz")
        notes_db.create_note("fooXbar no")
        results = notes_db.search_notes("_")
        titles = [n["title"] for n in results]
        assert "foo_bar baz" in titles
        assert "fooXbar no" not in titles

    def test_search_no_results(self, notes_db):
        notes_db.create_note("Hola")
        results = notes_db.search_notes("xyzxyz")
        assert results == []


class TestImages:
    """Operacions d'imatges bàsiques."""

    def test_add_image_returns_id(self, notes_db):
        nid = notes_db.create_note("amb imatge")
        img_id = notes_db.add_image(nid, "abc123.jpg", "abc123_256.jpg")
        assert isinstance(img_id, int) and img_id > 0

    def test_get_note_images_empty(self, notes_db):
        nid = notes_db.create_note("sense imatges")
        assert notes_db.get_note_images(nid) == []

    def test_get_note_images_ordered(self, notes_db):
        nid = notes_db.create_note("multi")
        notes_db.add_image(nid, "img1.jpg", "img1_256.jpg")
        notes_db.add_image(nid, "img2.jpg", "img2_256.jpg")
        images = notes_db.get_note_images(nid)
        assert len(images) == 2
        assert [im["filename"] for im in images] == ["img1.jpg", "img2.jpg"]

    def test_delete_image(self, notes_db):
        nid = notes_db.create_note("x")
        img_id = notes_db.add_image(nid, "i.jpg", "i_256.jpg")
        assert notes_db.delete_image(img_id) is True
        assert notes_db.get_note_images(nid) == []


class TestStats:
    """get_stats retorna comptadors raonables."""

    def test_stats_on_empty_db(self, notes_db):
        s = notes_db.get_stats()
        assert s["note_count"] == 0
        assert s["image_count"] == 0
        assert isinstance(s["db_size"], int)

    def test_stats_counts_increment(self, notes_db):
        notes_db.create_note("A")
        notes_db.create_note("B")
        nid = notes_db.create_note("C")
        notes_db.add_image(nid, "i.jpg", "i_256.jpg")
        s = notes_db.get_stats()
        assert s["note_count"] == 3
        assert s["image_count"] == 1
