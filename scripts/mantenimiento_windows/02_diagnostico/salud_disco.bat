@echo off
:: ═══════════════════════════════════════════════════════════════════════════
:: ANALIZADOR DE SALUD DEL DISCO
:: Sistema de Mantenimiento Windows - CEDIS Chedraui Cancún 427
:: ═══════════════════════════════════════════════════════════════════════════
:: Descripción: Muestra información de salud y estado de los discos
:: Requiere: Ejecutar como Administrador
:: Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
:: ═══════════════════════════════════════════════════════════════════════════

title Analizador de Salud del Disco - CEDIS 427
color 0B

echo.
echo ═══════════════════════════════════════════════════════════════════════════
echo                   ANALIZADOR DE SALUD DEL DISCO
echo                        CEDIS Cancún 427
echo ═══════════════════════════════════════════════════════════════════════════
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

:: Estado de los discos
echo ═══════════════════════════════════════════════════════════════════════════
echo [INFO] ESTADO DE LOS DISCOS DUROS:
echo ═══════════════════════════════════════════════════════════════════════════
wmic diskdrive get status
echo.

:: Información detallada de discos
echo ═══════════════════════════════════════════════════════════════════════════
echo [INFO] INFORMACIÓN DETALLADA DE DISCOS:
echo ═══════════════════════════════════════════════════════════════════════════
wmic diskdrive get model,size,mediatype,status,interfacetype
echo.

:: Información de particiones
echo ═══════════════════════════════════════════════════════════════════════════
echo [INFO] INFORMACIÓN DE PARTICIONES:
echo ═══════════════════════════════════════════════════════════════════════════
wmic partition get name,size,type
echo.

:: Espacio libre en unidades
echo ═══════════════════════════════════════════════════════════════════════════
echo [INFO] ESPACIO EN UNIDADES LÓGICAS:
echo ═══════════════════════════════════════════════════════════════════════════
wmic logicaldisk get name,size,freespace,filesystem
echo.

echo ═══════════════════════════════════════════════════════════════════════════
echo [COMPLETADO] Análisis de salud de disco finalizado.
echo ═══════════════════════════════════════════════════════════════════════════
echo.
pause
