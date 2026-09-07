# JMEJCat — Millores Definitives

**Versió analitzada:** 3.57 (25/08/2026)  
**Data del document:** 03/09/2026  
**Stack:** Python 3.13 + PySide6 6.11.2 + SQLite WAL + Pillow 12.3 + PyInstaller 6.22

## 1. Objectiu

Aquest document consolida les millores proposades per al projecte JMEJCat en un únic full de ruta tècnic, prioritzat i accionable.

Les propostes s'han revisat per eliminar duplicacions i conservar les millores que aporten més valor amb el menor impacte possible sobre el codi existent.

### Fonts analitzades

- Anàlisi del codi actual.
- `verify_automatica.py` — 49/49 comprovacions superades.
- `MILLORES_PROPOSADES.md`.
- `MELLORES_PROPOSTES.md`.

### Principi general d'implementació

> **Canvi mínim necessari.**

No es recomana una refactorització general del projecte. Les modificacions han de ser petites, independents i verificables.

Ordre de prioritat:

1. Correcció.
2. Seguretat i integritat.
3. Mantenibilitat.
4. Testabilitat.
5. Rendiment.
6. UX.
7. Distribució.

Evitar refactoritzacions àmplies si no són necessàries per resoldre un problema concret.

---

## 2. Estat actual i diagnòstic

JMEJCat presenta una arquitectura sòlida i funcional, adequada per a l'ús actual.

L'arquitectura principal gira al voltant de:

- `BaseDatabase`.
- `Database`.
- `TramitacioDatabase`.
- `MainWindow`.
- 8 mixins de la interfície.
- SQLite amb WAL i foreign keys.
- Sistema de còpies de seguretat amb `Connection.backup`.
- Build amb PyInstaller i carpeta `assets/`.

### Principals punts febles detectats

1. **Tests insuficients.**  
   `verify_automatica.py` és principalment un sistema de comprovacions basades en cerques de cadenes i no substitueix tests funcionals.

2. **Tipatge i lint incomplets.**  
   El projecte té tipatge parcial i encara hi ha incidències de Ruff, especialment `E501`.

3. **Seguretat de fils de SQLite.**  
   Existeix una connexió compartida amb `check_same_thread=False`, que pot provocar problemes de concurrència.

4. **Sistema de cerca limitat.**  
   Actualment es basa en `LIKE %` i principalment sobre el títol, sense FTS ni paginació.

5. **Integritat de dades.**  
   Bona part de la validació es fa a la interfície, però no existeixen suficients restriccions a nivell SQLite.

6. **Migracions.**  
   Existeix `DB_VERSION=1`, però no hi ha un sistema real de migracions versionades.

7. **Backups.**  
   El sistema actual és correcte, però es pot millorar la verificació abans d'una restauració i automatitzar backups periòdics.

8. **Imatges.**  
   La generació de miniatures és síncrona i hi ha un `LRU cache` definit però encara no implementat.

9. **UX.**  
   Es poden millorar arrossegar i deixar anar, Undo global, filtre "Avui", importació/exportació de Notes, etc.

10. **Distribució.**  
    Actualment no hi ha actualitzador, instal·lador estàndard ni signatura de codi.

---

## 3. Resum de prioritats

Les millores es divideixen en:

- **P0 — Obligatòries:** qualitat i correcció.
- **P1 — Recomanades:** robustesa, integritat i rendiment.
- **P2 — Opcionals:** UX avançada i distribució.

S'han identificat aproximadament **31 millores úniques**, després d'eliminar duplicacions entre les propostes originals.

### Estimació global

- **P0:** aproximadament 15–16 h.
- **P1:** aproximadament 15–20 h.
- **P2:** aproximadament 15–25 h.

Les estimacions són orientatives i poden variar segons el grau d'integració necessari.

---

# 4. P0 — Correcció i qualitat

## 4.1 Crear una suite real amb pytest

**Prioritat:** P0  
**Esforç estimat:** ~8 h

Crear una carpeta:

```text
tests/
```

### `test_database.py`

Cobrir com a mínim:

