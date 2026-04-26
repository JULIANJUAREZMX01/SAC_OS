#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
  ███████╗ █████╗  ██████╗    ███╗   ███╗ █████╗ ███████╗███████╗████████╗██████╗  ██████╗
  ██╔════╝██╔══██╗██╔════╝    ████╗ ████║██╔══██╗██╔════╝██╔════╝╚══██╔══╝██╔══██╗██╔═══██╗
  ███████╗███████║██║         ██╔████╔██║███████║█████╗  ███████╗   ██║   ██████╔╝██║   ██║
  ╚════██║██╔══██║██║         ██║╚██╔╝██║██╔══██║██╔══╝  ╚════██║   ██║   ██╔══██╗██║   ██║
  ███████║██║  ██║╚██████╗    ██║ ╚═╝ ██║██║  ██║███████╗███████║   ██║   ██║  ██║╚██████╔╝
  ╚══════╝╚═╝  ╚═╝ ╚═════╝    ╚═╝     ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝
===============================================================================

                    SAC - SCRIPT MAESTRO UNIFICADO
                    Sistema de Automatizacion de Consultas
                    CEDIS Cancun 427 - Tiendas Chedraui

===============================================================================

                        PUNTO DE ENTRADA UNICO

    Este es el UNICO archivo que necesita ejecutar para:
    - Instalar el sistema (primera vez)
    - Ejecutar el sistema (uso normal)
    - Modo monitor continuo
    - Generar reportes
    - Enviar alertas
    - Gestionar el sistema completo

===============================================================================

USO:
    python SAC.py                     # Modo interactivo (auto-detecta)
    python SAC.py --instalar          # Forzar instalacion
    python SAC.py --menu              # Menu principal
    python SAC.py --monitor           # Modo monitor continuo
    python SAC.py --reporte           # Generar reporte diario
    python SAC.py --validar OC123     # Validar OC especifica
    python SAC.py --status            # Ver estado del sistema
    python SAC.py --daemon            # Modo servicio (tareas programadas)
    python SAC.py --help              # Ayuda completa

===============================================================================

Desarrollado por: Julian Alexander Juarez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logistica Cancun 427

Version: 4.0.0
Fecha: Noviembre 2025
===============================================================================
"""

import os
import sys
import subprocess
import argparse
import json
import platform
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# ===============================================================================
# CONFIGURACION BASE
# ===============================================================================

VERSION = "4.0.0"
BASE_DIR = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(BASE_DIR))

# Archivos de estado
ENV_FILE = BASE_DIR / '.env'
INSTALADO_FLAG = BASE_DIR / 'config' / '.instalado'

# Requisitos minimos
PYTHON_MIN_VERSION = (3, 8)


# ===============================================================================
# COLORES TERMINAL
# ===============================================================================

class Colores:
    """Codigos de escape ANSI para colores"""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'

    # Colores texto
    ROJO = '\033[91m'
    VERDE = '\033[92m'
    AMARILLO = '\033[93m'
    AZUL = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    BLANCO = '\033[97m'

    # Chedraui
    CHEDRAUI = '\033[91m'  # Rojo Chedraui


# Habilitar colores en Windows
if sys.platform == 'win32':
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        for attr in dir(Colores):
            if not attr.startswith('_'):
                setattr(Colores, attr, '')


# ===============================================================================
# ESTADOS DEL SISTEMA
# ===============================================================================

class EstadoSistema(Enum):
    """Estados posibles del sistema"""
    NO_INSTALADO = "no_instalado"
    INSTALACION_PARCIAL = "instalacion_parcial"
    SIN_CREDENCIALES = "sin_credenciales"
    LISTO = "listo"
    ERROR = "error"


@dataclass
class InfoSistema:
    """Informacion del estado del sistema"""
    estado: EstadoSistema
    python_ok: bool
    directorios_ok: bool
    dependencias_ok: bool
    credenciales_ok: bool
    mensaje: str
    dependencias_faltantes: List[str]


# ===============================================================================
# UTILIDADES
# ===============================================================================

def limpiar_pantalla():
    """Limpia la pantalla de la terminal"""
    os.system('cls' if sys.platform == 'win32' else 'clear')


def imprimir_banner():
    """Imprime el banner del sistema"""
    limpiar_pantalla()
    print(f"""{Colores.CHEDRAUI}{Colores.BOLD}
