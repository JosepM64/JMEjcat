# JMEJCat — Technical Architecture Manifest

Version: 4.4
Status: Released
Core Principle: Separation of Concerns, Portable, Offline-First, Typed
License: LGPL v3
Language: English (technical-neutral vocabulary in code), Catalan in the UI

> This document describes the **real** structure of the codebase as of v4.4.
> Previous revisions (v3.x) described an aspirational `src/` package layout that
> was never adopted; the application uses a flat, module-per-concern layout at
> the repository root plus a small `core/` and `ui/` package.

---

## 1. ARCHITECTURAL OVERVIEW

### 1.1 Core Philosophy

- **Single Responsibility**: each module handles one concern (DB access, UI, export, backup…).
- **Portability**: copying the `data/` folder plus the executable = complete application state.
- **Simplicity**: minimal dependencies — Python + PySide6 + (optional) Pillow. SQLite via the stdlib.
- **Offline-First**: SQLite + local filesystem are the only data stores. No network calls at runtime.
- **Type-Safety**: the data layer is fully annotated and checked by mypy.

### 1.2 Technology Stack (as installed)

| Component | Version | Notes |
|---|---|---|
| Python | 3.13.x (3.13.14) | Conda env `jm_pyside_313` |
| PySide6 | 6.11.2 | Installed via **pip** (never conda-forge — breaks PyInstaller) |
| Pillow | 12.3.0 | Optional; used for thumbnails and image metadata |
| SQLite3 | stdlib | Direct `sqlite3` module, **not** QtSql |
| PyInstaller | 6.22.2 | Packaging (onedir) |
| ruff | 0.16.9 | Linter + formatter |
| mypy | 2.3.1 | Static type checking |
| pytest / pytest-cov | 9.1.1 / 7.1.0 | Test suite + coverage |

Runtime target: **Windows 10/11 64-bit only**.

### 1.3 Application Vocabulary

- UI labels: **Catalan** (Títol, Petició, Solució, Exemples, Cerca per títol…).
- Code identifiers, DB columns, file names: **English** (`title`, `request`, `solution`, `examples`).
- Class/function names: `PascalCase` / `snake_case`; 4-space indentation, double quotes, 100-col soft limit.

---

## 2. PROJECT LAYOUT

```text
JMEJCat/
├── jmejcat.py                # Entry point: logging, single-instance lock, QApplication
├── config.py                 # All constants (APP_VERSION, paths limits, colors, search fields)
├── utils.py                  # Path helpers (app/data/images/backups) + date validation
├── database.py               # Database (notes + images)
├── tramitacio_database.py    # TramitacioDatabase (court case files)
├── backup_manager.py         # Typed backup/restore/verify/cleanup
├── image_manager.py          # Image hashing, dedup, thumbnails
├── image_gallery.py          # Thumbnail grid widget
├── image_viewer.py           # Full-size image viewer (zoom)
├── ui_window.py              # MainWindow: composes the UI mixins
├── tramitacio_window.py      # TramitacioWindow (separate top-level window)
├── ui_dialogs.py             # Backup manager / verify / link dialogs
├── calculator.py             # Fee calculator for court amounts
├── md_exporter.py            # Markdown export
├── pdf_exporter.py           # PDF export (QtPrintSupport)
├── tramitacio_alarms.py      # Reminder/alarm helpers
├── core/                     # Shared, framework-free logic
│   ├── base_database.py      # BaseDatabase: connection, schema_version, migrations
│   ├── search.py             # escape_like / like_param / build_like_condition
│   └── tramit_colors.py      # Colour constants for case rows
├── ui/                       # MainWindow mixins + Tramitacio dialogs
│   ├── ui_window_menu.py     # Menus, actions, shortcuts
│   ├── ui_window_notes.py    # Note list, selection, save, autosave
│   ├── ui_window_editor.py   # Rich-text editors, expanded Solution editor, format painter
│   ├── ui_window_formatting.py # Formatting toolbar helpers
│   ├── ui_window_images.py   # Image gallery integration
│   ├── ui_window_export.py   # PDF / Markdown export
│   ├── ui_window_backup.py   # Backup dialogs and periodic backups
│   ├── ui_window_tramitacio.py # Tramitació panel inside the main window
│   └── tramitacio_edit_dialog.py # Non-modal case edit dialog
├── tests/                    # pytest suite (92 tests)
├── assets/                   # icon.ico + resources (bundled in the build)
├── build.bat                 # Windows build script (PyInstaller onedir)
├── JMEJCat.spec              # PyInstaller configuration
├── verify_automatica.py      # 50 self-checks (structure, imports, DB, config…)
└── pyproject.toml            # Tooling config only (ruff / mypy / pytest / coverage)
```

