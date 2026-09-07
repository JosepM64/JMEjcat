"""
Módulo de utilidades para JMEJCat
Funciones de path y helpers
"""

import logging
import sys
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_app_path() -> Path:
    """
    Obtiene la ruta base de la aplicación.

    Returns:
        Path: Ruta del ejecutable (empaquetado) o del script (desarrollo).
    """
    if getattr(sys, "frozen", False):
        # Ejecutable empaquetado con PyInstaller
        base_path = Path(sys.executable).parent
    else:
        # Desarrollo - directorio del script
        base_path = Path(__file__).parent

    logger.debug(f"Ruta de la aplicación: {base_path}")
    return base_path


@lru_cache(maxsize=1)
def get_data_path() -> Path:
    """
    Obtiene la ruta del directorio de datos.

    Returns:
        Path: Ruta del directorio data/.
    """
    data_path = get_app_path() / "data"
    logger.debug(f"Ruta de datos: {data_path}")
    return data_path


@lru_cache(maxsize=1)
def get_images_path() -> Path:
    """
    Obtiene la ruta del directorio de imágenes.

    Returns:
        Path: Ruta del directorio data/images/.
    """
    images_path = get_data_path() / "images"
    logger.debug(f"Ruta de imágenes: {images_path}")
    return images_path


@lru_cache(maxsize=1)
def get_original_images_path() -> Path:
    """
    Obtiene la ruta del directorio de imágenes originales.

    Returns:
        Path: Ruta del directorio data/images/original/.
    """
    original_path = get_images_path() / "original"
    logger.debug(f"Ruta de imágenes originales: {original_path}")
    return original_path


@lru_cache(maxsize=1)
def get_thumbnails_path() -> Path:
    """
    Obtiene la ruta del directorio de thumbnails.

    Returns:
        Path: Ruta del directorio data/images/thumbs/.
    """
    thumbs_path = get_images_path() / "thumbs"
    logger.debug(f"Ruta de thumbnails: {thumbs_path}")
    return thumbs_path


@lru_cache(maxsize=1)
def get_backups_path() -> Path:
    """
    Obtiene la ruta del directorio de backups.

    Returns:
        Path: Ruta del directorio data/backups/.
    """
    backups_path = get_data_path() / "backups"
    logger.debug(f"Ruta de backups: {backups_path}")
    return backups_path


def setup_data_directories() -> Path:
    """
    Crea todos los directorios necesarios para la aplicación.

    Returns:
        Path: Ruta del directorio de datos principal.

    Raises:
        OSError: Si no se pueden crear los directorios.
    """
    data_path = get_data_path()

    # Crear directorios principales
    directories = [
        data_path,
        get_images_path(),
        get_original_images_path(),
        get_thumbnails_path(),
        get_backups_path(),
    ]

    for directory in directories:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"Directorio creado/verificado: {directory}")
        except OSError as e:
            logger.error(f"Error creando directorio {directory}: {e}")
            raise

    # Verificar permisos de escritura
    test_file = data_path / ".write_test"
    try:
        test_file.write_text("test")
        test_file.unlink()
        logger.debug("Permisos de escritura verificados")
    except OSError as e:
        logger.error(f"Sin permisos de escritura en {data_path}: {e}")
        raise

    return data_path


def validate_date_ddmmyyyy(date_str: str) -> bool:
    """
    Valida que una data tingui el format dd/MM/yyyy i sigui una data real.

    Args:
        date_str: Data en format dd/MM/yyyy.

    Returns:
        bool: True si la data és vàlida, False altrament.
    """
    from datetime import datetime

    try:
        datetime.strptime(date_str, "%d/%m/%Y")
        return True
    except (ValueError, TypeError):
        return False


def format_file_size(bytes_size: int) -> str:
    """
    Formatea un tamaño de archivo en bytes a una representación legible.

    Args:
        bytes_size: Tamaño en bytes.

    Returns:
        str: Tamaño formateado (ej. "1.5 MB").
    """
    size = float(bytes_size)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024.0 or unit == "GB":
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return ""  # unreachable, però satisfà el tipus de retorn


def is_portable_mode() -> bool:
    """
    Verifica si la aplicación está en modo portable.

    Returns:
        bool: True si está en modo portable (ejecutable + data/), False en desarrollo.
    """
    return getattr(sys, "frozen", False)


def get_resource_path(relative_path: str) -> Path:
    """
    Obtiene la ruta absoluta a un recurso.

    Args:
        relative_path: Ruta relativa del recurso.

    Returns:
        Path: Ruta absoluta al recurso.
    """
    if is_portable_mode():
        # En modo portable, los recursos están en sys._MEIPASS
        base_path = Path(sys._MEIPASS)
    else:
        # En desarrollo, en el directorio de la aplicación
        base_path = get_app_path()

    return base_path / relative_path
