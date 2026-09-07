"""
Smoke tests per a `tramitacio_database.py` (Tramitació).

Cobreix:
- Schema (taula + UNIQUE INDEX (numero, any))
- CRUD bàsic
- `upsert_tramit` (v3.44: consolida info, evita duplicats)
- `_merge_info` (casos límit: old==new, new buit, separadors duplicats)
- Cerca i stats
"""

import pytest


class TestSchema:
    """L'schema es crea correctament amb les constraint correctes."""

    def test_tramitacio_table_exists(self, tramit_db):
        rows = tramit_db._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='tramitacio'"
        ).fetchall()
        assert len(rows) == 1

    def test_unique_index_numero_any_exists(self, tramit_db):
        rows = tramit_db._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' "
            "AND name='idx_tramitacio_numero_any'"
        ).fetchall()
        assert len(rows) == 1

    def test_reminder_column_exists(self, tramit_db):
        """Columna afegida per migració (v3.44+)."""
        cols = [r[1] for r in tramit_db._conn.execute("PRAGMA table_info(tramitacio)").fetchall()]
        assert "reminder_at" in cols


class TestTramitCRUD:
    """CRUD bàsic de tràmits."""

    def test_create_and_get(self, tramit_db):
        tid = tramit_db.create_tramit("12345", 2026, "01/01/2026", "Info inicial")
        t = tramit_db.get_tramit(tid)
        assert t is not None
        assert t["numero"] == "12345"
        assert t["any"] == 2026
        assert t["data"] == "01/01/2026"
        assert t["info"] == "Info inicial"

    def test_create_with_optional_fields(self, tramit_db):
        tid = tramit_db.create_tramit(
            "99999", 2026, "15/06/2026",
            info="", color="vermell", reminder_at="2026-12-31 10:00:00",
        )
        t = tramit_db.get_tramit(tid)
        assert t["color"] == "vermell"
        assert t["reminder_at"] == "2026-12-31 10:00:00"

    def test_update_tramit(self, tramit_db):
        tid = tramit_db.create_tramit("11111", 2026, "01/01/2026")
        ok = tramit_db.update_tramit(
            tid, "22222", 2026, "02/01/2026", "nova info", "blau", None
        )
        assert ok is True
        t = tramit_db.get_tramit(tid)
        assert t["numero"] == "22222"
        assert t["info"] == "nova info"

    def test_update_color(self, tramit_db):
        tid = tramit_db.create_tramit("33333", 2026, "01/01/2026")
        tramit_db.update_color(tid, "groc")
        assert tramit_db.get_tramit(tid)["color"] == "groc"

    def test_delete_tramit(self, tramit_db):
        tid = tramit_db.create_tramit("44444", 2026, "01/01/2026")
        assert tramit_db.delete_tramit(tid) is True
        assert tramit_db.get_tramit(tid) is None


class TestUpsertTramit:
    """`upsert_tramit` (v3.44) — insereix o consolida info si duplicat."""

    def test_insert_when_new(self, tramit_db):
        tid = tramit_db.upsert_tramit("55555", 2026, "01/01/2026", "info A")
        assert tramit_db.get_tramit(tid)["info"] == "info A"

    def test_consolidate_when_exists(self, tramit_db):
        tid = tramit_db.upsert_tramit("66666", 2026, "01/01/2026", "info A")
        tid2 = tramit_db.upsert_tramit("66666", 2026, "01/01/2026", "info B")
        # Mateix ID (upsert)
        assert tid == tid2
        t = tramit_db.get_tramit(tid)
        # La info s'ha consolidat amb el separador
        assert "info A" in t["info"]
        assert "info B" in t["info"]
        assert "--- Dades noves ---" in t["info"]

    def test_upsert_does_not_create_duplicate(self, tramit_db):
        tramit_db.upsert_tramit("77777", 2026, "01/01/2026", "x")
        tramit_db.upsert_tramit("77777", 2026, "01/01/2026", "y")
        all_tramits = tramit_db.get_all_tramits()
        assert len(all_tramits) == 1


