"""Text formatting, case cycling, color, and context menu mixin for MainWindow."""

from PySide6.QtGui import (
    QAction,
    QColor,
    QFont,
    QTextCharFormat,
    QTextCursor,
    QTextListFormat,
)
from PySide6.QtWidgets import (
    QApplication,
    QColorDialog,
    QDialog,
    QLineEdit,
    QMessageBox,
    QTextEdit,
)

from ui_dialogs import NoteLinkDialog


class UiWindowFormattingMixin:
    """Mixin: format_text, cycle_selected_text_case, change_text_color, clear_format, _clear_format_in_editor, _cycle_case, paste_as_plain_text, show_editor_context_menu, insert_note_link."""

    def format_text(self, style: str):
        """Aplica formato al texto seleccionado."""
        # Determinar editor activo
        focused = QApplication.focusWidget()
        if not isinstance(focused, QTextEdit):
            return

        editor = focused
        cursor = editor.textCursor()

        if not cursor.hasSelection():
            return

        fmt = QTextCharFormat()

        if style == "bold":
            current = cursor.charFormat().fontWeight()
            weight = QFont.Normal if current == QFont.Bold else QFont.Bold
            fmt.setFontWeight(weight)
        elif style == "italic":
            current = cursor.charFormat().fontItalic()
            fmt.setFontItalic(not current)
        elif style == "underline":
            current = cursor.charFormat().fontUnderline()
            fmt.setFontUnderline(not current)
        elif style == "strikeout":
            current = cursor.charFormat().fontStrikeOut()
            fmt.setFontStrikeOut(not current)
        elif style == "list":
            cursor.beginEditBlock()
            list_fmt = QTextListFormat()
            list_fmt.setStyle(QTextListFormat.Style.ListDisc)
            cursor.createList(list_fmt)
            cursor.endEditBlock()
            return
        elif style == "numbered_list":
            cursor.beginEditBlock()
            list_fmt = QTextListFormat()
            list_fmt.setStyle(QTextListFormat.Style.ListDecimal)
            cursor.createList(list_fmt)
            cursor.endEditBlock()
            return

        cursor.mergeCharFormat(fmt)
        editor.mergeCurrentCharFormat(fmt)

    def cycle_selected_text_case(self):
        """Canvia entre diferents modes de majúscules/minúscules del text seleccionat (Shift+F3)."""
        # Obtenir l'editor actiu
        focused = QApplication.focusWidget()
        if not isinstance(focused, QTextEdit):
            return

        editor = focused
        cursor = editor.textCursor()

        # Si no hi ha text seleccionat, seleccionar la paraula actual
        if not cursor.hasSelection():
            # Usar el enum correcte de QTextCursor
            cursor.select(QTextCursor.SelectionType.WordUnderCursor)

        selected_text = cursor.selectedText()
        if not selected_text:
            return

        # Detectar el mode actual del text seleccionat per determinar el següent
        current_mode = self._detect_text_case_mode(selected_text)

        # Cicle de modes: 0 (majúscules) -> 1 (minúscules) -> 2 (capitalitzat) -> 0
        next_mode = (current_mode + 1) % 3

        if next_mode == 0:
            # Mode 0: Tot majúscules
            new_text = selected_text.upper()
            mode_name = "MAJÚSCULES"
        elif next_mode == 1:
            # Mode 1: Tot minúscules
            new_text = selected_text.lower()
            mode_name = "minúscules"
        else:
            # Mode 2: Capitalitzar (primera lletra de cada paraula)
            new_text = selected_text.title()
            mode_name = "Capitalitzat"

        # Reemplaçar el text seleccionat
        cursor.insertText(new_text)

        # Seleccionar el nou text per permetre cicle continu
        # Usar els enums correctes de QTextCursor
        cursor.movePosition(
            QTextCursor.MoveOperation.Left,
            QTextCursor.MoveMode.MoveAnchor,
            len(new_text),
        )
        cursor.movePosition(
            QTextCursor.MoveOperation.Right,
            QTextCursor.MoveMode.KeepAnchor,
            len(new_text),
        )
        editor.setTextCursor(cursor)

        # Notificar canvi
        self.on_content_changed()

        # Mostrar indicador del mode actual
        self.statusBar().showMessage(f"Format: {mode_name}", 2000)

    def _detect_text_case_mode(self, text: str) -> int:
        """Detecta el mode actual del text. Retorna: 0=majúscules, 1=minúscules, 2=altres/mixt."""
        if text.isupper():
            return 0
        elif text.islower():
            return 1
        else:
            return 2

    def change_text_color(self):
        """Canvia el color del text seleccionat."""
        focused = QApplication.focusWidget()

        # Si el focus no està en un editor, provem de detectar quin està actiu
        if not isinstance(focused, QTextEdit):
            if self.solution_edit.hasFocus():
                focused = self.solution_edit
            elif self.request_edit.hasFocus():
                focused = self.request_edit
            else:
                # Fallback per defecte
                focused = self.solution_edit

        editor = focused
        # Obtenir el color actual
        current_color = editor.textColor()
        color = QColorDialog.getColor(
            current_color, self, "Seleccionar color de lletra"
        )

        if color.isValid():
            fmt = QTextCharFormat()
            fmt.setForeground(color)

            cursor = editor.textCursor()
            if not cursor.hasSelection():
                editor.mergeCurrentCharFormat(fmt)
            else:
                cursor.mergeCharFormat(fmt)
                editor.mergeCurrentCharFormat(fmt)

    def _clear_format_in_editor(self, editor: QTextEdit):
        """Limpia el formato en el editor especificado."""
        cursor = editor.textCursor()
        if cursor.hasSelection():
            fmt = QTextCharFormat()
            fmt.setFontWeight(QFont.Weight.Normal)
            fmt.setFontItalic(False)
            fmt.setFontUnderline(False)
            fmt.setForeground(QColor("black"))
            cursor.mergeCharFormat(fmt)
            editor.mergeCurrentCharFormat(fmt)

            editor.setFocus()

    def _cycle_case(self, editor):
        """Canvia entre diferents modes de majúscules/minúscules del text seleccionat."""
        cursor = editor.textCursor()

        if not cursor.hasSelection():
            cursor.select(QTextCursor.SelectionType.WordUnderCursor)

        selected_text = cursor.selectedText()
        if not selected_text:
            return

        current_mode = self._detect_text_case_mode(selected_text)
        next_mode = (current_mode + 1) % 3

        if next_mode == 0:
            new_text = selected_text.upper()
        elif next_mode == 1:
            new_text = selected_text.lower()
        else:
            new_text = selected_text.title()

        cursor.insertText(new_text)

        cursor.movePosition(
            QTextCursor.MoveOperation.Left,
            QTextCursor.MoveMode.MoveAnchor,
            len(new_text),
        )
        cursor.movePosition(
            QTextCursor.MoveOperation.Right,
            QTextCursor.MoveMode.KeepAnchor,
            len(new_text),
        )
        editor.setTextCursor(cursor)

        self.on_content_changed()

    def paste_as_plain_text(self):
        """Enganxa el contingut del portapapers com a text pla."""
        focused = QApplication.focusWidget()
        if isinstance(focused, (QTextEdit, QLineEdit)):
            clipboard = QApplication.clipboard()
            text = clipboard.text()
            if text:
                if isinstance(focused, QTextEdit):
                    focused.insertPlainText(text)
                else:
                    focused.insert(text)

    def show_editor_context_menu(self, editor, pos):
        """Mostra el menú de context personalitzat per als editors."""
        menu = editor.createStandardContextMenu()

        # Afegir separador
        menu.addSeparator()

        # Afegir acció de text pla
        paste_plain_action = QAction("📋 Enganxar text pla", self)
        paste_plain_action.setShortcut("Ctrl+Shift+V")
        paste_plain_action.triggered.connect(self.paste_as_plain_text)
        menu.addAction(paste_plain_action)

        # Afegir acció d'enllaçar a una nota
        link_note_action = QAction("🔗 Enllaçar a nota", self)
        link_note_action.triggered.connect(lambda: self.insert_note_link(editor))
        menu.addAction(link_note_action)

        menu.exec(editor.mapToGlobal(pos))

    def insert_note_link(self, editor):
        """Inserta un enllaç a una altra nota."""
        notes = self.db.get_all_notes()

        if not notes:
            QMessageBox.information(
                self, "Informació", "No hi ha notes disponibles per enllaçar."
            )
            return

        dialog = NoteLinkDialog(notes, self.current_note_id, self)
        if dialog.exec() == QDialog.Accepted:
            cursor = editor.textCursor()
            link_html = f'<a href="note:{dialog.selected_note_id}" style="color: #1976D2; text-decoration: underline;">{dialog.selected_title}</a>'
            cursor.insertHtml(link_html)

    def clear_format(self):
        """Limpia el formato del texto seleccionado."""
        focused = QApplication.focusWidget()
        if not isinstance(focused, QTextEdit):
            return

        editor = focused
        cursor = editor.textCursor()

        if not cursor.hasSelection():
            return

        fmt = QTextCharFormat()
        fmt.setFontWeight(QFont.Weight.Normal)
        fmt.setFontItalic(False)
        fmt.setFontUnderline(False)
        fmt.setFontStrikeOut(False)
        fmt.setForeground(QColor("black"))

        cursor.mergeCharFormat(fmt)
        editor.mergeCurrentCharFormat(fmt)
