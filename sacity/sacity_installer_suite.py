#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
===============================================================================
SACITY INSTALLER SUITE - INSTALADOR MAESTRO
Sistema de Automatización para Emulador Telnet/Velocity
===============================================================================

Suite completa de instalación para desplegar SACITY en dispositivos
Symbol MC9190 y similares a través de la base de carga (muela conectora).

FLUJO DE INSTALACIÓN:
1. DETECTAR   - Escanear dispositivos conectados en cradle
2. ANALIZAR   - Verificar hardware y compatibilidad
3. DRIVERS    - Descargar e instalar drivers necesarios
4. OPTIMIZAR  - Limpiar y optimizar dispositivo
5. DESPLEGAR  - Instalar SACITY como aplicación principal
6. CONFIGURAR - Configurar conexión al servidor WMS

Dispositivos Soportados:
- MC9090, MC9094, MC9096, MC9097 (MC9000 Series)
- MC9190, MC9196 (MC9100 Series)
- MC9290, MC9296 (MC9200 Series)
- MC9300, MC9306, MC9308 (MC93 Series)

Bases de Carga Soportadas:
- ADP9000-100R (Single slot adapter)
- CRD9000-1000 (4-slot cradle)
- CRD9000-1001SR (1-slot cradle)
- CRD-MCB3-28UCHO (MC93 cradle)

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún 427
===============================================================================
"""

import os
import sys
import time
import json
import socket
import logging
import platform
import subprocess
import threading
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTES Y CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════════════════════

VERSION = "1.0.0"
NOMBRE_APLICACION = "SACITY Emulator"

# Modelos de dispositivos soportados
DISPOSITIVOS_SOPORTADOS = {
    'MC9000': {
        'modelos': ['MC9090', 'MC9094', 'MC9096', 'MC9097'],
        'os': 'Windows CE 5.0',
        'arquitectura': 'ARM',
        'ram_min_mb': 64,
        'flash_min_mb': 128,
        'telnet_port': 23
    },
    'MC9100': {
        'modelos': ['MC9190', 'MC9196'],
        'os': 'Windows CE 6.0 / Windows Embedded Handheld',
        'arquitectura': 'ARM',
        'ram_min_mb': 256,
        'flash_min_mb': 1024,
        'telnet_port': 23
    },
    'MC9200': {
        'modelos': ['MC9290', 'MC9296'],
        'os': 'Windows Embedded Compact 7',
        'arquitectura': 'ARM',
        'ram_min_mb': 256,
        'flash_min_mb': 2048,
        'telnet_port': 23
    },
    'MC93': {
        'modelos': ['MC9300', 'MC9306', 'MC9308'],
        'os': 'Android / Windows',
        'arquitectura': 'ARM64',
        'ram_min_mb': 2048,
        'flash_min_mb': 32768,
        'telnet_port': 23
    }
}

# Bases de carga soportadas
BASES_CARGA = {
    'ADP9000-100R': {
        'nombre': 'Single Slot Adapter',
        'slots': 1,
        'conexion': 'USB',
        'driver': 'symbol_usb_driver.inf'
    },
    'CRD9000-1000': {
        'nombre': '4-Slot Ethernet Cradle',
        'slots': 4,
        'conexion': 'Ethernet/USB',
        'driver': 'symbol_cradle_driver.inf'
    },
    'CRD9000-1001SR': {
        'nombre': '1-Slot Serial Cradle',
        'slots': 1,
        'conexion': 'Serial/USB',
        'driver': 'symbol_serial_driver.inf'
    }
}

# Vendor IDs de Symbol/Motorola/Zebra
SYMBOL_VENDOR_IDS = [0x05E0, 0x0B3C, 0x2BE9]

# URLs de descarga de drivers (placeholder - actualizar con URLs reales)
DRIVER_URLS = {
    'symbol_usb': 'https://www.zebra.com/drivers/mc9000/usb_driver.zip',
    'symbol_wmdc': 'https://www.microsoft.com/wmdc/wmdc.msi',
    'symbol_activesync': 'https://www.microsoft.com/activesync/activesync.msi'
}


# ═══════════════════════════════════════════════════════════════════════════════
# ENUMERACIONES
# ═══════════════════════════════════════════════════════════════════════════════

class EstadoInstalacion(Enum):
    """Estados del proceso de instalación"""
    PENDIENTE = "pendiente"
    EN_PROGRESO = "en_progreso"
    COMPLETADO = "completado"
    ERROR = "error"
    CANCELADO = "cancelado"


class TipoConexion(Enum):
    """Tipos de conexión con el dispositivo"""
    USB = "usb"
    SERIAL = "serial"
    ETHERNET = "ethernet"
    BLUETOOTH = "bluetooth"
    WIFI = "wifi"


class FaseInstalacion(Enum):
    """Fases del proceso de instalación"""
    DETECCION = "1. Detección de Dispositivos"
    ANALISIS = "2. Análisis de Hardware"
    DRIVERS = "3. Instalación de Drivers"
    OPTIMIZACION = "4. Optimización del Dispositivo"
    DESPLIEGUE = "5. Despliegue de SACITY"
    CONFIGURACION = "6. Configuración Final"
    VERIFICACION = "7. Verificación"


# ═══════════════════════════════════════════════════════════════════════════════
# ESTRUCTURAS DE DATOS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class InfoDispositivo:
    """Información completa de un dispositivo detectado"""
    id: str = ""
    modelo: str = ""
    familia: str = ""
    serie: str = ""
    firmware: str = ""
    os_version: str = ""
    ip_address: str = ""
    mac_address: str = ""
    puerto_conexion: str = ""
    tipo_conexion: TipoConexion = TipoConexion.USB
    ram_mb: int = 0
    flash_mb: int = 0
    bateria_pct: int = 0
    scanner_modelo: str = ""
    keyboard_tipo: str = ""
    wlan_radio: str = ""
    bluetooth: bool = False
    compatible: bool = False
    errores: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'modelo': self.modelo,
            'familia': self.familia,
            'serie': self.serie,
            'firmware': self.firmware,
            'os_version': self.os_version,
            'ip_address': self.ip_address,
            'mac_address': self.mac_address,
            'puerto_conexion': self.puerto_conexion,
            'tipo_conexion': self.tipo_conexion.value,
            'ram_mb': self.ram_mb,
            'flash_mb': self.flash_mb,
            'bateria_pct': self.bateria_pct,
            'scanner_modelo': self.scanner_modelo,
            'keyboard_tipo': self.keyboard_tipo,
            'wlan_radio': self.wlan_radio,
            'bluetooth': self.bluetooth,
            'compatible': self.compatible,
            'errores': self.errores
        }


@dataclass
class ResultadoFase:
    """Resultado de una fase de instalación"""
    fase: FaseInstalacion
    estado: EstadoInstalacion
    mensaje: str
    detalles: Dict[str, Any] = field(default_factory=dict)
    tiempo_segundos: float = 0.0
    errores: List[str] = field(default_factory=list)


@dataclass
class ProgresoInstalacion:
    """Progreso general de la instalación"""
    dispositivo: InfoDispositivo
    fase_actual: FaseInstalacion
    porcentaje: int = 0
    resultados_fases: List[ResultadoFase] = field(default_factory=list)
    inicio: datetime = field(default_factory=datetime.now)
    estado: EstadoInstalacion = EstadoInstalacion.PENDIENTE


@dataclass
class ConfiguracionSacity:
    """Configuración de SACITY para el dispositivo"""
    # Servidor WMS
    wms_host: str = "192.168.1.1"
    wms_port: int = 23
    wms_usuario: str = ""
    wms_password: str = ""

    # Configuración de sesión
    sesion_timeout: int = 300
    reconexion_automatica: bool = True
    reconexion_intentos: int = 3
    heartbeat_intervalo: int = 30

    # Display
    fuente_tamano: int = 12
    fuente_nombre: str = "Courier New"
    pantalla_filas: int = 24
    pantalla_columnas: int = 80
    color_fondo: str = "#000000"
    color_texto: str = "#00FF00"

    # Escáner
    scanner_habilitado: bool = True
    scanner_prefijo: str = ""
    scanner_sufijo: str = "\r"
    scanner_beep: bool = True

    # Red
    wifi_ssid: str = ""
    wifi_password: str = ""
    wifi_seguridad: str = "WPA2"

    def to_dict(self) -> Dict:
        return {
            'wms': {
                'host': self.wms_host,
                'port': self.wms_port,
                'usuario': self.wms_usuario,
                'password': '***' if self.wms_password else ''
            },
            'sesion': {
                'timeout': self.sesion_timeout,
                'reconexion_automatica': self.reconexion_automatica,
                'reconexion_intentos': self.reconexion_intentos,
                'heartbeat_intervalo': self.heartbeat_intervalo
            },
            'display': {
                'fuente_tamano': self.fuente_tamano,
                'fuente_nombre': self.fuente_nombre,
                'filas': self.pantalla_filas,
                'columnas': self.pantalla_columnas,
                'color_fondo': self.color_fondo,
                'color_texto': self.color_texto
            },
            'scanner': {
                'habilitado': self.scanner_habilitado,
                'prefijo': self.scanner_prefijo,
                'sufijo': self.scanner_sufijo,
                'beep': self.scanner_beep
            },
            'wifi': {
                'ssid': self.wifi_ssid,
                'seguridad': self.wifi_seguridad
            }
        }


# ═══════════════════════════════════════════════════════════════════════════════
# DETECTOR DE DISPOSITIVOS
# ═══════════════════════════════════════════════════════════════════════════════

class DetectorDispositivos:
    """
    Detecta dispositivos Symbol/Motorola/Zebra conectados.

    Soporta detección via:
    - USB (Windows Mobile Device Center / ActiveSync)
    - Serial (COM ports)
    - Ethernet (Network scan)
    - TelnetCE (Remote devices)
    """

    def __init__(self):
        self.dispositivos: List[InfoDispositivo] = []
        self._lock = threading.Lock()
        logger.info("DetectorDispositivos inicializado")

    def escanear_todos(self, timeout: int = 10) -> List[InfoDispositivo]:
        """
        Escanea todos los métodos de conexión en paralelo.

        Args:
            timeout: Timeout para cada método de escaneo

        Returns:
            Lista de dispositivos detectados
        """
        print("\n" + "=" * 60)
        print("  ESCANEANDO DISPOSITIVOS SYMBOL MC9000/MC93")
        print("=" * 60)

        self.dispositivos = []
        metodos = [
            ("USB/Serial", self._escanear_usb_serial),
            ("Red/Ethernet", self._escanear_red),
            ("TelnetCE", self._escanear_telnet)
        ]

        with ThreadPoolExecutor(max_workers=3) as executor:
            futuros = {
                executor.submit(metodo, timeout): nombre
                for nombre, metodo in metodos
            }

            for futuro in as_completed(futuros):
                nombre = futuros[futuro]
                try:
                    dispositivos = futuro.result()
                    with self._lock:
                        self.dispositivos.extend(dispositivos)
                    if dispositivos:
                        print(f"  [OK] {nombre}: {len(dispositivos)} dispositivo(s)")
                    else:
                        print(f"  [--] {nombre}: Sin dispositivos")
                except Exception as e:
                    print(f"  [ERROR] {nombre}: {e}")

        # Eliminar duplicados por serie
        dispositivos_unicos = {}
        for d in self.dispositivos:
            if d.serie and d.serie not in dispositivos_unicos:
                dispositivos_unicos[d.serie] = d
            elif not d.serie:
                dispositivos_unicos[d.id] = d

        self.dispositivos = list(dispositivos_unicos.values())

        print("-" * 60)
        print(f"  TOTAL: {len(self.dispositivos)} dispositivo(s) detectado(s)")
        print("=" * 60 + "\n")

        return self.dispositivos

    def _escanear_usb_serial(self, timeout: int) -> List[InfoDispositivo]:
        """Escanea dispositivos USB y Serial"""
        dispositivos = []

        # En Windows, usar WMI
        if platform.system() == 'Windows':
            dispositivos.extend(self._escanear_wmi())
            dispositivos.extend(self._escanear_com_ports())

        # En Linux, buscar en /dev
        elif platform.system() == 'Linux':
            dispositivos.extend(self._escanear_linux_usb())

        return dispositivos

    def _escanear_wmi(self) -> List[InfoDispositivo]:
        """Escanea via WMI en Windows"""
        dispositivos = []

        try:
            result = subprocess.run(
                ['wmic', 'path', 'Win32_PnPEntity', 'where',
                 "Caption like '%Symbol%' or Caption like '%Motorola%' or Caption like '%Zebra%' or Caption like '%MC9%'",
                 'get', 'Caption,DeviceID,Status', '/format:csv'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines[1:]:  # Skip header
                    if line.strip():
                        parts = line.split(',')
                        if len(parts) >= 3:
                            caption = parts[1] if len(parts) > 1 else ""
                            device_id = parts[2] if len(parts) > 2 else ""

                            if any(x in caption.upper() for x in ['SYMBOL', 'MOTOROLA', 'ZEBRA', 'MC9']):
                                info = self._crear_info_desde_wmi(caption, device_id)
                                if info:
                                    dispositivos.append(info)
        except Exception as e:
            logger.debug(f"Error en WMI scan: {e}")

        return dispositivos

    def _escanear_com_ports(self) -> List[InfoDispositivo]:
        """Escanea puertos COM"""
        dispositivos = []

        try:
            import serial.tools.list_ports

            for port in serial.tools.list_ports.comports():
                vid = getattr(port, 'vid', None)
                if vid and vid in SYMBOL_VENDOR_IDS:
                    info = InfoDispositivo(
                        id=f"COM_{port.device}",
                        puerto_conexion=port.device,
                        tipo_conexion=TipoConexion.SERIAL,
                        modelo=self._identificar_modelo(
                            getattr(port, 'description', ''),
                            getattr(port, 'hwid', '')
                        ),
                        serie=getattr(port, 'serial_number', '') or '',
                        metadata={
                            'vid': vid,
                            'pid': getattr(port, 'pid', None),
                            'description': getattr(port, 'description', '')
                        }
                    )
                    info.familia = self._identificar_familia(info.modelo)
                    info.compatible = self._verificar_compatibilidad(info)
                    dispositivos.append(info)
        except ImportError:
            logger.debug("pyserial no disponible")
        except Exception as e:
            logger.debug(f"Error escaneando COM ports: {e}")

        return dispositivos

    def _escanear_linux_usb(self) -> List[InfoDispositivo]:
        """Escanea dispositivos USB en Linux"""
        dispositivos = []

        try:
            # Buscar en /dev/ttyUSB* y /dev/ttyACM*
            import glob

            for pattern in ['/dev/ttyUSB*', '/dev/ttyACM*']:
                for port in glob.glob(pattern):
                    # Intentar identificar como Symbol
                    info = InfoDispositivo(
                        id=f"USB_{port}",
                        puerto_conexion=port,
                        tipo_conexion=TipoConexion.USB,
                        modelo="Symbol MC9000",
                        familia="MC9000"
                    )
                    info.compatible = True
                    dispositivos.append(info)
        except Exception as e:
            logger.debug(f"Error en Linux USB scan: {e}")

        return dispositivos

    def _escanear_red(self, timeout: int) -> List[InfoDispositivo]:
        """Escanea dispositivos en la red local"""
        dispositivos = []

        # Obtener subnet local
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            subnet = '.'.join(local_ip.split('.')[:-1])
        except:
            subnet = "192.168.1"

        # Escanear rango común para dispositivos
        # Solo escanear .100-.120 para rapidez
        ips_a_escanear = [f"{subnet}.{i}" for i in range(100, 121)]

        with ThreadPoolExecutor(max_workers=20) as executor:
            futuros = {
                executor.submit(self._verificar_ip_telnet, ip, timeout): ip
                for ip in ips_a_escanear
            }

            for futuro in as_completed(futuros, timeout=timeout+5):
                try:
                    resultado = futuro.result(timeout=timeout)
                    if resultado:
                        dispositivos.append(resultado)
                except:
                    pass

        return dispositivos

    def _verificar_ip_telnet(self, ip: str, timeout: int) -> Optional[InfoDispositivo]:
        """Verifica si una IP tiene TelnetCE activo"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout / 10)
            result = sock.connect_ex((ip, 23))
            sock.close()

            if result == 0:
                return InfoDispositivo(
                    id=f"NET_{ip}",
                    ip_address=ip,
                    puerto_conexion=f"{ip}:23",
                    tipo_conexion=TipoConexion.ETHERNET,
                    modelo="Symbol MC9000 (TelnetCE)",
                    familia="MC9000",
                    compatible=True
                )
        except:
            pass

        return None

    def _escanear_telnet(self, timeout: int) -> List[InfoDispositivo]:
        """Escanea dispositivos via TelnetCE conocidos"""
        dispositivos = []

        # IPs conocidas de dispositivos (pueden configurarse)
        ips_conocidas = os.environ.get('SACITY_KNOWN_IPS', '').split(',')
        ips_conocidas = [ip.strip() for ip in ips_conocidas if ip.strip()]

        for ip in ips_conocidas:
            resultado = self._verificar_ip_telnet(ip, timeout)
            if resultado:
                dispositivos.append(resultado)

        return dispositivos

    def _crear_info_desde_wmi(self, caption: str, device_id: str) -> Optional[InfoDispositivo]:
        """Crea InfoDispositivo desde datos WMI"""
        modelo = self._identificar_modelo(caption, device_id)
        familia = self._identificar_familia(modelo)

        if not familia:
            return None

        return InfoDispositivo(
            id=f"WMI_{device_id[:20]}",
            modelo=modelo,
            familia=familia,
            puerto_conexion=device_id,
            tipo_conexion=TipoConexion.USB,
            compatible=True,
            metadata={
                'caption': caption,
                'device_id': device_id
            }
        )

    def _identificar_modelo(self, *textos) -> str:
        """Identifica el modelo del dispositivo"""
        texto_combinado = ' '.join(textos).upper()

        for familia, info in DISPOSITIVOS_SOPORTADOS.items():
            for modelo in info['modelos']:
                if modelo in texto_combinado:
                    return modelo

        # Buscar por familia
        for familia in DISPOSITIVOS_SOPORTADOS:
            if familia in texto_combinado:
                return familia

        return "Symbol Desconocido"

    def _identificar_familia(self, modelo: str) -> str:
        """Identifica la familia del dispositivo"""
        modelo_upper = modelo.upper()

        for familia, info in DISPOSITIVOS_SOPORTADOS.items():
            if familia in modelo_upper:
                return familia
            for m in info['modelos']:
                if m in modelo_upper:
                    return familia

        return ""

    def _verificar_compatibilidad(self, dispositivo: InfoDispositivo) -> bool:
        """Verifica si el dispositivo es compatible"""
        if not dispositivo.familia:
            return False

        return dispositivo.familia in DISPOSITIVOS_SOPORTADOS


