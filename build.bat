@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ========================================
echo    JMEJCat - Build con PyInstaller
echo ========================================
echo.

REM Tancar processos preexistents
echo Buscant procesos JMEJCat...
tasklist /FI "IMAGENAME eq JMEJCat.exe" 2>nul | findstr /I "JMEJCat.exe" >nul
if %ERRORLEVEL% EQU 0 (
    echo matant procés JMEJCat.exe...
    taskkill /IM JMEJCat.exe /F 2>nul
    echo OK - Procés aturat.
) else (
    echo Cap procés JMEJCat.exe trobat.
)
echo Esborrant lock file...
if exist "%USERPROFILE%\.jmejcat.lock" (
    del /q "%USERPROFILE%\.jmejcat.lock"
    echo OK - Lock file eliminat.
) else (
    echo Lock file no existeix.
)
echo.

REM Verificar que estamos en el directorio correcto
if not exist "jmejcat.py" (
    echo ERROR: No se encuentra jmejcat.py
    pause
    exit /b 1
)

REM Detectar conda, usar entorno jm_pyside_313
set CONDA_PATH=
for /f "tokens=*" %%i in ('where.exe conda 2^>nul') do (
    set "CONDA_PATH=%%i"
    goto :found_conda
)

:found_conda
if "%CONDA_PATH%"=="" (
    echo ERROR: conda no encontrado. Instala Miniconda3 y ejecuta: conda init
    pause
    exit /b 1
)

for /f "tokens=*" %%b in ('"%CONDA_PATH%" info --base 2^>nul') do set "CONDA_BASE=%%b"
if "%CONDA_BASE%"=="" (
    echo [WARNING] conda info --base ha fallat. Usant ruta per defecte.
    set "CONDA_BASE=C:\Users\JM\miniconda3"
) else (
    set "CONDA_PATH=%CONDA_BASE%\Scripts\conda.exe"
)

set CONDA_ENV=jm_pyside_313
echo [OK] Conda detectado: %CONDA_BASE%
echo -    Entorno: %CONDA_ENV%

REM Localitzar Python de l'entorn directament
set "CONDA_PYTHON=%CONDA_BASE%\envs\%CONDA_ENV%\python.exe"
if not exist "%CONDA_PYTHON%" (
    echo ERROR: No es troba Python a %CONDA_PYTHON%
    pause
    exit /b 1
)
echo [OK] Python: %CONDA_PYTHON%

REM Verificar entorno
if not exist "%CONDA_BASE%\envs\%CONDA_ENV%\python.exe" (
    echo ERROR: El entorno %CONDA_ENV% no existe a %CONDA_BASE%\envs\%CONDA_ENV%.
    echo Ejecuta: conda create -n %CONDA_ENV% python=3.13
    pause
    exit /b 1
)

REM Verificar Python 3.13
for /f "delims=" %%v in ('""%CONDA_PYTHON%" --version" 2^>^&1') do set PYTHON_VERSION=%%v
echo [INFO] %PYTHON_VERSION%
echo %PYTHON_VERSION% | findstr /r "^Python 3\.13\." >nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Se requiere Python 3.13.x - %PYTHON_VERSION%
    pause
    exit /b 1
)

REM Verificar dependencias
echo.
echo Verificando dependencias...

REM Verificar PySide6
"%CONDA_PYTHON%" -c "from PySide6.QtCore import qVersion; print(qVersion())" >"%TEMP%\jmejcat_pkg.txt" 2>nul
if %ERRORLEVEL% neq 0 (
    echo ERROR: PySide6 no instalado. Ejecuta: pip install PySide6
    pause
    exit /b 1
)
set /p PYSIDE_VER=<"%TEMP%\jmejcat_pkg.txt"
echo [OK] PySide6 %PYSIDE_VER%

REM Verificar Pillow
"%CONDA_PYTHON%" -c "import PIL; print(PIL.__version__)" >"%TEMP%\jmejcat_pkg.txt" 2>nul
if %ERRORLEVEL% neq 0 (
    echo [WARNING] Pillow no instalado. Miniaturas no funcionaran.
) else (
    set /p PILLOW_VER=<"%TEMP%\jmejcat_pkg.txt"
    echo [OK] Pillow %PILLOW_VER%
)

REM Verificar PyInstaller
"%CONDA_PYTHON%" -c "import PyInstaller; print(PyInstaller.__version__)" >"%TEMP%\jmejcat_pkg.txt" 2>nul
if %ERRORLEVEL% neq 0 (
    echo ERROR: PyInstaller no disponible. Ejecuta: pip install PyInstaller
    pause
    exit /b 1
)
set /p PYINST_VER=<"%TEMP%\jmejcat_pkg.txt"
echo [OK] PyInstaller %PYINST_VER%

