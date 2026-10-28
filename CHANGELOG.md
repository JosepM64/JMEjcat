# Changelog - JMEJCat

## v4.6 (2026-10-28)

### Filtre "CAT" a Gestió de Tramitació
- Nou botó toggle "CAT" a la barra de filtres de `tramitacio_window.py` (al costat de Color).
- Activat, mostra només els expediments amb `catalan = 1` (filtre a `get_all_tramits` / `search_tramits`).
- Estil verd quan està actiu; el botó "Netejar" el desmarca.
- La columna `catalan` ja existia des de v4.5 (migració defensiva `ALTER TABLE` per BD existents).

---\n\n## v4.5 (2026-10-28)

### Camp CAT (tramitar en català) als expedients de Tramitació
- BD: nova columna `catalan INTEGER DEFAULT 0` a la taula `tramitacio` (migració defensiva `ALTER TABLE` per a BD existents). `create_tramit`, `update_tramit` i `upsert_tramit` accepten `catalan: int = 0`.
- `TramitacioEditDialog`: nou botó toggle "CAT" al costat de Color. En verd = tramit en català; gris = no. L'estat es desa al camp `catalan` al Guardar / tancament automàtic i es recupera al obrir l'expedient.
- SoC manté: BD a `tramitacio_database.py`; UI al diàleg; versiòn pujada a 4.5.

## v4.4 (2026-10-22)

### Neteja de codi orfe
- Esborrats els mètodes/potències definits però mai cridats: `image_manager._generate_file_hash`, `utils.format_file_size`, `utils.get_resource_path`, `ui_window_notes.on_note_link_clicked` (duplicat de `_handle_link_click`).
- Esborrats els scripts de diagnòstic obsolets amb rutes hardcodejades: `analyze_db.py`, `analyze_tramitacio_bug.py`, `checks/` (check_null_ids, check_1435, fix_null_ids).
- Paràmetres morts eliminats: `now` a `_show_reminder_dialog`, `pdf_path` a `TramitacioWindow._on_pdf_export_finished`, `attrs` a `md_exporter.handle_starttag`; lambdes amb argument no utilitzat (`e`, `checked`).

### Fix: el pintor de format fa el que el tooltip anuncia
- Bug: el tooltip "🖌️ clic = 1 uso, doble clic = múltiples" no es complia: el doble clic no estava connectat i `multi_apply` era sempre `False`.
- Nou `_FormatPainterButton` (emissor de `doubleClicked`) connectat a `_handle_fp_double_click`: el doble clic copia el format i activa el mode multi-aplicació (ESC per sortir).
- `_apply_copied_format` centralitza l'aplicació del format (mode normal consumeix el format; mode multi el conserva).
- `force_close` de `_close_expanded_if_open` ja fa el que diu: desa i tanca sense preguntar.
- Tests nous: `tests/test_format_painter.py` (6 tests).

---

## v4.3 (2026-10-21)

