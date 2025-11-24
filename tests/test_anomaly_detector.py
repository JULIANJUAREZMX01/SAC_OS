"""
═══════════════════════════════════════════════════════════════
TESTS PARA DETECTOR DE ANOMALÍAS
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Tests unitarios para el detector de anomalías.

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
═══════════════════════════════════════════════════════════════
"""

import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Agregar path del proyecto
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.anomaly_detector import AnomalyDetector
from modules.reconciliation import ReconciliationEngine


# ═══════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════

@pytest.fixture
def detector():
    """Detector de anomalías"""
    return AnomalyDetector()


@pytest.fixture
def df_normal():
    """DataFrame con datos normales"""
    np.random.seed(42)
    return pd.DataFrame({
        'SKU': [f'SKU{i:03d}' for i in range(100)],
        'CANTIDAD': np.random.normal(100, 10, 100).astype(int),
        'PRECIO': np.random.uniform(10, 100, 100),
    })


@pytest.fixture
def df_con_outliers():
    """DataFrame con outliers"""
    np.random.seed(42)
    cantidades = np.random.normal(100, 10, 100).astype(int)
    cantidades[0] = 1000  # Outlier alto
    cantidades[1] = -50   # Outlier bajo
    return pd.DataFrame({
        'SKU': [f'SKU{i:03d}' for i in range(100)],
        'CANTIDAD': cantidades,
    })


@pytest.fixture
def df_con_duplicados():
    """DataFrame con duplicados"""
    return pd.DataFrame({
        'SKU': ['SKU001', 'SKU002', 'SKU001', 'SKU003', 'SKU002'],
        'CANTIDAD': [100, 200, 100, 150, 200],
    })


@pytest.fixture
def df_secuencia():
    """DataFrame con secuencia numérica"""
    return pd.DataFrame({
        'OC': ['OC001', 'OC002', 'OC003', 'OC005', 'OC006', 'OC008'],
    })


@pytest.fixture
def df_oc():
    """DataFrame de OC para reconciliación"""
    return pd.DataFrame({
        'SKU': ['SKU001', 'SKU002', 'SKU003'],
        'CANTIDAD': [100, 200, 150],
    })


@pytest.fixture
def df_distro():
    """DataFrame de distribución para reconciliación"""
    return pd.DataFrame({
        'SKU': ['SKU001', 'SKU002', 'SKU003'],
        'CANTIDAD': [100, 200, 150],
    })


@pytest.fixture
def df_distro_discrepancia():
    """DataFrame de distribución con discrepancias"""
    return pd.DataFrame({
        'SKU': ['SKU001', 'SKU002', 'SKU004'],  # SKU003 falta, SKU004 extra
        'CANTIDAD': [100, 250, 100],  # SKU002 tiene 50 de más
    })


# ═══════════════════════════════════════════════════════════════
# TESTS - AnomalyDetector
# ═══════════════════════════════════════════════════════════════

class TestAnomalyDetector:
    """Tests para AnomalyDetector"""

    def test_detector_inicializado(self, detector):
        """Test detector inicializado correctamente"""
        assert detector is not None
        assert detector.anomaly_count == 0

    def test_detectar_outliers_iqr(self, detector, df_con_outliers):
        """Test detectar outliers con método IQR"""
        outliers = detector.detect_outliers(df_con_outliers, 'CANTIDAD', method='iqr')
        assert not outliers.empty
        assert len(outliers) > 0

    def test_detectar_outliers_zscore(self, detector, df_con_outliers):
        """Test detectar outliers con método Z-score"""
        outliers = detector.detect_outliers(df_con_outliers, 'CANTIDAD', method='zscore')
        assert not outliers.empty

    def test_no_detectar_outliers_datos_normales(self, detector, df_normal):
        """Test no detectar outliers en datos normales"""
        detector.clear_anomalies()
        outliers = detector.detect_outliers(df_normal, 'CANTIDAD')
        # Puede haber algunos outliers naturales, pero deberían ser pocos
        assert len(outliers) < len(df_normal) * 0.1  # Menos del 10%

    def test_detectar_duplicados(self, detector, df_con_duplicados):
        """Test detectar duplicados"""
        duplicados = detector.detect_duplicates(df_con_duplicados, columns=['SKU', 'CANTIDAD'])
        assert not duplicados.empty
        assert len(duplicados) >= 2

    def test_detectar_duplicados_columna_unica(self, detector, df_con_duplicados):
        """Test detectar duplicados en columna única"""
        duplicados = detector.detect_duplicates(df_con_duplicados, columns=['SKU'])
        assert not duplicados.empty

    def test_no_duplicados(self, detector, df_normal):
        """Test no detectar duplicados cuando no hay"""
        duplicados = detector.detect_duplicates(df_normal, columns=['SKU'])
        assert duplicados.empty

    def test_detectar_secuencias_faltantes(self, detector, df_secuencia):
        """Test detectar secuencias faltantes"""
        faltantes = detector.detect_missing_sequences(df_secuencia, 'OC', prefix='OC')
        assert len(faltantes) > 0
        assert 4 in faltantes  # OC004 falta
        assert 7 in faltantes  # OC007 falta

    def test_detectar_patrones_inusuales(self, detector, df_con_outliers):
        """Test detectar patrones inusuales"""
        patrones = detector.detect_unusual_patterns(df_con_outliers)
        # Debería detectar algo dado los outliers
        assert isinstance(patrones, list)

    def test_generar_reporte_anomalias(self, detector, df_con_outliers):
        """Test generar reporte de anomalías"""
        report = detector.generate_anomaly_report(
            df_con_outliers,
            numeric_columns=['CANTIDAD'],
            key_columns=['SKU'],
        )
        assert report.total_records_analyzed == len(df_con_outliers)
        assert hasattr(report, 'anomalies')
        assert hasattr(report, 'outliers_count')

    def test_analizar_columna(self, detector, df_normal):
        """Test analizar columna individual"""
        analysis = detector.analyze_column(df_normal, 'CANTIDAD')
        assert 'column' in analysis
        assert 'min' in analysis
        assert 'max' in analysis
        assert 'mean' in analysis

    def test_limpiar_anomalias(self, detector, df_con_outliers):
        """Test limpiar anomalías detectadas"""
        detector.detect_outliers(df_con_outliers, 'CANTIDAD')
        assert detector.anomaly_count > 0
        detector.clear_anomalies()
        assert detector.anomaly_count == 0


