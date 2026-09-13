@echo off
setlocal enabledelayedexpansion
title Aura Writer - Asistente de Instalacion y Ejecucion
color 0b

cd /d "%~dp0"

echo =========================================================
echo                AURA WRITER - AUTO INSTALADOR
echo       "Tu obra masiva, protegida y profesional"
echo =========================================================
echo.

:: -----------------------------------------------------------------
:: 1. VERIFICAR O AUTO-INSTALAR PYTHON
:: -----------------------------------------------------------------
python --version >nul 2>&1
if %errorlevel% equ 0 (
    goto :PYTHON_OK
)

py --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PY_CMD=py"
    goto :PYTHON_OK
)

echo [!] Python no esta instalado en este equipo.
echo [1/4] Descargando e instalando Python oficial silenciosamente...
echo     (Esto se hace una sola vez y tomara aproximadamente 1 minuto)
echo.

set "PY_INSTALLER=python_installer.exe"
set "PY_URL=https://www.python.org/ftp/python/3.12.8/python-3.12.8-amd64.exe"

:: Descargar el instalador oficial de Python con PowerShell
powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; (New-Object System.Net.WebClient).DownloadFile('%PY_URL%', '%PY_INSTALLER%')"

if not exist "%PY_INSTALLER%" (
    color 0c
    echo [ERROR] No se pudo descargar Python automaticamente.
    echo Asegurate de tener conexion a internet o instala Python 3.12 desde https://python.org
    pause
    exit /b
)

echo [2/4] Instalando Python con configuracion completa (PATH habilitado)...
start /wait "" "%PY_INSTALLER%" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0 Include_pip=1

:: Limpiar el archivo instalador temporal
del /f /q "%PY_INSTALLER%" >nul 2>&1

:: Actualizar la variable PATH en esta sesion de terminal
set "PATH=%LOCALAPPDATA%\Programs\Python\Python312;%LOCALAPPDATA%\Programs\Python\Python312\Scripts;%PATH%"

:: Verificar si ya responde Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0e
    echo [AVISO] Python se instalo. Si la ventana no inicia sola,
    echo por favor cierra y vuelve a hacer doble clic en este archivo.
    pause
)

:PYTHON_OK
:: -----------------------------------------------------------------
:: 2. CREAR ENTORNO VIRTUAL
:: -----------------------------------------------------------------
if not exist "venv\Scripts\python.exe" (
    echo.
    echo [3/4] Creando entorno virtual aislado (venv)...
    python -m venv venv
    if %errorlevel% neq 0 (
        color 0c
        echo [ERROR] No se pudo crear el entorno virtual.
        pause
        exit /b
    )
)

:: -----------------------------------------------------------------
:: 3. INSTALAR / VERIFICAR LIBRERIAS
:: -----------------------------------------------------------------
echo [4/4] Verificando dependencias necesarias...
.\venv\Scripts\pip install --disable-pip-version-check -r requirements.txt >nul 2>&1
if %errorlevel% neq 0 (
    echo Instalando paquetes de Aura Writer, por favor espera un momento...
    .\venv\Scripts\pip install -r requirements.txt
)

:: -----------------------------------------------------------------
:: 4. INICIAR APLICACION
:: -----------------------------------------------------------------
echo.
echo =========================================================
echo              Iniciando Aura Writer...
echo =========================================================
echo.

start "" ".\venv\Scripts\pythonw.exe" "launcher.py"
if %errorlevel% neq 0 (
    .\venv\Scripts\python.exe launcher.py
)

exit
