#!/usr/bin/env python3
"""
===============================================================================
VALIDADOR DE CONEXIONES E INTERCONEXIONES DEL SISTEMA SAC
Sistema de Automatización de Consultas - CEDIS Cancún 427
===============================================================================

Este script valida todas las conexiones entre módulos, librerías, APIs,
bases de datos y servicios del sistema SAC.

Características:
- Validación de imports entre módulos
- Verificación de dependencias
- Prueba de conexión a DB2 (con soporte nativo sin credenciales)
- Verificación de configuración
- Análisis de interconexiones
- Generación de reporte de estado

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
===============================================================================
"""

import os
import sys
import json
import time
import logging
import importlib
import importlib.util
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import traceback

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ===============================================================================
# CONSTANTES Y CONFIGURACIÓN
# ===============================================================================

BASE_DIR = Path(__file__).resolve().parent

# Colores ANSI para terminal
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

# ===============================================================================
# ENUMS Y DATACLASSES
# ===============================================================================

class EstadoValidacion(Enum):
    """Estados posibles de validación"""
    EXITOSO = "✅ EXITOSO"
    FALLIDO = "❌ FALLIDO"
    ADVERTENCIA = "⚠️ ADVERTENCIA"
    OMITIDO = "⏭️ OMITIDO"
    PENDIENTE = "⏳ PENDIENTE"


class TipoValidacion(Enum):
    """Tipos de validación"""
    MODULO = "módulo"
    CONEXION_DB = "conexión_db"
    CONFIGURACION = "configuración"
    DEPENDENCIA = "dependencia"
    API = "api"
    EMAIL = "email"
    TELEGRAM = "telegram"
    FILESYSTEM = "filesystem"


@dataclass
class ResultadoValidacion:
    """Resultado de una validación individual"""
    nombre: str
    tipo: TipoValidacion
    estado: EstadoValidacion
    mensaje: str = ""
    detalles: Dict = field(default_factory=dict)
    tiempo_ms: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ReporteValidacion:
    """Reporte completo de validación"""
    total_validaciones: int = 0
    exitosos: int = 0
    fallidos: int = 0
    advertencias: int = 0
    omitidos: int = 0
    tiempo_total_ms: float = 0.0
    resultados: List[ResultadoValidacion] = field(default_factory=list)
    timestamp_inicio: str = ""
    timestamp_fin: str = ""
    version_sistema: str = ""


# ===============================================================================
# VALIDADOR PRINCIPAL
# ===============================================================================

