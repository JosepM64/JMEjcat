"""Tramitacio integration, reminder system, and snooze mixin for MainWindow."""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class UiWindowTramitacioMixin:
    """Mixin: Tramitacio integration, reminder system, snooze."""

    # Atribut creat dinàmicament a open_tramitacio (import lazy de la classe)
    tramitacio_window: Any

    def open_tramitacio(self, tramit_id: int | None = None):
        """Obre la finestra de Tramitació. Si tramit_id, obre directament aquell tràmit."""
        if (
            hasattr(self, "tramitacio_window")
            and self.tramitacio_window is not None
            and hasattr(self.tramitacio_window, "isVisible")
            and self.tramitacio_window.isVisible()
        ):
            # Ja està oberta, portar-la al davant
            self.tramitacio_window.raise_()
            self.tramitacio_window.activateWindow()
            if tramit_id:
                self.tramitacio_window.open_tramit_by_id(tramit_id)
            return

        from tramitacio_window import TramitacioWindow

        self.tramitacio_window = TramitacioWindow(self)
        self.tramitacio_window.show()
        if tramit_id:
            self.tramitacio_window.open_tramit_by_id(tramit_id)

    def check_tramit_reminders(self):
        """Verifica recordatoris de Tramitació (executat cada minut)."""
        from datetime import datetime

        now = datetime.now()

        if self.snooze_all_active or self.snooze_session_active:
            return

        try:
            tramits = self.tramit_db.get_all_tramits(None)
            for tramit in tramits:
                tramit_id = tramit["id"]
                reminder_at_str = tramit.get("reminder_at")
                if not reminder_at_str:
                    continue

                if tramit_id in self.triggered_reminders:
                    continue

                snooze_until = self.snoozed_reminders.get(tramit_id)
                if snooze_until and now < snooze_until:
                    continue

                try:
                    # fromisoformat accepta "2026-08-25 14:30:00", "2026-08-25T14:30", etc.
                    reminder_dt = datetime.fromisoformat(reminder_at_str)
                except ValueError:
                    logger.warning(f"Format de data no vàlid: {reminder_at_str}")
                    continue

                if now >= reminder_dt:
                    self._show_reminder_dialog(tramit, now)
        except Exception as e:
            logger.error(f"Error en check_tramit_reminders: {e}")

    def _show_reminder_dialog(self, tramit, now):
        """Mostra diàleg d'avís amb opcions d'ajornament."""
        from datetime import datetime, timedelta

        from PySide6.QtWidgets import (
            QDialog,
            QHBoxLayout,
            QLabel,
            QPushButton,
            QVBoxLayout,
        )

        tramit_id = tramit["id"]
        reminder_str = (
            tramit.get("reminder_at") or "sense data"
            if isinstance(tramit.get("reminder_at"), str)
            else "sense data"
        )
        dt_display = reminder_str
        try:
            dt_display = datetime.strptime(reminder_str, "%Y-%m-%d %H:%M:%S").strftime(
                "%d/%m/%Y %H:%M"
            )
        except ValueError:
            pass

        dialog = QDialog(self)
        dialog.setWindowTitle("Avís de Tramitació")
        dialog.setMinimumWidth(380)
        layout = QVBoxLayout(dialog)

        info_text = (
            f"<b>Tràmit {tramit['numero']}/{tramit['any']}</b><br>"
            f"<i>Data: {tramit.get('data', 'N/A')}</i><br>"
            f"Info: {tramit.get('info') or '(sense info)'}<br>"
            f"<hr>Avis establert: {dt_display}"
        )
        info_label = QLabel(info_text)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_1h = QPushButton("⏩ +1 hora")
        btn_1d = QPushButton("📅 +1 dia")
        if self.snooze_session_active:
            btn_session = QPushButton("🔊 Reactivar avisos")
        else:
            btn_session = QPushButton("🔇 Fins reinici")
        btn_all = QPushButton("🔇 TOTS")
        btn_all.setToolTip("Silenciar TOTS els avisos fins que reiniciïs l'aplicació")
        btn_edit = QPushButton("✏️")
        btn_edit.setToolTip("Editar aquest tramit")
        btn_edit.setMaximumWidth(32)
        btn_close = QPushButton("✓ Tancar")

        btn_layout.addWidget(btn_1h)
        btn_layout.addWidget(btn_1d)
        btn_layout.addWidget(btn_session)
        btn_layout.addWidget(btn_all)
        btn_layout.addWidget(btn_edit)
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)

        def do_snooze_1h():
            try:
                new_dt = datetime.now() + timedelta(hours=1)
                self.tramit_db.update_tramit(
                    tramit_id,
                    numero=tramit["numero"],
                    any=tramit["any"],
                    data=tramit["data"],
                    info=tramit["info"],
                    color=tramit.get("color", ""),
                    reminder_at=new_dt.strftime("%Y-%m-%d %H:%M:%S"),
                )
                self.snoozed_reminders[tramit_id] = new_dt
                self.triggered_reminders.discard(tramit_id)
            except Exception as exc:
                logger.exception(f"Error ajornant 1h: {exc}")
            finally:
                dialog.accept()

        def do_snooze_1d():
            try:
                new_dt = datetime.now() + timedelta(days=1)
                self.tramit_db.update_tramit(
                    tramit_id,
                    numero=tramit["numero"],
                    any=tramit["any"],
                    data=tramit["data"],
                    info=tramit["info"],
                    color=tramit.get("color", ""),
                    reminder_at=new_dt.strftime("%Y-%m-%d %H:%M:%S"),
                )
                self.snoozed_reminders[tramit_id] = new_dt
                self.triggered_reminders.discard(tramit_id)
            except Exception as exc:
                logger.exception(f"Error ajornant 1d: {exc}")
            finally:
                dialog.accept()

        def do_snooze_session():
            try:
                if self.snooze_session_active:
                    self.snooze_session_active = False
                    self.snoozed_reminders.clear()
                    self.triggered_reminders.clear()
                    self.statusBar().showMessage("Avisos reactivats", 3000)
                else:
                    from datetime import datetime as dt_mod
                    from datetime import timedelta as td_mod

                    far_future = dt_mod.now() + td_mod(days=365 * 10)
                    tramits = self.tramit_db.get_all_tramits(None)
                    for t in tramits:
                        tid = t["id"]
                        self.snoozed_reminders[tid] = far_future
                        self.triggered_reminders.discard(tid)
                    self.snooze_session_active = True
                    self.statusBar().showMessage(
                        "Avisos silenciats fins que reiniciis l'app", 3000
                    )
                if hasattr(self, "btn_snooze_session"):
                    self.btn_snooze_session.setText(
                        "Reactivar avisos"
                        if self.snooze_session_active
                        else "Fins reinici"
                    )
            except Exception as exc:
                logger.exception(f"Error en snooze sessio: {exc}")
            finally:
                dialog.accept()

        def do_close():
            self.triggered_reminders.add(tramit_id)
            dialog.accept()

        def do_edit():
            dialog.accept()
            self.open_tramitacio(tramit_id)

        btn_1h.clicked.connect(do_snooze_1h)
        btn_1d.clicked.connect(do_snooze_1d)
        btn_session.clicked.connect(do_snooze_session)
        btn_edit.clicked.connect(do_edit)
        btn_all.clicked.connect(do_snooze_session)
        btn_close.clicked.connect(do_close)

        dialog.exec()

    def snooze_all_today(self):
        """Silencia tots els avisos d'avui. Botó toggle."""
        from datetime import datetime, time, timedelta

        if self.snooze_all_active:
            self.snooze_all_active = False
            self.snoozed_reminders.clear()
            self.statusBar().showMessage("Avisos restaurades", 3000)
            if hasattr(self, "btn_snooze_all"):
                self.btn_snooze_all.setText("🔕 Silenciar avui")
            return

        now = datetime.now()
        end_of_day = datetime.combine(now.date(), time(23, 59, 59))
        keep_dt = end_of_day + timedelta(seconds=1)

        tramits = self.tramit_db.get_all_tramits(None)
        for tramit in tramits:
            reminder_at_str = tramit.get("reminder_at")
            if not reminder_at_str:
                continue
            try:
                reminder_dt = datetime.strptime(reminder_at_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                continue
            if reminder_dt.date() == now.date():
                tid = tramit["id"]
                self.snoozed_reminders[tid] = keep_dt
                self.triggered_reminders.discard(tid)

        self.snooze_all_active = True
        self.statusBar().showMessage("Avisos d'avui silenciats fins a les 00:00", 3000)
        if hasattr(self, "btn_snooze_all"):
            self.btn_snooze_all.setText("🔊 Restaurar avisos")

    def snooze_session_toggle(self):
        """Silencia/reactiva tots els avisos fins que es reiniciï l'app."""
        if self.snooze_session_active:
            self.snooze_session_active = False
            self.snoozed_reminders.clear()
            self.triggered_reminders.clear()
            self.statusBar().showMessage("Avisos reactivats", 3000)
            if hasattr(self, "btn_snooze_session"):
                self.btn_snooze_session.setText("🔇")
                self.btn_snooze_session.setToolTip(
                    "Silenciar tots els avisos fins que reiniciïs l'app"
                )
            return

        from datetime import datetime, timedelta

        far_future = datetime.now() + timedelta(days=365 * 10)
        tramits = self.tramit_db.get_all_tramits(None)
        for t in tramits:
            tid = t["id"]
            self.snoozed_reminders[tid] = far_future
            self.triggered_reminders.discard(tid)
        self.snooze_session_active = True
        self.statusBar().showMessage("Avisos silenciats fins que reiniciïs l'app", 3000)
        if hasattr(self, "btn_snooze_session"):
            self.btn_snooze_session.setText("🔊")
            self.btn_snooze_session.setToolTip("Reactivar avisos")
