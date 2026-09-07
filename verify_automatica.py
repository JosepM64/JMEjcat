#!/usr/bin/env python3
"""
Verificación Automatizada - JMEJCat
====================================
Proyecto: JMEJCat (Notas estructuradas)
Versión: 2.5

Ejecutar: python verify_automatica.py
"""

import os
import sys

PROJECT_NAME = "JMEJCat"
PROJECT_VERSION = "3.62"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = SCRIPT_DIR


class VerificationResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.results = []

    def add_pass(self, test_name, details=""):
        self.passed += 1
        self.results.append(("PASS", test_name, details))

    def add_fail(self, test_name, details=""):
        self.failed += 1
        self.results.append(("FAIL", test_name, details))

    def add_warning(self, test_name, details=""):
        self.warnings += 1
        self.results.append(("WARN", test_name, details))

    def print_summary(self):
        print("\n" + "=" * 60)
        print(f"RESUMEN DE VERIFICACION - {PROJECT_NAME} v{PROJECT_VERSION}")
        print("=" * 60)
        print(f"[OK] PASADOS:   {self.passed}")
        print(f"[X] FALLADOS:  {self.failed}")
        print(f"[!] AVISOS:    {self.warnings}")
        print("=" * 60)

        if self.failed > 0:
            print("\nFALLOS DETECTADOS:")
            for status, test, details in self.results:
                if status == "FAIL":
                    print(f"  [{status}] {test}")
                    if details:
                        print(f"         {details}")

        return self.failed == 0


def read_file(filepath):
    if not os.path.isabs(filepath):
        filepath = os.path.join(PROJECT_DIR, filepath)
    try:
        with open(filepath, encoding="utf-8", errors="ignore") as f:
            return f.read()
    except (FileNotFoundError, PermissionError, OSError):
        return ""


def verify_project_structure(result: VerificationResult):
    """Verifica estructura del proyecto"""
    print("\n[1/8] Estructura del Proyecto...")

    os.chdir(PROJECT_DIR)

    key_files = [
        "jmejcat.py",
        "ui_window.py",
        "ui_dialogs.py",
        "config.py",
        "database.py",
        "tramitacio_database.py",
        "tramitacio_window.py",
        "calculator.py",
        "pdf_exporter.py",
        "image_manager.py",
        "utils.py",
    ]

    for f in key_files:
        if os.path.exists(f):
            result.add_pass("Estructura", f)
        else:
            result.add_fail("Estructura", f"no encontrado: {f}")

    # Tests pytest (v3.60): només informatiu fins que superin 70% cobertura
    if os.path.isdir("tests"):
        result.add_pass("Estructura", "tests/ (pytest)")
    else:
        result.add_warning("Estructura", "tests/ no existeix (P0 Sprint 2)")


def verify_main_entry(result: VerificationResult):
    """Verifica punto de entrada"""
    print("[2/8] Punto de Entrada...")

    main_file = "jmejcat.py"
    if os.path.exists(main_file):
        content = read_file(main_file)

        checks = [
            ("def get_app_dir", "get_app_dir"),
            ("def setup_logging", "setup_logging"),
            ("def main", "main"),
            ("QApplication", "PySide6 QApplication"),
            ("sys.excepthook", "Manejador de excepciones"),
        ]

        for pattern, desc in checks:
            if pattern in content:
                result.add_pass("Main", desc)
            else:
                result.add_fail("Main", f"{desc} no encontrado")
    else:
        result.add_fail("Main", "jmejcat.py no encontrado")