**Runtime data** (never bundled in the build; created next to the executable):

```text
data/
├── jmejcat.db                # Notes + images
├── tramitacio.db             # Case files
├── backups/                  # Timestamped DB backups + image zips
└── images/
    ├── original/             # {sha256_12}.{ext} (deduplicated by content hash)
    └── thumbs/               # {sha256_12}_256.jpg
```

---

## 3. DATA LAYER

### 3.1 Base class — `core/base_database.py`

`BaseDatabase` owns everything shared by both databases:

- `init_database()` — subclass hook that creates tables and indexes.
- `schema_version` table (`version INTEGER`) + `migrate()` / `_apply_migration(target_version)`:
  migrations are applied in order and the version is bumped only on success.
- `_get_connection()` — context manager yielding a `sqlite3.Connection` with
  `row_factory = sqlite3.Row`, `PRAGMA foreign_keys = ON`.
- `close()` — closes the connection safely.

### 3.2 Notes schema (`database.py`)

```sql
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL CHECK(length(title) BETWEEN 1 AND 100),
    request TEXT,
    solution TEXT,
    examples TEXT CHECK(examples IS NULL OR length(examples) <= 500),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    note_id INTEGER NOT NULL,
    filename TEXT NOT NULL,
    thumb_filename TEXT NOT NULL,
    sort_order INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_notes_title ON notes(title);
CREATE INDEX IF NOT EXISTS idx_images_note ON images(note_id);
```

Migration **v2** adds the `CHECK` constraints. Existing databases keep working
(the constraints are additionally enforced in Python by `_validate_note_fields`).

Public API (`Database`):

| Method | Purpose |
|---|---|
| `create_note(title, request, solution, examples) -> int` | Insert a note |
| `get_note(note_id) -> dict \| None` | Fetch one note |
| `update_note(note_id, title, request, solution, examples) -> bool` | Update |
| `delete_note(note_id) -> bool` | Delete (cascade images) |
| `get_all_notes(...) -> list[dict]` | Ordered list for the navigator |
| `search_notes(query, fields=None, limit=None, offset=0) -> list[dict]` | **Unified search** (v4.0) |
| `add_image / get_note_images / delete_image` | Image records |
| `move_image_up / move_image_down` | Reordering |
| `get_stats() -> dict` | Counters for the status bar |

### 3.3 Tramitació schema (`tramitacio_database.py`)

```sql
CREATE TABLE IF NOT EXISTS tramitacio (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero TEXT NOT NULL CHECK(length(numero) BETWEEN 1 AND 5 AND numero NOT GLOB '*[^0-9]*'),
    any INTEGER NOT NULL CHECK(any BETWEEN 1000 AND 9999),
    data TEXT NOT NULL CHECK(length(data) = 10 AND data GLOB '[0-9][0-9]/[0-9][0-9]/[0-9][0-9][0-9][0-9]'),
    info TEXT,
    color TEXT DEFAULT '',
    reminder_at TEXT DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_tramitacio_numero_any ON tramitacio(numero, any);
CREATE INDEX IF NOT EXISTS idx_tramitacio_any ON tramitacio(any);
CREATE INDEX IF NOT EXISTS idx_tramitacio_data ON tramitacio(data);
```

Highlights:

- `reminder_at` is added defensively with `ALTER TABLE` (older databases).
- `_consolidate_duplicates()` merges duplicate `(numero, any)` rows **before**
  creating the UNIQUE index, so the index creation never fails.
- `upsert_tramit()` merges the `info` text of an existing case.
- Maintenance: `rebuild_indexes()`, `vacuum()`, `purge_old_records(days)`,
  `update_statistics()`, `get_database_stats()`.

### 3.4 Unified search (`core/search.py`)

```python
escape_like(query) -> str          # escapes %, _ and \
like_param(query) -> str            # "%" + escaped + "%"
build_like_condition(column, query) -> tuple[str, Any]   # ("col LIKE ? ESCAPE '\\'", param)
```

Both databases use the same helper, so `%` and `_` are matched **literally**.
`Database.search_notes` accepts a `fields` allow-list
(`{"title", "request", "solution", "examples"}`) — the column name can never be
injected — and optional `limit` / `offset` for pagination.
`TramitacioDatabase.search_tramits` mirrors the same signature.

