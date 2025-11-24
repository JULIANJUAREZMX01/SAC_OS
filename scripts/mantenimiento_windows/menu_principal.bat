@echo off
:: ═══════════════════════════════════════════════════════════════════════════
:: MENÚ PRINCIPAL DE MANTENIMIENTO WINDOWS
:: Sistema de Mantenimiento Windows - CEDIS Chedraui Cancún 427
:: ═══════════════════════════════════════════════════════════════════════════
:: Descripción: Menú interactivo para acceder a todas las herramientas
:: Requiere: Ejecutar como Administrador
:: Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
:: Jefe de Sistemas - CEDIS Chedraui Logística Cancún
:: ═══════════════════════════════════════════════════════════════════════════

:menu
@echo off
title Menu de Mantenimiento Windows - CEDIS Chedraui 427
color 0B
cls

echo.
echo ╔═══════════════════════════════════════════════════════════════════════════╗
echo ║                                                                           ║
echo ║        ███╗   ███╗ █████╗ ███╗   ██╗████████╗███████╗███╗   ██╗          ║
echo ║        ████╗ ████║██╔══██╗████╗  ██║╚══██╔══╝██╔════╝████╗  ██║          ║
echo ║        ██╔████╔██║███████║██╔██╗ ██║   ██║   █████╗  ██╔██╗ ██║          ║
echo ║        ██║╚██╔╝██║██╔══██║██║╚██╗██║   ██║   ██╔══╝  ██║╚██╗██║          ║
echo ║        ██║ ╚═╝ ██║██║  ██║██║ ╚████║   ██║   ███████╗██║ ╚████║          ║
echo ║        ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚═╝  ╚═══╝          ║
echo ║                                                                           ║
echo ║            SISTEMA DE MANTENIMIENTO WINDOWS - CEDIS 427                   ║
echo ║                    Tiendas Chedraui S.A. de C.V.                          ║
echo ║                                                                           ║
echo ╠═══════════════════════════════════════════════════════════════════════════╣
echo ║                                                                           ║
echo ║   [1] LIMPIEZA DEL SISTEMA                                                ║
echo ║       └─ Temporales, DNS, Disco                                           ║
echo ║                                                                           ║
echo ║   [2] DIAGNÓSTICO Y REPARACIÓN                                            ║
echo ║       └─ SFC, DISM, CHKDSK, Salud disco                                   ║
echo ║                                                                           ║
echo ║   [3] OPTIMIZACIÓN DE RENDIMIENTO                                         ║
echo ║       └─ Desfragmentar HDD, TRIM SSD, Limpiar updates                     ║
echo ║                                                                           ║
echo ║   [4] GESTIÓN DE SERVICIOS Y PROCESOS                                     ║
echo ║       └─ Ver servicios, CPU, Memoria, Telemetría                          ║
echo ║                                                                           ║
echo ║   [5] OPTIMIZACIÓN DE RED                                                 ║
echo ║       └─ Reset red, Optimizar TCP/IP                                      ║
echo ║                                                                           ║
echo ║   [6] OPTIMIZACIÓN DE INICIO                                              ║
echo ║       └─ Programas inicio, Fast Startup, Iconos                           ║
echo ║                                                                           ║
echo ║   [7] LIMPIEZA COMPLETA (PowerShell)                                      ║
echo ║       └─ Script maestro de limpieza automática                            ║
echo ║                                                                           ║
echo ║   [0] SALIR                                                               ║
echo ║                                                                           ║
echo ╚═══════════════════════════════════════════════════════════════════════════╝
echo.
echo   Desarrollado por: Julian Alexander Juarez Alvarado (ADMJAJA)
echo   Jefe de Sistemas - CEDIS Chedraui Logistica Cancun
echo.

set /p opcion="  Seleccione una opcion [0-7]: "

if "%opcion%"=="1" goto submenu_limpieza
if "%opcion%"=="2" goto submenu_diagnostico
if "%opcion%"=="3" goto submenu_optimizacion
if "%opcion%"=="4" goto submenu_servicios
if "%opcion%"=="5" goto submenu_red
if "%opcion%"=="6" goto submenu_inicio
if "%opcion%"=="7" goto limpieza_completa
if "%opcion%"=="0" goto salir

echo.
echo [ERROR] Opcion no valida. Intente de nuevo.
timeout /t 2 >nul
goto menu

:: ═══════════════════════════════════════════════════════════════════════════
:: SUBMENÚ: LIMPIEZA DEL SISTEMA
:: ═══════════════════════════════════════════════════════════════════════════

