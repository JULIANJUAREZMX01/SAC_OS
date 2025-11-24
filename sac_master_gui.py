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
║       SCRIPT MAESTRO GUI - ORQUESTADOR CENTRAL OPTIMIZADO v3.0               ║
║                   CEDIS CANCUN 427 - TIENDAS CHEDRAUI                        ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝

              "Las maquinas y los sistemas al servicio de los analistas"

SCRIPT MAESTRO UNIFICADO - Punto de entrada UNICO del sistema SAC.

Este script:
1. PRIMERO inicia la GUI con animaciones para feedback visual inmediato
2. Analiza exhaustivamente: dispositivo, red, usuario, entorno
3. Gestiona carpetas compartidas entre dispositivos
4. Registra capacidades necesarias para futuras features
5. Optimiza recursos automaticamente segun el hardware
6. Orquesta TODOS los subsistemas desde un punto central

Desarrollado por: Julian Alexander Juarez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logistica Cancun 427

Version: 3.0.0
Ultima actualizacion: Noviembre 2025
"""

import os
import sys
import time
import json
import socket
import platform
import threading
import subprocess
import logging
import shutil
import hashlib
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
import argparse
import signal
import queue

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURACION INICIAL
# ═══════════════════════════════════════════════════════════════════════════════

VERSION = "3.0.0"
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# ═══════════════════════════════════════════════════════════════════════════════
# COLORES ANSI PARA TERMINAL
# ═══════════════════════════════════════════════════════════════════════════════

class Colores:
    """Codigos de colores ANSI para terminal"""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    UNDERLINE = '\033[4m'

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
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_BLUE = '\033[44m'

    # Colores Chedraui
    CHEDRAUI_RED = '\033[91m'

# Detectar soporte de colores en Windows
if sys.platform == 'win32':
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        for attr in dir(Colores):
            if not attr.startswith('_'):
                setattr(Colores, attr, '')


# ═══════════════════════════════════════════════════════════════════════════════
# ESTRUCTURAS DE DATOS
# ═══════════════════════════════════════════════════════════════════════════════

class TipoDispositivo(Enum):
    """Tipos de dispositivos en la red"""
    SERVIDOR_PRINCIPAL = "servidor_principal"
    PC_SISTEMAS = "pc_sistemas"
    PC_USUARIO = "pc_usuario"
    TERMINAL = "terminal"
    DESCONOCIDO = "desconocido"


class EstadoSistema(Enum):
    """Estados del sistema"""
    INICIANDO = "iniciando"
    ANALIZANDO = "analizando"
    CONFIGURANDO = "configurando"
    LISTO = "listo"
    ERROR = "error"
    EJECUTANDO = "ejecutando"


@dataclass
class InfoDispositivo:
    """Informacion completa del dispositivo"""
    # Identificacion
    id_unico: str = ""
    hostname: str = ""
    tipo: TipoDispositivo = TipoDispositivo.DESCONOCIDO
    es_servidor_principal: bool = False

    # Sistema
    os_nombre: str = ""
    os_version: str = ""
    os_arquitectura: str = ""

    # Hardware
    cpu_nombre: str = ""
    cpu_nucleos: int = 0
    cpu_nucleos_logicos: int = 0
    cpu_frecuencia_mhz: float = 0.0
    ram_total_gb: float = 0.0
    ram_disponible_gb: float = 0.0
    disco_total_gb: float = 0.0
    disco_libre_gb: float = 0.0

    # Usuario
    usuario_actual: str = ""
    usuario_dominio: str = ""
    directorio_home: str = ""
    es_administrador: bool = False

    # Red
    ip_local: str = ""
    ip_publica: str = ""
    mac_address: str = ""
    gateway: str = ""
    dns_servers: List[str] = field(default_factory=list)
    conectividad_internet: bool = False
    latencia_internet_ms: float = 0.0

    # Rutas SAC
    ruta_sac_local: str = ""
    ruta_carpeta_intercambio: str = ""
    ruta_servidor_principal: str = ""


@dataclass
class CapacidadRequerida:
    """Capacidad o feature requerida detectada"""
    nombre: str
    descripcion: str
    prioridad: int  # 1-5 (1 = critica)
    detectado_en: str  # dispositivo/modulo que la requiere
    fecha_deteccion: str
    estado: str = "pendiente"  # pendiente, en_desarrollo, completada
    notas: str = ""


@dataclass
class ConfiguracionCompartida:
    """Configuracion compartida entre dispositivos"""
    version: str = VERSION
    servidor_principal: str = ""
    dispositivos_registrados: Dict[str, Dict] = field(default_factory=dict)
    capacidades_requeridas: List[Dict] = field(default_factory=list)
    datos_frecuentes: Dict[str, Any] = field(default_factory=dict)
    ultima_sincronizacion: str = ""


# ═══════════════════════════════════════════════════════════════════════════════
# CLASE PRINCIPAL: ANIMACIONES GUI
# ═══════════════════════════════════════════════════════════════════════════════

class AnimacionesGUI:
    """Sistema de animaciones para la interfaz de terminal"""

    SPINNER_FRAMES = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    SPINNER_DOTS = ['⣾', '⣽', '⣻', '⢿', '⡿', '⣟', '⣯', '⣷']
    PROGRESS_FULL = '█'
    PROGRESS_EMPTY = '░'

    LOGO_SAC = """
    ╔═══════════════════════════════════════════════════════════════════════════╗
    ║                                                                           ║
    ║   ███████╗ █████╗  ██████╗    ██╗   ██╗██████╗    ██████╗                 ║
    ║   ██╔════╝██╔══██╗██╔════╝    ██║   ██║╚════██╗   ╚════██╗                ║
    ║   ███████╗███████║██║         ██║   ██║ █████╔╝    █████╔╝                ║
    ║   ╚════██║██╔══██║██║         ╚██╗ ██╔╝ ╚═══██╗   ██╔═══╝                 ║
    ║   ███████║██║  ██║╚██████╗     ╚████╔╝ ██████╔╝   ███████╗                ║
    ║   ╚══════╝╚═╝  ╚═╝ ╚═════╝      ╚═══╝  ╚═════╝    ╚══════╝                ║
    ║                                                                           ║
    ║       Sistema de Automatizacion de Consultas - CEDIS Cancun 427          ║
    ║                      Tiendas Chedraui S.A. de C.V.                        ║
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

    @staticmethod
    def clear_screen():
        """Limpia la pantalla"""
        os.system('cls' if os.name == 'nt' else 'clear')

    @staticmethod
    def clear_line():
        """Limpia la linea actual"""
        sys.stdout.write('\r' + ' ' * 100 + '\r')
        sys.stdout.flush()

    @staticmethod
    def mostrar_logo_inicio():
        """Muestra el logo de inicio con animacion"""
        AnimacionesGUI.clear_screen()
        print(f"{Colores.CHEDRAUI_RED}{AnimacionesGUI.LOGO_STARTUP}{Colores.RESET}")
        time.sleep(0.5)

    @staticmethod
    def mostrar_logo_principal():
        """Muestra el logo principal"""
        AnimacionesGUI.clear_screen()
        print(f"{Colores.CHEDRAUI_RED}{AnimacionesGUI.LOGO_SAC}{Colores.RESET}")

    @staticmethod
    def typing_effect(texto: str, delay: float = 0.02):
        """Efecto de escritura letra por letra"""
        for char in texto:
            sys.stdout.write(char)
            sys.stdout.flush()
            time.sleep(delay)
        print()

    @staticmethod
    def spinner(mensaje: str, duracion: float = 2.0, frames: list = None):
        """Muestra un spinner animado"""
        if frames is None:
            frames = AnimacionesGUI.SPINNER_FRAMES

        start_time = time.time()
        i = 0
        while time.time() - start_time < duracion:
            sys.stdout.write(f'\r  {frames[i % len(frames)]} {mensaje}')
            sys.stdout.flush()
            time.sleep(0.1)
            i += 1
        AnimacionesGUI.clear_line()

    @staticmethod
    def progress_bar(mensaje: str, total_steps: int = 20, duracion: float = 2.0):
        """Muestra una barra de progreso animada"""
        step_time = duracion / total_steps
        for i in range(total_steps + 1):
            progress = int((i / total_steps) * 100)
            filled = int(i / total_steps * 30)
            bar = AnimacionesGUI.PROGRESS_FULL * filled + AnimacionesGUI.PROGRESS_EMPTY * (30 - filled)
            sys.stdout.write(f'\r  {mensaje} [{bar}] {progress}%')
            sys.stdout.flush()
            time.sleep(step_time)
        print()

    @staticmethod
    def mostrar_fase(numero: int, titulo: str, descripcion: str = ""):
        """Muestra el inicio de una fase con formato"""
        print(f"\n  {Colores.CYAN}{'═' * 65}{Colores.RESET}")
        print(f"  {Colores.BOLD}📌 FASE {numero}: {titulo}{Colores.RESET}")
        if descripcion:
            print(f"  {Colores.DIM}{descripcion}{Colores.RESET}")
        print(f"  {Colores.CYAN}{'═' * 65}{Colores.RESET}\n")

    @staticmethod
    def mostrar_item_ok(texto: str):
        """Muestra un item completado"""
        print(f"    {Colores.GREEN}✓{Colores.RESET} {texto}")

    @staticmethod
    def mostrar_item_warning(texto: str):
        """Muestra un item con advertencia"""
        print(f"    {Colores.YELLOW}⚠{Colores.RESET} {texto}")

    @staticmethod
    def mostrar_item_error(texto: str):
        """Muestra un item con error"""
        print(f"    {Colores.RED}✗{Colores.RESET} {texto}")

    @staticmethod
    def mostrar_item_info(texto: str):
        """Muestra un item informativo"""
        print(f"    {Colores.CYAN}ℹ{Colores.RESET} {texto}")


