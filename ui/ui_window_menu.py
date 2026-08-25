"""Menu, toolbar and shortcut setup mixin for MainWindow."""

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QToolBar, QLabel
from PySide6.QtCore import QSize


class UiWindowMenuMixin:
    """Mixin: menu bar, toolbar, status bar, action definitions, keyboard shortcuts."""

    def setup_menu(self):
        """Configura la barra de menú."""
        menubar = self.menuBar()

        # Menú Archivo
        file_menu = menubar.addMenu("📁 Fitxer")

        new_action = QAction("📄 Nova Nota", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_note)
        file_menu.addAction(new_action)

        save_action = QAction("💾 Desar Nota", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_note)
        file_menu.addAction(save_action)

        delete_action = QAction("🗑️ Esborrar Nota", self)
        delete_action.setShortcut("Delete")
        delete_action.triggered.connect(self.delete_current_note)
        file_menu.addAction(delete_action)

        file_menu.addSeparator()

        calc_menu_action = QAction("🧮 Calculadora de despeses", self)
        calc_menu_action.triggered.connect(self.open_calculator)
        file_menu.addAction(calc_menu_action)

        tramitacio_action = QAction("📋 Tramitació", self)
        tramitacio_action.triggered.connect(self.open_tramitacio)
        file_menu.addAction(tramitacio_action)

        stats_action = QAction("📊 Estadístiques", self)
        stats_action.triggered.connect(self.show_stats)
        file_menu.addAction(stats_action)

        file_menu.addSeparator()

        # Menú d'exportació
        export_menu = file_menu.addMenu("📄 Exportar")

        export_current_pdf_action = QAction("📄 Exportar Nota Actual a PDF", self)
        export_current_pdf_action.triggered.connect(self.export_current_note_pdf)
        export_menu.addAction(export_current_pdf_action)

        export_all_pdf_action = QAction("📚 Exportar Totes les Notes a PDF", self)
        export_all_pdf_action.triggered.connect(self.export_all_notes_pdf)
        export_menu.addAction(export_all_pdf_action)

        export_menu.addSeparator()

        export_current_md_action = QAction("📝 Exportar Nota Actual a Markdown", self)
        export_current_md_action.triggered.connect(self.export_current_note_md)
        export_menu.addAction(export_current_md_action)

        export_all_md_action = QAction("📚 Exportar Totes les Notes a Markdown", self)
        export_all_md_action.triggered.connect(self.export_all_notes_md)
        export_menu.addAction(export_all_md_action)

        file_menu.addSeparator()

        # Menú de backups
        backup_menu = file_menu.addMenu("💾 Backups")

        create_backup_action = QAction("💾 Crear Backup", self)
        create_backup_action.triggered.connect(self.create_backup_manual)
        backup_menu.addAction(create_backup_action)

        restore_backup_action = QAction("🔄 Restaurar Backup", self)
        restore_backup_action.triggered.connect(self.show_backup_manager)
        backup_menu.addAction(restore_backup_action)

        verify_backup_action = QAction("✅ Verificar Backups", self)
        verify_backup_action.triggered.connect(self.verify_backups_ui)
        backup_menu.addAction(verify_backup_action)

        # Separador
        backup_menu.addSeparator()

        # Netejar backups antics
        cleanup_backup_action = QAction("🧹 Netejar Backups Antics", self)
        cleanup_backup_action.triggered.connect(self.cleanup_old_backups_ui)
        backup_menu.addAction(cleanup_backup_action)

        file_menu.addSeparator()

        exit_action = QAction("🚪 Sortir", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Menú Editar
        edit_menu = menubar.addMenu("✏️ Editar")

        paste_plain_action = QAction("📋 Enganxar text pla", self)
        paste_plain_action.setShortcut("Ctrl+Shift+V")
        paste_plain_action.triggered.connect(self.paste_as_plain_text)
        edit_menu.addAction(paste_plain_action)

        edit_menu.addSeparator()

        # Formato de texto
        format_menu = edit_menu.addMenu("🎨 Format")

        bold_action = QAction("B Negreta", self)
        bold_action.setShortcut("Ctrl+B")
        bold_action.triggered.connect(lambda: self.format_text("bold"))
        format_menu.addAction(bold_action)

        italic_action = QAction("I Cursiva", self)
        italic_action.setShortcut("Ctrl+I")
        italic_action.triggered.connect(lambda: self.format_text("italic"))
        format_menu.addAction(italic_action)

        underline_action = QAction("S Subratllat", self)
        underline_action.setShortcut("Ctrl+U")
        underline_action.triggered.connect(lambda: self.format_text("underline"))
        format_menu.addAction(underline_action)

        strike_action = QAction("T Tatxat", self)
        strike_action.setShortcut("Ctrl+T")
        strike_action.triggered.connect(lambda: self.format_text("strikeout"))
        format_menu.addAction(strike_action)

        color_action = QAction("🎨 Color de lletra", self)
        color_action.triggered.connect(self.change_text_color)
        format_menu.addAction(color_action)

        edit_menu.addSeparator()

        clear_action = QAction("🗑️ Netejar Format", self)
        clear_action.triggered.connect(self.clear_format)
        edit_menu.addAction(clear_action)

        # Menú Ver (Opcions)
        view_menu = menubar.addMenu("⚙️ Opcions")

        self.autosave_action = QAction("💾 Autoguardat automàtic", self, checkable=True)
        self.autosave_action.setChecked(True)
        self.autosave_action.triggered.connect(self.toggle_autosave)
        view_menu.addAction(self.autosave_action)

        # Menú Ajuda
        help_menu = menubar.addMenu("❓ Ajuda")

        about_action = QAction("ℹ️ Quant a JMEJCat", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        docs_action = QAction("📚 Documentació", self)
        docs_action.triggered.connect(self.open_docs)
        help_menu.addAction(docs_action)

        help_menu.addSeparator()

        # Submenú Manteniment BD Tramitació
        maintenance_menu = help_menu.addMenu("🔧 Manteniment BD Tramitació")

        rebuild_action = QAction("🔄 Rebuild Índexs", self)
        rebuild_action.triggered.connect(self.maintenance_rebuild_indexes)
        maintenance_menu.addAction(rebuild_action)

        stats_action_db = QAction("📊 Actualitzar Estadístiques", self)
        stats_action_db.triggered.connect(self.maintenance_update_stats)
        maintenance_menu.addAction(stats_action_db)

        purge_action = QAction("🧹 Purga Dades Antigues", self)
        purge_action.triggered.connect(self.maintenance_purge)
        maintenance_menu.addAction(purge_action)

        vacuum_action = QAction("📦 VACUUM (Optimitzar BD)", self)
        vacuum_action.triggered.connect(self.maintenance_vacuum)
        maintenance_menu.addAction(vacuum_action)

        maintenance_menu.addSeparator()

        info_action = QAction("ℹ️ Estadístiques BD", self)
        info_action.triggered.connect(self.maintenance_show_stats)
        maintenance_menu.addAction(info_action)

    def setup_toolbar(self):
        """Configura la barra d'eines."""
        toolbar = QToolBar("Eines principals")
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)

        # Botón nueva nota
        new_action = QAction("📄", self)
        new_action.setToolTip("Nova nota (Ctrl+N)")
        new_action.triggered.connect(self.new_note)
        toolbar.addAction(new_action)

        # Botón guardar
        save_action = QAction("💾", self)
        save_action.setToolTip("Desar nota (Ctrl+S)")
        save_action.triggered.connect(self.save_note)
        toolbar.addAction(save_action)

        # Botón esborrar
        delete_action = QAction("🗑️", self)
        delete_action.setToolTip("Esborrar nota (Supr)")
        delete_action.triggered.connect(self.delete_current_note)
        toolbar.addAction(delete_action)

        toolbar.addSeparator()

        # Botón buscar
        search_action = QAction("🔍", self)
        search_action.setShortcut("Ctrl+F")
        search_action.setToolTip("Cercar (Ctrl+F)")
        search_action.triggered.connect(self.focus_search)
        toolbar.addAction(search_action)

        toolbar.addSeparator()

        # Botón añadir imagen
        image_action = QAction("🖼️", self)
        image_action.setToolTip("Afegir imatge (Ctrl+I)")
        image_action.triggered.connect(self.add_image)
        toolbar.addAction(image_action)

        # Botón calculadora
        calc_action = QAction("🧮", self)
        calc_action.setToolTip("Calculadora de despeses")
        calc_action.triggered.connect(self.open_calculator)
        toolbar.addAction(calc_action)

        # Botón Tramitació
        tramit_action = QAction("📋", self)
        tramit_action.setToolTip("Tramitació")
        tramit_action.triggered.connect(self.open_tramitacio)
        toolbar.addAction(tramit_action)

        # Botó silenciar avisos
        self.btn_snooze_all = QAction("🔕", self)
        self.btn_snooze_all.setToolTip("Silenciar tots els avisos d'avui")
        self.btn_snooze_all.triggered.connect(self.snooze_all_today)
        toolbar.addAction(self.btn_snooze_all)

        # Botó silenciar fins reinici
        self.btn_snooze_session = QAction("🔇", self)
        self.btn_snooze_session.setToolTip(
            "Silenciar tots els avisos fins que reiniciïs l'app"
        )
        self.btn_snooze_session.triggered.connect(self.snooze_session_toggle)
        toolbar.addAction(self.btn_snooze_session)

        toolbar.addSeparator()

        # Botones de formato
        bold_action_toolbar = QAction("𝗕", self)
        bold_action_toolbar.setToolTip("Negreta (Ctrl+B)")
        bold_action_toolbar.triggered.connect(lambda: self.format_text("bold"))
        toolbar.addAction(bold_action_toolbar)

        italic_action_toolbar = QAction("𝐼", self)
        italic_action_toolbar.setToolTip("Cursiva (Ctrl+I)")
        italic_action_toolbar.triggered.connect(lambda: self.format_text("italic"))
        toolbar.addAction(italic_action_toolbar)

        underline_action_toolbar = QAction("𝖴", self)
        underline_action_toolbar.setToolTip("Subratllat (Ctrl+U)")
        underline_action_toolbar.triggered.connect(
            lambda: self.format_text("underline")
        )
        toolbar.addAction(underline_action_toolbar)

        strike_action_toolbar = QAction("S̶", self)
        strike_action_toolbar.setToolTip("Tatxat (Ctrl+T)")
        strike_action_toolbar.triggered.connect(lambda: self.format_text("strikeout"))
        toolbar.addAction(strike_action_toolbar)

        color_action_toolbar = QAction("🎨", self)
        color_action_toolbar.setToolTip("Color de lletra")
        color_action_toolbar.triggered.connect(self.change_text_color)
        toolbar.addAction(color_action_toolbar)

        list_action_toolbar = QAction("•", self)
        list_action_toolbar.setToolTip("Llista (Vinyetes)")
        list_action_toolbar.triggered.connect(lambda: self.format_text("list"))
        toolbar.addAction(list_action_toolbar)

        numbered_list_action_toolbar = QAction("🔢", self)
        numbered_list_action_toolbar.setToolTip("Llista numerada")
        numbered_list_action_toolbar.triggered.connect(
            lambda: self.format_text("numbered_list")
        )
        toolbar.addAction(numbered_list_action_toolbar)

        paste_plain_action_toolbar = QAction("📋T", self)
        paste_plain_action_toolbar.setToolTip("Enganxar text pla (Ctrl+Shift+V)")
        paste_plain_action_toolbar.triggered.connect(self.paste_as_plain_text)
        toolbar.addAction(paste_plain_action_toolbar)

        toolbar.addSeparator()

        # Indicador de estado
        self.save_indicator = QLabel("  Desat  ")
        self.save_indicator.setStyleSheet("""
            QLabel {
                background-color: #4CAF50;
                color: white;
                padding: 2px 8px;
                border-radius: 3px;
                font-size: 10px;
            }
        """)
        toolbar.addWidget(self.save_indicator)
        self.save_indicator.hide()

    def setup_shortcuts(self):
        """Configura les dreceres de teclat."""
        # Les dreceres principals ja es gestionen via QAction al menú i toolbar
        pass
