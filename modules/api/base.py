"""
═══════════════════════════════════════════════════════════════
CLIENTE BASE PARA APIs EXTERNAS
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Clase base abstracta que define la interfaz común para todos
los clientes de API en el sistema SAC.

Características:
- Manejo de errores estandarizado
- Retry con backoff exponencial
- Cache configurable
- Logging integrado
- Métricas de uso

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════
"""

import logging
import time
import hashlib
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from functools import wraps

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# ENUMS Y CONSTANTES
# ═══════════════════════════════════════════════════════════════

class APIStatus(Enum):
    """Estado de la API"""
    ACTIVA = "activa"
    INACTIVA = "inactiva"
    ERROR = "error"
    MANTENIMIENTO = "mantenimiento"
    LIMITADA = "limitada"  # Rate limit alcanzado


# ═══════════════════════════════════════════════════════════════
# CLASES DE DATOS
# ═══════════════════════════════════════════════════════════════

@dataclass
class APIError(Exception):
    """Error de API estandarizado"""
    codigo: str
    mensaje: str
    api_nombre: str
    detalles: Optional[Dict] = None
    timestamp: datetime = field(default_factory=datetime.now)
    reintentar: bool = True  # Si se puede reintentar

    def __str__(self):
        return f"[{self.api_nombre}] {self.codigo}: {self.mensaje}"


@dataclass
class APIResponse:
    """Respuesta estandarizada de API"""
    exito: bool
    datos: Any = None
    mensaje: str = ""
    codigo_http: int = 200
    tiempo_respuesta_ms: float = 0.0
    desde_cache: bool = False
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convierte la respuesta a diccionario"""
        return {
            'exito': self.exito,
            'datos': self.datos,
            'mensaje': self.mensaje,
            'codigo_http': self.codigo_http,
            'tiempo_respuesta_ms': self.tiempo_respuesta_ms,
            'desde_cache': self.desde_cache,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata,
        }


@dataclass
class CacheEntry:
    """Entrada de cache"""
    key: str
    value: Any
    created_at: datetime
    expires_at: datetime
    hits: int = 0


@dataclass
class APIMetrics:
    """Métricas de uso de API"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    total_response_time_ms: float = 0.0
    last_request_at: Optional[datetime] = None
    last_error: Optional[str] = None
    last_error_at: Optional[datetime] = None

    @property
    def average_response_time_ms(self) -> float:
        """Tiempo promedio de respuesta"""
        if self.successful_requests == 0:
            return 0.0
        return self.total_response_time_ms / self.successful_requests

    @property
    def success_rate(self) -> float:
        """Tasa de éxito (0-100)"""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100

    @property
    def cache_hit_rate(self) -> float:
        """Tasa de aciertos de cache (0-100)"""
        total = self.cache_hits + self.cache_misses
        if total == 0:
            return 0.0
        return (self.cache_hits / total) * 100


# ═══════════════════════════════════════════════════════════════
# DECORADORES
# ═══════════════════════════════════════════════════════════════

def with_retry(max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 30.0):
    """
    Decorador para reintentos con backoff exponencial.

    Args:
        max_retries: Número máximo de reintentos
        base_delay: Delay base en segundos
        max_delay: Delay máximo en segundos
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except APIError as e:
                    last_exception = e
                    if not e.reintentar or attempt >= max_retries:
                        raise
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    logger.warning(
                        f"⚠️  Reintento {attempt + 1}/{max_retries} para {e.api_nombre} "
                        f"en {delay:.1f}s: {e.mensaje}"
                    )
                    time.sleep(delay)
                except Exception as e:
                    last_exception = e
                    if attempt >= max_retries:
                        raise
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    logger.warning(f"⚠️  Reintento {attempt + 1}/{max_retries} en {delay:.1f}s: {e}")
                    time.sleep(delay)
            raise last_exception
        return wrapper
    return decorator


def with_cache(ttl_seconds: int = 300):
    """
    Decorador para cache de respuestas.

    Args:
        ttl_seconds: Tiempo de vida del cache en segundos
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Generar clave de cache
            cache_key = self._generate_cache_key(func.__name__, args, kwargs)

            # Verificar cache
            cached = self._get_from_cache(cache_key)
            if cached is not None:
                self._metrics.cache_hits += 1
                logger.debug(f"📦 Cache hit para {func.__name__}")
                return cached

            self._metrics.cache_misses += 1

            # Ejecutar función
            result = func(self, *args, **kwargs)

            # Guardar en cache
            self._set_cache(cache_key, result, ttl_seconds)

            return result
        return wrapper
    return decorator


# ═══════════════════════════════════════════════════════════════
# CLASE BASE API CLIENT
# ═══════════════════════════════════════════════════════════════

