"""
═══════════════════════════════════════════════════════════════
TESTS PARA VALIDADORES
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Tests unitarios para los validadores del sistema SAC.

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
═══════════════════════════════════════════════════════════════
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Agregar path del proyecto
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.validation_result import (
    ValidationStatus,
    Severity,
    DataType,
    ValidationResult,
)
from modules.validators import (
    OCValidator,
    DistributionValidator,
    ASNValidator,
    SKUValidator,
    LPNValidator,
)


# ═══════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════

@pytest.fixture
def df_oc_valida():
    """DataFrame de OC válida"""
    return pd.DataFrame({
        'SKU': ['SKU001', 'SKU002', 'SKU003'],
        'CANTIDAD': [100, 200, 150],
        'ID_CODE': ['C123', 'C124', 'C125'],
        'VIGENCIA': [datetime.now() + timedelta(days=15)] * 3,
    })


@pytest.fixture
def df_oc_vacia():
    """DataFrame de OC vacía"""
    return pd.DataFrame()


@pytest.fixture
def df_oc_vencida():
    """DataFrame de OC vencida"""
    return pd.DataFrame({
        'SKU': ['SKU001'],
        'CANTIDAD': [100],
        'VIGENCIA': [datetime.now() - timedelta(days=10)],
    })


@pytest.fixture
def df_distro_valida():
    """DataFrame de distribución válida"""
    return pd.DataFrame({
        'SKU': ['SKU001', 'SKU002', 'SKU003'],
        'CANTIDAD': [100, 200, 150],
        'TIENDA': ['T001', 'T002', 'T003'],
    })


@pytest.fixture
def df_distro_excedente():
    """DataFrame de distribución excedente (OC total: 100+200+150=450)"""
    return pd.DataFrame({
        'SKU': ['SKU001', 'SKU002'],
        'CANTIDAD': [300, 250],  # Total 550, excede OC total 450
        'TIENDA': ['T001', 'T002'],
    })


@pytest.fixture
def df_sku_valido():
    """DataFrame de SKU válido"""
    return pd.DataFrame({
        'SKU': ['SKU001', 'SKU002'],
        'IP': [12, 24],
        'UPC': ['123456789012', '123456789013'],
        'DESCRIPCION': ['Producto 1', 'Producto 2'],
    })


@pytest.fixture
def df_sku_sin_ip():
    """DataFrame de SKU sin Inner Pack"""
    return pd.DataFrame({
        'SKU': ['SKU001', 'SKU002'],
        'IP': [0, None],
        'UPC': ['123456789012', '123456789013'],
    })


@pytest.fixture
def df_lpn_valido():
    """DataFrame de LPN válido"""
    return pd.DataFrame({
        'LPN': ['LPN0001234', 'LPN0001235'],
        'LOC': ['A01-01-01', 'A01-01-02'],
        'STATUS': [20, 20],
    })


# ═══════════════════════════════════════════════════════════════
# TESTS - OCValidator
# ═══════════════════════════════════════════════════════════════

class TestOCValidator:
    """Tests para OCValidator"""

    def test_validar_formato_oc_valido(self):
        """Test formato OC válido (patrón Chedraui)"""
        validator = OCValidator()
        result = validator.validar_formato_oc("750384123456")
        assert result.is_valid

    def test_validar_formato_oc_invalido(self):
        """Test formato OC inválido"""
        validator = OCValidator()
        result = validator.validar_formato_oc("123")
        assert not result.is_valid
        assert len(result.violations) > 0

    def test_validar_formato_oc_vacio(self):
        """Test formato OC vacío"""
        validator = OCValidator()
        result = validator.validar_formato_oc("")
        assert not result.is_valid
        assert result.violations[0].code == "OC_NUMERO_VACIO"

    def test_validar_existencia_oc(self, df_oc_valida):
        """Test OC existente"""
        validator = OCValidator()
        result = validator.validar_existencia_oc(df_oc_valida)
        assert result.is_valid

    def test_validar_existencia_oc_vacia(self, df_oc_vacia):
        """Test OC no existente"""
        validator = OCValidator()
        result = validator.validar_existencia_oc(df_oc_vacia)
        assert not result.is_valid
        assert result.violations[0].code == "OC_NO_EXISTE"

    def test_validar_vigencia_oc_valida(self, df_oc_valida):
        """Test OC con vigencia válida"""
        validator = OCValidator()
        result = validator.validar_vigencia_oc(df_oc_valida)
        assert result.is_valid

    def test_validar_vigencia_oc_vencida(self, df_oc_vencida):
        """Test OC vencida"""
        validator = OCValidator()
        result = validator.validar_vigencia_oc(df_oc_vencida)
        assert not result.is_valid
        assert any(v.code == "OC_VENCIDA" for v in result.violations)

    def test_validar_totales_oc_validos(self, df_oc_valida):
        """Test totales OC válidos"""
        validator = OCValidator()
        result = validator.validar_totales_oc(df_oc_valida)
        assert result.is_valid

    def test_validar_totales_oc_negativos(self):
        """Test totales OC negativos"""
        df = pd.DataFrame({
            'SKU': ['SKU001'],
            'CANTIDAD': [-100],
        })
        validator = OCValidator()
        result = validator.validar_totales_oc(df)
        assert not result.is_valid

    def test_validar_oc_completa(self, df_oc_valida):
        """Test validación completa de OC"""
        validator = OCValidator()
        result = validator.validar_oc_completa(df_oc_valida, "750384123456")
        assert result.is_valid


# ═══════════════════════════════════════════════════════════════
# TESTS - DistributionValidator
# ═══════════════════════════════════════════════════════════════

class TestDistributionValidator:
    """Tests para DistributionValidator"""

    def test_validar_sin_distribuciones(self, df_oc_valida, df_oc_vacia):
        """Test sin distribuciones"""
        validator = DistributionValidator()
        result = validator.validar_sin_distribuciones(df_oc_valida, df_oc_vacia)
        assert not result.is_valid
        assert result.violations[0].code == "SIN_DISTRIBUCIONES"

    def test_validar_distribucion_valida(self, df_oc_valida, df_distro_valida):
        """Test distribución válida"""
        validator = DistributionValidator()
        result = validator.validar_distribucion_excedente(df_oc_valida, df_distro_valida)
        assert result.is_valid

    def test_validar_distribucion_excedente(self, df_oc_valida, df_distro_excedente):
        """Test distribución excedente"""
        validator = DistributionValidator()
        result = validator.validar_distribucion_excedente(df_oc_valida, df_distro_excedente)
        assert not result.is_valid
        assert any(v.code == "DISTRIBUCION_EXCEDENTE" for v in result.violations)

    def test_validar_tiendas(self, df_distro_valida):
        """Test validación de tiendas"""
        validator = DistributionValidator()
        result = validator.validar_tiendas(df_distro_valida)
        assert result.is_valid

    def test_validar_cantidades_validas(self, df_distro_valida):
        """Test cantidades válidas"""
        validator = DistributionValidator()
        result = validator.validar_cantidades(df_distro_valida)
        assert result.is_valid

    def test_validar_cantidades_negativas(self):
        """Test cantidades negativas"""
        df = pd.DataFrame({
            'SKU': ['SKU001'],
            'CANTIDAD': [-50],
            'TIENDA': ['T001'],
        })
        validator = DistributionValidator()
        result = validator.validar_cantidades(df)
        assert not result.is_valid

    def test_reconciliar_oc_distro(self, df_oc_valida, df_distro_valida):
        """Test reconciliación OC vs Distro"""
        validator = DistributionValidator()
        result = validator.reconciliar_oc_distro(df_oc_valida, df_distro_valida)
        assert result.is_reconciled


# ═══════════════════════════════════════════════════════════════
# TESTS - SKUValidator
# ═══════════════════════════════════════════════════════════════

class TestSKUValidator:
    """Tests para SKUValidator"""

    def test_validar_innerpack_valido(self, df_sku_valido):
        """Test Inner Pack válido"""
        validator = SKUValidator()
        result = validator.validar_innerpack(df_sku_valido)
        assert result.is_valid

    def test_validar_innerpack_invalido(self, df_sku_sin_ip):
        """Test Inner Pack inválido"""
        validator = SKUValidator()
        result = validator.validar_innerpack(df_sku_sin_ip)
        assert not result.is_valid
        assert any(v.code == "SKU_SIN_INNERPACK" for v in result.violations)

    def test_validar_upc_valido(self, df_sku_valido):
        """Test UPC válido"""
        validator = SKUValidator()
        result = validator.validar_upc(df_sku_valido)
        assert result.is_valid

    def test_validar_descripcion(self, df_sku_valido):
        """Test descripción presente"""
        validator = SKUValidator()
        result = validator.validar_descripcion(df_sku_valido)
        assert result.is_valid


# ═══════════════════════════════════════════════════════════════
# TESTS - LPNValidator
# ═══════════════════════════════════════════════════════════════

class TestLPNValidator:
    """Tests para LPNValidator"""

    def test_validar_formato_lpn_valido(self):
        """Test formato LPN válido"""
        validator = LPNValidator()
        result = validator.validar_formato_lpn("LPN0001234567")
        assert result.is_valid

    def test_validar_formato_lpn_invalido(self):
        """Test formato LPN inválido"""
        validator = LPNValidator()
        result = validator.validar_formato_lpn("ABC")
        assert not result.is_valid

    def test_validar_ubicacion_lpn(self, df_lpn_valido):
        """Test ubicación LPN válida"""
        validator = LPNValidator()
        result = validator.validar_ubicacion_lpn(df_lpn_valido)
        assert result.is_valid

    def test_validar_status_lpn(self, df_lpn_valido):
        """Test status LPN válido"""
        validator = LPNValidator()
        result = validator.validar_status_lpn(df_lpn_valido)
        assert result.is_valid


# ═══════════════════════════════════════════════════════════════
# TESTS - ASNValidator
# ═══════════════════════════════════════════════════════════════

class TestASNValidator:
    """Tests para ASNValidator"""

    def test_validar_formato_asn_valido(self):
        """Test formato ASN válido"""
        validator = ASNValidator()
        result = validator.validar_formato_asn("ASN12345678")
        assert result.is_valid

    def test_validar_formato_asn_vacio(self):
        """Test formato ASN vacío"""
        validator = ASNValidator()
        result = validator.validar_formato_asn("")
        assert not result.is_valid

    def test_validar_status_asn(self):
        """Test status ASN válido"""
        df = pd.DataFrame({
            'ASN': ['ASN12345678'],
            'STATUS': [40],
        })
        validator = ASNValidator()
        result = validator.validar_status_asn(df)
        assert result.is_valid


# ═══════════════════════════════════════════════════════════════
# EJECUCIÓN
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
