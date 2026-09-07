# Handover JMEJCat — de l'equip actual al següent

**Data:** 2026-09-07
**Versió lliurada:** v3.62 (Sprint 1 + Sprint 2.1-2.10 complets)
**Document mestre de millores:** [`JMEJCat_Millores_Definitives.md`](./JMEJCat_Millores_Definitives.md)

---

## 1. Estat actual

| Item | Estat |
|------|-------|
| Versió | **v3.62** (`APP_VERSION` a `config.py`; també a `pyproject.toml` i `AGENTS.md`) |
| Build PyInstaller | Pendent rebuild — 117 MB onedir (últim verificat v3.60) |
| `verify_automatica.py` | **50/50 PASS** (v3.62) |
| Tests pytest | ✅ **70 passed** en 0.76s (cobertura 70%) |
| Ruff | ✅ **0 errors** (All checks passed) |
| Mypy | ✅ **0 errors** (40 source files) |
| CI | ✅ **.github/workflows/ci.yml** (windows-latest, Python 3.13) |

### Fet fins ara

**Sprint 1 (Quick Wins P0) — v3.60 ✅**

| ID  | Millora                                        | Estat |
|-----|------------------------------------------------|-------|
| A1  | Centralitzar `TRAMIT_COLORS` a `core/tramit_colors.py` | ✅ |
| A2  | Unificar `validate_date` a `utils`              | ✅ |
| A3  | `Path` natiu a `sqlite3.connect`                | ✅ |
| A4  | Thread-safety BD (Lock + busy_timeout=5000)     | ✅ |
| A5  | Hash imatges amb deduplicació                   | ✅ |
| R5  | Log rotation 30 dies                            | ✅ |

**Sprint 2.1-2.2 (Tooling) — v3.61 ✅**

| ID  | Millora                                        | Estat |
|-----|------------------------------------------------|-------|
| 2.1 | Suite pytest real (70 tests, cobertura 70%)     | ✅ |
| 2.2 | `pyproject.toml` Ruff + mypy (0 errors ambdós)  | ✅ |

**Sprint 2.3-2.10 (P1) — v3.62 ✅**

| ID  | Millora                                        | Estat |
|-----|------------------------------------------------|-------|
| 2.3 | CI GitHub Actions (windows-latest)             | ✅ |
| 2.4 | Paginació `get_all_*` limit/offset 200         | ✅ |
| 2.5 | Filtre "Avui" a Tramitació                     | ✅ |
| 2.6 | Debounce cerca 300 ms                          | ✅ |
| 2.7 | Verificar backup abans de restaurar            | ✅ |
| 2.8 | Backup automàtic periòdic 30 min               | ✅ |
| 2.9 | CHECK constraints (validat 0 violacions)        | ✅ |
| 2.10| Migracions versionades `schema_version` DBv2   | ✅ |

**Fitxers nous/creats:** `tests/` (3 arxius), `pyproject.toml`, `core/tramit_colors.py`, `.github/workflows/ci.yml`.

---

## 2. Què cal fer ara — Sprint 2 resta + P2

> Ordre recomanat. Els ítems ✅ ja estan fets.

### Sprint 2 completat ✅
- **2.3 CI** → `.github/workflows/ci.yml` fet (windows-latest)
- **2.4 Paginació** → `get_all_*` limit/offset 200
- **2.5 Avui** → botó Avui + `search_tramits(data)`
- **2.6 Debounce** → `QTimer` 300 ms a `on_search`
- **2.7 Verify backup** → `restore_backup()` verifica abans de copiar
- **2.8 Backup periòdic** → `QTimer` 30 min si modificat
- **2.9 CHECK** → title 100, examples 500, numero 1-5 dígits, any 1000-9999, data dd/MM/yyyy (0 violacions a C:/varis)
- **2.10 Migracions** → `schema_version` DB_VERSION=2

### 2.11 FTS5 (condicional a volum, ~6 h) ← **SEGÜENT opcional**
- Només si es preveuen >1.000 registres. Ara: ~89 notes / ~384 tràmits → **posposar** fins superar 1.000.
- Si s'activa: índex FTS5 sobre títol+petició+solució+info amb triggers AFTER INSERT/UPDATE.

---

## 3. Decisions pendents (abans de P2)

