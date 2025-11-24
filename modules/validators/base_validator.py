"""
═══════════════════════════════════════════════════════════════
VALIDADOR BASE
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Clase base abstracta para todos los validadores del sistema.
Implementa el patrón Template Method para validaciones.

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
═══════════════════════════════════════════════════════════════
"""

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Union

import pandas as pd

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
# REGLA DE VALIDACIÓN
# ═══════════════════════════════════════════════════════════════

@dataclass
class ValidationRule:
    """
    Representa una regla de validación individual

    Atributos:
        name: Nombre único de la regla
        description: Descripción de lo que valida
        severity: Severidad si la regla falla
        validator_func: Función que ejecuta la validación
        enabled: Si la regla está activa
        applicable_to: Tipos de datos a los que aplica
        error_code: Código de error si falla
        suggestion: Sugerencia para corregir
    """
    name: str
    description: str
    severity: Severity
    validator_func: Callable[[Any], bool]
    enabled: bool = True
    applicable_to: List[DataType] = field(default_factory=list)
    error_code: str = ""
    suggestion: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.error_code:
            self.error_code = self.name.upper().replace(" ", "_")

    def evaluate(self, data: Any) -> bool:
        """Evalúa la regla contra los datos proporcionados"""
        if not self.enabled:
            return True
        try:
            return self.validator_func(data)
        except Exception as e:
            logger.error(f"Error evaluando regla '{self.name}': {e}")
            return False


# ═══════════════════════════════════════════════════════════════
# VALIDADOR BASE
# ═══════════════════════════════════════════════════════════════

class BaseValidator(ABC):
    """
    Clase base abstracta para todos los validadores

    Implementa el patrón Template Method donde las subclases
    definen las reglas específicas de validación.
    """

    def __init__(self, name: str = None, data_type: DataType = None):
        """
        Inicializa el validador base

        Args:
            name: Nombre del validador
            data_type: Tipo de datos que valida
        """
        self.name = name or self.__class__.__name__
        self.data_type = data_type
        self._rules: Dict[str, ValidationRule] = {}
        self._enabled = True
        self._register_default_rules()

    @abstractmethod
    def _register_default_rules(self) -> None:
        """
        Registra las reglas por defecto del validador.
        Debe ser implementado por las subclases.
        """
        pass

    def validate(self, data: Any, context: Dict = None) -> ValidationResult:
        """
        Ejecuta todas las validaciones registradas

        Args:
            data: Datos a validar (puede ser DataFrame, dict, etc.)
            context: Contexto adicional para la validación

        Returns:
            ValidationResult con el resultado de todas las validaciones
        """
        start_time = time.time()
        context = context or {}

        logger.info(f"🔍 Iniciando validación con {self.name}")

        violations: List[ValidationViolation] = []
        warnings: List[ValidationWarning] = []

        if not self._enabled:
            logger.warning(f"⏭️ Validador {self.name} deshabilitado")
            return ValidationResult(
                is_valid=True,
                status=ValidationStatus.SKIPPED,
                validator_name=self.name,
                data_type=self.data_type,
            )

        # Pre-validación (datos vacíos, nulos, etc.)
        pre_result = self._pre_validate(data)
        if pre_result:
            violations.extend(pre_result)

        # Si hay errores críticos en pre-validación, retornar temprano
        if any(v.severity == Severity.CRITICAL for v in violations):
            execution_time = (time.time() - start_time) * 1000
            return ValidationResult(
                is_valid=False,
                status=ValidationStatus.FAILED,
                validator_name=self.name,
                data_type=self.data_type,
                violations=violations,
                execution_time_ms=execution_time,
                metadata={'context': context},
            )

        # Ejecutar cada regla
        for rule_name, rule in self._rules.items():
            if not rule.enabled:
                continue

            try:
                passed = rule.evaluate(data)
                if not passed:
                    violation = ValidationViolation(
                        code=rule.error_code,
                        message=rule.description,
                        severity=rule.severity,
                        suggestion=rule.suggestion,
                    )
                    violations.append(violation)
                    logger.warning(f"❌ Regla fallida: {rule.name}")
                else:
                    logger.debug(f"✅ Regla aprobada: {rule.name}")

            except Exception as e:
                logger.error(f"🔴 Error ejecutando regla '{rule_name}': {e}")
                violations.append(ValidationViolation(
                    code=f"RULE_EXECUTION_ERROR_{rule_name.upper()}",
                    message=f"Error ejecutando validación: {str(e)}",
                    severity=Severity.HIGH,
                ))

        # Post-validación (validaciones adicionales específicas)
        post_violations, post_warnings = self._post_validate(data, context)
        violations.extend(post_violations)
        warnings.extend(post_warnings)

        # Determinar resultado final
        execution_time = (time.time() - start_time) * 1000
        has_critical = any(v.severity in [Severity.CRITICAL, Severity.HIGH] for v in violations)

        result = ValidationResult(
            is_valid=not has_critical,
            status=ValidationStatus.FAILED if has_critical else (
                ValidationStatus.WARNING if warnings else ValidationStatus.PASSED
            ),
            validator_name=self.name,
            data_type=self.data_type,
            violations=violations,
            warnings=warnings,
            execution_time_ms=execution_time,
            metadata={'context': context, 'rules_evaluated': len(self._rules)},
        )

        logger.info(f"{'✅' if result.is_valid else '❌'} Validación completada: {result}")
        return result

    def _pre_validate(self, data: Any) -> List[ValidationViolation]:
        """
        Validaciones previas (datos nulos, vacíos, etc.)
        Puede ser sobrescrito por subclases.
        """
        violations = []

        if data is None:
            violations.append(ValidationViolation(
                code="NULL_DATA",
                message="Los datos proporcionados son nulos",
                severity=Severity.CRITICAL,
                suggestion="Proporcionar datos válidos para validación",
            ))
            return violations

        if isinstance(data, pd.DataFrame) and data.empty:
            violations.append(ValidationViolation(
                code="EMPTY_DATAFRAME",
                message="El DataFrame proporcionado está vacío",
                severity=Severity.HIGH,
                suggestion="Verificar que la consulta retorne datos",
            ))

        return violations

    def _post_validate(self, data: Any, context: Dict) -> tuple:
        """
        Validaciones posteriores específicas.
        Puede ser sobrescrito por subclases.

        Returns:
            Tuple[List[ValidationViolation], List[ValidationWarning]]
        """
        return [], []

    # ═══════════════════════════════════════════════════════════════
    # GESTIÓN DE REGLAS
    # ═══════════════════════════════════════════════════════════════

    def add_rule(self, rule: ValidationRule) -> None:
        """Añade una regla de validación"""
        self._rules[rule.name] = rule
        logger.debug(f"📋 Regla añadida: {rule.name}")

    def remove_rule(self, rule_name: str) -> bool:
        """
        Elimina una regla de validación

        Returns:
            True si se eliminó, False si no existía
        """
        if rule_name in self._rules:
            del self._rules[rule_name]
            logger.debug(f"🗑️ Regla eliminada: {rule_name}")
            return True
        return False

    def get_rules(self) -> List[ValidationRule]:
        """Retorna todas las reglas registradas"""
        return list(self._rules.values())

    def get_rule(self, rule_name: str) -> Optional[ValidationRule]:
        """Retorna una regla específica por nombre"""
        return self._rules.get(rule_name)

    def enable_rule(self, rule_name: str) -> bool:
        """Habilita una regla"""
        if rule_name in self._rules:
            self._rules[rule_name].enabled = True
            return True
        return False

    def disable_rule(self, rule_name: str) -> bool:
        """Deshabilita una regla"""
        if rule_name in self._rules:
            self._rules[rule_name].enabled = False
            return True
        return False

    def clear_rules(self) -> None:
        """Elimina todas las reglas"""
        self._rules.clear()
        logger.debug(f"🧹 Todas las reglas eliminadas de {self.name}")

    # ═══════════════════════════════════════════════════════════════
    # MÉTODOS UTILITARIOS
    # ═══════════════════════════════════════════════════════════════

    def enable(self) -> None:
        """Habilita el validador"""
        self._enabled = True

    def disable(self) -> None:
        """Deshabilita el validador"""
        self._enabled = False

    @property
    def is_enabled(self) -> bool:
        """Retorna si el validador está habilitado"""
        return self._enabled

    @property
    def rules_count(self) -> int:
        """Retorna el número de reglas registradas"""
        return len(self._rules)

    def __str__(self) -> str:
        return f"{self.name} ({self.rules_count} reglas)"

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}', rules={self.rules_count})>"


