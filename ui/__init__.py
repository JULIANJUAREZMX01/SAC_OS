"""
═══════════════════════════════════════════════════════════════
SACITY UI - Interfaz de Usuario
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Interfaz visual ASCII con tema cybersecurity y colores Chedraui

Componentes:
- Componentes UI (components)
- Configuración visual (visual_config)
- Aplicación principal (main)
- Demo interactivo (demo)

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
═══════════════════════════════════════════════════════════════
"""

from .components import *
from .visual_config import *

__all__ = [
    'Colores',
    'ArteASCII',
    'Animador',
    'Caja',
    'Menu',
    'PanelEstado',
]

__version__ = '2.0.0'
