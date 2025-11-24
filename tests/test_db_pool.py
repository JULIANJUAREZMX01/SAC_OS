"""
===============================================================
TESTS PARA POOL DE CONEXIONES
Sistema de Automatización de Consultas - CEDIS Cancún 427
===============================================================

Tests unitarios para el módulo db_pool.

Ejecutar:
    pytest tests/test_db_pool.py -v

Autor: Julián Alexander Juárez Alvarado (ADMJAJA)
===============================================================
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Importar módulos a testear
from modules.db_pool import (
    ConnectionPool,
    PooledConnection,
    PoolStatistics,
    PoolStatus,
    get_default_pool,
    close_default_pool,
)
from modules.db_connection import (
    DB2Connection,
    DB2PoolExhaustedError,
    ConnectionStatus,
)


# ===============================================================
# FIXTURES
# ===============================================================

@pytest.fixture
def mock_config():
    """Configuración mock para tests"""
    return {
        'host': 'test-host',
        'port': 50000,
        'database': 'TESTDB',
        'user': 'testuser',
        'password': 'testpass',
        'driver': '{IBM DB2 ODBC DRIVER}',
        'timeout': 30,
    }


@pytest.fixture
def mock_db2_connection():
    """Mock de DB2Connection"""
    mock = Mock(spec=DB2Connection)
    mock.is_connected.return_value = True
    mock.health_check.return_value = True
    mock.status = ConnectionStatus.CONNECTED
    return mock


@pytest.fixture
def pool_with_mocks(mock_config, mock_db2_connection):
    """Pool con conexiones mockeadas"""
    with patch('modules.db_pool.DB2Connection') as MockDB2:
        MockDB2.return_value = mock_db2_connection
        pool = ConnectionPool(
            config=mock_config,
            min_size=1,
            max_size=3,
            health_check_interval=1000  # Evitar checks durante tests
        )
        yield pool
        pool.close_all()


# ===============================================================
# TESTS DE INICIALIZACIÓN
# ===============================================================

class TestConnectionPoolInit:
    """Tests de inicialización del pool"""

    def test_init_with_defaults(self, mock_config):
        """Verifica inicialización con valores por defecto"""
        with patch('modules.db_pool.DB2Connection') as MockDB2:
            MockDB2.return_value = Mock(spec=DB2Connection)
            MockDB2.return_value.is_connected.return_value = True

            pool = ConnectionPool(
                config=mock_config,
                min_size=0,
                health_check_interval=1000
            )

            assert pool.min_size == 0
            assert pool.max_size == ConnectionPool.DEFAULT_MAX_SIZE
            assert pool._status == PoolStatus.RUNNING
            pool.close_all()

    def test_init_creates_min_connections(self, mock_config):
        """Verifica que se crean las conexiones mínimas"""
        with patch('modules.db_pool.DB2Connection') as MockDB2:
            mock_conn = Mock(spec=DB2Connection)
            mock_conn.is_connected.return_value = True
            MockDB2.return_value = mock_conn

            pool = ConnectionPool(
                config=mock_config,
                min_size=2,
                max_size=5,
                health_check_interval=1000
            )

            assert pool._pool.qsize() >= 2
            pool.close_all()

    def test_init_invalid_min_size(self, mock_config):
        """Verifica error con min_size inválido"""
        with pytest.raises(ValueError) as exc_info:
            ConnectionPool(config=mock_config, min_size=-1)
        assert "min_size" in str(exc_info.value)

    def test_init_invalid_max_size(self, mock_config):
        """Verifica error con max_size menor que min_size"""
        with pytest.raises(ValueError) as exc_info:
            ConnectionPool(config=mock_config, min_size=5, max_size=2)
        assert "max_size" in str(exc_info.value)


# ===============================================================
# TESTS DE ADQUISICIÓN DE CONEXIONES
# ===============================================================

class TestConnectionPoolAcquire:
    """Tests de adquisición de conexiones"""

    def test_get_connection_from_pool(self, pool_with_mocks):
        """Verifica obtención de conexión del pool"""
        with pool_with_mocks.get_connection() as conn:
            assert conn is not None
            assert conn.is_connected()

    def test_get_connection_expands_pool(self, mock_config):
        """Verifica expansión del pool cuando está vacío"""
        with patch('modules.db_pool.DB2Connection') as MockDB2:
            mock_conn = Mock(spec=DB2Connection)
            mock_conn.is_connected.return_value = True
            mock_conn.health_check.return_value = True
            mock_conn.status = ConnectionStatus.CONNECTED
            MockDB2.return_value = mock_conn

            pool = ConnectionPool(
                config=mock_config,
                min_size=0,
                max_size=3,
                health_check_interval=1000
            )

            # Primera conexión debe crear una nueva
            with pool.get_connection() as conn:
                assert conn is not None

            pool.close_all()

    def test_get_connection_timeout(self, mock_config):
        """Verifica timeout cuando el pool está agotado"""
        with patch('modules.db_pool.DB2Connection') as MockDB2:
            mock_conn = Mock(spec=DB2Connection)
            mock_conn.is_connected.return_value = True
            mock_conn.health_check.return_value = True
            mock_conn.status = ConnectionStatus.CONNECTED
            MockDB2.return_value = mock_conn

            pool = ConnectionPool(
                config=mock_config,
                min_size=1,
                max_size=1,
                acquire_timeout=0.1,
                health_check_interval=1000
            )

            # Adquirir la única conexión
            with pool.get_connection():
                # Intentar adquirir otra debería fallar por timeout
                with pytest.raises(DB2PoolExhaustedError):
                    with pool.get_connection():
                        pass

            pool.close_all()


# ===============================================================
# TESTS DE LIBERACIÓN DE CONEXIONES
# ===============================================================

class TestConnectionPoolRelease:
    """Tests de liberación de conexiones"""

    def test_release_returns_to_pool(self, pool_with_mocks):
        """Verifica que las conexiones vuelven al pool"""
        initial_idle = pool_with_mocks._pool.qsize()

        with pool_with_mocks.get_connection():
            # Durante el uso, hay una menos disponible
            assert pool_with_mocks._stats.current_active > 0

        # Después de liberar, debe estar disponible
        # Dar tiempo para que se procese la liberación
        time.sleep(0.1)
        assert pool_with_mocks._pool.qsize() >= initial_idle


# ===============================================================
# TESTS DE REDIMENSIONAMIENTO
# ===============================================================

class TestConnectionPoolResize:
    """Tests de redimensionamiento del pool"""

    def test_resize_increase_min(self, pool_with_mocks):
        """Verifica aumento del tamaño mínimo"""
        pool_with_mocks.resize_pool(min_size=2, max_size=5)

        assert pool_with_mocks.min_size == 2
        assert pool_with_mocks.max_size == 5

    def test_resize_invalid_values(self, pool_with_mocks):
        """Verifica error con valores inválidos"""
        with pytest.raises(ValueError):
            pool_with_mocks.resize_pool(min_size=10, max_size=5)


# ===============================================================
# TESTS DE ESTADÍSTICAS
# ===============================================================

class TestConnectionPoolStats:
    """Tests de estadísticas del pool"""

    def test_get_pool_status(self, pool_with_mocks):
        """Verifica obtención de estado del pool"""
        status = pool_with_mocks.get_pool_status()

        assert 'status' in status
        assert 'min_size' in status
        assert 'max_size' in status
        assert 'current_idle' in status
        assert 'current_active' in status
        assert 'statistics' in status

    def test_statistics_tracking(self, pool_with_mocks):
        """Verifica seguimiento de estadísticas"""
        initial_acquisitions = pool_with_mocks._stats.total_acquisitions

        with pool_with_mocks.get_connection():
            pass

        assert pool_with_mocks._stats.total_acquisitions > initial_acquisitions
        assert pool_with_mocks._stats.total_releases > 0


# ===============================================================
# TESTS DE CIERRE
# ===============================================================

class TestConnectionPoolClose:
    """Tests de cierre del pool"""

    def test_close_all(self, mock_config):
        """Verifica cierre de todas las conexiones"""
        with patch('modules.db_pool.DB2Connection') as MockDB2:
            mock_conn = Mock(spec=DB2Connection)
            mock_conn.is_connected.return_value = True
            mock_conn.health_check.return_value = True
            mock_conn.status = ConnectionStatus.CONNECTED
            MockDB2.return_value = mock_conn

            pool = ConnectionPool(
                config=mock_config,
                min_size=2,
                max_size=5,
                health_check_interval=1000
            )

            pool.close_all()

            assert pool._status == PoolStatus.CLOSED
            assert pool._pool.qsize() == 0


# ===============================================================
# TESTS DE CONTEXT MANAGER
# ===============================================================

class TestConnectionPoolContextManager:
    """Tests de context manager del pool"""

    def test_pool_as_context_manager(self, mock_config):
        """Verifica uso del pool como context manager"""
        with patch('modules.db_pool.DB2Connection') as MockDB2:
            mock_conn = Mock(spec=DB2Connection)
            mock_conn.is_connected.return_value = True
            MockDB2.return_value = mock_conn

            with ConnectionPool(
                config=mock_config,
                min_size=1,
                max_size=3,
                health_check_interval=1000
            ) as pool:
                assert pool._status == PoolStatus.RUNNING

            # Después de salir, debe estar cerrado
            assert pool._status == PoolStatus.CLOSED


# ===============================================================
# TESTS DE POOLED CONNECTION
# ===============================================================

class TestPooledConnection:
    """Tests de PooledConnection"""

    def test_pooled_connection_creation(self, mock_db2_connection):
        """Verifica creación de PooledConnection"""
        pooled = PooledConnection(connection=mock_db2_connection)

        assert pooled.connection == mock_db2_connection
        assert pooled.use_count == 0
        assert pooled.is_healthy is True

    def test_pooled_connection_mark_used(self, mock_db2_connection):
        """Verifica marcado de uso"""
        pooled = PooledConnection(connection=mock_db2_connection)
        initial_time = pooled.last_used

        time.sleep(0.01)
        pooled.mark_used()

        assert pooled.use_count == 1
        assert pooled.last_used > initial_time


# ===============================================================
# TESTS DE SINGLETON
# ===============================================================

class TestDefaultPool:
    """Tests de pool singleton"""

    def test_get_default_pool(self, mock_config):
        """Verifica obtención de pool por defecto"""
        # Limpiar cualquier pool existente
        close_default_pool()

        with patch('modules.db_pool.DB2Connection') as MockDB2:
            mock_conn = Mock(spec=DB2Connection)
            mock_conn.is_connected.return_value = True
            MockDB2.return_value = mock_conn

            pool1 = get_default_pool(config=mock_config)
            pool2 = get_default_pool(config=mock_config)

            assert pool1 is pool2  # Mismo singleton

            close_default_pool()

    def test_close_default_pool(self, mock_config):
        """Verifica cierre de pool por defecto"""
        close_default_pool()  # Asegurar que está limpio

        with patch('modules.db_pool.DB2Connection') as MockDB2:
            mock_conn = Mock(spec=DB2Connection)
            mock_conn.is_connected.return_value = True
            MockDB2.return_value = mock_conn

            pool = get_default_pool(config=mock_config)
            assert pool is not None

            close_default_pool()

            # Obtener de nuevo debe crear uno nuevo
            pool2 = get_default_pool(config=mock_config)
            assert pool2 is not pool

            close_default_pool()
