#!/usr/bin/env python3
"""
JMEJCat - Aplicación de notas estructuradas
Punto de entrada principal
Versió: 3.20
"""

import sys
import logging
import ctypes
import os
import traceback
from datetime import datetime
from pathlib import Path


# Manejador global de excepciones para capturar fallos tempranos
def get_app_dir():
    """Obtiene el directorio de la aplicación (portable friendly)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent


def global_exception_handler(exc_type, exc_value, exc_traceback):
    """Captura cualquier excepción no manejada y la escribe a un archivo de emergencia."""
    try:
        app_dir = get_app_dir()
        emergency_log = app_dir / "jmejcat_crash.log"
        with open(emergency_log, "a", encoding="utf-8") as f:
            f.write(f"=== CRASH {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
            f.write(f"Type: {exc_type.__name__}\n")
            f.write(f"Message: {exc_value}\n")
            f.write("Traceback:\n")
            traceback.print_tb(exc_traceback, file=f)
            f.write("\n\n")
        print(f"ERROR CRÍTICO: {exc_value}")
        print(f"Detalles guardados en: {emergency_log}")
    except Exception:
        pass  # No podemos hacer nada más
    # Llama al manejador por defecto
    sys.__excepthook__(exc_type, exc_value, exc_traceback)


sys.excepthook = global_exception_handler


# Configurar logging optimizado para producción
def setup_logging():
    """Configura logging optimizado para producción.
    Solo WARNING y ERROR en modo empaquetado para reducir tiempo de inicio."""
    app_dir = get_app_dir()

    if getattr(sys, "frozen", False):
        log_dir = app_dir / "logs"
    else:
        log_dir = Path.home() / ".jmejcat_logs"

    log_dir.mkdir(exist_ok=True)

    log_file = log_dir / f"jmejcat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    # Handler para archivo - WARNING en producción, DEBUG en desarrollo
    if getattr(sys, "frozen", False):
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.WARNING)
    else:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)

    # Handler para consola (solo si no estamos empaquetados)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Formato simplificado
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Configurar logger raíz
    root_logger = logging.getLogger()
    if getattr(sys, "frozen", False):
        root_logger.setLevel(logging.WARNING)
    else:
        root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)

    # Solo añadir consola si no estamos empaquetados
    if not getattr(sys, "frozen", False):
        root_logger.addHandler(console_handler)

    return log_file


# Iniciar logging inmediatamente
try:
    log_file = setup_logging()
    logger = logging.getLogger(__name__)
    if not getattr(sys, "frozen", False):
        logger.info("=" * 50)
        logger.info(f"INICIANDO JMEJCat - {datetime.now()}")
        logger.info(f"Python: {sys.version}")
        logger.info(f"Platform: {sys.platform}")
        logger.info(f"Executable: {sys.executable}")
        logger.info(f"Frozen: {getattr(sys, 'frozen', False)}")
        logger.info(f"Log file: {log_file}")
        logger.info("=" * 50)
except Exception as e:
    print(f"ERROR configurando logging: {e}")
    traceback.print_exc()

logger = logging.getLogger(__name__)

# Comprovar instància única
# Un lock antic (crash) no ha de bloquejar l'arrencada: només bloqueja si el
# PID del lock encara és un procés JMEJCat viu.
def _is_jmejcat_running(pid: int) -> bool:
    """Comprova si el PID pertany a un procés JMEJCat viu (Windows)."""
    try:
        kernel32 = ctypes.windll.kernel32
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        handle = kernel32.OpenProcess(
            PROCESS_QUERY_LIMITED_INFORMATION, False, int(pid)
        )
        if not handle:
            return False
        try:
            buf = ctypes.create_unicode_buffer(512)
            size = ctypes.c_uint(512)
            if kernel32.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size)):
                return "jmejcat" in Path(buf.value).name.lower()
            return True  # no hem pogut saber el nom; assumim que és viu
        finally:
            kernel32.CloseHandle(handle)
    except Exception:
        return True  # davant el dubte, no arrisquem dues instàncies


lock_file = Path.home() / ".jmejcat.lock"
try:
    if lock_file.exists():
        old_pid = lock_file.read_text().strip()
        if old_pid.isdigit() and _is_jmejcat_running(int(old_pid)):
            print(f"JMEJCat ya está ejecutando (PID: {old_pid})!")
            sys.exit(0)
        # Lock obsolet: el procés ja no existeix (crash) o el PID es reutilitzà
        lock_file.unlink(missing_ok=True)
        logger.info(f"Lock obsolet eliminat (PID anterior: {old_pid})")
except SystemExit:
    raise
except Exception:
    pass  # No bloquegem l'arrencada per un error de lock

# Crear lock file
try:
    lock_file.write_text(str(os.getpid()))
except Exception:
    pass  # No es crítico

# Identificador de aplicación para Windows (optimizado)
if sys.platform == "win32":
    try:
        myappid = "jmej.jmejcat.notes.v16"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass  # No es crítico

# Agregar ruta actual al path para imports (optimizado)
sys.path.insert(0, str(Path(__file__).parent))


# Importar módulos con lazy loading (solo cuando sea necesario)
def import_modules():
    """Importa módulos solo cuando sea necesario para reducir tiempo de inicio."""
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QIcon
    from ui_window import MainWindow
    from utils import setup_data_directories
    from backup_manager import BackupManager
    from config import APP_NAME, APP_VERSION

    return (
        QApplication,
        Qt,
        QIcon,
        MainWindow,
        setup_data_directories,
        BackupManager.backup_database,
        APP_NAME,
        APP_VERSION,
    )


def main():
    """Función principal de la aplicación."""
    global log_file  # Para acceder al archivo de log definido globalmente

    # Importar módulos solo cuando sea necesario (lazy loading)
    try:
        (
            QApplication,
            Qt,
            QIcon,
            MainWindow,
            setup_data_directories,
            backup_database,
            APP_NAME,
            APP_VERSION,
        ) = import_modules()
    except ImportError as e:
        print(f"ERROR: No se pudieron importar módulos: {e}")
        traceback.print_exc()
        sys.exit(1)

    logger.info(f"Iniciando {APP_NAME} v{APP_VERSION}")

    # Configurar directorios de datos (sin verificaciones redundantes)
    try:
        setup_data_directories()
    except Exception as e:
        print(f"Error: No se pudieron crear los directorios de datos: {e}")
        sys.exit(1)

    # Backup al inicio desactivat per optimitzar temps d'inici
    # El backup es fa només al tancar l'aplicació

    # Configurar entorno Qt para modo portable (optimizado)
    if getattr(sys, "frozen", False):
        base_path = Path(sys.executable).parent
        internal_path = base_path / "_internal"

        # Verificar existencia de _internal
        if not internal_path.exists():
            print("ERROR: El ejecutable está incompleto. Falta la carpeta _internal.")
            sys.exit(1)

        # Configurar plugin path para Qt
        plugin_path = internal_path / "PySide6" / "plugins"
        if plugin_path.exists():
            os.environ["QT_PLUGIN_PATH"] = str(plugin_path)

    # Crear aplicación Qt (optimizado)
    try:
        app = QApplication(sys.argv)
        app.setApplicationName(APP_NAME)
        app.setApplicationVersion(APP_VERSION)
    except Exception as e:
        print(f"ERROR: No se pudo inicializar la interfaz gráfica: {e}")
        traceback.print_exc()
        sys.exit(1)

    # Cargar icono (optimizado)
    assets_dir = Path(__file__).parent / "assets"
    icon_path = assets_dir / "icon.ico"
    if not icon_path.exists():
        icon_path = assets_dir / "JMEJCAT.ico"

    if icon_path.exists():
        try:
            app.setWindowIcon(QIcon(str(icon_path)))
        except Exception:
            pass  # No es crítico

    # Crear y mostrar ventana principal (optimizado)
    try:
        window = MainWindow()
        if icon_path.exists():
            window.setWindowIcon(QIcon(str(icon_path)))
        window.show()
    except Exception as e:
        print(f"Error crítico: {e}")
        traceback.print_exc()
        sys.exit(1)

    # Ejecutar aplicación con manejo de limpieza
    try:
        exit_code = app.exec()
        return exit_code
    finally:
        # Eliminar lock file (siempre se ejecuta, incluso con excepciones)
        try:
            if lock_file.exists():
                lock_file.unlink()
        except Exception:
            pass  # No es crítico


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nAplicación interrumpida por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"Error crítico no manejado: {e}")
        traceback.print_exc()
        sys.exit(1)