### Fix: el diàleg d'edició de tràmit no bloqueja la resta de finestres
- Bug: en editar un tràmit (número, any, data, info) el diàleg era modal i bloquejava totes les finestres (notes, tramitació, altres mòduls).
- `TramitacioEditDialog` és ara NO modal (`setModal(False)` + `NonModal`) i s'obre amb `show()` en lloc d'`exec()`.
- Senyal nou `dialog_closed` (s'emet una sola vegada, en acceptar, rebutjar o tancar amb la X) → `TramitacioWindow` actualitza la taula.
- Els diàlegs fills (avís, validacions, duplicats) són modals només respecte al diàleg d'edició (`WindowModal`), no respecte a tota l'app.
- Auto-guardat en tancar amb la X (ja existent) però les dades invàlides **no** tanquen el diàleg: es mostren els errors i el formulari es queda obert.
- Si el mateix tràmit ja té un diàleg obert, es porta al davant en lloc d'obrir-ne un altre.
- 6 tests nous (`tests/test_tramitacio_nonmodal.py`): no modal, sense finestra modal activa, tancament amb auto-guardat, dades invàlides, reutilització del diàleg.

---

## v4.2 (2026-10-08)

### Fix: editor expandit de Solució lligat a la nota d'origen
- Bug: amb l'expandit obert es podia obrir una altra nota i en desar se sobreescrivia la nova (el diàleg no recordava de quina nota era i `on_note_selected` només avisava si `isModified()`).
- `expand_solution_editor` captura `_expanded_note_id` + `_expanded_original_html`; sense nota oberta no s'obre.
- `_save_expanded_editor` desa només el camp solució a la nota d'origen (resta de camps des de la BD); si la principal mostra una altra nota, avisa on ha desat.
- `on_note_selected`/`new_note`/`_close_expanded_if_open`: comparen amb l'origen (no `isModified`), desen a l'origen si cal i tanquen el diàleg abans de canviar.
- `save_note` sincronitza l'expandit si és de la nota actual; `autosave` només el té en compte en aquest cas.
- Ajuda → Quant a: entrada v4.2.

---

## v4.1 (2026-10-06)

### Doble caixa de cerca (títol + text, independents)
- Segona `QLineEdit` sota la de títol (`ui_window.py`): "Cerca per títol..." (només `title`) i "Cerca dins el text..." (`request`+`solution`).
- Caixes independents: en escriure a una es buida l'altra (mana l'última tocada); debounce 300 ms compartit; `Ctrl+F` segueix anant a la de títol.
- Test `test_search_title_vs_body_split`; suite **80 passed**, ruff/mypy nets.

---

## v4.0 (2026-09-28)

### Cerca unificada + BackupManager strict + Tests integració + Ajuda
- `core/search.py` nou: `escape_like`/`like_param` compartit; `database.search_notes(query, fields, limit, offset)` multi-camp (`SEARCH_FIELDS=["title","request","solution"]`); `tramitacio_database.search_tramits(..., limit, offset)`.
- `backup_manager.py` tipat estricte (`BackupType`, `BackupInfo`, `Path|str` a restore/verify, `get_backup_list()->list[BackupInfo]`, filtre `db_name`); mogut al grup mypy strict + coverage.
- Tests nous (79 total): `test_backup_restore.py` (roundtrip, corrupt→False, cleanup), `test_search_unified.py` (multi-camp, paginació, escape), `test_export.py` (MD all-in-one/separat). Fix aïllament from-imports via `_patch_bm_paths`.
- Ajuda → Quant a: cerca multi-camp + novetats v4.0.
- Nota: empaquetat `src/jmejcat/` ajornat a v4.1 (requereix migrar build.bat/spec/CI/query.js amb shims; ara trencaria el build).

### Verificació
- `pytest -q` → **79 passed**
- `ruff check .` → **All checks passed**
- `mypy .` → **Success: no issues found in 44 source files**

---

## v3.62 (2026-09-07)

### Sprint 2 — P1: CI + Paginació + UX + Backups + Integritat (2.3-2.10)

#### 2.3 CI GitHub Actions
- Nou `.github/workflows/ci.yml` (windows-latest, Python 3.13): `pip install -r requirements.txt` → `ruff check .` → `mypy .` → `pytest -q` → `verify_automatica.py` (informatiu) → spec check. Criteri merge §17.

#### 2.4 Paginació `get_all_*`
- `database.py:get_all_notes(limit=200, offset=0)` i `tramitacio_database.py:get_all_tramits(color_filter, limit=200, offset=0)` amb `LIMIT ? OFFSET ?` (o `LIMIT -1 OFFSET ?` si limit None). Compatibilitat total — cridants sense paràmetres continuen retornant 200 per defecte.

#### 2.5 Filtre "Avui" a Tramitació
- `tramitacio_database.py:search_tramits(data: str | None)` nou param opcional `AND data = ?`.
- `tramitacio_window.py` nou botó `Avui` (checkable, toggled → `on_search_changed`) que filtra `QDate.currentDate().toString("dd/MM/yyyy")`; `clear_filters()` desmarca Avui.

#### 2.6 Debounce de cerca
- `ui/ui_window_notes.py:170 on_search` ara fa debounce 300 ms via `QTimer` singleShot (`SEARCH_DELAY_MS`). Nova `_do_search()` fa la cerca real. Evita cerques contínues a cada pulsació.

