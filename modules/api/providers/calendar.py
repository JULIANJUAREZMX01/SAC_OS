"""
═══════════════════════════════════════════════════════════════
API DE CALENDARIO MEXICANO
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Proporciona información sobre el calendario mexicano:
- Días festivos oficiales (Ley Federal del Trabajo)
- Días inhábiles bancarios
- Fines de semana
- Cálculo de días hábiles

Útil para:
- Planificación de recepciones
- Cálculo de fechas límite
- Programación de entregas

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════
"""

import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple, Union

from ..base import BaseAPIClient, APIResponse, APIError, with_cache

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# ENUMS Y CONSTANTES
# ═══════════════════════════════════════════════════════════════

class TipoDia(Enum):
    """Tipo de día en el calendario"""
    HABIL = "hábil"
    FIN_SEMANA = "fin_semana"
    FESTIVO = "festivo"
    FESTIVO_PUENTE = "festivo_puente"  # Lunes o viernes puente
    INHABIL_BANCARIO = "inhábil_bancario"


# Días festivos oficiales de México (Ley Federal del Trabajo)
# Formato: (mes, dia, nombre, es_movible)
DIAS_FESTIVOS_FIJOS = [
    (1, 1, "Año Nuevo", False),
    (2, 5, "Día de la Constitución", True),  # Primer lunes de febrero
    (3, 21, "Natalicio de Benito Juárez", True),  # Tercer lunes de marzo
    (5, 1, "Día del Trabajo", False),
    (9, 16, "Día de la Independencia", False),
    (11, 20, "Día de la Revolución", True),  # Tercer lunes de noviembre
    (12, 25, "Navidad", False),
]

# Días inhábiles bancarios adicionales
DIAS_INHABILES_BANCARIOS = [
    (1, 6, "Día de Reyes (bancario)"),
    (3, 18, "Viernes Santo (variable)"),  # Se calcula por Pascua
    (3, 19, "Jueves Santo (variable)"),  # Se calcula por Pascua
    (11, 2, "Día de Muertos"),
    (12, 12, "Día de la Virgen de Guadalupe"),
    (12, 31, "Fin de Año (bancario)"),
]


# ═══════════════════════════════════════════════════════════════
# CLASES DE DATOS
# ═══════════════════════════════════════════════════════════════

@dataclass
class DiaMexicano:
    """Información de un día en el calendario mexicano"""
    fecha: date
    tipo: TipoDia
    es_habil: bool
    es_festivo: bool
    nombre_festivo: Optional[str] = None
    dia_semana: str = ""
    semana_del_anio: int = 0

    def __post_init__(self):
        dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        self.dia_semana = dias_semana[self.fecha.weekday()]
        self.semana_del_anio = self.fecha.isocalendar()[1]

    def to_dict(self) -> Dict:
        return {
            'fecha': self.fecha.isoformat(),
            'tipo': self.tipo.value,
            'es_habil': self.es_habil,
            'es_festivo': self.es_festivo,
            'nombre_festivo': self.nombre_festivo,
            'dia_semana': self.dia_semana,
            'semana_del_anio': self.semana_del_anio,
        }


# ═══════════════════════════════════════════════════════════════
# FUNCIONES DE CÁLCULO DE FECHAS
# ═══════════════════════════════════════════════════════════════

def _calcular_pascua(anio: int) -> date:
    """
    Calcula la fecha de Pascua usando el algoritmo de Gauss.

    Args:
        anio: Año a calcular

    Returns:
        Fecha de Domingo de Pascua
    """
    a = anio % 19
    b = anio // 100
    c = anio % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    mes = (h + l - 7 * m + 114) // 31
    dia = ((h + l - 7 * m + 114) % 31) + 1
    return date(anio, mes, dia)


def _calcular_n_lunes(anio: int, mes: int, n: int) -> date:
    """
    Calcula el n-ésimo lunes de un mes.

    Args:
        anio: Año
        mes: Mes
        n: Número de lunes (1 = primero, 3 = tercero)

    Returns:
        Fecha del n-ésimo lunes
    """
    primer_dia = date(anio, mes, 1)
    dias_hasta_lunes = (7 - primer_dia.weekday()) % 7
    primer_lunes = primer_dia + timedelta(days=dias_hasta_lunes)
    return primer_lunes + timedelta(weeks=n - 1)


