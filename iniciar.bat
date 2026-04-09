@echo off
title CFC Store - Sistema de Ventas
color 1F
echo.
echo  ========================================
echo    CFC Store - Iniciando...
echo  ========================================
echo.

REM Verificar que Python esté instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Python no está instalado.
    echo  Descárgalo desde https://www.python.org/downloads/
    echo  Asegúrate de marcar "Add Python to PATH" al instalar.
    pause
    exit /b
)

REM Instalar dependencias si no están
echo  Verificando dependencias...
pip show flask >nul 2>&1
if errorlevel 1 (
    echo  Instalando Flask por primera vez...
    pip install flask --quiet
)

echo  Dependencias OK
echo.
echo  Abriendo CFC Store en el navegador...
echo  (Para cerrar, presiona Ctrl+C en esta ventana)
echo.

REM Ejecutar la app
python app.py

pause
