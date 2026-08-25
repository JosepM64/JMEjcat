@echo off
echo ========================================
echo    Tancar JMEJCat
echo ========================================
echo.

echo Buscant processos JMEJCat...

tasklist /FI "IMAGENAME eq JMEJCat.exe" 2>nul | findstr /I "JMEJCat.exe" >nul
if %ERRORLEVEL% EQU 0 (
    echo matant procés JMEJCat.exe...
    taskkill /IM JMEJCat.exe /F 2>nul
    echo OK - Procés aturat.
) else (
    echo Cap procés JMEJCat.exe trobat.
)

echo.
echo Esborrant lock file...
if exist "%USERPROFILE%\.jmejcat.lock" (
    del /q "%USERPROFILE%\.jmejcat.lock"
    echo OK - Lock file eliminat.
) else (
    echo Lock file no existeix.
)

echo.
echo ========================================
echo JMEJCat llest per executar.
echo ========================================
pause