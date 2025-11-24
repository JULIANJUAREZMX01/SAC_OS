"""
═══════════════════════════════════════════════════════════════
MÓDULO DE CONEXIÓN A BASE DE DATOS DB2
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Este módulo proporciona la conexión a IBM DB2 (Manhattan WMS) con:
- Retry logic con backoff exponencial
- Connection pooling
- Context manager para manejo automático de conexiones
- Ejecución de queries con retorno de DataFrame

Uso:
    from modules.db_connection import DB2Connection

    # Uso básico
    with DB2Connection() as db:
        df = db.execute_query("SELECT * FROM tabla")

    # Uso con configuración personalizada
    db = DB2Connection(config=custom_config)
    db.connect()
    df = db.execute_query("SELECT * FROM tabla", params=('valor',))
    db.disconnect()

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
═══════════════════════════════════════════════════════════════
"""

import os
import logging
import time
from typing import Optional, Dict, List, Tuple, Any, Union
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from queue import Queue, Empty
from threading import Lock
import pandas as pd

# Intentar importar drivers de DB2
try:
    import pyodbc
    PYODBC_AVAILABLE = True
except ImportError:
    PYODBC_AVAILABLE = False

try:
    import ibm_db
    import ibm_db_dbi
    IBM_DB_AVAILABLE = True
except ImportError:
    IBM_DB_AVAILABLE = False

# Importar configuración
try:
    from config import DB_CONFIG, DB_CONNECTION_STRING, SYSTEM_CONFIG
except ImportError:
    DB_CONFIG = {}
    DB_CONNECTION_STRING = ""
    SYSTEM_CONFIG = {'debug': False}

# ═══════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE LOGGING
# ═══════════════════════════════════════════════════════════════

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# ENUMS Y DATA CLASSES
# ═══════════════════════════════════════════════════════════════

class ConnectionDriver(Enum):
    """Drivers disponibles para conexión a DB2"""
    PYODBC = "pyodbc"
    IBM_DB = "ibm_db"
    AUTO = "auto"


class ConnectionStatus(Enum):
    """Estados posibles de la conexión"""
    DISCONNECTED = "desconectado"
    CONNECTED = "conectado"
    ERROR = "error"
    CONNECTING = "conectando"


@dataclass
class ConnectionStats:
    """Estadísticas de conexión"""
    total_connections: int = 0
    successful_connections: int = 0
    failed_connections: int = 0
    total_queries: int = 0
    successful_queries: int = 0
    failed_queries: int = 0
    total_retry_attempts: int = 0
    last_connection_time: Optional[datetime] = None
    last_query_time: Optional[datetime] = None
    last_error: Optional[str] = None


@dataclass
class QueryResult:
    """Resultado de una consulta"""
    success: bool
    data: Optional[pd.DataFrame] = None
    rows_affected: int = 0
    execution_time: float = 0.0
    error_message: Optional[str] = None


# ═══════════════════════════════════════════════════════════════
# EXCEPCIONES PERSONALIZADAS
# ═══════════════════════════════════════════════════════════════

class DB2ConnectionError(Exception):
    """Error de conexión a DB2"""
    pass


class DB2QueryError(Exception):
    """Error al ejecutar query"""
    pass


class DB2ConfigurationError(Exception):
    """Error de configuración"""
    pass


class DB2PoolExhaustedError(Exception):
    """Pool de conexiones agotado"""
    pass


# ═══════════════════════════════════════════════════════════════
# CLASE PRINCIPAL DE CONEXIÓN
# ═══════════════════════════════════════════════════════════════