# ═══════════════════════════════════════════════════════════════════════════════
# CLASE: ANALIZADOR DE SISTEMA
# ═══════════════════════════════════════════════════════════════════════════════

class AnalizadorSistema:
    """Analizador exhaustivo del sistema, red y usuario"""

    def __init__(self):
        self.info = InfoDispositivo()
        self.logger = logging.getLogger('SAC.Analizador')

    def generar_id_dispositivo(self) -> str:
        """Genera un ID unico para el dispositivo"""
        datos = f"{platform.node()}-{platform.machine()}-{self.obtener_mac_address()}"
        return hashlib.md5(datos.encode()).hexdigest()[:12].upper()

    def obtener_mac_address(self) -> str:
        """Obtiene la direccion MAC del dispositivo"""
        mac = ':'.join(['{:02x}'.format((uuid.getnode() >> ele) & 0xff)
                       for ele in range(0, 48, 8)][::-1])
        return mac.upper()

    def analizar_sistema_operativo(self):
        """Analiza informacion del sistema operativo"""
        self.info.os_nombre = platform.system()
        self.info.os_version = platform.version()
        self.info.os_arquitectura = platform.machine()
        self.info.hostname = socket.gethostname()

    def analizar_hardware(self):
        """Analiza el hardware del sistema"""
        # CPU
        self.info.cpu_nombre = platform.processor()
        try:
            import multiprocessing
            self.info.cpu_nucleos_logicos = multiprocessing.cpu_count()
            self.info.cpu_nucleos = self.info.cpu_nucleos_logicos // 2 or 1
        except:
            self.info.cpu_nucleos = 1
            self.info.cpu_nucleos_logicos = 1

        # RAM (sin psutil, usar alternativas)
        self._analizar_memoria_sin_psutil()

        # Disco
        self._analizar_disco()

    def _analizar_memoria_sin_psutil(self):
        """Analiza memoria sin necesidad de psutil"""
        try:
            if sys.platform == 'win32':
                # Windows
                import ctypes
                kernel32 = ctypes.windll.kernel32
                c_ulonglong = ctypes.c_ulonglong

                class MEMORYSTATUSEX(ctypes.Structure):
                    _fields_ = [
                        ('dwLength', ctypes.c_ulong),
                        ('dwMemoryLoad', ctypes.c_ulong),
                        ('ullTotalPhys', c_ulonglong),
                        ('ullAvailPhys', c_ulonglong),
                        ('ullTotalPageFile', c_ulonglong),
                        ('ullAvailPageFile', c_ulonglong),
                        ('ullTotalVirtual', c_ulonglong),
                        ('ullAvailVirtual', c_ulonglong),
                        ('ullAvailExtendedVirtual', c_ulonglong)
                    ]

                mem_status = MEMORYSTATUSEX()
                mem_status.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
                kernel32.GlobalMemoryStatusEx(ctypes.byref(mem_status))

                self.info.ram_total_gb = mem_status.ullTotalPhys / (1024**3)
                self.info.ram_disponible_gb = mem_status.ullAvailPhys / (1024**3)
            else:
                # Linux/Mac
                with open('/proc/meminfo', 'r') as f:
                    for line in f:
                        if 'MemTotal' in line:
                            self.info.ram_total_gb = int(line.split()[1]) / (1024**2)
                        elif 'MemAvailable' in line:
                            self.info.ram_disponible_gb = int(line.split()[1]) / (1024**2)
        except Exception as e:
            self.info.ram_total_gb = 4.0  # Valor por defecto
            self.info.ram_disponible_gb = 2.0

    def _analizar_disco(self):
        """Analiza espacio en disco"""
        try:
            if sys.platform == 'win32':
                import ctypes
                free_bytes = ctypes.c_ulonglong(0)
                total_bytes = ctypes.c_ulonglong(0)
                ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                    ctypes.c_wchar_p(str(BASE_DIR)[:3]),
                    None,
                    ctypes.pointer(total_bytes),
                    ctypes.pointer(free_bytes)
                )
                self.info.disco_total_gb = total_bytes.value / (1024**3)
                self.info.disco_libre_gb = free_bytes.value / (1024**3)
            else:
                statvfs = os.statvfs(str(BASE_DIR))
                self.info.disco_total_gb = (statvfs.f_blocks * statvfs.f_frsize) / (1024**3)
                self.info.disco_libre_gb = (statvfs.f_bfree * statvfs.f_frsize) / (1024**3)
        except:
            self.info.disco_total_gb = 100.0
            self.info.disco_libre_gb = 50.0

    def analizar_usuario(self):
        """Analiza informacion del usuario actual"""
        self.info.usuario_actual = os.getenv('USERNAME', os.getenv('USER', 'unknown'))
        self.info.directorio_home = str(Path.home())

        # Detectar dominio
        if sys.platform == 'win32':
            self.info.usuario_dominio = os.getenv('USERDOMAIN', '')

        # Verificar si es administrador
        try:
            if sys.platform == 'win32':
                import ctypes
                self.info.es_administrador = ctypes.windll.shell32.IsUserAnAdmin() != 0
            else:
                self.info.es_administrador = os.getuid() == 0
        except:
            self.info.es_administrador = False

    def analizar_red(self):
        """Analiza configuracion de red"""
        # IP Local
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            self.info.ip_local = s.getsockname()[0]
            s.close()
        except:
            self.info.ip_local = "127.0.0.1"

        # MAC Address
        self.info.mac_address = self.obtener_mac_address()

        # Conectividad a internet
        self._verificar_conectividad()

        # DNS
        self._obtener_dns_servers()

    def _verificar_conectividad(self):
        """Verifica conectividad a internet"""
        hosts_test = [("8.8.8.8", 53), ("1.1.1.1", 53)]

        for host, port in hosts_test:
            try:
                start = time.time()
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                sock.connect((host, port))
                self.info.latencia_internet_ms = (time.time() - start) * 1000
                self.info.conectividad_internet = True
                sock.close()
                break
            except:
                continue

    def _obtener_dns_servers(self):
        """Obtiene los servidores DNS configurados"""
        try:
            if sys.platform == 'win32':
                result = subprocess.run(
                    ['ipconfig', '/all'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                for line in result.stdout.split('\n'):
                    if 'DNS Servers' in line or 'Servidores DNS' in line:
                        dns = line.split(':')[-1].strip()
                        if dns:
                            self.info.dns_servers.append(dns)
            else:
                with open('/etc/resolv.conf', 'r') as f:
                    for line in f:
                        if line.startswith('nameserver'):
                            self.info.dns_servers.append(line.split()[1])
        except:
            pass

    def detectar_tipo_dispositivo(self):
        """Detecta el tipo de dispositivo basado en nombre y usuario"""
        hostname = self.info.hostname.upper()
        usuario = self.info.usuario_actual.upper()

        # Patrones para detectar servidor
        patrones_servidor = ['SRV', 'SERVER', 'SERVIDOR', 'DB', 'WMS']
        patrones_sistemas = ['ADM', 'SIS', 'SYS', 'ADMIN', 'IT']

        if any(p in hostname for p in patrones_servidor):
            self.info.tipo = TipoDispositivo.SERVIDOR_PRINCIPAL
            self.info.es_servidor_principal = True
        elif any(p in hostname or p in usuario for p in patrones_sistemas):
            self.info.tipo = TipoDispositivo.PC_SISTEMAS
        else:
            self.info.tipo = TipoDispositivo.PC_USUARIO

    def ejecutar_analisis_completo(self) -> InfoDispositivo:
        """Ejecuta el analisis completo del sistema"""
        self.info.id_unico = self.generar_id_dispositivo()
        self.analizar_sistema_operativo()
        self.analizar_hardware()
        self.analizar_usuario()
        self.analizar_red()
        self.detectar_tipo_dispositivo()

        # Rutas SAC
        self.info.ruta_sac_local = str(BASE_DIR)

        return self.info


# ═══════════════════════════════════════════════════════════════════════════════
# CLASE: GESTOR DE CARPETAS COMPARTIDAS
# ═══════════════════════════════════════════════════════════════════════════════

class GestorCarpetasCompartidas:
    """Gestiona las carpetas compartidas entre dispositivos"""

    def __init__(self, info_dispositivo: InfoDispositivo):
        self.info = info_dispositivo
        self.logger = logging.getLogger('SAC.GestorCarpetas')

        # Rutas base
        self.ruta_sac = BASE_DIR
        self.ruta_datos = BASE_DIR / 'data'
        self.ruta_compartido = BASE_DIR / 'shared'
        self.ruta_intercambio = None
        self.ruta_servidor = None

        # Archivo de configuracion compartida
        self.archivo_config = self.ruta_compartido / 'config_compartida.json'

    def crear_estructura_carpetas(self) -> bool:
        """Crea la estructura de carpetas necesaria"""
        try:
            # Estructura principal SAC
            carpetas_principales = [
                self.ruta_datos,
                self.ruta_datos / 'cache',
                self.ruta_datos / 'historico',
                self.ruta_datos / 'exportaciones',
                self.ruta_compartido,
                self.ruta_compartido / 'dispositivos',
                self.ruta_compartido / 'features_requeridas',
                self.ruta_compartido / 'datos_frecuentes',
                BASE_DIR / 'output' / 'logs',
                BASE_DIR / 'output' / 'resultados',
                BASE_DIR / 'output' / 'reportes',
                BASE_DIR / 'output' / 'backups',
            ]

            for carpeta in carpetas_principales:
                carpeta.mkdir(parents=True, exist_ok=True)

            # Carpeta especifica del dispositivo
            self.ruta_intercambio = self.ruta_compartido / 'dispositivos' / self.info.id_unico
            self.ruta_intercambio.mkdir(parents=True, exist_ok=True)

            # Subcarpetas de intercambio
            subcarpetas_intercambio = [
                'entrada',      # Archivos que llegan al dispositivo
                'salida',       # Archivos que salen del dispositivo
                'procesando',   # Archivos en proceso
                'completados',  # Archivos procesados
                'logs',         # Logs del dispositivo
            ]

            for sub in subcarpetas_intercambio:
                (self.ruta_intercambio / sub).mkdir(exist_ok=True)

            # Si es PC de usuario (no sistemas), crear carpeta de interaccion
            if self.info.tipo == TipoDispositivo.PC_USUARIO:
                self._crear_carpeta_usuario()

            return True

        except Exception as e:
            self.logger.error(f"Error creando estructura: {e}")
            return False

    def _crear_carpeta_usuario(self):
        """Crea carpeta de interaccion para usuarios no-sistemas"""
        # Carpeta en Documentos del usuario
        try:
            docs_path = Path(self.info.directorio_home) / 'Documents' / 'SAC_Intercambio'
            if not docs_path.exists():
                docs_path.mkdir(parents=True, exist_ok=True)

                # Subcarpetas para el usuario
                (docs_path / 'Subir_Archivos').mkdir(exist_ok=True)
                (docs_path / 'Descargar_Archivos').mkdir(exist_ok=True)
                (docs_path / 'Reportes').mkdir(exist_ok=True)

                # Crear README para el usuario
                readme_content = f"""
# SAC - Carpeta de Intercambio
# CEDIS Cancun 427 - Tiendas Chedraui
# ===========================================

Esta carpeta permite intercambiar archivos con el sistema SAC.

## Carpetas disponibles:

📁 Subir_Archivos/
   Coloque aqui los archivos que desea procesar.
   El sistema los recogerá automaticamente.

📁 Descargar_Archivos/
   Aqui encontrara los archivos procesados y exportados.

📁 Reportes/
   Reportes generados automaticamente para usted.

## Dispositivo: {self.info.hostname}
## ID: {self.info.id_unico}
## Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Contacto Sistemas: ADMJAJA
"""
                (docs_path / 'LEEME.txt').write_text(readme_content, encoding='utf-8')

            self.info.ruta_carpeta_intercambio = str(docs_path)

        except Exception as e:
            self.logger.warning(f"No se pudo crear carpeta de usuario: {e}")

    def registrar_dispositivo(self) -> bool:
        """Registra este dispositivo en la configuracion compartida"""
        try:
            config = self._cargar_config_compartida()

            # Agregar/actualizar este dispositivo
            config.dispositivos_registrados[self.info.id_unico] = {
                'hostname': self.info.hostname,
                'tipo': self.info.tipo.value,
                'ip_local': self.info.ip_local,
                'usuario': self.info.usuario_actual,
                'os': f"{self.info.os_nombre} {self.info.os_version}",
                'ram_gb': round(self.info.ram_total_gb, 1),
                'ultima_conexion': datetime.now().isoformat(),
                'ruta_intercambio': str(self.ruta_intercambio) if self.ruta_intercambio else "",
            }

            config.ultima_sincronizacion = datetime.now().isoformat()

            # Si es servidor principal, marcarlo
            if self.info.es_servidor_principal:
                config.servidor_principal = self.info.id_unico

            self._guardar_config_compartida(config)
            return True

        except Exception as e:
            self.logger.error(f"Error registrando dispositivo: {e}")
            return False

    def _cargar_config_compartida(self) -> ConfiguracionCompartida:
        """Carga la configuracion compartida"""
        try:
            if self.archivo_config.exists():
                with open(self.archivo_config, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    config = ConfiguracionCompartida(**data)
            else:
                config = ConfiguracionCompartida()
            return config
        except:
            return ConfiguracionCompartida()

    def _guardar_config_compartida(self, config: ConfiguracionCompartida):
        """Guarda la configuracion compartida"""
        try:
            with open(self.archivo_config, 'w', encoding='utf-8') as f:
                json.dump(asdict(config), f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Error guardando config: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# CLASE: REGISTRO DE CAPACIDADES
# ═══════════════════════════════════════════════════════════════════════════════

class RegistroCapacidades:
    """Registra capacidades y features necesarias"""

    def __init__(self, ruta_compartido: Path):
        self.ruta = ruta_compartido / 'features_requeridas'
        self.ruta.mkdir(parents=True, exist_ok=True)
        self.archivo = self.ruta / 'capacidades.json'
        self.logger = logging.getLogger('SAC.Capacidades')

    def registrar_capacidad(self, capacidad: CapacidadRequerida) -> bool:
        """Registra una nueva capacidad requerida"""
        try:
            capacidades = self._cargar_capacidades()

            # Verificar si ya existe
            existe = any(c['nombre'] == capacidad.nombre for c in capacidades)

            if not existe:
                capacidades.append(asdict(capacidad))
                self._guardar_capacidades(capacidades)
                self.logger.info(f"Nueva capacidad registrada: {capacidad.nombre}")

            return True
        except Exception as e:
            self.logger.error(f"Error registrando capacidad: {e}")
            return False

    def obtener_capacidades_pendientes(self) -> List[Dict]:
        """Obtiene todas las capacidades pendientes"""
        capacidades = self._cargar_capacidades()
        return [c for c in capacidades if c.get('estado') == 'pendiente']

    def _cargar_capacidades(self) -> List[Dict]:
        """Carga la lista de capacidades"""
        try:
            if self.archivo.exists():
                with open(self.archivo, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except:
            return []

    def _guardar_capacidades(self, capacidades: List[Dict]):
        """Guarda la lista de capacidades"""
        with open(self.archivo, 'w', encoding='utf-8') as f:
            json.dump(capacidades, f, indent=2, ensure_ascii=False)


# ═══════════════════════════════════════════════════════════════════════════════
# CLASE: OPTIMIZADOR DE RECURSOS
# ═══════════════════════════════════════════════════════════════════════════════

class OptimizadorRecursos:
    """Optimiza recursos basado en el hardware disponible"""

    def __init__(self, info: InfoDispositivo):
        self.info = info
        self.config = {}

    def calcular_configuracion_optima(self) -> Dict[str, Any]:
        """Calcula la configuracion optima basada en el hardware"""

        # Determinar nivel de recursos
        ram_gb = self.info.ram_disponible_gb
        nucleos = self.info.cpu_nucleos_logicos

        if ram_gb < 2 or nucleos < 2:
            nivel = "minimo"
        elif ram_gb < 4 or nucleos < 4:
            nivel = "bajo"
        elif ram_gb < 8 or nucleos < 8:
            nivel = "normal"
        elif ram_gb < 16:
            nivel = "alto"
        else:
            nivel = "maximo"

        # Configuracion basada en nivel
        configs = {
            "minimo": {
                "pool_size": 1,
                "workers": 1,
                "batch_size": 100,
                "buffer_mb": 64,
                "timeout": 60,
                "cache": False,
                "interval": 600,
            },
            "bajo": {
                "pool_size": 2,
                "workers": 2,
                "batch_size": 500,
                "buffer_mb": 128,
                "timeout": 45,
                "cache": True,
                "interval": 300,
            },
            "normal": {
                "pool_size": 3,
                "workers": 4,
                "batch_size": 1000,
                "buffer_mb": 256,
                "timeout": 30,
                "cache": True,
                "interval": 180,
            },
            "alto": {
                "pool_size": 5,
                "workers": 8,
                "batch_size": 2000,
                "buffer_mb": 512,
                "timeout": 30,
                "cache": True,
                "interval": 120,
            },
            "maximo": {
                "pool_size": 8,
                "workers": 12,
                "batch_size": 5000,
                "buffer_mb": 1024,
                "timeout": 30,
                "cache": True,
                "interval": 60,
            },
        }

        base = configs[nivel]

        self.config = {
            'system': {
                'level': nivel,
                'optimized_at': datetime.now().isoformat(),
            },
            'db': {
                'pool_size': base['pool_size'],
                'timeout': base['timeout'],
                'retry_count': 3,
            },
            'processing': {
                'workers': base['workers'],
                'batch_size': base['batch_size'],
                'buffer_mb': base['buffer_mb'],
            },
            'monitoring': {
                'interval_seconds': base['interval'],
                'cache_enabled': base['cache'],
            },
            'device': {
                'id': self.info.id_unico,
                'type': self.info.tipo.value,
                'hostname': self.info.hostname,
            }
        }

        return self.config

    def aplicar_optimizaciones(self):
        """Aplica optimizaciones al sistema"""
        # Configurar recolector de basura
        import gc
        gc.enable()
        gc.set_threshold(700, 10, 10)

        # Optimizar threads
        if hasattr(threading, 'stack_size'):
            try:
                threading.stack_size(512 * 1024)  # 512KB por thread
            except:
                pass


# ═══════════════════════════════════════════════════════════════════════════════
# CLASE PRINCIPAL: SAC MASTER GUI
# ═══════════════════════════════════════════════════════════════════════════════

class SACMasterGUI:
    """Clase principal del Script Maestro con GUI"""

    def __init__(self):
        self.version = VERSION
        self.inicio = datetime.now()
        self.estado = EstadoSistema.INICIANDO

        # Componentes
        self.info_dispositivo: Optional[InfoDispositivo] = None
        self.gestor_carpetas: Optional[GestorCarpetasCompartidas] = None
        self.registro_capacidades: Optional[RegistroCapacidades] = None
        self.optimizador: Optional[OptimizadorRecursos] = None
        self.config_optima: Dict = {}

        # Logging
        self._configurar_logging()

        # Estado
        self.gui_activa = False
        self.modulos_disponibles = {}

    def _configurar_logging(self):
        """Configura el sistema de logging"""
        log_dir = BASE_DIR / 'output' / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)

        fecha = datetime.now().strftime('%Y%m%d')
        log_file = log_dir / f'sac_master_gui_{fecha}.log'

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
            ]
        )
        self.logger = logging.getLogger('SAC.Master')

    def iniciar_gui_animaciones(self):
        """FASE 0: Inicia la GUI con animaciones (PRIMER ELEMENTO)"""
        self.gui_activa = True

        # Mostrar logo de inicio
        AnimacionesGUI.mostrar_logo_inicio()

        AnimacionesGUI.typing_effect(
            f"  {Colores.CYAN}Inicializando Sistema de Automatizacion de Consultas v{self.version}...{Colores.RESET}",
            0.015
        )
        print()

        # Barra de progreso inicial
        AnimacionesGUI.progress_bar("Cargando componentes iniciales", 20, 1.5)

        # Transicion a logo principal
        AnimacionesGUI.mostrar_logo_principal()

    def fase_analisis_sistema(self) -> bool:
        """FASE 1: Analisis exhaustivo del sistema"""
        AnimacionesGUI.mostrar_fase(1, "ANALISIS DEL SISTEMA",
            "Recopilando informacion del dispositivo, red y usuario...")

        try:
            analizador = AnalizadorSistema()

            # Analizar con feedback visual
            AnimacionesGUI.spinner("Analizando sistema operativo", 0.5)
            analizador.analizar_sistema_operativo()
            AnimacionesGUI.mostrar_item_ok(f"OS: {analizador.info.os_nombre} {analizador.info.os_version}")

            AnimacionesGUI.spinner("Analizando hardware", 0.5)
            analizador.analizar_hardware()
            AnimacionesGUI.mostrar_item_ok(f"RAM: {analizador.info.ram_total_gb:.1f} GB (disponible: {analizador.info.ram_disponible_gb:.1f} GB)")
            AnimacionesGUI.mostrar_item_ok(f"CPU: {analizador.info.cpu_nucleos_logicos} nucleos logicos")
            AnimacionesGUI.mostrar_item_ok(f"Disco libre: {analizador.info.disco_libre_gb:.1f} GB")

            AnimacionesGUI.spinner("Analizando usuario", 0.3)
            analizador.analizar_usuario()
            AnimacionesGUI.mostrar_item_ok(f"Usuario: {analizador.info.usuario_actual}")
            if analizador.info.es_administrador:
                AnimacionesGUI.mostrar_item_ok("Privilegios: Administrador")

            AnimacionesGUI.spinner("Analizando red", 0.5)
            analizador.analizar_red()
            AnimacionesGUI.mostrar_item_ok(f"IP Local: {analizador.info.ip_local}")
            if analizador.info.conectividad_internet:
                AnimacionesGUI.mostrar_item_ok(f"Internet: Conectado ({analizador.info.latencia_internet_ms:.0f}ms)")
            else:
                AnimacionesGUI.mostrar_item_warning("Internet: Sin conexion")

            # Detectar tipo de dispositivo
            analizador.detectar_tipo_dispositivo()
            analizador.info.id_unico = analizador.generar_id_dispositivo()
            analizador.info.ruta_sac_local = str(BASE_DIR)

            AnimacionesGUI.mostrar_item_info(f"Tipo dispositivo: {analizador.info.tipo.value}")
            AnimacionesGUI.mostrar_item_info(f"ID unico: {analizador.info.id_unico}")

            self.info_dispositivo = analizador.info
            self.estado = EstadoSistema.ANALIZANDO

            return True

        except Exception as e:
            AnimacionesGUI.mostrar_item_error(f"Error en analisis: {e}")
            self.logger.exception("Error en analisis del sistema")
            return False

    def fase_estructura_carpetas(self) -> bool:
        """FASE 2: Creacion de estructura de carpetas"""
        AnimacionesGUI.mostrar_fase(2, "ESTRUCTURA DE CARPETAS",
            "Creando carpetas compartidas y de intercambio...")

        try:
            self.gestor_carpetas = GestorCarpetasCompartidas(self.info_dispositivo)

            AnimacionesGUI.spinner("Creando estructura de carpetas", 0.5)
            if self.gestor_carpetas.crear_estructura_carpetas():
                AnimacionesGUI.mostrar_item_ok("Estructura principal creada")
                AnimacionesGUI.mostrar_item_ok(f"Carpeta de intercambio: {self.gestor_carpetas.ruta_intercambio}")

                if self.info_dispositivo.tipo == TipoDispositivo.PC_USUARIO:
                    AnimacionesGUI.mostrar_item_ok("Carpeta de usuario creada en Documentos")

            AnimacionesGUI.spinner("Registrando dispositivo", 0.3)
            if self.gestor_carpetas.registrar_dispositivo():
                AnimacionesGUI.mostrar_item_ok("Dispositivo registrado en sistema compartido")

            # Inicializar registro de capacidades
            self.registro_capacidades = RegistroCapacidades(self.gestor_carpetas.ruta_compartido)
            AnimacionesGUI.mostrar_item_ok("Registro de capacidades inicializado")

            return True

        except Exception as e:
            AnimacionesGUI.mostrar_item_error(f"Error creando estructura: {e}")
            self.logger.exception("Error en estructura de carpetas")
            return False

    def fase_optimizacion(self) -> bool:
        """FASE 3: Optimizacion de recursos"""
        AnimacionesGUI.mostrar_fase(3, "OPTIMIZACION DE RECURSOS",
            "Calculando configuracion optima basada en hardware...")

        try:
            self.optimizador = OptimizadorRecursos(self.info_dispositivo)

            AnimacionesGUI.spinner("Calculando configuracion optima", 0.5)
            self.config_optima = self.optimizador.calcular_configuracion_optima()

            nivel = self.config_optima['system']['level'].upper()
            AnimacionesGUI.mostrar_item_ok(f"Nivel de optimizacion: {nivel}")
            AnimacionesGUI.mostrar_item_ok(f"Pool de conexiones: {self.config_optima['db']['pool_size']}")
            AnimacionesGUI.mostrar_item_ok(f"Workers: {self.config_optima['processing']['workers']}")
            AnimacionesGUI.mostrar_item_ok(f"Batch size: {self.config_optima['processing']['batch_size']} registros")
            AnimacionesGUI.mostrar_item_ok(f"Intervalo monitoreo: {self.config_optima['monitoring']['interval_seconds']}s")

            AnimacionesGUI.spinner("Aplicando optimizaciones", 0.3)
            self.optimizador.aplicar_optimizaciones()
            AnimacionesGUI.mostrar_item_ok("Optimizaciones aplicadas")

            # Guardar configuracion
            config_file = BASE_DIR / 'data' / 'config_optima.json'
            config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config_optima, f, indent=2, ensure_ascii=False)
            AnimacionesGUI.mostrar_item_ok("Configuracion guardada")

            self.estado = EstadoSistema.CONFIGURANDO
            return True

        except Exception as e:
            AnimacionesGUI.mostrar_item_error(f"Error en optimizacion: {e}")
            self.logger.exception("Error en optimizacion")
            return False

    def fase_verificacion_modulos(self) -> bool:
        """FASE 4: Verificacion de modulos del sistema"""
        AnimacionesGUI.mostrar_fase(4, "VERIFICACION DE MODULOS",
            "Cargando y verificando modulos del sistema...")

        modulos = {
            'config': 'config',
            'monitor': 'monitor',
            'db_connection': 'modules.db_connection',
            'reportes': 'modules.reportes_excel',
            'gestor_correos': 'gestor_correos',
            'telegram': 'notificaciones_telegram',
            'auto_config': 'modules.modulo_auto_config',
        }

        for nombre, ruta in modulos.items():
            try:
                AnimacionesGUI.spinner(f"Cargando {nombre}", 0.2)
                __import__(ruta)
                self.modulos_disponibles[nombre] = True
                AnimacionesGUI.mostrar_item_ok(f"{nombre}")
            except ImportError:
                self.modulos_disponibles[nombre] = False
                AnimacionesGUI.mostrar_item_warning(f"{nombre} (no disponible)")

        # Verificar dependencias Python
        dependencias = ['pandas', 'openpyxl', 'dotenv', 'rich']
        for dep in dependencias:
            try:
                __import__(dep)
            except ImportError:
                # Registrar como capacidad necesaria
                cap = CapacidadRequerida(
                    nombre=f"dependencia_{dep}",
                    descripcion=f"Instalar paquete Python: {dep}",
                    prioridad=1,
                    detectado_en=self.info_dispositivo.hostname,
                    fecha_deteccion=datetime.now().isoformat()
                )
                self.registro_capacidades.registrar_capacidad(cap)

        return True

    def fase_verificacion_credenciales(self) -> bool:
        """FASE 5: Verificacion de credenciales"""
        AnimacionesGUI.mostrar_fase(5, "VERIFICACION DE CREDENCIALES",
            "Verificando configuracion de accesos...")

        env_file = BASE_DIR / '.env'

        if not env_file.exists():
            AnimacionesGUI.mostrar_item_warning("Archivo .env no encontrado")
            AnimacionesGUI.mostrar_item_info("Se requiere configurar credenciales")
            return True  # Continuar, se configurara despues

        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                contenido = f.read()

            # Verificar credenciales basicas
            credenciales = {
                'DB_USER': 'Base de datos',
                'DB_PASSWORD': 'Base de datos',
                'EMAIL_USER': 'Correo',
            }

            for cred, desc in credenciales.items():
                if f'{cred}=' in contenido:
                    valor = contenido.split(f'{cred}=')[1].split('\n')[0].strip()
                    if valor and valor not in ['', 'tu_usuario', 'your_password']:
                        AnimacionesGUI.mostrar_item_ok(f"{desc} ({cred})")
                    else:
                        AnimacionesGUI.mostrar_item_warning(f"{desc} ({cred}) - No configurado")
                else:
                    AnimacionesGUI.mostrar_item_warning(f"{desc} ({cred}) - Faltante")

            return True

        except Exception as e:
            AnimacionesGUI.mostrar_item_error(f"Error leyendo credenciales: {e}")
            return True

    def mostrar_resumen_inicio(self):
        """Muestra el resumen del inicio del sistema"""
        print(f"\n  {Colores.GREEN}{'═' * 65}{Colores.RESET}")
        print(f"  {Colores.BOLD}{Colores.GREEN}✓ SISTEMA SAC INICIADO CORRECTAMENTE{Colores.RESET}")
        print(f"  {Colores.GREEN}{'═' * 65}{Colores.RESET}")

        print(f"\n  {Colores.CYAN}Resumen del sistema:{Colores.RESET}")
        print(f"    Version:         {self.version}")
        print(f"    Dispositivo:     {self.info_dispositivo.hostname}")
        print(f"    Tipo:            {self.info_dispositivo.tipo.value}")
        print(f"    ID:              {self.info_dispositivo.id_unico}")
        print(f"    IP:              {self.info_dispositivo.ip_local}")
        print(f"    RAM disponible:  {self.info_dispositivo.ram_disponible_gb:.1f} GB")
        print(f"    Optimizacion:    {self.config_optima['system']['level'].upper()}")
        print(f"    Hora inicio:     {self.inicio.strftime('%Y-%m-%d %H:%M:%S')}")

        self.estado = EstadoSistema.LISTO

    def ejecutar_sistema_principal(self):
        """Ejecuta el sistema principal (menu o modo especificado)"""
        try:
            # Intentar importar y ejecutar main
            import main as sac_main

            if hasattr(sac_main, 'main'):
                sys.argv = ['sac_master_gui.py', '--menu']
                sac_main.main()

        except ImportError:
            # Si no existe main, mostrar menu basico
            self._mostrar_menu_basico()

    def _mostrar_menu_basico(self):
        """Menu basico si el sistema principal no esta disponible"""
        while True:
            print(f"\n  {Colores.BOLD}MENU PRINCIPAL SAC{Colores.RESET}")
            print(f"  {Colores.BLUE}{'═' * 50}{Colores.RESET}")
            print(f"  {Colores.CYAN}1.{Colores.RESET} Ver informacion del sistema")
            print(f"  {Colores.CYAN}2.{Colores.RESET} Ver configuracion optima")
            print(f"  {Colores.CYAN}3.{Colores.RESET} Ver capacidades pendientes")
            print(f"  {Colores.CYAN}4.{Colores.RESET} Registrar nueva capacidad")
            print(f"  {Colores.CYAN}0.{Colores.RESET} Salir")
            print(f"  {Colores.BLUE}{'═' * 50}{Colores.RESET}")

            opcion = input(f"\n  {Colores.GREEN}Seleccione una opcion: {Colores.RESET}").strip()

            if opcion == '1':
                self._mostrar_info_sistema()
            elif opcion == '2':
                self._mostrar_config_optima()
            elif opcion == '3':
                self._mostrar_capacidades_pendientes()
            elif opcion == '4':
                self._registrar_capacidad_interactivo()
            elif opcion == '0':
                print(f"\n  {Colores.CYAN}Hasta pronto!{Colores.RESET}\n")
                break

    def _mostrar_info_sistema(self):
        """Muestra informacion del sistema"""
        print(f"\n  {Colores.BOLD}INFORMACION DEL SISTEMA{Colores.RESET}")
        print(f"  {'─' * 50}")
        info = self.info_dispositivo
        print(f"  Hostname:      {info.hostname}")
        print(f"  ID:            {info.id_unico}")
        print(f"  Tipo:          {info.tipo.value}")
        print(f"  OS:            {info.os_nombre} {info.os_version}")
        print(f"  CPU:           {info.cpu_nucleos_logicos} nucleos")
        print(f"  RAM Total:     {info.ram_total_gb:.1f} GB")
        print(f"  RAM Disponible:{info.ram_disponible_gb:.1f} GB")
        print(f"  Disco Libre:   {info.disco_libre_gb:.1f} GB")
        print(f"  IP Local:      {info.ip_local}")
        print(f"  Internet:      {'Conectado' if info.conectividad_internet else 'Sin conexion'}")
        print(f"  Usuario:       {info.usuario_actual}")
        print(f"  Admin:         {'Si' if info.es_administrador else 'No'}")
        input(f"\n  {Colores.GREEN}Presione Enter para continuar...{Colores.RESET}")

    def _mostrar_config_optima(self):
        """Muestra la configuracion optima"""
        print(f"\n  {Colores.BOLD}CONFIGURACION OPTIMA{Colores.RESET}")
        print(f"  {'─' * 50}")
        print(json.dumps(self.config_optima, indent=4))
        input(f"\n  {Colores.GREEN}Presione Enter para continuar...{Colores.RESET}")

    def _mostrar_capacidades_pendientes(self):
        """Muestra capacidades pendientes"""
        print(f"\n  {Colores.BOLD}CAPACIDADES PENDIENTES{Colores.RESET}")
        print(f"  {'─' * 50}")

        pendientes = self.registro_capacidades.obtener_capacidades_pendientes()
        if pendientes:
            for i, cap in enumerate(pendientes, 1):
                print(f"  {i}. {cap['nombre']} (Prioridad: {cap['prioridad']})")
                print(f"     {cap['descripcion']}")
                print(f"     Detectado en: {cap['detectado_en']}")
                print()
        else:
            print("  No hay capacidades pendientes")

        input(f"\n  {Colores.GREEN}Presione Enter para continuar...{Colores.RESET}")

    def _registrar_capacidad_interactivo(self):
        """Registra una nueva capacidad interactivamente"""
        print(f"\n  {Colores.BOLD}REGISTRAR NUEVA CAPACIDAD{Colores.RESET}")
        print(f"  {'─' * 50}")

        nombre = input("  Nombre de la capacidad: ").strip()
        if not nombre:
            print(f"  {Colores.RED}Nombre requerido{Colores.RESET}")
            return

        descripcion = input("  Descripcion: ").strip()
        prioridad = input("  Prioridad (1-5, 1=critica): ").strip()
        try:
            prioridad = int(prioridad)
        except:
            prioridad = 3

        notas = input("  Notas adicionales: ").strip()

        cap = CapacidadRequerida(
            nombre=nombre,
            descripcion=descripcion,
            prioridad=prioridad,
            detectado_en=self.info_dispositivo.hostname,
            fecha_deteccion=datetime.now().isoformat(),
            notas=notas
        )

        if self.registro_capacidades.registrar_capacidad(cap):
            print(f"\n  {Colores.GREEN}✓ Capacidad registrada exitosamente{Colores.RESET}")
        else:
            print(f"\n  {Colores.RED}✗ Error registrando capacidad{Colores.RESET}")

        input(f"\n  {Colores.GREEN}Presione Enter para continuar...{Colores.RESET}")

    def ejecutar(self, args=None):
        """Metodo principal de ejecucion"""
        try:
            # FASE 0: INICIAR GUI CON ANIMACIONES (PRIMER ELEMENTO)
            self.iniciar_gui_animaciones()

            # FASE 1: ANALISIS DEL SISTEMA
            if not self.fase_analisis_sistema():
                return

            # FASE 2: ESTRUCTURA DE CARPETAS
            if not self.fase_estructura_carpetas():
                return

            # FASE 3: OPTIMIZACION
            if not self.fase_optimizacion():
                return

            # FASE 4: VERIFICACION DE MODULOS
            self.fase_verificacion_modulos()

            # FASE 5: VERIFICACION DE CREDENCIALES
            self.fase_verificacion_credenciales()

            # MOSTRAR RESUMEN
            self.mostrar_resumen_inicio()

            # EJECUTAR SISTEMA PRINCIPAL
            print(f"\n  {Colores.CYAN}Presione Enter para continuar al sistema principal...{Colores.RESET}")
            input()

            self.estado = EstadoSistema.EJECUTANDO
            self.ejecutar_sistema_principal()

        except KeyboardInterrupt:
            print(f"\n\n  {Colores.YELLOW}Sistema interrumpido por el usuario{Colores.RESET}")
        except Exception as e:
            print(f"\n  {Colores.RED}Error fatal: {e}{Colores.RESET}")
            self.logger.exception("Error fatal en SAC Master GUI")


# ═══════════════════════════════════════════════════════════════════════════════
# PUNTO DE ENTRADA
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Funcion principal de entrada"""
    parser = argparse.ArgumentParser(
        description='SAC Master GUI - Script Maestro Unificado v3.0',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python sac_master_gui.py              # Ejecutar con GUI completa
  python sac_master_gui.py --version    # Mostrar version
  python sac_master_gui.py --info       # Solo mostrar info del sistema
        """
    )

    parser.add_argument('--version', action='store_true', help='Mostrar version')
    parser.add_argument('--info', action='store_true', help='Solo mostrar informacion del sistema')
    parser.add_argument('--quiet', '-q', action='store_true', help='Modo silencioso')

    args = parser.parse_args()

    if args.version:
        print(f"SAC Master GUI v{VERSION}")
        print("Sistema de Automatizacion de Consultas")
        print("CEDIS Cancun 427 - Tiendas Chedraui")
        return

    # Ejecutar sistema
    sac = SACMasterGUI()
    sac.ejecutar(args)


if __name__ == "__main__":
    main()
