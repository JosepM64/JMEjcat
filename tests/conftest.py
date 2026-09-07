"""
Pytest configuration i fixtures compartides per a JMEJCat.

Proporciona:
- Aïllament del directori `data/` real de l'usuari (les proves usen un `tmp_path`).
- BD de notes i de tramitació ja inicialitzades.
- Una imatge PNG vàlida per als tests d'imatges.
- Fitxer de dades per als tests de càrrega de la base de dades.
"""

import os
import sqlite3
from pathlib import Path

import pytest
from PIL import Image


# Redirigim `get_data_path()` i company abans d'importar els mòduls que les usen.
# Així garantim que cap test escriu al `data/` real de l'usuari.
@pytest.fixture(autouse=True)
def isolate_data_dir(tmp_path, monkeypatch):
    """
    Reescriu les funcions `get_*_path()` de `utils.py` perquè apuntin a un
    directori temporal durant tota la sessió de test.

    S'aplica automàticament a TOTS els tests (autouse=True) — un test que
    necessiti el `data/` real pot fer `monkeypatch.undo()` o sobreescriure
    la fixture localment.
    """
    from utils import (
        get_data_path,
        get_images_path,
        get_original_images_path,
        get_thumbnails_path,
        get_backups_path,
    )

    # Crear subdirs dins tmp_path
    for fn, sub in (
        (get_data_path, ""),
        (get_images_path, "images"),
        (get_original_images_path, "images/original"),
        (get_thumbnails_path, "images/thumbs"),
        (get_backups_path, "backups"),
    ):
        target = tmp_path / sub
        target.mkdir(parents=True, exist_ok=True)
        monkeypatch.setattr(
            "utils." + fn.__name__, lambda _sub=target: _sub
        )

    return tmp_path


@pytest.fixture
def tmp_data_dir(tmp_path):
    """Directori `data/` temporal per a un test concret."""
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


@pytest.fixture
def notes_db(tmp_data_dir):
    """Instància de `Database` (notes) amb BD temporal."""
    from database import Database

    db = Database(tmp_data_dir / "jmejcat.db")
    yield db
    db.close()


@pytest.fixture
def tramit_db(tmp_data_dir):
    """Instància de `TramitacioDatabase` (tramitació) amb BD temporal."""
    from tramitacio_database import TramitacioDatabase

    db = TramitacioDatabase(tmp_data_dir / "tramitacio.db")
    yield db
    db.close()


@pytest.fixture
def sample_png(tmp_path) -> Path:
    """Imatge PNG vàlida (10x10 vermella) per a tests d'ImageManager."""
    img_path = tmp_path / "sample.png"
    Image.new("RGB", (10, 10), color=(255, 0, 0)).save(img_path)
    return img_path


@pytest.fixture
def image_manager(tmp_data_dir, sample_png):
    """`ImageManager` amb directoris temporals."""
    from image_manager import ImageManager

    mgr = ImageManager()
    # Processar la imatge sample per defecte (disponible com a info)
    info = mgr.process_image(sample_png)
    return mgr, info
