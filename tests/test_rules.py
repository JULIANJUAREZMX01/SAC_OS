"""
═══════════════════════════════════════════════════════════════
TESTS PARA MOTOR DE REGLAS
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Tests unitarios para el motor de reglas de negocio.

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
═══════════════════════════════════════════════════════════════
"""

import pytest
import pandas as pd
import sys
from pathlib import Path

# Agregar path del proyecto
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.validation_result import DataType, Severity
from modules.rules import RuleEngine, Rule, BusinessRules, REGLAS_PREDEFINIDAS


# ═══════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════

@pytest.fixture
def rule_engine():
    """Motor de reglas vacío"""
    return RuleEngine()


@pytest.fixture
def df_valido():
    """DataFrame válido para pruebas"""
    return pd.DataFrame({
        'SKU': ['SKU001', 'SKU002'],
        'CANTIDAD': [100, 200],
    })


@pytest.fixture
def df_vacio():
    """DataFrame vacío"""
    return pd.DataFrame()


# ═══════════════════════════════════════════════════════════════
# TESTS - Rule
# ═══════════════════════════════════════════════════════════════

class TestRule:
    """Tests para la clase Rule"""

    def test_crear_regla_basica(self):
        """Test crear regla básica"""
        rule = Rule(
            name="test_rule",
            description="Regla de prueba",
            category="TEST",
            severity=Severity.MEDIUM,
            condition=lambda df: True,
        )
        assert rule.name == "test_rule"
        assert rule.enabled == True
        assert rule.priority == 100

    def test_evaluar_regla_pasa(self, df_valido):
        """Test evaluar regla que pasa"""
        rule = Rule(
            name="datos_no_vacios",
            description="Datos no deben estar vacíos",
            category="TEST",
            severity=Severity.HIGH,
            condition=lambda df: isinstance(df, pd.DataFrame) and not df.empty,
        )
        result = rule.evaluate(df_valido)
        assert result.passed

    def test_evaluar_regla_falla(self, df_vacio):
        """Test evaluar regla que falla"""
        rule = Rule(
            name="datos_no_vacios",
            description="Datos no deben estar vacíos",
            category="TEST",
            severity=Severity.HIGH,
            condition=lambda df: isinstance(df, pd.DataFrame) and not df.empty,
        )
        result = rule.evaluate(df_vacio)
        assert not result.passed

    def test_regla_deshabilitada(self, df_vacio):
        """Test regla deshabilitada"""
        rule = Rule(
            name="regla_deshabilitada",
            description="Regla deshabilitada",
            category="TEST",
            severity=Severity.HIGH,
            condition=lambda df: False,  # Siempre fallaría
            enabled=False,
        )
        result = rule.evaluate(df_vacio)
        assert result.passed  # Pasa porque está deshabilitada


# ═══════════════════════════════════════════════════════════════
# TESTS - RuleEngine
# ═══════════════════════════════════════════════════════════════