class DB2Connection:
    """
    Clase para gestionar conexiones a IBM DB2 (Manhattan WMS)

    Características:
    - Soporte para pyodbc e ibm_db
    - Retry automático con backoff exponencial
    - Context manager para uso con 'with'
    - Ejecución de queries con retorno de DataFrame
    - Logging detallado de operaciones

    Ejemplo de uso:
        >>> with DB2Connection() as db:
        ...     df = db.execute_query("SELECT * FROM WMWHSE1.SKU")
        ...     print(df.head())
    """

    # Configuración por defecto de retry
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_BASE_DELAY = 2.0  # segundos
    DEFAULT_MAX_DELAY = 30.0  # segundos

    def __init__(
        self,
        config: Optional[Dict] = None,
        driver: ConnectionDriver = ConnectionDriver.AUTO,
        max_retries: int = DEFAULT_MAX_RETRIES,
        base_delay: float = DEFAULT_BASE_DELAY,
        max_delay: float = DEFAULT_MAX_DELAY,
        auto_connect: bool = False
    ):
        """
        Inicializa la conexión a DB2

        Args:
            config: Diccionario de configuración (usa DB_CONFIG por defecto)
            driver: Driver a utilizar (pyodbc, ibm_db o auto)
            max_retries: Número máximo de reintentos
            base_delay: Delay base para backoff exponencial (segundos)
            max_delay: Delay máximo para backoff (segundos)
            auto_connect: Si es True, conecta automáticamente
        """
        self.config = config or DB_CONFIG
        self.driver_type = driver
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay

        # Estado de la conexión
        self.connection = None
        self.cursor = None
        self.status = ConnectionStatus.DISCONNECTED
        self.stats = ConnectionStats()

        # Seleccionar driver
        self._selected_driver = self._select_driver()

        # Validar configuración
        self._validate_config()

        logger.info(f"💾 DB2Connection inicializado - Driver: {self._selected_driver}")

        if auto_connect:
            self.connect()

    def _select_driver(self) -> str:
        """
        Selecciona el driver a utilizar

        Returns:
            Nombre del driver seleccionado

        Raises:
            DB2ConfigurationError: Si no hay drivers disponibles
        """
        if self.driver_type == ConnectionDriver.AUTO:
            # Preferir ibm_db sobre pyodbc porque pyodbc requiere
            # IBM DB2 ODBC Driver instalado en el sistema operativo
            if IBM_DB_AVAILABLE:
                return "ibm_db"
            elif PYODBC_AVAILABLE:
                return "pyodbc"
            else:
                raise DB2ConfigurationError(
                    "❌ No hay drivers DB2 disponibles. "
                    "Instala ibm-db: pip install ibm-db"
                )
        elif self.driver_type == ConnectionDriver.PYODBC:
            if not PYODBC_AVAILABLE:
                raise DB2ConfigurationError(
                    "❌ pyodbc no está instalado. "
                    "Instala con: pip install pyodbc"
                )
            return "pyodbc"
        elif self.driver_type == ConnectionDriver.IBM_DB:
            if not IBM_DB_AVAILABLE:
                raise DB2ConfigurationError(
                    "❌ ibm-db no está instalado. "
                    "Instala con: pip install ibm-db"
                )
            return "ibm_db"

        return "pyodbc"  # Default

    def _validate_config(self) -> None:
        """
        Valida la configuración de conexión

        Raises:
            DB2ConfigurationError: Si la configuración es inválida
        """
        required_fields = ['host', 'port', 'database', 'user', 'password']
        missing = [f for f in required_fields if not self.config.get(f)]

        if missing:
            raise DB2ConfigurationError(
                f"❌ Campos de configuración faltantes: {', '.join(missing)}. "
                f"Configura estos valores en el archivo .env"
            )

        # Validar valores placeholder
        if self.config.get('user') == 'tu_usuario':
            logger.warning("⚠️  DB_USER tiene valor placeholder. Configura .env")

        if self.config.get('password') == 'tu_password':
            logger.warning("⚠️  DB_PASSWORD tiene valor placeholder. Configura .env")

    def _build_connection_string(self, native_mode: bool = False) -> str:
        """
        Construye el string de conexión según el driver

        Args:
            native_mode: Si True, intenta conexión sin credenciales (como DBeaver)

        Returns:
            String de conexión formateado
        """
        # Verificar si hay credenciales válidas
        user = self.config.get('user', '')
        password = self.config.get('password', '')
        has_credentials = user and password and user not in ['tu_usuario', ''] and password not in ['tu_password', '']

        if self._selected_driver == "pyodbc":
            # Verificar si hay DSN configurado
            dsn = self.config.get('dsn')
            if dsn and (native_mode or not has_credentials):
                # Conexión mediante DSN (como DBeaver guarda conexiones)
                conn_str = f"DSN={dsn};"
                logger.info("🔗 Usando conexión DSN (nativa)")
            elif native_mode or not has_credentials:
                # Conexión trust/nativa sin credenciales
                conn_str = (
                    f"DRIVER={self.config.get('driver', '{IBM DB2 ODBC DRIVER}')};"
                    f"HOSTNAME={self.config['host']};"
                    f"PORT={self.config['port']};"
                    f"DATABASE={self.config['database']};"
                    f"CONNECTTIMEOUT={self.config.get('timeout', 30)};"
                    f"Trusted_Connection=Yes;"
                )
                logger.info("🔗 Intentando conexión trusted (sin credenciales)")
            else:
                # Formato ODBC estándar con credenciales
                conn_str = (
                    f"DRIVER={self.config.get('driver', '{IBM DB2 ODBC DRIVER}')};"
                    f"HOSTNAME={self.config['host']};"
                    f"PORT={self.config['port']};"
                    f"DATABASE={self.config['database']};"
                    f"UID={user};"
                    f"PWD={password};"
                    f"CONNECTTIMEOUT={self.config.get('timeout', 30)};"
                )
        else:
            # Formato para ibm_db
            if native_mode or not has_credentials:
                # Conexión nativa ibm_db (trust authentication)
                conn_str = (
                    f"DATABASE={self.config['database']};"
                    f"HOSTNAME={self.config['host']};"
                    f"PORT={self.config['port']};"
                    f"PROTOCOL=TCPIP;"
                    f"AUTHENTICATION=SERVER;"
                )
                logger.info("🔗 Intentando conexión nativa ibm_db (trust auth)")
            else:
                # Formato estándar con credenciales
                conn_str = (
                    f"DATABASE={self.config['database']};"
                    f"HOSTNAME={self.config['host']};"
                    f"PORT={self.config['port']};"
                    f"PROTOCOL=TCPIP;"
                    f"UID={user};"
                    f"PWD={password};"
                )

        return conn_str

    def _calculate_delay(self, attempt: int) -> float:
        """
        Calcula el delay para backoff exponencial

        Args:
            attempt: Número de intento (0-indexed)

        Returns:
            Delay en segundos
        """
        delay = self.base_delay * (2 ** attempt)
        return min(delay, self.max_delay)

    def connect(self) -> bool:
        """
        Establece conexión a DB2 con retry logic

        Returns:
            True si la conexión fue exitosa

        Raises:
            DB2ConnectionError: Si no se puede establecer conexión
        """
        if self.status == ConnectionStatus.CONNECTED and self.connection:
            logger.debug("✅ Ya conectado a DB2")
            return True

        self.status = ConnectionStatus.CONNECTING
        self.stats.total_connections += 1

        connection_string = self._build_connection_string()

        for attempt in range(self.max_retries):
            try:
                logger.info(f"🔌 Conectando a DB2 (intento {attempt + 1}/{self.max_retries})...")

                if self._selected_driver == "pyodbc":
                    self.connection = pyodbc.connect(
                        connection_string,
                        timeout=self.config.get('timeout', 30)
                    )
                    self.cursor = self.connection.cursor()
                else:
                    # ibm_db
                    self.connection = ibm_db.connect(connection_string, "", "")
                    self.cursor = None  # ibm_db usa exec_immediate

                self.status = ConnectionStatus.CONNECTED
                self.stats.successful_connections += 1
                self.stats.last_connection_time = datetime.now()

                logger.info(f"✅ Conexión a DB2 establecida exitosamente")
                logger.info(f"   📍 Host: {self.config['host']}")
                logger.info(f"   📍 Database: {self.config['database']}")
                logger.info(f"   📍 Usuario: {self.config['user']}")

                return True

            except Exception as e:
                self.stats.total_retry_attempts += 1
                error_msg = str(e)
                self.stats.last_error = error_msg

                logger.warning(
                    f"⚠️  Intento {attempt + 1} fallido: {error_msg[:100]}..."
                )

                if attempt < self.max_retries - 1:
                    delay = self._calculate_delay(attempt)
                    logger.info(f"⏳ Esperando {delay:.1f}s antes del siguiente intento...")
                    time.sleep(delay)

        # Todos los intentos fallaron
        self.status = ConnectionStatus.ERROR
        self.stats.failed_connections += 1

        error_message = (
            f"❌ No se pudo conectar a DB2 después de {self.max_retries} intentos. "
            f"Último error: {self.stats.last_error}"
        )
        logger.error(error_message)
        raise DB2ConnectionError(error_message)

    def disconnect(self) -> bool:
        """
        Cierra la conexión a DB2

        Returns:
            True si se cerró correctamente
        """
        try:
            if self.cursor:
                if self._selected_driver == "pyodbc":
                    self.cursor.close()
                self.cursor = None

            if self.connection:
                if self._selected_driver == "pyodbc":
                    self.connection.close()
                else:
                    ibm_db.close(self.connection)
                self.connection = None

            self.status = ConnectionStatus.DISCONNECTED
            logger.info("🔌 Conexión a DB2 cerrada")
            return True

        except Exception as e:
            logger.error(f"❌ Error al cerrar conexión: {str(e)}")
            self.status = ConnectionStatus.DISCONNECTED
            return False

    def is_connected(self) -> bool:
        """
        Verifica si la conexión está activa

        Returns:
            True si está conectado
        """
        if self.status != ConnectionStatus.CONNECTED:
            return False

        if not self.connection:
            return False

        # Verificar conexión con query simple
        try:
            if self._selected_driver == "pyodbc":
                self.cursor.execute("SELECT 1 FROM SYSIBM.SYSDUMMY1")
                self.cursor.fetchone()
            else:
                stmt = ibm_db.exec_immediate(
                    self.connection,
                    "SELECT 1 FROM SYSIBM.SYSDUMMY1"
                )
                ibm_db.fetch_row(stmt)
            return True
        except Exception:
            self.status = ConnectionStatus.ERROR
            return False

    def execute_query(
        self,
        sql: str,
        params: Optional[Tuple] = None,
        fetch_as_df: bool = True
    ) -> Union[pd.DataFrame, QueryResult]:
        """
        Ejecuta una consulta SQL y retorna los resultados

        Args:
            sql: Consulta SQL a ejecutar
            params: Parámetros para la consulta (tupla)
            fetch_as_df: Si True, retorna DataFrame; si False, retorna QueryResult

        Returns:
            DataFrame con resultados o QueryResult

        Raises:
            DB2QueryError: Si hay error en la ejecución
        """
        if self.status != ConnectionStatus.CONNECTED:
            if not self.connect():
                raise DB2QueryError("❌ No hay conexión activa a DB2")

        self.stats.total_queries += 1
        start_time = time.time()

        try:
            logger.debug(f"🔍 Ejecutando query: {sql[:100]}...")

            if self._selected_driver == "pyodbc":
                if params:
                    self.cursor.execute(sql, params)
                else:
                    self.cursor.execute(sql)

                # Obtener resultados
                columns = [desc[0] for desc in self.cursor.description] if self.cursor.description else []
                rows = self.cursor.fetchall()

            else:
                # ibm_db
                if params:
                    stmt = ibm_db.prepare(self.connection, sql)
                    ibm_db.execute(stmt, params)
                else:
                    stmt = ibm_db.exec_immediate(self.connection, sql)

                # Obtener columnas
                columns = []
                col_count = ibm_db.num_fields(stmt)
                for i in range(col_count):
                    columns.append(ibm_db.field_name(stmt, i))

                # Obtener filas
                rows = []
                row = ibm_db.fetch_tuple(stmt)
                while row:
                    rows.append(row)
                    row = ibm_db.fetch_tuple(stmt)

            execution_time = time.time() - start_time
            self.stats.successful_queries += 1
            self.stats.last_query_time = datetime.now()

            logger.info(f"✅ Query ejecutada: {len(rows)} filas en {execution_time:.2f}s")

            # Crear DataFrame
            df = pd.DataFrame(rows, columns=columns) if rows else pd.DataFrame(columns=columns)

            if fetch_as_df:
                return df
            else:
                return QueryResult(
                    success=True,
                    data=df,
                    rows_affected=len(rows),
                    execution_time=execution_time
                )

        except Exception as e:
            execution_time = time.time() - start_time
            self.stats.failed_queries += 1
            self.stats.last_error = str(e)

            error_message = f"❌ Error ejecutando query: {str(e)}"
            logger.error(error_message)

            if fetch_as_df:
                raise DB2QueryError(error_message) from e
            else:
                return QueryResult(
                    success=False,
                    execution_time=execution_time,
                    error_message=str(e)
                )

    def execute_many(
        self,
        sql: str,
        params_list: List[Tuple]
    ) -> QueryResult:
        """
        Ejecuta una consulta múltiples veces con diferentes parámetros

        Args:
            sql: Consulta SQL con placeholders
            params_list: Lista de tuplas con parámetros

        Returns:
            QueryResult con información de la ejecución
        """
        if self.status != ConnectionStatus.CONNECTED:
            if not self.connect():
                raise DB2QueryError("❌ No hay conexión activa a DB2")

        start_time = time.time()
        rows_affected = 0

        try:
            logger.info(f"📊 Ejecutando batch de {len(params_list)} operaciones...")

            if self._selected_driver == "pyodbc":
                self.cursor.executemany(sql, params_list)
                rows_affected = self.cursor.rowcount
                self.connection.commit()
            else:
                # ibm_db - ejecutar uno por uno
                stmt = ibm_db.prepare(self.connection, sql)
                for params in params_list:
                    ibm_db.execute(stmt, params)
                    rows_affected += 1
                ibm_db.commit(self.connection)

            execution_time = time.time() - start_time

            logger.info(f"✅ Batch ejecutado: {rows_affected} operaciones en {execution_time:.2f}s")

            return QueryResult(
                success=True,
                rows_affected=rows_affected,
                execution_time=execution_time
            )

        except Exception as e:
            execution_time = time.time() - start_time
            error_message = str(e)

            # Intentar rollback
            try:
                if self._selected_driver == "pyodbc":
                    self.connection.rollback()
                else:
                    ibm_db.rollback(self.connection)
            except Exception:
                pass

            logger.error(f"❌ Error en batch: {error_message}")

            return QueryResult(
                success=False,
                rows_affected=rows_affected,
                execution_time=execution_time,
                error_message=error_message
            )

    def execute_scalar(self, sql: str, params: Optional[Tuple] = None) -> Any:
        """
        Ejecuta una consulta y retorna un único valor

        Args:
            sql: Consulta SQL
            params: Parámetros opcionales

        Returns:
            Valor escalar del resultado
        """
        df = self.execute_query(sql, params)
        if df.empty:
            return None
        return df.iloc[0, 0]

    def execute_non_query(
        self,
        sql: str,
        params: Optional[Tuple] = None,
        auto_commit: bool = True
    ) -> int:
        """
        Ejecuta una consulta que no retorna resultados (INSERT, UPDATE, DELETE)

        Args:
            sql: Consulta SQL a ejecutar
            params: Parámetros para la consulta
            auto_commit: Si True, hace commit automático

        Returns:
            Número de filas afectadas

        Raises:
            DB2QueryError: Si hay error en la ejecución
        """
        if self.status != ConnectionStatus.CONNECTED:
            if not self.connect():
                raise DB2QueryError("❌ No hay conexión activa a DB2")

        self.stats.total_queries += 1
        start_time = time.time()

        try:
            logger.debug(f"🔧 Ejecutando non-query: {sql[:100]}...")

            if self._selected_driver == "pyodbc":
                if params:
                    self.cursor.execute(sql, params)
                else:
                    self.cursor.execute(sql)
                rows_affected = self.cursor.rowcount

                if auto_commit:
                    self.connection.commit()
            else:
                # ibm_db
                if params:
                    stmt = ibm_db.prepare(self.connection, sql)
                    ibm_db.execute(stmt, params)
                else:
                    stmt = ibm_db.exec_immediate(self.connection, sql)
                rows_affected = ibm_db.num_rows(stmt)

                if auto_commit:
                    ibm_db.commit(self.connection)

            execution_time = time.time() - start_time
            self.stats.successful_queries += 1
            self.stats.last_query_time = datetime.now()

            logger.info(f"✅ Non-query ejecutada: {rows_affected} filas afectadas en {execution_time:.2f}s")
            return rows_affected

        except Exception as e:
            self.stats.failed_queries += 1
            self.stats.last_error = str(e)
            error_message = f"❌ Error ejecutando non-query: {str(e)}"
            logger.error(error_message)
            raise DB2QueryError(error_message) from e

    def execute_batch(
        self,
        sql_statements: List[str],
        auto_commit: bool = True
    ) -> List[int]:
        """
        Ejecuta múltiples consultas SQL secuencialmente

        Args:
            sql_statements: Lista de consultas SQL
            auto_commit: Si True, hace commit al final

        Returns:
            Lista con filas afectadas por cada consulta

        Raises:
            DB2QueryError: Si hay error en alguna ejecución
        """
        if self.status != ConnectionStatus.CONNECTED:
            if not self.connect():
                raise DB2QueryError("❌ No hay conexión activa a DB2")

        results = []
        start_time = time.time()

        try:
            logger.info(f"📦 Ejecutando batch de {len(sql_statements)} consultas...")

            for i, sql in enumerate(sql_statements):
                rows = self.execute_non_query(sql, auto_commit=False)
                results.append(rows)
                logger.debug(f"   [{i+1}/{len(sql_statements)}] {rows} filas afectadas")

            if auto_commit:
                self.commit()

            execution_time = time.time() - start_time
            logger.info(f"✅ Batch completado en {execution_time:.2f}s")
            return results

        except Exception as e:
            self.rollback()
            error_message = f"❌ Error en batch, rollback ejecutado: {str(e)}"
            logger.error(error_message)
            raise DB2QueryError(error_message) from e

    # ═══════════════════════════════════════════════════════════════
    # GESTIÓN DE TRANSACCIONES
    # ═══════════════════════════════════════════════════════════════

    def begin_transaction(self) -> bool:
        """
        Inicia una transacción explícita

        Returns:
            True si se inició correctamente
        """
        if self.status != ConnectionStatus.CONNECTED:
            if not self.connect():
                raise DB2ConnectionError("❌ No hay conexión activa para iniciar transacción")

        try:
            if self._selected_driver == "pyodbc":
                self.connection.autocommit = False
            # ibm_db por defecto no tiene autocommit

            logger.info("🔄 Transacción iniciada")
            return True

        except Exception as e:
            error_message = f"❌ Error al iniciar transacción: {str(e)}"
            logger.error(error_message)
            raise DB2ConnectionError(error_message) from e

    def commit(self) -> bool:
        """
        Confirma la transacción actual

        Returns:
            True si el commit fue exitoso
        """
        if not self.connection:
            raise DB2ConnectionError("❌ No hay conexión activa para commit")

        try:
            if self._selected_driver == "pyodbc":
                self.connection.commit()
            else:
                ibm_db.commit(self.connection)

            logger.info("✅ Transacción confirmada (commit)")
            return True

        except Exception as e:
            error_message = f"❌ Error en commit: {str(e)}"
            logger.error(error_message)
            raise DB2ConnectionError(error_message) from e

    def rollback(self) -> bool:
        """
        Revierte la transacción actual

        Returns:
            True si el rollback fue exitoso
        """
        if not self.connection:
            logger.warning("⚠️  No hay conexión activa para rollback")
            return False

        try:
            if self._selected_driver == "pyodbc":
                self.connection.rollback()
            else:
                ibm_db.rollback(self.connection)

            logger.info("🔙 Transacción revertida (rollback)")
            return True

        except Exception as e:
            error_message = f"❌ Error en rollback: {str(e)}"
            logger.error(error_message)
            return False

    @contextmanager
    def transaction(self):
        """
        Context manager para transacciones

        Ejemplo:
            >>> with db.transaction():
            ...     db.execute_non_query("INSERT INTO ...")
            ...     db.execute_non_query("UPDATE ...")
            ... # Commit automático al salir, rollback si hay error

        Yields:
            self para uso encadenado
        """
        self.begin_transaction()
        try:
            yield self
            self.commit()
        except Exception as e:
            self.rollback()
            raise

    # ═══════════════════════════════════════════════════════════════
    # HEALTH CHECK Y DIAGNÓSTICO
    # ═══════════════════════════════════════════════════════════════

    def health_check(self) -> bool:
        """
        Verifica el estado de salud de la conexión

        Returns:
            True si la conexión está saludable
        """
        try:
            if self.status != ConnectionStatus.CONNECTED:
                return False

            # Ejecutar query de prueba
            result = self.execute_scalar("SELECT 1 FROM SYSIBM.SYSDUMMY1")
            return result == 1

        except Exception as e:
            logger.warning(f"⚠️  Health check fallido: {str(e)}")
            return False

    def get_server_info(self) -> Dict:
        """
        Obtiene información del servidor DB2

        Returns:
            Diccionario con información del servidor
        """
        try:
            info = {}

            # Versión del servidor
            version_query = """
                SELECT SERVICE_LEVEL, FIXPACK_NUM
                FROM TABLE(SYSPROC.ENV_GET_INST_INFO()) AS INSTANCEINFO
            """
            try:
                df = self.execute_query(version_query)
                if not df.empty:
                    info['service_level'] = df.iloc[0, 0] if len(df.columns) > 0 else None
                    info['fixpack'] = df.iloc[0, 1] if len(df.columns) > 1 else None
            except Exception:
                info['service_level'] = 'No disponible'
                info['fixpack'] = 'No disponible'

            # Información de la instancia
            info['host'] = self.config.get('host')
            info['port'] = self.config.get('port')
            info['database'] = self.config.get('database')
            info['user'] = self.config.get('user')
            info['driver'] = self._selected_driver

            return info

        except Exception as e:
            logger.error(f"❌ Error obteniendo info del servidor: {str(e)}")
            return {'error': str(e)}

    def get_connection_stats(self) -> Dict:
        """
        Obtiene estadísticas detalladas de la conexión

        Returns:
            Diccionario con estadísticas completas
        """
        base_stats = self.get_stats()

        # Agregar información adicional
        base_stats.update({
            'config_host': self.config.get('host'),
            'config_port': self.config.get('port'),
            'config_database': self.config.get('database'),
            'config_timeout': self.config.get('timeout'),
            'max_retries': self.max_retries,
            'base_delay': self.base_delay,
            'max_delay': self.max_delay,
        })

        return base_stats

    def get_stats(self) -> Dict:
        """
        Obtiene estadísticas de la conexión

        Returns:
            Diccionario con estadísticas
        """
        return {
            'status': self.status.value,
            'driver': self._selected_driver,
            'total_connections': self.stats.total_connections,
            'successful_connections': self.stats.successful_connections,
            'failed_connections': self.stats.failed_connections,
            'total_queries': self.stats.total_queries,
            'successful_queries': self.stats.successful_queries,
            'failed_queries': self.stats.failed_queries,
            'total_retry_attempts': self.stats.total_retry_attempts,
            'last_connection_time': str(self.stats.last_connection_time) if self.stats.last_connection_time else None,
            'last_query_time': str(self.stats.last_query_time) if self.stats.last_query_time else None,
            'last_error': self.stats.last_error
        }

    def print_stats(self) -> None:
        """Imprime estadísticas de conexión formateadas"""
        stats = self.get_stats()

        print("\n" + "="*50)
        print("📊 ESTADÍSTICAS DE CONEXIÓN DB2")
        print("="*50)
        print(f"   Estado: {stats['status']}")
        print(f"   Driver: {stats['driver']}")
        print(f"\n   Conexiones:")
        print(f"      Total: {stats['total_connections']}")
        print(f"      Exitosas: {stats['successful_connections']}")
        print(f"      Fallidas: {stats['failed_connections']}")
        print(f"\n   Queries:")
        print(f"      Total: {stats['total_queries']}")
        print(f"      Exitosas: {stats['successful_queries']}")
        print(f"      Fallidas: {stats['failed_queries']}")
        print(f"\n   Reintentos: {stats['total_retry_attempts']}")

        if stats['last_error']:
            print(f"\n   ⚠️  Último error: {stats['last_error'][:50]}...")

        print("="*50 + "\n")

    # ═══════════════════════════════════════════════════════════════
    # CONTEXT MANAGER
    # ═══════════════════════════════════════════════════════════════

    def __enter__(self) -> 'DB2Connection':
        """Entrada al context manager"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Salida del context manager"""
        self.disconnect()
        return False  # No suprimir excepciones

    def __del__(self):
        """Destructor - asegurar que la conexión se cierre"""
        try:
            if self.status == ConnectionStatus.CONNECTED:
                self.disconnect()
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════════
# POOL DE CONEXIONES
# ═══════════════════════════════════════════════════════════════

