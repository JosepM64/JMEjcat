"""
Galeria d'imatges per JMEJCat
Widget que mostra una galeria de miniatures
"""

import logging
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QScrollArea,
    QGridLayout,
    QMenu,
)
from PySide6.QtGui import QAction
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, Signal

logger = logging.getLogger(__name__)


class ImageGallery(QWidget):
    """Widget que mostra una galeria de miniatures."""

    image_clicked = Signal(Path)  # Senyal quan es fa clic en una imatge
    image_delete_requested = Signal(int)  # Senyal per esborrar imatge (ID)
    image_move_up_requested = Signal(int)  # Senyal per moure amunt (ID)
    image_move_down_requested = Signal(int)  # Senyal per moure avall (ID)

    def __init__(self):
        super().__init__()
        self.setMinimumHeight(110)  # Reduït de 150 a 110 (2 línies menys)

        # Layout principal
        main_layout = QVBoxLayout()

        # Título
        title_label = QLabel("Imatges adjuntes:")
        title_label.setStyleSheet("font-weight: bold;")
        main_layout.addWidget(title_label)

        # Área de scroll para las miniaturas
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(80)  # Reduït de 120 a 80

        # Widget contenedor de miniaturas
        self.container = QWidget()
        self.grid_layout = QGridLayout(self.container)
        self.grid_layout.setSpacing(5)

        scroll_area.setWidget(self.container)
        main_layout.addWidget(scroll_area)

        self.setLayout(main_layout)

        self.thumbnail_labels = []

    def clear(self):
        """Neteja totes les miniatures."""
        for label in self.thumbnail_labels:
            label.deleteLater()
        self.thumbnail_labels.clear()

        # Limpiar layout
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def add_thumbnail(self, image_id: int, image_path: Path, thumb_path: Path):
        """Afegeix una miniatura a la galeria."""
        if not thumb_path.exists():
            logger.warning(f"Miniatura no trobada: {thumb_path}")
            return

        # Cargar pixmap
        pixmap = QPixmap(str(thumb_path))
        if pixmap.isNull():
            logger.warning(f"No s'ha pogut carregar miniatura: {thumb_path}")
            return

        # Escalar manteniendo relación de aspecto
        pixmap = pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        # Crear label para la miniatura
        label = QLabel()
        label.setPixmap(pixmap)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("""
            QLabel {
                border: 1px solid #ccc;
                border-radius: 3px;
                padding: 2px;
                background: white;
            }
            QLabel:hover {
                border: 2px solid #0078d7;
                padding: 1px;
            }
        """)
        label.setCursor(Qt.PointingHandCursor)
        label.setToolTip(
            f"Fes clic per veure la imatge\nBotó dret per esborrar\n{image_path.name}"
        )

        # Conectar clic i menú de context
        label.mousePressEvent = lambda e, p=image_path, i=image_id: (
            self._on_mouse_press(e, p, i)
        )

        # Calcular posición en grid
        count = len(self.thumbnail_labels)
        row = count // 4
        col = count % 4

        self.grid_layout.addWidget(label, row, col)
        self.thumbnail_labels.append(label)

    def _on_mouse_press(self, event, image_path: Path, image_id: int):
        """Gestiona el clic en una miniatura."""
        if event.button() == Qt.LeftButton:
            self.image_clicked.emit(image_path)
        elif event.button() == Qt.RightButton:
            self._show_context_menu(event.globalPos(), image_id)

    def _show_context_menu(self, pos, image_id: int):
        """Mostra el menú de context per a una imatge."""
        menu = QMenu(self)

        move_up_action = QAction("⬆ Pujar una posició", self)
        move_up_action.triggered.connect(
            lambda: self.image_move_up_requested.emit(image_id)
        )
        menu.addAction(move_up_action)

        move_down_action = QAction("⬇ Baixar una posició", self)
        move_down_action.triggered.connect(
            lambda: self.image_move_down_requested.emit(image_id)
        )
        menu.addAction(move_down_action)

        menu.addSeparator()

        delete_action = QAction("🗑️ Esborrar Imatge", self)
        delete_action.triggered.connect(
            lambda: self.image_delete_requested.emit(image_id)
        )
        menu.addAction(delete_action)

        menu.exec(pos)