===============================================================================
{Colores.RESET}{Colores.CHEDRAUI}
    ███████╗ █████╗  ██████╗
    ██╔════╝██╔══██╗██╔════╝
    ███████╗███████║██║
    ╚════██║██╔══██║██║
    ███████║██║  ██║╚██████╗
    ╚══════╝╚═╝  ╚═╝ ╚═════╝
{Colores.RESET}
    {Colores.CYAN}Sistema de Automatizacion de Consultas{Colores.RESET}
    {Colores.AMARILLO}CEDIS Chedraui Cancun 427 - Region Sureste{Colores.RESET}

    {Colores.BLANCO}Version: {VERSION}{Colores.RESET}
    {Colores.BLANCO}Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colores.RESET}
{Colores.CHEDRAUI}{Colores.BOLD}
===============================================================================
{Colores.RESET}
""")


def imprimir_separador(titulo: str = ""):
    """Imprime un separador con titulo opcional"""
    if titulo:
        print(f"\n{Colores.CYAN}{'═' * 70}{Colores.RESET}")
        print(f"{Colores.BOLD}  {titulo}{Colores.RESET}")
        print(f"{Colores.CYAN}{'═' * 70}{Colores.RESET}")
    else:
        print(f"{Colores.CYAN}{'─' * 70}{Colores.RESET}")


def imprimir_ok(mensaje: str):
    """Imprime mensaje de exito"""
    print(f"  {Colores.VERDE}✓{Colores.RESET} {mensaje}")


def imprimir_error(mensaje: str):
    """Imprime mensaje de error"""
    print(f"  {Colores.ROJO}✗{Colores.RESET} {mensaje}")


def imprimir_warn(mensaje: str):
    """Imprime advertencia"""
    print(f"  {Colores.AMARILLO}⚠{Colores.RESET} {mensaje}")


def imprimir_info(mensaje: str):
    """Imprime informacion"""
    print(f"  {Colores.CYAN}ℹ{Colores.RESET} {mensaje}")


def imprimir_proceso(mensaje: str):
    """Imprime proceso en curso"""
    print(f"  {Colores.MAGENTA}⟳{Colores.RESET} {mensaje}")


# ===============================================================================
# VERIFICACION DEL SISTEMA
# ===============================================================================

def verificar_python() -> bool:
    """Verifica version de Python"""
    return sys.version_info >= PYTHON_MIN_VERSION


def verificar_directorios() -> bool:
    """Verifica que existan los directorios necesarios"""
    directorios = [
        'config', 'modules', 'queries', 'output', 'output/logs', 'output/resultados'
    ]
    return all((BASE_DIR / d).exists() for d in directorios)


def verificar_dependencias_core() -> Tuple[bool, List[str]]:
    """Verifica dependencias minimas instaladas"""
    faltantes = []
    dependencias = {
        'pandas': 'pandas',
        'openpyxl': 'openpyxl',
        'dotenv': 'python-dotenv',
        'rich': 'rich',
    }

    for modulo, paquete in dependencias.items():
        try:
            __import__(modulo)
        except ImportError:
            faltantes.append(paquete)

    return len(faltantes) == 0, faltantes


def verificar_credenciales() -> bool:
    """Verifica que existan credenciales configuradas"""
    if not ENV_FILE.exists():
        return False

    try:
        contenido = ENV_FILE.read_text(encoding='utf-8')

        credenciales_requeridas = ['DB_USER=', 'DB_PASSWORD=']
        for cred in credenciales_requeridas:
            if cred not in contenido:
                return False

            # Verificar que tenga valor
            for linea in contenido.split('\n'):
                if linea.startswith(cred):
                    valor = linea.split('=', 1)[1].strip()
                    if not valor or valor in ['', 'tu_usuario', 'your_password']:
                        return False
                    break

        return True
    except Exception:
        return False


def verificar_sistema() -> InfoSistema:
    """Verifica el estado completo del sistema"""
    python_ok = verificar_python()
    directorios_ok = verificar_directorios()
    dependencias_ok, faltantes = verificar_dependencias_core()
    credenciales_ok = verificar_credenciales()
    instalado = INSTALADO_FLAG.exists()

    # Determinar estado
    if not python_ok:
        estado = EstadoSistema.ERROR
        mensaje = f"Python 3.8+ requerido. Actual: {sys.version_info.major}.{sys.version_info.minor}"
    elif not directorios_ok or not dependencias_ok:
        estado = EstadoSistema.NO_INSTALADO
        mensaje = "Sistema no instalado"
    elif not credenciales_ok:
        estado = EstadoSistema.SIN_CREDENCIALES
        mensaje = "Instalado pero sin credenciales"
    elif instalado:
        estado = EstadoSistema.LISTO
        mensaje = "Sistema listo para operar"
    else:
        estado = EstadoSistema.INSTALACION_PARCIAL
        mensaje = "Instalacion parcial detectada"

    return InfoSistema(
        estado=estado,
        python_ok=python_ok,
        directorios_ok=directorios_ok,
        dependencias_ok=dependencias_ok,
        credenciales_ok=credenciales_ok,
        mensaje=mensaje,
        dependencias_faltantes=faltantes
    )


def mostrar_estado_sistema(info: InfoSistema):
    """Muestra el estado del sistema en formato tabla"""
    imprimir_separador("ESTADO DEL SISTEMA")
    print()

    # Python
    if info.python_ok:
        imprimir_ok(f"Python: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    else:
        imprimir_error(f"Python: {sys.version_info.major}.{sys.version_info.minor} (requiere 3.8+)")

    # Directorios
    if info.directorios_ok:
        imprimir_ok("Estructura de directorios")
    else:
        imprimir_error("Estructura de directorios incompleta")

    # Dependencias
    if info.dependencias_ok:
        imprimir_ok("Dependencias core instaladas")
    else:
        imprimir_error(f"Dependencias faltantes: {', '.join(info.dependencias_faltantes)}")

    # Credenciales
    if info.credenciales_ok:
        imprimir_ok("Credenciales configuradas")
    else:
        imprimir_warn("Credenciales no configuradas")

    print()
    print(f"  {Colores.BOLD}Estado: {info.estado.value}{Colores.RESET}")
    print(f"  {Colores.DIM}{info.mensaje}{Colores.RESET}")
    print()


# ===============================================================================
# EJECUTORES DE SUBSISTEMAS
# ===============================================================================

def ejecutar_instalador() -> bool:
    """Ejecuta el instalador del sistema"""
    imprimir_proceso("Buscando instalador...")

    # Prioridad de instaladores
    instaladores = [
        'instalador_automatico_gui.py',  # Mas reciente, con GUI
        'instalar_sac.py',                # Instalador maestro
    ]

    for instalador in instaladores:
        ruta = BASE_DIR / instalador
        if ruta.exists():
            imprimir_ok(f"Usando: {instalador}")
            try:
                resultado = subprocess.run(
                    [sys.executable, str(ruta)],
                    cwd=str(BASE_DIR)
                )
                return resultado.returncode == 0
            except Exception as e:
                imprimir_error(f"Error ejecutando instalador: {e}")
                return False

    imprimir_error("No se encontro ningun instalador")
    return False


def ejecutar_sistema_principal() -> bool:
    """Ejecuta el sistema principal"""
    imprimir_proceso("Iniciando sistema principal...")

    # Prioridad de puntos de entrada
    puntos_entrada = [
        ('sac_master_gui.py', 'Script Maestro GUI v3.0'),
        ('sac_master.py', 'Script Maestro v2.0'),
        ('main.py', 'Menu principal'),
    ]

    for script, nombre in puntos_entrada:
        ruta = BASE_DIR / script
        if ruta.exists():
            imprimir_ok(f"Usando: {nombre}")
            try:
                resultado = subprocess.run(
                    [sys.executable, str(ruta)],
                    cwd=str(BASE_DIR)
                )
                return resultado.returncode == 0
            except KeyboardInterrupt:
                return True
            except Exception as e:
                imprimir_error(f"Error: {e}")
                return False

    imprimir_error("No se encontro punto de entrada del sistema")
    return False


def ejecutar_monitor() -> bool:
    """Ejecuta el monitor en tiempo real"""
    ruta = BASE_DIR / 'monitor.py'
    if ruta.exists():
        try:
            resultado = subprocess.run(
                [sys.executable, str(ruta)],
                cwd=str(BASE_DIR)
            )
            return resultado.returncode == 0
        except KeyboardInterrupt:
            return True

    imprimir_error("Monitor no encontrado")
    return False


def ejecutar_maestro_daemon() -> bool:
    """Ejecuta el orquestador en modo daemon"""
    ruta = BASE_DIR / 'maestro.py'
    if ruta.exists():
        try:
            resultado = subprocess.run(
                [sys.executable, str(ruta), '--daemon'],
                cwd=str(BASE_DIR)
            )
            return resultado.returncode == 0
        except KeyboardInterrupt:
            return True

    imprimir_error("Orquestador no encontrado")
    return False


def ejecutar_validacion_oc(oc: str) -> bool:
    """Ejecuta validacion de OC especifica"""
    ruta = BASE_DIR / 'main.py'
    if ruta.exists():
        try:
            resultado = subprocess.run(
                [sys.executable, str(ruta), '--oc', oc],
                cwd=str(BASE_DIR)
            )
            return resultado.returncode == 0
        except Exception as e:
            imprimir_error(f"Error: {e}")
            return False

    imprimir_error("main.py no encontrado")
    return False


def ejecutar_reporte_diario() -> bool:
    """Genera reporte diario"""
    ruta = BASE_DIR / 'main.py'
    if ruta.exists():
        try:
            resultado = subprocess.run(
                [sys.executable, str(ruta), '--reporte-diario'],
                cwd=str(BASE_DIR)
            )
            return resultado.returncode == 0
        except Exception as e:
            imprimir_error(f"Error: {e}")
            return False

    imprimir_error("main.py no encontrado")
    return False


# ===============================================================================
# MENU INTERACTIVO
# ===============================================================================

def mostrar_menu_principal():
    """Muestra el menu principal interactivo"""
    while True:
        imprimir_banner()

        print(f"""
  {Colores.BOLD}MENU PRINCIPAL{Colores.RESET}

    {Colores.VERDE}[1]{Colores.RESET} Iniciar Sistema SAC (Menu completo)
    {Colores.VERDE}[2]{Colores.RESET} Monitor en tiempo real
    {Colores.VERDE}[3]{Colores.RESET} Validar Orden de Compra
    {Colores.VERDE}[4]{Colores.RESET} Generar Reporte Diario
    {Colores.VERDE}[5]{Colores.RESET} Modo Daemon (tareas programadas)

    {Colores.CYAN}[6]{Colores.RESET} Ver estado del sistema
    {Colores.CYAN}[7]{Colores.RESET} Reinstalar sistema

    {Colores.AMARILLO}[0]{Colores.RESET} Salir
