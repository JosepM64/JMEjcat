"""
Finestra flotant per al mòdul de Tramitació
Gestió de tràmits amb grid, ordenació, cerca i colors
"""

import logging
import csv
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QLineEdit,
    QLabel,
    QMessageBox,
    QWidget,
    QComboBox,
    QMenu,
    QFileDialog,
    QProgressDialog,
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QAction, QColor

from tramitacio_database import TramitacioDatabase
from pdf_exporter import export_table_to_pdf
from ui.tramitacio_edit_dialog import TramitacioEditDialog
from tramitacio_alarms import TramitacioAlarmsDialog

logger = logging.getLogger(__name__)

# Colors disponibles per als markers (semitransparents)
TRAMIT_COLORS = {
    "": ("Sense color", QColor(0, 0, 0, 0)),
    "vermell": ("Vermell (Pendent)", QColor(255, 0, 0, 80)),
    "taronja": ("Taronja (Urgent)", QColor(255, 165, 0, 80)),
    "groc": ("Groc (Atenció)", QColor(255, 255, 0, 80)),
    "verd": ("Verd (Fet)", QColor(0, 255, 0, 80)),
    "blau": ("Blau (Info)", QColor(0, 0, 255, 80)),
    "lila": ("Lila (Especial)", QColor(128, 0, 128, 80)),
    "gris": ("Gris (Archivat)", QColor(128, 128, 128, 80)),
}