def verify_ui_classes(result: VerificationResult):
    """Verifica clases UI"""
    print("[3/8] Clases UI...")

    # Classes repartides entre fitxers després de la refactorització a mixins
    class_checks = [
        ("ui_window.py", "class MainWindow", "MainWindow"),
        ("image_viewer.py", "class ImageViewer", "ImageViewer"),
        ("image_gallery.py", "class ImageGallery", "ImageGallery"),
    ]
    for fname, pattern, desc in class_checks:
        if os.path.exists(fname) and pattern in read_file(fname):
            result.add_pass("UI", desc)
        else:
            result.add_fail("UI", f"{desc} no encontrado")

    ui_file = "ui_window.py"
    if os.path.exists(ui_file):
        content = read_file(ui_file)

        # Verificar métodos importantes
        methods = [
            ("def new_note", "Nueva nota"),
            ("def save_note", "Guardar nota"),
            ("def load_note", "Cargar nota"),
            ("def delete_current_note", "Borrar nota"),
            ("def on_search", "Buscar"),
            ("def show_about", "Acerca de"),
            ("def format_text", "Formatear texto"),
            ("def open_calculator", "Calculadora"),
            ("def open_tramitacio", "Tramitación"),
        ]

        for pattern, desc in methods:
            if pattern in content:
                result.add_pass("UI", desc)
            else:
                result.add_warning("UI", f"{desc} no encontrado")
    else:
        result.add_fail("UI", "ui_window.py no encontrado")


def verify_database(result: VerificationResult):
    """Verifica base de datos"""
    print("[4/8] Base de Datos...")

    db_file = "database.py"
    if os.path.exists(db_file):
        content = read_file(db_file)

        if "class Database" in content:
            result.add_pass("DB", "Clase Database")

            db_methods = [
                ("def _get_connection", "get_connection"),
                ("def init_database", "init_database"),
                ("def create_note", "create_note"),
                ("def update_note", "update_note"),
                ("def delete_note", "delete_note"),
                ("def get_all_notes", "get_all_notes"),
            ]

            for pattern, desc in db_methods:
                if pattern in content:
                    result.add_pass("DB", desc)
                else:
                    result.add_warning("DB", f"{desc} no encontrado")
        else:
            result.add_fail("DB", "Clase Database no encontrada")
    else:
        result.add_fail("DB", "database.py no encontrado")


def verify_tramitacio(result: VerificationResult):
    """Verifica módulo de tramitación"""
    print("[5/8] Tramitación...")

    tramit_file = "tramitacio_window.py"
    if os.path.exists(tramit_file):
        content = read_file(tramit_file)

        if "class TramitacioWindow" in content:
            result.add_pass("Tramitacio", "TramitacioWindow")
        else:
            result.add_fail("Tramitacio", "TramitacioWindow no encontrado")

        if "class TramitacioEditDialog" in content:
            result.add_pass("Tramitacio", "TramitacioEditDialog")
        else:
            result.add_warning("Tramitacio", "TramitacioEditDialog no encontrado")

        methods = [
            ("def load_data", "Cargar datos"),
            ("def on_nou_clicked", "Nueva tramitación"),
            ("def on_editar_clicked", "Editar tramitación"),
            ("def on_eliminar_clicked", "Eliminar tramitación"),
        ]

        for pattern, desc in methods:
            if pattern in content:
                result.add_pass("Tramitacio", desc)
            else:
                result.add_warning("Tramitacio", f"{desc} no encontrado")
    else:
        result.add_fail("Tramitacio", "tramitacio_window.py no encontrado")


def verify_utilities(result: VerificationResult):
    """Verifica utilidades"""
    print("[6/8] Utilidades...")

    # Calculator
    calc_file = "calculator.py"
    if os.path.exists(calc_file):
        content = read_file(calc_file)
        if "class CalculatorDialog" in content:
            result.add_pass("Utils", "CalculatorDialog")
        else:
            result.add_warning("Utils", "CalculatorDialog no encontrado")

    # PDF Exporter
    pdf_file = "pdf_exporter.py"
    if os.path.exists(pdf_file):
        content = read_file(pdf_file)
        if "class BasePDFExporter" in content:
            result.add_pass("Utils", "BasePDFExporter")
        else:
            result.add_warning("Utils", "BasePDFExporter no encontrado")

    # Image Manager
    img_file = "image_manager.py"
    if os.path.exists(img_file):
        content = read_file(img_file)
        if "class ImageManager" in content:
            result.add_pass("Utils", "ImageManager")
        else:
            result.add_warning("Utils", "ImageManager no encontrado")

    # Config
    config_file = "config.py"
    if os.path.exists(config_file):
        content = read_file(config_file)
        if "MIN_PYTHON_VERSION" in content:
            result.add_pass("Utils", "Config con versión mínima Python")
        else:
            result.add_warning("Utils", "MIN_PYTHON_VERSION no encontrado")


