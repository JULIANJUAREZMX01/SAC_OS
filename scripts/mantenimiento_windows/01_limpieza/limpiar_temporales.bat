@echo off
:: ═══════════════════════════════════════════════════════════════════════════
:: LIMPIADOR DE ARCHIVOS TEMPORALES
:: Sistema de Mantenimiento Windows - CEDIS Chedraui Cancún 427
:: ═══════════════════════════════════════════════════════════════════════════
:: Descripción: Elimina archivos temporales del usuario y del sistema
:: Requiere: Ejecutar como Administrador
:: Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
:: ═══════════════════════════════════════════════════════════════════════════

title Limpiador de Archivos Temporales - CEDIS 427
color 0A

echo.
echo ═══════════════════════════════════════════════════════════════════════════
echo                  LIMPIADOR DE ARCHIVOS TEMPORALES
echo                        CEDIS Cancún 427
echo ═══════════════════════════════════════════════════════════════════════════
echo.
echo [INFO] Iniciando limpieza de temporales...
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

:: Limpiar temporales del usuario
echo [PROCESO] Limpiando archivos temporales del usuario...
echo [RUTA] %TEMP%
del /q/f/s "%TEMP%\*" 2>nul
echo [OK] Temporales del usuario limpiados.
echo.

:: Limpiar temporales del sistema
echo [PROCESO] Limpiando archivos temporales del sistema...
echo [RUTA] C:\Windows\Temp
del /q/f/s "C:\Windows\Temp\*" 2>nul
echo [OK] Temporales del sistema limpiados.
echo.

:: Limpiar prefetch (opcional - mejora arranque)
echo [PROCESO] Limpiando caché de prefetch...
del /q/f/s "C:\Windows\Prefetch\*" 2>nul
echo [OK] Prefetch limpiado.
echo.

echo ═══════════════════════════════════════════════════════════════════════════
echo [COMPLETADO] Limpieza de archivos temporales finalizada.
echo ═══════════════════════════════════════════════════════════════════════════
echo.
pause
