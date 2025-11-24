"""
═══════════════════════════════════════════════════════════════
MÓDULO DE DESPLIEGUE EMPRESARIAL SAC
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Este paquete contiene herramientas para el despliegue empresarial
de SAC en entornos Windows corporativos.

Componentes:
- Install-SAC.ps1: Script PowerShell de instalación silenciosa
- sac_windows_service.py: Wrapper para servicio Windows
- README.md: Documentación de despliegue

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
═══════════════════════════════════════════════════════════════
"""

__version__ = "2.0.0"
__author__ = "Julián Alexander Juárez Alvarado"

# Importar componentes disponibles
try:
    from .sac_windows_service import (
        SACStandaloneService,
        install_service,
        remove_service,
        start_service,
        stop_service,
        get_service_status,
        run_debug
    )
except ImportError:
    # En caso de que pywin32 no esté disponible
    pass

__all__ = [
    'SACStandaloneService',
    'install_service',
    'remove_service',
    'start_service',
    'stop_service',
    'get_service_status',
    'run_debug'
]
