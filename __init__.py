"""
Módulo de configuración del Sistema SAC
========================================

Este módulo re-exporta las configuraciones desde config.py
para mantener compatibilidad con imports desde la carpeta config/

La versión se importa desde config.py (fuente única de verdad).
"""

import importlib.util
import sys
import os
from pathlib import Path

# Cargar el archivo config.py de la raíz del proyecto
_config_file = Path(__file__).resolve().parent.parent / "config.py"

# Valores por defecto (usados si config.py falla)
__version__ = '1.0.0'
__author__ = 'Julián Alexander Juárez Alvarado'
__author_code__ = 'ADMJAJA'
VERSION = '1.0.0'
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'WM260BASD'),
    'port': int(os.getenv('DB_PORT', 50000)),
    'database': os.getenv('DB_DATABASE', 'WM260BASD'),
    'user': os.getenv('DB_USER', 'tu_usuario'),
    'password': os.getenv('DB_PASSWORD', 'tu_password'),
    'driver': os.getenv('DB_DRIVER', '{IBM DB2 ODBC DRIVER}'),
    'timeout': int(os.getenv('DB_TIMEOUT', 30)),
}
DB_CONNECTION_STRING = ''
DB_POOL_CONFIG = {
    'min_size': 1,
    'max_size': 5,
    'acquire_timeout': 30.0,
    'max_idle_time': 300.0,
    'health_check_interval': 60.0,
    'max_lifetime': 3600.0,
}
CEDIS = {
    'code': os.getenv('CEDIS_CODE', '427'),
    'name': os.getenv('CEDIS_NAME', 'CEDIS Cancún'),
    'region': os.getenv('CEDIS_REGION', 'Sureste'),
    'almacen': os.getenv('CEDIS_ALMACEN', 'C22'),
    'warehouse': os.getenv('CEDIS_WAREHOUSE', 'WM260BASD'),
}
EMAIL_CONFIG = {
    'smtp_server': os.getenv('EMAIL_HOST', 'smtp.office365.com'),
    'smtp_port': int(os.getenv('EMAIL_PORT', 587)),
    'user': os.getenv('EMAIL_USER', 'tu_email@chedraui.com.mx'),
    'password': os.getenv('EMAIL_PASSWORD', 'tu_password'),
    'from_email': os.getenv('EMAIL_FROM', 'sac_cedis427@chedraui.com.mx'),
    'from_name': os.getenv('EMAIL_FROM_NAME', 'Sistema SAC - CEDIS 427'),
    'to_emails': [],
    'cc_emails': [],
    'enable_ssl': True,
}
IMAP_CONFIG = {}
CONFLICT_CONFIG = {}
_base_dir = Path(__file__).resolve().parent.parent
PATHS = {
    'base': _base_dir,
    'output': _base_dir / 'output',
    'logs': _base_dir / 'output' / 'logs',
    'resultados': _base_dir / 'output' / 'resultados',
    'queries': _base_dir / 'queries',
    'docs': _base_dir / 'docs',
    'config': _base_dir / 'config',
    'modules': _base_dir / 'modules',
    'tests': _base_dir / 'tests',
}
COLORS = {
    'chedraui_red': '#E31837',
    'chedraui_blue': '#003DA5',
    'chedraui_green': '#92D050',
    'critico': '#FF0000',
    'alto': '#FFC000',
    'medio': '#FFFF00',
    'bajo': '#92D050',
    'info': '#B4C7E7',
    'header': 'E31837',
    'subheader': 'F8CBAD',
    'ok': '92D050',
    'warning': 'FFC000',
    'error': 'FF0000',
}
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'date_format': '%Y-%m-%d %H:%M:%S',
}
TELEGRAM_CONFIG = {'enabled': False, 'bot_token': '', 'chat_ids': []}
WHATSAPP_CONFIG = {'enabled': False}
HABILITACION_CONFIG = {'enabled': False}
SYSTEM_CONFIG = {
    'version': VERSION,
    'environment': 'development',
    'debug': False,
    'enable_alerts': True,
    'enable_email': True,
    'timezone': 'America/Cancun',
}
UPS_CONFIG = {'health_check_enabled': False}
TRAFICO_CONFIG = {}
API_GLOBAL_CONFIG = {}
AGENTE_CONFIG = {}
OLLAMA_CONFIG = {}
DEVICE_KEYS_CONFIG = {}


