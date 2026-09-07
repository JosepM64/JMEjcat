"""
Smoke tests per a `config.py`.

Verifica que les constants crítiques existeixen i tenen valors raonables.
No carrega la BD ni la UI — només valors estàtics.
"""

import sys
from pathlib import Path

import pytest

import config


class TestAppMetadata:
    """Metadades de l'aplicació."""

    def test_app_name_is_jmejcat(self):
        assert config.APP_NAME == "JMEJCat"

    def test_app_version_is_string(self):
        # Versionat semver bàsic: "X.YZ" o "X.YZ.W"
        v = config.APP_VERSION
        assert isinstance(v, str)
        parts = v.split(".")
        assert len(parts) >= 2, f"Versió ha de tenir almenys 2 parts: {v}"
        for p in parts:
            assert p.isdigit(), f"Component de versió no numèric: {p}"

    def test_app_author_present(self):
        assert isinstance(config.APP_AUTHOR, str)
        assert len(config.APP_AUTHOR) > 0

    def test_app_license_is_lgpl(self):
        assert "LGPL" in config.APP_LICENSE

    def test_min_python_version_at_least_3_13(self):
        """v3.57+ requereix Python 3.13 — coherència amb jmejcat.py."""
        assert config.MIN_PYTHON_VERSION >= (3, 13)
        # El sistema real compleix?
        assert sys.version_info >= (3, 13)


class TestDatabaseConfig:
    """Constants de base de dades."""

    def test_db_filenames_present(self):
        assert config.DB_FILENAME.endswith(".db")
        assert config.DB_FILENAME_TRAMITACIO.endswith(".db")
        assert config.DB_FILENAME != config.DB_FILENAME_TRAMITACIO

    def test_db_version_is_positive_int(self):
        assert isinstance(config.DB_VERSION, int)
        assert config.DB_VERSION >= 1

    def test_backup_count_reasonable(self):
        assert 1 <= config.BACKUP_COUNT <= 50


class TestImageConfig:
    """Constants d'imatges."""

    def test_supported_extensions_includes_common(self):
        exts = config.SUPPORTED_IMAGE_EXTENSIONS
        for required in (".jpg", ".jpeg", ".png"):
            assert required in exts, f"Falta extensió {required}"

    def test_thumbnail_size_is_tuple_of_two_positive_ints(self):
        w, h = config.THUMBNAIL_SIZE
        assert isinstance(w, int) and isinstance(h, int)
        assert w > 0 and h > 0

    def test_thumbnail_quality_in_range(self):
        # JPEG quality: 1..95 raonable
        assert 1 <= config.THUMBNAIL_QUALITY <= 100

    def test_image_hash_length_positive(self):
        assert config.IMAGE_HASH_LENGTH > 0
        assert config.IMAGE_HASH_LENGTH <= 64  # SHA-256 hex


class TestUISearchConfig:
    """Constants d'UI i cerca."""

    def test_main_window_size_positive(self):
        w, h = config.MAIN_WINDOW_SIZE
        assert w > 0 and h > 0

    def test_min_window_size_smaller_than_main(self):
        mw, mh = config.MAIN_WINDOW_SIZE
        minw, minh = config.MIN_WINDOW_SIZE
        assert minw <= mw and minh <= mh

    def test_search_delay_positive(self):
        assert config.SEARCH_DELAY_MS > 0

    def test_search_fields_includes_title(self):
        # Decisió de disseny: la cerca va per title (veure §7 checkpoint)
        assert "title" in config.SEARCH_FIELDS

    def test_title_max_length_positive(self):
        assert config.TITLE_MAX_LENGTH > 0

    def test_examples_max_length_positive(self):
        assert config.EXAMPLES_MAX_LENGTH > 0


class TestPathHelpers:
    """Funcions que retornen paths (aïllades ja per la fixture)."""

    def test_get_user_config_path_returns_path(self, monkeypatch):
        # Forçar Linux-like per no dependre de Windows registry en CI
        monkeypatch.setattr(config.sys, "platform", "linux")
        p = config.get_user_config_path()
        assert isinstance(p, Path)
        # No crea el directori, només el retorna
        assert isinstance(p, Path)

    def test_get_default_export_path_returns_path(self):
        p = config.get_default_export_path()
        assert isinstance(p, Path)
        assert config.APP_NAME in p.name

    def test_get_app_title_includes_version(self):
        title = config.get_app_title()
        assert config.APP_NAME in title
        assert config.APP_VERSION in title
