"""
═══════════════════════════════════════════════════════════════════════
AGENTE SAC SIEMPRE ACTIVO - MODO BACKGROUND CONTINUO
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════════════

Extensión del Agente SAC que proporciona:
- Funcionamiento continuo en segundo plano (modo daemon)
- Detección automática de inactividad del analista
- Activación automática del modo "copiloto" tras 30 min sin respuesta
- Múltiples formas de invocación (CLI, API HTTP, eventos del sistema)
- Comunicación automática entre departamentos
- Autonomía condicional con confirmación cuando sea necesario
- Monitoreo proactivo y alertas inteligentes

FILOSOFÍA:
    "Las máquinas y los sistemas al servicio de los analistas"
    El agente actúa de forma independiente cuando es apropiado,
    pero siempre respeta la autoridad y dirección del equipo humano.

MODOS DE OPERACIÓN:
    1. Normal: Espera invocación del usuario
    2. Copiloto: Activa automáticamente tras 30 min sin respuesta
    3. Servicio: Ejecuta tareas programadas en background
    4. Vigilancia: Monitorea eventos del sistema sin intervenir

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════════════
"""

import os
import sys
import json
import logging
import threading
import time
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from abc import ABC, abstractmethod
import hashlib
import signal

# Importar el agente existente
try:
    from .agente_sac import AgenteSAC, NivelAcceso, EstadoAgente, TipoInteraccion
    from config import PATHS, CEDIS, SYSTEM_CONFIG
except ImportError as e:
    print(f"⚠️ Error en importaciones: {e}")
    PATHS = {'output': Path('output')}
    CEDIS = {'code': '427', 'name': 'CEDIS Cancún'}
    SYSTEM_CONFIG = {}

# Configurar logging
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════
# CONSTANTES
# ═══════════════════════════════════════════════════════════════════════

AGENTE_SIEMPRE_ACTIVO_VERSION = "1.0.0"
TIMEOUT_INACTIVIDAD_MINUTOS = 30
INTERVALO_CHEQUEO_SEGUNDOS = 60
INTERVALO_TAREAS_AUTONOMAS_MINUTOS = 15


class EstadoCopilotos(Enum):
    """Estados específicos del modo copiloto"""
    DESACTIVADO = "desactivado"
    MONITOREANDO = "monitoreando"
    ACTIVO = "activo"
    PAUSADO = "pausado"


class NivelAutonomia(Enum):
    """Niveles de autonomía permitida"""
    MINIMA = "minima"           # Solo alertas, sin acciones
    BASICA = "basica"           # Tareas simples preautorizadas
    MEDIA = "media"             # Más tareas, requiere confirmación si hay usuario
    ALTA = "alta"               # Ejecuta sin confirmación en horario no laboral


class TipoTareaAutonoma(Enum):
    """Tipos de tareas que puede ejecutar automáticamente"""
    GENERACION_REPORTE = "generacion_reporte"
    VALIDACION_OC = "validacion_oc"
    SINCRONIZACION_DATOS = "sincronizacion_datos"
    ENVIO_ALERTA = "envio_alerta"
    NOTIFICACION = "notificacion"
    COMUNICACION_INTERDEPT = "comunicacion_interdept"
    LIMPIEZA_LOGS = "limpieza_logs"
    VERIFICACION_SALUD = "verificacion_salud"


class TipoEvento(Enum):
    """Tipos de eventos del sistema"""
    INACTIVIDAD = "inactividad"
    ACTIVIDAD = "actividad"
    ERROR_CRITICO = "error_critico"
    ALERTA = "alerta"
    TAREA_COMPLETADA = "tarea_completada"
    USUARIO_CONECTADO = "usuario_conectado"
    USUARIO_DESCONECTADO = "usuario_desconectado"


