#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
===============================================================================
SACITY - Sistema de Automatización de Consultas - Emulador Telnet
===============================================================================

SACITY es un emulador de terminal Telnet/Velocity optimizado para dispositivos
Symbol MC9000/MC9100/MC9200/MC93 que permite la comunicación con sistemas
Manhattan WMS (Warehouse Management System).

COMPONENTES:
- sacity_installer_suite: Suite completa de instalación para desplegar SACITY
- sacity_client_ce: Cliente emulador que corre EN el dispositivo Windows CE
- sacity_core: Sistema core ligero (importado de módulo existente)
- sacity_config: Configuración del sistema
- sacity_validator: Validadores para datos de entrada

USO:
    # Para PC - Instalar en dispositivos
    from sacity import InstaladorSacity, ConfiguracionSacity

    instalador = InstaladorSacity()
    config = ConfiguracionSacity(wms_host="192.168.1.1", wms_port=23)
    instalador.ejecutar_instalacion_completa(config)

    # Para Dispositivo CE - Cliente emulador
    from sacity.sacity_client_ce import SacityClient

    client = SacityClient(config)
    client.connect()

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
CEDIS Cancún 427 - Tiendas Chedraui
===============================================================================
"""

__version__ = "1.0.0"
__author__ = "Julián Alexander Juárez Alvarado (ADMJAJA)"
__email__ = "sistemas@chedraui.com.mx"
__description__ = "Emulador Telnet/Velocity para Symbol MC9000"

# Importar componentes principales
try:
    from .sacity_installer_suite import (
        InstaladorSacity,
        ConfiguracionSacity,
        DetectorDispositivos,
        AnalizadorHardware,
        GestorDrivers,
        OptimizadorDispositivo,
        DesplegadorSacity,
        InfoDispositivo,
        EstadoInstalacion,
        TipoConexion,
        FaseInstalacion
    )
except ImportError:
    pass

# Importar cliente CE (puede no estar disponible en todas las plataformas)
try:
    from .sacity_client_ce import (
        SacityClient,
        TelnetClient,
        ScreenBuffer,
        ScannerHandler
    )
except ImportError:
    pass

# Importar componentes existentes del core
try:
    from .sacyty_core import SACyty
    from .sacyty_config import SACytyConfig
    from .sacyty_validator import SACytyValidator
except ImportError:
    pass

# Exportar todo
__all__ = [
    # Version info
    '__version__',
    '__author__',
    '__description__',

    # Installer Suite
    'InstaladorSacity',
    'ConfiguracionSacity',
    'DetectorDispositivos',
    'AnalizadorHardware',
    'GestorDrivers',
    'OptimizadorDispositivo',
    'DesplegadorSacity',
    'InfoDispositivo',
    'EstadoInstalacion',
    'TipoConexion',
    'FaseInstalacion',

    # Client CE
    'SacityClient',
    'TelnetClient',
    'ScreenBuffer',
    'ScannerHandler',

    # Core (legacy)
    'SACyty',
    'SACytyConfig',
    'SACytyValidator'
]
