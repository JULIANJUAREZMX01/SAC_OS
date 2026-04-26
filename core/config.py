"""
═══════════════════════════════════════════════════════════════
CONFIGURACIÓN CENTRAL DEL SISTEMA SAC
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Este módulo contiene toda la configuración centralizada del sistema.
TODOS los demás módulos deben importar configuraciones desde aquí.

Uso:
    from config import (
        DB_CONFIG, CEDIS, EMAIL_CONFIG, PATHS, COLORS,
        EXCEL_COLORS, VERSION, SYSTEM_CONFIG
    )

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# ═══════════════════════════════════════════════════════════════
# VERSIÓN DEL SISTEMA (FUENTE ÚNICA DE VERDAD)
# ═══════════════════════════════════════════════════════════════

VERSION = "1.0.0"
__version__ = VERSION
__author__ = "Julián Alexander Juárez Alvarado"
__author_code__ = "ADMJAJA"

# ═══════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE BASE DE DATOS DB2
# ═══════════════════════════════════════════════════════════════

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'lg00bk.chedraui.com'),
    'port': int(os.getenv('DB_PORT', 50000)),
    'database': os.getenv('DB_DATABASE', 'WM260BASD'),
    'user': os.getenv('DB_USER', 'tu_usuario'),
    'password': os.getenv('DB_PASSWORD', 'tu_password'),
    'driver': os.getenv('DB_DRIVER', '{IBM DB2 ODBC DRIVER}'),
    'timeout': int(os.getenv('DB_TIMEOUT', 30)),
}

# String de conexión ODBC
DB_CONNECTION_STRING = (
    f"DRIVER={DB_CONFIG['driver']};"
    f"HOSTNAME={DB_CONFIG['host']};"
    f"PORT={DB_CONFIG['port']};"
    f"DATABASE={DB_CONFIG['database']};"
    f"UID={DB_CONFIG['user']};"
    f"PWD={DB_CONFIG['password']};"
    f"CONNECTTIMEOUT={DB_CONFIG['timeout']};"
)

# ═══════════════════════════════════════════════════════════════
# CONFIGURACIÓN DEL POOL DE CONEXIONES
# ═══════════════════════════════════════════════════════════════

DB_POOL_CONFIG = {
    'min_size': int(os.getenv('DB_POOL_MIN_SIZE', 1)),
    'max_size': int(os.getenv('DB_POOL_MAX_SIZE', 5)),
    'acquire_timeout': float(os.getenv('DB_POOL_ACQUIRE_TIMEOUT', 30.0)),
    'max_idle_time': float(os.getenv('DB_POOL_MAX_IDLE_TIME', 300.0)),  # 5 minutos
    'health_check_interval': float(os.getenv('DB_POOL_HEALTH_CHECK_INTERVAL', 60.0)),  # 1 minuto
    'max_lifetime': float(os.getenv('DB_POOL_MAX_LIFETIME', 3600.0)),  # 1 hora
}

# ═══════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE CEDIS
# ═══════════════════════════════════════════════════════════════

CEDIS = {
    'code': os.getenv('CEDIS_CODE', '427'),
    'name': os.getenv('CEDIS_NAME', 'CEDIS Cancún'),
    'region': os.getenv('CEDIS_REGION', 'Sureste'),
    'almacen': os.getenv('CEDIS_ALMACEN', 'C22'),
    'warehouse': os.getenv('CEDIS_WAREHOUSE', 'WM260BASD'),
}

# ═══════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE EMAIL (ENVÍO - SMTP)
# ═══════════════════════════════════════════════════════════════

EMAIL_CONFIG = {
    'smtp_server': os.getenv('EMAIL_HOST', 'smtp.office365.com'),
    'smtp_port': int(os.getenv('EMAIL_PORT', 587)),
    'user': os.getenv('EMAIL_USER', 'tu_email@chedraui.com.mx'),
    'password': os.getenv('EMAIL_PASSWORD', 'tu_password'),
    'from_email': os.getenv('EMAIL_FROM', 'sac_cedis427@chedraui.com.mx'),
    'from_name': os.getenv('EMAIL_FROM_NAME', 'Sistema SAC - CEDIS 427'),
    'to_emails': [e.strip() for e in os.getenv('EMAIL_TO', 'planning@chedraui.com.mx').split(',') if e.strip()],
    'cc_emails': [e.strip() for e in os.getenv('EMAIL_CC', '').split(',') if e.strip()],
    'enable_ssl': os.getenv('EMAIL_SSL', 'true').lower() == 'true',
}

# ═══════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE EMAIL (RECEPCIÓN - IMAP)
# ═══════════════════════════════════════════════════════════════

IMAP_CONFIG = {
    'imap_host': os.getenv('IMAP_HOST', 'imap.office365.com'),
    'imap_port': int(os.getenv('IMAP_PORT', 993)),
    'imap_user': os.getenv('IMAP_USER') or os.getenv('EMAIL_USER') or 'tu_email@chedraui.com.mx',
    'imap_password': os.getenv('IMAP_PASSWORD') or os.getenv('EMAIL_PASSWORD') or 'tu_password',
    'carpeta_adjuntos': os.getenv('IMAP_CARPETA_ADJUNTOS', 'output/adjuntos'),
}

# ═══════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE CONFLICTOS EXTERNOS
# ═══════════════════════════════════════════════════════════════

CONFLICT_CONFIG = {
    'analista_turno_email': os.getenv('ANALISTA_TURNO_EMAIL', 'planning@chedraui.com.mx'),
    'supervisor_email': os.getenv('SUPERVISOR_EMAIL', 'supervisor@chedraui.com.mx'),
    'dias_busqueda_correos': int(os.getenv('CONFLICT_DIAS_BUSQUEDA', 7)),
    'auto_analizar': os.getenv('CONFLICT_AUTO_ANALIZAR', 'true').lower() == 'true',
    'auto_notificar': os.getenv('CONFLICT_AUTO_NOTIFICAR', 'true').lower() == 'true',
}

# ═══════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE RUTAS
# ═══════════════════════════════════════════════════════════════

# Directorio base del proyecto
BASE_DIR = Path(__file__).resolve().parent

PATHS = {
    'base': BASE_DIR,
    'output': BASE_DIR / 'output',
    'logs': BASE_DIR / 'output' / 'logs',
    'resultados': BASE_DIR / 'output' / 'resultados',
    'queries': BASE_DIR / 'queries',
    'docs': BASE_DIR / 'docs',
    'config': BASE_DIR / 'config',
    'modules': BASE_DIR / 'modules',
    'tests': BASE_DIR / 'tests',
}

# Crear directorios si no existen
for path_name, path in PATHS.items():
    if path_name in ['logs', 'resultados']:
        path.mkdir(parents=True, exist_ok=True)

# ═══════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE LOGGING
# ═══════════════════════════════════════════════════════════════

LOGGING_CONFIG = {
    'level': os.getenv('LOG_LEVEL', 'INFO'),
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'date_format': '%Y-%m-%d %H:%M:%S',
    'file': PATHS['logs'] / f"sac_{os.getenv('CEDIS_CODE', '427')}.log",
    'max_bytes': int(os.getenv('LOG_MAX_BYTES', 10485760)),  # 10MB
    'backup_count': int(os.getenv('LOG_BACKUP_COUNT', 5)),
}

# ═══════════════════════════════════════════════════════════════
# CONFIGURACIÓN DEL SISTEMA
# ═══════════════════════════════════════════════════════════════

SYSTEM_CONFIG = {
    'version': VERSION,  # Usar la constante VERSION centralizada
    'environment': os.getenv('ENVIRONMENT', 'production'),
    'debug': os.getenv('DEBUG', 'false').lower() == 'true',
    'enable_alerts': os.getenv('ENABLE_ALERTS', 'true').lower() == 'true',
    'enable_email': os.getenv('ENABLE_EMAIL', 'true').lower() == 'true',
    'timezone': os.getenv('TIMEZONE', 'America/Cancun'),
}

# ═══════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE TELEGRAM
# ═══════════════════════════════════════════════════════════════

TELEGRAM_CONFIG = {
    'bot_token': os.getenv('TELEGRAM_BOT_TOKEN', ''),
    'chat_ids': [
        cid.strip() for cid in os.getenv('TELEGRAM_CHAT_IDS', '').split(',')
        if cid.strip()
    ],
    'enabled': os.getenv('TELEGRAM_ENABLED', 'true').lower() == 'true',
    'alertas_criticas': os.getenv('TELEGRAM_ALERTAS_CRITICAS', 'true').lower() == 'true',
    'resumen_diario': os.getenv('TELEGRAM_RESUMEN_DIARIO', 'true').lower() == 'true',
}

# ═══════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE WHATSAPP
# ═══════════════════════════════════════════════════════════════

WHATSAPP_CONFIG = {
    'api_url': os.getenv('WHATSAPP_API_URL', ''),
    'api_token': os.getenv('WHATSAPP_API_TOKEN', ''),
    'group_id': os.getenv('WHATSAPP_GROUP_ID', ''),
    'phone_numbers': [
        p.strip() for p in os.getenv('WHATSAPP_PHONE_NUMBERS', '').split(',')
        if p.strip()
    ],
    'enabled': os.getenv('WHATSAPP_ENABLED', 'true').lower() == 'true',
}

# ═══════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE HABILITACIÓN AUTOMÁTICA DE USUARIOS
# ═══════════════════════════════════════════════════════════════

HABILITACION_CONFIG = {
    # Horario de operación
    'hora_inicio': int(os.getenv('HABILITACION_HORA_INICIO', 6)),      # 6:00 AM
    'hora_fin': int(os.getenv('HABILITACION_HORA_FIN', 18)),           # 6:00 PM
    'dias_operacion': os.getenv('HABILITACION_DIAS', '0,1,2,3,4,5').split(','),  # Lun-Sáb
    'timezone': os.getenv('HABILITACION_TIMEZONE', 'America/Cancun'),

    # Intervalos de chequeo
    'intervalo_chequeo_segundos': int(os.getenv('HABILITACION_INTERVALO', 30)),
    'intervalo_dormitorio_segundos': int(os.getenv('HABILITACION_INTERVALO_DORMIDO', 300)),

    # Notificaciones
    'notificar_telegram': os.getenv('HABILITACION_TELEGRAM', 'true').lower() == 'true',
    'notificar_whatsapp': os.getenv('HABILITACION_WHATSAPP', 'true').lower() == 'true',

    # Control
    'enabled': os.getenv('HABILITACION_ENABLED', 'true').lower() == 'true',
    'max_habilitaciones_hora': int(os.getenv('HABILITACION_MAX_POR_HORA', 50)),
}

# ═══════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE APIs EXTERNAS
# ═══════════════════════════════════════════════════════════════

API_GLOBAL_CONFIG = {
    'cache_enabled': os.getenv('API_CACHE_ENABLED', 'true').lower() == 'true',
    'cache_ttl_seconds': int(os.getenv('API_CACHE_TTL', 300)),
    'timeout_seconds': int(os.getenv('API_TIMEOUT', 30)),
    'max_retries': int(os.getenv('API_MAX_RETRIES', 3)),
    'retry_base_delay': float(os.getenv('API_RETRY_DELAY', 1.0)),
}

# ═══════════════════════════════════════════════════════════════
# CONFIGURACIÓN DEL SISTEMA UPS BACKUP
# ═══════════════════════════════════════════════════════════════

UPS_CONFIG = {
    # Health check
    'health_check_interval': int(os.getenv('UPS_HEALTH_CHECK_INTERVAL', 30)),  # segundos
    'max_errores_offline': int(os.getenv('UPS_MAX_ERRORES_OFFLINE', 3)),
    'health_check_enabled': os.getenv('UPS_HEALTH_CHECK_ENABLED', 'true').lower() == 'true',

    # Snapshots
    'snapshot_ttl_default': int(os.getenv('UPS_SNAPSHOT_TTL', 60)),  # minutos
    'auto_snapshot_criticos': os.getenv('UPS_AUTO_SNAPSHOT_CRITICOS', 'true').lower() == 'true',

    # Operaciones pendientes
    'max_intentos_sync': int(os.getenv('UPS_MAX_INTENTOS_SYNC', 3)),
    'expiracion_operaciones_dias': int(os.getenv('UPS_EXPIRACION_OPS_DIAS', 7)),

    # Sincronización
    'auto_sync_enabled': os.getenv('UPS_AUTO_SYNC', 'false').lower() == 'true',
    'sync_batch_size': int(os.getenv('UPS_SYNC_BATCH_SIZE', 100)),

    # Modo mantenimiento
    'mantenimiento_duracion_default': int(os.getenv('UPS_MANT_DURACION', 60)),  # minutos

    # Tablas críticas para snapshot automático
    'tablas_criticas': [
        'ASN',
        'ORDERS',
        'RECEIPTDETAIL',
        'LPNDETAIL',
        'LOTXLOCXID',
    ],
}

# ═══════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE CONTROL DE TRÁFICO
# ═══════════════════════════════════════════════════════════════

TRAFICO_CONFIG = {
    # Almacén configurado
    'almacen': os.getenv('TRAFICO_ALMACEN', '427'),

    # Compuertas
    'compuertas_recibo_inicio': int(os.getenv('TRAFICO_COMP_RECIBO_INICIO', 1)),
    'compuertas_recibo_fin': int(os.getenv('TRAFICO_COMP_RECIBO_FIN', 20)),
    'compuertas_expedicion_inicio': int(os.getenv('TRAFICO_COMP_EXP_INICIO', 21)),
    'compuertas_expedicion_fin': int(os.getenv('TRAFICO_COMP_EXP_FIN', 40)),

    # Horarios de operación
    'hora_inicio': os.getenv('TRAFICO_HORA_INICIO', '06:00'),
    'hora_fin': os.getenv('TRAFICO_HORA_FIN', '22:00'),

    # Configuración de slots
    'duracion_slot_minutos': int(os.getenv('TRAFICO_SLOT_DURACION', 30)),
    'buffer_entre_citas_minutos': int(os.getenv('TRAFICO_BUFFER_CITAS', 10)),

    # Capacidad simultánea
    'capacidad_simultanea_recibo': int(os.getenv('TRAFICO_CAP_RECIBO', 10)),
    'capacidad_simultanea_expedicion': int(os.getenv('TRAFICO_CAP_EXPEDICION', 15)),

    # Circuitos disponibles (para almacén 427)
    'circuitos': [200, 201, 202],

    # Tiempos base de operación (minutos)
    'tiempo_descarga_tarima': float(os.getenv('TRAFICO_TIEMPO_DESCARGA', 2.0)),
    'tiempo_carga_tarima': float(os.getenv('TRAFICO_TIEMPO_CARGA', 2.5)),
    'tiempo_setup_compuerta': int(os.getenv('TRAFICO_TIEMPO_SETUP', 10)),
    'tiempo_liberacion': int(os.getenv('TRAFICO_TIEMPO_LIBERACION', 5)),
    'tiempo_verificacion_docs': int(os.getenv('TRAFICO_TIEMPO_VERIF', 15)),
    'buffer_seguridad': int(os.getenv('TRAFICO_BUFFER_SEGURIDAD', 10)),

    # Aprendizaje automático
    'ml_enabled': os.getenv('TRAFICO_ML_ENABLED', 'true').lower() == 'true',
    'ml_min_muestras': int(os.getenv('TRAFICO_ML_MIN_MUESTRAS', 5)),
    'ml_tasa_aprendizaje': float(os.getenv('TRAFICO_ML_TASA', 0.1)),
    'ml_actualizacion_auto': os.getenv('TRAFICO_ML_AUTO_UPDATE', 'true').lower() == 'true',

    # Alertas de tráfico
    'alerta_retraso_minutos': int(os.getenv('TRAFICO_ALERTA_RETRASO', 15)),
    'alerta_capacidad_pct': float(os.getenv('TRAFICO_ALERTA_CAP', 0.9)),

    # Notificaciones
    'notificar_nuevas_citas': os.getenv('TRAFICO_NOTIF_NUEVAS', 'true').lower() == 'true',
    'notificar_cambios_compuerta': os.getenv('TRAFICO_NOTIF_CAMBIOS', 'true').lower() == 'true',
    'notificar_conflictos': os.getenv('TRAFICO_NOTIF_CONFLICTOS', 'true').lower() == 'true',

    # Días de operación (0=Lunes, 6=Domingo)
    'dias_operacion': [0, 1, 2, 3, 4, 5],  # Lunes a Sábado

    # Visión (placeholder para futuro)
    'vision_enabled': os.getenv('TRAFICO_VISION_ENABLED', 'false').lower() == 'true',
    'vision_camaras': [],  # Se configurará cuando se implemente
}

# Rutas específicas para control de tráfico
PATHS['trafico'] = PATHS['output'] / 'trafico'
PATHS['trafico_scheduling'] = PATHS['output'] / 'trafico' / 'scheduling'
PATHS['trafico'].mkdir(parents=True, exist_ok=True)
PATHS['trafico_scheduling'].mkdir(parents=True, exist_ok=True)

# ═══════════════════════════════════════════════════════════════
# CONFIGURACIÓN DEL AGENTE SAC
# ═══════════════════════════════════════════════════════════════

AGENTE_CONFIG = {
    # Versión del agente
    'version': '1.0.0',
    'codename': 'Godí',

    # Usuario administrador con acceso completo CLI
    'admin_usuario': os.getenv('AGENTE_ADMIN_USER', 'u427jd15'),
    'admin_descripcion': 'Administrador de la red GCH',

    # Usuarios del equipo de sistemas (acceso avanzado)
    'usuarios_sistemas': os.getenv('AGENTE_SISTEMAS_USERS', 'admjaja,larry,adrian').split(','),

    # Configuración de datos
    'data_dir': 'output/agente_sac',
    'max_historial_usuario': int(os.getenv('AGENTE_MAX_HISTORIAL', 100)),
    'max_recordatorios': int(os.getenv('AGENTE_MAX_RECORDATORIOS', 50)),

    # Aprendizaje
    'aprendizaje_enabled': os.getenv('AGENTE_APRENDIZAJE', 'true').lower() == 'true',
    'umbral_favoritos': int(os.getenv('AGENTE_UMBRAL_FAV', 3)),  # Usos para ser favorito

    # Interfaz
    'mostrar_sugerencias': os.getenv('AGENTE_SUGERENCIAS', 'true').lower() == 'true',
    'max_sugerencias': int(os.getenv('AGENTE_MAX_SUGERENCIAS', 5)),

    # Comandos permitidos (para ejecución - solo admin)
    'comandos_permitidos': [
        'python', 'pip', 'git', 'dir', 'ls', 'type', 'cat', 'ipconfig', 'ping',
    ],

    # Timeouts
    'timeout_comando': int(os.getenv('AGENTE_TIMEOUT_CMD', 30)),  # segundos
    'timeout_script': int(os.getenv('AGENTE_TIMEOUT_SCRIPT', 120)),  # segundos
}

# Rutas del Agente SAC
PATHS['agente_sac'] = PATHS['output'] / 'agente_sac'
PATHS['agente_sac'].mkdir(parents=True, exist_ok=True)

# ═══════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE OLLAMA (IA para Agente SAC)
# ═══════════════════════════════════════════════════════════════

OLLAMA_CONFIG = {
    # URL del servidor Ollama
    'base_url': os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434'),

    # API Key (opcional para instalaciones locales)
    'api_key': os.getenv('OLLAMA_API_KEY', ''),

    # Modelos
    'model': os.getenv('OLLAMA_MODEL', 'llama2'),
    'model_fallback': os.getenv('OLLAMA_MODEL_FALLBACK', 'mistral'),

    # Habilitación
    'enabled': os.getenv('OLLAMA_ENABLED', 'true').lower() == 'true',

    # Parámetros de generación
    'timeout': int(os.getenv('OLLAMA_TIMEOUT', 60)),
    'max_tokens': int(os.getenv('OLLAMA_MAX_TOKENS', 2048)),
    'temperature': float(os.getenv('OLLAMA_TEMPERATURE', 0.7)),

    # Prompt del sistema
    'system_prompt': os.getenv(
        'OLLAMA_SYSTEM_PROMPT',
        'Eres el Agente SAC, asistente virtual del CEDIS Cancún 427 de Tiendas Chedraui. '
        'Fuiste creado por Julián Alexander Juárez Alvarado (ADMJAJA), Jefe de Sistemas. '
        'Ayudas a los colaboradores con soporte técnico, consultas del sistema SAC, y resolución de problemas. '
        'Responde de manera profesional, concisa y en español.'
    ),
}

# ═══════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE DEVICE KEYS (Autorización de dispositivos)
# ═══════════════════════════════════════════════════════════════

DEVICE_KEYS_CONFIG = {
    # Master Key del sistema
    'master_key': os.getenv('SAC_MASTER_KEY', ''),
    'master_key_hash': os.getenv('SAC_MASTER_KEY_HASH', ''),
    'master_key_expiry': os.getenv('SAC_MASTER_KEY_EXPIRY', '2026-01-01'),

    # Device keys registradas
    'device_keys': {
        'ADMJAJA': os.getenv('SAC_DEVICE_KEY_ADMJAJA', ''),
        'ADMIN': os.getenv('SAC_DEVICE_KEY_ADMIN', ''),
        'LARRY': os.getenv('SAC_DEVICE_KEY_LARRY', ''),
        'ADRIAN': os.getenv('SAC_DEVICE_KEY_ADRIAN', ''),
        'SERVER': os.getenv('SAC_DEVICE_KEY_SERVER', ''),
    },

    # Lista de keys activas
    'active_keys': [
        k.strip() for k in os.getenv('SAC_ACTIVE_DEVICE_KEYS', '').split(',')
        if k.strip()
    ],

    # Configuración de validación
    'require_device_key': os.getenv('SAC_REQUIRE_DEVICE_KEY', 'true').lower() == 'true',
    'allow_unknown_devices': os.getenv('SAC_ALLOW_UNKNOWN_DEVICES', 'false').lower() == 'true',

    # Formato de keys
    'key_format': 'SAC-{cedis}-{tipo}-{id}',
    'cedis': '427',
}

# ═══════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE COLORES (Para reportes y consola)
# ═══════════════════════════════════════════════════════════════

# Colores con formato #RRGGBB (para uso general)
COLORS = {
    # Colores corporativos Chedraui
    'chedraui_red': '#E31837',
    'chedraui_blue': '#003DA5',
    'chedraui_green': '#92D050',

    # Colores para alertas
    'critico': '#FF0000',
    'alto': '#FFC000',
    'medio': '#FFFF00',
    'bajo': '#92D050',
    'info': '#B4C7E7',

    # Colores para Excel (compatibilidad)
    'header': 'E31837',
    'subheader': 'F8CBAD',
    'ok': '92D050',
    'warning': 'FFC000',
    'error': 'FF0000',
}


# ═══════════════════════════════════════════════════════════════
# COLORES PARA EXCEL (Sin '#' para openpyxl - FUENTE ÚNICA)
# ═══════════════════════════════════════════════════════════════

class ExcelColors:
    """
    Colores corporativos Chedraui para Excel (openpyxl).
    Esta clase es la FUENTE ÚNICA de colores para todos los módulos Excel.

    Uso:
        from config import ExcelColors
        cell.fill = PatternFill(start_color=ExcelColors.HEADER_RED, ...)
    """

    # Colores principales corporativos
    HEADER_RED = "E31837"      # Rojo Chedraui - encabezados
    CHEDRAUI_BLUE = "003DA5"   # Azul Chedraui
    WHITE = "FFFFFF"
    BLACK = "000000"

    # Colores de estado
    OK_GREEN = "92D050"        # Verde - éxito/OK
    WARNING_YELLOW = "FFC000"  # Amarillo/Naranja - advertencia
    ERROR_RED = "FF0000"       # Rojo - error
    INFO_BLUE = "B4C7E7"       # Azul claro - información

    # Colores de fondo
    SUBHEADER = "F8CBAD"       # Durazno claro - subencabezados
    LIGHT_GRAY = "F2F2F2"      # Gris claro
    ALT_ROW = "E7E6E6"         # Filas alternas
    MEDIUM_YELLOW = "FFE699"   # Amarillo medio
    LIGHT_BLUE = "DDEBF7"      # Azul claro fondo
    LIGHT_GREEN = "C6EFCE"     # Verde claro fondo
    LIGHT_RED = "FFC7CE"       # Rojo claro fondo

    # Colores de severidad
    CRITICO = "FF0000"
    ALTO = "FFC000"
    MEDIO = "FFFF00"
    BAJO = "92D050"

    # Colores para gráficos
    CHART_COLORS = [
        "E31837",  # Rojo Chedraui
        "003DA5",  # Azul Chedraui
        "92D050",  # Verde
        "FFC000",  # Naranja
        "7030A0",  # Morado
        "00B0F0",  # Azul claro
        "FF6600",  # Naranja oscuro
        "339933",  # Verde oscuro
    ]


# Alias para compatibilidad
EXCEL_COLORS = ExcelColors

# ═══════════════════════════════════════════════════════════════
# VALIDACIÓN DE CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════

# Valores por defecto inseguros que indican configuración incompleta
_VALORES_DEFAULT_INSEGUROS = {
    'tu_usuario', 'tu_password', 'tu_email@chedraui.com.mx',
    'your_password', 'password', 'admin', 'root', 'test',
    'changeme', 'default', 'secret', '123456', 'qwerty'
}

# Rangos válidos para validación
_RANGOS_VALIDOS = {
    'puerto_db': (1, 65535),
    'puerto_smtp': (1, 65535),
    'timeout_db': (5, 300),
    'pool_min': (1, 10),
    'pool_max': (1, 50),
    'acquire_timeout': (5.0, 120.0),
    'max_idle_time': (60.0, 3600.0),
    'health_check_interval': (10.0, 300.0),
    'max_lifetime': (300.0, 86400.0),  # 5 min a 24 horas
}


def _es_valor_inseguro(valor: str) -> bool:
    """Verifica si un valor es un placeholder inseguro"""
    if not valor:
        return True
    return valor.lower() in _VALORES_DEFAULT_INSEGUROS


def _validar_rango(valor, nombre: str, rango: tuple) -> list:
    """Valida que un valor esté dentro de un rango específico"""
    errores = []
    min_val, max_val = rango
    if valor < min_val:
        errores.append(f"⚠️  {nombre} muy bajo ({valor}), mínimo recomendado: {min_val}")
    elif valor > max_val:
        errores.append(f"⚠️  {nombre} muy alto ({valor}), máximo recomendado: {max_val}")
    return errores


def validar_configuracion_critica() -> tuple:
    """
    Valida SOLO la configuración crítica para operación.

    Returns:
        tuple: (bool, list) - (es_valida, lista_errores_criticos)
    """
    errores = []

    # Validaciones críticas de DB
    if _es_valor_inseguro(DB_CONFIG['user']):
        errores.append("🔴 CRÍTICO: DB_USER no configurado o es inseguro")
    if _es_valor_inseguro(DB_CONFIG['password']):
        errores.append("🔴 CRÍTICO: DB_PASSWORD no configurado o es inseguro")
    if not DB_CONFIG['host']:
        errores.append("🔴 CRÍTICO: DB_HOST no configurado")

    # Validaciones críticas de Email
    if _es_valor_inseguro(EMAIL_CONFIG['user']):
        errores.append("🔴 CRÍTICO: EMAIL_USER no configurado o es inseguro")
    if _es_valor_inseguro(EMAIL_CONFIG['password']):
        errores.append("🔴 CRÍTICO: EMAIL_PASSWORD no configurado o es inseguro")

    return len(errores) == 0, errores


def validar_configuracion():
    """
    Valida que toda la configuración esté correctamente establecida.
    Incluye validaciones críticas, de advertencia e informativas.

    Returns:
        tuple: (bool, list) - (es_valida, lista_errores)
    """
    errores = []

    # 1. Validaciones críticas de DB
    if _es_valor_inseguro(DB_CONFIG['user']):
        errores.append("🔴 CRÍTICO: DB_USER no configurado en .env")
    if _es_valor_inseguro(DB_CONFIG['password']):
        errores.append("🔴 CRÍTICO: DB_PASSWORD no configurado en .env")

    # Validar puerto DB en rango válido
    errores.extend(_validar_rango(
        DB_CONFIG['port'], 'DB_PORT', _RANGOS_VALIDOS['puerto_db']
    ))

    # Validar timeout razonable
    errores.extend(_validar_rango(
        DB_CONFIG['timeout'], 'DB_TIMEOUT', _RANGOS_VALIDOS['timeout_db']
    ))

    # 2. Validaciones críticas de Email
    if _es_valor_inseguro(EMAIL_CONFIG['user']):
        errores.append("🔴 CRÍTICO: EMAIL_USER no configurado en .env")
    if _es_valor_inseguro(EMAIL_CONFIG['password']):
        errores.append("🔴 CRÍTICO: EMAIL_PASSWORD no configurado en .env")

    # Validar puerto SMTP
    errores.extend(_validar_rango(
        EMAIL_CONFIG['smtp_port'], 'EMAIL_PORT', _RANGOS_VALIDOS['puerto_smtp']
    ))
    puertos_smtp_comunes = {25, 465, 587, 2525}
    if EMAIL_CONFIG['smtp_port'] not in puertos_smtp_comunes:
        errores.append(f"ℹ️  EMAIL_PORT ({EMAIL_CONFIG['smtp_port']}) no es un puerto SMTP común")

    # 3. Validar Pool de conexiones - tamaños
    if DB_POOL_CONFIG['min_size'] > DB_POOL_CONFIG['max_size']:
        errores.append("🔴 CRÍTICO: DB_POOL_MIN_SIZE > DB_POOL_MAX_SIZE (configuración inválida)")
    errores.extend(_validar_rango(
        DB_POOL_CONFIG['min_size'], 'DB_POOL_MIN_SIZE', _RANGOS_VALIDOS['pool_min']
    ))
    errores.extend(_validar_rango(
        DB_POOL_CONFIG['max_size'], 'DB_POOL_MAX_SIZE', _RANGOS_VALIDOS['pool_max']
    ))

    # Validar Pool de conexiones - timeouts
    errores.extend(_validar_rango(
        DB_POOL_CONFIG['acquire_timeout'], 'DB_POOL_ACQUIRE_TIMEOUT', _RANGOS_VALIDOS['acquire_timeout']
    ))
    errores.extend(_validar_rango(
        DB_POOL_CONFIG['max_idle_time'], 'DB_POOL_MAX_IDLE_TIME', _RANGOS_VALIDOS['max_idle_time']
    ))
    errores.extend(_validar_rango(
        DB_POOL_CONFIG['health_check_interval'], 'DB_POOL_HEALTH_CHECK_INTERVAL', _RANGOS_VALIDOS['health_check_interval']
    ))
    errores.extend(_validar_rango(
        DB_POOL_CONFIG['max_lifetime'], 'DB_POOL_MAX_LIFETIME', _RANGOS_VALIDOS['max_lifetime']
    ))

    # 4. Validar Telegram (opcional pero recomendado)
    if not TELEGRAM_CONFIG['bot_token']:
        errores.append("ℹ️  TELEGRAM_BOT_TOKEN no configurado (notificaciones deshabilitadas)")
    if not TELEGRAM_CONFIG['chat_ids']:
        errores.append("ℹ️  TELEGRAM_CHAT_IDS no configurado (notificaciones deshabilitadas)")

    # 5. Validar directorios existen
    for path_name in ['logs', 'resultados']:
        if not PATHS[path_name].exists():
            errores.append(f"⚠️  Directorio {path_name} no existe: {PATHS[path_name]}")

    # Solo considerar inválido si hay errores críticos
    errores_criticos = [e for e in errores if "CRÍTICO" in e]
    es_valida = len(errores_criticos) == 0
    return es_valida, errores


def obtener_estado_configuracion() -> dict:
    """
    Obtiene un resumen del estado de la configuración.

    Returns:
        dict: Estado de cada componente de configuración
    """
    es_valida, errores = validar_configuracion()
    errores_criticos = [e for e in errores if "CRÍTICO" in e]
    errores_advertencia = [e for e in errores if "⚠️" in e]

    return {
        # Estado de servicios
        'db_configurada': not _es_valor_inseguro(DB_CONFIG['user']) and not _es_valor_inseguro(DB_CONFIG['password']),
        'email_configurado': not _es_valor_inseguro(EMAIL_CONFIG['user']) and not _es_valor_inseguro(EMAIL_CONFIG['password']),
        'telegram_configurado': bool(TELEGRAM_CONFIG['bot_token'] and TELEGRAM_CONFIG['chat_ids']),
        # Estado del sistema
        'debug_activo': SYSTEM_CONFIG['debug'],
        'alertas_activas': SYSTEM_CONFIG['enable_alerts'],
        'email_activo': SYSTEM_CONFIG['enable_email'],
        'entorno': SYSTEM_CONFIG['environment'],
        # Estado del pool
        'pool_min_size': DB_POOL_CONFIG['min_size'],
        'pool_max_size': DB_POOL_CONFIG['max_size'],
        'pool_configurado_correctamente': DB_POOL_CONFIG['min_size'] <= DB_POOL_CONFIG['max_size'],
        # Resumen de validación
        'configuracion_valida': es_valida,
        'total_errores_criticos': len(errores_criticos),
        'total_advertencias': len(errores_advertencia),
    }


def imprimir_configuracion():
    """
    Imprime un resumen de la configuración actual (sin passwords)
    """
    print("\n" + "="*60)
    print("📋 CONFIGURACIÓN DEL SISTEMA SAC")
    print("="*60)

    print(f"\n🏢 CEDIS:")
    print(f"   Código: {CEDIS['code']}")
    print(f"   Nombre: {CEDIS['name']}")
    print(f"   Región: {CEDIS['region']}")
    print(f"   Almacén: {CEDIS['almacen']}")

    print(f"\n💾 BASE DE DATOS:")
    print(f"   Host: {DB_CONFIG['host']}")
    print(f"   Puerto: {DB_CONFIG['port']}")
    print(f"   Database: {DB_CONFIG['database']}")
    print(f"   Usuario: {DB_CONFIG['user']}")
    print(f"   Password: {'*' * 8 if DB_CONFIG['password'] != 'tu_password' else '❌ NO CONFIGURADO'}")

    print(f"\n📧 EMAIL:")
    print(f"   Servidor: {EMAIL_CONFIG['smtp_server']}")
    print(f"   Puerto: {EMAIL_CONFIG['smtp_port']}")
    print(f"   Usuario: {EMAIL_CONFIG['user']}")
    print(f"   Password: {'*' * 8 if EMAIL_CONFIG['password'] != 'tu_password' else '❌ NO CONFIGURADO'}")
    print(f"   Destinatarios: {', '.join(EMAIL_CONFIG['to_emails'])}")

    print(f"\n🔧 SISTEMA:")
    print(f"   Versión: {SYSTEM_CONFIG['version']}")
    print(f"   Entorno: {SYSTEM_CONFIG['environment']}")
    print(f"   Debug: {SYSTEM_CONFIG['debug']}")
    print(f"   Alertas: {SYSTEM_CONFIG['enable_alerts']}")

    print(f"\n📱 TELEGRAM:")
    telegram_status = "✅ Configurado" if TELEGRAM_CONFIG['bot_token'] else "❌ NO CONFIGURADO"
    print(f"   Bot Token: {telegram_status}")
    print(f"   Chat IDs: {len(TELEGRAM_CONFIG['chat_ids'])} configurados")
    print(f"   Habilitado: {TELEGRAM_CONFIG['enabled']}")
    print(f"   Alertas Críticas: {TELEGRAM_CONFIG['alertas_criticas']}")
    print(f"   Resumen Diario: {TELEGRAM_CONFIG['resumen_diario']}")

    print(f"\n🔋 UPS BACKUP:")
    print(f"   Health Check: {'✅ Habilitado' if UPS_CONFIG['health_check_enabled'] else '❌ Deshabilitado'}")
    print(f"   Intervalo Health Check: {UPS_CONFIG['health_check_interval']}s")
    print(f"   Max Errores Offline: {UPS_CONFIG['max_errores_offline']}")
    print(f"   Snapshot TTL: {UPS_CONFIG['snapshot_ttl_default']} min")
    print(f"   Auto Sync: {'✅' if UPS_CONFIG['auto_sync_enabled'] else '❌'}")
    print(f"   Tablas Críticas: {len(UPS_CONFIG['tablas_criticas'])}")

    print(f"\n📱 WHATSAPP:")
    whatsapp_status = "✅ Configurado" if WHATSAPP_CONFIG['api_url'] and WHATSAPP_CONFIG['api_token'] else "❌ NO CONFIGURADO"
    print(f"   API: {whatsapp_status}")
    print(f"   Grupo ID: {'✅ Configurado' if WHATSAPP_CONFIG['group_id'] else '❌ No configurado'}")
    print(f"   Números: {len(WHATSAPP_CONFIG['phone_numbers'])} configurados")
    print(f"   Habilitado: {WHATSAPP_CONFIG['enabled']}")

    print(f"\n👤 HABILITACIÓN AUTOMÁTICA DE USUARIOS:")
    print(f"   Estado: {'✅ Activo' if HABILITACION_CONFIG['enabled'] else '❌ Inactivo'}")
    print(f"   Horario: {HABILITACION_CONFIG['hora_inicio']}:00 - {HABILITACION_CONFIG['hora_fin']}:00")
    print(f"   Días: Lun-Sáb")
    print(f"   Zona Horaria: {HABILITACION_CONFIG['timezone']}")
    print(f"   Intervalo Chequeo: {HABILITACION_CONFIG['intervalo_chequeo_segundos']}s")
    print(f"   Telegram: {'✅' if HABILITACION_CONFIG['notificar_telegram'] else '❌'}")
    print(f"   WhatsApp: {'✅' if HABILITACION_CONFIG['notificar_whatsapp'] else '❌'}")

    print(f"\n📁 RUTAS:")
    print(f"   Base: {PATHS['base']}")
    print(f"   Output: {PATHS['output']}")
    print(f"   Logs: {PATHS['logs']}")

    # Validar configuración
    es_valida, errores = validar_configuracion()

    if es_valida:
        print(f"\n✅ Configuración válida")
    else:
        print(f"\n⚠️  Errores de configuración encontrados:")
        for error in errores:
            print(f"   {error}")
        print(f"\n💡 Consejo: Configura el archivo .env con tus credenciales")

    print("="*60 + "\n")


# ═══════════════════════════════════════════════════════════════
# EXPORTAR TODO
# ═══════════════════════════════════════════════════════════════

__all__ = [
    # Versión del sistema
    'VERSION',
    '__version__',
    '__author__',
    '__author_code__',

    # Configuraciones principales
    'DB_CONFIG',
    'DB_CONNECTION_STRING',
    'DB_POOL_CONFIG',
    'CEDIS',
    'EMAIL_CONFIG',
    'IMAP_CONFIG',
    'CONFLICT_CONFIG',
    'TELEGRAM_CONFIG',
    'WHATSAPP_CONFIG',
    'HABILITACION_CONFIG',
    'API_GLOBAL_CONFIG',
    'UPS_CONFIG',
    'TRAFICO_CONFIG',
    'AGENTE_CONFIG',
    'OLLAMA_CONFIG',
    'DEVICE_KEYS_CONFIG',
    'PATHS',
    'LOGGING_CONFIG',
    'SYSTEM_CONFIG',

    # Colores
    'COLORS',
    'ExcelColors',
    'EXCEL_COLORS',

    # Funciones de validación
    'validar_configuracion',
    'validar_configuracion_critica',
    'obtener_estado_configuracion',
    'imprimir_configuracion',
]


# ═══════════════════════════════════════════════════════════════
# EJECUTAR AL IMPORTAR
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Si se ejecuta directamente, mostrar configuración
    imprimir_configuracion()
# Alias for compatibility
# Looking at root __init__.py, it says SACITYConfig is in core/config.py.
from sacity.sacyty.sacyty_config import SACYTYConfig as SACITYConfig
