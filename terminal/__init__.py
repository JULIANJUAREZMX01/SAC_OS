"""
═══════════════════════════════════════════════════════════════
SACITY TERMINAL - Emulador VT100/VT220
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Emulador de terminal Telnet para dispositivos Symbol MC9000

Componentes:
- Shell VT100/VT220 (shell)
- Cliente CE para Windows Embedded (client_ce)

Soporta:
- Dispositivos Symbol MC9190, MC9200, MC9300
- Windows CE 5.0, 6.0, 7.0
- Conexión Telnet con reconexión automática

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
═══════════════════════════════════════════════════════════════
"""

from .shell import SacityShell, BufferPantalla
from .client_ce import SacityClient

__all__ = [
    'SacityShell',
    'BufferPantalla',
    'SacityClient',
]

__version__ = '2.0.0'
