"""
═══════════════════════════════════════════════════════════════
CONFIGURACIÓN DE APIs EXTERNAS
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Configuración centralizada para todas las APIs externas.
Los valores sensibles se cargan desde variables de entorno.

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════
"""

import os
from typing import Dict, List, Tuple

# ═══════════════════════════════════════════════════════════════
# CONFIGURACIÓN GENERAL DE APIs
# ═══════════════════════════════════════════════════════════════

API_CONFIG = {
    # ───────────────────────────────────────────────────────────
    # CONFIGURACIÓN GLOBAL
    # ───────────────────────────────────────────────────────────
    'global': {
        'cache_enabled': os.getenv('API_CACHE_ENABLED', 'true').lower() == 'true',
        'cache_ttl_seconds': int(os.getenv('API_CACHE_TTL', 300)),
        'timeout_seconds': int(os.getenv('API_TIMEOUT', 30)),
        'max_retries': int(os.getenv('API_MAX_RETRIES', 3)),
        'retry_base_delay': float(os.getenv('API_RETRY_DELAY', 1.0)),
    },

    # ───────────────────────────────────────────────────────────
    # CALENDAR API (Calendario Mexicano)
    # Estado: ACTIVA
    # ───────────────────────────────────────────────────────────
    'calendar': {
        'enabled': True,
        'cache_ttl_seconds': 86400,  # 24 horas (datos estáticos)
        'anio_inicio': 2020,
        'anio_fin': 2030,
        'zona_horaria': 'America/Cancun',
    },

    # ───────────────────────────────────────────────────────────
    # EXCHANGE RATE API (Tipo de Cambio)
    # Estado: ACTIVA
    # Fuente: Datos públicos (sin API key requerida)
    # ───────────────────────────────────────────────────────────
    'exchange_rate': {
        'enabled': True,
        'cache_ttl_seconds': 3600,  # 1 hora
        'moneda_base': 'MXN',
        'monedas_seguimiento': ['USD', 'EUR'],
        # Fuentes públicas de tipo de cambio
        'fuentes': [
            'frankfurter',  # API gratuita sin key
            'exchangerate-api',  # Fallback
        ],
    },

    # ───────────────────────────────────────────────────────────
    # WEATHER API (Clima para Logística)
    # Estado: ACTIVA
    # Fuente: Open-Meteo (gratuita, sin API key)
    # ───────────────────────────────────────────────────────────
    'weather': {
        'enabled': True,
        'cache_ttl_seconds': 1800,  # 30 minutos
        # Coordenadas de Cancún (CEDIS)
        'ubicacion_default': {
            'nombre': 'CEDIS Cancún',
            'latitud': 21.1619,
            'longitud': -86.8515,
        },
        # Ubicaciones adicionales para monitoreo
        'ubicaciones_monitoreo': [
            {'nombre': 'Villahermosa', 'latitud': 17.9892, 'longitud': -92.9475},
            {'nombre': 'Mérida', 'latitud': 20.9674, 'longitud': -89.5926},
            {'nombre': 'Chetumal', 'latitud': 18.5001, 'longitud': -88.2961},
        ],
        # Alertas de clima
        'alertas': {
            'temperatura_maxima': 40,  # °C
            'velocidad_viento_maxima': 60,  # km/h
            'probabilidad_lluvia_alta': 70,  # %
        },
    },

    # ───────────────────────────────────────────────────────────
    # TELEGRAM BOT API (Notificaciones)
    # Estado: FUTURO (Roadmap v1.1)
    # Requiere: Bot token y chat IDs
    # ───────────────────────────────────────────────────────────
    # 'telegram': {
    #     'enabled': False,
    #     'bot_token': os.getenv('TELEGRAM_BOT_TOKEN', ''),
    #     'chat_ids': os.getenv('TELEGRAM_CHAT_IDS', '').split(','),
    #     'parse_mode': 'HTML',
    #     'disable_notification_horario': ['22:00', '07:00'],
    # },

    # ───────────────────────────────────────────────────────────
    # SAP INTEGRATION API
    # Estado: FUTURO (Roadmap v2.0)
    # Requiere: Credenciales SAP y configuración de conexión
    # ───────────────────────────────────────────────────────────
    # 'sap': {
    #     'enabled': False,
    #     'base_url': os.getenv('SAP_BASE_URL', ''),
    #     'client': os.getenv('SAP_CLIENT', ''),
    #     'username': os.getenv('SAP_USERNAME', ''),
    #     'password': os.getenv('SAP_PASSWORD', ''),
    #     'timeout_seconds': 60,
    # },

    # ───────────────────────────────────────────────────────────
    # POWER BI API (Dashboards)
    # Estado: FUTURO (Roadmap v2.0)
    # Requiere: Azure AD credentials
    # ───────────────────────────────────────────────────────────
    # 'powerbi': {
    #     'enabled': False,
    #     'tenant_id': os.getenv('POWERBI_TENANT_ID', ''),
    #     'client_id': os.getenv('POWERBI_CLIENT_ID', ''),
    #     'client_secret': os.getenv('POWERBI_CLIENT_SECRET', ''),
    #     'workspace_id': os.getenv('POWERBI_WORKSPACE_ID', ''),
    # },

    # ───────────────────────────────────────────────────────────
    # FLEET TRACKING API (Rastreo de Flotilla)
    # Estado: FUTURO (Roadmap v2.0)
    # Requiere: API del proveedor de GPS
    # ───────────────────────────────────────────────────────────
    # 'fleet_tracking': {
    #     'enabled': False,
    #     'provider': os.getenv('FLEET_PROVIDER', 'samsara'),
    #     'api_key': os.getenv('FLEET_API_KEY', ''),
    #     'refresh_interval_seconds': 60,
    # },

    # ───────────────────────────────────────────────────────────
    # WHATSAPP BUSINESS API
    # Estado: FUTURO (Roadmap v2.0)
    # Requiere: Meta Business Account
    # ───────────────────────────────────────────────────────────
    # 'whatsapp': {
    #     'enabled': False,
    #     'phone_number_id': os.getenv('WHATSAPP_PHONE_ID', ''),
    #     'access_token': os.getenv('WHATSAPP_TOKEN', ''),
    #     'webhook_verify_token': os.getenv('WHATSAPP_WEBHOOK_TOKEN', ''),
    # },

    # ───────────────────────────────────────────────────────────
    # GEOCODING API (Geolocalización)
    # Estado: FUTURO (Roadmap v1.2)
    # Para: Validación de direcciones de entrega
    # ───────────────────────────────────────────────────────────
    # 'geocoding': {
    #     'enabled': False,
    #     'provider': 'nominatim',  # OpenStreetMap (gratuito)
    #     'cache_ttl_seconds': 604800,  # 7 días
    # },

    # ───────────────────────────────────────────────────────────
    # QR/BARCODE API (Generación de códigos)
    # Estado: FUTURO (Roadmap v1.2)
    # Para: Etiquetas de cartones y LPNs
    # ───────────────────────────────────────────────────────────
    # 'barcode': {
    #     'enabled': False,
    #     'default_format': 'CODE128',
    #     'qr_error_correction': 'M',
    # },
}


