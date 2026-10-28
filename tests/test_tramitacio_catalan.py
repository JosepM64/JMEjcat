"""
Tests del camp CAT (tramitar en català) als expedients de Tramitació (v4.5).

Comproven que:
- la BD emmagatzema i retorna el camp `catalan` (0/1),
- el diàleg d'edició mostra l'estat del botó CAT al carregar un tràmit,
- clicar el botó i desar actualitza `catalan` a la BD.
"""

import os

import pytest

# Headless: evita finestres reals durant els tests
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(scope="session")
def qt_app():
    """Instància QApplication (headless)."""
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture
def tramit_window(qt_app, tramit_db, monkeypatch):
    """Finestra de Tramitació amb la BD temporal del test."""
    import tramitacio_window as tw
    from tramitacio_window import TramitacioWindow

    monkeypatch.setattr(tw, "TramitacioDatabase", lambda: tramit_db)
    window = TramitacioWindow(None)
    window.db = tramit_db
    window._owns_db = False
    window.load_data()
    yield window
    window.close()


def _open_editor(window, tramit_db, numero="12345", catalan=0):
    """Crea un tràmit, el selecciona i obre el diàleg d'edició."""
    from PySide6.QtWidgets import QApplication

    tid = tramit_db.create_tramit(
        numero, 2026, "01/01/2026", "info inicial", catalan=catalan
    )
    window.load_data()
    window.table.selectRow(0)
    window.on_editar_clicked()
    QApplication.processEvents()
    return tid, window._edit_dialogs[0]


class TestCatalanBD:
    """El camp `catalan` s'emmagatzema i recupera correctament a la BD."""

    def test_create_tramit_catalan_default_zero(self, tramit_db):
        tid = tramit_db.create_tramit("11111", 2026, "01/01/2026", "info")
        assert tramit_db.get_tramit(tid)["catalan"] == 0

    def test_create_tramit_catalan_one(self, tramit_db):
        tid = tramit_db.create_tramit("11111", 2026, "01/01/2026", "info", catalan=1)
        assert tramit_db.get_tramit(tid)["catalan"] == 1

    def test_update_tramit_catalan(self, tramit_db):
        tid = tramit_db.create_tramit("11111", 2026, "01/01/2026", "info", catalan=0)
        ok = tramit_db.update_tramit(
            tid, "11111", 2026, "01/01/2026", "info", catalan=1
        )
        assert ok is True
        assert tramit_db.get_tramit(tid)["catalan"] == 1


class TestCatalanDialog:
    """El diàleg d'edició reflects i desa l'estat del botó CAT."""

    def test_dialog_shows_catalan_checked(self, tramit_window, tramit_db, qt_app):
        tid, dialog = _open_editor(tramit_window, tramit_db, catalan=1)
        assert dialog.btn_catalan.isChecked() is True
        dialog.close()
        qt_app.processEvents()
        assert tramit_db.get_tramit(tid)["catalan"] == 1

    def test_dialog_shows_catalan_unchecked(self, tramit_window, tramit_db, qt_app):
        tid, dialog = _open_editor(tramit_window, tramit_db, catalan=0)
        assert dialog.btn_catalan.isChecked() is False
        dialog.close()
        qt_app.processEvents()
        assert tramit_db.get_tramit(tid)["catalan"] == 0

    def test_toggle_catalan_saved_on_close(self, tramit_window, tramit_db, qt_app):
        tid, dialog = _open_editor(tramit_window, tramit_db, catalan=0)
        # Activar el botó CAT (canvia a verd)
        dialog.btn_catalan.setChecked(True)
        dialog._apply_catalan_style(True)

        dialog.close()
        qt_app.processEvents()

        assert tramit_db.get_tramit(tid)["catalan"] == 1
        assert tramit_window._edit_dialogs == []

    def test_toggle_catalan_saved_on_guardar(self, tramit_window, tramit_db, qt_app):
        tid, dialog = _open_editor(tramit_window, tramit_db, catalan=0)
        dialog.btn_catalan.setChecked(True)
        dialog._apply_catalan_style(True)

        assert dialog.on_guardar_clicked() is True
        qt_app.processEvents()

        assert tramit_db.get_tramit(tid)["catalan"] == 1
        assert tramit_window._edit_dialogs == []