#### 2.7 Verificar backup abans de restaurar
- `backup_manager.py:restore_backup()` crida `verify_backup_file()` abans de `shutil.copy2`; si invàlid → `False` + log `Backup invàlid, restauració abortada`. Fix `verify_backup_file()` per tancar connexió sempre (evita lock a Windows en fitxers corruptes).

#### 2.8 Backup automàtic periòdic
- `ui_window.py` nou `QTimer` 30 min (`_periodic_backup_timer`) que, si `current_note_modified`, desa la nota i fa `BackupManager.backup_database()` + `cleanup_old_backups()` silenciosa. Log informat.

#### 2.9 CHECK constraints a BD
- `database.py`: `title CHECK(length(title) BETWEEN 1 AND 100)`, `examples CHECK(... <=500)`
- `tramitacio_database.py`: `numero CHECK(length 1-5 AND NOT GLOB '*[^0-9]*')`, `any CHECK(BETWEEN 1000 AND 9999)`, `data CHECK(length=10 AND GLOB '[0-9][0-9]/[0-9][0-9]/[0-9][0-9][0-9][0-9]')`
- Validació prèvia a `C:\varis\JMEJCat\data` (384 tràmits / 89 notes): **0 violacions**. Noves BD ja tenen CHECK; BD existents validen a nivell aplicació (`_validate_*` → ValueError) mantenint compatibilitat.

#### 2.10 Sistema de migracions versionades
- `core/base_database.py`: taula `schema_version` + `_ensure_schema_version_table()` / `_get/_set_schema_version()` + `migrate()` que compara `config.DB_VERSION` (ara **2**) amb versió emmagatzemada i crida `_apply_migration(v)`. `Database` i `TramitacioDatabase` sobreescriuen `_apply_migration(2)` amb log compatibilitat. Primera init → `schema_version=2`.

### Verificació
- `ruff check .` → **All checks passed**
- `mypy .` → **Success: no issues found in 40 source files**
- `pytest -q` → **70 passed**
- `verify_automatica.py` → **50/50 PASS** (v3.62)
- Manual: paginació (limit 2 / offset 1), filtre Avui (1/2), debounce, restore corrupt → False, backup periòdic, CHECK rebuig (101 chars, 501, numero ABC, any 99, data 2024-01-01) tots OK.

---

## v3.61 (2026-09-06)

### Sprint 2 — Tooling: pytest + Ruff + mypy (2.1 i 2.2)

#### 2.1 Suite pytest real (70 tests)
- Nou directori `tests/` amb fixtures aïllades a `tmp_path` (mai toca el `data/` real):
  - `conftest.py` — `notes_db`, `tramit_db`, `tmp_data_dir`, `sample_png`, aïllament automàtic de `utils.get_*_path()`
  - `test_config.py` (21) — metadades, BD, imatges, UI, paths
  - `test_database.py` (24) — schema/WAL/FK, CRUD, cerca ESCAPE literal `%` `_`, imatges, stats
  - `test_tramitacio.py` (25) — schema+UNIQUE, CRUD, upsert, `_merge_info` (5 casos), cerca, alarmes, stats
- **Cobertura:** 70% total (config 94%, tramitacio_database 77%, database 70%, core.base_database 84%)
- `verify_automatica.py` ara informa de l'existència de la suite (50/50 PASS)

#### 2.2 Ruff + mypy via `pyproject.toml`
- **Nou fitxer** `pyproject.toml`: configuració de Ruff (F,E,W,UP,I; línia 100), mypy, pytest i coverage
- **Ruff**: 110 errors corregits (108 auto-fix: imports no usats, UP/I; 2 manuals E402) → **0 errors** a tota la base
- **Mypy**: 821 → **0 errors** en 40 fitxers:
  - Mòduls core (`database`, `tramitacio_database`, `core.*`, `utils`): `disallow_untyped_defs=true`
  - Afegits tipus `str | None`/`int | None` (PEP 484) i `-> None` a funcions sense anotar
  - `cast(int, cursor.lastrowid)` / `cast(int, cursor.rowcount)` (sqlite3 retorna Any)
  - Dicts anotats a `backup_manager` (`list[dict[str, Any]]`, `result: dict[str, Any]`)
  - `ImageManager.original_dir/thumbs_dir: Path` + `img: Image.Image`
  - `image_viewer.all_images: list[Path] | None`
  - Capa UI (mixins): deute arquitectònic conegut → `disable_error_code = ["call-overload", "arg-type", "has-type"]` només per a `ui.*` (P2 HANDOVER)

