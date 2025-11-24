@echo off
:: ═══════════════════════════════════════════════════════════════════════════
:: LIMPIADOR DE ESPACIO EN DISCO
:: Sistema de Mantenimiento Windows - CEDIS Chedraui Cancún 427
:: ═══════════════════════════════════════════════════════════════════════════
:: Descripción: Ejecuta el liberador de espacio en disco de Windows
:: Requiere: Ejecutar como Administrador
:: Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
:: ═══════════════════════════════════════════════════════════════════════════

title Liberador de Espacio en Disco - CEDIS 427
color 0A

echo.
echo ═══════════════════════════════════════════════════════════════════════════
echo                    LIBERADOR DE ESPACIO EN DISCO
echo                        CEDIS Cancún 427
echo ═══════════════════════════════════════════════════════════════════════════
echo.
echo [INFO] Iniciando limpieza de disco...
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

:: Ejecutar limpieza de disco
echo [PROCESO] Ejecutando Liberador de Espacio en Disco...
cleanmgr /sagerun:1

echo.
echo ═══════════════════════════════════════════════════════════════════════════
echo [COMPLETADO] Limpieza de disco finalizada.
echo ═══════════════════════════════════════════════════════════════════════════
echo.
pause