- `create_note`.
- `search_notes`.
- `get_all_notes`.
- `ESCAPE`.
- Cerca literal del caràcter `%`.
- Cerca literal del caràcter `_`.
- Cerca sense resultats.
- Caràcters especials.

Referència:

```text
database.py:135
```

### `test_tramitacio.py`

Cobrir:

- `upsert_tramit`.
- `_merge_info`.
- `_consolidate_duplicates`.

Referències:

```text
tramitacio_database.py:275
tramitacio_database.py:320
tramitacio_database.py:73
```

Casos mínims:

- `old == new`.
- Separadors duplicats.
- `new_info` buit.
- Duplicats.
- Actualització d'un registre existent.

### `test_backup.py`

Cobrir:

- `backup_database`.
- `cleanup_old_backups`.
- `verify_backup_file`.
- Restauració.
- Reobertura de la base de dades.
- Comparació del nombre de registres.

Referències:

```text
backup_manager.py:304
backup_manager.py:414
```

### Criteris d'acceptació

```bash
pytest -q
```

Objectiu de cobertura:

> **Més del 70 %** en:

```text
database*.py
backup_manager.py
tramitacio_database.py
```

---

## 4.2 Tipatge i lint progressius

**Prioritat:** P0  
**Esforç estimat:** ~3 h

Crear o completar `pyproject.toml`.

Configuració recomanada de Ruff:

```toml
[tool.ruff]
line-length = 100
target-version = "py313"

[tool.ruff.lint]
select = ["F", "E", "W", "UP", "I"]
```

Configuració inicial de mypy:

```toml
[tool.mypy]
python_version = "3.13"
strict = true
```

### Fitxers especialment rellevants

```text
core/base_database.py:19
ui_window.py:377
pdf_exporter.py:283
```

La correcció s'ha de fer progressivament.

**No** es recomana fer una gran refactorització de tipatge de tot el projecte d'una vegada.

---

## 4.3 Integració contínua amb GitHub Actions

**Prioritat:** P0  
**Esforç estimat:** ~4 h

Crear:

```text
.github/workflows/ci.yml
```

La CI hauria de:

1. Configurar Python 3.13.
2. Instal·lar dependències.
3. Instal·lar `pytest`, `ruff` i `mypy`.
4. Executar Ruff.
5. Executar mypy.
6. Executar pytest.
7. Executar `verify_automatica.py`.

Runner recomanat:

```text
windows-latest
```

---

## 4.4 Smoke test del build

**Prioritat:** P0  
**Esforç estimat:** ~2 h

Integrar una comprovació mínima del resultat de PyInstaller.

Comprovar:

```text
dist/JMEJCat/JMEJCat.exe
```

Idealment:

```bash
JMEJCat.exe --version
```

o implementar un smoke test equivalent que comprovi que l'aplicació arrenca correctament.

---

# 5. P1 — Robustesa de la base de dades

## 5.1 Thread-safety de SQLite

**Prioritat:** P1  
**Esforç estimat:** ~30 min

Actualment:

```text
core/base_database.py:19
```

utilitza:

```python
check_same_thread=False
```

i existeix una connexió compartida entre la UI i processos/QThreads.

Un exemple és:

```text
pdf_exporter.py:28
```

### Risc

Possibles errors:

```text
Database is locked
```

o problemes de concurrència.

### Solució

Afegir un:

```python
threading.Lock
```

per protegir les operacions sobre la connexió compartida.

Afegir també:

```sql
PRAGMA busy_timeout=5000;
```

Aquesta millora substitueix les propostes duplicades relatives a thread-safety de SQLite.

---

# 6. Integritat de dades

## 6.1 CHECK constraints

**Prioritat:** P1  
**Esforç estimat:** ~1 h

Afegir restriccions SQLite per evitar dades impossibles encara que s'afegeixin fora de la UI.

Exemples:

- Número entre 1 i 5 dígits.
- Any amb 4 dígits.
- Data en format `dd/MM/yyyy`.
- Títol màxim de 100 caràcters.
- Exemples màxim de 500 caràcters.

Fitxers implicats:

