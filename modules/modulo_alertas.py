"""
═══════════════════════════════════════════════════════════════
MÓDULO DE ALERTAS Y MONITOREO DEL SISTEMA
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Sistema centralizado de gestión de alertas que registra y notifica:
- Inicios y finalizaciones de fases del sistema
- Caídas y recuperaciones del sistema
- Estados del modo Copiloto (activación/desactivación)
- Detecciones de nueva información
- Discrepancias y errores con pasos de solución
- Ajustes realizados en el sistema
- Eventos de monitoreo en tiempo real

"Las máquinas y los sistemas al servicio de los analistas"

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
═══════════════════════════════════════════════════════════════
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import threading
import uuid

# Configuración del sistema
try:
    from config import CEDIS, PATHS, EMAIL_CONFIG
except ImportError:
    CEDIS = {'code': '427', 'name': 'Cancún'}
    PATHS = {'logs': Path('./output/logs')}
    EMAIL_CONFIG = {}

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# ENUMERACIONES DE TIPOS DE ALERTAS Y EVENTOS
# ═══════════════════════════════════════════════════════════════

class TipoAlerta(Enum):
    """Tipos de alertas del sistema"""
    # Alertas de Sistema
    SISTEMA_INICIADO = "sistema_iniciado"
    SISTEMA_DETENIDO = "sistema_detenido"
    SISTEMA_CAIDO = "sistema_caido"
    SISTEMA_RECUPERADO = "sistema_recuperado"

    # Alertas de Fases
    FASE_INICIADA = "fase_iniciada"
    FASE_COMPLETADA = "fase_completada"
    FASE_ERROR = "fase_error"
    FASE_CANCELADA = "fase_cancelada"

    # Alertas del Copiloto
    COPILOTO_ACTIVADO = "copiloto_activado"
    COPILOTO_DESACTIVADO = "copiloto_desactivado"
    COPILOTO_PAUSADO = "copiloto_pausado"
    COPILOTO_REANUDADO = "copiloto_reanudado"
    COPILOTO_CORRECCION_INICIADA = "copiloto_correccion_iniciada"
    COPILOTO_CORRECCION_COMPLETADA = "copiloto_correccion_completada"
    COPILOTO_CORRECCION_FALLIDA = "copiloto_correccion_fallida"

    # Alertas de Monitoreo
    MONITOREO_INICIADO = "monitoreo_iniciado"
    MONITOREO_DETENIDO = "monitoreo_detenido"
    MONITOREO_PAUSADO = "monitoreo_pausado"

    # Alertas de Datos
    NUEVA_INFORMACION = "nueva_informacion_detectada"
    DATOS_ACTUALIZADOS = "datos_actualizados"
    DATOS_SINCRONIZADOS = "datos_sincronizados"

    # Alertas de Discrepancias y Errores
    DISCREPANCIA_DETECTADA = "discrepancia_detectada"
    ERROR_CRITICO = "error_critico"
    ERROR_ALTO = "error_alto"
    ERROR_MEDIO = "error_medio"
    ERROR_BAJO = "error_bajo"
    ADVERTENCIA = "advertencia"

    # Alertas de Ajustes
    AJUSTE_REALIZADO = "ajuste_realizado"
    AJUSTE_AUTOMATICO = "ajuste_automatico"
    AJUSTE_MANUAL = "ajuste_manual"
    AJUSTE_REVERTIDO = "ajuste_revertido"

    # Alertas de Conexión
    CONEXION_DB_ESTABLECIDA = "conexion_db_establecida"
    CONEXION_DB_PERDIDA = "conexion_db_perdida"
    CONEXION_DB_RECUPERADA = "conexion_db_recuperada"

    # Alertas de Reportes
    REPORTE_GENERADO = "reporte_generado"
    REPORTE_ENVIADO = "reporte_enviado"
    REPORTE_ERROR = "reporte_error"


class SeveridadAlerta(Enum):
    """Niveles de severidad de las alertas"""
    CRITICO = "🔴 CRÍTICO"
    ALTO = "🟠 ALTO"
    MEDIO = "🟡 MEDIO"
    BAJO = "🟢 BAJO"
    INFO = "ℹ️ INFO"
    EXITO = "✅ ÉXITO"
    DEBUG = "🔧 DEBUG"


class EstadoSistema(Enum):
    """Estados posibles del sistema"""
    ACTIVO = "activo"
    INACTIVO = "inactivo"
    EN_PAUSA = "en_pausa"
    EN_ERROR = "en_error"
    EN_RECUPERACION = "en_recuperacion"
    MANTENIMIENTO = "mantenimiento"


class EstadoCopiloto(Enum):
    """Estados del modo Copiloto"""
    ACTIVO = "activo"
    INACTIVO = "inactivo"
    PAUSADO = "pausado"
    EJECUTANDO = "ejecutando_correccion"
    ESPERANDO_CONFIRMACION = "esperando_confirmacion"
    EN_ERROR = "en_error"


class FaseSistema(Enum):
    """Fases del sistema de monitoreo"""
    INICIALIZACION = "inicializacion"
    CONEXION_DB = "conexion_db"
    CARGA_DATOS = "carga_datos"
    VALIDACION = "validacion"
    DETECCION_ANOMALIAS = "deteccion_anomalias"
    GENERACION_REPORTES = "generacion_reportes"
    ENVIO_NOTIFICACIONES = "envio_notificaciones"
    CORRECCION_DATOS = "correccion_datos"
    SINCRONIZACION = "sincronizacion"
    FINALIZACION = "finalizacion"


# ═══════════════════════════════════════════════════════════════
# CLASES DE DATOS PARA ALERTAS Y EVENTOS
# ═══════════════════════════════════════════════════════════════

@dataclass
class Alerta:
    """Representa una alerta del sistema"""
    id: str
    tipo: TipoAlerta
    severidad: SeveridadAlerta
    titulo: str
    mensaje: str
    timestamp: datetime
    modulo: str
    detalles: Optional[Dict[str, Any]] = None
    pasos_solucion: Optional[List[str]] = None
    datos_afectados: Optional[Dict[str, Any]] = None
    resuelta: bool = False
    fecha_resolucion: Optional[datetime] = None
    resolucion_notas: Optional[str] = None

    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())[:8]

    def to_dict(self) -> Dict:
        """Convierte la alerta a diccionario"""
        return {
            'id': self.id,
            'tipo': self.tipo.value,
            'severidad': self.severidad.value,
            'titulo': self.titulo,
            'mensaje': self.mensaje,
            'timestamp': self.timestamp.isoformat(),
            'modulo': self.modulo,
            'detalles': self.detalles,
            'pasos_solucion': self.pasos_solucion,
            'datos_afectados': self.datos_afectados,
            'resuelta': self.resuelta,
            'fecha_resolucion': self.fecha_resolucion.isoformat() if self.fecha_resolucion else None,
            'resolucion_notas': self.resolucion_notas
        }

    def __str__(self) -> str:
        return f"[{self.severidad.value}] {self.titulo} - {self.mensaje}"


@dataclass
class EventoFase:
    """Representa un evento de inicio/fin de fase"""
    id: str
    fase: FaseSistema
    estado: str  # 'iniciada', 'completada', 'error', 'cancelada'
    timestamp: datetime
    duracion_segundos: Optional[float] = None
    mensaje: Optional[str] = None
    metricas: Optional[Dict[str, Any]] = None
    errores: Optional[List[str]] = None

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'fase': self.fase.value,
            'estado': self.estado,
            'timestamp': self.timestamp.isoformat(),
            'duracion_segundos': self.duracion_segundos,
            'mensaje': self.mensaje,
            'metricas': self.metricas,
            'errores': self.errores
        }


@dataclass
class EventoCopiloto:
    """Representa un evento del modo Copiloto"""
    id: str
    estado_anterior: Optional[EstadoCopiloto]
    estado_nuevo: EstadoCopiloto
    timestamp: datetime
    razon: str
    anomalias_procesadas: int = 0
    correcciones_realizadas: int = 0
    correcciones_fallidas: int = 0
    detalles: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'estado_anterior': self.estado_anterior.value if self.estado_anterior else None,
            'estado_nuevo': self.estado_nuevo.value,
            'timestamp': self.timestamp.isoformat(),
            'razon': self.razon,
            'anomalias_procesadas': self.anomalias_procesadas,
            'correcciones_realizadas': self.correcciones_realizadas,
            'correcciones_fallidas': self.correcciones_fallidas,
            'detalles': self.detalles
        }


@dataclass
class Discrepancia:
    """Representa una discrepancia detectada"""
    id: str
    tipo: str
    severidad: SeveridadAlerta
    descripcion: str
    timestamp: datetime
    fuente_a: str
    fuente_b: str
    valor_esperado: Any
    valor_encontrado: Any
    diferencia: Optional[Any] = None
    registros_afectados: int = 0
    pasos_resolucion: Optional[List[str]] = None
    resuelta: bool = False

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'tipo': self.tipo,
            'severidad': self.severidad.value,
            'descripcion': self.descripcion,
            'timestamp': self.timestamp.isoformat(),
            'fuente_a': self.fuente_a,
            'fuente_b': self.fuente_b,
            'valor_esperado': str(self.valor_esperado),
            'valor_encontrado': str(self.valor_encontrado),
            'diferencia': str(self.diferencia) if self.diferencia else None,
            'registros_afectados': self.registros_afectados,
            'pasos_resolucion': self.pasos_resolucion,
            'resuelta': self.resuelta
        }


@dataclass
class AjusteRealizado:
    """Representa un ajuste realizado en el sistema"""
    id: str
    tipo: str  # 'automatico', 'manual'
    descripcion: str
    timestamp: datetime
    modulo: str
    campo_afectado: str
    valor_anterior: Any
    valor_nuevo: Any
    usuario: Optional[str] = None
    razon: Optional[str] = None
    reversible: bool = True
    revertido: bool = False

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'tipo': self.tipo,
            'descripcion': self.descripcion,
            'timestamp': self.timestamp.isoformat(),
            'modulo': self.modulo,
            'campo_afectado': self.campo_afectado,
            'valor_anterior': str(self.valor_anterior),
            'valor_nuevo': str(self.valor_nuevo),
            'usuario': self.usuario,
            'razon': self.razon,
            'reversible': self.reversible,
            'revertido': self.revertido
        }


# ═══════════════════════════════════════════════════════════════
# CLASE PRINCIPAL: GESTOR DE ALERTAS
# ═══════════════════════════════════════════════════════════════

class GestorAlertas:
    """
    Sistema centralizado de gestión de alertas y eventos del sistema.

    Funcionalidades:
    - Registro y almacenamiento de alertas
    - Gestión de eventos de fases
    - Control del estado del Copiloto
    - Registro de discrepancias
    - Historial de ajustes
    - Notificaciones y callbacks
    - Persistencia en archivo

    Uso:
        gestor = GestorAlertas()

        # Registrar alerta
        gestor.registrar_alerta(
            tipo=TipoAlerta.ERROR_CRITICO,
            severidad=SeveridadAlerta.CRITICO,
            titulo="Error en conexión DB",
            mensaje="No se pudo conectar a DB2",
            modulo="db_connection",
            pasos_solucion=["Verificar credenciales", "Revisar firewall"]
        )

        # Iniciar fase
        gestor.iniciar_fase(FaseSistema.VALIDACION)

        # Activar copiloto
        gestor.activar_copiloto(razon="Inicio de sesión de monitoreo")
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        """Implementación de Singleton thread-safe"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, archivo_log: Optional[Path] = None,
                 enviar_notificaciones: bool = True):
        """
        Inicializa el gestor de alertas

        Args:
            archivo_log: Ruta para persistir alertas (JSON)
            enviar_notificaciones: Si se deben enviar notificaciones por email
        """
        # Evitar reinicialización del singleton
        if hasattr(self, '_initialized') and self._initialized:
            return

        self._initialized = True

        # Almacenamiento de alertas y eventos
        self.alertas: List[Alerta] = []
        self.eventos_fases: List[EventoFase] = []
        self.eventos_copiloto: List[EventoCopiloto] = []
        self.discrepancias: List[Discrepancia] = []
        self.ajustes: List[AjusteRealizado] = []

        # Estados actuales
        self.estado_sistema = EstadoSistema.INACTIVO
        self.estado_copiloto = EstadoCopiloto.INACTIVO
        self.fase_actual: Optional[FaseSistema] = None
        self.fase_inicio_timestamp: Optional[datetime] = None

        # Configuración
        self.archivo_log = archivo_log or PATHS.get('logs', Path('./output/logs')) / 'alertas_sistema.json'
        self.enviar_notificaciones = enviar_notificaciones

        # Callbacks para notificaciones
        self._callbacks_alerta: List[Callable[[Alerta], None]] = []
        self._callbacks_fase: List[Callable[[EventoFase], None]] = []
        self._callbacks_copiloto: List[Callable[[EventoCopiloto], None]] = []

        # Contadores de sesión
        self.contador_alertas = 0
        self.contador_errores_criticos = 0
        self.contador_correcciones = 0

        # Timestamp de inicio
        self.timestamp_inicio = datetime.now()

        logger.info("✅ GestorAlertas inicializado")

    # ═══════════════════════════════════════════════════════════════
    # GESTIÓN DE ALERTAS
    # ═══════════════════════════════════════════════════════════════

    def registrar_alerta(
        self,
        tipo: TipoAlerta,
        severidad: SeveridadAlerta,
        titulo: str,
        mensaje: str,
        modulo: str,
        detalles: Optional[Dict[str, Any]] = None,
        pasos_solucion: Optional[List[str]] = None,
        datos_afectados: Optional[Dict[str, Any]] = None
    ) -> Alerta:
        """
        Registra una nueva alerta en el sistema

        Args:
            tipo: Tipo de alerta
            severidad: Nivel de severidad
            titulo: Título breve de la alerta
            mensaje: Descripción detallada
            modulo: Módulo que genera la alerta
            detalles: Información adicional
            pasos_solucion: Lista de pasos para resolver
            datos_afectados: Datos relacionados con la alerta

        Returns:
            Alerta registrada
        """
        self.contador_alertas += 1

        if severidad == SeveridadAlerta.CRITICO:
            self.contador_errores_criticos += 1

        alerta = Alerta(
            id=f"ALT-{self.contador_alertas:05d}",
            tipo=tipo,
            severidad=severidad,
            titulo=titulo,
            mensaje=mensaje,
            timestamp=datetime.now(),
            modulo=modulo,
            detalles=detalles,
            pasos_solucion=pasos_solucion,
            datos_afectados=datos_afectados
        )

        self.alertas.append(alerta)

        # Log según severidad
        log_msg = f"{alerta}"
        if severidad == SeveridadAlerta.CRITICO:
            logger.critical(log_msg)
        elif severidad == SeveridadAlerta.ALTO:
            logger.error(log_msg)
        elif severidad == SeveridadAlerta.MEDIO:
            logger.warning(log_msg)
        else:
            logger.info(log_msg)

        # Ejecutar callbacks
        for callback in self._callbacks_alerta:
            try:
                callback(alerta)
            except Exception as e:
                logger.error(f"Error en callback de alerta: {e}")

        # Persistir
        self._persistir_alertas()

        return alerta

    def resolver_alerta(self, alerta_id: str, notas: Optional[str] = None) -> bool:
        """
        Marca una alerta como resuelta

        Args:
            alerta_id: ID de la alerta a resolver
            notas: Notas sobre la resolución

        Returns:
            True si se resolvió correctamente
        """
        for alerta in self.alertas:
            if alerta.id == alerta_id:
                alerta.resuelta = True
                alerta.fecha_resolucion = datetime.now()
                alerta.resolucion_notas = notas
                logger.info(f"✅ Alerta {alerta_id} marcada como resuelta")
                self._persistir_alertas()
                return True

        logger.warning(f"⚠️ Alerta {alerta_id} no encontrada")
        return False

    def obtener_alertas_activas(self, severidad_minima: Optional[SeveridadAlerta] = None) -> List[Alerta]:
        """
        Obtiene las alertas no resueltas

        Args:
            severidad_minima: Filtrar por severidad mínima

        Returns:
            Lista de alertas activas
        """
        alertas_activas = [a for a in self.alertas if not a.resuelta]

        if severidad_minima:
            orden_severidad = {
                SeveridadAlerta.CRITICO: 5,
                SeveridadAlerta.ALTO: 4,
                SeveridadAlerta.MEDIO: 3,
                SeveridadAlerta.BAJO: 2,
                SeveridadAlerta.INFO: 1,
                SeveridadAlerta.EXITO: 0,
                SeveridadAlerta.DEBUG: -1
            }
            nivel_minimo = orden_severidad.get(severidad_minima, 0)
            alertas_activas = [
                a for a in alertas_activas
                if orden_severidad.get(a.severidad, 0) >= nivel_minimo
            ]

        return alertas_activas

    # ═══════════════════════════════════════════════════════════════
    # GESTIÓN DE FASES DEL SISTEMA
    # ═══════════════════════════════════════════════════════════════

    def iniciar_fase(self, fase: FaseSistema, mensaje: Optional[str] = None) -> EventoFase:
        """
        Registra el inicio de una fase del sistema

        Args:
            fase: Fase que inicia
            mensaje: Mensaje descriptivo opcional

        Returns:
            Evento de fase registrado
        """
        self.fase_actual = fase
        self.fase_inicio_timestamp = datetime.now()

        evento = EventoFase(
            id=f"FASE-{len(self.eventos_fases) + 1:04d}",
            fase=fase,
            estado='iniciada',
            timestamp=datetime.now(),
            mensaje=mensaje or f"Fase {fase.value} iniciada"
        )

        self.eventos_fases.append(evento)

        # Registrar alerta informativa
        self.registrar_alerta(
            tipo=TipoAlerta.FASE_INICIADA,
            severidad=SeveridadAlerta.INFO,
            titulo=f"Fase Iniciada: {fase.value}",
            mensaje=mensaje or f"Se inició la fase {fase.value}",
            modulo="gestor_alertas"
        )

        logger.info(f"▶️ Fase iniciada: {fase.value}")

        # Callbacks
        for callback in self._callbacks_fase:
            try:
                callback(evento)
            except Exception as e:
                logger.error(f"Error en callback de fase: {e}")

        return evento

    def completar_fase(
        self,
        fase: Optional[FaseSistema] = None,
        metricas: Optional[Dict[str, Any]] = None,
        mensaje: Optional[str] = None
    ) -> EventoFase:
        """
        Registra la finalización exitosa de una fase

        Args:
            fase: Fase completada (usa la actual si no se especifica)
            metricas: Métricas de la fase
            mensaje: Mensaje de completación

        Returns:
            Evento de fase registrado
        """
        fase = fase or self.fase_actual

        duracion = None
        if self.fase_inicio_timestamp:
            duracion = (datetime.now() - self.fase_inicio_timestamp).total_seconds()

        evento = EventoFase(
            id=f"FASE-{len(self.eventos_fases) + 1:04d}",
            fase=fase,
            estado='completada',
            timestamp=datetime.now(),
            duracion_segundos=duracion,
            mensaje=mensaje or f"Fase {fase.value} completada",
            metricas=metricas
        )

        self.eventos_fases.append(evento)

        # Registrar alerta de éxito
        self.registrar_alerta(
            tipo=TipoAlerta.FASE_COMPLETADA,
            severidad=SeveridadAlerta.EXITO,
            titulo=f"Fase Completada: {fase.value}",
            mensaje=f"Fase completada en {duracion:.2f}s" if duracion else "Fase completada",
            modulo="gestor_alertas",
            detalles={'metricas': metricas, 'duracion_segundos': duracion}
        )

        logger.info(f"✅ Fase completada: {fase.value} ({duracion:.2f}s)" if duracion else f"✅ Fase completada: {fase.value}")

        self.fase_actual = None
        self.fase_inicio_timestamp = None

        return evento

    def error_fase(
        self,
        fase: Optional[FaseSistema] = None,
        errores: Optional[List[str]] = None,
        mensaje: Optional[str] = None
    ) -> EventoFase:
        """
        Registra un error en la fase actual

        Args:
            fase: Fase con error
            errores: Lista de errores detectados
            mensaje: Mensaje de error

        Returns:
            Evento de fase registrado
        """
        fase = fase or self.fase_actual

        duracion = None
        if self.fase_inicio_timestamp:
            duracion = (datetime.now() - self.fase_inicio_timestamp).total_seconds()

        evento = EventoFase(
            id=f"FASE-{len(self.eventos_fases) + 1:04d}",
            fase=fase,
            estado='error',
            timestamp=datetime.now(),
            duracion_segundos=duracion,
            mensaje=mensaje or f"Error en fase {fase.value}",
            errores=errores
        )

        self.eventos_fases.append(evento)

        # Registrar alerta de error
        self.registrar_alerta(
            tipo=TipoAlerta.FASE_ERROR,
            severidad=SeveridadAlerta.ALTO,
            titulo=f"Error en Fase: {fase.value}",
            mensaje=mensaje or "Se produjo un error durante la ejecución de la fase",
            modulo="gestor_alertas",
            detalles={'errores': errores},
            pasos_solucion=[
                "Revisar los logs del sistema",
                "Verificar la configuración del módulo",
                "Reintentar la operación",
                "Contactar al administrador si persiste"
            ]
        )

        logger.error(f"❌ Error en fase: {fase.value}")

        self.fase_actual = None
        self.fase_inicio_timestamp = None

        return evento

    # ═══════════════════════════════════════════════════════════════
    # GESTIÓN DEL MODO COPILOTO
    # ═══════════════════════════════════════════════════════════════

    def activar_copiloto(self, razon: str, detalles: Optional[Dict] = None) -> EventoCopiloto:
        """
        Activa el modo Copiloto

        Args:
            razon: Razón de la activación
            detalles: Detalles adicionales

        Returns:
            Evento de copiloto registrado
        """
        estado_anterior = self.estado_copiloto
        self.estado_copiloto = EstadoCopiloto.ACTIVO

        evento = EventoCopiloto(
            id=f"COP-{len(self.eventos_copiloto) + 1:04d}",
            estado_anterior=estado_anterior,
            estado_nuevo=EstadoCopiloto.ACTIVO,
            timestamp=datetime.now(),
            razon=razon,
            detalles=detalles
        )

        self.eventos_copiloto.append(evento)

        self.registrar_alerta(
            tipo=TipoAlerta.COPILOTO_ACTIVADO,
            severidad=SeveridadAlerta.INFO,
            titulo="🤖 Modo Copiloto Activado",
            mensaje=f"El sistema entrará en modo de corrección automática. Razón: {razon}",
            modulo="copiloto"
        )

        logger.info(f"🤖 Copiloto ACTIVADO: {razon}")

        # Callbacks
        for callback in self._callbacks_copiloto:
            try:
                callback(evento)
            except Exception as e:
                logger.error(f"Error en callback de copiloto: {e}")

        return evento

    def desactivar_copiloto(
        self,
        razon: str,
        anomalias_procesadas: int = 0,
        correcciones_realizadas: int = 0,
        correcciones_fallidas: int = 0
    ) -> EventoCopiloto:
        """
        Desactiva el modo Copiloto

        Args:
            razon: Razón de la desactivación
            anomalias_procesadas: Total de anomalías procesadas
            correcciones_realizadas: Correcciones exitosas
            correcciones_fallidas: Correcciones fallidas

        Returns:
            Evento de copiloto registrado
        """
        estado_anterior = self.estado_copiloto
        self.estado_copiloto = EstadoCopiloto.INACTIVO

        evento = EventoCopiloto(
            id=f"COP-{len(self.eventos_copiloto) + 1:04d}",
            estado_anterior=estado_anterior,
            estado_nuevo=EstadoCopiloto.INACTIVO,
            timestamp=datetime.now(),
            razon=razon,
            anomalias_procesadas=anomalias_procesadas,
            correcciones_realizadas=correcciones_realizadas,
            correcciones_fallidas=correcciones_fallidas
        )

        self.eventos_copiloto.append(evento)
        self.contador_correcciones += correcciones_realizadas

        resumen = (
            f"Anomalías procesadas: {anomalias_procesadas}, "
            f"Correcciones: {correcciones_realizadas} exitosas / {correcciones_fallidas} fallidas"
        )

        self.registrar_alerta(
            tipo=TipoAlerta.COPILOTO_DESACTIVADO,
            severidad=SeveridadAlerta.INFO,
            titulo="🛑 Modo Copiloto Desactivado",
            mensaje=f"El sistema dejará de enviar alertas de corrección. {resumen}",
            modulo="copiloto",
            detalles={
                'anomalias_procesadas': anomalias_procesadas,
                'correcciones_realizadas': correcciones_realizadas,
                'correcciones_fallidas': correcciones_fallidas
            }
        )

        logger.info(f"🛑 Copiloto DESACTIVADO: {razon}")

        for callback in self._callbacks_copiloto:
            try:
                callback(evento)
            except Exception as e:
                logger.error(f"Error en callback de copiloto: {e}")

        return evento

    def pausar_copiloto(self, razon: str) -> EventoCopiloto:
        """Pausa temporalmente el modo Copiloto"""
        estado_anterior = self.estado_copiloto
        self.estado_copiloto = EstadoCopiloto.PAUSADO

        evento = EventoCopiloto(
            id=f"COP-{len(self.eventos_copiloto) + 1:04d}",
            estado_anterior=estado_anterior,
            estado_nuevo=EstadoCopiloto.PAUSADO,
            timestamp=datetime.now(),
            razon=razon
        )

        self.eventos_copiloto.append(evento)

        self.registrar_alerta(
            tipo=TipoAlerta.COPILOTO_PAUSADO,
            severidad=SeveridadAlerta.INFO,
            titulo="⏸️ Modo Copiloto Pausado",
            mensaje=f"Alertas de corrección pausadas temporalmente. Razón: {razon}",
            modulo="copiloto"
        )

        logger.info(f"⏸️ Copiloto PAUSADO: {razon}")
        return evento

    def reanudar_copiloto(self, razon: str) -> EventoCopiloto:
        """Reanuda el modo Copiloto después de una pausa"""
        estado_anterior = self.estado_copiloto
        self.estado_copiloto = EstadoCopiloto.ACTIVO

        evento = EventoCopiloto(
            id=f"COP-{len(self.eventos_copiloto) + 1:04d}",
            estado_anterior=estado_anterior,
            estado_nuevo=EstadoCopiloto.ACTIVO,
            timestamp=datetime.now(),
            razon=razon
        )

        self.eventos_copiloto.append(evento)

        self.registrar_alerta(
            tipo=TipoAlerta.COPILOTO_REANUDADO,
            severidad=SeveridadAlerta.INFO,
            titulo="▶️ Modo Copiloto Reanudado",
            mensaje=f"Se reanudan las alertas de corrección. Razón: {razon}",
            modulo="copiloto"
        )

        logger.info(f"▶️ Copiloto REANUDADO: {razon}")
        return evento

    # ═══════════════════════════════════════════════════════════════
    # GESTIÓN DEL ESTADO DEL SISTEMA
    # ═══════════════════════════════════════════════════════════════

    def sistema_iniciado(self) -> Alerta:
        """Registra el inicio del sistema"""
        self.estado_sistema = EstadoSistema.ACTIVO
        self.timestamp_inicio = datetime.now()

        return self.registrar_alerta(
            tipo=TipoAlerta.SISTEMA_INICIADO,
            severidad=SeveridadAlerta.EXITO,
            titulo="🚀 Sistema SAC Iniciado",
            mensaje=f"Sistema de Automatización de Consultas iniciado correctamente. CEDIS: {CEDIS.get('name', '427')}",
            modulo="sistema",
            detalles={'cedis': CEDIS, 'timestamp_inicio': self.timestamp_inicio.isoformat()}
        )

    def sistema_detenido(self, razon: str = "Detención programada") -> Alerta:
        """Registra la detención del sistema"""
        self.estado_sistema = EstadoSistema.INACTIVO
        duracion = datetime.now() - self.timestamp_inicio

        return self.registrar_alerta(
            tipo=TipoAlerta.SISTEMA_DETENIDO,
            severidad=SeveridadAlerta.INFO,
            titulo="🔴 Sistema SAC Detenido",
            mensaje=f"Sistema detenido después de {duracion}. Razón: {razon}",
            modulo="sistema",
            detalles={
                'duracion_total': str(duracion),
                'alertas_totales': self.contador_alertas,
                'errores_criticos': self.contador_errores_criticos,
                'correcciones': self.contador_correcciones
            }
        )

    def sistema_caido(self, error: str, detalles: Optional[Dict] = None) -> Alerta:
        """Registra una caída del sistema"""
        self.estado_sistema = EstadoSistema.EN_ERROR

        return self.registrar_alerta(
            tipo=TipoAlerta.SISTEMA_CAIDO,
            severidad=SeveridadAlerta.CRITICO,
            titulo="💀 CAÍDA DEL SISTEMA",
            mensaje=f"El sistema ha caído inesperadamente. Error: {error}",
            modulo="sistema",
            detalles=detalles,
            pasos_solucion=[
                "1. Verificar logs del sistema en output/logs/",
                "2. Revisar conexión a base de datos",
                "3. Verificar servicios de red",
                "4. Reiniciar el servicio: python main.py",
                "5. Contactar a TI si el problema persiste"
            ]
        )

    def sistema_recuperado(self) -> Alerta:
        """Registra la recuperación del sistema después de una caída"""
        self.estado_sistema = EstadoSistema.ACTIVO

        return self.registrar_alerta(
            tipo=TipoAlerta.SISTEMA_RECUPERADO,
            severidad=SeveridadAlerta.EXITO,
            titulo="✅ Sistema Recuperado",
            mensaje="El sistema se ha recuperado y está operando normalmente",
            modulo="sistema"
        )

    # ═══════════════════════════════════════════════════════════════
    # GESTIÓN DEL MONITOREO
    # ═══════════════════════════════════════════════════════════════

    def monitoreo_iniciado(self, intervalo_segundos: int = 60) -> Alerta:
        """Registra el inicio del modo monitoreo"""
        return self.registrar_alerta(
            tipo=TipoAlerta.MONITOREO_INICIADO,
            severidad=SeveridadAlerta.INFO,
            titulo="👁️ Modo Monitoreo Activado",
            mensaje=f"El sistema monitoreará cambios cada {intervalo_segundos} segundos",
            modulo="monitoreo",
            detalles={'intervalo_segundos': intervalo_segundos}
        )

    def monitoreo_detenido(self, razon: str) -> Alerta:
        """Registra la detención del modo monitoreo"""
        return self.registrar_alerta(
            tipo=TipoAlerta.MONITOREO_DETENIDO,
            severidad=SeveridadAlerta.INFO,
            titulo="🔕 Modo Monitoreo Desactivado",
            mensaje=f"Se dejan de enviar alertas de monitoreo. Razón: {razon}",
            modulo="monitoreo"
        )

    # ═══════════════════════════════════════════════════════════════
    # GESTIÓN DE DISCREPANCIAS
    # ═══════════════════════════════════════════════════════════════

    def registrar_discrepancia(
        self,
        tipo: str,
        severidad: SeveridadAlerta,
        descripcion: str,
        fuente_a: str,
        fuente_b: str,
        valor_esperado: Any,
        valor_encontrado: Any,
        registros_afectados: int = 0,
        pasos_resolucion: Optional[List[str]] = None
    ) -> Discrepancia:
        """
        Registra una discrepancia detectada entre fuentes de datos

        Args:
            tipo: Tipo de discrepancia
            severidad: Nivel de severidad
            descripcion: Descripción de la discrepancia
            fuente_a: Primera fuente de datos
            fuente_b: Segunda fuente de datos
            valor_esperado: Valor que se esperaba
            valor_encontrado: Valor que se encontró
            registros_afectados: Cantidad de registros afectados
            pasos_resolucion: Pasos para resolver la discrepancia

        Returns:
            Discrepancia registrada
        """
        # Calcular diferencia si es numérico
        diferencia = None
        try:
            if isinstance(valor_esperado, (int, float)) and isinstance(valor_encontrado, (int, float)):
                diferencia = valor_encontrado - valor_esperado
        except (TypeError, ValueError):
            pass

        discrepancia = Discrepancia(
            id=f"DIS-{len(self.discrepancias) + 1:04d}",
            tipo=tipo,
            severidad=severidad,
            descripcion=descripcion,
            timestamp=datetime.now(),
            fuente_a=fuente_a,
            fuente_b=fuente_b,
            valor_esperado=valor_esperado,
            valor_encontrado=valor_encontrado,
            diferencia=diferencia,
            registros_afectados=registros_afectados,
            pasos_resolucion=pasos_resolucion or [
                "1. Verificar datos en ambas fuentes",
                "2. Identificar la fuente correcta",
                "3. Corregir los datos inconsistentes",
                "4. Validar la corrección"
            ]
        )

        self.discrepancias.append(discrepancia)

        # Registrar también como alerta
        self.registrar_alerta(
            tipo=TipoAlerta.DISCREPANCIA_DETECTADA,
            severidad=severidad,
            titulo=f"⚡ Discrepancia: {tipo}",
            mensaje=descripcion,
            modulo="validacion",
            detalles={
                'fuente_a': fuente_a,
                'fuente_b': fuente_b,
                'valor_esperado': str(valor_esperado),
                'valor_encontrado': str(valor_encontrado),
                'diferencia': str(diferencia) if diferencia else None,
                'registros_afectados': registros_afectados
            },
            pasos_solucion=pasos_resolucion
        )

        logger.warning(f"⚡ Discrepancia detectada: {tipo} - {descripcion}")

        return discrepancia

    def resolver_discrepancia(self, discrepancia_id: str) -> bool:
        """Marca una discrepancia como resuelta"""
        for disc in self.discrepancias:
            if disc.id == discrepancia_id:
                disc.resuelta = True
                logger.info(f"✅ Discrepancia {discrepancia_id} resuelta")
                return True
        return False

    # ═══════════════════════════════════════════════════════════════
    # GESTIÓN DE AJUSTES
    # ═══════════════════════════════════════════════════════════════

    def registrar_ajuste(
        self,
        tipo: str,
        descripcion: str,
        modulo: str,
        campo_afectado: str,
        valor_anterior: Any,
        valor_nuevo: Any,
        usuario: Optional[str] = None,
        razon: Optional[str] = None,
        reversible: bool = True
    ) -> AjusteRealizado:
        """
        Registra un ajuste realizado en el sistema

        Args:
            tipo: 'automatico' o 'manual'
            descripcion: Descripción del ajuste
            modulo: Módulo afectado
            campo_afectado: Campo que fue modificado
            valor_anterior: Valor antes del ajuste
            valor_nuevo: Valor después del ajuste
            usuario: Usuario que realizó el ajuste (si es manual)
            razon: Razón del ajuste
            reversible: Si el ajuste puede revertirse

        Returns:
            Ajuste registrado
        """
        ajuste = AjusteRealizado(
            id=f"AJU-{len(self.ajustes) + 1:04d}",
            tipo=tipo,
            descripcion=descripcion,
            timestamp=datetime.now(),
            modulo=modulo,
            campo_afectado=campo_afectado,
            valor_anterior=valor_anterior,
            valor_nuevo=valor_nuevo,
            usuario=usuario,
            razon=razon,
            reversible=reversible
        )

        self.ajustes.append(ajuste)

        # Registrar como alerta
        tipo_alerta = TipoAlerta.AJUSTE_AUTOMATICO if tipo == 'automatico' else TipoAlerta.AJUSTE_MANUAL

        self.registrar_alerta(
            tipo=tipo_alerta,
            severidad=SeveridadAlerta.INFO,
            titulo=f"🔧 Ajuste {'Automático' if tipo == 'automatico' else 'Manual'}",
            mensaje=descripcion,
            modulo=modulo,
            detalles={
                'campo': campo_afectado,
                'valor_anterior': str(valor_anterior),
                'valor_nuevo': str(valor_nuevo),
                'usuario': usuario,
                'razon': razon
            }
        )

        logger.info(f"🔧 Ajuste registrado: {descripcion}")

        return ajuste

    def revertir_ajuste(self, ajuste_id: str) -> bool:
        """
        Revierte un ajuste previamente realizado

        Args:
            ajuste_id: ID del ajuste a revertir

        Returns:
            True si se revirtió correctamente
        """
        for ajuste in self.ajustes:
            if ajuste.id == ajuste_id:
                if not ajuste.reversible:
                    logger.warning(f"⚠️ Ajuste {ajuste_id} no es reversible")
                    return False

                if ajuste.revertido:
                    logger.warning(f"⚠️ Ajuste {ajuste_id} ya fue revertido")
                    return False

                ajuste.revertido = True

                self.registrar_alerta(
                    tipo=TipoAlerta.AJUSTE_REVERTIDO,
                    severidad=SeveridadAlerta.INFO,
                    titulo="↩️ Ajuste Revertido",
                    mensaje=f"Se revirtió el ajuste: {ajuste.descripcion}",
                    modulo=ajuste.modulo,
                    detalles={
                        'ajuste_id': ajuste_id,
                        'campo': ajuste.campo_afectado,
                        'valor_restaurado': str(ajuste.valor_anterior)
                    }
                )

                logger.info(f"↩️ Ajuste {ajuste_id} revertido")
                return True

        return False

    # ═══════════════════════════════════════════════════════════════
    # DETECCIÓN DE NUEVA INFORMACIÓN
    # ═══════════════════════════════════════════════════════════════

    def nueva_informacion_detectada(
        self,
        tipo_dato: str,
        cantidad: int,
        detalles: Optional[Dict] = None,
        requiere_accion: bool = False
    ) -> Alerta:
        """
        Registra la detección de nueva información en el sistema

        Args:
            tipo_dato: Tipo de dato detectado (OC, ASN, Distribución, etc.)
            cantidad: Cantidad de nuevos registros
            detalles: Información adicional
            requiere_accion: Si requiere acción del usuario

        Returns:
            Alerta registrada
        """
        severidad = SeveridadAlerta.MEDIO if requiere_accion else SeveridadAlerta.INFO

        return self.registrar_alerta(
            tipo=TipoAlerta.NUEVA_INFORMACION,
            severidad=severidad,
            titulo=f"📥 Nueva Información: {tipo_dato}",
            mensaje=f"Se detectaron {cantidad} nuevo(s) registro(s) de tipo {tipo_dato}",
            modulo="deteccion",
            detalles=detalles,
            pasos_solucion=[
                "1. Revisar los nuevos registros",
                "2. Validar la información",
                "3. Procesar según corresponda"
            ] if requiere_accion else None
        )

    # ═══════════════════════════════════════════════════════════════
    # ERRORES CON PASOS DE SOLUCIÓN
    # ═══════════════════════════════════════════════════════════════

    def registrar_error(
        self,
        severidad: SeveridadAlerta,
        titulo: str,
        mensaje: str,
        modulo: str,
        excepcion: Optional[Exception] = None,
        pasos_solucion: Optional[List[str]] = None,
        datos_afectados: Optional[Dict] = None
    ) -> Alerta:
        """
        Registra un error con pasos de solución detallados

        Args:
            severidad: Nivel de severidad del error
            titulo: Título del error
            mensaje: Descripción del error
            modulo: Módulo donde ocurrió
            excepcion: Excepción original (si aplica)
            pasos_solucion: Lista de pasos para resolver
            datos_afectados: Datos relacionados con el error

        Returns:
            Alerta registrada
        """
        tipo_alerta = {
            SeveridadAlerta.CRITICO: TipoAlerta.ERROR_CRITICO,
            SeveridadAlerta.ALTO: TipoAlerta.ERROR_ALTO,
            SeveridadAlerta.MEDIO: TipoAlerta.ERROR_MEDIO,
            SeveridadAlerta.BAJO: TipoAlerta.ERROR_BAJO,
        }.get(severidad, TipoAlerta.ADVERTENCIA)

        detalles = {}
        if excepcion:
            detalles['excepcion'] = str(excepcion)
            detalles['tipo_excepcion'] = type(excepcion).__name__

        # Pasos de solución por defecto según severidad
        if not pasos_solucion:
            if severidad == SeveridadAlerta.CRITICO:
                pasos_solucion = [
                    "1. DETENER operaciones actuales",
                    "2. Revisar logs del sistema inmediatamente",
                    "3. Verificar estado de la base de datos",
                    "4. Contactar al equipo de TI",
                    "5. Documentar el incidente"
                ]
            elif severidad == SeveridadAlerta.ALTO:
                pasos_solucion = [
                    "1. Revisar los logs del módulo afectado",
                    "2. Verificar la configuración",
                    "3. Reintentar la operación",
                    "4. Escalar si persiste"
                ]
            else:
                pasos_solucion = [
                    "1. Revisar el mensaje de error",
                    "2. Verificar los datos de entrada",
                    "3. Reintentar la operación"
                ]

        return self.registrar_alerta(
            tipo=tipo_alerta,
            severidad=severidad,
            titulo=titulo,
            mensaje=mensaje,
            modulo=modulo,
            detalles=detalles,
            pasos_solucion=pasos_solucion,
            datos_afectados=datos_afectados
        )

    # ═══════════════════════════════════════════════════════════════
    # CALLBACKS Y SUSCRIPCIONES
    # ═══════════════════════════════════════════════════════════════

    def suscribir_alertas(self, callback: Callable[[Alerta], None]) -> None:
        """Suscribe un callback para recibir nuevas alertas"""
        self._callbacks_alerta.append(callback)

    def suscribir_fases(self, callback: Callable[[EventoFase], None]) -> None:
        """Suscribe un callback para recibir eventos de fases"""
        self._callbacks_fase.append(callback)

    def suscribir_copiloto(self, callback: Callable[[EventoCopiloto], None]) -> None:
        """Suscribe un callback para recibir eventos del copiloto"""
        self._callbacks_copiloto.append(callback)

    # ═══════════════════════════════════════════════════════════════
    # REPORTES Y ESTADÍSTICAS
    # ═══════════════════════════════════════════════════════════════

    def obtener_resumen(self) -> Dict[str, Any]:
        """
        Obtiene un resumen completo del estado del sistema

        Returns:
            Diccionario con estadísticas y estado actual
        """
        alertas_por_severidad = {}
        for alerta in self.alertas:
            sev = alerta.severidad.value
            alertas_por_severidad[sev] = alertas_por_severidad.get(sev, 0) + 1

        tiempo_activo = datetime.now() - self.timestamp_inicio

        return {
            'timestamp': datetime.now().isoformat(),
            'estado_sistema': self.estado_sistema.value,
            'estado_copiloto': self.estado_copiloto.value,
            'fase_actual': self.fase_actual.value if self.fase_actual else None,
            'tiempo_activo': str(tiempo_activo),
            'estadisticas': {
                'alertas_totales': len(self.alertas),
                'alertas_activas': len([a for a in self.alertas if not a.resuelta]),
                'alertas_por_severidad': alertas_por_severidad,
                'errores_criticos': self.contador_errores_criticos,
                'discrepancias_totales': len(self.discrepancias),
                'discrepancias_activas': len([d for d in self.discrepancias if not d.resuelta]),
                'ajustes_realizados': len(self.ajustes),
                'ajustes_revertidos': len([a for a in self.ajustes if a.revertido]),
                'fases_completadas': len([e for e in self.eventos_fases if e.estado == 'completada']),
                'fases_con_error': len([e for e in self.eventos_fases if e.estado == 'error']),
                'correcciones_copiloto': self.contador_correcciones
            },
            'cedis': CEDIS
        }

    def generar_reporte_alertas(self, desde: Optional[datetime] = None) -> List[Dict]:
        """
        Genera un reporte de alertas

        Args:
            desde: Fecha desde la cual incluir alertas

        Returns:
            Lista de alertas como diccionarios
        """
        alertas = self.alertas
        if desde:
            alertas = [a for a in alertas if a.timestamp >= desde]

        return [a.to_dict() for a in alertas]

    def generar_historial_fases(self) -> List[Dict]:
        """Genera el historial de fases ejecutadas"""
        return [e.to_dict() for e in self.eventos_fases]

    def generar_historial_copiloto(self) -> List[Dict]:
        """Genera el historial de eventos del copiloto"""
        return [e.to_dict() for e in self.eventos_copiloto]

    # ═══════════════════════════════════════════════════════════════
    # PERSISTENCIA
    # ═══════════════════════════════════════════════════════════════

    def _persistir_alertas(self) -> None:
        """Persiste las alertas en archivo JSON"""
        try:
            # Crear directorio si no existe
            self.archivo_log.parent.mkdir(parents=True, exist_ok=True)

            datos = {
                'ultima_actualizacion': datetime.now().isoformat(),
                'resumen': self.obtener_resumen(),
                'alertas': [a.to_dict() for a in self.alertas[-100:]],  # Últimas 100
                'discrepancias': [d.to_dict() for d in self.discrepancias[-50:]],
                'ajustes': [a.to_dict() for a in self.ajustes[-50:]]
            }

            with open(self.archivo_log, 'w', encoding='utf-8') as f:
                json.dump(datos, f, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"Error al persistir alertas: {e}")

    def cargar_alertas(self) -> bool:
        """
        Carga alertas desde archivo JSON

        Returns:
            True si se cargaron correctamente
        """
        try:
            if not self.archivo_log.exists():
                return False

            with open(self.archivo_log, 'r', encoding='utf-8') as f:
                datos = json.load(f)

            logger.info(f"✅ Alertas cargadas desde {self.archivo_log}")
            return True

        except Exception as e:
            logger.error(f"Error al cargar alertas: {e}")
            return False

    # ═══════════════════════════════════════════════════════════════
    # UTILIDADES
    # ═══════════════════════════════════════════════════════════════

    def limpiar_alertas_antiguas(self, dias: int = 7) -> int:
        """
        Elimina alertas resueltas más antiguas que X días

        Args:
            dias: Días de antigüedad para eliminar

        Returns:
            Cantidad de alertas eliminadas
        """
        fecha_limite = datetime.now() - timedelta(days=dias)
        alertas_originales = len(self.alertas)

        self.alertas = [
            a for a in self.alertas
            if not a.resuelta or a.timestamp >= fecha_limite
        ]

        eliminadas = alertas_originales - len(self.alertas)

        if eliminadas > 0:
            logger.info(f"🗑️ {eliminadas} alertas antiguas eliminadas")

        return eliminadas

    def reset(self) -> None:
        """Reinicia el gestor de alertas (uso en testing)"""
        self.alertas.clear()
        self.eventos_fases.clear()
        self.eventos_copiloto.clear()
        self.discrepancias.clear()
        self.ajustes.clear()
        self.contador_alertas = 0
        self.contador_errores_criticos = 0
        self.contador_correcciones = 0
        self.estado_sistema = EstadoSistema.INACTIVO
        self.estado_copiloto = EstadoCopiloto.INACTIVO
        self.fase_actual = None
        self.timestamp_inicio = datetime.now()
        logger.info("🔄 GestorAlertas reiniciado")


# ═══════════════════════════════════════════════════════════════
# INSTANCIA GLOBAL (SINGLETON)
# ═══════════════════════════════════════════════════════════════

# Crear instancia global para uso en todo el sistema
gestor_alertas = GestorAlertas()


# ═══════════════════════════════════════════════════════════════
# FUNCIONES DE CONVENIENCIA
# ═══════════════════════════════════════════════════════════════

def alerta_critica(titulo: str, mensaje: str, modulo: str,
                   pasos: Optional[List[str]] = None) -> Alerta:
    """Función de conveniencia para alertas críticas"""
    return gestor_alertas.registrar_alerta(
        tipo=TipoAlerta.ERROR_CRITICO,
        severidad=SeveridadAlerta.CRITICO,
        titulo=titulo,
        mensaje=mensaje,
        modulo=modulo,
        pasos_solucion=pasos
    )


def alerta_info(titulo: str, mensaje: str, modulo: str) -> Alerta:
    """Función de conveniencia para alertas informativas"""
    return gestor_alertas.registrar_alerta(
        tipo=TipoAlerta.ADVERTENCIA,
        severidad=SeveridadAlerta.INFO,
        titulo=titulo,
        mensaje=mensaje,
        modulo=modulo
    )


def alerta_exito(titulo: str, mensaje: str, modulo: str) -> Alerta:
    """Función de conveniencia para alertas de éxito"""
    return gestor_alertas.registrar_alerta(
        tipo=TipoAlerta.DATOS_ACTUALIZADOS,
        severidad=SeveridadAlerta.EXITO,
        titulo=titulo,
        mensaje=mensaje,
        modulo=modulo
    )


# ═══════════════════════════════════════════════════════════════
# EXPORTACIONES
# ═══════════════════════════════════════════════════════════════

__all__ = [
    # Enumeraciones
    'TipoAlerta',
    'SeveridadAlerta',
    'EstadoSistema',
    'EstadoCopiloto',
    'FaseSistema',
    # Clases de datos
    'Alerta',
    'EventoFase',
    'EventoCopiloto',
    'Discrepancia',
    'AjusteRealizado',
    # Clase principal
    'GestorAlertas',
    # Instancia global
    'gestor_alertas',
    # Funciones de conveniencia
    'alerta_critica',
    'alerta_info',
    'alerta_exito',
]


# ═══════════════════════════════════════════════════════════════
# EJEMPLO DE USO
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("""
    ═══════════════════════════════════════════════════════════════
    MÓDULO DE ALERTAS Y MONITOREO - DEMOSTRACIÓN
    Sistema SAC - CEDIS Cancún 427
    ═══════════════════════════════════════════════════════════════
    """)

    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Obtener instancia del gestor
    gestor = GestorAlertas()

    # 1. Iniciar sistema
    print("\n📍 1. Iniciando sistema...")
    gestor.sistema_iniciado()

    # 2. Iniciar fase de validación
    print("\n📍 2. Iniciando fase de validación...")
    gestor.iniciar_fase(FaseSistema.VALIDACION, "Validando OCs del día")

    # 3. Activar copiloto
    print("\n📍 3. Activando modo Copiloto...")
    gestor.activar_copiloto("Inicio de sesión de monitoreo matutino")

    # 4. Detectar nueva información
    print("\n📍 4. Detectando nueva información...")
    gestor.nueva_informacion_detectada(
        tipo_dato="Órdenes de Compra",
        cantidad=15,
        detalles={'ocs': ['OC001', 'OC002', 'OC003']},
        requiere_accion=True
    )

    # 5. Registrar discrepancia
    print("\n📍 5. Registrando discrepancia...")
    gestor.registrar_discrepancia(
        tipo="CANTIDAD_OC_VS_DISTRIBUCION",
        severidad=SeveridadAlerta.ALTO,
        descripcion="La cantidad distribuida excede la cantidad de la OC",
        fuente_a="Orden de Compra",
        fuente_b="Distribuciones",
        valor_esperado=1000,
        valor_encontrado=1150,
        registros_afectados=5,
        pasos_resolucion=[
            "1. Verificar la OC original en Manhattan",
            "2. Revisar las distribuciones generadas",
            "3. Ajustar cantidades en el sistema",
            "4. Notificar a Planning"
        ]
    )

    # 6. Registrar error
    print("\n📍 6. Registrando error...")
    gestor.registrar_error(
        severidad=SeveridadAlerta.MEDIO,
        titulo="Error de conexión temporal",
        mensaje="Timeout al consultar tabla WMWHSE1.ASN",
        modulo="db_connection",
        pasos_solucion=[
            "1. Verificar estado de la red",
            "2. Reintentar la consulta",
            "3. Si persiste, revisar el servidor DB2"
        ]
    )

    # 7. Registrar ajuste
    print("\n📍 7. Registrando ajuste automático...")
    gestor.registrar_ajuste(
        tipo="automatico",
        descripcion="Ajuste de cantidad en distribución",
        modulo="copiloto_correcciones",
        campo_afectado="QUANTITY",
        valor_anterior=1150,
        valor_nuevo=1000,
        razon="Corrección por exceso detectado"
    )

    # 8. Completar fase
    print("\n📍 8. Completando fase...")
    gestor.completar_fase(
        metricas={'ocs_validadas': 15, 'errores_detectados': 2}
    )

    # 9. Pausar copiloto
    print("\n📍 9. Pausando copiloto...")
    gestor.pausar_copiloto("Pausa para almuerzo")

    # 10. Reanudar copiloto
    print("\n📍 10. Reanudando copiloto...")
    gestor.reanudar_copiloto("Fin de pausa")

    # 11. Desactivar copiloto
    print("\n📍 11. Desactivando copiloto...")
    gestor.desactivar_copiloto(
        razon="Fin de jornada",
        anomalias_procesadas=10,
        correcciones_realizadas=8,
        correcciones_fallidas=2
    )

    # 12. Mostrar resumen
    print("\n" + "═" * 60)
    print("📊 RESUMEN DEL SISTEMA")
    print("═" * 60)

    resumen = gestor.obtener_resumen()
    print(f"\n🔹 Estado del Sistema: {resumen['estado_sistema']}")
    print(f"🔹 Estado Copiloto: {resumen['estado_copiloto']}")
    print(f"🔹 Tiempo activo: {resumen['tiempo_activo']}")
    print(f"\n📈 Estadísticas:")
    for key, value in resumen['estadisticas'].items():
        print(f"   - {key}: {value}")

    # 13. Mostrar alertas activas
    alertas_activas = gestor.obtener_alertas_activas()
    print(f"\n⚠️ Alertas activas: {len(alertas_activas)}")
    for alerta in alertas_activas[:5]:
        print(f"   [{alerta.severidad.value}] {alerta.titulo}")

    # 14. Detener sistema
    print("\n📍 14. Deteniendo sistema...")
    gestor.sistema_detenido("Fin de demostración")

    print("\n" + "═" * 60)
    print("✅ Demostración completada")
    print("═" * 60)