class DB2ConnectionPool:
    """
    Pool de conexiones para DB2

    Proporciona gestión eficiente de múltiples conexiones
    con reutilización y límites configurables.

    Ejemplo:
        >>> pool = DB2ConnectionPool(min_connections=2, max_connections=10)
        >>> with pool.get_connection() as conn:
        ...     df = conn.execute_query("SELECT * FROM tabla")
    """

    def __init__(
        self,
        config: Optional[Dict] = None,
        min_connections: int = 1,
        max_connections: int = 5,
        connection_timeout: float = 30.0
    ):
        """
        Inicializa el pool de conexiones

        Args:
            config: Configuración de conexión
            min_connections: Conexiones mínimas en el pool
            max_connections: Conexiones máximas en el pool
            connection_timeout: Timeout para obtener conexión del pool
        """
        self.config = config or DB_CONFIG
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.connection_timeout = connection_timeout

        self._pool: Queue = Queue(maxsize=max_connections)
        self._lock = Lock()
        self._active_connections = 0
        self._created_connections = 0

        # Pre-crear conexiones mínimas
        self._initialize_pool()

        logger.info(
            f"🏊 Pool de conexiones inicializado "
            f"(min={min_connections}, max={max_connections})"
        )

    def _initialize_pool(self) -> None:
        """Inicializa el pool con conexiones mínimas"""
        for _ in range(self.min_connections):
            try:
                conn = DB2Connection(config=self.config, auto_connect=True)
                self._pool.put(conn)
                self._created_connections += 1
            except Exception as e:
                logger.warning(f"⚠️  No se pudo crear conexión inicial: {e}")

    def _create_connection(self) -> DB2Connection:
        """Crea una nueva conexión"""
        conn = DB2Connection(config=self.config, auto_connect=True)
        self._created_connections += 1
        return conn

    @contextmanager
    def get_connection(self):
        """
        Obtiene una conexión del pool (context manager)

        Yields:
            DB2Connection disponible

        Raises:
            DB2PoolExhaustedError: Si no hay conexiones disponibles
        """
        connection = None

        try:
            # Intentar obtener del pool
            try:
                connection = self._pool.get(timeout=self.connection_timeout)

                # Verificar que la conexión esté activa
                if not connection.is_connected():
                    logger.info("🔄 Reconectando conexión del pool...")
                    connection.connect()

            except Empty:
                # Pool vacío, crear nueva si hay espacio
                with self._lock:
                    if self._created_connections < self.max_connections:
                        logger.info("📈 Expandiendo pool de conexiones...")
                        connection = self._create_connection()
                    else:
                        raise DB2PoolExhaustedError(
                            f"❌ Pool agotado. Máximo de {self.max_connections} conexiones alcanzado"
                        )

            self._active_connections += 1
            yield connection

        finally:
            if connection:
                self._active_connections -= 1
                # Devolver al pool si hay espacio
                try:
                    self._pool.put_nowait(connection)
                except Exception:
                    # Pool lleno, cerrar conexión
                    connection.disconnect()

    def close_all(self) -> None:
        """Cierra todas las conexiones del pool"""
        logger.info("🔒 Cerrando todas las conexiones del pool...")

        while not self._pool.empty():
            try:
                conn = self._pool.get_nowait()
                conn.disconnect()
            except Empty:
                break

        self._created_connections = 0
        self._active_connections = 0
        logger.info("✅ Pool cerrado")

    def get_pool_stats(self) -> Dict:
        """
        Obtiene estadísticas del pool

        Returns:
            Diccionario con estadísticas
        """
        return {
            'min_connections': self.min_connections,
            'max_connections': self.max_connections,
            'created_connections': self._created_connections,
            'active_connections': self._active_connections,
            'available_connections': self._pool.qsize()
        }

    def __enter__(self):
        """Entrada al context manager del pool"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Salida del context manager - cierra todas las conexiones"""
        self.close_all()
        return False