```text
database.py
tramitacio_database.py
```

### Important

Abans d'afegir les restriccions s'ha de comprovar que les dades existents compleixen les noves regles.

---

## 6.2 Sistema de migracions versionades

**Prioritat:** P1  
**Esforç estimat:** ~2 h

Actualment existeix:

```text
DB_VERSION=1
```

però no hi ha un sistema de migracions pròpiament dit.

Crear una taula:

```sql
schema_version
```

i implementar una funció:

```python
migrate()
```

a:

```text
core/base_database.py
```

L'objectiu és permetre evolucions futures de l'esquema sense haver de reconstruir manualment la base de dades.

---

## 6.3 Atomicitat de les operacions amb imatges

**Prioritat:** P1  
**Esforç estimat:** ~1 h

Actualment existeix una seqüència semblant a:

1. Eliminar registre de BD.
2. Eliminar fitxers.

Si falla l'operació de fitxers poden quedar fitxers orfes.

Referències:

```text
ui_window_images.py
database.py:180
image_manager.py:178
```

### Solució

Coordinar l'eliminació de:

- registre SQLite;
- fitxer físic;

o implementar una detecció periòdica de fitxers orfes i una neteja segura.

---

# 7. Backups

## 7.1 Verificar el backup abans de restaurar

**Prioritat:** P1  
**Esforç estimat:** ~1 h

Existeix:

```text
verify_backup_file()
```

a:

```text
backup_manager.py:304
```

Però `restore_backup()` a:

```text
backup_manager.py:93
```

actualment fa una còpia amb:

```python
shutil.copy2
```

sense verificar prèviament el backup.

### Flux recomanat

```text
Seleccionar backup
       ↓
Verificar backup
       ↓
Obrir/provar la BD
       ↓
Executar una consulta bàsica
       ↓
Comparar registres
       ↓
Restaurar
```

La verificació pot incloure:

```sql
COUNT(*)
```

sobre les taules principals.

---

## 7.2 Backup automàtic periòdic

**Prioritat:** P1  
**Esforç estimat:** ~1 h

El sistema actual ja disposa de:

- `Connection.backup`.
- Neteja de backups.
- `BACKUP_COUNT=5`.

La neteja dels backups ja està implementada i s'ha reduït el nombre a 5 el 03/09/2026.

Afegir, si es considera necessari, backups automàtics periòdics.

Exemple:

> Cada 30 minuts, però només si hi ha hagut modificacions.

Això evita generar còpies innecessàries.

---

## 7.3 Rotació dels logs

**Prioritat:** P1  
**Esforç estimat:** ~15 min

A:

```text
jmejcat.py:49
```

es creen fitxers del tipus:

```text
jmejcat_YYYYMMDD_HHMMSS.log
```

sense una política clara de retenció.

### Solució recomanada

Utilitzar:

```python
RotatingFileHandler
```

o una retenció temporal d'uns 30 dies.

Configuració orientativa:

```text
5 fitxers × 1 MB
```

---

# 8. Arquitectura i mantenibilitat

## 8.1 Centralitzar `TRAMIT_COLORS`

**Prioritat:** P1  
**Esforç estimat:** ~15 min

Actualment apareix en diferents fitxers:

```text
tramitacio_window.py:38
tramitacio_edit_dialog.py:32
tramitacio_alarms.py:213
```

Centralitzar-lo a:

```text
config.py
```

o:

```text
core/constants.py
```

---

## 8.2 Unificar `validate_date`

**Prioritat:** P1  
**Esforç estimat:** ~10 min

La validació de dates està duplicada a:

```text
tramitacio_edit_dialog.py:291
tramitacio_window.py
```

Crear una funció comuna:

```python
utils.validate_date_ddmmyyyy()
```

Utilitzar:

```python
QDate.fromString()
```

amb el fallback necessari.

---

## 8.3 Utilitzar `Path` de forma nativa

**Prioritat:** P1  
**Esforç estimat:** ~5 min

A:

```text
core/base_database.py:19
```

es converteix el camí a `str`.

