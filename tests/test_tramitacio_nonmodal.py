"""
Tests del mode NO modal del diàleg d'edició de tràmit (v4.3).

Comproven que:
- el diàlg d'edició no bloqueja l'aplicació (no és modal),
- el diàlg avisa el pare quan es tanca (i la taula es refresca),
- la X tanca el diàleg i auto-guarda els canvis,
- dades invàlides no tanquen el diàleg.
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

    # Evitar que la finestra creï la BD real de l'usuari
    monkeypatch.setattr(tw, "TramitacioDatabase", lambda: tramit_db)
    window = TramitacioWindow(None)
    window.db = tramit_db
    window._owns_db = False
    window.load_data()
    yield window
    window.close()


def _open_editor(window, tramit_db, numero="12345"):
    """Crea un tràmit, el selecciona i obre el diàleg d'edició."""
    from PySide6.QtWidgets import QApplication

    tid = tramit_db.create_tramit(numero, 2026, "01/01/2026", "info inicial")
    window.load_data()
    window.table.selectRow(0)
    window.on_editar_clicked()
    QApplication.processEvents()
    return tid, window._edit_dialogs[0]


class TestDialogNoModal:
    """El diàleg d'edició no ha de bloquejar la resta de finestres."""

    def test_edit_dialog_is_not_modal(self, tramit_window, tramit_db):
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QApplication

        _tid, dialog = _open_editor(tramit_window, tramit_db)

        assert dialog.isVisible()
        assert not dialog.isModal()
        assert dialog.windowModality() == Qt.WindowModality.NonModal
        # Cap finestra modal bloquejant l'aplicació
        assert QApplication.activeModalWidget() is None

    def test_other_windows_stay_usable(self, tramit_window, tramit_db, qt_app):
        """La finestra de tramitació continua operativa amb el diàlg obert."""
        from PySide6.QtWidgets import QApplication

        _tid, dialog = _open_editor(tramit_window, tramit_db)

        # Es pot seguir interactuant amb la finestra pare
        assert not tramit_window.isModal()
        assert QApplication.activeModalWidget() is None
        assert QApplication.activeWindow() in (dialog, tramit_window, None)


class TestDialogClose:
    """Tancament del diàleg: avís al pare i auto-guardat."""

    def test_close_button_saves_and_notifies(self, tramit_window, tramit_db, qt_app):
        tid, dialog = _open_editor(tramit_window, tramit_db)
        dialog.info_input.setPlainText("info editada")

        dialog.close()
        qt_app.processEvents()

        # Desat automàticament
        assert tramit_db.get_tramit(tid)["info"] == "info editada"
        # El pare ja no el té obert
        assert tramit_window._edit_dialogs == []

    def test_save_button_closes_and_refreshes(self, tramit_window, tramit_db, qt_app):
        tid, dialog = _open_editor(tramit_window, tramit_db)
        dialog.info_input.setPlainText("desat")

        assert dialog.on_guardar_clicked() is True
        qt_app.processEvents()

        assert tramit_db.get_tramit(tid)["info"] == "desat"
        assert tramit_window._edit_dialogs == []
        # La taula mostra la info nova
        assert tramit_window.table.item(0, 5).text() == "desat"

    def test_invalid_data_keeps_dialog_open(self, tramit_window, tramit_db, qt_app):
        """Si les dades no són vàlides el diàlg no es tanca."""
        from PySide6.QtWidgets import QMessageBox

        _tid, dialog = _open_editor(tramit_window, tramit_db)
        # Evitar el message box (bloquejaria el test)
        dialog._msg = lambda *args, **kwargs: QMessageBox.StandardButton.No  # type: ignore[method-assign]
        dialog.data_input.setText("")

        dialog.close()
        qt_app.processEvents()

        assert dialog.isVisible()
        assert len(tramit_window._edit_dialogs) == 1

    def test_same_tramit_reuses_open_dialog(self, tramit_window, tramit_db, qt_app):
        """Si el tràmit ja té un diàlg obert, es porta al davant."""
        _tid, dialog = _open_editor(tramit_window, tramit_db)

        tramit_window.on_editar_clicked()
        qt_app.processEvents()

        assert len(tramit_window._edit_dialogs) == 1
        assert tramit_window._edit_dialogs[0] is dialog