def verify_dialogs(result: VerificationResult):
    """Verifica diàlegs extrets"""
    print("[7/8] Diàlegs...")

    dialogs_file = "ui_dialogs.py"
    if os.path.exists(dialogs_file):
        content = read_file(dialogs_file)

        classes = [
            ("class NoteLinkDialog", "NoteLinkDialog"),
            ("class BackupManagerDialog", "BackupManagerDialog"),
            ("class VerifyBackupsDialog", "VerifyBackupsDialog"),
        ]

        for pattern, desc in classes:
            if pattern in content:
                result.add_pass("Dialegs", desc)
            else:
                result.add_warning("Dialegs", f"{desc} no encontrado")
    else:
        result.add_fail("Dialegs", "ui_dialogs.py no encontrado")


def verify_pyside_imports(result: VerificationResult):
    """Verifica imports de PySide6"""
    print("[8/8] Imports PySide6...")

    key_files = ["jmejcat.py", "ui_window.py", "tramitacio_window.py"]
    all_content = ""
    for f in key_files:
        all_content += read_file(f) + "\n"

    pyside_imports = [
        ("QApplication", "QApplication"),
        ("QMainWindow", "QMainWindow"),
        ("QDialog", "QDialog"),
        ("QWidget", "QWidget"),
        ("QTextEdit", "QTextEdit"),
        ("QTableWidget", "QTableWidget"),
    ]

    for lib, name in pyside_imports:
        if lib in all_content:
            result.add_pass("PySide6", name)
        else:
            result.add_fail("PySide6", f"{name} no importado")


def verify_features(result: VerificationResult):
    """Verifica funcionalidades clave"""
    print("[9/8] Funcionalidades...")

    ui_content = read_file("ui_window.py")

    features = [
        ("autosave", "Autoguardado"),
        ("backup", "Backup manual"),
        ("export_current_note_pdf", "Exportar PDF nota actual"),
        ("export_all_notes_pdf", "Exportar todas las notas PDF"),
        ("load_note_images", "Cargar imágenes de nota"),
        ("add_image", "Añadir imagen"),
        ("ImageGallery", "Galería de imágenes"),
        ("show_stats", "Estadísticas"),
    ]

    for pattern, desc in features:
        if pattern in ui_content:
            result.add_pass("Features", desc)
        else:
            result.add_warning("Features", f"{desc} no encontrado")


def main():
    print("=" * 60)
    print(f"{PROJECT_NAME} - Verificacion Automatizada")
    print("=" * 60)
    print(f"Python: {sys.version}")
    print(f"Directorio proyecto: {PROJECT_DIR}")

    os.chdir(PROJECT_DIR)

    result = VerificationResult()

    verify_project_structure(result)
    verify_main_entry(result)
    verify_ui_classes(result)
    verify_database(result)
    verify_tramitacio(result)
    verify_utilities(result)
    verify_dialogs(result)
    verify_pyside_imports(result)
    verify_features(result)

    success = result.print_summary()

    if success:
        print("\n[OK] TODAS LAS VERIFICACIONES PASARON")
        print("El proyecto esta listo para continuar.")
        return 0
    else:
        print("\n[X] ALGUNAS VERIFICACIONES FALLARON")
        print("Revisa los fallos antes de continuar.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
