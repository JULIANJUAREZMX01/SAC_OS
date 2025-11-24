"""
═══════════════════════════════════════════════════════════════
REGISTRO DE APIs EXTERNAS
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Gestiona el registro, inicialización y acceso a todas las APIs
del sistema. Patrón Singleton para acceso global.

Uso:
    from modules.api import api_registry, get_api

    # Obtener API
    calendar = get_api('calendar')

    # Listar APIs
    apis = api_registry.list_apis()

    # Estado global
    status = api_registry.get_status()

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Type
from .base import BaseAPIClient, APIStatus

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# CLASE REGISTRY
# ═══════════════════════════════════════════════════════════════

class APIRegistry:
    """
    Registro central de APIs.

    Gestiona:
    - Registro de APIs disponibles
    - Inicialización lazy de instancias
    - Estado global de APIs
    - Health checks
    """

    _instance: Optional['APIRegistry'] = None
    _initialized: bool = False

    def __new__(cls):
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Inicializa el registry (solo una vez)"""
        if self._initialized:
            return

        self._apis: Dict[str, BaseAPIClient] = {}
        self._api_classes: Dict[str, Type[BaseAPIClient]] = {}
        self._created_at = datetime.now()
        self._initialized = True

        logger.info("📚 API Registry inicializado")

    def register(
        self,
        name: str,
        api_class: Type[BaseAPIClient],
        auto_init: bool = True,
        **init_kwargs
    ) -> Optional[BaseAPIClient]:
        """
        Registra una nueva API.

        Args:
            name: Nombre único de la API
            api_class: Clase del cliente API
            auto_init: Inicializar inmediatamente
            **init_kwargs: Argumentos para inicialización

        Returns:
            Instancia de la API si auto_init=True
        """
        name = name.lower()

        if name in self._api_classes:
            logger.warning(f"⚠️  API '{name}' ya registrada, actualizando...")

        self._api_classes[name] = api_class

        if auto_init:
            try:
                instance = api_class(**init_kwargs)
                self._apis[name] = instance
                logger.info(f"✅ API '{name}' registrada e inicializada")
                return instance
            except Exception as e:
                logger.error(f"❌ Error inicializando API '{name}': {e}")
                return None
        else:
            logger.info(f"📝 API '{name}' registrada (inicialización diferida)")
            return None

    def get(self, name: str, **init_kwargs) -> Optional[BaseAPIClient]:
        """
        Obtiene una API por nombre.

        Args:
            name: Nombre de la API
            **init_kwargs: Argumentos si necesita inicialización

        Returns:
            Instancia de la API o None
        """
        name = name.lower()

        # Si ya existe instancia, retornarla
        if name in self._apis:
            return self._apis[name]

        # Si existe clase pero no instancia, inicializar
        if name in self._api_classes:
            try:
                instance = self._api_classes[name](**init_kwargs)
                self._apis[name] = instance
                logger.info(f"✅ API '{name}' inicializada bajo demanda")
                return instance
            except Exception as e:
                logger.error(f"❌ Error inicializando API '{name}': {e}")
                return None

        logger.warning(f"⚠️  API '{name}' no encontrada")
        return None

    def unregister(self, name: str) -> bool:
        """
        Elimina una API del registro.

        Args:
            name: Nombre de la API

        Returns:
            True si se eliminó correctamente
        """
        name = name.lower()
        removed = False

        if name in self._apis:
            del self._apis[name]
            removed = True

        if name in self._api_classes:
            del self._api_classes[name]
            removed = True

        if removed:
            logger.info(f"🗑️  API '{name}' eliminada del registro")

        return removed

    def list_apis(self) -> List[Dict]:
        """
        Lista todas las APIs registradas.

        Returns:
            Lista de información de cada API
        """
        result = []

        for name, api_class in self._api_classes.items():
            instance = self._apis.get(name)

            info = {
                'nombre': name,
                'clase': api_class.__name__,
                'inicializada': instance is not None,
                'estado': instance.get_status().value if instance else 'no_inicializada',
                'descripcion': getattr(api_class, 'API_DESCRIPTION', 'Sin descripción'),
                'version': getattr(api_class, 'API_VERSION', '1.0'),
            }

            if instance:
                info['metricas'] = instance.get_metrics()

            result.append(info)

        return result

    def get_status(self) -> Dict:
        """
        Obtiene el estado global del registry.

        Returns:
            Estado de todas las APIs
        """
        total = len(self._api_classes)
        initialized = len(self._apis)
        active = sum(1 for api in self._apis.values() if api.is_available())

        return {
            'total_registradas': total,
            'total_inicializadas': initialized,
            'total_activas': active,
            'created_at': self._created_at.isoformat(),
            'uptime_minutes': (datetime.now() - self._created_at).total_seconds() / 60,
            'apis': {
                name: {
                    'estado': api.get_status().value,
                    'disponible': api.is_available(),
                }
                for name, api in self._apis.items()
            }
        }

    def health_check_all(self) -> Dict[str, bool]:
        """
        Ejecuta health check en todas las APIs inicializadas.

        Returns:
            Dict con nombre -> resultado health check
        """
        results = {}

        for name, api in self._apis.items():
            try:
                results[name] = api.health_check()
                if results[name]:
                    api.set_status(APIStatus.ACTIVA)
                else:
                    api.set_status(APIStatus.ERROR)
            except Exception as e:
                logger.error(f"❌ Health check falló para '{name}': {e}")
                results[name] = False
                api.set_status(APIStatus.ERROR)

        return results

    def get_all_metrics(self) -> Dict[str, Dict]:
        """
        Obtiene métricas de todas las APIs.

        Returns:
            Dict con nombre -> métricas
        """
        return {
            name: api.get_metrics()
            for name, api in self._apis.items()
        }

    def __len__(self) -> int:
        return len(self._api_classes)

    def __contains__(self, name: str) -> bool:
        return name.lower() in self._api_classes

    def __iter__(self):
        return iter(self._apis.values())


