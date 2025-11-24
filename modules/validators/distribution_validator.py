"""
═══════════════════════════════════════════════════════════════
VALIDADOR DE DISTRIBUCIONES
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Validador especializado para Distribuciones y reconciliación
OC vs Distribuciones.

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
═══════════════════════════════════════════════════════════════
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from .base_validator import BaseValidator, ValidationRule
from ..validation_result import (
    DataType,
    Severity,
    ValidationResult,
    ValidationStatus,
    ValidationViolation,
    ValidationWarning,
    ReconciliationResult,
    DiscrepancyRecord,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# CONSTANTES
# ═══════════════════════════════════════════════════════════════

# Tolerancia de diferencia en distribuciones (0.01 = 1%)
DEFAULT_TOLERANCE = 0.01


class DistributionValidator(BaseValidator):
    """
    Validador especializado para Distribuciones

    Valida:
    - Distribución excedente (más distribuciones que OC)
    - Distribución incompleta (menos distribuciones que OC)
    - Sin distribuciones
    - Tiendas válidas
    - Cantidades correctas
    - Reconciliación OC vs Distribución
    """

    def __init__(self, tolerance: float = DEFAULT_TOLERANCE):
        """
        Inicializa el validador de distribuciones

        Args:
            tolerance: Tolerancia de diferencia aceptable (0-1)
        """
        self.tolerance = tolerance
        super().__init__(name="DistributionValidator", data_type=DataType.DISTRIBUTION)

    def _register_default_rules(self) -> None:
        """Registra las reglas por defecto para distribuciones"""

        self.add_rule(ValidationRule(
            name="distro_not_empty",
            description="Las distribuciones no deben estar vacías",
            severity=Severity.CRITICAL,
            validator_func=lambda df: isinstance(df, pd.DataFrame) and not df.empty,
            error_code="SIN_DISTRIBUCIONES",
            suggestion="Notificar a Planning para crear distribuciones",
        ))

        self.add_rule(ValidationRule(
            name="distro_has_tienda",
            description="Las distribuciones deben tener tienda destino",
            severity=Severity.HIGH,
            validator_func=self._check_tienda_column,
            error_code="DISTRO_SIN_TIENDA",
            suggestion="Verificar que todas las distribuciones tengan tienda asignada",
        ))

    def _check_tienda_column(self, df: Any) -> bool:
        """Verifica que exista columna de tienda"""
        if not isinstance(df, pd.DataFrame):
            return False
        tienda_cols = ['TIENDA', 'STORE', 'STORERKEY', 'DESTINO']
        return any(col in df.columns or col.upper() in [c.upper() for c in df.columns]
                   for col in tienda_cols)

    # ═══════════════════════════════════════════════════════════════
    # VALIDACIONES ESPECÍFICAS
    # ═══════════════════════════════════════════════════════════════

    def validar_distribucion_excedente(self, df_oc: pd.DataFrame,
                                       df_distro: pd.DataFrame,
                                       oc_col: str = 'CANTIDAD',
                                       distro_col: str = 'CANTIDAD') -> ValidationResult:
        """
        Valida que las distribuciones no excedan la OC

        Args:
            df_oc: DataFrame con datos de OC
            df_distro: DataFrame con distribuciones
            oc_col: Columna de cantidad en OC
            distro_col: Columna de cantidad en distribuciones

        Returns:
            ValidationResult indicando si hay excedente
        """
        violations = []
        warnings = []

        if df_oc is None or df_oc.empty:
            violations.append(ValidationViolation(
                code="OC_VACIA",
                message="No hay datos de OC para comparar",
                severity=Severity.HIGH,
            ))
            return ValidationResult.create_failed(
                "DistributionValidator.validar_distribucion_excedente",
                violations,
                DataType.DISTRIBUTION,
            )

        if df_distro is None or df_distro.empty:
            # Sin distribuciones no puede haber excedente
            return ValidationResult.create_passed(
                "DistributionValidator.validar_distribucion_excedente",
                DataType.DISTRIBUTION,
                {'motivo': 'Sin distribuciones para comparar'},
            )

        try:
            # Encontrar columnas
            col_oc = self._find_column(df_oc, oc_col)
            col_distro = self._find_column(df_distro, distro_col)

            if col_oc is None or col_distro is None:
                warnings.append(ValidationWarning(
                    code="COLUMNAS_NO_ENCONTRADAS",
                    message="No se encontraron columnas de cantidad para comparar",
                ))
                result = ValidationResult.create_passed(
                    "DistributionValidator.validar_distribucion_excedente",
                    DataType.DISTRIBUTION,
                )
                result.warnings = warnings
                return result

            total_oc = df_oc[col_oc].sum()
            total_distro = df_distro[col_distro].sum()

            if total_oc == 0:
                violations.append(ValidationViolation(
                    code="OC_TOTAL_CERO",
                    message="Total de OC es cero",
                    severity=Severity.HIGH,
                ))
                return ValidationResult.create_failed(
                    "DistributionValidator.validar_distribucion_excedente",
                    violations,
                    DataType.DISTRIBUTION,
                )

            diferencia = total_distro - total_oc
            porcentaje_diff = (diferencia / total_oc) * 100 if total_oc > 0 else 0

            if diferencia > 0:
                # Hay excedente
                severity = Severity.CRITICAL if porcentaje_diff > 5 else Severity.HIGH

                violations.append(ValidationViolation(
                    code="DISTRIBUCION_EXCEDENTE",
                    message=f"Distribuciones exceden OC en {diferencia:,.0f} unidades ({porcentaje_diff:.2f}%)",
                    severity=severity,
                    expected_value=total_oc,
                    actual_value=total_distro,
                    suggestion="URGENTE: Corregir distribuciones excedentes antes de recibir",
                ))

                return ValidationResult.create_failed(
                    "DistributionValidator.validar_distribucion_excedente",
                    violations,
                    DataType.DISTRIBUTION,
                    {
                        'total_oc': total_oc,
                        'total_distro': total_distro,
                        'excedente': diferencia,
                        'porcentaje': porcentaje_diff,
                    },
                )

            # Verificar si está dentro de tolerancia
            if abs(porcentaje_diff) <= self.tolerance * 100:
                return ValidationResult.create_passed(
                    "DistributionValidator.validar_distribucion_excedente",
                    DataType.DISTRIBUTION,
                    {
                        'total_oc': total_oc,
                        'total_distro': total_distro,
                        'diferencia': diferencia,
                    },
                )

        except Exception as e:
            logger.error(f"Error validando excedente: {e}")
            violations.append(ValidationViolation(
                code="ERROR_VALIDACION",
                message=f"Error durante validación: {str(e)}",
                severity=Severity.HIGH,
            ))

        if violations:
            return ValidationResult.create_failed(
                "DistributionValidator.validar_distribucion_excedente",
                violations,
                DataType.DISTRIBUTION,
            )

        return ValidationResult.create_passed(
            "DistributionValidator.validar_distribucion_excedente",
            DataType.DISTRIBUTION,
        )

    def validar_distribucion_incompleta(self, df_oc: pd.DataFrame,
                                        df_distro: pd.DataFrame,
                                        oc_col: str = 'CANTIDAD',
                                        distro_col: str = 'CANTIDAD') -> ValidationResult:
        """
        Valida que las distribuciones cubran completamente la OC

        Args:
            df_oc: DataFrame con datos de OC
            df_distro: DataFrame con distribuciones

        Returns:
            ValidationResult indicando si está incompleta
        """
        violations = []
        warnings = []

        if df_oc is None or df_oc.empty:
            return ValidationResult.create_passed(
                "DistributionValidator.validar_distribucion_incompleta",
                DataType.DISTRIBUTION,
            )

        if df_distro is None or df_distro.empty:
            violations.append(ValidationViolation(
                code="SIN_DISTRIBUCIONES",
                message="No hay distribuciones para la OC",
                severity=Severity.CRITICAL,
                suggestion="Crear distribuciones para la OC",
            ))
            return ValidationResult.create_failed(
                "DistributionValidator.validar_distribucion_incompleta",
                violations,
                DataType.DISTRIBUTION,
            )

        try:
            col_oc = self._find_column(df_oc, oc_col)
            col_distro = self._find_column(df_distro, distro_col)

            if col_oc is None or col_distro is None:
                return ValidationResult.create_passed(
                    "DistributionValidator.validar_distribucion_incompleta",
                    DataType.DISTRIBUTION,
                )

            total_oc = df_oc[col_oc].sum()
            total_distro = df_distro[col_distro].sum()

            faltante = total_oc - total_distro
            porcentaje_faltante = (faltante / total_oc) * 100 if total_oc > 0 else 0

            if faltante > 0 and porcentaje_faltante > self.tolerance * 100:
                severity = Severity.HIGH if porcentaje_faltante > 10 else Severity.MEDIUM

                violations.append(ValidationViolation(
                    code="DISTRIBUCION_INCOMPLETA",
                    message=f"Faltan {faltante:,.0f} unidades por distribuir ({porcentaje_faltante:.2f}%)",
                    severity=severity,
                    expected_value=total_oc,
                    actual_value=total_distro,
                    suggestion="Completar distribuciones faltantes",
                ))

                return ValidationResult.create_failed(
                    "DistributionValidator.validar_distribucion_incompleta",
                    violations,
                    DataType.DISTRIBUTION,
                    {
                        'total_oc': total_oc,
                        'total_distro': total_distro,
                        'faltante': faltante,
                        'porcentaje_faltante': porcentaje_faltante,
                    },
                )

        except Exception as e:
            logger.error(f"Error validando distribución incompleta: {e}")

        return ValidationResult.create_passed(
            "DistributionValidator.validar_distribucion_incompleta",
            DataType.DISTRIBUTION,
        )

    def validar_sin_distribuciones(self, df_oc: pd.DataFrame,
                                   df_distro: pd.DataFrame) -> ValidationResult:
        """
        Valida que la OC tenga distribuciones

        Args:
            df_oc: DataFrame con datos de OC
            df_distro: DataFrame con distribuciones

        Returns:
            ValidationResult indicando si tiene distribuciones
        """
        if df_distro is None or df_distro.empty:
            oc_info = ""
            if df_oc is not None and not df_oc.empty:
                total = df_oc['CANTIDAD'].sum() if 'CANTIDAD' in df_oc.columns else len(df_oc)
                oc_info = f" (OC tiene {total:,.0f} unidades)"

            return ValidationResult.create_failed(
                "DistributionValidator.validar_sin_distribuciones",
                [ValidationViolation(
                    code="SIN_DISTRIBUCIONES",
                    message=f"La OC no tiene distribuciones asignadas{oc_info}",
                    severity=Severity.CRITICAL,
                    suggestion="URGENTE: Solicitar a Planning la creación de distribuciones",
                )],
                DataType.DISTRIBUTION,
            )

        return ValidationResult.create_passed(
            "DistributionValidator.validar_sin_distribuciones",
            DataType.DISTRIBUTION,
            {'total_distribuciones': len(df_distro)},
        )

    def validar_tiendas(self, df_distro: pd.DataFrame,
                       tiendas_validas: List[str] = None) -> ValidationResult:
        """
        Valida que las tiendas destino sean válidas

        Args:
            df_distro: DataFrame con distribuciones
            tiendas_validas: Lista de tiendas válidas (opcional)

        Returns:
            ValidationResult con validación de tiendas
        """
        violations = []
        warnings = []

        if df_distro is None or df_distro.empty:
            return ValidationResult.create_passed(
                "DistributionValidator.validar_tiendas",
                DataType.DISTRIBUTION,
            )

        # Encontrar columna de tienda
        tienda_col = None
        for col in ['TIENDA', 'STORE', 'STORERKEY', 'DESTINO']:
            found = self._find_column(df_distro, col)
            if found:
                tienda_col = found
                break

        if tienda_col is None:
            warnings.append(ValidationWarning(
                code="COLUMNA_TIENDA_NO_ENCONTRADA",
                message="No se encontró columna de tienda",
            ))
            result = ValidationResult.create_passed(
                "DistributionValidator.validar_tiendas",
                DataType.DISTRIBUTION,
            )
            result.warnings = warnings
            return result

        tiendas_en_distro = df_distro[tienda_col].dropna().unique()

        # Verificar tiendas vacías/nulas
        nulas = df_distro[df_distro[tienda_col].isna()]
        if not nulas.empty:
            violations.append(ValidationViolation(
                code="TIENDA_NULA",
                message=f"{len(nulas)} distribuciones sin tienda asignada",
                severity=Severity.HIGH,
                suggestion="Asignar tienda a todas las distribuciones",
            ))

        # Si hay lista de tiendas válidas, verificar
        if tiendas_validas:
            tiendas_invalidas = [t for t in tiendas_en_distro if t not in tiendas_validas]
            if tiendas_invalidas:
                violations.append(ValidationViolation(
                    code="TIENDA_INVALIDA",
                    message=f"Tiendas no reconocidas: {', '.join(map(str, tiendas_invalidas[:5]))}",
                    severity=Severity.MEDIUM,
                    suggestion="Verificar códigos de tienda en catálogo",
                    affected_records=list(tiendas_invalidas),
                ))

        if violations:
            return ValidationResult.create_failed(
                "DistributionValidator.validar_tiendas",
                violations,
                DataType.DISTRIBUTION,
            )

        result = ValidationResult.create_passed(
            "DistributionValidator.validar_tiendas",
            DataType.DISTRIBUTION,
            {'tiendas_encontradas': len(tiendas_en_distro)},
        )
        result.warnings = warnings
        return result

    def validar_cantidades(self, df_distro: pd.DataFrame,
                          cantidad_col: str = 'CANTIDAD') -> ValidationResult:
        """
        Valida las cantidades en distribuciones

        Args:
            df_distro: DataFrame con distribuciones
            cantidad_col: Nombre de columna de cantidad

        Returns:
            ValidationResult con validación de cantidades
        """
        violations = []
        warnings = []

        if df_distro is None or df_distro.empty:
            return ValidationResult.create_passed(
                "DistributionValidator.validar_cantidades",
                DataType.DISTRIBUTION,
            )

        col = self._find_column(df_distro, cantidad_col)
        if col is None:
            return ValidationResult.create_passed(
                "DistributionValidator.validar_cantidades",
                DataType.DISTRIBUTION,
            )

        # Verificar cantidades negativas
        negativos = df_distro[df_distro[col] < 0]
        if not negativos.empty:
            violations.append(ValidationViolation(
                code="CANTIDAD_NEGATIVA",
                message=f"{len(negativos)} distribuciones con cantidad negativa",
                severity=Severity.CRITICAL,
                suggestion="Corregir cantidades negativas",
            ))

        # Verificar cantidades cero
        ceros = df_distro[df_distro[col] == 0]
        if not ceros.empty:
            warnings.append(ValidationWarning(
                code="CANTIDAD_CERO",
                message=f"{len(ceros)} distribuciones con cantidad cero",
            ))

        # Verificar valores nulos
        nulos = df_distro[df_distro[col].isna()]
        if not nulos.empty:
            violations.append(ValidationViolation(
                code="CANTIDAD_NULA",
                message=f"{len(nulos)} distribuciones sin cantidad",
                severity=Severity.HIGH,
            ))

        if violations:
            result = ValidationResult.create_failed(
                "DistributionValidator.validar_cantidades",
                violations,
                DataType.DISTRIBUTION,
            )
        else:
            result = ValidationResult.create_passed(
                "DistributionValidator.validar_cantidades",
                DataType.DISTRIBUTION,
                {'total_cantidad': df_distro[col].sum()},
            )

        result.warnings = warnings
        return result

    def reconciliar_oc_distro(self, df_oc: pd.DataFrame,
                              df_distro: pd.DataFrame,
                              sku_col: str = 'SKU',
                              cant_col: str = 'CANTIDAD') -> ReconciliationResult:
        """
        Reconcilia OC vs Distribuciones a nivel de SKU

        Args:
            df_oc: DataFrame con datos de OC
            df_distro: DataFrame con distribuciones
            sku_col: Columna de SKU
            cant_col: Columna de cantidad

        Returns:
            ReconciliationResult con el resultado de reconciliación
        """
        discrepancies = []
        missing_in_oc = []
        missing_in_distro = []

        if df_oc is None or df_oc.empty:
            return ReconciliationResult(
                is_reconciled=False,
                source_a_name="OC",
                source_b_name="Distribuciones",
                total_records_a=0,
                total_records_b=len(df_distro) if df_distro is not None else 0,
                matched_records=0,
            )

        if df_distro is None or df_distro.empty:
            return ReconciliationResult(
                is_reconciled=False,
                source_a_name="OC",
                source_b_name="Distribuciones",
                total_records_a=len(df_oc),
                total_records_b=0,
                matched_records=0,
            )

        try:
            # Encontrar columnas
            sku_oc = self._find_column(df_oc, sku_col)
            sku_distro = self._find_column(df_distro, sku_col)
            cant_oc_col = self._find_column(df_oc, cant_col)
            cant_distro_col = self._find_column(df_distro, cant_col)

            if not all([sku_oc, sku_distro, cant_oc_col, cant_distro_col]):
                return ReconciliationResult(
                    is_reconciled=False,
                    source_a_name="OC",
                    source_b_name="Distribuciones",
                    total_records_a=len(df_oc),
                    total_records_b=len(df_distro),
                    matched_records=0,
                    metadata={'error': 'Columnas requeridas no encontradas'},
                )

            # Agrupar por SKU
            oc_agrupado = df_oc.groupby(sku_oc)[cant_oc_col].sum()
            distro_agrupado = df_distro.groupby(sku_distro)[cant_distro_col].sum()

            skus_oc = set(oc_agrupado.index)
            skus_distro = set(distro_agrupado.index)

            # SKUs faltantes
            missing_in_distro = list(skus_oc - skus_distro)
            missing_in_oc = list(skus_distro - skus_oc)

            # Comparar cantidades
            skus_comunes = skus_oc & skus_distro
            matched = 0

            for sku in skus_comunes:
                cant_oc = oc_agrupado[sku]
                cant_distro = distro_agrupado[sku]

                if cant_oc == cant_distro:
                    matched += 1
                else:
                    diff = cant_distro - cant_oc
                    pct_diff = (diff / cant_oc * 100) if cant_oc > 0 else 100

                    severity = Severity.CRITICAL if abs(pct_diff) > 10 else Severity.MEDIUM

                    discrepancies.append(DiscrepancyRecord(
                        record_id=str(sku),
                        source_a_name="OC",
                        source_b_name="Distribución",
                        field="CANTIDAD",
                        value_a=cant_oc,
                        value_b=cant_distro,
                        difference=diff,
                        percentage_diff=pct_diff,
                        severity=severity,
                        suggested_correction="Ajustar distribución" if diff > 0 else "Completar distribución",
                    ))

            is_reconciled = len(discrepancies) == 0 and len(missing_in_distro) == 0

            return ReconciliationResult(
                is_reconciled=is_reconciled,
                source_a_name="OC",
                source_b_name="Distribuciones",
                total_records_a=len(skus_oc),
                total_records_b=len(skus_distro),
                matched_records=matched,
                discrepancies=discrepancies,
                missing_in_a=missing_in_oc,
                missing_in_b=missing_in_distro,
            )

        except Exception as e:
            logger.error(f"Error en reconciliación: {e}")
            return ReconciliationResult(
                is_reconciled=False,
                source_a_name="OC",
                source_b_name="Distribuciones",
                total_records_a=len(df_oc),
                total_records_b=len(df_distro),
                matched_records=0,
                metadata={'error': str(e)},
            )

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

__all__ = ['DistributionValidator']
