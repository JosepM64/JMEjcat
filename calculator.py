"""
Mòdul de càlculs senzills per a JMEJCat
Proporciona utilitats per a despeses i restes de pagaments
"""

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)


class CustomSpinBox(QDoubleSpinBox):
    """QDoubleSpinBox personalitzat que selecciona tot el text en rebre focus."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
        self.setGroupSeparatorShown(True)
        self.setRange(0, 99999999.99)
        self.setDecimals(2)

    def focusInEvent(self, event):
        super().focusInEvent(event)
        # Seleccionar tot el text desprès d'un breu instant
        # per assegurar que el focus s'ha establert
        QTimer.singleShot(0, self.selectAll)


class CalculatorDialog(QDialog):
    """Diàleg de càlculs ràpids."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Calculadora de Notes - JMEJCat")
        self.setMinimumWidth(500)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # --- SECCIÓ 1: CÀLCUL 30% ---
        section1 = QFrame()
        section1.setFrameShape(QFrame.Shape.StyledPanel)
        section1.setFrameShadow(QFrame.Shadow.Raised)
        s1_layout = QVBoxLayout(section1)

        title1 = QLabel("<b>Càlcul de Despeses (30%)</b>")
        s1_layout.addWidget(title1)

        grid1 = QGridLayout()

        # Principal
        grid1.addWidget(QLabel("Principal:"), 0, 0)
        self.principal_input = CustomSpinBox()
        self.principal_input.valueChanged.connect(self.calculate_gastos)
        grid1.addWidget(self.principal_input, 0, 1)

        # Gastos (30%)
        grid1.addWidget(QLabel("Gastos (30%):"), 1, 0)
        self.gastos_result = QLabel("0,00")
        self.gastos_result.setStyleSheet("color: #d32f2f; font-weight: bold;")
        grid1.addWidget(self.gastos_result, 1, 1)

        # Total
        grid1.addWidget(QLabel("TOTAL (Sumatori):"), 2, 0)
        self.total_sum_result = QLabel("0,00")
        self.total_sum_result.setStyleSheet(
            "color: #2e7d32; font-weight: bold; font-size: 14px;"
        )
        grid1.addWidget(self.total_sum_result, 2, 1)

        # Botons secció 1
        s1_buttons = QHBoxLayout()
        copy_gastos_btn = QPushButton("📋 Copiar Gastos")
        copy_gastos_btn.clicked.connect(self.copy_gastos)

        copy_total_btn = QPushButton("📋 Copiar Total")
        copy_total_btn.clicked.connect(self.copy_total)

        clear1_btn = QPushButton("🗑️ Esborrar")
        clear1_btn.clicked.connect(self.clear_section1)

        s1_buttons.addWidget(copy_gastos_btn)
        s1_buttons.addWidget(copy_total_btn)
        s1_buttons.addWidget(clear1_btn)

        s1_layout.addLayout(grid1)
        s1_layout.addLayout(s1_buttons)
        layout.addWidget(section1)

        # --- SECCIÓ 2: RESTA DE PAGAMENTS ---
        section2 = QFrame()
        section2.setFrameShape(QFrame.Shape.StyledPanel)
        section2.setFrameShadow(QFrame.Shadow.Raised)
        s2_layout = QVBoxLayout(section2)

        title2 = QLabel("<b>Càlcul de Resta de Pagaments</b>")
        s2_layout.addWidget(title2)

        grid2 = QGridLayout()

        # Inicial
        grid2.addWidget(QLabel("Quantitat Inicial:"), 0, 0)
        self.inicial_input = CustomSpinBox()
        self.inicial_input.valueChanged.connect(self.calculate_resta)
        grid2.addWidget(self.inicial_input, 0, 1)

        # Pagament 1
        grid2.addWidget(QLabel("Pagament 1:"), 1, 0)
        self.pag1_input = CustomSpinBox()
        self.pag1_input.valueChanged.connect(self.calculate_resta)
        grid2.addWidget(self.pag1_input, 1, 1)

        # Pagament 2
        grid2.addWidget(QLabel("Pagament 2:"), 2, 0)
        self.pag2_input = CustomSpinBox()
        self.pag2_input.valueChanged.connect(self.calculate_resta)
        grid2.addWidget(self.pag2_input, 2, 1)

        # Pagament 3
        grid2.addWidget(QLabel("Pagament 3:"), 3, 0)
        self.pag3_input = CustomSpinBox()
        self.pag3_input.valueChanged.connect(self.calculate_resta)
        grid2.addWidget(self.pag3_input, 3, 1)

        # Resta
        grid2.addWidget(QLabel("RESTA:"), 4, 0)
        self.resta_result = QLabel("0,00")
        self.resta_result.setStyleSheet(
            "color: #1976d2; font-weight: bold; font-size: 14px;"
        )
        grid2.addWidget(self.resta_result, 4, 1)

        # Botons secció 2
        s2_buttons = QHBoxLayout()
        copy_resta_btn = QPushButton("📋 Copiar Resta")
        copy_resta_btn.clicked.connect(self.copy_resta)

        clear2_btn = QPushButton("🗑️ Esborrar")
        clear2_btn.clicked.connect(self.clear_section2)

        s2_buttons.addWidget(copy_resta_btn)
        s2_buttons.addWidget(clear2_btn)

        s2_layout.addLayout(grid2)
        s2_layout.addLayout(s2_buttons)
        layout.addWidget(section2)

        # --- SECCIÓ 3: TAXACIÓ DE COURES ---
        section3 = QFrame()
        section3.setFrameShape(QFrame.Shape.StyledPanel)
        section3.setFrameShadow(QFrame.Shadow.Raised)
        s3_layout = QVBoxLayout(section3)

        title3 = QLabel("<b>Taxació de costes</b>")
        s3_layout.addWidget(title3)

        grid3 = QGridLayout()

        grid3.addWidget(QLabel("Procurador:"), 0, 0)
        self.procurador_input = CustomSpinBox()
        self.procurador_input.valueChanged.connect(self.calculate_taxacio)
        grid3.addWidget(self.procurador_input, 0, 1)

        grid3.addWidget(QLabel("Advocat:"), 1, 0)
        self.advocat_input = CustomSpinBox()
        self.advocat_input.valueChanged.connect(self.calculate_taxacio)
        grid3.addWidget(self.advocat_input, 1, 1)

        grid3.addWidget(QLabel("Interessos:"), 2, 0)
        self.interessos_input = CustomSpinBox()
        self.interessos_input.valueChanged.connect(self.calculate_taxacio)
        grid3.addWidget(self.interessos_input, 2, 1)

        grid3.addWidget(QLabel("Sumatori:"), 3, 0)
        self.taxacio_result = QLabel("0,00")
        self.taxacio_result.setStyleSheet(
            "color: #2e7d32; font-weight: bold; font-size: 14px;"
        )
        grid3.addWidget(self.taxacio_result, 3, 1)

        s3_buttons = QHBoxLayout()
        copy_taxacio_btn = QPushButton("📋 Copiar Sumatori")
        copy_taxacio_btn.clicked.connect(self.copy_taxacio)

        clear3_btn = QPushButton("🗑️ Esborrar")
        clear3_btn.clicked.connect(self.clear_section3)

        s3_buttons.addWidget(copy_taxacio_btn)
        s3_buttons.addWidget(clear3_btn)

        s3_layout.addLayout(grid3)
        s3_layout.addLayout(s3_buttons)
        layout.addWidget(section3)

        # Botó Tancar
        close_btn = QPushButton("Tancar")
        close_btn.setMinimumHeight(40)
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

    def _format_currency(self, value: float) -> str:
        """Formata un valor com a moneda amb punt de milers i coma decimal."""
        return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def calculate_gastos(self):
        """Calcula el 30% i el total."""
        principal = self.principal_input.value()
        gastos = principal * 0.30
        total = principal + gastos

        self.gastos_result.setText(self._format_currency(gastos))
        self.total_sum_result.setText(self._format_currency(total))

    def calculate_resta(self):
        """Calcula la resta de la quantitat inicial menys els pagaments."""
        inicial = self.inicial_input.value()
        resta = (
            inicial
            - self.pag1_input.value()
            - self.pag2_input.value()
            - self.pag3_input.value()
        )
        self.resta_result.setText(self._format_currency(resta))

    def copy_gastos(self):
        """Copia els gastos al portapapers amb feedback visual."""
        self._copy_to_clipboard(self.gastos_result)

    def copy_total(self):
        """Copia el total al portapapers amb feedback visual."""
        self._copy_to_clipboard(self.total_sum_result)

    def copy_resta(self):
        """Copia la resta al portapapers amb feedback visual."""
        self._copy_to_clipboard(self.resta_result)

    def _reset_button(self, button, original_text):
        """Restaura el text i estil original del botó."""
        button.setText(original_text)
        button.setStyleSheet("")

    def _copy_to_clipboard(self, source_label):
        """Copia el text del source_label al portapapers amb feedback visual."""
        sender = self.sender()
        original_text = sender.text()
        text = source_label.text()
        QApplication.clipboard().setText(text)

        sender.setText("✅ Copiat!")
        sender.setStyleSheet(
            "background-color: #c8e6c9; color: #2e7d32; font-weight: bold;"
        )
        QTimer.singleShot(1000, lambda: self._reset_button(sender, original_text))

    def clear_section1(self):
        """Esborra els valors de la secció 1."""
        self.principal_input.setValue(0)
        self.calculate_gastos()

    def clear_section2(self):
        """Esborra els valors de la secció 2."""
        self.inicial_input.setValue(0)
        self.pag1_input.setValue(0)
        self.pag2_input.setValue(0)
        self.pag3_input.setValue(0)
        self.calculate_resta()

    def calculate_taxacio(self):
        """Calcula el sumatori de Procurador + Advocat + Interessos."""
        total = (
            self.procurador_input.value()
            + self.advocat_input.value()
            + self.interessos_input.value()
        )
        self.taxacio_result.setText(self._format_currency(total))

    def copy_taxacio(self):
        """Copia el sumatori al portapapers amb feedback visual."""
        self._copy_to_clipboard(self.taxacio_result)

    def clear_section3(self):
        """Esborra els valors de la secció 3."""
        self.procurador_input.setValue(0)
        self.advocat_input.setValue(0)
        self.interessos_input.setValue(0)
        self.calculate_taxacio()
