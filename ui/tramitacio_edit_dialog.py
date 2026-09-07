"""
Diàleg per crear/editar un tràmit
"""

import logging
from datetime import datetime
from typing import Any

from PySide6.QtCore import QDateTime, Qt
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDateTimeEdit,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from calculator import CalculatorDialog
from core.tramit_colors import TRAMIT_COLORS
from tramitacio_database import TramitacioDatabase

logger = logging.getLogger(__name__)


class TramitacioEditDialog(QDialog):
    """Diàleg per crear/editar un tràmit."""

    def __init__(
        self,
        parent: QWidget | None = None,
        tramit: dict[str, Any] | None = None,
        initial_numero: str | None = None,
        initial_any: str | None = None,
        db: TramitacioDatabase | None = None,
    ):
        super().__init__(parent)
        self.tramit = tramit if tramit is not None else {}
        self.initial_numero = initial_numero
        self.initial_any = initial_any
        if db is not None:
            self.db = db
            self._owns_db = False
        else:
            self.db = TramitacioDatabase()
            self._owns_db = True
        self.calculator_dialog = None
        self._cancel_clicked = False
        self.setup_ui()
        if tramit:
            self.load_data()
        else:
            # Pre-omplir valors inicials si s'han proporcionat
            if initial_numero:
                self.numero_input.setText(initial_numero)
            if initial_any:
                self.any_input.setText(initial_any)

    def closeEvent(self, event):
        """Auto-guarda en tancar, tanca BD si cal."""
        if not self._cancel_clicked and not self.result():
            self._auto_save_on_close()
        if getattr(self, "_owns_db", False) and hasattr(self, "db"):
            self.db.close()
        super().closeEvent(event)

    def _auto_save_on_close(self):
        """Guarda automàticament si el formulari té dades vàlides."""
        if not self.numero_input.text().strip() or not self.any_input.text().strip():
            return
        self.on_guardar_clicked()

    def setup_ui(self):
        """Configura la interfície del diàleg."""
        if self.tramit:
            self.setWindowTitle("Editar Tràmit")
        else:
            self.setWindowTitle("Nou Tràmit")
        self.setMinimumSize(1050, 600)
        self.resize(1050, 600)
        layout = QVBoxLayout(self)
        # Número
        numero_layout = QHBoxLayout()
        numero_layout.addWidget(QLabel("Número (5 dígits):"))
        self.numero_input = QLineEdit()
        self.numero_input.setMaxLength(5)
        self.numero_input.setPlaceholderText("00000 (1-5 dígits)")
        numero_layout.addWidget(self.numero_input)
        layout.addLayout(numero_layout)
        # Any
        any_layout = QHBoxLayout()
        any_layout.addWidget(QLabel("Any (4 dígits):"))
        self.any_input = QLineEdit()
        self.any_input.setMaxLength(4)
        self.any_input.setPlaceholderText("2026")
        any_layout.addWidget(self.any_input)
        layout.addLayout(any_layout)
        # Data
        data_layout = QHBoxLayout()
        data_layout.addWidget(QLabel("Data (dd/MM/yyyy):"))
        self.data_input = QLineEdit()
        self.data_input.setPlaceholderText("DD/MM/YYYY")
        # Data per defecte: avui (si és nou) o la guardada (si és edició)
        # S'estableix en load_data() o aquí si és nou
        self.btn_data_avui = QPushButton("↻ Avui")
        self.btn_data_avui.setToolTip("Posar data d'avui")
        self.btn_data_avui.clicked.connect(self.on_data_avui_clicked)
        self.btn_data_avui.setMaximumWidth(60)
        data_layout.addWidget(self.data_input)
        data_layout.addWidget(self.btn_data_avui)
        layout.addLayout(data_layout)
        # Info
        info_layout = QVBoxLayout()
        info_layout.addWidget(QLabel("Info:"))
        self.info_input = QTextEdit()
        self.info_input.setPlaceholderText("Informació addicional...")
        self.info_input.setMinimumHeight(120)
        self.info_input.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.info_input.customContextMenuRequested.connect(self.show_info_context_menu)
        info_layout.addWidget(self.info_input, 1)  # Stretch factor = 1
        layout.addLayout(info_layout)
        # Botons
        button_layout = QHBoxLayout()
        # Botó Calculadora (per obrir-lo mentre s'edita)
        self.btn_calculadora = QPushButton("🧮 Calculadora")
        self.btn_calculadora.clicked.connect(self.open_calculator)
        button_layout.addWidget(self.btn_calculadora)
        # Botó Avís
        self.reminder_button = QPushButton("⏰ Establir avís")
        self.reminder_button.clicked.connect(self.open_reminder_dialog)
        button_layout.addWidget(self.reminder_button)
        # Color
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("Color:"))
        self.color_input = QComboBox()
        self.color_input.addItem("Sense color", "")
        for color_key, (color_name, _) in TRAMIT_COLORS.items():
            if color_key:
                self.color_input.addItem(color_name, color_key)
        color_layout.addWidget(self.color_input)
        button_layout.addLayout(color_layout)
        button_layout.addStretch()
        self.btn_guardar = QPushButton("Guardar")
        self.btn_guardar.clicked.connect(self.on_guardar_clicked)
        button_layout.addWidget(self.btn_guardar)
        self.btn_cancelar = QPushButton("Cancel·lar")
        self.btn_cancelar.clicked.connect(self._on_cancel_clicked)
        button_layout.addWidget(self.btn_cancelar)
        layout.addLayout(button_layout)

        # Botó petit per treure l'avís (apareix quan hi ha avís)
        reminder_remove_layout = QHBoxLayout()
        reminder_remove_layout.addStretch()
        self.btn_remove_reminder = QPushButton("🗑 Treure avís")
        self.btn_remove_reminder.setFixedHeight(22)
        self.btn_remove_reminder.setStyleSheet("font-size: 10px; padding: 0 6px;")
        self.btn_remove_reminder.clicked.connect(self.remove_reminder)
        self.btn_remove_reminder.setVisible(False)
        reminder_remove_layout.addWidget(self.btn_remove_reminder)
        layout.addLayout(reminder_remove_layout)

    def load_data(self):
        """Carrega les dades del tràmit al formulari."""
        if self.tramit:
            self.numero_input.setText(self.tramit["numero"])
            self.any_input.setText(str(self.tramit["any"]))
            self.data_input.setText(self.tramit["data"])
            self.info_input.setPlainText(self.tramit["info"] or "")
            # Carregar color
            tramit_color = self.tramit.get("color", "")
            index = self.color_input.findData(tramit_color)
            if index >= 0:
                self.color_input.setCurrentIndex(index)
            # Mostrar l'estat de l'avís
            reminder_at = self.tramit.get("reminder_at")
            if reminder_at:
                try:
                    dt = datetime.strptime(reminder_at, "%Y-%m-%d %H:%M:%S")
                    self.reminder_button.setText(
                        f"⏰ Avís establert: {dt.strftime('%d/%m/%Y %H:%M')}"
                    )
                except Exception:
                    self.reminder_button.setText("⏰ Avís establert")
                self.btn_remove_reminder.setVisible(True)
            else:
                self.reminder_button.setText("⏰ Establir avís")
                self.btn_remove_reminder.setVisible(False)
        else:
            # Data per defecte: avui per a nous registres
            avui = datetime.now().strftime("%d/%m/%Y")
            self.data_input.setText(avui)
            self.reminder_button.setText("⏰ Establir avís")

    def show_info_context_menu(self, pos):
        """Mostra menú contextual al camp Info amb opció d'enganxar text pla."""
        menu = self.info_input.createStandardContextMenu()
        menu.addSeparator()
        paste_plain = menu.addAction("📋 Enganxar com a text pla")
        action = menu.exec(self.info_input.mapToGlobal(pos))
        if action == paste_plain:
            clipboard = QApplication.clipboard()
            text = clipboard.text()
            if text:
                cursor = self.info_input.textCursor()
                cursor.insertText(text)

    def on_data_avui_clicked(self):
        """Posa la data d'avui al camp data."""
        avui = datetime.now().strftime("%d/%m/%Y")
        self.data_input.setText(avui)

    def open_calculator(self):
        """Obre la calculadora com a finestra independent."""
        if self.calculator_dialog is not None and self.calculator_dialog.isVisible():
            self.calculator_dialog.raise_()
            self.calculator_dialog.activateWindow()
            return
        self.calculator_dialog = CalculatorDialog(parent=self)
        self.calculator_dialog.show()

    def open_reminder_dialog(self):
        """Obre el dialeg per establir un avís al tràmit."""
        from PySide6.QtWidgets import (
            QDialog,
            QHBoxLayout,
            QLabel,
            QPushButton,
            QVBoxLayout,
        )

        dialog = QDialog(self)
        dialog.setWindowTitle("Estableix l'avís")
        dialog.setMinimumWidth(300)
        layout = QVBoxLayout(dialog)
        label = QLabel("Selecciona la data i hora de l'avís:")
        layout.addWidget(label)
        self.reminder_edit = QDateTimeEdit()
        self.reminder_edit.setCalendarPopup(True)
        self.reminder_edit.setDisplayFormat("dd/MM/yyyy HH:mm")
        # Per defecte: data i hora actual
        self.reminder_edit.setDateTime(QDateTime.currentDateTime())
        layout.addWidget(self.reminder_edit)
        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("Acceptar")
        btn_ok.clicked.connect(dialog.accept)
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(dialog.reject)
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)
        if dialog.exec() == QDialog.Accepted:
            selected_dt = self.reminder_edit.dateTime()
            # Format ISO per a SQLite: YYYY-MM-DD HH:MM:SS
            reminder_str = selected_dt.toString("yyyy-MM-dd HH:mm:ss")
            self.tramit["reminder_at"] = reminder_str
            self.reminder_button.setText(
                f"⏰ Avís establert: {selected_dt.toString('dd/MM/yyyy HH:mm')}"
            )
            self.btn_remove_reminder.setVisible(True)
        else:
            # Si l'usuari cancella, netegem l'avís
            if "reminder_at" in self.tramit:
                del self.tramit["reminder_at"]
            self.reminder_button.setText("⏰ Establir avís")
            self.btn_remove_reminder.setVisible(False)

    def remove_reminder(self):
        """Elimina l'avís programat."""
        self.tramit["reminder_at"] = None
        self.reminder_button.setText("⏰ Establir avís")
        self.btn_remove_reminder.setVisible(False)

    def validate_date(self, date_str: str) -> bool:
        """Valida que la data tingui el format dd/MM/yyyy i sigui vàlida."""
        from utils import validate_date_ddmmyyyy
        return validate_date_ddmmyyyy(date_str)

    def _on_cancel_clicked(self):
        """Cancel·lació explícita: no auto-guarda en tancar."""
        self._cancel_clicked = True
        self.reject()

    def on_guardar_clicked(self):
        """Guarda el tràmit."""
        numero = self.numero_input.text().strip()
        any_text = self.any_input.text().strip()
        data = self.data_input.text().strip()
        info = self.info_input.toPlainText().strip()
        color = self.color_input.currentData()
        # Validacions
        if not numero or not numero.isdigit() or len(numero) > 5:
            QMessageBox.warning(
                self, "Error", "El número ha de tenir entre 1 i 5 dígits."
            )
            return
        if not any_text or len(any_text) != 4 or not any_text.isdigit():
            QMessageBox.warning(self, "Error", "L'any ha de tenir 4 dígits.")
            return
        if not data:
            QMessageBox.warning(self, "Error", "La data és obligatòria.")
            return
        # Validar format data (dd/MM/yyyy)
        if not self.validate_date(data):
            QMessageBox.warning(
                self, "Error", "La data ha de ser en format dd/MM/yyyy (ex: 10/03/2026)"
            )
            return
        any_val = int(any_text)
        reminder_at = self.tramit.get("reminder_at")

        # Comprovar duplicats (només si és un tràmit nou o si ha canviat número/any)
        existing = None
        is_new = not self.tramit.get("id")
        if is_new:
            existing = self.db.get_tramit_by_numero_any(numero, any_val)
        else:
            # En edició, comprovar si número/any han canviat i xocen amb un altre
            old_numero = self.tramit.get("numero")
            old_any = self.tramit.get("any")
            if numero != old_numero or any_val != old_any:
                existing = self.db.get_tramit_by_numero_any(
                    numero, any_val, exclude_id=self.tramit["id"]
                )

        if existing:
            reply = QMessageBox.question(
                self,
                "Duplicat detectat",
                f"Ja existeix un tràmit amb Número {numero} i Any {any_val}.\n\n"
                f"Vols actualitzar-lo amb les noves dades?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        try:
            if existing and reply == QMessageBox.StandardButton.Yes:
                # Sobreescriure el registre existent duplicat
                self.db.update_tramit(
                    existing["id"], numero, any_val, data, info, color,
                    reminder_at=reminder_at
                )
            elif self.tramit.get("id"):
                # Edició directa: reemplaçar, no mergejar
                self.db.update_tramit(
                    self.tramit["id"], numero, any_val, data, info, color,
                    reminder_at=reminder_at
                )
            else:
                # Tràmit nou
                self.db.create_tramit(
                    numero, any_val, data, info, color,
                    reminder_at=reminder_at
                )
            self.accept()
        except Exception as e:
            logger.error(f"Error guardant tràmit: {e}")
            QMessageBox.critical(self, "Error", f"Error guardant: {e}")