# ═══════════════════════════════════════════════════════════════
# FUNCIONES UTILITARIAS
# ═══════════════════════════════════════════════════════════════

def test_connection(config: Optional[Dict] = None) -> bool:
    """
    Prueba la conexión a DB2

    Args:
        config: Configuración opcional

    Returns:
        True si la conexión es exitosa
    """
    try:
        logger.info("🔍 Probando conexión a DB2...")

        with DB2Connection(config=config) as db:
            # Query de prueba
            df = db.execute_query("SELECT 1 AS TEST FROM SYSIBM.SYSDUMMY1")

            if not df.empty and df.iloc[0, 0] == 1:
                logger.info("✅ Conexión a DB2 exitosa")
                db.print_stats()
                return True
            else:
                logger.error("❌ Conexión establecida pero query de prueba falló")
                return False

    except Exception as e:
        logger.error(f"❌ Error en prueba de conexión: {str(e)}")
        return False


def get_connection_info() -> Dict:
    """
    Obtiene información sobre la configuración de conexión

    Returns:
        Diccionario con información (sin password)
    """
    return {
        'host': DB_CONFIG.get('host'),
        'port': DB_CONFIG.get('port'),
        'database': DB_CONFIG.get('database'),
        'user': DB_CONFIG.get('user'),
        'password_configured': DB_CONFIG.get('password') not in [None, '', 'tu_password'],
        'timeout': DB_CONFIG.get('timeout'),
        'driver': DB_CONFIG.get('driver'),
        'dsn': DB_CONFIG.get('dsn'),
        'pyodbc_available': PYODBC_AVAILABLE,
        'ibm_db_available': IBM_DB_AVAILABLE
    }