Amb Python 3.11+ és possible passar un `Path` directament a `sqlite3.connect()`.

És una millora petita de neteja i consistència.

---

## 8.4 Fer més robust el hash d'imatges

**Prioritat:** P1  
**Esforç estimat:** ~20 min

Actualment el hash depèn del contingut i del timestamp.

A:

```text
image_manager.py:58
```

es recomana utilitzar:

```text
SHA256(conteningut)
```

Flux:

1. Calcular SHA-256.
2. Comprovar si ja existeix.
3. Si existeix, reutilitzar-lo o gestionar el duplicat.
4. Si hi ha conflicte de nom, generar un sufix.

---

# 9. Rendiment i escalabilitat

## 9.1 Paginació

**Prioritat:** P1  
**Esforç estimat:** ~1 h

Actualment es carreguen tots els registres:

```text
database.py:123
tramitacio_database.py:210
```

Afegir:

```sql
LIMIT
OFFSET
```

Per exemple:

```text
LIMIT 200
```

com a primera pàgina.

Això evita carregar milers de registres de cop.

---

## 9.2 Debounce de la cerca

**Prioritat:** P1  
**Esforç estimat:** ~10 min

Actualment:

```text
ui_window_notes.py:170
```

el `textChanged` provoca cerques contínues.

Utilitzar un:

```python
QTimer
```

amb:

```text
SEARCH_DELAY_MS=300
```

La cerca s'executaria uns 300 ms després de l'última pulsació.

---

## 9.3 FTS5

**Prioritat:** P1/P2 segons volum  
**Esforç estimat:** ~6 h

La cerca actual utilitza `LIKE %` i principalment el títol.

Referència:

```text
config.py:124
```

FTS5 permetria buscar de forma molt més eficient sobre:

- títol;
- petició;
- solució;
- exemples;
- informació.

Es podria crear un índex FTS5 amb triggers:

```text
AFTER INSERT
AFTER UPDATE
```

### Recomanació

Prioritzar FTS5 si el volum supera aproximadament:

```text
1.000 registres
```

Si el volum és petit:

> Primer implementar paginació + debounce + millores de la cerca actual.

---

## 9.4 Cache LRU de miniatures

**Prioritat:** P1/P2  
**Esforç estimat:** ~2 h

Existeix:

```text
IMAGE_CACHE_SIZE=50
```

però el cache no està implementat.

Implementar un LRU mitjançant:

```python
functools.lru_cache
```

o:

```text
cachetools.LRUCache
```

sobre la càrrega de miniatures.

Fitxers:

```text
image_gallery.py
image_manager.py
```

---

## 9.5 Lazy loading i QListView

**Prioritat:** P1/P2  
**Esforç estimat:** ~3 h

`QListWidget` pot degradar el rendiment amb un nombre elevat d'elements.

Referències:

```text
ui_window.py:174
ui_window_notes.py
```

Migració progressiva cap a:

```text
QListView
QAbstractListModel
fetchMore
```

### Important

No fer aquesta migració fins que:

- els tests siguin suficients;
- la necessitat de rendiment estigui demostrada.

És una modificació estructural.

---

# 10. P2 — Millores d'UX

## 10.1 Undo/Redo global

**Prioritat:** P2  
**Esforç estimat:** ~4 h

Utilitzar:

```python
QUndoStack
```

per permetre desfer operacions com:

- eliminar nota;
- moure imatge;
- canviar color;
- actualitzar tramitació.

---

## 10.2 Drag & Drop d'imatges

**Prioritat:** P2  
**Esforç estimat:** ~2 h

Permetre arrossegar fitxers directament sobre:

```text
ImageGallery
```

per incorporar-los.

---

## 10.3 Filtre "Avui"

**Prioritat:** P2  
**Esforç estimat:** ~30 min

Afegir un filtre a Tramitació basat en:

```python
QDate.currentDate()
```

per mostrar només les actuacions del dia.

---

## 10.4 Cerca global

**Prioritat:** P2  
**Esforç estimat:** ~3 h

Afegir una cerca que englobi:

- Notes.
- Tramitació.

Dreceres proposades:

