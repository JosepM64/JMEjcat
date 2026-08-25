"""Note CRUD, list management, search, autosave and link navigation mixin for MainWindow."""

import logging

from PySide6.QtWidgets import (
    QLineEdit,
    QTextEdit,
    QListWidgetItem,
    QMessageBox,
    QApplication,
)
from PySide6.QtCore import Qt, QTimer

from calculator import CalculatorDialog
from config import (
    TITLE_TRUNCATE_LENGTH,
    TITLE_TRUNCATE_SUFFIX,
    EXAMPLES_MAX_LENGTH,
    AUTOSAVE_INTERVAL,
)

logger = logging.getLogger(__name__)


class UiWindowNotesMixin:
    """Mixin: Note CRUD (create, open, save, delete, rename), note list management, recent notes, autosave, search, link navigation, calculator."""

    def eventFilter(self, obj, event):
        """Filtra events per detectar Ctrl+Click a enllaços."""
        return self._handle_link_click(obj, event)

    def on_title_changed(self, text: str):
        """Gestiona els canvis al camp títol amb conversió automàtica a majúscules."""
        # Bloquejar senyals temporalment per evitar recursivitat
        self.title_input.blockSignals(True)

        # Convertir a majúscules
        upper_text = text.upper()

        # Només actualitzar si hi ha canvis per mantindre el cursor
        if text != upper_text:
            cursor_pos = self.title_input.cursorPosition()
            self.title_input.setText(upper_text)
            # Restaurar posició del cursor
            self.title_input.setCursorPosition(cursor_pos)

        self.title_input.blockSignals(False)

        # Notificar que el contingut ha canviat
        self.on_content_changed()

    def on_title_edited(self, text: str):
        """Gestiona l'edició del títol (quan l'usuari escriu)."""
        # La conversió ja es fa a on_title_changed
        pass

    def on_content_changed(self):
        """Marca la nota com a modificada."""
        # No marcar com a modificat si estem carregant una nota
        if getattr(self, "_loading_note", False):
            return
        if self.current_note_id is not None:
            self.current_note_modified = True
            self.save_indicator.setText("  Modificat  ")
            self.save_indicator.setStyleSheet("""
                QLabel {
                    background-color: #ff9800;
                    color: white;
                    padding: 2px 8px;
                    border-radius: 3px;
                    font-size: 10px;
                }
            """)
            self.save_indicator.show()

    def focus_search(self):
        """Enfoca el camp de cerca."""
        self.search_input.setFocus()
        self.search_input.selectAll()

    def _handle_link_click(self, obj, event):
        """Detecta Ctrl+Click a enllaços per navegar."""
        if (
            event.type() == event.Type.MouseButtonPress
            and event.modifiers() == Qt.KeyboardModifier.ControlModifier
        ):
            cursor = obj.cursorForPosition(event.pos())
            if cursor:
                char_format = cursor.charFormat()
                if char_format.isValid() and char_format.isAnchor():
                    href = char_format.anchorHref()
                    if href and href.startswith("note:"):
                        note_id = href[5:]
                        try:
                            note_id = int(note_id)
                            note = self.db.get_note(note_id)
                            if note:
                                self.load_note_by_id(note_id)
                        except ValueError:
                            pass
                        return True
        return False

    def on_note_link_clicked(self, url):
        """Navega a la nota enllaçada quan es fa clic a l'enllaç."""
        url_str = url.toString()

        if url_str.startswith("note:"):
            note_id = url_str[5:]

            try:
                note_id = int(note_id)
            except ValueError:
                return

            note = self.db.get_note(note_id)
            if note:
                self.load_note_by_id(note_id)

    def load_note_by_id(self, note_id):
        """Carrega una nota pel seu ID."""
        self._loading_note = True

        note = self.db.get_note(note_id)
        if note:
            self.current_note_id = note["id"]
            self.title_input.setText(note["title"])
            self.request_edit.setHtml(note["request"])
            self.solution_edit.setHtml(note["solution"])
            self.examples_edit.setText(note["examples"] or "")

            self.current_note_modified = False
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

            self.load_note_images(note_id)

            self.statusBar().showMessage(f"Oberta: {note['title']}", 2000)

        self._loading_note = False

    def _populate_notes_list(self, notes):
        """Omple la llista de notes amb els items."""
        self.notes_list.clear()
        trunc_at = TITLE_TRUNCATE_LENGTH
        for note in notes:
            title = note["title"]
            if len(title) > trunc_at:
                title = title[: trunc_at - TITLE_TRUNCATE_SUFFIX] + "..."
            item = QListWidgetItem(title)
            item.setData(Qt.UserRole, note["id"])
            self.notes_list.addItem(item)
        self.notes_count_label.setText(f"{len(notes)} notas")

    def load_notes(self):
        """Carga la lista de notas."""
        notes = self.db.get_all_notes()
        self._populate_notes_list(notes)
        logger.info(f"Notas cargadas: {len(notes)}")

    def on_search(self):
        """Filtra notes segons el text de cerca."""
        query = self.search_input.text().strip()
        if query:
            notes = self.db.search_notes(query)
        else:
            notes = self.db.get_all_notes()
        self._populate_notes_list(notes)

    def on_note_selected(self, item):
        """Carga una nota seleccionada."""
        note_id = item.data(Qt.UserRole)

        # Verificar si el editor ampliat està obert
        if (
            hasattr(self, "expand_dialog")
            and self.expand_dialog is not None
            and self.expand_dialog.isVisible()
        ):
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
                    return

                if reply == QMessageBox.StandardButton.Yes:
                    # Desar contingut al camp principal
                    solution = editor.toHtml()
                    self.solution_edit.setHtml(solution)

                    # Actualitzar a la base de dades
                    title = self.title_input.text()
                    request = self.request_edit.toHtml()
                    examples_text = self.examples_edit.text()
                    self.db.update_note(
                        self.current_note_id, title, request, solution, examples_text
                    )

                    self.current_note_modified = False
                    self.load_notes()

                # Tancar l'editor ampliat i programar carregar la nota
                target_note_id = note_id
                dialog = self.expand_dialog
                self.expand_dialog = None
                dialog.close()
                QTimer.singleShot(
                    100, lambda: self._finish_note_change(dialog, target_note_id)
                )
                return

        # Verificar si hi ha canvis a la nota actual
        if self.current_note_modified:
            msgBox = QMessageBox(self)
            msgBox.setWindowTitle("Canvis sense desar")
            msgBox.setText("Vols desar els canvis abans de carregar una altra nota?")
            msgBox.setStandardButtons(
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            msgBox.button(QMessageBox.Yes).setText("Sí")
            msgBox.button(QMessageBox.No).setText("No")
            msgBox.button(QMessageBox.Cancel).setText("Cancel·lar")
            reply = msgBox.exec()

            if reply == QMessageBox.Yes:
                self.save_note()
            elif reply == QMessageBox.Cancel:
                return

        # Carregar la nova nota
        self.load_note(note_id)

    def _finish_note_change(self, dialog, note_id):
        """Acaba de tancar el diàleg i carrega la nota."""
        dialog.deleteLater()
        self.load_note(note_id)

    def load_note(self, note_id: int):
        """Carrega una nota específica."""
        # Activar flag de càrrega per evitar marcar com a modificat
        self._loading_note = True

        note = self.db.get_note(note_id)
        if not note:
            self._loading_note = False
            QMessageBox.warning(self, "Error", "No s'ha pogut carregar la nota.")
            return

        self.current_note_id = note_id
        self.current_note_modified = False

        # Cargar datos
        self.title_input.setText(note["title"].upper())
        self.request_edit.setHtml(note["request"] or "")
        self.solution_edit.setHtml(note["solution"] or "")
        self.examples_edit.setText(note["examples"] or "")

        # Cargar imágenes
        self.load_note_images(note_id)

        # Actualitzar indicador
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

        self.statusBar().showMessage(f"Nota carregada: {note['title']}")
        logger.info(f"Nota {note_id} carregada")

        # Desactivar flag de càrrega
        self._loading_note = False

    def new_note(self):
        """Crea una nueva nota."""
        # Preguntar si guardar canvis
        if self.current_note_modified:
            msgBox = QMessageBox(self)
            msgBox.setWindowTitle("Canvis sense desar")
            msgBox.setText("Vols desar els canvis abans de crear una nova nota?")
            msgBox.setStandardButtons(
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            msgBox.setButtonText(QMessageBox.Yes, "Sí")
            msgBox.setButtonText(QMessageBox.No, "No")
            msgBox.setButtonText(QMessageBox.Cancel, "Cancel·lar")
            reply = msgBox.exec()

            if reply == QMessageBox.Yes:
                self.save_note()
            elif reply == QMessageBox.Cancel:
                return

        # Limpiar campos
        self.current_note_id = None
        self.current_note_modified = False

        self.title_input.clear()
        self.request_edit.clear()
        self.solution_edit.clear()
        self.examples_edit.clear()
        self.image_gallery.clear()

        # Ocultar indicador
        self.save_indicator.hide()

        self.statusBar().showMessage("Nueva nota lista")
        self.title_input.setFocus()
        logger.info("Nueva nota creada")

    def autosave_note(self):
        """Guarda automàticament la nota si ha estat modificada."""
        if not (self.autosave_enabled and self.current_note_id is not None
                and not self._loading_note):
            return

        # Si l'editor expandit està obert i modificat, sincronitzar flag
        if (hasattr(self, 'expand_dialog') and self.expand_dialog is not None
                and self.expand_dialog.isVisible()):
            editor = self.expand_dialog.findChild(QTextEdit)
            if editor and editor.document().isModified():
                self.current_note_modified = True

        if self.current_note_modified:
            self.save_note()
            logger.info("Autoguardat executat")

    def toggle_autosave(self):
        """Activa o desactiva l'autoguardat."""
        self.autosave_enabled = self.autosave_action.isChecked()
        if self.autosave_enabled:
            self.autosave_timer.start(AUTOSAVE_INTERVAL * 1000)
            self.statusBar().showMessage("Autoguardat activat", 2000)
        else:
            self.autosave_timer.stop()
            self.statusBar().showMessage("Autoguardat desactivat", 2000)

    def save_note(self):
        """Guarda la nota actual."""
        title = self.title_input.text().strip()
        if not title:
            QMessageBox.warning(self, "Avís", "El títol no pot estar buit.")
            self.title_input.setFocus()
            return

        # Validar longitud d'exemples
        examples = self.examples_edit.text()
        if len(examples) > EXAMPLES_MAX_LENGTH:
            QMessageBox.warning(
                self,
                "Avís",
                f"Els exemples no poden excedir {EXAMPLES_MAX_LENGTH} caràcters.",
            )
            return

        # Obtener contenido
        request = self.request_edit.toHtml()
        solution = self.solution_edit.toHtml()
        examples_text = self.examples_edit.text()

        try:
            if self.current_note_id is None:
                # Crear nova nota
                note_id = self.db.create_note(title, request, solution, examples_text)
                self.current_note_id = note_id
                self.statusBar().showMessage(f"Nota creada: {title}")
                logger.info(f"Nota creada amb ID: {note_id}")
            else:
                # Actualitzar nota existent
                success = self.db.update_note(
                    self.current_note_id, title, request, solution, examples_text
                )
                if success:
                    self.statusBar().showMessage(f"Nota desada: {title}")
                    logger.info(f"Nota {self.current_note_id} actualitzada")
                else:
                    QMessageBox.warning(self, "Error", "No s'ha pogut desar la nota.")
                    return

            # Marcar com a desat
            self.current_note_modified = False
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

            # Actualitzar llista de notes
            self.load_notes()

            # Seleccionar la nota actual a la llista
            for i in range(self.notes_list.count()):
                item = self.notes_list.item(i)
                if item.data(Qt.UserRole) == self.current_note_id:
                    self.notes_list.setCurrentItem(item)
                    break

        except Exception as e:
            logger.error(f"Error desant nota: {e}")
            QMessageBox.critical(
                self, "Error", f"No s'ha pogut desar la nota:\n{str(e)}"
            )

    def delete_current_note(self):
        """Esborra la nota actual."""
        # Evitar esborrar nota si estem editant text i s'ha premut la tecla Delete
        focused = QApplication.focusWidget()
        if isinstance(focused, (QTextEdit, QLineEdit)):
            # Si el focus està en un camp de text, no esborrem la nota
            # (Això permet que la tecla Del funcioni per esborrar caràcters)
            return

        if self.current_note_id is None:
            QMessageBox.warning(
                self, "Avís", "No hi ha cap nota seleccionada per esborrar."
            )
            return

        title = self.title_input.text() or "Nota sense títol"

        msgBox = QMessageBox(self)
        msgBox.setWindowTitle("Confirmar esborrat")
        msgBox.setText(
            f"Estàs segur que vols esborrar la nota '{title}'?\nAquesta acció no es pot desfer."
        )
        msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msgBox.setDefaultButton(QMessageBox.No)
        msgBox.setButtonText(QMessageBox.Yes, "Sí")
        msgBox.setButtonText(QMessageBox.No, "No")
        reply = msgBox.exec()

        if reply == QMessageBox.Yes:
            try:
                # Obtenir imatges per esborrar fitxers després
                images = self.db.get_note_images(self.current_note_id)

                # Esborrar de la base de dades (CASCADE esborrarà les referències d'imatges)
                success = self.db.delete_note(self.current_note_id)

                if success:
                    # Esborrar fitxers d'imatges del disc
                    for img in images:
                        self.image_manager.delete_image_files(
                            img["filename"], img["thumb_filename"]
                        )

                    self.statusBar().showMessage(f"Nota esborrada: {title}")
                    logger.info(f"Nota {self.current_note_id} esborrada")

                    # Netejar editor i recarregar llista
                    self.current_note_id = None
                    self.current_note_modified = False
                    self.new_note()
                    self.load_notes()
                else:
                    QMessageBox.warning(
                        self, "Error", "No s'ha pogut esborrar la nota."
                    )

            except Exception as e:
                logger.error(f"Error esborrant nota: {e}")
                QMessageBox.critical(
                    self, "Error", f"Error en esborrar la nota:\n{str(e)}"
                )

    def open_calculator(self):
        """Obre el diàleg de la calculadora."""
        if (
            hasattr(self, "calculator_window")
            and self.calculator_window is not None
            and hasattr(self.calculator_window, "isVisible")
            and self.calculator_window.isVisible()
        ):
            self.calculator_window.raise_()
            self.calculator_window.activateWindow()
            return

        self.calculator_window = CalculatorDialog(self)
        self.calculator_window.show()
        self.calculator_window.raise_()
        self.calculator_window.activateWindow()
