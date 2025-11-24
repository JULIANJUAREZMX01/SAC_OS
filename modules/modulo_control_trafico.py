"""
═══════════════════════════════════════════════════════════════════════════════
MÓDULO DE CONTROL DE TRÁFICO Y SCHEDULING
Sistema de Automatización de Consultas - Chedraui CEDIS 427
═══════════════════════════════════════════════════════════════════════════════

Sistema integral de gestión de tráfico para el CEDIS 427 que incluye:
- Organización de citas de recibo y expedición
- Asignación inteligente de compuertas con transportistas
- Estimación de tiempos de carga basada en datos históricos
- Aprendizaje en tiempo real para optimización de parámetros
- Asignación automática de circuitos (200, 201, 202)
- Gestión y organización de equipos operativos

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
═══════════════════════════════════════════════════════════════════════════════
"""

import logging
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta, time
from collections import defaultdict
import json
import pickle
from pathlib import Path
import statistics
import math

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTES Y CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════════════════════

ALMACEN_427 = "427"
CEDIS_NAME = "CEDIS Cancún"

# Configuración de compuertas disponibles
COMPUERTAS_RECIBO = list(range(1, 21))      # Compuertas 1-20 para recibo
COMPUERTAS_EXPEDICION = list(range(21, 41)) # Compuertas 21-40 para expedición

# Circuitos disponibles para el almacén 427
CIRCUITOS_DISPONIBLES = [200, 201, 202]

# Horarios de operación
HORA_INICIO_OPERACION = time(6, 0)   # 6:00 AM
HORA_FIN_OPERACION = time(22, 0)     # 10:00 PM

# Configuración de slots de tiempo (en minutos)
DURACION_SLOT_MINUTOS = 30

# Tiempos base de operación (minutos) - serán ajustados por ML
TIEMPOS_BASE = {
    'descarga_tarima': 2,           # Tiempo por tarima
    'carga_tarima': 2.5,            # Tiempo por tarima en expedición
    'setup_compuerta': 10,          # Tiempo de preparación
    'liberacion_compuerta': 5,      # Tiempo de liberación
    'verificacion_documentos': 15,  # Tiempo verificación documental
    'buffer_seguridad': 10,         # Buffer adicional
}

# Capacidades por tipo de vehículo
CAPACIDAD_VEHICULOS = {
    'trailer_48': {'tarimas': 48, 'factor_tiempo': 1.0},
    'trailer_53': {'tarimas': 53, 'factor_tiempo': 1.1},
    'torton': {'tarimas': 24, 'factor_tiempo': 0.6},
    'rabon': {'tarimas': 12, 'factor_tiempo': 0.4},
    'camioneta': {'tarimas': 4, 'factor_tiempo': 0.2},
}

# ═══════════════════════════════════════════════════════════════════════════════
# ENUMS Y TIPOS
# ═══════════════════════════════════════════════════════════════════════════════

class TipoCita(Enum):
    """Tipos de citas disponibles"""
    RECIBO = "RECIBO"
    EXPEDICION = "EXPEDICION"
    CROSS_DOCK = "CROSS_DOCK"
    DEVOLUCION = "DEVOLUCION"


class EstadoCita(Enum):
    """Estados posibles de una cita"""
    PROGRAMADA = "🔵 PROGRAMADA"
    CONFIRMADA = "✅ CONFIRMADA"
    EN_PATIO = "🚛 EN PATIO"
    EN_COMPUERTA = "🔄 EN COMPUERTA"
    EN_PROCESO = "⏳ EN PROCESO"
    COMPLETADA = "✅ COMPLETADA"
    CANCELADA = "❌ CANCELADA"
    REPROGRAMADA = "🔄 REPROGRAMADA"
    RETRASADA = "⚠️ RETRASADA"


class EstadoCompuerta(Enum):
    """Estados de una compuerta"""
    DISPONIBLE = "🟢 DISPONIBLE"
    OCUPADA = "🔴 OCUPADA"
    MANTENIMIENTO = "🔧 MANTENIMIENTO"
    RESERVADA = "🟡 RESERVADA"


class PrioridadCita(Enum):
    """Niveles de prioridad para citas"""
    URGENTE = 1
    ALTA = 2
    NORMAL = 3
    BAJA = 4


class TipoCircuito(Enum):
    """Circuitos de distribución disponibles"""
    CIRCUITO_200 = 200  # Zona Centro/Norte de Quintana Roo
    CIRCUITO_201 = 201  # Zona Sur de Quintana Roo
    CIRCUITO_202 = 202  # Zona Yucatán/Campeche


# ═══════════════════════════════════════════════════════════════════════════════
# DATACLASSES - ESTRUCTURAS DE DATOS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Transportista:
    """Información del transportista"""
    id_transportista: str
    nombre: str
    rfc: str
    telefono: str
    email: Optional[str] = None
    tipo_vehiculo: str = 'trailer_48'
    placas: Optional[str] = None
    nombre_operador: Optional[str] = None
    licencia_operador: Optional[str] = None
    calificacion: float = 5.0  # Rating 1-5
    historico_puntualidad: float = 0.95  # % de puntualidad
    citas_completadas: int = 0
    tiempo_promedio_descarga: Optional[float] = None  # Minutos
    activo: bool = True
    metadata: Dict = field(default_factory=dict)


@dataclass
class Compuerta:
    """Información de una compuerta/dock"""
    numero: int
    tipo: TipoCita
    estado: EstadoCompuerta = EstadoCompuerta.DISPONIBLE
    capacidad_vehiculo: List[str] = field(default_factory=lambda: list(CAPACIDAD_VEHICULOS.keys()))
    tiene_rampa: bool = True
    tiene_nivelador: bool = True
    zona: str = "PRINCIPAL"
    temperatura_controlada: bool = False
    cita_actual: Optional[str] = None  # ID de cita actual
    ultimo_uso: Optional[datetime] = None
    tiempo_promedio_operacion: Optional[float] = None
    mantenimiento_programado: Optional[datetime] = None
    notas: str = ""


@dataclass
class SlotTiempo:
    """Slot de tiempo disponible"""
    hora_inicio: datetime
    hora_fin: datetime
    compuerta: int
    disponible: bool = True
    cita_asignada: Optional[str] = None
    prioridad_reserva: Optional[PrioridadCita] = None


@dataclass
class CitaTrafico:
    """Cita de tráfico (recibo o expedición)"""
    id_cita: str
    tipo: TipoCita
    estado: EstadoCita
    fecha_programada: datetime
    hora_programada: time
    hora_llegada_real: Optional[datetime] = None
    hora_inicio_operacion: Optional[datetime] = None
    hora_fin_operacion: Optional[datetime] = None

    # Información del transporte
    transportista: Optional[Transportista] = None
    tipo_vehiculo: str = 'trailer_48'
    placas: str = ""
    operador: str = ""

    # Asignaciones
    compuerta_asignada: Optional[int] = None
    circuito_asignado: Optional[int] = None
    equipo_asignado: Optional[str] = None

    # Información de carga
    numero_oc: Optional[str] = None
    numero_asn: Optional[str] = None
    cantidad_tarimas: int = 0
    cantidad_cajas: int = 0
    peso_kg: float = 0.0
    tiendas_destino: List[str] = field(default_factory=list)

    # Tiempos estimados
    tiempo_estimado_minutos: int = 60
    tiempo_real_minutos: Optional[int] = None

    # Prioridad y notas
    prioridad: PrioridadCita = PrioridadCita.NORMAL
    notas: str = ""
    alertas: List[str] = field(default_factory=list)

    # Metadata
    creado_por: str = "SISTEMA"
    fecha_creacion: datetime = field(default_factory=datetime.now)
    ultima_modificacion: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)


@dataclass
class EquipoOperativo:
    """Equipo operativo asignado"""
    id_equipo: str
    nombre: str
    tipo: str  # 'RECIBO', 'EXPEDICION', 'MONTACARGAS', 'VERIFICADOR'
    miembros: List[str] = field(default_factory=list)
    lider: Optional[str] = None
    turno: str = "MATUTINO"  # MATUTINO, VESPERTINO, NOCTURNO
    zona_asignada: Optional[str] = None
    compuertas_asignadas: List[int] = field(default_factory=list)
    capacidad_tarimas_hora: int = 30
    activo: bool = True
    eficiencia_promedio: float = 1.0  # Factor de eficiencia


@dataclass
class MetricasRendimiento:
    """Métricas de rendimiento para aprendizaje"""
    fecha: datetime
    tipo_operacion: TipoCita
    transportista_id: str
    compuerta: int
    circuito: int
    tipo_vehiculo: str
    cantidad_tarimas: int
    tiempo_estimado: int
    tiempo_real: int
    desviacion_porcentaje: float
    hora_llegada: datetime
    puntualidad: bool  # Llegó a tiempo
    equipo_id: str
    condiciones: Dict = field(default_factory=dict)  # Clima, día semana, etc.


@dataclass
class ParametrosAprendizaje:
    """Parámetros del sistema de aprendizaje"""
    factor_tiempo_descarga: float = 1.0
    factor_tiempo_carga: float = 1.0
    factor_setup: float = 1.0
    factores_por_transportista: Dict[str, float] = field(default_factory=dict)
    factores_por_compuerta: Dict[int, float] = field(default_factory=dict)
    factores_por_circuito: Dict[int, float] = field(default_factory=dict)
    factores_por_hora: Dict[int, float] = field(default_factory=dict)
    factores_por_dia_semana: Dict[int, float] = field(default_factory=dict)
    ultima_actualizacion: datetime = field(default_factory=datetime.now)
    total_muestras: int = 0
    precision_modelo: float = 0.0


# ═══════════════════════════════════════════════════════════════════════════════
# CLASE PRINCIPAL: GESTOR DE CONTROL DE TRÁFICO
# ═══════════════════════════════════════════════════════════════════════════════

