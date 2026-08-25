# JMEJCat — Projecte

## Descripció
Gestió d'apunts i control d'expedients per a un tramitador d'un jutjat de lo civil (Barcelona). Portable i offline. Python 3.13 + PySide6 + SQLite (WAL).
- **Versió**: 3.56 | **Data**: 2026-08-25 | **Build**: ~110 MB
- **Repo**: https://github.com/JosepM64/JMEjcat (públic, branch `main`)

## Estructura
```
JMEJCat/
├── jmejcat.py              # Entry point (lock instància única, logging, excepthook)
├── config.py               # Constants, APP_VERSION
├── ui_window.py            # MainWindow (composta amb 8 mixins del paquet ui/)
├── database.py             # Notes DB (hereda BaseDatabase)
├── tramitacio_database.py  # Tramitació DB (upsert, alarmes, manteniment)
├── tramitacio_window.py    # Finestra de tramitació (taula, filtres, export CSV/PDF)
├── tramitacio_alarms.py    # Finestra d'alarmes cronològiques
├── backup_manager.py       # Backups via API sqlite3 (snapshot WAL consistent)
├── core/base_database.py   # BaseDatabase compartida (WAL, FK, connexió persistent)
├── ui/                     # 8 mixins UI + tramitacio_edit_dialog
├── pdf_exporter.py         # Export PDF (QThread)
├── md_exporter.py          # Export Markdown
├── image_manager.py        # Imatges (thumbnails, SHA256)
├── calculator.py           # Calculadora despeses/diferència de pagaments
├── query.js                # Consultes externes (better-sqlite3)
├── CHANGELOG.md            # Historial complet de canvis
└── data/                   # BD portables + imatges (NO al repo; es crea sola al 1r arrencada)
```

## Com executar
```bat
python jmejcat.py
```

## Com compilar
```bat
build.bat
# Resultat: dist/JMEJCat/JMEJCat.exe (~117 MB)
# Versió: llegida automàticament de config.py
```

## Verificació
```bat
python verify_automatica.py
```

## Dependències
```
PySide6, Pillow, PyInstaller, Node.js 24+, better-sqlite3
# SQLite3 inclòs amb Python
```

## Query externa (Node.js)
```bash
node query.js s                          # Stats
node query.js t [numero] [any] [limit]   # Tramitacions
node query.js n [títol] [limit]          # Notes
node query.js i <note_id>                # Imatges
node query.js c all                      # Checkpoint WAL
```

## Últimes versions
- **v3.56 (2026-08-25)**: zoom Ctrl +/- amb context d'aplicació — funciona també a l'editor expandit de Solució i la finestra de Tramitació
- **v3.55 (2026-08-25)**: visor "ajustar" limitat al 100% (mai ampliar → nitidesa); cerca amb %/_ literal (ESCAPE); recordatoris accepten dates ISO qualssevol; fora doble closeEvent a Tramitació; ajuda "Quant a" amb dreceres; llibreries al dia
- **v3.54 (2026-08-25)**: zoom global UI (Ctrl +/-/0 + menú Opcions, persistent); fix visor fullscreen (re-fit en redimensionar); fix lock obsolet (comprova si el PID és viu); fora processEvents del thread PDF; verify 49/49
- **v3.53 (2026-08-25)**: build PyInstaller sense dades privades ni codi font (spec `datas` només assets); backups BD via API sqlite3 (`Connection.backup`, snapshot consistent amb WAL viu); descripció oficial (tramitador jutjat civil); projecte publicat a GitHub
- **v3.52**: Fix ID nulls a Tramitació + protecció _get_tramit_id
- **v3.51**: Finestra edició tramit +50%, camp Info +50%
- **v3.5**: Finestra Tramitació +50%, edició usa update_tramit en lloc de merge
- **v3.44**: UPsert tramitació (evita duplicats amb consolidació d'info), pantalla d'alarmes cronològiques, eines manteniment BD (Rebuild/VACUUM/Purga/Stats)

 Versions anteriors: veure `CHANGELOG.md`

## Regles
- 4 espais indentació
- Sempre `verify_automatica.py` abans de build
- La versió viu a `config.py` (APP_VERSION); build.bat la llegeix per al README del dist
- **MAI** afegir `data/` ni `*.py` al bloc `datas` de `JMEJCat.spec` (hi van dades reals d'expedients)
- Backups de BD sempre via API sqlite3 (`Connection.backup`), mai `shutil.copy2` (WAL en calent)

## Funcionalitats v3.5+
- **UPsert Tramitació**: `tramitacio_database.py:upsert_tramit()` consolida info amb separador `--- Dades noves ---`
- **Alarmes**: `tramitacio_alarms.py` — finestra cronològica amb filtre passades/futurs
- **Manteniment BD**: Menú Ajuda → Manteniment BD Tramitació (REINDEX, ANALYZE, VACUUM, PURGE, STATS)