Search UI (v4.1): two independent boxes — *Cerca per títol…* (`fields=["title"]`)
and *Cerca dins el text…* (`fields=["request", "solution"]`) — with a shared
300 ms debounce; writing in one clears the other; `Ctrl+F` focuses the title box.

---

## 4. CORE COMPONENTS

### 4.1 `BackupManager` (`backup_manager.py`, fully typed)

Typed dataclasses: `BackupType`, `BackupInfo`, `VerifyResult`.

| Method | Purpose |
|---|---|
| `backup_database(backup_type="all") -> bool` | Timestamped copy of the DBs (and optional image zip) |
| `restore_backup(backup_filename: str \| Path) -> bool` | Restore a backup (path or name) |
| `get_backup_list(db_name: str \| None = None) -> list[BackupInfo]` | Sorted inventory, optional per-DB filter |
| `verify_backup_file(backup_path: Path \| str) -> VerifyResult` | Integrity check of one file |
| `verify_backups_in_folder(folder_path) -> list[BackupInfo]` | Integrity check of the whole folder |
| `cleanup_old_backups(...)` | Keep the last `BACKUP_COUNT` (5) backups |

Automatic backups run **on application close** and **periodically (every 30 min)**,
and the retained backups are verified by `verify_automatica.py`.

### 4.2 `ImageManager` (`image_manager.py`)

- Content hash: `sha256(content)[:12]` → identical images are **deduplicated**
  (`_resolve_unique_name()` appends `_1`, `_2`… on collision).
- Thumbnails: `THUMBNAIL_SIZE = (256, 256)`, JPEG quality 85.
- Works with or without Pillow (falls back to copying the original).

### 4.3 Exporters

- `pdf_exporter.py` — PDF via `QtPrintSupport` (`QTextDocument.print()`).
- `md_exporter.py` — Markdown conversion of a note (HTML → Markdown, `html.parser`).
- `calculator.py` — court fee calculation (30 % expenses, `TAX_PERCENTAGE`).

---

## 5. USER INTERFACE

### 5.1 `MainWindow` (`ui_window.py`)

Composed from eight mixins (single responsibility per concern):

```python
class MainWindow(
    UiWindowMenuMixin, UiWindowEditorMixin, UiWindowFormattingMixin,
    UiWindowNotesMixin, UiWindowImagesMixin, UiWindowExportMixin,
    UiWindowBackupMixin, UiWindowTramitacioMixin, QMainWindow,
): ...
```

Layout:

```text
QMainWindow
├── MenuBar: Fitxer, Editar, Format, Eines, Ajuda (Catalan UI)
├── Central: QSplitter (300 / 900)
│   ├── Left panel
│   │   ├── QLineEdit "Cerca per títol…"      (Ctrl+F)
│   │   ├── QLineEdit "Cerca dins el text…"
│   │   └── QListWidget (note titles + counters)
│   └── Right panel
│       ├── QLineEdit  [Títol]
│       ├── QTextEdit  [Petició]      (rich text)
│       ├── QTextEdit  [Solució]      (rich text, expandable)
│       ├── QTextEdit  [Exemples]
│       └── ImageGallery (4 columns)
└── StatusBar: save indicator, counters, transient messages
```

Behaviour highlights:

- **Autosave** every 30 s (`AUTOSAVE_INTERVAL`), only when the note is dirty.
- **Expanded Solution editor** (`Ctrl+Shift+E`): a non-modal dialog **bound to its
  origin note** (`_expanded_note_id` / `_expanded_original_html`). Saving always
  writes to that note, even if the main window has moved on to another one (fix v4.2).
- **Format painter**: copies the formatting of the current selection; double-click
  activates multi-application mode; `Esc` resets it (v4.4).
- **Zoom**: `Ctrl++` / `Ctrl+-` / `Ctrl+0` change the font size application-wide
  (persisted with `QSettings`), including the expanded editor and Tramitació window.
- **Closing**: asks to save, runs a final backup and cleans the backup folder.

### 5.2 Tramitació window (`tramitacio_window.py`)

- Table of cases with colour tags, filters, statistics, PDF/Markdown export.
- **Edit dialog is non-modal (v4.3)**: `TramitacioEditDialog` is opened with
  `show()` instead of `exec()`, so the rest of the application stays usable.
  - Closing with the X auto-saves to the case's own database.
  - Invalid data keeps the dialog open and shows a `WindowModal` warning
    (blocking only the dialog, not the whole application).
  - A custom `dialog_closed` signal notifies the parent (Qt does not emit
    `finished` when a window is closed with the X).
  - The parent keeps a registry (`_edit_dialogs`) and reuses/raises an already
    open dialog for the same case.

