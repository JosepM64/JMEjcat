# -*- mode: python ; coding: utf-8 -*-
"""
JMEJCat - PyInstaller Configuration
Optimized for minimal size and maximum performance

Analysis of PySide6 usage in codebase:
- QtWidgets: Used in ui_window.py, ui_dialogs.py, tramitacio_window.py, calculator.py, jmejcat.py
- QtCore: Used in all modules for Qt, Signal, QTimer, QDate, etc.
- QtGui: Used in all modules for icons, colors, fonts, etc.
- QtPrintSupport: Used in ui_window.py for PDF export
- QtSql: NOT used (SQLite is used directly via sqlite3 module)
- QtOpenGL: NOT used (no 3D graphics)
- QtQml/QtQuick: NOT used (no QML/Quick components)

Optimizations applied:
- Removed unused Qt modules (Qml, Quick, Sql, Xml)
- Increased optimization level to 2 (bytecode optimization)
- Strip disabled (Windows strip not available, warnings are harmless)
- Added extensive excludes for unused Python modules
- Separated UI components into independent modules (image_viewer.py, image_gallery.py, ui_dialogs.py)
"""
import os
import glob

pyside_module = __import__('PySide6')
pyside_path = getattr(pyside_module, '__file__', None) or pyside_module.__path__[0]

# Find all required DLLs dynamically
binaries = []

# Core Qt DLLs needed (conservative approach to avoid missing dependencies)
core_dlls = [
    'Qt6PrintSupport.dll',
    # Essential dependencies
    'Qt6Network.dll',  # Required by Qt6Core
    'Qt6OpenGL.dll',  # Required by Qt6Gui
    'Qt6OpenGLWidgets.dll',  # Required by Qt6Widgets
    # Platform plugin (required)
    'qwindows.dll',
]

for dll in core_dlls:
    dll_path = os.path.join(pyside_path, dll)
    if os.path.exists(dll_path):
        binaries.append((dll_path, '.'))

# Add platform plugins
platforms_src = os.path.join(pyside_path, 'plugins', 'platforms')
if os.path.exists(platforms_src):
    binaries.append((platforms_src, os.path.join('PySide6', 'plugins', 'platforms')))

# Add styles (optional but useful)
styles_src = os.path.join(pyside_path, 'plugins', 'styles')
if os.path.exists(styles_src):
    binaries.append((styles_src, os.path.join('PySide6', 'plugins', 'styles')))

a = Analysis(
    ['jmejcat.py'],
    pathex=[],
    binaries=binaries,
    # User data (data/) and source code are intentionally NOT bundled:
    # the app creates data/ next to the exe on first run.
    datas=[
        ('assets', 'assets'),
    ],
    hiddenimports=[
        'PySide6',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.QtPrintSupport',
        'sqlite3',
        'dataclasses',
        'html.parser',
        'md_exporter',
        'core',
        'core.base_database',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib', 'numpy', 'scipy', 'pandas', 'IPython', 'jupyter',
        'PyQt5', 'PyQt6',
        'tkinter', 'tkinter.ttk', 'tkinter.messagebox',
        'email', 'email.mime', 'email.utils',
        'http', 'http.client', 'http.server',
        'urllib', 'urllib.parse', 'urllib.request',
        'xml', 'xml.etree', 'xml.dom',
        'unittest', 'unittest.mock',
        'pdb', 'bdb', 'cmd',
        'pydoc', 'doctest',
        'distutils', 'setuptools',
        'pip', 'conda',
    ],
    noarchive=False,
    optimize=2,
    runtime_tmpdir=None,
)
pyz = PYZ(a.pure)

# Filter out unnecessary binaries
exclude_binaries = {'opengl32sw.dll'}
a.binaries = [b for b in a.binaries if os.path.basename(b[0]) not in exclude_binaries]

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='JMEJCat',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets\\icon.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='JMEJCat',
)
