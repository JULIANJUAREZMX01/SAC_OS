"""
═══════════════════════════════════════════════════════════════
PROVEEDORES DE APIs EXTERNAS
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Proveedores de APIs activos y disponibles para SAC.

APIs Activas:
- CalendarAPI: Calendario mexicano con días festivos
- ExchangeRateAPI: Tipo de cambio MXN/USD
- WeatherAPI: Pronóstico del clima

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════
"""

from .calendar import CalendarAPI, DiaMexicano, TipoDia
from .exchange_rate import ExchangeRateAPI, TipoCambio
from .weather import WeatherAPI, PronosticoClima, CondicionClima

__all__ = [
    # Calendar
    'CalendarAPI',
    'DiaMexicano',
    'TipoDia',

    # Exchange Rate
    'ExchangeRateAPI',
    'TipoCambio',

    # Weather
    'WeatherAPI',
    'PronosticoClima',
    'CondicionClima',
]