### 5.3 Keyboard shortcuts

| Context | Shortcut | Action |
|---|---|---|
| Global | `Ctrl+N` / `Ctrl+S` / `Ctrl+F` / `Ctrl+Q` | New / Save / Focus search / Quit |
| Global | `Ctrl++`, `Ctrl+-`, `Ctrl+0` | UI zoom in / out / reset |
| Editors | `Ctrl+B`, `Ctrl+I`, `Ctrl+U`, `Ctrl+T` | Bold, italic, underline, strikethrough |
| Editors | `Ctrl+Shift+V` | Paste as plain text |
| Editors | `Shift+F3` | Cycle upper/lower case |
| Editors | `Ctrl+Shift+E` | Expand Solution editor |
| Editors | `Esc` | Reset format painter |

---

## 6. CONFIGURATION

### 6.1 `config.py` (single source of truth)

| Group | Constants |
|---|---|
| Metadata | `APP_NAME`, `APP_VERSION` (**4.4**), `APP_AUTHOR`, `APP_LICENSE`, `APP_WEBSITE` |
| Database | `DB_FILENAME="jmejcat.db"`, `DB_FILENAME_TRAMITACIO="tramitacio.db"`, `DB_VERSION=2`, `BACKUP_COUNT=5` |
| Images | `THUMBNAIL_SIZE=(256, 256)`, `THUMBNAIL_QUALITY=85`, `IMAGE_HASH_LENGTH=12`, `SUPPORTED_IMAGE_EXTENSIONS` |
| UI limits | `TITLE_MAX_LENGTH=100`, `EXAMPLES_MAX_LENGTH=500`, `MAIN_WINDOW_SIZE`, `SPLITTER_SIZES`, `GALLERY_COLUMNS=4` |
| Search | `SEARCH_DELAY_MS=300`, `SEARCH_FIELDS=["title","request","solution"]` |
| Timing | `AUTOSAVE_INTERVAL=30` |
| Tramitació | `DATE_FORMAT="dd/MM/yyyy"`, `TAX_PERCENTAGE=0.30` |
| Theme | `COLORS`, `FONTS` |

`MIN_PYTHON_VERSION = (3, 13, 0)` is enforced at import time.

### 6.2 `utils.py` — path management

`get_app_path()`, `get_data_path()`, `get_images_path()`,
`get_original_images_path()`, `get_thumbnails_path()`, `get_backups_path()`
(all `lru_cache`d) resolve relative to the executable when frozen, or to the
project folder in development. `setup_data_directories()` creates the tree and
verifies write permissions. `validate_date_ddmmyyyy()` and `is_portable_mode()`
are the only other helpers.

### 6.3 `jmejcat.py` — entry point

1. Installs a global exception handler (`jmejcat_crash.log` next to the exe).
2. Configures logging: `logs/` next to the exe when frozen, `~/.jmejcat_logs` in
   development, WARNING level in production, 30-day log rotation.
3. **Single instance**: `~/.jmejcat.lock` stores the PID; a stale lock (crashed
   process) is detected and removed instead of blocking startup.
4. Sets `QT_PLUGIN_PATH` for the bundled `_internal/PySide6/plugins`.
5. Creates the data directories, then `MainWindow` and `app.exec()`.

---

## 7. BUILD & DEPLOYMENT

### 7.1 `build.bat` (Windows)

Steps: kill any running `JMEJCat.exe` → clean `build/` and `dist/` → run
PyInstaller with `JMEJCat.spec` → remove unused PySide6 modules → write
`dist/JMEJCat/README.txt` → report **BUILD EXITOSO**.

Requires `verify_automatica.py` to pass before packaging.

### 7.2 `JMEJCat.spec`

- `Analysis(['jmejcat.py'])`, `datas=[('assets','assets')]`.
- **`data/` is never bundled**: the app creates it next to the exe on first run,
  so real user data is never overwritten by a build.
- `optimize=2`, `upx=True`, `console=False`, `icon=['assets\\icon.ico']`.
- Explicitly excluded: `matplotlib`, `numpy`, `scipy`, `pandas`, `tkinter`,
  `PyQt5/6`, `email`, `http`, `urllib`, `xml`, `unittest`, `pip`, `conda`…
- `exclude_binaries={'opengl32sw.dll'}`.

### 7.3 Portable distribution (onedir)

