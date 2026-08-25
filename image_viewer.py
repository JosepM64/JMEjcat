"""
Visualitzador d'imatges per JMEJCat
Diàleg per visualitzar imatges a mida completa amb navegació
"""

import logging
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QMessageBox,
)
from PySide6.QtGui import QPixmap, QPainter
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem

logger = logging.getLogger(__name__)


class ImageViewer(QDialog):
    """Diàleg per visualitzar imatges a mida completa amb navegació."""

    def __init__(
        self, image_path: Path, all_images: list = None, current_index: int = 0
    ):
        super().__init__()
        self.setWindowTitle("Visualitzador d'Imatge - JMEJCat")
        self.setMinimumSize(800, 600)

        # Guardar lista de imágenes para navegación
        self.all_images = all_images if all_images else [image_path]
        self.current_index = current_index
        self.zoom_level = 1.0

        # Crear widget de gráficos
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setRenderHint(QPainter.SmoothPixmapTransform)
        self.view.setDragMode(QGraphicsView.ScrollHandDrag)

        # Instalar event filter para Ctrl+wheel zoom
        self.view.viewport().installEventFilter(self)

        # Cargar imagen
        self.pixmap = QPixmap(str(image_path))
        if self.pixmap.isNull():
            QMessageBox.warning(self, "Error", "No s'ha pogut carregar la imatge.")
            self.close()
            return

        self.scene.addItem(QGraphicsPixmapItem(self.pixmap))

        # Configurar layout
        layout = QVBoxLayout()
        layout.addWidget(self.view)

        # Barra de herramientas inferior
        toolbar = QHBoxLayout()

        # Botones de navegación (siempre visibles)
        self.prev_btn = QPushButton("◀")
        self.prev_btn.clicked.connect(self.show_previous)
        self.prev_btn.setFixedSize(30, 30)
        self.prev_btn.setToolTip("Imatge anterior")
        self.prev_btn.setEnabled(len(self.all_images) > 1)

        self.next_btn = QPushButton("▶")
        self.next_btn.clicked.connect(self.show_next)
        self.next_btn.setFixedSize(30, 30)
        self.next_btn.setToolTip("Imatge següent")
        self.next_btn.setEnabled(len(self.all_images) > 1)

        # Indicador de posición
        self.index_label = QLabel(f"{self.current_index + 1}/{len(self.all_images)}")
        self.index_label.setStyleSheet("padding: 0 10px; font-weight: bold;")

        toolbar.addWidget(self.prev_btn)
        toolbar.addWidget(self.next_btn)
        toolbar.addWidget(self.index_label)
        toolbar.addSpacing(10)

        zoom_in_btn = QPushButton("+")
        zoom_in_btn.clicked.connect(self.zoom_in)
        zoom_in_btn.setFixedSize(30, 30)

        zoom_out_btn = QPushButton("-")
        zoom_out_btn.clicked.connect(self.zoom_out)
        zoom_out_btn.setFixedSize(30, 30)

        reset_btn = QPushButton("⟲")
        reset_btn.clicked.connect(self.reset_zoom)
        reset_btn.setFixedSize(30, 30)
        reset_btn.setToolTip("Restaurar zoom")

        fit_btn = QPushButton("⊞")
        fit_btn.clicked.connect(self.fit_to_screen)
        fit_btn.setFixedSize(30, 30)
        fit_btn.setToolTip("Ajustar a pantalla")

        fullscreen_btn = QPushButton("⛶")
        fullscreen_btn.clicked.connect(self.toggle_fullscreen)
        fullscreen_btn.setFixedSize(30, 30)
        fullscreen_btn.setToolTip("Pantalla completa (F11)")

        close_btn = QPushButton("Tancar")
        close_btn.clicked.connect(self.close)

        toolbar.addWidget(zoom_in_btn)
        toolbar.addWidget(zoom_out_btn)
        toolbar.addWidget(reset_btn)
        toolbar.addWidget(fit_btn)
        toolbar.addWidget(fullscreen_btn)
        toolbar.addStretch()
        toolbar.addWidget(close_btn)

        layout.addLayout(toolbar)
        self.setLayout(layout)

        self.fit_to_screen()

        # Doble clic per ajustar a pantalla
        self.view.setMouseTracking(True)

    def show_previous(self):
        """Mostra la imatge anterior."""
        if self.current_index > 0:
            self.current_index -= 1
            self.load_current_image()

    def show_next(self):
        """Mostra la imatge següent."""
        if self.current_index < len(self.all_images) - 1:
            self.current_index += 1
            self.load_current_image()

    def load_current_image(self):
        """Carrega la imatge actual."""
        image_path = self.all_images[self.current_index]

        # Actualitzar pixmap
        self.scene.clear()
        self.pixmap = QPixmap(str(image_path))
        if not self.pixmap.isNull():
            self.scene.addItem(QGraphicsPixmapItem(self.pixmap))

        # Actualitzar indicador
        if hasattr(self, "index_label"):
            self.index_label.setText(f"{self.current_index + 1}/{len(self.all_images)}")

        # Actualitzar títol
        self.setWindowTitle(
            f"Visualitzador d'Imatge - {image_path.name} ({self.current_index + 1}/{len(self.all_images)})"
        )

        # Actualitzar estat dels botons de navegació
        if hasattr(self, "prev_btn"):
            self.prev_btn.setEnabled(self.current_index > 0)
        if hasattr(self, "next_btn"):
            self.next_btn.setEnabled(self.current_index < len(self.all_images) - 1)

        # Mantenir el darrer zoom (ajustat a pantalla)
        self.fit_to_screen()

    def zoom_in(self):
        """Aumenta el zoom."""
        self.zoom_level *= 1.2
        self.view.resetTransform()
        self.view.scale(self.zoom_level, self.zoom_level)

    def zoom_out(self):
        """Disminuye el zoom."""
        self.zoom_level /= 1.2
        self.view.resetTransform()
        self.view.scale(self.zoom_level, self.zoom_level)

    def reset_zoom(self):
        """Restaura el zoom original."""
        self.zoom_level = 1.0
        self.view.resetTransform()
        self.view.scale(self.zoom_level, self.zoom_level)

    def fit_to_screen(self):
        """Ajusta la imatge a la pantalla."""
        if self.pixmap.isNull():
            return

        # Obtenir mides de la vista i la imatge
        view_size = self.view.viewport().size()
        pixmap_size = self.pixmap.size()

        if pixmap_size.isEmpty():
            return

        # Calcular factor d'escala per ajustar
        scale_x = view_size.width() / pixmap_size.width()
        scale_y = view_size.height() / pixmap_size.height()

        # Usar el factor mes petit per mantenir proporcions
        scale_factor = min(scale_x, scale_y) * 0.95

        self.zoom_level = scale_factor
        self.view.resetTransform()
        self.view.scale(self.zoom_level, self.zoom_level)

    def mouseDoubleClickEvent(self, event):
        """Doble clic per ajustar a pantalla."""
        self.fit_to_screen()

    def toggle_fullscreen(self):
        """Canvia entre mode pantalla completa i normal."""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def keyPressEvent(self, event):
        """Gestiona les tecles dret."""
        if event.key() == Qt.Key.Key_F11:
            self.toggle_fullscreen()
        elif event.key() == Qt.Key.Key_Escape and self.isFullScreen():
            self.showNormal()
        else:
            super().keyPressEvent(event)

    def eventFilter(self, obj, event):
        """Captura eventos de wheel para zoom con Ctrl+wheel."""
        if event.type() == event.Type.Wheel:
            modifiers = event.modifiers()
            if modifiers == Qt.KeyboardModifier.ControlModifier:
                if event.angleDelta().y() > 0:
                    self.zoom_in()
                else:
                    self.zoom_out()
                return True
        return super().eventFilter(obj, event)
