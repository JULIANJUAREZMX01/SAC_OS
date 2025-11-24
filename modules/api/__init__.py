"""
═══════════════════════════════════════════════════════════════
MÓDULO DE APIS EXTERNAS
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Sistema modular para integración de APIs externas que agregan
capacidades, recursos y beneficios a las operaciones de SAC.

APIs Activas:
------------
- CalendarAPI: Calendario mexicano con días festivos y hábiles
- ExchangeRateAPI: Tipo de cambio (Banxico/público)
- WeatherAPI: Clima para planificación logística

APIs Futuras (Roadmap):
----------------------
- TelegramBotAPI: Notificaciones y comandos interactivos
- PowerBIAPI: Integración con dashboards
- SAPAPI: Integración con sistema ERP
- FleetTrackingAPI: Rastreo de flotilla
- WhatsAppBusinessAPI: Comunicación con proveedores

Uso:
    from modules.api import (
        APIRegistry, api_registry,
        CalendarAPI, ExchangeRateAPI, WeatherAPI,
        get_api, list_apis
    )

    # Obtener API específica
    calendar = get_api('calendar')
    es_feriado = calendar.es_dia_festivo('2025-12-25')

    # Listar APIs disponibles
    apis = list_apis()

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════
"""

# Importar versión desde configuración centralizada
from config import VERSION

__version__ = VERSION
__author__ = "Julián Alexander Juárez Alvarado"

# ═══════════════════════════════════════════════════════════════
# IMPORTACIONES DEL SISTEMA DE APIS
# ═══════════════════════════════════════════════════════════════

# Core del sistema
from .base import BaseAPIClient, APIResponse, APIError, APIStatus
from .registry import APIRegistry, api_registry, get_api, list_apis, get_api_status
from .config import API_CONFIG, validate_api_config

# Proveedores activos
from .providers.calendar import CalendarAPI, DiaMexicano, TipoDia
from .providers.exchange_rate import ExchangeRateAPI, TipoCambio
from .providers.weather import WeatherAPI, PronosticoClima, CondicionClima

# ═══════════════════════════════════════════════════════════════
# EXPORTACIONES
# ═══════════════════════════════════════════════════════════════

__all__ = [
    # Core
    'BaseAPIClient',
    'APIResponse',
    'APIError',
    'APIStatus',

    # Registry
    'APIRegistry',
    'api_registry',
    'get_api',
    'list_apis',
    'get_api_status',

    # Configuration
    'API_CONFIG',
    'validate_api_config',

    # Calendar API
    'CalendarAPI',
    'DiaMexicano',
    'TipoDia',

    # Exchange Rate API
    'ExchangeRateAPI',
    'TipoCambio',

    # Weather API
    'WeatherAPI',
    'PronosticoClima',
    'CondicionClima',
]
