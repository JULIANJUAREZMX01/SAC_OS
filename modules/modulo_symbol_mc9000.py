#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
===============================================================================
MODULO DE GESTION DE DISPOSITIVOS SYMBOL MC9000/MC93
Sistema de Automatizacion de Consultas - CEDIS Cancun 427
===============================================================================

Este modulo proporciona capacidades completas para gestionar dispositivos
Symbol MC9000 y MC93 series (Motorola/Zebra) incluyendo:

- Deteccion automatica de dispositivos conectados via USB/Serial
- Comunicacion via TelnetCE para control remoto
- Gestion de drivers para bases de carga CRD9000
- Monitoreo de salud del dispositivo (bateria, almacenamiento, red)
- Integracion con asistente IA para comandos en lenguaje natural
- Despliegue remoto de aplicaciones

Dispositivos Soportados:
- MC9000 Series: MC9090, MC9094, MC9096, MC9097
- MC9100 Series: MC9190, MC9196
- MC9200 Series: MC9290, MC9296
- MC93 Series: MC9300, MC9306, MC9308

Bases de Carga Soportadas:
- CRD9000-1000 (4-slot cradle)
- CRD9000-1001SR (1-slot cradle)
- CRD-MCB3-28UCHO (MC93 cradle)

Uso:
    from modules.modulo_symbol_mc9000 import (
        GestorDispositivosSymbol,
        SymbolTelnetCE,
        crear_gestor_symbol
    )

    gestor = crear_gestor_symbol()
    dispositivos = gestor.detectar_dispositivos()

    # Conectar via Telnet
    if gestor.conectar_telnet("192.168.1.100"):
        info = gestor.obtener_info_dispositivo()
        print(info)

Desarrollado por: Julian Alexander Juarez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logistica Cancun 427

Version: 1.0.0
Ultima actualizacion: Noviembre 2025
===============================================================================
"""

import os
import sys
import platform
import subprocess
import socket
import logging
import time
import threading
import json
import re
import smtplib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# Configurar logging
logger = logging.getLogger(__name__)

# ===============================================================================
# CONSTANTES Y CONFIGURACION
# ===============================================================================

# Vendor IDs de Symbol/Motorola/Zebra
SYMBOL_VENDOR_IDS = [0x05E0, 0x0B3C, 0x2BE9]

# Modelos conocidos por familia
MODELOS_CONOCIDOS = {
    'MC9000': ['MC9090', 'MC9094', 'MC9096', 'MC9097'],
    'MC9100': ['MC9190', 'MC9196'],
    'MC9200': ['MC9290', 'MC9296'],
    'MC93': ['MC9300', 'MC9306', 'MC9308']
}

# Bases de carga soportadas
BASES_CARGA = {
    'CRD9000-1000': {
        'descripcion': 'Base de 4 slots MC9000',
        'slots': 4,
        'tipo': 'USB/Serial'
    },
    'CRD9000-1001SR': {
        'descripcion': 'Base de 1 slot MC9000',
        'slots': 1,
        'tipo': 'USB'
    },
    'CRD-MCB3-28UCHO': {
        'descripcion': 'Base de carga MC93',
        'slots': 4,
        'tipo': 'USB'
    }
}

# Comandos TelnetCE disponibles
COMANDOS_TELNETCE = {
    'info_dispositivo': 'devinfo',
    'nombre_dispositivo': 'devname',
    'config_ip': 'ipconfig',
    'bateria': 'power',
    'almacenamiento': 'dir',
    'procesos': 'ps',
    'reiniciar': 'reboot',
    'apagar': 'shutdown',
    'wlan': 'wlanconfig',
    'escanear': 'scan',
    'fecha_hora': 'date',
    'memoria': 'mem',
    'version': 'ver'
}

# Configuración de Email
@dataclass
class ConfiguracionEmail:
    """Configuración SMTP para alertas y respuestas"""
    host_smtp: str = "smtp.office365.com"
    puerto_smtp: int = 587
    usuario: str = ""
    contraseña: str = ""
    remitente_email: str = ""
    remitente_nombre: str = "SAC - CEDIS 427 (SACITY)"
    destinatarios_alertas: List[str] = field(default_factory=list)
    usar_tls: bool = True
    timeout_smtp: int = 10

# Colores para terminal
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


# ===============================================================================
# ENUMERACIONES
# ===============================================================================

class EstadoDispositivo(Enum):
    """Estados posibles de un dispositivo Symbol"""
    CONECTADO = "conectado"
    DESCONECTADO = "desconectado"
    CARGANDO = "cargando"
    EN_USO = "en_uso"
    ERROR = "error"
    DESCONOCIDO = "desconocido"


class TipoConexion(Enum):
    """Tipos de conexion soportados"""
    USB = "usb"
    SERIAL = "serial"
    TELNET = "telnet"
    ACTIVESYNC = "activesync"


class NivelBateria(Enum):
    """Niveles de bateria del dispositivo"""
    CRITICO = "critico"      # < 15%
    BAJO = "bajo"            # 15-30%
    MEDIO = "medio"          # 30-60%
    ALTO = "alto"            # 60-90%
    COMPLETO = "completo"    # > 90%


class SeveridadAlerta(Enum):
    """Niveles de severidad para alertas"""
    CRITICO = "CRITICO"
    ALTO = "ALTO"
    MEDIO = "MEDIO"
    BAJO = "BAJO"
    INFO = "INFO"


# ===============================================================================
# ESTRUCTURAS DE DATOS
# ===============================================================================

@dataclass
class InfoDispositivo:
    """Informacion completa de un dispositivo Symbol"""
    modelo: str = ""
    serie: str = ""
    firmware: str = ""
    familia: str = ""
    puerto: str = ""
    tipo_conexion: TipoConexion = TipoConexion.USB
    estado: EstadoDispositivo = EstadoDispositivo.DESCONOCIDO
    ip_address: str = ""
    mac_address: str = ""
    bateria_porcentaje: int = 0
    nivel_bateria: NivelBateria = NivelBateria.MEDIO
    almacenamiento_libre_mb: float = 0.0
    almacenamiento_total_mb: float = 0.0
    ultimo_contacto: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convertir a diccionario"""
        return {
            'modelo': self.modelo,
            'serie': self.serie,
            'firmware': self.firmware,
            'familia': self.familia,
            'puerto': self.puerto,
            'tipo_conexion': self.tipo_conexion.value,
            'estado': self.estado.value,
            'ip_address': self.ip_address,
            'mac_address': self.mac_address,
            'bateria_porcentaje': self.bateria_porcentaje,
            'nivel_bateria': self.nivel_bateria.value,
            'almacenamiento_libre_mb': self.almacenamiento_libre_mb,
            'almacenamiento_total_mb': self.almacenamiento_total_mb,
            'ultimo_contacto': self.ultimo_contacto.isoformat() if self.ultimo_contacto else None,
            'metadata': self.metadata
        }


@dataclass
class ResultadoComando:
    """Resultado de ejecutar un comando en el dispositivo"""
    comando: str
    exito: bool
    respuesta: str
    tiempo_ejecucion_ms: float
    timestamp: datetime = field(default_factory=datetime.now)
    errores: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            'comando': self.comando,
            'exito': self.exito,
            'respuesta': self.respuesta,
            'tiempo_ejecucion_ms': self.tiempo_ejecucion_ms,
            'timestamp': self.timestamp.isoformat(),
            'errores': self.errores
        }


