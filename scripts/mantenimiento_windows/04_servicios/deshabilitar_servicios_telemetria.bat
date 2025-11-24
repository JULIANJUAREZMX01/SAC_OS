@echo off
:: ═══════════════════════════════════════════════════════════════════════════
:: DESHABILITADOR DE SERVICIOS DE TELEMETRÍA
:: Sistema de Mantenimiento Windows - CEDIS Chedraui Cancún 427
:: ═══════════════════════════════════════════════════════════════════════════
:: Descripción: Deshabilita servicios de telemetría que pueden afectar rendimiento
:: Requiere: Ejecutar como Administrador
:: ADVERTENCIA: Esto desactiva servicios de diagnóstico de Microsoft
:: Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
:: ═══════════════════════════════════════════════════════════════════════════

title Deshabilitador de Servicios de Telemetría - CEDIS 427
color 0E

echo.
echo ═══════════════════════════════════════════════════════════════════════════
echo             DESHABILITADOR DE SERVICIOS DE TELEMETRÍA
echo                        CEDIS Cancún 427
echo ═══════════════════════════════════════════════════════════════════════════
echo.
echo [ADVERTENCIA] Este script deshabilita los siguientes servicios:
echo   - DiagTrack (Experiencias de usuario conectadas y telemetría)
echo   - SysMain (Superfetch - caché de aplicaciones)
echo.
echo [INFO] Esto puede mejorar el rendimiento pero desactiva diagnósticos.
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
set /p confirmar="¿Desea continuar y deshabilitar estos servicios? (S/N): "

if /i "%confirmar%"=="S" (
    echo.
    echo [PROCESO] Deshabilitando servicio DiagTrack...
    sc config "DiagTrack" start=disabled
    sc stop "DiagTrack" >nul 2>&1
    echo [OK] DiagTrack deshabilitado.
    echo.

    echo [PROCESO] Deshabilitando servicio SysMain (Superfetch)...
    sc config "SysMain" start=disabled
    sc stop "SysMain" >nul 2>&1
    echo [OK] SysMain deshabilitado.
    echo.

    echo [PROCESO] Deshabilitando servicio dmwappushservice...
    sc config "dmwappushservice" start=disabled
    sc stop "dmwappushservice" >nul 2>&1
    echo [OK] dmwappushservice deshabilitado.
    echo.
) else (
    echo.
    echo [INFO] Operación cancelada por el usuario.
)

echo.
echo ═══════════════════════════════════════════════════════════════════════════
echo [COMPLETADO] Proceso de deshabilitación de servicios finalizado.
echo ═══════════════════════════════════════════════════════════════════════════
echo.
pause
