@echo off
setlocal
chcp 65001 >nul
title EEL CIBERSEGURIDAD - Analizador de Historial de Navegacion
color 0A
mode con: cols=118 lines=40 >nul 2>&1
cd /d "%~dp0"

cls
echo ======================================================================================================================
echo                                      EEL CIBERSEGURIDAD
echo                              ANALIZADOR DE HISTORIAL DE NAVEGACION // WINDOWS
echo ======================================================================================================================
echo.
echo [*] Verificando entorno Python...
echo.

where py >nul 2>&1
if %errorlevel%==0 (
    py -3 --version >nul 2>&1
    if %errorlevel%==0 (
        echo [OK] Python 3 detectado.
        timeout /t 1 >nul
        py -3 analizador_navegacion.py
        goto :fin
    )
)

where python >nul 2>&1
if %errorlevel%==0 (
    python --version >nul 2>&1
    if %errorlevel%==0 (
        echo [OK] Python 3 detectado.
        timeout /t 1 >nul
        python analizador_navegacion.py
        goto :fin
    )
)

echo [!] Python 3 no fue detectado.
echo.
echo El Analizador de Historial de Navegacion necesita Python 3 para ejecutarse.
echo No instala programas automaticamente ni modifica las protecciones de Windows.
echo.
choice /C SN /N /M "Desea abrir la pagina oficial de Python para Windows? [S/N]: "
if errorlevel 2 goto :sinpython
if errorlevel 1 start "" "https://www.python.org/downloads/windows/"

:sinpython
echo.
echo Instale Python 3 y vuelva a ejecutar INICIAR.bat.
pause

:fin
endlocal
