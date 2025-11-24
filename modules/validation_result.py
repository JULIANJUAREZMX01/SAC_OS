"""
═══════════════════════════════════════════════════════════════
CLASES DE RESULTADO DE VALIDACIÓN
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Clases para representar resultados de validaciones y operaciones
del sistema SAC.

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
═══════════════════════════════════════════════════════════════
"""

import logging
from dataclasses import dataclass, field as dataclass_field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# ENUMERACIONES
# ═══════════════════════════════════════════════════════════════

class ValidationStatus(Enum):
    """Estado de una validación"""
    PASSED = "✅ APROBADO"
    FAILED = "❌ FALLIDO"
    WARNING = "⚠️ ADVERTENCIA"
    SKIPPED = "⏭️ OMITIDO"
    ERROR = "🔴 ERROR"


class Severity(Enum):
    """Niveles de severidad para errores y advertencias"""
    CRITICAL = "🔴 CRÍTICO"
    HIGH = "🟠 ALTO"
    MEDIUM = "🟡 MEDIO"
    LOW = "🟢 BAJO"
    INFO = "ℹ️ INFO"

    @property
    def priority(self) -> int:
        """Retorna prioridad numérica (mayor = más crítico)"""
        priorities = {
            Severity.CRITICAL: 5,
            Severity.HIGH: 4,
            Severity.MEDIUM: 3,
            Severity.LOW: 2,
            Severity.INFO: 1,
        }
        return priorities.get(self, 0)


class DataType(Enum):
    """Tipos de datos que se pueden validar"""
    OC = "ORDEN_COMPRA"
    DISTRIBUTION = "DISTRIBUCION"
    ASN = "ASN"
    SKU = "SKU"
    LPN = "LPN"
    LOCATION = "UBICACION"
    USER = "USUARIO"
    INVENTORY = "INVENTARIO"
    RECEIPT = "RECIBO"
    SHIPMENT = "ENVIO"


# ═══════════════════════════════════════════════════════════════
# CLASES DE VIOLACIÓN Y ERROR
# ═══════════════════════════════════════════════════════════════

