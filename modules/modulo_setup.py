#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
===============================================================================
MODULO DE SETUP CON ANIMACIONES - SISTEMA SAC v2.0
Sistema de Automatizacion de Consultas - CEDIS Cancun 427
===============================================================================

Modulo unificado que integra:
- Animaciones de carga durante el inicio
- Auto-configuracion del sistema
- Instalacion de dependencias
- Verificacion de entorno

Este modulo debe ejecutarse AL INICIO del sistema para garantizar
que todo este correctamente configurado antes de operar.

USO:
    from modules.modulo_setup import ejecutar_setup_inicial

    resultado = ejecutar_setup_inicial()
    if resultado.exito:
        # Sistema listo para operar
        pass

Desarrollado por: Julian Alexander Juarez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logistica Cancun
===============================================================================
"""

import os
import sys
import time
import subprocess
import platform
import socket
import shutil
import json
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum

# Directorio base del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent


# ===============================================================================
# CONSTANTES Y CONFIGURACION
# ===============================================================================

VERSION = "2.0.0"
ENV_FILE = BASE_DIR / '.env'
INSTALADO_FLAG = BASE_DIR / 'config' / '.instalado'
REQUIREMENTS_FILE = BASE_DIR / 'requirements.txt'

PYTHON_MIN_VERSION = (3, 8)

# Estructura de directorios requerida
DIRECTORIOS_REQUERIDOS = [
    'config', 'docs', 'modules', 'modules/excel_templates', 'modules/email',
    'queries', 'queries/obligatorias', 'queries/preventivas', 'queries/bajo_demanda',
    'tests', 'output', 'output/logs', 'output/resultados', 'logs', 'templates'
]

# Dependencias minimas para funcionar
DEPENDENCIAS_CORE = [
    'python-dotenv',
    'pandas',
    'openpyxl',
]

# Dependencias completas de produccion
DEPENDENCIAS_PRODUCCION = [
    'rich', 'python-dotenv', 'pandas', 'numpy', 'openpyxl',
    'XlsxWriter', 'Pillow', 'reportlab', 'PyYAML', 'pydantic',
    'pydantic-settings', 'colorama', 'tqdm', 'schedule',
    'python-dateutil', 'pytz', 'requests', 'Flask', 'Jinja2',
    'python-telegram-bot',
]


# ===============================================================================
# COLORES Y UTILIDADES DE TERMINAL
# ===============================================================================

class Colores:
    """Codigos de colores ANSI para terminal"""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'


def limpiar_pantalla():
    """Limpia la pantalla de la terminal."""
    os.system('cls' if os.name == 'nt' else 'clear')


def ocultar_cursor():
    """Oculta el cursor de la terminal."""
    print("\033[?25l", end="", flush=True)


def mostrar_cursor():
    """Muestra el cursor de la terminal."""
    print("\033[?25h", end="", flush=True)


def color_texto(texto: str, color: str) -> str:
    """Aplica color al texto."""
    return f"{color}{texto}{Colores.RESET}"


# ===============================================================================
# ESTADOS Y ESTRUCTURAS DE DATOS
# ===============================================================================

class EstadoSetup(Enum):
    """Estados del proceso de setup"""
    NO_INICIADO = "no_iniciado"
    EN_PROGRESO = "en_progreso"
    COMPLETADO = "completado"
    ERROR = "error"
    OMITIDO = "omitido"


class TipoMensaje(Enum):
    """Tipos de mensajes para la consola"""
    INFO = "info"
    OK = "ok"
    WARN = "warn"
    ERROR = "error"
    TITULO = "titulo"


@dataclass
class PasoSetup:
    """Representa un paso del proceso de setup"""
    nombre: str
    descripcion: str
    estado: EstadoSetup = EstadoSetup.NO_INICIADO
    mensaje: str = ""
    duracion_seg: float = 0.0


@dataclass
class ResultadoSetup:
    """Resultado del proceso de setup"""
    exito: bool = False
    mensaje: str = ""
    pasos: List[PasoSetup] = field(default_factory=list)
    duracion_total_seg: float = 0.0
    dependencias_instaladas: int = 0
    dependencias_faltantes: List[str] = field(default_factory=list)
    advertencias: List[str] = field(default_factory=list)
    errores: List[str] = field(default_factory=list)
    configuracion_valida: bool = False
    sistema_listo: bool = False


# ===============================================================================
# ANIMACIONES DE CARGA
# ===============================================================================

class AnimacionCarga:
    """Clase para mostrar animaciones de carga durante el setup"""

    # Arte ASCII del camion CEDIS
    CAMION_FRAMES = [
        "      🚛💨",
        "       🚛💨",
        "        🚛💨",
        "         🚛💨",
        "          🚛💨",
        "           🚛",
    ]

    SPINNER_CHARS = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    BARRA_CHARS = {
        'llena': '█',
        'media': '▓',
        'vacia': '░',
        'animacion': ['▓', '▒', '░', '▒'],
    }

    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.activa = False
        self._thread = None
        self._mensaje_actual = ""

    def _print(self, mensaje: str, tipo: TipoMensaje = TipoMensaje.INFO):
        """Imprime mensaje formateado"""
        if not self.verbose:
            return

        prefijos = {
            TipoMensaje.INFO: f"  {Colores.CYAN}i{Colores.RESET}",
            TipoMensaje.OK: f"  {Colores.GREEN}✓{Colores.RESET}",
            TipoMensaje.WARN: f"  {Colores.YELLOW}⚠{Colores.RESET}",
            TipoMensaje.ERROR: f"  {Colores.RED}✗{Colores.RESET}",
            TipoMensaje.TITULO: f"\n  {Colores.BOLD}{Colores.BLUE}",
        }

        sufijo = Colores.RESET if tipo == TipoMensaje.TITULO else ""
        print(f"{prefijos.get(tipo, '  ')}{mensaje}{sufijo}")

    def mostrar_splash(self):
        """Muestra la pantalla de inicio animada"""
        if not self.verbose:
            return

        splash = f"""
{Colores.RED}
     ██████╗██╗  ██╗███████╗██████╗ ██████╗  █████╗ ██╗   ██╗██╗
    ██╔════╝██║  ██║██╔════╝██╔══██╗██╔══██╗██╔══██╗██║   ██║██║
    ██║     ███████║█████╗  ██║  ██║██████╔╝███████║██║   ██║██║
    ██║     ██╔══██║██╔══╝  ██║  ██║██╔══██╗██╔══██║██║   ██║██║
    ╚██████╗██║  ██║███████╗██████╔╝██║  ██║██║  ██║╚██████╔╝██║
     ╚═════╝╚═╝  ╚═╝╚══════╝╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝
{Colores.RESET}
        {Colores.CYAN}╔═══════════════════════════════════════════════════╗
        ║     🚛  SISTEMA DE AUTOMATIZACION DE CONSULTAS    ║
        ║              CEDIS CANCUN 427 - SAC               ║
        ╚═══════════════════════════════════════════════════╝{Colores.RESET}
