@echo off
:: ═══════════════════════════════════════════════════════════════════════════
:: DESFRAGMENTADOR DE DISCO HDD
:: Sistema de Mantenimiento Windows - CEDIS Chedraui Cancún 427
:: ═══════════════════════════════════════════════════════════════════════════
:: Descripción: Desfragmenta discos duros mecánicos (HDD)
:: IMPORTANTE: NO usar en discos SSD
:: Requiere: Ejecutar como Administrador
:: Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
:: ═══════════════════════════════════════════════════════════════════════════

title Desfragmentador de Disco HDD - CEDIS 427
color 0E

echo.
echo ═══════════════════════════════════════════════════════════════════════════
echo                   DESFRAGMENTADOR DE DISCO HDD
echo                        CEDIS Cancún 427
echo ═══════════════════════════════════════════════════════════════════════════
echo.
echo [ADVERTENCIA] Este proceso es SOLO para discos HDD (mecánicos).
echo [ADVERTENCIA] NO ejecutar en discos SSD - puede reducir su vida útil.
echo [ADVERTENCIA] El proceso puede tomar varias horas.
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
echo [INFO] TIPO DE DISCO DETECTADO:
echo ═══════════════════════════════════════════════════════════════════════════
wmic diskdrive get model,mediatype
echo.

:: Confirmar operación
set /p confirmar="¿Confirma que el disco C: es HDD y desea desfragmentar? (S/N): "

if /i "%confirmar%"=="S" (
    echo.
    echo [PROCESO] Iniciando desfragmentación optimizada del disco C:...
    echo [INFO] Este proceso puede tomar varias horas dependiendo del tamaño del disco.
    echo.
    defrag C: /O /V
    echo.
    echo [OK] Desfragmentación completada.
) else (
    echo.
    echo [INFO] Operación cancelada por el usuario.
)

echo.
echo ═══════════════════════════════════════════════════════════════════════════
echo [COMPLETADO] Proceso de desfragmentación finalizado.
echo ═══════════════════════════════════════════════════════════════════════════
echo.
pause