class TestRuleEngine:
    """Tests para RuleEngine"""

    def test_agregar_regla(self, rule_engine):
        """Test agregar regla al motor"""
        rule = Rule(
            name="test_rule",
            description="Test",
            category="TEST",
            severity=Severity.LOW,
            condition=lambda df: True,
        )
        rule_engine.add_rule(rule)
        assert rule_engine.rules_count == 1

    def test_eliminar_regla(self, rule_engine):
        """Test eliminar regla del motor"""
        rule = Rule(
            name="test_rule",
            description="Test",
            category="TEST",
            severity=Severity.LOW,
            condition=lambda df: True,
        )
        rule_engine.add_rule(rule)
        assert rule_engine.remove_rule("test_rule")
        assert rule_engine.rules_count == 0

    def test_obtener_regla(self, rule_engine):
        """Test obtener regla por nombre"""
        rule = Rule(
            name="test_rule",
            description="Test",
            category="TEST",
            severity=Severity.LOW,
            condition=lambda df: True,
        )
        rule_engine.add_rule(rule)
        retrieved = rule_engine.get_rule("test_rule")
        assert retrieved is not None
        assert retrieved.name == "test_rule"

    def test_evaluar_todas_reglas(self, rule_engine, df_valido):
        """Test evaluar todas las reglas"""
        rule1 = Rule(
            name="rule1",
            description="Rule 1",
            category="TEST",
            severity=Severity.LOW,
            condition=lambda df: True,
        )
        rule2 = Rule(
            name="rule2",
            description="Rule 2",
            category="TEST",
            severity=Severity.LOW,
            condition=lambda df: isinstance(df, pd.DataFrame),
        )
        rule_engine.add_rule(rule1)
        rule_engine.add_rule(rule2)

        results = rule_engine.evaluate_all(df_valido)
        assert len(results) == 2
        assert all(r.passed for r in results)

    def test_obtener_reglas_por_categoria(self, rule_engine):
        """Test obtener reglas por categoría"""
        rule1 = Rule(name="rule1", description="R1", category="CAT_A",
                    severity=Severity.LOW, condition=lambda df: True)
        rule2 = Rule(name="rule2", description="R2", category="CAT_B",
                    severity=Severity.LOW, condition=lambda df: True)
        rule_engine.add_rule(rule1)
        rule_engine.add_rule(rule2)

        rules_a = rule_engine.get_rules_by_category("CAT_A")
        assert len(rules_a) == 1
        assert rules_a[0].name == "rule1"

    def test_habilitar_deshabilitar_regla(self, rule_engine):
        """Test habilitar/deshabilitar regla"""
        rule = Rule(name="test", description="Test", category="TEST",
                   severity=Severity.LOW, condition=lambda df: True)
        rule_engine.add_rule(rule)

        assert rule_engine.disable_rule("test")
        assert not rule_engine.get_rule("test").enabled

        assert rule_engine.enable_rule("test")
        assert rule_engine.get_rule("test").enabled

    def test_evaluar_y_resumir(self, rule_engine, df_valido):
        """Test evaluar y obtener resumen"""
        rule = Rule(name="test", description="Test", category="TEST",
                   severity=Severity.LOW, condition=lambda df: True)
        rule_engine.add_rule(rule)

        summary = rule_engine.evaluate_and_summarize(df_valido)
        assert 'total_rules' in summary
        assert 'passed' in summary
        assert 'failed' in summary
        assert summary['pass_rate'] == 100

    def test_limpiar_reglas(self, rule_engine):
        """Test limpiar todas las reglas"""
        rule = Rule(name="test", description="Test", category="TEST",
                   severity=Severity.LOW, condition=lambda df: True)
        rule_engine.add_rule(rule)
        rule_engine.clear_rules()
        assert rule_engine.rules_count == 0


# ═══════════════════════════════════════════════════════════════
# TESTS - BusinessRules
# ═══════════════════════════════════════════════════════════════

class TestBusinessRules:
    """Tests para BusinessRules"""

    def test_constantes_definidas(self):
        """Test constantes de reglas definidas"""
        assert BusinessRules.RULE_OC_MAX_DAYS == 30
        assert BusinessRules.RULE_DISTRO_TOLERANCE == 0.01
        assert BusinessRules.RULE_ASN_STALE_DAYS == 7

    def test_get_rule(self):
        """Test obtener regla por nombre"""
        valor = BusinessRules.get_rule("OC_MAX_DAYS")
        assert valor == 30

    def test_get_all_rules(self):
        """Test obtener todas las reglas"""
        rules = BusinessRules.get_all_rules()
        assert isinstance(rules, dict)
        assert len(rules) > 0
        assert 'RULE_OC_MAX_DAYS' in rules


# ═══════════════════════════════════════════════════════════════
# TESTS - Reglas Predefinidas
# ═══════════════════════════════════════════════════════════════

class TestReglasPredefinidas:
    """Tests para reglas predefinidas"""

    def test_reglas_predefinidas_existen(self):
        """Test reglas predefinidas existen"""
        assert len(REGLAS_PREDEFINIDAS) > 0

    def test_reglas_predefinidas_validas(self):
        """Test todas las reglas predefinidas son válidas"""
        for rule in REGLAS_PREDEFINIDAS:
            assert rule.name
            assert rule.description
            assert rule.category
            assert isinstance(rule.severity, Severity)

    def test_evaluar_reglas_predefinidas(self, df_valido):
        """Test evaluar reglas predefinidas con datos válidos"""
        engine = RuleEngine()
        for rule in REGLAS_PREDEFINIDAS:
            engine.add_rule(rule)

        results = engine.evaluate_all(df_valido)
        # Al menos algunas deberían pasar
        assert any(r.passed for r in results)


# ═══════════════════════════════════════════════════════════════
# EJECUCIÓN
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
