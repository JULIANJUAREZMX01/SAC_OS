"""
===============================================================
TESTS PARA REPOSITORIOS
Sistema de Automatización de Consultas - CEDIS Cancún 427
===============================================================

Tests unitarios para los repositorios.

Ejecutar:
    pytest tests/test_repositories.py -v

Autor: Julián Alexander Juárez Alvarado (ADMJAJA)
===============================================================
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import pandas as pd

# Importar módulos a testear
from modules.repositories import (
    BaseRepository,
    OCRepository,
    DistributionRepository,
    ASNRepository,
)
from modules.repositories.base_repository import (
    RepositoryError,
    EntityNotFoundError,
)
from modules.db_connection import DB2Connection


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
def mock_connection():
    """Mock de conexión DB2"""
    conn = Mock(spec=DB2Connection)
    conn.is_connected.return_value = True
    conn.status = Mock()
    conn.execute_query = Mock()
    conn.execute_non_query = Mock()
    return conn


# ===============================================================
# TESTS DE BASE REPOSITORY
# ===============================================================

class TestBaseRepository:
    """Tests de BaseRepository"""

    def test_base_repository_requires_table(self):
        """Verifica que BaseRepository requiere TABLE definido"""
        class InvalidRepo(BaseRepository):
            pass  # No define TABLE

        with pytest.raises(RepositoryError) as exc_info:
            InvalidRepo()
        assert "TABLE" in str(exc_info.value)

    def test_full_table_name(self, mock_connection):
        """Verifica construcción de nombre completo de tabla"""
        repo = OCRepository(connection=mock_connection)
        assert repo.full_table_name == "WMWHSE1.ORDERS"


# ===============================================================
# TESTS DE OC REPOSITORY
# ===============================================================

class TestOCRepository:
    """Tests de OCRepository"""

    def test_init(self, mock_connection):
        """Verifica inicialización"""
        repo = OCRepository(connection=mock_connection)
        assert repo.TABLE == "ORDERS"
        assert repo.PRIMARY_KEY == "ORDERKEY"

    def test_find_by_oc_number(self, mock_connection):
        """Verifica búsqueda por número de OC"""
        repo = OCRepository(connection=mock_connection)

        # Mock del resultado
        mock_df = pd.DataFrame({
            'ORDERKEY': ['OC001'],
            'EXTERNORDERKEY': ['C750384123456'],
            'STATUS': ['0']
        })
        mock_connection.execute_query.return_value = mock_df

        result = repo.find_by_oc_number('750384123456')

        assert not result.empty
        mock_connection.execute_query.assert_called_once()

    def test_find_by_oc_number_adds_prefix(self, mock_connection):
        """Verifica que se agrega prefijo C"""
        repo = OCRepository(connection=mock_connection)
        mock_connection.execute_query.return_value = pd.DataFrame()

        repo.find_by_oc_number('750384123456')

        # Verificar que los parámetros incluyen el prefijo C
        call_args = mock_connection.execute_query.call_args
        params = call_args[0][1]  # Segundo argumento (params)
        assert 'C750384123456' in params

    def test_find_pending_ocs(self, mock_connection):
        """Verifica búsqueda de OCs pendientes"""
        repo = OCRepository(connection=mock_connection)

        mock_df = pd.DataFrame({
            'ORDERKEY': ['OC001', 'OC002'],
            'STATUS': ['0', '1']
        })
        mock_connection.execute_query.return_value = mock_df

        result = repo.find_pending_ocs(days_back=30)

        assert len(result) == 2

    def test_find_expired_ocs(self, mock_connection):
        """Verifica búsqueda de OCs vencidas"""
        repo = OCRepository(connection=mock_connection)

        mock_df = pd.DataFrame({
            'ORDERKEY': ['OC001'],
            'DIAS_VENCIDA': [5]
        })
        mock_connection.execute_query.return_value = mock_df

        result = repo.find_expired_ocs()

        assert not result.empty

    def test_get_oc_summary_found(self, mock_connection):
        """Verifica resumen de OC encontrada"""
        repo = OCRepository(connection=mock_connection)

        mock_df = pd.DataFrame({
            'ORDERKEY': ['OC001'],
            'EXTERNORDERKEY': ['C750384123456'],
            'STORERKEY': ['C22'],
            'STATUS': ['0'],
            'ORDERDATE': [datetime.now()],
            'DELIVERYDATE': [datetime.now()],
            'SKU': ['SKU001'],
            'OPENQTY': [100],
            'SHIPPEDQTY': [50],
            'ORIGINALQTY': [100]
        })
        mock_connection.execute_query.return_value = mock_df

        summary = repo.get_oc_summary('C750384123456')

        assert summary['found'] is True
        assert 'total_lines' in summary
        assert 'completion_pct' in summary

    def test_get_oc_summary_not_found(self, mock_connection):
        """Verifica resumen de OC no encontrada"""
        repo = OCRepository(connection=mock_connection)
        mock_connection.execute_query.return_value = pd.DataFrame()

        summary = repo.get_oc_summary('INVALID')

        assert summary['found'] is False


# ===============================================================
# TESTS DE DISTRIBUTION REPOSITORY
# ===============================================================

class TestDistributionRepository:
    """Tests de DistributionRepository"""

    def test_init(self, mock_connection):
        """Verifica inicialización"""
        repo = DistributionRepository(connection=mock_connection)
        assert repo.TABLE == "ORDERDETAIL"

    def test_find_by_oc(self, mock_connection):
        """Verifica búsqueda de distribuciones por OC"""
        repo = DistributionRepository(connection=mock_connection)

        mock_df = pd.DataFrame({
            'SKU': ['SKU001', 'SKU002'],
            'TIENDA': ['T001', 'T002'],
            'QTY_SOLICITADA': [100, 200]
        })
        mock_connection.execute_query.return_value = mock_df

        result = repo.find_by_oc('C750384123456')

        assert len(result) == 2

    def test_find_by_store(self, mock_connection):
        """Verifica búsqueda por tienda"""
        repo = DistributionRepository(connection=mock_connection)

        mock_df = pd.DataFrame({
            'OC': ['OC001'],
            'SKU': ['SKU001'],
            'ORIGINALQTY': [100]
        })
        mock_connection.execute_query.return_value = mock_df

        result = repo.find_by_store('T001', days_back=30)

        assert not result.empty

    def test_get_distribution_totals(self, mock_connection):
        """Verifica obtención de totales"""
        repo = DistributionRepository(connection=mock_connection)

        mock_df = pd.DataFrame({
            'SKU': ['SKU001', 'SKU001'],
            'TIENDA': ['T001', 'T002'],
            'QTY_SOLICITADA': [100, 150],
            'QTY_PENDIENTE': [50, 75],
            'QTY_ENVIADA': [50, 75]
        })
        mock_connection.execute_query.return_value = mock_df

        totals = repo.get_distribution_totals('C750384123456')

        assert totals['found'] is True
        assert totals['qty_solicitada'] == 250
        assert 'pct_enviado' in totals

    def test_find_exceeding_distributions(self, mock_connection):
        """Verifica búsqueda de distribuciones excedentes"""
        repo = DistributionRepository(connection=mock_connection)

        mock_df = pd.DataFrame({
            'SKU': ['SKU001'],
            'TOTAL_DISTRIBUIDO': [150],
            'TOTAL_OC': [100],
            'EXCEDENTE': [50]
        })
        mock_connection.execute_query.return_value = mock_df

        result = repo.find_exceeding_distributions('C750384123456')

        assert len(result) == 1
        assert result.iloc[0]['EXCEDENTE'] == 50


# ===============================================================
# TESTS DE ASN REPOSITORY
# ===============================================================

class TestASNRepository:
    """Tests de ASNRepository"""

    def test_init(self, mock_connection):
        """Verifica inicialización"""
        repo = ASNRepository(connection=mock_connection)
        assert repo.TABLE == "ASN"
        assert repo.PRIMARY_KEY == "ASNKEY"

    def test_find_by_asn_number(self, mock_connection):
        """Verifica búsqueda por número de ASN"""
        repo = ASNRepository(connection=mock_connection)

        mock_df = pd.DataFrame({
            'ASNKEY': ['ASN001'],
            'EXTERNRECEIPTKEY': ['ASN123456'],
            'STATUS': ['0']
        })
        mock_connection.execute_query.return_value = mock_df

        result = repo.find_by_asn_number('ASN123456')

        assert not result.empty

    def test_find_pending_asns(self, mock_connection):
        """Verifica búsqueda de ASNs pendientes"""
        repo = ASNRepository(connection=mock_connection)

        mock_df = pd.DataFrame({
            'ASNKEY': ['ASN001', 'ASN002'],
            'STATUS': ['0', '1']
        })
        mock_connection.execute_query.return_value = mock_df

        result = repo.find_pending_asns(days_back=30)

        assert len(result) == 2

    def test_find_by_status(self, mock_connection):
        """Verifica búsqueda por estado"""
        repo = ASNRepository(connection=mock_connection)

        mock_df = pd.DataFrame({
            'ASNKEY': ['ASN001'],
            'STATUS': ['0']
        })
        mock_connection.execute_query.return_value = mock_df

        result = repo.find_by_status('0')

        assert not result.empty

    def test_find_stale_asns(self, mock_connection):
        """Verifica búsqueda de ASNs estancados"""
        repo = ASNRepository(connection=mock_connection)

        mock_df = pd.DataFrame({
            'ASNKEY': ['ASN001'],
            'HORAS_SIN_ACTUALIZAR': [48]
        })
        mock_connection.execute_query.return_value = mock_df

        result = repo.find_stale_asns(hours_threshold=24)

        assert not result.empty

    def test_get_asn_summary_found(self, mock_connection):
        """Verifica resumen de ASN encontrado"""
        repo = ASNRepository(connection=mock_connection)

        mock_df = pd.DataFrame({
            'ASNKEY': ['ASN001'],
            'EXTERNRECEIPTKEY': ['ASN123456'],
            'STORERKEY': ['C22'],
            'STATUS': ['0'],
            'EXPECTEDRECEIPTDATE': [datetime.now()],
            'SKU': ['SKU001'],
            'EXPECTEDQTY': [100],
            'RECEIVEDQTY': [50]
        })
        mock_connection.execute_query.return_value = mock_df

        summary = repo.get_asn_summary('ASN123456')

        assert summary['found'] is True
        assert summary['status_desc'] == 'Nuevo'
        assert 'reception_pct' in summary

    def test_get_asn_summary_not_found(self, mock_connection):
        """Verifica resumen de ASN no encontrado"""
        repo = ASNRepository(connection=mock_connection)
        mock_connection.execute_query.return_value = pd.DataFrame()

        summary = repo.get_asn_summary('INVALID')

        assert summary['found'] is False

    def test_get_reception_status(self, mock_connection):
        """Verifica estado de recepción"""
        repo = ASNRepository(connection=mock_connection)

        mock_df = pd.DataFrame({
            'ASNKEY': ['ASN001'],
            'EXTERNRECEIPTKEY': ['ASN123456'],
            'STORERKEY': ['C22'],
            'STATUS': ['0'],
            'EXPECTEDRECEIPTDATE': [datetime.now()],
            'SKU': ['SKU001'],
            'EXPECTEDQTY': [100],
            'RECEIVEDQTY': [100]  # 100% recibido
        })
        mock_connection.execute_query.return_value = mock_df

        status = repo.get_reception_status('ASN123456')

        assert status['reception_status'] == 'Completado'
        assert status['reception_alert'] == 'success'


# ===============================================================
# TESTS DE OPERACIONES CRUD
# ===============================================================

class TestCRUDOperations:
    """Tests de operaciones CRUD en repositorios"""

    def test_find_where(self, mock_connection):
        """Verifica búsqueda con condiciones"""
        repo = OCRepository(connection=mock_connection)

        mock_df = pd.DataFrame({
            'ORDERKEY': ['OC001'],
            'STATUS': ['0']
        })
        mock_connection.execute_query.return_value = mock_df

        result = repo.find_where({'STATUS': '0'})

        assert len(result) == 1

    def test_count(self, mock_connection):
        """Verifica conteo de registros"""
        repo = OCRepository(connection=mock_connection)

        mock_df = pd.DataFrame({'COUNT': [42]})
        mock_connection.execute_query.return_value = mock_df

        count = repo.count()

        assert count == 42

    def test_exists(self, mock_connection):
        """Verifica existencia de registro"""
        repo = OCRepository(connection=mock_connection)

        mock_df = pd.DataFrame({'COUNT': [1]})
        mock_connection.execute_query.return_value = mock_df

        exists = repo.exists('OC001')

        assert exists is True

    def test_to_dataframe(self, mock_connection):
        """Verifica conversión a DataFrame"""
        repo = OCRepository(connection=mock_connection)

        records = [
            {'ORDERKEY': 'OC001', 'STATUS': '0'},
            {'ORDERKEY': 'OC002', 'STATUS': '1'}
        ]

        df = repo.to_dataframe(records)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2


# ===============================================================
# TESTS DE CONTEXT MANAGER
# ===============================================================

class TestRepositoryContextManager:
    """Tests de context manager en repositorios"""

    def test_repository_as_context_manager(self, mock_config, mock_connection):
        """Verifica uso como context manager"""
        with patch('modules.repositories.base_repository.DB2Connection') as MockDB2:
            MockDB2.return_value = mock_connection

            with OCRepository(config=mock_config) as repo:
                assert repo is not None
