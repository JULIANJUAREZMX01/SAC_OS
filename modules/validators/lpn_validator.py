"""
═══════════════════════════════════════════════════════════════
VALIDADOR DE LPN (License Plate Number)
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Validador especializado para LPN/Cartones del sistema Manhattan WMS.

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


# ═══════════════════════════════════════════════════════════════
# CONSTANTES
# ═══════════════════════════════════════════════════════════════

LPN_PATTERNS = {
    'STANDARD': r'^LPN\d{7,10}$',      # LPN seguido de 7-10 dígitos
    'CARTON': r'^CTN\d{7,10}$',        # CTN seguido de 7-10 dígitos
    'PALLET': r'^PLT\d{7,10}$',        # PLT seguido de 7-10 dígitos
    'GENERIC': r'^[A-Z]{2,4}\d{6,12}$', # Prefijo alfabético + dígitos
}

# Status válidos de LPN
LPN_STATUS_VALIDOS = {
    10: "Creado",
    20: "En Ubicación",
    30: "En Picking",
    40: "En Staging",
    50: "Cargado",
    90: "Cerrado",
    99: "Anulado",
}


class LPNValidator(BaseValidator):
    """
    Validador especializado para LPN/Cartones

    Valida:
    - Formato de LPN
    - Ubicación válida
    - Status válido
    - Integridad de datos
    """

    def __init__(self):
        super().__init__(name="LPNValidator", data_type=DataType.LPN)

    def _register_default_rules(self) -> None:
        """Registra las reglas por defecto para LPN"""

        self.add_rule(ValidationRule(
            name="lpn_not_empty",
            description="Datos de LPN no deben estar vacíos",
            severity=Severity.HIGH,
            validator_func=lambda df: isinstance(df, pd.DataFrame) and not df.empty,
            error_code="LPN_DATOS_VACIOS",
        ))

    # ═══════════════════════════════════════════════════════════════
    # VALIDACIONES ESPECÍFICAS
    # ═══════════════════════════════════════════════════════════════

    def validar_formato_lpn(self, lpn: str) -> ValidationResult:
        """
        Valida el formato de un número de LPN

        Args:
            lpn: Número de LPN

        Returns:
            ValidationResult con el resultado
        """
        violations = []
        warnings = []

        if not lpn:
            violations.append(ValidationViolation(
                code="LPN_VACIO",
                message="Número de LPN no proporcionado",
                severity=Severity.CRITICAL,
            ))
            return ValidationResult.create_failed(
                "LPNValidator.validar_formato_lpn",
                violations,
                DataType.LPN,
            )

        lpn_limpio = str(lpn).strip().upper()

        # Verificar contra patrones
        format_valid = False
        matched_pattern = None

        for pattern_name, pattern in LPN_PATTERNS.items():
            if re.match(pattern, lpn_limpio):
                format_valid = True
                matched_pattern = pattern_name
                break

        if not format_valid:
            warnings.append(ValidationWarning(
                code="LPN_FORMATO_NO_ESTANDAR",
                message=f"Formato de LPN '{lpn}' no es estándar",
            ))

        if len(lpn_limpio) < 6:
            violations.append(ValidationViolation(
                code="LPN_MUY_CORTO",
                message=f"LPN demasiado corto: {len(lpn_limpio)} caracteres",
                severity=Severity.HIGH,
            ))

        if violations:
            return ValidationResult.create_failed(
                "LPNValidator.validar_formato_lpn",
                violations,
                DataType.LPN,
            )

        result = ValidationResult.create_passed(
            "LPNValidator.validar_formato_lpn",
            DataType.LPN,
            {'lpn': lpn_limpio, 'pattern': matched_pattern},
        )
        result.warnings = warnings
        return result

    def validar_ubicacion_lpn(self, df_lpn: pd.DataFrame,
                             ubicacion_col: str = 'LOC') -> ValidationResult:
        """
        Valida las ubicaciones de los LPNs

        Args:
            df_lpn: DataFrame con datos de LPN
            ubicacion_col: Columna de ubicación

        Returns:
            ValidationResult con validación de ubicaciones
        """
        violations = []
        warnings = []

        if df_lpn is None or df_lpn.empty:
            return ValidationResult.create_passed(
                "LPNValidator.validar_ubicacion_lpn",
                DataType.LPN,
            )

        col = self._find_column(df_lpn, ubicacion_col)
        if col is None:
            # Intentar otras posibles columnas
            for alt_col in ['LOCATION', 'UBICACION', 'STORERKEY']:
                col = self._find_column(df_lpn, alt_col)
                if col:
                    break

        if col is None:
            warnings.append(ValidationWarning(
                code="LPN_SIN_COL_UBICACION",
                message="No se encontró columna de ubicación",
            ))
            result = ValidationResult.create_passed(
                "LPNValidator.validar_ubicacion_lpn",
                DataType.LPN,
            )
            result.warnings = warnings
            return result

        # LPNs sin ubicación
        sin_ubicacion = df_lpn[df_lpn[col].isna() | (df_lpn[col].astype(str).str.strip() == '')]
        if not sin_ubicacion.empty:
            violations.append(ValidationViolation(
                code="LPN_SIN_UBICACION",
                message=f"{len(sin_ubicacion)} LPNs sin ubicación asignada",
                severity=Severity.HIGH,
                suggestion="Asignar ubicación a todos los LPNs",
            ))

        # LPNs con ubicación STAGE (staging area) - advertencia
        stage_lpns = df_lpn[df_lpn[col].astype(str).str.contains('STAGE', case=False, na=False)]
        if not stage_lpns.empty:
            warnings.append(ValidationWarning(
                code="LPN_EN_STAGING",
                message=f"{len(stage_lpns)} LPNs en área de staging",
                details="Verificar si están pendientes de carga",
            ))

        # LPNs con ubicación problemática
        problem_locs = ['ERROR', 'LOST', 'PERDIDO', 'TEMP']
        for loc in problem_locs:
            problem_lpns = df_lpn[df_lpn[col].astype(str).str.contains(loc, case=False, na=False)]
            if not problem_lpns.empty:
                warnings.append(ValidationWarning(
                    code=f"LPN_UBICACION_{loc.upper()}",
                    message=f"{len(problem_lpns)} LPNs con ubicación '{loc}'",
                ))

        if violations:
            result = ValidationResult.create_failed(
                "LPNValidator.validar_ubicacion_lpn",
                violations,
                DataType.LPN,
            )
        else:
            result = ValidationResult.create_passed(
                "LPNValidator.validar_ubicacion_lpn",
                DataType.LPN,
            )

        result.warnings = warnings
        return result

    def validar_status_lpn(self, df_lpn: pd.DataFrame,
                          status_col: str = 'STATUS') -> ValidationResult:
        """
        Valida el status de los LPNs

        Args:
            df_lpn: DataFrame con datos de LPN
            status_col: Columna de status

        Returns:
            ValidationResult con validación de status
        """
        violations = []
        warnings = []

        if df_lpn is None or df_lpn.empty:
            return ValidationResult.create_passed(
                "LPNValidator.validar_status_lpn",
                DataType.LPN,
            )

        col = self._find_column(df_lpn, status_col)
        if col is None:
            return ValidationResult.create_passed(
                "LPNValidator.validar_status_lpn",
                DataType.LPN,
            )

        try:
            status_valores = df_lpn[col].dropna().unique()

            # Status inválidos
            status_invalidos = []
            for s in status_valores:
                try:
                    if int(s) not in LPN_STATUS_VALIDOS:
                        status_invalidos.append(s)
                except (ValueError, TypeError):
                    status_invalidos.append(s)

            if status_invalidos:
                violations.append(ValidationViolation(
                    code="LPN_STATUS_INVALIDO",
                    message=f"Status no reconocidos: {status_invalidos}",
                    severity=Severity.MEDIUM,
                ))

            # LPNs anulados
            anulados = df_lpn[df_lpn[col].astype(str).isin(['99', '98'])]
            if not anulados.empty:
                warnings.append(ValidationWarning(
                    code="LPN_ANULADOS",
                    message=f"{len(anulados)} LPNs con status anulado",
                ))

        except Exception as e:
            logger.error(f"Error validando status LPN: {e}")

        if violations:
            result = ValidationResult.create_failed(
                "LPNValidator.validar_status_lpn",
                violations,
                DataType.LPN,
            )
        else:
            result = ValidationResult.create_passed(
                "LPNValidator.validar_status_lpn",
                DataType.LPN,
            )

        result.warnings = warnings
        return result

    def validar_lpn_completo(self, df_lpn: pd.DataFrame) -> ValidationResult:
        """
        Ejecuta validación completa de LPNs

        Args:
            df_lpn: DataFrame con datos de LPN

        Returns:
            ValidationResult consolidado
        """
        results = []

        # 1. Validación base
        base_result = self.validate(df_lpn)
        results.append(base_result)

        if not base_result.is_valid:
            return base_result

        # 2. Validar ubicaciones
        results.append(self.validar_ubicacion_lpn(df_lpn))

        # 3. Validar status
        results.append(self.validar_status_lpn(df_lpn))

        # 4. Validar formatos individuales si hay columna LPN
        lpn_col = self._find_column(df_lpn, 'LPN')
        if lpn_col:
            lpns_invalidos = []
            for lpn in df_lpn[lpn_col].dropna().unique()[:100]:  # Limitar a 100 para performance
                result = self.validar_formato_lpn(str(lpn))
                if not result.is_valid:
                    lpns_invalidos.append(lpn)

            if lpns_invalidos:
                results.append(ValidationResult.create_failed(
                    "LPNValidator.validar_formatos",
                    [ValidationViolation(
                        code="LPN_FORMATOS_INVALIDOS",
                        message=f"{len(lpns_invalidos)} LPNs con formato inválido",
                        severity=Severity.MEDIUM,
                        affected_records=lpns_invalidos[:10],
                    )],
                    DataType.LPN,
                ))

        # Consolidar resultados
        final_result = results[0]
        for result in results[1:]:
            final_result = final_result.merge(result)

        final_result.validator_name = "LPNValidator.validar_lpn_completo"
        return final_result

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

__all__ = ['LPNValidator', 'LPN_PATTERNS', 'LPN_STATUS_VALIDOS']