@dataclass
class ValidationViolation:
    """Representa una violación de regla de validación"""
    code: str
    message: str
    severity: Severity
    field: Optional[str] = None
    expected_value: Optional[Any] = None
    actual_value: Optional[Any] = None
    suggestion: Optional[str] = None
    affected_records: Optional[List[Any]] = None
    timestamp: datetime = dataclass_field(default_factory=datetime.now)

    def __str__(self) -> str:
        return f"{self.severity.value} [{self.code}] {self.message}"

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la violación a diccionario"""
        return {
            'code': self.code,
            'message': self.message,
            'severity': self.severity.value,
            'field': self.field,
            'expected_value': str(self.expected_value) if self.expected_value else None,
            'actual_value': str(self.actual_value) if self.actual_value else None,
            'suggestion': self.suggestion,
            'affected_records_count': len(self.affected_records) if self.affected_records else 0,
            'timestamp': self.timestamp.isoformat(),
        }


@dataclass
class ValidationWarning:
    """Representa una advertencia de validación (no crítica)"""
    code: str
    message: str
    field: Optional[str] = None
    details: Optional[str] = None
    timestamp: datetime = dataclass_field(default_factory=datetime.now)

    def __str__(self) -> str:
        return f"⚠️ [{self.code}] {self.message}"


# ═══════════════════════════════════════════════════════════════
# RESULTADO DE VALIDACIÓN
# ═══════════════════════════════════════════════════════════════

@dataclass
class ValidationResult:
    """
    Resultado de una validación individual o conjunto de validaciones

    Atributos:
        is_valid: Indica si la validación pasó
        status: Estado de la validación
        validator_name: Nombre del validador que ejecutó la validación
        data_type: Tipo de dato validado
        violations: Lista de violaciones encontradas
        warnings: Lista de advertencias
        metadata: Información adicional sobre la validación
        execution_time_ms: Tiempo de ejecución en milisegundos
        timestamp: Momento de la validación
    """
    is_valid: bool
    status: ValidationStatus
    validator_name: str
    data_type: Optional[DataType] = None
    violations: List[ValidationViolation] = dataclass_field(default_factory=list)
    warnings: List[ValidationWarning] = dataclass_field(default_factory=list)
    metadata: Dict[str, Any] = dataclass_field(default_factory=dict)
    execution_time_ms: float = 0.0
    timestamp: datetime = dataclass_field(default_factory=datetime.now)

    def __str__(self) -> str:
        status_str = "✅ VÁLIDO" if self.is_valid else "❌ INVÁLIDO"
        return f"{status_str} - {self.validator_name}: {len(self.violations)} violaciones, {len(self.warnings)} advertencias"

    @property
    def has_critical_violations(self) -> bool:
        """Verifica si hay violaciones críticas"""
        return any(v.severity == Severity.CRITICAL for v in self.violations)

    @property
    def has_high_violations(self) -> bool:
        """Verifica si hay violaciones altas o críticas"""
        return any(v.severity in [Severity.CRITICAL, Severity.HIGH] for v in self.violations)

    @property
    def max_severity(self) -> Optional[Severity]:
        """Retorna la severidad máxima encontrada"""
        if not self.violations:
            return None
        return max(self.violations, key=lambda v: v.severity.priority).severity

    def add_violation(self, violation: ValidationViolation) -> None:
        """Añade una violación al resultado"""
        self.violations.append(violation)
        if violation.severity in [Severity.CRITICAL, Severity.HIGH]:
            self.is_valid = False
            self.status = ValidationStatus.FAILED

    def add_warning(self, warning: ValidationWarning) -> None:
        """Añade una advertencia al resultado"""
        self.warnings.append(warning)
        if self.status == ValidationStatus.PASSED:
            self.status = ValidationStatus.WARNING

    def merge(self, other: 'ValidationResult') -> 'ValidationResult':
        """Combina dos resultados de validación"""
        merged = ValidationResult(
            is_valid=self.is_valid and other.is_valid,
            status=ValidationStatus.FAILED if not (self.is_valid and other.is_valid) else self.status,
            validator_name=f"{self.validator_name}+{other.validator_name}",
            data_type=self.data_type or other.data_type,
            violations=self.violations + other.violations,
            warnings=self.warnings + other.warnings,
            metadata={**self.metadata, **other.metadata},
            execution_time_ms=self.execution_time_ms + other.execution_time_ms,
        )
        return merged

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el resultado a diccionario"""
        return {
            'is_valid': self.is_valid,
            'status': self.status.value,
            'validator_name': self.validator_name,
            'data_type': self.data_type.value if self.data_type else None,
            'violations_count': len(self.violations),
            'warnings_count': len(self.warnings),
            'violations': [v.to_dict() for v in self.violations],
            'warnings': [str(w) for w in self.warnings],
            'max_severity': self.max_severity.value if self.max_severity else None,
            'execution_time_ms': self.execution_time_ms,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata,
        }

    @classmethod
    def create_passed(cls, validator_name: str, data_type: DataType = None,
                      metadata: Dict = None) -> 'ValidationResult':
        """Crea un resultado exitoso"""
        return cls(
            is_valid=True,
            status=ValidationStatus.PASSED,
            validator_name=validator_name,
            data_type=data_type,
            metadata=metadata or {},
        )

    @classmethod
    def create_failed(cls, validator_name: str, violations: List[ValidationViolation],
                      data_type: DataType = None, metadata: Dict = None) -> 'ValidationResult':
        """Crea un resultado fallido"""
        return cls(
            is_valid=False,
            status=ValidationStatus.FAILED,
            validator_name=validator_name,
            data_type=data_type,
            violations=violations,
            metadata=metadata or {},
        )


# ═══════════════════════════════════════════════════════════════
# RESULTADO DE RECONCILIACIÓN
# ═══════════════════════════════════════════════════════════════

