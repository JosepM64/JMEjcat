"""
Diàlegs reutilitzables per JMEJCat
Separats de ui_window.py per mantenir SoC
"""

import logging
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QFileDialog,
    QMessageBox,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
)
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt

from utils import get_backups_path
from backup_manager import BackupManager

logger = logging.getLogger(__name__)


class NoteLinkDialog(QDialog):
    """Diàleg per seleccionar una nota per enllaçar."""

    def __init__(self, notes, current_note_id, parent=None):
        super().__init__(parent)
        self.notes = notes
        self.current_note_id = current_note_id
        self.selected_note_id = None
        self.selected_title = None
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Seleccionar nota per enllaçar")
        self.setMinimumSize(400, 300)
        layout = QVBoxLayout()

        search_label = QLabel("Cercar:")
        layout.addWidget(search_label)

        search_input = QLineEdit()
        search_input.setPlaceholderText("Escriu per cercar...")
        layout.addWidget(search_input)

        notes_list = QListWidget()
        notes_list.setAlternatingRowColors(True)
        layout.addWidget(notes_list)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        cancel_btn = QPushButton("Cancel·lar")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        select_btn = QPushButton("Seleccionar")
        select_btn.setDefault(True)
        btn_layout.addWidget(select_btn)
        layout.addLayout(btn_layout)

        def update_list():
            query = search_input.text().strip().lower()
            notes_list.clear()
            for note in self.notes:
                if note["id"] == self.current_note_id:
                    continue
                title = note["title"]
                if query and query not in title.lower():
                    continue
                item = QListWidgetItem(title)
                item.setData(Qt.UserRole, note["id"])
                notes_list.addItem(item)

        search_input.textChanged.connect(update_list)
        update_list()

        def on_select():
            current = notes_list.currentItem()
            if not current:
                QMessageBox.warning(self, "Atenció", "Selecciona una nota.")
                return
            self.selected_note_id = current.data(Qt.UserRole)
            self.selected_title = current.text()
            self.accept()

        select_btn.clicked.connect(on_select)
        notes_list.itemDoubleClicked.connect(on_select)
        self.setLayout(layout)