# ═══════════════════════════════════════════════════════════════
# VALIDADORES DE UTILIDAD
# ═══════════════════════════════════════════════════════════════

class DataFrameValidator(BaseValidator):
    """Validador genérico para DataFrames de Pandas"""

    def __init__(self, required_columns: List[str] = None):
        self.required_columns = required_columns or []
        super().__init__(name="DataFrameValidator")

    def _register_default_rules(self) -> None:
        """Registra reglas por defecto para DataFrames"""
        self.add_rule(ValidationRule(
            name="not_empty",
            description="El DataFrame no debe estar vacío",
            severity=Severity.HIGH,
            validator_func=lambda df: isinstance(df, pd.DataFrame) and not df.empty,
        ))

    def _post_validate(self, data: Any, context: Dict) -> tuple:
        """Valida columnas requeridas"""
        violations = []
        warnings = []

        if isinstance(data, pd.DataFrame) and self.required_columns:
            missing_cols = [col for col in self.required_columns if col not in data.columns]
            if missing_cols:
                violations.append(ValidationViolation(
                    code="MISSING_REQUIRED_COLUMNS",
                    message=f"Columnas requeridas faltantes: {', '.join(missing_cols)}",
                    severity=Severity.HIGH,
                    field="columns",
                    expected_value=self.required_columns,
                    actual_value=list(data.columns),
                    suggestion="Verificar que el DataFrame contenga todas las columnas necesarias",
                ))

            # Verificar valores nulos en columnas requeridas existentes
            existing_required = [col for col in self.required_columns if col in data.columns]
            for col in existing_required:
                null_count = data[col].isna().sum()
                if null_count > 0:
                    warnings.append(ValidationWarning(
                        code=f"NULL_VALUES_{col.upper()}",
                        message=f"Se encontraron {null_count} valores nulos en columna '{col}'",
                        field=col,
                    ))

        return violations, warnings


# ═══════════════════════════════════════════════════════════════
# EXPORTAR
# ═══════════════════════════════════════════════════════════════

__all__ = [
    'BaseValidator',
    'ValidationRule',
    'DataFrameValidator',
]