### Verificació
- `ruff check .` → **All checks passed**
- `mypy .` → **Success: no issues found in 40 source files**
- `pytest -q` → **70 passed in 0.72s**
- `verify_automatica.py` → **50/50 PASS**
- Imports de tots els mòduls: OK (sense regressions)

### Pròxims pasos (Sprint 2)
- 2.3 CI GitHub Actions
- 2.4 Paginació `get_all_*` (LIMIT/OFFSET)
- 2.5 Filtre "Avui" a Tramitació
- 2.6 Debounce de cerca (300 ms)
- 2.7 Verificar backup abans de restaurar
- 2.8 Backup automàtic periòdic
- 2.9 CHECK constraints a BD
- 2.10 Sistema de migracions versionades
- 2.11 FTS5 (condicional a volum)

---

## v3.60 (2026-09-04)

### Refactor: Sprint 1 (P0 + Quick Wins) — A1-A5, R5

#### A1: Centralitzar `TRAMIT_COLORS`
- **Abans:** duplicat a `tramitacio_window.py:38`, `tramitacio_edit_dialog.py:32` i `tramitacio_alarms.py:213`
- **Ara:** font única a `core/tramit_colors.py`; tothom importa des d'allà
- **Verificat:** l'app arrenca i obre finestres de tramitació/alarmes correctament

#### A2: Unificar `validate_date`
- **Abans:** `TramitacioEditDialog.validate_date()` i línia 208 de `tramitacio_window.py` feien servir la mateixa validació en paral·lel
- **Ara:** `utils.validate_date_ddmmyyyy()` (funció única)

#### A3: `Path` natiu a `sqlite3.connect`
- **Abans:** `sqlite3.connect(str(db_path))`
- **Ara:** `sqlite3.connect(db_path)` (Python 3.11+ ja ho admet)

#### A4: Thread-safety SQLite (A4)
- `BaseDatabase._conn` ara es protegeix amb `threading.Lock` dins de `_get_connection`
- Afegit `PRAGMA busy_timeout=5000` (espera fins 5s si la BD està ocupada)
- Justificació: la connexió era compartida entre UI i `QThread` (PDF export) — risc de `Database is locked`

#### A5: Hash d'imatges robust
- **Abans:** `SHA256(content + timestamp)` (timestamp només per garantir unicitat — però això NO era deduplicació)
- **Ara:** `SHA256(content)` pur + mètode `_resolve_unique_name()` que dedup si ja existeix o afegeix sufix `_1`, `_2`... si el nom col·lideix amb contingut diferent
- **Test:** afegir la mateixa imatge 2× retorna el mateix filename

#### R5: Log rotation (30 dies)
- `setup_logging()` esborra `data/logs/jmejcat_YYYYMMDD_*.log` més antics de 30 dies
- Evita infinitat de fitxers de log a llarg termini
- Errors individuals (nom de fitxer invàlid, permís denegat) no bloquegen l'arrencada

### Verificació
- `python verify_automatica.py` → **49/49 PASS** (sense regressions)
- Tests manuals: arrencada, finestres Notes/Tramitació/Alarmes, afegir imatges deduplicades

### Canvis incompatibles
- Cap. Tots els canvis són additius o refactors interns.
- Nous fitxers: `core/tramit_colors.py` (afegit al `JMEJCat.spec` via auto-detect)

### Pròxims pasos (Sprint 2 — P1)
- P1.1 Paginació `get_all_*` (LIMIT/OFFSET)
- P1.2 FTS5 per Notes + Tramitació
- P1.3 Filtre "Avui" a Tramitació
- P1.4 Debounce de cerca (300 ms)
- P1.5 Verificar backup abans de restaurar
- P1.6 Backup automàtic periòdic
- P1.7 CHECK constraints a BD
- P1.8 Sistema de migracions versionades
- Veure `JMEJCat_Millores_Definitives.md` per a detalls complets