class ExcelColors:
    """Colores corporativos Chedraui para Excel"""
    HEADER_RED = "E31837"
    CHEDRAUI_BLUE = "003DA5"
    WHITE = "FFFFFF"
    BLACK = "000000"
    OK_GREEN = "92D050"
    WARNING_YELLOW = "FFC000"
    ERROR_RED = "FF0000"
    INFO_BLUE = "B4C7E7"
    SUBHEADER = "F8CBAD"
    LIGHT_GRAY = "F2F2F2"
    ALT_ROW = "E7E6E6"


EXCEL_COLORS = ExcelColors


def validar_configuracion():
    """Valida la configuración"""
    errores = []
    if DB_CONFIG.get('user') in ('tu_usuario', 'your_user'):
        errores.append("DB_USER no configurado")
    if DB_CONFIG.get('password') in ('tu_password', 'your_password'):
        errores.append("DB_PASSWORD no configurado")
    return len(errores) == 0, errores


def validar_configuracion_critica():
    return validar_configuracion()


def obtener_estado_configuracion():
    return {
        'db_configurada': DB_CONFIG.get('user') not in ('tu_usuario', 'your_user'),
        'email_configurado': EMAIL_CONFIG.get('user') not in ('tu_email@chedraui.com.mx',),
        'configuracion_valida': validar_configuracion()[0],
    }


def imprimir_configuracion():
    print("=" * 60)
    print("CONFIGURACIÓN DEL SISTEMA SAC")
    print("=" * 60)
    print(f"CEDIS: {CEDIS.get('name')} ({CEDIS.get('code')})")
    print(f"DB Host: {DB_CONFIG.get('host')}")
    print(f"DB User: {DB_CONFIG.get('user')}")
    print("=" * 60)


# Intentar cargar el config.py completo para sobrescribir valores por defecto
if _config_file.exists():
    try:
        spec = importlib.util.spec_from_file_location("config_root", str(_config_file))
        if spec and spec.loader:
            _config_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(_config_module)

            # Re-exportar todas las variables públicas desde config.py
            _exports = [
                'VERSION', '__version__', '__author__', '__author_code__',
                'DB_CONFIG', 'DB_CONNECTION_STRING', 'DB_POOL_CONFIG',
                'CEDIS', 'EMAIL_CONFIG', 'IMAP_CONFIG', 'CONFLICT_CONFIG',
                'PATHS', 'COLORS', 'LOGGING_CONFIG', 'TELEGRAM_CONFIG',
                'WHATSAPP_CONFIG', 'HABILITACION_CONFIG', 'SYSTEM_CONFIG',
                'UPS_CONFIG', 'TRAFICO_CONFIG', 'API_GLOBAL_CONFIG',
                'AGENTE_CONFIG', 'OLLAMA_CONFIG', 'DEVICE_KEYS_CONFIG',
                'ExcelColors', 'EXCEL_COLORS',
                'validar_configuracion', 'validar_configuracion_critica',
                'obtener_estado_configuracion', 'imprimir_configuracion',
            ]

            for name in _exports:
                if hasattr(_config_module, name):
                    globals()[name] = getattr(_config_module, name)

    except ImportError as e:
        # Si falta python-dotenv u otra dependencia, usar valores por defecto
        import warnings
        warnings.warn(
            f"No se pudo cargar config.py completamente: {e}. "
            "Usando valores por defecto. Instala las dependencias con: "
            "pip install python-dotenv"
        )
    except Exception as e:
        import warnings
        warnings.warn(f"Error cargando config.py: {e}. Usando valores por defecto.")


# Lista de exports para 'from config import *'
__all__ = [
    'VERSION', '__version__', '__author__', '__author_code__',
    'DB_CONFIG', 'DB_CONNECTION_STRING', 'DB_POOL_CONFIG',
    'CEDIS', 'EMAIL_CONFIG', 'IMAP_CONFIG', 'CONFLICT_CONFIG',
    'PATHS', 'COLORS', 'LOGGING_CONFIG', 'TELEGRAM_CONFIG',
    'WHATSAPP_CONFIG', 'HABILITACION_CONFIG', 'SYSTEM_CONFIG',
    'UPS_CONFIG', 'TRAFICO_CONFIG', 'API_GLOBAL_CONFIG',
    'AGENTE_CONFIG', 'OLLAMA_CONFIG', 'DEVICE_KEYS_CONFIG',
    'ExcelColors', 'EXCEL_COLORS',
    'validar_configuracion', 'validar_configuracion_critica',
    'obtener_estado_configuracion', 'imprimir_configuracion',
]