# ═══════════════════════════════════════════════════════════════
# FUNCIONES DE VALIDACIÓN
# ═══════════════════════════════════════════════════════════════

def validate_api_config() -> Tuple[bool, List[str]]:
    """
    Valida la configuración de APIs.

    Returns:
        Tuple[bool, List[str]]: (es_valida, lista_errores)
    """
    errores = []

    # Validar configuración global
    global_config = API_CONFIG.get('global', {})
    if global_config.get('timeout_seconds', 0) < 5:
        errores.append("⚠️  API_TIMEOUT muy bajo (mínimo 5 segundos)")

    if global_config.get('max_retries', 0) > 10:
        errores.append("⚠️  API_MAX_RETRIES muy alto (máximo recomendado: 10)")

    # Validar configuración de weather
    weather_config = API_CONFIG.get('weather', {})
    if weather_config.get('enabled'):
        ubicacion = weather_config.get('ubicacion_default', {})
        if not ubicacion.get('latitud') or not ubicacion.get('longitud'):
            errores.append("❌ Weather API: Coordenadas no configuradas")

    return len(errores) == 0, errores


def get_api_config(api_name: str) -> Dict:
    """
    Obtiene la configuración de una API específica.

    Args:
        api_name: Nombre de la API

    Returns:
        Dict con la configuración
    """
    # Combinar configuración global con específica
    global_config = API_CONFIG.get('global', {}).copy()
    api_specific = API_CONFIG.get(api_name, {})

    global_config.update(api_specific)
    return global_config


def is_api_enabled(api_name: str) -> bool:
    """
    Verifica si una API está habilitada.

    Args:
        api_name: Nombre de la API

    Returns:
        bool: True si está habilitada
    """
    api_config = API_CONFIG.get(api_name, {})
    return api_config.get('enabled', False)


# ═══════════════════════════════════════════════════════════════
# EXPORTACIONES
# ═══════════════════════════════════════════════════════════════

__all__ = [
    'API_CONFIG',
    'validate_api_config',
    'get_api_config',
    'is_api_enabled',
]
