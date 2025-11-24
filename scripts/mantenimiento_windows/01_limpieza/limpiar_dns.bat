@echo off
:: ═══════════════════════════════════════════════════════════════════════════
:: LIMPIADOR DE CACHÉ DNS
:: Sistema de Mantenimiento Windows - CEDIS Chedraui Cancún 427
:: ═══════════════════════════════════════════════════════════════════════════
:: Descripción: Limpia la caché DNS del sistema
:: Requiere: Ejecutar como Administrador
:: Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
:: ═══════════════════════════════════════════════════════════════════════════

title Limpiador de Caché DNS - CEDIS 427
color 0A

echo.
echo ═══════════════════════════════════════════════════════════════════════════
echo                      LIMPIADOR DE CACHÉ DNS
echo                        CEDIS Cancún 427
echo ═══════════════════════════════════════════════════════════════════════════
echo.
echo [INFO] Iniciando limpieza de caché DNS...
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

:: Mostrar caché DNS antes de limpiar
echo [INFO] Mostrando estadísticas de caché DNS actual...
ipconfig /displaydns | find "Record Name" /c
echo.

:: Limpiar caché DNS
echo [PROCESO] Limpiando caché DNS...
ipconfig /flushdns
echo.

:: Renovar IP
echo [PROCESO] Renovando configuración IP...
ipconfig /release >nul 2>&1
ipconfig /renew >nul 2>&1
echo [OK] Configuración IP renovada.
echo.

echo ═══════════════════════════════════════════════════════════════════════════
echo [COMPLETADO] Caché DNS limpiado correctamente.
echo ═══════════════════════════════════════════════════════════════════════════
echo.
pause
