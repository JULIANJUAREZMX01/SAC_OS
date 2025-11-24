"""
═══════════════════════════════════════════════════════════════
API DE CLIMA PARA LOGÍSTICA
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Proporciona información meteorológica para planificación logística:
- Pronóstico actual y extendido
- Alertas de condiciones adversas
- Impacto en operaciones

Fuente:
- Open-Meteo API (gratuita, sin API key)

Útil para:
- Planificación de rutas de distribución
- Alertas de huracanes/tormentas
- Decisiones de carga/descarga

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════
"""

import logging
import urllib.request
import urllib.error
import json
from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum
from typing import Dict, List, Optional, Tuple

from ..base import BaseAPIClient, APIResponse, APIError, APIStatus, with_retry

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# CONSTANTES
# ═══════════════════════════════════════════════════════════════

OPEN_METEO_BASE_URL = "https://api.open-meteo.com/v1"

# Códigos de condición climática WMO
WMO_CODES = {
    0: ("Despejado", "☀️"),
    1: ("Mayormente despejado", "🌤️"),
    2: ("Parcialmente nublado", "⛅"),
    3: ("Nublado", "☁️"),
    45: ("Neblina", "🌫️"),
    48: ("Neblina con escarcha", "🌫️"),
    51: ("Llovizna ligera", "🌦️"),
    53: ("Llovizna moderada", "🌦️"),
    55: ("Llovizna intensa", "🌧️"),
    61: ("Lluvia ligera", "🌧️"),
    63: ("Lluvia moderada", "🌧️"),
    65: ("Lluvia intensa", "🌧️"),
    71: ("Nevada ligera", "🌨️"),
    73: ("Nevada moderada", "🌨️"),
    75: ("Nevada intensa", "🌨️"),
    77: ("Granizo", "🌨️"),
    80: ("Chubascos ligeros", "🌧️"),
    81: ("Chubascos moderados", "🌧️"),
    82: ("Chubascos intensos", "⛈️"),
    85: ("Nevada con chubascos ligeros", "🌨️"),
    86: ("Nevada con chubascos intensos", "🌨️"),
    95: ("Tormenta eléctrica", "⛈️"),
    96: ("Tormenta con granizo ligero", "⛈️"),
    99: ("Tormenta con granizo intenso", "⛈️"),
}

# Ubicaciones predefinidas
UBICACIONES_CEDIS = {
    'cancun': {'nombre': 'CEDIS Cancún', 'latitud': 21.1619, 'longitud': -86.8515},
    'villahermosa': {'nombre': 'Villahermosa', 'latitud': 17.9892, 'longitud': -92.9475},
    'merida': {'nombre': 'Mérida', 'latitud': 20.9674, 'longitud': -89.5926},
    'chetumal': {'nombre': 'Chetumal', 'latitud': 18.5001, 'longitud': -88.2961},
    'playa_carmen': {'nombre': 'Playa del Carmen', 'latitud': 20.6296, 'longitud': -87.0739},
}


# ═══════════════════════════════════════════════════════════════
# ENUMS
# ═══════════════════════════════════════════════════════════════

class CondicionClima(Enum):
    """Condición general del clima"""
    OPTIMO = "óptimo"
    BUENO = "bueno"
    ACEPTABLE = "aceptable"
    PRECAUCION = "precaución"
    ADVERSO = "adverso"
    CRITICO = "crítico"


class ImpactoLogistico(Enum):
    """Impacto en operaciones logísticas"""
    NINGUNO = "ninguno"
    BAJO = "bajo"
    MODERADO = "moderado"
    ALTO = "alto"
    SEVERO = "severo"


# ═══════════════════════════════════════════════════════════════
# CLASES DE DATOS
# ═══════════════════════════════════════════════════════════════

