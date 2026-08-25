"""Backup creation, restore, listing, and cleanup mixin for MainWindow."""

from PySide6.QtWidgets import QMessageBox

from ui_dialogs import BackupManagerDialog, VerifyBackupsDialog


class UiWindowBackupMixin:
    """Mixin: Backup creation, restore, listing, cleanup."""

    def create_backup_manual(self):
        """Crea un backup manualment de notes i imatges."""
        from backup_manager import BackupManager

        try:
            # Backup de notes
            success_notes = BackupManager.backup_database("notes")

            # Backup de imatges
            success_images = BackupManager.backup_database("images")

            if success_notes or success_images:
                msg = "Backup creat correctament:\n"
                if success_notes:
                    msg += "- Notes (bases de dades)\n"
                if success_images:
                    msg += "- Imatges\n"
                QMessageBox.information(self, "Backup Creat", msg)
                self.statusBar().showMessage("Backup creat")
            else:
                QMessageBox.warning(self, "Error", "No s'ha pogut crear cap backup.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error creant backup:\n{str(e)}")

    def show_backup_manager(self):
        """Mostra el gestor de backups."""
        dialog = BackupManagerDialog(self)
        dialog.exec()

    def verify_backups_ui(self):
        """Diàleg per verificar backups en una carpeta."""
        dialog = VerifyBackupsDialog(self)
        dialog.exec()

    def cleanup_old_backups_ui(self):
        """Elimina backups antics, mantenint només els més recents."""
        from backup_manager import BackupManager

        # Confirmar amb l'usuari
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Eliminar Backups Antics")
        msg_box.setText(
            "¿Eliminar backups antics, mantenint només els 5 més recents de cada tipus (Notes, Tramitació i Imatges)?\n\n"
            "Aquesta acció eliminarà permanentment els backups més antics."
        )
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.button(QMessageBox.Yes).setText("Sí")
        msg_box.button(QMessageBox.No).setText("No")
        msg_box.setDefaultButton(QMessageBox.No)
        reply = msg_box.exec()

        if reply == QMessageBox.Yes:
            try:
                deleted_count, deleted_files = BackupManager.cleanup_old_backups()

                if deleted_count > 0:
                    msg = f"S'han eliminat {deleted_count} backups antics:\n"
                    # Mostrar només primers 10 noms per no saturar
                    for filename in deleted_files[:10]:
                        msg += f"• {filename}\n"
                    if len(deleted_files) > 10:
                        msg += f"... i {len(deleted_files) - 10} més.\n"

                    QMessageBox.information(self, "Backups Eliminats", msg)
                else:
                    QMessageBox.information(
                        self,
                        "Backups Eliminats",
                        "No s'han trobat backups antics per eliminar.\n"
                        "Ja es mantenen només els 5 més recents de cada tipus (Notes, Tramitació i Imatges).",
                    )
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Error eliminant backups antics:\n{str(e)}"
                )
