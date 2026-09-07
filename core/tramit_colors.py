"""
Colors disponibles per als tràmits (font única de veritat).

Abans estava duplicat a tramitacio_window.py, tramitacio_edit_dialog.py
i tramitacio_alarms.py. Ara tothom importa d'aquí.
"""

from PySide6.QtGui import QColor

# Colors semitransparents per als markers de tràmits
TRAMIT_COLORS = {
    "": ("Sense color", QColor(0, 0, 0, 0)),
    "vermell": ("Vermell (Pendent)", QColor(255, 0, 0, 80)),
    "taronja": ("Taronja (Urgent)", QColor(255, 165, 0, 80)),
    "groc": ("Groc (Atenció)", QColor(255, 255, 0, 80)),
    "verd": ("Verd (Fet)", QColor(0, 255, 0, 80)),
    "blau": ("Blau (Info)", QColor(0, 0, 255, 80)),
    "lila": ("Lila (Especial)", QColor(128, 0, 128, 80)),
    "gris": ("Gris (Archivat)", QColor(128, 128, 128, 80)),
}
