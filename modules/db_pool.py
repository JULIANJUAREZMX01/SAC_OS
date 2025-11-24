"""
===============================================================
POOL DE CONEXIONES AVANZADO PARA DB2
Sistema de Automatizacion de Consultas - CEDIS Cancun 427
===============================================================

Este modulo proporciona un pool de conexiones avanzado con:
- Gestion dinamica del tamano del pool
- Health checks automaticos
- Estadisticas detalladas
- Limpieza automatica de conexiones inactivas
- Thread-safe operations

Uso:
    from modules.db_pool import ConnectionPool

    # Crear pool
    pool = ConnectionPool(min_size=2, max_size=10)

    # Usar conexion
    with pool.get_connection() as conn:
        df = conn.execute_query("SELECT * FROM tabla")

    # Obtener estadisticas
    stats = pool.get_pool_status()

Desarrollado por: Julian Alexander Juarez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logistica Cancun
===============================================================
"""

import logging
import time
import threading
from typing import Optional, Dict, List, Callable
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from queue import Queue, Empty, Full
from enum import Enum

# Importar la clase de conexion
from .db_connection import (
    DB2Connection,
    DB2ConnectionError,
    DB2PoolExhaustedError,
    ConnectionStatus
)

# Importar configuracion
try:
    from config import DB_CONFIG
except ImportError:
    DB_CONFIG = {}

# ===============================================================
# CONFIGURACION DE LOGGING
# ===============================================================

logger = logging.getLogger(__name__)


# ===============================================================
# ENUMS Y DATA CLASSES
# ===============================================================

class PoolStatus(Enum):
    """Estados del pool de conexiones"""
    INITIALIZING = "inicializando"
    RUNNING = "ejecutando"
    DRAINING = "drenando"
    CLOSED = "cerrado"


@dataclass
class PooledConnection:
    """Wrapper para conexiones del pool"""
    connection: DB2Connection
    created_at: datetime = field(default_factory=datetime.now)
    last_used: datetime = field(default_factory=datetime.now)
    use_count: int = 0
    is_healthy: bool = True

    def mark_used(self):
        """Marca la conexion como usada"""
        self.last_used = datetime.now()
        self.use_count += 1


@dataclass
class PoolStatistics:
    """Estadisticas del pool"""
    total_connections_created: int = 0
    total_connections_destroyed: int = 0
    total_acquisitions: int = 0
    total_releases: int = 0
    total_timeouts: int = 0
    total_health_checks: int = 0
    failed_health_checks: int = 0
    peak_connections: int = 0
    current_active: int = 0
    current_idle: int = 0


# ===============================================================
# CLASE PRINCIPAL DEL POOL
# ===============================================================

