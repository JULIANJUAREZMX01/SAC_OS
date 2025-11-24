"""
═══════════════════════════════════════════════════════════════
DETECTOR DE ANOMALÍAS
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Sistema de detección de anomalías en datos para identificar:
- Outliers estadísticos
- Duplicados
- Secuencias faltantes
- Patrones inusuales

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
═══════════════════════════════════════════════════════════════
"""

import logging
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

from .validation_result import (
    Anomaly,
    AnomalyReport,
    Severity,
)

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """
    Detector de anomalías para datos de Planning/WMS

    Detecta:
    - Valores atípicos (outliers)
    - Registros duplicados
    - Secuencias numéricas faltantes
    - Patrones inusuales en datos
    """

    def __init__(self, sensitivity: float = 1.5):
        """
        Inicializa el detector de anomalías

        Args:
            sensitivity: Factor de sensibilidad para detección de outliers
                        (menor = más sensible, mayor = menos sensible)
                        Default: 1.5 (estándar IQR)
        """
        self.sensitivity = sensitivity
        self._anomalies: List[Anomaly] = []

    # ═══════════════════════════════════════════════════════════════
    # DETECCIÓN DE OUTLIERS
    # ═══════════════════════════════════════════════════════════════

    def detect_outliers(self, df: pd.DataFrame, column: str,
                       method: str = 'iqr') -> pd.DataFrame:
        """
        Detecta valores atípicos en una columna

        Args:
            df: DataFrame con datos
            column: Columna a analizar
            method: Método de detección ('iqr', 'zscore', 'percentile')

        Returns:
            DataFrame con solo los outliers
        """
        if df is None or df.empty:
            return pd.DataFrame()

        if column not in df.columns:
            logger.warning(f"Columna '{column}' no encontrada")
            return pd.DataFrame()

        # Obtener valores numéricos
        try:
            values = pd.to_numeric(df[column], errors='coerce')
        except Exception:
            logger.warning(f"No se pudo convertir columna '{column}' a numérico")
            return pd.DataFrame()

        if method == 'iqr':
            outliers_mask = self._detect_outliers_iqr(values)
        elif method == 'zscore':
            outliers_mask = self._detect_outliers_zscore(values)
        elif method == 'percentile':
            outliers_mask = self._detect_outliers_percentile(values)
        else:
            outliers_mask = self._detect_outliers_iqr(values)

        outliers_df = df[outliers_mask].copy()

        # Registrar anomalías
        for idx, row in outliers_df.iterrows():
            self._anomalies.append(Anomaly(
                anomaly_id=f"OUT_{uuid.uuid4().hex[:8]}",
                anomaly_type="OUTLIER",
                description=f"Valor atípico en {column}: {row[column]}",
                severity=Severity.MEDIUM,
                affected_field=column,
                affected_value=row[column],
                expected_range=self._get_expected_range(values, method),
                confidence_score=0.85,
                context={'index': idx, 'method': method},
            ))

        logger.info(f"📊 {len(outliers_df)} outliers detectados en '{column}' (método: {method})")
        return outliers_df

    def _detect_outliers_iqr(self, series: pd.Series) -> pd.Series:
        """Detecta outliers usando el método IQR"""
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1

        lower_bound = Q1 - self.sensitivity * IQR
        upper_bound = Q3 + self.sensitivity * IQR

        return (series < lower_bound) | (series > upper_bound)

    def _detect_outliers_zscore(self, series: pd.Series, threshold: float = 3.0) -> pd.Series:
        """Detecta outliers usando Z-score"""
        mean = series.mean()
        std = series.std()

        if std == 0:
            return pd.Series([False] * len(series))

        z_scores = np.abs((series - mean) / std)
        return z_scores > threshold

    def _detect_outliers_percentile(self, series: pd.Series,
                                   lower_pct: float = 1,
                                   upper_pct: float = 99) -> pd.Series:
        """Detecta outliers usando percentiles"""
        lower = series.quantile(lower_pct / 100)
        upper = series.quantile(upper_pct / 100)
        return (series < lower) | (series > upper)

    def _get_expected_range(self, series: pd.Series, method: str) -> str:
        """Obtiene el rango esperado según el método"""
        if method == 'iqr':
            Q1 = series.quantile(0.25)
            Q3 = series.quantile(0.75)
            IQR = Q3 - Q1
            lower = Q1 - self.sensitivity * IQR
            upper = Q3 + self.sensitivity * IQR
        elif method == 'zscore':
            mean = series.mean()
            std = series.std()
            lower = mean - 3 * std
            upper = mean + 3 * std
        else:
            lower = series.quantile(0.01)
            upper = series.quantile(0.99)

        return f"{lower:.2f} - {upper:.2f}"

    # ═══════════════════════════════════════════════════════════════
    # DETECCIÓN DE DUPLICADOS
    # ═══════════════════════════════════════════════════════════════

    def detect_duplicates(self, df: pd.DataFrame,
                         columns: Union[str, List[str]] = None,
                         keep: str = False) -> pd.DataFrame:
        """
        Detecta registros duplicados

        Args:
            df: DataFrame con datos
            columns: Columna(s) para detectar duplicados (None = todas)
            keep: 'first', 'last', o False (marcar todos)

        Returns:
            DataFrame con registros duplicados
        """
        if df is None or df.empty:
            return pd.DataFrame()

        if columns:
            if isinstance(columns, str):
                columns = [columns]
            # Verificar que las columnas existen
            columns = [c for c in columns if c in df.columns]
            if not columns:
                return pd.DataFrame()

        duplicates_mask = df.duplicated(subset=columns, keep=keep)
        duplicates_df = df[duplicates_mask].copy()

        # Registrar anomalías
        cols_str = ', '.join(columns) if columns else 'todas las columnas'
        for idx, row in duplicates_df.iterrows():
            key_values = row[columns].to_dict() if columns else "registro completo"
            self._anomalies.append(Anomaly(
                anomaly_id=f"DUP_{uuid.uuid4().hex[:8]}",
                anomaly_type="DUPLICATE",
                description=f"Registro duplicado en {cols_str}",
                severity=Severity.MEDIUM,
                affected_field=cols_str,
                affected_value=str(key_values),
                confidence_score=1.0,
                context={'index': idx, 'columns': columns},
            ))

        logger.info(f"📊 {len(duplicates_df)} duplicados detectados en [{cols_str}]")
        return duplicates_df

    # ═══════════════════════════════════════════════════════════════
    # DETECCIÓN DE SECUENCIAS FALTANTES
    # ═══════════════════════════════════════════════════════════════

    def detect_missing_sequences(self, df: pd.DataFrame, column: str,
                                prefix: str = None) -> List[Any]:
        """
        Detecta números faltantes en una secuencia

        Args:
            df: DataFrame con datos
            column: Columna con la secuencia
            prefix: Prefijo a remover para extraer números (ej: 'OC')

        Returns:
            Lista de valores faltantes en la secuencia
        """
        if df is None or df.empty or column not in df.columns:
            return []

        try:
            # Extraer valores numéricos
            values = df[column].dropna().astype(str)

            if prefix:
                # Remover prefijo y convertir a números
                numbers = values.str.replace(prefix, '', regex=False)
                numbers = pd.to_numeric(numbers, errors='coerce').dropna()
            else:
                numbers = pd.to_numeric(values, errors='coerce').dropna()

            if numbers.empty:
                return []

            numbers = numbers.astype(int)
            min_val = numbers.min()
            max_val = numbers.max()

            # Encontrar faltantes
            expected = set(range(min_val, max_val + 1))
            actual = set(numbers)
            missing = sorted(expected - actual)

            # Si hay demasiados faltantes, probablemente no es una secuencia continua
            if len(missing) > len(actual) * 0.5:  # Más del 50% faltantes
                logger.info(f"ℹ️ Secuencia en '{column}' no parece ser continua")
                return []

            # Registrar anomalías
            for val in missing[:100]:  # Limitar a 100 para no saturar
                formatted_val = f"{prefix}{val}" if prefix else val
                self._anomalies.append(Anomaly(
                    anomaly_id=f"SEQ_{uuid.uuid4().hex[:8]}",
                    anomaly_type="MISSING_SEQUENCE",
                    description=f"Valor faltante en secuencia: {formatted_val}",
                    severity=Severity.LOW,
                    affected_field=column,
                    affected_value=formatted_val,
                    expected_range=f"{min_val} - {max_val}",
                    confidence_score=0.7,
                ))

            logger.info(f"📊 {len(missing)} valores faltantes en secuencia '{column}'")
            return missing

        except Exception as e:
            logger.error(f"Error detectando secuencias faltantes: {e}")
            return []

    # ═══════════════════════════════════════════════════════════════
    # DETECCIÓN DE PATRONES INUSUALES
    # ═══════════════════════════════════════════════════════════════

    def detect_unusual_patterns(self, df: pd.DataFrame) -> List[Anomaly]:
        """
        Detecta patrones inusuales en los datos

        Args:
            df: DataFrame con datos

        Returns:
            Lista de anomalías detectadas
        """
        patterns: List[Anomaly] = []

        if df is None or df.empty:
            return patterns

        # 1. Detectar columnas con valores únicos muy bajos (posible error)
        for col in df.columns:
            unique_ratio = df[col].nunique() / len(df)
            if unique_ratio < 0.001 and len(df) > 100:  # Menos del 0.1% únicos
                patterns.append(Anomaly(
                    anomaly_id=f"PAT_{uuid.uuid4().hex[:8]}",
                    anomaly_type="LOW_VARIANCE",
                    description=f"Columna '{col}' tiene muy poca variación",
                    severity=Severity.INFO,
                    affected_field=col,
                    affected_value=f"{df[col].nunique()} valores únicos",
                    confidence_score=0.6,
                ))

        # 2. Detectar valores que son todos iguales a cero o vacío
        for col in df.columns:
            if df[col].dtype in ['int64', 'float64']:
                zero_ratio = (df[col] == 0).sum() / len(df)
                if zero_ratio > 0.95:  # Más del 95% son ceros
                    patterns.append(Anomaly(
                        anomaly_id=f"PAT_{uuid.uuid4().hex[:8]}",
                        anomaly_type="MOSTLY_ZERO",
                        description=f"Columna '{col}' tiene más del 95% de valores en cero",
                        severity=Severity.LOW,
                        affected_field=col,
                        affected_value=f"{zero_ratio*100:.1f}% ceros",
                        confidence_score=0.7,
                    ))

        # 3. Detectar valores nulos excesivos
        for col in df.columns:
            null_ratio = df[col].isna().sum() / len(df)
            if null_ratio > 0.5:  # Más del 50% nulos
                severity = Severity.HIGH if null_ratio > 0.9 else Severity.MEDIUM
                patterns.append(Anomaly(
                    anomaly_id=f"PAT_{uuid.uuid4().hex[:8]}",
                    anomaly_type="HIGH_NULL_RATE",
                    description=f"Columna '{col}' tiene {null_ratio*100:.1f}% de valores nulos",
                    severity=severity,
                    affected_field=col,
                    affected_value=f"{null_ratio*100:.1f}% nulos",
                    confidence_score=0.9,
                ))

        # 4. Detectar distribución muy sesgada
        for col in df.select_dtypes(include=[np.number]).columns:
            try:
                skewness = df[col].skew()
                if abs(skewness) > 5:  # Sesgo muy alto
                    patterns.append(Anomaly(
                        anomaly_id=f"PAT_{uuid.uuid4().hex[:8]}",
                        anomaly_type="HIGH_SKEWNESS",
                        description=f"Columna '{col}' tiene distribución muy sesgada",
                        severity=Severity.INFO,
                        affected_field=col,
                        affected_value=f"Skewness: {skewness:.2f}",
                        confidence_score=0.6,
                    ))
            except Exception:
                pass

        self._anomalies.extend(patterns)
        logger.info(f"📊 {len(patterns)} patrones inusuales detectados")
        return patterns

    # ═══════════════════════════════════════════════════════════════
    # GENERACIÓN DE REPORTE
    # ═══════════════════════════════════════════════════════════════

    def generate_anomaly_report(self, df: pd.DataFrame = None,
                                numeric_columns: List[str] = None,
                                key_columns: List[str] = None,
                                sequence_column: str = None) -> AnomalyReport:
        """
        Genera un reporte completo de anomalías

        Args:
            df: DataFrame a analizar
            numeric_columns: Columnas numéricas para detectar outliers
            key_columns: Columnas clave para detectar duplicados
            sequence_column: Columna para detectar secuencias faltantes

        Returns:
            AnomalyReport con todas las anomalías encontradas
        """
        start_time = time.time()
        self._anomalies.clear()  # Limpiar anomalías previas

        total_records = len(df) if df is not None and not df.empty else 0
        outliers_count = 0
        duplicates_count = 0
        missing_sequences: List[Any] = []
        unusual_patterns: List[str] = []

        if df is not None and not df.empty:
            # 1. Detectar outliers en columnas numéricas
            if numeric_columns:
                for col in numeric_columns:
                    if col in df.columns:
                        outliers = self.detect_outliers(df, col)
                        outliers_count += len(outliers)
            else:
                # Auto-detectar columnas numéricas
                for col in df.select_dtypes(include=[np.number]).columns:
                    outliers = self.detect_outliers(df, col)
                    outliers_count += len(outliers)

            # 2. Detectar duplicados
            if key_columns:
                duplicates = self.detect_duplicates(df, key_columns)
            else:
                duplicates = self.detect_duplicates(df)
            duplicates_count = len(duplicates)

            # 3. Detectar secuencias faltantes
            if sequence_column and sequence_column in df.columns:
                missing_sequences = self.detect_missing_sequences(df, sequence_column)

            # 4. Detectar patrones inusuales
            patterns = self.detect_unusual_patterns(df)
            unusual_patterns = [p.description for p in patterns]

        execution_time = (time.time() - start_time) * 1000

        report = AnomalyReport(
            total_records_analyzed=total_records,
            anomalies=self._anomalies.copy(),
            outliers_count=outliers_count,
            duplicates_count=duplicates_count,
            missing_sequences=missing_sequences,
            unusual_patterns=unusual_patterns,
            execution_time_ms=execution_time,
        )

        logger.info(f"📊 Reporte de anomalías generado: {len(report.anomalies)} anomalías en {execution_time:.2f}ms")
        return report

    def analyze_column(self, df: pd.DataFrame, column: str) -> Dict[str, Any]:
        """
        Análisis completo de una columna

        Args:
            df: DataFrame con datos
            column: Columna a analizar

        Returns:
            Diccionario con estadísticas y anomalías
        """
        if df is None or df.empty or column not in df.columns:
            return {}

        analysis = {
            'column': column,
            'dtype': str(df[column].dtype),
            'total_values': len(df[column]),
            'unique_values': df[column].nunique(),
            'null_count': df[column].isna().sum(),
            'null_percentage': (df[column].isna().sum() / len(df)) * 100,
        }

        if df[column].dtype in ['int64', 'float64']:
            analysis.update({
                'min': df[column].min(),
                'max': df[column].max(),
                'mean': df[column].mean(),
                'median': df[column].median(),
                'std': df[column].std(),
                'outliers_count': len(self.detect_outliers(df, column)),
            })

        return analysis

    # ═══════════════════════════════════════════════════════════════
    # UTILIDADES
    # ═══════════════════════════════════════════════════════════════

    def clear_anomalies(self) -> None:
        """Limpia las anomalías detectadas"""
        self._anomalies.clear()

    @property
    def anomalies(self) -> List[Anomaly]:
        """Retorna las anomalías detectadas"""
        return self._anomalies.copy()

    @property
    def anomaly_count(self) -> int:
        """Número de anomalías detectadas"""
        return len(self._anomalies)


# ═══════════════════════════════════════════════════════════════
# EXPORTAR
# ═══════════════════════════════════════════════════════════════

__all__ = ['AnomalyDetector']
