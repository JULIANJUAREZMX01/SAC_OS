@echo off
:: ═══════════════════════════════════════════════════════════════════════════
:: OPTIMIZADOR DE DISCO SSD (TRIM)
:: Sistema de Mantenimiento Windows - CEDIS Chedraui Cancún 427
:: ═══════════════════════════════════════════════════════════════════════════
:: Descripción: Ejecuta TRIM para optimizar discos SSD
:: IMPORTANTE: SOLO usar en discos SSD
:: Requiere: Ejecutar como Administrador
:: Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
:: ═══════════════════════════════════════════════════════════════════════════

title Optimizador de Disco SSD - CEDIS 427
color 0E

echo.
echo ═══════════════════════════════════════════════════════════════════════════
echo                    OPTIMIZADOR DE DISCO SSD
echo                        CEDIS Cancún 427
echo ═══════════════════════════════════════════════════════════════════════════
echo.
echo [INFO] Este proceso ejecuta TRIM para optimizar el rendimiento del SSD.
echo [INFO] Es seguro y rápido (generalmente menos de 5 minutos).
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

:: Mostrar información de discos
echo ═══════════════════════════════════════════════════════════════════════════
echo [INFO] DISCOS DETECTADOS:
echo ═══════════════════════════════════════════════════════════════════════════
wmic diskdrive get model,mediatype
echo.

:: Ejecutar optimización
echo [PROCESO] Ejecutando optimización TRIM en disco C:...
defrag C: /L /V

echo.
echo ═══════════════════════════════════════════════════════════════════════════
echo [COMPLETADO] Optimización de SSD finalizada.
echo ═══════════════════════════════════════════════════════════════════════════
echo.
pause