| Pregunta | Impacte |
|----------|---------|
| **SQLCipher?** — Es requereix xifratge de BD en repòs? | Promou §12 a P0 si s'accepta; sinó P2 |
| **Certificat EV?** — ~300-400€/any justificat? | Sí → Sprint 5; No → portable sense signar |
| **Updater auto o notificació?** | Notificació més simple i segur (D2 de la llista) |
| **MSI vs portable?** | Usuaris finals — instal·lador o carpeta neta? |

---

## 4. Comandes de verificació (pre-merge)

```bash
# Totes han de passar
python verify_automatica.py
C:\Users\JM\miniconda3\envs\jm_pyside_313\python.exe -m ruff check .
C:\Users\JM\miniconda3\envs\jm_pyside_313\python.exe -m mypy .
C:\Users\JM\miniconda3\envs\jm_pyside_313\python.exe -m pytest -q
node query.js s
node query.js t "" "" 50
build.bat
```

**Comandes de cobertura:**
```bash
C:\Users\JM\miniconda3\envs\jm_pyside_313\python.exe -m pytest --cov=database --cov=tramitacio_database --cov=config --cov=core.base_database --cov=utils
```

---

## 5. Estructura del projecte (referència ràpida)

```
JMEJCat/
├── jmejcat.py                 # Entry point (lock, logging rotatiu 30 dies)
├── config.py                  # Constants, APP_VERSION = 3.62, DB_VERSION=2
├── ui_window.py               # MainWindow + 8 mixins + backup periòdic 30 min
├── database.py                # Notes DB (CHECK title 100, examples 500, paginació)
├── tramitacio_database.py     # Tramitació DB (CHECK + Avui + paginació + upsert)
├── backup_manager.py          # Backups sqlite3 + verify abans restaurar
├── pyproject.toml             # Ruff + mypy + pytest + coverage
├── core/
│   ├── base_database.py       # WAL + FK + Lock + migrate schema_version
│   └── tramit_colors.py       # Paleta colors (font única)
├── ui/                        # 8 mixins (debounce 300ms a notes)
├── tests/                     # 70 tests pytest (conftest + 3 arxius)
├── pdf_exporter.py, md_exporter.py, image_manager.py
├── calculator.py, query.js
├── .github/workflows/ci.yml   # CI windows-latest (ruff/mypy/pytest/verify)
└── data/                      # BD + imatges + logs (exclòs al build)
```

---

## 6. Notes per a l'equip següent

1. **Principi rector:** "Canvi mínim necessari" — canvis petits i verificables, cap refactor ample.
2. **Estabilitat > funcionalitats:** projecte en producció amb dades judicials reals.
3. **Criteri de merge actual:** `ruff check .` + `mypy .` + `pytest -q` + `verify_automatica.py` (50/50). `verify_automatica.py` és informatiu, no bloqueja.
4. **Mypy i els mixins UI:** hi ha `disable_error_code = ["call-overload", "arg-type", "has-type"]` **només** per a `ui.*` (els mixins no hereten QWidget al tipus — deute P2). No l'amplieu a mòduls core.
5. **Versions:** pujar `APP_VERSION` (config.py) + `version` (pyproject.toml) + entrada CHANGELOG.md + AGENTS.md.
6. **Build:** `JMEJCat.spec` NO ha d'incloure `data/` ni codi font (regla AGENTS.md).
7. **Entorn:** `C:\Users\JM\miniconda3\envs\jm_pyside_313\python.exe` (pytest 9.1.1, ruff 0.16.4, mypy 2.3.1, pytest-cov 7.1.0).
8. **Dades reals de prova:** `C:\varis\JMEJCat` conté una build amb `data/` real (jmejcat.db + tramitacio.db + backups) — útil per validar 2.9 (CHECK constraints).

---

## 7. Estat de les versions

| Versió | Data | Contingut |
|--------|------|-----------|
| 3.57 | 2026-08-25 | Base (zoom text, cerca literal, backups WAL) |
| 3.60 | 2026-09-04 | Sprint 1: A1-A5, R5 (colors, dates, Path, thread-safety, hash, logs) |
| 3.61 | 2026-09-06 | Sprint 2.1-2.2: pytest (70), Ruff 0, mypy 0, pyproject.toml |
| 3.62 | 2026-09-07 | Sprint 2.3-2.10: CI, paginació, Avui, debounce, backup verify/periodic, CHECK, migracions |

---

*Document actualitzat el 2026-09-07. Següent tasca recomanada: **2.11 FTS5 (posposat fins 1.000 registres) o P2 UX (Drag&Drop, Undo, Dark Mode)**.*
