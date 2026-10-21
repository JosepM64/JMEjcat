"""
Finestra principal de JMEJCat
Interfície d'usuari amb PySide6
"""

import logging

from PySide6.QtCore import QSettings, Qt, QTimer, QUrl
from PySide6.QtGui import (
    QDesktopServices,
    QFontMetrics,
    QKeySequence,
    QShortcut,
)
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from config import (
    APP_AUTHOR,
    APP_NAME,
    APP_VERSION,
    APP_WEBSITE,
    AUTOSAVE_INTERVAL,
    EXAMPLES_MAX_LENGTH,
    SOLUTION_STRETCH,
    SPLITTER_SIZES,
    TITLE_MAX_LENGTH,
)
from database import Database
from image_gallery import ImageGallery
from image_manager import ImageManager
from tramitacio_database import TramitacioDatabase
from ui.ui_window_backup import UiWindowBackupMixin
from ui.ui_window_editor import UiWindowEditorMixin
from ui.ui_window_export import UiWindowExportMixin
from ui.ui_window_formatting import UiWindowFormattingMixin
from ui.ui_window_images import UiWindowImagesMixin
from ui.ui_window_menu import UiWindowMenuMixin
from ui.ui_window_notes import UiWindowNotesMixin
from ui.ui_window_tramitacio import UiWindowTramitacioMixin

logger = logging.getLogger(__name__)


