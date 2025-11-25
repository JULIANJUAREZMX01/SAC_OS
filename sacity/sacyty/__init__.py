"""
═══════════════════════════════════════════════════════════════════════════════
SACYTY - Sistema de Automatización Chedraui Yucatán TinY
Modelo Ligero para Despliegue en Dispositivos
═══════════════════════════════════════════════════════════════════════════════

SACYTY es una versión optimizada y ligera del Sistema SAC, diseñada para:
- Instalación rápida en dispositivos a recuperar
- Mínimo consumo de recursos
- Funcionalidad esencial sin dependencias pesadas
- Despliegue mediante la suite SAC

Características:
- ~35% del tamaño del sistema completo
- Sin GUI ni dashboard web
- Sin integraciones de mensajería (Telegram/WhatsApp)
- Sin animaciones ni efectos visuales
- Enfocado en validación y conectividad

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
═══════════════════════════════════════════════════════════════════════════════
"""

__version__ = "1.0.0"
__author__ = "ADMJAJA"
__name__ = "SACYTY"
__description__ = "Sistema de Automatización Chedraui - Modelo Ligero"

from .sacyty_core import SACYTYCore
from .sacyty_config import SACYTYConfig
from .sacyty_validator import SACYTYValidator

__all__ = [
    "SACYTYCore",
    "SACYTYConfig",
    "SACYTYValidator",
    "__version__",
    "__author__",
    "__name__",
    "__description__"
]
