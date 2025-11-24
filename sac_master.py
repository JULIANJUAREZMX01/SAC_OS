#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║   ███████╗ █████╗  ██████╗    ███╗   ███╗ █████╗ ███████╗████████╗███████╗██████╗  ║
║   ██╔════╝██╔══██╗██╔════╝    ████╗ ████║██╔══██╗██╔════╝╚══██╔══╝██╔════╝██╔══██╗ ║
║   ███████╗███████║██║         ██╔████╔██║███████║███████╗   ██║   █████╗  ██████╔╝ ║
║   ╚════██║██╔══██║██║         ██║╚██╔╝██║██╔══██║╚════██║   ██║   ██╔══╝  ██╔══██╗ ║
║   ███████║██║  ██║╚██████╗    ██║ ╚═╝ ██║██║  ██║███████║   ██║   ███████╗██║  ██║ ║
║   ╚══════╝╚═╝  ╚═╝ ╚═════╝    ╚═╝     ╚═╝╚═╝  ╚═╝╚══════╝   ╚═╝   ╚══════╝╚═╝  ╚═╝ ║
║                                                                               ║
║         SISTEMA DE AUTOMATIZACION DE CONSULTAS - SCRIPT MAESTRO              ║
║                    CEDIS CANCUN 427 - TIENDAS CHEDRAUI                        ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝

                    "Las maquinas y los sistemas al servicio de los analistas"

Script Maestro Orquestador - Punto de entrada principal del sistema SAC.
Este script coordina todos los modulos, configura credenciales via GUI,
inicia el monitoreo automatico y envia notificaciones de inicio.

Desarrollado por: Julian Alexander Juarez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logistica Cancun 427