def _obtener_festivos_anio(anio: int) -> Dict[date, str]:
    """
    Obtiene todos los días festivos de un año.

    Args:
        anio: Año a consultar

    Returns:
        Dict con fecha -> nombre del festivo
    """
    festivos = {}

    # Festivos fijos y movibles
    for mes, dia, nombre, es_movible in DIAS_FESTIVOS_FIJOS:
        if es_movible:
            # Días movibles al lunes más cercano
            if mes == 2 and dia == 5:  # Constitución - primer lunes febrero
                fecha = _calcular_n_lunes(anio, 2, 1)
            elif mes == 3 and dia == 21:  # Juárez - tercer lunes marzo
                fecha = _calcular_n_lunes(anio, 3, 3)
            elif mes == 11 and dia == 20:  # Revolución - tercer lunes noviembre
                fecha = _calcular_n_lunes(anio, 11, 3)
            else:
                fecha = date(anio, mes, dia)
        else:
            fecha = date(anio, mes, dia)

        festivos[fecha] = nombre

    # Semana Santa (basada en Pascua)
    pascua = _calcular_pascua(anio)
    jueves_santo = pascua - timedelta(days=3)
    viernes_santo = pascua - timedelta(days=2)
    festivos[jueves_santo] = "Jueves Santo"
    festivos[viernes_santo] = "Viernes Santo"

    return festivos


# ═══════════════════════════════════════════════════════════════
# CLASE PRINCIPAL
# ═══════════════════════════════════════════════════════════════

