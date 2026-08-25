"""Expanded editor and inline editor formatting mixin for MainWindow."""

import logging

from PySide6.QtWidgets import (
    QApplication,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QDialog,
    QLabel,
    QTextEdit,
    QMessageBox,
    QSizePolicy,
    QFontComboBox,
    QComboBox,
    QColorDialog,
)
from PySide6.QtGui import (
    QKeySequence,
    QShortcut,
    QTextCharFormat,
    QFont,
    QTextListFormat,
    QTextBlockFormat,
    QTextCursor,
)
from PySide6.QtCore import Qt, QTimer

logger = logging.getLogger(__name__)


class UiWindowEditorMixin:
    """Mixin: expand_solution_editor, _toggle_*, _set_font_*, _set_line_spacing, format painter, expanded editor dialog."""

    def _close_expanded_if_open(self, force_close: bool = False):
        """
        Tanca l'editor ampliat de forma segura.
        Si hi ha canvis pendents, pregunta a l'usuari.

        Args:
            force_close: Si True, tanca sense preguntar.

        Returns:
            bool: True si s'ha tancat (o estava tancat), False si l'usuari ha cancel·lat.
        """
        if not hasattr(self, "expand_dialog") or self.expand_dialog is None:
            return True

        if not self.expand_dialog.isVisible():
            self.expand_dialog.deleteLater()
            self.expand_dialog = None
            return True

        # Verificar si hi ha canvis pendents
        editor = self.expand_dialog.findChild(QTextEdit)
        if editor and editor.document().isModified():
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Canvis pendents")
            msg_box.setText("L'editor ampliat té canvis pendents. Vols desar-los?")
            msg_box.setStandardButtons(
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No
                | QMessageBox.StandardButton.Cancel
            )
            msg_box.button(QMessageBox.StandardButton.Yes).setText("Desar")
            msg_box.button(QMessageBox.StandardButton.No).setText("Descartar")
            msg_box.button(QMessageBox.StandardButton.Cancel).setText("Cancel·lar")
            msg_box.setDefaultButton(QMessageBox.StandardButton.Cancel)

            reply = msg_box.exec()

            if reply == QMessageBox.StandardButton.Cancel:
                return False

            if reply == QMessageBox.StandardButton.Yes:
                self._save_expanded_editor(editor, None)

        # Tancar el diàleg
        self.expand_dialog.close()
        self.expand_dialog.deleteLater()
        self.expand_dialog = None
        return True

    def expand_solution_editor(self):
        """Amplía el editor de Solució en un diálogo modal (solo una ventana)."""
        if hasattr(self, "expand_dialog") and self.expand_dialog is not None:
            if self.expand_dialog.isVisible():
                self.expand_dialog.raise_()
                self.expand_dialog.activateWindow()
                return
            else:
                self.expand_dialog.deleteLater()
                self.expand_dialog = None

        dialog = QDialog(self)
        self.expand_dialog = dialog
        title = self.title_input.text().strip() or "Sense titol"
        dialog.setWindowTitle(f"Editar Solució - {title}")
        dialog.setMinimumSize(800, 600)
        dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)

        layout = QVBoxLayout()

        editor = QTextEdit()
        editor.setHtml(self.solution_edit.toHtml())
        editor.setStyleSheet(
            "background-color: white; border: 1px solid #ccc; padding: 10px;"
        )
        editor.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        editor.customContextMenuRequested.connect(
            lambda pos: self.show_editor_context_menu(editor, pos)
        )

        toolbar = QHBoxLayout()

        bold_btn = QPushButton("𝗕")
        bold_btn.setFixedSize(35, 28)
        bold_btn.setToolTip("Negreta (Ctrl+B)")
        bold_btn.clicked.connect(lambda: self._toggle_bold(editor))

        italic_btn = QPushButton("𝐼")
        italic_btn.setFixedSize(35, 28)
        italic_btn.setToolTip("Cursiva (Ctrl+I)")
        italic_btn.clicked.connect(lambda: self._toggle_italic(editor))

        underline_btn = QPushButton("𝖴")
        underline_btn.setFixedSize(35, 28)
        underline_btn.setToolTip("Subratllat (Ctrl+U)")
        underline_btn.clicked.connect(lambda: self._toggle_underline(editor))

        strike_btn = QPushButton("S̶")
        strike_btn.setFixedSize(35, 28)
        strike_btn.setToolTip("Tatxat (Ctrl+T)")
        strike_btn.clicked.connect(lambda: self._toggle_strike(editor))

        color_btn = QPushButton("🎨")
        color_btn.setFixedSize(35, 28)
        color_btn.setToolTip("Color de lletra")
        color_btn.clicked.connect(lambda: self._pick_text_color(editor))

        font_family_combo = QFontComboBox()
        font_family_combo.setFixedWidth(150)
        font_family_combo.setToolTip("Font family")
        font_family_combo.currentFontChanged.connect(
            lambda font: self._set_font_family(editor, font)
        )

        font_size_combo = QComboBox()
        font_size_combo.setFixedWidth(50)
        font_size_combo.setToolTip("Font size")
        font_sizes = [8, 9, 10, 11, 12, 14, 16, 18, 20, 22, 24, 26, 28, 36, 48, 72]
        font_size_combo.addItems([str(s) for s in font_sizes])
        font_size_combo.setCurrentText("14")
        font_size_combo.currentTextChanged.connect(
            lambda size: self._set_font_size(editor, size)
        )

        bullet_btn = QPushButton("•")
        bullet_btn.setFixedSize(35, 28)
        bullet_btn.setToolTip("Llista (Vinyetes)")
        bullet_btn.clicked.connect(lambda: self._insert_bullet_list(editor))

        number_btn = QPushButton("🔢")
        number_btn.setFixedSize(35, 28)
        number_btn.setToolTip("Llista numerada")
        number_btn.clicked.connect(lambda: self._insert_numbered_list(editor))

        line_spacing_combo = QComboBox()
        line_spacing_combo.setFixedWidth(70)
        line_spacing_combo.setToolTip("Interlineat")
        line_spacing_combo.addItems(["1.0", "1.15", "1.5", "1.75", "2.0", "2.5", "3.0"])
        line_spacing_combo.setCurrentText("1.0")
        line_spacing_combo.currentTextChanged.connect(
            lambda spacing: self._set_line_spacing(editor, spacing)
        )

        toolbar.addSpacing(10)
        toolbar.addWidget(line_spacing_combo)

        copy_btn = QPushButton("📄C")
        copy_btn.setFixedSize(45, 28)
        copy_btn.setToolTip("Copiar (Ctrl+C)")
        copy_btn.clicked.connect(lambda: editor.copy())

        paste_btn = QPushButton("📋F")
        paste_btn.setFixedSize(45, 28)
        paste_btn.setToolTip("Enganxar amb format (Ctrl+V)")
        paste_btn.clicked.connect(lambda: editor.paste())

        paste_plain_btn = QPushButton("📋T")
        paste_plain_btn.setFixedSize(45, 28)
        paste_plain_btn.setToolTip("Enganxar text pla (Ctrl+Shift+V)")
        paste_plain_btn.clicked.connect(lambda: self._paste_plain_text(editor))

        format_painter_btn = QPushButton("🖌️")
        format_painter_btn.setFixedSize(35, 28)
        format_painter_btn.setToolTip("Copiar format")
        self.format_painter_btn = format_painter_btn

        def on_fp_clicked():
            try:
                cursor = editor.textCursor()
                if cursor.hasSelection():
                    if self.copied_format[0] is None:
                        self.copied_format[0] = cursor.charFormat()
                        format_painter_btn.setStyleSheet("background-color: #90EE90;")
                        format_painter_btn.setToolTip("Aplicar format (clica aqui)")
                    else:
                        cursor.setCharFormat(self.copied_format[0])
                        format_painter_btn.setStyleSheet("")
                        self.copied_format[0] = None
                        format_painter_btn.setToolTip("Copiar format")
                else:
                    self.copied_format[0] = None
                    format_painter_btn.setStyleSheet("")
                    format_painter_btn.setToolTip("Selecciona text amb format")
            except Exception as e:
                logger.warning(f"FP error: {e}")

        format_painter_btn.clicked.connect(on_fp_clicked)

        fp_shortcut = QShortcut(QKeySequence("Esc"), editor)
        fp_shortcut.setContext(Qt.ShortcutContext.WidgetShortcut)
        fp_shortcut.activated.connect(
            lambda: (
                setattr(self, "copied_format", [None]),
                format_painter_btn.setStyleSheet(""),
            )
        )

        case_btn = QPushButton("Aa")
        case_btn.setFixedSize(35, 28)
        case_btn.setToolTip("Canviar majúscules/minúscules (Shift+F3)")
        case_btn.clicked.connect(lambda: self._cycle_case(editor))

        toolbar.addWidget(bold_btn)
        toolbar.addWidget(italic_btn)
        toolbar.addWidget(underline_btn)
        toolbar.addWidget(strike_btn)
        toolbar.addWidget(color_btn)
        toolbar.addWidget(font_family_combo)
        toolbar.addWidget(font_size_combo)
        toolbar.addSpacing(10)
        toolbar.addWidget(bullet_btn)
        toolbar.addWidget(number_btn)
        toolbar.addSpacing(10)
        toolbar.addWidget(copy_btn)
        toolbar.addWidget(paste_btn)
        toolbar.addWidget(paste_plain_btn)
        toolbar.addWidget(format_painter_btn)
        toolbar.addWidget(case_btn)

        cancel_btn = QPushButton("✖")
        cancel_btn.setFixedSize(35, 28)
        cancel_btn.setToolTip("Tancar (Sortir)")
        cancel_btn.clicked.connect(lambda: self._close_expanded_editor(dialog, editor))

        save_btn = QPushButton("💾")
        save_btn.setFixedSize(35, 28)
        save_btn.setToolTip("Desar canvis")
        save_btn.clicked.connect(lambda: self._save_expanded_editor(editor, save_btn))

        format_label = QLabel()
        format_label.setStyleSheet("color: #666; font-size: 11px; padding: 0 10px;")
        format_label.setMinimumWidth(150)

        self.expand_indicator = QLabel("Desat")
        self.expand_indicator.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
        )
        self.expand_indicator.setStyleSheet("""
            QLabel {
                background-color: #4CAF50;
                color: white;
                padding: 3px 8px;
                border-radius: 3px;
                font-size: 10px;
            }
        """)

        toolbar.addWidget(cancel_btn)
        toolbar.addWidget(save_btn)
        toolbar.addSpacing(10)
        toolbar.addWidget(format_label)
        toolbar.addWidget(self.expand_indicator)

        toolbar.addStretch()

        def on_editor_changed():
            if hasattr(self, "expand_indicator"):
                self.expand_indicator.setText("Modificat")
                self.expand_indicator.setStyleSheet("""
                    QLabel {
                        background-color: #FF9800;
                        color: white;
                        padding: 3px 8px;
                        border-radius: 3px;
                        font-size: 10px;
                    }
                """)

        editor.textChanged.connect(on_editor_changed)

        def update_format_info():
            try:
                cursor = editor.textCursor()
                if cursor.hasSelection():
                    char_fmt = cursor.charFormat()
                    font = char_fmt.font()
                    info = f"Selecció: {font.family()} {font.pointSize()}pt"
                    if char_fmt.fontWeight() == QFont.Weight.Bold:
                        info += " B"
                    if char_fmt.fontItalic():
                        info += " I"
                    if char_fmt.fontUnderline():
                        info += " U"
                    format_label.setText(info)
                else:
                    format_label.setText("")
            except Exception as e:
                logger.warning(f"Error format info: {e}")

        editor.selectionChanged.connect(update_format_info)
        editor.installEventFilter(self)

        case_shortcut = QShortcut(QKeySequence("Shift+F3"), editor)
        case_shortcut.setContext(Qt.ShortcutContext.WidgetShortcut)
        case_shortcut.activated.connect(lambda: self._cycle_case(editor))

        undo_shortcut = QShortcut(QKeySequence("Ctrl+Z"), editor)
        undo_shortcut.setContext(Qt.ShortcutContext.WidgetShortcut)
        undo_shortcut.activated.connect(editor.undo)

        def try_close():
            original_html = self.solution_edit.toHtml()
            current_html = editor.toHtml()

            if original_html != current_html:
                msgBox = QMessageBox(dialog)
                msgBox.setWindowTitle("Canvis sense desar")
                msgBox.setText("Vols desar els canvis abans de sortir?")
                msgBox.setStandardButtons(
                    QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
                )
                msgBox.setButtonText(QMessageBox.Save, "Desar")
                msgBox.setButtonText(QMessageBox.Discard, "Descartar")
                msgBox.setButtonText(QMessageBox.Cancel, "Cancel·lar")
                reply = msgBox.exec()

                if reply == QMessageBox.Save:
                    self._save_expanded_editor(editor, None)
                    dialog.close()
                    self.expand_dialog = None
                    return
                elif reply == QMessageBox.Discard:
                    dialog.close()
                    self.expand_dialog = None
                    return
            else:
                dialog.close()
                self.expand_dialog = None
                return

        dialog.finished.connect(try_close)
        cancel_btn.clicked.connect(try_close)

        layout.addLayout(toolbar)
        layout.addWidget(editor)
        dialog.setLayout(layout)

        dialog.show()

    def _save_expanded_editor(self, editor, save_btn, close_after_save: bool = False):
        """Guarda el contenido del editor ampliado.

        Args:
            editor: El QTextEdit del editor
            save_btn: El botón de guardar (puede ser None)
            close_after_save: Si True, cierra el diálogo después de guardar
        """
        if self.current_note_id is None:
            self.statusBar().showMessage("No hi ha cap nota seleccionada", 2000)
            return

        solution = editor.toHtml()
        self.solution_edit.setHtml(solution)

        title = self.title_input.text()
        request = self.request_edit.toHtml()
        examples_text = self.examples_edit.text()

        success = self.db.update_note(
            self.current_note_id, title, request, solution, examples_text
        )

        if success:
            self.current_note_modified = False
            self.statusBar().showMessage("Canvis desats", 2000)
            self.load_notes()

            # Actualizar indicador de la pantalla principal
            self.save_indicator.setText("  Desat  ")
            self.save_indicator.setStyleSheet("""
                QLabel {
                    background-color: #4CAF50;
                    color: white;
                    padding: 2px 8px;
                    border-radius: 3px;
                    font-size: 10px;
                }
            """)
            self.save_indicator.show()

            # Actualizar indicador del editor ampliado
            if hasattr(self, "expand_indicator"):
                self.expand_indicator.setText("Desat")
                self.expand_indicator.setStyleSheet("""
                    QLabel {
                        background-color: #4CAF50;
                        color: white;
                        padding: 3px 8px;
                        border-radius: 3px;
                        font-size: 10px;
                    }
                """)

            if save_btn:
                save_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #4CAF50;
                        border: none;
                        border-radius: 3px;
                    }
                """)

                QTimer.singleShot(1000, lambda: save_btn.setStyleSheet(""))

            # Marcar que s'ha de tancar i carregar una nota
            if (
                close_after_save
                and hasattr(self, "expand_dialog")
                and self.expand_dialog
            ):
                self._pending_note_to_load = getattr(
                    self, "_pending_note_to_load", None
                )
                # Programar el tancament
                QTimer.singleShot(100, self._do_close_expanded_and_load)
        else:
            QMessageBox.warning(self, "Error", "No s'ha pogut desar la nota.")

    def _do_close_expanded_and_load(self):
        """Tanca l'editor ampliat i carrega la nota pendent."""
        if hasattr(self, "expand_dialog") and self.expand_dialog is not None:
            self.expand_dialog.close()
            self.expand_dialog.deleteLater()
            self.expand_dialog = None

        # Carregar la nota pendent si n'hi ha
        if (
            hasattr(self, "_pending_note_to_load")
            and self._pending_note_to_load is not None
        ):
            note_id = self._pending_note_to_load
            self._pending_note_to_load = None
            self.load_note(note_id)

    def _close_expanded_editor(self, dialog, editor):
        """Tanca l'editor ampliat, preguntant si desar canvis si n'hi ha."""
        original_html = self.solution_edit.toHtml()
        current_html = editor.toHtml()

        if original_html != current_html:
            msgBox = QMessageBox(dialog)
            msgBox.setWindowTitle("Canvis sense desar")
            msgBox.setText("Vols desar els canvis abans de sortir?")
            msgBox.setStandardButtons(
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )
            msgBox.setButtonText(QMessageBox.Save, "Desar")
            msgBox.setButtonText(QMessageBox.Discard, "Descartar")
            msgBox.setButtonText(QMessageBox.Cancel, "Cancel·lar")
            reply = msgBox.exec()

            if reply == QMessageBox.Save:
                self._save_expanded_editor(editor, None)
                dialog.accept()
                return
            elif reply == QMessageBox.Discard:
                dialog.reject()
                return
            else:
                return

        dialog.reject()

    def _insert_bullet_list(self, editor):
        cursor = editor.textCursor()
        cursor.beginEditBlock()
        list_fmt = QTextListFormat()
        list_fmt.setStyle(QTextListFormat.Style.ListDisc)
        cursor.createList(list_fmt)
        cursor.endEditBlock()

    def _insert_numbered_list(self, editor):
        cursor = editor.textCursor()
        cursor.beginEditBlock()
        list_fmt = QTextListFormat()
        list_fmt.setStyle(QTextListFormat.Style.ListDecimal)
        cursor.createList(list_fmt)
        cursor.endEditBlock()

    def _paste_plain_text(self, editor):
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if text:
            editor.insertPlainText(text)

    def _set_font_family(self, editor, font):
        """Canvia la font del text seleccionat."""
        cursor = editor.textCursor()
        fmt = QTextCharFormat()
        fmt.setFontFamily(font.family())

        if cursor.hasSelection():
            cursor.mergeCharFormat(fmt)
        editor.mergeCurrentCharFormat(fmt)

    def _set_font_size(self, editor, size):
        """Canvia la mida de la lletra del text seleccionat."""
        try:
            size_float = float(size)
        except ValueError:
            return

        cursor = editor.textCursor()
        fmt = QTextCharFormat()
        fmt.setFontPointSize(size_float)

        if cursor.hasSelection():
            cursor.mergeCharFormat(fmt)
        editor.mergeCurrentCharFormat(fmt)

    def _reset_format_painter(self, format_painter_btn):
        """Reseteja el format painter."""
        if hasattr(self, "copied_format"):
            self.copied_format[0] = None
            self.multi_apply[0] = False
            if format_painter_btn:
                format_painter_btn.setStyleSheet("")
                format_painter_btn.setToolTip(
                    "Copiar format (🖌️ clic = 1 uso, doble clic = múltiples)"
                )

    def _handle_fp_double_click(self, event, editor, format_painter_btn):
        """Handle double click per multi-apply mode."""
        if event.button() == Qt.MouseButton.LeftButton:
            cursor = editor.textCursor()
            if cursor.hasSelection():
                self.copied_format[0] = cursor.charFormat()
                self.multi_apply[0] = True
                format_painter_btn.setStyleSheet("background-color: #90EE90;")
                format_painter_btn.setToolTip(
                    "Mode múltiples! Clica per aplicar, ESC per sortir"
                )
                event.accept()

    def _apply_copied_format(self, editor):
        """Aplica el format copiat al text seleccionat."""
        if self.copied_format[0] is not None:
            cursor = editor.textCursor()
            if cursor.hasSelection():
                cursor.setCharFormat(self.copied_format[0])
                if not self.multi_apply[0]:
                    self._reset_format_painter(self.format_painter_btn)

    def _set_line_spacing(self, editor, spacing):
        """Canvia l'interlineat del text per als blocs seleccionats o tot el document."""
        try:
            spacing_float = float(spacing)
        except ValueError:
            logger.warning(f"Valor d'interlineat invàlid: {spacing}")
            return

        # Qt espera el valor com a percentatge (100 = simple)
        percent = int(spacing_float * 100)
        block_fmt = QTextBlockFormat()
        # ProportionalHeight = 1 (SingleHeight=0, ProportionalHeight=1, FixedHeight=2, MinimumHeight=3, LineDistanceHeight=4)
        block_fmt.setLineHeight(percent, 1)  # 1 = ProportionalHeight

        cursor = editor.textCursor()
        has_sel = cursor.hasSelection()

        # Si no hi ha selecció, seleccionar tot el document
        if not has_sel:
            cursor.select(QTextCursor.SelectionType.Document)

        # Obtenir inici i final de la selecció
        start_pos = cursor.selectionStart()
        end_pos = cursor.selectionEnd()

        # Iterar per tots els blocs dins la selecció
        doc = editor.document()
        block = doc.findBlock(start_pos)
        end_block = doc.findBlock(end_pos)

        # Comptador de blocs
        block_count = 0

        # Aplicar format a cada bloc individualment
        cursor.beginEditBlock()
        list_block_count = 0
        processed_lists = (
            set()
        )  # Per evitar processar la mateixa llista múltiples vegades
        while block.isValid() and block.position() <= end_block.position():
            # Verificar si el bloc pertany a una llista
            text_list = block.textList()
            if text_list:
                list_block_count += 1
                # Processar el format de la llista si encara no s'ha fet
                list_id = id(text_list)
                if list_id not in processed_lists:
                    processed_lists.add(list_id)
                    # Obtenir i ajustar el format de la llista
                    # TODO: Investigar com ajustar l'espaiat de les llistes si cal
                    # list_fmt = text_list.format()
                    # list_fmt.setProperty(QTextFormat.Margin, 0)
                    # list_fmt.setProperty(QTextFormat.Padding, 0)
                    # text_list.setFormat(list_fmt)
                    pass

                # Per a blocs de llista, ajustar també els marges del bloc
                block_fmt_list = QTextBlockFormat()
                block_fmt_list.setLineHeight(percent, 1)
                # Reduir marges superiors/inferiors per a llistes per a un interlineat consistent
                # Qt afegeix marges addicionals per defecte a les llistes
                block_fmt_list.setTopMargin(0)
                block_fmt_list.setBottomMargin(0)
                # Mantenir el sagnat per a la visualització correcta de vinyetes/números
                # block_fmt_list.setTextIndent(0)  # No canviar el sagnat

                block_cursor = QTextCursor(block)
                block_cursor.mergeBlockFormat(block_fmt_list)
                # Debug: registrar marges del bloc de llista
                if spacing_float == 1.0:  # Només debug per a interlineat 1.0
                    current_fmt = block.blockFormat()
                    logger.debug(
                        f"Bloc de llista - TopMargin: {current_fmt.topMargin()}, BottomMargin: {current_fmt.bottomMargin()}, TextIndent: {current_fmt.textIndent()}"
                    )
            else:
                block_cursor = QTextCursor(block)
                block_cursor.mergeBlockFormat(block_fmt)

            block = block.next()
            block_count += 1
        cursor.endEditBlock()

        # Addicionalment, aplicar CSS per a compatibilitat amb contingut HTML
        try:
            # Això afecta només el contingut HTML renderitzat, no el text pla
            doc.setDefaultStyleSheet(f"body {{ line-height: {spacing_float}; }}")
        except Exception as e:
            logger.debug(f"No s'ha pogut aplicar CSS d'interlineat: {e}")

        # Restaurar selecció original
        cursor.setPosition(start_pos)
        cursor.setPosition(end_pos, QTextCursor.MoveMode.KeepAnchor)
        editor.setTextCursor(cursor)
        editor.update()
        logger.debug(
            f"Interlineat aplicat: {spacing_float} ({percent}%) - Selecció: {'Sí' if has_sel else 'No'} - Blocs: {block_count} - Blocs de llista: {list_block_count}"
        )

    def _toggle_bold(self, editor):
        cursor = editor.textCursor()
        fmt = QTextCharFormat()
        current = cursor.charFormat().fontWeight()
        weight = QFont.Normal if current == QFont.Bold else QFont.Bold
        fmt.setFontWeight(weight)
        cursor.mergeCharFormat(fmt)
        editor.mergeCurrentCharFormat(fmt)

    def _toggle_italic(self, editor):
        cursor = editor.textCursor()
        fmt = QTextCharFormat()
        current = cursor.charFormat().fontItalic()
        fmt.setFontItalic(not current)
        cursor.mergeCharFormat(fmt)
        editor.mergeCurrentCharFormat(fmt)

    def _toggle_underline(self, editor):
        cursor = editor.textCursor()
        fmt = QTextCharFormat()
        current = cursor.charFormat().fontUnderline()
        fmt.setFontUnderline(not current)
        cursor.mergeCharFormat(fmt)
        editor.mergeCurrentCharFormat(fmt)

    def _toggle_strike(self, editor):
        cursor = editor.textCursor()
        if cursor.hasSelection():
            fmt = QTextCharFormat()
            fmt.setFontStrikeOut(not cursor.charFormat().fontStrikeOut())
            cursor.mergeCharFormat(fmt)
            editor.mergeCurrentCharFormat(fmt)

    def _pick_text_color(self, editor):
        color = QColorDialog.getColor(editor.textColor(), self)
        if color.isValid():
            cursor = editor.textCursor()
            fmt = QTextCharFormat()
            fmt.setForeground(color)
            cursor.mergeCharFormat(fmt)
            editor.mergeCurrentCharFormat(fmt)
