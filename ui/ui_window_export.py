"""PDF and Markdown export orchestration mixin for MainWindow."""

import logging
from pathlib import Path

from PySide6.QtWidgets import QFileDialog, QMessageBox, QProgressDialog
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import Qt, QUrl

from pdf_exporter import export_notes_to_pdf
from md_exporter import export_notes_to_md

logger = logging.getLogger(__name__)


class UiWindowExportMixin:
    """Mixin: PDF/MD export orchestration, export dialogs."""

    def export_current_note_pdf(self):
        """Exporta la nota actual a PDF."""
        if self.current_note_id is None:
            QMessageBox.warning(
                self,
                "Error",
                "No hi ha cap nota seleccionada per exportar.\n"
                "Selecciona una nota o crea una nova.",
            )
            return

        # Obtenir la nota actual
        note = self.db.get_note(self.current_note_id)
        if not note:
            QMessageBox.warning(self, "Error", "No s'ha pogut obtenir la nota.")
            return

        # Diàleg per seleccionar on guardar
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Exportar Nota a PDF", f"{note['title']}.pdf", "PDF (*.pdf)"
        )

        if not file_path:
            return

        output_path = Path(file_path)

        # Mostrar diàleg de progrés
        self.progress_dialog = QProgressDialog(
            "S'està exportant la nota a PDF...", "Cancel·lar", 0, 0, self
        )
        self.progress_dialog.setWindowTitle("Exportant a PDF")
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setCancelButton(None)
        self.progress_dialog.show()

        # Exportar en fil separat
        self.pdf_exporter = export_notes_to_pdf(
            [note],
            output_path,
            parent=self,
            callback=lambda success, msg, path: self._on_pdf_export_finished(
                success, msg, path
            ),
        )

    def export_all_notes_pdf(self):
        """Exporta totes les notes a PDF."""
        notes = self.db.get_all_notes()

        if not notes:
            QMessageBox.information(self, "Informació", "No hi ha notes per exportar.")
            return

        # Diàleg per seleccionar on guardar
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Exportar Totes les Notes a PDF", "JMEJCat_Notes.pdf", "PDF (*.pdf)"
        )

        if not file_path:
            return

        output_path = Path(file_path)

        # Confirmar si hi ha moltes notes
        if len(notes) > 10:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Confirmar Exportació")
            msg_box.setText(
                f"Vols exportar {len(notes)} notes a PDF?\n\nAixò pot trigar uns segons."
            )
            msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg_box.button(QMessageBox.Yes).setText("Sí")
            msg_box.button(QMessageBox.No).setText("No")
            msg_box.setDefaultButton(QMessageBox.No)
            reply = msg_box.exec()
            if reply != QMessageBox.Yes:
                return

        # Mostrar diàleg de progrés
        self.progress_dialog = QProgressDialog(
            f"S'estan exportant {len(notes)} notes a PDF...", "Cancel·lar", 0, 0, self
        )
        self.progress_dialog.setWindowTitle("Exportant a PDF")
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setCancelButton(None)
        self.progress_dialog.show()

        # Exportar en fil separat
        self.pdf_exporter = export_notes_to_pdf(
            notes,
            output_path,
            parent=self,
            callback=lambda success, msg, path: self._on_pdf_export_finished(
                success, msg, path
            ),
        )

    def _on_pdf_export_finished(self, success: bool, message: str, pdf_path: str = ""):
        """
        Callback quan acaba l'exportació a PDF.
        """
        if hasattr(self, "progress_dialog") and self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None

        if success and pdf_path:
            # Mostrar diàleg amb opcions
            msgBox = QMessageBox(self)
            msgBox.setWindowTitle("Exportació completada")
            msgBox.setText("PDF exportat correctament!")
            msgBox.setInformativeText("Què vols fer ara?")

            btn_open = msgBox.addButton("Obrir PDF", QMessageBox.ActionRole)
            btn_folder = msgBox.addButton("Obrir carpeta", QMessageBox.ActionRole)
            msgBox.addButton("Tancar", QMessageBox.RejectRole)

            msgBox.exec()

            clicked = msgBox.clickedButton()

            if clicked == btn_open:
                QDesktopServices.openUrl(QUrl.fromLocalFile(pdf_path))
            elif clicked == btn_folder:
                folder_path = str(Path(pdf_path).parent)
                QDesktopServices.openUrl(QUrl.fromLocalFile(folder_path))

            self.statusBar().showMessage("PDF exportat correctament")
        elif success:
            QMessageBox.information(self, "Èxit", message)
            self.statusBar().showMessage("PDF exportat correctament")
        else:
            QMessageBox.critical(self, "Error", message)

    def export_current_note_md(self):
        """Exporta la nota actual a Markdown."""
        if self.current_note_id is None:
            QMessageBox.warning(self, "Error", "No hi ha cap nota seleccionada.")
            return

        note = self.db.get_note(self.current_note_id)
        if not note:
            QMessageBox.warning(self, "Error", "No s'ha pogut obtenir la nota.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Exportar Nota a Markdown", f"{note['title']}.md", "Markdown (*.md)"
        )
        if not file_path:
            return

        export_notes_to_md([note], Path(file_path), all_in_one=True)
        QMessageBox.information(self, "Èxit", f"Nota exportada a:\n{file_path}")

    def export_all_notes_md(self):
        """Exporta totes les notes a Markdown (un sol fitxer)."""
        notes = self.db.get_all_notes()
        if not notes:
            QMessageBox.information(self, "Informació", "No hi ha notes per exportar.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Exportar Notes a Markdown", "JMEJCat_Notes.md", "Markdown (*.md)"
        )
        if not file_path:
            return

        export_notes_to_md(notes, Path(file_path), all_in_one=True)
        QMessageBox.information(
            self, "Èxit", f"{len(notes)} notes exportades a:\n{file_path}"
        )