```text
Ctrl+Shift+F
```

Els resultats podrien estar agrupats per tipus.

---

## 10.5 Importació/exportació CSV de Notes

**Prioritat:** P2  
**Esforç estimat:** ~2 h

Prendre com a referència l'exportació CSV existent a:

```text
tramitacio_window.py:449
```

Utilitzar:

```text
QUOTE_ALL
utf-8-sig
```

per facilitar compatibilitat amb Excel i Windows.

---

## 10.6 Dark Mode

**Prioritat:** P2  
**Esforç estimat:** ~1 h

Utilitzar:

```python
QPalette
```

i guardar la preferència amb:

```python
QSettings
```

---

## 10.7 Exportació XLSX

**Prioritat:** P2  
**Esforç estimat:** ~2 h

Utilitzar:

```text
openpyxl
```

per exportar:

- Notes.
- Tramitació.

---

# 11. P2 — Distribució

## 11.1 Signatura de codi

**Prioritat:** P2  
**Esforç estimat:** ~2 h + cost del certificat

Actualment:

```text
JMEJCat.spec
```

conté:

```python
codesign_identity=None
```

La signatura de codi pot reduir avisos de SmartScreen i millorar la confiança de l'usuari.

Cost orientatiu del certificat:

```text
~300–400 €/any
```

### Recomanació

No és prioritari si JMEJCat es distribueix únicament en un entorn controlat.

---

## 11.2 Auto-Updater

**Prioritat:** P2  
**Esforç estimat:** ~8 h

Comparar:

```text
APP_VERSION
```

amb les versions publicades a GitHub Releases.

Flux inicial recomanat:

```text
Nova versió disponible
        ↓
Notificar l'usuari
        ↓
Descarregar
        ↓
Instal·lar
```

### Recomanació

Començar per un sistema de **notificació**, no per una actualització completament automàtica.

---

## 11.3 Instal·lador MSI / Inno Setup

**Prioritat:** P2  
**Esforç estimat:** ~4 h

Actualment el build genera:

```text
dist/JMEJCat/
```

en format `onedir`.

Un instal·lador estàndard permetria:

- Menú Inici.
- Desinstal·lació.
- Associació amb `.jmejcat`.
- Dreceres.
- Instal·lació estàndard.

Es pot valorar:

```text
MSI
```

o:

```text
Inno Setup
```

---

# 12. SQLCipher

**Prioritat:** Opcional / P0-P1 segons requisits de seguretat  
**Esforç estimat:** ~4 h

Actualment:

```text
data/jmejcat.db
data/tramitacio.db
```

són bases de dades SQLite en text pla.

SQLCipher permetria xifratge de la base de dades en repòs.

### Recomanació

Integrar-ho darrere d'una opció experimental:

```text
EXPERIMENTAL_FEATURES
```

a:

```text
config.py:141
```

El xifratge podria utilitzar PBKDF2 i SQLCipher.

### Decisió important

Si les dades contenen informació personal o judicial que requereix protecció en repòs:

> Promoure SQLCipher a P0/P1.

Si no existeix aquest requisit:

> Mantenir-lo com a opcional.

No introduir SQLCipher sense un requisit de seguretat clar i un pla de compatibilitat/migració.

---

# 13. Decisions pendents

Abans d'implementar algunes de les millores P2/P1 cal decidir:

### SQLCipher

> Es requereix xifratge de les bases de dades en repòs?

### FTS5

> S'espera superar els 1.000 registres?

### Updater

> Es vol només notificació o actualització automàtica?

### Instal·lador

> Es prefereix aplicació portable o instal·lador?

### Signatura

> La distribució externa justifica el cost del certificat?

---

# 14. Pla d'implementació recomanat

## Fase 1 — Qualitat

Implementar primer:

1. pytest.
2. Ruff.
3. mypy.
4. GitHub Actions.
5. Smoke test del build.
6. Centralitzar `TRAMIT_COLORS`.
7. Unificar `validate_date`.
8. Utilitzar `Path`.
9. Millorar hash d'imatges.
10. Rotació dels logs.

