"""Image management mixin for MainWindow."""

import logging
from pathlib import Path

from PySide6.QtWidgets import QFileDialog, QMessageBox

from image_viewer import ImageViewer

logger = logging.getLogger(__name__)


class UiWindowImagesMixin:
    """Mixin: Image management (add, remove, view, reorder), image gallery integration."""

    def load_note_images(self, note_id: int):
        """Carrega les imatges d'una nota."""
        self.image_gallery.clear()

        images = self.db.get_note_images(note_id)

        for img in images:
            # Obtener rutas de archivos
            img_path = self.image_manager.get_image_path(img["filename"])
            thumb_path = self.image_manager.get_image_path(
                img["thumb_filename"], thumbnail=True
            )

            # Añadir miniatura a la galería
            self.image_gallery.add_thumbnail(img["id"], img_path, thumb_path)

        logger.info(f"{len(images)} imatges carregades per nota {note_id}")

    def add_image(self):
        """Afegeix una imatge a la nota actual."""
        if self.current_note_id is None:
            QMessageBox.warning(
                self, "Avís", "Has de desar la nota abans d'afegir imatges."
            )
            return

        # Obrir diàleg de selecció de fitxers
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar imatge",
            "",
            "Imatges (*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.webp);;Tots els fitxers (*.*)",
        )

        if not file_path:
            return

        source_path = Path(file_path)

        # Processar imatge
        image_info = self.image_manager.process_image(source_path)

        if image_info is None:
            QMessageBox.warning(
                self,
                "Error",
                "No s'ha pogut processar la imatge. Assegura't que és un fitxer d'imatge vàlid.",
            )
            return

        # Desar a la base de dades
        try:
            image_id = self.db.add_image(
                self.current_note_id, image_info.filename, image_info.thumb_filename
            )

            # Actualitzar galeria
            self.load_note_images(self.current_note_id)

            self.statusBar().showMessage(f"Imatge afegida: {source_path.name}")
            logger.info(f"Imatge {image_id} afegida a nota {self.current_note_id}")

        except Exception as e:
            logger.error(f"Error afegint imatge: {e}")
            QMessageBox.warning(
                self, "Error", f"No s'ha pogut afegir la imatge:\n{str(e)}"
            )

    def delete_image(self, image_id: int):
        """Esborra una imatge."""
        msgBox = QMessageBox(self)
        msgBox.setWindowTitle("Confirmar esborrat")
        msgBox.setText("Estàs segur que vols esborrar aquesta imatge?")
        msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msgBox.setDefaultButton(QMessageBox.No)
        msgBox.setButtonText(QMessageBox.Yes, "Sí")
        msgBox.setButtonText(QMessageBox.No, "No")
        reply = msgBox.exec()

        if reply == QMessageBox.Yes:
            try:
                # Obtenir informació de la imatge abans d'esborrar-la
                # Com que no tenim get_image per ID directament, la busquem a la llista de la nota actual
                images = self.db.get_note_images(self.current_note_id)
                img_to_delete = next(
                    (img for img in images if img["id"] == image_id), None
                )

                if img_to_delete:
                    # Esborrar de la base de dades
                    success = self.db.delete_image(image_id)

                    if success:
                        # Esborrar fitxers del disc
                        self.image_manager.delete_image_files(
                            img_to_delete["filename"], img_to_delete["thumb_filename"]
                        )

                        # Actualitzar galeria
                        self.load_note_images(self.current_note_id)
                        self.statusBar().showMessage("Imatge esborrada")
                    else:
                        QMessageBox.warning(
                            self,
                            "Error",
                            "No s'ha pogut esborrar la imatge de la base de dades.",
                        )

            except Exception as e:
                logger.error(f"Error esborrant imatge: {e}")
                QMessageBox.critical(
                    self, "Error", f"Error en esborrar la imatge:\n{str(e)}"
                )

    def move_image_up(self, image_id: int):
        """Mou una imatge una posició amunt."""
        try:
            success = self.db.move_image_up(image_id, self.current_note_id)
            if success:
                self.load_note_images(self.current_note_id)
                self.statusBar().showMessage("Imatge moguda amunt")
            else:
                self.statusBar().showMessage("La imatge ja és la primera")
        except Exception as e:
            logger.error(f"Error movent imatge: {e}")

    def move_image_down(self, image_id: int):
        """Mou una imatge una posició avall."""
        try:
            success = self.db.move_image_down(image_id, self.current_note_id)
            if success:
                self.load_note_images(self.current_note_id)
                self.statusBar().showMessage("Imatge moguda avall")
            else:
                self.statusBar().showMessage("La imatge ja és l'última")
        except Exception as e:
            logger.error(f"Error movent imatge: {e}")

    def open_image_viewer(self, image_path: Path):
        """Obre el visualitzador d'imatges amb navegació."""
        if not image_path.exists():
            QMessageBox.warning(
                self, "Error", "La imatge no existeix al sistema de fitxers."
            )
            return

        # Obtenir totes les imatges de la nota actual
        all_images = []
        current_index = 0

        # Obtenir imatges de la nota actual
        if self.current_note_id is not None:
            images = self.db.get_note_images(self.current_note_id)
            original_dir = self.image_manager.original_dir

            for i, img in enumerate(images):
                img_path = original_dir / img["filename"]
                all_images.append(img_path)
                # Trobar quin és l'índex de la imatge clicada
                if str(img_path.resolve()) == str(image_path.resolve()):
                    current_index = i

        # Si no hem trobat imatges, usar només la imatge actual
        if not all_images:
            all_images = [image_path]
            current_index = 0

        viewer = ImageViewer(image_path, all_images, current_index)
        viewer.exec()