""")

        try:
            opcion = input(f"  {Colores.CYAN}Seleccione opcion: {Colores.RESET}").strip()

            if opcion == '1':
                ejecutar_sistema_principal()
                input(f"\n  {Colores.CYAN}Presione Enter para continuar...{Colores.RESET}")

            elif opcion == '2':
                ejecutar_monitor()
                input(f"\n  {Colores.CYAN}Presione Enter para continuar...{Colores.RESET}")

            elif opcion == '3':
                oc = input(f"  {Colores.CYAN}Numero de OC: {Colores.RESET}").strip()
                if oc:
                    ejecutar_validacion_oc(oc)
                input(f"\n  {Colores.CYAN}Presione Enter para continuar...{Colores.RESET}")

            elif opcion == '4':
                ejecutar_reporte_diario()
                input(f"\n  {Colores.CYAN}Presione Enter para continuar...{Colores.RESET}")

            elif opcion == '5':
                ejecutar_maestro_daemon()
                input(f"\n  {Colores.CYAN}Presione Enter para continuar...{Colores.RESET}")

            elif opcion == '6':
                info = verificar_sistema()
                mostrar_estado_sistema(info)
                input(f"\n  {Colores.CYAN}Presione Enter para continuar...{Colores.RESET}")

            elif opcion == '7':
                confirmar = input(f"  {Colores.AMARILLO}Confirmar reinstalacion? (s/N): {Colores.RESET}").strip().lower()
                if confirmar == 's':
                    if INSTALADO_FLAG.exists():
                        INSTALADO_FLAG.unlink()
                    ejecutar_instalador()
                input(f"\n  {Colores.CYAN}Presione Enter para continuar...{Colores.RESET}")

            elif opcion == '0':
                print(f"\n  {Colores.CYAN}Hasta pronto - SAC{Colores.RESET}\n")
                break

        except KeyboardInterrupt:
            print(f"\n\n  {Colores.CYAN}Hasta pronto - SAC{Colores.RESET}\n")
            break


def mostrar_menu_sin_credenciales():
    """Menu cuando falta configurar credenciales"""
    while True:
        imprimir_banner()

        print(f"""
  {Colores.AMARILLO}╔══════════════════════════════════════════════════════════════╗
  ║      SISTEMA INSTALADO - ESPERANDO CREDENCIALES             ║
  ╚══════════════════════════════════════════════════════════════╝{Colores.RESET}

  El sistema esta instalado pero necesita credenciales para operar.

    {Colores.VERDE}[1]{Colores.RESET} Configurar credenciales ahora
    {Colores.VERDE}[2]{Colores.RESET} Editar archivo .env manualmente
    {Colores.CYAN}[3]{Colores.RESET} Ver estado del sistema
    {Colores.AMARILLO}[4]{Colores.RESET} Intentar ejecutar SAC (sin validar credenciales)

    {Colores.ROJO}[0]{Colores.RESET} Salir