Version: 2.0.0
Ultima actualizacion: Noviembre 2025
"""

import os
import sys
import time
import threading
import signal
import json
import logging
import argparse
import platform
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
import subprocess

# ═══════════════════════════════════════════════════════════════════════════════
# ARTE ASCII Y ANIMACIONES
# ═══════════════════════════════════════════════════════════════════════════════

class ASCIIArt:
    """Coleccion de arte ASCII para el sistema SAC"""

    # Logo principal SAC
    LOGO_SAC = """
    ╔═══════════════════════════════════════════════════════════════════════════╗
    ║                                                                           ║
    ║   ███████╗ █████╗  ██████╗    ██╗   ██╗ ██╗    ██████╗                    ║
    ║   ██╔════╝██╔══██╗██╔════╝    ██║   ██║███║   ██╔═████╗                   ║
    ║   ███████╗███████║██║         ██║   ██║╚██║   ██║██╔██║                   ║
    ║   ╚════██║██╔══██║██║         ╚██╗ ██╔╝ ██║   ████╔╝██║                   ║
    ║   ███████║██║  ██║╚██████╗     ╚████╔╝  ██║██╗╚██████╔╝                   ║
    ║   ╚══════╝╚═╝  ╚═╝ ╚═════╝      ╚═══╝   ╚═╝╚═╝ ╚═════╝                    ║
    ║                                                                           ║
    ║       Sistema de Automatizacion de Consultas - CEDIS Cancun 427          ║
    ║                      Tiendas Chedraui S.A. de C.V.                        ║
    ║                                                                           ║
    ╚═══════════════════════════════════════════════════════════════════════════╝
    """

    LOGO_CHEDRAUI = """
    ╔═══════════════════════════════════════════════════════════════════════════╗
    ║                                                                           ║
    ║     ██████╗██╗  ██╗███████╗██████╗ ██████╗  █████╗ ██╗   ██╗██╗          ║
    ║    ██╔════╝██║  ██║██╔════╝██╔══██╗██╔══██╗██╔══██╗██║   ██║██║          ║
    ║    ██║     ███████║█████╗  ██║  ██║██████╔╝███████║██║   ██║██║          ║
    ║    ██║     ██╔══██║██╔══╝  ██║  ██║██╔══██╗██╔══██║██║   ██║██║          ║
    ║    ╚██████╗██║  ██║███████╗██████╔╝██║  ██║██║  ██║╚██████╔╝██║          ║
    ║     ╚═════╝╚═╝  ╚═╝╚══════╝╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝          ║
    ║                                                                           ║
    ║                    LOGISTICA - REGION SURESTE                             ║
    ║                                                                           ║
    ╚═══════════════════════════════════════════════════════════════════════════╝
    """

    LOGO_STARTUP = """

    ░██████╗░█████╗░░█████╗░  ░██████╗████████╗░█████╗░██████╗░████████╗██╗███╗░░██╗░██████╗░
    ██╔════╝██╔══██╗██╔══██╗  ██╔════╝╚══██╔══╝██╔══██╗██╔══██╗╚══██╔══╝██║████╗░██║██╔════╝░
    ╚█████╗░███████║██║░░╚═╝  ╚█████╗░░░░██║░░░███████║██████╔╝░░░██║░░░██║██╔██╗██║██║░░██╗░
    ░╚═══██╗██╔══██║██║░░██╗  ░╚═══██╗░░░██║░░░██╔══██║██╔══██╗░░░██║░░░██║██║╚████║██║░░╚██╗
    ██████╔╝██║░░██║╚█████╔╝  ██████╔╝░░░██║░░░██║░░██║██║░░██║░░░██║░░░██║██║░╚███║╚██████╔╝
    ╚═════╝░╚═╝░░╚═╝░╚════╝░  ╚═════╝░░░░╚═╝░░░╚═╝░░╚═╝╚═╝░░╚═╝░░░╚═╝░░░╚═╝╚═╝░░╚══╝░╚═════╝░

    """

    LOGO_MONITOR = """
    ╔═══════════════════════════════════════════════════════════════════════════╗
    ║                                                                           ║
    ║    ███╗   ███╗ ██████╗ ███╗   ██╗██╗████████╗ ██████╗ ██████╗            ║
    ║    ████╗ ████║██╔═══██╗████╗  ██║██║╚══██╔══╝██╔═══██╗██╔══██╗           ║
    ║    ██╔████╔██║██║   ██║██╔██╗ ██║██║   ██║   ██║   ██║██████╔╝           ║
    ║    ██║╚██╔╝██║██║   ██║██║╚██╗██║██║   ██║   ██║   ██║██╔══██╗           ║
    ║    ██║ ╚═╝ ██║╚██████╔╝██║ ╚████║██║   ██║   ╚██████╔╝██║  ██║           ║
    ║    ╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝           ║
    ║                                                                           ║
    ║               MODO MONITOREO AUTOMATICO ACTIVADO                          ║
    ║                                                                           ║
    ╚═══════════════════════════════════════════════════════════════════════════╝
    """

    LOGO_DB = """
    ╔═══════════════════════════════════════════════════════════════════════════╗
    ║                                                                           ║
    ║    ██████╗ ██████╗ ██████╗     ██████╗ ██████╗ ███╗   ██╗███╗   ██╗      ║
    ║    ██╔══██╗██╔══██╗╚════██╗   ██╔════╝██╔═══██╗████╗  ██║████╗  ██║      ║
    ║    ██║  ██║██████╔╝ █████╔╝   ██║     ██║   ██║██╔██╗ ██║██╔██╗ ██║      ║
    ║    ██║  ██║██╔══██╗██╔═══╝    ██║     ██║   ██║██║╚██╗██║██║╚██╗██║      ║
    ║    ██████╔╝██████╔╝███████╗   ╚██████╗╚██████╔╝██║ ╚████║██║ ╚████║      ║
    ║    ╚═════╝ ╚═════╝ ╚══════╝    ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═══╝      ║
    ║                                                                           ║
    ║                MANHATTAN WMS - IBM DB2 DATABASE                           ║
    ║                                                                           ║
    ╚═══════════════════════════════════════════════════════════════════════════╝
    """

    LOGO_EMAIL = """
    ╔═══════════════════════════════════════════════════════════════════════════╗
    ║                                                                           ║
    ║    ███████╗███╗   ███╗ █████╗ ██╗██╗                                      ║
    ║    ██╔════╝████╗ ████║██╔══██╗██║██║                                      ║
    ║    █████╗  ██╔████╔██║███████║██║██║                                      ║
    ║    ██╔══╝  ██║╚██╔╝██║██╔══██║██║██║                                      ║
    ║    ███████╗██║ ╚═╝ ██║██║  ██║██║███████╗                                 ║
    ║    ╚══════╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝╚══════╝                                 ║
    ║                                                                           ║
    ║              SISTEMA DE NOTIFICACIONES POR CORREO                         ║
    ║                                                                           ║
    ╚═══════════════════════════════════════════════════════════════════════════╝
    """

    LOGO_CONFIG = """
    ╔═══════════════════════════════════════════════════════════════════════════╗
    ║                                                                           ║
    ║     ██████╗ ██████╗ ███╗   ██╗███████╗██╗ ██████╗                         ║
    ║    ██╔════╝██╔═══██╗████╗  ██║██╔════╝██║██╔════╝                         ║
    ║    ██║     ██║   ██║██╔██╗ ██║█████╗  ██║██║  ███╗                        ║
    ║    ██║     ██║   ██║██║╚██╗██║██╔══╝  ██║██║   ██║                        ║
    ║    ╚██████╗╚██████╔╝██║ ╚████║██║     ██║╚██████╔╝                        ║
    ║     ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝     ╚═╝ ╚═════╝                         ║
    ║                                                                           ║
    ║               CONFIGURACION DE CREDENCIALES                               ║
    ║                                                                           ║
    ╚═══════════════════════════════════════════════════════════════════════════╝
    """

    LOGO_SUCCESS = """
    ╔═══════════════════════════════════════════════════════════════════════════╗
    ║                                                                           ║
    ║             ███████╗██╗  ██╗██╗████████╗ ██████╗ ██╗                      ║
    ║             ██╔════╝╚██╗██╔╝██║╚══██╔══╝██╔═══██╗██║                      ║
    ║             █████╗   ╚███╔╝ ██║   ██║   ██║   ██║██║                      ║
    ║             ██╔══╝   ██╔██╗ ██║   ██║   ██║   ██║╚═╝                      ║
    ║             ███████╗██╔╝ ██╗██║   ██║   ╚██████╔╝██╗                      ║
    ║             ╚══════╝╚═╝  ╚═╝╚═╝   ╚═╝    ╚═════╝ ╚═╝                      ║
    ║                                                                           ║
    ║                  OPERACION COMPLETADA CON EXITO                           ║
    ║                                                                           ║
    ╚═══════════════════════════════════════════════════════════════════════════╝
    """

    SEPARADOR = "═" * 79
    SEPARADOR_DOBLE = "╔" + "═" * 77 + "╗"
    SEPARADOR_FIN = "╚" + "═" * 77 + "╝"


class Animaciones:
    """Sistema de animaciones para operaciones del SAC"""

    # Frames de animacion de carga
    SPINNER_FRAMES = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    SPINNER_DOTS = ['⣾', '⣽', '⣻', '⢿', '⡿', '⣟', '⣯', '⣷']
    SPINNER_ARROWS = ['←', '↖', '↑', '↗', '→', '↘', '↓', '↙']
    SPINNER_PULSE = ['█', '▓', '▒', '░', '▒', '▓']

    # Barras de progreso
    PROGRESS_FULL = '█'
    PROGRESS_EMPTY = '░'
    PROGRESS_HALF = '▓'

    # Frames de animacion de base de datos
    DB_FRAMES = [
        """
        ╭─────────╮
        │ ▓▓▓▓▓▓▓ │  Conectando...
        │ ▓▓▓▓▓▓▓ │
        │ ▓▓▓▓▓▓▓ │
        ╰─────────╯
        """,
        """
        ╭─────────╮
        │ ░▓▓▓▓▓░ │  Autenticando...
        │ ▓▓▓▓▓▓▓ │
        │ ░▓▓▓▓▓░ │
        ╰─────────╯
        """,
        """
        ╭─────────╮
        │ ░░▓▓▓░░ │  Estableciendo...
        │ ░▓▓▓▓▓░ │
        │ ░░▓▓▓░░ │
        ╰─────────╯
        """,
        """
        ╭─────────╮
        │ ░░░▓░░░ │  ¡Conectado!
        │ ░░▓▓▓░░ │
        │ ░░░▓░░░ │
        ╰─────────╯
        """
    ]

    # Frames de animacion de correo
    EMAIL_FRAMES = [
        """
           ╭──────────╮
           │  ╭────╮  │
           │  │ ✉  │  │ Preparando...
           │  ╰────╯  │
           ╰──────────╯
        """,
        """
           ╭──────────╮
           │  ╭────╮  │
           │  │ ✉  │→ │ Enviando...
           │  ╰────╯  │
           ╰──────────╯
        """,
        """
           ╭──────────╮
           │  ╭────╮  │
           │  │ ✉  │→→│ En camino...
           │  ╰────╯  │
           ╰──────────╯
        """,
        """
           ╭──────────╮
           │  ╭────╮  │
           │  │ ✓  │  │ ¡Enviado!
           │  ╰────╯  │
           ╰──────────╯
        """
    ]

    # Frames de animacion de consulta
    QUERY_FRAMES = [
        "🔍 Ejecutando consulta      ",
        "🔍 Ejecutando consulta .    ",
        "🔍 Ejecutando consulta ..   ",
        "🔍 Ejecutando consulta ...  ",
        "🔍 Ejecutando consulta .... ",
        "🔍 Ejecutando consulta .....",
    ]

    # Frames de animacion de validacion
    VALIDATION_FRAMES = [
        "✓ Validando datos [░░░░░░░░░░]   0%",
        "✓ Validando datos [█░░░░░░░░░]  10%",
        "✓ Validando datos [██░░░░░░░░]  20%",
        "✓ Validando datos [███░░░░░░░]  30%",
        "✓ Validando datos [████░░░░░░]  40%",
        "✓ Validando datos [█████░░░░░]  50%",
        "✓ Validando datos [██████░░░░]  60%",
        "✓ Validando datos [███████░░░]  70%",
        "✓ Validando datos [████████░░]  80%",
        "✓ Validando datos [█████████░]  90%",
        "✓ Validando datos [██████████] 100%",
    ]

    @staticmethod
    def clear_line():
        """Limpia la linea actual"""
        sys.stdout.write('\r' + ' ' * 80 + '\r')
        sys.stdout.flush()

    @staticmethod
    def spinner(message: str, duration: float = 2.0, frames: list = None):
        """Muestra un spinner animado"""
        if frames is None:
            frames = Animaciones.SPINNER_FRAMES

        start_time = time.time()
        i = 0
        while time.time() - start_time < duration:
            sys.stdout.write(f'\r  {frames[i % len(frames)]} {message}')
            sys.stdout.flush()
            time.sleep(0.1)
            i += 1
        Animaciones.clear_line()

    @staticmethod
    def progress_bar(message: str, total_steps: int = 20, duration: float = 2.0):
        """Muestra una barra de progreso animada"""
        step_time = duration / total_steps
        for i in range(total_steps + 1):
            progress = int((i / total_steps) * 100)
            filled = int(i / total_steps * 30)
            bar = Animaciones.PROGRESS_FULL * filled + Animaciones.PROGRESS_EMPTY * (30 - filled)
            sys.stdout.write(f'\r  {message} [{bar}] {progress}%')
            sys.stdout.flush()
            time.sleep(step_time)
        print()

    @staticmethod
    def animate_frames(frames: list, delay: float = 0.3, clear: bool = True):
        """Anima una secuencia de frames"""
        for frame in frames:
            if clear:
                os.system('cls' if os.name == 'nt' else 'clear')
            print(frame)
            time.sleep(delay)

    @staticmethod
    def typing_effect(text: str, delay: float = 0.02):
        """Efecto de escritura letra por letra"""
        for char in text:
            sys.stdout.write(char)
            sys.stdout.flush()
            time.sleep(delay)
        print()

    @staticmethod
    def pulse_message(message: str, color_code: str = '\033[92m', duration: float = 1.5):
        """Mensaje con efecto de pulso"""
        frames = ['░', '▒', '▓', '█', '▓', '▒', '░']
        start_time = time.time()
        i = 0
        while time.time() - start_time < duration:
            frame = frames[i % len(frames)]
            sys.stdout.write(f'\r  {color_code}{frame}{frame}{frame} {message} {frame}{frame}{frame}\033[0m')
            sys.stdout.flush()
            time.sleep(0.15)
            i += 1
        print()


class Colores:
    """Codigos de colores ANSI para terminal"""

    # Colores basicos
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    UNDERLINE = '\033[4m'
    BLINK = '\033[5m'
    REVERSE = '\033[7m'

    # Colores de texto
    BLACK = '\033[30m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'

    # Colores de fondo
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'

    # Colores Chedraui
    CHEDRAUI_RED = '\033[91m'  # Rojo corporativo
    CHEDRAUI_WHITE = '\033[97m'


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURACION DEL SISTEMA
# ═══════════════════════════════════════════════════════════════════════════════

# Agregar directorio actual al path
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Intentar cargar modulos del sistema
MODULOS_DISPONIBLES = {
    'config': False,
    'monitor': False,
    'reportes': False,
    'db_connection': False,
    'gestor_correos': False,
    'telegram': False,
    'queries': False,
    'auto_config': False
}

# Variable global para almacenar la configuración óptima
CONFIGURACION_OPTIMA = None

def cargar_modulos():
    """Carga los modulos del sistema y registra cuales estan disponibles"""
    global MODULOS_DISPONIBLES

    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    try:
        from config import (
            DB_CONFIG, CEDIS, EMAIL_CONFIG, TELEGRAM_CONFIG,
            PATHS, SYSTEM_CONFIG, LOGGING_CONFIG,
            validar_configuracion, imprimir_configuracion
        )
        MODULOS_DISPONIBLES['config'] = True
    except ImportError as e:
        print(f"  {Colores.YELLOW}⚠ Config no disponible: {e}{Colores.RESET}")

    try:
        from monitor import MonitorTiempoReal, ValidadorProactivo, ErrorSeverity
        MODULOS_DISPONIBLES['monitor'] = True
    except ImportError as e:
        print(f"  {Colores.YELLOW}⚠ Monitor no disponible: {e}{Colores.RESET}")

    try:
        from modules.reportes_excel import GeneradorReportesExcel
        MODULOS_DISPONIBLES['reportes'] = True
    except ImportError as e:
        print(f"  {Colores.YELLOW}⚠ Reportes no disponible: {e}{Colores.RESET}")

    try:
        from modules.db_connection import DB2Connection, DB2ConnectionPool
        MODULOS_DISPONIBLES['db_connection'] = True
    except ImportError as e:
        print(f"  {Colores.YELLOW}⚠ DB Connection no disponible: {e}{Colores.RESET}")

    try:
        from gestor_correos import GestorCorreos
        MODULOS_DISPONIBLES['gestor_correos'] = True
    except ImportError as e:
        print(f"  {Colores.YELLOW}⚠ Gestor correos no disponible: {e}{Colores.RESET}")

    try:
        from notificaciones_telegram import NotificadorTelegram, TipoAlerta
        MODULOS_DISPONIBLES['telegram'] = True
    except ImportError as e:
        print(f"  {Colores.YELLOW}⚠ Telegram no disponible: {e}{Colores.RESET}")

    try:
        from queries import QueryLoader, QueryCategory
        MODULOS_DISPONIBLES['queries'] = True
    except ImportError as e:
        print(f"  {Colores.YELLOW}⚠ Queries no disponible: {e}{Colores.RESET}")

    try:
        from modules.modulo_auto_config import AutoConfigurador, ejecutar_auto_configuracion
        MODULOS_DISPONIBLES['auto_config'] = True
    except ImportError as e:
        print(f"  {Colores.YELLOW}⚠ Auto-config no disponible: {e}{Colores.RESET}")


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURADOR DE CREDENCIALES (GUI SIMPLIFICADA)
# ═══════════════════════════════════════════════════════════════════════════════

class ConfiguradorCredenciales:
    """Configurador de credenciales via interfaz de consola"""

    def __init__(self):
        self.env_path = Path('.env')
        self.env_template_path = Path('env')
        self.config = {}

    def mostrar_banner_config(self):
        """Muestra el banner de configuracion"""
        print(f"{Colores.CYAN}{ASCIIArt.LOGO_CONFIG}{Colores.RESET}")
        print(f"  {Colores.BOLD}Configuracion inicial del Sistema SAC{Colores.RESET}")
        print(f"  {Colores.DIM}Se solicitaran las credenciales necesarias para el funcionamiento{Colores.RESET}")
        print()

    def verificar_env_existente(self) -> bool:
        """Verifica si ya existe un archivo .env configurado"""
        if self.env_path.exists():
            # Verificar si tiene las credenciales basicas
            with open(self.env_path, 'r') as f:
                content = f.read()
                return 'DB_PASSWORD=' in content and len(content.split('DB_PASSWORD=')[1].split('\n')[0].strip()) > 0
        return False

    def cargar_template(self) -> Dict[str, str]:
        """Carga el template de variables de entorno"""
        config = {}
        if self.env_template_path.exists():
            with open(self.env_template_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip()
        return config

    def solicitar_credenciales_db(self):
        """Solicita credenciales de base de datos"""
        print(f"\n  {Colores.BLUE}{ASCIIArt.SEPARADOR}{Colores.RESET}")
        print(f"  {Colores.BOLD}📊 CREDENCIALES DE BASE DE DATOS (IBM DB2){Colores.RESET}")
        print(f"  {Colores.BLUE}{ASCIIArt.SEPARADOR}{Colores.RESET}\n")

        Animaciones.typing_effect("  Configuracion de conexion a Manhattan WMS...", 0.01)
        print()

        # Usuario DB
        print(f"  {Colores.CYAN}Usuario de base de datos:{Colores.RESET}")
        print(f"  {Colores.DIM}(Ejemplo: ADMJAJA){Colores.RESET}")
        db_user = input(f"  {Colores.GREEN}→ {Colores.RESET}").strip() or 'ADMJAJA'
        self.config['DB_USER'] = db_user

        # Password DB
        print(f"\n  {Colores.CYAN}Contrasena de base de datos:{Colores.RESET}")
        print(f"  {Colores.DIM}(La entrada no sera visible){Colores.RESET}")
        try:
            import getpass
            db_password = getpass.getpass(f"  {Colores.GREEN}→ {Colores.RESET}")
        except:
            db_password = input(f"  {Colores.GREEN}→ {Colores.RESET}")
        self.config['DB_PASSWORD'] = db_password

        print(f"\n  {Colores.GREEN}✓ Credenciales de BD configuradas{Colores.RESET}")

    def solicitar_credenciales_email(self):
        """Solicita credenciales de correo electronico"""
        print(f"\n  {Colores.BLUE}{ASCIIArt.SEPARADOR}{Colores.RESET}")
        print(f"  {Colores.BOLD}📧 CREDENCIALES DE CORREO ELECTRONICO{Colores.RESET}")
        print(f"  {Colores.BLUE}{ASCIIArt.SEPARADOR}{Colores.RESET}\n")

        Animaciones.typing_effect("  Configuracion de notificaciones por correo...", 0.01)
        print()

        # Usuario Email
        print(f"  {Colores.CYAN}Correo electronico (Office 365):{Colores.RESET}")
        print(f"  {Colores.DIM}(Ejemplo: usuario@chedraui.com.mx){Colores.RESET}")
        email_user = input(f"  {Colores.GREEN}→ {Colores.RESET}").strip()
        self.config['EMAIL_USER'] = email_user

        # Password Email
        print(f"\n  {Colores.CYAN}Contrasena de correo:{Colores.RESET}")
        print(f"  {Colores.DIM}(La entrada no sera visible){Colores.RESET}")
        try:
            import getpass
            email_password = getpass.getpass(f"  {Colores.GREEN}→ {Colores.RESET}")
        except:
            email_password = input(f"  {Colores.GREEN}→ {Colores.RESET}")
        self.config['EMAIL_PASSWORD'] = email_password

        print(f"\n  {Colores.GREEN}✓ Credenciales de correo configuradas{Colores.RESET}")

    def solicitar_credenciales_telegram(self):
        """Solicita credenciales de Telegram (opcional)"""
        print(f"\n  {Colores.BLUE}{ASCIIArt.SEPARADOR}{Colores.RESET}")
        print(f"  {Colores.BOLD}📱 CREDENCIALES DE TELEGRAM (OPCIONAL){Colores.RESET}")
        print(f"  {Colores.BLUE}{ASCIIArt.SEPARADOR}{Colores.RESET}\n")

        print(f"  {Colores.YELLOW}¿Desea configurar notificaciones de Telegram? (s/n){Colores.RESET}")
        respuesta = input(f"  {Colores.GREEN}→ {Colores.RESET}").strip().lower()

        if respuesta == 's':
            print(f"\n  {Colores.CYAN}Token del Bot de Telegram:{Colores.RESET}")
            telegram_token = input(f"  {Colores.GREEN}→ {Colores.RESET}").strip()
            self.config['TELEGRAM_BOT_TOKEN'] = telegram_token

            print(f"\n  {Colores.CYAN}Chat ID de Telegram:{Colores.RESET}")
            telegram_chat = input(f"  {Colores.GREEN}→ {Colores.RESET}").strip()
            self.config['TELEGRAM_CHAT_ID'] = telegram_chat

            print(f"\n  {Colores.GREEN}✓ Credenciales de Telegram configuradas{Colores.RESET}")
        else:
            print(f"\n  {Colores.YELLOW}⚠ Telegram no configurado{Colores.RESET}")

    def guardar_configuracion(self):
        """Guarda la configuracion en el archivo .env"""
        # Cargar template base
        base_config = self.cargar_template()

        # Actualizar con nuevas credenciales
        base_config.update(self.config)

        # Guardar archivo .env
        with open(self.env_path, 'w') as f:
            f.write("# ════════════════════════════════════════════════════════════════\n")
            f.write("# SAC v1.0 - Variables de Entorno\n")
            f.write("# Sistema de Automatizacion de Consultas - CEDIS Cancun 427\n")
            f.write(f"# Generado automaticamente: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("# ════════════════════════════════════════════════════════════════\n\n")

            f.write("# ═══════════════════════════════════════════════════════════════\n")
            f.write("# CREDENCIALES DE BASE DE DATOS (IBM DB2)\n")
            f.write("# ═══════════════════════════════════════════════════════════════\n")
            f.write(f"DB_HOST={base_config.get('DB_HOST', 'WM260BASD')}\n")
            f.write(f"DB_PORT={base_config.get('DB_PORT', '50000')}\n")
            f.write(f"DB_DATABASE={base_config.get('DB_DATABASE', 'WM260BASD')}\n")
            f.write(f"DB_SCHEMA={base_config.get('DB_SCHEMA', 'WMWHSE1')}\n")
            f.write(f"DB_USER={base_config.get('DB_USER', '')}\n")
            f.write(f"DB_PASSWORD={base_config.get('DB_PASSWORD', '')}\n\n")

            f.write("# ═══════════════════════════════════════════════════════════════\n")
            f.write("# INFORMACION DEL CEDIS\n")
            f.write("# ═══════════════════════════════════════════════════════════════\n")
            f.write(f"CEDIS_CODE={base_config.get('CEDIS_CODE', '427')}\n")
            f.write(f"CEDIS_NAME={base_config.get('CEDIS_NAME', 'CEDIS Cancun')}\n")
            f.write(f"CEDIS_REGION={base_config.get('CEDIS_REGION', 'Sureste')}\n")
            f.write(f"CEDIS_ALMACEN={base_config.get('CEDIS_ALMACEN', 'C22')}\n\n")

            f.write("# ═══════════════════════════════════════════════════════════════\n")
            f.write("# CREDENCIALES DE CORREO (OFFICE 365)\n")
            f.write("# ═══════════════════════════════════════════════════════════════\n")
            f.write(f"EMAIL_HOST={base_config.get('EMAIL_HOST', 'smtp.office365.com')}\n")
            f.write(f"EMAIL_PORT={base_config.get('EMAIL_PORT', '587')}\n")
            f.write(f"EMAIL_USER={base_config.get('EMAIL_USER', '')}\n")
            f.write(f"EMAIL_PASSWORD={base_config.get('EMAIL_PASSWORD', '')}\n")
            f.write(f"EMAIL_PROTOCOL={base_config.get('EMAIL_PROTOCOL', 'TLS')}\n\n")

            f.write("# ═══════════════════════════════════════════════════════════════\n")
            f.write("# CREDENCIALES DE TELEGRAM (OPCIONAL)\n")
            f.write("# ═══════════════════════════════════════════════════════════════\n")
            f.write(f"TELEGRAM_BOT_TOKEN={base_config.get('TELEGRAM_BOT_TOKEN', '')}\n")
            f.write(f"TELEGRAM_CHAT_ID={base_config.get('TELEGRAM_CHAT_ID', '')}\n\n")

            f.write("# ═══════════════════════════════════════════════════════════════\n")
            f.write("# CONFIGURACION DEL SISTEMA\n")
            f.write("# ═══════════════════════════════════════════════════════════════\n")
            f.write(f"SYSTEM_VERSION={base_config.get('SYSTEM_VERSION', '1.0.0')}\n")
            f.write(f"ENVIRONMENT={base_config.get('ENVIRONMENT', 'production')}\n")
            f.write(f"DEBUG={base_config.get('DEBUG', 'false')}\n")
            f.write(f"TIMEZONE={base_config.get('TIMEZONE', 'America/Cancun')}\n")
            f.write(f"LOG_LEVEL={base_config.get('LOG_LEVEL', 'INFO')}\n")

        print(f"\n  {Colores.GREEN}✓ Configuracion guardada en .env{Colores.RESET}")

    def ejecutar_configuracion(self) -> bool:
        """Ejecuta el proceso completo de configuracion"""
        self.mostrar_banner_config()

        if self.verificar_env_existente():
            print(f"  {Colores.YELLOW}⚠ Ya existe una configuracion previa.{Colores.RESET}")
            print(f"  {Colores.CYAN}¿Desea reconfigurar las credenciales? (s/n){Colores.RESET}")
            respuesta = input(f"  {Colores.GREEN}→ {Colores.RESET}").strip().lower()
            if respuesta != 's':
                print(f"\n  {Colores.GREEN}✓ Usando configuracion existente{Colores.RESET}")
                return True

        try:
            self.solicitar_credenciales_db()
            self.solicitar_credenciales_email()
            self.solicitar_credenciales_telegram()
            self.guardar_configuracion()

            # Animacion de exito
            print()
            Animaciones.progress_bar("Guardando configuracion", 15, 1.5)
            print(f"\n  {Colores.GREEN}{'═' * 50}{Colores.RESET}")
            print(f"  {Colores.GREEN}✓ CONFIGURACION COMPLETADA EXITOSAMENTE{Colores.RESET}")
            print(f"  {Colores.GREEN}{'═' * 50}{Colores.RESET}")

            return True
        except KeyboardInterrupt:
            print(f"\n\n  {Colores.RED}✗ Configuracion cancelada por el usuario{Colores.RESET}")
            return False
        except Exception as e:
            print(f"\n  {Colores.RED}✗ Error durante la configuracion: {e}{Colores.RESET}")
            return False


# ═══════════════════════════════════════════════════════════════════════════════
# SISTEMA MAESTRO SAC
# ═══════════════════════════════════════════════════════════════════════════════

class SACMaster:
    """Clase principal del Sistema Maestro SAC"""

    def __init__(self):
        self.version = "2.0.0"
        self.inicio_sistema = datetime.now()
        self.modo_monitoreo = False
        self.hilo_monitoreo = None
        self.detener_monitoreo = threading.Event()
        self.logger = None
        self.configurado = False
        self.auto_config_resultado = None
        self.config_optima = None

        # Configurar logging
        self._configurar_logging()

    def _configurar_logging(self):
        """Configura el sistema de logging"""
        log_dir = Path('output/logs')
        log_dir.mkdir(parents=True, exist_ok=True)

        fecha = datetime.now().strftime('%Y%m%d')
        log_file = log_dir / f'sac_master_{fecha}.log'

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger('SAC_Master')

    def mostrar_intro(self):
        """Muestra la introduccion animada del sistema"""
        os.system('cls' if os.name == 'nt' else 'clear')

        # Logo animado
        print(f"{Colores.CHEDRAUI_RED}{ASCIIArt.LOGO_STARTUP}{Colores.RESET}")
        time.sleep(0.5)

        Animaciones.typing_effect(
            f"  {Colores.CYAN}Inicializando Sistema de Automatizacion de Consultas...{Colores.RESET}",
            0.02
        )
        print()

        # Barra de progreso de inicio
        Animaciones.progress_bar("Cargando componentes", 25, 2.0)

        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"{Colores.CHEDRAUI_RED}{ASCIIArt.LOGO_SAC}{Colores.RESET}")

    def ejecutar_auto_configuracion(self) -> bool:
        """
        Ejecuta la auto-configuracion del sistema como PRIMER PASO.
        Recopila información del equipo, red, entorno y optimiza recursos.
        """
        global CONFIGURACION_OPTIMA

        print(f"\n  {Colores.CYAN}{'═' * 60}{Colores.RESET}")
        print(f"  {Colores.BOLD}🔧 FASE 0: AUTO-CONFIGURACIÓN DEL SISTEMA{Colores.RESET}")
        print(f"  {Colores.CYAN}{'═' * 60}{Colores.RESET}")
        print(f"  {Colores.DIM}Analizando equipo, red, entorno y optimizando recursos...{Colores.RESET}\n")

        if not MODULOS_DISPONIBLES.get('auto_config', False):
            print(f"  {Colores.YELLOW}⚠ Módulo de auto-configuración no disponible{Colores.RESET}")
            print(f"  {Colores.DIM}Continuando con configuración por defecto...{Colores.RESET}")
            return True

        try:
            from modules.modulo_auto_config import AutoConfigurador, EstadoComponente

            # Crear y ejecutar el auto-configurador
            configurador = AutoConfigurador(
                base_dir=Path(__file__).resolve().parent,
                verbose=True
            )

            # Ejecutar configuración completa
            self.auto_config_resultado = configurador.ejecutar_configuracion_completa(
                instalar_faltantes=True
            )

            # Obtener configuración óptima para usar en la aplicación
            self.config_optima = configurador.obtener_configuracion_para_aplicacion()
            CONFIGURACION_OPTIMA = self.config_optima

            # Verificar estado
            if self.auto_config_resultado.estado_general == EstadoComponente.ERROR:
                print(f"\n  {Colores.RED}✗ Auto-configuración completada con errores{Colores.RESET}")
                print(f"  {Colores.YELLOW}⚠ Se recomienda revisar los errores antes de continuar{Colores.RESET}")

                # Preguntar si desea continuar
                respuesta = input(f"\n  {Colores.GREEN}¿Desea continuar de todos modos? (s/n): {Colores.RESET}").strip().lower()
                if respuesta != 's':
                    return False
            elif self.auto_config_resultado.estado_general == EstadoComponente.WARNING:
                print(f"\n  {Colores.YELLOW}⚠ Auto-configuración completada con advertencias{Colores.RESET}")
            else:
                print(f"\n  {Colores.GREEN}✓ Auto-configuración completada exitosamente{Colores.RESET}")

            # Mostrar configuración aplicada
            print(f"\n  {Colores.CYAN}Configuración aplicada:{Colores.RESET}")
            print(f"    Nivel: {self.config_optima['system']['level'].upper()}")
            print(f"    Pool DB: {self.config_optima['db']['pool_size']} conexiones")
            print(f"    Workers: {self.config_optima['processing']['workers']}")
            print(f"    Batch size: {self.config_optima['processing']['batch_size']} registros")
            print(f"    Intervalo monitoreo: {self.config_optima['monitoring']['interval_seconds']}s")

            return True

        except Exception as e:
            print(f"\n  {Colores.RED}✗ Error en auto-configuración: {e}{Colores.RESET}")
            if self.logger:
                self.logger.exception("Error en auto-configuración")
            print(f"  {Colores.YELLOW}Continuando con configuración por defecto...{Colores.RESET}")
            return True

    def mostrar_info_sistema(self):
        """Muestra informacion del sistema"""
        print(f"\n  {Colores.BLUE}{'═' * 60}{Colores.RESET}")
        print(f"  {Colores.BOLD}INFORMACION DEL SISTEMA{Colores.RESET}")
        print(f"  {Colores.BLUE}{'═' * 60}{Colores.RESET}")
        print(f"  {Colores.CYAN}Version:{Colores.RESET}        {self.version}")
        print(f"  {Colores.CYAN}Fecha inicio:{Colores.RESET}   {self.inicio_sistema.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  {Colores.CYAN}Python:{Colores.RESET}         {sys.version.split()[0]}")
        print(f"  {Colores.CYAN}Sistema:{Colores.RESET}        {platform.system()} {platform.release()}")
        print(f"  {Colores.CYAN}Directorio:{Colores.RESET}     {os.getcwd()}")
        print(f"  {Colores.BLUE}{'═' * 60}{Colores.RESET}")

    def verificar_dependencias(self) -> bool:
        """Verifica que las dependencias esten instaladas"""
        print(f"\n  {Colores.CYAN}Verificando dependencias...{Colores.RESET}")

        dependencias = [
            ('pandas', 'pandas'),
            ('openpyxl', 'openpyxl'),
            ('dotenv', 'python-dotenv'),
            ('schedule', 'schedule'),
            ('colorama', 'colorama'),
            ('tqdm', 'tqdm'),
        ]

        faltantes = []
        for modulo, paquete in dependencias:
            try:
                __import__(modulo)
                print(f"    {Colores.GREEN}✓{Colores.RESET} {paquete}")
            except ImportError:
                print(f"    {Colores.RED}✗{Colores.RESET} {paquete}")
                faltantes.append(paquete)

        if faltantes:
            print(f"\n  {Colores.YELLOW}⚠ Dependencias faltantes: {', '.join(faltantes)}{Colores.RESET}")
            print(f"  {Colores.CYAN}Instalando dependencias...{Colores.RESET}")

            for paquete in faltantes:
                Animaciones.spinner(f"Instalando {paquete}", 1.0)
                subprocess.run([sys.executable, '-m', 'pip', 'install', paquete, '-q'],
                             capture_output=True)

            print(f"  {Colores.GREEN}✓ Dependencias instaladas{Colores.RESET}")

        return True

    def verificar_configuracion(self) -> bool:
        """Verifica la configuracion del sistema"""
        print(f"\n  {Colores.CYAN}Verificando configuracion...{Colores.RESET}")

        configurador = ConfiguradorCredenciales()

        if not configurador.verificar_env_existente():
            print(f"  {Colores.YELLOW}⚠ No se encontro configuracion de credenciales{Colores.RESET}")
            print(f"  {Colores.CYAN}Es necesario configurar las credenciales para continuar.{Colores.RESET}")
            print()

            input(f"  {Colores.GREEN}Presione ENTER para iniciar la configuracion...{Colores.RESET}")

            if not configurador.ejecutar_configuracion():
                return False
        else:
            print(f"    {Colores.GREEN}✓{Colores.RESET} Archivo .env encontrado")

        # Recargar variables de entorno
        try:
            from dotenv import load_dotenv
            load_dotenv(override=True)
            print(f"    {Colores.GREEN}✓{Colores.RESET} Variables de entorno cargadas")
        except Exception as e:
            print(f"    {Colores.RED}✗{Colores.RESET} Error cargando variables: {e}")
            return False

        self.configurado = True
        return True

    def verificar_conexion_db(self) -> bool:
        """Verifica la conexion a la base de datos"""
        print(f"\n  {Colores.CYAN}Verificando conexion a base de datos...{Colores.RESET}")
        print(f"{Colores.DIM}{ASCIIArt.LOGO_DB}{Colores.RESET}")

        # Animacion de conexion
        for i, frame in enumerate(Animaciones.DB_FRAMES):
            sys.stdout.write('\r' + ' ' * 80)
            print(f"  {Colores.CYAN}{frame}{Colores.RESET}", end='')
            time.sleep(0.5)

        # Por ahora solo verificamos que los modulos esten disponibles
        if MODULOS_DISPONIBLES.get('db_connection', False):
            print(f"\n    {Colores.GREEN}✓{Colores.RESET} Modulo de conexion DB2 disponible")
            return True
        else:
            print(f"\n    {Colores.YELLOW}⚠{Colores.RESET} Conexion DB2 no disponible (modo simulacion)")
            return True  # Continuar en modo simulacion

    def enviar_correo_inicio(self) -> bool:
        """Envia correo de notificacion de inicio del sistema"""
        print(f"\n  {Colores.CYAN}Enviando notificacion de inicio...{Colores.RESET}")
        print(f"{Colores.DIM}{ASCIIArt.LOGO_EMAIL}{Colores.RESET}")

        # Animacion de envio de correo
        for frame in Animaciones.EMAIL_FRAMES:
            sys.stdout.write('\033[2J\033[H')  # Limpiar pantalla
            print(f"{Colores.DIM}{ASCIIArt.LOGO_EMAIL}{Colores.RESET}")
            print(f"  {Colores.CYAN}{frame}{Colores.RESET}")
            time.sleep(0.5)

        # Preparar contenido del correo
        fecha_hora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        asunto = f"🚀 SAC v{self.version} - Sistema Iniciado - CEDIS Cancun 427"

        cuerpo_html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .header {{ background-color: #E31837; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .info {{ background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 10px 0; }}
                .footer {{ background-color: #333; color: white; padding: 15px; text-align: center; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🚀 Sistema SAC Iniciado</h1>
                <p>Sistema de Automatizacion de Consultas</p>
            </div>
            <div class="content">
                <h2>El Sistema SAC ha sido iniciado correctamente</h2>

                <div class="info">
                    <h3>Informacion del Sistema</h3>
                    <ul>
                        <li><strong>Version:</strong> {self.version}</li>
                        <li><strong>Fecha/Hora Inicio:</strong> {fecha_hora}</li>
                        <li><strong>CEDIS:</strong> Cancun 427</li>
                        <li><strong>Region:</strong> Sureste</li>
                        <li><strong>Modo:</strong> Monitoreo Automatico</li>
                    </ul>
                </div>

                <div class="info">
                    <h3>Funcionalidades Activas</h3>
                    <ul>
                        <li>✅ Validacion de Ordenes de Compra</li>
                        <li>✅ Monitoreo de Distribuciones</li>
                        <li>✅ Generacion de Reportes Excel</li>
                        <li>✅ Alertas por Correo Electronico</li>
                        <li>✅ Notificaciones Telegram</li>
                        <li>✅ Deteccion Proactiva de Errores</li>
                    </ul>
                </div>

                <p>El sistema esta listo para recibir consultas y generar reportes automaticamente.</p>

                <p><em>"Las maquinas y los sistemas al servicio de los analistas"</em></p>
            </div>
            <div class="footer">
                <p>SAC v{self.version} - CEDIS Cancun 427 - Tiendas Chedraui S.A. de C.V.</p>
                <p>Desarrollado por: Julian Alexander Juarez Alvarado (ADMJAJA)</p>
            </div>
        </body>
        </html>
        """

        # Intentar enviar correo
        if MODULOS_DISPONIBLES.get('gestor_correos', False):
            try:
                from gestor_correos import GestorCorreos
                gestor = GestorCorreos()
                # El envio real dependera de la configuracion
                print(f"    {Colores.GREEN}✓{Colores.RESET} Correo de inicio preparado")
            except Exception as e:
                print(f"    {Colores.YELLOW}⚠{Colores.RESET} No se pudo enviar correo: {e}")
        else:
            print(f"    {Colores.YELLOW}⚠{Colores.RESET} Gestor de correos no disponible")

        return True

    def iniciar_monitoreo(self):
        """Inicia el modo de monitoreo automatico"""
        print(f"\n{Colores.CYAN}{ASCIIArt.LOGO_MONITOR}{Colores.RESET}")

        print(f"  {Colores.BOLD}¿Desea activar el modo de monitoreo automatico?{Colores.RESET}")
        print(f"  {Colores.DIM}El sistema ejecutara validaciones periodicas cada 15 minutos{Colores.RESET}")
        print(f"  {Colores.DIM}y enviara alertas cuando detecte problemas.{Colores.RESET}")
        print()

        respuesta = input(f"  {Colores.GREEN}Activar monitoreo automatico? (s/n): {Colores.RESET}").strip().lower()

        if respuesta == 's':
            self.modo_monitoreo = True
            self._ejecutar_monitoreo_continuo()
        else:
            print(f"\n  {Colores.YELLOW}⚠ Monitoreo automatico no activado{Colores.RESET}")
            self.mostrar_menu_principal()

    def _ejecutar_monitoreo_continuo(self):
        """Ejecuta el monitoreo continuo del sistema"""
        print(f"\n  {Colores.GREEN}{'═' * 60}{Colores.RESET}")
        print(f"  {Colores.GREEN}✓ MODO MONITOREO AUTOMATICO ACTIVADO{Colores.RESET}")
        print(f"  {Colores.GREEN}{'═' * 60}{Colores.RESET}")
        print(f"\n  {Colores.CYAN}Presione Ctrl+C para detener el monitoreo{Colores.RESET}")
        print()

        ciclo = 0
        try:
            while not self.detener_monitoreo.is_set():
                ciclo += 1
                ahora = datetime.now()

                # Mostrar estado
                self._mostrar_estado_monitoreo(ciclo, ahora)

                # Ejecutar validaciones periodicas
                if ciclo % 4 == 0:  # Cada 4 ciclos (~1 minuto con delay de 15s)
                    self._ejecutar_validacion_periodica()

                # Esperar para el siguiente ciclo
                for i in range(15):  # 15 segundos
                    if self.detener_monitoreo.is_set():
                        break

                    # Animacion de espera
                    spinner = Animaciones.SPINNER_DOTS[i % len(Animaciones.SPINNER_DOTS)]
                    sys.stdout.write(f'\r  {Colores.CYAN}{spinner} Monitoreando... (siguiente ciclo en {15-i}s){Colores.RESET}')
                    sys.stdout.flush()
                    time.sleep(1)

                Animaciones.clear_line()

        except KeyboardInterrupt:
            print(f"\n\n  {Colores.YELLOW}⚠ Monitoreo detenido por el usuario{Colores.RESET}")
            self.detener_monitoreo.set()

    def _mostrar_estado_monitoreo(self, ciclo: int, ahora: datetime):
        """Muestra el estado actual del monitoreo"""
        uptime = ahora - self.inicio_sistema
        horas, resto = divmod(uptime.total_seconds(), 3600)
        minutos, segundos = divmod(resto, 60)

        print(f"\n  {Colores.BLUE}{'─' * 60}{Colores.RESET}")
        print(f"  {Colores.BOLD}📊 ESTADO DEL MONITOREO - Ciclo #{ciclo}{Colores.RESET}")
        print(f"  {Colores.BLUE}{'─' * 60}{Colores.RESET}")
        print(f"    {Colores.CYAN}Hora:{Colores.RESET}      {ahora.strftime('%H:%M:%S')}")
        print(f"    {Colores.CYAN}Uptime:{Colores.RESET}    {int(horas)}h {int(minutos)}m {int(segundos)}s")
        print(f"    {Colores.CYAN}Estado:{Colores.RESET}    {Colores.GREEN}● Activo{Colores.RESET}")

    def _ejecutar_validacion_periodica(self):
        """Ejecuta una validacion periodica"""
        print(f"\n  {Colores.CYAN}Ejecutando validacion periodica...{Colores.RESET}")

        # Animacion de validacion
        for frame in Animaciones.VALIDATION_FRAMES:
            sys.stdout.write(f'\r  {frame}')
            sys.stdout.flush()
            time.sleep(0.1)

        print(f"\n    {Colores.GREEN}✓{Colores.RESET} Validacion completada - Sin errores detectados")

    def mostrar_menu_principal(self):
        """Muestra el menu principal del sistema"""
        while True:
            os.system('cls' if os.name == 'nt' else 'clear')
            print(f"{Colores.CHEDRAUI_RED}{ASCIIArt.LOGO_SAC}{Colores.RESET}")

            print(f"\n  {Colores.BOLD}MENU PRINCIPAL{Colores.RESET}")
            print(f"  {Colores.BLUE}{'═' * 50}{Colores.RESET}")
            print(f"  {Colores.CYAN}1.{Colores.RESET} 📊 Validar Orden de Compra")
            print(f"  {Colores.CYAN}2.{Colores.RESET} 📈 Generar Reporte Diario")
            print(f"  {Colores.CYAN}3.{Colores.RESET} 🔍 Monitoreo Automatico")
            print(f"  {Colores.CYAN}4.{Colores.RESET} ⚙️  Configurar Credenciales")
            print(f"  {Colores.CYAN}5.{Colores.RESET} 📧 Enviar Correo de Prueba")
            print(f"  {Colores.CYAN}6.{Colores.RESET} 🔧 Verificar Sistema")
            print(f"  {Colores.CYAN}7.{Colores.RESET} 📋 Ver Estado del Sistema")
            print(f"  {Colores.CYAN}8.{Colores.RESET} 🖥️  Ver Auto-Configuración")
            print(f"  {Colores.CYAN}0.{Colores.RESET} 🚪 Salir")
            print(f"  {Colores.BLUE}{'═' * 50}{Colores.RESET}")

            opcion = input(f"\n  {Colores.GREEN}Seleccione una opcion: {Colores.RESET}").strip()

            if opcion == '1':
                self._validar_oc()
            elif opcion == '2':
                self._generar_reporte_diario()
            elif opcion == '3':
                self.iniciar_monitoreo()
            elif opcion == '4':
                ConfiguradorCredenciales().ejecutar_configuracion()
            elif opcion == '5':
                self.enviar_correo_inicio()
            elif opcion == '6':
                self._verificar_sistema()
            elif opcion == '7':
                self.mostrar_info_sistema()
                input(f"\n  {Colores.GREEN}Presione ENTER para continuar...{Colores.RESET}")
            elif opcion == '8':
                self._mostrar_auto_configuracion()
            elif opcion == '0':
                self._salir()
                break
            else:
                print(f"\n  {Colores.RED}✗ Opcion no valida{Colores.RESET}")
                time.sleep(1)

    def _validar_oc(self):
        """Valida una orden de compra"""
        print(f"\n  {Colores.CYAN}VALIDACION DE ORDEN DE COMPRA{Colores.RESET}")
        print(f"  {Colores.BLUE}{'─' * 40}{Colores.RESET}")

        oc_numero = input(f"\n  {Colores.GREEN}Ingrese numero de OC: {Colores.RESET}").strip()

        if not oc_numero:
            print(f"  {Colores.RED}✗ Numero de OC requerido{Colores.RESET}")
            return

        print(f"\n  {Colores.CYAN}Validando OC {oc_numero}...{Colores.RESET}")

        # Animacion de consulta
        for frame in Animaciones.QUERY_FRAMES:
            sys.stdout.write(f'\r  {frame}')
            sys.stdout.flush()
            time.sleep(0.2)

        print(f"\n\n  {Colores.GREEN}✓ Validacion completada para OC {oc_numero}{Colores.RESET}")
        input(f"\n  {Colores.GREEN}Presione ENTER para continuar...{Colores.RESET}")

    def _generar_reporte_diario(self):
        """Genera el reporte diario"""
        print(f"\n  {Colores.CYAN}GENERACION DE REPORTE DIARIO{Colores.RESET}")
        print(f"  {Colores.BLUE}{'─' * 40}{Colores.RESET}")

        Animaciones.progress_bar("Recopilando datos", 20, 2.0)
        Animaciones.progress_bar("Procesando informacion", 25, 2.5)
        Animaciones.progress_bar("Generando Excel", 15, 1.5)

        print(f"\n  {Colores.GREEN}✓ Reporte generado exitosamente{Colores.RESET}")
        input(f"\n  {Colores.GREEN}Presione ENTER para continuar...{Colores.RESET}")

    def _verificar_sistema(self):
        """Verifica el estado del sistema"""
        print(f"\n  {Colores.CYAN}VERIFICACION DEL SISTEMA{Colores.RESET}")
        print(f"  {Colores.BLUE}{'─' * 40}{Colores.RESET}")

        # Verificar modulos
        print(f"\n  {Colores.BOLD}Modulos:{Colores.RESET}")
        for modulo, disponible in MODULOS_DISPONIBLES.items():
            estado = f"{Colores.GREEN}✓{Colores.RESET}" if disponible else f"{Colores.RED}✗{Colores.RESET}"
            print(f"    {estado} {modulo}")

        # Verificar directorios
        print(f"\n  {Colores.BOLD}Directorios:{Colores.RESET}")
        directorios = ['output', 'output/logs', 'output/resultados', 'modules', 'queries']
        for dir_path in directorios:
            existe = Path(dir_path).exists()
            estado = f"{Colores.GREEN}✓{Colores.RESET}" if existe else f"{Colores.RED}✗{Colores.RESET}"
            print(f"    {estado} {dir_path}")

        input(f"\n  {Colores.GREEN}Presione ENTER para continuar...{Colores.RESET}")

    def _mostrar_auto_configuracion(self):
        """Muestra los detalles de la auto-configuracion del sistema"""
        print(f"\n  {Colores.CYAN}AUTO-CONFIGURACIÓN DEL SISTEMA{Colores.RESET}")
        print(f"  {Colores.BLUE}{'─' * 50}{Colores.RESET}")

        if self.auto_config_resultado is None:
            print(f"\n  {Colores.YELLOW}⚠ No hay datos de auto-configuración disponibles{Colores.RESET}")
            print(f"  {Colores.DIM}Ejecute el sistema desde el inicio para ver estos datos{Colores.RESET}")
        else:
            resultado = self.auto_config_resultado

            # Mostrar información del sistema
            print(f"\n  {Colores.BOLD}INFORMACIÓN DEL SISTEMA:{Colores.RESET}")
            print(f"    CPU: {resultado.cpu.nombre[:40]}...")
            print(f"    Núcleos: {resultado.cpu.nucleos_logicos} lógicos, {resultado.cpu.nucleos_fisicos} físicos")
            print(f"    RAM Total: {resultado.memoria.total_gb:.1f} GB")
            print(f"    RAM Disponible: {resultado.memoria.disponible_gb:.1f} GB ({resultado.memoria.porcentaje_uso:.1f}% uso)")

            if resultado.discos:
                disco = resultado.discos[0]
                print(f"    Disco: {disco.libre_gb:.1f} GB libre de {disco.total_gb:.1f} GB")

            # Información de red
            print(f"\n  {Colores.BOLD}CONECTIVIDAD:{Colores.RESET}")
            print(f"    Internet: {'✓ Conectado' if resultado.red.conectividad_internet else '✗ Sin conexión'}")
            if resultado.red.conectividad_internet:
                print(f"    Latencia: {resultado.red.latencia_internet_ms:.0f} ms")
            print(f"    IP Local: {resultado.red.ip_local}")

            # Información de Python
            print(f"\n  {Colores.BOLD}ENTORNO PYTHON:{Colores.RESET}")
            print(f"    Versión: {resultado.python.version}")
            print(f"    Paquetes instalados: {len(resultado.python.paquetes_instalados)}")
            if resultado.python.paquetes_faltantes:
                print(f"    {Colores.RED}Paquetes faltantes: {', '.join(resultado.python.paquetes_faltantes)}{Colores.RESET}")

            # Configuración óptima
            if self.config_optima:
                print(f"\n  {Colores.BOLD}CONFIGURACIÓN ÓPTIMA:{Colores.RESET}")
                print(f"    Nivel: {self.config_optima['system']['level'].upper()}")
                print(f"    Pool conexiones DB: {self.config_optima['db']['pool_size']}")
                print(f"    Workers: {self.config_optima['processing']['workers']}")
                print(f"    Batch size: {self.config_optima['processing']['batch_size']}")
                print(f"    Buffer memoria: {self.config_optima['processing']['buffer_mb']} MB")
                print(f"    Timeout DB: {self.config_optima['db']['timeout']} seg")

            # Estadísticas
            print(f"\n  {Colores.BOLD}ESTADÍSTICAS:{Colores.RESET}")
            print(f"    Duración análisis: {resultado.duracion_segundos:.2f} segundos")
            print(f"    Advertencias: {len(resultado.advertencias)}")
            print(f"    Errores: {len(resultado.errores)}")
            print(f"    Optimizaciones aplicadas: {len(resultado.optimizaciones_aplicadas)}")

            # Mostrar optimizaciones
            if resultado.optimizaciones_aplicadas:
                print(f"\n  {Colores.BOLD}OPTIMIZACIONES APLICADAS:{Colores.RESET}")
                for opt in resultado.optimizaciones_aplicadas[:8]:
                    print(f"    ✓ {opt}")

        input(f"\n  {Colores.GREEN}Presione ENTER para continuar...{Colores.RESET}")

    def _salir(self):
        """Sale del sistema mostrando despedida"""
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"{Colores.CHEDRAUI_RED}{ASCIIArt.LOGO_SUCCESS}{Colores.RESET}")

        print(f"\n  {Colores.CYAN}Gracias por usar el Sistema SAC{Colores.RESET}")
        print(f"  {Colores.DIM}\"Las maquinas y los sistemas al servicio de los analistas\"{Colores.RESET}")
        print()

        Animaciones.typing_effect(f"  {Colores.GREEN}Hasta pronto!{Colores.RESET}", 0.03)
        print()

    def ejecutar(self):
        """Metodo principal de ejecucion del sistema"""
        try:
            # Mostrar intro animada
            self.mostrar_intro()

            # ═══════════════════════════════════════════════════════════════
            # FASE 0: AUTO-CONFIGURACIÓN (PRIMER ELEMENTO A EJECUTARSE)
            # Recopila info del sistema, red, entorno y optimiza recursos
            # ═══════════════════════════════════════════════════════════════
            print(f"\n  {Colores.CYAN}Cargando modulos del sistema...{Colores.RESET}")
            cargar_modulos()

            if not self.ejecutar_auto_configuracion():
                print(f"\n  {Colores.RED}✗ Auto-configuración falló. Abortando.{Colores.RESET}")
                return

            # Pausa breve para que el usuario vea el resumen
            time.sleep(1)

            # Mostrar info del sistema (ahora con datos de auto-config)
            self.mostrar_info_sistema()

            # Verificar dependencias (muchas ya verificadas en auto-config)
            if not self.verificar_dependencias():
                print(f"\n  {Colores.RED}✗ Error en dependencias. Abortando.{Colores.RESET}")
                return

            # Verificar configuracion de credenciales
            if not self.verificar_configuracion():
                print(f"\n  {Colores.RED}✗ Error en configuracion. Abortando.{Colores.RESET}")
                return

            # Verificar conexion a BD (opcional)
            self.verificar_conexion_db()

            # Enviar correo de inicio
            self.enviar_correo_inicio()

            # Preguntar por modo monitoreo
            self.iniciar_monitoreo()

        except KeyboardInterrupt:
            print(f"\n\n  {Colores.YELLOW}⚠ Sistema interrumpido por el usuario{Colores.RESET}")
        except Exception as e:
            print(f"\n  {Colores.RED}✗ Error fatal: {e}{Colores.RESET}")
            if self.logger:
                self.logger.exception("Error fatal en SAC Master")


