@echo off
:: ═══════════════════════════════════════════════════════════════════════════
:: RESETEADOR DE CONFIGURACIÓN DE RED
:: Sistema de Mantenimiento Windows - CEDIS Chedraui Cancún 427
:: ═══════════════════════════════════════════════════════════════════════════
:: Descripción: Resetea completamente la configuración de red
:: Requiere: Ejecutar como Administrador
:: IMPORTANTE: Requiere reinicio para aplicar cambios
:: Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
:: ═══════════════════════════════════════════════════════════════════════════

title Reseteador de Configuración de Red - CEDIS 427
color 0B

echo.
echo ═══════════════════════════════════════════════════════════════════════════
echo               RESETEADOR DE CONFIGURACIÓN DE RED
echo                        CEDIS Cancún 427
echo ═══════════════════════════════════════════════════════════════════════════
echo.
echo [ADVERTENCIA] Este proceso reseteará toda la configuración de red.
echo [ADVERTENCIA] Requiere reinicio del sistema para aplicar cambios.
echo.
echo [INFO] Fecha/Hora: %date% %time%
echo.

:: Verificar privilegios de administrador
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Este script requiere privilegios de administrador.
    echo [INFO] Por favor, ejecute como Administrador.
    pause
    exit /b 1
)

echo [OK] Privilegios de administrador verificados.
echo.

:: Confirmar operación
set /p confirmar="¿Desea continuar con el reseteo de red? (S/N): "

if /i "%confirmar%"=="S" (
    echo.
    echo [PASO 1/4] Reseteando catálogo Winsock...
    netsh winsock reset
    echo [OK] Winsock reseteado.
    echo.

    echo [PASO 2/4] Reseteando configuración IP...
    netsh int ip reset
    echo [OK] Configuración IP reseteada.
    echo.

    echo [PASO 3/4] Limpiando caché DNS...
    ipconfig /flushdns
    echo [OK] Caché DNS limpiado.
    echo.

    echo [PASO 4/4] Renovando configuración IP...
    ipconfig /release >nul 2>&1
    ipconfig /renew >nul 2>&1
    echo [OK] Configuración IP renovada.
    echo.

    echo ═══════════════════════════════════════════════════════════════════════════
    echo [COMPLETADO] Reseteo de red completado.
    echo [IMPORTANTE] Reinicie el equipo para aplicar todos los cambios.
    echo ═══════════════════════════════════════════════════════════════════════════
) else (
    echo.
    echo [INFO] Operación cancelada por el usuario.
)

echo.
pause