@dataclass
class AlertaDispositivo:
    """Alerta generada por un dispositivo"""
    dispositivo_serie: str
    tipo: str
    severidad: SeveridadAlerta
    mensaje: str
    detalles: str
    solucion: str
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        return {
            'dispositivo_serie': self.dispositivo_serie,
            'tipo': self.tipo,
            'severidad': self.severidad.value,
            'mensaje': self.mensaje,
            'detalles': self.detalles,
            'solucion': self.solucion,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class ReporteHealthCheck:
    """Reporte de salud de un dispositivo"""
    dispositivo: InfoDispositivo
    verificaciones: Dict[str, bool] = field(default_factory=dict)
    alertas: List[AlertaDispositivo] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    estado_general: str = "OK"

    def to_dict(self) -> Dict:
        return {
            'dispositivo': self.dispositivo.to_dict(),
            'verificaciones': self.verificaciones,
            'alertas': [a.to_dict() for a in self.alertas],
            'timestamp': self.timestamp.isoformat(),
            'estado_general': self.estado_general
        }


# ===============================================================================
# DETECTOR DE DISPOSITIVOS
# ===============================================================================

class DetectorDispositivosSymbol:
    """
    Detecta dispositivos Symbol conectados via USB/Serial.

    Soporta deteccion automatica de:
    - MC9000, MC9100, MC9200, MC93 series
    - Bases de carga CRD9000
    """

    def __init__(self):
        self.vendor_ids = SYMBOL_VENDOR_IDS
        self.modelos_conocidos = MODELOS_CONOCIDOS
        self._dispositivos_cache: List[InfoDispositivo] = []
        self._ultima_deteccion: Optional[datetime] = None
        logger.info("DetectorDispositivosSymbol inicializado")

    def detectar_dispositivos_usb(self) -> List[InfoDispositivo]:
        """
        Detecta dispositivos Symbol conectados via USB.

        Returns:
            Lista de dispositivos detectados
        """
        dispositivos = []

        try:
            # Intentar usar pyserial para detectar puertos COM
            try:
                import serial.tools.list_ports
                ports = list(serial.tools.list_ports.comports())

                for port in ports:
                    vid = getattr(port, 'vid', None)
                    if vid and vid in self.vendor_ids:
                        info = self._crear_info_dispositivo_desde_puerto(port)
                        dispositivos.append(info)
                        logger.info(f"Dispositivo Symbol detectado en {port.device}")

            except ImportError:
                logger.warning("pyserial no disponible, usando deteccion alternativa")
                dispositivos = self._detectar_alternativo()

        except Exception as e:
            logger.error(f"Error detectando dispositivos USB: {e}")

        # En Windows, intentar detectar via registro/WMI
        if platform.system() == 'Windows':
            dispositivos.extend(self._detectar_windows())

        self._dispositivos_cache = dispositivos
        self._ultima_deteccion = datetime.now()

        return dispositivos

    def _crear_info_dispositivo_desde_puerto(self, port) -> InfoDispositivo:
        """Crea InfoDispositivo desde informacion del puerto serial"""
        modelo = self._identificar_modelo(
            getattr(port, 'description', ''),
            getattr(port, 'hwid', '')
        )

        familia = self._identificar_familia(modelo)

        return InfoDispositivo(
            modelo=modelo,
            puerto=port.device,
            tipo_conexion=TipoConexion.USB,
            estado=EstadoDispositivo.CONECTADO,
            serie=self._extraer_serie(getattr(port, 'serial_number', '')),
            metadata={
                'vendor_id': getattr(port, 'vid', None),
                'product_id': getattr(port, 'pid', None),
                'description': getattr(port, 'description', ''),
                'hwid': getattr(port, 'hwid', '')
            },
            familia=familia,
            ultimo_contacto=datetime.now()
        )

    def _identificar_modelo(self, descripcion: str, hwid: str) -> str:
        """Identifica el modelo especifico del dispositivo"""
        texto = f"{descripcion} {hwid}".upper()

        for familia, modelos in self.modelos_conocidos.items():
            for modelo in modelos:
                if modelo in texto:
                    return modelo

        # Intentar identificar por familia
        for familia in self.modelos_conocidos:
            if familia in texto:
                return familia

        return "Symbol Desconocido"

    def _identificar_familia(self, modelo: str) -> str:
        """Identifica la familia del dispositivo"""
        for familia, modelos in self.modelos_conocidos.items():
            if modelo in modelos or modelo == familia:
                return familia
        return "Desconocida"

    def _extraer_serie(self, serial_str: str) -> str:
        """Extrae y formatea el numero de serie"""
        if not serial_str:
            return f"SN-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        return serial_str

    def _detectar_alternativo(self) -> List[InfoDispositivo]:
        """Metodo alternativo de deteccion sin pyserial"""
        dispositivos = []

        if platform.system() == 'Linux':
            # Buscar en /dev/ttyUSB* y /dev/ttyACM*
            for pattern in ['/dev/ttyUSB*', '/dev/ttyACM*']:
                try:
                    import glob
                    for port in glob.glob(pattern):
                        # Verificar si es un dispositivo Symbol
                        info = InfoDispositivo(
                            modelo="Symbol Desconocido",
                            puerto=port,
                            tipo_conexion=TipoConexion.SERIAL,
                            estado=EstadoDispositivo.CONECTADO,
                            familia="Desconocida",
                            ultimo_contacto=datetime.now()
                        )
                        dispositivos.append(info)
                except Exception as e:
                    logger.debug(f"Error buscando puertos: {e}")

        return dispositivos

    def _detectar_windows(self) -> List[InfoDispositivo]:
        """Deteccion especifica para Windows usando WMI/registro"""
        dispositivos = []

        try:
            # Intentar usar WMI
            import subprocess
            result = subprocess.run(
                ['wmic', 'path', 'Win32_PnPEntity', 'where',
                 "Caption like '%Symbol%' or Caption like '%Motorola%' or Caption like '%Zebra%'",
                 'get', 'Caption,DeviceID,Status', '/format:list'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                # Parsear resultado
                current_device = {}
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    if '=' in line:
                        key, value = line.split('=', 1)
                        current_device[key] = value
                    elif current_device:
                        # Fin de dispositivo
                        if current_device.get('Caption'):
                            info = InfoDispositivo(
                                modelo=self._identificar_modelo(
                                    current_device.get('Caption', ''),
                                    current_device.get('DeviceID', '')
                                ),
                                puerto=current_device.get('DeviceID', ''),
                                tipo_conexion=TipoConexion.USB,
                                estado=EstadoDispositivo.CONECTADO
                                    if current_device.get('Status') == 'OK'
                                    else EstadoDispositivo.ERROR,
                                familia=self._identificar_familia(
                                    current_device.get('Caption', '')
                                ),
                                ultimo_contacto=datetime.now()
                            )
                            dispositivos.append(info)
                        current_device = {}

        except Exception as e:
            logger.debug(f"Error en deteccion Windows: {e}")

        return dispositivos

    def obtener_dispositivos_en_cache(self) -> List[InfoDispositivo]:
        """Retorna dispositivos de la ultima deteccion"""
        return self._dispositivos_cache


# ===============================================================================
# COMUNICACION TELNETCE
# ===============================================================================

class SymbolTelnetCE:
    """
    Maneja comunicacion TelnetCE con dispositivos Symbol.

    TelnetCE es un servidor telnet ligero para Windows CE/Mobile
    que permite control remoto de dispositivos Symbol.
    """

    def __init__(
        self,
        host: str = '192.168.1.1',
        port: int = 23,
        timeout: int = 10,
        usuario: str = 'admin',
        password: str = '',
        familia_dispositivo: str = 'MC9200',
        config_email: Optional[ConfiguracionEmail] = None
    ):
        self.host = host
        self.port = port
        # Optimizar timeout por familia de dispositivo
        TIMEOUTS_OPTIMOS = {
            'MC9000': 10,
            'MC9100': 20,
            'MC9200': 25,
            'MC93': 12
        }
        self.timeout = TIMEOUTS_OPTIMOS.get(familia_dispositivo, timeout)
        self.usuario = usuario
        self.password = password
        self.familia_dispositivo = familia_dispositivo
        self.conexion = None
        self._conectado = False
        self._lock = threading.Lock()
        self._heartbeat_activo = False
        self._heartbeat_thread = None
        self._config_email = config_email or ConfiguracionEmail()
        logger.info(f"✅ SymbolTelnetCE inicializado para {host}:{port} (familia: {familia_dispositivo}, timeout: {self.timeout}s)")

    def conectar(self, max_reintentos: int = 3) -> bool:
        """
        Establece conexion TelnetCE con el dispositivo.

        Args:
            max_reintentos: Número máximo de intentos de reconexión

        Returns:
            True si la conexion fue exitosa
        """
        try:
            import telnetlib

            for intento in range(max_reintentos):
                try:
                    with self._lock:
                        self.conexion = telnetlib.Telnet(
                            self.host,
                            self.port,
                            self.timeout
                        )

                        # Esperar prompt de login si hay
                        if self.usuario:
                            try:
                                self.conexion.read_until(b"Login:", self.timeout)
                                self.conexion.write(self.usuario.encode('ascii') + b"\r\n")
                            except EOFError:
                                logger.warning(f"⚠️ Sin respuesta esperada para login en {self.host}")

                        if self.password:
                            try:
                                self.conexion.read_until(b"Password:", self.timeout)
                                self.conexion.write(self.password.encode('ascii') + b"\r\n")
                            except EOFError:
                                logger.warning(f"⚠️ Sin respuesta esperada para password en {self.host}")

                        # Esperar prompt de comando
                        try:
                            self.conexion.read_until(b">", self.timeout)
                        except EOFError:
                            logger.warning(f"⚠️ Sin respuesta esperada para prompt en {self.host}")

                        self._conectado = True
                        logger.info(f"✅ Conectado a {self.host}:{self.port}")
                        return True

                except (socket.timeout, socket.error, ConnectionRefusedError) as e:
                    intento_num = intento + 1
                    if intento_num < max_reintentos:
                        # Exponential backoff: 2^intento segundos
                        espera = 2 ** intento
                        logger.warning(
                            f"⚠️ Intento {intento_num}/{max_reintentos} falló: {e}. "
                            f"Reintentando en {espera}s..."
                        )
                        time.sleep(espera)
                    else:
                        logger.error(
                            f"❌ No se pudo conectar tras {max_reintentos} intentos a {self.host}:{self.port}"
                        )
                        self._conectado = False
                        return False
                except EOFError:
                    logger.warning(f"⚠️ Conexión cerrada por dispositivo (intento {intento + 1})")
                    if intento + 1 < max_reintentos:
                        time.sleep(2 ** intento)
                    else:
                        self._conectado = False
                        return False

        except ImportError:
            logger.error("❌ telnetlib no disponible")
            return False
        except Exception as e:
            logger.exception(f"❌ Error conectando via Telnet: {e}")
            self._conectado = False
            return False

    def desconectar(self):
        """Cierra la conexion Telnet y detiene heartbeat"""
        try:
            # Detener heartbeat primero
            self.detener_heartbeat()

            with self._lock:
                if self.conexion:
                    self.conexion.close()
                    self.conexion = None
                self._conectado = False
                logger.info("✅ Desconectado de Telnet")
        except Exception as e:
            logger.error(f"❌ Error desconectando: {e}")

    def ejecutar_comando(
        self,
        comando: str,
        tiempo_espera: float = 2.0,
        usar_polling: bool = True
    ) -> ResultadoComando:
        """
        Ejecuta un comando en el dispositivo via Telnet.

        FASE 3 OPTIMIZATION: Usa polling eficiente en lugar de sleep bloqueante.

        Args:
            comando: Comando a ejecutar
            tiempo_espera: Tiempo máximo a esperar respuesta en segundos
            usar_polling: Si True, usa polling eficiente; si False, usa sleep tradicional

        Returns:
            ResultadoComando con la respuesta
        """
        inicio = time.time()

        if not self._conectado or not self.conexion:
            return ResultadoComando(
                comando=comando,
                exito=False,
                respuesta="",
                tiempo_ejecucion_ms=0,
                errores=["No conectado al dispositivo"]
            )

        try:
            with self._lock:
                # Enviar comando
                self.conexion.write(comando.encode('ascii') + b"\r\n")

                # Esperar respuesta: POLLING EFICIENTE en lugar de sleep bloqueante
                if usar_polling:
                    respuesta = self._esperar_respuesta_con_polling(tiempo_espera)
                else:
                    # Fallback: sleep tradicional (menos eficiente)
                    time.sleep(tiempo_espera)
                    respuesta_raw = self.conexion.read_very_eager()
                    respuesta = respuesta_raw.decode('ascii', errors='ignore')

                # Limpiar respuesta
                respuesta_limpia = self._limpiar_respuesta(respuesta, comando)

                # Validar que device no reportó error
                if self._detectar_error_en_respuesta(respuesta_limpia):
                    tiempo_ms = (time.time() - inicio) * 1000
                    return ResultadoComando(
                        comando=comando,
                        exito=False,
                        respuesta=respuesta_limpia,
                        tiempo_ejecucion_ms=tiempo_ms,
                        errores=["Dispositivo reportó error en respuesta"]
                    )

                tiempo_ms = (time.time() - inicio) * 1000

                return ResultadoComando(
                    comando=comando,
                    exito=True,
                    respuesta=respuesta_limpia,
                    tiempo_ejecucion_ms=tiempo_ms
                )

        except socket.timeout:
            tiempo_ms = (time.time() - inicio) * 1000
            return ResultadoComando(
                comando=comando,
                exito=False,
                respuesta="",
                tiempo_ejecucion_ms=tiempo_ms,
                errores=["Timeout esperando respuesta del dispositivo"]
            )
        except Exception as e:
            tiempo_ms = (time.time() - inicio) * 1000
            logger.exception(f"Error ejecutando comando: {e}")
            return ResultadoComando(
                comando=comando,
                exito=False,
                respuesta="",
                tiempo_ejecucion_ms=tiempo_ms,
                errores=[f"{type(e).__name__}: {str(e)}"]
            )

    def _esperar_respuesta_con_polling(self, timeout: float) -> str:
        """
        Espera respuesta usando polling eficiente (no sleep bloqueante).

        FASE 3: Optimization para bajo consumo de CPU en legacy devices.
        - Polls cada 10-50ms en lugar de sleep 2 segundos
        - Detecta prompt '>' para respuesta completa
        - Compatible con devices lentos (MC9200 8+ años)
        """
        inicio = time.time()
        buffer = b""
        poll_delay = 0.01  # 10ms - muy eficiente

        while time.time() - inicio < timeout:
            try:
                dato = self.conexion.read_very_eager()
                if dato:
                    buffer += dato
                    # Prompt encontrado = respuesta completa
                    if b'>' in buffer:
                        break
                    # Si ya tenemos datos, reducir espera entre polls
                    poll_delay = 0.01
            except socket.timeout:
                pass  # Timeout esperado, continuar
            except Exception:
                pass

            # Sleep mínimo para no saturar CPU
            time.sleep(poll_delay)

        return buffer.decode('ascii', errors='ignore')

    def _detectar_error_en_respuesta(self, respuesta: str) -> bool:
        """
        Detecta si el dispositivo reportó un error en la respuesta.

        Palabras clave de error típicas en TelnetCE.
        """
        if not respuesta:
            return False

        respuesta_lower = respuesta.lower()
        keywords_error = [
            'error',
            'no encontrado',
            'inválido',
            'no autorizado',
            'comando no reconocido',
            'access denied',
            'bad parameter'
        ]

        return any(keyword in respuesta_lower for keyword in keywords_error)

    def _limpiar_respuesta(self, respuesta: str, comando: str) -> str:
        """Limpia la respuesta telnet de eco y prompts"""
        lineas = respuesta.split('\r\n')
        lineas_limpias = [
            linea for linea in lineas
            if linea.strip() and
               comando not in linea and
               '>' not in linea
        ]
        return '\n'.join(lineas_limpias)

    def obtener_info_dispositivo(self) -> Dict[str, str]:
        """
        Obtiene informacion completa del dispositivo.

        Returns:
            Diccionario con toda la informacion disponible
        """
        info = {}

        comandos_info = {
            'nombre': 'devname',
            'version': 'ver',
            'config_ip': 'ipconfig',
            'bateria': 'power',
            'almacenamiento': 'dir \\',
            'fecha_hora': 'date',
            'memoria': 'mem'
        }

        for clave, comando in comandos_info.items():
            resultado = self.ejecutar_comando(comando)
            if resultado.exito:
                info[clave] = resultado.respuesta
            else:
                info[clave] = f"Error: {', '.join(resultado.errores)}"

        return info

    def obtener_estado_bateria(self) -> Tuple[int, NivelBateria]:
        """
        Obtiene estado de la bateria.

        Returns:
            Tupla (porcentaje, nivel)
        """
        resultado = self.ejecutar_comando('power')

        if not resultado.exito:
            return 0, NivelBateria.CRITICO

        # Parsear respuesta
        porcentaje = 50  # Default
        try:
            # Buscar patron como "Battery: 75%"
            match = re.search(r'(\d+)\s*%', resultado.respuesta)
            if match:
                porcentaje = int(match.group(1))
        except Exception as e:
            logger.debug(f"Error parseando bateria: {e}")

        # Determinar nivel
        if porcentaje < 15:
            nivel = NivelBateria.CRITICO
        elif porcentaje < 30:
            nivel = NivelBateria.BAJO
        elif porcentaje < 60:
            nivel = NivelBateria.MEDIO
        elif porcentaje < 90:
            nivel = NivelBateria.ALTO
        else:
            nivel = NivelBateria.COMPLETO

        return porcentaje, nivel

    def reiniciar_dispositivo(self) -> bool:
        """Reinicia el dispositivo"""
        resultado = self.ejecutar_comando('reboot', tiempo_espera=1.0)
        return resultado.exito

    def esta_conectado(self) -> bool:
        """Verifica si hay conexion activa"""
        return self._conectado and self.conexion is not None

    # ═══════════════════════════════════════════════════════════════
    # HEARTBEAT / KEEPALIVE PARA FIABILIDAD
    # ═══════════════════════════════════════════════════════════════

    def iniciar_heartbeat(self, intervalo_segundos: int = 30) -> bool:
        """
        Inicia heartbeat periódico para mantener conexión viva.

        Args:
            intervalo_segundos: Segundos entre heartbeats

        Returns:
            True si se inició correctamente
        """
        if self._heartbeat_activo:
            logger.warning("⚠️ Heartbeat ya está activo")
            return False

        self._heartbeat_activo = True
        self._heartbeat_thread = threading.Thread(
            target=self._loop_heartbeat,
            args=(intervalo_segundos,),
            daemon=True,
            name=f"Heartbeat-{self.host}"
        )
        self._heartbeat_thread.start()
        logger.info(f"✅ Heartbeat iniciado para {self.host} (intervalo: {intervalo_segundos}s)")
        return True

    def detener_heartbeat(self):
        """Detiene el heartbeat periódico"""
        self._heartbeat_activo = False
        if self._heartbeat_thread:
            self._heartbeat_thread.join(timeout=5)
        logger.info(f"✅ Heartbeat detenido para {self.host}")

    def _loop_heartbeat(self, intervalo: int):
        """Loop interno de heartbeat (ejecutado en thread separado)"""
        while self._heartbeat_activo and self._conectado:
            try:
                # Comando lightweight para heartbeat
                resultado = self.ejecutar_comando('echo SAC-heartbeat', tiempo_espera=1.0)

                if not resultado.exito:
                    logger.warning(f"⚠️ Heartbeat falló para {self.host} - intentando reconectar")
                    self._conectado = False
                    # Intentar reconectar automáticamente
                    if self.conectar(max_reintentos=2):
                        logger.info(f"✅ Reconexión automática exitosa para {self.host}")
                    else:
                        logger.error(f"❌ No se pudo reconectar a {self.host}")
                        self._heartbeat_activo = False
                        break

                time.sleep(intervalo)

            except Exception as e:
                logger.error(f"❌ Error en heartbeat: {e}")
                self._heartbeat_activo = False
                break

    # ═══════════════════════════════════════════════════════════════
    # FUNCIONES DE EMAIL PARA ALERTAS Y RESPUESTAS
    # ═══════════════════════════════════════════════════════════════

    def enviar_alerta_email(self, alerta: AlertaDispositivo,
                           destinatarios: Optional[List[str]] = None) -> bool:
        """
        Envía alerta crítica por email a operadores.

        Args:
            alerta: La alerta a enviar
            destinatarios: Lista de emails (usa config si no se proporciona)

        Returns:
            True si se envió exitosamente
        """
        if not self._config_email.usuario or not self._config_email.contraseña:
            logger.warning("⚠️ Email no configurado - no se puede enviar alerta")
            return False

        destinatarios = destinatarios or self._config_email.destinatarios_alertas
        if not destinatarios:
            logger.warning("⚠️ Sin destinatarios configurados para alertas")
            return False

        try:
            # Construir HTML del email
            asunto = f"🚨 [SAC-ALERTA {alerta.severidad.value}] {alerta.mensaje}"
            cuerpo_html = f"""
            <html>
                <body style="font-family: Arial; color: #333;">
                    <h2 style="color: red;">⚠️ ALERTA DEL SISTEMA SAC</h2>
                    <table border="1" cellpadding="10" style="border-collapse: collapse;">
                        <tr style="background-color: #f0f0f0;">
                            <td><b>Dispositivo</b></td>
                            <td>{alerta.dispositivo_serie}</td>
                        </tr>
                        <tr>
                            <td><b>Tipo</b></td>
                            <td>{alerta.tipo}</td>
                        </tr>
                        <tr>
                            <td><b>Severidad</b></td>
                            <td style="color: red;"><b>{alerta.severidad.value}</b></td>
                        </tr>
                        <tr>
                            <td><b>Mensaje</b></td>
                            <td>{alerta.mensaje}</td>
                        </tr>
                        <tr>
                            <td><b>Detalles</b></td>
                            <td>{alerta.detalles}</td>
                        </tr>
                        <tr>
                            <td><b>Solución</b></td>
                            <td style="color: green;"><b>{alerta.solucion}</b></td>
                        </tr>
                        <tr style="background-color: #f0f0f0;">
                            <td><b>Hora</b></td>
                            <td>{alerta.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</td>
                        </tr>
                    </table>
                    <hr>
                    <p style="color: #999; font-size: 12px;">
                        Sistema SAC - CEDIS 427<br>
                        Emulador SACITY para dispositivos Symbol MC9000/MC93<br>
                        Este es un mensaje automático. No responda.
                    </p>
                </body>
            </html>
            """

            return self._enviar_smtp(destinatarios, asunto, cuerpo_html)

        except Exception as e:
            logger.exception(f"❌ Error enviando alerta por email: {e}")
            return False

    def enviar_respuesta_comando_email(self, destinatario: str, comando: str,
                                       resultado: 'ResultadoComando') -> bool:
        """
        Envía resultado de comando ejecutado por email.

        Args:
            destinatario: Email del remitente original
            comando: Comando que se ejecutó
            resultado: Resultado de la ejecución

        Returns:
            True si se envió exitosamente
        """
        if not self._config_email.usuario or not self._config_email.contraseña:
            logger.warning("⚠️ Email no configurado - no se puede enviar respuesta")
            return False

        try:
            estado = "✅ EXITOSO" if resultado.exito else "❌ FALLIDO"
            asunto = f"[SAC] Respuesta: {comando[:50]} - {estado}"

            cuerpo_html = f"""
            <html>
                <body style="font-family: Arial; color: #333;">
                    <h2>📋 Respuesta de Comando SAC</h2>
                    <p><b>Dispositivo:</b> {self.host}:{self.port}</p>
                    <p><b>Comando:</b> <code>{comando}</code></p>
                    <p><b>Estado:</b> <span style="color: {'green' if resultado.exito else 'red'};"><b>{estado}</b></span></p>
                    <p><b>Tiempo:</b> {resultado.tiempo_ejecucion_ms:.1f}ms</p>

                    <h3>Respuesta:</h3>
                    <pre style="background-color: #f5f5f5; padding: 10px; border-radius: 5px; overflow-x: auto;">
{resultado.respuesta if resultado.respuesta else "(Sin respuesta)"}
                    </pre>

                    {f'<h3 style="color: red;">Errores:</h3><ul>' +
                     ''.join(f'<li>{err}</li>' for err in resultado.errores) +
                     '</ul>' if resultado.errores else ''}

                    <hr>
                    <p style="color: #999; font-size: 12px;">
                        Sistema SAC - CEDIS 427 | {resultado.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
                    </p>
                </body>
            </html>
            """

            return self._enviar_smtp([destinatario], asunto, cuerpo_html)

        except Exception as e:
            logger.exception(f"❌ Error enviando respuesta por email: {e}")
            return False

    def _enviar_smtp(self, destinatarios: List[str], asunto: str, cuerpo_html: str) -> bool:
        """
        Envía email vía SMTP (método interno).

        Args:
            destinatarios: Lista de emails
            asunto: Asunto del email
            cuerpo_html: Cuerpo en HTML

        Returns:
            True si se envió
        """
        try:
            # Crear mensaje
            mensaje = MIMEMultipart('alternative')
            mensaje['Subject'] = asunto
            mensaje['From'] = f"{self._config_email.remitente_nombre} <{self._config_email.remitente_email}>"
            mensaje['To'] = ', '.join(destinatarios)

            # Agregar HTML
            parte_html = MIMEText(cuerpo_html, 'html')
            mensaje.attach(parte_html)

            # Conectar y enviar
            with smtplib.SMTP(
                self._config_email.host_smtp,
                self._config_email.puerto_smtp,
                timeout=self._config_email.timeout_smtp
            ) as servidor:

                if self._config_email.usar_tls:
                    servidor.starttls()

                servidor.login(
                    self._config_email.usuario,
                    self._config_email.contraseña
                )

                servidor.send_message(mensaje)
                logger.info(f"✅ Email enviado a {len(destinatarios)} destinatario(s): {asunto[:50]}")
                return True

        except smtplib.SMTPAuthenticationError:
            logger.error("❌ Error de autenticación SMTP - verificar credenciales")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"❌ Error SMTP: {e}")
            return False
        except Exception as e:
            logger.exception(f"❌ Error enviando email: {e}")
            return False


# ===============================================================================
# GESTOR DE DRIVERS
# ===============================================================================

class GestorDriversCradle:
    """
    Gestiona drivers para bases de carga Symbol CRD9000.
    """

    def __init__(self, ruta_drivers: Optional[Path] = None):
        self.ruta_drivers = ruta_drivers or Path("drivers/symbol")
        self.bases_soportadas = BASES_CARGA
        logger.info("GestorDriversCradle inicializado")

    def verificar_drivers_instalados(self, modelo_base: str) -> bool:
        """
        Verifica si los drivers estan instalados para un modelo.

        Args:
            modelo_base: Modelo de la base de carga (ej: CRD9000-1000)

        Returns:
            True si los drivers estan instalados
        """
        if platform.system() != 'Windows':
            # En Linux/Mac generalmente no se necesitan drivers especiales
            return True

        try:
            # Verificar en registro de Windows
            import winreg

            # Buscar driver Symbol/Zebra
            rutas_busqueda = [
                r"SYSTEM\CurrentControlSet\Services\symbolusb",
                r"SYSTEM\CurrentControlSet\Services\zebrausb",
                r"SYSTEM\CurrentControlSet\Services\motousb"
            ]

            for ruta in rutas_busqueda:
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, ruta)
                    winreg.CloseKey(key)
                    return True
                except FileNotFoundError:
                    continue

            return False

        except ImportError:
            logger.warning("winreg no disponible")
            return False
        except Exception as e:
            logger.error(f"Error verificando drivers: {e}")
            return False

    def instalar_drivers(self, modelo_base: str) -> Tuple[bool, str]:
        """
        Instala drivers para un modelo de base de carga.

        Args:
            modelo_base: Modelo de la base de carga

        Returns:
            Tupla (exito, mensaje)
        """
        if modelo_base not in self.bases_soportadas:
            return False, f"Modelo {modelo_base} no soportado"

        if platform.system() != 'Windows':
            return True, "Drivers no requeridos en este sistema operativo"

        # Buscar archivo INF del driver
        ruta_inf = self._buscar_driver_inf(modelo_base)

        if not ruta_inf:
            return False, f"No se encontro driver para {modelo_base}"

        try:
            # Usar pnputil para instalar driver
            result = subprocess.run(
                ['pnputil', '/add-driver', str(ruta_inf), '/install'],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                return True, f"Driver instalado: {ruta_inf.name}"
            else:
                return False, f"Error instalando driver: {result.stderr}"

        except subprocess.TimeoutExpired:
            return False, "Timeout instalando driver"
        except Exception as e:
            return False, f"Error: {str(e)}"

    def _buscar_driver_inf(self, modelo_base: str) -> Optional[Path]:
        """Busca archivo INF del driver para un modelo"""
        if not self.ruta_drivers.exists():
            return None

        # Mapeo de modelo a carpeta de driver
        mapeo_carpetas = {
            'CRD9000-1000': 'crd9000',
            'CRD9000-1001SR': 'crd9000',
            'CRD-MCB3-28UCHO': 'mc93'
        }

        carpeta = mapeo_carpetas.get(modelo_base, modelo_base.lower())
        ruta_carpeta = self.ruta_drivers / carpeta

        if ruta_carpeta.exists():
            for inf_file in ruta_carpeta.glob('*.inf'):
                return inf_file

        return None

    def obtener_info_base(self, modelo_base: str) -> Optional[Dict]:
        """Obtiene informacion de una base de carga"""
        return self.bases_soportadas.get(modelo_base)


# ===============================================================================
# ASISTENTE IA PARA DISPOSITIVOS
# ===============================================================================

class AsistenteIASymbol:
    """
    Asistente IA para control de dispositivos Symbol via lenguaje natural.

    Permite ejecutar comandos como:
    - "Mostrar bateria"
    - "Ver estado de red"
    - "Reiniciar dispositivo"
    - "Listar archivos"
    """

    def __init__(
        self,
        detector: DetectorDispositivosSymbol,
        telnet: Optional[SymbolTelnetCE] = None
    ):
        self.detector = detector
        self.telnet = telnet
        self.comandos_nl = self._crear_mapeo_comandos()
        logger.info("AsistenteIASymbol inicializado")

    def _crear_mapeo_comandos(self) -> Dict[str, Dict]:
        """Crea mapeo de frases naturales a comandos"""
        return {
            'bateria': {
                'patrones': ['bateria', 'battery', 'carga', 'energia', 'power'],
                'comando': 'power',
                'descripcion': 'Muestra estado de bateria'
            },
            'red': {
                'patrones': ['red', 'network', 'ip', 'internet', 'wifi', 'wlan'],
                'comando': 'ipconfig',
                'descripcion': 'Muestra configuracion de red'
            },
            'almacenamiento': {
                'patrones': ['almacenamiento', 'storage', 'disco', 'espacio', 'archivos'],
                'comando': 'dir \\',
                'descripcion': 'Muestra almacenamiento'
            },
            'reiniciar': {
                'patrones': ['reiniciar', 'reboot', 'restart', 'reinicio'],
                'comando': 'reboot',
                'descripcion': 'Reinicia el dispositivo'
            },
            'procesos': {
                'patrones': ['procesos', 'processes', 'apps', 'aplicaciones', 'programas'],
                'comando': 'ps',
                'descripcion': 'Lista procesos activos'
            },
            'escanear': {
                'patrones': ['escanear', 'scan', 'codigo', 'barras', 'barcode'],
                'comando': 'scan',
                'descripcion': 'Activa escaner'
            },
            'memoria': {
                'patrones': ['memoria', 'memory', 'ram'],
                'comando': 'mem',
                'descripcion': 'Muestra estado de memoria'
            },
            'fecha': {
                'patrones': ['fecha', 'hora', 'date', 'time', 'reloj'],
                'comando': 'date',
                'descripcion': 'Muestra fecha y hora'
            },
            'version': {
                'patrones': ['version', 'firmware', 'sistema', 'os'],
                'comando': 'ver',
                'descripcion': 'Muestra version del sistema'
            }
        }

    def procesar_comando_natural(self, entrada: str) -> ResultadoComando:
        """
        Procesa un comando en lenguaje natural.

        Args:
            entrada: Texto del usuario en lenguaje natural

        Returns:
            ResultadoComando con la respuesta
        """
        entrada_lower = entrada.lower()

        # Buscar comando coincidente
        for nombre, info in self.comandos_nl.items():
            for patron in info['patrones']:
                if patron in entrada_lower:
                    if self.telnet and self.telnet.esta_conectado():
                        return self.telnet.ejecutar_comando(info['comando'])
                    else:
                        return ResultadoComando(
                            comando=info['comando'],
                            exito=False,
                            respuesta="",
                            tiempo_ejecucion_ms=0,
                            errores=["No hay conexion activa con el dispositivo"]
                        )

        # Comando no reconocido
        return ResultadoComando(
            comando=entrada,
            exito=False,
            respuesta="",
            tiempo_ejecucion_ms=0,
            errores=[
                "Comando no reconocido",
                f"Comandos disponibles: {', '.join(self.comandos_nl.keys())}"
            ]
        )

    def obtener_ayuda(self) -> str:
        """Retorna ayuda de comandos disponibles"""
        lineas = ["Comandos disponibles:\n"]
        for nombre, info in self.comandos_nl.items():
            lineas.append(f"  - {nombre}: {info['descripcion']}")
            lineas.append(f"    Palabras clave: {', '.join(info['patrones'])}")
        return '\n'.join(lineas)

    def ejecutar_health_check(self, enviar_alertas: bool = True) -> ReporteHealthCheck:
        """
        Ejecuta verificacion de salud automatizada.

        Args:
            enviar_alertas: Si True, envía alertas críticas por email

        Returns:
            ReporteHealthCheck con resultados
        """
        verificaciones = {}
        alertas = []

        # Detectar dispositivos
        dispositivos = self.detector.detectar_dispositivos_usb()

        if not dispositivos:
            alerta_no_dispositivos = AlertaDispositivo(
                dispositivo_serie="N/A",
                tipo="NO_DISPOSITIVOS",
                severidad=SeveridadAlerta.ALTO,
                mensaje="No se detectaron dispositivos Symbol",
                detalles="Verificar conexion USB y drivers",
                solucion="Conectar dispositivo o instalar drivers"
            )
            alertas.append(alerta_no_dispositivos)

            # Enviar alerta si está habilitado
            if enviar_alertas and self.telnet:
                self.telnet.enviar_alerta_email(alerta_no_dispositivos)

            return ReporteHealthCheck(
                dispositivo=InfoDispositivo(),
                verificaciones={'dispositivos_detectados': False},
                alertas=alertas,
                estado_general="ERROR"
            )

        dispositivo = dispositivos[0]
        verificaciones['dispositivos_detectados'] = True

        if self.telnet and self.telnet.esta_conectado():
            # Verificar bateria
            porcentaje, nivel = self.telnet.obtener_estado_bateria()
            dispositivo.bateria_porcentaje = porcentaje
            dispositivo.nivel_bateria = nivel

            verificaciones['bateria'] = porcentaje > 15

            if nivel == NivelBateria.CRITICO:
                alerta_bateria_critica = AlertaDispositivo(
                    dispositivo_serie=dispositivo.serie,
                    tipo="BATERIA_CRITICA",
                    severidad=SeveridadAlerta.CRITICO,
                    mensaje=f"Bateria critica: {porcentaje}%",
                    detalles="El dispositivo puede apagarse",
                    solucion="Cargar inmediatamente"
                )
                alertas.append(alerta_bateria_critica)

                # ENVIAR ALERTA CRÍTICA POR EMAIL INMEDIATAMENTE
                if enviar_alertas:
                    logger.warning(f"🚨 Enviando alerta de batería crítica por email")
                    self.telnet.enviar_alerta_email(alerta_bateria_critica)

            elif nivel == NivelBateria.BAJO:
                alerta_bateria_baja = AlertaDispositivo(
                    dispositivo_serie=dispositivo.serie,
                    tipo="BATERIA_BAJA",
                    severidad=SeveridadAlerta.MEDIO,
                    mensaje=f"Bateria baja: {porcentaje}%",
                    detalles="Considerar cargar pronto",
                    solucion="Programar carga"
                )
                alertas.append(alerta_bateria_baja)

                # Enviar alerta
                if enviar_alertas:
                    self.telnet.enviar_alerta_email(alerta_bateria_baja)

            # Verificar red
            resultado_red = self.telnet.ejecutar_comando('ipconfig')
            verificaciones['red'] = resultado_red.exito

            # Verificar almacenamiento
            resultado_storage = self.telnet.ejecutar_comando('dir \\')
            verificaciones['almacenamiento'] = resultado_storage.exito

        # Determinar estado general
        if any(a.severidad == SeveridadAlerta.CRITICO for a in alertas):
            estado_general = "CRITICO"
        elif any(a.severidad == SeveridadAlerta.ALTO for a in alertas):
            estado_general = "ADVERTENCIA"
        elif all(verificaciones.values()):
            estado_general = "OK"
        else:
            estado_general = "PARCIAL"

        reporte = ReporteHealthCheck(
            dispositivo=dispositivo,
            verificaciones=verificaciones,
            alertas=alertas,
            estado_general=estado_general
        )

        # Log resumen de health check
        emoji_estado = "✅" if estado_general == "OK" else "⚠️" if estado_general in ["PARCIAL", "ADVERTENCIA"] else "🔴"
        logger.info(f"{emoji_estado} Health Check: {estado_general} | Batería: {dispositivo.bateria_porcentaje}% | "
                   f"Alertas: {len(alertas)}")

        return reporte


# ===============================================================================
# GESTOR PRINCIPAL DE DISPOSITIVOS SYMBOL
# ===============================================================================

class GestorDispositivosSymbol:
    """
    Gestor principal para dispositivos Symbol MC9000/MC93.

    Integra todas las capacidades:
    - Deteccion de dispositivos
    - Comunicacion TelnetCE
    - Gestion de drivers
    - Asistente IA
    - Monitoreo de salud
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}

        # Inicializar componentes
        self.detector = DetectorDispositivosSymbol()
        self.gestor_drivers = GestorDriversCradle()
        self.telnet: Optional[SymbolTelnetCE] = None
        self.asistente_ia: Optional[AsistenteIASymbol] = None

        # Estado
        self._dispositivos: List[InfoDispositivo] = []
        self._dispositivo_activo: Optional[InfoDispositivo] = None

        logger.info("GestorDispositivosSymbol inicializado")

    def inicializar(self) -> bool:
        """
        Inicializa el gestor y detecta dispositivos.

        Returns:
            True si se detecto al menos un dispositivo
        """
        print(f"\n{Colores.CYAN}{'='*60}{Colores.RESET}")
        print(f"{Colores.BOLD}  GESTOR DE DISPOSITIVOS SYMBOL MC9000/MC93{Colores.RESET}")
        print(f"{Colores.CYAN}{'='*60}{Colores.RESET}\n")

        # Detectar dispositivos
        print(f"{Colores.YELLOW}Detectando dispositivos...{Colores.RESET}")
        self._dispositivos = self.detector.detectar_dispositivos_usb()

        if self._dispositivos:
            print(f"{Colores.GREEN}Se detectaron {len(self._dispositivos)} dispositivo(s):{Colores.RESET}")
            for i, disp in enumerate(self._dispositivos, 1):
                print(f"  {i}. {disp.modelo} ({disp.familia}) en {disp.puerto}")

            # Seleccionar primer dispositivo como activo
            self._dispositivo_activo = self._dispositivos[0]

            # Inicializar asistente IA
            self.asistente_ia = AsistenteIASymbol(self.detector, self.telnet)

            return True
        else:
            print(f"{Colores.RED}No se detectaron dispositivos Symbol{Colores.RESET}")
            return False

    def detectar_dispositivos(self) -> List[InfoDispositivo]:
        """Detecta y retorna dispositivos conectados"""
        self._dispositivos = self.detector.detectar_dispositivos_usb()
        return self._dispositivos

    def conectar_telnet(
        self,
        host: str,
        port: int = 23,
        usuario: str = 'admin',
        password: str = '',
        familia_dispositivo: str = 'MC9200',
        config_email: Optional[ConfiguracionEmail] = None
    ) -> bool:
        """
        Conecta via TelnetCE a un dispositivo.

        Args:
            host: IP del dispositivo
            port: Puerto telnet (default 23)
            usuario: Usuario de login
            password: Password
            familia_dispositivo: Familia del dispositivo (MC9000, MC9100, MC9200, MC93)
            config_email: Configuración de email para alertas

        Returns:
            True si la conexion fue exitosa
        """
        self.telnet = SymbolTelnetCE(
            host,
            port,
            timeout=10,
            usuario=usuario,
            password=password,
            familia_dispositivo=familia_dispositivo,
            config_email=config_email
        )

        # Conectar con reintentos automáticos
        conectado = self.telnet.conectar(max_reintentos=3)

        if conectado:
            # Iniciar heartbeat automático
            self.telnet.iniciar_heartbeat(intervalo_segundos=30)

            if self.asistente_ia:
                self.asistente_ia.telnet = self.telnet

            logger.info(f"✅ Conexión TelnetCE establecida con {host}:{port}")
        else:
            logger.error(f"❌ No se pudo conectar a {host}:{port}")

        return conectado

    def desconectar_telnet(self):
        """Desconecta la sesion Telnet activa"""
        if self.telnet:
            self.telnet.desconectar()

    def obtener_info_dispositivo(self) -> Optional[Dict[str, str]]:
        """Obtiene informacion del dispositivo conectado via Telnet"""
        if not self.telnet or not self.telnet.esta_conectado():
            return None
        return self.telnet.obtener_info_dispositivo()

    def ejecutar_comando(self, comando: str) -> ResultadoComando:
        """
        Ejecuta un comando en el dispositivo.

        Args:
            comando: Comando a ejecutar (puede ser natural o tecnico)

        Returns:
            ResultadoComando
        """
        # Intentar primero como comando natural via asistente
        if self.asistente_ia:
            resultado = self.asistente_ia.procesar_comando_natural(comando)
            if resultado.exito or 'No reconocido' not in str(resultado.errores):
                return resultado

        # Ejecutar comando tecnico directamente
        if self.telnet and self.telnet.esta_conectado():
            return self.telnet.ejecutar_comando(comando)

        return ResultadoComando(
            comando=comando,
            exito=False,
            respuesta="",
            tiempo_ejecucion_ms=0,
            errores=["No hay conexion activa"]
        )

    def ejecutar_health_check(self) -> ReporteHealthCheck:
        """Ejecuta verificacion de salud completa"""
        if self.asistente_ia:
            return self.asistente_ia.ejecutar_health_check()

        return ReporteHealthCheck(
            dispositivo=InfoDispositivo(),
            verificaciones={},
            alertas=[],
            estado_general="NO_INICIALIZADO"
        )

    def verificar_drivers(self, modelo_base: str) -> bool:
        """Verifica si los drivers estan instalados"""
        return self.gestor_drivers.verificar_drivers_instalados(modelo_base)

    def instalar_drivers(self, modelo_base: str) -> Tuple[bool, str]:
        """Instala drivers para una base de carga"""
        return self.gestor_drivers.instalar_drivers(modelo_base)

    def obtener_dispositivo_activo(self) -> Optional[InfoDispositivo]:
        """Retorna el dispositivo activo actual"""
        return self._dispositivo_activo

    def seleccionar_dispositivo(self, indice: int) -> bool:
        """
        Selecciona un dispositivo por indice.

        Args:
            indice: Indice del dispositivo (0-based)

        Returns:
            True si la seleccion fue exitosa
        """
        if 0 <= indice < len(self._dispositivos):
            self._dispositivo_activo = self._dispositivos[indice]
            return True
        return False

    def modo_interactivo(self):
        """
        Inicia modo interactivo de comandos.
        """
        print(f"\n{Colores.CYAN}{'='*60}{Colores.RESET}")
        print(f"{Colores.BOLD}  MODO INTERACTIVO SYMBOL SAC{Colores.RESET}")
        print(f"{Colores.CYAN}{'='*60}{Colores.RESET}")
        print(f"\nComandos disponibles: bateria, red, almacenamiento, procesos")
        print(f"Escribe 'ayuda' para mas informacion o 'salir' para terminar.\n")

        while True:
            try:
                entrada = input(f"{Colores.GREEN}SAC-Symbol>{Colores.RESET} ").strip()

                if not entrada:
                    continue

                entrada_lower = entrada.lower()

                if entrada_lower in ['salir', 'exit', 'quit', 'q']:
                    print(f"\n{Colores.YELLOW}Saliendo del modo interactivo...{Colores.RESET}")
                    break

                if entrada_lower in ['ayuda', 'help', '?']:
                    if self.asistente_ia:
                        print(self.asistente_ia.obtener_ayuda())
                    continue

                if entrada_lower in ['health', 'salud', 'verificar']:
                    reporte = self.ejecutar_health_check()
                    self._mostrar_reporte_health(reporte)
                    continue

                # Ejecutar comando
                resultado = self.ejecutar_comando(entrada)

                if resultado.exito:
                    print(f"\n{Colores.WHITE}{resultado.respuesta}{Colores.RESET}")
                    print(f"{Colores.DIM}(Tiempo: {resultado.tiempo_ejecucion_ms:.1f}ms){Colores.RESET}\n")
                else:
                    print(f"\n{Colores.RED}Error: {', '.join(resultado.errores)}{Colores.RESET}\n")

            except KeyboardInterrupt:
                print(f"\n\n{Colores.YELLOW}Operacion cancelada{Colores.RESET}")
                break
            except Exception as e:
                print(f"\n{Colores.RED}Error: {e}{Colores.RESET}\n")

    def _mostrar_reporte_health(self, reporte: ReporteHealthCheck):
        """Muestra reporte de salud formateado"""
        print(f"\n{Colores.CYAN}--- REPORTE DE SALUD ---{Colores.RESET}")
        print(f"Dispositivo: {reporte.dispositivo.modelo} ({reporte.dispositivo.serie})")
        print(f"Estado General: ", end="")

        if reporte.estado_general == "OK":
            print(f"{Colores.GREEN}{reporte.estado_general}{Colores.RESET}")
        elif reporte.estado_general == "CRITICO":
            print(f"{Colores.RED}{reporte.estado_general}{Colores.RESET}")
        else:
            print(f"{Colores.YELLOW}{reporte.estado_general}{Colores.RESET}")

        print(f"\nVerificaciones:")
        for nombre, resultado in reporte.verificaciones.items():
            icono = f"{Colores.GREEN}OK{Colores.RESET}" if resultado else f"{Colores.RED}FALLO{Colores.RESET}"
            print(f"  - {nombre}: {icono}")

        if reporte.alertas:
            print(f"\n{Colores.YELLOW}Alertas:{Colores.RESET}")
            for alerta in reporte.alertas:
                print(f"  [{alerta.severidad.value}] {alerta.mensaje}")
                print(f"    Solucion: {alerta.solucion}")

        print()


# ===============================================================================
# FUNCIONES DE CONVENIENCIA
# ===============================================================================

def crear_gestor_symbol(config: Optional[Dict] = None) -> GestorDispositivosSymbol:
    """
    Crea e inicializa un gestor de dispositivos Symbol.

    Args:
        config: Configuracion opcional

    Returns:
        GestorDispositivosSymbol inicializado
    """
    gestor = GestorDispositivosSymbol(config)
    gestor.inicializar()
    return gestor


def detectar_dispositivos_symbol() -> List[InfoDispositivo]:
    """
    Detecta dispositivos Symbol conectados.

    Returns:
        Lista de dispositivos detectados
    """
    detector = DetectorDispositivosSymbol()
    return detector.detectar_dispositivos_usb()


def conectar_symbol_telnet(
    host: str,
    port: int = 23,
    usuario: str = 'admin',
    password: str = ''
) -> Optional[SymbolTelnetCE]:
    """
    Conecta a un dispositivo Symbol via TelnetCE.

    Args:
        host: IP del dispositivo
        port: Puerto telnet
        usuario: Usuario
        password: Password

    Returns:
        SymbolTelnetCE conectado o None
    """
    telnet = SymbolTelnetCE(host, port, 10, usuario, password)
    if telnet.conectar():
        return telnet
    return None


def health_check_symbol() -> ReporteHealthCheck:
    """
    Ejecuta health check rapido de dispositivos Symbol.

    Returns:
        ReporteHealthCheck
    """
    gestor = GestorDispositivosSymbol()
    gestor.inicializar()
    return gestor.ejecutar_health_check()


# ===============================================================================
# DEMO Y PRUEBAS
# ===============================================================================

def demo_symbol_mc9000():
    """Demo del modulo de dispositivos Symbol"""
    print(f"\n{'='*60}")
    print("  DEMO: MODULO SYMBOL MC9000/MC93 - SAC v2.0")
    print(f"{'='*60}\n")

    # Crear gestor
    gestor = crear_gestor_symbol()

    # Mostrar dispositivos detectados
    dispositivos = gestor.detectar_dispositivos()
    print(f"\nDispositivos detectados: {len(dispositivos)}")

    for disp in dispositivos:
        print(f"\n  Modelo: {disp.modelo}")
        print(f"  Familia: {disp.familia}")
        print(f"  Puerto: {disp.puerto}")
        print(f"  Estado: {disp.estado.value}")

    # Si hay dispositivos, ofrecer modo interactivo
    if dispositivos:
        respuesta = input("\nDesea entrar al modo interactivo? (s/n): ")
        if respuesta.lower() in ['s', 'si', 'yes', 'y']:
            # Para demo, simular conexion exitosa
            print("\nNota: Para conectar via Telnet, ejecute:")
            print("  gestor.conectar_telnet('192.168.1.100')")
            print("\nIniciando modo interactivo (modo simulacion)...\n")
            gestor.modo_interactivo()
    else:
        print("\nNo se detectaron dispositivos Symbol conectados.")
        print("Asegurese de que:")
        print("  1. El dispositivo esta conectado via USB o en la base de carga")
        print("  2. Los drivers estan instalados (Windows)")
        print("  3. TelnetCE esta habilitado en el dispositivo")

    print(f"\n{'='*60}")
    print("  FIN DEL DEMO")
    print(f"{'='*60}\n")


# ===============================================================================
# PUNTO DE ENTRADA
# ===============================================================================

if __name__ == "__main__":
    # Configurar logging basico
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Ejecutar demo
    demo_symbol_mc9000()
