@echo off
:: ═══════════════════════════════════════════════════════════════════════════
:: VISOR DE PROGRAMAS DE INICIO
:: Sistema de Mantenimiento Windows - CEDIS Chedraui Cancún 427
:: ═══════════════════════════════════════════════════════════════════════════
:: Descripción: Muestra todos los programas que inician con Windows
:: Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
:: ═══════════════════════════════════════════════════════════════════════════

title Visor de Programas de Inicio - CEDIS 427
color 0D

echo.
echo ═══════════════════════════════════════════════════════════════════════════
echo                   VISOR DE PROGRAMAS DE INICIO
echo                        CEDIS Cancún 427
echo ═══════════════════════════════════════════════════════════════════════════
echo.
echo [INFO] Fecha/Hora: %date% %time%
echo.

echo ═══════════════════════════════════════════════════════════════════════════
echo [INFO] PROGRAMAS QUE INICIAN CON WINDOWS:
echo ═══════════════════════════════════════════════════════════════════════════
echo.
wmic startup get caption,command,location
echo.

echo ═══════════════════════════════════════════════════════════════════════════
echo [INFO] LISTA COMPLETA CON DETALLES:
echo ═══════════════════════════════════════════════════════════════════════════
echo.
wmic startup list full
echo.

echo ═══════════════════════════════════════════════════════════════════════════
echo [RECOMENDACIÓN] Para deshabilitar programas de inicio:
echo   1. Presione Ctrl+Shift+Esc para abrir el Administrador de Tareas
echo   2. Vaya a la pestaña "Inicio"
echo   3. Deshabilite los programas innecesarios
echo ═══════════════════════════════════════════════════════════════════════════
echo.
pause
