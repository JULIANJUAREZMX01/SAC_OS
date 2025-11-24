"""
═══════════════════════════════════════════════════════════════
REGLAS DE NEGOCIO PREDEFINIDAS
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Reglas de negocio específicas para Planning/WMS de Chedraui.

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
═══════════════════════════════════════════════════════════════
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import pandas as pd

from .rule_engine import Rule, RuleEngine
from ..validation_result import DataType, Severity, ValidationViolation

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# CONSTANTES DE REGLAS DE NEGOCIO
# ═══════════════════════════════════════════════════════════════

@dataclass
class BusinessRules:
    """
    Constantes y parámetros de reglas de negocio

    Configuraciones específicas para CEDIS Chedraui.
    """

    # Reglas de OC
    RULE_OC_MAX_DAYS: int = 30  # Días máximos de vigencia
    RULE_OC_MIN_ITEMS: int = 1  # Mínimo de items por OC
    RULE_OC_MAX_ITEMS: int = 5000  # Máximo de items por OC

    # Reglas de Distribución
    RULE_DISTRO_TOLERANCE: float = 0.01  # 1% tolerancia
    RULE_DISTRO_MAX_EXCEDENTE: float = 0.0  # 0% excedente permitido
    RULE_DISTRO_MIN_CANTIDAD: int = 1  # Cantidad mínima

    # Reglas de ASN
    RULE_ASN_STALE_DAYS: int = 7  # Días para considerar estancado
    RULE_ASN_MAX_WAIT_DAYS: int = 14  # Días máximo de espera

    # Reglas de SKU
    RULE_SKU_MIN_IP: int = 1  # Inner Pack mínimo
    RULE_SKU_MAX_IP: int = 9999  # Inner Pack máximo
    RULE_SKU_DESC_MIN_LENGTH: int = 3  # Longitud mínima descripción

    # Reglas de LPN
    RULE_LPN_MIN_LENGTH: int = 6  # Longitud mínima
    RULE_LPN_MAX_LENGTH: int = 20  # Longitud máxima

    # Reglas de Inventario
    RULE_INV_NEGATIVE_ALLOWED: bool = False  # Inventario negativo
    RULE_INV_MAX_VARIANCE: float = 0.02  # 2% variación máxima

    # Reglas de Recibo
    RULE_RECEIPT_TOLERANCE: float = 0.05  # 5% tolerancia en recibo
    RULE_RECEIPT_MAX_OVERAGE: float = 0.0  # 0% sobre-recibo

    @classmethod
    def get_rule(cls, name: str) -> Any:
        """Obtiene el valor de una regla por nombre"""
        attr_name = f"RULE_{name.upper()}"
        return getattr(cls, attr_name, None)

    @classmethod
    def get_all_rules(cls) -> Dict[str, Any]:
        """Obtiene todas las reglas como diccionario"""
        return {
            attr: getattr(cls, attr)
            for attr in dir(cls)
            if attr.startswith('RULE_')
        }

    @classmethod
    def validate_against_rules(cls, data: pd.DataFrame,
                               data_type: DataType) -> List[ValidationViolation]:
        """
        Valida datos contra las reglas de negocio

        Args:
            data: DataFrame a validar
            data_type: Tipo de datos

        Returns:
            Lista de violaciones encontradas
        """
        violations = []

        if data is None or data.empty:
            return violations

        # Validaciones según tipo de dato
        if data_type == DataType.OC:
            violations.extend(cls._validate_oc_rules(data))
        elif data_type == DataType.DISTRIBUTION:
            violations.extend(cls._validate_distro_rules(data))
        elif data_type == DataType.ASN:
            violations.extend(cls._validate_asn_rules(data))
        elif data_type == DataType.SKU:
            violations.extend(cls._validate_sku_rules(data))

        return violations

    @classmethod
    def _validate_oc_rules(cls, df: pd.DataFrame) -> List[ValidationViolation]:
        """Valida reglas específicas de OC"""
        violations = []

        # Verificar número de items
        if len(df) > cls.RULE_OC_MAX_ITEMS:
            violations.append(ValidationViolation(
                code="OC_EXCEDE_MAX_ITEMS",
                message=f"OC excede máximo de items ({len(df)} > {cls.RULE_OC_MAX_ITEMS})",
                severity=Severity.HIGH,
            ))

        if len(df) < cls.RULE_OC_MIN_ITEMS:
            violations.append(ValidationViolation(
                code="OC_SIN_ITEMS",
                message=f"OC no tiene items suficientes ({len(df)} < {cls.RULE_OC_MIN_ITEMS})",
                severity=Severity.CRITICAL,
            ))

        return violations

    @classmethod
    def _validate_distro_rules(cls, df: pd.DataFrame) -> List[ValidationViolation]:
        """Valida reglas específicas de distribución"""
        violations = []

        # Verificar cantidades mínimas
        if 'CANTIDAD' in df.columns:
            below_min = df[df['CANTIDAD'] < cls.RULE_DISTRO_MIN_CANTIDAD]
            if not below_min.empty:
                violations.append(ValidationViolation(
                    code="DISTRO_CANTIDAD_INVALIDA",
                    message=f"{len(below_min)} distribuciones con cantidad menor a {cls.RULE_DISTRO_MIN_CANTIDAD}",
                    severity=Severity.HIGH,
                ))

        return violations

    @classmethod
    def _validate_asn_rules(cls, df: pd.DataFrame) -> List[ValidationViolation]:
        """Valida reglas específicas de ASN"""
        violations = []

        # Las validaciones específicas de ASN se manejan en ASNValidator
        return violations

    @classmethod
    def _validate_sku_rules(cls, df: pd.DataFrame) -> List[ValidationViolation]:
        """Valida reglas específicas de SKU"""
        violations = []

        # Verificar Inner Pack
        if 'IP' in df.columns:
            invalid_ip = df[
                (df['IP'] < cls.RULE_SKU_MIN_IP) |
                (df['IP'] > cls.RULE_SKU_MAX_IP)
            ]
            if not invalid_ip.empty:
                violations.append(ValidationViolation(
                    code="SKU_IP_FUERA_RANGO",
                    message=f"{len(invalid_ip)} SKUs con IP fuera de rango ({cls.RULE_SKU_MIN_IP}-{cls.RULE_SKU_MAX_IP})",
                    severity=Severity.MEDIUM,
                ))

        return violations


# ═══════════════════════════════════════════════════════════════
# REGLAS PREDEFINIDAS
# ═══════════════════════════════════════════════════════════════

def _oc_no_vacia(data):
    """Regla: OC no debe estar vacía"""
    if isinstance(data, pd.DataFrame):
        return not data.empty
    return data is not None


def _oc_tiene_sku(data):
    """Regla: OC debe tener columna SKU"""
    if isinstance(data, pd.DataFrame):
        return 'SKU' in data.columns or 'sku' in [c.lower() for c in data.columns]
    return False


def _distro_no_excede_oc(data):
    """Regla: Distribución no debe exceder OC"""
    # Esta regla requiere contexto adicional (df_oc)
    # Se implementa en el validador específico
    return True


def _asn_no_estancado(data):
    """Regla: ASN no debe estar estancado"""
    # Implementado en ASNValidator
    return True


def _sku_tiene_ip(data):
    """Regla: SKU debe tener Inner Pack"""
    if isinstance(data, pd.DataFrame):
        if 'IP' in data.columns:
            sin_ip = data[data['IP'].isna() | (data['IP'] == 0)]
            return sin_ip.empty
    return True


def _cantidades_positivas(data):
    """Regla: Todas las cantidades deben ser positivas"""
    if isinstance(data, pd.DataFrame):
        for col in ['CANTIDAD', 'QTY', 'QUANTITY']:
            if col in data.columns:
                if (data[col] < 0).any():
                    return False
    return True


# Lista de reglas predefinidas
REGLAS_PREDEFINIDAS: List[Rule] = [
    # Reglas de OC
    Rule(
        name="oc_no_vacia",
        description="La Orden de Compra no debe estar vacía",
        category="OC",
        severity=Severity.CRITICAL,
        condition=_oc_no_vacia,
        message_template="OC vacía - no contiene registros",
        priority=10,
        applicable_types=[DataType.OC],
    ),
    Rule(
        name="oc_tiene_sku",
        description="La OC debe contener información de SKU",
        category="OC",
        severity=Severity.HIGH,
        condition=_oc_tiene_sku,
        message_template="OC sin columna de SKU",
        priority=20,
        applicable_types=[DataType.OC],
    ),
    Rule(
        name="oc_max_items",
        description=f"OC no debe exceder {BusinessRules.RULE_OC_MAX_ITEMS} items",
        category="OC",
        severity=Severity.HIGH,
        condition=lambda df: len(df) <= BusinessRules.RULE_OC_MAX_ITEMS if isinstance(df, pd.DataFrame) else True,
        message_template=f"OC excede límite de {BusinessRules.RULE_OC_MAX_ITEMS} items",
        priority=30,
        applicable_types=[DataType.OC],
    ),

    # Reglas de Distribución
    Rule(
        name="distro_no_vacia",
        description="Las distribuciones no deben estar vacías",
        category="DISTRIBUCION",
        severity=Severity.CRITICAL,
        condition=lambda df: isinstance(df, pd.DataFrame) and not df.empty,
        message_template="Sin distribuciones asignadas",
        priority=10,
        applicable_types=[DataType.DISTRIBUTION],
    ),
    Rule(
        name="distro_cantidades_positivas",
        description="Las cantidades distribuidas deben ser positivas",
        category="DISTRIBUCION",
        severity=Severity.CRITICAL,
        condition=_cantidades_positivas,
        message_template="Cantidades negativas en distribución",
        priority=20,
        applicable_types=[DataType.DISTRIBUTION],
    ),

    # Reglas de SKU
    Rule(
        name="sku_tiene_innerpack",
        description="SKU debe tener Inner Pack configurado",
        category="SKU",
        severity=Severity.MEDIUM,
        condition=_sku_tiene_ip,
        message_template="SKUs sin Inner Pack configurado",
        priority=30,
        applicable_types=[DataType.SKU],
    ),

    # Reglas de ASN
    Rule(
        name="asn_existe",
        description="El ASN debe existir en el sistema",
        category="ASN",
        severity=Severity.HIGH,
        condition=lambda df: isinstance(df, pd.DataFrame) and not df.empty,
        message_template="ASN no encontrado en sistema",
        priority=10,
        applicable_types=[DataType.ASN],
    ),

    # Reglas de LPN
    Rule(
        name="lpn_tiene_ubicacion",
        description="LPN debe tener ubicación asignada",
        category="LPN",
        severity=Severity.HIGH,
        condition=lambda df: True,  # Implementado en LPNValidator
        message_template="LPN sin ubicación asignada",
        priority=20,
        applicable_types=[DataType.LPN],
    ),

    # Reglas Generales
    Rule(
        name="datos_no_nulos",
        description="Los datos críticos no deben ser nulos",
        category="GENERAL",
        severity=Severity.MEDIUM,
        condition=lambda df: isinstance(df, pd.DataFrame) and df.notna().any().any(),
        message_template="Se encontraron datos nulos en campos críticos",
        priority=50,
        applicable_types=[],  # Aplica a todos
    ),
]


def crear_motor_reglas_predefinido() -> RuleEngine:
    """
    Crea un motor de reglas con las reglas predefinidas cargadas

    Returns:
        RuleEngine con reglas predefinidas
    """
    engine = RuleEngine()

    for rule in REGLAS_PREDEFINIDAS:
        engine.add_rule(rule)

    logger.info(f"✅ Motor de reglas creado con {engine.rules_count} reglas predefinidas")
    return engine


# ═══════════════════════════════════════════════════════════════
# EXPORTAR
# ═══════════════════════════════════════════════════════════════

__all__ = [
    'BusinessRules',
    'REGLAS_PREDEFINIDAS',
    'crear_motor_reglas_predefinido',
]
