"""
═══════════════════════════════════════════════════════════════
MÓDULO DE REGLAS DE NEGOCIO
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Motor de reglas de negocio y configuración de reglas para
el sistema SAC.

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
═══════════════════════════════════════════════════════════════
"""

from .rule_engine import RuleEngine, Rule
from .business_rules import BusinessRules, REGLAS_PREDEFINIDAS

__all__ = [
    'RuleEngine',
    'Rule',
    'BusinessRules',
    'REGLAS_PREDEFINIDAS',
]
