"""
===============================================================================
MÓDULO DE ALMACENAMIENTO DE CONFLICTOS - SISTEMA SAC
Sistema de Automatización de Consultas - CEDIS Cancún 427
===============================================================================

Almacenamiento persistente de conflictos externos detectados por correo.
Utiliza archivos JSON para persistencia simple y portable.

Funcionalidades:
- CRUD completo de conflictos
- Historial de eventos por conflicto
- Estados de flujo de trabajo
- Búsqueda y filtrado
- Estadísticas y reportes

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
===============================================================================
"""

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
import threading

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# ENUMERACIONES
# ═══════════════════════════════════════════════════════════════

class EstadoConflicto(Enum):
    """Estados del ciclo de vida de un conflicto"""
    NUEVO = "NUEVO"                         # Recién detectado
    ANALIZADO = "ANALIZADO"                 # Análisis completado
    NOTIFICADO = "NOTIFICADO"               # Analista notificado
    EN_REVISION = "EN_REVISION"             # Analista revisando
    CONFIRMADO = "CONFIRMADO"               # Analista confirmó el ajuste
    EN_RESOLUCION = "EN_RESOLUCION"         # Ejecutando resolución
    RESUELTO = "RESUELTO"                   # Conflicto resuelto
    ESCALADO = "ESCALADO"                   # Escalado a supervisor
    RECHAZADO = "RECHAZADO"                 # Conflicto rechazado/inválido
    DOCUMENTADO = "DOCUMENTADO"             # Documentación generada


class TipoEvento(Enum):
    """Tipos de eventos en el historial de un conflicto"""
    CREADO = "CREADO"
    CORREO_RECIBIDO = "CORREO_RECIBIDO"
    ANALISIS_INICIADO = "ANALISIS_INICIADO"
    ANALISIS_COMPLETADO = "ANALISIS_COMPLETADO"
    NOTIFICACION_ENVIADA = "NOTIFICACION_ENVIADA"
    ASIGNADO = "ASIGNADO"
    REVISION_INICIADA = "REVISION_INICIADA"
    CONFIRMACION_RECIBIDA = "CONFIRMACION_RECIBIDA"
    RESOLUCION_INICIADA = "RESOLUCION_INICIADA"
    RESOLUCION_COMPLETADA = "RESOLUCION_COMPLETADA"
    RESOLUCION_FALLIDA = "RESOLUCION_FALLIDA"
    ESCALADO = "ESCALADO"
    RECHAZADO = "RECHAZADO"
    DOCUMENTACION_GENERADA = "DOCUMENTACION_GENERADA"
    RESPUESTA_ENVIADA = "RESPUESTA_ENVIADA"
    NOTA_AGREGADA = "NOTA_AGREGADA"
    ESTADO_CAMBIADO = "ESTADO_CAMBIADO"


# ═══════════════════════════════════════════════════════════════
# DATACLASSES
# ═══════════════════════════════════════════════════════════════

