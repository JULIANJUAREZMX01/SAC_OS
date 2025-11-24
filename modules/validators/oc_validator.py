"""
═══════════════════════════════════════════════════════════════
VALIDADOR DE ÓRDENES DE COMPRA (OC)
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Validador especializado para Órdenes de Compra del sistema
Manhattan WMS.

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
═══════════════════════════════════════════════════════════════
"""

import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pandas as pd

from .base_validator import BaseValidator, ValidationRule
from ..validation_result import (
    DataType,
    Severity,
    ValidationResult,
    ValidationStatus,
    ValidationViolation,
    ValidationWarning,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# PATRONES DE FORMATO DE OC
# ═══════════════════════════════════════════════════════════════

OC_PATTERNS = {
    'CHEDRAUI_750': r'^750384\d{6}$',       # Patrón Chedraui 750384XXXXXX
    'CHEDRAUI_811': r'^811117\d{6}$',       # Patrón Chedraui 811117XXXXXX
    'CHEDRAUI_40': r'^40\d{11}$',           # Patrón 40XXXXXXXXXXX
    'GENERIC': r'^[A-Z0-9]{8,15}$',         # Patrón genérico
}

# Días máximos de vigencia por defecto
DEFAULT_MAX_DAYS = 30


class OCValidator(BaseValidator):
    """
    Validador especializado para Órdenes de Compra (OC)

    Valida:
    - Formato de número de OC
    - Existencia en sistema
    - Vigencia/expiración
    - Totales y cantidades
    - Completitud de datos
    - Prefijo 'C' en ID_CODE
    """

    def __init__(self, max_vigencia_dias: int = DEFAULT_MAX_DAYS):
        """
        Inicializa el validador de OC

        Args:
            max_vigencia_dias: Días máximos de vigencia permitidos
        """
        self.max_vigencia_dias = max_vigencia_dias
        super().__init__(name="OCValidator", data_type=DataType.OC)

    def _register_default_rules(self) -> None:
        """Registra las reglas por defecto para OC"""

        # Regla: DataFrame no vacío
        self.add_rule(ValidationRule(
            name="oc_not_empty",
            description="La OC debe existir en el sistema",
            severity=Severity.CRITICAL,
            validator_func=lambda df: isinstance(df, pd.DataFrame) and not df.empty,
            error_code="OC_NO_ENCONTRADA",
            suggestion="Verificar número de OC y confirmar integración en Manhattan",
        ))

        # Regla: Columnas básicas presentes
        self.add_rule(ValidationRule(
            name="oc_required_columns",
            description="Columnas básicas requeridas presentes",
            severity=Severity.HIGH,
            validator_func=self._check_required_columns,
            error_code="OC_COLUMNAS_FALTANTES",
            suggestion="Verificar consulta SQL retorne todas las columnas necesarias",
        ))

    def _check_required_columns(self, df: Any) -> bool:
        """Verifica columnas mínimas requeridas"""
        if not isinstance(df, pd.DataFrame):
            return False
        required = ['SKU', 'CANTIDAD']  # Mínimo requerido
        return all(col in df.columns or col.upper() in df.columns for col in required)

    # ═══════════════════════════════════════════════════════════════
    # VALIDACIONES ESPECÍFICAS
    # ═══════════════════════════════════════════════════════════════

    def validar_formato_oc(self, oc_numero: str) -> ValidationResult:
        """
        Valida el formato del número de OC

        Args:
            oc_numero: Número de orden de compra

        Returns:
            ValidationResult con el resultado de la validación
        """
        violations = []
        warnings = []

        if not oc_numero:
            violations.append(ValidationViolation(
                code="OC_NUMERO_VACIO",
                message="Número de OC no proporcionado",
                severity=Severity.CRITICAL,
                suggestion="Proporcionar un número de OC válido",
            ))
            return ValidationResult.create_failed(
                "OCValidator.validar_formato_oc",
                violations,
                DataType.OC,
            )

        # Limpiar número
        oc_limpio = str(oc_numero).strip().upper()

        # Verificar contra patrones conocidos
        format_valid = False
        matched_pattern = None

        for pattern_name, pattern in OC_PATTERNS.items():
            if re.match(pattern, oc_limpio):
                format_valid = True
                matched_pattern = pattern_name
                break

        if not format_valid:
            warnings.append(ValidationWarning(
                code="OC_FORMATO_NO_ESTANDAR",
                message=f"Formato de OC '{oc_numero}' no coincide con patrones estándar",
                details="Puede ser válido pero no sigue formato Chedraui típico",
            ))

        # Verificar longitud mínima
        if len(oc_limpio) < 8:
            violations.append(ValidationViolation(
                code="OC_FORMATO_CORTO",
                message=f"Número de OC demasiado corto: {len(oc_limpio)} caracteres",
                severity=Severity.HIGH,
                expected_value="8-15 caracteres",
                actual_value=len(oc_limpio),
                suggestion="Verificar número completo de OC",
            ))

        if violations:
            return ValidationResult.create_failed(
                "OCValidator.validar_formato_oc",
                violations,
                DataType.OC,
                {'matched_pattern': matched_pattern},
            )

        result = ValidationResult.create_passed(
            "OCValidator.validar_formato_oc",
            DataType.OC,
            {'matched_pattern': matched_pattern, 'oc_numero': oc_limpio},
        )
        result.warnings = warnings
        return result

    def validar_existencia_oc(self, df_oc: pd.DataFrame) -> ValidationResult:
        """
        Valida que la OC exista (DataFrame no vacío)

        Args:
            df_oc: DataFrame con datos de la OC

        Returns:
            ValidationResult indicando si la OC existe
        """
        if df_oc is None or df_oc.empty:
            return ValidationResult.create_failed(
                "OCValidator.validar_existencia_oc",
                [ValidationViolation(
                    code="OC_NO_EXISTE",
                    message="La OC no existe en el sistema",
                    severity=Severity.CRITICAL,
                    suggestion="Verificar número de OC o confirmar integración en Manhattan",
                )],
                DataType.OC,
            )

        return ValidationResult.create_passed(
            "OCValidator.validar_existencia_oc",
            DataType.OC,
            {'registros_encontrados': len(df_oc)},
        )

    def validar_vigencia_oc(self, df_oc: pd.DataFrame,
                            fecha_columna: str = 'VIGENCIA') -> ValidationResult:
        """
        Valida la vigencia/expiración de la OC

        Args:
            df_oc: DataFrame con datos de la OC
            fecha_columna: Nombre de la columna de vigencia

        Returns:
            ValidationResult con estado de vigencia
        """
        violations = []
        warnings = []

        if df_oc is None or df_oc.empty:
            return ValidationResult.create_failed(
                "OCValidator.validar_vigencia_oc",
                [ValidationViolation(
                    code="OC_DATOS_VACIOS",
                    message="No hay datos de OC para validar vigencia",
                    severity=Severity.HIGH,
                )],
                DataType.OC,
            )

        # Buscar columna de vigencia (case insensitive)
        col_vigencia = None
        for col in df_oc.columns:
            if col.upper() == fecha_columna.upper():
                col_vigencia = col
                break

        if col_vigencia is None:
            warnings.append(ValidationWarning(
                code="OC_SIN_COLUMNA_VIGENCIA",
                message=f"No se encontró columna '{fecha_columna}' para validar vigencia",
            ))
            result = ValidationResult.create_passed(
                "OCValidator.validar_vigencia_oc",
                DataType.OC,
            )
            result.warnings = warnings
            return result

        try:
            df_oc[col_vigencia] = pd.to_datetime(df_oc[col_vigencia], errors='coerce')
            ahora = datetime.now()

            # Verificar OC vencidas
            oc_vencidas = df_oc[df_oc[col_vigencia] < ahora]
            if not oc_vencidas.empty:
                fecha_vencimiento = oc_vencidas[col_vigencia].min()
                dias_vencida = (ahora - fecha_vencimiento).days

                violations.append(ValidationViolation(
                    code="OC_VENCIDA",
                    message=f"OC vencida hace {dias_vencida} días",
                    severity=Severity.HIGH,
                    expected_value=f"Vigencia >= {ahora.strftime('%Y-%m-%d')}",
                    actual_value=fecha_vencimiento.strftime('%Y-%m-%d'),
                    suggestion="Contactar proveedor para extensión o evaluar cancelación",
                    affected_records=list(oc_vencidas.index),
                ))

            # Verificar OC próximas a vencer (7 días)
            limite_advertencia = ahora + timedelta(days=7)
            proximas_vencer = df_oc[
                (df_oc[col_vigencia] >= ahora) &
                (df_oc[col_vigencia] <= limite_advertencia)
            ]
            if not proximas_vencer.empty:
                dias_restantes = (proximas_vencer[col_vigencia].min() - ahora).days
                warnings.append(ValidationWarning(
                    code="OC_PROXIMA_VENCER",
                    message=f"OC próxima a vencer en {dias_restantes} días",
                    details=f"Fecha límite: {proximas_vencer[col_vigencia].min().strftime('%Y-%m-%d')}",
                ))

            # Verificar vigencia excesiva (más de max_vigencia_dias)
            limite_max = ahora + timedelta(days=self.max_vigencia_dias)
            vigencia_excesiva = df_oc[df_oc[col_vigencia] > limite_max]
            if not vigencia_excesiva.empty:
                warnings.append(ValidationWarning(
                    code="OC_VIGENCIA_EXTENDIDA",
                    message=f"OC con vigencia mayor a {self.max_vigencia_dias} días",
                    details="Verificar que la vigencia extendida sea intencional",
                ))

        except Exception as e:
            logger.error(f"Error validando vigencia: {e}")
            warnings.append(ValidationWarning(
                code="OC_ERROR_FECHA",
                message=f"Error procesando fechas de vigencia: {str(e)}",
            ))

        if violations:
            result = ValidationResult.create_failed(
                "OCValidator.validar_vigencia_oc",
                violations,
                DataType.OC,
            )
        else:
            result = ValidationResult.create_passed(
                "OCValidator.validar_vigencia_oc",
                DataType.OC,
            )

        result.warnings = warnings
        return result

    def validar_totales_oc(self, df_oc: pd.DataFrame,
                          cantidad_columna: str = 'CANTIDAD') -> ValidationResult:
        """
        Valida los totales y cantidades de la OC

        Args:
            df_oc: DataFrame con datos de la OC
            cantidad_columna: Nombre de la columna de cantidad

        Returns:
            ValidationResult con validación de totales
        """
        violations = []
        warnings = []

        if df_oc is None or df_oc.empty:
            return ValidationResult.create_failed(
                "OCValidator.validar_totales_oc",
                [ValidationViolation(
                    code="OC_DATOS_VACIOS",
                    message="No hay datos para validar totales",
                    severity=Severity.HIGH,
                )],
                DataType.OC,
            )

        # Buscar columna de cantidad
        col_cantidad = None
        for col in df_oc.columns:
            if col.upper() == cantidad_columna.upper():
                col_cantidad = col
                break

        if col_cantidad is None:
            warnings.append(ValidationWarning(
                code="OC_SIN_COLUMNA_CANTIDAD",
                message=f"No se encontró columna '{cantidad_columna}'",
            ))
            result = ValidationResult.create_passed(
                "OCValidator.validar_totales_oc",
                DataType.OC,
            )
            result.warnings = warnings
            return result

        try:
            # Verificar cantidades negativas
            negativos = df_oc[df_oc[col_cantidad] < 0]
            if not negativos.empty:
                violations.append(ValidationViolation(
                    code="OC_CANTIDAD_NEGATIVA",
                    message=f"{len(negativos)} registros con cantidad negativa",
                    severity=Severity.CRITICAL,
                    suggestion="Corregir cantidades negativas en la OC",
                    affected_records=list(negativos.index),
                ))

            # Verificar cantidades cero
            ceros = df_oc[df_oc[col_cantidad] == 0]
            if not ceros.empty:
                warnings.append(ValidationWarning(
                    code="OC_CANTIDAD_CERO",
                    message=f"{len(ceros)} registros con cantidad cero",
                    details="Verificar si las cantidades cero son intencionales",
                ))

            # Verificar total general
            total = df_oc[col_cantidad].sum()
            if total <= 0:
                violations.append(ValidationViolation(
                    code="OC_TOTAL_INVALIDO",
                    message=f"Total de OC inválido: {total}",
                    severity=Severity.CRITICAL,
                    expected_value="> 0",
                    actual_value=total,
                ))

            # Verificar cantidades muy altas (outliers)
            q99 = df_oc[col_cantidad].quantile(0.99)
            outliers = df_oc[df_oc[col_cantidad] > q99 * 10]  # 10x el percentil 99
            if not outliers.empty:
                warnings.append(ValidationWarning(
                    code="OC_CANTIDAD_ATIPICA",
                    message=f"{len(outliers)} registros con cantidades atípicamente altas",
                    details="Verificar que las cantidades altas sean correctas",
                ))

        except Exception as e:
            logger.error(f"Error validando totales: {e}")
            violations.append(ValidationViolation(
                code="OC_ERROR_TOTALES",
                message=f"Error calculando totales: {str(e)}",
                severity=Severity.HIGH,
            ))

        if violations:
            result = ValidationResult.create_failed(
                "OCValidator.validar_totales_oc",
                violations,
                DataType.OC,
                {'total_cantidad': total if 'total' in locals() else None},
            )
        else:
            result = ValidationResult.create_passed(
                "OCValidator.validar_totales_oc",
                DataType.OC,
                {'total_cantidad': total if 'total' in locals() else None},
            )

        result.warnings = warnings
        return result

    def validar_oc_completa(self, df_oc: pd.DataFrame,
                           oc_numero: str = None) -> ValidationResult:
        """
        Ejecuta validación completa de una OC

        Args:
            df_oc: DataFrame con datos de la OC
            oc_numero: Número de OC (opcional, para validar formato)

        Returns:
            ValidationResult consolidado con todas las validaciones
        """
        results = []

        # 1. Validar formato si se proporciona número
        if oc_numero:
            results.append(self.validar_formato_oc(oc_numero))

        # 2. Validar existencia
        results.append(self.validar_existencia_oc(df_oc))

        # Si no existe, no continuar con otras validaciones
        if not results[-1].is_valid:
            return results[-1]

        # 3. Validar vigencia
        results.append(self.validar_vigencia_oc(df_oc))

        # 4. Validar totales
        results.append(self.validar_totales_oc(df_oc))

        # 5. Validar letra C en ID_CODE
        results.append(self.validar_prefijo_c(df_oc))

        # Consolidar resultados
        final_result = results[0]
        for result in results[1:]:
            final_result = final_result.merge(result)

        final_result.validator_name = "OCValidator.validar_oc_completa"
        return final_result

    def validar_prefijo_c(self, df_oc: pd.DataFrame,
                         id_columna: str = 'ID_CODE') -> ValidationResult:
        """
        Valida que los registros tengan prefijo 'C' en ID_CODE

        Args:
            df_oc: DataFrame con datos de la OC
            id_columna: Nombre de la columna de ID

        Returns:
            ValidationResult con validación de prefijo
        """
        violations = []
        warnings = []

        if df_oc is None or df_oc.empty:
            return ValidationResult.create_passed(
                "OCValidator.validar_prefijo_c",
                DataType.OC,
            )

        # Buscar columna ID
        col_id = None
        for col in df_oc.columns:
            if col.upper() == id_columna.upper():
                col_id = col
                break

        if col_id is None:
            warnings.append(ValidationWarning(
                code="OC_SIN_COLUMNA_ID",
                message=f"No se encontró columna '{id_columna}'",
            ))
            result = ValidationResult.create_passed(
                "OCValidator.validar_prefijo_c",
                DataType.OC,
            )
            result.warnings = warnings
            return result

        # Verificar prefijo C
        sin_prefijo_c = df_oc[~df_oc[col_id].astype(str).str.upper().str.startswith('C')]
        if not sin_prefijo_c.empty:
            violations.append(ValidationViolation(
                code="OC_SIN_PREFIJO_C",
                message=f"{len(sin_prefijo_c)} registros sin prefijo 'C' en {id_columna}",
                severity=Severity.MEDIUM,
                suggestion="Notificar a Planning para corrección de ID_CODE",
                affected_records=list(sin_prefijo_c[col_id].unique()[:10]),
            ))

        if violations:
            result = ValidationResult.create_failed(
                "OCValidator.validar_prefijo_c",
                violations,
                DataType.OC,
            )
        else:
            result = ValidationResult.create_passed(
                "OCValidator.validar_prefijo_c",
                DataType.OC,
            )

        result.warnings = warnings
        return result


# ═══════════════════════════════════════════════════════════════
# EXPORTAR
# ═══════════════════════════════════════════════════════════════

__all__ = ['OCValidator', 'OC_PATTERNS']
