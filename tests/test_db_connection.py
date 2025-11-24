"""
═══════════════════════════════════════════════════════════════
TESTS - MÓDULO DE CONEXIÓN A BASE DE DATOS DB2
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Suite de tests para el módulo db_connection.py

Ejecutar tests:
    pytest tests/test_db_connection.py -v
    pytest tests/test_db_connection.py -v --cov=modules/db_connection

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
═══════════════════════════════════════════════════════════════
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import sys
import os

# Agregar path del proyecto para imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.db_connection import (
    DB2Connection,
    DB2ConnectionPool,
    ConnectionDriver,
    ConnectionStatus,
    ConnectionStats,
    QueryResult,
    DB2ConnectionError,
    DB2QueryError,
    DB2ConfigurationError,
    DB2PoolExhaustedError,
    test_connection,
    get_connection_info,
    PYODBC_AVAILABLE,
    IBM_DB_AVAILABLE
)


# ═══════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════

@pytest.fixture
def mock_config():
    """Configuración de prueba"""
    return {
        'host': 'test_host',
        'port': 50000,
        'database': 'test_db',
        'user': 'test_user',
        'password': 'test_password',
        'driver': '{IBM DB2 ODBC DRIVER}',
        'timeout': 30
    }


@pytest.fixture
def mock_config_invalid():
    """Configuración inválida (sin password)"""
    return {
        'host': 'test_host',
        'port': 50000,
        'database': 'test_db',
        'user': 'test_user',
        'password': None,
        'driver': '{IBM DB2 ODBC DRIVER}',
        'timeout': 30
    }


@pytest.fixture
def mock_pyodbc_connection():
    """Mock de conexión pyodbc"""
    mock_conn = Mock()
    mock_cursor = Mock()
    mock_cursor.description = [('COL1',), ('COL2',), ('COL3',)]
    mock_cursor.fetchall.return_value = [(1, 'a', 100), (2, 'b', 200)]
    mock_cursor.fetchone.return_value = (1,)
    mock_conn.cursor.return_value = mock_cursor
    return mock_conn, mock_cursor


# ═══════════════════════════════════════════════════════════════
# TESTS - INICIALIZACIÓN
# ═══════════════════════════════════════════════════════════════

class TestDB2ConnectionInit:
    """Tests para inicialización de DB2Connection"""

    def test_init_with_default_config(self):
        """Test inicialización con configuración por defecto"""
        # Debe poder inicializar si hay drivers disponibles
        if PYODBC_AVAILABLE or IBM_DB_AVAILABLE:
            conn = DB2Connection()
            assert conn.status == ConnectionStatus.DISCONNECTED
            assert conn.connection is None
            assert conn.cursor is None

    def test_init_with_custom_config(self, mock_config):
        """Test inicialización con configuración personalizada"""
        if PYODBC_AVAILABLE or IBM_DB_AVAILABLE:
            conn = DB2Connection(config=mock_config)
            assert conn.config == mock_config
            assert conn.status == ConnectionStatus.DISCONNECTED

    def test_init_retry_settings(self, mock_config):
        """Test configuración de retry"""
        if PYODBC_AVAILABLE or IBM_DB_AVAILABLE:
            conn = DB2Connection(
                config=mock_config,
                max_retries=5,
                base_delay=1.0,
                max_delay=60.0
            )
            assert conn.max_retries == 5
            assert conn.base_delay == 1.0
            assert conn.max_delay == 60.0

    def test_init_invalid_config(self, mock_config_invalid):
        """Test que falla con configuración inválida"""
        if PYODBC_AVAILABLE or IBM_DB_AVAILABLE:
            with pytest.raises(DB2ConfigurationError):
                DB2Connection(config=mock_config_invalid)


# ═══════════════════════════════════════════════════════════════
# TESTS - DRIVER SELECTION
# ═══════════════════════════════════════════════════════════════

class TestDriverSelection:
    """Tests para selección de driver"""

    def test_auto_driver_selection(self, mock_config):
        """Test selección automática de driver"""
        if PYODBC_AVAILABLE or IBM_DB_AVAILABLE:
            conn = DB2Connection(
                config=mock_config,
                driver=ConnectionDriver.AUTO
            )
            assert conn._selected_driver in ['pyodbc', 'ibm_db']

    @pytest.mark.skipif(not PYODBC_AVAILABLE, reason="pyodbc no disponible")
    def test_pyodbc_driver_selection(self, mock_config):
        """Test selección explícita de pyodbc"""
        conn = DB2Connection(
            config=mock_config,
            driver=ConnectionDriver.PYODBC
        )
        assert conn._selected_driver == 'pyodbc'

    @pytest.mark.skipif(not IBM_DB_AVAILABLE, reason="ibm_db no disponible")
    def test_ibm_db_driver_selection(self, mock_config):
        """Test selección explícita de ibm_db"""
        conn = DB2Connection(
            config=mock_config,
            driver=ConnectionDriver.IBM_DB
        )
        assert conn._selected_driver == 'ibm_db'


# ═══════════════════════════════════════════════════════════════
# TESTS - CONNECTION STRING
# ═══════════════════════════════════════════════════════════════

class TestConnectionString:
    """Tests para construcción de connection string"""

    def test_build_pyodbc_connection_string(self, mock_config):
        """Test construcción de string ODBC para pyodbc"""
        if PYODBC_AVAILABLE:
            conn = DB2Connection(
                config=mock_config,
                driver=ConnectionDriver.PYODBC
            )
            conn_str = conn._build_connection_string()

            assert 'DRIVER=' in conn_str
            assert f"HOSTNAME={mock_config['host']}" in conn_str
            assert f"PORT={mock_config['port']}" in conn_str
            assert f"DATABASE={mock_config['database']}" in conn_str
            assert f"UID={mock_config['user']}" in conn_str

    def test_connection_string_has_timeout(self, mock_config):
        """Test que el string incluye timeout"""
        if PYODBC_AVAILABLE:
            conn = DB2Connection(
                config=mock_config,
                driver=ConnectionDriver.PYODBC
            )
            conn_str = conn._build_connection_string()
            assert 'CONNECTTIMEOUT=' in conn_str


# ═══════════════════════════════════════════════════════════════
# TESTS - BACKOFF CALCULATION
# ═══════════════════════════════════════════════════════════════

class TestBackoffCalculation:
    """Tests para cálculo de backoff exponencial"""

    def test_calculate_delay_first_attempt(self, mock_config):
        """Test delay para primer intento"""
        if PYODBC_AVAILABLE or IBM_DB_AVAILABLE:
            conn = DB2Connection(config=mock_config, base_delay=2.0)
            delay = conn._calculate_delay(0)
            assert delay == 2.0

    def test_calculate_delay_exponential(self, mock_config):
        """Test delay exponencial"""
        if PYODBC_AVAILABLE or IBM_DB_AVAILABLE:
            conn = DB2Connection(config=mock_config, base_delay=2.0)
            assert conn._calculate_delay(0) == 2.0
            assert conn._calculate_delay(1) == 4.0
            assert conn._calculate_delay(2) == 8.0
            assert conn._calculate_delay(3) == 16.0

    def test_calculate_delay_respects_max(self, mock_config):
        """Test que delay respeta máximo"""
        if PYODBC_AVAILABLE or IBM_DB_AVAILABLE:
            conn = DB2Connection(
                config=mock_config,
                base_delay=2.0,
                max_delay=10.0
            )
            delay = conn._calculate_delay(10)  # Sin límite sería 2048
            assert delay == 10.0


# ═══════════════════════════════════════════════════════════════
# TESTS - CONNECTION (MOCKED)
# ═══════════════════════════════════════════════════════════════

class TestConnection:
    """Tests para conexión a DB2 (con mocks)"""

    @pytest.mark.skipif(not PYODBC_AVAILABLE, reason="pyodbc no disponible")
    @patch('modules.db_connection.pyodbc')
    def test_connect_success(self, mock_pyodbc, mock_config, mock_pyodbc_connection):
        """Test conexión exitosa"""
        mock_conn, mock_cursor = mock_pyodbc_connection
        mock_pyodbc.connect.return_value = mock_conn

        conn = DB2Connection(config=mock_config)
        result = conn.connect()

        assert result is True
        assert conn.status == ConnectionStatus.CONNECTED
        assert conn.stats.successful_connections == 1

    @pytest.mark.skipif(not PYODBC_AVAILABLE, reason="pyodbc no disponible")
    @patch('modules.db_connection.pyodbc')
    def test_connect_failure_retries(self, mock_pyodbc, mock_config):
        """Test que reintenta en caso de fallo"""
        mock_pyodbc.connect.side_effect = Exception("Connection failed")

        conn = DB2Connection(
            config=mock_config,
            max_retries=2,
            base_delay=0.01  # Delay muy corto para tests
        )

        with pytest.raises(DB2ConnectionError):
            conn.connect()

        assert conn.stats.total_retry_attempts >= 1
        assert conn.stats.failed_connections == 1

    @pytest.mark.skipif(not PYODBC_AVAILABLE, reason="pyodbc no disponible")
    @patch('modules.db_connection.pyodbc')
    def test_disconnect(self, mock_pyodbc, mock_config, mock_pyodbc_connection):
        """Test desconexión"""
        mock_conn, mock_cursor = mock_pyodbc_connection
        mock_pyodbc.connect.return_value = mock_conn

        conn = DB2Connection(config=mock_config)
        conn.connect()
        result = conn.disconnect()

        assert result is True
        assert conn.status == ConnectionStatus.DISCONNECTED
        assert conn.connection is None


# ═══════════════════════════════════════════════════════════════
# TESTS - QUERY EXECUTION (MOCKED)
# ═══════════════════════════════════════════════════════════════

class TestQueryExecution:
    """Tests para ejecución de queries"""

    @pytest.mark.skipif(not PYODBC_AVAILABLE, reason="pyodbc no disponible")
    @patch('modules.db_connection.pyodbc')
    def test_execute_query_returns_dataframe(
        self, mock_pyodbc, mock_config, mock_pyodbc_connection
    ):
        """Test que execute_query retorna DataFrame"""
        mock_conn, mock_cursor = mock_pyodbc_connection
        mock_pyodbc.connect.return_value = mock_conn

        conn = DB2Connection(config=mock_config)
        conn.connect()
        result = conn.execute_query("SELECT * FROM TEST")

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert list(result.columns) == ['COL1', 'COL2', 'COL3']

    @pytest.mark.skipif(not PYODBC_AVAILABLE, reason="pyodbc no disponible")
    @patch('modules.db_connection.pyodbc')
    def test_execute_query_with_params(
        self, mock_pyodbc, mock_config, mock_pyodbc_connection
    ):
        """Test execute_query con parámetros"""
        mock_conn, mock_cursor = mock_pyodbc_connection
        mock_pyodbc.connect.return_value = mock_conn

        conn = DB2Connection(config=mock_config)
        conn.connect()
        conn.execute_query("SELECT * FROM TEST WHERE ID = ?", params=(1,))

        mock_cursor.execute.assert_called_with(
            "SELECT * FROM TEST WHERE ID = ?",
            (1,)
        )

    @pytest.mark.skipif(not PYODBC_AVAILABLE, reason="pyodbc no disponible")
    @patch('modules.db_connection.pyodbc')
    def test_execute_query_updates_stats(
        self, mock_pyodbc, mock_config, mock_pyodbc_connection
    ):
        """Test que execute_query actualiza estadísticas"""
        mock_conn, mock_cursor = mock_pyodbc_connection
        mock_pyodbc.connect.return_value = mock_conn

        conn = DB2Connection(config=mock_config)
        conn.connect()
        conn.execute_query("SELECT * FROM TEST")

        assert conn.stats.total_queries == 1
        assert conn.stats.successful_queries == 1
        assert conn.stats.last_query_time is not None

    @pytest.mark.skipif(not PYODBC_AVAILABLE, reason="pyodbc no disponible")
    @patch('modules.db_connection.pyodbc')
    def test_execute_query_returns_query_result(
        self, mock_pyodbc, mock_config, mock_pyodbc_connection
    ):
        """Test execute_query con fetch_as_df=False"""
        mock_conn, mock_cursor = mock_pyodbc_connection
        mock_pyodbc.connect.return_value = mock_conn

        conn = DB2Connection(config=mock_config)
        conn.connect()
        result = conn.execute_query("SELECT * FROM TEST", fetch_as_df=False)

        assert isinstance(result, QueryResult)
        assert result.success is True
        assert result.rows_affected == 2
        assert isinstance(result.data, pd.DataFrame)


# ═══════════════════════════════════════════════════════════════
# TESTS - CONTEXT MANAGER
# ═══════════════════════════════════════════════════════════════

class TestContextManager:
    """Tests para context manager"""

    @pytest.mark.skipif(not PYODBC_AVAILABLE, reason="pyodbc no disponible")
    @patch('modules.db_connection.pyodbc')
    def test_context_manager_connects(
        self, mock_pyodbc, mock_config, mock_pyodbc_connection
    ):
        """Test que context manager conecta al entrar"""
        mock_conn, mock_cursor = mock_pyodbc_connection
        mock_pyodbc.connect.return_value = mock_conn

        with DB2Connection(config=mock_config) as conn:
            assert conn.status == ConnectionStatus.CONNECTED

    @pytest.mark.skipif(not PYODBC_AVAILABLE, reason="pyodbc no disponible")
    @patch('modules.db_connection.pyodbc')
    def test_context_manager_disconnects(
        self, mock_pyodbc, mock_config, mock_pyodbc_connection
    ):
        """Test que context manager desconecta al salir"""
        mock_conn, mock_cursor = mock_pyodbc_connection
        mock_pyodbc.connect.return_value = mock_conn

        with DB2Connection(config=mock_config) as conn:
            pass

        assert conn.status == ConnectionStatus.DISCONNECTED


# ═══════════════════════════════════════════════════════════════
# TESTS - STATISTICS
# ═══════════════════════════════════════════════════════════════

class TestStatistics:
    """Tests para estadísticas"""

    def test_get_stats_returns_dict(self, mock_config):
        """Test que get_stats retorna diccionario"""
        if PYODBC_AVAILABLE or IBM_DB_AVAILABLE:
            conn = DB2Connection(config=mock_config)
            stats = conn.get_stats()

            assert isinstance(stats, dict)
            assert 'status' in stats
            assert 'driver' in stats
            assert 'total_connections' in stats
            assert 'successful_queries' in stats

    def test_stats_initial_values(self, mock_config):
        """Test valores iniciales de estadísticas"""
        if PYODBC_AVAILABLE or IBM_DB_AVAILABLE:
            conn = DB2Connection(config=mock_config)

            assert conn.stats.total_connections == 0
            assert conn.stats.successful_connections == 0
            assert conn.stats.failed_connections == 0
            assert conn.stats.total_queries == 0


# ═══════════════════════════════════════════════════════════════
# TESTS - CONNECTION POOL
# ═══════════════════════════════════════════════════════════════

class TestConnectionPool:
    """Tests para pool de conexiones"""

    @pytest.mark.skipif(not PYODBC_AVAILABLE, reason="pyodbc no disponible")
    @patch('modules.db_connection.pyodbc')
    def test_pool_initialization(self, mock_pyodbc, mock_config, mock_pyodbc_connection):
        """Test inicialización del pool"""
        mock_conn, mock_cursor = mock_pyodbc_connection
        mock_pyodbc.connect.return_value = mock_conn

        pool = DB2ConnectionPool(
            config=mock_config,
            min_connections=2,
            max_connections=5
        )

        assert pool.min_connections == 2
        assert pool.max_connections == 5

    @pytest.mark.skipif(not PYODBC_AVAILABLE, reason="pyodbc no disponible")
    @patch('modules.db_connection.pyodbc')
    def test_pool_get_connection(self, mock_pyodbc, mock_config, mock_pyodbc_connection):
        """Test obtener conexión del pool"""
        mock_conn, mock_cursor = mock_pyodbc_connection
        mock_pyodbc.connect.return_value = mock_conn

        pool = DB2ConnectionPool(
            config=mock_config,
            min_connections=1,
            max_connections=5
        )

        with pool.get_connection() as conn:
            assert isinstance(conn, DB2Connection)
            assert conn.status == ConnectionStatus.CONNECTED

    @pytest.mark.skipif(not PYODBC_AVAILABLE, reason="pyodbc no disponible")
    @patch('modules.db_connection.pyodbc')
    def test_pool_stats(self, mock_pyodbc, mock_config, mock_pyodbc_connection):
        """Test estadísticas del pool"""
        mock_conn, mock_cursor = mock_pyodbc_connection
        mock_pyodbc.connect.return_value = mock_conn

        pool = DB2ConnectionPool(
            config=mock_config,
            min_connections=1,
            max_connections=5
        )

        stats = pool.get_pool_stats()

        assert 'min_connections' in stats
        assert 'max_connections' in stats
        assert 'created_connections' in stats
        assert 'active_connections' in stats


# ═══════════════════════════════════════════════════════════════
# TESTS - UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════

class TestUtilityFunctions:
    """Tests para funciones utilitarias"""

    def test_get_connection_info(self):
        """Test get_connection_info retorna diccionario"""
        info = get_connection_info()

        assert isinstance(info, dict)
        assert 'host' in info
        assert 'port' in info
        assert 'database' in info
        assert 'user' in info
        assert 'password_configured' in info
        assert 'pyodbc_available' in info
        assert 'ibm_db_available' in info

    def test_get_connection_info_hides_password(self):
        """Test que get_connection_info no expone password"""
        info = get_connection_info()
        assert 'password' not in info
        assert 'password_configured' in info


# ═══════════════════════════════════════════════════════════════
# TESTS - DATA CLASSES
# ═══════════════════════════════════════════════════════════════

class TestDataClasses:
    """Tests para data classes"""

    def test_connection_stats_defaults(self):
        """Test valores por defecto de ConnectionStats"""
        stats = ConnectionStats()

        assert stats.total_connections == 0
        assert stats.successful_connections == 0
        assert stats.failed_connections == 0
        assert stats.total_queries == 0
        assert stats.last_connection_time is None
        assert stats.last_error is None

    def test_query_result_success(self):
        """Test QueryResult exitoso"""
        df = pd.DataFrame({'col1': [1, 2], 'col2': ['a', 'b']})
        result = QueryResult(
            success=True,
            data=df,
            rows_affected=2,
            execution_time=0.5
        )

        assert result.success is True
        assert result.rows_affected == 2
        assert result.execution_time == 0.5
        assert result.error_message is None

    def test_query_result_failure(self):
        """Test QueryResult con error"""
        result = QueryResult(
            success=False,
            error_message="Query failed"
        )

        assert result.success is False
        assert result.data is None
        assert result.error_message == "Query failed"


# ═══════════════════════════════════════════════════════════════
# TESTS - ENUMS
# ═══════════════════════════════════════════════════════════════

class TestEnums:
    """Tests para enums"""

    def test_connection_driver_values(self):
        """Test valores de ConnectionDriver"""
        assert ConnectionDriver.PYODBC.value == 'pyodbc'
        assert ConnectionDriver.IBM_DB.value == 'ibm_db'
        assert ConnectionDriver.AUTO.value == 'auto'

    def test_connection_status_values(self):
        """Test valores de ConnectionStatus"""
        assert ConnectionStatus.DISCONNECTED.value == 'desconectado'
        assert ConnectionStatus.CONNECTED.value == 'conectado'
        assert ConnectionStatus.ERROR.value == 'error'
        assert ConnectionStatus.CONNECTING.value == 'conectando'


# ═══════════════════════════════════════════════════════════════
# TESTS - EXCEPTIONS
# ═══════════════════════════════════════════════════════════════

class TestExceptions:
    """Tests para excepciones personalizadas"""

    def test_db2_connection_error(self):
        """Test DB2ConnectionError"""
        with pytest.raises(DB2ConnectionError):
            raise DB2ConnectionError("Test connection error")

    def test_db2_query_error(self):
        """Test DB2QueryError"""
        with pytest.raises(DB2QueryError):
            raise DB2QueryError("Test query error")

    def test_db2_configuration_error(self):
        """Test DB2ConfigurationError"""
        with pytest.raises(DB2ConfigurationError):
            raise DB2ConfigurationError("Test config error")

    def test_db2_pool_exhausted_error(self):
        """Test DB2PoolExhaustedError"""
        with pytest.raises(DB2PoolExhaustedError):
            raise DB2PoolExhaustedError("Pool exhausted")


# ═══════════════════════════════════════════════════════════════
# TESTS - INTEGRATION (Requieren conexión real - skip por defecto)
# ═══════════════════════════════════════════════════════════════

@pytest.mark.skipif(
    os.getenv('RUN_INTEGRATION_TESTS', 'false').lower() != 'true',
    reason="Tests de integración deshabilitados. Set RUN_INTEGRATION_TESTS=true"
)
class TestIntegration:
    """Tests de integración (requieren DB2 real)"""

    def test_real_connection(self):
        """Test conexión real a DB2"""
        result = test_connection()
        assert result is True

    def test_real_query(self):
        """Test query real"""
        with DB2Connection() as conn:
            df = conn.execute_query("SELECT 1 AS TEST FROM SYSIBM.SYSDUMMY1")
            assert not df.empty
            assert df.iloc[0, 0] == 1


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Ejecutar tests con pytest
    pytest.main([__file__, "-v", "--tb=short"])