# ═══════════════════════════════════════════════════════════════
# INSTANCIA GLOBAL Y FUNCIONES DE CONVENIENCIA
# ═══════════════════════════════════════════════════════════════

# Instancia global singleton
api_registry = APIRegistry()


def get_api(name: str, **kwargs) -> Optional[BaseAPIClient]:
    """
    Obtiene una API del registry global.

    Args:
        name: Nombre de la API
        **kwargs: Argumentos de inicialización

    Returns:
        Instancia de la API
    """
    return api_registry.get(name, **kwargs)


def list_apis() -> List[Dict]:
    """
    Lista todas las APIs disponibles.

    Returns:
        Lista de información de APIs
    """
    return api_registry.list_apis()


def get_api_status() -> Dict:
    """
    Obtiene el estado global de APIs.

    Returns:
        Estado del registry
    """
    return api_registry.get_status()


# ═══════════════════════════════════════════════════════════════
# INICIALIZACIÓN DE APIS AL IMPORTAR
# ═══════════════════════════════════════════════════════════════

def _initialize_default_apis():
    """
    Inicializa las APIs predeterminadas.
    Llamado automáticamente al importar el módulo.
    """
    try:
        # Importar proveedores disponibles
        from .providers.calendar import CalendarAPI
        from .providers.exchange_rate import ExchangeRateAPI
        from .providers.weather import WeatherAPI

        # Registrar APIs activas
        api_registry.register('calendar', CalendarAPI, auto_init=True)
        api_registry.register('exchange_rate', ExchangeRateAPI, auto_init=True)
        api_registry.register('weather', WeatherAPI, auto_init=True)

        logger.info(f"✅ {len(api_registry)} APIs inicializadas correctamente")

    except ImportError as e:
        logger.warning(f"⚠️  Algunas APIs no pudieron cargarse: {e}")
    except Exception as e:
        logger.error(f"❌ Error inicializando APIs: {e}")


# Auto-inicializar al importar
_initialize_default_apis()
