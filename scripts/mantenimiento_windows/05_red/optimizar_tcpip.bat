@echo off
:: ═══════════════════════════════════════════════════════════════════════════
:: OPTIMIZADOR TCP/IP
:: Sistema de Mantenimiento Windows - CEDIS Chedraui Cancún 427
:: ═══════════════════════════════════════════════════════════════════════════
:: Descripción: Optimiza la configuración TCP/IP para mejor rendimiento
:: Requiere: Ejecutar como Administrador
:: Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
:: ═══════════════════════════════════════════════════════════════════════════

title Optimizador TCP/IP - CEDIS 427
color 0B

echo.
echo ═══════════════════════════════════════════════════════════════════════════
echo                      OPTIMIZADOR TCP/IP
echo                        CEDIS Cancún 427
echo ═══════════════════════════════════════════════════════════════════════════
echo.
echo [INFO] Este proceso optimiza la configuración TCP/IP.
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

:: Mostrar configuración actual
echo ═══════════════════════════════════════════════════════════════════════════
echo [INFO] CONFIGURACIÓN TCP ACTUAL:
echo ═══════════════════════════════════════════════════════════════════════════
netsh interface tcp show global
echo.

:: Optimizar autotuning
echo [PROCESO] Configurando autotuning a nivel normal...
netsh interface tcp set global autotuninglevel=normal
echo [OK] Autotuning configurado.
echo.

:: Habilitar ECN
echo [PROCESO] Habilitando ECN (Explicit Congestion Notification)...
netsh interface tcp set global ecncapability=enabled
echo [OK] ECN habilitado.
echo.

:: Deshabilitar escalado de ventana heurístico
echo [PROCESO] Optimizando heurísticas de red...
netsh interface tcp set heuristics disabled
echo [OK] Heurísticas optimizadas.
echo.

:: Mostrar nueva configuración
echo ═══════════════════════════════════════════════════════════════════════════
echo [INFO] NUEVA CONFIGURACIÓN TCP:
echo ═══════════════════════════════════════════════════════════════════════════
netsh interface tcp show global
echo.

echo ═══════════════════════════════════════════════════════════════════════════
echo [COMPLETADO] Optimización TCP/IP finalizada.
echo ═══════════════════════════════════════════════════════════════════════════
echo.
pause