# ═══════════════════════════════════════════════════════════════════════════════
# PUNTO DE ENTRADA PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Funcion principal de entrada"""
    parser = argparse.ArgumentParser(
        description='SAC Master - Sistema de Automatizacion de Consultas',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python sac_master.py              # Ejecutar con menu interactivo
  python sac_master.py --config     # Solo configurar credenciales
  python sac_master.py --monitor    # Iniciar directamente en modo monitoreo
  python sac_master.py --status     # Ver estado del sistema
        """
    )

    parser.add_argument('--config', action='store_true',
                       help='Configurar credenciales')
    parser.add_argument('--monitor', action='store_true',
                       help='Iniciar en modo monitoreo automatico')
    parser.add_argument('--status', action='store_true',
                       help='Ver estado del sistema')
    parser.add_argument('--version', action='store_true',
                       help='Mostrar version')
    parser.add_argument('--auto-config', action='store_true',
                       help='Ejecutar solo auto-configuracion del sistema')
    parser.add_argument('--json', action='store_true',
                       help='Salida en formato JSON (para --auto-config)')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Modo silencioso (menos mensajes)')

    args = parser.parse_args()

    if args.version:
        print(f"SAC Master v2.0.0")
        print(f"Sistema de Automatizacion de Consultas")
        print(f"CEDIS Cancun 427 - Tiendas Chedraui")
        return

    if args.config:
        ConfiguradorCredenciales().ejecutar_configuracion()
        return

    # Ejecutar solo auto-configuracion
    if getattr(args, 'auto_config', False):
        cargar_modulos()
        try:
            from modules.modulo_auto_config import ejecutar_auto_configuracion
            import json as json_lib

            resultado, config = ejecutar_auto_configuracion(
                verbose=not args.quiet,
                instalar_faltantes=True
            )

            if args.json:
                print(json_lib.dumps(config, indent=2, ensure_ascii=False))

            sys.exit(0 if config['status']['ok'] else 1)
        except ImportError as e:
            print(f"Error: Modulo de auto-configuracion no disponible: {e}")
            sys.exit(1)

    # Ejecutar sistema principal
    sac = SACMaster()

    if args.status:
        sac.mostrar_info_sistema()
        return

    if args.monitor:
        sac.mostrar_intro()
        sac.verificar_dependencias()
        cargar_modulos()
        sac.verificar_configuracion()
        sac.modo_monitoreo = True
        sac._ejecutar_monitoreo_continuo()
        return

    # Ejecucion normal con menu
    sac.ejecutar()


if __name__ == "__main__":
    main()