---

## v3.57 (2026-08-25)

### Fix: El zoom ara també escala el text dels editors
- **Bug**: Amb Ctrl +/- creixien els menús i etiquetes, però el text **dins dels editors** (Solució, editor expandit) restava igual
- **Causa**: Els QTextEdit guarden la font dins del document (`QTextDocument.defaultFont`) i no segueixen la font de l'aplicació un cop creats
- **Solució**: En aplicar el zoom s'actualitza explícitament la font de tots els editors oberts (finestra principal, editor expandit)
- Nota: el text amb format explícit (mida de lletra aplicada manualment des de la paleta) manté la seva mida — és inherent al text enriquit

---

## v3.56 (2026-08-25)

### Fix: Zoom (Ctrl +/-) a totes les finestres
- **Bug**: Els dreceres Ctrl + / Ctrl - / Ctrl 0 només funcionaven amb la finestra principal en focus; a l'editor expandit de Solució i a la finestra de Tramitació no feien res
- **Solució**: Els dreceres ara usen context **d'aplicació** (`Qt.ApplicationShortcut`): actius des de qualsevol finestra del programa
- El canvi de mida s'aplica a totes les finestres obertes simultàniament

---

## v3.55 (2026-08-25)

### Fix: Visor d'imatges — límit estàndard del 100%
- "Ajustar a pantalla" (⊞, doble clic) **no amplia mai per sobre del 100%**: les imatges petites es veuen nítides a mida real
- Per ampliar-les, zoom manual (+/- o Ctrl+roda) — l'ampliació digital sempre genera borrositat
- Nota: la qualitat de les imatges depèn del fitxer d'origen; JMEJCat no recomprimeix res (els originals es copien byte a byte)

### Fix: Cerca amb caràcters especials
- Cercar `%` o `_` ara funciona literal (abans actuaven com comodins SQL) a notes i tramitacions

### Fix: Recordatoris de Tramitació
- El parseig de dates accepta qualsevol format ISO (`fromisoformat`), no només `YYYY-MM-DD HH:MM:SS` exacte

### Fix: Doble tancament de BD a Tramitació
- `closeEvent` cridava `super().closeEvent(event)` dues vegades