class MainWindow(
    UiWindowMenuMixin,
    UiWindowEditorMixin,
    UiWindowFormattingMixin,
    UiWindowNotesMixin,
    UiWindowImagesMixin,
    UiWindowExportMixin,
    UiWindowBackupMixin,
    UiWindowTramitacioMixin,
    QMainWindow,
):
    """Finestra principal de l'aplicació."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setGeometry(100, 100, 1200, 700)

        # Inicializar componentes
        self.db = Database()
        self.tramit_db = TramitacioDatabase()
        self.image_manager = ImageManager()
        self.current_note_id = None
        self.current_note_modified = False
        self._loading_note = (
            False  # Flag per evitar marcar com a modificat durant càrrega
        )
        self.progress_dialog = None
        self.pdf_exporter = None
        self.autosave_enabled = True
        self.expand_dialog = None  # Editor expandit de solució (único)
        self.format_painter_btn = None
        self.copied_format = [None]
        self.multi_apply = [False]

        # Timer per autoguardat
        self.autosave_timer = QTimer()
        if hasattr(self, "autosave_note"):
            self.autosave_timer.timeout.connect(self.autosave_note)
            self.autosave_timer.start(AUTOSAVE_INTERVAL * 1000)

        # Timer per avisos de Tramitació (funciona sempre, finestra oberta o no)
        self.triggered_reminders = set()
        self.reminder_timer = QTimer(self)
        self.reminder_timer.timeout.connect(self.check_tramit_reminders)
        self.reminder_timer.start(60000)  # cada minut
        self.snoozed_reminders = {}  # {tramit_id: datetime_when_to_show}
        self.snooze_all_active = False  # botó "silenciar avui"
        self.snooze_session_active = False  # botó "silenciar fins reinici"

        # 2.8: Backup automàtic periòdic cada 30 min només si hi ha canvis pendents
        self._periodic_backup_timer = QTimer(self)
        self._periodic_backup_timer.timeout.connect(self._periodic_backup)
        self._periodic_backup_timer.start(30 * 60 * 1000)  # 30 min

        # Configurar UI
        self.setup_ui()
        self.setup_menu()
        self.setup_toolbar()
        self.setup_shortcuts()

        # Zoom global de la UI (Ctrl + / Ctrl - / Ctrl 0), persistent entre sessions
        base_pt = QApplication.font().pointSize()
        self._base_font_pt = base_pt if base_pt and base_pt > 0 else 10
        try:
            saved_pt = int(
                QSettings("JMEJCat", "JMEJCat")
                .value("ui_font_pt", self._base_font_pt)
            )
        except (TypeError, ValueError):
            saved_pt = self._base_font_pt
        self._ui_font_pt = max(7, min(20, saved_pt))
        self._apply_ui_font()
        self.setup_zoom_shortcuts()

        # Cargar datos iniciales
        self.load_notes()

        # Mostrar estado
        self.statusBar().showMessage("Llest")

        # Afegir informació d'autor a l'esquerra de la barra d'estat
        author_label = QLabel(f" {APP_AUTHOR} | v{APP_VERSION} ")
        author_label.setStyleSheet("color: #666; font-size: 10px;")
        author_label.setCursor(Qt.PointingHandCursor)
        author_label.mousePressEvent = lambda e: self.open_website()
        self.statusBar().addPermanentWidget(author_label)

        logger.info("Finestra principal inicialitzada")

    def setup_ui(self):
        """Configura la interfície d'usuari."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # Splitter principal
        splitter = QSplitter(Qt.Horizontal)

        # --- Panel izquierdo: Navegación ---
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(5, 5, 5, 5)

        # Barra de búsqueda
        search_label = QLabel("Cercar notes:")
        search_label.setStyleSheet("font-weight: bold;")
        left_layout.addWidget(search_label)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Cerca per títol...")
        self.search_input.textChanged.connect(self.on_search)
        left_layout.addWidget(self.search_input)

        self.search_text_input = QLineEdit()
        self.search_text_input.setPlaceholderText("Cerca dins el text...")
        self.search_text_input.textChanged.connect(self.on_search_text)
        left_layout.addWidget(self.search_text_input)

        # Lista de notas
        notes_label = QLabel("Notes:")
        notes_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        left_layout.addWidget(notes_label)

        self.notes_list = QListWidget()
        self.notes_list.setAlternatingRowColors(True)
        self.notes_list.itemClicked.connect(self.on_note_selected)
        left_layout.addWidget(self.notes_list, 1)  # Factor de estiramiento

        # Contador
        self.notes_count_label = QLabel("0 notes")
        self.notes_count_label.setStyleSheet("color: #666; font-style: italic;")
        left_layout.addWidget(self.notes_count_label)

        # Botón nueva nota
        new_note_btn = QPushButton("➕ Nova Nota")
        new_note_btn.clicked.connect(self.new_note)
        new_note_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        left_layout.addWidget(new_note_btn)

        splitter.addWidget(left_panel)

        # --- Panel derecho: Editor ---
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(10, 10, 10, 10)

        # Título
        title_label = QLabel("Títol:")
        title_label.setStyleSheet("font-weight: bold;")
        right_layout.addWidget(title_label)

        self.title_input = QLineEdit()
        self.title_input.setMaxLength(TITLE_MAX_LENGTH)
        self.title_input.textChanged.connect(self.on_title_changed)
        self.title_input.textEdited.connect(self.on_title_edited)
        right_layout.addWidget(self.title_input)

        # Petición
        request_label = QLabel("Petició:")
        request_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        right_layout.addWidget(request_label)

        self.request_edit = QTextEdit()
        self.request_edit.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.request_edit.customContextMenuRequested.connect(
            lambda pos: self.show_editor_context_menu(self.request_edit, pos)
        )
        self.request_edit.textChanged.connect(self.on_content_changed)
        self.request_edit.installEventFilter(self)
        right_layout.addWidget(self.request_edit, 1)  # Una mica més petit

        # Atajo Shift+F3 para cambiar entre modos de mayúsculas/minúsculas
        self.request_case_shortcut = QShortcut(
            QKeySequence("Shift+F3"), self.request_edit
        )
        self.request_case_shortcut.setContext(Qt.ShortcutContext.WidgetShortcut)
        self.request_case_shortcut.activated.connect(self.cycle_selected_text_case)

        # Solución
        solution_label = QLabel("Solució:")
        solution_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        right_layout.addWidget(solution_label)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(solution_label)
        btn_layout.addStretch()

        self.expand_solution_btn = QPushButton("⬜")
        self.expand_solution_btn.setFixedSize(30, 25)
        self.expand_solution_btn.setToolTip("Ampliar editor")
        self.expand_solution_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 3px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.expand_solution_btn.clicked.connect(self.expand_solution_editor)
        btn_layout.addWidget(self.expand_solution_btn)

        right_layout.addLayout(btn_layout)

        self.solution_edit = QTextEdit()
        self.solution_edit.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.solution_edit.customContextMenuRequested.connect(
            lambda pos: self.show_editor_context_menu(self.solution_edit, pos)
        )
        # Habilitar tabuladors com a espais
        self.solution_edit.setTabStopDistance(
            QFontMetrics(self.solution_edit.font()).horizontalAdvance(" ") * 4
        )
        self.solution_edit.textChanged.connect(self.on_content_changed)
        self.solution_edit.installEventFilter(self)
        right_layout.addWidget(
            self.solution_edit, SOLUTION_STRETCH
        )  # Molt més espai per solució (abans 12)

        # Atajo Shift+F3 para cambiar entre modos de mayúsculas/minúsculas
        self.solution_case_shortcut = QShortcut(
            QKeySequence("Shift+F3"), self.solution_edit
        )
        self.solution_case_shortcut.setContext(Qt.ShortcutContext.WidgetShortcut)
        self.solution_case_shortcut.activated.connect(self.cycle_selected_text_case)

        # Atajo Ctrl+Shift+E para expandir el editor
        self.expand_solution_shortcut = QShortcut(
            QKeySequence("Ctrl+Shift+E"), self.solution_edit
        )
        self.expand_solution_shortcut.setContext(Qt.ShortcutContext.WidgetShortcut)
        self.expand_solution_shortcut.activated.connect(self.expand_solution_editor)

        # Ejemplos
        examples_label = QLabel("Exemples:")
        examples_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        right_layout.addWidget(examples_label)

        self.examples_edit = QLineEdit()
        self.examples_edit.setMaxLength(EXAMPLES_MAX_LENGTH)
        self.examples_edit.textChanged.connect(self.on_content_changed)
        right_layout.addWidget(self.examples_edit)

        # Galería de imágenes
        self.image_gallery = ImageGallery()
        self.image_gallery.image_clicked.connect(self.open_image_viewer)
        self.image_gallery.image_delete_requested.connect(self.delete_image)
        self.image_gallery.image_move_up_requested.connect(self.move_image_up)
        self.image_gallery.image_move_down_requested.connect(self.move_image_down)
        right_layout.addWidget(self.image_gallery)

        # Botón para añadir imagen
        self.add_image_btn = QPushButton("📷 Afegir Imatge")
        self.add_image_btn.clicked.connect(self.add_image)
        self.add_image_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
        """)
        right_layout.addWidget(self.add_image_btn)

        splitter.addWidget(right_panel)

        # Configurar proporciones del splitter
        splitter.setSizes(list(SPLITTER_SIZES))

        main_layout.addWidget(splitter)

    def show_stats(self):
        """Mostra estadístiques de l'aplicació."""
        stats = self.db.get_stats()

        # Obtener uso de disco de imágenes
        original_size, thumbs_size = self.image_manager.get_disk_usage()

        message = f"""
        📊 Estadísticas de JMEJCat

        📝 Notas: {stats["note_count"]}
        🖼️ Imágenes: {stats["image_count"]}

        💾 Tamaño base de datos: {stats["db_size"] / 1024:.1f} KB
        💿 Imágenes originales: {original_size / 1024:.1f} KB
        📱 Thumbnails: {thumbs_size / 1024:.1f} KB

        📅 Actividad reciente:
        """

        for activity in stats["recent_activity"][:5]:  # Últimos 5 días
            message += f"  {activity['date']}: {activity['count']} notas\n"

        QMessageBox.information(self, "Estadístiques", message.strip())

    def show_about(self):
        """Mostra el diàleg 'Quant a'."""
        import sqlite3
        import sys

        import PIL
        from PySide6.QtCore import qVersion

        pyside_version = qVersion()
        pillow_version = PIL.__version__
        sqlite_version = sqlite3.sqlite_version
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

        about_text = f"""
        <h2>{APP_NAME}</h2>
        <p><b>Versió:</b> {APP_VERSION}</p>
        <p><b>Autor:</b> {APP_AUTHOR}</p>
        <p><b>Web:</b> <a href="{APP_WEBSITE}">{APP_WEBSITE}</a></p>
        <p><b>Secció:</b> Secció Civil del TI de Barcelona. Plaça núm. 46</p>

        <p>Gestió d'apunts i control d'expedients per a un tramitador de jutjat
        civil. Portable i offline: tots els dades es guarden a la carpeta
        <b>data/</b> del programa.</p>

        <h3>Característiques:</h3>
        <ul>
            <li>Notes amb títol, petició, solució i exemples</li>
            <li>Format de text enriquit (negreta, cursiva, subratllat)</li>
            <li>Tramitació d'expedients: número, any, colors, recordatoris i alarmes</li>
            <li>Gestió d'imatges amb miniatures i visor amb zoom</li>
            <li>Cerca instantània per títol i per text (dues caixes)</li>
            <li>Exportació a PDF, Markdown i CSV</li>
            <li>Calculadora de despeses i diferència de pagaments</li>
            <li>Sistema de backups automàtics</li>
        </ul>

        <h3>Dreceres útils:</h3>
        <ul>
            <li><b>Ctrl+N</b> nova nota · <b>Ctrl+S</b> desar · <b>Ctrl+F</b> cercar</li>
            <li><b>Ctrl+B / I / U / T</b> negreta, cursiva, subratllat, tatxat</li>
            <li><b>Ctrl+I</b> inserir imatge</li>
            <li><b>Ctrl + / Ctrl - / Ctrl 0</b> mida de la interfície (portàtils)</li>
            <li>Visor d'imatges: roda+Ctrl zoom · doble clic ajustar · <b>F11</b> pantalla completa</li>
            <li><b>Ctrl+Q</b> sortir</li>
        </ul>

        <h3>Tecnologies:</h3>
        <ul>
            <li>Python {python_version}</li>
            <li>PySide6 {pyside_version}</li>
            <li>SQLite {sqlite_version}</li>
            <li>Pillow {pillow_version}</li>
        </ul>

        <p>Llicència: LGPL v3</p>

        <h3>Novetats v4.3:</h3>
        <ul>
            <li>El diàleg d'edició de tràmit ja no bloqueja la resta de finestres</li>
        </ul>

        <h3>Novetats v4.2:</h3>
        <ul>
            <li>L'editor ampliat de Solució desa sempre a la seva nota d'origen</li>
        </ul>

        <h3>Novetats v4.1:</h3>
        <ul>
            <li>Dues caixes de cerca: per títol i dins el text (mana l'última tocada)</li>
        </ul>

        <h3>Novetats v4.0:</h3>
        <ul>
            <li>Cerca unificada: títol + petició + solució, amb paginació</li>
            <li>Backups tipats i verificats (restore segur, neteja per tipus)</li>
            <li>Tests d'integració: restore, export MD, cerca</li>
        </ul>
        """

        QMessageBox.about(self, f"Quant a {APP_NAME}", about_text)

    def open_docs(self):
        """Obre la documentació."""
        QMessageBox.information(
            self,
            "Documentació",
            "La documentació està inclosa als fitxers del projecte.\n"
            "Consulta els fitxers README.md i TECHNICAL_MANIFEST.md",
        )

    # --- Funcions de Manteniment BD Tramitació ---

    def _get_tramit_db(self):
        """Obté la instància de TramitacioDatabase."""
        if hasattr(self, "tramit_db") and self.tramit_db:
            return self.tramit_db
        from tramitacio_database import TramitacioDatabase
        return TramitacioDatabase()

    def maintenance_rebuild_indexes(self):
        """Reconstrueix els índexs de la BD de Tramitació."""
        reply = QMessageBox.question(
            self,
            "Rebuild Índexs",
            "Vols reconstruir els índexs de la BD de Tramitació?\n\n"
            "Això pot trigar una estona amb molts registres.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                db = self._get_tramit_db()
                result = db.rebuild_indexes()
                QMessageBox.information(self, "Rebuild completat", result)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error reconstruint índexs:\n{e}")

    def maintenance_update_stats(self):
        """Actualitza les estadístiques de la BD de Tramitació."""
        try:
            db = self._get_tramit_db()
            result = db.update_statistics()
            QMessageBox.information(self, "Estadístiques", result)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error actualitzant estadístiques:\n{e}")

    def maintenance_purge(self):
        """Elimina registres antics de la BD de Tramitació."""
        from PySide6.QtWidgets import QInputDialog
        days, ok = QInputDialog.getInt(
            self,
            "Purga de dades",
            "Eliminar registres amb més de N dies:",
            365, 30, 3650
        )
        if not ok:
            return
        reply = QMessageBox.question(
            self,
            "Confirmar purga",
            f"Vols eliminar els registres actualitzats fa més de {days} dies?\n\n"
            "Aquesta acció és irreversible.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                db = self._get_tramit_db()
                deleted = db.purge_old_records(days)
                QMessageBox.information(
                    self, "Purga completada",
                    f"S'han eliminat {deleted} registres."
                )
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error en la purga:\n{e}")

    def maintenance_vacuum(self):
        """Optimitza l'espai de la BD de Tramitació."""
        reply = QMessageBox.question(
            self,
            "VACUUM",
            "Vols optimitzar la BD de Tramitació?\n\n"
            "Això redueix l'espai utilitzat però pot trigar una estona.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                db = self._get_tramit_db()
                result = db.vacuum()
                QMessageBox.information(self, "VACUUM completat", result)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error executant VACUUM:\n{e}")

    def maintenance_show_stats(self):
        """Mostra estadístiques de la BD de Tramitació."""
        try:
            db = self._get_tramit_db()
            stats = db.get_database_stats()
            message = f"""
📊 Estadístiques BD Tramitació

📝 Total registres: {stats['total_records']}
📋 Duplicats: {stats['duplicates']}
💾 Mida fitxer: {stats['file_size_mb']} MB

🎨 Per color:
"""
            for color, count in stats['by_color'].items():
                message += f"  • {color}: {count}\n"
            message += "\n📅 Per any:\n"
            for year, count in stats['by_year'].items():
                message += f"  • {year}: {count}\n"
            QMessageBox.information(self, "Estadístiques BD", message.strip())
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error obtenint estadístiques:\n{e}")

    def _periodic_backup(self):
        """Backup automàtic cada 30 min només si hi ha modificacions pendents (2.8)."""
        if not getattr(self, "current_note_modified", False):
            return
        try:
            from backup_manager import BackupManager

            # Guardar primer la nota si està modificada
            if hasattr(self, "save_note"):
                try:
                    self.save_note()
                except Exception as e:
                    logger.warning(f"Error en desar abans del backup periòdic: {e}")
            ok = BackupManager.backup_database()
            if ok:
                logger.info("Backup periòdic executat (30 min, hi havia canvis)")
                # Neteja antics silenciosa
                try:
                    BackupManager.cleanup_old_backups()
                except Exception:
                    pass
            else:
                logger.warning("Backup periòdic fallit")
        except Exception as e:
            logger.warning(f"Error en backup periòdic: {e}")

    def open_website(self):
        """Obre la web de l'autor."""
        QDesktopServices.openUrl(QUrl(APP_WEBSITE))

    # --- Zoom global de la UI ---

    def setup_zoom_shortcuts(self):
        """Dreceres de zoom: Ctrl++ / Ctrl+= augmenta, Ctrl+- redueix, Ctrl+0 restaura.
        Context d'aplicació: funcionen també dins l'editor expandit de Solució
        i la finestra de Tramitació, no només a la finestra principal."""
        for seq, fn in (
            ("Ctrl++", self.zoom_ui_in),
            ("Ctrl+=", self.zoom_ui_in),
            ("Ctrl+-", self.zoom_ui_out),
            ("Ctrl+0", self.zoom_ui_reset),
        ):
            shortcut = QShortcut(QKeySequence(seq), self)
            shortcut.setContext(Qt.ApplicationShortcut)
            shortcut.activated.connect(fn)

    def _apply_ui_font(self):
        """Aplica la mida de lletra global i la desa a QSettings."""
        font = QApplication.font()
        font.setPointSize(self._ui_font_pt)
        QApplication.setFont(font)
        # Els QTextEdit guarden la font dins del document (defaultFont) i no
        # segueixen la font de l'app un cop creats: cal actualitzar-los a mà.
        for w in QApplication.allWidgets():
            if isinstance(w, QTextEdit):
                w.setFont(font)
                w.document().setDefaultFont(font)
        QSettings("JMEJCat", "JMEJCat").setValue("ui_font_pt", self._ui_font_pt)

    def zoom_ui_in(self):
        """Augmenta la mida de lletra de tota l'aplicació."""
        if self._ui_font_pt < 20:
            self._ui_font_pt += 1
            self._apply_ui_font()
            self.statusBar().showMessage(
                f"Mida de lletra: {self._ui_font_pt} pt (Ctrl+0 per restaurar)"
            )

    def zoom_ui_out(self):
        """Redueix la mida de lletra de tota l'aplicació."""
        if self._ui_font_pt > 7:
            self._ui_font_pt -= 1
            self._apply_ui_font()
            self.statusBar().showMessage(
                f"Mida de lletra: {self._ui_font_pt} pt (Ctrl+0 per restaurar)"
            )

    def zoom_ui_reset(self):
        """Restaura la mida de lletra per defecte."""
        self._ui_font_pt = self._base_font_pt
        self._apply_ui_font()
        self.statusBar().showMessage("Mida de lletra restaurada")

    def closeEvent(self, event):
        """Evento al cerrar la ventana."""
        # Comprovar editor expandit abans de res
        if not self._close_expanded_if_open():
            event.ignore()
            return

        # Preguntar si guardar canvis
        if self.current_note_modified:
            msgBox = QMessageBox(self)
            msgBox.setWindowTitle("Canvis sense desar")
            msgBox.setText("Vols desar els canvis abans de sortir?")
            msgBox.setStandardButtons(
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            msgBox.setButtonText(QMessageBox.Yes, "Sí")
            msgBox.setButtonText(QMessageBox.No, "No")
            msgBox.setButtonText(QMessageBox.Cancel, "Cancel·lar")
            reply = msgBox.exec()

            if reply == QMessageBox.Yes:
                self.save_note()
            elif reply == QMessageBox.Cancel:
                event.ignore()
                return

        # Realizar backup + neteja automàtica (manté BACKUP_COUNT per tipus)
        from backup_manager import BackupManager

        try:
            BackupManager.backup_database()
            logger.info("Backup realizado al cerrar")
            try:
                deleted, _ = BackupManager.cleanup_old_backups()
                if deleted:
                    logger.info(f"Cleanup backups: {deleted} antics eliminats")
            except Exception as ce:
                logger.warning(f"Error netejant backups antics: {ce}")
        except Exception as e:
            logger.warning(f"Error realizando backup al cerrar: {e}")

        logger.info("Aplicació tancada")
        # Tancar connexions BD
        if hasattr(self, "db"):
            self.db.close()
        if hasattr(self, "tramit_db"):
            self.tramit_db.close()
        event.accept()