REM Verificar Ruff
"%CONDA_PYTHON%" -c "import ruff" 2>nul
if %ERRORLEVEL% neq 0 (
    echo [WARNING] Ruff no instalado. Se omite analisis.
    goto :ruff_done
)
echo [OK] Ruff disponible
echo Ejecutando analisis de codigo con Ruff (opcional)...
"%CONDA_PYTHON%" -m ruff check --select F,E,W --line-length 100 --exclude backups,dist,fix_*.py,restore_functions.py --output-format=concise . 2>nul
echo [OK] Analisis completado.
:ruff_done

REM Crear estructura de directorios
echo.
echo Creando estructura de directorios...
if not exist "data" mkdir data
if not exist "data\images" mkdir data\images
if not exist "data\images\original" mkdir data\images\original
if not exist "data\images\thumbs" mkdir data\images\thumbs
if not exist "data\backups" mkdir data\backups
if not exist "assets" mkdir assets

REM Verificar icono
set ICON_OPTION=
if exist "assets\icon.ico" (
    set ICON_OPTION=--icon=assets/icon.ico
    echo Icono 'icon.ico' encontrado.
) else if exist "assets\JMEJCAT.ico" (
    set ICON_OPTION=--icon=assets/JMEJCAT.ico
    echo Icono 'JMEJCAT.ico' encontrado.
) else (
    echo Icono no encontrado, usando predeterminado.
)

REM Limpiar builds anteriores
echo.
echo Limpiando builds anteriores...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist

REM Ejecutar PyInstaller
echo.
echo Ejecutando PyInstaller (esto puede tardar 2-4 minutos)...
"%CONDA_PYTHON%" -m PyInstaller --noconfirm --clean JMEJCat.spec

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo BUILD FALLIDO
    pause
    exit /b 1
)

REM Limpiar PySide6 innecesarios
echo.
echo Limpiando archivos innecesarios...
if exist "dist\JMEJCat\_internal\PySide6" (
    if exist "dist\JMEJCat\_internal\PySide6\*.exe" del /q "dist\JMEJCat\_internal\PySide6\*.exe"
    if exist "dist\JMEJCat\_internal\PySide6\scripts" rmdir /s /q "dist\JMEJCat\_internal\PySide6\scripts"
    if exist "dist\JMEJCat\_internal\PySide6\doc" rmdir /s /q "dist\JMEJCat\_internal\PySide6\doc"
    if exist "dist\JMEJCat\_internal\PySide6\include" rmdir /s /q "dist\JMEJCat\_internal\PySide6\include"
    if exist "dist\JMEJCat\_internal\PySide6\lib" rmdir /s /q "dist\JMEJCat\_internal\PySide6\lib"
    if exist "dist\JMEJCat\_internal\PySide6\support" rmdir /s /q "dist\JMEJCat\_internal\PySide6\support"
    for /d %%d in (dist\JMEJCat\_internal\PySide6\Qt3D*) do rmdir /s /q "%%d"
    for /d %%d in (dist\JMEJCat\_internal\PySide6\QtBluetooth*) do rmdir /s /q "%%d"
    for /d %%d in (dist\JMEJCat\_internal\PySide6\QtCharts*) do rmdir /s /q "%%d"
    for /d %%d in (dist\JMEJCat\_internal\PySide6\QtDBus*) do rmdir /s /q "%%d"
    for /d %%d in (dist\JMEJCat\_internal\PySide6\QtDesigner*) do rmdir /s /q "%%d"
    for /d %%d in (dist\JMEJCat\_internal\PySide6\QtHelp*) do rmdir /s /q "%%d"
    for /d %%d in (dist\JMEJCat\_internal\PySide6\QtLocation*) do rmdir /s /q "%%d"
    for /d %%d in (dist\JMEJCat\_internal\PySide6\QtMultimedia*) do rmdir /s /q "%%d"
    for /d %%d in (dist\JMEJCat\_internal\PySide6\QtNetwork*) do rmdir /s /q "%%d"
    for /d %%d in (dist\JMEJCat\_internal\PySide6\QtNfc*) do rmdir /s /q "%%d"
    for /d %%d in (dist\JMEJCat\_internal\PySide6\QtPositioning*) do rmdir /s /q "%%d"
    for /d %%d in (dist\JMEJCat\_internal\PySide6\QtQuick3D*) do rmdir /s /q "%%d"
    for /d %%d in (dist\JMEJCat\_internal\PySide6\QtSensors*) do rmdir /s /q "%%d"
    for /d %%d in (dist\JMEJCat\_internal\PySide6\QtSerialPort*) do rmdir /s /q "%%d"
    for /d %%d in (dist\JMEJCat\_internal\PySide6\QtStateMachine*) do rmdir /s /q "%%d"
    for /d %%d in (dist\JMEJCat\_internal\PySide6\QtTextToSpeech*) do rmdir /s /q "%%d"
    for /d %%d in (dist\JMEJCat\_internal\PySide6\QtWebEngine*) do rmdir /s /q "%%d"
    for /d %%d in (dist\JMEJCat\_internal\PySide6\QtWebSockets*) do rmdir /s /q "%%d"
    for /d %%d in (dist\JMEJCat\_internal\PySide6\QtWebView*) do rmdir /s /q "%%d"
    echo Limpieza completada.
)