```text
dist/JMEJCat/
├── JMEJCat.exe
├── _internal/            # Python runtime + Qt (onedir layout)
├── assets/
└── README.txt            # Catalan instructions
```

`data/` is created on first run next to the executable.
The bundle is ~110–120 MB.

---

## 8. QUALITY ASSURANCE

### 8.1 Tooling configuration (`pyproject.toml`)

- **ruff**: `line-length = 100`, `target-version = "py313"`, `select = ["F","E","W","UP","I"]`,
  `E501` ignored globally (HTML/CSS inside f-strings). Excludes `build/`, `dist/`,
  `data/`, `backups/`, `tests/`.
- **mypy**: `python_version = "3.13"`, `warn_return_any`, `ignore_missing_imports`,
  `disable_error_code = ["attr-defined"]`.
  - Stricter group (`disallow_untyped_defs = true`): `core.base_database`,
    `core.tramit_colors`, `core.search`, `database`, `tramitacio_database`,
    `backup_manager`, `utils`.
  - Relaxed group (Qt callbacks): `ui_window`, `ui.*`, `jmejcat`, `calculator`,
    `image_*`, `*_exporter`, `tramitacio_*`, with `call-overload`, `arg-type`,
    `has-type` disabled (known debt: the mixins do not inherit `QWidget`).
  - Tests are not type-checked.
- **pytest**: `testpaths = ["tests"]`, `--strict-markers`, `--tb=short`.
- **coverage**: `branch = true`, source = data layer + `core` + `config` + `utils`,
  `fail_under = 70`.

### 8.2 Test suite (92 tests)

| File | Coverage |
|---|---|
| `tests/conftest.py` | Fixtures; patches `utils.*` paths |
| `test_database.py` | CRUD, validation, ordering, images |
| `test_tramitacio.py` | Cases, upsert, alarms, maintenance |
| `test_search_unified.py` | Multi-field search, escaping, pagination, title/body split |
| `test_backup_restore.py` | Backup, restore, verify, cleanup (isolated paths) |
| `test_export.py` | Markdown / PDF export paths |
| `test_format_painter.py` | Format painter modes and signals (v4.4) |
| `test_tramitacio_nonmodal.py` | Non-modal dialog behaviour (v4.3) |
| `test_config.py` | Constants and version consistency |

### 8.3 Commands

```powershell
& 'C:\Users\JM\miniconda3\envs\jm_pyside_313\python.exe' -m pytest -q
& 'C:\Users\JM\miniconda3\envs\jm_pyside_313\python.exe' -m ruff check .
& 'C:\Users\JM\miniconda3\envs\jm_pyside_313\python.exe' -m mypy .
& 'C:\Users\JM\miniconda3\envs\jm_pyside_313\python.exe' verify_automatica.py
```

`verify_automatica.py` performs 50 self-checks (structure, imports, database
schema, config/version consistency, backups, assets) and must report
**50/50 PASSED** before any build.

### 8.4 Version consistency rule

Every release updates **all** of the following, or the verification fails:

`config.py` (`APP_VERSION`) · `pyproject.toml` (`version`) ·
`verify_automatica.py` (`PROJECT_VERSION`) · `AGENTS.md` · `CHANGELOG.md` ·
`ui_window.py` → *Ajuda → Quant a* (novetats).

---

## 9. KNOWN DEBTS & ROADMAP

### 9.1 Open items

1. **Flat layout** — the modules live at the repository root instead of a
   `src/jmejcat/` package. Migrating requires coordinated changes in
   `build.bat`, `JMEJCat.spec`, CI and `query.js` (deferred on purpose).
2. **Mixins are not `QWidget` subclasses** — hence the mypy exemptions for the
   UI layer.
3. **Format painter only in the expanded Solution editor**, not in the main
   window (pending decision).
4. **`TECHNICAL_MANIFEST.md`** — this revision (v4.4) replaces the obsolete
   v3.57 text; it must be refreshed with every major version bump.
5. `query.js` / `node_modules` — leftover tooling not used by the application.

### 9.2 Planned

- Packaging under `src/jmejcat/` (with compatibility shims).
- Progressive typing: extend the strict mypy group to the UI mixins.
- Coverage target raise from 70 % to 85 %.
- Optional `note_metadata` table (tags / category / priority) for the notes DB.

---

Maintainer: JMEJCat Development Team
License: LGPL v3 (compatible with PySide6)
Minimum Python: 3.13.0
Target Platform: Windows 10/11 64-bit
Repository: https://github.com/JosepM64/JMEjcat
