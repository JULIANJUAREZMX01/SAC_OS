@echo off
REM ═══════════════════════════════════════════════════════════════════════════════
REM  SAC - Sistema de Automatización de Consultas
REM  CEDIS Chedraui Cancún 427 - Región Sureste
REM
REM  EJECUTAR ESTE ARCHIVO PARA INICIAR SAC
REM  La instalación es completamente automática
REM ═══════════════════════════════════════════════════════════════════════════════

title SAC - Sistema de Automatización de Consultas

REM Cambiar al directorio del script
cd /d "%~dp0"

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ═══════════════════════════════════════════════════════════════════════════════
    echo  ERROR: Python no está instalado o no está en el PATH
    echo ═══════════════════════════════════════════════════════════════════════════════
    echo.
    echo  Por favor instale Python 3.8 o superior desde:
    echo  https://www.python.org/downloads/
    echo.
    echo  Asegúrese de marcar "Add Python to PATH" durante la instalación
    echo.
    pause
    exit /b 1
)

REM Ejecutar SAC
echo.
echo ═══════════════════════════════════════════════════════════════════════════════
echo  Iniciando SAC - Sistema de Automatización de Consultas
echo ═══════════════════════════════════════════════════════════════════════════════
echo.

python SAC.py

REM Mantener ventana abierta si hay error
if errorlevel 1 (
    echo.
    echo Presione cualquier tecla para cerrar...
    pause >nul
)
