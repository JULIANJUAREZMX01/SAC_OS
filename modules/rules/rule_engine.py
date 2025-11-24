"""
═══════════════════════════════════════════════════════════════
MOTOR DE REGLAS DE NEGOCIO
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Motor para evaluar reglas de negocio configurables.

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
═══════════════════════════════════════════════════════════════
"""

import logging
import time
import yaml
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

import pandas as pd

from ..validation_result import (
    DataType,
    Severity,
    RuleResult,
    ValidationViolation,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# CLASES DE REGLA
# ═══════════════════════════════════════════════════════════════

@dataclass
class Rule:
    """
    Representa una regla de negocio

    Atributos:
        name: Nombre único de la regla
        description: Descripción de lo que valida
        category: Categoría de la regla (OC, DISTRO, ASN, etc.)
        severity: Severidad si la regla falla
        condition: Función o expresión que evalúa la regla
        message_template: Plantilla de mensaje de error
        enabled: Si la regla está activa
        priority: Prioridad de ejecución (menor = más alta)
        applicable_types: Tipos de datos a los que aplica
        metadata: Información adicional
    """
    name: str
    description: str
    category: str
    severity: Severity
    condition: Union[Callable[[Any], bool], str]
    message_template: str = ""
    enabled: bool = True
    priority: int = 100
    applicable_types: List[DataType] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def evaluate(self, data: Any, context: Dict = None) -> RuleResult:
        """
        Evalúa la regla contra los datos proporcionados

        Args:
            data: Datos a evaluar
            context: Contexto adicional

        Returns:
            RuleResult con el resultado de la evaluación
        """
        context = context or {}

        if not self.enabled:
            return RuleResult(
                rule_name=self.name,
                rule_description=self.description,
                passed=True,
                message="Regla deshabilitada",
                metadata={'skipped': True},
            )

        try:
            # Evaluar condición
            if callable(self.condition):
                passed = self.condition(data)
            elif isinstance(self.condition, str):
                # Evaluar expresión string (con cuidado)
                passed = self._evaluate_expression(self.condition, data, context)
            else:
                passed = False

            violations = []
            if not passed:
                message = self._format_message(data, context)
                violations.append(ValidationViolation(
                    code=f"RULE_{self.name.upper()}",
                    message=message,
                    severity=self.severity,
                ))

            return RuleResult(
                rule_name=self.name,
                rule_description=self.description,
                passed=passed,
                message=self._format_message(data, context) if not passed else "OK",
                violations=violations,
                metadata={'category': self.category},
            )

        except Exception as e:
            logger.error(f"Error evaluando regla '{self.name}': {e}")
            return RuleResult(
                rule_name=self.name,
                rule_description=self.description,
                passed=False,
                message=f"Error evaluando regla: {str(e)}",
                violations=[ValidationViolation(
                    code=f"RULE_ERROR_{self.name.upper()}",
                    message=f"Error en evaluación: {str(e)}",
                    severity=Severity.HIGH,
                )],
            )

    def _evaluate_expression(self, expr: str, data: Any, context: Dict) -> bool:
        """Evalúa una expresión string de forma segura"""
        # Contexto seguro para evaluación
        safe_context = {
            'data': data,
            'context': context,
            'len': len,
            'sum': sum,
            'min': min,
            'max': max,
            'abs': abs,
            'isinstance': isinstance,
            'pd': pd,
        }

        if isinstance(data, pd.DataFrame):
            safe_context['df'] = data

        try:
            return eval(expr, {"__builtins__": {}}, safe_context)
        except Exception as e:
            logger.warning(f"Error evaluando expresión '{expr}': {e}")
            return False

    def _format_message(self, data: Any, context: Dict) -> str:
        """Formatea el mensaje de error con datos del contexto"""
        if not self.message_template:
            return self.description

        try:
            format_vars = {'data': data, **context}
            if isinstance(data, pd.DataFrame):
                format_vars['rows'] = len(data)
            return self.message_template.format(**format_vars)
        except Exception:
            return self.description


# ═══════════════════════════════════════════════════════════════
# MOTOR DE REGLAS
# ═══════════════════════════════════════════════════════════════

class RuleEngine:
    """
    Motor para gestionar y evaluar reglas de negocio

    Características:
    - Carga reglas desde archivos YAML
    - Evaluación condicional por tipo de datos
    - Priorización de reglas
    - Resultados detallados
    """

    def __init__(self):
        """Inicializa el motor de reglas"""
        self._rules: Dict[str, Rule] = {}
        self._categories: Dict[str, List[str]] = {}

    def load_rules(self, config_file: Union[str, Path]) -> int:
        """
        Carga reglas desde un archivo YAML

        Args:
            config_file: Ruta al archivo de configuración

        Returns:
            Número de reglas cargadas
        """
        config_path = Path(config_file)

        if not config_path.exists():
            logger.warning(f"Archivo de reglas no encontrado: {config_path}")
            return 0

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            if not config or 'rules' not in config:
                logger.warning("No se encontraron reglas en el archivo")
                return 0

            count = 0
            for rule_config in config['rules']:
                rule = self._create_rule_from_config(rule_config)
                if rule:
                    self.add_rule(rule)
                    count += 1

            logger.info(f"✅ {count} reglas cargadas desde {config_path}")
            return count

        except Exception as e:
            logger.error(f"Error cargando reglas: {e}")
            return 0

    def _create_rule_from_config(self, config: Dict) -> Optional[Rule]:
        """Crea una regla desde configuración de diccionario"""
        try:
            # Mapear severidad
            severity_map = {
                'critical': Severity.CRITICAL,
                'high': Severity.HIGH,
                'medium': Severity.MEDIUM,
                'low': Severity.LOW,
                'info': Severity.INFO,
            }

            severity = severity_map.get(
                config.get('severity', 'medium').lower(),
                Severity.MEDIUM
            )

            # Mapear tipos de datos
            type_map = {
                'oc': DataType.OC,
                'distribution': DataType.DISTRIBUTION,
                'asn': DataType.ASN,
                'sku': DataType.SKU,
                'lpn': DataType.LPN,
            }

            applicable_types = [
                type_map[t.lower()]
                for t in config.get('applicable_types', [])
                if t.lower() in type_map
            ]

            return Rule(
                name=config['name'],
                description=config.get('description', ''),
                category=config.get('category', 'general'),
                severity=severity,
                condition=config.get('condition', 'True'),
                message_template=config.get('message', ''),
                enabled=config.get('enabled', True),
                priority=config.get('priority', 100),
                applicable_types=applicable_types,
                metadata=config.get('metadata', {}),
            )

        except KeyError as e:
            logger.error(f"Configuración de regla incompleta: falta '{e}'")
            return None
        except Exception as e:
            logger.error(f"Error creando regla: {e}")
            return None

    def add_rule(self, rule: Rule) -> None:
        """Añade una regla al motor"""
        self._rules[rule.name] = rule

        # Indexar por categoría
        if rule.category not in self._categories:
            self._categories[rule.category] = []
        if rule.name not in self._categories[rule.category]:
            self._categories[rule.category].append(rule.name)

        logger.debug(f"📋 Regla añadida: {rule.name} ({rule.category})")

    def remove_rule(self, rule_name: str) -> bool:
        """Elimina una regla del motor"""
        if rule_name in self._rules:
            rule = self._rules[rule_name]
            del self._rules[rule_name]

            # Actualizar índice de categorías
            if rule.category in self._categories:
                self._categories[rule.category] = [
                    r for r in self._categories[rule.category]
                    if r != rule_name
                ]

            logger.debug(f"🗑️ Regla eliminada: {rule_name}")
            return True
        return False

    def get_rule(self, rule_name: str) -> Optional[Rule]:
        """Obtiene una regla por nombre"""
        return self._rules.get(rule_name)

    def get_rules_by_category(self, category: str) -> List[Rule]:
        """Obtiene todas las reglas de una categoría"""
        rule_names = self._categories.get(category, [])
        return [self._rules[name] for name in rule_names if name in self._rules]

    def get_applicable_rules(self, data_type: DataType) -> List[Rule]:
        """
        Obtiene reglas aplicables a un tipo de datos

        Args:
            data_type: Tipo de datos a filtrar

        Returns:
            Lista de reglas aplicables
        """
        applicable = []
        for rule in self._rules.values():
            if not rule.applicable_types or data_type in rule.applicable_types:
                applicable.append(rule)

        # Ordenar por prioridad
        return sorted(applicable, key=lambda r: r.priority)

    def evaluate_rule(self, rule_name: str, data: Any,
                     context: Dict = None) -> RuleResult:
        """
        Evalúa una regla específica

        Args:
            rule_name: Nombre de la regla
            data: Datos a evaluar
            context: Contexto adicional

        Returns:
            RuleResult con el resultado
        """
        rule = self._rules.get(rule_name)

        if not rule:
            return RuleResult(
                rule_name=rule_name,
                rule_description="Regla no encontrada",
                passed=False,
                message=f"Regla '{rule_name}' no existe en el motor",
            )

        return rule.evaluate(data, context)

    def evaluate_all(self, data: Any, context: Dict = None,
                    data_type: DataType = None,
                    category: str = None) -> List[RuleResult]:
        """
        Evalúa todas las reglas aplicables

        Args:
            data: Datos a evaluar
            context: Contexto adicional
            data_type: Filtrar por tipo de datos
            category: Filtrar por categoría

        Returns:
            Lista de RuleResult
        """
        start_time = time.time()
        context = context or {}
        results = []

        # Filtrar reglas
        rules_to_evaluate = []

        if category:
            rules_to_evaluate = self.get_rules_by_category(category)
        elif data_type:
            rules_to_evaluate = self.get_applicable_rules(data_type)
        else:
            rules_to_evaluate = sorted(
                self._rules.values(),
                key=lambda r: r.priority
            )

        # Evaluar reglas
        for rule in rules_to_evaluate:
            if not rule.enabled:
                continue

            result = rule.evaluate(data, context)
            results.append(result)

        execution_time = (time.time() - start_time) * 1000
        logger.info(
            f"✅ {len(results)} reglas evaluadas en {execution_time:.2f}ms "
            f"({sum(1 for r in results if r.passed)} pasaron, "
            f"{sum(1 for r in results if not r.passed)} fallaron)"
        )

        return results

    def evaluate_and_summarize(self, data: Any, context: Dict = None,
                               data_type: DataType = None) -> Dict[str, Any]:
        """
        Evalúa reglas y retorna un resumen

        Args:
            data: Datos a evaluar
            context: Contexto adicional
            data_type: Filtrar por tipo de datos

        Returns:
            Diccionario con resumen de resultados
        """
        results = self.evaluate_all(data, context, data_type)

        passed = [r for r in results if r.passed]
        failed = [r for r in results if not r.passed]

        # Agrupar fallos por severidad
        by_severity = {}
        for result in failed:
            for v in result.violations:
                sev = v.severity.value
                if sev not in by_severity:
                    by_severity[sev] = []
                by_severity[sev].append({
                    'rule': result.rule_name,
                    'message': v.message,
                })

        return {
            'total_rules': len(results),
            'passed': len(passed),
            'failed': len(failed),
            'pass_rate': len(passed) / len(results) * 100 if results else 100,
            'by_severity': by_severity,
            'failed_rules': [r.rule_name for r in failed],
            'timestamp': datetime.now().isoformat(),
        }

    # ═══════════════════════════════════════════════════════════════
    # PROPIEDADES Y UTILIDADES
    # ═══════════════════════════════════════════════════════════════

    @property
    def rules_count(self) -> int:
        """Número total de reglas"""
        return len(self._rules)

    @property
    def categories(self) -> List[str]:
        """Lista de categorías disponibles"""
        return list(self._categories.keys())

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

    def enable_category(self, category: str) -> int:
        """Habilita todas las reglas de una categoría"""
        count = 0
        for rule_name in self._categories.get(category, []):
            if rule_name in self._rules:
                self._rules[rule_name].enabled = True
                count += 1
        return count

    def disable_category(self, category: str) -> int:
        """Deshabilita todas las reglas de una categoría"""
        count = 0
        for rule_name in self._categories.get(category, []):
            if rule_name in self._rules:
                self._rules[rule_name].enabled = False
                count += 1
        return count

    def clear_rules(self) -> None:
        """Elimina todas las reglas"""
        self._rules.clear()
        self._categories.clear()
        logger.info("🧹 Todas las reglas eliminadas")

    def __str__(self) -> str:
        return f"RuleEngine({self.rules_count} reglas, {len(self.categories)} categorías)"


# ═══════════════════════════════════════════════════════════════
# EXPORTAR
# ═══════════════════════════════════════════════════════════════

__all__ = ['RuleEngine', 'Rule']
