@echo off
:: ═══════════════════════════════════════════════════════════════════════════
:: LIMPIADOR DE CACHÉ DE ICONOS
:: Sistema de Mantenimiento Windows - CEDIS Chedraui Cancún 427
:: ═══════════════════════════════════════════════════════════════════════════
:: Descripción: Limpia la caché de iconos para resolver problemas visuales
:: Requiere: Ejecutar como Administrador
:: NOTA: El Explorador se reiniciará automáticamente
:: Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
:: ═══════════════════════════════════════════════════════════════════════════

title Limpiador de Caché de Iconos - CEDIS 427
color 0D

echo.
echo ═══════════════════════════════════════════════════════════════════════════
echo                   LIMPIADOR DE CACHÉ DE ICONOS
echo                        CEDIS Cancún 427
echo ═══════════════════════════════════════════════════════════════════════════
echo.
echo [INFO] Este proceso limpia la caché de iconos de Windows.
echo [INFO] El Explorador de Windows se reiniciará automáticamente.
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
set /p confirmar="¿Desea limpiar la caché de iconos? (S/N): "

if /i "%confirmar%"=="S" (
    echo.
    echo [PROCESO] Preparando limpieza de caché de iconos...
    ie4uinit.exe -show

    echo [PROCESO] Cerrando Explorador de Windows...
    taskkill /IM explorer.exe /F >nul 2>&1

    echo [PROCESO] Eliminando archivo de caché de iconos...
    del /A /Q "%localappdata%\IconCache.db" >nul 2>&1
    del /A /F /Q "%localappdata%\Microsoft\Windows\Explorer\iconcache*" >nul 2>&1

    echo [PROCESO] Reiniciando Explorador de Windows...
    start explorer.exe

    echo.
    echo ═══════════════════════════════════════════════════════════════════════════
    echo [COMPLETADO] Caché de iconos limpiado correctamente.
    echo [INFO] Los iconos pueden tardar unos segundos en regenerarse.
    echo ═══════════════════════════════════════════════════════════════════════════
) else (
    echo.
    echo [INFO] Operación cancelada por el usuario.
)

echo.
pause