# ═══════════════════════════════════════════════════════════════
# TESTS - ReconciliationEngine
# ═══════════════════════════════════════════════════════════════

class TestReconciliationEngine:
    """Tests para ReconciliationEngine"""

    def test_reconciliar_oc_distro_coincide(self, df_oc, df_distro):
        """Test reconciliación OC vs Distro cuando coinciden"""
        engine = ReconciliationEngine()
        result = engine.reconcile_oc_vs_distro(df_oc, df_distro)
        assert result.is_reconciled
        assert len(result.discrepancies) == 0
        assert result.matched_records == 3

    def test_reconciliar_oc_distro_discrepancia(self, df_oc, df_distro_discrepancia):
        """Test reconciliación OC vs Distro con discrepancias"""
        engine = ReconciliationEngine()
        result = engine.reconcile_oc_vs_distro(df_oc, df_distro_discrepancia)
        assert not result.is_reconciled
        assert len(result.discrepancies) > 0 or len(result.missing_in_b) > 0

    def test_reconciliar_oc_vacia(self, df_distro):
        """Test reconciliación con OC vacía"""
        engine = ReconciliationEngine()
        result = engine.reconcile_oc_vs_distro(pd.DataFrame(), df_distro)
        assert not result.is_reconciled
        assert result.total_records_a == 0

    def test_reconciliar_distro_vacia(self, df_oc):
        """Test reconciliación con distribución vacía"""
        engine = ReconciliationEngine()
        result = engine.reconcile_oc_vs_distro(df_oc, pd.DataFrame())
        assert not result.is_reconciled
        assert result.total_records_b == 0

    def test_generar_reporte_discrepancias(self, df_oc, df_distro_discrepancia):
        """Test generar reporte de discrepancias"""
        engine = ReconciliationEngine()
        engine.reconcile_oc_vs_distro(df_oc, df_distro_discrepancia)
        report = engine.generate_discrepancy_report()
        assert isinstance(report, pd.DataFrame)

    def test_sugerir_correcciones(self, df_oc, df_distro_discrepancia):
        """Test sugerir correcciones"""
        engine = ReconciliationEngine()
        engine.reconcile_oc_vs_distro(df_oc, df_distro_discrepancia)
        suggestions = engine.suggest_corrections()
        assert isinstance(suggestions, list)

    def test_match_rate(self, df_oc, df_distro):
        """Test tasa de coincidencia"""
        engine = ReconciliationEngine()
        result = engine.reconcile_oc_vs_distro(df_oc, df_distro)
        assert result.match_rate == 100.0

    def test_reconciliar_inventario(self):
        """Test reconciliación de inventario"""
        df_sistema = pd.DataFrame({
            'SKU': ['SKU001', 'SKU002'],
            'CANTIDAD': [100, 200],
        })
        df_fisico = pd.DataFrame({
            'SKU': ['SKU001', 'SKU002'],
            'CANTIDAD': [100, 200],
        })
        engine = ReconciliationEngine()
        result = engine.reconcile_inventario(df_sistema, df_fisico)
        assert result.is_reconciled


# ═══════════════════════════════════════════════════════════════
# EJECUCIÓN
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