class BaseAPIClient(ABC):
    """
    Clase base abstracta para clientes de API.

    Proporciona funcionalidad común:
    - Gestión de cache
    - Métricas de uso
    - Manejo de errores
    - Logging
    """

    # Información de la API (sobrescribir en subclases)
    API_NAME: str = "BaseAPI"
    API_VERSION: str = "1.0"
    API_DESCRIPTION: str = "API base abstracta"

    def __init__(
        self,
        cache_enabled: bool = True,
        cache_ttl_seconds: int = 300,
        timeout_seconds: int = 30,
        max_retries: int = 3,
    ):
        """
        Inicializa el cliente de API.

        Args:
            cache_enabled: Habilitar cache
            cache_ttl_seconds: TTL del cache
            timeout_seconds: Timeout para requests
            max_retries: Máximo de reintentos
        """
        self._cache_enabled = cache_enabled
        self._cache_ttl = cache_ttl_seconds
        self._timeout = timeout_seconds
        self._max_retries = max_retries
        self._cache: Dict[str, CacheEntry] = {}
        self._metrics = APIMetrics()
        self._status = APIStatus.ACTIVA
        self._initialized_at = datetime.now()

        logger.info(f"✅ {self.API_NAME} v{self.API_VERSION} inicializado")

    # ═══════════════════════════════════════════════════════════════
    # MÉTODOS ABSTRACTOS (Implementar en subclases)
    # ═══════════════════════════════════════════════════════════════

    @abstractmethod
    def health_check(self) -> bool:
        """
        Verifica si la API está disponible.

        Returns:
            bool: True si la API responde correctamente
        """
        pass

    @abstractmethod
    def get_info(self) -> Dict:
        """
        Obtiene información sobre la API.

        Returns:
            Dict: Información de la API
        """
        pass

    # ═══════════════════════════════════════════════════════════════
    # MÉTODOS DE CACHE
    # ═══════════════════════════════════════════════════════════════

    def _generate_cache_key(self, method: str, args: tuple, kwargs: dict) -> str:
        """Genera clave única para cache"""
        key_data = {
            'method': method,
            'args': str(args),
            'kwargs': str(sorted(kwargs.items())),
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()

    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Obtiene valor del cache si existe y no ha expirado"""
        if not self._cache_enabled:
            return None

        entry = self._cache.get(key)
        if entry is None:
            return None

        if datetime.now() > entry.expires_at:
            del self._cache[key]
            return None

        entry.hits += 1
        return entry.value

    def _set_cache(self, key: str, value: Any, ttl_seconds: Optional[int] = None):
        """Guarda valor en cache"""
        if not self._cache_enabled:
            return

        ttl = ttl_seconds or self._cache_ttl
        self._cache[key] = CacheEntry(
            key=key,
            value=value,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(seconds=ttl),
        )

    def clear_cache(self):
        """Limpia todo el cache"""
        self._cache.clear()
        logger.info(f"🗑️  Cache limpiado para {self.API_NAME}")

    def get_cache_stats(self) -> Dict:
        """Obtiene estadísticas del cache"""
        now = datetime.now()
        entries = list(self._cache.values())
        active = [e for e in entries if e.expires_at > now]

        return {
            'total_entries': len(entries),
            'active_entries': len(active),
            'expired_entries': len(entries) - len(active),
            'total_hits': sum(e.hits for e in entries),
        }

    # ═══════════════════════════════════════════════════════════════
    # MÉTODOS DE MÉTRICAS
    # ═══════════════════════════════════════════════════════════════

    def get_metrics(self) -> Dict:
        """Obtiene métricas de uso de la API"""
        return {
            'api_name': self.API_NAME,
            'api_version': self.API_VERSION,
            'status': self._status.value,
            'total_requests': self._metrics.total_requests,
            'successful_requests': self._metrics.successful_requests,
            'failed_requests': self._metrics.failed_requests,
            'success_rate': f"{self._metrics.success_rate:.1f}%",
            'average_response_time_ms': f"{self._metrics.average_response_time_ms:.2f}",
            'cache_hit_rate': f"{self._metrics.cache_hit_rate:.1f}%",
            'last_request_at': self._metrics.last_request_at.isoformat() if self._metrics.last_request_at else None,
            'last_error': self._metrics.last_error,
            'initialized_at': self._initialized_at.isoformat(),
            'uptime_minutes': (datetime.now() - self._initialized_at).total_seconds() / 60,
        }

    def _record_request(self, success: bool, response_time_ms: float, error: Optional[str] = None):
        """Registra una request en las métricas"""
        self._metrics.total_requests += 1
        self._metrics.last_request_at = datetime.now()

        if success:
            self._metrics.successful_requests += 1
            self._metrics.total_response_time_ms += response_time_ms
        else:
            self._metrics.failed_requests += 1
            self._metrics.last_error = error
            self._metrics.last_error_at = datetime.now()

    # ═══════════════════════════════════════════════════════════════
    # MÉTODOS DE UTILIDAD
    # ═══════════════════════════════════════════════════════════════

    def get_status(self) -> APIStatus:
        """Obtiene el estado actual de la API"""
        return self._status

    def set_status(self, status: APIStatus):
        """Establece el estado de la API"""
        old_status = self._status
        self._status = status
        if old_status != status:
            logger.info(f"📊 {self.API_NAME} cambió estado: {old_status.value} -> {status.value}")

    def is_available(self) -> bool:
        """Verifica si la API está disponible para uso"""
        return self._status in (APIStatus.ACTIVA, APIStatus.LIMITADA)

    def __repr__(self) -> str:
        return f"<{self.API_NAME} v{self.API_VERSION} [{self._status.value}]>"

    def __str__(self) -> str:
        return f"{self.API_NAME} v{self.API_VERSION}"