def test_native_connection(config: Optional[Dict] = None) -> Tuple[bool, str]:
    """
    Prueba la conexión nativa a DB2 sin credenciales (como DBeaver).

    Intenta múltiples métodos de autenticación:
    1. Trust Authentication
    2. DSN preconfigurado
    3. Kerberos
    4. Variables de entorno DB2

    Args:
        config: Configuración opcional (usa DB_CONFIG por defecto)

    Returns:
        Tuple[bool, str]: (éxito, método_usado o mensaje_error)
    """
    cfg = config or DB_CONFIG

    metodos = [
        ('trust_auth', _try_trust_auth),
        ('dsn', _try_dsn),
        ('kerberos', _try_kerberos),
        ('db2_env', _try_db2_env),
    ]

    for nombre, func in metodos:
        try:
            resultado = func(cfg)
            if resultado:
                logger.info(f"✅ Conexión nativa exitosa usando: {nombre}")
                return True, nombre
        except Exception as e:
            logger.debug(f"Método {nombre} falló: {str(e)}")
            continue

    return False, "No se pudo establecer conexión nativa"


def _try_trust_auth(config: Dict) -> bool:
    """Intenta conexión trust authentication"""
    if IBM_DB_AVAILABLE:
        conn_str = (
            f"DATABASE={config['database']};"
            f"HOSTNAME={config['host']};"
            f"PORT={config['port']};"
            f"PROTOCOL=TCPIP;"
            f"AUTHENTICATION=SERVER;"
        )
        conn = ibm_db.connect(conn_str, "", "")
        if conn:
            stmt = ibm_db.exec_immediate(conn, "SELECT 1 FROM SYSIBM.SYSDUMMY1")
            row = ibm_db.fetch_tuple(stmt)
            ibm_db.close(conn)
            return row and row[0] == 1
    return False


