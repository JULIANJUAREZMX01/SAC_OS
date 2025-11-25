"""
═══════════════════════════════════════════════════════════════
SACITY INSTALLER - Suite de Instalación
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Suite completa de instalación para dispositivos Symbol MC9000

Modos de instalación:
- --full: Instalación completa con UI y emulador
- --minimal: Solo core esencial
- --core-only: Core sin UI

Dispositivos soportados:
- Symbol MC9000, MC9100, MC9200, MC93 series

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
═══════════════════════════════════════════════════════════════
"""

from .suite import *

__all__ = [
    'InstaladorSacity',
    'DetectorDispositivos',
    'AnalizadorHardware',
    'GestorDrivers',
    'OptimizadorDispositivo',
    'DesplegadorSacity',
]

__version__ = '2.0.0'
