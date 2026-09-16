@echo off
:: ═══════════════════════════════════════════════════════════
:: Aura Writer — Script de Build Windows (PyInstaller)
:: ═══════════════════════════════════════════════════════════
title Aura Writer Build

:: Usar el Python del venv del proyecto si existe (tiene todas las deps)
:: Si no existe, intentar con el Python del PATH (puede fallar si faltan módulos)
if exist "%~dp0venv\Scripts\python.exe" (
    echo [INFO] Usando Python del entorno virtual del proyecto...
    set PYTHON="%~dp0venv\Scripts\python.exe"
) else (
    echo [INFO] venv no encontrado, usando Python del PATH...
    set PYTHON=python
)

echo [1/4] Verificando entorno Python...
%PYTHON% --version || (echo ERROR: Python no encontrado & pause & exit /b 1)

echo [2/4] Instalando dependencias de produccion...
%PYTHON% -m pip install -r requirements.txt --quiet
%PYTHON% -m pip install pyinstaller>=6.0 --quiet

echo [3/4] Compilando ejecutable con PyInstaller...
%PYTHON% -m PyInstaller aura_writer.spec --noconfirm --clean

if errorlevel 1 (
    echo.
    echo ERROR: La compilacion fallo.
    pause
    exit /b 1
)

echo [4/4] Listo!
echo.
echo El ejecutable se encuentra en:
echo   dist\AuraWriter.exe
echo.
pause
