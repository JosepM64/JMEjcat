# JMEJCat - Guia Ràpida de Desenvolupament

## Per reprendre el projecte

Copia i enganxa això en iniciar una sessió amb l'agent:

```
Aquest és el projecte JMEJCat (v3.62), gestió d'apunts i control d'expedients
d'un tramitador d'un jutjat civil de Barcelona. Python 3.13 + PySide6 + SQLite (WAL).

Per entendre el projecte ràpidament:
1. Llegeix AGENTS.md (estat, estructura, regles) i CHANGELOG.md (històric)
2. Executa la verificació: python verify_automatica.py (50 checks) + pytest/ruff/mypy

Arxius clau:
- jmejcat.py (entrada, lock d'instància única)
- ui_window.py (MainWindow amb 8 mixins del paquet ui/)
- core/base_database.py (BaseDatabase compartida, WAL)
- database.py / tramitacio_database.py (les dues BD)
- JMEJCat.spec + build.bat (build PyInstaller)

Repo: https://github.com/JosepM64/JMEjcat
```

---

## Resum del Projecte

**JMEJCat** és una aplicació d'escriptori portable i offline per a la **gestió
d'apunts i el control d'expedients** d'un tramitador en un jutjat de lo civil
de Barcelona.

### Tecnologia
- **Llenguatge**: Python 3.13 (conda `jm_pyside_313`)
- **UI**: PySide6 6.11 (Qt6)
- **BD**: SQLite en mode WAL (dues BD: `data/jmejcat.db`, `data/tramitacio.db`)
- **Imatges**: Pillow (miniatures 256px; els originals es copien sense recomprimir)
- **Empaquetat**: PyInstaller 6.22 (`JMEJCat.spec`, onedir ~110 MB)

### Estructura
```
JMEJCat/
├── jmejcat.py              # Punt d'entrada (logging, lock, excepthook)
├── ui_window.py            # MainWindow (8 mixins + backup periòdic 30 min)
├── ui/                     # Mixins: menu, editor, formatting, notes (debounce 300ms), images,
│                           #   export, backup, tramitacio + tramitacio_edit_dialog
├── core/base_database.py   # BaseDatabase: WAL + FK + Lock + migrate schema_version (v2)
├── database.py             # BD notes (CHECK title 100, examples 500, paginació 200)
├── tramitacio_database.py  # BD tramitació (CHECK numero/any/data, Avui, paginació, upsert)
├── tramitacio_window.py    # Finestra tramitació (filtre Avui, taula, export)
├── tramitacio_alarms.py    # Alarmes cronològiques
├── backup_manager.py       # Backups via API sqlite3 + verify abans restaurar
├── image_manager.py        # Imatges: hash SHA256, miniatures, originals
├── image_viewer.py         # Visor (zoom Ctrl+roda, F11, límit 100% al fit)
├── image_gallery.py        # Galeria de miniatures
├── pdf_exporter.py         # Export PDF (QThread + signals)
├── md_exporter.py          # Export Markdown
├── calculator.py           # Calculadora despeses/pagaments
├── config.py               # Constants i APP_VERSION=3.62 / DB_VERSION=2
├── utils.py                # Rutes (app/data/images/backups)
├── query.js                # CLI Node per consultar les BD (better-sqlite3)
├── verify_automatica.py    # Verificació automàtica (50 checks)
├── .github/workflows/ci.yml # CI windows-latest (ruff/mypy/pytest/verify)
└── data/                   # Dades de l'usuari (MAI al repo ni al build)
```

---

## Checklist obligatori abans de cada release

```bash
python verify_automatica.py    # Ha de dir: PASADOS: 50
C:\Users\JM\miniconda3\envs\jm_pyside_313\python.exe -m ruff check .
C:\Users\JM\miniconda3\envs\jm_pyside_313\python.exe -m mypy .
C:\Users\JM\miniconda3\envs\jm_pyside_313\python.exe -m pytest -q
```

La versió viu a `config.py` (APP_VERSION) + `pyproject.toml` (version); `build.bat` la llegeix.
Recorda actualitzar CHANGELOG.md, AGENTS.md i HANDOVER.md.

---

## Com fer canvis

1. **Editar codi**: modificar els fitxers corresponents
2. **Provar en local**: `python jmejcat.py` (conda jm_pyside_313)
3. **Verificar**: `python verify_automatica.py`
4. **Compilar**: `build.bat` → `dist/JMEJCat/JMEJCat.exe`
5. **Commit + push**: repo git → https://github.com/JosepM64/JMEjcat

---

## Regles importants (apreses amb dolor)

- **MAI** afegir `data/` ni `*.py` al bloc `datas` de `JMEJCat.spec`
  (hi anaven expedients reals dins de cada build)
- Backups de BD sempre via **API sqlite3** (`Connection.backup`), mai
  `shutil.copy2` (la BD viu en WAL i una còpia de fitxer pot sortir trencada)
- Els `.db` del USB (`F:\segur`) són la còpia de treball real de l'usuari:
  si s'editen índexs, fer-ho amb l'eina del menú Ajuda → Manteniment BD
- `node_modules/` + `query.js` són intencionals (CLI de consulta BD)

---

**Última actualització:** 2026-09-07
**Versió:** 3.62
**Desenvolupador:** Josep Maria Tapia Estaragues
**Llicència:** LGPL v3
