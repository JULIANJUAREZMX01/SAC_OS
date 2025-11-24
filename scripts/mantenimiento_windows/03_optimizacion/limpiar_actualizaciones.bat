@echo off
:: ═══════════════════════════════════════════════════════════════════════════
:: LIMPIADOR DE ARCHIVOS DE ACTUALIZACIÓN
:: Sistema de Mantenimiento Windows - CEDIS Chedraui Cancún 427
:: ═══════════════════════════════════════════════════════════════════════════
:: Descripción: Limpia archivos obsoletos de Windows Update
:: Puede liberar varios GB de espacio
:: Requiere: Ejecutar como Administrador
:: Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
:: ═══════════════════════════════════════════════════════════════════════════

title Limpiador de Archivos de Actualización - CEDIS 427
color 0E

echo.
echo ═══════════════════════════════════════════════════════════════════════════
echo              LIMPIADOR DE ARCHIVOS DE ACTUALIZACIÓN
echo                        CEDIS Cancún 427
echo ═══════════════════════════════════════════════════════════════════════════
echo.
echo [INFO] Este proceso puede liberar varios GB de espacio.
echo [INFO] Elimina componentes obsoletos de Windows Update.
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

:: Paso 1: Limpieza de componentes
echo ═══════════════════════════════════════════════════════════════════════════
echo [PASO 1/2] Limpiando componentes obsoletos...
echo ═══════════════════════════════════════════════════════════════════════════
Dism.exe /online /Cleanup-Image /StartComponentCleanup
echo.
echo [OK] Componentes obsoletos limpiados.
echo.

:: Paso 2: Limpieza de Service Pack supersedidos
echo ═══════════════════════════════════════════════════════════════════════════
echo [PASO 2/2] Limpiando Service Packs supersedidos...
echo ═══════════════════════════════════════════════════════════════════════════
Dism.exe /online /Cleanup-Image /SPSuperseded
echo.
echo [OK] Service Packs obsoletos limpiados.
echo.

echo ═══════════════════════════════════════════════════════════════════════════
echo [COMPLETADO] Limpieza de archivos de actualización finalizada.
echo ═══════════════════════════════════════════════════════════════════════════
echo.
pause