@dataclass
class PronosticoClima:
    """Pronóstico del clima para una ubicación"""
    ubicacion: str
    latitud: float
    longitud: float
    fecha: date
    hora: Optional[int] = None  # None = promedio del día

    # Temperatura
    temperatura: float = 0.0
    temperatura_min: Optional[float] = None
    temperatura_max: Optional[float] = None
    sensacion_termica: Optional[float] = None

    # Condiciones
    codigo_wmo: int = 0
    condicion: str = ""
    emoji: str = ""

    # Precipitación
    probabilidad_lluvia: float = 0.0
    precipitacion_mm: float = 0.0

    # Viento
    velocidad_viento: float = 0.0
    direccion_viento: int = 0
    rafagas: Optional[float] = None

    # Humedad y otros
    humedad: float = 0.0
    presion: Optional[float] = None
    visibilidad: Optional[float] = None
    indice_uv: Optional[float] = None

    # Evaluación logística
    condicion_general: CondicionClima = CondicionClima.BUENO
    impacto_logistico: ImpactoLogistico = ImpactoLogistico.NINGUNO
    alertas: List[str] = field(default_factory=list)

    timestamp: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        # Obtener descripción del código WMO
        if self.codigo_wmo in WMO_CODES:
            self.condicion, self.emoji = WMO_CODES[self.codigo_wmo]
        else:
            self.condicion = "Desconocido"
            self.emoji = "❓"

        # Evaluar condición general
        self._evaluar_condicion()

    def _evaluar_condicion(self):
        """Evalúa la condición general y el impacto logístico"""
        alertas = []

        # Evaluar temperatura
        if self.temperatura > 40:
            alertas.append("🌡️ Temperatura extremadamente alta")
            self.condicion_general = CondicionClima.ADVERSO
        elif self.temperatura > 35:
            alertas.append("🌡️ Temperatura muy alta")

        # Evaluar lluvia
        if self.probabilidad_lluvia > 80:
            alertas.append("🌧️ Alta probabilidad de lluvia")
            self.impacto_logistico = ImpactoLogistico.ALTO
        elif self.probabilidad_lluvia > 60:
            alertas.append("🌦️ Probable lluvia")
            self.impacto_logistico = ImpactoLogistico.MODERADO

        # Evaluar viento
        if self.velocidad_viento > 80:
            alertas.append("💨 Vientos peligrosos")
            self.condicion_general = CondicionClima.CRITICO
            self.impacto_logistico = ImpactoLogistico.SEVERO
        elif self.velocidad_viento > 60:
            alertas.append("💨 Vientos fuertes")
            self.impacto_logistico = ImpactoLogistico.ALTO
        elif self.velocidad_viento > 40:
            alertas.append("💨 Vientos moderados")

        # Evaluar condiciones de tormenta
        if self.codigo_wmo >= 95:
            alertas.append("⛈️ Tormenta eléctrica")
            self.condicion_general = CondicionClima.ADVERSO
            self.impacto_logistico = ImpactoLogistico.ALTO

        self.alertas = alertas

        # Determinar condición general si no se estableció
        if self.condicion_general == CondicionClima.BUENO:
            if len(alertas) == 0:
                self.condicion_general = CondicionClima.OPTIMO
            elif len(alertas) == 1:
                self.condicion_general = CondicionClima.ACEPTABLE
            else:
                self.condicion_general = CondicionClima.PRECAUCION

    def to_dict(self) -> Dict:
        return {
            'ubicacion': self.ubicacion,
            'latitud': self.latitud,
            'longitud': self.longitud,
            'fecha': self.fecha.isoformat(),
            'hora': self.hora,
            'temperatura': self.temperatura,
            'temperatura_min': self.temperatura_min,
            'temperatura_max': self.temperatura_max,
            'sensacion_termica': self.sensacion_termica,
            'condicion': self.condicion,
            'emoji': self.emoji,
            'probabilidad_lluvia': self.probabilidad_lluvia,
            'precipitacion_mm': self.precipitacion_mm,
            'velocidad_viento': self.velocidad_viento,
            'humedad': self.humedad,
            'condicion_general': self.condicion_general.value,
            'impacto_logistico': self.impacto_logistico.value,
            'alertas': self.alertas,
            'timestamp': self.timestamp.isoformat(),
        }

    def __str__(self) -> str:
        return (
            f"{self.emoji} {self.ubicacion}: {self.temperatura:.1f}°C, "
            f"{self.condicion}, 💧{self.probabilidad_lluvia:.0f}%"
        )


# ═══════════════════════════════════════════════════════════════
# CLASE PRINCIPAL
# ═══════════════════════════════════════════════════════════════

