"""
Tests del pintor de format (v4.4).

Comproven que:
- el doble clic del botó activa el mode multi-aplicació (funcionalitat que
  el tooltip anunciava però no estava connectada),
- el format copiat s'aplica al text seleccionat,
- en mode normal el format es consumeix (un sol ús) i en mode multi es conserva,
- el reset (ESC) neteja l'estat.
"""

import os

import pytest

# Headless: evita finestres reals durant els tests
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from ui.ui_window_editor import (  # noqa: E402  (import després del setenv)
    UiWindowEditorMixin,
    _FormatPainterButton,
)


@pytest.fixture(scope="session")
def qt_app():
    """Instància QApplication (headless)."""
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    yield app


class _PainterHost(UiWindowEditorMixin):
    """Host minimal amb els atributs que fa servir el pintor de format."""

    def __init__(self):
        self.copied_format = [None]
        self.multi_apply = [False]
        self.format_painter_btn = None


def _make_editor(text="Hola món"):
    """QTextEdit amb tot el text seleccionat."""
    from PySide6.QtGui import QTextCursor
    from PySide6.QtWidgets import QTextEdit

    editor = QTextEdit()
    editor.setPlainText(text)
    cursor = editor.textCursor()
    cursor.select(QTextCursor.SelectionType.Document)
    editor.setTextCursor(cursor)
    return editor


def _bold_format():
    """QTextCharFormat en negreta."""
    from PySide6.QtGui import QFont, QTextCharFormat

    fmt = QTextCharFormat()
    fmt.setFontWeight(QFont.Weight.Bold)
    return fmt


class TestFormatPainter:
    """Aplicació del format copiat."""

    def test_apply_copied_format_applies_to_selection(self, qt_app):
        host = _PainterHost()
        editor = _make_editor()
        host.copied_format[0] = _bold_format()

        host._apply_copied_format(editor)

        from PySide6.QtGui import QFont

        assert editor.textCursor().charFormat().fontWeight() == QFont.Weight.Bold

    def test_single_use_consumes_copied_format(self, qt_app):
        host = _PainterHost()
        editor = _make_editor()
        host.copied_format[0] = _bold_format()

        host._apply_copied_format(editor)

        assert host.copied_format[0] is None
        assert host.multi_apply[0] is False

    def test_multi_apply_keeps_copied_format(self, qt_app):
        host = _PainterHost()
        editor = _make_editor()
        host.copied_format[0] = _bold_format()
        host.multi_apply[0] = True

        host._apply_copied_format(editor)

        assert host.copied_format[0] is not None
        assert host.multi_apply[0] is True


class TestFormatPainterMultiMode:
    """Mode multi-aplicació (doble clic)."""

    def test_double_click_enables_multi_apply(self, qt_app):
        from PySide6.QtWidgets import QPushButton

        host = _PainterHost()
        editor = _make_editor()
        button = QPushButton("x")
        host.format_painter_btn = button

        host._handle_fp_double_click(button, editor)

        assert host.multi_apply[0] is True
        assert host.copied_format[0] is not None

    def test_button_emits_double_clicked(self, qt_app):
        from PySide6.QtCore import Qt
        from PySide6.QtTest import QTest

        button = _FormatPainterButton("x")
        button.show()
        qt_app.processEvents()

        fired = []
        button.doubleClicked.connect(lambda: fired.append(True))

        QTest.mouseDClick(button, Qt.MouseButton.LeftButton)
        qt_app.processEvents()

        assert fired == [True]

    def test_reset_clears_state(self, qt_app):
        host = _PainterHost()
        host.copied_format[0] = _bold_format()
        host.multi_apply[0] = True

        host._reset_format_painter(None)

        assert host.copied_format[0] is None
        assert host.multi_apply[0] is False
