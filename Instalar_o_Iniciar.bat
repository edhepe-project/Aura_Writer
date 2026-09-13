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

set "ES_PRIMERA_VEZ=0"

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

set "ES_PRIMERA_VEZ=1"
color 0e
echo [!] Python no detectado en este equipo.
echo [1/4] Descargando Python 3.12 oficial (64-bit)...
echo.

set "PY_INSTALLER=python_installer.exe"
set "PY_URL=https://www.python.org/ftp/python/3.12.8/python-3.12.8-amd64.exe"

:: Descargar instalador con barra de progreso en PowerShell
powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; $wc = New-Object System.Net.WebClient; $wc.DownloadFile('%PY_URL%', '%PY_INSTALLER%')"

if not exist "%PY_INSTALLER%" (
    color 0c
    echo [ERROR] No se pudo descargar Python automaticamente.
    echo Asegurate de estar conectado a internet.
    pause
    exit /b
)

echo [2/4] Instalando Python silenciosamente en este equipo...
echo     (Por favor espera un minuto mientras finaliza la instalacion)
start /wait "" "%PY_INSTALLER%" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0 Include_pip=1

del /f /q "%PY_INSTALLER%" >nul 2>&1
set "PATH=%LOCALAPPDATA%\Programs\Python\Python312;%LOCALAPPDATA%\Programs\Python\Python312\Scripts;%PATH%"

:PYTHON_OK
:: -----------------------------------------------------------------
:: 2. CREAR ENTORNO VIRTUAL
:: -----------------------------------------------------------------
if not exist "venv\Scripts\python.exe" (
    set "ES_PRIMERA_VEZ=1"
    echo.
    echo [3/4] Configurando entorno de trabajo seguro (venv)...
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
if not exist "venv\Lib\site-packages\PyQt6" (
    set "ES_PRIMERA_VEZ=1"
    echo [4/4] Instalando paquetes y librerias graficas de Aura Writer...
    echo     (Descargando PyQt6, Criptografia, etc. Esto toma 1-2 minutos...)
    echo.
    .\venv\Scripts\pip install -r requirements.txt
) else (
    echo Verificando componentes... [OK]
)

:: -----------------------------------------------------------------
:: 4. NOTIFICACION DE INSTALACION COMPLETADA
:: -----------------------------------------------------------------
if "%ES_PRIMERA_VEZ%"=="1" (
    color 0a
    echo.
    echo =========================================================
    echo   EXITO: INSTALACION COMPLETADA CORRECTAMENTE!
    echo =========================================================
    echo.
    echo Todo esta listo. Abriendo Aura Writer...
    
    :: Mostrar ventana emergente nativa de Windows avisando que termino
    powershell -Command "[System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms') | Out-Null; [System.Windows.Forms.MessageBox]::Show('La instalacion de Aura Writer ha finalizado con exito.`n`nSe abrira la aplicacion de inmediato.', 'Aura Writer', [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Information)"
)

:: -----------------------------------------------------------------
:: 5. INICIAR APLICACION
:: -----------------------------------------------------------------
echo Iniciando Aura Writer...
start "" ".\venv\Scripts\pythonw.exe" "launcher.py"
if %errorlevel% neq 0 (
    .\venv\Scripts\python.exe launcher.py
)

exit
