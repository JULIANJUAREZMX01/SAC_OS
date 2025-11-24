#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════════════════════
MÓDULO DE AUTO-CONFIGURACIÓN DEL SISTEMA SAC
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════════════════════

Este módulo se ejecuta como PRIMER ELEMENTO del script maestro para:
- Recopilar información completa del equipo (CPU, RAM, disco, SO)
- Analizar conectividad de red (DNS, puertos, latencia)
- Verificar entorno Python y dependencias
- Escanear documentos y datos necesarios
- Optimizar recursos del sistema para ejecución óptima
- Configurar automáticamente parámetros según capacidades detectadas

Uso:
    from modules.modulo_auto_config import AutoConfigurador

    configurador = AutoConfigurador()
    resultado = configurador.ejecutar_configuracion_completa()

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún 427

Versión: 1.0.0
Última actualización: Noviembre 2025
═══════════════════════════════════════════════════════════════════════════════
"""

import os
import sys
import platform
import socket
import subprocess
import shutil
import json
import logging
import time
import threading
import gc
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
import importlib.util

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTES Y CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════════════════════

# Importar versión desde configuración centralizada
from config import VERSION

# Colores para terminal
class Colores:
    """Códigos de colores ANSI para terminal"""
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


class NivelOptimizacion(Enum):
    """Niveles de optimización del sistema"""
    MINIMO = "minimo"       # Recursos muy limitados
    BAJO = "bajo"           # Recursos limitados
    NORMAL = "normal"       # Recursos adecuados
    ALTO = "alto"           # Buenos recursos
    MAXIMO = "maximo"       # Recursos abundantes


class EstadoComponente(Enum):
    """Estados de los componentes del sistema"""
    OK = "ok"
    WARNING = "warning"
    ERROR = "error"
    NOT_AVAILABLE = "not_available"


# ═══════════════════════════════════════════════════════════════════════════════
# ESTRUCTURAS DE DATOS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class InfoCPU:
    """Información del procesador"""
    nombre: str = ""
    nucleos_fisicos: int = 0
    nucleos_logicos: int = 0
    frecuencia_max_mhz: float = 0.0
    frecuencia_actual_mhz: float = 0.0
    uso_porcentaje: float = 0.0
    arquitectura: str = ""


@dataclass
class InfoMemoria:
    """Información de memoria RAM"""
    total_gb: float = 0.0
    disponible_gb: float = 0.0
    usada_gb: float = 0.0
    porcentaje_uso: float = 0.0
    swap_total_gb: float = 0.0
    swap_usado_gb: float = 0.0


@dataclass
class InfoDisco:
    """Información de almacenamiento"""
    ruta: str = ""
    total_gb: float = 0.0
    usado_gb: float = 0.0
    libre_gb: float = 0.0
    porcentaje_uso: float = 0.0
    tipo_fs: str = ""


@dataclass
class InfoSistemaOperativo:
    """Información del sistema operativo"""
    nombre: str = ""
    version: str = ""
    arquitectura: str = ""
    hostname: str = ""
    usuario_actual: str = ""
    directorio_home: str = ""
    directorio_trabajo: str = ""
    variables_entorno: Dict[str, str] = field(default_factory=dict)


@dataclass
class InfoRed:
    """Información de red"""
    hostname: str = ""
    ip_local: str = ""
    interfaces: List[Dict] = field(default_factory=list)
    dns_servers: List[str] = field(default_factory=list)
    conectividad_internet: bool = False
    latencia_internet_ms: float = 0.0
    puertos_db_accesibles: Dict[str, bool] = field(default_factory=dict)


@dataclass
class InfoPython:
    """Información del entorno Python"""
    version: str = ""
    version_info: Tuple = ()
    ejecutable: str = ""
    ruta_paquetes: str = ""
    encoding: str = ""
    paquetes_instalados: Dict[str, str] = field(default_factory=dict)
    paquetes_faltantes: List[str] = field(default_factory=list)


@dataclass
class InfoProyecto:
    """Información del proyecto SAC"""
    directorio_base: str = ""
    archivos_python: int = 0
    archivos_sql: int = 0
    archivos_config: int = 0
    archivos_docs: int = 0
    tamaño_total_mb: float = 0.0
    estructura_valida: bool = False
    modulos_disponibles: Dict[str, bool] = field(default_factory=dict)


@dataclass
class ConfiguracionOptima:
    """Configuración óptima calculada"""
    nivel_optimizacion: NivelOptimizacion = NivelOptimizacion.NORMAL
    pool_conexiones_db: int = 3
    workers_procesamiento: int = 2
    buffer_memoria_mb: int = 256
    timeout_queries_seg: int = 30
    batch_size_registros: int = 1000
    cache_habilitado: bool = True
    compresion_logs: bool = False
    intervalo_monitoreo_seg: int = 300
    reintentos_conexion: int = 3


@dataclass
class ResultadoConfiguracion:
    """Resultado completo de la auto-configuración"""
    timestamp: str = ""
    duracion_segundos: float = 0.0
    estado_general: EstadoComponente = EstadoComponente.OK

    # Información recopilada
    cpu: InfoCPU = field(default_factory=InfoCPU)
    memoria: InfoMemoria = field(default_factory=InfoMemoria)
    discos: List[InfoDisco] = field(default_factory=list)
    sistema_operativo: InfoSistemaOperativo = field(default_factory=InfoSistemaOperativo)
    red: InfoRed = field(default_factory=InfoRed)
    python: InfoPython = field(default_factory=InfoPython)
    proyecto: InfoProyecto = field(default_factory=InfoProyecto)

    # Configuración calculada
    configuracion_optima: ConfiguracionOptima = field(default_factory=ConfiguracionOptima)

    # Mensajes y alertas
    mensajes: List[str] = field(default_factory=list)
    advertencias: List[str] = field(default_factory=list)
    errores: List[str] = field(default_factory=list)
    optimizaciones_aplicadas: List[str] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════════════
# CLASE PRINCIPAL: AUTO-CONFIGURADOR
# ═══════════════════════════════════════════════════════════════════════════════

class AutoConfigurador:
    """
    Clase principal para auto-configuración del sistema SAC.

    Recopila información completa del sistema, analiza capacidades,
    y configura parámetros óptimos para la ejecución de la aplicación.
    """

    # Arte ASCII para el módulo
    LOGO = """
    ╔═══════════════════════════════════════════════════════════════════════════╗
    ║                                                                           ║
    ║     █████╗ ██╗   ██╗████████╗ ██████╗        ██████╗ ██████╗ ███╗   ██╗  ║
    ║    ██╔══██╗██║   ██║╚══██╔══╝██╔═══██╗      ██╔════╝██╔═══██╗████╗  ██║  ║
    ║    ███████║██║   ██║   ██║   ██║   ██║█████╗██║     ██║   ██║██╔██╗ ██║  ║
    ║    ██╔══██║██║   ██║   ██║   ██║   ██║╚════╝██║     ██║   ██║██║╚██╗██║  ║
    ║    ██║  ██║╚██████╔╝   ██║   ╚██████╔╝      ╚██████╗╚██████╔╝██║ ╚████║  ║
    ║    ╚═╝  ╚═╝ ╚═════╝    ╚═╝    ╚═════╝        ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝  ║
    ║                                                                           ║
    ║          MÓDULO DE AUTO-CONFIGURACIÓN - SISTEMA SAC v1.0                  ║
    ║                                                                           ║
    ╚═══════════════════════════════════════════════════════════════════════════╝
    """

    def __init__(self, base_dir: Path = None, verbose: bool = True):
        """
        Inicializa el auto-configurador.

        Args:
            base_dir: Directorio base del proyecto (auto-detecta si es None)
            verbose: Si True, muestra mensajes en consola
        """
        self.base_dir = base_dir or Path(__file__).resolve().parent.parent
        self.verbose = verbose
        self.resultado = ResultadoConfiguracion()
        self.logger = self._configurar_logging()

        # Dependencias requeridas por el proyecto SAC
        self.dependencias_requeridas = [
            'pandas',
            'openpyxl',
            'python-dotenv',
            'schedule',
            'colorama',
            'tqdm',
            'requests',
            'jinja2',
        ]

        # Dependencias opcionales
        self.dependencias_opcionales = [
            'pyodbc',           # Conexión DB2
            'ibm_db',           # Conexión IBM DB2 nativa
            'matplotlib',       # Gráficos
            'numpy',            # Cálculos numéricos
            'psutil',           # Info del sistema
            'aiohttp',          # Async HTTP
        ]

        # Puertos a verificar
        self.puertos_verificar = {
            'DB2': [('WM260BASD', 50000)],
            'SMTP': [('smtp.office365.com', 587)],
            'HTTP': [('www.google.com', 80), ('www.chedraui.com.mx', 443)],
        }

    def _configurar_logging(self) -> logging.Logger:
        """Configura el sistema de logging"""
        logger = logging.getLogger('AutoConfigurador')
        logger.setLevel(logging.DEBUG)

        # Handler para archivo
        log_dir = self.base_dir / 'output' / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)

        fecha = datetime.now().strftime('%Y%m%d')
        log_file = log_dir / f'auto_config_{fecha}.log'

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))

        logger.addHandler(file_handler)
        return logger

    def _print(self, mensaje: str, tipo: str = "info"):
        """Imprime mensaje en consola con formato"""
        if not self.verbose:
            return

        prefijos = {
            "info": f"  {Colores.CYAN}ℹ{Colores.RESET}",
            "ok": f"  {Colores.GREEN}✓{Colores.RESET}",
            "warn": f"  {Colores.YELLOW}⚠{Colores.RESET}",
            "error": f"  {Colores.RED}✗{Colores.RESET}",
            "titulo": f"\n  {Colores.BOLD}{Colores.BLUE}",
            "subtitulo": f"  {Colores.CYAN}",
        }

        sufijo = Colores.RESET if tipo in ["titulo", "subtitulo"] else ""
        print(f"{prefijos.get(tipo, '  ')}{mensaje}{sufijo}")

    def _ejecutar_comando(self, comando: List[str], timeout: int = 10) -> Tuple[bool, str]:
        """Ejecuta un comando del sistema y retorna resultado"""
        try:
            resultado = subprocess.run(
                comando,
                capture_output=True,
                text=True,
                timeout=timeout,
                shell=(platform.system() == 'Windows')
            )
            return resultado.returncode == 0, resultado.stdout.strip()
        except subprocess.TimeoutExpired:
            return False, "Timeout"
        except Exception as e:
            return False, str(e)

    # ═══════════════════════════════════════════════════════════════════════════
    # RECOPILACIÓN DE INFORMACIÓN DEL SISTEMA
    # ═══════════════════════════════════════════════════════════════════════════

    def recopilar_info_cpu(self) -> InfoCPU:
        """Recopila información del procesador"""
        self._print("Analizando procesador...", "subtitulo")

        info = InfoCPU()
        info.arquitectura = platform.machine()
        info.nucleos_logicos = os.cpu_count() or 1

        # Intentar obtener más info con psutil si está disponible
        try:
            import psutil
            info.nucleos_fisicos = psutil.cpu_count(logical=False) or info.nucleos_logicos
            info.uso_porcentaje = psutil.cpu_percent(interval=0.5)

            freq = psutil.cpu_freq()
            if freq:
                info.frecuencia_max_mhz = freq.max
                info.frecuencia_actual_mhz = freq.current
        except ImportError:
            info.nucleos_fisicos = info.nucleos_logicos

        # Obtener nombre del procesador
        if platform.system() == 'Windows':
            info.nombre = platform.processor()
        elif platform.system() == 'Linux':
            try:
                with open('/proc/cpuinfo', 'r') as f:
                    for line in f:
                        if 'model name' in line:
                            info.nombre = line.split(':')[1].strip()
                            break
            except:
                info.nombre = platform.processor()
        else:
            info.nombre = platform.processor()

        self._print(f"CPU: {info.nombre[:50]}... ({info.nucleos_logicos} núcleos)", "ok")
        self.resultado.cpu = info
        return info

    def recopilar_info_memoria(self) -> InfoMemoria:
        """Recopila información de memoria RAM"""
        self._print("Analizando memoria RAM...", "subtitulo")

        info = InfoMemoria()

        try:
            import psutil
            mem = psutil.virtual_memory()
            info.total_gb = mem.total / (1024**3)
            info.disponible_gb = mem.available / (1024**3)
            info.usada_gb = mem.used / (1024**3)
            info.porcentaje_uso = mem.percent

            swap = psutil.swap_memory()
            info.swap_total_gb = swap.total / (1024**3)
            info.swap_usado_gb = swap.used / (1024**3)

            self._print(
                f"RAM: {info.total_gb:.1f} GB total, {info.disponible_gb:.1f} GB disponible "
                f"({info.porcentaje_uso:.1f}% uso)", "ok"
            )
        except ImportError:
            # Fallback sin psutil
            if platform.system() == 'Linux':
                try:
                    with open('/proc/meminfo', 'r') as f:
                        lines = f.readlines()
                        for line in lines:
                            if 'MemTotal' in line:
                                info.total_gb = int(line.split()[1]) / (1024**2)
                            elif 'MemAvailable' in line:
                                info.disponible_gb = int(line.split()[1]) / (1024**2)
                    info.usada_gb = info.total_gb - info.disponible_gb
                    info.porcentaje_uso = (info.usada_gb / info.total_gb) * 100 if info.total_gb > 0 else 0
                    self._print(f"RAM: {info.total_gb:.1f} GB total (sin psutil)", "ok")
                except:
                    self._print("No se pudo obtener información de memoria", "warn")
            else:
                self._print("Instalar psutil para información detallada de memoria", "warn")

        self.resultado.memoria = info
        return info

    def recopilar_info_disco(self) -> List[InfoDisco]:
        """Recopila información de almacenamiento"""
        self._print("Analizando almacenamiento...", "subtitulo")

        discos = []

        # Obtener info del disco del proyecto
        try:
            uso = shutil.disk_usage(self.base_dir)
            info_proyecto = InfoDisco(
                ruta=str(self.base_dir),
                total_gb=uso.total / (1024**3),
                usado_gb=uso.used / (1024**3),
                libre_gb=uso.free / (1024**3),
                porcentaje_uso=(uso.used / uso.total) * 100
            )
            discos.append(info_proyecto)

            self._print(
                f"Disco proyecto: {info_proyecto.libre_gb:.1f} GB libre de "
                f"{info_proyecto.total_gb:.1f} GB ({info_proyecto.porcentaje_uso:.1f}% uso)", "ok"
            )

            # Advertencia si queda poco espacio
            if info_proyecto.libre_gb < 1:
                self._print("¡Espacio en disco crítico! Menos de 1 GB libre", "error")
                self.resultado.errores.append("Espacio en disco crítico")
            elif info_proyecto.libre_gb < 5:
                self._print("Espacio en disco bajo. Menos de 5 GB libre", "warn")
                self.resultado.advertencias.append("Espacio en disco bajo")

        except Exception as e:
            self._print(f"Error al obtener info de disco: {e}", "error")

        # Intentar obtener info de todos los discos con psutil
        try:
            import psutil
            for particion in psutil.disk_partitions(all=False):
                try:
                    uso = psutil.disk_usage(particion.mountpoint)
                    info = InfoDisco(
                        ruta=particion.mountpoint,
                        total_gb=uso.total / (1024**3),
                        usado_gb=uso.used / (1024**3),
                        libre_gb=uso.free / (1024**3),
                        porcentaje_uso=uso.percent,
                        tipo_fs=particion.fstype
                    )
                    if info.ruta != str(self.base_dir):
                        discos.append(info)
                except:
                    pass
        except ImportError:
            pass

        self.resultado.discos = discos
        return discos

    def recopilar_info_so(self) -> InfoSistemaOperativo:
        """Recopila información del sistema operativo"""
        self._print("Analizando sistema operativo...", "subtitulo")

        info = InfoSistemaOperativo(
            nombre=platform.system(),
            version=platform.release(),
            arquitectura=platform.machine(),
            hostname=socket.gethostname(),
            usuario_actual=os.getenv('USER') or os.getenv('USERNAME') or 'unknown',
            directorio_home=str(Path.home()),
            directorio_trabajo=str(Path.cwd()),
        )

        # Variables de entorno relevantes
        env_relevantes = [
            'PATH', 'PYTHONPATH', 'VIRTUAL_ENV', 'CONDA_PREFIX',
            'DB_HOST', 'DB_PORT', 'DB_USER', 'EMAIL_USER',
            'LANG', 'LC_ALL', 'TZ', 'TERM'
        ]

        for var in env_relevantes:
            valor = os.getenv(var)
            if valor:
                # Ocultar valores sensibles
                if 'PASSWORD' in var or 'SECRET' in var or 'TOKEN' in var:
                    info.variables_entorno[var] = '***OCULTO***'
                else:
                    info.variables_entorno[var] = valor[:100]  # Limitar longitud

        self._print(f"SO: {info.nombre} {info.version} ({info.arquitectura})", "ok")
        self._print(f"Host: {info.hostname} | Usuario: {info.usuario_actual}", "ok")

        self.resultado.sistema_operativo = info
        return info

    def recopilar_info_red(self) -> InfoRed:
        """Recopila información de red y conectividad"""
        self._print("Analizando red y conectividad...", "subtitulo")

        info = InfoRed()
        info.hostname = socket.gethostname()

        # IP local
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            info.ip_local = s.getsockname()[0]
            s.close()
            self._print(f"IP Local: {info.ip_local}", "ok")
        except:
            info.ip_local = "127.0.0.1"
            self._print("No se pudo determinar IP local", "warn")

        # Interfaces de red (con psutil)
        try:
            import psutil
            for nombre, addrs in psutil.net_if_addrs().items():
                for addr in addrs:
                    if addr.family == socket.AF_INET:
                        info.interfaces.append({
                            'nombre': nombre,
                            'ip': addr.address,
                            'mascara': addr.netmask
                        })
        except ImportError:
            pass

        # Servidores DNS
        try:
            if platform.system() == 'Linux':
                with open('/etc/resolv.conf', 'r') as f:
                    for line in f:
                        if line.startswith('nameserver'):
                            info.dns_servers.append(line.split()[1])
        except:
            pass

        # Verificar conectividad a internet
        self._print("Verificando conectividad a internet...", "subtitulo")
        servidores_test = ['8.8.8.8', '1.1.1.1', 'www.google.com']

        for servidor in servidores_test:
            try:
                inicio = time.time()
                socket.create_connection((servidor, 80), timeout=5)
                latencia = (time.time() - inicio) * 1000
                info.conectividad_internet = True
                info.latencia_internet_ms = latencia
                self._print(f"Internet: Conectado (latencia: {latencia:.0f}ms)", "ok")
                break
            except:
                continue

        if not info.conectividad_internet:
            self._print("Sin conexión a internet", "warn")
            self.resultado.advertencias.append("Sin conexión a internet")

        # Verificar puertos importantes
        self._print("Verificando accesibilidad de puertos...", "subtitulo")
        for servicio, puertos in self.puertos_verificar.items():
            for host, puerto in puertos:
                try:
                    socket.create_connection((host, puerto), timeout=5)
                    info.puertos_db_accesibles[f"{servicio}:{host}:{puerto}"] = True
                    self._print(f"{servicio} ({host}:{puerto}): Accesible", "ok")
                except:
                    info.puertos_db_accesibles[f"{servicio}:{host}:{puerto}"] = False
                    self._print(f"{servicio} ({host}:{puerto}): No accesible", "warn")

        self.resultado.red = info
        return info

    def recopilar_info_python(self) -> InfoPython:
        """Recopila información del entorno Python"""
        self._print("Analizando entorno Python...", "subtitulo")

        info = InfoPython(
            version=platform.python_version(),
            version_info=sys.version_info[:3],
            ejecutable=sys.executable,
            ruta_paquetes=str(Path(sys.executable).parent / 'Lib' / 'site-packages'),
            encoding=sys.getdefaultencoding(),
        )

        self._print(f"Python: {info.version} ({info.ejecutable})", "ok")

        # Verificar paquetes instalados
        self._print("Verificando dependencias requeridas...", "subtitulo")

        for paquete in self.dependencias_requeridas:
            try:
                spec = importlib.util.find_spec(paquete.replace('-', '_'))
                if spec:
                    # Obtener versión si es posible
                    try:
                        mod = __import__(paquete.replace('-', '_'))
                        version = getattr(mod, '__version__', 'instalado')
                    except:
                        version = 'instalado'
                    info.paquetes_instalados[paquete] = version
                    self._print(f"{paquete}: {version}", "ok")
                else:
                    info.paquetes_faltantes.append(paquete)
                    self._print(f"{paquete}: NO INSTALADO", "error")
            except Exception as e:
                info.paquetes_faltantes.append(paquete)
                self._print(f"{paquete}: Error - {e}", "error")

        # Verificar paquetes opcionales
        self._print("Verificando dependencias opcionales...", "subtitulo")
        for paquete in self.dependencias_opcionales:
            try:
                spec = importlib.util.find_spec(paquete.replace('-', '_'))
                if spec:
                    info.paquetes_instalados[paquete] = 'instalado'
                    self._print(f"{paquete}: Disponible", "ok")
                else:
                    self._print(f"{paquete}: No instalado (opcional)", "info")
            except:
                self._print(f"{paquete}: No instalado (opcional)", "info")

        # Registrar paquetes faltantes como advertencia
        if info.paquetes_faltantes:
            self.resultado.errores.append(
                f"Dependencias faltantes: {', '.join(info.paquetes_faltantes)}"
            )

        self.resultado.python = info
        return info

    def recopilar_info_proyecto(self) -> InfoProyecto:
        """Recopila información del proyecto SAC"""
        self._print("Analizando estructura del proyecto...", "subtitulo")

        info = InfoProyecto(directorio_base=str(self.base_dir))

        # Contar archivos por tipo
        for archivo in self.base_dir.rglob('*'):
            if archivo.is_file():
                if archivo.suffix == '.py':
                    info.archivos_python += 1
                elif archivo.suffix == '.sql':
                    info.archivos_sql += 1
                elif archivo.suffix in ['.md', '.txt', '.rst']:
                    info.archivos_docs += 1
                elif archivo.suffix in ['.env', '.ini', '.cfg', '.json', '.yaml']:
                    info.archivos_config += 1

                try:
                    info.tamaño_total_mb += archivo.stat().st_size / (1024**2)
                except:
                    pass

        self._print(
            f"Archivos: {info.archivos_python} .py, {info.archivos_sql} .sql, "
            f"{info.archivos_docs} docs, {info.archivos_config} config", "ok"
        )
        self._print(f"Tamaño total: {info.tamaño_total_mb:.2f} MB", "ok")

        # Verificar estructura de directorios requerida
        directorios_requeridos = [
            'modules', 'queries', 'config', 'docs', 'tests',
            'output', 'output/logs', 'output/resultados'
        ]

        estructura_ok = True
        for dir_name in directorios_requeridos:
            dir_path = self.base_dir / dir_name
            if not dir_path.exists():
                self._print(f"Directorio faltante: {dir_name}", "warn")
                estructura_ok = False
                # Crear directorio faltante
                dir_path.mkdir(parents=True, exist_ok=True)
                self._print(f"Directorio creado: {dir_name}", "ok")

        info.estructura_valida = estructura_ok

        # Verificar módulos principales del proyecto
        modulos_principales = [
            'config', 'monitor', 'gestor_correos', 'main',
            'modules.reportes_excel', 'modules.db_connection'
        ]

        self._print("Verificando módulos del proyecto...", "subtitulo")
        for modulo in modulos_principales:
            try:
                spec = importlib.util.find_spec(modulo)
                if spec:
                    info.modulos_disponibles[modulo] = True
                    self._print(f"Módulo {modulo}: Disponible", "ok")
                else:
                    info.modulos_disponibles[modulo] = False
                    self._print(f"Módulo {modulo}: No encontrado", "warn")
            except Exception as e:
                info.modulos_disponibles[modulo] = False
                self._print(f"Módulo {modulo}: Error - {str(e)[:30]}", "warn")

        self.resultado.proyecto = info
        return info

    # ═══════════════════════════════════════════════════════════════════════════
    # CÁLCULO DE CONFIGURACIÓN ÓPTIMA
    # ═══════════════════════════════════════════════════════════════════════════

    def calcular_configuracion_optima(self) -> ConfiguracionOptima:
        """Calcula la configuración óptima basada en recursos del sistema"""
        self._print("Calculando configuración óptima...", "titulo")

        config = ConfiguracionOptima()

        # Determinar nivel de optimización basado en RAM disponible
        ram_disponible = self.resultado.memoria.disponible_gb
        cpu_nucleos = self.resultado.cpu.nucleos_logicos

        if ram_disponible >= 8 and cpu_nucleos >= 8:
            config.nivel_optimizacion = NivelOptimizacion.MAXIMO
        elif ram_disponible >= 4 and cpu_nucleos >= 4:
            config.nivel_optimizacion = NivelOptimizacion.ALTO
        elif ram_disponible >= 2 and cpu_nucleos >= 2:
            config.nivel_optimizacion = NivelOptimizacion.NORMAL
        elif ram_disponible >= 1:
            config.nivel_optimizacion = NivelOptimizacion.BAJO
        else:
            config.nivel_optimizacion = NivelOptimizacion.MINIMO

        self._print(f"Nivel de optimización: {config.nivel_optimizacion.value.upper()}", "ok")

        # Configurar parámetros según nivel
        niveles = {
            NivelOptimizacion.MAXIMO: {
                'pool_conexiones_db': 10,
                'workers_procesamiento': cpu_nucleos,
                'buffer_memoria_mb': 1024,
                'timeout_queries_seg': 60,
                'batch_size_registros': 5000,
                'cache_habilitado': True,
                'compresion_logs': True,
                'intervalo_monitoreo_seg': 60,
                'reintentos_conexion': 5,
            },
            NivelOptimizacion.ALTO: {
                'pool_conexiones_db': 5,
                'workers_procesamiento': max(cpu_nucleos - 2, 2),
                'buffer_memoria_mb': 512,
                'timeout_queries_seg': 45,
                'batch_size_registros': 2500,
                'cache_habilitado': True,
                'compresion_logs': True,
                'intervalo_monitoreo_seg': 120,
                'reintentos_conexion': 4,
            },
            NivelOptimizacion.NORMAL: {
                'pool_conexiones_db': 3,
                'workers_procesamiento': max(cpu_nucleos // 2, 2),
                'buffer_memoria_mb': 256,
                'timeout_queries_seg': 30,
                'batch_size_registros': 1000,
                'cache_habilitado': True,
                'compresion_logs': False,
                'intervalo_monitoreo_seg': 300,
                'reintentos_conexion': 3,
            },
            NivelOptimizacion.BAJO: {
                'pool_conexiones_db': 2,
                'workers_procesamiento': 1,
                'buffer_memoria_mb': 128,
                'timeout_queries_seg': 20,
                'batch_size_registros': 500,
                'cache_habilitado': False,
                'compresion_logs': False,
                'intervalo_monitoreo_seg': 600,
                'reintentos_conexion': 2,
            },
            NivelOptimizacion.MINIMO: {
                'pool_conexiones_db': 1,
                'workers_procesamiento': 1,
                'buffer_memoria_mb': 64,
                'timeout_queries_seg': 15,
                'batch_size_registros': 100,
                'cache_habilitado': False,
                'compresion_logs': False,
                'intervalo_monitoreo_seg': 900,
                'reintentos_conexion': 1,
            },
        }

        # Aplicar configuración del nivel
        params = niveles.get(config.nivel_optimizacion, niveles[NivelOptimizacion.NORMAL])
        for key, value in params.items():
            setattr(config, key, value)

        # Mostrar configuración
        self._print(f"  Pool conexiones DB: {config.pool_conexiones_db}", "info")
        self._print(f"  Workers procesamiento: {config.workers_procesamiento}", "info")
        self._print(f"  Buffer memoria: {config.buffer_memoria_mb} MB", "info")
        self._print(f"  Timeout queries: {config.timeout_queries_seg} seg", "info")
        self._print(f"  Batch size: {config.batch_size_registros} registros", "info")
        self._print(f"  Cache: {'Habilitado' if config.cache_habilitado else 'Deshabilitado'}", "info")
        self._print(f"  Intervalo monitoreo: {config.intervalo_monitoreo_seg} seg", "info")

        self.resultado.configuracion_optima = config
        return config

    # ═══════════════════════════════════════════════════════════════════════════
    # OPTIMIZACIONES DEL SISTEMA
    # ═══════════════════════════════════════════════════════════════════════════

    def aplicar_optimizaciones(self) -> List[str]:
        """Aplica optimizaciones al sistema"""
        self._print("Aplicando optimizaciones...", "titulo")

        optimizaciones = []

        # 1. Limpiar caché de Python
        gc.collect()
        optimizaciones.append("Limpieza de caché de Python")
        self._print("Caché de Python limpiado", "ok")

        # 2. Crear directorios necesarios
        directorios = [
            self.base_dir / 'output' / 'logs',
            self.base_dir / 'output' / 'resultados',
            self.base_dir / 'output' / 'cache',
            self.base_dir / 'output' / 'temp',
        ]

        for dir_path in directorios:
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                optimizaciones.append(f"Directorio creado: {dir_path.name}")
                self._print(f"Directorio creado: {dir_path.name}", "ok")

        # 3. Limpiar archivos temporales antiguos
        temp_dir = self.base_dir / 'output' / 'temp'
        if temp_dir.exists():
            archivos_eliminados = 0
            for archivo in temp_dir.glob('*'):
                try:
                    if archivo.is_file():
                        # Eliminar archivos de más de 7 días
                        edad = time.time() - archivo.stat().st_mtime
                        if edad > 7 * 24 * 3600:
                            archivo.unlink()
                            archivos_eliminados += 1
                except:
                    pass

            if archivos_eliminados > 0:
                optimizaciones.append(f"Archivos temporales eliminados: {archivos_eliminados}")
                self._print(f"Archivos temporales eliminados: {archivos_eliminados}", "ok")

        # 4. Rotar logs antiguos
        logs_dir = self.base_dir / 'output' / 'logs'
        if logs_dir.exists():
            logs_rotados = 0
            for log_file in logs_dir.glob('*.log'):
                try:
                    # Si el log es mayor a 10 MB, comprimirlo
                    if log_file.stat().st_size > 10 * 1024 * 1024:
                        import gzip
                        with open(log_file, 'rb') as f_in:
                            with gzip.open(f"{log_file}.gz", 'wb') as f_out:
                                f_out.writelines(f_in)
                        log_file.unlink()
                        logs_rotados += 1
                except:
                    pass

            if logs_rotados > 0:
                optimizaciones.append(f"Logs rotados: {logs_rotados}")
                self._print(f"Logs rotados: {logs_rotados}", "ok")

        # 5. Establecer variables de entorno para optimización
        os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # No crear .pyc
        optimizaciones.append("Variables de entorno optimizadas")
        self._print("Variables de entorno optimizadas", "ok")

        # 6. Verificar y ajustar límites del sistema (Linux)
        if platform.system() == 'Linux':
            try:
                import resource
                # Aumentar límite de archivos abiertos si es posible
                soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
                if soft < 4096 and hard >= 4096:
                    resource.setrlimit(resource.RLIMIT_NOFILE, (4096, hard))
                    optimizaciones.append("Límite de archivos abiertos aumentado")
                    self._print("Límite de archivos abiertos aumentado", "ok")
            except:
                pass

        self.resultado.optimizaciones_aplicadas = optimizaciones
        return optimizaciones

    def instalar_dependencias_faltantes(self) -> bool:
        """Intenta instalar dependencias faltantes"""
        if not self.resultado.python.paquetes_faltantes:
            return True

        self._print("Instalando dependencias faltantes...", "titulo")

        for paquete in self.resultado.python.paquetes_faltantes[:]:
            self._print(f"Instalando {paquete}...", "info")
            try:
                subprocess.run(
                    [sys.executable, '-m', 'pip', 'install', paquete, '-q'],
                    capture_output=True,
                    timeout=120
                )
                self._print(f"{paquete} instalado correctamente", "ok")
                self.resultado.python.paquetes_faltantes.remove(paquete)
                self.resultado.python.paquetes_instalados[paquete] = 'recién instalado'
            except Exception as e:
                self._print(f"Error instalando {paquete}: {e}", "error")

        return len(self.resultado.python.paquetes_faltantes) == 0

    # ═══════════════════════════════════════════════════════════════════════════
    # GENERACIÓN DE REPORTE
    # ═══════════════════════════════════════════════════════════════════════════

    def generar_reporte_json(self) -> str:
        """Genera un reporte JSON con toda la información"""
        reporte_path = self.base_dir / 'output' / 'auto_config_report.json'

        # Convertir enums a strings para JSON
        resultado_dict = asdict(self.resultado)
        resultado_dict['estado_general'] = self.resultado.estado_general.value
        resultado_dict['configuracion_optima']['nivel_optimizacion'] = \
            self.resultado.configuracion_optima.nivel_optimizacion.value

        with open(reporte_path, 'w', encoding='utf-8') as f:
            json.dump(resultado_dict, f, indent=2, ensure_ascii=False, default=str)

        self._print(f"Reporte JSON guardado: {reporte_path}", "ok")
        return str(reporte_path)

    def mostrar_resumen(self):
        """Muestra un resumen del resultado de la configuración"""
        print(f"\n{Colores.BOLD}{Colores.BLUE}{'═' * 70}{Colores.RESET}")
        print(f"{Colores.BOLD}{Colores.BLUE}{'RESUMEN DE AUTO-CONFIGURACIÓN'.center(70)}{Colores.RESET}")
        print(f"{Colores.BOLD}{Colores.BLUE}{'═' * 70}{Colores.RESET}\n")

        # Estado general
        estado_color = {
            EstadoComponente.OK: Colores.GREEN,
            EstadoComponente.WARNING: Colores.YELLOW,
            EstadoComponente.ERROR: Colores.RED,
        }
        color = estado_color.get(self.resultado.estado_general, Colores.WHITE)
        print(f"  Estado General: {color}{self.resultado.estado_general.value.upper()}{Colores.RESET}")
        print(f"  Duración: {self.resultado.duracion_segundos:.2f} segundos")
        print(f"  Nivel Optimización: {self.resultado.configuracion_optima.nivel_optimizacion.value.upper()}")

        # Recursos
        print(f"\n  {Colores.CYAN}RECURSOS DEL SISTEMA:{Colores.RESET}")
        print(f"    CPU: {self.resultado.cpu.nucleos_logicos} núcleos")
        print(f"    RAM: {self.resultado.memoria.total_gb:.1f} GB "
              f"({self.resultado.memoria.disponible_gb:.1f} GB disponible)")
        if self.resultado.discos:
            print(f"    Disco: {self.resultado.discos[0].libre_gb:.1f} GB libre")

        # Red
        print(f"\n  {Colores.CYAN}CONECTIVIDAD:{Colores.RESET}")
        print(f"    Internet: {'✓ Conectado' if self.resultado.red.conectividad_internet else '✗ Sin conexión'}")
        print(f"    IP Local: {self.resultado.red.ip_local}")

        # Python
        print(f"\n  {Colores.CYAN}ENTORNO PYTHON:{Colores.RESET}")
        print(f"    Versión: {self.resultado.python.version}")
        print(f"    Dependencias: {len(self.resultado.python.paquetes_instalados)} instaladas")
        if self.resultado.python.paquetes_faltantes:
            print(f"    {Colores.RED}Faltantes: {', '.join(self.resultado.python.paquetes_faltantes)}{Colores.RESET}")

        # Estadísticas
        if self.resultado.advertencias:
            print(f"\n  {Colores.YELLOW}ADVERTENCIAS ({len(self.resultado.advertencias)}):{Colores.RESET}")
            for adv in self.resultado.advertencias[:5]:
                print(f"    ⚠ {adv}")

        if self.resultado.errores:
            print(f"\n  {Colores.RED}ERRORES ({len(self.resultado.errores)}):{Colores.RESET}")
            for err in self.resultado.errores[:5]:
                print(f"    ✗ {err}")

        if self.resultado.optimizaciones_aplicadas:
            print(f"\n  {Colores.GREEN}OPTIMIZACIONES APLICADAS ({len(self.resultado.optimizaciones_aplicadas)}):{Colores.RESET}")
            for opt in self.resultado.optimizaciones_aplicadas[:5]:
                print(f"    ✓ {opt}")

        print(f"\n{Colores.BOLD}{Colores.BLUE}{'═' * 70}{Colores.RESET}\n")

    # ═══════════════════════════════════════════════════════════════════════════
    # MÉTODO PRINCIPAL DE EJECUCIÓN
    # ═══════════════════════════════════════════════════════════════════════════

    def ejecutar_configuracion_completa(self, instalar_faltantes: bool = True) -> ResultadoConfiguracion:
        """
        Ejecuta el proceso completo de auto-configuración.

        Args:
            instalar_faltantes: Si True, intenta instalar dependencias faltantes

        Returns:
            ResultadoConfiguracion con toda la información recopilada
        """
        inicio = time.time()
        self.resultado.timestamp = datetime.now().isoformat()

        if self.verbose:
            print(f"{Colores.CYAN}{self.LOGO}{Colores.RESET}")
            time.sleep(0.3)

        self._print("Iniciando auto-configuración del sistema...", "titulo")

        # Agregar directorio al path
        if str(self.base_dir) not in sys.path:
            sys.path.insert(0, str(self.base_dir))

        try:
            # 1. Recopilar información del sistema
            self._print("FASE 1: Recopilación de información del sistema", "titulo")
            self.recopilar_info_cpu()
            self.recopilar_info_memoria()
            self.recopilar_info_disco()
            self.recopilar_info_so()

            # 2. Verificar red y conectividad
            self._print("FASE 2: Análisis de red y conectividad", "titulo")
            self.recopilar_info_red()

            # 3. Verificar entorno Python
            self._print("FASE 3: Verificación del entorno Python", "titulo")
            self.recopilar_info_python()

            # 4. Instalar dependencias faltantes si se solicita
            if instalar_faltantes and self.resultado.python.paquetes_faltantes:
                self._print("FASE 3.5: Instalación de dependencias", "titulo")
                self.instalar_dependencias_faltantes()

            # 5. Verificar proyecto
            self._print("FASE 4: Análisis del proyecto SAC", "titulo")
            self.recopilar_info_proyecto()

            # 6. Calcular configuración óptima
            self._print("FASE 5: Cálculo de configuración óptima", "titulo")
            self.calcular_configuracion_optima()

            # 7. Aplicar optimizaciones
            self._print("FASE 6: Aplicación de optimizaciones", "titulo")
            self.aplicar_optimizaciones()

            # 8. Determinar estado general
            if self.resultado.errores:
                self.resultado.estado_general = EstadoComponente.ERROR
            elif self.resultado.advertencias:
                self.resultado.estado_general = EstadoComponente.WARNING
            else:
                self.resultado.estado_general = EstadoComponente.OK

            # 9. Generar reporte
            self.generar_reporte_json()

        except Exception as e:
            self._print(f"Error durante la configuración: {e}", "error")
            self.resultado.errores.append(f"Error crítico: {str(e)}")
            self.resultado.estado_general = EstadoComponente.ERROR
            self.logger.exception("Error durante auto-configuración")

        # Registrar duración
        self.resultado.duracion_segundos = time.time() - inicio

        # Mostrar resumen
        if self.verbose:
            self.mostrar_resumen()

        self.logger.info(
            f"Auto-configuración completada: {self.resultado.estado_general.value} "
            f"en {self.resultado.duracion_segundos:.2f}s"
        )

        return self.resultado

    def obtener_configuracion_para_aplicacion(self) -> Dict[str, Any]:
        """
        Retorna un diccionario con la configuración lista para usar en la aplicación.

        Returns:
            Dict con parámetros de configuración
        """
        config = self.resultado.configuracion_optima

        return {
            # Configuración de base de datos
            'db': {
                'pool_size': config.pool_conexiones_db,
                'timeout': config.timeout_queries_seg,
                'retry_count': config.reintentos_conexion,
            },
            # Configuración de procesamiento
            'processing': {
                'workers': config.workers_procesamiento,
                'batch_size': config.batch_size_registros,
                'buffer_mb': config.buffer_memoria_mb,
            },
            # Configuración de monitoreo
            'monitoring': {
                'interval_seconds': config.intervalo_monitoreo_seg,
                'cache_enabled': config.cache_habilitado,
                'compress_logs': config.compresion_logs,
            },
            # Información del sistema
            'system': {
                'level': config.nivel_optimizacion.value,
                'cpu_cores': self.resultado.cpu.nucleos_logicos,
                'ram_available_gb': self.resultado.memoria.disponible_gb,
                'internet_connected': self.resultado.red.conectividad_internet,
            },
            # Estado
            'status': {
                'ok': self.resultado.estado_general == EstadoComponente.OK,
                'warnings': len(self.resultado.advertencias),
                'errors': len(self.resultado.errores),
            }
        }


# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIÓN DE CONVENIENCIA PARA USO RÁPIDO
# ═══════════════════════════════════════════════════════════════════════════════

def ejecutar_auto_configuracion(
    base_dir: Path = None,
    verbose: bool = True,
    instalar_faltantes: bool = True
) -> Tuple[ResultadoConfiguracion, Dict[str, Any]]:
    """
    Función de conveniencia para ejecutar la auto-configuración.

    Args:
        base_dir: Directorio base del proyecto
        verbose: Mostrar mensajes en consola
        instalar_faltantes: Instalar dependencias faltantes

    Returns:
        Tupla (ResultadoConfiguracion, Dict con config para aplicación)
    """
    configurador = AutoConfigurador(base_dir=base_dir, verbose=verbose)
    resultado = configurador.ejecutar_configuracion_completa(instalar_faltantes)
    config_app = configurador.obtener_configuracion_para_aplicacion()

    return resultado, config_app


# ═══════════════════════════════════════════════════════════════════════════════
# EXPORTAR CLASES Y FUNCIONES
# ═══════════════════════════════════════════════════════════════════════════════

__all__ = [
    'AutoConfigurador',
    'ejecutar_auto_configuracion',
    'ResultadoConfiguracion',
    'ConfiguracionOptima',
    'NivelOptimizacion',
    'EstadoComponente',
    'InfoCPU',
    'InfoMemoria',
    'InfoDisco',
    'InfoSistemaOperativo',
    'InfoRed',
    'InfoPython',
    'InfoProyecto',
    'VERSION',
]


# ═══════════════════════════════════════════════════════════════════════════════
# EJECUCIÓN DIRECTA
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description='Módulo de Auto-Configuración del Sistema SAC',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Ejecutar sin mensajes en consola')
    parser.add_argument('--no-install', action='store_true',
                       help='No instalar dependencias faltantes')
    parser.add_argument('--json', action='store_true',
                       help='Mostrar resultado en formato JSON')

    args = parser.parse_args()

    resultado, config = ejecutar_auto_configuracion(
        verbose=not args.quiet,
        instalar_faltantes=not args.no_install
    )

    if args.json:
        print(json.dumps(config, indent=2, ensure_ascii=False))

    sys.exit(0 if resultado.estado_general == EstadoComponente.OK else 1)