""")

        try:
            opcion = input(f"  {Colores.CYAN}Seleccione opcion: {Colores.RESET}").strip()

            if opcion == '1':
                ejecutar_instalador()  # El instalador tiene GUI de credenciales

                # Re-verificar
                info = verificar_sistema()
                if info.credenciales_ok:
                    imprimir_ok("Credenciales configuradas correctamente")
                    input(f"\n  {Colores.CYAN}Presione Enter para continuar...{Colores.RESET}")
                    return True  # Credenciales configuradas, continuar

            elif opcion == '2':
                if not ENV_FILE.exists():
                    env_template = BASE_DIR / 'env'
                    if env_template.exists():
                        import shutil
                        shutil.copy(env_template, ENV_FILE)
                        imprimir_ok("Archivo .env creado desde template")

                imprimir_info(f"Archivo .env ubicado en:\n    {ENV_FILE}")
                imprimir_info("Edite el archivo con sus credenciales y vuelva a ejecutar")
                input(f"\n  {Colores.CYAN}Presione Enter para continuar...{Colores.RESET}")

            elif opcion == '3':
                info = verificar_sistema()
                mostrar_estado_sistema(info)
                input(f"\n  {Colores.CYAN}Presione Enter para continuar...{Colores.RESET}")

            elif opcion == '4':
                return True  # Continuar sin validar

            elif opcion == '0':
                print(f"\n  {Colores.CYAN}Hasta pronto - SAC{Colores.RESET}\n")
                return False

        except KeyboardInterrupt:
            return False


# ===============================================================================
# FLUJO PRINCIPAL
# ===============================================================================

def flujo_automatico():
    """Flujo automatico: detecta estado y actua en consecuencia"""
    imprimir_banner()

    imprimir_proceso("Verificando estado del sistema...")
    print()

    info = verificar_sistema()

    # Sistema no instalado
    if info.estado == EstadoSistema.NO_INSTALADO:
        imprimir_warn(info.mensaje)
        print()

        print(f"""
  {Colores.CYAN}╔══════════════════════════════════════════════════════════════╗
  ║              INSTALACION DE SAC                              ║
  ╠══════════════════════════════════════════════════════════════╣
  ║                                                              ║
  ║  Se detecta que el sistema no esta instalado.                ║
  ║  El instalador automatico ejecutara:                         ║
  ║                                                              ║
  ║   1. Verificacion de requisitos                              ║
  ║   2. Instalacion de dependencias                             ║
  ║   3. Creacion de estructura                                  ║
  ║   4. Configuracion de credenciales (al final)                ║
  ║                                                              ║
  ╚══════════════════════════════════════════════════════════════╝
{Colores.RESET}
""")

        try:
            input(f"  {Colores.CYAN}Presione Enter para iniciar instalacion...{Colores.RESET}")
        except KeyboardInterrupt:
            print()
            return

        if ejecutar_instalador():
            imprimir_ok("Instalacion completada")

            # Re-verificar y continuar
            info = verificar_sistema()
        else:
            imprimir_error("Error en la instalacion")
            return

    # Sistema con instalacion parcial
    if info.estado == EstadoSistema.INSTALACION_PARCIAL:
        imprimir_warn("Instalacion parcial detectada")
        imprimir_info("Completando instalacion...")

        if ejecutar_instalador():
            info = verificar_sistema()

    # Sin credenciales
    if info.estado == EstadoSistema.SIN_CREDENCIALES:
        if not mostrar_menu_sin_credenciales():
            return

        # Re-verificar
        info = verificar_sistema()

    # Error de Python u otro error fatal
    if info.estado == EstadoSistema.ERROR:
        imprimir_error(info.mensaje)
        return

    # Sistema listo - mostrar menu principal
    if info.estado == EstadoSistema.LISTO or info.credenciales_ok:
        mostrar_menu_principal()


# ===============================================================================
# MAIN
# ===============================================================================

def main():
    """Funcion principal"""
    parser = argparse.ArgumentParser(
        description='SAC - Script Maestro Unificado v' + VERSION,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python SAC.py                     # Modo automatico/interactivo
  python SAC.py --instalar          # Forzar instalacion
  python SAC.py --menu              # Menu principal
  python SAC.py --monitor           # Monitor en tiempo real
  python SAC.py --validar OC123     # Validar OC especifica
  python SAC.py --reporte           # Generar reporte diario
  python SAC.py --daemon            # Modo servicio
  python SAC.py --status            # Ver estado del sistema

Desarrollado por ADMJAJA - CEDIS Cancun 427
        """
    )

    parser.add_argument('--version', '-v', action='store_true',
                        help='Mostrar version')
    parser.add_argument('--instalar', '-i', action='store_true',
                        help='Forzar instalacion del sistema')
    parser.add_argument('--reinstalar', action='store_true',
                        help='Reinstalar desde cero')
    parser.add_argument('--menu', '-m', action='store_true',
                        help='Mostrar menu principal')
    parser.add_argument('--monitor', action='store_true',
                        help='Ejecutar monitor en tiempo real')
    parser.add_argument('--validar', '--oc', metavar='OC',
                        help='Validar OC especifica')
    parser.add_argument('--reporte', '--reporte-diario', action='store_true',
                        help='Generar reporte diario')
    parser.add_argument('--daemon', action='store_true',
                        help='Ejecutar en modo daemon (tareas programadas)')
    parser.add_argument('--status', '-s', action='store_true',
                        help='Mostrar estado del sistema')

    args = parser.parse_args()

    # Version
    if args.version:
        print(f"SAC - Sistema de Automatizacion de Consultas v{VERSION}")
        print("CEDIS Cancun 427 - Tiendas Chedraui")
        print(f"Python: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
        print(f"Plataforma: {platform.system()} {platform.release()}")
        return 0

    # Status
    if args.status:
        imprimir_banner()
        info = verificar_sistema()
        mostrar_estado_sistema(info)
        return 0 if info.estado == EstadoSistema.LISTO else 1

    # Reinstalar
    if args.reinstalar:
        imprimir_banner()
        imprimir_warn("Modo reinstalacion activado")
        if INSTALADO_FLAG.exists():
            INSTALADO_FLAG.unlink()
        if ENV_FILE.exists():
            ENV_FILE.unlink()
        return 0 if ejecutar_instalador() else 1

    # Instalar
    if args.instalar:
        imprimir_banner()
        return 0 if ejecutar_instalador() else 1

    # Verificar sistema antes de operaciones que lo requieren
    info = verificar_sistema()

    # Monitor
    if args.monitor:
        if info.estado != EstadoSistema.LISTO:
            imprimir_banner()
            imprimir_error("Sistema no instalado. Ejecute: python SAC.py --instalar")
            return 1
        imprimir_banner()
        return 0 if ejecutar_monitor() else 1

    # Validar OC
    if args.validar:
        if info.estado != EstadoSistema.LISTO:
            imprimir_banner()
            imprimir_error("Sistema no instalado. Ejecute: python SAC.py --instalar")
            return 1
        imprimir_banner()
        return 0 if ejecutar_validacion_oc(args.validar) else 1

    # Reporte
    if args.reporte:
        if info.estado != EstadoSistema.LISTO:
            imprimir_banner()
            imprimir_error("Sistema no instalado. Ejecute: python SAC.py --instalar")
            return 1
        imprimir_banner()
        return 0 if ejecutar_reporte_diario() else 1

    # Daemon
    if args.daemon:
        if info.estado != EstadoSistema.LISTO:
            imprimir_banner()
            imprimir_error("Sistema no instalado. Ejecute: python SAC.py --instalar")
            return 1
        imprimir_banner()
        return 0 if ejecutar_maestro_daemon() else 1

    # Menu
    if args.menu:
        if info.estado not in [EstadoSistema.LISTO, EstadoSistema.SIN_CREDENCIALES]:
            imprimir_banner()
            imprimir_error("Sistema no instalado. Ejecute: python SAC.py --instalar")
            return 1
        mostrar_menu_principal()
        return 0

    # Modo automatico por defecto
    flujo_automatico()
    return 0


# ===============================================================================
# EJECUCION
# ===============================================================================

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n\n  {Colores.CYAN}Hasta pronto - SAC{Colores.RESET}\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n  {Colores.ROJO}Error fatal: {e}{Colores.RESET}\n")
        sys.exit(1)