class CalendarAPI(BaseAPIClient):
    """
    API de Calendario Mexicano.

    Proporciona información sobre días hábiles, festivos y fines de semana
    para planificación de operaciones logísticas.
    """

    API_NAME = "CalendarAPI"
    API_VERSION = "1.0"
    API_DESCRIPTION = "Calendario mexicano con días festivos y hábiles"

    def __init__(
        self,
        anio_inicio: int = 2020,
        anio_fin: int = 2030,
        **kwargs
    ):
        """
        Inicializa el calendario.

        Args:
            anio_inicio: Año inicial del rango
            anio_fin: Año final del rango
        """
        super().__init__(cache_ttl_seconds=86400, **kwargs)  # Cache 24h
        self._anio_inicio = anio_inicio
        self._anio_fin = anio_fin
        self._festivos_cache: Dict[int, Dict[date, str]] = {}

        # Pre-cargar festivos para años comunes
        self._precargar_festivos()

    def _precargar_festivos(self):
        """Pre-carga los días festivos para el rango configurado"""
        anio_actual = datetime.now().year
        for anio in range(anio_actual - 1, anio_actual + 3):
            if anio not in self._festivos_cache:
                self._festivos_cache[anio] = _obtener_festivos_anio(anio)

    def _get_festivos_anio(self, anio: int) -> Dict[date, str]:
        """Obtiene festivos de un año (con cache)"""
        if anio not in self._festivos_cache:
            self._festivos_cache[anio] = _obtener_festivos_anio(anio)
        return self._festivos_cache[anio]

    # ═══════════════════════════════════════════════════════════
    # MÉTODOS PRINCIPALES
    # ═══════════════════════════════════════════════════════════

    def obtener_dia(self, fecha: date) -> DiaMexicano:
        """
        Obtiene información completa de un día.

        Args:
            fecha: Fecha a consultar

        Returns:
            DiaMexicano con la información
        """
        festivos = self._get_festivos_anio(fecha.year)

        # Determinar tipo y si es festivo
        es_festivo = fecha in festivos
        nombre_festivo = festivos.get(fecha)
        es_fin_semana = fecha.weekday() >= 5

        if es_festivo:
            tipo = TipoDia.FESTIVO
        elif es_fin_semana:
            tipo = TipoDia.FIN_SEMANA
        else:
            tipo = TipoDia.HABIL

        es_habil = tipo == TipoDia.HABIL

        return DiaMexicano(
            fecha=fecha,
            tipo=tipo,
            es_habil=es_habil,
            es_festivo=es_festivo,
            nombre_festivo=nombre_festivo,
        )

    def es_dia_habil(self, fecha: date) -> bool:
        """Verifica si una fecha es día hábil"""
        return self.obtener_dia(fecha).es_habil

    def es_dia_festivo(self, fecha: Union[date, str]) -> bool:
        """
        Verifica si una fecha es día festivo.

        Args:
            fecha: Fecha como date o string 'YYYY-MM-DD'
        """
        if isinstance(fecha, str):
            fecha = datetime.strptime(fecha, '%Y-%m-%d').date()
        return self.obtener_dia(fecha).es_festivo

    def obtener_festivos_anio(self, anio: int) -> List[DiaMexicano]:
        """
        Obtiene todos los días festivos de un año.

        Args:
            anio: Año a consultar

        Returns:
            Lista de DiaMexicano
        """
        festivos = self._get_festivos_anio(anio)
        return [
            DiaMexicano(
                fecha=fecha,
                tipo=TipoDia.FESTIVO,
                es_habil=False,
                es_festivo=True,
                nombre_festivo=nombre,
            )
            for fecha, nombre in sorted(festivos.items())
        ]

    def obtener_festivos_mes(self, anio: int, mes: int) -> List[DiaMexicano]:
        """Obtiene festivos de un mes específico"""
        festivos = self.obtener_festivos_anio(anio)
        return [f for f in festivos if f.fecha.month == mes]

    def contar_dias_habiles(self, fecha_inicio: date, fecha_fin: date) -> int:
        """
        Cuenta los días hábiles entre dos fechas (inclusive).

        Args:
            fecha_inicio: Fecha de inicio
            fecha_fin: Fecha de fin

        Returns:
            Número de días hábiles
        """
        if fecha_inicio > fecha_fin:
            fecha_inicio, fecha_fin = fecha_fin, fecha_inicio

        dias_habiles = 0
        fecha_actual = fecha_inicio

        while fecha_actual <= fecha_fin:
            if self.es_dia_habil(fecha_actual):
                dias_habiles += 1
            fecha_actual += timedelta(days=1)

        return dias_habiles

    def sumar_dias_habiles(self, fecha: date, dias: int) -> date:
        """
        Suma días hábiles a una fecha.

        Args:
            fecha: Fecha inicial
            dias: Días hábiles a sumar (puede ser negativo)

        Returns:
            Nueva fecha
        """
        if dias == 0:
            return fecha

        direccion = 1 if dias > 0 else -1
        dias_restantes = abs(dias)
        fecha_actual = fecha

        while dias_restantes > 0:
            fecha_actual += timedelta(days=direccion)
            if self.es_dia_habil(fecha_actual):
                dias_restantes -= 1

        return fecha_actual

    def obtener_proximo_dia_habil(self, fecha: date) -> date:
        """
        Obtiene el próximo día hábil desde una fecha.

        Args:
            fecha: Fecha de referencia

        Returns:
            Próximo día hábil
        """
        fecha_actual = fecha
        while not self.es_dia_habil(fecha_actual):
            fecha_actual += timedelta(days=1)
        return fecha_actual

    def obtener_semana_laboral(self, fecha: date) -> Tuple[date, date]:
        """
        Obtiene el rango de la semana laboral (lunes a viernes).

        Args:
            fecha: Cualquier fecha de la semana

        Returns:
            Tuple (lunes, viernes)
        """
        dias_desde_lunes = fecha.weekday()
        lunes = fecha - timedelta(days=dias_desde_lunes)
        viernes = lunes + timedelta(days=4)
        return lunes, viernes

    def obtener_calendario_mes(self, anio: int, mes: int) -> List[DiaMexicano]:
        """
        Obtiene el calendario completo de un mes.

        Args:
            anio: Año
            mes: Mes (1-12)

        Returns:
            Lista de DiaMexicano para cada día
        """
        from calendar import monthrange
        _, ultimo_dia = monthrange(anio, mes)

        return [
            self.obtener_dia(date(anio, mes, dia))
            for dia in range(1, ultimo_dia + 1)
        ]

    def resumen_mes(self, anio: int, mes: int) -> Dict:
        """
        Obtiene un resumen del mes.

        Args:
            anio: Año
            mes: Mes

        Returns:
            Dict con estadísticas del mes
        """
        calendario = self.obtener_calendario_mes(anio, mes)

        return {
            'anio': anio,
            'mes': mes,
            'total_dias': len(calendario),
            'dias_habiles': sum(1 for d in calendario if d.es_habil),
            'fines_semana': sum(1 for d in calendario if d.tipo == TipoDia.FIN_SEMANA),
            'festivos': sum(1 for d in calendario if d.es_festivo),
            'lista_festivos': [
                {'fecha': d.fecha.isoformat(), 'nombre': d.nombre_festivo}
                for d in calendario if d.es_festivo
            ],
        }

    # ═══════════════════════════════════════════════════════════
    # MÉTODOS DE BaseAPIClient
    # ═══════════════════════════════════════════════════════════

    def health_check(self) -> bool:
        """Verifica que el calendario funcione correctamente"""
        try:
            # Verificar que podemos obtener información de hoy
            hoy = self.obtener_dia(date.today())
            return hoy is not None
        except Exception as e:
            logger.error(f"❌ Health check falló: {e}")
            return False

    def get_info(self) -> Dict:
        """Obtiene información de la API"""
        return {
            'nombre': self.API_NAME,
            'version': self.API_VERSION,
            'descripcion': self.API_DESCRIPTION,
            'rango_anios': f"{self._anio_inicio}-{self._anio_fin}",
            'anios_cacheados': list(self._festivos_cache.keys()),
            'total_festivos_cacheados': sum(
                len(f) for f in self._festivos_cache.values()
            ),
        }