class BackupManagerDialog(QDialog):
    """Gestor de backups amb opcions de restaurar i eliminar."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.setWindowTitle("Restaurar Còpia de Seguretat")
        self.setMinimumSize(550, 450)
        self.setup_ui()

    def setup_ui(self):
        backups = BackupManager.get_backup_list()
        if not backups:
            QMessageBox.information(
                self,
                "Gestor de Backups",
                "No hi ha backups disponibles.\n\n"
                "Es creen backups automàticament quan tanques l'aplicació.",
            )
            self.reject()
            return

        layout = QVBoxLayout(self)

        info_label = QLabel("Selecciona una còpia de seguretat per restaurar:")
        info_label.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(info_label)

        list_widget = QListWidget()
        list_widget.setSelectionMode(QListWidget.SingleSelection)

        for backup in backups:
            item_text = f"[{backup['db_type']}] {backup['date']} - {backup['size_kb']}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, backup["filename"])
            list_widget.addItem(item)

        layout.addWidget(list_widget)

        if list_widget.count() > 0:
            list_widget.setCurrentRow(0)

        button_layout = QHBoxLayout()

        restore_btn = QPushButton("🔄 Restaurar")
        restore_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3; color: white;
                padding: 8px 16px; border-radius: 4px;
            }
            QPushButton:hover { background-color: #1976D2; }
        """)

        delete_btn = QPushButton("🗑️ Eliminar")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336; color: white;
                padding: 8px 16px; border-radius: 4px;
            }
            QPushButton:hover { background-color: #d32f2f; }
        """)

        close_btn = QPushButton("❌ Tancar")

        button_layout.addWidget(restore_btn)
        button_layout.addWidget(delete_btn)
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)

        def do_restore():
            selected = list_widget.currentItem()
            if not selected:
                QMessageBox.warning(self, "Error", "Selecciona un backup primer.")
                return

            filename = selected.data(Qt.UserRole)

            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Confirmar Restauració")
            msg_box.setText(
                f"Vols restaurar la còpia de seguretat del {selected.text()}?\n\n"
                "Les dades actuals es sobreescriuran."
            )
            msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg_box.button(QMessageBox.Yes).setText("Sí")
            msg_box.button(QMessageBox.No).setText("No")
            msg_box.setDefaultButton(QMessageBox.No)
            reply = msg_box.exec()

            if reply == QMessageBox.Yes:
                try:
                    success = BackupManager.restore_backup(filename)
                    if success:
                        QMessageBox.information(
                            self,
                            "Èxit",
                            "Backup restaurat correctament.\n\n"
                            "L'aplicació es reiniciarà per aplicar els canvis.",
                        )
                        self.accept()
                        if self.main_window:
                            self.main_window.load_notes()
                            self.main_window.new_note()
                            self.main_window.statusBar().showMessage("Backup restaurat")
                    else:
                        QMessageBox.critical(
                            self, "Error", "No s'ha pogut restaurar el backup."
                        )
                except Exception as e:
                    QMessageBox.critical(
                        self, "Error", f"Error restaurant backup:\n{str(e)}"
                    )

        def do_delete():
            selected = list_widget.currentItem()
            if not selected:
                QMessageBox.warning(self, "Error", "Selecciona un backup primer.")
                return

            filename = selected.data(Qt.UserRole)

            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Confirmar Eliminar")
            msg_box.setText(
                f"Vols eliminar la còpia de seguretat del {selected.text()}?\n\n"
                "Aquesta acció no es pot desfer."
            )
            msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg_box.button(QMessageBox.Yes).setText("Sí")
            msg_box.button(QMessageBox.No).setText("No")
            msg_box.setDefaultButton(QMessageBox.No)
            reply = msg_box.exec()

            if reply == QMessageBox.Yes:
                try:
                    backup_path = get_backups_path() / filename
                    backup_path.unlink()

                    row = list_widget.currentRow()
                    list_widget.takeItem(row)

                    QMessageBox.information(
                        self, "Èxit", "Backup eliminat correctament."
                    )
                except Exception as e:
                    QMessageBox.critical(
                        self, "Error", f"Error eliminant backup:\n{str(e)}"
                    )

        restore_btn.clicked.connect(do_restore)
        delete_btn.clicked.connect(do_delete)
        close_btn.clicked.connect(self.reject)

        self.setLayout(layout)


class VerifyBackupsDialog(QDialog):
    """Diàleg per verificar la integritat dels backups en una carpeta."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Verificació de Backups")
        self.setMinimumSize(700, 500)
        self.setup_ui()

    def setup_ui(self):
        from backup_manager import BackupManager

        folder = QFileDialog.getExistingDirectory(
            self, "Selecciona la carpeta de backups a verificar", str(Path.home())
        )
        if not folder:
            self.reject()
            return

        folder_path = Path(folder)
        backups = BackupManager.verify_backups_in_folder(folder_path)

        self.setWindowTitle(f"Verificació de Backups - {folder_path.name}")
        layout = QVBoxLayout(self)

        info_label = QLabel(
            f"Backups verificats a: {folder_path}\nTotal: {len(backups)} fitxers"
        )
        layout.addWidget(info_label)

        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["Nom", "Tipus", "Mida", "Estat", "Error"])
        table.setRowCount(len(backups))
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setEditTriggers(QTableWidget.NoEditTriggers)

        for row, bk in enumerate(backups):
            table.setItem(row, 0, QTableWidgetItem(bk["filename"]))
            table.setItem(row, 1, QTableWidgetItem(bk["db_type"]))
            table.setItem(row, 2, QTableWidgetItem(bk["size_kb"]))
            status_item = QTableWidgetItem("✅ Vàlid" if bk["valid"] else "❌ Corrupte")
            status_item.setForeground(QColor("#4CAF50" if bk["valid"] else "#F44336"))
            table.setItem(row, 3, status_item)
            error_item = QTableWidgetItem(bk.get("error") or "")
            table.setItem(row, 4, error_item)

        table.resizeColumnsToContents()
        layout.addWidget(table)

        close_btn = QPushButton("Tancar")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        self.setLayout(layout)
