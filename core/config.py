"""
═══════════════════════════════════════════════════════════════════════════════
SACYTY - Configuración Ligera
Sistema de Automatización Chedraui - Modelo TinY
═══════════════════════════════════════════════════════════════════════════════

Configuración mínima para despliegue en dispositivos a recuperar.
Sin dependencias externas para carga de variables de entorno.

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
═══════════════════════════════════════════════════════════════════════════════
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass, field

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTES DEL SISTEMA
# ═══════════════════════════════════════════════════════════════════════════════

SACYTY_VERSION = "1.0.0"
SACYTY_NAME = "SACYTY"
SACYTY_DESCRIPTION = "Sistema de Automatización Chedraui - Modelo Ligero"

# ═══════════════════════════════════════════════════════════════════════════════
# RUTAS BASE
# ═══════════════════════════════════════════════════════════════════════════════

def get_base_path() -> Path:
    """Obtener ruta base del sistema SACYTY"""
    return Path(__file__).parent.parent


def get_sacyty_path() -> Path:
    """Obtener ruta del módulo SACYTY"""
    return Path(__file__).parent


# ═══════════════════════════════════════════════════════════════════════════════
# CARGA DE VARIABLES DE ENTORNO (SIN DEPENDENCIAS)
# ═══════════════════════════════════════════════════════════════════════════════

def load_env_file(env_path: Optional[Path] = None) -> Dict[str, str]:
    """
    Cargar variables de entorno desde archivo .env sin dependencias externas.

    Args:
        env_path: Ruta al archivo .env (opcional)

    Returns:
        Dict con las variables cargadas
    """
    if env_path is None:
        env_path = get_base_path() / ".env"

    env_vars = {}

    if not env_path.exists():
        return env_vars

    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Ignorar comentarios y líneas vacías
                if not line or line.startswith('#'):
                    continue

                # Separar clave=valor
                if '=' in line:
                    key, _, value = line.partition('=')
                    key = key.strip()
                    value = value.strip()

                    # Remover comillas si existen
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]

                    env_vars[key] = value
                    # También establecer en os.environ
                    os.environ.setdefault(key, value)
    except Exception as e:
        logging.warning(f"No se pudo cargar .env: {e}")

    return env_vars


# Cargar variables al importar el módulo
_ENV_VARS = load_env_file()


def get_env(key: str, default: str = "") -> str:
    """Obtener variable de entorno con valor por defecto"""
    return os.environ.get(key, _ENV_VARS.get(key, default))


def get_env_bool(key: str, default: bool = False) -> bool:
    """Obtener variable de entorno como booleano"""
    value = get_env(key, str(default)).lower()
    return value in ('true', '1', 'yes', 'si', 'on')


def get_env_int(key: str, default: int = 0) -> int:
    """Obtener variable de entorno como entero"""
    try:
        return int(get_env(key, str(default)))
    except ValueError:
        return default


# ═══════════════════════════════════════════════════════════════════════════════
# DATACLASS DE CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class DatabaseConfig:
    """Configuración de conexión a base de datos"""
    host: str = "WM260BASD"
    port: int = 50000
    database: str = "WM260BASD"
    schema: str = "WMWHSE1"
    user: str = ""
    password: str = ""
    driver: str = "IBM DB2 ODBC DRIVER"
    timeout: int = 30
    pool_size: int = 3

    @classmethod
    def from_env(cls) -> 'DatabaseConfig':
        """Crear configuración desde variables de entorno"""
        return cls(
            host=get_env('DB_HOST', 'WM260BASD'),
            port=get_env_int('DB_PORT', 50000),
            database=get_env('DB_DATABASE', 'WM260BASD'),
            schema=get_env('DB_SCHEMA', 'WMWHSE1'),
            user=get_env('DB_USER', ''),
            password=get_env('DB_PASSWORD', ''),
            driver=get_env('DB_DRIVER', 'IBM DB2 ODBC DRIVER'),
            timeout=get_env_int('DB_TIMEOUT', 30),
            pool_size=get_env_int('DB_POOL_SIZE', 3)
        )

    def get_connection_string(self) -> str:
        """Generar cadena de conexión ODBC"""
        return (
            f"DRIVER={{{self.driver}}};"
            f"HOSTNAME={self.host};"
            f"PORT={self.port};"
            f"DATABASE={self.database};"
            f"PROTOCOL=TCPIP;"
            f"UID={self.user};"
            f"PWD={self.password};"
        )

    def is_configured(self) -> bool:
        """Verificar si las credenciales están configuradas"""
        return bool(self.user and self.password)


@dataclass
class CEDISConfig:
    """Configuración del CEDIS"""
    code: str = "427"
    name: str = "CEDIS Cancún"
    region: str = "Sureste"
    warehouse: str = "C22"
    timezone: str = "America/Cancun"

    @classmethod
    def from_env(cls) -> 'CEDISConfig':
        """Crear configuración desde variables de entorno"""
        return cls(
            code=get_env('CEDIS_CODE', '427'),
            name=get_env('CEDIS_NAME', 'CEDIS Cancún'),
            region=get_env('CEDIS_REGION', 'Sureste'),
            warehouse=get_env('CEDIS_ALMACEN', 'C22'),
            timezone=get_env('TIMEZONE', 'America/Cancun')
        )


@dataclass
class EmailConfig:
    """Configuración de correo electrónico"""
    host: str = "smtp.office365.com"
    port: int = 587
    user: str = ""
    password: str = ""
    from_name: str = "SACYTY - Sistema Ligero"
    use_tls: bool = True

    @classmethod
    def from_env(cls) -> 'EmailConfig':
        """Crear configuración desde variables de entorno"""
        return cls(
            host=get_env('EMAIL_HOST', 'smtp.office365.com'),
            port=get_env_int('EMAIL_PORT', 587),
            user=get_env('EMAIL_USER', ''),
            password=get_env('EMAIL_PASSWORD', ''),
            from_name=get_env('EMAIL_FROM_NAME', 'SACYTY - Sistema Ligero'),
            use_tls=get_env_bool('EMAIL_USE_TLS', True)
        )

    def is_configured(self) -> bool:
        """Verificar si las credenciales están configuradas"""
        return bool(self.user and self.password)


@dataclass
class PathsConfig:
    """Configuración de rutas del sistema"""
    base: Path = field(default_factory=get_base_path)
    sacyty: Path = field(default_factory=get_sacyty_path)
    logs: Path = field(default_factory=lambda: get_base_path() / "output" / "logs")
    output: Path = field(default_factory=lambda: get_base_path() / "output" / "resultados")
    queries: Path = field(default_factory=lambda: get_base_path() / "queries")
    temp: Path = field(default_factory=lambda: get_base_path() / "output" / "temp")

    def ensure_directories(self) -> None:
        """Crear directorios necesarios si no existen"""
        for path in [self.logs, self.output, self.temp]:
            path.mkdir(parents=True, exist_ok=True)


@dataclass
class LoggingConfig:
    """Configuración de logging"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"
    max_bytes: int = 5242880  # 5MB
    backup_count: int = 3

    @classmethod
    def from_env(cls) -> 'LoggingConfig':
        """Crear configuración desde variables de entorno"""
        return cls(
            level=get_env('LOG_LEVEL', 'INFO'),
            format=get_env('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
            date_format=get_env('LOG_DATE_FORMAT', '%Y-%m-%d %H:%M:%S'),
            max_bytes=get_env_int('LOG_MAX_BYTES', 5242880),
            backup_count=get_env_int('LOG_BACKUP_COUNT', 3)
        )


# ═══════════════════════════════════════════════════════════════════════════════
# CLASE PRINCIPAL DE CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════════════════════

class SACYTYConfig:
    """
    Configuración centralizada para SACYTY.
    Modelo ligero sin dependencias externas para .env
    """

    def __init__(self, config_file: Optional[Path] = None):
        """
        Inicializar configuración.

        Args:
            config_file: Archivo de configuración JSON opcional
        """
        # Cargar desde .env primero
        load_env_file()

        # Inicializar configuraciones
        self.database = DatabaseConfig.from_env()
        self.cedis = CEDISConfig.from_env()
        self.email = EmailConfig.from_env()
        self.paths = PathsConfig()
        self.logging = LoggingConfig.from_env()

        # Metadatos del sistema
        self.version = SACYTY_VERSION
        self.name = SACYTY_NAME
        self.description = SACYTY_DESCRIPTION
        self.environment = get_env('ENVIRONMENT', 'production')
        self.debug = get_env_bool('DEBUG', False)

        # Cargar configuración desde archivo JSON si existe
        if config_file and config_file.exists():
            self._load_from_json(config_file)

        # Asegurar que los directorios existan
        self.paths.ensure_directories()

        # Configurar logging
        self._setup_logging()

    def _load_from_json(self, config_file: Path) -> None:
        """Cargar configuración desde archivo JSON"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Aplicar configuraciones del JSON
            if 'database' in data:
                for key, value in data['database'].items():
                    if hasattr(self.database, key):
                        setattr(self.database, key, value)

            if 'cedis' in data:
                for key, value in data['cedis'].items():
                    if hasattr(self.cedis, key):
                        setattr(self.cedis, key, value)

            if 'email' in data:
                for key, value in data['email'].items():
                    if hasattr(self.email, key):
                        setattr(self.email, key, value)

        except Exception as e:
            logging.warning(f"Error cargando configuración JSON: {e}")

    def _setup_logging(self) -> None:
        """Configurar sistema de logging"""
        log_level = getattr(logging, self.logging.level.upper(), logging.INFO)

        # Configurar formato
        formatter = logging.Formatter(
            self.logging.format,
            datefmt=self.logging.date_format
        )

        # Handler de consola
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(log_level)

        # Configurar logger raíz
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)

        # Limpiar handlers existentes
        root_logger.handlers.clear()
        root_logger.addHandler(console_handler)

        # Handler de archivo (opcional)
        try:
            from logging.handlers import RotatingFileHandler

            log_file = self.paths.logs / f"sacyty_{self.cedis.code}.log"
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=self.logging.max_bytes,
                backupCount=self.logging.backup_count
            )
            file_handler.setFormatter(formatter)
            file_handler.setLevel(log_level)
            root_logger.addHandler(file_handler)
        except Exception as e:
            logging.warning(f"No se pudo configurar log en archivo: {e}")

    def validate(self) -> Tuple[bool, List[str]]:
        """
        Validar configuración completa.

        Returns:
            Tuple[bool, List[str]]: (es_valida, lista_de_errores)
        """
        errors = []

        # Validar base de datos
        if not self.database.is_configured():
            errors.append("Credenciales de base de datos no configuradas (DB_USER, DB_PASSWORD)")

        if not self.database.host:
            errors.append("Host de base de datos no especificado (DB_HOST)")

        # Validar CEDIS
        if not self.cedis.code:
            errors.append("Código de CEDIS no especificado (CEDIS_CODE)")

        # Validar rutas
        if not self.paths.base.exists():
            errors.append(f"Ruta base no existe: {self.paths.base}")

        # Validar email (opcional, solo warning)
        if not self.email.is_configured():
            logging.warning("Email no configurado - notificaciones deshabilitadas")

        return len(errors) == 0, errors

    def to_dict(self) -> Dict[str, Any]:
        """Convertir configuración a diccionario (sin datos sensibles)"""
        return {
            'version': self.version,
            'name': self.name,
            'environment': self.environment,
            'debug': self.debug,
            'database': {
                'host': self.database.host,
                'port': self.database.port,
                'database': self.database.database,
                'schema': self.database.schema,
                'configured': self.database.is_configured()
            },
            'cedis': {
                'code': self.cedis.code,
                'name': self.cedis.name,
                'region': self.cedis.region,
                'warehouse': self.cedis.warehouse
            },
            'email': {
                'host': self.email.host,
                'port': self.email.port,
                'configured': self.email.is_configured()
            },
            'paths': {
                'base': str(self.paths.base),
                'logs': str(self.paths.logs),
                'output': str(self.paths.output)
            }
        }

    def print_status(self) -> None:
        """Imprimir estado de configuración"""
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║         SACYTY - Configuración del Sistema                  ║
╠══════════════════════════════════════════════════════════════╣
║  Version: {self.version:<48} ║
║  CEDIS: {self.cedis.code} - {self.cedis.name:<40} ║
║  Region: {self.cedis.region:<48} ║
╠══════════════════════════════════════════════════════════════╣
║  Base de Datos:                                              ║
║    Host: {self.database.host:<49} ║
║    Puerto: {self.database.port:<47} ║
║    Configurada: {'SI' if self.database.is_configured() else 'NO':<44} ║
╠══════════════════════════════════════════════════════════════╣
║  Email:                                                      ║
║    Servidor: {self.email.host:<45} ║
║    Configurado: {'SI' if self.email.is_configured() else 'NO':<43} ║
╚══════════════════════════════════════════════════════════════╝
""")


# ═══════════════════════════════════════════════════════════════════════════════
# INSTANCIA GLOBAL DE CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════════════════════

# Instancia singleton para uso global
_config_instance: Optional[SACYTYConfig] = None


def get_config() -> SACYTYConfig:
    """Obtener instancia de configuración (singleton)"""
    global _config_instance
    if _config_instance is None:
        _config_instance = SACYTYConfig()
    return _config_instance


def reload_config() -> SACYTYConfig:
    """Recargar configuración"""
    global _config_instance
    _config_instance = SACYTYConfig()
    return _config_instance


# ═══════════════════════════════════════════════════════════════════════════════
# EJECUCIÓN DIRECTA
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    config = get_config()
    config.print_status()

    is_valid, errors = config.validate()
    if not is_valid:
        print("\nErrores de configuración:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("\nConfiguración válida")