@dataclass
class DiscrepancyRecord:
    """Representa una discrepancia encontrada durante reconciliación"""
    record_id: str
    source_a_name: str
    source_b_name: str
    field: str
    value_a: Any
    value_b: Any
    difference: Optional[Any] = None
    percentage_diff: Optional[float] = None
    severity: Severity = Severity.MEDIUM
    suggested_correction: Optional[str] = None

    def __str__(self) -> str:
        return f"[{self.record_id}] {self.field}: {self.value_a} vs {self.value_b}"


@dataclass
class ReconciliationResult:
    """
    Resultado de una operación de reconciliación

    Compara dos fuentes de datos y reporta discrepancias
    """
    is_reconciled: bool
    source_a_name: str
    source_b_name: str
    total_records_a: int
    total_records_b: int
    matched_records: int
    discrepancies: List[DiscrepancyRecord] = dataclass_field(default_factory=list)
    missing_in_a: List[str] = dataclass_field(default_factory=list)
    missing_in_b: List[str] = dataclass_field(default_factory=list)
    metadata: Dict[str, Any] = dataclass_field(default_factory=dict)
    execution_time_ms: float = 0.0
    timestamp: datetime = dataclass_field(default_factory=datetime.now)

    def __str__(self) -> str:
        status = "✅ RECONCILIADO" if self.is_reconciled else "❌ DISCREPANCIAS"
        return f"{status} - {self.source_a_name} vs {self.source_b_name}: {len(self.discrepancies)} discrepancias"

    @property
    def match_rate(self) -> float:
        """Tasa de coincidencia como porcentaje"""
        total = max(self.total_records_a, self.total_records_b)
        if total == 0:
            return 100.0
        return (self.matched_records / total) * 100

    @property
    def discrepancy_rate(self) -> float:
        """Tasa de discrepancia como porcentaje"""
        return 100.0 - self.match_rate

    @property
    def critical_discrepancies(self) -> List[DiscrepancyRecord]:
        """Filtra discrepancias críticas"""
        return [d for d in self.discrepancies if d.severity == Severity.CRITICAL]

    def add_discrepancy(self, discrepancy: DiscrepancyRecord) -> None:
        """Añade una discrepancia"""
        self.discrepancies.append(discrepancy)
        self.is_reconciled = False

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el resultado a diccionario"""
        return {
            'is_reconciled': self.is_reconciled,
            'source_a': self.source_a_name,
            'source_b': self.source_b_name,
            'total_records_a': self.total_records_a,
            'total_records_b': self.total_records_b,
            'matched_records': self.matched_records,
            'match_rate': round(self.match_rate, 2),
            'discrepancy_count': len(self.discrepancies),
            'missing_in_a': len(self.missing_in_a),
            'missing_in_b': len(self.missing_in_b),
            'critical_discrepancies': len(self.critical_discrepancies),
            'execution_time_ms': self.execution_time_ms,
            'timestamp': self.timestamp.isoformat(),
        }


# ═══════════════════════════════════════════════════════════════
# RESULTADO DE DETECCIÓN DE ANOMALÍAS
# ═══════════════════════════════════════════════════════════════

@dataclass
class Anomaly:
    """Representa una anomalía detectada en los datos"""
    anomaly_id: str
    anomaly_type: str
    description: str
    severity: Severity
    affected_field: str
    affected_value: Any
    expected_range: Optional[str] = None
    confidence_score: float = 1.0
    context: Dict[str, Any] = dataclass_field(default_factory=dict)
    timestamp: datetime = dataclass_field(default_factory=datetime.now)

    def __str__(self) -> str:
        return f"{self.severity.value} [{self.anomaly_type}] {self.description}"

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la anomalía a diccionario"""
        return {
            'anomaly_id': self.anomaly_id,
            'type': self.anomaly_type,
            'description': self.description,
            'severity': self.severity.value,
            'field': self.affected_field,
            'value': str(self.affected_value),
            'expected_range': self.expected_range,
            'confidence': self.confidence_score,
            'timestamp': self.timestamp.isoformat(),
        }