class GestorControlTrafico:
    """
    Gestor principal de control de tráfico para CEDIS 427.

    Funcionalidades:
    - Gestión de citas de recibo y expedición
    - Asignación inteligente de compuertas
    - Estimación de tiempos basada en ML
    - Asignación de circuitos
    - Gestión de equipos operativos
    """

    def __init__(
        self,
        almacen: str = ALMACEN_427,
        ruta_datos: Optional[Path] = None
    ):
        """
        Inicializa el gestor de control de tráfico.

        Args:
            almacen: Código del almacén (default: 427)
            ruta_datos: Ruta para persistencia de datos
        """
        self.almacen = almacen
        self.ruta_datos = ruta_datos or Path("output/trafico")
        self.ruta_datos.mkdir(parents=True, exist_ok=True)

        # Inicializar estructuras de datos
        self.citas: Dict[str, CitaTrafico] = {}
        self.compuertas: Dict[int, Compuerta] = {}
        self.transportistas: Dict[str, Transportista] = {}
        self.equipos: Dict[str, EquipoOperativo] = {}
        self.slots_disponibles: List[SlotTiempo] = []
        self.historico_metricas: List[MetricasRendimiento] = []

        # Parámetros de aprendizaje
        self.parametros_ml = ParametrosAprendizaje()

        # Inicializar compuertas
        self._inicializar_compuertas()

        # Cargar datos persistidos
        self._cargar_datos()

        logger.info(f"🚛 Gestor de Control de Tráfico inicializado - Almacén {almacen}")

    def _inicializar_compuertas(self) -> None:
        """Inicializa las compuertas del CEDIS"""
        # Compuertas de recibo
        for num in COMPUERTAS_RECIBO:
            self.compuertas[num] = Compuerta(
                numero=num,
                tipo=TipoCita.RECIBO,
                zona="RECIBO_PRINCIPAL" if num <= 10 else "RECIBO_SECUNDARIO"
            )

        # Compuertas de expedición
        for num in COMPUERTAS_EXPEDICION:
            self.compuertas[num] = Compuerta(
                numero=num,
                tipo=TipoCita.EXPEDICION,
                zona="EXPEDICION_PRINCIPAL" if num <= 30 else "EXPEDICION_SECUNDARIO"
            )

        logger.info(f"✅ {len(self.compuertas)} compuertas inicializadas")

    # ═══════════════════════════════════════════════════════════════════════════
    # GESTIÓN DE CITAS
    # ═══════════════════════════════════════════════════════════════════════════

    def crear_cita(
        self,
        tipo: TipoCita,
        fecha: datetime,
        hora: time,
        transportista_id: Optional[str] = None,
        numero_oc: Optional[str] = None,
        numero_asn: Optional[str] = None,
        cantidad_tarimas: int = 0,
        tiendas_destino: List[str] = None,
        prioridad: PrioridadCita = PrioridadCita.NORMAL,
        tipo_vehiculo: str = 'trailer_48',
        notas: str = ""
    ) -> Tuple[bool, str, Optional[CitaTrafico]]:
        """
        Crea una nueva cita de tráfico.

        Args:
            tipo: Tipo de cita (RECIBO/EXPEDICION)
            fecha: Fecha de la cita
            hora: Hora programada
            transportista_id: ID del transportista
            numero_oc: Número de orden de compra
            numero_asn: Número de ASN
            cantidad_tarimas: Cantidad de tarimas
            tiendas_destino: Lista de tiendas destino
            prioridad: Nivel de prioridad
            tipo_vehiculo: Tipo de vehículo
            notas: Notas adicionales

        Returns:
            Tuple con (éxito, mensaje, cita creada)
        """
        try:
            # Generar ID único
            id_cita = f"CITA-{self.almacen}-{tipo.value[:3]}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

            # Obtener transportista si existe
            transportista = self.transportistas.get(transportista_id) if transportista_id else None

            # Calcular tiempo estimado
            tiempo_estimado = self.estimar_tiempo_operacion(
                tipo=tipo,
                cantidad_tarimas=cantidad_tarimas,
                tipo_vehiculo=tipo_vehiculo,
                transportista_id=transportista_id
            )

            # Buscar y asignar compuerta óptima
            compuerta_optima = self._buscar_compuerta_optima(
                tipo=tipo,
                fecha=fecha,
                hora=hora,
                duracion_minutos=tiempo_estimado,
                tipo_vehiculo=tipo_vehiculo,
                prioridad=prioridad
            )

            if compuerta_optima is None:
                return (False, "❌ No hay compuertas disponibles para el horario solicitado", None)

            # Asignar circuito si es expedición
            circuito = None
            if tipo == TipoCita.EXPEDICION and tiendas_destino:
                circuito = self._asignar_circuito_optimo(tiendas_destino)

            # Crear la cita
            cita = CitaTrafico(
                id_cita=id_cita,
                tipo=tipo,
                estado=EstadoCita.PROGRAMADA,
                fecha_programada=fecha,
                hora_programada=hora,
                transportista=transportista,
                tipo_vehiculo=tipo_vehiculo,
                compuerta_asignada=compuerta_optima,
                circuito_asignado=circuito,
                numero_oc=numero_oc,
                numero_asn=numero_asn,
                cantidad_tarimas=cantidad_tarimas,
                tiendas_destino=tiendas_destino or [],
                tiempo_estimado_minutos=tiempo_estimado,
                prioridad=prioridad,
                notas=notas
            )

            # Guardar cita
            self.citas[id_cita] = cita

            # Actualizar estado de compuerta
            self.compuertas[compuerta_optima].estado = EstadoCompuerta.RESERVADA

            # Persistir datos
            self._guardar_datos()

            logger.info(f"✅ Cita {id_cita} creada exitosamente - Compuerta {compuerta_optima}")

            return (True, f"✅ Cita creada: {id_cita}", cita)

        except Exception as e:
            logger.error(f"❌ Error al crear cita: {e}")
            return (False, f"❌ Error: {str(e)}", None)

    def actualizar_estado_cita(
        self,
        id_cita: str,
        nuevo_estado: EstadoCita,
        hora_evento: Optional[datetime] = None,
        notas: str = ""
    ) -> Tuple[bool, str]:
        """
        Actualiza el estado de una cita.

        Args:
            id_cita: ID de la cita
            nuevo_estado: Nuevo estado
            hora_evento: Hora del evento (si aplica)
            notas: Notas adicionales

        Returns:
            Tuple con (éxito, mensaje)
        """
        if id_cita not in self.citas:
            return (False, f"❌ Cita {id_cita} no encontrada")

        cita = self.citas[id_cita]
        estado_anterior = cita.estado
        cita.estado = nuevo_estado
        cita.ultima_modificacion = datetime.now()

        hora_evento = hora_evento or datetime.now()

        # Actualizar campos según el nuevo estado
        if nuevo_estado == EstadoCita.EN_PATIO:
            cita.hora_llegada_real = hora_evento
            # Calcular puntualidad
            programada = datetime.combine(cita.fecha_programada, cita.hora_programada)
            diferencia = (hora_evento - programada).total_seconds() / 60
            if diferencia > 15:  # Más de 15 minutos tarde
                cita.alertas.append(f"⚠️ Llegada tardía: {int(diferencia)} min de retraso")

        elif nuevo_estado == EstadoCita.EN_COMPUERTA:
            if cita.compuerta_asignada:
                self.compuertas[cita.compuerta_asignada].estado = EstadoCompuerta.OCUPADA
                self.compuertas[cita.compuerta_asignada].cita_actual = id_cita

        elif nuevo_estado == EstadoCita.EN_PROCESO:
            cita.hora_inicio_operacion = hora_evento

        elif nuevo_estado == EstadoCita.COMPLETADA:
            cita.hora_fin_operacion = hora_evento
            if cita.hora_inicio_operacion:
                cita.tiempo_real_minutos = int(
                    (hora_evento - cita.hora_inicio_operacion).total_seconds() / 60
                )
            # Liberar compuerta
            if cita.compuerta_asignada:
                self.compuertas[cita.compuerta_asignada].estado = EstadoCompuerta.DISPONIBLE
                self.compuertas[cita.compuerta_asignada].cita_actual = None
                self.compuertas[cita.compuerta_asignada].ultimo_uso = hora_evento

            # Registrar métricas para aprendizaje
            self._registrar_metricas_completacion(cita)

        elif nuevo_estado == EstadoCita.CANCELADA:
            if cita.compuerta_asignada:
                self.compuertas[cita.compuerta_asignada].estado = EstadoCompuerta.DISPONIBLE
                self.compuertas[cita.compuerta_asignada].cita_actual = None

        if notas:
            cita.notas += f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M')}] {notas}"

        self._guardar_datos()

        logger.info(f"🔄 Cita {id_cita}: {estado_anterior.value} → {nuevo_estado.value}")

        return (True, f"✅ Estado actualizado: {nuevo_estado.value}")

    def obtener_citas_dia(
        self,
        fecha: datetime,
        tipo: Optional[TipoCita] = None
    ) -> List[CitaTrafico]:
        """Obtiene todas las citas de un día específico"""
        citas_dia = []
        fecha_solo = fecha.date() if isinstance(fecha, datetime) else fecha

        for cita in self.citas.values():
            cita_fecha = cita.fecha_programada.date() if isinstance(cita.fecha_programada, datetime) else cita.fecha_programada
            if cita_fecha == fecha_solo:
                if tipo is None or cita.tipo == tipo:
                    citas_dia.append(cita)

        # Ordenar por hora programada
        citas_dia.sort(key=lambda c: c.hora_programada)

        return citas_dia

    def obtener_ocupacion_compuertas(
        self,
        fecha: datetime,
        hora_inicio: time,
        hora_fin: time
    ) -> Dict[int, List[Dict]]:
        """
        Obtiene la ocupación de compuertas en un rango de tiempo.

        Returns:
            Dict con número de compuerta y lista de slots ocupados
        """
        ocupacion = {}

        for num, compuerta in self.compuertas.items():
            ocupacion[num] = {
                'tipo': compuerta.tipo.value,
                'estado_actual': compuerta.estado.value,
                'slots_ocupados': []
            }

        citas_dia = self.obtener_citas_dia(fecha)

        for cita in citas_dia:
            if cita.compuerta_asignada and cita.estado not in [EstadoCita.CANCELADA, EstadoCita.COMPLETADA]:
                ocupacion[cita.compuerta_asignada]['slots_ocupados'].append({
                    'id_cita': cita.id_cita,
                    'hora_inicio': cita.hora_programada.strftime('%H:%M'),
                    'duracion': cita.tiempo_estimado_minutos,
                    'transportista': cita.transportista.nombre if cita.transportista else 'N/A',
                    'estado': cita.estado.value
                })

        return ocupacion

    # ═══════════════════════════════════════════════════════════════════════════
    # ASIGNACIÓN DE COMPUERTAS
    # ═══════════════════════════════════════════════════════════════════════════

    def _buscar_compuerta_optima(
        self,
        tipo: TipoCita,
        fecha: datetime,
        hora: time,
        duracion_minutos: int,
        tipo_vehiculo: str,
        prioridad: PrioridadCita
    ) -> Optional[int]:
        """
        Busca la compuerta óptima para una cita.

        Algoritmo de optimización:
        1. Filtrar compuertas por tipo (recibo/expedición)
        2. Verificar disponibilidad en el horario
        3. Considerar capacidad de vehículo
        4. Optimizar por tiempo promedio de operación
        5. Balancear carga entre compuertas

        Returns:
            Número de compuerta óptima o None si no hay disponibilidad
        """
        # Filtrar compuertas del tipo correcto
        compuertas_candidatas = [
            c for c in self.compuertas.values()
            if c.tipo == tipo and c.estado != EstadoCompuerta.MANTENIMIENTO
        ]

        if not compuertas_candidatas:
            return None

        # Verificar que el vehículo sea compatible
        compuertas_candidatas = [
            c for c in compuertas_candidatas
            if tipo_vehiculo in c.capacidad_vehiculo
        ]

        # Verificar disponibilidad en el horario
        hora_inicio = datetime.combine(fecha, hora)
        hora_fin = hora_inicio + timedelta(minutes=duracion_minutos)

        compuertas_disponibles = []

        for compuerta in compuertas_candidatas:
            if self._verificar_disponibilidad_compuerta(
                compuerta.numero, hora_inicio, hora_fin
            ):
                compuertas_disponibles.append(compuerta)

        if not compuertas_disponibles:
            return None

        # Calcular score para cada compuerta
        scores = []
        for compuerta in compuertas_disponibles:
            score = self._calcular_score_compuerta(
                compuerta, fecha, tipo_vehiculo, prioridad
            )
            scores.append((compuerta.numero, score))

        # Ordenar por score (mayor es mejor)
        scores.sort(key=lambda x: x[1], reverse=True)

        return scores[0][0]

    def _verificar_disponibilidad_compuerta(
        self,
        numero_compuerta: int,
        hora_inicio: datetime,
        hora_fin: datetime
    ) -> bool:
        """Verifica si una compuerta está disponible en un rango de tiempo"""
        for cita in self.citas.values():
            if (cita.compuerta_asignada == numero_compuerta and
                cita.estado not in [EstadoCita.CANCELADA, EstadoCita.COMPLETADA]):

                cita_inicio = datetime.combine(cita.fecha_programada, cita.hora_programada)
                cita_fin = cita_inicio + timedelta(minutes=cita.tiempo_estimado_minutos)

                # Verificar superposición
                if not (hora_fin <= cita_inicio or hora_inicio >= cita_fin):
                    return False

        return True

    def _calcular_score_compuerta(
        self,
        compuerta: Compuerta,
        fecha: datetime,
        tipo_vehiculo: str,
        prioridad: PrioridadCita
    ) -> float:
        """
        Calcula un score de optimalidad para una compuerta.

        Factores considerados:
        - Tiempo promedio de operación (mejor tiempo = mayor score)
        - Carga de trabajo (balanceo)
        - Zona de la compuerta
        - Factor de aprendizaje histórico
        """
        score = 100.0

        # Factor de tiempo promedio
        if compuerta.tiempo_promedio_operacion:
            # Normalizar entre 0.8 y 1.2
            factor_tiempo = 1.0 - (compuerta.tiempo_promedio_operacion - 60) / 120
            factor_tiempo = max(0.8, min(1.2, factor_tiempo))
            score *= factor_tiempo

        # Factor de carga (menos citas = mayor score)
        citas_en_compuerta = sum(
            1 for c in self.citas.values()
            if c.compuerta_asignada == compuerta.numero and
            c.fecha_programada.date() == fecha.date() and
            c.estado not in [EstadoCita.CANCELADA, EstadoCita.COMPLETADA]
        )
        score *= max(0.5, 1.0 - (citas_en_compuerta * 0.1))

        # Factor de zona principal
        if "PRINCIPAL" in compuerta.zona:
            score *= 1.1

        # Factor de aprendizaje
        if compuerta.numero in self.parametros_ml.factores_por_compuerta:
            score *= self.parametros_ml.factores_por_compuerta[compuerta.numero]

        # Prioridad alta prefiere compuertas principales
        if prioridad == PrioridadCita.URGENTE:
            if compuerta.numero <= 5 or (compuerta.numero >= 21 and compuerta.numero <= 25):
                score *= 1.2

        return score

    def reasignar_compuerta(
        self,
        id_cita: str,
        nueva_compuerta: int,
        motivo: str = ""
    ) -> Tuple[bool, str]:
        """Reasigna una cita a una nueva compuerta"""
        if id_cita not in self.citas:
            return (False, f"❌ Cita {id_cita} no encontrada")

        if nueva_compuerta not in self.compuertas:
            return (False, f"❌ Compuerta {nueva_compuerta} no existe")

        cita = self.citas[id_cita]
        compuerta_anterior = cita.compuerta_asignada

        # Verificar compatibilidad de tipo
        if self.compuertas[nueva_compuerta].tipo != cita.tipo:
            return (False, f"❌ La compuerta {nueva_compuerta} no es compatible con citas de {cita.tipo.value}")

        # Verificar disponibilidad
        hora_inicio = datetime.combine(cita.fecha_programada, cita.hora_programada)
        hora_fin = hora_inicio + timedelta(minutes=cita.tiempo_estimado_minutos)

        if not self._verificar_disponibilidad_compuerta(nueva_compuerta, hora_inicio, hora_fin):
            return (False, f"❌ La compuerta {nueva_compuerta} no está disponible en ese horario")

        # Realizar reasignación
        cita.compuerta_asignada = nueva_compuerta
        cita.ultima_modificacion = datetime.now()
        cita.notas += f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M')}] Reasignación: {compuerta_anterior} → {nueva_compuerta}. {motivo}"

        # Actualizar estados de compuertas si la cita está en proceso
        if cita.estado in [EstadoCita.EN_COMPUERTA, EstadoCita.EN_PROCESO]:
            if compuerta_anterior:
                self.compuertas[compuerta_anterior].estado = EstadoCompuerta.DISPONIBLE
                self.compuertas[compuerta_anterior].cita_actual = None
            self.compuertas[nueva_compuerta].estado = EstadoCompuerta.OCUPADA
            self.compuertas[nueva_compuerta].cita_actual = id_cita

        self._guardar_datos()

        logger.info(f"🔄 Cita {id_cita} reasignada: Compuerta {compuerta_anterior} → {nueva_compuerta}")

        return (True, f"✅ Compuerta reasignada exitosamente")

    # ═══════════════════════════════════════════════════════════════════════════
    # ASIGNACIÓN DE CIRCUITOS
    # ═══════════════════════════════════════════════════════════════════════════

    def _asignar_circuito_optimo(self, tiendas_destino: List[str]) -> int:
        """
        Asigna el circuito óptimo basado en las tiendas destino.

        Circuito 200: Zona Centro/Norte de Quintana Roo
        Circuito 201: Zona Sur de Quintana Roo
        Circuito 202: Zona Yucatán/Campeche

        Args:
            tiendas_destino: Lista de códigos de tiendas

        Returns:
            Número de circuito asignado
        """
        # Mapeo de tiendas a zonas (ejemplo - se debe configurar según datos reales)
        zonas_tiendas = {
            '200': ['C427', 'C428', 'C429', 'C430', 'C431', 'C432'],  # Cancún, Playa, etc.
            '201': ['C433', 'C434', 'C435', 'C436', 'C437'],          # Chetumal, Bacalar, etc.
            '202': ['C438', 'C439', 'C440', 'C441', 'C442', 'C443'],  # Mérida, Campeche, etc.
        }

        # Contar tiendas por zona
        conteo_zonas = defaultdict(int)

        for tienda in tiendas_destino:
            for circuito, tiendas_circuito in zonas_tiendas.items():
                if tienda in tiendas_circuito:
                    conteo_zonas[circuito] += 1
                    break

        # Si hay tiendas identificadas, usar el circuito predominante
        if conteo_zonas:
            circuito_optimo = max(conteo_zonas.items(), key=lambda x: x[1])[0]
            return int(circuito_optimo)

        # Por defecto, circuito 200 (zona principal)
        return 200

    def obtener_citas_por_circuito(
        self,
        circuito: int,
        fecha: Optional[datetime] = None
    ) -> List[CitaTrafico]:
        """Obtiene todas las citas de un circuito específico"""
        citas_circuito = []
        fecha_filtro = (fecha or datetime.now()).date()

        for cita in self.citas.values():
            if cita.circuito_asignado == circuito:
                if fecha is None or cita.fecha_programada.date() == fecha_filtro:
                    citas_circuito.append(cita)

        return sorted(citas_circuito, key=lambda c: c.hora_programada)

    def optimizar_secuencia_circuito(
        self,
        circuito: int,
        fecha: datetime
    ) -> List[CitaTrafico]:
        """
        Optimiza la secuencia de citas para un circuito.

        Considera:
        - Ubicación geográfica de tiendas
        - Prioridad de entregas
        - Capacidad de vehículos
        - Ventanas de tiempo de tiendas

        Returns:
            Lista de citas en secuencia optimizada
        """
        citas = self.obtener_citas_por_circuito(circuito, fecha)

        if not citas:
            return []

        # Ordenar por prioridad y luego por hora
        citas_ordenadas = sorted(
            citas,
            key=lambda c: (c.prioridad.value, c.hora_programada)
        )

        # Aplicar factores de aprendizaje si existen
        if circuito in self.parametros_ml.factores_por_circuito:
            factor = self.parametros_ml.factores_por_circuito[circuito]
            for cita in citas_ordenadas:
                cita.tiempo_estimado_minutos = int(cita.tiempo_estimado_minutos * factor)

        logger.info(f"📦 Secuencia optimizada para circuito {circuito}: {len(citas_ordenadas)} citas")

        return citas_ordenadas

    # ═══════════════════════════════════════════════════════════════════════════
    # ESTIMACIÓN DE TIEMPOS (con ML)
    # ═══════════════════════════════════════════════════════════════════════════

    def estimar_tiempo_operacion(
        self,
        tipo: TipoCita,
        cantidad_tarimas: int,
        tipo_vehiculo: str = 'trailer_48',
        transportista_id: Optional[str] = None,
        compuerta: Optional[int] = None,
        circuito: Optional[int] = None
    ) -> int:
        """
        Estima el tiempo de operación usando el modelo de aprendizaje.

        El tiempo se calcula como:
        Tiempo = (setup + (tarimas * tiempo_por_tarima) + liberación + buffer) * factores_ML

        Args:
            tipo: Tipo de operación
            cantidad_tarimas: Número de tarimas
            tipo_vehiculo: Tipo de vehículo
            transportista_id: ID del transportista
            compuerta: Número de compuerta
            circuito: Número de circuito

        Returns:
            Tiempo estimado en minutos
        """
        # Tiempo base
        tiempo_setup = TIEMPOS_BASE['setup_compuerta']
        tiempo_liberacion = TIEMPOS_BASE['liberacion_compuerta']
        tiempo_verificacion = TIEMPOS_BASE['verificacion_documentos']
        buffer = TIEMPOS_BASE['buffer_seguridad']

        # Tiempo por tarima según tipo de operación
        if tipo == TipoCita.RECIBO:
            tiempo_tarima = TIEMPOS_BASE['descarga_tarima']
            factor_base = self.parametros_ml.factor_tiempo_descarga
        else:
            tiempo_tarima = TIEMPOS_BASE['carga_tarima']
            factor_base = self.parametros_ml.factor_tiempo_carga

        # Factor de tipo de vehículo
        factor_vehiculo = CAPACIDAD_VEHICULOS.get(
            tipo_vehiculo, {'factor_tiempo': 1.0}
        )['factor_tiempo']

        # Calcular tiempo base
        tiempo_operacion = cantidad_tarimas * tiempo_tarima * factor_vehiculo
        tiempo_total = tiempo_setup + tiempo_verificacion + tiempo_operacion + tiempo_liberacion + buffer

        # Aplicar factores de aprendizaje
        factor_ml = factor_base * self.parametros_ml.factor_setup

        # Factor por transportista
        if transportista_id and transportista_id in self.parametros_ml.factores_por_transportista:
            factor_ml *= self.parametros_ml.factores_por_transportista[transportista_id]

        # Factor por compuerta
        if compuerta and compuerta in self.parametros_ml.factores_por_compuerta:
            factor_ml *= self.parametros_ml.factores_por_compuerta[compuerta]

        # Factor por circuito
        if circuito and circuito in self.parametros_ml.factores_por_circuito:
            factor_ml *= self.parametros_ml.factores_por_circuito[circuito]

        # Factor por hora del día
        hora_actual = datetime.now().hour
        if hora_actual in self.parametros_ml.factores_por_hora:
            factor_ml *= self.parametros_ml.factores_por_hora[hora_actual]

        # Factor por día de la semana
        dia_semana = datetime.now().weekday()
        if dia_semana in self.parametros_ml.factores_por_dia_semana:
            factor_ml *= self.parametros_ml.factores_por_dia_semana[dia_semana]

        tiempo_final = int(tiempo_total * factor_ml)

        # Mínimo 15 minutos, máximo 480 minutos (8 horas)
        tiempo_final = max(15, min(480, tiempo_final))

        logger.debug(f"⏱️ Tiempo estimado: {tiempo_final} min (base: {tiempo_total:.1f}, factor ML: {factor_ml:.3f})")

        return tiempo_final

    def _registrar_metricas_completacion(self, cita: CitaTrafico) -> None:
        """Registra métricas al completar una cita para aprendizaje"""
        if cita.tiempo_real_minutos is None or cita.tiempo_estimado_minutos == 0:
            return

        desviacion = ((cita.tiempo_real_minutos - cita.tiempo_estimado_minutos)
                      / cita.tiempo_estimado_minutos) * 100

        puntualidad = True
        if cita.hora_llegada_real and cita.hora_programada:
            programada = datetime.combine(cita.fecha_programada, cita.hora_programada)
            diferencia = (cita.hora_llegada_real - programada).total_seconds() / 60
            puntualidad = diferencia <= 15

        metrica = MetricasRendimiento(
            fecha=datetime.now(),
            tipo_operacion=cita.tipo,
            transportista_id=cita.transportista.id_transportista if cita.transportista else "N/A",
            compuerta=cita.compuerta_asignada or 0,
            circuito=cita.circuito_asignado or 0,
            tipo_vehiculo=cita.tipo_vehiculo,
            cantidad_tarimas=cita.cantidad_tarimas,
            tiempo_estimado=cita.tiempo_estimado_minutos,
            tiempo_real=cita.tiempo_real_minutos,
            desviacion_porcentaje=desviacion,
            hora_llegada=cita.hora_llegada_real or datetime.now(),
            puntualidad=puntualidad,
            equipo_id=cita.equipo_asignado or "N/A",
            condiciones={
                'dia_semana': cita.fecha_programada.weekday(),
                'hora': cita.hora_programada.hour,
                'prioridad': cita.prioridad.value
            }
        )

        self.historico_metricas.append(metrica)

        # Actualizar modelo de aprendizaje cada 10 métricas
        if len(self.historico_metricas) % 10 == 0:
            self.actualizar_modelo_aprendizaje()

        logger.info(f"📊 Métrica registrada - Desviación: {desviacion:.1f}%")

    def actualizar_modelo_aprendizaje(self) -> Dict[str, Any]:
        """
        Actualiza los parámetros del modelo de aprendizaje basado en métricas históricas.

        Algoritmo:
        1. Agrupa métricas por dimensión (transportista, compuerta, etc.)
        2. Calcula la desviación promedio por grupo
        3. Ajusta los factores para minimizar desviación futura

        Returns:
            Dict con los nuevos parámetros y estadísticas
        """
        if len(self.historico_metricas) < 5:
            logger.warning("⚠️ Insuficientes datos para actualizar modelo (min 5 métricas)")
            return {'status': 'insufficient_data', 'samples': len(self.historico_metricas)}

        logger.info("🧠 Actualizando modelo de aprendizaje...")

        # Calcular factor global de descarga/carga
        metricas_recibo = [m for m in self.historico_metricas if m.tipo_operacion == TipoCita.RECIBO]
        metricas_expedicion = [m for m in self.historico_metricas if m.tipo_operacion == TipoCita.EXPEDICION]

        if metricas_recibo:
            desviacion_promedio_recibo = statistics.mean([m.desviacion_porcentaje for m in metricas_recibo])
            self.parametros_ml.factor_tiempo_descarga = self._ajustar_factor(
                self.parametros_ml.factor_tiempo_descarga, desviacion_promedio_recibo
            )

        if metricas_expedicion:
            desviacion_promedio_expedicion = statistics.mean([m.desviacion_porcentaje for m in metricas_expedicion])
            self.parametros_ml.factor_tiempo_carga = self._ajustar_factor(
                self.parametros_ml.factor_tiempo_carga, desviacion_promedio_expedicion
            )

        # Calcular factores por transportista
        transportistas_metricas = defaultdict(list)
        for m in self.historico_metricas:
            if m.transportista_id != "N/A":
                transportistas_metricas[m.transportista_id].append(m.desviacion_porcentaje)

        for trans_id, desviaciones in transportistas_metricas.items():
            if len(desviaciones) >= 3:
                desv_promedio = statistics.mean(desviaciones)
                factor_actual = self.parametros_ml.factores_por_transportista.get(trans_id, 1.0)
                self.parametros_ml.factores_por_transportista[trans_id] = self._ajustar_factor(
                    factor_actual, desv_promedio
                )

        # Calcular factores por compuerta
        compuertas_metricas = defaultdict(list)
        for m in self.historico_metricas:
            if m.compuerta > 0:
                compuertas_metricas[m.compuerta].append(m.desviacion_porcentaje)

        for comp, desviaciones in compuertas_metricas.items():
            if len(desviaciones) >= 3:
                desv_promedio = statistics.mean(desviaciones)
                factor_actual = self.parametros_ml.factores_por_compuerta.get(comp, 1.0)
                self.parametros_ml.factores_por_compuerta[comp] = self._ajustar_factor(
                    factor_actual, desv_promedio
                )

        # Calcular factores por circuito
        circuitos_metricas = defaultdict(list)
        for m in self.historico_metricas:
            if m.circuito > 0:
                circuitos_metricas[m.circuito].append(m.desviacion_porcentaje)

        for circ, desviaciones in circuitos_metricas.items():
            if len(desviaciones) >= 3:
                desv_promedio = statistics.mean(desviaciones)
                factor_actual = self.parametros_ml.factores_por_circuito.get(circ, 1.0)
                self.parametros_ml.factores_por_circuito[circ] = self._ajustar_factor(
                    factor_actual, desv_promedio
                )

        # Calcular factores por hora del día
        horas_metricas = defaultdict(list)
        for m in self.historico_metricas:
            hora = m.condiciones.get('hora', 12)
            horas_metricas[hora].append(m.desviacion_porcentaje)

        for hora, desviaciones in horas_metricas.items():
            if len(desviaciones) >= 2:
                desv_promedio = statistics.mean(desviaciones)
                factor_actual = self.parametros_ml.factores_por_hora.get(hora, 1.0)
                self.parametros_ml.factores_por_hora[hora] = self._ajustar_factor(
                    factor_actual, desv_promedio
                )

        # Calcular factores por día de la semana
        dias_metricas = defaultdict(list)
        for m in self.historico_metricas:
            dia = m.condiciones.get('dia_semana', 0)
            dias_metricas[dia].append(m.desviacion_porcentaje)

        for dia, desviaciones in dias_metricas.items():
            if len(desviaciones) >= 2:
                desv_promedio = statistics.mean(desviaciones)
                factor_actual = self.parametros_ml.factores_por_dia_semana.get(dia, 1.0)
                self.parametros_ml.factores_por_dia_semana[dia] = self._ajustar_factor(
                    factor_actual, desv_promedio
                )

        # Calcular precisión del modelo
        if self.historico_metricas:
            desviaciones_abs = [abs(m.desviacion_porcentaje) for m in self.historico_metricas[-50:]]
            self.parametros_ml.precision_modelo = 100 - statistics.mean(desviaciones_abs)

        self.parametros_ml.ultima_actualizacion = datetime.now()
        self.parametros_ml.total_muestras = len(self.historico_metricas)

        self._guardar_datos()

        resultado = {
            'status': 'updated',
            'total_muestras': self.parametros_ml.total_muestras,
            'precision_modelo': f"{self.parametros_ml.precision_modelo:.1f}%",
            'factor_descarga': self.parametros_ml.factor_tiempo_descarga,
            'factor_carga': self.parametros_ml.factor_tiempo_carga,
            'transportistas_ajustados': len(self.parametros_ml.factores_por_transportista),
            'compuertas_ajustadas': len(self.parametros_ml.factores_por_compuerta),
            'circuitos_ajustados': len(self.parametros_ml.factores_por_circuito)
        }

        logger.info(f"✅ Modelo actualizado - Precisión: {resultado['precision_modelo']}")

        return resultado

    def _ajustar_factor(self, factor_actual: float, desviacion: float) -> float:
        """
        Ajusta un factor basado en la desviación observada.

        Si la desviación es positiva (tiempo real > estimado), aumenta el factor.
        Si la desviación es negativa (tiempo real < estimado), disminuye el factor.

        Args:
            factor_actual: Factor actual
            desviacion: Desviación porcentual observada

        Returns:
            Factor ajustado
        """
        # Tasa de aprendizaje adaptativa
        tasa_aprendizaje = 0.1

        # Ajuste proporcional a la desviación
        ajuste = (desviacion / 100) * tasa_aprendizaje

        nuevo_factor = factor_actual * (1 + ajuste)

        # Limitar el factor entre 0.5 y 2.0
        nuevo_factor = max(0.5, min(2.0, nuevo_factor))

        return round(nuevo_factor, 4)

    def obtener_estadisticas_modelo(self) -> Dict[str, Any]:
        """Obtiene estadísticas detalladas del modelo de aprendizaje"""
        if not self.historico_metricas:
            return {'status': 'no_data'}

        ultimas_50 = self.historico_metricas[-50:]

        stats = {
            'total_muestras': len(self.historico_metricas),
            'precision_modelo': f"{self.parametros_ml.precision_modelo:.1f}%",
            'ultima_actualizacion': self.parametros_ml.ultima_actualizacion.strftime('%Y-%m-%d %H:%M'),
            'factores_globales': {
                'descarga': self.parametros_ml.factor_tiempo_descarga,
                'carga': self.parametros_ml.factor_tiempo_carga,
                'setup': self.parametros_ml.factor_setup
            },
            'metricas_recientes': {
                'desviacion_promedio': f"{statistics.mean([m.desviacion_porcentaje for m in ultimas_50]):.1f}%",
                'desviacion_std': f"{statistics.stdev([m.desviacion_porcentaje for m in ultimas_50]) if len(ultimas_50) > 1 else 0:.1f}%",
                'puntualidad': f"{(sum(1 for m in ultimas_50 if m.puntualidad) / len(ultimas_50)) * 100:.1f}%"
            },
            'transportistas_top': self._obtener_top_transportistas(),
            'compuertas_eficientes': self._obtener_compuertas_eficientes()
        }

        return stats

    def _obtener_top_transportistas(self, n: int = 5) -> List[Dict]:
        """Obtiene los transportistas con mejor desempeño"""
        if not self.historico_metricas:
            return []

        trans_stats = defaultdict(list)
        for m in self.historico_metricas:
            if m.transportista_id != "N/A":
                trans_stats[m.transportista_id].append({
                    'desviacion': m.desviacion_porcentaje,
                    'puntualidad': m.puntualidad
                })

        resultados = []
        for trans_id, stats in trans_stats.items():
            if len(stats) >= 3:
                desv_promedio = statistics.mean([s['desviacion'] for s in stats])
                puntualidad = sum(1 for s in stats if s['puntualidad']) / len(stats)
                score = (100 - abs(desv_promedio)) * puntualidad
                resultados.append({
                    'transportista_id': trans_id,
                    'operaciones': len(stats),
                    'desviacion_promedio': f"{desv_promedio:.1f}%",
                    'puntualidad': f"{puntualidad*100:.1f}%",
                    'score': round(score, 2)
                })

        resultados.sort(key=lambda x: x['score'], reverse=True)
        return resultados[:n]

    def _obtener_compuertas_eficientes(self, n: int = 5) -> List[Dict]:
        """Obtiene las compuertas más eficientes"""
        if not self.historico_metricas:
            return []

        comp_stats = defaultdict(list)
        for m in self.historico_metricas:
            if m.compuerta > 0:
                comp_stats[m.compuerta].append(abs(m.desviacion_porcentaje))

        resultados = []
        for comp, desviaciones in comp_stats.items():
            if len(desviaciones) >= 3:
                desv_promedio = statistics.mean(desviaciones)
                resultados.append({
                    'compuerta': comp,
                    'operaciones': len(desviaciones),
                    'desviacion_promedio': f"{desv_promedio:.1f}%",
                    'eficiencia': f"{100 - desv_promedio:.1f}%"
                })

        resultados.sort(key=lambda x: float(x['eficiencia'].replace('%', '')), reverse=True)
        return resultados[:n]

    # ═══════════════════════════════════════════════════════════════════════════
    # GESTIÓN DE TRANSPORTISTAS
    # ═══════════════════════════════════════════════════════════════════════════

    def registrar_transportista(
        self,
        nombre: str,
        rfc: str,
        telefono: str,
        tipo_vehiculo: str = 'trailer_48',
        **kwargs
    ) -> Tuple[bool, str, Optional[Transportista]]:
        """Registra un nuevo transportista"""
        try:
            id_transportista = f"TRANS-{self.almacen}-{len(self.transportistas) + 1:04d}"

            transportista = Transportista(
                id_transportista=id_transportista,
                nombre=nombre,
                rfc=rfc,
                telefono=telefono,
                tipo_vehiculo=tipo_vehiculo,
                **kwargs
            )

            self.transportistas[id_transportista] = transportista
            self._guardar_datos()

            logger.info(f"✅ Transportista registrado: {id_transportista} - {nombre}")

            return (True, f"✅ Transportista registrado: {id_transportista}", transportista)

        except Exception as e:
            logger.error(f"❌ Error al registrar transportista: {e}")
            return (False, f"❌ Error: {str(e)}", None)

    def actualizar_calificacion_transportista(
        self,
        transportista_id: str,
        nueva_calificacion: float,
        comentario: str = ""
    ) -> Tuple[bool, str]:
        """Actualiza la calificación de un transportista"""
        if transportista_id not in self.transportistas:
            return (False, f"❌ Transportista {transportista_id} no encontrado")

        trans = self.transportistas[transportista_id]
        calificacion_anterior = trans.calificacion

        # Promedio ponderado con historial
        peso_historial = min(trans.citas_completadas, 20) / 20  # Más peso con más historial
        trans.calificacion = (calificacion_anterior * peso_historial + nueva_calificacion * (1 - peso_historial))
        trans.calificacion = round(trans.calificacion, 2)

        if comentario:
            trans.metadata['ultimo_comentario'] = comentario
            trans.metadata['fecha_ultimo_comentario'] = datetime.now().isoformat()

        self._guardar_datos()

        logger.info(f"⭐ Calificación actualizada: {transportista_id} = {trans.calificacion}")

        return (True, f"✅ Calificación actualizada: {trans.calificacion}")

    def obtener_ranking_transportistas(self) -> List[Dict]:
        """Obtiene el ranking de transportistas por desempeño"""
        ranking = []

        for trans in self.transportistas.values():
            if not trans.activo:
                continue

            score = (
                trans.calificacion * 20 +  # Max 100 puntos
                trans.historico_puntualidad * 50 +  # Max 50 puntos
                min(trans.citas_completadas / 10, 10)  # Max 10 puntos
            )

            ranking.append({
                'id': trans.id_transportista,
                'nombre': trans.nombre,
                'calificacion': trans.calificacion,
                'puntualidad': f"{trans.historico_puntualidad*100:.1f}%",
                'citas_completadas': trans.citas_completadas,
                'score': round(score, 2)
            })

        ranking.sort(key=lambda x: x['score'], reverse=True)
        return ranking

    # ═══════════════════════════════════════════════════════════════════════════
    # GESTIÓN DE EQUIPOS
    # ═══════════════════════════════════════════════════════════════════════════

    def registrar_equipo(
        self,
        nombre: str,
        tipo: str,
        miembros: List[str],
        lider: str,
        turno: str = "MATUTINO",
        compuertas: List[int] = None
    ) -> Tuple[bool, str, Optional[EquipoOperativo]]:
        """Registra un nuevo equipo operativo"""
        try:
            id_equipo = f"EQ-{self.almacen}-{tipo[:3]}-{len(self.equipos) + 1:03d}"

            equipo = EquipoOperativo(
                id_equipo=id_equipo,
                nombre=nombre,
                tipo=tipo,
                miembros=miembros,
                lider=lider,
                turno=turno,
                compuertas_asignadas=compuertas or []
            )

            self.equipos[id_equipo] = equipo
            self._guardar_datos()

            logger.info(f"✅ Equipo registrado: {id_equipo} - {nombre}")

            return (True, f"✅ Equipo registrado: {id_equipo}", equipo)

        except Exception as e:
            logger.error(f"❌ Error al registrar equipo: {e}")
            return (False, f"❌ Error: {str(e)}", None)

    def asignar_equipo_a_cita(
        self,
        id_cita: str,
        id_equipo: str
    ) -> Tuple[bool, str]:
        """Asigna un equipo operativo a una cita"""
        if id_cita not in self.citas:
            return (False, f"❌ Cita {id_cita} no encontrada")

        if id_equipo not in self.equipos:
            return (False, f"❌ Equipo {id_equipo} no encontrado")

        equipo = self.equipos[id_equipo]
        cita = self.citas[id_cita]

        # Verificar compatibilidad de tipo
        if cita.tipo.value not in equipo.tipo:
            return (False, f"❌ El equipo {id_equipo} no es compatible con citas de {cita.tipo.value}")

        cita.equipo_asignado = id_equipo
        cita.ultima_modificacion = datetime.now()

        self._guardar_datos()

        logger.info(f"👥 Equipo {id_equipo} asignado a cita {id_cita}")

        return (True, f"✅ Equipo {equipo.nombre} asignado exitosamente")

    def obtener_carga_equipos(self, fecha: datetime = None) -> Dict[str, Dict]:
        """Obtiene la carga de trabajo actual de cada equipo"""
        fecha = fecha or datetime.now()
        carga = {}

        for equipo in self.equipos.values():
            if not equipo.activo:
                continue

            citas_asignadas = [
                c for c in self.citas.values()
                if c.equipo_asignado == equipo.id_equipo and
                c.fecha_programada.date() == fecha.date() and
                c.estado not in [EstadoCita.CANCELADA, EstadoCita.COMPLETADA]
            ]

            tarimas_totales = sum(c.cantidad_tarimas for c in citas_asignadas)
            tiempo_estimado_total = sum(c.tiempo_estimado_minutos for c in citas_asignadas)

            carga[equipo.id_equipo] = {
                'nombre': equipo.nombre,
                'tipo': equipo.tipo,
                'turno': equipo.turno,
                'miembros': len(equipo.miembros),
                'citas_asignadas': len(citas_asignadas),
                'tarimas_totales': tarimas_totales,
                'tiempo_estimado_minutos': tiempo_estimado_total,
                'capacidad_restante': max(0, 8 * 60 - tiempo_estimado_total),  # 8 horas de turno
                'porcentaje_ocupacion': min(100, (tiempo_estimado_total / (8 * 60)) * 100)
            }

        return carga

    def optimizar_asignacion_equipos(self, fecha: datetime = None) -> Dict[str, str]:
        """
        Optimiza la asignación de equipos a citas pendientes.

        Algoritmo:
        1. Obtiene citas sin equipo asignado
        2. Obtiene carga actual de cada equipo
        3. Asigna citas al equipo con menor carga compatible

        Returns:
            Dict con id_cita -> id_equipo asignado
        """
        fecha = fecha or datetime.now()
        asignaciones = {}

        # Obtener citas sin equipo
        citas_sin_equipo = [
            c for c in self.citas.values()
            if c.equipo_asignado is None and
            c.fecha_programada.date() == fecha.date() and
            c.estado not in [EstadoCita.CANCELADA, EstadoCita.COMPLETADA]
        ]

        if not citas_sin_equipo:
            return asignaciones

        # Ordenar por prioridad
        citas_sin_equipo.sort(key=lambda c: c.prioridad.value)

        for cita in citas_sin_equipo:
            # Buscar equipos compatibles
            equipos_compatibles = [
                e for e in self.equipos.values()
                if e.activo and cita.tipo.value in e.tipo
            ]

            if not equipos_compatibles:
                continue

            # Obtener carga actual
            carga = self.obtener_carga_equipos(fecha)

            # Seleccionar equipo con menor ocupación
            mejor_equipo = min(
                equipos_compatibles,
                key=lambda e: carga.get(e.id_equipo, {}).get('porcentaje_ocupacion', 100)
            )

            # Verificar que tiene capacidad
            carga_equipo = carga.get(mejor_equipo.id_equipo, {})
            if carga_equipo.get('porcentaje_ocupacion', 100) < 90:
                exito, _ = self.asignar_equipo_a_cita(cita.id_cita, mejor_equipo.id_equipo)
                if exito:
                    asignaciones[cita.id_cita] = mejor_equipo.id_equipo

        logger.info(f"🔄 Optimización completada: {len(asignaciones)} asignaciones realizadas")

        return asignaciones

    # ═══════════════════════════════════════════════════════════════════════════
    # DASHBOARD Y REPORTES
    # ═══════════════════════════════════════════════════════════════════════════

    def obtener_dashboard(self, fecha: datetime = None) -> Dict[str, Any]:
        """
        Genera un dashboard completo del estado de tráfico.

        Returns:
            Dict con métricas y estado actual
        """
        fecha = fecha or datetime.now()
        citas_dia = self.obtener_citas_dia(fecha)

        # Contar por estado
        conteo_estados = defaultdict(int)
        for cita in citas_dia:
            conteo_estados[cita.estado.value] += 1

        # Contar por tipo
        conteo_tipos = defaultdict(int)
        for cita in citas_dia:
            conteo_tipos[cita.tipo.value] += 1

        # Compuertas ocupadas
        compuertas_ocupadas = sum(
            1 for c in self.compuertas.values()
            if c.estado == EstadoCompuerta.OCUPADA
        )

        # Citas en proceso
        citas_en_proceso = [c for c in citas_dia if c.estado == EstadoCita.EN_PROCESO]

        # Citas retrasadas
        ahora = datetime.now()
        citas_retrasadas = []
        for cita in citas_dia:
            if cita.estado in [EstadoCita.PROGRAMADA, EstadoCita.CONFIRMADA]:
                programada = datetime.combine(cita.fecha_programada, cita.hora_programada)
                if ahora > programada + timedelta(minutes=15):
                    citas_retrasadas.append(cita)

        # Próximas citas
        proximas = sorted(
            [c for c in citas_dia if c.estado in [EstadoCita.PROGRAMADA, EstadoCita.CONFIRMADA, EstadoCita.EN_PATIO]],
            key=lambda c: c.hora_programada
        )[:5]

        dashboard = {
            'fecha': fecha.strftime('%Y-%m-%d'),
            'hora_actual': ahora.strftime('%H:%M'),
            'resumen': {
                'total_citas': len(citas_dia),
                'citas_recibo': conteo_tipos.get('RECIBO', 0),
                'citas_expedicion': conteo_tipos.get('EXPEDICION', 0),
                'completadas': conteo_estados.get('✅ COMPLETADA', 0),
                'en_proceso': len(citas_en_proceso),
                'retrasadas': len(citas_retrasadas),
                'canceladas': conteo_estados.get('❌ CANCELADA', 0)
            },
            'compuertas': {
                'total': len(self.compuertas),
                'ocupadas': compuertas_ocupadas,
                'disponibles': len(self.compuertas) - compuertas_ocupadas,
                'porcentaje_ocupacion': f"{(compuertas_ocupadas / len(self.compuertas)) * 100:.1f}%"
            },
            'proximas_citas': [
                {
                    'id': c.id_cita,
                    'hora': c.hora_programada.strftime('%H:%M'),
                    'tipo': c.tipo.value,
                    'compuerta': c.compuerta_asignada,
                    'transportista': c.transportista.nombre if c.transportista else 'N/A'
                } for c in proximas
            ],
            'alertas': [
                {
                    'id': c.id_cita,
                    'mensaje': f"Cita retrasada {int((ahora - datetime.combine(c.fecha_programada, c.hora_programada)).total_seconds()/60)} min"
                } for c in citas_retrasadas
            ],
            'metricas_ml': {
                'precision_modelo': f"{self.parametros_ml.precision_modelo:.1f}%",
                'muestras_aprendizaje': self.parametros_ml.total_muestras
            }
        }

        return dashboard

    def generar_reporte_diario(self, fecha: datetime = None) -> Dict[str, Any]:
        """Genera un reporte detallado del día"""
        fecha = fecha or datetime.now()
        citas_dia = self.obtener_citas_dia(fecha)

        completadas = [c for c in citas_dia if c.estado == EstadoCita.COMPLETADA]

        # Calcular métricas de rendimiento
        tiempos_reales = [c.tiempo_real_minutos for c in completadas if c.tiempo_real_minutos]
        tiempos_estimados = [c.tiempo_estimado_minutos for c in completadas if c.tiempo_real_minutos]

        desviaciones = []
        for c in completadas:
            if c.tiempo_real_minutos and c.tiempo_estimado_minutos:
                desv = ((c.tiempo_real_minutos - c.tiempo_estimado_minutos) / c.tiempo_estimado_minutos) * 100
                desviaciones.append(desv)

        # Puntualidad
        puntuales = sum(1 for c in completadas if c.hora_llegada_real and
                       (c.hora_llegada_real - datetime.combine(c.fecha_programada, c.hora_programada)).total_seconds() <= 900)

        reporte = {
            'fecha': fecha.strftime('%Y-%m-%d'),
            'generado': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'resumen_citas': {
                'total_programadas': len(citas_dia),
                'completadas': len(completadas),
                'canceladas': sum(1 for c in citas_dia if c.estado == EstadoCita.CANCELADA),
                'tasa_cumplimiento': f"{(len(completadas)/len(citas_dia)*100) if citas_dia else 0:.1f}%"
            },
            'metricas_tiempo': {
                'tiempo_promedio_real': f"{statistics.mean(tiempos_reales):.1f} min" if tiempos_reales else "N/A",
                'tiempo_promedio_estimado': f"{statistics.mean(tiempos_estimados):.1f} min" if tiempos_estimados else "N/A",
                'desviacion_promedio': f"{statistics.mean(desviaciones):.1f}%" if desviaciones else "N/A",
                'precision_estimacion': f"{100 - abs(statistics.mean(desviaciones)):.1f}%" if desviaciones else "N/A"
            },
            'metricas_puntualidad': {
                'citas_puntuales': puntuales,
                'tasa_puntualidad': f"{(puntuales/len(completadas)*100) if completadas else 0:.1f}%"
            },
            'por_circuito': {},
            'por_compuerta': {},
            'tarimas_procesadas': sum(c.cantidad_tarimas for c in completadas)
        }

        # Agregar estadísticas por circuito
        for circuito in CIRCUITOS_DISPONIBLES:
            citas_circ = [c for c in completadas if c.circuito_asignado == circuito]
            if citas_circ:
                reporte['por_circuito'][circuito] = {
                    'citas': len(citas_circ),
                    'tarimas': sum(c.cantidad_tarimas for c in citas_circ)
                }

        return reporte

    # ═══════════════════════════════════════════════════════════════════════════
    # PERSISTENCIA DE DATOS
    # ═══════════════════════════════════════════════════════════════════════════

    def _guardar_datos(self) -> None:
        """Guarda todos los datos en archivos"""
        try:
            # Guardar citas
            citas_data = {k: self._cita_to_dict(v) for k, v in self.citas.items()}
            with open(self.ruta_datos / 'citas.json', 'w', encoding='utf-8') as f:
                json.dump(citas_data, f, ensure_ascii=False, indent=2, default=str)

            # Guardar transportistas
            trans_data = {k: self._transportista_to_dict(v) for k, v in self.transportistas.items()}
            with open(self.ruta_datos / 'transportistas.json', 'w', encoding='utf-8') as f:
                json.dump(trans_data, f, ensure_ascii=False, indent=2, default=str)

            # Guardar equipos
            equipos_data = {k: self._equipo_to_dict(v) for k, v in self.equipos.items()}
            with open(self.ruta_datos / 'equipos.json', 'w', encoding='utf-8') as f:
                json.dump(equipos_data, f, ensure_ascii=False, indent=2, default=str)

            # Guardar parámetros ML
            ml_data = {
                'factor_tiempo_descarga': self.parametros_ml.factor_tiempo_descarga,
                'factor_tiempo_carga': self.parametros_ml.factor_tiempo_carga,
                'factor_setup': self.parametros_ml.factor_setup,
                'factores_por_transportista': self.parametros_ml.factores_por_transportista,
                'factores_por_compuerta': {str(k): v for k, v in self.parametros_ml.factores_por_compuerta.items()},
                'factores_por_circuito': {str(k): v for k, v in self.parametros_ml.factores_por_circuito.items()},
                'factores_por_hora': {str(k): v for k, v in self.parametros_ml.factores_por_hora.items()},
                'factores_por_dia_semana': {str(k): v for k, v in self.parametros_ml.factores_por_dia_semana.items()},
                'ultima_actualizacion': self.parametros_ml.ultima_actualizacion.isoformat(),
                'total_muestras': self.parametros_ml.total_muestras,
                'precision_modelo': self.parametros_ml.precision_modelo
            }
            with open(self.ruta_datos / 'parametros_ml.json', 'w', encoding='utf-8') as f:
                json.dump(ml_data, f, ensure_ascii=False, indent=2)

            # Guardar métricas históricas (últimas 1000)
            metricas_data = [self._metrica_to_dict(m) for m in self.historico_metricas[-1000:]]
            with open(self.ruta_datos / 'historico_metricas.json', 'w', encoding='utf-8') as f:
                json.dump(metricas_data, f, ensure_ascii=False, indent=2, default=str)

            logger.debug("💾 Datos guardados exitosamente")

        except Exception as e:
            logger.error(f"❌ Error al guardar datos: {e}")

    def _cargar_datos(self) -> None:
        """Carga los datos desde archivos"""
        try:
            # Cargar citas
            citas_file = self.ruta_datos / 'citas.json'
            if citas_file.exists():
                with open(citas_file, 'r', encoding='utf-8') as f:
                    citas_data = json.load(f)
                    self.citas = {k: self._dict_to_cita(v) for k, v in citas_data.items()}

            # Cargar transportistas
            trans_file = self.ruta_datos / 'transportistas.json'
            if trans_file.exists():
                with open(trans_file, 'r', encoding='utf-8') as f:
                    trans_data = json.load(f)
                    self.transportistas = {k: self._dict_to_transportista(v) for k, v in trans_data.items()}

            # Cargar equipos
            equipos_file = self.ruta_datos / 'equipos.json'
            if equipos_file.exists():
                with open(equipos_file, 'r', encoding='utf-8') as f:
                    equipos_data = json.load(f)
                    self.equipos = {k: self._dict_to_equipo(v) for k, v in equipos_data.items()}

            # Cargar parámetros ML
            ml_file = self.ruta_datos / 'parametros_ml.json'
            if ml_file.exists():
                with open(ml_file, 'r', encoding='utf-8') as f:
                    ml_data = json.load(f)
                    self.parametros_ml.factor_tiempo_descarga = ml_data.get('factor_tiempo_descarga', 1.0)
                    self.parametros_ml.factor_tiempo_carga = ml_data.get('factor_tiempo_carga', 1.0)
                    self.parametros_ml.factor_setup = ml_data.get('factor_setup', 1.0)
                    self.parametros_ml.factores_por_transportista = ml_data.get('factores_por_transportista', {})
                    self.parametros_ml.factores_por_compuerta = {int(k): v for k, v in ml_data.get('factores_por_compuerta', {}).items()}
                    self.parametros_ml.factores_por_circuito = {int(k): v for k, v in ml_data.get('factores_por_circuito', {}).items()}
                    self.parametros_ml.factores_por_hora = {int(k): v for k, v in ml_data.get('factores_por_hora', {}).items()}
                    self.parametros_ml.factores_por_dia_semana = {int(k): v for k, v in ml_data.get('factores_por_dia_semana', {}).items()}
                    self.parametros_ml.total_muestras = ml_data.get('total_muestras', 0)
                    self.parametros_ml.precision_modelo = ml_data.get('precision_modelo', 0.0)

            # Cargar métricas históricas
            metricas_file = self.ruta_datos / 'historico_metricas.json'
            if metricas_file.exists():
                with open(metricas_file, 'r', encoding='utf-8') as f:
                    metricas_data = json.load(f)
                    self.historico_metricas = [self._dict_to_metrica(m) for m in metricas_data]

            logger.info(f"📂 Datos cargados: {len(self.citas)} citas, {len(self.transportistas)} transportistas")

        except Exception as e:
            logger.warning(f"⚠️ No se pudieron cargar datos previos: {e}")

    # Métodos de conversión para serialización
    def _cita_to_dict(self, cita: CitaTrafico) -> Dict:
        return {
            'id_cita': cita.id_cita,
            'tipo': cita.tipo.value,
            'estado': cita.estado.value,
            'fecha_programada': cita.fecha_programada.isoformat() if isinstance(cita.fecha_programada, datetime) else str(cita.fecha_programada),
            'hora_programada': cita.hora_programada.isoformat() if isinstance(cita.hora_programada, time) else str(cita.hora_programada),
            'hora_llegada_real': cita.hora_llegada_real.isoformat() if cita.hora_llegada_real else None,
            'hora_inicio_operacion': cita.hora_inicio_operacion.isoformat() if cita.hora_inicio_operacion else None,
            'hora_fin_operacion': cita.hora_fin_operacion.isoformat() if cita.hora_fin_operacion else None,
            'transportista_id': cita.transportista.id_transportista if cita.transportista else None,
            'tipo_vehiculo': cita.tipo_vehiculo,
            'placas': cita.placas,
            'operador': cita.operador,
            'compuerta_asignada': cita.compuerta_asignada,
            'circuito_asignado': cita.circuito_asignado,
            'equipo_asignado': cita.equipo_asignado,
            'numero_oc': cita.numero_oc,
            'numero_asn': cita.numero_asn,
            'cantidad_tarimas': cita.cantidad_tarimas,
            'cantidad_cajas': cita.cantidad_cajas,
            'peso_kg': cita.peso_kg,
            'tiendas_destino': cita.tiendas_destino,
            'tiempo_estimado_minutos': cita.tiempo_estimado_minutos,
            'tiempo_real_minutos': cita.tiempo_real_minutos,
            'prioridad': cita.prioridad.value,
            'notas': cita.notas,
            'alertas': cita.alertas,
            'creado_por': cita.creado_por,
            'fecha_creacion': cita.fecha_creacion.isoformat(),
            'ultima_modificacion': cita.ultima_modificacion.isoformat(),
            'metadata': cita.metadata
        }

    def _dict_to_cita(self, data: Dict) -> CitaTrafico:
        transportista = self.transportistas.get(data.get('transportista_id')) if data.get('transportista_id') else None

        return CitaTrafico(
            id_cita=data['id_cita'],
            tipo=TipoCita(data['tipo']),
            estado=EstadoCita(data['estado']),
            fecha_programada=datetime.fromisoformat(data['fecha_programada']) if data['fecha_programada'] else datetime.now(),
            hora_programada=time.fromisoformat(data['hora_programada']) if data['hora_programada'] else time(8, 0),
            hora_llegada_real=datetime.fromisoformat(data['hora_llegada_real']) if data.get('hora_llegada_real') else None,
            hora_inicio_operacion=datetime.fromisoformat(data['hora_inicio_operacion']) if data.get('hora_inicio_operacion') else None,
            hora_fin_operacion=datetime.fromisoformat(data['hora_fin_operacion']) if data.get('hora_fin_operacion') else None,
            transportista=transportista,
            tipo_vehiculo=data.get('tipo_vehiculo', 'trailer_48'),
            placas=data.get('placas', ''),
            operador=data.get('operador', ''),
            compuerta_asignada=data.get('compuerta_asignada'),
            circuito_asignado=data.get('circuito_asignado'),
            equipo_asignado=data.get('equipo_asignado'),
            numero_oc=data.get('numero_oc'),
            numero_asn=data.get('numero_asn'),
            cantidad_tarimas=data.get('cantidad_tarimas', 0),
            cantidad_cajas=data.get('cantidad_cajas', 0),
            peso_kg=data.get('peso_kg', 0.0),
            tiendas_destino=data.get('tiendas_destino', []),
            tiempo_estimado_minutos=data.get('tiempo_estimado_minutos', 60),
            tiempo_real_minutos=data.get('tiempo_real_minutos'),
            prioridad=PrioridadCita(data.get('prioridad', 3)),
            notas=data.get('notas', ''),
            alertas=data.get('alertas', []),
            creado_por=data.get('creado_por', 'SISTEMA'),
            fecha_creacion=datetime.fromisoformat(data['fecha_creacion']) if data.get('fecha_creacion') else datetime.now(),
            ultima_modificacion=datetime.fromisoformat(data['ultima_modificacion']) if data.get('ultima_modificacion') else datetime.now(),
            metadata=data.get('metadata', {})
        )

    def _transportista_to_dict(self, trans: Transportista) -> Dict:
        return {
            'id_transportista': trans.id_transportista,
            'nombre': trans.nombre,
            'rfc': trans.rfc,
            'telefono': trans.telefono,
            'email': trans.email,
            'tipo_vehiculo': trans.tipo_vehiculo,
            'placas': trans.placas,
            'nombre_operador': trans.nombre_operador,
            'licencia_operador': trans.licencia_operador,
            'calificacion': trans.calificacion,
            'historico_puntualidad': trans.historico_puntualidad,
            'citas_completadas': trans.citas_completadas,
            'tiempo_promedio_descarga': trans.tiempo_promedio_descarga,
            'activo': trans.activo,
            'metadata': trans.metadata
        }

    def _dict_to_transportista(self, data: Dict) -> Transportista:
        return Transportista(**data)

    def _equipo_to_dict(self, equipo: EquipoOperativo) -> Dict:
        return {
            'id_equipo': equipo.id_equipo,
            'nombre': equipo.nombre,
            'tipo': equipo.tipo,
            'miembros': equipo.miembros,
            'lider': equipo.lider,
            'turno': equipo.turno,
            'zona_asignada': equipo.zona_asignada,
            'compuertas_asignadas': equipo.compuertas_asignadas,
            'capacidad_tarimas_hora': equipo.capacidad_tarimas_hora,
            'activo': equipo.activo,
            'eficiencia_promedio': equipo.eficiencia_promedio
        }

    def _dict_to_equipo(self, data: Dict) -> EquipoOperativo:
        return EquipoOperativo(**data)

    def _metrica_to_dict(self, metrica: MetricasRendimiento) -> Dict:
        return {
            'fecha': metrica.fecha.isoformat(),
            'tipo_operacion': metrica.tipo_operacion.value,
            'transportista_id': metrica.transportista_id,
            'compuerta': metrica.compuerta,
            'circuito': metrica.circuito,
            'tipo_vehiculo': metrica.tipo_vehiculo,
            'cantidad_tarimas': metrica.cantidad_tarimas,
            'tiempo_estimado': metrica.tiempo_estimado,
            'tiempo_real': metrica.tiempo_real,
            'desviacion_porcentaje': metrica.desviacion_porcentaje,
            'hora_llegada': metrica.hora_llegada.isoformat(),
            'puntualidad': metrica.puntualidad,
            'equipo_id': metrica.equipo_id,
            'condiciones': metrica.condiciones
        }

    def _dict_to_metrica(self, data: Dict) -> MetricasRendimiento:
        return MetricasRendimiento(
            fecha=datetime.fromisoformat(data['fecha']),
            tipo_operacion=TipoCita(data['tipo_operacion']),
            transportista_id=data['transportista_id'],
            compuerta=data['compuerta'],
            circuito=data['circuito'],
            tipo_vehiculo=data['tipo_vehiculo'],
            cantidad_tarimas=data['cantidad_tarimas'],
            tiempo_estimado=data['tiempo_estimado'],
            tiempo_real=data['tiempo_real'],
            desviacion_porcentaje=data['desviacion_porcentaje'],
            hora_llegada=datetime.fromisoformat(data['hora_llegada']),
            puntualidad=data['puntualidad'],
            equipo_id=data['equipo_id'],
            condiciones=data.get('condiciones', {})
        )