@dataclass
class EventoConflicto:
    """Representa un evento en el historial del conflicto"""
    id: str
    tipo: TipoEvento
    timestamp: datetime
    descripcion: str
    usuario: Optional[str] = None
    datos_adicionales: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para serialización"""
        return {
            'id': self.id,
            'tipo': self.tipo.value,
            'timestamp': self.timestamp.isoformat(),
            'descripcion': self.descripcion,
            'usuario': self.usuario,
            'datos_adicionales': self.datos_adicionales
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EventoConflicto':
        """Crea instancia desde diccionario"""
        return cls(
            id=data['id'],
            tipo=TipoEvento(data['tipo']),
            timestamp=datetime.fromisoformat(data['timestamp']),
            descripcion=data['descripcion'],
            usuario=data.get('usuario'),
            datos_adicionales=data.get('datos_adicionales')
        )


@dataclass
class ConflictoExterno:
    """Representa un conflicto reportado externamente"""
    # Identificación
    id: str
    fecha_creacion: datetime

    # Datos del correo origen
    correo_id: str
    correo_remitente_email: str
    correo_remitente_nombre: str
    correo_asunto: str
    correo_cuerpo: str
    correo_fecha: datetime
    correo_adjuntos: List[str] = field(default_factory=list)

    # Clasificación
    tipo_conflicto: str
    severidad: str
    palabras_clave: List[str] = field(default_factory=list)

    # Datos extraídos
    oc_numeros: List[str] = field(default_factory=list)
    tiendas_afectadas: List[str] = field(default_factory=list)
    cantidades: List[float] = field(default_factory=list)

    # Estado y asignación
    estado: EstadoConflicto = EstadoConflicto.NUEVO
    asignado_a: Optional[str] = None
    fecha_asignacion: Optional[datetime] = None

    # Resolución
    accion_confirmada: Optional[str] = None
    resultado_resolucion: Optional[str] = None
    fecha_resolucion: Optional[datetime] = None
    notas_resolucion: Optional[str] = None

    # Documentación
    archivo_reporte: Optional[str] = None
    correo_respuesta_id: Optional[str] = None

    # Validación interna
    validacion_interna_id: Optional[str] = None
    confirmado_por_sistema: bool = False

    # Historial
    eventos: List[EventoConflicto] = field(default_factory=list)

    def agregar_evento(
        self,
        tipo: TipoEvento,
        descripcion: str,
        usuario: str = None,
        datos: Dict = None
    ):
        """Agrega un evento al historial"""
        evento = EventoConflicto(
            id=str(uuid.uuid4())[:8],
            tipo=tipo,
            timestamp=datetime.now(),
            descripcion=descripcion,
            usuario=usuario,
            datos_adicionales=datos
        )
        self.eventos.append(evento)

    def cambiar_estado(self, nuevo_estado: EstadoConflicto, usuario: str = None):
        """Cambia el estado del conflicto"""
        estado_anterior = self.estado
        self.estado = nuevo_estado
        self.agregar_evento(
            TipoEvento.ESTADO_CAMBIADO,
            f"Estado cambiado de {estado_anterior.value} a {nuevo_estado.value}",
            usuario=usuario,
            datos={'estado_anterior': estado_anterior.value, 'estado_nuevo': nuevo_estado.value}
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para serialización JSON"""
        return {
            'id': self.id,
            'fecha_creacion': self.fecha_creacion.isoformat(),

            'correo_id': self.correo_id,
            'correo_remitente_email': self.correo_remitente_email,
            'correo_remitente_nombre': self.correo_remitente_nombre,
            'correo_asunto': self.correo_asunto,
            'correo_cuerpo': self.correo_cuerpo,
            'correo_fecha': self.correo_fecha.isoformat(),
            'correo_adjuntos': self.correo_adjuntos,

            'tipo_conflicto': self.tipo_conflicto,
            'severidad': self.severidad,
            'palabras_clave': self.palabras_clave,

            'oc_numeros': self.oc_numeros,
            'tiendas_afectadas': self.tiendas_afectadas,
            'cantidades': self.cantidades,

            'estado': self.estado.value,
            'asignado_a': self.asignado_a,
            'fecha_asignacion': self.fecha_asignacion.isoformat() if self.fecha_asignacion else None,

            'accion_confirmada': self.accion_confirmada,
            'resultado_resolucion': self.resultado_resolucion,
            'fecha_resolucion': self.fecha_resolucion.isoformat() if self.fecha_resolucion else None,
            'notas_resolucion': self.notas_resolucion,

            'archivo_reporte': self.archivo_reporte,
            'correo_respuesta_id': self.correo_respuesta_id,

            'validacion_interna_id': self.validacion_interna_id,
            'confirmado_por_sistema': self.confirmado_por_sistema,

            'eventos': [e.to_dict() for e in self.eventos]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConflictoExterno':
        """Crea instancia desde diccionario"""
        conflicto = cls(
            id=data['id'],
            fecha_creacion=datetime.fromisoformat(data['fecha_creacion']),

            correo_id=data['correo_id'],
            correo_remitente_email=data['correo_remitente_email'],
            correo_remitente_nombre=data['correo_remitente_nombre'],
            correo_asunto=data['correo_asunto'],
            correo_cuerpo=data['correo_cuerpo'],
            correo_fecha=datetime.fromisoformat(data['correo_fecha']),
            correo_adjuntos=data.get('correo_adjuntos', []),

            tipo_conflicto=data['tipo_conflicto'],
            severidad=data['severidad'],
            palabras_clave=data.get('palabras_clave', []),

            oc_numeros=data.get('oc_numeros', []),
            tiendas_afectadas=data.get('tiendas_afectadas', []),
            cantidades=data.get('cantidades', []),

            estado=EstadoConflicto(data['estado']),
            asignado_a=data.get('asignado_a'),
            fecha_asignacion=datetime.fromisoformat(data['fecha_asignacion']) if data.get('fecha_asignacion') else None,

            accion_confirmada=data.get('accion_confirmada'),
            resultado_resolucion=data.get('resultado_resolucion'),
            fecha_resolucion=datetime.fromisoformat(data['fecha_resolucion']) if data.get('fecha_resolucion') else None,
            notas_resolucion=data.get('notas_resolucion'),

            archivo_reporte=data.get('archivo_reporte'),
            correo_respuesta_id=data.get('correo_respuesta_id'),

            validacion_interna_id=data.get('validacion_interna_id'),
            confirmado_por_sistema=data.get('confirmado_por_sistema', False),

            eventos=[]
        )

        # Cargar eventos
        for evento_data in data.get('eventos', []):
            conflicto.eventos.append(EventoConflicto.from_dict(evento_data))

        return conflicto


# ═══════════════════════════════════════════════════════════════
# CLASE PRINCIPAL: ALMACENAMIENTO DE CONFLICTOS
# ═══════════════════════════════════════════════════════════════

class ConflictStorage:
    """
    Almacenamiento persistente de conflictos en formato JSON.

    Provee operaciones CRUD, búsqueda y estadísticas sobre
    los conflictos registrados.
    """

    def __init__(self, ruta_archivo: str = None):
        """
        Inicializa el almacenamiento.

        Args:
            ruta_archivo: Ruta al archivo JSON de conflictos
        """
        if ruta_archivo is None:
            from config import PATHS
            ruta_archivo = PATHS['output'] / 'conflictos.json'

        self.ruta_archivo = Path(ruta_archivo)
        self._lock = threading.Lock()
        self._conflictos: Dict[str, ConflictoExterno] = {}

        # Cargar datos existentes
        self._cargar()

        logger.info(f"📁 ConflictStorage inicializado: {self.ruta_archivo}")
        logger.info(f"   Conflictos cargados: {len(self._conflictos)}")

    def _cargar(self):
        """Carga los conflictos desde el archivo JSON"""
        if not self.ruta_archivo.exists():
            logger.info("📁 Archivo de conflictos no existe, creando nuevo...")
            self._guardar()
            return

        try:
            with open(self.ruta_archivo, 'r', encoding='utf-8') as f:
                data = json.load(f)

            for conflicto_data in data.get('conflictos', []):
                conflicto = ConflictoExterno.from_dict(conflicto_data)
                self._conflictos[conflicto.id] = conflicto

        except Exception as e:
            logger.error(f"❌ Error cargando conflictos: {e}")
            self._conflictos = {}

    def _guardar(self):
        """Guarda los conflictos al archivo JSON"""
        try:
            # Asegurar que el directorio existe
            self.ruta_archivo.parent.mkdir(parents=True, exist_ok=True)

            data = {
                'version': '1.0.0',
                'ultima_actualizacion': datetime.now().isoformat(),
                'total_conflictos': len(self._conflictos),
                'conflictos': [c.to_dict() for c in self._conflictos.values()]
            }

            with open(self.ruta_archivo, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.error(f"❌ Error guardando conflictos: {e}")

    def generar_id(self) -> str:
        """Genera un ID único para un nuevo conflicto"""
        fecha = datetime.now().strftime('%Y%m%d')
        secuencia = len([c for c in self._conflictos.values()
                        if c.fecha_creacion.strftime('%Y%m%d') == fecha]) + 1
        return f"CONF-{fecha}-{secuencia:03d}"

    # ═══════════════════════════════════════════════════════════
    # OPERACIONES CRUD
    # ═══════════════════════════════════════════════════════════

    def crear(self, conflicto: ConflictoExterno) -> str:
        """
        Crea un nuevo conflicto en el almacenamiento.

        Args:
            conflicto: Conflicto a almacenar

        Returns:
            ID del conflicto creado
        """
        with self._lock:
            # Generar ID si no tiene
            if not conflicto.id:
                conflicto.id = self.generar_id()

            # Agregar evento de creación
            conflicto.agregar_evento(
                TipoEvento.CREADO,
                f"Conflicto creado desde correo de {conflicto.correo_remitente_email}"
            )

            self._conflictos[conflicto.id] = conflicto
            self._guardar()

            logger.info(f"✅ Conflicto creado: {conflicto.id}")
            return conflicto.id

    def obtener(self, conflicto_id: str) -> Optional[ConflictoExterno]:
        """
        Obtiene un conflicto por su ID.

        Args:
            conflicto_id: ID del conflicto

        Returns:
            ConflictoExterno o None si no existe
        """
        return self._conflictos.get(conflicto_id)

    def actualizar(self, conflicto: ConflictoExterno) -> bool:
        """
        Actualiza un conflicto existente.

        Args:
            conflicto: Conflicto con datos actualizados

        Returns:
            True si se actualizó correctamente
        """
        with self._lock:
            if conflicto.id not in self._conflictos:
                logger.error(f"❌ Conflicto {conflicto.id} no existe")
                return False

            self._conflictos[conflicto.id] = conflicto
            self._guardar()

            logger.info(f"✅ Conflicto actualizado: {conflicto.id}")
            return True

    def eliminar(self, conflicto_id: str) -> bool:
        """
        Elimina un conflicto (solo si está cerrado).

        Args:
            conflicto_id: ID del conflicto a eliminar

        Returns:
            True si se eliminó correctamente
        """
        with self._lock:
            conflicto = self._conflictos.get(conflicto_id)
            if not conflicto:
                return False

            # Solo permitir eliminar conflictos cerrados
            estados_cerrados = [
                EstadoConflicto.RESUELTO,
                EstadoConflicto.RECHAZADO,
                EstadoConflicto.DOCUMENTADO
            ]
            if conflicto.estado not in estados_cerrados:
                logger.warning(f"⚠️ No se puede eliminar conflicto en estado {conflicto.estado.value}")
                return False

            del self._conflictos[conflicto_id]
            self._guardar()

            logger.info(f"🗑️ Conflicto eliminado: {conflicto_id}")
            return True

    # ═══════════════════════════════════════════════════════════
    # BÚSQUEDA Y FILTRADO
    # ═══════════════════════════════════════════════════════════

    def listar_todos(self) -> List[ConflictoExterno]:
        """Lista todos los conflictos"""
        return list(self._conflictos.values())

    def listar_por_estado(self, estado: EstadoConflicto) -> List[ConflictoExterno]:
        """Lista conflictos por estado"""
        return [c for c in self._conflictos.values() if c.estado == estado]

    def listar_pendientes(self) -> List[ConflictoExterno]:
        """Lista conflictos pendientes de resolución"""
        estados_pendientes = [
            EstadoConflicto.NUEVO,
            EstadoConflicto.ANALIZADO,
            EstadoConflicto.NOTIFICADO,
            EstadoConflicto.EN_REVISION,
            EstadoConflicto.CONFIRMADO,
            EstadoConflicto.EN_RESOLUCION
        ]
        return [c for c in self._conflictos.values() if c.estado in estados_pendientes]

    def listar_por_asignado(self, usuario: str) -> List[ConflictoExterno]:
        """Lista conflictos asignados a un usuario"""
        return [c for c in self._conflictos.values() if c.asignado_a == usuario]

    def listar_por_oc(self, oc_numero: str) -> List[ConflictoExterno]:
        """Lista conflictos relacionados con una OC"""
        return [c for c in self._conflictos.values() if oc_numero in c.oc_numeros]

    def buscar(
        self,
        estado: EstadoConflicto = None,
        tipo: str = None,
        severidad: str = None,
        asignado_a: str = None,
        fecha_desde: datetime = None,
        fecha_hasta: datetime = None,
        oc_numero: str = None,
        tienda: str = None
    ) -> List[ConflictoExterno]:
        """
        Búsqueda avanzada de conflictos.

        Args:
            estado: Filtrar por estado
            tipo: Filtrar por tipo de conflicto
            severidad: Filtrar por severidad
            asignado_a: Filtrar por usuario asignado
            fecha_desde: Fecha mínima de creación
            fecha_hasta: Fecha máxima de creación
            oc_numero: Filtrar por número de OC
            tienda: Filtrar por tienda afectada

        Returns:
            Lista de conflictos que coinciden
        """
        resultados = list(self._conflictos.values())

        if estado:
            resultados = [c for c in resultados if c.estado == estado]

        if tipo:
            resultados = [c for c in resultados if c.tipo_conflicto == tipo]

        if severidad:
            resultados = [c for c in resultados if c.severidad == severidad]

        if asignado_a:
            resultados = [c for c in resultados if c.asignado_a == asignado_a]

        if fecha_desde:
            resultados = [c for c in resultados if c.fecha_creacion >= fecha_desde]

        if fecha_hasta:
            resultados = [c for c in resultados if c.fecha_creacion <= fecha_hasta]

        if oc_numero:
            resultados = [c for c in resultados if oc_numero in c.oc_numeros]

        if tienda:
            resultados = [c for c in resultados if tienda in c.tiendas_afectadas]

        return resultados

    # ═══════════════════════════════════════════════════════════
    # OPERACIONES DE FLUJO DE TRABAJO
    # ═══════════════════════════════════════════════════════════

    def asignar(
        self,
        conflicto_id: str,
        usuario: str,
        asignador: str = "SISTEMA"
    ) -> bool:
        """
        Asigna un conflicto a un usuario.

        Args:
            conflicto_id: ID del conflicto
            usuario: Usuario a asignar
            asignador: Usuario que asigna

        Returns:
            True si se asignó correctamente
        """
        conflicto = self.obtener(conflicto_id)
        if not conflicto:
            return False

        conflicto.asignado_a = usuario
        conflicto.fecha_asignacion = datetime.now()
        conflicto.agregar_evento(
            TipoEvento.ASIGNADO,
            f"Asignado a {usuario}",
            usuario=asignador
        )

        return self.actualizar(conflicto)

    def agregar_nota(
        self,
        conflicto_id: str,
        nota: str,
        usuario: str
    ) -> bool:
        """
        Agrega una nota al historial del conflicto.

        Args:
            conflicto_id: ID del conflicto
            nota: Texto de la nota
            usuario: Usuario que agrega la nota

        Returns:
            True si se agregó correctamente
        """
        conflicto = self.obtener(conflicto_id)
        if not conflicto:
            return False

        conflicto.agregar_evento(
            TipoEvento.NOTA_AGREGADA,
            nota,
            usuario=usuario
        )

        return self.actualizar(conflicto)

    # ═══════════════════════════════════════════════════════════
    # ESTADÍSTICAS
    # ═══════════════════════════════════════════════════════════

    def obtener_estadisticas(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas generales del almacenamiento.

        Returns:
            Diccionario con estadísticas
        """
        conflictos = list(self._conflictos.values())
        total = len(conflictos)

        if total == 0:
            return {
                'total': 0,
                'por_estado': {},
                'por_tipo': {},
                'por_severidad': {},
                'pendientes': 0,
                'resueltos': 0,
                'tiempo_promedio_resolucion': None
            }

        # Por estado
        por_estado = {}
        for estado in EstadoConflicto:
            count = len([c for c in conflictos if c.estado == estado])
            if count > 0:
                por_estado[estado.value] = count

        # Por tipo
        por_tipo = {}
        for c in conflictos:
            tipo = c.tipo_conflicto
            por_tipo[tipo] = por_tipo.get(tipo, 0) + 1

        # Por severidad
        por_severidad = {}
        for c in conflictos:
            sev = c.severidad
            por_severidad[sev] = por_severidad.get(sev, 0) + 1

        # Pendientes y resueltos
        pendientes = len(self.listar_pendientes())
        resueltos = len([c for c in conflictos if c.estado in [
            EstadoConflicto.RESUELTO,
            EstadoConflicto.DOCUMENTADO
        ]])

        # Tiempo promedio de resolución
        tiempos = []
        for c in conflictos:
            if c.fecha_resolucion and c.fecha_creacion:
                delta = (c.fecha_resolucion - c.fecha_creacion).total_seconds()
                tiempos.append(delta)

        tiempo_promedio = sum(tiempos) / len(tiempos) if tiempos else None

        return {
            'total': total,
            'por_estado': por_estado,
            'por_tipo': por_tipo,
            'por_severidad': por_severidad,
            'pendientes': pendientes,
            'resueltos': resueltos,
            'tiempo_promedio_resolucion_segundos': tiempo_promedio,
            'tiempo_promedio_resolucion_horas': tiempo_promedio / 3600 if tiempo_promedio else None,
            'ultima_actualizacion': datetime.now().isoformat()
        }


# ═══════════════════════════════════════════════════════════════
# FUNCIONES DE UTILIDAD
# ═══════════════════════════════════════════════════════════════

_storage_instance: Optional[ConflictStorage] = None


def obtener_storage() -> ConflictStorage:
    """
    Obtiene la instancia singleton del storage.

    Returns:
        ConflictStorage
    """
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = ConflictStorage()
    return _storage_instance


def crear_conflicto_desde_correo(correo) -> ConflictoExterno:
    """
    Crea un ConflictoExterno desde un CorreoRecibido.

    Args:
        correo: CorreoRecibido del módulo email_receiver

    Returns:
        ConflictoExterno listo para almacenar
    """
    storage = obtener_storage()

    conflicto = ConflictoExterno(
        id=storage.generar_id(),
        fecha_creacion=datetime.now(),

        correo_id=correo.id_mensaje,
        correo_remitente_email=correo.remitente_email,
        correo_remitente_nombre=correo.remitente_nombre,
        correo_asunto=correo.asunto,
        correo_cuerpo=correo.cuerpo_texto,
        correo_fecha=correo.fecha_recepcion,
        correo_adjuntos=[adj.ruta_guardado for adj in correo.adjuntos if adj.ruta_guardado],

        tipo_conflicto=correo.tipo_conflicto_detectado.value if correo.tipo_conflicto_detectado else "OTRO",
        severidad=correo.severidad_detectada.value if correo.severidad_detectada else "🟡 MEDIO",
        palabras_clave=correo.palabras_clave_encontradas,

        oc_numeros=correo.oc_numeros,
        tiendas_afectadas=correo.tiendas_mencionadas,
        cantidades=correo.cantidades_mencionadas,

        estado=EstadoConflicto.NUEVO
    )

    conflicto.agregar_evento(
        TipoEvento.CORREO_RECIBIDO,
        f"Correo recibido de {correo.remitente_email}: {correo.asunto}"
    )

    return conflicto


# ═══════════════════════════════════════════════════════════════
# EJEMPLO DE USO
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║  📁 ALMACENAMIENTO DE CONFLICTOS - SISTEMA SAC                ║
    ║  Sistema de Automatización de Consultas - CEDIS Cancún 427    ║
    ╚═══════════════════════════════════════════════════════════════╝

    Este módulo provee almacenamiento persistente para conflictos
    reportados externamente por correo electrónico.

    Uso:
        from modules.conflicts import ConflictStorage, ConflictoExterno

        storage = ConflictStorage()

        # Crear conflicto
        conflicto = ConflictoExterno(...)
        storage.crear(conflicto)

        # Listar pendientes
        pendientes = storage.listar_pendientes()

        # Obtener estadísticas
        stats = storage.obtener_estadisticas()
    """)

    # Demo con datos de ejemplo
    storage = ConflictStorage('output/conflictos_demo.json')

    # Crear conflicto de ejemplo
    conflicto_demo = ConflictoExterno(
        id=storage.generar_id(),
        fecha_creacion=datetime.now(),
        correo_id="MSG001",
        correo_remitente_email="analista@chedraui.com.mx",
        correo_remitente_nombre="Juan García",
        correo_asunto="Problema distribución OC 750384000123",
        correo_cuerpo="Se detectó exceso de distribución en la OC mencionada.",
        correo_fecha=datetime.now(),
        tipo_conflicto="DISTRIBUCION_EXCEDENTE",
        severidad="🔴 CRÍTICO",
        oc_numeros=["750384000123"],
        tiendas_afectadas=["002", "003"]
    )

    # Almacenar
    storage.crear(conflicto_demo)

    # Mostrar estadísticas
    stats = storage.obtener_estadisticas()
    print(f"\n📊 Estadísticas:")
    print(f"   Total: {stats['total']}")
    print(f"   Pendientes: {stats['pendientes']}")
    print(f"   Por estado: {stats['por_estado']}")
