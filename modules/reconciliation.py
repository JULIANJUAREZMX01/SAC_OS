"""
═══════════════════════════════════════════════════════════════
MOTOR DE RECONCILIACIÓN
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Sistema de reconciliación de datos entre diferentes fuentes
para detectar discrepancias.

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
═══════════════════════════════════════════════════════════════
"""

import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from .validation_result import (
    CorrectionSuggestion,
    DiscrepancyRecord,
    ReconciliationResult,
    Severity,
)

logger = logging.getLogger(__name__)


class ReconciliationEngine:
    """
    Motor de reconciliación de datos

    Compara diferentes fuentes de datos para identificar discrepancias:
    - OC vs Distribuciones
    - ASN vs Recibo
    - Sistema vs Inventario Físico
    """

    def __init__(self, tolerance: float = 0.01):
        """
        Inicializa el motor de reconciliación

        Args:
            tolerance: Tolerancia de diferencia aceptable (0-1)
        """
        self.tolerance = tolerance
        self._last_result: Optional[ReconciliationResult] = None

    # ═══════════════════════════════════════════════════════════════
    # RECONCILIACIÓN OC VS DISTRIBUCIÓN
    # ═══════════════════════════════════════════════════════════════

    def reconcile_oc_vs_distro(self, df_oc: pd.DataFrame,
                               df_distro: pd.DataFrame,
                               key_col: str = 'SKU',
                               qty_col: str = 'CANTIDAD') -> ReconciliationResult:
        """
        Reconcilia OC contra Distribuciones

        Args:
            df_oc: DataFrame con datos de OC
            df_distro: DataFrame con distribuciones
            key_col: Columna clave para match
            qty_col: Columna de cantidad

        Returns:
            ReconciliationResult con el resultado
        """
        start_time = time.time()

        # Validaciones iniciales
        if df_oc is None or df_oc.empty:
            return ReconciliationResult(
                is_reconciled=False,
                source_a_name="OC",
                source_b_name="Distribuciones",
                total_records_a=0,
                total_records_b=len(df_distro) if df_distro is not None else 0,
                matched_records=0,
                metadata={'error': 'OC vacía'},
            )

        if df_distro is None or df_distro.empty:
            return ReconciliationResult(
                is_reconciled=False,
                source_a_name="OC",
                source_b_name="Distribuciones",
                total_records_a=len(df_oc),
                total_records_b=0,
                matched_records=0,
                metadata={'error': 'Sin distribuciones'},
            )

        # Normalizar nombres de columnas
        key_oc = self._find_column(df_oc, key_col)
        key_distro = self._find_column(df_distro, key_col)
        qty_oc = self._find_column(df_oc, qty_col)
        qty_distro = self._find_column(df_distro, qty_col)

        if not all([key_oc, key_distro, qty_oc, qty_distro]):
            return ReconciliationResult(
                is_reconciled=False,
                source_a_name="OC",
                source_b_name="Distribuciones",
                total_records_a=len(df_oc),
                total_records_b=len(df_distro),
                matched_records=0,
                metadata={'error': 'Columnas requeridas no encontradas'},
            )

        # Agrupar por clave
        oc_grouped = df_oc.groupby(key_oc)[qty_oc].sum()
        distro_grouped = df_distro.groupby(key_distro)[qty_distro].sum()

        # Identificar conjuntos
        keys_oc = set(oc_grouped.index)
        keys_distro = set(distro_grouped.index)

        missing_in_distro = list(keys_oc - keys_distro)
        missing_in_oc = list(keys_distro - keys_oc)
        common_keys = keys_oc & keys_distro

        # Comparar cantidades
        discrepancies = []
        matched = 0

        for key in common_keys:
            qty_a = oc_grouped[key]
            qty_b = distro_grouped[key]

            if qty_a == qty_b:
                matched += 1
            else:
                diff = qty_b - qty_a
                pct_diff = (diff / qty_a * 100) if qty_a != 0 else 100

                # Determinar severidad
                if pct_diff > 0:  # Excedente
                    severity = Severity.CRITICAL if abs(pct_diff) > 5 else Severity.HIGH
                    correction = "Reducir distribución"
                else:  # Faltante
                    severity = Severity.HIGH if abs(pct_diff) > 10 else Severity.MEDIUM
                    correction = "Completar distribución"

                discrepancies.append(DiscrepancyRecord(
                    record_id=str(key),
                    source_a_name="OC",
                    source_b_name="Distribución",
                    field=qty_col,
                    value_a=qty_a,
                    value_b=qty_b,
                    difference=diff,
                    percentage_diff=pct_diff,
                    severity=severity,
                    suggested_correction=correction,
                ))

        execution_time = (time.time() - start_time) * 1000

        is_reconciled = (
            len(discrepancies) == 0 and
            len(missing_in_distro) == 0 and
            len(missing_in_oc) == 0
        )

        result = ReconciliationResult(
            is_reconciled=is_reconciled,
            source_a_name="OC",
            source_b_name="Distribuciones",
            total_records_a=len(keys_oc),
            total_records_b=len(keys_distro),
            matched_records=matched,
            discrepancies=discrepancies,
            missing_in_a=missing_in_oc,
            missing_in_b=missing_in_distro,
            execution_time_ms=execution_time,
            metadata={
                'total_qty_oc': oc_grouped.sum(),
                'total_qty_distro': distro_grouped.sum(),
                'difference': distro_grouped.sum() - oc_grouped.sum(),
            },
        )

        self._last_result = result
        logger.info(f"📊 Reconciliación OC vs Distro: {result}")
        return result

    # ═══════════════════════════════════════════════════════════════
    # RECONCILIACIÓN ASN VS RECIBO
    # ═══════════════════════════════════════════════════════════════

    def reconcile_asn_vs_recibo(self, df_asn: pd.DataFrame,
                                df_recibo: pd.DataFrame,
                                key_col: str = 'SKU',
                                qty_col: str = 'CANTIDAD') -> ReconciliationResult:
        """
        Reconcilia ASN contra Recibo

        Args:
            df_asn: DataFrame con datos de ASN
            df_recibo: DataFrame con datos de recibo
            key_col: Columna clave para match
            qty_col: Columna de cantidad

        Returns:
            ReconciliationResult con el resultado
        """
        start_time = time.time()

        if df_asn is None or df_asn.empty:
            return ReconciliationResult(
                is_reconciled=False,
                source_a_name="ASN",
                source_b_name="Recibo",
                total_records_a=0,
                total_records_b=len(df_recibo) if df_recibo is not None else 0,
                matched_records=0,
            )

        if df_recibo is None or df_recibo.empty:
            return ReconciliationResult(
                is_reconciled=False,
                source_a_name="ASN",
                source_b_name="Recibo",
                total_records_a=len(df_asn),
                total_records_b=0,
                matched_records=0,
                metadata={'warning': 'Sin registros de recibo'},
            )

        # Similar lógica a OC vs Distro
        key_asn = self._find_column(df_asn, key_col)
        key_recibo = self._find_column(df_recibo, key_col)
        qty_asn = self._find_column(df_asn, qty_col)
        qty_recibo = self._find_column(df_recibo, qty_col)

        if not all([key_asn, key_recibo, qty_asn, qty_recibo]):
            return ReconciliationResult(
                is_reconciled=False,
                source_a_name="ASN",
                source_b_name="Recibo",
                total_records_a=len(df_asn),
                total_records_b=len(df_recibo),
                matched_records=0,
                metadata={'error': 'Columnas no encontradas'},
            )

        asn_grouped = df_asn.groupby(key_asn)[qty_asn].sum()
        recibo_grouped = df_recibo.groupby(key_recibo)[qty_recibo].sum()

        keys_asn = set(asn_grouped.index)
        keys_recibo = set(recibo_grouped.index)

        missing_in_recibo = list(keys_asn - keys_recibo)
        extra_in_recibo = list(keys_recibo - keys_asn)
        common_keys = keys_asn & keys_recibo

        discrepancies = []
        matched = 0

        for key in common_keys:
            qty_a = asn_grouped[key]
            qty_b = recibo_grouped[key]

            if qty_a == qty_b:
                matched += 1
            else:
                diff = qty_b - qty_a
                pct_diff = (diff / qty_a * 100) if qty_a != 0 else 100

                severity = Severity.CRITICAL if diff > 0 else Severity.HIGH
                correction = "Verificar sobre-recibo" if diff > 0 else "Recibo pendiente"

                discrepancies.append(DiscrepancyRecord(
                    record_id=str(key),
                    source_a_name="ASN",
                    source_b_name="Recibo",
                    field=qty_col,
                    value_a=qty_a,
                    value_b=qty_b,
                    difference=diff,
                    percentage_diff=pct_diff,
                    severity=severity,
                    suggested_correction=correction,
                ))

        execution_time = (time.time() - start_time) * 1000

        is_reconciled = len(discrepancies) == 0 and len(missing_in_recibo) == 0

        result = ReconciliationResult(
            is_reconciled=is_reconciled,
            source_a_name="ASN",
            source_b_name="Recibo",
            total_records_a=len(keys_asn),
            total_records_b=len(keys_recibo),
            matched_records=matched,
            discrepancies=discrepancies,
            missing_in_a=extra_in_recibo,
            missing_in_b=missing_in_recibo,
            execution_time_ms=execution_time,
        )

        self._last_result = result
        logger.info(f"📊 Reconciliación ASN vs Recibo: {result}")
        return result

    # ═══════════════════════════════════════════════════════════════
    # RECONCILIACIÓN DE INVENTARIO
    # ═══════════════════════════════════════════════════════════════

    def reconcile_inventario(self, df_sistema: pd.DataFrame,
                            df_fisico: pd.DataFrame,
                            key_col: str = 'SKU',
                            qty_col: str = 'CANTIDAD',
                            loc_col: str = 'UBICACION') -> ReconciliationResult:
        """
        Reconcilia inventario de sistema vs físico

        Args:
            df_sistema: DataFrame con inventario de sistema
            df_fisico: DataFrame con conteo físico
            key_col: Columna clave (SKU)
            qty_col: Columna de cantidad
            loc_col: Columna de ubicación

        Returns:
            ReconciliationResult con el resultado
        """
        start_time = time.time()

        if df_sistema is None or df_sistema.empty:
            return ReconciliationResult(
                is_reconciled=False,
                source_a_name="Sistema",
                source_b_name="Físico",
                total_records_a=0,
                total_records_b=len(df_fisico) if df_fisico is not None else 0,
                matched_records=0,
            )

        if df_fisico is None or df_fisico.empty:
            return ReconciliationResult(
                is_reconciled=False,
                source_a_name="Sistema",
                source_b_name="Físico",
                total_records_a=len(df_sistema),
                total_records_b=0,
                matched_records=0,
            )

        # Encontrar columnas
        key_sys = self._find_column(df_sistema, key_col)
        key_fis = self._find_column(df_fisico, key_col)
        qty_sys = self._find_column(df_sistema, qty_col)
        qty_fis = self._find_column(df_fisico, qty_col)
        loc_sys = self._find_column(df_sistema, loc_col)
        loc_fis = self._find_column(df_fisico, loc_col)

        if not all([key_sys, key_fis, qty_sys, qty_fis]):
            return ReconciliationResult(
                is_reconciled=False,
                source_a_name="Sistema",
                source_b_name="Físico",
                total_records_a=len(df_sistema),
                total_records_b=len(df_fisico),
                matched_records=0,
                metadata={'error': 'Columnas no encontradas'},
            )

        # Crear clave compuesta (SKU + Ubicación si disponible)
        if loc_sys and loc_fis:
            df_sistema = df_sistema.copy()
            df_fisico = df_fisico.copy()
            df_sistema['_key'] = df_sistema[key_sys].astype(str) + '_' + df_sistema[loc_sys].astype(str)
            df_fisico['_key'] = df_fisico[key_fis].astype(str) + '_' + df_fisico[loc_fis].astype(str)
            key_sys = '_key'
            key_fis = '_key'

        sistema_grouped = df_sistema.groupby(key_sys)[qty_sys].sum()
        fisico_grouped = df_fisico.groupby(key_fis)[qty_fis].sum()

        keys_sistema = set(sistema_grouped.index)
        keys_fisico = set(fisico_grouped.index)

        missing_fisico = list(keys_sistema - keys_fisico)
        extra_fisico = list(keys_fisico - keys_sistema)
        common_keys = keys_sistema & keys_fisico

        discrepancies = []
        matched = 0
        total_variance = 0

        for key in common_keys:
            qty_a = sistema_grouped[key]
            qty_b = fisico_grouped[key]
            diff = qty_b - qty_a

            if abs(diff) <= qty_a * self.tolerance:  # Dentro de tolerancia
                matched += 1
            else:
                total_variance += abs(diff)
                pct_diff = (diff / qty_a * 100) if qty_a != 0 else 100

                # Severidad basada en diferencia
                if abs(pct_diff) > 10:
                    severity = Severity.CRITICAL
                elif abs(pct_diff) > 5:
                    severity = Severity.HIGH
                else:
                    severity = Severity.MEDIUM

                correction = "Ajuste de inventario" if diff < 0 else "Verificar excedente"

                discrepancies.append(DiscrepancyRecord(
                    record_id=str(key),
                    source_a_name="Sistema",
                    source_b_name="Físico",
                    field=qty_col,
                    value_a=qty_a,
                    value_b=qty_b,
                    difference=diff,
                    percentage_diff=pct_diff,
                    severity=severity,
                    suggested_correction=correction,
                ))

        execution_time = (time.time() - start_time) * 1000

        is_reconciled = len(discrepancies) == 0

        result = ReconciliationResult(
            is_reconciled=is_reconciled,
            source_a_name="Sistema",
            source_b_name="Físico",
            total_records_a=len(keys_sistema),
            total_records_b=len(keys_fisico),
            matched_records=matched,
            discrepancies=discrepancies,
            missing_in_a=extra_fisico,
            missing_in_b=missing_fisico,
            execution_time_ms=execution_time,
            metadata={
                'total_variance': total_variance,
                'tolerance_used': self.tolerance,
            },
        )

        self._last_result = result
        logger.info(f"📊 Reconciliación Inventario: {result}")
        return result

    # ═══════════════════════════════════════════════════════════════
    # GENERACIÓN DE REPORTES Y SUGERENCIAS
    # ═══════════════════════════════════════════════════════════════

    def generate_discrepancy_report(self) -> pd.DataFrame:
        """
        Genera un DataFrame con todas las discrepancias del último resultado

        Returns:
            DataFrame con discrepancias
        """
        if not self._last_result or not self._last_result.discrepancies:
            return pd.DataFrame()

        data = []
        for d in self._last_result.discrepancies:
            data.append({
                'ID': d.record_id,
                'Campo': d.field,
                f'Valor_{d.source_a_name}': d.value_a,
                f'Valor_{d.source_b_name}': d.value_b,
                'Diferencia': d.difference,
                'Diferencia_%': f"{d.percentage_diff:.2f}%",
                'Severidad': d.severity.value,
                'Corrección_Sugerida': d.suggested_correction,
            })

        return pd.DataFrame(data)

    def suggest_corrections(self) -> List[CorrectionSuggestion]:
        """
        Genera sugerencias de corrección basadas en las discrepancias

        Returns:
            Lista de CorrectionSuggestion
        """
        if not self._last_result:
            return []

        suggestions = []

        for d in self._last_result.discrepancies:
            # Determinar valor sugerido basado en regla de negocio
            if d.source_a_name == "OC":
                # Para OC vs Distro, ajustar distribución a OC
                suggested = d.value_a
                reason = "La distribución debe igualar la OC"
            elif d.source_a_name == "ASN":
                # Para ASN vs Recibo, mantener lo recibido pero verificar
                suggested = d.value_b
                reason = "Verificar cantidad física recibida"
            else:
                # Por defecto, usar el valor del sistema
                suggested = d.value_a
                reason = "Ajustar al valor del sistema"

            auto_correctable = abs(d.percentage_diff or 0) < 5  # Auto-corregible si <5%

            suggestions.append(CorrectionSuggestion(
                record_id=d.record_id,
                field=d.field,
                current_value=d.value_b,
                suggested_value=suggested,
                correction_type="ADJUSTMENT",
                confidence=0.8 if auto_correctable else 0.5,
                reason=reason,
                auto_correctable=auto_correctable,
                requires_approval=not auto_correctable,
            ))

        return suggestions

    # ═══════════════════════════════════════════════════════════════
    # UTILIDADES
    # ═══════════════════════════════════════════════════════════════

    def _find_column(self, df: pd.DataFrame, col_name: str) -> Optional[str]:
        """Encuentra una columna por nombre (case insensitive)"""
        if df is None or df.empty:
            return None
        for col in df.columns:
            if col.upper() == col_name.upper():
                return col
        return None

    @property
    def last_result(self) -> Optional[ReconciliationResult]:
        """Retorna el último resultado de reconciliación"""
        return self._last_result


# ═══════════════════════════════════════════════════════════════
# EXPORTAR
# ═══════════════════════════════════════════════════════════════

__all__ = ['ReconciliationEngine']