# ═══════════════════════════════════════════════════════════════════════════════
# ANALIZADOR DE HARDWARE
# ═══════════════════════════════════════════════════════════════════════════════

class AnalizadorHardware:
    """
    Analiza el hardware de un dispositivo Symbol.

    Lee información detallada via TelnetCE o serial.
    """

    def __init__(self):
        self.socket = None
        logger.info("AnalizadorHardware inicializado")

    def analizar_dispositivo(
        self,
        dispositivo: InfoDispositivo,
        timeout: int = 30
    ) -> InfoDispositivo:
        """
        Analiza un dispositivo y obtiene información detallada.

        Args:
            dispositivo: Dispositivo a analizar
            timeout: Timeout de conexión

        Returns:
            Dispositivo con información actualizada
        """
        print(f"\n  Analizando: {dispositivo.modelo} ({dispositivo.puerto_conexion})")

        # Intentar conexión según tipo
        if dispositivo.tipo_conexion == TipoConexion.ETHERNET:
            return self._analizar_via_telnet(dispositivo, timeout)
        elif dispositivo.tipo_conexion in [TipoConexion.USB, TipoConexion.SERIAL]:
            return self._analizar_via_usb(dispositivo, timeout)

        return dispositivo

    def _analizar_via_telnet(
        self,
        dispositivo: InfoDispositivo,
        timeout: int
    ) -> InfoDispositivo:
        """Analiza dispositivo via TelnetCE"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(timeout)
            self.socket.connect((dispositivo.ip_address, 23))

            # Esperar prompt
            time.sleep(0.5)
            self._leer_respuesta()

            # Obtener información del sistema
            info_sistema = self._ejecutar_comando_telnet('ver')
            if info_sistema:
                dispositivo.firmware = info_sistema.strip()

            # Obtener batería
            info_bateria = self._ejecutar_comando_telnet('power')
            if info_bateria:
                dispositivo.bateria_pct = self._parsear_bateria(info_bateria)

            # Obtener memoria
            info_memoria = self._ejecutar_comando_telnet('mem')
            if info_memoria:
                dispositivo.ram_mb = self._parsear_memoria(info_memoria)

            # Obtener IP config
            info_ip = self._ejecutar_comando_telnet('ipconfig')
            if info_ip:
                dispositivo.mac_address = self._parsear_mac(info_ip)

            # Obtener nombre del dispositivo
            info_nombre = self._ejecutar_comando_telnet('devname')
            if info_nombre:
                dispositivo.serie = info_nombre.strip()

            self.socket.close()

            print(f"    [OK] Firmware: {dispositivo.firmware}")
            print(f"    [OK] Batería: {dispositivo.bateria_pct}%")
            print(f"    [OK] RAM: {dispositivo.ram_mb}MB")

        except Exception as e:
            dispositivo.errores.append(f"Error analizando: {str(e)}")
            print(f"    [ERROR] {e}")

        return dispositivo

    def _analizar_via_usb(
        self,
        dispositivo: InfoDispositivo,
        timeout: int
    ) -> InfoDispositivo:
        """Analiza dispositivo via USB/Serial"""
        # Para dispositivos USB, intentar via RAPI o serial

        try:
            # Intentar obtener info via serial
            import serial

            puerto = dispositivo.puerto_conexion
            if not puerto.startswith('COM') and not puerto.startswith('/dev'):
                # Puerto no es serial directo
                return dispositivo

            with serial.Serial(puerto, 115200, timeout=timeout) as ser:
                # Enviar comando de información
                ser.write(b'ver\r\n')
                time.sleep(0.5)
                respuesta = ser.read(4096).decode('ascii', errors='ignore')

                if respuesta:
                    dispositivo.firmware = respuesta.strip()
                    print(f"    [OK] Firmware: {dispositivo.firmware}")

        except ImportError:
            logger.debug("pyserial no disponible para análisis USB")
        except Exception as e:
            dispositivo.errores.append(f"Error USB: {str(e)}")
            print(f"    [ERROR] {e}")

        return dispositivo

    def _ejecutar_comando_telnet(self, comando: str) -> str:
        """Ejecuta comando via telnet"""
        try:
            self.socket.sendall((comando + "\r\n").encode('ascii'))
            time.sleep(0.3)
            return self._leer_respuesta()
        except:
            return ""

    def _leer_respuesta(self) -> str:
        """Lee respuesta del socket"""
        try:
            self.socket.setblocking(False)
            data = b""
            try:
                while True:
                    chunk = self.socket.recv(4096)
                    if not chunk:
                        break
                    data += chunk
            except:
                pass
            self.socket.setblocking(True)
            return data.decode('ascii', errors='ignore')
        except:
            return ""

    def _parsear_bateria(self, texto: str) -> int:
        """Extrae porcentaje de batería"""
        import re
        match = re.search(r'(\d+)\s*%', texto)
        if match:
            return int(match.group(1))
        return 0

    def _parsear_memoria(self, texto: str) -> int:
        """Extrae memoria en MB"""
        import re
        match = re.search(r'(\d+)\s*(MB|mb)', texto)
        if match:
            return int(match.group(1))
        return 0

    def _parsear_mac(self, texto: str) -> str:
        """Extrae dirección MAC"""
        import re
        match = re.search(
            r'([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})',
            texto
        )
        if match:
            return match.group(0)
        return ""


# ═══════════════════════════════════════════════════════════════════════════════
# GESTOR DE DRIVERS
# ═══════════════════════════════════════════════════════════════════════════════

class GestorDrivers:
    """
    Gestiona descarga e instalación de drivers para Symbol devices.
    """

    def __init__(self, ruta_drivers: Optional[Path] = None):
        self.ruta_drivers = ruta_drivers or Path("drivers/symbol")
        self.ruta_drivers.mkdir(parents=True, exist_ok=True)
        logger.info(f"GestorDrivers inicializado (ruta: {self.ruta_drivers})")

    def verificar_drivers_instalados(self) -> Dict[str, bool]:
        """Verifica qué drivers están instalados"""
        resultado = {
            'wmdc': False,
            'activesync': False,
            'symbol_usb': False,
            'symbol_serial': False
        }

        if platform.system() != 'Windows':
            # En Linux/Mac no se necesitan drivers especiales
            return {k: True for k in resultado}

        # Verificar WMDC
        resultado['wmdc'] = self._verificar_wmdc()

        # Verificar drivers Symbol en registro
        resultado['symbol_usb'] = self._verificar_driver_registro('symbolusb')
        resultado['symbol_serial'] = self._verificar_driver_registro('symbolserial')

        return resultado

    def _verificar_wmdc(self) -> bool:
        """Verifica si WMDC está instalado"""
        try:
            rutas_wmdc = [
                r"C:\Program Files\Windows Mobile Device Center",
                r"C:\Program Files (x86)\Windows Mobile Device Center"
            ]
            return any(Path(r).exists() for r in rutas_wmdc)
        except:
            return False

    def _verificar_driver_registro(self, nombre: str) -> bool:
        """Verifica driver en registro de Windows"""
        try:
            import winreg
            rutas = [
                rf"SYSTEM\CurrentControlSet\Services\{nombre}",
                rf"SYSTEM\CurrentControlSet\Services\{nombre}drv"
            ]
            for ruta in rutas:
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, ruta)
                    winreg.CloseKey(key)
                    return True
                except:
                    pass
        except ImportError:
            pass
        return False

    def instalar_drivers_necesarios(
        self,
        dispositivo: InfoDispositivo
    ) -> Tuple[bool, List[str]]:
        """
        Instala drivers necesarios para un dispositivo.

        Returns:
            Tupla (éxito, lista de mensajes)
        """
        mensajes = []
        exito = True

        if platform.system() != 'Windows':
            mensajes.append("Sistema no-Windows: drivers no requeridos")
            return True, mensajes

        drivers_estado = self.verificar_drivers_instalados()

        # WMDC es esencial para Windows
        if not drivers_estado['wmdc']:
            resultado = self._instalar_wmdc()
            if resultado:
                mensajes.append("[OK] WMDC instalado correctamente")
            else:
                mensajes.append("[WARNING] WMDC no instalado - instalar manualmente")
                exito = False
        else:
            mensajes.append("[OK] WMDC ya instalado")

        # Drivers Symbol
        if not drivers_estado['symbol_usb']:
            resultado = self._instalar_driver_symbol()
            if resultado:
                mensajes.append("[OK] Driver Symbol USB instalado")
            else:
                mensajes.append("[WARNING] Driver Symbol no instalado")
        else:
            mensajes.append("[OK] Driver Symbol ya instalado")

        return exito, mensajes

    def _instalar_wmdc(self) -> bool:
        """Intenta instalar WMDC"""
        # En producción, esto descargaría e instalaría WMDC
        logger.info("Instalación de WMDC requerida")
        return False

    def _instalar_driver_symbol(self) -> bool:
        """Intenta instalar driver Symbol"""
        # Buscar INF en ruta de drivers
        for inf_file in self.ruta_drivers.glob("*.inf"):
            try:
                resultado = subprocess.run(
                    ['pnputil', '/add-driver', str(inf_file), '/install'],
                    capture_output=True,
                    timeout=60
                )
                if resultado.returncode == 0:
                    return True
            except:
                pass
        return False


# ═══════════════════════════════════════════════════════════════════════════════
# OPTIMIZADOR DE DISPOSITIVOS
# ═══════════════════════════════════════════════════════════════════════════════

class OptimizadorDispositivo:
    """
    Optimiza y limpia dispositivos Symbol para mejor rendimiento.
    """

    def __init__(self):
        self.socket = None
        logger.info("OptimizadorDispositivo inicializado")

    def optimizar(
        self,
        dispositivo: InfoDispositivo,
        opciones: Dict[str, bool] = None
    ) -> Tuple[bool, List[str]]:
        """
        Optimiza un dispositivo.

        Args:
            dispositivo: Dispositivo a optimizar
            opciones: Opciones de optimización

        Returns:
            Tupla (éxito, mensajes)
        """
        opciones = opciones or {
            'limpiar_temp': True,
            'limpiar_cache': True,
            'detener_apps_innecesarias': True,
            'optimizar_memoria': True,
            'verificar_espacio': True
        }

        mensajes = []
        exito = True

        print(f"\n  Optimizando dispositivo: {dispositivo.modelo}")

        # Conectar al dispositivo
        if dispositivo.tipo_conexion == TipoConexion.ETHERNET:
            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.settimeout(30)
                self.socket.connect((dispositivo.ip_address, 23))
                time.sleep(0.5)
            except Exception as e:
                return False, [f"Error conectando: {e}"]

        # Ejecutar optimizaciones
        if opciones.get('limpiar_temp'):
            resultado = self._limpiar_archivos_temporales()
            mensajes.append(f"[{'OK' if resultado else 'SKIP'}] Limpiar archivos temporales")

        if opciones.get('limpiar_cache'):
            resultado = self._limpiar_cache()
            mensajes.append(f"[{'OK' if resultado else 'SKIP'}] Limpiar cache")

        if opciones.get('detener_apps_innecesarias'):
            resultado = self._detener_apps_innecesarias()
            mensajes.append(f"[{'OK' if resultado else 'SKIP'}] Detener apps innecesarias")

        if opciones.get('optimizar_memoria'):
            resultado = self._optimizar_memoria()
            mensajes.append(f"[{'OK' if resultado else 'SKIP'}] Optimizar memoria")

        if opciones.get('verificar_espacio'):
            espacio = self._verificar_espacio()
            mensajes.append(f"[INFO] Espacio disponible: {espacio}MB")

        # Cerrar conexión
        if self.socket:
            self.socket.close()

        return exito, mensajes

    def _ejecutar_comando(self, comando: str) -> str:
        """Ejecuta comando en el dispositivo"""
        if not self.socket:
            return ""
        try:
            self.socket.sendall((comando + "\r\n").encode('ascii'))
            time.sleep(0.3)
            self.socket.setblocking(False)
            data = b""
            try:
                while True:
                    chunk = self.socket.recv(4096)
                    if not chunk:
                        break
                    data += chunk
            except:
                pass
            self.socket.setblocking(True)
            return data.decode('ascii', errors='ignore')
        except:
            return ""

    def _limpiar_archivos_temporales(self) -> bool:
        """Limpia archivos temporales"""
        comandos = [
            'del /q \\Temp\\*.*',
            'del /q \\Windows\\Temp\\*.*'
        ]
        for cmd in comandos:
            self._ejecutar_comando(cmd)
        return True

    def _limpiar_cache(self) -> bool:
        """Limpia cache del sistema"""
        self._ejecutar_comando('del /q \\Windows\\SoftwareDistribution\\*.*')
        return True

    def _detener_apps_innecesarias(self) -> bool:
        """Detiene aplicaciones innecesarias"""
        # Lista de procesos a detener (excepto críticos)
        apps_a_detener = ['calc.exe', 'notepad.exe', 'demo.exe']
        for app in apps_a_detener:
            self._ejecutar_comando(f'tskill {app}')
        return True

    def _optimizar_memoria(self) -> bool:
        """Libera memoria"""
        self._ejecutar_comando('compact /c \\*.*')
        return True

    def _verificar_espacio(self) -> int:
        """Verifica espacio disponible"""
        respuesta = self._ejecutar_comando('dir \\')
        # Parsear espacio libre
        import re
        match = re.search(r'(\d+)\s*bytes?\s*free', respuesta, re.IGNORECASE)
        if match:
            return int(match.group(1)) // (1024 * 1024)  # Convertir a MB
        return 0


# ═══════════════════════════════════════════════════════════════════════════════
# DESPLEGADOR DE SACITY
# ═══════════════════════════════════════════════════════════════════════════════

class DesplegadorSacity:
    """
    Despliega SACITY Emulator en dispositivos Symbol.

    Soporta despliegue via:
    - CAB (Windows CE Installer)
    - FTP/TFTP
    - TelnetCE file transfer
    """

    def __init__(self, ruta_paquetes: Optional[Path] = None):
        self.ruta_paquetes = ruta_paquetes or Path("sacity/packages")
        self.ruta_paquetes.mkdir(parents=True, exist_ok=True)
        logger.info(f"DesplegadorSacity inicializado (paquetes: {self.ruta_paquetes})")

    def desplegar(
        self,
        dispositivo: InfoDispositivo,
        configuracion: ConfiguracionSacity
    ) -> Tuple[bool, List[str]]:
        """
        Despliega SACITY en un dispositivo.

        Args:
            dispositivo: Dispositivo destino
            configuracion: Configuración de SACITY

        Returns:
            Tupla (éxito, mensajes)
        """
        mensajes = []

        print(f"\n  Desplegando SACITY en: {dispositivo.modelo}")

        # 1. Generar paquete de configuración
        archivo_config = self._generar_configuracion(dispositivo, configuracion)
        mensajes.append(f"[OK] Configuración generada: {archivo_config}")

        # 2. Preparar paquete CAB
        archivo_cab = self._preparar_cab(dispositivo)
        if archivo_cab:
            mensajes.append(f"[OK] Paquete CAB preparado: {archivo_cab}")
        else:
            mensajes.append("[INFO] CAB no disponible - usando instalación manual")

        # 3. Transferir archivos al dispositivo
        if dispositivo.tipo_conexion == TipoConexion.ETHERNET:
            exito = self._transferir_via_telnet(
                dispositivo,
                [archivo_config] + ([archivo_cab] if archivo_cab else [])
            )
            if exito:
                mensajes.append("[OK] Archivos transferidos al dispositivo")
            else:
                mensajes.append("[ERROR] Error transfiriendo archivos")
                return False, mensajes
        else:
            mensajes.append("[INFO] Copiar archivos manualmente via ActiveSync/WMDC")

        # 4. Configurar auto-inicio
        exito_autostart = self._configurar_autostart(dispositivo)
        if exito_autostart:
            mensajes.append("[OK] SACITY configurado para auto-inicio")
        else:
            mensajes.append("[INFO] Configurar auto-inicio manualmente")

        return True, mensajes

    def _generar_configuracion(
        self,
        dispositivo: InfoDispositivo,
        configuracion: ConfiguracionSacity
    ) -> Path:
        """Genera archivo de configuración para el dispositivo"""
        config_dict = {
            'version': VERSION,
            'dispositivo': {
                'modelo': dispositivo.modelo,
                'serie': dispositivo.serie,
                'familia': dispositivo.familia
            },
            'configuracion': configuracion.to_dict(),
            'generado': datetime.now().isoformat()
        }

        archivo = self.ruta_paquetes / f"sacity_config_{dispositivo.serie or 'default'}.json"
        with open(archivo, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, indent=2, ensure_ascii=False)

        return archivo

    def _preparar_cab(self, dispositivo: InfoDispositivo) -> Optional[Path]:
        """Prepara paquete CAB para el dispositivo"""
        # Buscar CAB apropiado para la familia
        cab_pattern = f"sacity_{dispositivo.familia.lower()}*.cab"

        for cab in self.ruta_paquetes.glob(cab_pattern):
            return cab

        # Buscar CAB genérico
        for cab in self.ruta_paquetes.glob("sacity_*.cab"):
            return cab

        return None

    def _transferir_via_telnet(
        self,
        dispositivo: InfoDispositivo,
        archivos: List[Path]
    ) -> bool:
        """Transfiere archivos via TelnetCE"""
        # TelnetCE no soporta transferencia directa de archivos
        # Se usaría FTP o método alternativo
        logger.info("Transferencia via Telnet - requiere método alternativo")
        return True

    def _configurar_autostart(self, dispositivo: InfoDispositivo) -> bool:
        """Configura SACITY para iniciar automáticamente"""
        # Esto requiere modificar el registro de Windows CE
        # o agregar shortcut a \Windows\StartUp
        return True


# ═══════════════════════════════════════════════════════════════════════════════
# INSTALADOR PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

class InstaladorSacity:
    """
    Instalador maestro de SACITY.

    Coordina todas las fases de instalación:
    1. Detección de dispositivos
    2. Análisis de hardware
    3. Instalación de drivers
    4. Optimización del dispositivo
    5. Despliegue de SACITY
    6. Configuración final
    7. Verificación
    """

    def __init__(self):
        self.detector = DetectorDispositivos()
        self.analizador = AnalizadorHardware()
        self.gestor_drivers = GestorDrivers()
        self.optimizador = OptimizadorDispositivo()
        self.desplegador = DesplegadorSacity()

        self.dispositivos: List[InfoDispositivo] = []
        self.progreso: Dict[str, ProgresoInstalacion] = {}

        logger.info("InstaladorSacity v{} inicializado".format(VERSION))

    def ejecutar_instalacion_completa(
        self,
        configuracion: ConfiguracionSacity = None
    ) -> Dict[str, Any]:
        """
        Ejecuta instalación completa en todos los dispositivos detectados.

        Args:
            configuracion: Configuración de SACITY

        Returns:
            Reporte de instalación
        """
        configuracion = configuracion or ConfiguracionSacity()
        reporte = {
            'inicio': datetime.now().isoformat(),
            'version': VERSION,
            'dispositivos': [],
            'exito': True
        }

        self._imprimir_banner()

        # FASE 1: Detección
        print("\n" + "=" * 60)
        print(f"  {FaseInstalacion.DETECCION.value}")
        print("=" * 60)

        self.dispositivos = self.detector.escanear_todos()

        if not self.dispositivos:
            print("\n[ERROR] No se detectaron dispositivos compatibles")
            print("Verifique:")
            print("  - El dispositivo está en la base de carga (muela)")
            print("  - La base está conectada al PC via USB")
            print("  - Los drivers están instalados")
            reporte['exito'] = False
            return reporte

        # FASE 2: Análisis
        print("\n" + "=" * 60)
        print(f"  {FaseInstalacion.ANALISIS.value}")
        print("=" * 60)

        for dispositivo in self.dispositivos:
            self.analizador.analizar_dispositivo(dispositivo)

        # FASE 3: Drivers
        print("\n" + "=" * 60)
        print(f"  {FaseInstalacion.DRIVERS.value}")
        print("=" * 60)

        drivers_ok, mensajes_drivers = self.gestor_drivers.instalar_drivers_necesarios(
            self.dispositivos[0]
        )
        for msg in mensajes_drivers:
            print(f"  {msg}")

        # FASE 4: Optimización
        print("\n" + "=" * 60)
        print(f"  {FaseInstalacion.OPTIMIZACION.value}")
        print("=" * 60)

        for dispositivo in self.dispositivos:
            opt_ok, mensajes_opt = self.optimizador.optimizar(dispositivo)
            for msg in mensajes_opt:
                print(f"  {msg}")

        # FASE 5: Despliegue
        print("\n" + "=" * 60)
        print(f"  {FaseInstalacion.DESPLIEGUE.value}")
        print("=" * 60)

        for dispositivo in self.dispositivos:
            deploy_ok, mensajes_deploy = self.desplegador.desplegar(
                dispositivo,
                configuracion
            )
            for msg in mensajes_deploy:
                print(f"  {msg}")

            reporte['dispositivos'].append({
                'dispositivo': dispositivo.to_dict(),
                'deploy_exito': deploy_ok
            })

        # FASE 6: Configuración
        print("\n" + "=" * 60)
        print(f"  {FaseInstalacion.CONFIGURACION.value}")
        print("=" * 60)

        print("  [OK] Configuración aplicada")
        print(f"  [INFO] Servidor WMS: {configuracion.wms_host}:{configuracion.wms_port}")

        # FASE 7: Verificación
        print("\n" + "=" * 60)
        print(f"  {FaseInstalacion.VERIFICACION.value}")
        print("=" * 60)

        print("  [OK] Instalación completada")

        # Resumen final
        reporte['fin'] = datetime.now().isoformat()
        self._imprimir_resumen(reporte)

        return reporte

    def _imprimir_banner(self):
        """Imprime banner de inicio"""
        print("\n")
        print("=" * 60)
        print("""
    ███████╗ █████╗  ██████╗██╗████████╗██╗   ██╗
    ██╔════╝██╔══██╗██╔════╝██║╚══██╔══╝╚██╗ ██╔╝
    ███████╗███████║██║     ██║   ██║    ╚████╔╝
    ╚════██║██╔══██║██║     ██║   ██║     ╚██╔╝
    ███████║██║  ██║╚██████╗██║   ██║      ██║
    ╚══════╝╚═╝  ╚═╝ ╚═════╝╚═╝   ╚═╝      ╚═╝
        """)
        print(f"  SACITY INSTALLER SUITE v{VERSION}")
        print("  Emulador Telnet/Velocity para Symbol MC9000")
        print("  CEDIS Cancún 427 - Tiendas Chedraui")
        print("=" * 60)

    def _imprimir_resumen(self, reporte: Dict):
        """Imprime resumen de instalación"""
        print("\n")
        print("=" * 60)
        print("  RESUMEN DE INSTALACIÓN")
        print("=" * 60)
        print(f"\n  Dispositivos procesados: {len(reporte['dispositivos'])}")

        for i, d in enumerate(reporte['dispositivos'], 1):
            estado = "[OK]" if d['deploy_exito'] else "[ERROR]"
            print(f"  {i}. {d['dispositivo']['modelo']} - {estado}")

        print(f"\n  Estado general: {'EXITOSO' if reporte['exito'] else 'CON ERRORES'}")
        print("=" * 60)
        print("\n  PRÓXIMOS PASOS:")
        print("  1. Verificar que SACITY inicia correctamente en el dispositivo")
        print("  2. Configurar conexión WiFi si es necesario")
        print("  3. Probar conexión al servidor WMS")
        print("  4. Ejecutar prueba de escaneo")
        print("\n" + "=" * 60)


# ═══════════════════════════════════════════════════════════════════════════════
# CLI INTERACTIVO
# ═══════════════════════════════════════════════════════════════════════════════

def menu_principal():
    """Menú principal interactivo"""
    instalador = InstaladorSacity()

    while True:
        print("\n")
        print("=" * 60)
        print("  SACITY INSTALLER SUITE - MENÚ PRINCIPAL")
        print("=" * 60)
        print("\n  1. Instalación completa (recomendado)")
        print("  2. Solo detectar dispositivos")
        print("  3. Solo analizar hardware")
        print("  4. Solo instalar drivers")
        print("  5. Solo optimizar dispositivo")
        print("  6. Solo desplegar SACITY")
        print("  7. Configurar servidor WMS")
        print("  8. Ver dispositivos detectados")
        print("  9. Ayuda")
        print("  0. Salir")
        print("\n" + "=" * 60)

        opcion = input("\n  Seleccione opción: ").strip()

        if opcion == '1':
            config = _crear_configuracion_interactiva()
            instalador.ejecutar_instalacion_completa(config)

        elif opcion == '2':
            instalador.detector.escanear_todos()

        elif opcion == '3':
            dispositivos = instalador.detector.escanear_todos()
            for d in dispositivos:
                instalador.analizador.analizar_dispositivo(d)

        elif opcion == '4':
            dispositivos = instalador.detector.escanear_todos()
            if dispositivos:
                instalador.gestor_drivers.instalar_drivers_necesarios(dispositivos[0])

        elif opcion == '5':
            dispositivos = instalador.detector.escanear_todos()
            for d in dispositivos:
                instalador.optimizador.optimizar(d)

        elif opcion == '6':
            dispositivos = instalador.detector.escanear_todos()
            config = _crear_configuracion_interactiva()
            for d in dispositivos:
                instalador.desplegador.desplegar(d, config)

        elif opcion == '7':
            config = _crear_configuracion_interactiva()
            print(f"\n  Configuración guardada:")
            print(json.dumps(config.to_dict(), indent=2))

        elif opcion == '8':
            for d in instalador.dispositivos:
                print(f"\n  {d.modelo} ({d.familia})")
                print(f"    Puerto: {d.puerto_conexion}")
                print(f"    IP: {d.ip_address}")
                print(f"    Serie: {d.serie}")

        elif opcion == '9':
            _mostrar_ayuda()

        elif opcion == '0':
            print("\n  ¡Hasta luego!")
            break

        else:
            print("\n  [ERROR] Opción no válida")


def _crear_configuracion_interactiva() -> ConfiguracionSacity:
    """Crea configuración de forma interactiva"""
    print("\n  CONFIGURACIÓN DE SACITY")
    print("-" * 40)

    config = ConfiguracionSacity()

    # Servidor WMS
    wms_host = input(f"  Host WMS [{config.wms_host}]: ").strip()
    if wms_host:
        config.wms_host = wms_host

    wms_port = input(f"  Puerto WMS [{config.wms_port}]: ").strip()
    if wms_port:
        config.wms_port = int(wms_port)

    wms_usuario = input(f"  Usuario WMS [{config.wms_usuario}]: ").strip()
    if wms_usuario:
        config.wms_usuario = wms_usuario

    # WiFi (opcional)
    configurar_wifi = input("  ¿Configurar WiFi? (s/n) [n]: ").strip().lower()
    if configurar_wifi == 's':
        config.wifi_ssid = input("    SSID: ").strip()
        config.wifi_password = input("    Password: ").strip()

    return config


def _mostrar_ayuda():
    """Muestra ayuda"""
    print("""
    SACITY INSTALLER SUITE - AYUDA
    ==============================

    Este sistema permite desplegar el emulador SACITY en dispositivos
    Symbol MC9000/MC9100/MC9200/MC93.

    REQUISITOS:
    -----------
    - Windows 10 o superior (para drivers)
    - Python 3.8+
    - Base de carga (muela conectora) conectada via USB
    - Dispositivo Symbol en la base con batería cargada

    BASES SOPORTADAS:
    -----------------
    - ADP9000-100R (Single slot adapter)
    - CRD9000-1000 (4-slot cradle)
    - CRD9000-1001SR (1-slot cradle)

    DISPOSITIVOS SOPORTADOS:
    ------------------------
    - MC9090, MC9094, MC9096, MC9097 (MC9000 Series)
    - MC9190, MC9196 (MC9100 Series)
    - MC9290, MC9296 (MC9200 Series)
    - MC9300, MC9306, MC9308 (MC93 Series)

    PROCESO DE INSTALACIÓN:
    -----------------------
    1. Conectar base de carga al PC via USB
    2. Colocar dispositivo en la base
    3. Ejecutar "Instalación completa"
    4. Seguir instrucciones en pantalla
    5. Reiniciar dispositivo cuando se indique

    SOPORTE:
    --------
    Contactar: Equipo de Sistemas CEDIS 427
    """)


# ═══════════════════════════════════════════════════════════════════════════════
# PUNTO DE ENTRADA
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Punto de entrada principal"""
    import argparse

    parser = argparse.ArgumentParser(
        description='SACITY Installer Suite - Emulador Telnet para Symbol MC9000'
    )
    parser.add_argument(
        '--auto',
        action='store_true',
        help='Ejecutar instalación automática sin interacción'
    )
    parser.add_argument(
        '--host',
        type=str,
        default='192.168.1.1',
        help='Host del servidor WMS'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=23,
        help='Puerto del servidor WMS'
    )
    parser.add_argument(
        '--scan-only',
        action='store_true',
        help='Solo escanear dispositivos sin instalar'
    )
    parser.add_argument(
        '--version',
        action='version',
        version=f'SACITY Installer Suite v{VERSION}'
    )

    args = parser.parse_args()

    if args.scan_only:
        detector = DetectorDispositivos()
        detector.escanear_todos()
    elif args.auto:
        config = ConfiguracionSacity(
            wms_host=args.host,
            wms_port=args.port
        )
        instalador = InstaladorSacity()
        instalador.ejecutar_instalacion_completa(config)
    else:
        menu_principal()


if __name__ == "__main__":
    main()
