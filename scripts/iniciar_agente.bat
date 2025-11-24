@echo off
REM ═══════════════════════════════════════════════════════════════
REM AGENTE SAC - Script de Inicio para Windows
REM CEDIS Cancún 427 - Tiendas Chedraui
REM ═══════════════════════════════════════════════════════════════
REM
REM Este script inicia el Agente SAC al iniciar sesión en Windows.
REM
REM INSTALACIÓN:
REM 1. Copiar este archivo al directorio de inicio del usuario:
REM    %APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
REM
REM 2. O crear una tarea programada con el Programador de Tareas
REM
REM Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
REM ═══════════════════════════════════════════════════════════════

title Agente SAC - CEDIS 427

REM Configurar directorio del proyecto
set SAC_DIR=C:\SAC_V01_427_ADMJAJA

REM Verificar si existe el directorio
if not exist "%SAC_DIR%" (
    echo [ERROR] No se encontro el directorio del SAC: %SAC_DIR%
    echo Por favor, verifica la ruta de instalacion.
    pause
    exit /b 1
)

REM Cambiar al directorio del proyecto
cd /d "%SAC_DIR%"

REM Verificar que Python esté disponible
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no esta instalado o no esta en el PATH
    echo Instala Python 3.8+ desde python.org
    pause
    exit /b 1
)

REM Iniciar el Agente SAC
echo.
echo ============================================
echo   Iniciando Agente SAC - CEDIS 427
echo   Tiendas Chedraui S.A. de C.V.
echo ============================================
echo.

python iniciar_agente.py %*

REM Si se ejecutó con error, mostrar mensaje
if errorlevel 1 (
    echo.
    echo [ERROR] Hubo un problema al ejecutar el Agente SAC
    pause
)
