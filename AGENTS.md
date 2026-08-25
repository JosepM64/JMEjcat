# JMEJCat — Projecte

## Descripció
Notes estructurades portable i offline. Python 3.13 + PySide6 + SQLite.
- **Versió**: 3.52 | **Data**: 2026-07-19 | **Build**: ~117 MB

## Estructura
```
JMEJCat/
├── jmejcat.py              # Entry point
├── config.py               # Constants, APP_VERSION
├── backup_manager.py       # Backup logic
├── database.py             # Notes DB (hereda BaseDatabase)
├── tramitacio_database.py  # Tramitació DB (upsert, alarmes, manteniment)
├── tramitacio_alarms.py    # Finestra d'alarmes cronològiques
├── core/base_database.py   # BaseDatabase compartida
├── ui/                     # UI modular
├── pdf_exporter.py         # Export PDF
├── md_exporter.py          # Export Markdown
├── query.js                # Consultes externes (better-sqlite3)
├── CHANGELOG.md            # Historial de canvis
└── data/                   # BD portables + imatges
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

## Últimes 4 versions
- **v3.52**: Fix ID nulls a Tramitació + protecció _get_tramit_id
- **v3.51**: Finestra edició tramit +50%, camp Info +50%
- **v3.5**: Finestra Tramitació +50%, edició usa update_tramit en lloc de merge
- **v3.44**: UPsert tramitació (evita duplicats amb consolidació d'info), pantalla d'alarmes cronològiques, eines manteniment BD (Rebuild/VACUUM/Purga/Stats)
- **v3.43**: Fix editor expandit: closeEvent + autosave capturen canvis de l'expandit, unificació try_close
- **v3.42**: `busy_timeout` a query.js, `WAL` pragma només en escriptura (fix llegir amb JMEJCat obert)

 Versions anteriors: veure `CHANGELOG.md`

## Regles
- 4 espais indentació
- Imports amb `src.*`
- Sempre `verify_automatica.py` abans de build

## Funcionalitats v3.5+
- **UPsert Tramitació**: `tramitacio_database.py:upsert_tramit()` consolida info amb separador `--- Dades noves ---`
- **Alarmes**: `tramitacio_alarms.py` — finestra cronològica amb filtre passades/futurs
- **Manteniment BD**: Menú Ajuda → Manteniment BD Tramitació (REINDEX, ANALYZE, VACUUM, PURGE, STATS)