:submenu_limpieza
cls
echo.
echo ╔═══════════════════════════════════════════════════════════════════════════╗
echo ║                      LIMPIEZA DEL SISTEMA                                 ║
echo ╠═══════════════════════════════════════════════════════════════════════════╣
echo ║                                                                           ║
echo ║   [1] Liberador de Espacio en Disco (cleanmgr)                            ║
echo ║   [2] Limpiar Archivos Temporales                                         ║
echo ║   [3] Limpiar Cache DNS                                                   ║
echo ║                                                                           ║
echo ║   [0] Volver al menu principal                                            ║
echo ║                                                                           ║
echo ╚═══════════════════════════════════════════════════════════════════════════╝
echo.

set /p sub1="  Seleccione una opcion [0-3]: "

if "%sub1%"=="1" call "%~dp0\01_limpieza\limpiar_disco.bat"
if "%sub1%"=="2" call "%~dp0\01_limpieza\limpiar_temporales.bat"
if "%sub1%"=="3" call "%~dp0\01_limpieza\limpiar_dns.bat"
if "%sub1%"=="0" goto menu

goto submenu_limpieza

:: ═══════════════════════════════════════════════════════════════════════════
:: SUBMENÚ: DIAGNÓSTICO Y REPARACIÓN
:: ═══════════════════════════════════════════════════════════════════════════

:submenu_diagnostico
cls
echo.
echo ╔═══════════════════════════════════════════════════════════════════════════╗
echo ║                    DIAGNOSTICO Y REPARACION                               ║
echo ╠═══════════════════════════════════════════════════════════════════════════╣
echo ║                                                                           ║
echo ║   [1] Verificar Integridad del Sistema (SFC + DISM)                       ║
echo ║   [2] Verificar Disco Duro (CHKDSK)                                       ║
echo ║   [3] Analizar Salud del Disco                                            ║
echo ║                                                                           ║
echo ║   [0] Volver al menu principal                                            ║
echo ║                                                                           ║
echo ╚═══════════════════════════════════════════════════════════════════════════╝
echo.

set /p sub2="  Seleccione una opcion [0-3]: "

if "%sub2%"=="1" call "%~dp0\02_diagnostico\verificar_sistema.bat"
if "%sub2%"=="2" call "%~dp0\02_diagnostico\verificar_disco.bat"
if "%sub2%"=="3" call "%~dp0\02_diagnostico\salud_disco.bat"
if "%sub2%"=="0" goto menu

goto submenu_diagnostico

:: ═══════════════════════════════════════════════════════════════════════════
:: SUBMENÚ: OPTIMIZACIÓN DE RENDIMIENTO
:: ═══════════════════════════════════════════════════════════════════════════

:submenu_optimizacion
cls
echo.
echo ╔═══════════════════════════════════════════════════════════════════════════╗
echo ║                   OPTIMIZACION DE RENDIMIENTO                             ║
echo ╠═══════════════════════════════════════════════════════════════════════════╣
echo ║                                                                           ║
echo ║   [1] Desfragmentar Disco HDD (SOLO HDD - NO SSD)                         ║
echo ║   [2] Optimizar Disco SSD (TRIM)                                          ║
echo ║   [3] Limpiar Archivos de Actualizacion                                   ║
echo ║                                                                           ║
echo ║   [0] Volver al menu principal                                            ║
echo ║                                                                           ║
echo ╚═══════════════════════════════════════════════════════════════════════════╝
echo.

set /p sub3="  Seleccione una opcion [0-3]: "

if "%sub3%"=="1" call "%~dp0\03_optimizacion\desfragmentar_hdd.bat"
if "%sub3%"=="2" call "%~dp0\03_optimizacion\optimizar_ssd.bat"
if "%sub3%"=="3" call "%~dp0\03_optimizacion\limpiar_actualizaciones.bat"
if "%sub3%"=="0" goto menu

goto submenu_optimizacion

:: ═══════════════════════════════════════════════════════════════════════════
:: SUBMENÚ: GESTIÓN DE SERVICIOS Y PROCESOS
:: ═══════════════════════════════════════════════════════════════════════════

:submenu_servicios
cls
echo.
echo ╔═══════════════════════════════════════════════════════════════════════════╗
echo ║                  GESTION DE SERVICIOS Y PROCESOS                          ║
echo ╠═══════════════════════════════════════════════════════════════════════════╣
echo ║                                                                           ║
echo ║   [1] Ver Servicios en Ejecucion (PowerShell)                             ║
echo ║   [2] Ver Procesos por Consumo de CPU (PowerShell)                        ║
echo ║   [3] Ver Procesos por Consumo de Memoria (PowerShell)                    ║
echo ║   [4] Deshabilitar Servicios de Telemetria                                ║
echo ║                                                                           ║
echo ║   [0] Volver al menu principal                                            ║
echo ║                                                                           ║
echo ╚═══════════════════════════════════════════════════════════════════════════╝
echo.

set /p sub4="  Seleccione una opcion [0-4]: "