### Ajuda actualitzada
- El diàleg "Quant a" reflecteix la funció real (gestió d'apunts i expedients de tramitació) i inclou totes les dreceres de teclat (zoom Ctrl+/-, visor F11, etc.)

### Llibreries
- pyinstaller-hooks-contrib 2026.7 · better-sqlite3 13 (eina query.js)
- PySide6 6.11.2, Pillow 12.3.0, PyInstaller 6.22.2: ja al dia

---

## v3.54 (2026-08-25)

### Nou: Zoom global de la interfície
- **Ctrl +** / **Ctrl -**: augmenta/redueix la mida de lletra de tota l'app (útil en portàtils)
- **Ctrl 0**: restaura la mida normal; també disponible al menú Opcions
- La preferència es recorda entre sessions (QSettings)

### Fix: Visor d'imatges a pantalla completa
- **Bug**: En anar a pantalla completa (⛶ / F11) la imatge es quedava a la mida anterior, centrada i sense créixer
- **Solució**: Qualsevol redimensió de la finestra (pantalla completa, maximitzar) recàlcula l'ajust automàticament
- El primer ajust ara es fa quan la finestra ja té la mida real; doble clic sobre la imatge = ajustar a pantalla
- Zoom manual (botons, Ctrl+roda) desactiva el re-ajust fins que es premi ⊞

### Fix: Lock d'instància única
- **Bug**: Si l'app crashjava, el fitxer `.jmejcat.lock` bloquejava totes les arrencades següents (calia `tancar_jmejcat.bat`)
- **Solució**: Només bloqueja si el PID del lock encara és un procés JMEJCat viu; si és obsolet, s'esborra i continua

### Fix: Exportació PDF
- Eliminades crides `processEvents()` des del thread d'exportació (anti-patró; el progrés ja arriba via signals)

### Fix: Verificació automàtica
- `verify_automatica.py` actualitzat a l'arquitectura actual: **49/49 verificacions superades** (abans 47 amb 2 fallos per classes mogudes de fitxer)

---

## v3.53 (2026-08-25)

### Fix: Build sense dades privades ni codi font
- **JMEJCat.spec**: Els blocs `datas` incloïen `data/jmejcat.db`, `data/tramitacio.db`, `data/images` i tots els `.py` del projecte dins de cada build (`dist/JMEJCat/_internal/`)
- **Risc**: Les dades personals reals i el codi font s'incrustaven a cada executable distribuït
- **Solució**: Només s'empaqueta `assets/`; l'aplicació crea `data/` al costat de l'exe en el primer arrencada (`utils.setup_data_directories`)

### Fix: Backups segurs amb BD en calent (WAL)
- **backup_manager.py**: `backup_database()` copiava les BD amb `shutil.copy2` mentre SQLite treballava en mode WAL, podent produir backups incomplets o trencats
- **Solució**: S'usa l'API de backup de SQLite (`Connection.backup`), que genera un snapshot consistent que inclou el contingut pendent del WAL
- **Verificat**: Prova funcional correcta (86 notes + 369 tràmits exportats íntegrament)

---

## v3.52 (2026-07-23)

### Millora finestra Edició Tràmit
- **Mida augmentada**: Finestra d'edició individual amplada a 1050×600 (igual que la llista de Tramitació)
- **Camp Color reubicat**: El selector de Color s'ha mougit del formulari principal a la barra de botons, situated entre "Establir avís" i "Guardar" per allunyada espai vertical al formulari
- **Disformació original mantenida**: La disposició vertical dels camps (Número, Any, Data, Info) s'ha preservat tal com estava originalment
- **Botons sense canvis**: Manté els botons originals (Calculadora, Alarmes, Guardar, Cancel·lar) sense afegir ni eliminar cap

---

## v3.51 (2026-07-19)

### Millora finestra Tramitació
- Finestra un 50% més gran (1050×750)
- Edició d'expedients ara usa `update_tramit` (reemplaça info) en lloc de `upsert_tramit` (mergeja)

### Fix Bloqueig info a Tramitació
- **Bug**: El mètode `_merge_info` retornava `old_info` quan `new_info` era buit, impedint esborrar el camp Info
- **Afectava**: Dades inserides manualment per SQL o blocs acumulats no es podien treure des del programa
- **Solució**: Quan l'usuari neteja el camp Info, ara es guarda buit correctament

## v3.44 (2026-07-07)

### Nou: Sistema d'UPERT per Tramitació
- **Evitar duplicats**: Quan es crea un tràmit amb número+any que ja existeix, es mostra diàleg de confirmació per actualitzar
- **Consolidació d'info**: Si es confirma la fusió, l'info antiga es manté i la nova s'afegeix amb separador `--- Dades noves ---`
- **Índex UNIQUE**: S'afegit restricció UNIQUE a `(numero, any)` per integritat a nivell de BD
- **Migració automàtica**: Els duplicats existents es consoliden a l'iniciar l'aplicació

### Nou: Pantalla d'Alarmes
- **Llistat cronològic**: Nova finestra amb totes les alarmes ordenades per data
- **Indicador d'estat**: Color segons proximitat (vermell=passada, groc=avui, taronja≤3 dies, verd>3 dies)
- **Filtre**: Checkbox per mostrar/ocultar alarmes passades
- **Accés ràpid**: Doble clic o botó per obrir el tràmit associat
- **Botó "⏰ Alarmes"**: Afegit a la barra de botons de Tramitació

### Nou: Eines de Manteniment BD
Menú **Ajuda → Manteniment BD Tramitació** amb:
- **Rebuild Índexs**: Reconstrueix tots els índexs (REINDEX)
- **Actualitzar Estadístiques**: Optimitza consultes (ANALYZE)
- **Purga Dades Antigues**: Elimina registres amb més de N dies
- **VACUUM**: Redueix l'espai utilitzat
- **Estadístiques BD**: Mostra resum de registres, mida, duplicats

---

## v3.43
- Versió anterior (sense changelog documentat)
