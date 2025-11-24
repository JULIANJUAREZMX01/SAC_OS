@echo off
:: ═══════════════════════════════════════════════════════════════════════════
:: VERIFICADOR DE DISCO DURO
:: Sistema de Mantenimiento Windows - CEDIS Chedraui Cancún 427
:: ═══════════════════════════════════════════════════════════════════════════
:: Descripción: Ejecuta CHKDSK para verificar y reparar el disco
:: Requiere: Ejecutar como Administrador
:: IMPORTANTE: Requiere reinicio para discos del sistema
:: Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
:: ═══════════════════════════════════════════════════════════════════════════

title Verificador de Disco Duro - CEDIS 427
color 0B

echo.
echo ═══════════════════════════════════════════════════════════════════════════
echo                    VERIFICADOR DE DISCO DURO
echo                        CEDIS Cancún 427
echo ═══════════════════════════════════════════════════════════════════════════
echo.
echo [ADVERTENCIA] Este proceso puede requerir reinicio del sistema.
echo [ADVERTENCIA] Guarde todo su trabajo antes de continuar.
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

:: Mostrar estado actual de los discos
echo ═══════════════════════════════════════════════════════════════════════════
echo [INFO] Estado actual de los discos:
echo ═══════════════════════════════════════════════════════════════════════════
wmic diskdrive get status,model,size
echo.

:: Preguntar al usuario
echo [PREGUNTA] ¿Desea programar verificación del disco C: en el próximo reinicio?
echo [INFO] Opciones: /f = Corregir errores, /r = Localizar sectores defectuosos
echo.
set /p respuesta="Escriba S para continuar o N para cancelar: "

if /i "%respuesta%"=="S" (
    echo.
    echo [PROCESO] Programando verificación de disco para el próximo reinicio...
    chkdsk C: /f /r /x
    echo.
    echo [INFO] La verificación se ejecutará en el próximo reinicio.
    echo [RECOMENDACIÓN] Reinicie el equipo cuando sea conveniente.
) else (
    echo.
    echo [INFO] Operación cancelada por el usuario.
)

echo.
echo ═══════════════════════════════════════════════════════════════════════════
echo [COMPLETADO] Proceso de verificación de disco finalizado.
echo ═══════════════════════════════════════════════════════════════════════════
echo.
pause