class WeatherAPI(BaseAPIClient):
    """
    API de Clima para Logística.

    Proporciona pronósticos y alertas meteorológicas
    para planificación de operaciones.
    """

    API_NAME = "WeatherAPI"
    API_VERSION = "1.0"
    API_DESCRIPTION = "Pronóstico del clima para planificación logística"

    def __init__(
        self,
        ubicacion_default: Optional[Dict] = None,
        timeout_seconds: int = 15,
        **kwargs
    ):
        """
        Inicializa la API de clima.

        Args:
            ubicacion_default: Ubicación por defecto
            timeout_seconds: Timeout para requests
        """
        super().__init__(
            cache_ttl_seconds=1800,  # Cache 30 minutos
            timeout_seconds=timeout_seconds,
            **kwargs
        )
        self._ubicacion_default = ubicacion_default or UBICACIONES_CEDIS['cancun']

    def _hacer_request(self, url: str) -> Dict:
        """Realiza request HTTP GET"""
        try:
            req = urllib.request.Request(
                url,
                headers={'User-Agent': 'SAC-CEDIS/1.0'}
            )
            with urllib.request.urlopen(req, timeout=self._timeout) as response:
                return json.loads(response.read().decode())
        except urllib.error.URLError as e:
            logger.error(f"❌ Error de conexión: {e}")
            raise APIError(
                codigo="CONNECTION_ERROR",
                mensaje=f"Error conectando a API de clima: {e}",
                api_nombre=self.API_NAME,
            )
        except json.JSONDecodeError as e:
            logger.error(f"❌ Error parseando JSON: {e}")
            raise APIError(
                codigo="PARSE_ERROR",
                mensaje="Respuesta inválida de API de clima",
                api_nombre=self.API_NAME,
            )

    @with_retry(max_retries=2)
    def _obtener_pronostico_raw(
        self,
        latitud: float,
        longitud: float,
        dias: int = 7
    ) -> Dict:
        """
        Obtiene datos raw de Open-Meteo.

        Args:
            latitud: Latitud
            longitud: Longitud
            dias: Días de pronóstico

        Returns:
            Dict con datos de la API
        """
        import time
        start_time = time.time()

        url = (
            f"{OPEN_METEO_BASE_URL}/forecast?"
            f"latitude={latitud}&longitude={longitud}"
            f"&current=temperature_2m,relative_humidity_2m,weather_code,"
            f"wind_speed_10m,wind_direction_10m"
            f"&daily=weather_code,temperature_2m_max,temperature_2m_min,"
            f"precipitation_sum,precipitation_probability_max,"
            f"wind_speed_10m_max,wind_gusts_10m_max"
            f"&timezone=America/Cancun"
            f"&forecast_days={dias}"
        )

        try:
            data = self._hacer_request(url)
            response_time = (time.time() - start_time) * 1000
            self._record_request(True, response_time)
            return data
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self._record_request(False, response_time, str(e))
            raise

    # ═══════════════════════════════════════════════════════════
    # MÉTODOS PRINCIPALES
    # ═══════════════════════════════════════════════════════════

    def obtener_clima_actual(
        self,
        ubicacion: Optional[str] = None,
        latitud: Optional[float] = None,
        longitud: Optional[float] = None
    ) -> PronosticoClima:
        """
        Obtiene el clima actual.

        Args:
            ubicacion: Nombre de ubicación predefinida
            latitud: Latitud (si no se usa ubicación)
            longitud: Longitud (si no se usa ubicación)

        Returns:
            PronosticoClima actual
        """
        # Resolver ubicación
        if ubicacion:
            ubicacion = ubicacion.lower().replace(' ', '_')
            if ubicacion in UBICACIONES_CEDIS:
                ubi = UBICACIONES_CEDIS[ubicacion]
                nombre = ubi['nombre']
                latitud = ubi['latitud']
                longitud = ubi['longitud']
            else:
                raise APIError(
                    codigo="INVALID_LOCATION",
                    mensaje=f"Ubicación '{ubicacion}' no reconocida",
                    api_nombre=self.API_NAME,
                )
        elif latitud is None or longitud is None:
            ubi = self._ubicacion_default
            nombre = ubi['nombre']
            latitud = ubi['latitud']
            longitud = ubi['longitud']
        else:
            nombre = f"Lat:{latitud:.2f}, Lon:{longitud:.2f}"

        # Verificar cache
        cache_key = f"actual_{latitud}_{longitud}"
        cached = self._get_from_cache(cache_key)
        if cached:
            self._metrics.cache_hits += 1
            return cached

        self._metrics.cache_misses += 1

        # Obtener datos
        data = self._obtener_pronostico_raw(latitud, longitud, dias=1)
        current = data.get('current', {})

        pronostico = PronosticoClima(
            ubicacion=nombre,
            latitud=latitud,
            longitud=longitud,
            fecha=date.today(),
            temperatura=current.get('temperature_2m', 0),
            codigo_wmo=current.get('weather_code', 0),
            velocidad_viento=current.get('wind_speed_10m', 0),
            direccion_viento=current.get('wind_direction_10m', 0),
            humedad=current.get('relative_humidity_2m', 0),
        )

        self._set_cache(cache_key, pronostico)
        return pronostico

    def obtener_pronostico_diario(
        self,
        ubicacion: Optional[str] = None,
        dias: int = 7,
        latitud: Optional[float] = None,
        longitud: Optional[float] = None
    ) -> List[PronosticoClima]:
        """
        Obtiene pronóstico extendido por días.

        Args:
            ubicacion: Nombre de ubicación
            dias: Días de pronóstico (1-16)
            latitud: Latitud opcional
            longitud: Longitud opcional

        Returns:
            Lista de PronosticoClima
        """
        # Resolver ubicación
        if ubicacion:
            ubicacion = ubicacion.lower().replace(' ', '_')
            if ubicacion in UBICACIONES_CEDIS:
                ubi = UBICACIONES_CEDIS[ubicacion]
                nombre = ubi['nombre']
                latitud = ubi['latitud']
                longitud = ubi['longitud']
            else:
                raise APIError(
                    codigo="INVALID_LOCATION",
                    mensaje=f"Ubicación '{ubicacion}' no reconocida",
                    api_nombre=self.API_NAME,
                )
        elif latitud is None or longitud is None:
            ubi = self._ubicacion_default
            nombre = ubi['nombre']
            latitud = ubi['latitud']
            longitud = ubi['longitud']
        else:
            nombre = f"Lat:{latitud:.2f}, Lon:{longitud:.2f}"

        dias = min(max(dias, 1), 16)

        # Obtener datos
        data = self._obtener_pronostico_raw(latitud, longitud, dias)
        daily = data.get('daily', {})

        pronosticos = []
        fechas = daily.get('time', [])

        for i, fecha_str in enumerate(fechas):
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()

            pronostico = PronosticoClima(
                ubicacion=nombre,
                latitud=latitud,
                longitud=longitud,
                fecha=fecha,
                temperatura=(
                    (daily.get('temperature_2m_max', [0])[i] +
                     daily.get('temperature_2m_min', [0])[i]) / 2
                ),
                temperatura_min=daily.get('temperature_2m_min', [None])[i],
                temperatura_max=daily.get('temperature_2m_max', [None])[i],
                codigo_wmo=daily.get('weather_code', [0])[i],
                probabilidad_lluvia=daily.get('precipitation_probability_max', [0])[i] or 0,
                precipitacion_mm=daily.get('precipitation_sum', [0])[i] or 0,
                velocidad_viento=daily.get('wind_speed_10m_max', [0])[i] or 0,
                rafagas=daily.get('wind_gusts_10m_max', [None])[i],
            )
            pronosticos.append(pronostico)

        return pronosticos

    def obtener_clima_cedis(self) -> Dict[str, PronosticoClima]:
        """
        Obtiene el clima de todas las ubicaciones CEDIS.

        Returns:
            Dict con ubicacion -> PronosticoClima
        """
        resultados = {}

        for key in UBICACIONES_CEDIS.keys():
            try:
                resultados[key] = self.obtener_clima_actual(key)
            except APIError as e:
                logger.warning(f"⚠️  Error obteniendo clima de {key}: {e}")

        return resultados

    def hay_condiciones_adversas(
        self,
        ubicacion: Optional[str] = None
    ) -> Tuple[bool, List[str]]:
        """
        Verifica si hay condiciones adversas.

        Args:
            ubicacion: Ubicación a verificar

        Returns:
            Tuple (hay_adversas, lista_alertas)
        """
        pronostico = self.obtener_clima_actual(ubicacion)

        adverso = pronostico.condicion_general in (
            CondicionClima.ADVERSO,
            CondicionClima.CRITICO
        )

        return adverso, pronostico.alertas

    def obtener_resumen_regional(self) -> Dict:
        """
        Obtiene un resumen del clima en la región.

        Returns:
            Dict con resumen regional
        """
        climas = self.obtener_clima_cedis()

        alertas_regionales = []
        for ubi, clima in climas.items():
            if clima.alertas:
                alertas_regionales.extend([
                    f"{clima.ubicacion}: {alerta}"
                    for alerta in clima.alertas
                ])

        return {
            'fecha': date.today().isoformat(),
            'ubicaciones': {k: v.to_dict() for k, v in climas.items()},
            'total_ubicaciones': len(climas),
            'alertas_regionales': alertas_regionales,
            'hay_condiciones_adversas': any(
                c.condicion_general in (CondicionClima.ADVERSO, CondicionClima.CRITICO)
                for c in climas.values()
            ),
        }

    # ═══════════════════════════════════════════════════════════
    # MÉTODOS DE BaseAPIClient
    # ═══════════════════════════════════════════════════════════

    def health_check(self) -> bool:
        """Verifica que la API funcione"""
        try:
            clima = self.obtener_clima_actual()
            return clima is not None
        except Exception as e:
            logger.error(f"❌ Health check falló: {e}")
            return False

    def get_info(self) -> Dict:
        """Obtiene información de la API"""
        return {
            'nombre': self.API_NAME,
            'version': self.API_VERSION,
            'descripcion': self.API_DESCRIPTION,
            'fuente': 'Open-Meteo (gratuita)',
            'ubicacion_default': self._ubicacion_default['nombre'],
            'ubicaciones_disponibles': list(UBICACIONES_CEDIS.keys()),
            'max_dias_pronostico': 16,
        }
