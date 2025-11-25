"""
═══════════════════════════════════════════════════════════════
SACITY CORE - Motor Principal
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Módulo core consolidado que incluye:
- Motor principal (engine)
- Configuración (config)
- Validador (validator)

Anteriormente conocido como SACYTY (typo corregido)

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
═══════════════════════════════════════════════════════════════
"""

from .engine import SACITYCore
from .config import SACITYConfig
from .validator import SACITYValidator, ValidationResult, ValidationStatus

__all__ = [
    'SACITYCore',
    'SACITYConfig',
    'SACITYValidator',
    'ValidationResult',
    'ValidationStatus',
]

__version__ = '2.0.0'
