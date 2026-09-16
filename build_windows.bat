@echo off
:: ═══════════════════════════════════════════════════════════════════════════
:: Aura Writer — Script de Build Windows (PyInstaller + Inno Setup)
:: Genera el ejecutable y el instalador en un solo comando.
:: ═══════════════════════════════════════════════════════════════════════════
title Aura Writer Build

:: ── 1. Seleccionar Python (venv del proyecto si existe) ─────────────────
if exist "%~dp0venv\Scripts\python.exe" (
    echo [INFO] Usando Python del entorno virtual del proyecto...
    set PYTHON="%~dp0venv\Scripts\python.exe"
) else (
    echo [INFO] venv no encontrado, usando Python del PATH...
    set PYTHON=python
)

:: ── 2. Leer la versión desde src/version.py ─────────────────────────────
echo [1/5] Leyendo version de la aplicacion...
for /f "usebackq delims=" %%V in (`%PYTHON% -c "import sys; sys.path.insert(0,'src'); from version import __version__; print(__version__)"`) do set APP_VERSION=%%V
if "%APP_VERSION%"=="" (
    echo ERROR: No se pudo leer la version desde src/version.py
    pause & exit /b 1
)
echo       Version detectada: %APP_VERSION%

:: ── 3. Verificar entorno ────────────────────────────────────────────────
echo [2/5] Verificando entorno Python...
%PYTHON% --version || (echo ERROR: Python no encontrado & pause & exit /b 1)

echo       Instalando/actualizando dependencias...
%PYTHON% -m pip install -r requirements.txt --quiet
%PYTHON% -m pip install pyinstaller>=6.0 --quiet

:: ── 4. Compilar ejecutable con PyInstaller ──────────────────────────────
echo [3/5] Compilando ejecutable con PyInstaller...
%PYTHON% -m PyInstaller aura_writer.spec --noconfirm --clean

if errorlevel 1 (
    echo.
    echo ERROR: La compilacion PyInstaller fallo.
    pause & exit /b 1
)
echo       OK! Ejecutable: dist\AuraWriter.exe

:: ── 5. Buscar ISCC.exe (Inno Setup) ────────────────────────────────────
echo [4/5] Buscando compilador Inno Setup (ISCC.exe)...

set ISCC=
if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set ISCC="%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if not defined ISCC if exist "%USERPROFILE%\AppData\Local\Programs\Inno Setup 6\ISCC.exe" set ISCC="%USERPROFILE%\AppData\Local\Programs\Inno Setup 6\ISCC.exe"
if not defined ISCC if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set ISCC="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not defined ISCC if exist "C:\Program Files\Inno Setup 6\ISCC.exe" set ISCC="C:\Program Files\Inno Setup 6\ISCC.exe"

if not defined ISCC (
    echo.
    echo [AVISO] Inno Setup no encontrado. Saltando creacion del instalador.
    echo         Descargalo de: https://jrsoftware.org/isdl.php
    echo.
    goto :done
)
echo       ISCC encontrado: %ISCC%

:: ── 6. Compilar instalador con Inno Setup ───────────────────────────────
echo [5/5] Generando instalador con Inno Setup...
%ISCC% /DMyAppVersion="%APP_VERSION%" installer.iss

if errorlevel 1 (
    echo.
    echo ERROR: La compilacion del instalador fallo.
    pause & exit /b 1
)
echo       OK! Instalador: installer_output\AuraWriter_Setup_v%APP_VERSION%.exe

:done
echo.
echo ════════════════════════════════════════
echo  Build completado correctamente!
echo ════════════════════════════════════════
echo  Ejecutable:  dist\AuraWriter.exe
if defined ISCC (
echo  Instalador:  installer_output\AuraWriter_Setup_v%APP_VERSION%.exe
)
echo.
pause
