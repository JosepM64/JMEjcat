"""
Módulo de gestión de imágenes para JMEJCat
Genera hashes únicos, thumbnails y maneja archivos de imagen
"""

import hashlib
import shutil
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple
from dataclasses import dataclass

from config import IMAGE_HASH_LENGTH, THUMBNAIL_SIZE, THUMBNAIL_QUALITY
from utils import get_original_images_path, get_thumbnails_path

logger = logging.getLogger(__name__)

# Intentar importar Pillow (opcional)
try:
    from PIL import Image

    HAS_PILLOW = True
    logger.info("Pillow disponible para procesamiento de imágenes")
except ImportError:
    HAS_PILLOW = False
    logger.warning("Pillow no instalado. Las miniaturas no se generarán.")


@dataclass
class ImageInfo:
    """Información de una imagen procesada."""

    filename: str
    thumb_filename: str
    width: int
    height: int
    file_size: int
    hash: str


class ImageManager:
    """Gestiona todas las operaciones con imágenes."""

    def __init__(self):
        """Inicializa el gestor de imágenes."""
        self.original_dir = get_original_images_path()
        self.thumbs_dir = get_thumbnails_path()

        # Asegurar que los directorios existen
        self.original_dir.mkdir(parents=True, exist_ok=True)
        self.thumbs_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Directorio de imágenes: {self.original_dir}")
        logger.info(f"Directorio de thumbnails: {self.thumbs_dir}")

    @staticmethod
    def _generate_file_hash(source_path: Path, length: int = IMAGE_HASH_LENGTH) -> str:
        """Genera un hash único para el archivo."""
        # Leer contenido del archivo
        content = source_path.read_bytes()

        # Añadir timestamp para garantizar unicidad
        timestamp = str(datetime.now().timestamp()).encode()

        # Generar hash SHA256
        hash_obj = hashlib.sha256(content + timestamp)
        return hash_obj.hexdigest()[:length]

    def _generate_thumbnail(self, source_path: Path, thumb_path: Path):
        """Genera una miniatura de la imagen."""
        if not HAS_PILLOW:
            # Fallback: copiar imagen original
            shutil.copy2(source_path, thumb_path)
            logger.warning(f"Pillow no disponible, copiando original: {source_path}")
            return

        try:
            with Image.open(source_path) as img:
                # Convertir a RGB si es necesario
                if img.mode in ("RGBA", "LA", "P"):
                    # Crear fondo blanco para transparencias
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    if img.mode == "P":
                        img = img.convert("RGBA")
                    background.paste(
                        img, mask=img.split()[-1] if img.mode == "RGBA" else None
                    )
                    img = background
                elif img.mode != "RGB":
                    img = img.convert("RGB")

                # Generar thumbnail
                img.thumbnail(THUMBNAIL_SIZE)

                # Guardar con calidad optimizada
                img.save(thumb_path, "JPEG", quality=THUMBNAIL_QUALITY, optimize=True)

                logger.debug(f"Thumbnail generado: {thumb_path}")

        except Exception as e:
            logger.error(f"Error generando thumbnail: {e}")
            # Fallback a copiar original
            shutil.copy2(source_path, thumb_path)

    def process_image(self, source_path: Path) -> Optional[ImageInfo]:
        """
        Procesa una imagen: genera hash, copia original, crea thumbnail.

        Returns:
            ImageInfo con información de la imagen procesada, o None si hay error.
        """
        if not source_path.exists():
            logger.error(f"Archivo no encontrado: {source_path}")
            return None

        # Validar extensión de archivo
        valid_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"}
        if source_path.suffix.lower() not in valid_extensions:
            logger.error(f"Extensión no soportada: {source_path.suffix}")
            return None

        try:
            # Generar hash único
            file_hash = self._generate_file_hash(source_path)

            # Crear nombres de archivo
            ext = source_path.suffix.lower()
            filename = f"{file_hash}{ext}"
            thumb_filename = f"{file_hash}_256.jpg"

            # Rutas destino
            target_path = self.original_dir / filename
            thumb_path = self.thumbs_dir / thumb_filename

            # Copiar imagen original
            shutil.copy2(source_path, target_path)
            logger.info(f"Imagen copiada a: {target_path}")

            # Generar thumbnail
            self._generate_thumbnail(source_path, thumb_path)

            # Obtener información de la imagen
            width, height = 0, 0
            if HAS_PILLOW:
                with Image.open(target_path) as img:
                    width, height = img.size

            file_size = target_path.stat().st_size

            return ImageInfo(
                filename=filename,
                thumb_filename=thumb_filename,
                width=width,
                height=height,
                file_size=file_size,
                hash=file_hash,
            )

        except Exception as e:
            logger.error(f"Error procesando imagen {source_path}: {e}")

            # Limpiar archivos si hubo error
            if "target_path" in locals() and target_path.exists():
                target_path.unlink()
            if "thumb_path" in locals() and thumb_path.exists():
                thumb_path.unlink()

            return None

    def get_image_path(self, filename: str, thumbnail: bool = False) -> Path:
        """Obtiene la ruta completa de una imagen."""
        if thumbnail:
            return self.thumbs_dir / filename
        else:
            return self.original_dir / filename

    def delete_image_files(self, filename: str, thumb_filename: str):
        """Elimina los archivos de imagen y thumbnail."""
        original_file = self.original_dir / filename
        thumb_file = self.thumbs_dir / thumb_filename

        try:
            if original_file.exists():
                original_file.unlink()
                logger.info(f"Imagen original eliminada: {original_file}")

            if thumb_file.exists():
                thumb_file.unlink()
                logger.info(f"Thumbnail eliminado: {thumb_file}")

        except Exception as e:
            logger.error(f"Error eliminando archivos de imagen: {e}")

    def get_disk_usage(self) -> Tuple[int, int]:
        """Obtiene el uso de disco por las imágenes."""
        original_size = sum(
            f.stat().st_size for f in self.original_dir.glob("*") if f.is_file()
        )
        thumbs_size = sum(
            f.stat().st_size for f in self.thumbs_dir.glob("*") if f.is_file()
        )
        return original_size, thumbs_size