REM README de distribución
echo.
echo Creando README para distribucion...
for /f "tokens=1,2 delims== " %%a in ('findstr /b "APP_VERSION" config.py') do set "APP_VER=%%b"
set "APP_VER=%APP_VER:"=%"
>  "dist\JMEJCat\README.txt" echo JMEJCat v%APP_VER% - Aplicacion Portable
>> "dist\JMEJCat\README.txt" echo ========================================
>> "dist\JMEJCat\README.txt" echo.
>> "dist\JMEJCat\README.txt" echo Para usar JMEJCat:
>> "dist\JMEJCat\README.txt" echo 1. Ejecuta JMEJCat.exe
>> "dist\JMEJCat\README.txt" echo 2. Todos tus datos se guardan en la carpeta data/
>> "dist\JMEJCat\README.txt" echo 3. Para mover la aplicacion, copia toda la carpeta
>> "dist\JMEJCat\README.txt" echo.
>> "dist\JMEJCat\README.txt" echo Caracteristicas:
>> "dist\JMEJCat\README.txt" echo - Notas estructuradas (Titulo, Peticion, Solucion, Ejemplos)
>> "dist\JMEJCat\README.txt" echo - Formato de texto enriquecido (Ctrl+B, Ctrl+I, Ctrl+U, Ctrl+T)
>> "dist\JMEJCat\README.txt" echo - Imagenes con miniaturas (Ctrl+I para insertar)
>> "dist\JMEJCat\README.txt" echo - Calculadora de despeses integrada
>> "dist\JMEJCat\README.txt" echo - Modulo Tramitacion con upsert (evita duplicados)
>> "dist\JMEJCat\README.txt" echo - Pantalla de alarmes cronologicas
>> "dist\JMEJCat\README.txt" echo - Herramientas de mantenimiento BD (Rebuild, VACUUM, etc.)
>> "dist\JMEJCat\README.txt" echo - Exportacio a PDF
>> "dist\JMEJCat\README.txt" echo - Busqueda instantanea (Ctrl+F)
>> "dist\JMEJCat\README.txt" echo - Auto-backup al cerrar
>> "dist\JMEJCat\README.txt" echo.
>> "dist\JMEJCat\README.txt" echo Atajos de teclado:
>> "dist\JMEJCat\README.txt" echo Ctrl+N: Nueva nota
>> "dist\JMEJCat\README.txt" echo Ctrl+S: Guardar nota
>> "dist\JMEJCat\README.txt" echo Ctrl+F: Buscar
>> "dist\JMEJCat\README.txt" echo Ctrl+I: Insertar imagen
>> "dist\JMEJCat\README.txt" echo Ctrl+Q: Salir
>> "dist\JMEJCat\README.txt" echo.
>> "dist\JMEJCat\README.txt" echo Licencia: LGPL v3
>> "dist\JMEJCat\README.txt" echo.
>> "dist\JMEJCat\README.txt" echo ========================================
>> "dist\JMEJCat\README.txt" echo Solucion de problemas:
>> "dist\JMEJCat\README.txt" echo ========================================
>> "dist\JMEJCat\README.txt" echo.
>> "dist\JMEJCat\README.txt" echo Si la aplicacion no inicia:
>> "dist\JMEJCat\README.txt" echo - Verifica que tienes Visual C++ Redistributable 2015-2022
>> "dist\JMEJCat\README.txt" echo - Revisa los archivos de log en la carpeta logs/
>> "dist\JMEJCat\README.txt" echo - Si hay un archivo jmejcat_crash.log, envialo al desarrollador
>> "dist\JMEJCat\README.txt" echo.
>> "dist\JMEJCat\README.txt" echo Descargar VC++ Redistributable:
>> "dist\JMEJCat\README.txt" echo https://aka.ms/vs/17/release/vc_redist.x64.exe

if exist "TROUBLESHOOTING.txt" (
    copy "TROUBLESHOOTING.txt" "dist\JMEJCat\TROUBLESHOOTING.txt" /Y >nul
)
echo README creado.

echo.
echo ========================================
echo BUILD EXITOSO
echo ========================================
echo.
echo Carpeta generada: dist\JMEJCat\
echo.
echo Prueba ejecutando: dist\JMEJCat\JMEJCat.exe
echo.
exit /b 0
