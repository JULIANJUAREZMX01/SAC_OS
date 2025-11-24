"""
═══════════════════════════════════════════════════════════════
VALIDADOR DE SKU
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Validador especializado para SKUs y maestro de productos.

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
═══════════════════════════════════════════════════════════════
"""

import logging
import re
from typing import Any, Dict, List, Optional

import pandas as pd

from .base_validator import BaseValidator, ValidationRule
from ..validation_result import (
    DataType,
    Severity,
    ValidationResult,
    ValidationViolation,
    ValidationWarning,
)

logger = logging.getLogger(__name__)


class SKUValidator(BaseValidator):
    """
    Validador especializado para SKU/Productos

    Valida:
    - Inner Pack (IP) configurado
    - UPC válido
    - Descripción presente
    - Dimensiones del producto
    """

    def __init__(self):
        super().__init__(name="SKUValidator", data_type=DataType.SKU)

    def _register_default_rules(self) -> None:
        """Registra las reglas por defecto para SKU"""

        self.add_rule(ValidationRule(
            name="sku_not_empty",
            description="Datos de SKU no deben estar vacíos",
            severity=Severity.HIGH,
            validator_func=lambda df: isinstance(df, pd.DataFrame) and not df.empty,
            error_code="SKU_DATOS_VACIOS",
        ))

    # ═══════════════════════════════════════════════════════════════
    # VALIDACIONES ESPECÍFICAS
    # ═══════════════════════════════════════════════════════════════

    def validar_innerpack(self, df_sku: pd.DataFrame,
                         ip_col: str = 'IP') -> ValidationResult:
        """
        Valida que los SKUs tengan Inner Pack configurado

        Args:
            df_sku: DataFrame con datos de SKU
            ip_col: Columna de Inner Pack

        Returns:
            ValidationResult con validación de IP
        """
        violations = []
        warnings = []

        if df_sku is None or df_sku.empty:
            return ValidationResult.create_passed(
                "SKUValidator.validar_innerpack",
                DataType.SKU,
            )

        col = self._find_column(df_sku, ip_col)
        if col is None:
            warnings.append(ValidationWarning(
                code="SKU_SIN_COLUMNA_IP",
                message=f"No se encontró columna '{ip_col}'",
            ))
            result = ValidationResult.create_passed(
                "SKUValidator.validar_innerpack",
                DataType.SKU,
            )
            result.warnings = warnings
            return result

        # SKUs sin IP o con IP = 0
        sin_ip = df_sku[(df_sku[col].isna()) | (df_sku[col] == 0)]

        if not sin_ip.empty:
            sku_col = self._find_column(df_sku, 'SKU')
            skus_afectados = list(sin_ip[sku_col].unique()[:10]) if sku_col else []

            severity = Severity.HIGH if len(sin_ip) > 10 else Severity.MEDIUM

            violations.append(ValidationViolation(
                code="SKU_SIN_INNERPACK",
                message=f"{len(sin_ip)} SKUs sin Inner Pack configurado",
                severity=severity,
                suggestion="Actualizar Inner Pack en maestro de productos",
                affected_records=skus_afectados,
            ))

        # IP negativos
        ip_negativos = df_sku[df_sku[col] < 0]
        if not ip_negativos.empty:
            violations.append(ValidationViolation(
                code="SKU_IP_NEGATIVO",
                message=f"{len(ip_negativos)} SKUs con IP negativo",
                severity=Severity.CRITICAL,
            ))

        # IP muy altos (posible error)
        ip_altos = df_sku[df_sku[col] > 1000]
        if not ip_altos.empty:
            warnings.append(ValidationWarning(
                code="SKU_IP_ALTO",
                message=f"{len(ip_altos)} SKUs con IP mayor a 1000",
                details="Verificar que el IP sea correcto",
            ))

        if violations:
            result = ValidationResult.create_failed(
                "SKUValidator.validar_innerpack",
                violations,
                DataType.SKU,
            )
        else:
            result = ValidationResult.create_passed(
                "SKUValidator.validar_innerpack",
                DataType.SKU,
            )

        result.warnings = warnings
        return result

    def validar_upc(self, df_sku: pd.DataFrame,
                   upc_col: str = 'UPC') -> ValidationResult:
        """
        Valida los códigos UPC de los SKUs

        Args:
            df_sku: DataFrame con datos de SKU
            upc_col: Columna de UPC

        Returns:
            ValidationResult con validación de UPC
        """
        violations = []
        warnings = []

        if df_sku is None or df_sku.empty:
            return ValidationResult.create_passed(
                "SKUValidator.validar_upc",
                DataType.SKU,
            )

        col = self._find_column(df_sku, upc_col)
        if col is None:
            return ValidationResult.create_passed(
                "SKUValidator.validar_upc",
                DataType.SKU,
            )

        # UPC vacíos
        sin_upc = df_sku[df_sku[col].isna() | (df_sku[col].astype(str).str.strip() == '')]
        if not sin_upc.empty:
            warnings.append(ValidationWarning(
                code="SKU_SIN_UPC",
                message=f"{len(sin_upc)} SKUs sin código UPC",
            ))

        # Validar formato UPC (típicamente 12-14 dígitos)
        def es_upc_valido(upc):
            if pd.isna(upc):
                return True  # Ya contados como sin UPC
            upc_str = str(upc).strip()
            return bool(re.match(r'^\d{8,14}$', upc_str))

        df_con_upc = df_sku[~df_sku[col].isna()]
        if not df_con_upc.empty:
            upc_invalidos = df_con_upc[~df_con_upc[col].apply(es_upc_valido)]
            if not upc_invalidos.empty:
                violations.append(ValidationViolation(
                    code="SKU_UPC_INVALIDO",
                    message=f"{len(upc_invalidos)} SKUs con formato de UPC inválido",
                    severity=Severity.MEDIUM,
                    suggestion="Verificar que UPC tenga 8-14 dígitos",
                ))

        # Verificar UPCs duplicados
        upcs_duplicados = df_sku[col].dropna()
        duplicados = upcs_duplicados[upcs_duplicados.duplicated()]
        if not duplicados.empty:
            violations.append(ValidationViolation(
                code="SKU_UPC_DUPLICADO",
                message=f"{len(duplicados)} UPCs duplicados encontrados",
                severity=Severity.HIGH,
                suggestion="Verificar y corregir UPCs duplicados",
            ))

        if violations:
            result = ValidationResult.create_failed(
                "SKUValidator.validar_upc",
                violations,
                DataType.SKU,
            )
        else:
            result = ValidationResult.create_passed(
                "SKUValidator.validar_upc",
                DataType.SKU,
            )

        result.warnings = warnings
        return result

    def validar_descripcion(self, df_sku: pd.DataFrame,
                           desc_col: str = 'DESCRIPCION') -> ValidationResult:
        """
        Valida que los SKUs tengan descripción

        Args:
            df_sku: DataFrame con datos de SKU
            desc_col: Columna de descripción

        Returns:
            ValidationResult con validación de descripción
        """
        violations = []
        warnings = []

        if df_sku is None or df_sku.empty:
            return ValidationResult.create_passed(
                "SKUValidator.validar_descripcion",
                DataType.SKU,
            )

        col = self._find_column(df_sku, desc_col)
        if col is None:
            return ValidationResult.create_passed(
                "SKUValidator.validar_descripcion",
                DataType.SKU,
            )

        # Sin descripción
        sin_desc = df_sku[df_sku[col].isna() | (df_sku[col].astype(str).str.strip() == '')]
        if not sin_desc.empty:
            violations.append(ValidationViolation(
                code="SKU_SIN_DESCRIPCION",
                message=f"{len(sin_desc)} SKUs sin descripción",
                severity=Severity.MEDIUM,
                suggestion="Agregar descripción a todos los SKUs",
            ))

        # Descripciones muy cortas
        df_con_desc = df_sku[~(df_sku[col].isna() | (df_sku[col].astype(str).str.strip() == ''))]
        if not df_con_desc.empty:
            desc_cortas = df_con_desc[df_con_desc[col].astype(str).str.len() < 3]
            if not desc_cortas.empty:
                warnings.append(ValidationWarning(
                    code="SKU_DESC_CORTA",
                    message=f"{len(desc_cortas)} SKUs con descripción muy corta",
                ))

        if violations:
            result = ValidationResult.create_failed(
                "SKUValidator.validar_descripcion",
                violations,
                DataType.SKU,
            )
        else:
            result = ValidationResult.create_passed(
                "SKUValidator.validar_descripcion",
                DataType.SKU,
            )

        result.warnings = warnings
        return result

    def validar_dimensiones(self, df_sku: pd.DataFrame,
                           peso_col: str = 'PESO',
                           largo_col: str = 'LARGO',
                           ancho_col: str = 'ANCHO',
                           alto_col: str = 'ALTO') -> ValidationResult:
        """
        Valida dimensiones y peso de los SKUs

        Args:
            df_sku: DataFrame con datos de SKU
            peso_col, largo_col, ancho_col, alto_col: Columnas de dimensiones

        Returns:
            ValidationResult con validación de dimensiones
        """
        violations = []
        warnings = []

        if df_sku is None or df_sku.empty:
            return ValidationResult.create_passed(
                "SKUValidator.validar_dimensiones",
                DataType.SKU,
            )

        columnas_dim = {
            'peso': self._find_column(df_sku, peso_col),
            'largo': self._find_column(df_sku, largo_col),
            'ancho': self._find_column(df_sku, ancho_col),
            'alto': self._find_column(df_sku, alto_col),
        }

        # Validar cada dimensión
        for dim_nombre, col in columnas_dim.items():
            if col is None:
                continue

            # Valores nulos
            nulos = df_sku[df_sku[col].isna()]
            if not nulos.empty:
                warnings.append(ValidationWarning(
                    code=f"SKU_SIN_{dim_nombre.upper()}",
                    message=f"{len(nulos)} SKUs sin {dim_nombre}",
                ))

            # Valores negativos
            negativos = df_sku[df_sku[col] < 0]
            if not negativos.empty:
                violations.append(ValidationViolation(
                    code=f"SKU_{dim_nombre.upper()}_NEGATIVO",
                    message=f"{len(negativos)} SKUs con {dim_nombre} negativo",
                    severity=Severity.MEDIUM,
                ))

            # Valores cero (excepto para peso que podría ser válido para items digitales)
            if dim_nombre != 'peso':
                ceros = df_sku[df_sku[col] == 0]
                if not ceros.empty:
                    warnings.append(ValidationWarning(
                        code=f"SKU_{dim_nombre.upper()}_CERO",
                        message=f"{len(ceros)} SKUs con {dim_nombre} = 0",
                    ))

        if violations:
            result = ValidationResult.create_failed(
                "SKUValidator.validar_dimensiones",
                violations,
                DataType.SKU,
            )
        else:
            result = ValidationResult.create_passed(
                "SKUValidator.validar_dimensiones",
                DataType.SKU,
            )

        result.warnings = warnings
        return result

    # ═══════════════════════════════════════════════════════════════
    # MÉTODOS AUXILIARES
    # ═══════════════════════════════════════════════════════════════

    def _find_column(self, df: pd.DataFrame, col_name: str) -> Optional[str]:
        """Encuentra una columna por nombre (case insensitive)"""
        if df is None or df.empty:
            return None
        for col in df.columns:
            if col.upper() == col_name.upper():
                return col
        return None


# ═══════════════════════════════════════════════════════════════
# EXPORTAR
# ═══════════════════════════════════════════════════════════════

__all__ = ['SKUValidator']