# ═══════════════════════════════════════════════════════════════════════
# DATACLASSES
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class ConfiguracionCopiloto:
    """Configuración del modo copiloto automático"""
    habilitado: bool = True
    timeout_minutos: int = TIMEOUT_INACTIVIDAD_MINUTOS
    nivel_autonomia: NivelAutonomia = NivelAutonomia.BASICA
    tareas_autorizadas: List[TipoTareaAutonoma] = field(default_factory=lambda: [
        TipoTareaAutonoma.GENERACION_REPORTE,
        TipoTareaAutonoma.ENVIO_ALERTA,
        TipoTareaAutonoma.NOTIFICACION,
        TipoTareaAutonoma.VERIFICACION_SALUD,
    ])
    notificar_al_activar: bool = True
    registrar_acciones: bool = True
    horario_inicio_no_laboral: str = "22:00"  # HH:MM
    horario_fin_no_laboral: str = "08:00"     # HH:MM


@dataclass
class EventoSistema:
    """Evento del sistema para auditoría"""
    tipo: TipoEvento
    timestamp: datetime = field(default_factory=datetime.now)
    usuario: Optional[str] = None
    detalles: Dict[str, Any] = field(default_factory=dict)
    severidad: str = "INFO"  # INFO, WARNING, ERROR, CRITICO
    procesado: bool = False


@dataclass
class TareaAutonoma:
    """Tarea a ejecutar automáticamente"""
    id: str
    tipo: TipoTareaAutonoma
    descripcion: str
    parametros: Dict[str, Any] = field(default_factory=dict)
    prioridad: int = 5  # 1-10, 10 es máxima
    requiere_confirmacion: bool = False
    ejecutada: bool = False
    resultado: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class EstadisticasAgente:
    """Estadísticas del funcionamiento del agente"""
    total_tareas_ejecutadas: int = 0
    total_errores: int = 0
    tiempo_actividad_total: float = 0.0  # segundos
    ultimo_evento: Optional[datetime] = None
    tareas_pendientes: int = 0
    modo_copiloto_activaciones: int = 0
    tiempo_en_copiloto_total: float = 0.0  # segundos


# ═══════════════════════════════════════════════════════════════════════
# MONITOR DE INACTIVIDAD
# ═══════════════════════════════════════════════════════════════════════

class MonitorInactividad:
    """Monitorea la inactividad del analista/usuario"""

    def __init__(self, timeout_minutos: int = TIMEOUT_INACTIVIDAD_MINUTOS):
        self.timeout = timedelta(minutes=timeout_minutos)
        self.ultima_actividad = datetime.now()
        self.actividad_registrada = []
        self._lock = threading.Lock()

    def registrar_actividad(self, usuario: Optional[str] = None, actividad: str = "interacción"):
        """Registra una actividad del usuario"""
        with self._lock:
            self.ultima_actividad = datetime.now()
            self.actividad_registrada.append({
                'timestamp': datetime.now(),
                'usuario': usuario,
                'tipo': actividad
            })

    def obtener_tiempo_inactivo(self) -> timedelta:
        """Obtiene el tiempo de inactividad actual"""
        with self._lock:
            return datetime.now() - self.ultima_actividad

    def esta_inactivo(self) -> bool:
        """Verifica si ha habido inactividad mayor al timeout"""
        return self.obtener_tiempo_inactivo() > self.timeout

    def obtener_ultimo_evento_actividad(self) -> Optional[Dict]:
        """Obtiene el último evento registrado"""
        with self._lock:
            return self.actividad_registrada[-1] if self.actividad_registrada else None


# ═══════════════════════════════════════════════════════════════════════
# AUTORIZADOR AUTÓNOMO
# ═══════════════════════════════════════════════════════════════════════