def _try_dsn(config: Dict) -> bool:
    """Intenta conexión mediante DSN"""
    dsn = config.get('dsn', config.get('database'))
    if PYODBC_AVAILABLE and dsn:
        conn = pyodbc.connect(f"DSN={dsn};", autocommit=True)
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM SYSIBM.SYSDUMMY1")
            row = cursor.fetchone()
            conn.close()
            return row and row[0] == 1
    return False


def _try_kerberos(config: Dict) -> bool:
    """Intenta conexión con Kerberos"""
    if IBM_DB_AVAILABLE:
        conn_str = (
            f"DATABASE={config['database']};"
            f"HOSTNAME={config['host']};"
            f"PORT={config['port']};"
            f"PROTOCOL=TCPIP;"
            f"AUTHENTICATION=KERBEROS;"
        )
        conn = ibm_db.connect(conn_str, "", "")
        if conn:
            stmt = ibm_db.exec_immediate(conn, "SELECT 1 FROM SYSIBM.SYSDUMMY1")
            row = ibm_db.fetch_tuple(stmt)
            ibm_db.close(conn)
            return row and row[0] == 1
    return False


def _try_db2_env(config: Dict) -> bool:
    """Intenta conexión usando variables de entorno DB2"""
    db2_instance = os.environ.get('DB2INSTANCE')
    if IBM_DB_AVAILABLE and db2_instance:
        conn_str = f"DATABASE={config['database']};"
        conn = ibm_db.connect(conn_str, "", "")
        if conn:
            stmt = ibm_db.exec_immediate(conn, "SELECT 1 FROM SYSIBM.SYSDUMMY1")
            row = ibm_db.fetch_tuple(stmt)
            ibm_db.close(conn)
            return row and row[0] == 1
    return False


