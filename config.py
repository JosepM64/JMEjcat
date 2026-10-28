"""
Configuración y constantes de JMEJCat
"""

import os
import sys
from pathlib import Path

# ============================================================================
# METADATOS DE LA APLICACIÓN
# ============================================================================

APP_NAME = "JMEJCat"
APP_VERSION = "4.6"
APP_AUTHOR = "Josep Maria Tapia Estaragues"
APP_WEBSITE = "https://www.posicionamientowebysem.com/"
APP_LICENSE = "LGPL v3"
APP_DESCRIPTION = "Gestión de apuntes y control de expedientes de un tramitador en un juzgado civil de Barcelona"

# ============================================================================
# CONFIGURACIÓN DEL SISTEMA
# ============================================================================

# Intervalo de autoguardado (en segundos, 0 para desactivar)
AUTOSAVE_INTERVAL = 30
# CONFIGURACIÓN DEL SISTEMA
# ============================================================================

# Versión mínima de Python requerida
MIN_PYTHON_VERSION = (3, 13, 0)

# Verificar versión de Python
if sys.version_info < MIN_PYTHON_VERSION:
    raise RuntimeError(
        f"JMEJCat requiere Python {'.'.join(map(str, MIN_PYTHON_VERSION))} o superior. "
        f"Versión actual: {sys.version}"
    )

# ============================================================================
# CONFIGURACIÓN DE BASE DE DATOS
# ============================================================================

# Nombre del archivo de base de datos
DB_FILENAME = "jmejcat.db"
DB_FILENAME_TRAMITACIO = "tramitacio.db"

# Versión del esquema de base de datos (incrementar en migraciones)
DB_VERSION = 2

# Número de backups a mantener
BACKUP_COUNT = 5

# ============================================================================
# CONFIGURACIÓN DE IMÁGENES
# ============================================================================

# Tamaño de thumbnail (ancho, alto) en píxeles
THUMBNAIL_SIZE = (256, 256)

# Calidad de JPEG para thumbnails (1-100)
THUMBNAIL_QUALITY = 85

# Longitud del hash para nombres de archivo de imágenes
IMAGE_HASH_LENGTH = 12

# Extensiones de imagen soportadas
SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"}

# ============================================================================
# CONFIGURACIÓN DE INTERFAZ DE USUARIO
# ============================================================================

# Límites de longitud para campos
TITLE_MAX_LENGTH = 100  # Caracteres máximos para título
EXAMPLES_MAX_LENGTH = 500  # Caracteres máximos para ejemplos

# Tamaños de ventana
MAIN_WINDOW_SIZE = (1200, 700)  # Ancho, Alto en píxeles
MIN_WINDOW_SIZE = (800, 500)  # Tamaño mínimo de ventana

# Layout
SPLITTER_SIZES = (300, 900)  # Proporciones del splitter principal
SOLUTION_STRETCH = 14  # Factor d'estirament de l'editor de solució
TITLE_TRUNCATE_LENGTH = 50  # Longitud màxima del títol abans de truncar
TITLE_TRUNCATE_SUFFIX = 3  # Caràcters a restar al truncar ("...")

# Imatges (galeria)
GALLERY_COLUMNS = 4  # Columnes a la quadrícula de miniatures
ZOOM_FACTOR = 1.2  # Factor de zoom al visualitzador d'imatges

# Tramitació
DATE_FORMAT = "dd/MM/yyyy"  # Format de data per Tramitació

# Calculadora
TAX_PERCENTAGE = 0.30  # Percentatge de despeses (30%)

# Colores (en formato hexadecimal o nombres Qt)
COLORS = {
    "primary": "#2196F3",  # Azul principal
    "success": "#4CAF50",  # Verde para éxito
    "warning": "#FF9800",  # Naranja para advertencias
    "danger": "#F44336",  # Rojo para errores
    "background": "#F5F5F5",  # Fondo gris claro
    "text": "#212121",  # Texto principal
    "text_secondary": "#757575",  # Texto secundario
}

# Fuentes
FONTS = {
    "default": "Segoe UI" if sys.platform == "win32" else "Arial",
    "monospace": "Consolas" if sys.platform == "win32" else "Monospace",
    "title_size": 12,
    "text_size": 10,
}

# ============================================================================
# CONFIGURACIÓN DE BÚSQUEDA
# ============================================================================

# Tiempo de espera antes de realizar búsqueda (en ms)
SEARCH_DELAY_MS = 300

# Campos en los que buscar (v4.0: títol + contingut)
SEARCH_FIELDS = ["title", "request", "solution"]

# ============================================================================
# CONFIGURACIÓN DE RENDIMIENTO
# ============================================================================

# Tamaño máximo de caché de imágenes en memoria (en número de imágenes)
IMAGE_CACHE_SIZE = 50

# ============================================================================
# CONFIGURACIÓN DE DESARROLLO
# ============================================================================

# Nivel de logging por defecto
LOG_LEVEL = "INFO"

# Activar/desactivar características experimentales
EXPERIMENTAL_FEATURES = {
    "advanced_search": False,
    "markdown_support": False,
    "cloud_sync": False,
}

# ============================================================================
# FUNCIONES DE CONFIGURACIÓN
# ============================================================================


def get_app_title() -> str:
    """Devuelve el título completo de la aplicación."""
    return f"{APP_NAME} v{APP_VERSION}"


def get_user_config_path() -> Path:
    """
    Devuelve la ruta para configuración de usuario.

    En Windows: %APPDATA%/JMEJCat
    En Linux/macOS: ~/.config/jmejcat
    """
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:  # Linux y otros Unix
        base = Path.home() / ".config"

    return base / APP_NAME.lower()


def get_default_export_path() -> Path:
    """Devuelve la ruta por defecto para exportaciones."""
    return Path.home() / "Desktop" / f"{APP_NAME}_Exports"