@dataclass
class AnomalyReport:
    """Reporte de anomalías detectadas"""
    total_records_analyzed: int
    anomalies: List[Anomaly] = dataclass_field(default_factory=list)
    outliers_count: int = 0
    duplicates_count: int = 0
    missing_sequences: List[Any] = dataclass_field(default_factory=list)
    unusual_patterns: List[str] = dataclass_field(default_factory=list)
    metadata: Dict[str, Any] = dataclass_field(default_factory=dict)
    execution_time_ms: float = 0.0
    timestamp: datetime = dataclass_field(default_factory=datetime.now)

    def __str__(self) -> str:
        return f"📊 Análisis de {self.total_records_analyzed} registros: {len(self.anomalies)} anomalías detectadas"

    @property
    def anomaly_rate(self) -> float:
        """Tasa de anomalías como porcentaje"""
        if self.total_records_analyzed == 0:
            return 0.0
        return (len(self.anomalies) / self.total_records_analyzed) * 100

    @property
    def critical_anomalies(self) -> List[Anomaly]:
        """Filtra anomalías críticas"""
        return [a for a in self.anomalies if a.severity == Severity.CRITICAL]

    def add_anomaly(self, anomaly: Anomaly) -> None:
        """Añade una anomalía al reporte"""
        self.anomalies.append(anomaly)

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el reporte a diccionario"""
        return {
            'total_records': self.total_records_analyzed,
            'total_anomalies': len(self.anomalies),
            'anomaly_rate': round(self.anomaly_rate, 2),
            'outliers': self.outliers_count,
            'duplicates': self.duplicates_count,
            'missing_sequences': len(self.missing_sequences),
            'unusual_patterns': len(self.unusual_patterns),
            'critical_count': len(self.critical_anomalies),
            'execution_time_ms': self.execution_time_ms,
            'timestamp': self.timestamp.isoformat(),
        }


# ═══════════════════════════════════════════════════════════════
# RESULTADO DE REGLA
# ═══════════════════════════════════════════════════════════════

@dataclass
class RuleResult:
    """Resultado de la evaluación de una regla de negocio"""
    rule_name: str
    rule_description: str
    passed: bool
    message: str
    violations: List[ValidationViolation] = dataclass_field(default_factory=list)
    metadata: Dict[str, Any] = dataclass_field(default_factory=dict)
    timestamp: datetime = dataclass_field(default_factory=datetime.now)

    def __str__(self) -> str:
        status = "✅" if self.passed else "❌"
        return f"{status} {self.rule_name}: {self.message}"

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el resultado a diccionario"""
        return {
            'rule_name': self.rule_name,
            'description': self.rule_description,
            'passed': self.passed,
            'message': self.message,
            'violations_count': len(self.violations),
            'timestamp': self.timestamp.isoformat(),
        }


# ═══════════════════════════════════════════════════════════════
# CORRECTION SUGGESTION
# ═══════════════════════════════════════════════════════════════

@dataclass
class CorrectionSuggestion:
    """Sugerencia de corrección para una discrepancia o error"""
    record_id: str
    field: str
    current_value: Any
    suggested_value: Any
    correction_type: str
    confidence: float
    reason: str
    auto_correctable: bool = False
    requires_approval: bool = True

    def __str__(self) -> str:
        return f"[{self.record_id}] {self.field}: '{self.current_value}' → '{self.suggested_value}'"

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la sugerencia a diccionario"""
        return {
            'record_id': self.record_id,
            'field': self.field,
            'current_value': str(self.current_value),
            'suggested_value': str(self.suggested_value),
            'correction_type': self.correction_type,
            'confidence': self.confidence,
            'reason': self.reason,
            'auto_correctable': self.auto_correctable,
            'requires_approval': self.requires_approval,
        }


# ═══════════════════════════════════════════════════════════════
# EXPORTAR TODO
# ═══════════════════════════════════════════════════════════════

__all__ = [
    # Enums
    'ValidationStatus',
    'Severity',
    'DataType',
    # Violation & Warning
    'ValidationViolation',
    'ValidationWarning',
    # Results
    'ValidationResult',
    'ReconciliationResult',
    'DiscrepancyRecord',
    'AnomalyReport',
    'Anomaly',
    'RuleResult',
    'CorrectionSuggestion',
]