---

## Fase 2 — Nucli robust

Després:

1. Thread-safety de SQLite.
2. CHECK constraints.
3. Migracions.
4. Atomicitat d'imatges.
5. Verificació de backups abans de restaurar.
6. Backup automàtic periòdic.

---

## Fase 3 — Rendiment base

A continuació:

1. Paginació.
2. Debounce de cerca.
3. Filtre "Avui".
4. Drag & Drop.
5. CSV de Notes.

---

## Fase 4 — Escalabilitat

Només si les mètriques ho justifiquen:

1. FTS5.
2. Cache LRU.
3. QListView / Lazy Loading.
4. Undo/Redo.
5. Cerca global.

Mesurar:

- nombre de Notes;
- nombre de Tramitacions;
- temps de cerca;
- temps de càrrega de la UI;
- memòria utilitzada.

---

## Fase 5 — UX i distribució

Finalment:

1. Dark Mode.
2. XLSX.
3. Signatura de codi.
4. Auto-Updater.
5. Instal·lador.

---

# 15. Mètriques objectiu

| Mètrica | Actual | Objectiu |
|---|---:|---:|
| Build onedir | ~117 MB | <100 MB |
| Arrencada desenvolupament | ~2–3 s | <1,5 s |
| Arrencada EXE | ~4–6 s | <3 s |
| `verify_automatica.py` | 49 checks | 49+ |
| Cobertura core | 0 % | >70 % |
| Duplicacions conegudes | 5 | 0 |
| Cerca | `LIKE` / títol | FTS5 quan es justifiqui |
| Thread-safe DB | No | Sí |
| Backups | 5/tipus | 5+ amb verificació |
| CI | No | Sí |
| Migracions | No | Sí |

### Nota

Els temps d'arrencada i la mida del build són **objectius de rendiment**, no requisits funcionals.

No s'ha de sacrificar estabilitat per assolir-los.

---

# 16. Comandes de verificació

### Verificació automàtica

```bash
python verify_automatica.py
```

### Ruff

```bash
C:\Users\JM\miniconda3\envs\jm_pyside_313\python.exe -m ruff check --select F,E,W --line-length 100 .
```

### mypy

```bash
C:\Users\JM\miniconda3\envs\jm_pyside_313\python.exe -m mypy .
```

### pytest

```bash
C:\Users\JM\miniconda3\envs\jm_pyside_313\python.exe -m pytest -q
```

### Consultes existents

```bash
node query.js s
```

```bash
node query.js t "" "" 50
```

### Build

```bash
build.bat
```

---

# 17. Criteris de merge

Una modificació es considera preparada per integrar a `main` quan compleixi:

```text
pytest                → PASS (obligatori)
Ruff                  → PASS (obligatori)
mypy                  → PASS (obligatori)
build.bat             → PASS (obligatori)
verify_automatica.py  → PASS (informatiu; no bloqueja merge
                      fins que pytest arribi a cobertura >70%)
```

> **Nota:** `verify_automatica.py` només realitza cerques de cadenes (§2, punt 1),
> per tant no és una garantia funcional real. Un cop la suite `pytest`
> superi el 70% de cobertura als mòduls core (`database*.py`,
> `tramitacio_database.py`, `backup_manager.py`), `pytest` passa a ser
> l'únic criteri de tests i `verify_automatica.py` es rebaixa a smoke test
> opcional.

Quan una millora no sigui aplicable a algun d'aquests criteris, s'ha de justificar explícitament.

---

# 18. Referències ràpides del projecte

| Component | Fitxer / referència | Funció |
|---|---|---|
| Entry point | `jmejcat.py:1` | Lock, logging, excepthook |
| Base DB | `core/base_database.py:13` | WAL, FK, connexió |
| Notes DB | `database.py:17` | CRUD, cerca, ESCAPE |
| Tramitació DB | `tramitacio_database.py:18` | UPSERT, alarmes, manteniment |
| MainWindow | `ui_window.py:58` | 8 mixins, zoom, close |
| Backup | `backup_manager.py:20` | `Connection.backup`, cleanup |
| Imatges | `image_manager.py:42` | Hash, miniatures, ús de disc |
| Tramitació UI | `tramitacio_window.py:50` | Grid, colors, PDF, CSV |
| Config | `config.py:1` | Constants, paths, versions |
| Verificació | `verify_automatica.py:1` | 49 comprovacions |
| Build | `build.bat:1` | PyInstaller, conda, cleanup |
| Spec | `JMEJCat.spec:1` | Exclusions, UPX, optimize |

