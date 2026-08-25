# Changelog - JMEJCat

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