class AutorizadorAutonomo:
    """Determina qué acciones puede ejecutar el agente automáticamente"""

    def __init__(self, config: ConfiguracionCopiloto = None):
        self.config = config or ConfiguracionCopiloto()
        self._lock = threading.Lock()

    def puede_ejecutar_tarea(
        self,
        tarea: TipoTareaAutonoma,
        hay_usuario_activo: bool = False,
        nivel_critico: bool = False
    ) -> Tuple[bool, str]:
        """
        Determina si puede ejecutar una tarea automáticamente.

        Retorna: (puede_ejecutar, razon)
        """
        with self._lock:
            # Verificar si está en lista de autorizadas
            if tarea not in self.config.tareas_autorizadas:
                return False, f"Tarea {tarea.value} no está autorizada"

            # Si hay usuario activo, puede necesitar confirmación
            if hay_usuario_activo and self.config.nivel_autonomia in [
                NivelAutonomia.MINIMA,
                NivelAutonomia.BASICA
            ]:
                return False, "Usuario activo - requiere confirmación manual"

            # En horario no laboral, puede ejecutar más cosas
            if self._esta_en_horario_no_laboral():
                return True, "Horario no laboral - autorizado"

            # En horario laboral, restricciones mayores
            if self.config.nivel_autonomia == NivelAutonomia.ALTA:
                return True, "Nivel de autonomía alto"

            return True, "Autorizado"

    def _esta_en_horario_no_laboral(self) -> bool:
        """Verifica si está en horario no laboral"""
        hora_actual = datetime.now().hour
        # Convertir strings HH:MM a enteros
        inicio = int(self.config.horario_inicio_no_laboral.split(':')[0])
        fin = int(self.config.horario_fin_no_laboral.split(':')[0])

        if inicio > fin:  # Nocturno (22:00 a 08:00)
            return hora_actual >= inicio or hora_actual < fin
        else:  # Diurno (08:00 a 22:00)
            return fin <= hora_actual < inicio


# ═══════════════════════════════════════════════════════════════════════
# MOTOR DE TAREAS AUTÓNOMAS
# ═══════════════════════════════════════════════════════════════════════

class MotorTareasAutonomas:
    """Ejecuta tareas automáticamente en modo copiloto"""

    def __init__(self, agente: 'AgenteSAC' = None):
        self.agente = agente
        self.tareas_pendientes: List[TareaAutonoma] = []
        self.tareas_completadas: List[TareaAutonoma] = []
        self._lock = threading.Lock()
        self.callbacks: Dict[TipoTareaAutonoma, Callable] = {}

    def registrar_callback(self, tipo_tarea: TipoTareaAutonoma, callback: Callable):
        """Registra un callback para ejecutar un tipo de tarea"""
        self.callbacks[tipo_tarea] = callback

    def agregar_tarea(self, tarea: TareaAutonoma):
        """Agrega una tarea a la cola de ejecución"""
        with self._lock:
            self.tareas_pendientes.append(tarea)
            logger.info(f"✅ Tarea agregada: {tarea.id} - {tarea.tipo.value}")

    def obtener_proxima_tarea(self) -> Optional[TareaAutonoma]:
        """Obtiene la siguiente tarea con mayor prioridad"""
        with self._lock:
            if not self.tareas_pendientes:
                return None
            # Ordenar por prioridad (mayor primero)
            self.tareas_pendientes.sort(key=lambda t: t.prioridad, reverse=True)
            return self.tareas_pendientes[0]

    def ejecutar_tarea(self, tarea: TareaAutonoma) -> bool:
        """Ejecuta una tarea específica"""
        logger.info(f"🚀 Ejecutando tarea: {tarea.id}")

        try:
            # Obtener callback registrado
            callback = self.callbacks.get(tarea.tipo)
            if not callback:
                logger.warning(f"⚠️ No hay callback para {tarea.tipo.value}")
                tarea.resultado = "Sin callback registrado"
                return False

            # Ejecutar callback
            resultado = callback(tarea.parametros)
            tarea.resultado = str(resultado)
            tarea.ejecutada = True

            with self._lock:
                if tarea in self.tareas_pendientes:
                    self.tareas_pendientes.remove(tarea)
                self.tareas_completadas.append(tarea)

            logger.info(f"✅ Tarea completada: {tarea.id}")
            return True

        except Exception as e:
            logger.error(f"❌ Error en tarea {tarea.id}: {e}")
            tarea.resultado = f"Error: {str(e)}"
            return False

    def procesar_cola_tareas(self):
        """Procesa todas las tareas pendientes"""
        while True:
            tarea = self.obtener_proxima_tarea()
            if not tarea:
                break
            self.ejecutar_tarea(tarea)


# ═══════════════════════════════════════════════════════════════════════
# AGENTE SAC SIEMPRE ACTIVO - CLASE PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════