class DB2NativeConnection:
    """
    Conexión nativa a DB2 sin credenciales explícitas.

    Similar a como DBeaver maneja las conexiones guardadas,
    esta clase intenta conectar usando:
    - Trust Authentication
    - DSN preconfigurado
    - Kerberos
    - Variables de entorno del sistema

    Ejemplo:
        >>> with DB2NativeConnection() as db:
        ...     df = db.execute_query("SELECT * FROM TABLA")
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or DB_CONFIG
        self.connection = None
        self.method_used = None

    def connect(self) -> bool:
        """Intenta conexión nativa"""
        success, method = test_native_connection(self.config)
        if success:
            self.method_used = method
            # Crear conexión persistente
            if method == 'trust_auth':
                conn_str = (
                    f"DATABASE={self.config['database']};"
                    f"HOSTNAME={self.config['host']};"
                    f"PORT={self.config['port']};"
                    f"PROTOCOL=TCPIP;"
                    f"AUTHENTICATION=SERVER;"
                )
                self.connection = ibm_db.connect(conn_str, "", "")
            elif method == 'dsn':
                dsn = self.config.get('dsn', self.config.get('database'))
                self.connection = pyodbc.connect(f"DSN={dsn};", autocommit=True)
            elif method == 'kerberos':
                conn_str = (
                    f"DATABASE={self.config['database']};"
                    f"HOSTNAME={self.config['host']};"
                    f"PORT={self.config['port']};"
                    f"PROTOCOL=TCPIP;"
                    f"AUTHENTICATION=KERBEROS;"
                )
                self.connection = ibm_db.connect(conn_str, "", "")
            elif method == 'db2_env':
                conn_str = f"DATABASE={self.config['database']};"
                self.connection = ibm_db.connect(conn_str, "", "")
            return True
        return False

    def execute_query(self, sql: str) -> 'pd.DataFrame':
        """Ejecuta query y retorna DataFrame"""
        if not self.connection:
            raise DB2ConnectionError("No hay conexión activa")

        if self.method_used == 'dsn':
            # pyodbc
            cursor = self.connection.cursor()
            cursor.execute(sql)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            return pd.DataFrame(rows, columns=columns)
        else:
            # ibm_db
            stmt = ibm_db.exec_immediate(self.connection, sql)
            columns = []
            for i in range(ibm_db.num_fields(stmt)):
                columns.append(ibm_db.field_name(stmt, i))
            rows = []
            row = ibm_db.fetch_tuple(stmt)
            while row:
                rows.append(row)
                row = ibm_db.fetch_tuple(stmt)
            return pd.DataFrame(rows, columns=columns)

    def disconnect(self):
        """Cierra la conexión"""
        if self.connection:
            if self.method_used == 'dsn':
                self.connection.close()
            else:
                ibm_db.close(self.connection)
            self.connection = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
        return False


# ═══════════════════════════════════════════════════════════════
# EXPORTAR
# ═══════════════════════════════════════════════════════════════

__all__ = [
    # Clases principales
    'DB2Connection',
    'DB2ConnectionPool',
    'DB2NativeConnection',

    # Enums y Data Classes
    'ConnectionDriver',
    'ConnectionStatus',
    'ConnectionStats',
    'QueryResult',

    # Excepciones
    'DB2ConnectionError',
    'DB2QueryError',
    'DB2ConfigurationError',
    'DB2PoolExhaustedError',

    # Funciones utilitarias
    'test_connection',
    'get_connection_info',
    'test_native_connection',

    # Flags de disponibilidad
    'PYODBC_AVAILABLE',
    'IBM_DB_AVAILABLE',
]


# ═══════════════════════════════════════════════════════════════
# EJECUTAR AL IMPORTAR
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Si se ejecuta directamente, mostrar información y probar conexión
    print("\n" + "="*60)
    print("💾 MÓDULO DE CONEXIÓN DB2 - SAC CEDIS 427")
    print("="*60)

    info = get_connection_info()

    print(f"\n📋 Configuración:")
    print(f"   Host: {info['host']}")
    print(f"   Puerto: {info['port']}")
    print(f"   Base de datos: {info['database']}")
    print(f"   Usuario: {info['user']}")
    print(f"   Password configurado: {'✅ Sí' if info['password_configured'] else '❌ No'}")
    print(f"   Timeout: {info['timeout']}s")

    print(f"\n🔧 Drivers disponibles:")
    print(f"   pyodbc: {'✅ Disponible' if info['pyodbc_available'] else '❌ No instalado'}")
    print(f"   ibm-db: {'✅ Disponible' if info['ibm_db_available'] else '❌ No instalado'}")

    # Probar conexión si hay credenciales
    if info['password_configured']:
        print(f"\n🔍 Probando conexión...")
        test_connection()
    else:
        print(f"\n⚠️  Configura las credenciales en .env para probar la conexión")

    print("="*60 + "\n")
