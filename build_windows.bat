@echo off
:: ═══════════════════════════════════════════════════════════
:: Aura Writer — Script de Build Windows (PyInstaller)
:: ═══════════════════════════════════════════════════════════
title Aura Writer Build

echo [1/4] Verificando entorno Python...
python --version || (echo ERROR: Python no encontrado en PATH & pause & exit /b 1)

echo [2/4] Instalando dependencias de produccion...
pip install -r requirements.txt --quiet
pip install pyinstaller>=6.0 --quiet

echo [3/4] Compilando ejecutable con PyInstaller...
pyinstaller aura_writer.spec --noconfirm --clean

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