class TestMergeInfo:
    """`_merge_info` (privat però lògicament crític per al flux)."""

    def test_empty_new_returns_empty(self, tramit_db):
        # Accés directe a la funció interna
        assert tramit_db._merge_info("abc", "") == ""
        assert tramit_db._merge_info("", "") == ""

    def test_empty_old_returns_new(self, tramit_db):
        assert tramit_db._merge_info("", "nou") == "nou"

    def test_identical_returns_old(self, tramit_db):
        assert tramit_db._merge_info("abc", "abc") == "abc"

    def test_distinct_concatenates_with_separator(self, tramit_db):
        result = tramit_db._merge_info("vell", "nou")
        assert "vell" in result
        assert "nou" in result
        assert "--- Dades noves ---" in result

    def test_duplicate_block_not_added_twice(self, tramit_db):
        """Si new == últim bloc, no re-afegeix."""
        first = tramit_db._merge_info("vell", "nou")
        again = tramit_db._merge_info(first, "nou")
        # El separador no s'ha duplicat
        assert again.count("--- Dades noves ---") == first.count("--- Dades noves ---")
        assert "nou" in again


class TestSearch:
    """Cerca per número / any / color."""

    def test_search_by_numero(self, tramit_db):
        tramit_db.create_tramit("12345", 2026, "01/01/2026")
        tramit_db.create_tramit("99999", 2025, "01/01/2025")
        results = tramit_db.search_tramits(numero="12345")
        assert len(results) == 1
        assert results[0]["numero"] == "12345"

    def test_search_by_any(self, tramit_db):
        tramit_db.create_tramit("11111", 2026, "01/01/2026")
        tramit_db.create_tramit("22222", 2025, "01/01/2025")
        results = tramit_db.search_tramits(any=2025)
        assert len(results) == 1
        assert results[0]["any"] == 2025

    def test_search_by_color(self, tramit_db):
        tramit_db.create_tramit("11111", 2026, "01/01/2026", color="vermell")
        tramit_db.create_tramit("22222", 2026, "01/01/2026", color="verd")
        results = tramit_db.search_tramits(color_filter="vermell")
        assert len(results) == 1

    def test_search_literal_percent(self, tramit_db):
        """v3.55: % s'ha de cercar literalment."""
        tramit_db.create_tramit("12345", 2026, "01/01/2026", info="10%")
        tramit_db.create_tramit("99999", 2026, "01/01/2026", info="res")
        results = tramit_db.search_tramits(numero="%")
        # Només el que té '%' al numero — cap, perquè numero no té '%'
        assert len(results) == 0


class TestAlarms:
    """`get_alarms` — alarmes ordenades cronològicament."""

    def test_no_reminders_no_alarms(self, tramit_db):
        tramit_db.create_tramit("11111", 2026, "01/01/2026")
        assert tramit_db.get_alarms() == []

    def test_future_reminder_appears(self, tramit_db):
        tramit_db.create_tramit(
            "11111", 2026, "01/01/2026", reminder_at="2099-12-31 10:00:00"
        )
        alarms = tramit_db.get_alarms()
        assert len(alarms) == 1
        assert alarms[0]["reminder_at"] == "2099-12-31 10:00:00"

    def test_past_reminder_hidden_by_default(self, tramit_db):
        tramit_db.create_tramit(
            "11111", 2026, "01/01/2026", reminder_at="2000-01-01 00:00:00"
        )
        assert tramit_db.get_alarms() == []
        # Però apareix amb include_past=True
        assert len(tramit_db.get_alarms(include_past=True)) == 1


class TestStats:
    """`get_database_stats`."""

    def test_stats_empty(self, tramit_db):
        s = tramit_db.get_database_stats()
        assert s["total_records"] == 0
        assert s["duplicates"] == 0
        assert s["file_size_mb"] >= 0

    def test_stats_with_records(self, tramit_db):
        tramit_db.create_tramit("11111", 2026, "01/01/2026", color="vermell")
        tramit_db.create_tramit("22222", 2026, "02/01/2026", color="verd")
        s = tramit_db.get_database_stats()
        assert s["total_records"] == 2
        assert s["by_color"].get("vermell") == 1
        assert s["by_color"].get("verd") == 1
        assert s["by_year"].get(2026) == 2