class AgenteSACSimpreActivo:
    """
    Agente SAC que funciona continuamente en background.
    Extiende AgenteSAC con capacidades de autonomía y modo copiloto.
    """

    def __init__(self, config: Optional[ConfiguracionCopiloto] = None):
        self.version = AGENTE_SIEMPRE_ACTIVO_VERSION
        self.config = config or ConfiguracionCopiloto()
        self.activo = True
        self.estado_copiloto = EstadoCopilotos.DESACTIVADO

        # Componentes
        self.monitor = MonitorInactividad(self.config.timeout_minutos)
        self.autorizador = AutorizadorAutonomo(self.config)
        self.motor_tareas = MotorTareasAutonomas()

        # Intenta cargar agente existente
        try:
            self.agente_sac = AgenteSAC()
        except Exception as e:
            logger.warning(f"⚠️ No se pudo cargar AgenteSAC: {e}")
            self.agente_sac = None

        # Estado
        self.estadisticas = EstadisticasAgente()
        self.eventos: List[EventoSistema] = []
        self._lock = threading.Lock()

        # Configurar signals para shutdown limpio
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)

        logger.info(f"🤖 Agente SAC Siempre Activo v{self.version} inicializado")

    def iniciar(self):
        """Inicia el agente en modo background continuo"""
        logger.info("🚀 Iniciando Agente SAC Siempre Activo en modo background...")

        # Hilos de trabajo
        hilos = [
            threading.Thread(target=self._monitorear_inactividad, daemon=True),
            threading.Thread(target=self._procesar_tareas_autonomas, daemon=True),
            threading.Thread(target=self._verificar_salud_sistema, daemon=True),
        ]

        for hilo in hilos:
            hilo.start()
            logger.info(f"✅ Hilo iniciado: {hilo.name}")

        # Mantener el agente activo
        try:
            while self.activo:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("⏹️ Deteniendo agente...")
            self._detener()

    def _monitorear_inactividad(self):
        """Monitorea inactividad y activa modo copiloto"""
        logger.info("📊 Monitor de inactividad iniciado")

        while self.activo:
            try:
                if self.monitor.esta_inactivo():
                    if self.estado_copiloto == EstadoCopilotos.DESACTIVADO:
                        self._activar_modo_copiloto()
                else:
                    if self.estado_copiloto == EstadoCopilotos.ACTIVO:
                        self._desactivar_modo_copiloto()

            except Exception as e:
                logger.error(f"❌ Error en monitor: {e}")

            time.sleep(INTERVALO_CHEQUEO_SEGUNDOS)

    def _procesar_tareas_autonomas(self):
        """Procesa tareas autónomas en segundo plano"""
        logger.info("🎯 Procesador de tareas autónomas iniciado")

        while self.activo:
            try:
                if self.estado_copiloto == EstadoCopilotos.ACTIVO:
                    self.motor_tareas.procesar_cola_tareas()

            except Exception as e:
                logger.error(f"❌ Error procesando tareas: {e}")
                self._registrar_evento(EventoSistema(
                    tipo=TipoEvento.ERROR_CRITICO,
                    detalles={'error': str(e), 'modulo': 'procesador_tareas'}
                ))

            time.sleep(INTERVALO_TAREAS_AUTONOMAS_MINUTOS * 60)

    def _verificar_salud_sistema(self):
        """Verifica la salud del sistema periódicamente"""
        logger.info("💚 Verificador de salud iniciado")

        while self.activo:
            try:
                # Verificación simple de salud
                self._registrar_evento(EventoSistema(
                    tipo=TipoEvento.VERIFICACION_SALUD,
                    detalles={
                        'estado_copiloto': self.estado_copiloto.value,
                        'tareas_pendientes': len(self.motor_tareas.tareas_pendientes),
                        'estadisticas': asdict(self.estadisticas)
                    }
                ))

            except Exception as e:
                logger.error(f"❌ Error verificando salud: {e}")

            time.sleep(60)  # Cada minuto

    def _activar_modo_copiloto(self):
        """Activa el modo copiloto automático"""
        logger.info("🤖 MODO COPILOTO ACTIVADO - Sin respuesta del usuario")
        self.estado_copiloto = EstadoCopilotos.ACTIVO
        self.estadisticas.modo_copiloto_activaciones += 1

        self._registrar_evento(EventoSistema(
            tipo=TipoEvento.INACTIVIDAD,
            severidad="WARNING",
            detalles={'tiempo_inactividad_minutos': self.config.timeout_minutos}
        ))

        if self.config.notificar_al_activar:
            self._enviar_notificacion_copiloto_activado()

    def _desactivar_modo_copiloto(self):
        """Desactiva el modo copiloto"""
        if self.estado_copiloto == EstadoCopilotos.ACTIVO:
            logger.info("👤 Actividad detectada - Modo copiloto desactivado")
            self.estado_copiloto = EstadoCopilotos.DESACTIVADO

            self._registrar_evento(EventoSistema(
                tipo=TipoEvento.ACTIVIDAD,
                severidad="INFO",
                detalles={'razon': 'Usuario activo nuevamente'}
            ))

    def _registrar_evento(self, evento: EventoSistema):
        """Registra un evento del sistema"""
        with self._lock:
            self.eventos.append(evento)
            # Mantener solo últimos 1000 eventos
            if len(self.eventos) > 1000:
                self.eventos = self.eventos[-1000:]

        logger.debug(f"📝 Evento registrado: {evento.tipo.value}")

    def _enviar_notificacion_copiloto_activado(self):
        """Envía notificación cuando se activa el copiloto"""
        try:
            # Aquí se podría integrar con email, Telegram, etc.
            logger.info("📧 Notificación: Modo copiloto activado (sin respuesta por 30 min)")
        except Exception as e:
            logger.error(f"❌ Error enviando notificación: {e}")

    def registrar_actividad_usuario(self, usuario: str, actividad: str = "interacción"):
        """Registra actividad del usuario para resetear el timer"""
        self.monitor.registrar_actividad(usuario, actividad)
        self._registrar_evento(EventoSistema(
            tipo=TipoEvento.ACTIVIDAD,
            usuario=usuario,
            detalles={'tipo_actividad': actividad}
        ))

    def obtener_estado(self) -> Dict[str, Any]:
        """Obtiene el estado actual del agente"""
        with self._lock:
            return {
                'version': self.version,
                'activo': self.activo,
                'estado_copiloto': self.estado_copiloto.value,
                'tiempo_inactivo': str(self.monitor.obtener_tiempo_inactivo()),
                'tareas_pendientes': len(self.motor_tareas.tareas_pendientes),
                'estadisticas': asdict(self.estadisticas),
                'timestamp': datetime.now().isoformat()
            }

    def _detener(self):
        """Detiene el agente limpiamente"""
        logger.info("🛑 Deteniendo Agente SAC Siempre Activo...")
        self.activo = False

    def _handle_shutdown(self, signum, frame):
        """Maneja señales de shutdown"""
        logger.info(f"⚠️ Señal de shutdown recibida (signum={signum})")
        self._detener()
        sys.exit(0)


# ═══════════════════════════════════════════════════════════════════════
# FUNCIONES DE UTILIDAD
# ═══════════════════════════════════════════════════════════════════════

def crear_agente_siempre_activo(
    timeout_minutos: int = TIMEOUT_INACTIVIDAD_MINUTOS,
    nivel_autonomia: NivelAutonomia = NivelAutonomia.BASICA
) -> AgenteSACSimpreActivo:
    """
    Factory para crear una instancia del agente siempre activo.
    """
    config = ConfiguracionCopiloto(
        timeout_minutos=timeout_minutos,
        nivel_autonomia=nivel_autonomia
    )
    return AgenteSACSimpreActivo(config)


# Instancia global del agente
_agente_global: Optional[AgenteSACSimpreActivo] = None


def obtener_agente_siempre_activo() -> AgenteSACSimpreActivo:
    """Obtiene o crea la instancia global del agente"""
    global _agente_global
    if _agente_global is None:
        _agente_global = crear_agente_siempre_activo()
    return _agente_global


if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Crear e iniciar agente
    agente = obtener_agente_siempre_activo()
    agente.iniciar()
