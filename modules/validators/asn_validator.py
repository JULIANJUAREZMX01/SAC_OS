"""
═══════════════════════════════════════════════════════════════
VALIDADOR DE ASN (Advanced Shipping Notice)
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Validador especializado para ASN del sistema Manhattan WMS.

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
# CONSTANTES
# ═══════════════════════════════════════════════════════════════

ASN_PATTERNS = {
    'STANDARD': r'^ASN\d{8,12}$',      # ASN seguido de 8-12 dígitos
    'GENERIC': r'^[A-Z0-9]{10,20}$',    # Patrón genérico
}

# Status válidos de ASN en Manhattan WMS
ASN_STATUS_VALIDOS = {
    10: "Creado",
    20: "En Tránsito",
    30: "En Muelle",
    40: "En Proceso de Recibo",
    50: "Parcialmente Recibido",
    90: "Completamente Recibido",
    99: "Cerrado",
}

# Días para considerar un ASN estancado
DEFAULT_STALE_DAYS = 7


class ASNValidator(BaseValidator):
    """
    Validador especializado para ASN

    Valida:
    - Formato de ASN
    - Status válido
    - ASN actualizado (no estancado)
    - Correspondencia ASN-OC
    """

    def __init__(self, stale_days: int = DEFAULT_STALE_DAYS):
        """
        Inicializa el validador de ASN

        Args:
            stale_days: Días sin actualización para considerar estancado
        """
        self.stale_days = stale_days
        super().__init__(name="ASNValidator", data_type=DataType.ASN)

    def _register_default_rules(self) -> None:
        """Registra las reglas por defecto para ASN"""

        self.add_rule(ValidationRule(
            name="asn_not_empty",
            description="El ASN debe existir en el sistema",
            severity=Severity.HIGH,
            validator_func=lambda df: isinstance(df, pd.DataFrame) and not df.empty,
            error_code="ASN_NO_ENCONTRADO",
            suggestion="Verificar número de ASN o confirmar integración EDI",
        ))

    # ═══════════════════════════════════════════════════════════════
    # VALIDACIONES ESPECÍFICAS
    # ═══════════════════════════════════════════════════════════════

    def validar_formato_asn(self, asn_numero: str) -> ValidationResult:
        """
        Valida el formato del número de ASN

        Args:
            asn_numero: Número de ASN

        Returns:
            ValidationResult con el resultado
        """
        violations = []
        warnings = []

        if not asn_numero:
            violations.append(ValidationViolation(
                code="ASN_NUMERO_VACIO",
                message="Número de ASN no proporcionado",
                severity=Severity.CRITICAL,
            ))
            return ValidationResult.create_failed(
                "ASNValidator.validar_formato_asn",
                violations,
                DataType.ASN,
            )

        asn_limpio = str(asn_numero).strip().upper()

        # Verificar patrones
        format_valid = False
        for pattern_name, pattern in ASN_PATTERNS.items():
            if re.match(pattern, asn_limpio):
                format_valid = True
                break

        if not format_valid:
            warnings.append(ValidationWarning(
                code="ASN_FORMATO_NO_ESTANDAR",
                message=f"Formato de ASN '{asn_numero}' no es estándar",
            ))

        if len(asn_limpio) < 8:
            violations.append(ValidationViolation(
                code="ASN_MUY_CORTO",
                message=f"ASN demasiado corto: {len(asn_limpio)} caracteres",
                severity=Severity.HIGH,
            ))

        if violations:
            return ValidationResult.create_failed(
                "ASNValidator.validar_formato_asn",
                violations,
                DataType.ASN,
            )

        result = ValidationResult.create_passed(
            "ASNValidator.validar_formato_asn",
            DataType.ASN,
            {'asn_numero': asn_limpio},
        )
        result.warnings = warnings
        return result

    def validar_status_asn(self, df_asn: pd.DataFrame,
                          status_col: str = 'STATUS') -> ValidationResult:
        """
        Valida el status del ASN

        Args:
            df_asn: DataFrame con datos del ASN
            status_col: Nombre de columna de status

        Returns:
            ValidationResult con validación de status
        """
        violations = []
        warnings = []

        if df_asn is None or df_asn.empty:
            return ValidationResult.create_failed(
                "ASNValidator.validar_status_asn",
                [ValidationViolation(
                    code="ASN_DATOS_VACIOS",
                    message="No hay datos de ASN para validar",
                    severity=Severity.HIGH,
                )],
                DataType.ASN,
            )

        col = self._find_column(df_asn, status_col)
        if col is None:
            warnings.append(ValidationWarning(
                code="ASN_SIN_COLUMNA_STATUS",
                message=f"No se encontró columna '{status_col}'",
            ))
            result = ValidationResult.create_passed(
                "ASNValidator.validar_status_asn",
                DataType.ASN,
            )
            result.warnings = warnings
            return result

        try:
            status_valores = df_asn[col].dropna().unique()

            # Verificar status inválidos
            status_invalidos = [s for s in status_valores
                               if int(s) not in ASN_STATUS_VALIDOS]

            if status_invalidos:
                violations.append(ValidationViolation(
                    code="ASN_STATUS_INVALIDO",
                    message=f"Status no reconocidos: {status_invalidos}",
                    severity=Severity.MEDIUM,
                    suggestion="Verificar status con documentación Manhattan WMS",
                ))

            # Verificar si hay ASN en status problemático
            for status in status_valores:
                if int(status) in [10]:  # Solo creado, sin movimiento
                    warnings.append(ValidationWarning(
                        code="ASN_STATUS_INICIAL",
                        message=f"ASN en status inicial ({status}: Creado)",
                        details="Verificar si el ASN ya debería estar en proceso",
                    ))

        except Exception as e:
            logger.error(f"Error validando status: {e}")

        if violations:
            result = ValidationResult.create_failed(
                "ASNValidator.validar_status_asn",
                violations,
                DataType.ASN,
            )
        else:
            result = ValidationResult.create_passed(
                "ASNValidator.validar_status_asn",
                DataType.ASN,
            )

        result.warnings = warnings
        return result

    def validar_asn_actualizado(self, df_asn: pd.DataFrame,
                                fecha_col: str = 'ULTIMA_MOD') -> ValidationResult:
        """
        Valida que el ASN tenga actualizaciones recientes

        Args:
            df_asn: DataFrame con datos del ASN
            fecha_col: Columna de fecha de última modificación

        Returns:
            ValidationResult indicando si está actualizado
        """
        violations = []
        warnings = []

        if df_asn is None or df_asn.empty:
            return ValidationResult.create_passed(
                "ASNValidator.validar_asn_actualizado",
                DataType.ASN,
            )

        col = self._find_column(df_asn, fecha_col)
        if col is None:
            return ValidationResult.create_passed(
                "ASNValidator.validar_asn_actualizado",
                DataType.ASN,
            )

        try:
            df_asn[col] = pd.to_datetime(df_asn[col], errors='coerce')
            ahora = datetime.now()
            limite = ahora - timedelta(days=self.stale_days)

            asn_estancados = df_asn[df_asn[col] < limite]

            if not asn_estancados.empty:
                dias_sin_update = (ahora - asn_estancados[col].max()).days

                if dias_sin_update > self.stale_days * 2:
                    violations.append(ValidationViolation(
                        code="ASN_MUY_ESTANCADO",
                        message=f"ASN sin actualización hace {dias_sin_update} días",
                        severity=Severity.HIGH,
                        suggestion="Verificar status con proveedor urgentemente",
                    ))
                else:
                    warnings.append(ValidationWarning(
                        code="ASN_ESTANCADO",
                        message=f"ASN sin actualización hace {dias_sin_update} días",
                        details="Verificar estado del envío",
                    ))

        except Exception as e:
            logger.error(f"Error validando actualización: {e}")

        if violations:
            result = ValidationResult.create_failed(
                "ASNValidator.validar_asn_actualizado",
                violations,
                DataType.ASN,
            )
        else:
            result = ValidationResult.create_passed(
                "ASNValidator.validar_asn_actualizado",
                DataType.ASN,
            )

        result.warnings = warnings
        return result

    def validar_asn_oc_match(self, df_asn: pd.DataFrame,
                            df_oc: pd.DataFrame,
                            asn_sku_col: str = 'SKU',
                            oc_sku_col: str = 'SKU') -> ValidationResult:
        """
        Valida correspondencia entre ASN y OC

        Args:
            df_asn: DataFrame con datos del ASN
            df_oc: DataFrame con datos de OC

        Returns:
            ValidationResult con validación de correspondencia
        """
        violations = []
        warnings = []

        if df_asn is None or df_asn.empty:
            return ValidationResult.create_passed(
                "ASNValidator.validar_asn_oc_match",
                DataType.ASN,
            )

        if df_oc is None or df_oc.empty:
            violations.append(ValidationViolation(
                code="OC_NO_DISPONIBLE",
                message="No hay datos de OC para comparar con ASN",
                severity=Severity.HIGH,
            ))
            return ValidationResult.create_failed(
                "ASNValidator.validar_asn_oc_match",
                violations,
                DataType.ASN,
            )

        try:
            col_asn = self._find_column(df_asn, asn_sku_col)
            col_oc = self._find_column(df_oc, oc_sku_col)

            if col_asn and col_oc:
                skus_asn = set(df_asn[col_asn].dropna().unique())
                skus_oc = set(df_oc[col_oc].dropna().unique())

                # SKUs en ASN pero no en OC
                skus_extra = skus_asn - skus_oc
                if skus_extra:
                    violations.append(ValidationViolation(
                        code="ASN_SKU_SIN_OC",
                        message=f"{len(skus_extra)} SKUs en ASN sin correspondencia en OC",
                        severity=Severity.HIGH,
                        affected_records=list(skus_extra)[:10],
                        suggestion="Verificar que el ASN corresponda a la OC correcta",
                    ))

                # SKUs en OC pero no en ASN
                skus_faltantes = skus_oc - skus_asn
                if skus_faltantes:
                    warnings.append(ValidationWarning(
                        code="ASN_SKU_FALTANTES",
                        message=f"{len(skus_faltantes)} SKUs de OC no están en ASN",
                        details="Puede ser envío parcial",
                    ))

        except Exception as e:
            logger.error(f"Error validando correspondencia ASN-OC: {e}")

        if violations:
            result = ValidationResult.create_failed(
                "ASNValidator.validar_asn_oc_match",
                violations,
                DataType.ASN,
            )
        else:
            result = ValidationResult.create_passed(
                "ASNValidator.validar_asn_oc_match",
                DataType.ASN,
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

__all__ = ['ASNValidator', 'ASN_PATTERNS', 'ASN_STATUS_VALIDOS']