"""
        try:
            ocultar_cursor()
            limpiar_pantalla()

            # Mostrar splash linea por linea
            for linea in splash.split('\n'):
                print(linea)
                time.sleep(0.03)

            print()
            time.sleep(0.5)

        finally:
            mostrar_cursor()

    def barra_progreso(self, actual: int, total: int, mensaje: str = "", ancho: int = 40) -> str:
        """Genera una barra de progreso"""
        if total == 0:
            progreso = 0
        else:
            progreso = actual / total

        completado = int(ancho * progreso)
        restante = ancho - completado

        barra_llena = color_texto(self.BARRA_CHARS['llena'] * completado, Colores.GREEN)
        barra_vacia = color_texto(self.BARRA_CHARS['vacia'] * restante, Colores.BLUE)

        porcentaje = f"{progreso * 100:5.1f}%"

        return f"[{barra_llena}{barra_vacia}] {color_texto(porcentaje, Colores.YELLOW)} {mensaje}"

    def animar_tarea(self, mensaje: str, duracion: float = 2.0, callback: Callable = None):
        """Muestra animacion mientras se ejecuta una tarea"""
        if not self.verbose:
            if callback:
                callback()
            return

        try:
            ocultar_cursor()
            inicio = time.time()
            frame_idx = 0
            spin_idx = 0

            # Si hay callback, ejecutarlo en hilo separado
            resultado_callback = [None]
            error_callback = [None]

            if callback:
                def ejecutar_callback():
                    try:
                        resultado_callback[0] = callback()
                    except Exception as e:
                        error_callback[0] = e

                thread = threading.Thread(target=ejecutar_callback)
                thread.start()

                while thread.is_alive():
                    frame = self.CAMION_FRAMES[frame_idx % len(self.CAMION_FRAMES)]
                    spin = self.SPINNER_CHARS[spin_idx % len(self.SPINNER_CHARS)]

                    print(f"\r   {color_texto(spin, Colores.YELLOW)} {mensaje}... {frame}    ",
                          end="", flush=True)

                    frame_idx += 1
                    spin_idx += 1
                    time.sleep(0.1)

                thread.join()

                if error_callback[0]:
                    print(f"\r   {color_texto('✗', Colores.RED)} {mensaje}... Error           ")
                    raise error_callback[0]
                else:
                    print(f"\r   {color_texto('✓', Colores.GREEN)} {mensaje}... Completado           ")
            else:
                # Solo animacion por duracion
                while time.time() - inicio < duracion:
                    frame = self.CAMION_FRAMES[frame_idx % len(self.CAMION_FRAMES)]
                    spin = self.SPINNER_CHARS[spin_idx % len(self.SPINNER_CHARS)]

                    print(f"\r   {color_texto(spin, Colores.YELLOW)} {mensaje}... {frame}    ",
                          end="", flush=True)

                    frame_idx += 1
                    spin_idx += 1
                    time.sleep(0.1)

                print(f"\r   {color_texto('✓', Colores.GREEN)} {mensaje}... Completado           ")

        finally:
            mostrar_cursor()

    def mostrar_paso(self, numero: int, total: int, titulo: str):
        """Muestra un paso del proceso de setup"""
        if not self.verbose:
            return

        print(f"\n{Colores.BOLD}{Colores.BLUE}[{numero}/{total}] {titulo}{Colores.RESET}")
        print("─" * 60)


# ===============================================================================
# CLASE PRINCIPAL: SETUP MANAGER
# ===============================================================================

class SetupManager:
    """
    Gestor principal del proceso de setup con animaciones integradas.

    Unifica:
    - Verificacion de entorno
    - Creacion de directorios
    - Instalacion de dependencias
    - Configuracion inicial
    - Auto-configuracion del sistema
    """

    def __init__(self, verbose: bool = True, mostrar_splash: bool = True):
        """
        Inicializa el gestor de setup.

        Args:
            verbose: Mostrar mensajes y animaciones
            mostrar_splash: Mostrar pantalla de inicio
        """
        self.verbose = verbose
        self.mostrar_splash = mostrar_splash
        self.animacion = AnimacionCarga(verbose)
        self.resultado = ResultadoSetup()

    def _verificar_paquete(self, nombre: str) -> bool:
        """Verifica si un paquete esta instalado"""
        mapeo = {
            'python-dotenv': 'dotenv',
            'python-dateutil': 'dateutil',
            'python-telegram-bot': 'telegram',
            'Pillow': 'PIL',
            'PyYAML': 'yaml',
            'pydantic-settings': 'pydantic_settings',
        }
        modulo = mapeo.get(nombre, nombre.replace('-', '_').lower())

        try:
            __import__(modulo)
            return True
        except ImportError:
            return False

    def _instalar_paquete(self, paquete: str, silencioso: bool = True) -> bool:
        """Instala un paquete Python"""
        args = [sys.executable, '-m', 'pip', 'install', paquete]
        if silencioso:
            args.extend(['-q', '--disable-pip-version-check'])

        try:
            resultado = subprocess.run(args, capture_output=True, text=True, timeout=120)
            return resultado.returncode == 0
        except:
            return False

    def _ejecutar_comando(self, cmd: List[str], timeout: int = 60) -> Tuple[bool, str]:
        """Ejecuta un comando del sistema"""
        try:
            resultado = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            salida = (resultado.stdout or '') + (resultado.stderr or '')
            return resultado.returncode == 0, salida
        except subprocess.TimeoutExpired:
            return False, "Timeout excedido"
        except Exception as e:
            return False, str(e)

    # =========================================================================
    # PASOS DEL SETUP
    # =========================================================================

    def verificar_python(self) -> bool:
        """Verifica version de Python"""
        version_ok = sys.version_info >= PYTHON_MIN_VERSION

        if version_ok:
            self.animacion._print(
                f"Python {sys.version.split()[0]} - Compatible",
                TipoMensaje.OK
            )
        else:
            self.animacion._print(
                f"Python {sys.version.split()[0]} - Requiere 3.8+",
                TipoMensaje.ERROR
            )
            self.resultado.errores.append(f"Python {PYTHON_MIN_VERSION[0]}.{PYTHON_MIN_VERSION[1]}+ requerido")

        return version_ok

    def verificar_pip(self) -> bool:
        """Verifica que pip este disponible"""
        ok, _ = self._ejecutar_comando([sys.executable, '-m', 'pip', '--version'])

        if ok:
            self.animacion._print("pip disponible", TipoMensaje.OK)
        else:
            self.animacion._print("pip no disponible", TipoMensaje.ERROR)
            self.resultado.errores.append("pip no disponible")

        return ok

    def crear_directorios(self) -> int:
        """Crea la estructura de directorios necesaria"""
        creados = 0

        for dir_path in DIRECTORIOS_REQUERIDOS:
            full_path = BASE_DIR / dir_path
            if not full_path.exists():
                full_path.mkdir(parents=True, exist_ok=True)
                creados += 1

        if creados > 0:
            self.animacion._print(f"{creados} directorios creados", TipoMensaje.OK)
        else:
            self.animacion._print("Estructura de directorios existente", TipoMensaje.OK)

        return creados

    def verificar_env(self) -> bool:
        """Verifica si existe y es valido el archivo .env"""
        if not ENV_FILE.exists():
            self.animacion._print("Archivo .env no encontrado", TipoMensaje.WARN)
            return False

        try:
            with open(ENV_FILE, 'r', encoding='utf-8') as f:
                contenido = f.read()

            # Verificar que tenga credenciales basicas
            tiene_db = 'DB_USER=' in contenido and 'DB_PASSWORD=' in contenido
            tiene_email = 'EMAIL_USER=' in contenido

            if tiene_db and tiene_email:
                self.animacion._print("Configuracion .env valida", TipoMensaje.OK)
                return True
            else:
                self.animacion._print("Configuracion .env incompleta", TipoMensaje.WARN)
                return False

        except Exception as e:
            self.animacion._print(f"Error leyendo .env: {e}", TipoMensaje.ERROR)
            return False

    def instalar_dependencias_core(self) -> Tuple[int, int]:
        """Instala dependencias minimas necesarias"""
        instaladas = 0
        fallidas = 0

        for dep in DEPENDENCIAS_CORE:
            nombre = dep.split('>=')[0].split('==')[0]

            if self._verificar_paquete(nombre):
                instaladas += 1
            else:
                if self._instalar_paquete(dep):
                    instaladas += 1
                    self.animacion._print(f"{nombre} instalado", TipoMensaje.OK)
                else:
                    fallidas += 1
                    self.resultado.dependencias_faltantes.append(nombre)
                    self.animacion._print(f"{nombre} fallo", TipoMensaje.WARN)

        return instaladas, fallidas

    def instalar_dependencias_produccion(self) -> Tuple[int, int]:
        """Instala todas las dependencias de produccion"""
        instaladas = 0
        fallidas = 0
        total = len(DEPENDENCIAS_PRODUCCION)

        for i, dep in enumerate(DEPENDENCIAS_PRODUCCION, 1):
            nombre = dep.split('>=')[0].split('==')[0]

            if self.verbose:
                barra = self.animacion.barra_progreso(i, total, nombre)
                print(f"\r   {barra}    ", end="", flush=True)

            if self._verificar_paquete(nombre):
                instaladas += 1
            else:
                if self._instalar_paquete(dep):
                    instaladas += 1
                else:
                    fallidas += 1
                    self.resultado.dependencias_faltantes.append(nombre)

        if self.verbose:
            print()  # Nueva linea despues de la barra

        return instaladas, fallidas

    def verificar_conectividad(self) -> Dict[str, bool]:
        """Verifica conectividad de red"""
        resultados = {}

        # Internet
        try:
            socket.create_connection(("8.8.8.8", 80), timeout=5)
            resultados['internet'] = True
            self.animacion._print("Conectividad a Internet: OK", TipoMensaje.OK)
        except:
            resultados['internet'] = False
            self.animacion._print("Sin conexion a Internet", TipoMensaje.WARN)
            self.resultado.advertencias.append("Sin conexion a Internet")

        # DB2
        try:
            socket.create_connection(("WM260BASD", 50000), timeout=5)
            resultados['db2'] = True
            self.animacion._print("Servidor DB2: Accesible", TipoMensaje.OK)
        except:
            resultados['db2'] = False
            self.animacion._print("Servidor DB2: No accesible", TipoMensaje.WARN)

        # SMTP
        try:
            socket.create_connection(("smtp.office365.com", 587), timeout=5)
            resultados['smtp'] = True
            self.animacion._print("Servidor SMTP: Accesible", TipoMensaje.OK)
        except:
            resultados['smtp'] = False
            self.animacion._print("Servidor SMTP: No accesible", TipoMensaje.WARN)

        return resultados

    def obtener_info_sistema(self) -> Dict:
        """Obtiene informacion del sistema"""
        info = {
            'os': platform.system(),
            'os_version': platform.release(),
            'arquitectura': platform.machine(),
            'python': sys.version.split()[0],
            'hostname': socket.gethostname(),
            'cpu_count': os.cpu_count() or 1,
        }

        # RAM (si psutil esta disponible)
        try:
            import psutil
            mem = psutil.virtual_memory()
            info['ram_total_gb'] = round(mem.total / (1024**3), 1)
            info['ram_disponible_gb'] = round(mem.available / (1024**3), 1)
        except:
            info['ram_total_gb'] = 'N/A'
            info['ram_disponible_gb'] = 'N/A'

        # Espacio en disco
        try:
            uso = shutil.disk_usage(BASE_DIR)
            info['disco_libre_gb'] = round(uso.free / (1024**3), 1)
        except:
            info['disco_libre_gb'] = 'N/A'

        return info

    def marcar_instalado(self):
        """Marca el sistema como instalado"""
        INSTALADO_FLAG.parent.mkdir(exist_ok=True)

        registro = {
            'timestamp': datetime.now().isoformat(),
            'version': VERSION,
            'python': sys.version.split()[0],
            'sistema': platform.system(),
        }

        with open(INSTALADO_FLAG, 'w', encoding='utf-8') as f:
            json.dump(registro, f, indent=2)

    def esta_instalado(self) -> bool:
        """Verifica si el sistema ya esta instalado"""
        return INSTALADO_FLAG.exists() and ENV_FILE.exists()

    # =========================================================================
    # EJECUCION PRINCIPAL
    # =========================================================================

    def ejecutar(self, forzar: bool = False, solo_verificar: bool = False) -> ResultadoSetup:
        """
        Ejecuta el proceso completo de setup.

        Args:
            forzar: Ejecutar aunque ya este instalado
            solo_verificar: Solo verificar sin instalar

        Returns:
            ResultadoSetup con el resultado del proceso
        """
        inicio = time.time()

        try:
            # Mostrar splash si esta habilitado
            if self.mostrar_splash and self.verbose:
                self.animacion.mostrar_splash()

            # Verificar si ya esta instalado
            if self.esta_instalado() and not forzar:
                if self.verbose:
                    print(f"\n{Colores.GREEN}✓ Sistema SAC ya configurado y listo{Colores.RESET}\n")
                self.resultado.exito = True
                self.resultado.sistema_listo = True
                self.resultado.mensaje = "Sistema ya instalado"
                return self.resultado

            if self.verbose:
                print(f"\n{Colores.CYAN}Iniciando configuracion del sistema...{Colores.RESET}\n")

            # PASO 1: Verificar entorno Python
            self.animacion.mostrar_paso(1, 5, "Verificando Entorno Python")

            def verificar_entorno():
                self.verificar_python()
                self.verificar_pip()

            self.animacion.animar_tarea("Verificando Python y pip", callback=verificar_entorno)

            # PASO 2: Crear estructura de directorios
            self.animacion.mostrar_paso(2, 5, "Preparando Estructura del Proyecto")

            def crear_estructura():
                self.crear_directorios()

            self.animacion.animar_tarea("Creando directorios", callback=crear_estructura)

            # PASO 3: Instalar dependencias
            self.animacion.mostrar_paso(3, 5, "Instalando Dependencias")

            if not solo_verificar:
                # Primero instalar dependencias core
                self.animacion._print("Instalando dependencias core...", TipoMensaje.INFO)
                core_ok, core_fail = self.instalar_dependencias_core()

                # Luego las de produccion con barra de progreso
                self.animacion._print("Instalando dependencias de produccion...", TipoMensaje.INFO)
                prod_ok, prod_fail = self.instalar_dependencias_produccion()

                self.resultado.dependencias_instaladas = core_ok + prod_ok

                if core_fail + prod_fail > 0:
                    self.animacion._print(
                        f"{core_fail + prod_fail} dependencias no pudieron instalarse",
                        TipoMensaje.WARN
                    )
            else:
                self.animacion._print("Modo verificacion - omitiendo instalacion", TipoMensaje.INFO)

            # PASO 4: Verificar configuracion
            self.animacion.mostrar_paso(4, 5, "Verificando Configuracion")

            def verificar_config():
                self.resultado.configuracion_valida = self.verificar_env()

            self.animacion.animar_tarea("Verificando archivo .env", callback=verificar_config)

            if not self.resultado.configuracion_valida:
                self.animacion._print(
                    "Ejecuta 'python instalar_sac.py' para configurar credenciales",
                    TipoMensaje.INFO
                )

            # PASO 5: Verificar conectividad y finalizar
            self.animacion.mostrar_paso(5, 5, "Verificando Sistema")

            def verificar_final():
                self.verificar_conectividad()
                info = self.obtener_info_sistema()
                self.animacion._print(
                    f"Sistema: {info['os']} | RAM: {info.get('ram_disponible_gb', 'N/A')} GB | "
                    f"Disco: {info.get('disco_libre_gb', 'N/A')} GB libre",
                    TipoMensaje.INFO
                )

            self.animacion.animar_tarea("Verificando sistema", callback=verificar_final)

            # Marcar como instalado si todo salio bien
            if not self.resultado.errores and not solo_verificar:
                self.marcar_instalado()
                self.resultado.sistema_listo = True

            # Determinar resultado final
            if self.resultado.errores:
                self.resultado.exito = False
                self.resultado.mensaje = f"Setup con errores: {len(self.resultado.errores)}"
            elif self.resultado.advertencias:
                self.resultado.exito = True
                self.resultado.mensaje = f"Setup completado con {len(self.resultado.advertencias)} advertencias"
            else:
                self.resultado.exito = True
                self.resultado.mensaje = "Setup completado exitosamente"

            # Mostrar resumen
            if self.verbose:
                self._mostrar_resumen()

        except KeyboardInterrupt:
            self.resultado.exito = False
            self.resultado.mensaje = "Setup cancelado por el usuario"
            if self.verbose:
                print(f"\n{Colores.YELLOW}Setup cancelado{Colores.RESET}")

        except Exception as e:
            self.resultado.exito = False
            self.resultado.mensaje = f"Error durante setup: {str(e)}"
            self.resultado.errores.append(str(e))
            if self.verbose:
                print(f"\n{Colores.RED}Error: {e}{Colores.RESET}")

        finally:
            mostrar_cursor()
            self.resultado.duracion_total_seg = time.time() - inicio

        return self.resultado

    def _mostrar_resumen(self):
        """Muestra resumen del proceso de setup"""
        print(f"\n{Colores.BOLD}{'═' * 60}{Colores.RESET}")
        print(f"{Colores.BOLD}RESUMEN DE CONFIGURACION{Colores.RESET}")
        print(f"{'═' * 60}")

        # Estado
        if self.resultado.exito:
            estado = f"{Colores.GREEN}✓ COMPLETADO{Colores.RESET}"
        else:
            estado = f"{Colores.RED}✗ CON ERRORES{Colores.RESET}"
        print(f"\n  Estado: {estado}")
        print(f"  Duracion: {self.resultado.duracion_total_seg:.1f} segundos")
        print(f"  Dependencias: {self.resultado.dependencias_instaladas} instaladas")

        if self.resultado.dependencias_faltantes:
            print(f"  {Colores.YELLOW}Faltantes: {', '.join(self.resultado.dependencias_faltantes[:5])}{Colores.RESET}")

        if self.resultado.advertencias:
            print(f"\n  {Colores.YELLOW}Advertencias ({len(self.resultado.advertencias)}):{Colores.RESET}")
            for adv in self.resultado.advertencias[:3]:
                print(f"    - {adv}")

        if self.resultado.errores:
            print(f"\n  {Colores.RED}Errores ({len(self.resultado.errores)}):{Colores.RESET}")
            for err in self.resultado.errores[:3]:
                print(f"    - {err}")

        print(f"\n{'═' * 60}\n")

        if self.resultado.sistema_listo:
            print(f"  {Colores.GREEN}Sistema SAC listo para operar{Colores.RESET}")
            print(f"  Ejecuta: {Colores.CYAN}python main.py{Colores.RESET}\n")


# ===============================================================================
# FUNCIONES DE CONVENIENCIA
# ===============================================================================

def ejecutar_setup_inicial(
    verbose: bool = True,
    mostrar_splash: bool = True,
    forzar: bool = False
) -> ResultadoSetup:
    """
    Funcion de conveniencia para ejecutar el setup inicial.

    Esta funcion debe llamarse al inicio del sistema para garantizar
    que todo este correctamente configurado.

    Args:
        verbose: Mostrar mensajes y animaciones
        mostrar_splash: Mostrar pantalla de inicio
        forzar: Ejecutar aunque ya este instalado

    Returns:
        ResultadoSetup con el resultado del proceso
    """
    manager = SetupManager(verbose=verbose, mostrar_splash=mostrar_splash)
    return manager.ejecutar(forzar=forzar)


def verificar_sistema_listo() -> bool:
    """
    Verifica rapidamente si el sistema esta listo para operar.

    Returns:
        True si el sistema esta configurado y listo
    """
    return INSTALADO_FLAG.exists() and ENV_FILE.exists()


def obtener_estado_setup() -> Dict:
    """
    Obtiene el estado actual del setup.

    Returns:
        Diccionario con informacion del estado
    """
    estado = {
        'instalado': INSTALADO_FLAG.exists(),
        'env_existe': ENV_FILE.exists(),
        'version': VERSION,
        'timestamp': None,
    }

    if INSTALADO_FLAG.exists():
        try:
            with open(INSTALADO_FLAG, 'r') as f:
                data = json.load(f)
                estado['timestamp'] = data.get('timestamp')
        except:
            pass

    return estado


# ===============================================================================
# EXPORTAR
# ===============================================================================

__all__ = [
    'SetupManager',
    'ResultadoSetup',
    'AnimacionCarga',
    'ejecutar_setup_inicial',
    'verificar_sistema_listo',
    'obtener_estado_setup',
    'EstadoSetup',
    'VERSION',
]


# ===============================================================================
# EJECUCION DIRECTA
# ===============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Setup del Sistema SAC')
    parser.add_argument('--forzar', '-f', action='store_true',
                       help='Forzar re-configuracion')
    parser.add_argument('--silencioso', '-q', action='store_true',
                       help='Modo silencioso sin animaciones')
    parser.add_argument('--verificar', '-v', action='store_true',
                       help='Solo verificar sin instalar')

    args = parser.parse_args()

    resultado = ejecutar_setup_inicial(
        verbose=not args.silencioso,
        mostrar_splash=not args.silencioso,
        forzar=args.forzar
    )

    sys.exit(0 if resultado.exito else 1)
