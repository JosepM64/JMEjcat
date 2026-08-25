"""
Finestra d'alarmes de Tramitació
Mostra les alarmes ordenades cronològicament amb accés ràpid al tràmit
"""

import logging
from datetime import datetime
from typing import Optional

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QLabel,
    QWidget,
    QCheckBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from tramitacio_database import TramitacioDatabase

logger = logging.getLogger(__name__)


class TramitacioAlarmsDialog(QDialog):
    """Finestra d'alarmes de Tramitació."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        if parent is not None and hasattr(parent, "tramit_db"):
            self.db = parent.tramit_db
            self._owns_db = False
        else:
            self.db = TramitacioDatabase()
            self._owns_db = True
        self.include_past = False
        self.setup_ui()
        self.load_alarms()

    def closeEvent(self, event):
        if getattr(self, "_owns_db", False) and hasattr(self, "db"):
            self.db.close()
        super().closeEvent(event)

    def setup_ui(self):
        self.setWindowTitle("⏰ Alarmes de Tramitació")
        self.setMinimumSize(600, 400)
        self.setModal(False)

        layout = QVBoxLayout(self)

        # Capçalera
        header_layout = QHBoxLayout()
        title = QLabel("⏰ Alarmes Programades")
        title.setStyleSheet("font-size: 14px; font-weight: bold; padding: 5px;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        self.chk_include_past = QCheckBox("Mostrar també les passades")
        self.chk_include_past.stateChanged.connect(self.on_filter_changed)
        header_layout.addWidget(self.chk_include_past)

        layout.addLayout(header_layout)

        # Taula d'alarmes
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["⏰ Alarma", "Estat", "Número", "Any", "Data Tràmit", "Info"]
        )

        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionsClickable(True)

        self.table.setColumnWidth(0, 140)  # Data alarma
        self.table.setColumnWidth(1, 70)   # Estat
        self.table.setColumnWidth(2, 60)   # Número
        self.table.setColumnWidth(3, 50)   # Any
        self.table.setColumnWidth(4, 90)   # Data tràmit

        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.doubleClicked.connect(self.on_open_tramit)

        layout.addWidget(self.table)

        # Botons
        btn_layout = QHBoxLayout()

        self.btn_open = QPushButton("📋 Obrir Tràmit")
        self.btn_open.clicked.connect(self.on_open_tramit)
        btn_layout.addWidget(self.btn_open)

        self.btn_refresh = QPushButton("🔄 Actualitzar")
        self.btn_refresh.clicked.connect(self.load_alarms)
        btn_layout.addWidget(self.btn_refresh)

        btn_layout.addStretch()

        self.btn_close = QPushButton("Tancar")
        self.btn_close.clicked.connect(self.close)
        btn_layout.addWidget(self.btn_close)

        layout.addLayout(btn_layout)

    def on_filter_changed(self, state):
        self.include_past = state == Qt.CheckState.Checked.value
        self.load_alarms()

    def load_alarms(self):
        """Carrega les alarmes a la taula."""
        try:
            alarms = self.db.get_alarms(include_past=self.include_past)
            self.table.setRowCount(len(alarms))

            now = datetime.now()

            for row, tramit in enumerate(alarms):
                reminder_str = tramit.get("reminder_at", "")
                # Parsejar data alarma
                try:
                    reminder_dt = datetime.strptime(reminder_str, "%Y-%m-%d %H:%M:%S")
                    is_past = reminder_dt < now
                    alarm_text = reminder_dt.strftime("%d/%m/%Y %H:%M")
                except (ValueError, TypeError):
                    is_past = False
                    alarm_text = reminder_str

                # Columna 0: Data alarma
                alarm_item = QTableWidgetItem(alarm_text)
                alarm_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 0, alarm_item)

                # Columna 1: Estat
                if is_past:
                    estat_text = "PASSADA"
                    estat_color = QColor(255, 200, 200, 150)  # Vermell clar
                else:
                    # Calcular temps restant
                    diff = reminder_dt - now
                    dies = diff.days
                    if dies == 0:
                        estat_text = "AVUI"
                        estat_color = QColor(255, 255, 200, 150)  # Groc clar
                    elif dies <= 3:
                        estat_text = f"{dies}d"
                        estat_color = QColor(255, 220, 180, 150)  # Taronja clar
                    else:
                        estat_text = f"{dies}d"
                        estat_color = QColor(200, 255, 200, 150)  # Verd clar

                estat_item = QTableWidgetItem(estat_text)
                estat_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                estat_item.setBackground(estat_color)
                self.table.setItem(row, 1, estat_item)

                # Columna 2: Número
                self.table.setItem(row, 2, QTableWidgetItem(tramit["numero"]))

                # Columna 3: Any
                self.table.setItem(row, 3, QTableWidgetItem(str(tramit["any"])))

                # Columna 4: Data tràmit
                self.table.setItem(row, 4, QTableWidgetItem(tramit["data"]))

                # Columna 5: Info (resum)
                info = tramit.get("info") or ""
                if len(info) > 60:
                    info = info[:57] + "..."
                self.table.setItem(row, 5, QTableWidgetItem(info))

                # Guardar ID del tràmit com a UserRole a la primera columna
                alarm_item.setData(Qt.ItemDataRole.UserRole, tramit["id"])

                # Aplicar color de fila si té color
                tramit_color = tramit.get("color", "")
                if tramit_color and tramit_color in _get_tramit_colors():
                    color_qcolor = _get_tramit_colors()[tramit_color]
                    for col in range(2, 6):
                        item = self.table.item(row, col)
                        if item:
                            item.setBackground(color_qcolor)

        except Exception as e:
            logger.error(f"Error carregant alarmes: {e}")

    def on_open_tramit(self):
        """Obre el tràmit seleccionat a la finestra de tramitació."""
        row = self.table.currentRow()
        if row < 0:
            return
        tramit_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if tramit_id:
            # Si el pare és TramitacioWindow, cridar open_tramit_by_id
            parent = self.parent()
            if parent and hasattr(parent, "open_tramit_by_id"):
                parent.open_tramit_by_id(tramit_id)
            # Si el pare és MainWindow, obrir finestra de tramitació
            elif parent and hasattr(parent, "open_tramitacio"):
                parent.open_tramitacio()
                # Cercar la finestra de tramitació i obrir el tràmit
                for child in parent.findChildren(type(parent)):
                    if hasattr(child, "open_tramit_by_id"):
                        child.open_tramit_by_id(tramit_id)
                        break


def _get_tramit_colors():
    """Retorna els colors disponibles (importat de tramitacio_window)."""
    try:
        from tramitacio_window import TRAMIT_COLORS
        return {k: v[1] for k, v in TRAMIT_COLORS.items() if k}
    except ImportError:
        return {}