class ConnectionPool:
    """
    Pool de conexiones avanzado para IBM DB2

    Caracteristicas:
    - Tamano dinamico del pool (min/max)
    - Health checks periodicos
    - Limpieza de conexiones inactivas
    - Estadisticas detalladas
    - Thread-safe
    - Context manager support

    Ejemplo de uso:
        >>> pool = ConnectionPool(min_size=2, max_size=10)
        >>> with pool.get_connection() as conn:
        ...     df = conn.execute_query("SELECT * FROM tabla")
        >>> pool.close_all()
    """

    # Configuracion por defecto
    DEFAULT_MIN_SIZE = 1
    DEFAULT_MAX_SIZE = 5
    DEFAULT_ACQUIRE_TIMEOUT = 30.0
    DEFAULT_MAX_IDLE_TIME = 300.0  # 5 minutos
    DEFAULT_HEALTH_CHECK_INTERVAL = 60.0  # 1 minuto
    DEFAULT_MAX_LIFETIME = 3600.0  # 1 hora

    def __init__(
        self,
        config: Optional[Dict] = None,
        min_size: int = DEFAULT_MIN_SIZE,
        max_size: int = DEFAULT_MAX_SIZE,
        acquire_timeout: float = DEFAULT_ACQUIRE_TIMEOUT,
        max_idle_time: float = DEFAULT_MAX_IDLE_TIME,
        health_check_interval: float = DEFAULT_HEALTH_CHECK_INTERVAL,
        max_lifetime: float = DEFAULT_MAX_LIFETIME,
        on_connection_error: Optional[Callable] = None
    ):
        """
        Inicializa el pool de conexiones

        Args:
            config: Configuracion de conexion a DB2
            min_size: Numero minimo de conexiones
            max_size: Numero maximo de conexiones
            acquire_timeout: Timeout para obtener conexion (segundos)
            max_idle_time: Tiempo maximo de inactividad (segundos)
            health_check_interval: Intervalo de health checks (segundos)
            max_lifetime: Tiempo maximo de vida de una conexion (segundos)
            on_connection_error: Callback para errores de conexion
        """
        # Validar parametros
        if min_size < 0:
            raise ValueError("min_size debe ser >= 0")
        if max_size < min_size:
            raise ValueError("max_size debe ser >= min_size")
        if max_size < 1:
            raise ValueError("max_size debe ser >= 1")

        self.config = config or DB_CONFIG
        self.min_size = min_size
        self.max_size = max_size
        self.acquire_timeout = acquire_timeout
        self.max_idle_time = max_idle_time
        self.health_check_interval = health_check_interval
        self.max_lifetime = max_lifetime
        self.on_connection_error = on_connection_error

        # Estado interno
        self._pool: Queue = Queue(maxsize=max_size)
        self._lock = threading.RLock()
        self._status = PoolStatus.INITIALIZING
        self._stats = PoolStatistics()
        self._active_connections: Dict[int, PooledConnection] = {}

        # Thread para mantenimiento
        self._maintenance_thread: Optional[threading.Thread] = None
        self._stop_maintenance = threading.Event()

        # Inicializar pool
        self._initialize_pool()

        # Iniciar mantenimiento
        self._start_maintenance()

        logger.info(
            f"Connection pool inicializado "
            f"(min={min_size}, max={max_size})"
        )

    def _initialize_pool(self) -> None:
        """Inicializa el pool con conexiones minimas"""
        logger.info(f"Inicializando pool con {self.min_size} conexiones...")

        for _ in range(self.min_size):
            try:
                self._create_and_add_connection()
            except Exception as e:
                logger.warning(f"No se pudo crear conexion inicial: {e}")

        self._status = PoolStatus.RUNNING
        self._stats.current_idle = self._pool.qsize()

    def _create_connection(self) -> PooledConnection:
        """Crea una nueva conexion envuelta"""
        conn = DB2Connection(config=self.config, auto_connect=True)
        pooled = PooledConnection(connection=conn)
        self._stats.total_connections_created += 1
        return pooled

    def _create_and_add_connection(self) -> bool:
        """Crea una conexion y la agrega al pool"""
        try:
            pooled = self._create_connection()
            self._pool.put_nowait(pooled)

            # Actualizar estadisticas
            total = self._pool.qsize() + len(self._active_connections)
            if total > self._stats.peak_connections:
                self._stats.peak_connections = total

            return True
        except Full:
            return False
        except Exception as e:
            logger.error(f"Error creando conexion: {e}")
            return False

    def _destroy_connection(self, pooled: PooledConnection) -> None:
        """Destruye una conexion"""
        try:
            pooled.connection.disconnect()
        except (ConnectionError, OSError, AttributeError) as e:
            logger.debug(f"Error al destruir conexión (esperado en cleanup): {e}")
        finally:
            self._stats.total_connections_destroyed += 1

    def _is_connection_healthy(self, pooled: PooledConnection) -> bool:
        """Verifica si una conexion esta saludable"""
        self._stats.total_health_checks += 1

        try:
            # Verificar tiempo de vida
            age = (datetime.now() - pooled.created_at).total_seconds()
            if age > self.max_lifetime:
                logger.debug(f"Conexion excede tiempo de vida ({age:.0f}s)")
                return False

            # Verificar salud de la conexion
            if not pooled.connection.health_check():
                logger.debug("Health check de conexion fallido")
                self._stats.failed_health_checks += 1
                return False

            return True

        except Exception as e:
            logger.warning(f"Error en health check: {e}")
            self._stats.failed_health_checks += 1
            return False

    @contextmanager
    def get_connection(self):
        """
        Obtiene una conexion del pool (context manager)

        Yields:
            DB2Connection disponible

        Raises:
            DB2PoolExhaustedError: Si no hay conexiones disponibles
        """
        pooled = None
        start_time = time.time()

        try:
            pooled = self._acquire_connection()
            yield pooled.connection

        except Exception as e:
            if self.on_connection_error:
                self.on_connection_error(e)
            raise

        finally:
            if pooled:
                self._release_connection(pooled)

    def _acquire_connection(self) -> PooledConnection:
        """Adquiere una conexion del pool"""
        self._stats.total_acquisitions += 1
        deadline = time.time() + self.acquire_timeout

        while time.time() < deadline:
            # Intentar obtener del pool
            try:
                pooled = self._pool.get(timeout=min(1.0, self.acquire_timeout))

                # Verificar salud
                if self._is_connection_healthy(pooled):
                    pooled.mark_used()

                    with self._lock:
                        self._active_connections[id(pooled)] = pooled
                        self._stats.current_active = len(self._active_connections)
                        self._stats.current_idle = self._pool.qsize()

                    return pooled
                else:
                    # Conexion no saludable, destruir
                    self._destroy_connection(pooled)
                    continue

            except Empty:
                # Pool vacio, intentar crear nueva conexion
                with self._lock:
                    total = self._pool.qsize() + len(self._active_connections)
                    if total < self.max_size:
                        try:
                            logger.info("Expandiendo pool de conexiones...")
                            pooled = self._create_connection()
                            pooled.mark_used()
                            self._active_connections[id(pooled)] = pooled
                            self._stats.current_active = len(self._active_connections)

                            # Actualizar peak
                            total = self._pool.qsize() + len(self._active_connections)
                            if total > self._stats.peak_connections:
                                self._stats.peak_connections = total

                            return pooled
                        except Exception as e:
                            logger.error(f"Error creando nueva conexion: {e}")
                            continue

        # Timeout alcanzado
        self._stats.total_timeouts += 1
        raise DB2PoolExhaustedError(
            f"No se pudo obtener conexion en {self.acquire_timeout}s. "
            f"Pool: {self._pool.qsize()} disponibles, "
            f"{len(self._active_connections)} activas, "
            f"max={self.max_size}"
        )

    def _release_connection(self, pooled: PooledConnection) -> None:
        """Devuelve una conexion al pool"""
        self._stats.total_releases += 1

        with self._lock:
            # Remover de activas
            self._active_connections.pop(id(pooled), None)
            self._stats.current_active = len(self._active_connections)

        # Si el pool esta cerrado, destruir
        if self._status in (PoolStatus.DRAINING, PoolStatus.CLOSED):
            self._destroy_connection(pooled)
            return

        # Verificar si la conexion sigue saludable
        if pooled.connection.status == ConnectionStatus.CONNECTED:
            try:
                self._pool.put_nowait(pooled)
                self._stats.current_idle = self._pool.qsize()
            except Full:
                # Pool lleno, destruir
                self._destroy_connection(pooled)
        else:
            # Conexion no conectada, destruir
            self._destroy_connection(pooled)

    def resize_pool(self, min_size: int, max_size: int) -> None:
        """
        Redimensiona el pool de conexiones

        Args:
            min_size: Nuevo tamano minimo
            max_size: Nuevo tamano maximo
        """
        if min_size < 0:
            raise ValueError("min_size debe ser >= 0")
        if max_size < min_size:
            raise ValueError("max_size debe ser >= min_size")

        with self._lock:
            old_min, old_max = self.min_size, self.max_size
            self.min_size = min_size
            self.max_size = max_size

            # Si el nuevo minimo es mayor, crear conexiones
            current_total = self._pool.qsize() + len(self._active_connections)
            if current_total < min_size:
                for _ in range(min_size - current_total):
                    self._create_and_add_connection()

            # Si el nuevo maximo es menor, marcar para reduccion
            # (se reducira en el mantenimiento)

            logger.info(
                f"Pool redimensionado: "
                f"({old_min}, {old_max}) -> ({min_size}, {max_size})"
            )

    def _start_maintenance(self) -> None:
        """Inicia el thread de mantenimiento"""
        self._stop_maintenance.clear()
        self._maintenance_thread = threading.Thread(
            target=self._maintenance_loop,
            daemon=True,
            name="db-pool-maintenance"
        )
        self._maintenance_thread.start()

    def _maintenance_loop(self) -> None:
        """Loop de mantenimiento del pool"""
        while not self._stop_maintenance.is_set():
            try:
                self._perform_maintenance()
            except Exception as e:
                logger.error(f"Error en mantenimiento del pool: {e}")

            # Esperar hasta el proximo ciclo
            self._stop_maintenance.wait(timeout=self.health_check_interval)

    def _perform_maintenance(self) -> None:
        """Realiza tareas de mantenimiento"""
        if self._status != PoolStatus.RUNNING:
            return

        connections_to_check = []

        # Obtener conexiones para verificar
        while not self._pool.empty():
            try:
                pooled = self._pool.get_nowait()
                connections_to_check.append(pooled)
            except Empty:
                break

        # Verificar cada conexion
        healthy_connections = []
        for pooled in connections_to_check:
            # Verificar tiempo de inactividad
            idle_time = (datetime.now() - pooled.last_used).total_seconds()

            # Verificar si debemos mantenerla
            current_total = len(healthy_connections) + len(self._active_connections)
            keep_for_min = current_total < self.min_size

            if idle_time > self.max_idle_time and not keep_for_min:
                logger.debug(f"Cerrando conexion inactiva ({idle_time:.0f}s)")
                self._destroy_connection(pooled)
                continue

            # Health check
            if self._is_connection_healthy(pooled):
                healthy_connections.append(pooled)
            else:
                self._destroy_connection(pooled)

        # Devolver conexiones saludables al pool
        for pooled in healthy_connections:
            try:
                self._pool.put_nowait(pooled)
            except Full:
                self._destroy_connection(pooled)

        # Asegurar minimo de conexiones
        current_total = self._pool.qsize() + len(self._active_connections)
        while current_total < self.min_size:
            if self._create_and_add_connection():
                current_total += 1
            else:
                break

        self._stats.current_idle = self._pool.qsize()

    def close_all(self) -> None:
        """Cierra todas las conexiones del pool"""
        logger.info("Cerrando pool de conexiones...")
        self._status = PoolStatus.DRAINING

        # Detener mantenimiento
        self._stop_maintenance.set()
        if self._maintenance_thread:
            self._maintenance_thread.join(timeout=5.0)

        # Cerrar conexiones en el pool
        while not self._pool.empty():
            try:
                pooled = self._pool.get_nowait()
                self._destroy_connection(pooled)
            except Empty:
                break

        # Las conexiones activas se cerraran cuando se liberen

        self._status = PoolStatus.CLOSED
        self._stats.current_idle = 0

        logger.info("Pool de conexiones cerrado")

    def get_pool_status(self) -> Dict:
        """
        Obtiene el estado actual del pool

        Returns:
            Diccionario con estado y estadisticas
        """
        return {
            'status': self._status.value,
            'min_size': self.min_size,
            'max_size': self.max_size,
            'current_idle': self._pool.qsize(),
            'current_active': len(self._active_connections),
            'total_connections': self._pool.qsize() + len(self._active_connections),
            'statistics': {
                'total_created': self._stats.total_connections_created,
                'total_destroyed': self._stats.total_connections_destroyed,
                'total_acquisitions': self._stats.total_acquisitions,
                'total_releases': self._stats.total_releases,
                'total_timeouts': self._stats.total_timeouts,
                'total_health_checks': self._stats.total_health_checks,
                'failed_health_checks': self._stats.failed_health_checks,
                'peak_connections': self._stats.peak_connections
            }
        }

    def print_status(self) -> None:
        """Imprime el estado del pool formateado"""
        status = self.get_pool_status()

        print("\n" + "="*55)
        print(" CONNECTION POOL STATUS")
        print("="*55)
        print(f"   Estado: {status['status']}")
        print(f"   Tamano: {status['min_size']} - {status['max_size']}")
        print(f"\n   Conexiones:")
        print(f"      Inactivas: {status['current_idle']}")
        print(f"      Activas: {status['current_active']}")
        print(f"      Total: {status['total_connections']}")
        print(f"\n   Estadisticas:")
        print(f"      Creadas: {status['statistics']['total_created']}")
        print(f"      Destruidas: {status['statistics']['total_destroyed']}")
        print(f"      Adquisiciones: {status['statistics']['total_acquisitions']}")
        print(f"      Liberaciones: {status['statistics']['total_releases']}")
        print(f"      Timeouts: {status['statistics']['total_timeouts']}")
        print(f"      Health checks: {status['statistics']['total_health_checks']}")
        print(f"      Health checks fallidos: {status['statistics']['failed_health_checks']}")
        print(f"      Pico de conexiones: {status['statistics']['peak_connections']}")
        print("="*55 + "\n")

    def __enter__(self):
        """Entrada al context manager del pool"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Salida del context manager - cierra todas las conexiones"""
        self.close_all()
        return False

    def __del__(self):
        """Destructor - asegurar limpieza"""
        try:
            if self._status == PoolStatus.RUNNING:
                self.close_all()
        except Exception:
            pass