---

# 19. Principis de desenvolupament

1. No fer refactoritzacions innecessàries.
2. No canviar APIs si no és imprescindible.
3. Escriure els tests abans o conjuntament amb els canvis.
4. Fer canvis petits i independents.
5. Executar `verify_automatica.py`, Ruff, mypy i pytest abans del merge.
6. No afegir dependències noves sense justificació.
7. Mesurar abans d'optimitzar.
8. Prioritzar estabilitat davant de funcionalitats secundàries.
9. Mantenir la compatibilitat amb les bases de dades existents.
10. Fer que cada PR sigui clar, petit i fàcil de verificar.

---

# 20. Resum final de prioritats

## P0 — Fer

### Qualitat

- pytest.
- Ruff.
- mypy.
- GitHub Actions.
- Smoke test del build.

## P1 — Recomanat

### Robustesa

- Thread-safety de SQLite.
- CHECK constraints.
- Migracions.
- Atomicitat d'imatges.
- Verificació dels backups.
- Backup automàtic.

### Arquitectura

- Centralitzar `TRAMIT_COLORS`.
- Unificar `validate_date`.
- `Path` natiu.
- Hash SHA-256 d'imatges.

### Rendiment

- Paginació.
- Debounce de cerca.
- FTS5 quan el volum ho justifiqui.
- Cache LRU.
- Lazy loading quan sigui necessari.

## P2 — Quan hi hagi temps

### UX

- Undo/Redo.
- Drag & Drop.
- Filtre Avui.
- Cerca global.
- CSV Notes.
- Dark Mode.
- XLSX.

### Distribució

- Signatura.
- Auto-Updater.
- Instal·lador.

## Opcional

- SQLCipher.
- FTS5 si el volum actual no ho justifica.
- QListView/Lazy Loading si les mètriques no mostren cap problema.

---

# 21. Estat actual

**Versió:** 3.57  
**Última verificació:** 03/09/2026

### Actualment OK

- `verify_automatica.py`: **49/49 PASS**.
- Sistema de backups funcional.
- Neteja de backups implementada.
- Nombre de backups: **5 per tipus**.
- Build PyInstaller funcional.
- Build aproximat: **117 MB onedir**.

### Pendents

- pytest.
- CI.
- Thread-safety SQLite.
- CHECK constraints.
- Migracions.
- FTS5.
- Cache LRU.
- Millores UX.
- Distribució avançada.

---

# 22. Informació del projecte

**Projecte:** JMEJCat  
**Responsable:** Josep Maria Tapia Estaragues  
**Versió analitzada:** 3.57  
**Llicència:** LGPL v3  
**Branca:** `main`

**Repositori:**  
https://github.com/JosepM64/JMEjcat

---

# 23. Conclusió

JMEJCat es troba en un estat funcional i prou sòlid per continuar el desenvolupament sense una reestructuració general.

La prioritat no ha de ser afegir moltes funcionalitats noves immediatament, sinó consolidar primer:

1. Tests reals.
2. Qualitat de codi.
3. CI.
4. Robustesa de SQLite.
5. Integritat de dades.
6. Migracions.
7. Backups verificables.

Un cop aquestes bases estiguin resoltes, les millores de rendiment i UX es poden implementar progressivament en funció de les necessitats reals.

La regla principal del projecte ha de ser:

> **Estabilitat primer, canvis petits, tests sempre i optimització només quan les mètriques demostrin que és necessària.**

Aquest document constitueix el **full de ruta tècnic definitiu de millores de JMEJCat**, amb les propostes duplicades consolidades i ordenades segons prioritat, risc i esforç.
