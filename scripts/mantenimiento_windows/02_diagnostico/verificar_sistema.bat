@echo off
:: ═══════════════════════════════════════════════════════════════════════════
:: VERIFICADOR DE INTEGRIDAD DEL SISTEMA
:: Sistema de Mantenimiento Windows - CEDIS Chedraui Cancún 427
:: ═══════════════════════════════════════════════════════════════════════════
:: Descripción: Ejecuta SFC y DISM para reparar archivos del sistema
:: Requiere: Ejecutar como Administrador
:: IMPORTANTE: Este proceso puede tomar 30-60 minutos
:: Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
:: ═══════════════════════════════════════════════════════════════════════════

title Verificador de Integridad del Sistema - CEDIS 427
color 0B

echo.
echo ═══════════════════════════════════════════════════════════════════════════
echo              VERIFICADOR DE INTEGRIDAD DEL SISTEMA
echo                        CEDIS Cancún 427
echo ═══════════════════════════════════════════════════════════════════════════
echo.
echo [ADVERTENCIA] Este proceso puede tomar entre 30-60 minutos.
echo [ADVERTENCIA] No cierre esta ventana durante la ejecución.
echo.
echo [INFO] Fecha/Hora de inicio: %date% %time%
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

:: Paso 1: Ejecutar SFC
echo ═══════════════════════════════════════════════════════════════════════════
echo [PASO 1/2] Ejecutando System File Checker (SFC)...
echo ═══════════════════════════════════════════════════════════════════════════
echo.
sfc /scannow
echo.
echo [OK] SFC completado.
echo.

:: Paso 2: Ejecutar DISM
echo ═══════════════════════════════════════════════════════════════════════════
echo [PASO 2/2] Ejecutando DISM (Restauración de Imagen)...
echo ═══════════════════════════════════════════════════════════════════════════
echo.
DISM /Online /Cleanup-Image /RestoreHealth
echo.
echo [OK] DISM completado.
echo.

echo ═══════════════════════════════════════════════════════════════════════════
echo [COMPLETADO] Verificación de integridad finalizada.
echo [INFO] Fecha/Hora de fin: %date% %time%
echo.
echo [RECOMENDACIÓN] Se recomienda reiniciar el equipo después de esta operación.
echo ═══════════════════════════════════════════════════════════════════════════
echo.
pause
