@echo off
title Instalador e Inicio de Aura Writer
color 0b

echo ===================================================
echo            AURA WRITER - AUTO INSTALADOR
echo ===================================================
echo.

:: 1. Verificar si Python esta instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0c
    echo [ERROR] Python no esta instalado o no se agrego al PATH.
    echo Por favor instala Python desde https://www.python.org/
    echo y asegurate de marcar "Add Python to PATH".
    echo.
    pause
    exit /b
)

:: 2. Crear entorno virtual si no existe
if not exist "venv\Scripts\python.exe" (
    echo [1/3] Creando entorno virtual aislado (venv)...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] No se pudo crear el entorno virtual.
        pause
        exit /b
    )
)

:: 3. Instalar/Actualizar librerias
echo [2/3] Verificando dependencias necesarias...
.\venv\Scripts\pip install --disable-pip-version-check -r requirements.txt >nul 2>&1
if %errorlevel% neq 0 (
    echo Instalando paquetes por primera vez, esto puede tardar un minuto...
    .\venv\Scripts\pip install -r requirements.txt
)

:: 4. Lanzar la aplicacion
echo [3/3] Iniciando Aura Writer...
echo.
start "" ".\venv\Scripts\pythonw.exe" "launcher.py"

:: Si pythonw falla por alguna razon, fallback a python normal
if %errorlevel% neq 0 (
    .\venv\Scripts\python.exe launcher.py
)

exit
