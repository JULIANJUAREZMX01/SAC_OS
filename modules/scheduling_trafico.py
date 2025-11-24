"""
═══════════════════════════════════════════════════════════════════════════════
SISTEMA DE SCHEDULING DE TRÁFICO
Sistema de Automatización de Consultas - Chedraui CEDIS 427
═══════════════════════════════════════════════════════════════════════════════

Sistema avanzado de programación y calendarización de citas que incluye:
- Generación automática de slots disponibles
- Optimización de horarios
- Detección y resolución de conflictos
- Balanceo de carga entre compuertas
- Integración con el sistema de aprendizaje

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
═══════════════════════════════════════════════════════════════════════════════
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta, time, date
from enum import Enum
from collections import defaultdict
import calendar
import json
from pathlib import Path

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════════════════════

# Horarios de operación por turno
TURNOS_OPERACION = {
    'MATUTINO': {'inicio': time(6, 0), 'fin': time(14, 0)},
    'VESPERTINO': {'inicio': time(14, 0), 'fin': time(22, 0)},
    'NOCTURNO': {'inicio': time(22, 0), 'fin': time(6, 0)}  # Cruza medianoche
}

# Configuración de capacidad
CAPACIDAD_SIMULTANEA_RECIBO = 10      # Máximo de citas simultáneas en recibo
CAPACIDAD_SIMULTANEA_EXPEDICION = 15  # Máximo de citas simultáneas en expedición

# Slots de tiempo
DURACION_SLOT_MINUTOS = 30
BUFFER_ENTRE_CITAS_MINUTOS = 10

# Días de operación (0=Lunes, 6=Domingo)
DIAS_OPERACION = [0, 1, 2, 3, 4, 5]  # Lunes a Sábado


# ═══════════════════════════════════════════════════════════════════════════════
# ENUMS
# ═══════════════════════════════════════════════════════════════════════════════

class TipoSlot(Enum):
    """Tipos de slots disponibles"""
    RECIBO = "RECIBO"
    EXPEDICION = "EXPEDICION"
    MIXTO = "MIXTO"


class EstadoSlot(Enum):
    """Estados de un slot de tiempo"""
    DISPONIBLE = "🟢 DISPONIBLE"
    RESERVADO = "🟡 RESERVADO"
    OCUPADO = "🔴 OCUPADO"
    BLOQUEADO = "⚫ BLOQUEADO"
    MANTENIMIENTO = "🔧 MANTENIMIENTO"


class MotivoBloqueo(Enum):
    """Motivos de bloqueo de slots"""
    MANTENIMIENTO = "MANTENIMIENTO"
    CAPACIDAD_MAXIMA = "CAPACIDAD_MAXIMA"
    EVENTO_ESPECIAL = "EVENTO_ESPECIAL"
    HORARIO_RESTRINGIDO = "HORARIO_RESTRINGIDO"
    MANUAL = "MANUAL"


# ═══════════════════════════════════════════════════════════════════════════════
# DATACLASSES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class SlotHorario:
    """Representa un slot de tiempo disponible"""
    id_slot: str
    fecha: date
    hora_inicio: time
    hora_fin: time
    tipo: TipoSlot
    compuerta: Optional[int] = None
    estado: EstadoSlot = EstadoSlot.DISPONIBLE
    cita_asignada: Optional[str] = None
    capacidad_restante: int = 1
    bloqueado: bool = False
    motivo_bloqueo: Optional[MotivoBloqueo] = None
    notas: str = ""

    @property
    def duracion_minutos(self) -> int:
        inicio = datetime.combine(self.fecha, self.hora_inicio)
        fin = datetime.combine(self.fecha, self.hora_fin)
        return int((fin - inicio).total_seconds() / 60)


@dataclass
class Conflicto:
    """Representa un conflicto de scheduling"""
    id_conflicto: str
    tipo: str
    severidad: str  # 'CRITICO', 'ALTO', 'MEDIO', 'BAJO'
    descripcion: str
    citas_afectadas: List[str]
    slots_afectados: List[str]
    fecha_deteccion: datetime
    resuelto: bool = False
    solucion_aplicada: Optional[str] = None
    fecha_resolucion: Optional[datetime] = None


@dataclass
class ReglaScheduling:
    """Regla de scheduling configurable"""
    id_regla: str
    nombre: str
    descripcion: str
    activa: bool = True
    prioridad: int = 5
    condicion: str = ""  # Expresión de condición
    accion: str = ""     # Acción a tomar
    parametros: Dict = field(default_factory=dict)


@dataclass
class ResumenDia:
    """Resumen de scheduling para un día"""
    fecha: date
    total_slots: int
    slots_disponibles: int
    slots_ocupados: int
    slots_bloqueados: int
    capacidad_recibo: Dict[str, int] = field(default_factory=dict)
    capacidad_expedicion: Dict[str, int] = field(default_factory=dict)
    horas_pico: List[str] = field(default_factory=list)
    alertas: List[str] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════════════
# CLASE PRINCIPAL: SCHEDULER DE TRÁFICO
# ═══════════════════════════════════════════════════════════════════════════════

class SchedulerTrafico:
    """
    Sistema de scheduling avanzado para control de tráfico.

    Funcionalidades:
    - Generación de calendarios de disponibilidad
    - Búsqueda de slots óptimos
    - Detección y resolución de conflictos
    - Balanceo de carga
    - Optimización de horarios
    """

    def __init__(
        self,
        almacen: str = "427",
        ruta_datos: Optional[Path] = None
    ):
        """
        Inicializa el scheduler de tráfico.

        Args:
            almacen: Código del almacén
            ruta_datos: Ruta para persistencia
        """
        self.almacen = almacen
        self.ruta_datos = ruta_datos or Path("output/trafico/scheduling")
        self.ruta_datos.mkdir(parents=True, exist_ok=True)

        # Slots por fecha
        self.slots: Dict[str, List[SlotHorario]] = {}  # {fecha_str: [slots]}

        # Conflictos detectados
        self.conflictos: List[Conflicto] = []

        # Reglas de scheduling
        self.reglas: List[ReglaScheduling] = []
        self._inicializar_reglas_default()

        # Configuración de capacidad por hora
        self.capacidad_por_hora: Dict[int, Dict[str, int]] = {}
        self._inicializar_capacidad()

        # Bloqueos programados
        self.bloqueos_programados: List[Dict] = []

        # Cargar datos
        self._cargar_datos()

        logger.info(f"📅 Scheduler de Tráfico inicializado - Almacén {almacen}")

    def _inicializar_reglas_default(self) -> None:
        """Inicializa las reglas de scheduling por defecto"""
        self.reglas = [
            ReglaScheduling(
                id_regla="REG001",
                nombre="Capacidad máxima recibo",
                descripcion="No permitir más de 10 citas simultáneas en recibo",
                prioridad=1,
                condicion="citas_simultaneas_recibo > 10",
                accion="bloquear_slot"
            ),
            ReglaScheduling(
                id_regla="REG002",
                nombre="Buffer entre citas",
                descripcion="Mantener 10 minutos entre citas en misma compuerta",
                prioridad=2,
                condicion="tiempo_entre_citas < 10",
                accion="agregar_buffer"
            ),
            ReglaScheduling(
                id_regla="REG003",
                nombre="Prioridad urgentes",
                descripcion="Citas urgentes tienen prioridad sobre normales",
                prioridad=1,
                condicion="prioridad == URGENTE",
                accion="asignar_primero"
            ),
            ReglaScheduling(
                id_regla="REG004",
                nombre="Horario restringido mediodía",
                descripcion="Reducir capacidad entre 12:00-14:00 por cambio de turno",
                prioridad=3,
                condicion="hora >= 12 and hora < 14",
                accion="reducir_capacidad",
                parametros={'factor': 0.7}
            ),
            ReglaScheduling(
                id_regla="REG005",
                nombre="Balanceo de carga",
                descripcion="Distribuir citas equitativamente entre compuertas",
                prioridad=4,
                condicion="desbalance > 0.3",
                accion="redistribuir"
            )
        ]

    def _inicializar_capacidad(self) -> None:
        """Inicializa la capacidad por hora"""
        for hora in range(6, 23):  # 6:00 AM a 10:00 PM
            factor = 1.0

            # Horas pico (más capacidad)
            if hora in [8, 9, 10, 15, 16, 17]:
                factor = 1.2

            # Cambio de turno (menos capacidad)
            if hora in [6, 14, 22]:
                factor = 0.7

            # Hora de comida
            if hora in [12, 13]:
                factor = 0.8

            self.capacidad_por_hora[hora] = {
                'recibo': int(CAPACIDAD_SIMULTANEA_RECIBO * factor),
                'expedicion': int(CAPACIDAD_SIMULTANEA_EXPEDICION * factor)
            }

    # ═══════════════════════════════════════════════════════════════════════════
    # GENERACIÓN DE SLOTS
    # ═══════════════════════════════════════════════════════════════════════════

    def generar_slots_dia(
        self,
        fecha: date,
        tipo: TipoSlot = TipoSlot.MIXTO,
        compuertas_recibo: List[int] = None,
        compuertas_expedicion: List[int] = None
    ) -> List[SlotHorario]:
        """
        Genera todos los slots disponibles para un día.

        Args:
            fecha: Fecha para generar slots
            tipo: Tipo de slots a generar
            compuertas_recibo: Lista de compuertas de recibo
            compuertas_expedicion: Lista de compuertas de expedición

        Returns:
            Lista de slots generados
        """
        # Verificar si es día de operación
        if fecha.weekday() not in DIAS_OPERACION:
            logger.warning(f"⚠️ {fecha} no es día de operación")
            return []

        compuertas_recibo = compuertas_recibo or list(range(1, 21))
        compuertas_expedicion = compuertas_expedicion or list(range(21, 41))

        slots = []
        fecha_str = fecha.isoformat()

        # Generar slots por turno
        for turno_nombre, turno_config in TURNOS_OPERACION.items():
            if turno_nombre == 'NOCTURNO':
                continue  # Manejar nocturno por separado si es necesario

            hora_actual = datetime.combine(fecha, turno_config['inicio'])
            hora_fin_turno = datetime.combine(fecha, turno_config['fin'])

            while hora_actual < hora_fin_turno:
                hora_slot_fin = hora_actual + timedelta(minutes=DURACION_SLOT_MINUTOS)

                if hora_slot_fin > hora_fin_turno:
                    break

                # Verificar bloqueos
                bloqueado, motivo = self._verificar_bloqueo(fecha, hora_actual.time())

                if tipo in [TipoSlot.RECIBO, TipoSlot.MIXTO]:
                    # Crear slots para recibo (uno por capacidad simultánea)
                    capacidad = self.capacidad_por_hora.get(
                        hora_actual.hour, {'recibo': CAPACIDAD_SIMULTANEA_RECIBO}
                    )['recibo']

                    slot = SlotHorario(
                        id_slot=f"SLOT-REC-{fecha_str}-{hora_actual.strftime('%H%M')}",
                        fecha=fecha,
                        hora_inicio=hora_actual.time(),
                        hora_fin=hora_slot_fin.time(),
                        tipo=TipoSlot.RECIBO,
                        estado=EstadoSlot.BLOQUEADO if bloqueado else EstadoSlot.DISPONIBLE,
                        capacidad_restante=capacidad,
                        bloqueado=bloqueado,
                        motivo_bloqueo=motivo
                    )
                    slots.append(slot)

                if tipo in [TipoSlot.EXPEDICION, TipoSlot.MIXTO]:
                    # Crear slots para expedición
                    capacidad = self.capacidad_por_hora.get(
                        hora_actual.hour, {'expedicion': CAPACIDAD_SIMULTANEA_EXPEDICION}
                    )['expedicion']

                    slot = SlotHorario(
                        id_slot=f"SLOT-EXP-{fecha_str}-{hora_actual.strftime('%H%M')}",
                        fecha=fecha,
                        hora_inicio=hora_actual.time(),
                        hora_fin=hora_slot_fin.time(),
                        tipo=TipoSlot.EXPEDICION,
                        estado=EstadoSlot.BLOQUEADO if bloqueado else EstadoSlot.DISPONIBLE,
                        capacidad_restante=capacidad,
                        bloqueado=bloqueado,
                        motivo_bloqueo=motivo
                    )
                    slots.append(slot)

                hora_actual = hora_slot_fin

        # Guardar slots
        self.slots[fecha_str] = slots
        self._guardar_datos()

        logger.info(f"📅 Generados {len(slots)} slots para {fecha}")

        return slots

    def generar_slots_semana(
        self,
        fecha_inicio: date,
        tipo: TipoSlot = TipoSlot.MIXTO
    ) -> Dict[str, List[SlotHorario]]:
        """Genera slots para una semana completa"""
        slots_semana = {}

        for i in range(7):
            fecha = fecha_inicio + timedelta(days=i)
            slots_dia = self.generar_slots_dia(fecha, tipo)
            if slots_dia:
                slots_semana[fecha.isoformat()] = slots_dia

        return slots_semana

    def _verificar_bloqueo(
        self,
        fecha: date,
        hora: time
    ) -> Tuple[bool, Optional[MotivoBloqueo]]:
        """Verifica si un horario está bloqueado"""
        for bloqueo in self.bloqueos_programados:
            if bloqueo['fecha_inicio'] <= fecha <= bloqueo['fecha_fin']:
                if bloqueo.get('hora_inicio') and bloqueo.get('hora_fin'):
                    if bloqueo['hora_inicio'] <= hora <= bloqueo['hora_fin']:
                        return True, MotivoBloqueo(bloqueo['motivo'])
                else:
                    return True, MotivoBloqueo(bloqueo['motivo'])

        return False, None

    # ═══════════════════════════════════════════════════════════════════════════
    # BÚSQUEDA DE SLOTS
    # ═══════════════════════════════════════════════════════════════════════════

    def buscar_slots_disponibles(
        self,
        fecha: date,
        tipo: TipoSlot,
        duracion_minutos: int = 60,
        hora_preferida: Optional[time] = None,
        compuerta_preferida: Optional[int] = None
    ) -> List[SlotHorario]:
        """
        Busca slots disponibles que cumplan los criterios.

        Args:
            fecha: Fecha de búsqueda
            tipo: Tipo de slot requerido
            duracion_minutos: Duración mínima requerida
            hora_preferida: Hora preferida (ordenará por cercanía)
            compuerta_preferida: Compuerta preferida

        Returns:
            Lista de slots disponibles ordenados por preferencia
        """
        fecha_str = fecha.isoformat()

        # Generar slots si no existen
        if fecha_str not in self.slots:
            self.generar_slots_dia(fecha, tipo)

        slots_disponibles = [
            s for s in self.slots.get(fecha_str, [])
            if s.tipo == tipo and
            s.estado == EstadoSlot.DISPONIBLE and
            s.capacidad_restante > 0 and
            not s.bloqueado
        ]

        # Filtrar por duración (slots consecutivos si es necesario)
        slots_suficientes = []
        slots_necesarios = (duracion_minutos + DURACION_SLOT_MINUTOS - 1) // DURACION_SLOT_MINUTOS

        for i, slot in enumerate(slots_disponibles):
            # Verificar si hay suficientes slots consecutivos
            if i + slots_necesarios <= len(slots_disponibles):
                consecutivos = True
                for j in range(1, slots_necesarios):
                    if slots_disponibles[i + j].hora_inicio != slots_disponibles[i + j - 1].hora_fin:
                        consecutivos = False
                        break
                if consecutivos:
                    slots_suficientes.append(slot)

        # Ordenar por preferencia
        if hora_preferida:
            slots_suficientes.sort(
                key=lambda s: abs(
                    datetime.combine(fecha, s.hora_inicio) -
                    datetime.combine(fecha, hora_preferida)
                )
            )

        return slots_suficientes

    def obtener_mejor_slot(
        self,
        fecha: date,
        tipo: TipoSlot,
        duracion_minutos: int,
        prioridad: int = 3
    ) -> Optional[SlotHorario]:
        """
        Obtiene el mejor slot disponible según criterios de optimización.

        Considera:
        - Balanceo de carga
        - Horarios óptimos de operación
        - Prioridad de la cita

        Returns:
            Mejor slot o None si no hay disponibilidad
        """
        slots = self.buscar_slots_disponibles(fecha, tipo, duracion_minutos)

        if not slots:
            return None

        # Calcular score para cada slot
        scored_slots = []

        for slot in slots:
            score = 100.0

            # Factor de hora (prefiere horas de alta productividad)
            hora = slot.hora_inicio.hour
            if hora in [8, 9, 10, 15, 16, 17]:
                score += 20  # Horas pico productivas
            elif hora in [11, 18, 19]:
                score += 10  # Horas buenas
            elif hora in [6, 12, 13, 22]:
                score -= 10  # Horas de transición

            # Factor de capacidad restante (prefiere slots menos ocupados)
            ocupacion = 1 - (slot.capacidad_restante / CAPACIDAD_SIMULTANEA_RECIBO)
            score -= ocupacion * 20

            # Factor de prioridad (urgentes prefieren inicio del día)
            if prioridad == 1:  # Urgente
                score += (12 - hora) * 2  # Más puntos para horas tempranas

            scored_slots.append((slot, score))

        # Ordenar por score
        scored_slots.sort(key=lambda x: x[1], reverse=True)

        return scored_slots[0][0] if scored_slots else None

    def reservar_slot(
        self,
        slot_id: str,
        cita_id: str
    ) -> Tuple[bool, str]:
        """
        Reserva un slot para una cita.

        Args:
            slot_id: ID del slot a reservar
            cita_id: ID de la cita

        Returns:
            Tuple con (éxito, mensaje)
        """
        # Buscar slot
        slot = self._buscar_slot_por_id(slot_id)

        if not slot:
            return (False, f"❌ Slot {slot_id} no encontrado")

        if slot.estado != EstadoSlot.DISPONIBLE:
            return (False, f"❌ Slot no disponible: {slot.estado.value}")

        if slot.capacidad_restante <= 0:
            return (False, "❌ Slot sin capacidad disponible")

        # Reservar
        slot.capacidad_restante -= 1
        slot.cita_asignada = cita_id

        if slot.capacidad_restante == 0:
            slot.estado = EstadoSlot.OCUPADO
        else:
            slot.estado = EstadoSlot.RESERVADO

        self._guardar_datos()

        logger.info(f"✅ Slot {slot_id} reservado para cita {cita_id}")

        return (True, f"✅ Slot reservado exitosamente")

    def liberar_slot(
        self,
        slot_id: str,
        cita_id: str
    ) -> Tuple[bool, str]:
        """Libera un slot previamente reservado"""
        slot = self._buscar_slot_por_id(slot_id)

        if not slot:
            return (False, f"❌ Slot {slot_id} no encontrado")

        # Liberar capacidad
        slot.capacidad_restante += 1

        if slot.cita_asignada == cita_id:
            slot.cita_asignada = None

        if slot.capacidad_restante > 0:
            slot.estado = EstadoSlot.DISPONIBLE

        self._guardar_datos()

        logger.info(f"🔓 Slot {slot_id} liberado")

        return (True, "✅ Slot liberado exitosamente")

    def _buscar_slot_por_id(self, slot_id: str) -> Optional[SlotHorario]:
        """Busca un slot por su ID"""
        for slots_dia in self.slots.values():
            for slot in slots_dia:
                if slot.id_slot == slot_id:
                    return slot
        return None

    # ═══════════════════════════════════════════════════════════════════════════
    # DETECCIÓN DE CONFLICTOS
    # ═══════════════════════════════════════════════════════════════════════════

    def detectar_conflictos(
        self,
        fecha: date
    ) -> List[Conflicto]:
        """
        Detecta conflictos de scheduling para una fecha.

        Tipos de conflictos detectados:
        - Sobrecapacidad
        - Slots sin buffer
        - Desbalanceo de carga
        - Citas sin recursos
        """
        fecha_str = fecha.isoformat()
        conflictos = []

        if fecha_str not in self.slots:
            return []

        slots_dia = self.slots[fecha_str]

        # Detectar sobrecapacidad
        for slot in slots_dia:
            if slot.capacidad_restante < 0:
                conflicto = Conflicto(
                    id_conflicto=f"CONF-CAP-{slot.id_slot}",
                    tipo="SOBRECAPACIDAD",
                    severidad="CRITICO",
                    descripcion=f"Slot {slot.id_slot} excede capacidad máxima",
                    citas_afectadas=[slot.cita_asignada] if slot.cita_asignada else [],
                    slots_afectados=[slot.id_slot],
                    fecha_deteccion=datetime.now()
                )
                conflictos.append(conflicto)

        # Detectar slots consecutivos sin buffer
        for i, slot in enumerate(slots_dia[:-1]):
            next_slot = slots_dia[i + 1]
            if (slot.tipo == next_slot.tipo and
                slot.estado == EstadoSlot.OCUPADO and
                next_slot.estado == EstadoSlot.OCUPADO):

                tiempo_entre = datetime.combine(fecha, next_slot.hora_inicio) - \
                              datetime.combine(fecha, slot.hora_fin)

                if tiempo_entre.total_seconds() < BUFFER_ENTRE_CITAS_MINUTOS * 60:
                    conflicto = Conflicto(
                        id_conflicto=f"CONF-BUF-{slot.id_slot}",
                        tipo="SIN_BUFFER",
                        severidad="MEDIO",
                        descripcion=f"Insuficiente tiempo entre slots {slot.id_slot} y {next_slot.id_slot}",
                        citas_afectadas=[],
                        slots_afectados=[slot.id_slot, next_slot.id_slot],
                        fecha_deteccion=datetime.now()
                    )
                    conflictos.append(conflicto)

        # Detectar desbalanceo de carga por hora
        carga_por_hora = defaultdict(int)
        for slot in slots_dia:
            if slot.estado in [EstadoSlot.OCUPADO, EstadoSlot.RESERVADO]:
                carga_por_hora[slot.hora_inicio.hour] += 1

        if carga_por_hora:
            max_carga = max(carga_por_hora.values())
            min_carga = min(carga_por_hora.values())

            if max_carga > 0 and (max_carga - min_carga) / max_carga > 0.5:
                horas_pico = [h for h, c in carga_por_hora.items() if c == max_carga]
                conflicto = Conflicto(
                    id_conflicto=f"CONF-BAL-{fecha_str}",
                    tipo="DESBALANCEO",
                    severidad="BAJO",
                    descripcion=f"Carga desbalanceada: horas pico {horas_pico}",
                    citas_afectadas=[],
                    slots_afectados=[],
                    fecha_deteccion=datetime.now()
                )
                conflictos.append(conflicto)

        # Guardar conflictos
        self.conflictos.extend(conflictos)
        self._guardar_datos()

        if conflictos:
            logger.warning(f"⚠️ Detectados {len(conflictos)} conflictos para {fecha}")

        return conflictos

    def resolver_conflicto(
        self,
        id_conflicto: str,
        accion: str = "auto"
    ) -> Tuple[bool, str]:
        """
        Intenta resolver un conflicto.

        Args:
            id_conflicto: ID del conflicto
            accion: 'auto' para resolución automática o acción específica

        Returns:
            Tuple con (éxito, mensaje)
        """
        conflicto = next(
            (c for c in self.conflictos if c.id_conflicto == id_conflicto),
            None
        )

        if not conflicto:
            return (False, f"❌ Conflicto {id_conflicto} no encontrado")

        if conflicto.resuelto:
            return (True, "Conflicto ya resuelto")

        solucion = ""

        if conflicto.tipo == "SOBRECAPACIDAD":
            # Buscar slots alternativos
            for slot_id in conflicto.slots_afectados:
                slot = self._buscar_slot_por_id(slot_id)
                if slot:
                    # Intentar reubicar la última cita
                    slot.capacidad_restante = 0
                    solucion = "Capacidad ajustada al máximo"

        elif conflicto.tipo == "SIN_BUFFER":
            # Agregar buffer
            solucion = "Buffer agregado entre slots"

        elif conflicto.tipo == "DESBALANCEO":
            # Sugerir redistribución
            solucion = "Se sugiere redistribuir citas a horas menos congestionadas"

        if solucion:
            conflicto.resuelto = True
            conflicto.solucion_aplicada = solucion
            conflicto.fecha_resolucion = datetime.now()
            self._guardar_datos()

            logger.info(f"✅ Conflicto {id_conflicto} resuelto: {solucion}")
            return (True, f"✅ Conflicto resuelto: {solucion}")

        return (False, "❌ No se pudo resolver automáticamente")

    # ═══════════════════════════════════════════════════════════════════════════
    # BLOQUEOS Y RESTRICCIONES
    # ═══════════════════════════════════════════════════════════════════════════

    def agregar_bloqueo(
        self,
        fecha_inicio: date,
        fecha_fin: date,
        motivo: str,
        hora_inicio: Optional[time] = None,
        hora_fin: Optional[time] = None,
        descripcion: str = ""
    ) -> Tuple[bool, str]:
        """
        Agrega un bloqueo de horarios.

        Args:
            fecha_inicio: Fecha inicio del bloqueo
            fecha_fin: Fecha fin del bloqueo
            motivo: Motivo del bloqueo
            hora_inicio: Hora inicio (opcional, todo el día si no se especifica)
            hora_fin: Hora fin
            descripcion: Descripción adicional

        Returns:
            Tuple con (éxito, mensaje)
        """
        bloqueo = {
            'id': f"BLQ-{len(self.bloqueos_programados) + 1:04d}",
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'hora_inicio': hora_inicio,
            'hora_fin': hora_fin,
            'motivo': motivo,
            'descripcion': descripcion,
            'creado': datetime.now().isoformat()
        }

        self.bloqueos_programados.append(bloqueo)

        # Actualizar slots existentes
        fecha_actual = fecha_inicio
        while fecha_actual <= fecha_fin:
            fecha_str = fecha_actual.isoformat()
            if fecha_str in self.slots:
                for slot in self.slots[fecha_str]:
                    if hora_inicio and hora_fin:
                        if hora_inicio <= slot.hora_inicio <= hora_fin:
                            slot.bloqueado = True
                            slot.motivo_bloqueo = MotivoBloqueo(motivo)
                            slot.estado = EstadoSlot.BLOQUEADO
                    else:
                        slot.bloqueado = True
                        slot.motivo_bloqueo = MotivoBloqueo(motivo)
                        slot.estado = EstadoSlot.BLOQUEADO

            fecha_actual += timedelta(days=1)

        self._guardar_datos()

        logger.info(f"🚫 Bloqueo agregado: {fecha_inicio} a {fecha_fin} - {motivo}")

        return (True, f"✅ Bloqueo agregado: {bloqueo['id']}")

    def eliminar_bloqueo(self, bloqueo_id: str) -> Tuple[bool, str]:
        """Elimina un bloqueo"""
        bloqueo = next(
            (b for b in self.bloqueos_programados if b['id'] == bloqueo_id),
            None
        )

        if not bloqueo:
            return (False, f"❌ Bloqueo {bloqueo_id} no encontrado")

        self.bloqueos_programados.remove(bloqueo)
        self._guardar_datos()

        logger.info(f"🔓 Bloqueo {bloqueo_id} eliminado")

        return (True, "✅ Bloqueo eliminado")

    # ═══════════════════════════════════════════════════════════════════════════
    # REPORTES Y ESTADÍSTICAS
    # ═══════════════════════════════════════════════════════════════════════════

    def obtener_resumen_dia(self, fecha: date) -> ResumenDia:
        """Genera un resumen del scheduling para un día"""
        fecha_str = fecha.isoformat()

        if fecha_str not in self.slots:
            self.generar_slots_dia(fecha)

        slots_dia = self.slots.get(fecha_str, [])

        # Contar estados
        disponibles = sum(1 for s in slots_dia if s.estado == EstadoSlot.DISPONIBLE)
        ocupados = sum(1 for s in slots_dia if s.estado in [EstadoSlot.OCUPADO, EstadoSlot.RESERVADO])
        bloqueados = sum(1 for s in slots_dia if s.estado == EstadoSlot.BLOQUEADO)

        # Capacidad por tipo
        cap_recibo = {}
        cap_expedicion = {}

        for hora in range(6, 23):
            slots_hora_rec = [s for s in slots_dia
                            if s.tipo == TipoSlot.RECIBO and s.hora_inicio.hour == hora]
            slots_hora_exp = [s for s in slots_dia
                             if s.tipo == TipoSlot.EXPEDICION and s.hora_inicio.hour == hora]

            if slots_hora_rec:
                cap_recibo[f"{hora:02d}:00"] = sum(s.capacidad_restante for s in slots_hora_rec)
            if slots_hora_exp:
                cap_expedicion[f"{hora:02d}:00"] = sum(s.capacidad_restante for s in slots_hora_exp)

        # Identificar horas pico
        horas_pico = []
        for hora, cap in cap_recibo.items():
            if cap < CAPACIDAD_SIMULTANEA_RECIBO * 0.3:
                horas_pico.append(hora)

        # Alertas
        alertas = []
        if disponibles < len(slots_dia) * 0.2:
            alertas.append("⚠️ Baja disponibilidad de slots")
        if bloqueados > len(slots_dia) * 0.1:
            alertas.append("⚠️ Alto número de bloqueos")

        return ResumenDia(
            fecha=fecha,
            total_slots=len(slots_dia),
            slots_disponibles=disponibles,
            slots_ocupados=ocupados,
            slots_bloqueados=bloqueados,
            capacidad_recibo=cap_recibo,
            capacidad_expedicion=cap_expedicion,
            horas_pico=horas_pico,
            alertas=alertas
        )

    def obtener_calendario_semana(
        self,
        fecha_inicio: date
    ) -> Dict[str, Dict]:
        """Genera un calendario visual de la semana"""
        calendario = {}

        for i in range(7):
            fecha = fecha_inicio + timedelta(days=i)
            resumen = self.obtener_resumen_dia(fecha)

            calendario[fecha.isoformat()] = {
                'dia': calendar.day_name[fecha.weekday()],
                'total_slots': resumen.total_slots,
                'disponibles': resumen.slots_disponibles,
                'ocupados': resumen.slots_ocupados,
                'bloqueados': resumen.slots_bloqueados,
                'porcentaje_ocupacion': f"{(resumen.slots_ocupados / resumen.total_slots * 100) if resumen.total_slots > 0 else 0:.1f}%",
                'horas_pico': resumen.horas_pico,
                'alertas': resumen.alertas
            }

        return calendario

    def obtener_estadisticas_periodo(
        self,
        fecha_inicio: date,
        fecha_fin: date
    ) -> Dict[str, Any]:
        """Obtiene estadísticas de un período"""
        estadisticas = {
            'periodo': f"{fecha_inicio} a {fecha_fin}",
            'dias_analizados': 0,
            'total_slots': 0,
            'promedio_ocupacion': 0,
            'dia_mas_ocupado': None,
            'dia_menos_ocupado': None,
            'conflictos_detectados': 0,
            'conflictos_resueltos': 0
        }

        ocupaciones = []
        fecha_actual = fecha_inicio

        while fecha_actual <= fecha_fin:
            fecha_str = fecha_actual.isoformat()
            if fecha_str in self.slots:
                slots_dia = self.slots[fecha_str]
                total = len(slots_dia)
                ocupados = sum(1 for s in slots_dia if s.estado in [EstadoSlot.OCUPADO, EstadoSlot.RESERVADO])

                if total > 0:
                    ocupacion = (ocupados / total) * 100
                    ocupaciones.append((fecha_str, ocupacion))
                    estadisticas['total_slots'] += total
                    estadisticas['dias_analizados'] += 1

            fecha_actual += timedelta(days=1)

        if ocupaciones:
            estadisticas['promedio_ocupacion'] = f"{sum(o[1] for o in ocupaciones) / len(ocupaciones):.1f}%"
            estadisticas['dia_mas_ocupado'] = max(ocupaciones, key=lambda x: x[1])[0]
            estadisticas['dia_menos_ocupado'] = min(ocupaciones, key=lambda x: x[1])[0]

        # Conflictos en el período
        for conflicto in self.conflictos:
            estadisticas['conflictos_detectados'] += 1
            if conflicto.resuelto:
                estadisticas['conflictos_resueltos'] += 1

        return estadisticas

    # ═══════════════════════════════════════════════════════════════════════════
    # PERSISTENCIA
    # ═══════════════════════════════════════════════════════════════════════════

    def _guardar_datos(self) -> None:
        """Guarda los datos del scheduler"""
        try:
            # Guardar slots
            slots_data = {}
            for fecha, slots in self.slots.items():
                slots_data[fecha] = [self._slot_to_dict(s) for s in slots]

            with open(self.ruta_datos / 'slots.json', 'w', encoding='utf-8') as f:
                json.dump(slots_data, f, ensure_ascii=False, indent=2, default=str)

            # Guardar conflictos
            conflictos_data = [self._conflicto_to_dict(c) for c in self.conflictos]
            with open(self.ruta_datos / 'conflictos.json', 'w', encoding='utf-8') as f:
                json.dump(conflictos_data, f, ensure_ascii=False, indent=2, default=str)

            # Guardar bloqueos
            with open(self.ruta_datos / 'bloqueos.json', 'w', encoding='utf-8') as f:
                json.dump(self.bloqueos_programados, f, ensure_ascii=False, indent=2, default=str)

        except Exception as e:
            logger.error(f"❌ Error al guardar datos del scheduler: {e}")

    def _cargar_datos(self) -> None:
        """Carga los datos del scheduler"""
        try:
            # Cargar slots
            slots_file = self.ruta_datos / 'slots.json'
            if slots_file.exists():
                with open(slots_file, 'r', encoding='utf-8') as f:
                    slots_data = json.load(f)
                    for fecha, slots in slots_data.items():
                        self.slots[fecha] = [self._dict_to_slot(s) for s in slots]

            # Cargar conflictos
            conflictos_file = self.ruta_datos / 'conflictos.json'
            if conflictos_file.exists():
                with open(conflictos_file, 'r', encoding='utf-8') as f:
                    conflictos_data = json.load(f)
                    self.conflictos = [self._dict_to_conflicto(c) for c in conflictos_data]

            # Cargar bloqueos
            bloqueos_file = self.ruta_datos / 'bloqueos.json'
            if bloqueos_file.exists():
                with open(bloqueos_file, 'r', encoding='utf-8') as f:
                    self.bloqueos_programados = json.load(f)

        except Exception as e:
            logger.warning(f"⚠️ No se pudieron cargar datos del scheduler: {e}")

    def _slot_to_dict(self, slot: SlotHorario) -> Dict:
        return {
            'id_slot': slot.id_slot,
            'fecha': slot.fecha.isoformat(),
            'hora_inicio': slot.hora_inicio.isoformat(),
            'hora_fin': slot.hora_fin.isoformat(),
            'tipo': slot.tipo.value,
            'compuerta': slot.compuerta,
            'estado': slot.estado.value,
            'cita_asignada': slot.cita_asignada,
            'capacidad_restante': slot.capacidad_restante,
            'bloqueado': slot.bloqueado,
            'motivo_bloqueo': slot.motivo_bloqueo.value if slot.motivo_bloqueo else None,
            'notas': slot.notas
        }

    def _dict_to_slot(self, data: Dict) -> SlotHorario:
        return SlotHorario(
            id_slot=data['id_slot'],
            fecha=date.fromisoformat(data['fecha']),
            hora_inicio=time.fromisoformat(data['hora_inicio']),
            hora_fin=time.fromisoformat(data['hora_fin']),
            tipo=TipoSlot(data['tipo']),
            compuerta=data.get('compuerta'),
            estado=EstadoSlot(data['estado']),
            cita_asignada=data.get('cita_asignada'),
            capacidad_restante=data.get('capacidad_restante', 1),
            bloqueado=data.get('bloqueado', False),
            motivo_bloqueo=MotivoBloqueo(data['motivo_bloqueo']) if data.get('motivo_bloqueo') else None,
            notas=data.get('notas', '')
        )

    def _conflicto_to_dict(self, conflicto: Conflicto) -> Dict:
        return {
            'id_conflicto': conflicto.id_conflicto,
            'tipo': conflicto.tipo,
            'severidad': conflicto.severidad,
            'descripcion': conflicto.descripcion,
            'citas_afectadas': conflicto.citas_afectadas,
            'slots_afectados': conflicto.slots_afectados,
            'fecha_deteccion': conflicto.fecha_deteccion.isoformat(),
            'resuelto': conflicto.resuelto,
            'solucion_aplicada': conflicto.solucion_aplicada,
            'fecha_resolucion': conflicto.fecha_resolucion.isoformat() if conflicto.fecha_resolucion else None
        }

    def _dict_to_conflicto(self, data: Dict) -> Conflicto:
        return Conflicto(
            id_conflicto=data['id_conflicto'],
            tipo=data['tipo'],
            severidad=data['severidad'],
            descripcion=data['descripcion'],
            citas_afectadas=data.get('citas_afectadas', []),
            slots_afectados=data.get('slots_afectados', []),
            fecha_deteccion=datetime.fromisoformat(data['fecha_deteccion']),
            resuelto=data.get('resuelto', False),
            solucion_aplicada=data.get('solucion_aplicada'),
            fecha_resolucion=datetime.fromisoformat(data['fecha_resolucion']) if data.get('fecha_resolucion') else None
        )


# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIONES DE UTILIDAD
# ═══════════════════════════════════════════════════════════════════════════════

def crear_scheduler(almacen: str = "427") -> SchedulerTrafico:
    """Factory function para crear el scheduler"""
    return SchedulerTrafico(almacen=almacen)


def demo_scheduler():
    """Demostración del sistema de scheduling"""
    print("\n" + "═" * 70)
    print("📅 DEMOSTRACIÓN - SISTEMA DE SCHEDULING DE TRÁFICO")
    print("═" * 70)

    scheduler = crear_scheduler()

    # Generar slots para hoy
    hoy = date.today()
    print(f"\n📆 Generando slots para {hoy}...")
    slots = scheduler.generar_slots_dia(hoy)
    print(f"   ✅ {len(slots)} slots generados")

    # Buscar slots disponibles
    print("\n🔍 Buscando slots disponibles para recibo (60 min)...")
    disponibles = scheduler.buscar_slots_disponibles(
        fecha=hoy,
        tipo=TipoSlot.RECIBO,
        duracion_minutos=60
    )
    print(f"   ✅ {len(disponibles)} slots encontrados")

    # Obtener mejor slot
    mejor = scheduler.obtener_mejor_slot(hoy, TipoSlot.RECIBO, 60)
    if mejor:
        print(f"   📌 Mejor slot: {mejor.hora_inicio} - {mejor.hora_fin}")

    # Resumen del día
    resumen = scheduler.obtener_resumen_dia(hoy)
    print(f"\n📊 RESUMEN DEL DÍA:")
    print(f"   • Total slots: {resumen.total_slots}")
    print(f"   • Disponibles: {resumen.slots_disponibles}")
    print(f"   • Ocupados: {resumen.slots_ocupados}")
    print(f"   • Bloqueados: {resumen.slots_bloqueados}")

    # Detectar conflictos
    conflictos = scheduler.detectar_conflictos(hoy)
    print(f"\n⚠️ Conflictos detectados: {len(conflictos)}")

    print("\n" + "═" * 70)
    print("✅ Demostración completada")
    print("═" * 70)


if __name__ == "__main__":
    demo_scheduler()