# ===============================================================
# SINGLETON DEL POOL (OPCIONAL)
# ===============================================================

_default_pool: Optional[ConnectionPool] = None
_pool_lock = threading.Lock()


def get_default_pool(
    config: Optional[Dict] = None,
    min_size: int = ConnectionPool.DEFAULT_MIN_SIZE,
    max_size: int = ConnectionPool.DEFAULT_MAX_SIZE
) -> ConnectionPool:
    """
    Obtiene el pool de conexiones por defecto (singleton)

    Args:
        config: Configuracion de conexion
        min_size: Tamano minimo del pool
        max_size: Tamano maximo del pool

    Returns:
        ConnectionPool singleton
    """
    global _default_pool

    with _pool_lock:
        if _default_pool is None:
            _default_pool = ConnectionPool(
                config=config,
                min_size=min_size,
                max_size=max_size
            )
        return _default_pool


def close_default_pool() -> None:
    """Cierra el pool por defecto"""
    global _default_pool

    with _pool_lock:
        if _default_pool is not None:
            _default_pool.close_all()
            _default_pool = None


# ===============================================================
# EXPORTAR
# ===============================================================

__all__ = [
    # Clases principales
    'ConnectionPool',
    'PooledConnection',
    'PoolStatistics',
    'PoolStatus',

    # Funciones de singleton
    'get_default_pool',
    'close_default_pool',
]


# ===============================================================
# EJECUTAR AL IMPORTAR
# ===============================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print(" POOL DE CONEXIONES DB2 - SAC CEDIS 427")
    print("="*60)

    print("\n Este modulo proporciona un pool de conexiones avanzado.")
    print("\n Uso basico:")
    print("   from modules.db_pool import ConnectionPool")
    print("   ")
    print("   pool = ConnectionPool(min_size=2, max_size=10)")
    print("   with pool.get_connection() as conn:")
    print("       df = conn.execute_query('SELECT * FROM tabla')")
    print("   pool.close_all()")

    print("\n Uso con singleton:")
    print("   from modules.db_pool import get_default_pool")
    print("   ")
    print("   pool = get_default_pool()")
    print("   with pool.get_connection() as conn:")
    print("       df = conn.execute_query('SELECT * FROM tabla')")

    print("\n="*60 + "\n")