if "%sub4%"=="1" powershell -ExecutionPolicy Bypass -File "%~dp0\04_servicios\ver_servicios.ps1"
if "%sub4%"=="2" powershell -ExecutionPolicy Bypass -File "%~dp0\04_servicios\ver_procesos_cpu.ps1"
if "%sub4%"=="3" powershell -ExecutionPolicy Bypass -File "%~dp0\04_servicios\ver_procesos_memoria.ps1"
if "%sub4%"=="4" call "%~dp0\04_servicios\deshabilitar_servicios_telemetria.bat"
if "%sub4%"=="0" goto menu

goto submenu_servicios

:: ═══════════════════════════════════════════════════════════════════════════
:: SUBMENÚ: OPTIMIZACIÓN DE RED
:: ═══════════════════════════════════════════════════════════════════════════

:submenu_red
cls
echo.
echo ╔═══════════════════════════════════════════════════════════════════════════╗
echo ║                       OPTIMIZACION DE RED                                 ║
echo ╠═══════════════════════════════════════════════════════════════════════════╣
echo ║                                                                           ║
echo ║   [1] Resetear Configuracion de Red                                       ║
echo ║   [2] Optimizar TCP/IP                                                    ║
echo ║                                                                           ║
echo ║   [0] Volver al menu principal                                            ║
echo ║                                                                           ║
echo ╚═══════════════════════════════════════════════════════════════════════════╝
echo.

set /p sub5="  Seleccione una opcion [0-2]: "

if "%sub5%"=="1" call "%~dp0\05_red\resetear_red.bat"
if "%sub5%"=="2" call "%~dp0\05_red\optimizar_tcpip.bat"
if "%sub5%"=="0" goto menu

goto submenu_red

:: ═══════════════════════════════════════════════════════════════════════════
:: SUBMENÚ: OPTIMIZACIÓN DE INICIO
:: ═══════════════════════════════════════════════════════════════════════════

:submenu_inicio
cls
echo.
echo ╔═══════════════════════════════════════════════════════════════════════════╗
echo ║                      OPTIMIZACION DE INICIO                               ║
echo ╠═══════════════════════════════════════════════════════════════════════════╣
echo ║                                                                           ║
echo ║   [1] Ver Programas de Inicio                                             ║
echo ║   [2] Deshabilitar Inicio Rapido (PowerShell)                             ║
echo ║   [3] Limpiar Cache de Iconos                                             ║
echo ║                                                                           ║
echo ║   [0] Volver al menu principal                                            ║
echo ║                                                                           ║
echo ╚═══════════════════════════════════════════════════════════════════════════╝
echo.

set /p sub6="  Seleccione una opcion [0-3]: "

if "%sub6%"=="1" call "%~dp0\06_inicio\ver_programas_inicio.bat"
if "%sub6%"=="2" powershell -ExecutionPolicy Bypass -File "%~dp0\06_inicio\deshabilitar_inicio_rapido.ps1"
if "%sub6%"=="3" call "%~dp0\06_inicio\limpiar_cache_iconos.bat"
if "%sub6%"=="0" goto menu

goto submenu_inicio

:: ═══════════════════════════════════════════════════════════════════════════
:: LIMPIEZA COMPLETA
:: ═══════════════════════════════════════════════════════════════════════════

:limpieza_completa
cls
echo.
echo ╔═══════════════════════════════════════════════════════════════════════════╗
echo ║                     LIMPIEZA COMPLETA DEL SISTEMA                         ║
echo ╠═══════════════════════════════════════════════════════════════════════════╣
echo ║                                                                           ║
echo ║   Este script ejecutara:                                                  ║
echo ║   - Limpieza de archivos temporales                                       ║
echo ║   - Vaciado de papelera                                                   ║
echo ║   - Limpieza de cache DNS                                                 ║
echo ║   - Verificacion de integridad del sistema                                ║
echo ║                                                                           ║
echo ╚═══════════════════════════════════════════════════════════════════════════╝
echo.

set /p confirmar="  ¿Desea ejecutar la limpieza completa? (S/N): "

if /i "%confirmar%"=="S" (
    powershell -ExecutionPolicy Bypass -File "%~dp0\07_completo\limpieza_completa.ps1"
)

goto menu

:: ═══════════════════════════════════════════════════════════════════════════
:: SALIR
:: ═══════════════════════════════════════════════════════════════════════════

:salir
cls
echo.
echo ╔═══════════════════════════════════════════════════════════════════════════╗
echo ║                                                                           ║
echo ║                    Gracias por usar el Sistema de                         ║
echo ║                    Mantenimiento Windows - CEDIS 427                      ║
echo ║                                                                           ║
echo ║                    Tiendas Chedraui S.A. de C.V.                          ║
echo ║                                                                           ║
echo ╚═══════════════════════════════════════════════════════════════════════════╝
echo.
echo   "Las maquinas y los sistemas al servicio de los analistas"
echo.
timeout /t 3 >nul
exit