class TramitacioWindow(QDialog):
    """Finestra flotant per a la gestió de Tramitació."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        # Reusar la BD del pare (MainWindow) si està disponible
        if parent is not None and hasattr(parent, "tramit_db"):
            self.db = parent.tramit_db
            self._owns_db = False
        else:
            self.db = TramitacioDatabase()
            self._owns_db = True
        self.current_sort_column = 4  # Data column default
        self.current_sort_order = Qt.SortOrder.DescendingOrder
        self.pdf_exporter = None
        self.progress_dialog = None
        self.setup_ui()
        self.load_data()

    def closeEvent(self, event):
        """Tanca la connexió BD si la finestra la posseeix."""
        if getattr(self, "_owns_db", False) and hasattr(self, "db"):
            self.db.close()
        super().closeEvent(event)
        super().closeEvent(event)

    def setup_ui(self):
        """Configura la interfície d'usuari."""
        self.setWindowTitle("Tramitació")
        self.setMinimumSize(1050, 600)
        self.resize(1050, 600)
        self.setModal(False)  # Finestra flotant independent

        layout = QVBoxLayout(self)

        # Titol
        title_label = QLabel("Gestió de Tramitació")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 5px;")
        layout.addWidget(title_label)

        # Cercador
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Cercar:"))

        self.search_numero = QLineEdit()
        self.search_numero.setPlaceholderText("Número")
        self.search_numero.setMaximumWidth(80)
        self.search_numero.textChanged.connect(self.on_search_changed)
        search_layout.addWidget(self.search_numero)

        self.search_any = QLineEdit()
        self.search_any.setPlaceholderText("Any")
        self.search_any.setMaximumWidth(60)
        self.search_any.textChanged.connect(self.on_search_changed)
        search_layout.addWidget(self.search_any)

        search_layout.addWidget(QLabel(" Color:"))
        self.color_filter = QComboBox()
        self.color_filter.addItem("Tots", "")
        for color_key, (color_name, _) in TRAMIT_COLORS.items():
            if color_key:
                self.color_filter.addItem(color_name, color_key)
        self.color_filter.currentIndexChanged.connect(self.on_search_changed)
        search_layout.addWidget(self.color_filter)

        # Botó per esborrar filtres
        self.btn_clear_filters = QPushButton("Netejar")
        self.btn_clear_filters.clicked.connect(self.clear_filters)
        search_layout.addWidget(self.btn_clear_filters)

        search_layout.addStretch()
        layout.addLayout(search_layout)

        # Taula/Grid
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["⏰", "ID", "Número", "Any", "Data", "Info"]
        )

        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionsClickable(True)
        header.setSortIndicatorShown(True)
        header.sectionClicked.connect(self.on_header_clicked)

        self.table.setColumnWidth(0, 25)  # ⏰ recordatori
        self.table.setColumnHidden(1, True)  # Ocultar ID
        self.table.setColumnWidth(2, 60)  # Número (5 dígits)
        self.table.setColumnWidth(3, 50)  # Any (4 dígits)
        self.table.setColumnWidth(4, 90)  # Data

        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(
            QTableWidget.EditTrigger.DoubleClicked
            | QTableWidget.EditTrigger.EditKeyPressed
        )
        self.table.cellDoubleClicked.connect(self.on_cell_double_clicked)

        # Menú contextual per canviar colors
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)

        self.table.setSortingEnabled(False)

        layout.addWidget(self.table)

        # Botons
        button_layout = QHBoxLayout()

        self.btn_nou = QPushButton("Nou")
        self.btn_nou.clicked.connect(self.on_nou_clicked)
        button_layout.addWidget(self.btn_nou)

        self.btn_editar = QPushButton("Editar")
        self.btn_editar.clicked.connect(self.on_editar_clicked)
        button_layout.addWidget(self.btn_editar)

        self.btn_eliminar = QPushButton("Eliminar")
        self.btn_eliminar.clicked.connect(self.on_eliminar_clicked)
        button_layout.addWidget(self.btn_eliminar)

        self.btn_actualitzar = QPushButton("Actualitzar")
        self.btn_actualitzar.clicked.connect(self.load_data)
        button_layout.addWidget(self.btn_actualitzar)

        self.btn_export_csv = QPushButton("Exportar CSV")
        self.btn_export_csv.clicked.connect(self.export_csv)
        button_layout.addWidget(self.btn_export_csv)

        self.btn_export_pdf = QPushButton("Exportar PDF")
        self.btn_export_pdf.clicked.connect(self.export_pdf)
        button_layout.addWidget(self.btn_export_pdf)

        self.btn_alarms = QPushButton("⏰ Alarmes")
        self.btn_alarms.clicked.connect(self.show_alarms)
        button_layout.addWidget(self.btn_alarms)

        button_layout.addStretch()

        self.btn_tancar = QPushButton("Tancar")
        self.btn_tancar.clicked.connect(self.close)
        button_layout.addWidget(self.btn_tancar)

        layout.addLayout(button_layout)

    def load_data(self):
        """Carrega les dades de la base de dades."""
        try:
            numero = self.search_numero.text().strip()
            any_text = self.search_any.text().strip()
            color_filter = self.color_filter.currentData()

            any_val = None
            if any_text.isdigit():
                any_val = int(any_text)

            if numero or any_val or color_filter:
                tramits = self.db.search_tramits(numero, any_val, color_filter)
            else:
                tramits = self.db.get_all_tramits(color_filter)

            self.table.setRowCount(len(tramits))

            for row, tramit in enumerate(tramits):
                # Columna 0: ⏰ recordatori
                reminder_item = QTableWidgetItem(
                    "⏰" if tramit.get("reminder_at") else ""
                )
                reminder_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 0, reminder_item)

                # Columna 1: ID (ocult)
                self.table.setItem(row, 1, QTableWidgetItem(str(tramit["id"])))

                self.table.setItem(row, 2, QTableWidgetItem(tramit["numero"]))
                self.table.setItem(row, 3, QTableWidgetItem(str(tramit["any"])))

                data_item = QTableWidgetItem(tramit["data"])
                date_obj = QDate.fromString(tramit["data"], "dd/MM/yyyy")
                data_item.setData(Qt.ItemDataRole.UserRole, date_obj)
                self.table.setItem(row, 4, data_item)

                self.table.setItem(row, 5, QTableWidgetItem(tramit["info"] or ""))

                # Aplicar color de fons
                tramit_color = tramit.get("color", "")
                if tramit_color and tramit_color in TRAMIT_COLORS:
                    color = TRAMIT_COLORS[tramit_color][1]
                    for col in range(1, 6):
                        item = self.table.item(row, col)
                        if item:
                            item.setBackground(color)

        except Exception as e:
            logger.error(f"Error carregant dades: {e}")
            QMessageBox.critical(self, "Error", f"Error carregant dades: {e}")

    def open_tramit_by_id(self, tramit_id: int):
        """Obre el diàleg d'edició per a un tràmit especific per ID."""
        try:
            tramit = self.db.get_tramit(tramit_id)
            if tramit:
                dialog = TramitacioEditDialog(self, tramit, db=self.db)
                if dialog.exec():
                    self.load_data()  # Actualitzar la llista si s'han fet canvis
                    # Aplicar color de fons si hi ha color
                    tramit_color = tramit.get("color", "")
                    if tramit_color and tramit_color in TRAMIT_COLORS:
                        color = TRAMIT_COLORS[tramit_color][1]
                        # Trobar la fila del tràmit actualitzat per aplicar el color
                        for row in range(self.table.rowCount()):
                            if int(self.table.item(row, 1).text()) == tramit_id:
                                for col in range(1, 6):
                                    item = self.table.item(row, col)
                                    if item:
                                        item.setBackground(color)
                                break
            self.sort_data()
        except Exception as e:
            logger.error(f"Error carregant dades: {e}")
            QMessageBox.critical(self, "Error", f"Error carregant dades: {e}")

    def sort_data(self):
        """Ordena les dades segons la columna actual."""
        if self.current_sort_column == 4:
            self.sort_by_date()
        else:
            self.table.sortItems(self.current_sort_column, self.current_sort_order)
        # Mostrar indicador d'ordenació al header
        self.table.horizontalHeader().setSortIndicator(
            self.current_sort_column, self.current_sort_order
        )

    def sort_by_date(self):
        """Ordena les dades per data (dd/MM/yyyy)."""
        from datetime import datetime

        rows = []
        for row in range(self.table.rowCount()):
            data_str = self.table.item(row, 4).text()
            try:
                data_obj = datetime.strptime(data_str, "%d/%m/%Y")
            except ValueError:
                data_obj = datetime.min
            rows.append((row, data_obj))
        rows.sort(
            key=lambda x: x[1],
            reverse=(self.current_sort_order == Qt.SortOrder.DescendingOrder),
        )
        self.table.setSortingEnabled(False)
        # Desassignar tots els ítems de la taula (take)
        # per evitar problemes de propietat
        original_items = {}
        for row in range(self.table.rowCount()):
            row_items = []
            for col in range(6):
                item = self.table.takeItem(row, col)
                row_items.append(item)
            original_items[row] = row_items
        # Tornar a inserir els ítems en l'ordenat
        for new_row, (old_row, _) in enumerate(rows):
            row_items = original_items[old_row]
            for col in range(6):
                item = row_items[col]
                if item:
                    self.table.setItem(new_row, col, item)

    def on_header_clicked(self, column: int):
        """Gestiona el clic a la capçalera per ordenar."""
        if column <= 1:  # ⏰ (0) i ID (1) - no ordenar
            return
        if self.current_sort_column == column:
            # Canviar ordre
            if self.current_sort_order == Qt.SortOrder.AscendingOrder:
                self.current_sort_order = Qt.SortOrder.DescendingOrder
            else:
                self.current_sort_order = Qt.SortOrder.AscendingOrder
        else:
            self.current_sort_column = column
            self.current_sort_order = Qt.SortOrder.AscendingOrder
        self.sort_data()

    def on_search_changed(self):
        """Gestiona el canvi al cercador."""
        self.load_data()

    def clear_filters(self):
        """Esborra tots els filtres de cerca."""
        self.search_numero.clear()
        self.search_any.clear()
        self.color_filter.setCurrentIndex(0)  # "Tots" colors

    def show_context_menu(self, pos):
        """Mostra el menú contextual per canviar colors."""
        item = self.table.itemAt(pos)
        if not item:
            return
        row = item.row()
        tramit_id = int(self.table.item(row, 1).text())
        menu = QMenu(self)
        # Opció per treure color
        action_clear = QAction("Sense color", self)
        action_clear.triggered.connect(lambda: self.set_row_color(tramit_id, ""))
        menu.addAction(action_clear)
        menu.addSeparator()
        # Opcions de color
        for color_key, (color_name, _) in TRAMIT_COLORS.items():
            if color_key:
                action = QAction(color_name, self)
                action.triggered.connect(
                    lambda checked, ck=color_key: self.set_row_color(tramit_id, ck)
                )
                menu.addAction(action)
        menu.exec(self.table.viewport().mapToGlobal(pos))

    def set_row_color(self, tramit_id: int, color: str):
        """Canvia el color d'una tramitació."""
        try:
            self.db.update_color(tramit_id, color)
            self.load_data()
        except Exception as e:
            logger.error(f"Error canviant color: {e}")
            QMessageBox.critical(self, "Error", f"Error canviant color: {e}")

    def on_nou_clicked(self):
        """Obre el diàleg per crear un nou tràmit.
        Si hi ha valors al cercador, els utilitza com a valors inicials."""
        # Obtenir valors del cercador
        numero = self.search_numero.text().strip()
        any_text = self.search_any.text().strip()
        dialog = TramitacioEditDialog(
            self, initial_numero=numero, initial_any=any_text, db=self.db
        )
        if dialog.exec():
            self.load_data()

    def _get_tramit_id(self, row: int) -> int | None:
        try:
            return int(self.table.item(row, 1).text())
        except (ValueError, AttributeError):
            logger.error(f"ID invàlid a la fila {row}")
            return None

    def on_editar_clicked(self):
        """Obre el diàleg per editar el tràmit seleccionat."""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Avís", "Selecciona un tràmit per editar.")
            return
        tramit_id = self._get_tramit_id(row)
        if tramit_id is None:
            QMessageBox.warning(self, "Error", "ID de tràmit invàlid.")
            return
        tramit = self.db.get_tramit(tramit_id)
        if tramit:
            dialog = TramitacioEditDialog(self, tramit, db=self.db)
            if dialog.exec():
                self.load_data()

    def on_cell_double_clicked(self, row: int, column: int):
        """Obre el diàleg per editar quan es fa doble clic a una cel·la."""
        if column <= 1:  # ⏰ i ID - ignorar
            return
        tramit_id = self._get_tramit_id(row)
        if tramit_id is None:
            return
        tramit = self.db.get_tramit(tramit_id)
        if tramit:
            dialog = TramitacioEditDialog(self, tramit, db=self.db)
            if dialog.exec():
                self.load_data()

    def on_eliminar_clicked(self):
        """Elimina el tràmit seleccionat."""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Avís", "Selecciona un tràmit per eliminar.")
            return
        tramit_id = self._get_tramit_id(row)
        if tramit_id is None:
            return
        reply = QMessageBox.question(
            self,
            "Confirmar eliminació",
            "Segur que vols eliminar aquest tràmit?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self.db.delete_tramit(tramit_id):
                self.load_data()
            else:
                QMessageBox.critical(self, "Error", "Error eliminant el tràmit.")

    def show_alarms(self):
        """Mostra la finestra d'alarmes."""
        dialog = TramitacioAlarmsDialog(self)
        dialog.show()

    def export_csv(self):
        """Exporta les dades a un fitxer CSV."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Exportar a CSV", "", "CSV (*.csv)"
        )
        if not file_path:
            return
        try:
            with open(file_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f, quoting=csv.QUOTE_ALL)
                writer.writerow(["Número", "Any", "Data", "Info"])
                for row in range(self.table.rowCount()):
                    row_data = []
                    for col in range(1, 5):
                        item = self.table.item(row, col)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)
            QMessageBox.information(self, "Exportat", f"CSV guardat a:\n{file_path}")
        except Exception as e:
            logger.error(f"Error exportant CSV: {e}")
            QMessageBox.critical(self, "Error", f"Error exportant: {e}")

    def export_pdf(self):
        """Exporta les dades a un fitxer PDF amb format elegant."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Exportar a PDF", "Tramitacio.pdf", "PDF (*.pdf)"
        )
        if not file_path:
            return
        try:
            # Recolectar datos de la tabla
            data = []
            for row in range(self.table.rowCount()):
                row_data = []
                for col in range(2, 6):  # columnes visibles: Número, Any, Data, Info
                    item = self.table.item(row, col)
                    row_data.append(item.text() if item else "")
                data.append(row_data)
            headers = ["Número", "Any", "Data", "Info"]
            output_path = Path(file_path)
            # Mostrar diàleg de progrés
            self.progress_dialog = QProgressDialog(
                "S'està exportant a PDF...", "Cancel·lar", 0, 0, self
            )
            self.progress_dialog.setWindowTitle("Exportant a PDF")
            self.progress_dialog.setWindowModality(Qt.WindowModal)
            self.progress_dialog.setCancelButton(None)
            self.progress_dialog.show()
            # Exportar en fil separat, guardant referència
            self.pdf_exporter = export_table_to_pdf(
                data=data,
                headers=headers,
                title="Tramitació",
                output_path=output_path,
                parent=self,
                callback=lambda success, msg, path: self._on_pdf_export_finished(
                    success, msg, path
                ),
            )
        except Exception as e:
            logger.error(f"Error exportant PDF: {e}")
            QMessageBox.critical(self, "Error", f"Error exportant: {e}")

    def _on_pdf_export_finished(self, success: bool, message: str, pdf_path: str = ""):
        """Callback cuando la exportación PDF termina"""
        if hasattr(self, "progress_dialog") and self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
        # Netejar referència al exporter
        self.pdf_exporter = None
        if success:
            QMessageBox.information(self, "Exportat", message)
        else:
            QMessageBox.critical(self, "Error", message)