class ValidadorConexiones:
    """
    Validador completo de conexiones e interconexiones del sistema SAC.

    Verifica:
    - Imports de módulos
    - Configuración central
    - Conexión a base de datos
    - Servicios externos (Email, Telegram)
    - APIs internas
    - Sistema de archivos
    """

    def __init__(self, modo_verbose: bool = True, intentar_conexion_nativa: bool = True):
        """
        Inicializa el validador

        Args:
            modo_verbose: Si True, muestra detalles en consola
            intentar_conexion_nativa: Si True, intenta conexión DB sin credenciales
        """
        self.modo_verbose = modo_verbose
        self.intentar_conexion_nativa = intentar_conexion_nativa
        self.reporte = ReporteValidacion()
        self.reporte.timestamp_inicio = datetime.now().isoformat()

        # Módulos a validar
        self.modulos_core = [
            'config',
            'monitor',
            'main',
            'maestro',
            'gestor_correos',
        ]

        self.modulos_modules = [
            'modules.db_connection',
            'modules.db_pool',
            'modules.query_builder',
            'modules.db_schema',
            'modules.db_local',
            'modules.db_sync',
            'modules.repositories',
            'modules.modulo_cartones',
            'modules.modulo_lpn',
            'modules.modulo_ubicaciones',
            'modules.modulo_usuarios',
            'modules.reportes_excel',
            'modules.modulo_alertas',
            'modules.modulo_auto_config',
            'modules.modulo_ups_backup',
            'modules.modulo_control_trafico',
            'modules.modulo_habilitacion_usuarios',
            'modules.agente_sac',
            'modules.agente_ia',
            'modules.scheduling_trafico',
            'modules.api',
            'modules.modulo_symbol_mc9000',
            'modules.modulo_funciones_cedis',
        ]

        self.dependencias_externas = [
            ('pandas', 'pip install pandas'),
            ('openpyxl', 'pip install openpyxl'),
            ('dotenv', 'pip install python-dotenv'),
            ('requests', 'pip install requests'),
            ('yaml', 'pip install pyyaml'),
            ('jinja2', 'pip install jinja2'),
        ]

        self.dependencias_db = [
            ('ibm_db', 'pip install ibm-db'),
            ('pyodbc', 'pip install pyodbc'),
        ]

    def _log(self, mensaje: str, nivel: str = "INFO"):
        """Log con formato"""
        if self.modo_verbose:
            if nivel == "ERROR":
                print(f"{Colors.RED}{mensaje}{Colors.ENDC}")
            elif nivel == "WARNING":
                print(f"{Colors.WARNING}{mensaje}{Colors.ENDC}")
            elif nivel == "SUCCESS":
                print(f"{Colors.GREEN}{mensaje}{Colors.ENDC}")
            else:
                print(mensaje)

    def _agregar_resultado(self, resultado: ResultadoValidacion):
        """Agrega un resultado al reporte"""
        self.reporte.resultados.append(resultado)
        self.reporte.total_validaciones += 1

        if resultado.estado == EstadoValidacion.EXITOSO:
            self.reporte.exitosos += 1
        elif resultado.estado == EstadoValidacion.FALLIDO:
            self.reporte.fallidos += 1
        elif resultado.estado == EstadoValidacion.ADVERTENCIA:
            self.reporte.advertencias += 1
        elif resultado.estado == EstadoValidacion.OMITIDO:
            self.reporte.omitidos += 1

    # =========================================================================
    # VALIDACIÓN DE MÓDULOS
    # =========================================================================

    def validar_modulo(self, nombre_modulo: str) -> ResultadoValidacion:
        """
        Valida que un módulo pueda ser importado correctamente

        Args:
            nombre_modulo: Nombre del módulo a validar

        Returns:
            ResultadoValidacion con el estado
        """
        inicio = time.time()

        try:
            modulo = importlib.import_module(nombre_modulo)
            tiempo = (time.time() - inicio) * 1000

            # Obtener información del módulo
            detalles = {
                'archivo': getattr(modulo, '__file__', 'N/A'),
                'version': getattr(modulo, '__version__', getattr(modulo, 'VERSION', 'N/A')),
                'exports': len(getattr(modulo, '__all__', [])),
            }

            resultado = ResultadoValidacion(
                nombre=nombre_modulo,
                tipo=TipoValidacion.MODULO,
                estado=EstadoValidacion.EXITOSO,
                mensaje=f"Módulo importado correctamente",
                detalles=detalles,
                tiempo_ms=tiempo
            )

            self._log(f"  {resultado.estado.value} {nombre_modulo} ({tiempo:.1f}ms)", "SUCCESS")

        except ImportError as e:
            tiempo = (time.time() - inicio) * 1000
            resultado = ResultadoValidacion(
                nombre=nombre_modulo,
                tipo=TipoValidacion.MODULO,
                estado=EstadoValidacion.FALLIDO,
                mensaje=f"Error de importación: {str(e)}",
                detalles={'error': str(e), 'traceback': traceback.format_exc()},
                tiempo_ms=tiempo
            )
            self._log(f"  {resultado.estado.value} {nombre_modulo}: {str(e)[:50]}", "ERROR")

        except Exception as e:
            tiempo = (time.time() - inicio) * 1000
            resultado = ResultadoValidacion(
                nombre=nombre_modulo,
                tipo=TipoValidacion.MODULO,
                estado=EstadoValidacion.FALLIDO,
                mensaje=f"Error inesperado: {str(e)}",
                detalles={'error': str(e), 'traceback': traceback.format_exc()},
                tiempo_ms=tiempo
            )
            self._log(f"  {resultado.estado.value} {nombre_modulo}: {str(e)[:50]}", "ERROR")

        self._agregar_resultado(resultado)
        return resultado

    def validar_todos_modulos(self) -> List[ResultadoValidacion]:
        """Valida todos los módulos del sistema"""
        self._log("\n" + "="*60)
        self._log("📦 VALIDANDO MÓDULOS CORE")
        self._log("="*60)

        resultados = []

        # Módulos core
        for modulo in self.modulos_core:
            resultados.append(self.validar_modulo(modulo))

        self._log("\n" + "="*60)
        self._log("📦 VALIDANDO MÓDULOS DEL DIRECTORIO modules/")
        self._log("="*60)

        # Módulos en modules/
        for modulo in self.modulos_modules:
            resultados.append(self.validar_modulo(modulo))

        return resultados

    # =========================================================================
    # VALIDACIÓN DE DEPENDENCIAS
    # =========================================================================

    def validar_dependencia(self, nombre: str, comando_instalacion: str) -> ResultadoValidacion:
        """Valida una dependencia externa"""
        inicio = time.time()

        try:
            modulo = importlib.import_module(nombre)
            tiempo = (time.time() - inicio) * 1000

            version = getattr(modulo, '__version__', 'N/A')

            resultado = ResultadoValidacion(
                nombre=nombre,
                tipo=TipoValidacion.DEPENDENCIA,
                estado=EstadoValidacion.EXITOSO,
                mensaje=f"Versión: {version}",
                detalles={'version': version},
                tiempo_ms=tiempo
            )
            self._log(f"  {resultado.estado.value} {nombre} v{version}", "SUCCESS")

        except ImportError:
            tiempo = (time.time() - inicio) * 1000
            resultado = ResultadoValidacion(
                nombre=nombre,
                tipo=TipoValidacion.DEPENDENCIA,
                estado=EstadoValidacion.FALLIDO,
                mensaje=f"No instalado. Instalar con: {comando_instalacion}",
                detalles={'comando': comando_instalacion},
                tiempo_ms=tiempo
            )
            self._log(f"  {resultado.estado.value} {nombre}: {comando_instalacion}", "ERROR")

        self._agregar_resultado(resultado)
        return resultado

    def validar_todas_dependencias(self) -> List[ResultadoValidacion]:
        """Valida todas las dependencias"""
        self._log("\n" + "="*60)
        self._log("📚 VALIDANDO DEPENDENCIAS EXTERNAS")
        self._log("="*60)

        resultados = []

        for nombre, comando in self.dependencias_externas:
            resultados.append(self.validar_dependencia(nombre, comando))

        self._log("\n" + "="*60)
        self._log("💾 VALIDANDO DRIVERS DE BASE DE DATOS")
        self._log("="*60)

        for nombre, comando in self.dependencias_db:
            resultados.append(self.validar_dependencia(nombre, comando))

        return resultados

    # =========================================================================
    # VALIDACIÓN DE CONFIGURACIÓN
    # =========================================================================

    def validar_configuracion(self) -> ResultadoValidacion:
        """Valida la configuración central del sistema"""
        inicio = time.time()

        try:
            from config import (
                DB_CONFIG, EMAIL_CONFIG, CEDIS, PATHS,
                SYSTEM_CONFIG, validar_configuracion
            )

            es_valida, errores = validar_configuracion()
            tiempo = (time.time() - inicio) * 1000

            errores_criticos = [e for e in errores if "CRÍTICO" in e]

            detalles = {
                'db_host': DB_CONFIG.get('host'),
                'db_port': DB_CONFIG.get('port'),
                'db_database': DB_CONFIG.get('database'),
                'db_user': DB_CONFIG.get('user'),
                'db_password_configurado': DB_CONFIG.get('password') not in ['tu_password', '', None],
                'email_user': EMAIL_CONFIG.get('user'),
                'email_configurado': EMAIL_CONFIG.get('password') not in ['tu_password', '', None],
                'cedis_code': CEDIS.get('code'),
                'version': SYSTEM_CONFIG.get('version'),
                'errores': errores,
                'errores_criticos': len(errores_criticos),
            }

            if es_valida:
                estado = EstadoValidacion.EXITOSO
                mensaje = "Configuración válida"
            elif errores_criticos:
                estado = EstadoValidacion.FALLIDO
                mensaje = f"{len(errores_criticos)} errores críticos encontrados"
            else:
                estado = EstadoValidacion.ADVERTENCIA
                mensaje = f"{len(errores)} advertencias encontradas"

            resultado = ResultadoValidacion(
                nombre="config.py",
                tipo=TipoValidacion.CONFIGURACION,
                estado=estado,
                mensaje=mensaje,
                detalles=detalles,
                tiempo_ms=tiempo
            )

            self._log(f"\n  {resultado.estado.value} Configuración: {mensaje}",
                     "SUCCESS" if es_valida else "WARNING")

            if errores:
                for error in errores[:5]:  # Mostrar solo los primeros 5
                    self._log(f"     {error}", "WARNING" if "⚠️" in error else "ERROR")

        except Exception as e:
            tiempo = (time.time() - inicio) * 1000
            resultado = ResultadoValidacion(
                nombre="config.py",
                tipo=TipoValidacion.CONFIGURACION,
                estado=EstadoValidacion.FALLIDO,
                mensaje=f"Error cargando configuración: {str(e)}",
                detalles={'error': str(e)},
                tiempo_ms=tiempo
            )
            self._log(f"  {resultado.estado.value} Error: {str(e)}", "ERROR")

        self._agregar_resultado(resultado)
        return resultado

    # =========================================================================
    # VALIDACIÓN DE CONEXIÓN A BASE DE DATOS
    # =========================================================================

    def validar_conexion_db(self, usar_credenciales: bool = True) -> ResultadoValidacion:
        """
        Valida la conexión a la base de datos DB2

        Args:
            usar_credenciales: Si False, intenta conexión nativa
        """
        inicio = time.time()

        try:
            from modules.db_connection import (
                DB2Connection, get_connection_info,
                IBM_DB_AVAILABLE, PYODBC_AVAILABLE
            )
            from config import DB_CONFIG

            info = get_connection_info()

            # Verificar si hay drivers disponibles
            if not IBM_DB_AVAILABLE and not PYODBC_AVAILABLE:
                tiempo = (time.time() - inicio) * 1000
                resultado = ResultadoValidacion(
                    nombre="DB2 Connection",
                    tipo=TipoValidacion.CONEXION_DB,
                    estado=EstadoValidacion.FALLIDO,
                    mensaje="No hay drivers DB2 disponibles (ibm_db o pyodbc)",
                    detalles=info,
                    tiempo_ms=tiempo
                )
                self._log(f"  {resultado.estado.value} Sin drivers DB2", "ERROR")
                self._agregar_resultado(resultado)
                return resultado

            # Si no hay credenciales configuradas y se pide conexión nativa
            if not usar_credenciales or not info.get('password_configured'):
                # Intentar conexión nativa (trust authentication o Kerberos)
                return self._intentar_conexion_nativa(info, inicio)

            # Intentar conexión con credenciales
            try:
                with DB2Connection() as db:
                    # Query de prueba
                    df = db.execute_query("SELECT 1 AS TEST FROM SYSIBM.SYSDUMMY1")

                    if not df.empty and df.iloc[0, 0] == 1:
                        tiempo = (time.time() - inicio) * 1000

                        # Obtener info adicional del servidor
                        server_info = db.get_server_info()

                        resultado = ResultadoValidacion(
                            nombre="DB2 Connection",
                            tipo=TipoValidacion.CONEXION_DB,
                            estado=EstadoValidacion.EXITOSO,
                            mensaje=f"Conexión exitosa a {DB_CONFIG['host']}",
                            detalles={
                                **info,
                                'server_info': server_info,
                                'stats': db.get_stats()
                            },
                            tiempo_ms=tiempo
                        )
                        self._log(f"  {resultado.estado.value} Conectado a {DB_CONFIG['host']}", "SUCCESS")
                    else:
                        raise Exception("Query de prueba no retornó resultado esperado")

            except Exception as e:
                tiempo = (time.time() - inicio) * 1000
                resultado = ResultadoValidacion(
                    nombre="DB2 Connection",
                    tipo=TipoValidacion.CONEXION_DB,
                    estado=EstadoValidacion.FALLIDO,
                    mensaje=f"Error de conexión: {str(e)[:100]}",
                    detalles={**info, 'error': str(e)},
                    tiempo_ms=tiempo
                )
                self._log(f"  {resultado.estado.value} {str(e)[:60]}", "ERROR")

        except ImportError as e:
            tiempo = (time.time() - inicio) * 1000
            resultado = ResultadoValidacion(
                nombre="DB2 Connection",
                tipo=TipoValidacion.CONEXION_DB,
                estado=EstadoValidacion.FALLIDO,
                mensaje=f"Error importando módulo: {str(e)}",
                detalles={'error': str(e)},
                tiempo_ms=tiempo
            )
            self._log(f"  {resultado.estado.value} {str(e)}", "ERROR")

        self._agregar_resultado(resultado)
        return resultado

    def _intentar_conexion_nativa(self, info: Dict, inicio: float) -> ResultadoValidacion:
        """
        Intenta conexión nativa a DB2 sin credenciales explícitas.

        Métodos soportados:
        1. Trust authentication (DB2 configurado para confiar en usuario OS)
        2. Kerberos (si está configurado)
        3. Variables de entorno del sistema
        4. IBM i (AS/400) con perfil de usuario
        """
        from config import DB_CONFIG

        metodos_intentados = []

        # Método 1: Trust authentication (vaciar UID/PWD)
        try:
            import ibm_db

            # Conexión trust (DB2 usa el usuario del sistema operativo)
            conn_string = (
                f"DATABASE={DB_CONFIG['database']};"
                f"HOSTNAME={DB_CONFIG['host']};"
                f"PORT={DB_CONFIG['port']};"
                f"PROTOCOL=TCPIP;"
                f"AUTHENTICATION=SERVER;"  # Trust authentication
            )

            conn = ibm_db.connect(conn_string, "", "")
            if conn:
                stmt = ibm_db.exec_immediate(conn, "SELECT 1 FROM SYSIBM.SYSDUMMY1")
                row = ibm_db.fetch_tuple(stmt)
                ibm_db.close(conn)

                if row and row[0] == 1:
                    tiempo = (time.time() - inicio) * 1000
                    resultado = ResultadoValidacion(
                        nombre="DB2 Connection (Native)",
                        tipo=TipoValidacion.CONEXION_DB,
                        estado=EstadoValidacion.EXITOSO,
                        mensaje="Conexión nativa exitosa (Trust Authentication)",
                        detalles={**info, 'metodo': 'trust_authentication'},
                        tiempo_ms=tiempo
                    )
                    self._log(f"  {resultado.estado.value} Conexión nativa (Trust Auth)", "SUCCESS")
                    return resultado

        except Exception as e:
            metodos_intentados.append(('trust_auth', str(e)))

        # Método 2: Kerberos
        try:
            import ibm_db

            conn_string = (
                f"DATABASE={DB_CONFIG['database']};"
                f"HOSTNAME={DB_CONFIG['host']};"
                f"PORT={DB_CONFIG['port']};"
                f"PROTOCOL=TCPIP;"
                f"AUTHENTICATION=KERBEROS;"
            )

            conn = ibm_db.connect(conn_string, "", "")
            if conn:
                stmt = ibm_db.exec_immediate(conn, "SELECT 1 FROM SYSIBM.SYSDUMMY1")
                row = ibm_db.fetch_tuple(stmt)
                ibm_db.close(conn)

                if row and row[0] == 1:
                    tiempo = (time.time() - inicio) * 1000
                    resultado = ResultadoValidacion(
                        nombre="DB2 Connection (Native)",
                        tipo=TipoValidacion.CONEXION_DB,
                        estado=EstadoValidacion.EXITOSO,
                        mensaje="Conexión nativa exitosa (Kerberos)",
                        detalles={**info, 'metodo': 'kerberos'},
                        tiempo_ms=tiempo
                    )
                    self._log(f"  {resultado.estado.value} Conexión nativa (Kerberos)", "SUCCESS")
                    return resultado

        except Exception as e:
            metodos_intentados.append(('kerberos', str(e)))

        # Método 3: Variables de entorno del sistema (DB2INSTANCE, etc.)
        try:
            import ibm_db

            # Verificar si hay configuración de instancia DB2
            db2_instance = os.environ.get('DB2INSTANCE')
            if db2_instance:
                # Conexión usando instancia local
                conn_string = f"DATABASE={DB_CONFIG['database']};"
                conn = ibm_db.connect(conn_string, "", "")
                if conn:
                    stmt = ibm_db.exec_immediate(conn, "SELECT 1 FROM SYSIBM.SYSDUMMY1")
                    row = ibm_db.fetch_tuple(stmt)
                    ibm_db.close(conn)

                    if row and row[0] == 1:
                        tiempo = (time.time() - inicio) * 1000
                        resultado = ResultadoValidacion(
                            nombre="DB2 Connection (Native)",
                            tipo=TipoValidacion.CONEXION_DB,
                            estado=EstadoValidacion.EXITOSO,
                            mensaje=f"Conexión nativa exitosa (DB2INSTANCE={db2_instance})",
                            detalles={**info, 'metodo': 'db2_instance', 'instance': db2_instance},
                            tiempo_ms=tiempo
                        )
                        self._log(f"  {resultado.estado.value} Conexión nativa (Instance)", "SUCCESS")
                        return resultado

        except Exception as e:
            metodos_intentados.append(('db2_instance', str(e)))

        # Método 4: pyodbc con DSN (Data Source Name)
        try:
            import pyodbc

            # Intentar con DSN si existe
            dsn_name = DB_CONFIG.get('dsn', DB_CONFIG['database'])
            conn = pyodbc.connect(f"DSN={dsn_name};", autocommit=True)
            if conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM SYSIBM.SYSDUMMY1")
                row = cursor.fetchone()
                conn.close()

                if row and row[0] == 1:
                    tiempo = (time.time() - inicio) * 1000
                    resultado = ResultadoValidacion(
                        nombre="DB2 Connection (Native)",
                        tipo=TipoValidacion.CONEXION_DB,
                        estado=EstadoValidacion.EXITOSO,
                        mensaje=f"Conexión nativa exitosa (DSN={dsn_name})",
                        detalles={**info, 'metodo': 'dsn', 'dsn': dsn_name},
                        tiempo_ms=tiempo
                    )
                    self._log(f"  {resultado.estado.value} Conexión nativa (DSN)", "SUCCESS")
                    return resultado

        except Exception as e:
            metodos_intentados.append(('dsn', str(e)))

        # Ningún método funcionó
        tiempo = (time.time() - inicio) * 1000
        resultado = ResultadoValidacion(
            nombre="DB2 Connection (Native)",
            tipo=TipoValidacion.CONEXION_DB,
            estado=EstadoValidacion.ADVERTENCIA,
            mensaje="Conexión nativa no disponible - Se requieren credenciales",
            detalles={
                **info,
                'metodos_intentados': metodos_intentados,
                'sugerencia': 'Configure DB_USER y DB_PASSWORD en .env o configure Trust Auth en DB2'
            },
            tiempo_ms=tiempo
        )
        self._log(f"  {resultado.estado.value} Conexión nativa no disponible", "WARNING")
        return resultado

    # =========================================================================
    # VALIDACIÓN DE SISTEMA DE ARCHIVOS
    # =========================================================================

    def validar_filesystem(self) -> List[ResultadoValidacion]:
        """Valida la estructura del sistema de archivos"""
        self._log("\n" + "="*60)
        self._log("📁 VALIDANDO SISTEMA DE ARCHIVOS")
        self._log("="*60)

        resultados = []

        directorios_requeridos = [
            ('output', BASE_DIR / 'output'),
            ('output/logs', BASE_DIR / 'output' / 'logs'),
            ('output/resultados', BASE_DIR / 'output' / 'resultados'),
            ('modules', BASE_DIR / 'modules'),
            ('queries', BASE_DIR / 'queries'),
            ('config', BASE_DIR / 'config'),
            ('docs', BASE_DIR / 'docs'),
        ]

        archivos_requeridos = [
            ('config.py', BASE_DIR / 'config.py'),
            ('main.py', BASE_DIR / 'main.py'),
            ('monitor.py', BASE_DIR / 'monitor.py'),
            ('requirements.txt', BASE_DIR / 'requirements.txt'),
            ('.env', BASE_DIR / '.env'),
        ]

        # Validar directorios
        for nombre, path in directorios_requeridos:
            inicio = time.time()

            if path.exists() and path.is_dir():
                estado = EstadoValidacion.EXITOSO
                mensaje = "Directorio existe"
                # Contar archivos
                try:
                    archivos = list(path.glob('*'))
                    detalles = {'path': str(path), 'archivos': len(archivos)}
                except Exception:
                    detalles = {'path': str(path)}
            else:
                estado = EstadoValidacion.FALLIDO
                mensaje = "Directorio no existe"
                detalles = {'path': str(path)}

            tiempo = (time.time() - inicio) * 1000
            resultado = ResultadoValidacion(
                nombre=f"Dir: {nombre}",
                tipo=TipoValidacion.FILESYSTEM,
                estado=estado,
                mensaje=mensaje,
                detalles=detalles,
                tiempo_ms=tiempo
            )

            self._log(f"  {resultado.estado.value} {nombre}/", "SUCCESS" if estado == EstadoValidacion.EXITOSO else "ERROR")
            resultados.append(resultado)
            self._agregar_resultado(resultado)

        # Validar archivos
        for nombre, path in archivos_requeridos:
            inicio = time.time()

            if path.exists() and path.is_file():
                estado = EstadoValidacion.EXITOSO
                mensaje = f"Archivo existe ({path.stat().st_size} bytes)"
                detalles = {'path': str(path), 'size': path.stat().st_size}
            elif nombre == '.env':
                # .env es opcional pero recomendado
                estado = EstadoValidacion.ADVERTENCIA
                mensaje = "Archivo no existe - Crear desde 'env' template"
                detalles = {'path': str(path), 'sugerencia': 'cp env .env'}
            else:
                estado = EstadoValidacion.FALLIDO
                mensaje = "Archivo no existe"
                detalles = {'path': str(path)}

            tiempo = (time.time() - inicio) * 1000
            resultado = ResultadoValidacion(
                nombre=f"File: {nombre}",
                tipo=TipoValidacion.FILESYSTEM,
                estado=estado,
                mensaje=mensaje,
                detalles=detalles,
                tiempo_ms=tiempo
            )

            nivel = "SUCCESS" if estado == EstadoValidacion.EXITOSO else ("WARNING" if estado == EstadoValidacion.ADVERTENCIA else "ERROR")
            self._log(f"  {resultado.estado.value} {nombre}", nivel)
            resultados.append(resultado)
            self._agregar_resultado(resultado)

        return resultados

    # =========================================================================
    # VALIDACIÓN DE INTERCONEXIONES
    # =========================================================================

    def validar_interconexiones(self) -> List[ResultadoValidacion]:
        """Valida las interconexiones entre módulos"""
        self._log("\n" + "="*60)
        self._log("🔗 VALIDANDO INTERCONEXIONES ENTRE MÓDULOS")
        self._log("="*60)

        resultados = []

        # Pruebas de interconexión
        pruebas = [
            ('config -> db_connection', self._test_config_to_db),
            ('config -> email', self._test_config_to_email),
            ('config -> modules', self._test_config_to_modules),
            ('modules -> repositories', self._test_modules_to_repos),
            ('modules -> validators', self._test_modules_to_validators),
            ('monitor -> alertas', self._test_monitor_to_alertas),
            ('queries -> db_connection', self._test_queries_to_db),
        ]

        for nombre, test_func in pruebas:
            resultado = test_func(nombre)
            resultados.append(resultado)
            self._agregar_resultado(resultado)

        return resultados

    def _test_config_to_db(self, nombre: str) -> ResultadoValidacion:
        """Prueba interconexión config -> db_connection"""
        inicio = time.time()

        try:
            from config import DB_CONFIG
            from modules.db_connection import DB2Connection, get_connection_info

            info = get_connection_info()

            # Verificar que db_connection use la configuración correcta
            if info['host'] == DB_CONFIG['host'] and info['port'] == DB_CONFIG['port']:
                estado = EstadoValidacion.EXITOSO
                mensaje = "Configuración sincronizada correctamente"
            else:
                estado = EstadoValidacion.ADVERTENCIA
                mensaje = "Posible desincronización de configuración"

            tiempo = (time.time() - inicio) * 1000
            resultado = ResultadoValidacion(
                nombre=nombre,
                tipo=TipoValidacion.MODULO,
                estado=estado,
                mensaje=mensaje,
                detalles=info,
                tiempo_ms=tiempo
            )

        except Exception as e:
            tiempo = (time.time() - inicio) * 1000
            resultado = ResultadoValidacion(
                nombre=nombre,
                tipo=TipoValidacion.MODULO,
                estado=EstadoValidacion.FALLIDO,
                mensaje=str(e),
                tiempo_ms=tiempo
            )

        self._log(f"  {resultado.estado.value} {nombre}",
                 "SUCCESS" if resultado.estado == EstadoValidacion.EXITOSO else "ERROR")
        return resultado

    def _test_config_to_email(self, nombre: str) -> ResultadoValidacion:
        """Prueba interconexión config -> email"""
        inicio = time.time()

        try:
            from config import EMAIL_CONFIG

            # Verificar campos de email
            campos_requeridos = ['smtp_server', 'smtp_port', 'user', 'password']
            campos_presentes = all(EMAIL_CONFIG.get(c) for c in campos_requeridos)

            if campos_presentes:
                estado = EstadoValidacion.EXITOSO
                mensaje = f"Email configurado para {EMAIL_CONFIG['smtp_server']}"
            else:
                estado = EstadoValidacion.ADVERTENCIA
                mensaje = "Configuración de email incompleta"

            tiempo = (time.time() - inicio) * 1000
            resultado = ResultadoValidacion(
                nombre=nombre,
                tipo=TipoValidacion.MODULO,
                estado=estado,
                mensaje=mensaje,
                detalles={'smtp_server': EMAIL_CONFIG.get('smtp_server')},
                tiempo_ms=tiempo
            )

        except Exception as e:
            tiempo = (time.time() - inicio) * 1000
            resultado = ResultadoValidacion(
                nombre=nombre,
                tipo=TipoValidacion.MODULO,
                estado=EstadoValidacion.FALLIDO,
                mensaje=str(e),
                tiempo_ms=tiempo
            )

        self._log(f"  {resultado.estado.value} {nombre}",
                 "SUCCESS" if resultado.estado == EstadoValidacion.EXITOSO else "WARNING")
        return resultado

    def _test_config_to_modules(self, nombre: str) -> ResultadoValidacion:
        """Prueba interconexión config -> modules"""
        inicio = time.time()

        try:
            from config import VERSION
            from modules import __version__

            if VERSION == __version__:
                estado = EstadoValidacion.EXITOSO
                mensaje = f"Versión sincronizada: {VERSION}"
            else:
                estado = EstadoValidacion.ADVERTENCIA
                mensaje = f"Versiones diferentes: config={VERSION}, modules={__version__}"

            tiempo = (time.time() - inicio) * 1000
            resultado = ResultadoValidacion(
                nombre=nombre,
                tipo=TipoValidacion.MODULO,
                estado=estado,
                mensaje=mensaje,
                tiempo_ms=tiempo
            )

        except Exception as e:
            tiempo = (time.time() - inicio) * 1000
            resultado = ResultadoValidacion(
                nombre=nombre,
                tipo=TipoValidacion.MODULO,
                estado=EstadoValidacion.FALLIDO,
                mensaje=str(e),
                tiempo_ms=tiempo
            )

        self._log(f"  {resultado.estado.value} {nombre}",
                 "SUCCESS" if resultado.estado == EstadoValidacion.EXITOSO else "WARNING")
        return resultado

    def _test_modules_to_repos(self, nombre: str) -> ResultadoValidacion:
        """Prueba interconexión modules -> repositories"""
        inicio = time.time()

        try:
            from modules.repositories import (
                BaseRepository, OCRepository,
                DistributionRepository, ASNRepository
            )

            estado = EstadoValidacion.EXITOSO
            mensaje = "Repositorios disponibles"

            tiempo = (time.time() - inicio) * 1000
            resultado = ResultadoValidacion(
                nombre=nombre,
                tipo=TipoValidacion.MODULO,
                estado=estado,
                mensaje=mensaje,
                tiempo_ms=tiempo
            )

        except Exception as e:
            tiempo = (time.time() - inicio) * 1000
            resultado = ResultadoValidacion(
                nombre=nombre,
                tipo=TipoValidacion.MODULO,
                estado=EstadoValidacion.FALLIDO,
                mensaje=str(e),
                tiempo_ms=tiempo
            )

        self._log(f"  {resultado.estado.value} {nombre}",
                 "SUCCESS" if resultado.estado == EstadoValidacion.EXITOSO else "ERROR")
        return resultado

    def _test_modules_to_validators(self, nombre: str) -> ResultadoValidacion:
        """Prueba interconexión modules -> validators"""
        inicio = time.time()

        try:
            from modules.validators import (
                BaseValidator, OCValidator,
                DistributionValidator, ASNValidator
            )

            estado = EstadoValidacion.EXITOSO
            mensaje = "Validadores disponibles"

            tiempo = (time.time() - inicio) * 1000
            resultado = ResultadoValidacion(
                nombre=nombre,
                tipo=TipoValidacion.MODULO,
                estado=estado,
                mensaje=mensaje,
                tiempo_ms=tiempo
            )

        except Exception as e:
            tiempo = (time.time() - inicio) * 1000
            resultado = ResultadoValidacion(
                nombre=nombre,
                tipo=TipoValidacion.MODULO,
                estado=EstadoValidacion.FALLIDO,
                mensaje=str(e),
                tiempo_ms=tiempo
            )

        self._log(f"  {resultado.estado.value} {nombre}",
                 "SUCCESS" if resultado.estado == EstadoValidacion.EXITOSO else "ERROR")
        return resultado

    def _test_monitor_to_alertas(self, nombre: str) -> ResultadoValidacion:
        """Prueba interconexión monitor -> alertas"""
        inicio = time.time()

        try:
            from monitor import MonitorTiempoReal, ErrorSeverity
            from modules.modulo_alertas import GestorAlertas, TipoAlerta

            estado = EstadoValidacion.EXITOSO
            mensaje = "Sistema de monitoreo y alertas conectado"

            tiempo = (time.time() - inicio) * 1000
            resultado = ResultadoValidacion(
                nombre=nombre,
                tipo=TipoValidacion.MODULO,
                estado=estado,
                mensaje=mensaje,
                tiempo_ms=tiempo
            )

        except Exception as e:
            tiempo = (time.time() - inicio) * 1000
            resultado = ResultadoValidacion(
                nombre=nombre,
                tipo=TipoValidacion.MODULO,
                estado=EstadoValidacion.FALLIDO,
                mensaje=str(e),
                tiempo_ms=tiempo
            )

        self._log(f"  {resultado.estado.value} {nombre}",
                 "SUCCESS" if resultado.estado == EstadoValidacion.EXITOSO else "ERROR")
        return resultado

    def _test_queries_to_db(self, nombre: str) -> ResultadoValidacion:
        """Prueba interconexión queries -> db_connection"""
        inicio = time.time()

        try:
            from queries import QueryLoader, QueryCategory

            loader = QueryLoader()
            categorias = loader.listar_categorias()

            estado = EstadoValidacion.EXITOSO
            mensaje = f"QueryLoader disponible con {len(categorias)} categorías"

            tiempo = (time.time() - inicio) * 1000
            resultado = ResultadoValidacion(
                nombre=nombre,
                tipo=TipoValidacion.MODULO,
                estado=estado,
                mensaje=mensaje,
                detalles={'categorias': categorias},
                tiempo_ms=tiempo
            )

        except Exception as e:
            tiempo = (time.time() - inicio) * 1000
            resultado = ResultadoValidacion(
                nombre=nombre,
                tipo=TipoValidacion.MODULO,
                estado=EstadoValidacion.FALLIDO,
                mensaje=str(e),
                tiempo_ms=tiempo
            )

        self._log(f"  {resultado.estado.value} {nombre}",
                 "SUCCESS" if resultado.estado == EstadoValidacion.EXITOSO else "ERROR")
        return resultado

    # =========================================================================
    # EJECUCIÓN COMPLETA
    # =========================================================================

    def ejecutar_validacion_completa(self) -> ReporteValidacion:
        """
        Ejecuta todas las validaciones y genera el reporte completo

        Returns:
            ReporteValidacion con todos los resultados
        """
        self._log("\n" + "="*70)
        self._log("🔍 VALIDADOR DE CONEXIONES E INTERCONEXIONES - SAC CEDIS 427")
        self._log("="*70)
        self._log(f"   Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self._log(f"   Directorio: {BASE_DIR}")

        inicio_total = time.time()

        # 1. Validar sistema de archivos
        self.validar_filesystem()

        # 2. Validar dependencias externas
        self.validar_todas_dependencias()

        # 3. Validar configuración
        self._log("\n" + "="*60)
        self._log("⚙️ VALIDANDO CONFIGURACIÓN")
        self._log("="*60)
        self.validar_configuracion()

        # 4. Validar módulos
        self.validar_todos_modulos()

        # 5. Validar interconexiones
        self.validar_interconexiones()

        # 6. Validar conexión a base de datos
        self._log("\n" + "="*60)
        self._log("💾 VALIDANDO CONEXIÓN A BASE DE DATOS")
        self._log("="*60)

        if self.intentar_conexion_nativa:
            self._log("   Intentando conexión nativa (sin credenciales)...")
            self.validar_conexion_db(usar_credenciales=False)
        else:
            self.validar_conexion_db(usar_credenciales=True)

        # Finalizar reporte
        self.reporte.tiempo_total_ms = (time.time() - inicio_total) * 1000
        self.reporte.timestamp_fin = datetime.now().isoformat()

        try:
            from config import VERSION
            self.reporte.version_sistema = VERSION
        except Exception:
            self.reporte.version_sistema = "N/A"

        # Mostrar resumen
        self._mostrar_resumen()

        return self.reporte

    def _mostrar_resumen(self):
        """Muestra resumen del reporte"""
        self._log("\n" + "="*70)
        self._log("📊 RESUMEN DE VALIDACIÓN")
        self._log("="*70)

        r = self.reporte

        self._log(f"\n   Total validaciones: {r.total_validaciones}")
        self._log(f"   ✅ Exitosos:        {r.exitosos} ({r.exitosos/r.total_validaciones*100:.1f}%)", "SUCCESS")
        self._log(f"   ❌ Fallidos:        {r.fallidos} ({r.fallidos/r.total_validaciones*100:.1f}%)", "ERROR")
        self._log(f"   ⚠️  Advertencias:    {r.advertencias}", "WARNING")
        self._log(f"   ⏭️  Omitidos:        {r.omitidos}")
        self._log(f"\n   Tiempo total:       {r.tiempo_total_ms:.1f}ms")
        self._log(f"   Versión SAC:        {r.version_sistema}")

        # Mostrar errores críticos
        fallidos = [r for r in self.reporte.resultados if r.estado == EstadoValidacion.FALLIDO]
        if fallidos:
            self._log("\n" + "-"*60)
            self._log("❌ ERRORES QUE REQUIEREN ATENCIÓN:", "ERROR")
            for f in fallidos[:10]:
                self._log(f"   • {f.nombre}: {f.mensaje[:60]}", "ERROR")

        # Estado general
        self._log("\n" + "="*70)
        if r.fallidos == 0:
            self._log("🎉 SISTEMA VALIDADO CORRECTAMENTE", "SUCCESS")
        elif r.fallidos <= 3:
            self._log("⚠️  SISTEMA CON ADVERTENCIAS MENORES", "WARNING")
        else:
            self._log("❌ SISTEMA CON ERRORES - REVISAR CONFIGURACIÓN", "ERROR")
        self._log("="*70 + "\n")

    def guardar_reporte(self, archivo: str = None) -> str:
        """
        Guarda el reporte en formato JSON

        Args:
            archivo: Ruta del archivo (opcional)

        Returns:
            Ruta del archivo guardado
        """
        if archivo is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            archivo = BASE_DIR / 'output' / 'logs' / f'validacion_{timestamp}.json'

        # Convertir a diccionario serializable
        reporte_dict = {
            'total_validaciones': self.reporte.total_validaciones,
            'exitosos': self.reporte.exitosos,
            'fallidos': self.reporte.fallidos,
            'advertencias': self.reporte.advertencias,
            'omitidos': self.reporte.omitidos,
            'tiempo_total_ms': self.reporte.tiempo_total_ms,
            'timestamp_inicio': self.reporte.timestamp_inicio,
            'timestamp_fin': self.reporte.timestamp_fin,
            'version_sistema': self.reporte.version_sistema,
            'resultados': [
                {
                    'nombre': r.nombre,
                    'tipo': r.tipo.value,
                    'estado': r.estado.value,
                    'mensaje': r.mensaje,
                    'detalles': r.detalles,
                    'tiempo_ms': r.tiempo_ms,
                    'timestamp': r.timestamp,
                }
                for r in self.reporte.resultados
            ]
        }

        Path(archivo).parent.mkdir(parents=True, exist_ok=True)

        with open(archivo, 'w', encoding='utf-8') as f:
            json.dump(reporte_dict, f, indent=2, ensure_ascii=False)

        self._log(f"\n📄 Reporte guardado en: {archivo}")
        return str(archivo)


# ===============================================================================
# FUNCIONES DE CONVENIENCIA
# ===============================================================================

def validar_sistema(verbose: bool = True, conexion_nativa: bool = True) -> ReporteValidacion:
    """
    Función de conveniencia para validar todo el sistema

    Args:
        verbose: Mostrar detalles en consola
        conexion_nativa: Intentar conexión DB sin credenciales

    Returns:
        ReporteValidacion con resultados
    """
    validador = ValidadorConexiones(
        modo_verbose=verbose,
        intentar_conexion_nativa=conexion_nativa
    )
    return validador.ejecutar_validacion_completa()


def validar_modulos_solamente(verbose: bool = True) -> List[ResultadoValidacion]:
    """Valida solo los módulos (sin conexión DB)"""
    validador = ValidadorConexiones(modo_verbose=verbose)
    validador.validar_todas_dependencias()
    return validador.validar_todos_modulos()


def validar_conexion_db_nativa() -> ResultadoValidacion:
    """Intenta conexión nativa a DB2"""
    validador = ValidadorConexiones(modo_verbose=True, intentar_conexion_nativa=True)
    return validador.validar_conexion_db(usar_credenciales=False)


# ===============================================================================
# PUNTO DE ENTRADA
# ===============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description='Validador de conexiones e interconexiones del Sistema SAC'
    )
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Modo silencioso (sin output detallado)'
    )
    parser.add_argument(
        '--no-db',
        action='store_true',
        help='Omitir validación de base de datos'
    )
    parser.add_argument(
        '--native-only',
        action='store_true',
        help='Solo intentar conexión nativa (sin credenciales)'
    )
    parser.add_argument(
        '--save', '-s',
        action='store_true',
        help='Guardar reporte en archivo JSON'
    )
    parser.add_argument(
        '--modules-only',
        action='store_true',
        help='Solo validar módulos (sin conexión DB)'
    )

    args = parser.parse_args()

    if args.modules_only:
        validar_modulos_solamente(verbose=not args.quiet)
    else:
        validador = ValidadorConexiones(
            modo_verbose=not args.quiet,
            intentar_conexion_nativa=not args.no_db
        )

        reporte = validador.ejecutar_validacion_completa()

        if args.save:
            validador.guardar_reporte()

        # Exit code basado en resultado
        sys.exit(0 if reporte.fallidos == 0 else 1)