# ═══════════════════════════════════════════════════════════════════════════════
# CLASE PARA VISIÓN CON CÁMARAS (PLACEHOLDER PARA FUTURO)
# ═══════════════════════════════════════════════════════════════════════════════

class MonitorVisionTrafico:
    """
    Placeholder para futuro sistema de monitoreo con visión por cámaras.

    Esta clase será implementada cuando se integre un LLM con capacidades de visión
    para monitorear:
    - Estado de patio y compuertas
    - Detección de vehículos
    - Lectura automática de placas
    - Monitoreo de seguridad
    """

    def __init__(self, gestor_trafico: GestorControlTrafico):
        self.gestor = gestor_trafico
        self.camaras_configuradas: Dict[str, Dict] = {}
        self.ultimo_analisis: Optional[datetime] = None
        logger.info("📷 Monitor de visión inicializado (en desarrollo)")

    def configurar_camara(
        self,
        id_camara: str,
        ubicacion: str,
        tipo: str,
        url_stream: Optional[str] = None
    ) -> bool:
        """Configura una cámara para monitoreo"""
        self.camaras_configuradas[id_camara] = {
            'ubicacion': ubicacion,
            'tipo': tipo,  # 'PATIO', 'COMPUERTA', 'SEGURIDAD'
            'url_stream': url_stream,
            'activa': False,
            'ultimo_frame': None
        }
        logger.info(f"📷 Cámara {id_camara} configurada en {ubicacion}")
        return True

    def analizar_imagen(self, id_camara: str, imagen_path: str) -> Dict[str, Any]:
        """
        Placeholder para análisis de imagen con LLM de visión.

        En el futuro, esta función:
        1. Enviará la imagen a un LLM con visión (Claude, GPT-4V, etc.)
        2. Analizará el contenido para detectar:
           - Vehículos presentes
           - Estado de compuertas
           - Actividad en patio
           - Posibles alertas de seguridad
        3. Actualizará el estado del gestor de tráfico
        """
        logger.info(f"📷 Análisis de imagen pendiente de implementación")
        return {
            'status': 'not_implemented',
            'message': 'La integración con LLM de visión está pendiente de implementación',
            'camara': id_camara,
            'imagen': imagen_path
        }

    def obtener_estado_camaras(self) -> Dict[str, Dict]:
        """Obtiene el estado actual de todas las cámaras"""
        return self.camaras_configuradas


# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIONES DE UTILIDAD
# ═══════════════════════════════════════════════════════════════════════════════

def crear_gestor_trafico(almacen: str = ALMACEN_427) -> GestorControlTrafico:
    """Factory function para crear el gestor de tráfico"""
    return GestorControlTrafico(almacen=almacen)


def demo_control_trafico():
    """Demostración del sistema de control de tráfico"""
    print("\n" + "═" * 70)
    print("🚛 DEMOSTRACIÓN - SISTEMA DE CONTROL DE TRÁFICO CEDIS 427")
    print("═" * 70)

    # Crear gestor
    gestor = crear_gestor_trafico()

    # Registrar un transportista de ejemplo
    exito, msg, transportista = gestor.registrar_transportista(
        nombre="Transportes del Sureste SA",
        rfc="TSU850101ABC",
        telefono="9981234567",
        tipo_vehiculo="trailer_48"
    )
    print(f"\n📋 {msg}")

    # Registrar un equipo de ejemplo
    exito, msg, equipo = gestor.registrar_equipo(
        nombre="Equipo Recibo A",
        tipo="RECIBO",
        miembros=["Juan Pérez", "María García", "Carlos López"],
        lider="Juan Pérez",
        turno="MATUTINO",
        compuertas=[1, 2, 3, 4, 5]
    )
    print(f"👥 {msg}")

    # Crear una cita de ejemplo
    fecha_cita = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)
    exito, msg, cita = gestor.crear_cita(
        tipo=TipoCita.RECIBO,
        fecha=fecha_cita,
        hora=time(10, 0),
        transportista_id=transportista.id_transportista if transportista else None,
        numero_oc="OC12345678",
        cantidad_tarimas=48,
        prioridad=PrioridadCita.NORMAL,
        tipo_vehiculo="trailer_48",
        notas="Cita de demostración"
    )
    print(f"\n📅 {msg}")

    if cita:
        print(f"   • Compuerta asignada: {cita.compuerta_asignada}")
        print(f"   • Tiempo estimado: {cita.tiempo_estimado_minutos} minutos")

    # Mostrar dashboard
    dashboard = gestor.obtener_dashboard()
    print(f"\n📊 DASHBOARD:")
    print(f"   • Total citas hoy: {dashboard['resumen']['total_citas']}")
    print(f"   • Compuertas disponibles: {dashboard['compuertas']['disponibles']}/{dashboard['compuertas']['total']}")
    print(f"   • Precisión del modelo: {dashboard['metricas_ml']['precision_modelo']}")

    # Mostrar estadísticas del modelo
    stats = gestor.obtener_estadisticas_modelo()
    print(f"\n🧠 MODELO DE APRENDIZAJE:")
    print(f"   • Total muestras: {stats.get('total_muestras', 0)}")
    print(f"   • Estado: {'Activo' if stats.get('total_muestras', 0) >= 5 else 'Recopilando datos...'}")

    print("\n" + "═" * 70)
    print("✅ Demostración completada")
    print("═" * 70)


# ═══════════════════════════════════════════════════════════════════════════════
# PUNTO DE ENTRADA
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    demo_control_trafico()
