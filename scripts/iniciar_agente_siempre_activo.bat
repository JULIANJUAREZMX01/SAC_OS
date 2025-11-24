@echo off
REM ═══════════════════════════════════════════════════════════════════════
REM INICIAR AGENTE SAC SIEMPRE ACTIVO - WINDOWS BATCH
REM Sistema de Automatización de Consultas - CEDIS Cancún 427
REM ═══════════════════════════════════════════════════════════════════════
REM
REM Este script inicia el Agente SAC Siempre Activo en Windows.
REM Puede ser agregado a Startup para iniciar automáticamente.
REM
REM INSTALACIÓN EN STARTUP:
REM 1. Crear acceso directo a este archivo
REM 2. Mover a: C:\Users\<usuario>\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup
REM
REM ═══════════════════════════════════════════════════════════════════════

setlocal enabledelayedexpansion

REM Cambiar a directorio del proyecto
cd /d "%~dp0\.."

REM Verificar que existe el proyecto SAC
if not exist "config.py" (
    echo ❌ Error: No se encontró config.py
    echo Asegúrate de ejecutar este script desde el directorio raíz del proyecto SAC
    pause
    exit /b 1
)

echo.
echo ╔═══════════════════════════════════════════════════════════════════════╗
echo ║                                                                       ║
echo ║     🤖 AGENTE SAC SIEMPRE ACTIVO - INICIALIZANDO...                ║
echo ║                                                                       ║
echo ║     Sistema de Automatización de Consultas                          ║
echo ║     CEDIS Cancún 427 - Tiendas Chedraui                            ║
echo ║                                                                       ║
echo ╚═══════════════════════════════════════════════════════════════════════╝
echo.

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: Python no está instalado o no está en PATH
    echo    Descarga Python desde https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Python detectado
echo.

REM Crear directorio de logs si no existe
if not exist "output\logs" mkdir output\logs

REM Verificar argumentos
if "%1"=="" (
    echo 📊 Iniciando en modo interactivo...
    echo.
    python scripts\iniciar_agente_siempre_activo.py
) else if "%1"=="--daemon" (
    echo 🚀 Iniciando como servicio en background...
    start /B python scripts\iniciar_agente_siempre_activo.py --daemon
    echo ✅ Agente iniciado en background
    echo 📝 Ver logs en: output\logs\agente_siempre_activo.log
) else if "%1"=="--estado" (
    echo 📊 Mostrando estado del agente...
    echo.
    python scripts\iniciar_agente_siempre_activo.py --estado
) else if "%1"=="--ayuda" (
    echo 📖 Ayuda del Agente SAC Siempre Activo
    echo.
    echo Formas de uso:
    echo   iniciar_agente_siempre_activo.bat
    echo       Inicia en modo interactivo
    echo.
    echo   iniciar_agente_siempre_activo.bat --daemon
    echo       Inicia como servicio en background
    echo.
    echo   iniciar_agente_siempre_activo.bat --estado
    echo       Muestra estado actual del agente
    echo.
    echo   iniciar_agente_siempre_activo.bat --ayuda
    echo       Muestra esta ayuda
) else (
    echo ❓ Opción desconocida: %1
    echo    Ejecuta: iniciar_agente_siempre_activo.bat --ayuda
)

pause
