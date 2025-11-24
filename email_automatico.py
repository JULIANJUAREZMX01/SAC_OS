#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════════════════════
SISTEMA AUTOMÁTICO DE CORREOS
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════════════════════

Este módulo maneja el envío automático de correos en:
- Modo background (thread independiente)
- Modo daemon (servicio continuo)
- Modo scheduled (tareas programadas)

Características:
✅ Cola de envío automática
✅ Reintentos con backoff exponencial
✅ Detección de errores críticos
✅ Envío automático de alertas
✅ Histórico de envíos
✅ Thread-safe

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
═══════════════════════════════════════════════════════════════════════════════
"""

import logging
import threading
import time
import queue
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict
from enum import Enum
import json
from pathlib import Path
import traceback

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# ENUMS Y DATACLASSES
# ═══════════════════════════════════════════════════════════════════════════════

class TipoEmail(Enum):
    """Tipos de correos automáticos"""
    REPORTE_DIARIO = "reporte_diario"
    ALERTA_CRITICA = "alerta_critica"
    VALIDACION_OC = "validacion_oc"
    PROGRAMA_RECIBO = "programa_recibo"
    ERROR_SISTEMA = "error_sistema"
    CONFIRMACION = "confirmacion"
    RESUMEN_SEMANAL = "resumen_semanal"
    RECORDATORIO = "recordatorio"


@dataclass
class TareaEmail:
    """Representa una tarea de envío de email"""
    tipo: str
    destinatarios: List[str]
    asunto: str
    contenido: str
    datos: Dict[str, Any] = None
    archivos: List[str] = None
    prioritario: bool = False
    timestamp: datetime = None
    reintentos: int = 0
    max_reintentos: int = 3
    html: bool = True

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.datos is None:
            self.datos = {}
        if self.archivos is None:
            self.archivos = []

    def to_dict(self) -> Dict:
        """Convierte a diccionario para serialización"""
        d = asdict(self)
        d['timestamp'] = self.timestamp.isoformat()
        d['prioritario'] = self.prioritario
        d['html'] = self.html
        return d


class EstadoTarea(Enum):
    """Estado de una tarea de email"""
    PENDIENTE = "pendiente"
    ENVIANDO = "enviando"
    ENVIADO = "enviado"
    FALLIDO = "fallido"
    REINTENTANDO = "reintentando"


@dataclass
class ResultadoEmail:
    """Resultado del envío de un email"""
    tarea_id: str
    tipo: str
    estado: EstadoTarea
    timestamp: datetime
    destinatarios: List[str]
    mensaje_error: Optional[str] = None
    intentos: int = 0

    def to_dict(self) -> Dict:
        """Convierte a diccionario"""
        return {
            'tarea_id': self.tarea_id,
            'tipo': self.tipo,
            'estado': self.estado.value,
            'timestamp': self.timestamp.isoformat(),
            'destinatarios': self.destinatarios,
            'mensaje_error': self.mensaje_error,
            'intentos': self.intentos,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# GESTOR DE COLA DE EMAILS
# ═══════════════════════════════════════════════════════════════════════════════

class ColaEmails:
    """Gestiona la cola de correos a enviar"""

    def __init__(self, max_size: int = 100):
        self.cola = queue.Queue(maxsize=max_size)
        self.historial = []
        self.lock = threading.Lock()
        self.max_historial = 1000
        logger.info(f"✅ ColaEmails inicializada (max_size={max_size})")

    def agregar(self, tarea: TareaEmail) -> str:
        """Agrega una tarea a la cola"""
        tarea_id = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{id(tarea)}"
        try:
            self.cola.put((tarea_id, tarea), timeout=5)
            logger.info(f"✅ Tarea agregada a cola: {tarea_id} ({tarea.tipo})")
            return tarea_id
        except queue.Full:
            logger.error(f"❌ Cola llena, no se pudo agregar tarea: {tarea_id}")
            return None

    def obtener(self, timeout: float = 1.0):
        """Obtiene la siguiente tarea de la cola"""
        try:
            return self.cola.get(timeout=timeout)
        except queue.Empty:
            return None

    def registrar_resultado(self, resultado: ResultadoEmail):
        """Registra el resultado de un envío"""
        with self.lock:
            self.historial.append(resultado)
            # Mantener solo los últimos N resultados
            if len(self.historial) > self.max_historial:
                self.historial.pop(0)
        logger.info(f"📊 Resultado registrado: {resultado.tipo} - {resultado.estado.value}")

    def obtener_historial(self, tipo: str = None, limite: int = 50) -> List[ResultadoEmail]:
        """Obtiene el historial de envíos"""
        with self.lock:
            historial = list(self.historial)

        if tipo:
            historial = [r for r in historial if r.tipo == tipo]

        return historial[-limite:]

    def obtener_estadisticas(self) -> Dict[str, Any]:
        """Obtiene estadísticas de la cola"""
        with self.lock:
            historial = list(self.historial)

        total = len(historial)
        enviados = sum(1 for r in historial if r.estado == EstadoTarea.ENVIADO)
        fallidos = sum(1 for r in historial if r.estado == EstadoTarea.FALLIDO)

        return {
            'total_tareas': total,
            'enviados': enviados,
            'fallidos': fallidos,
            'tasa_exito': f"{(enviados/total*100):.1f}%" if total > 0 else "N/A",
            'tamaño_cola': self.cola.qsize(),
            'tamaño_maximo': self.cola.maxsize,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# TRABAJADOR DE EMAIL
# ═══════════════════════════════════════════════════════════════════════════════

class TrabajadorEmail:
    """Worker que procesa tareas de email en background"""

    def __init__(
        self,
        cola: ColaEmails,
        email_sender: Callable = None,
        intervalo_check: float = 5.0
    ):
        self.cola = cola
        self.email_sender = email_sender
        self.intervalo_check = intervalo_check
        self.activo = False
        self.thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()
        logger.info("✅ TrabajadorEmail inicializado")

    def iniciar(self):
        """Inicia el worker en un thread independiente"""
        with self.lock:
            if self.activo:
                logger.warning("⚠️  TrabajadorEmail ya está activo")
                return

            self.activo = True
            self.thread = threading.Thread(target=self._loop_procesamiento, daemon=True)
            self.thread.start()
            logger.info("✅ TrabajadorEmail iniciado en background")

    def detener(self):
        """Detiene el worker"""
        with self.lock:
            self.activo = False

        if self.thread:
            self.thread.join(timeout=5)
        logger.info("✅ TrabajadorEmail detenido")

    def _loop_procesamiento(self):
        """Loop principal de procesamiento"""
        logger.info("🔄 Loop de procesamiento iniciado")

        while self.activo:
            try:
                # Obtener siguiente tarea
                resultado = self.cola.obtener(timeout=self.intervalo_check)

                if resultado is None:
                    continue

                tarea_id, tarea = resultado
                self._procesar_tarea(tarea_id, tarea)

            except Exception as e:
                logger.error(f"❌ Error en loop de procesamiento: {e}\n{traceback.format_exc()}")
                time.sleep(1)

    def _procesar_tarea(self, tarea_id: str, tarea: TareaEmail):
        """Procesa una tarea de email individual"""
        logger.info(f"📧 Procesando tarea: {tarea_id} ({tarea.tipo})")

        resultado = ResultadoEmail(
            tarea_id=tarea_id,
            tipo=tarea.tipo,
            estado=EstadoTarea.ENVIANDO,
            timestamp=datetime.now(),
            destinatarios=tarea.destinatarios,
        )

        try:
            # Enviar email
            if self.email_sender:
                exito = self.email_sender(tarea)
            else:
                # Modo simulado si no hay sender
                exito = self._enviar_simulado(tarea)

            if exito:
                resultado.estado = EstadoTarea.ENVIADO
                logger.info(f"✅ Email enviado: {tarea_id} a {len(tarea.destinatarios)} destinatarios")
            else:
                raise Exception("El sender retornó False")

        except Exception as e:
            logger.error(f"❌ Error al procesar tarea {tarea_id}: {e}")
            tarea.reintentos += 1
            resultado.intentos = tarea.reintentos
            resultado.mensaje_error = str(e)

            # Reintentar si no ha excedido el máximo
            if tarea.reintentos < tarea.max_reintentos:
                resultado.estado = EstadoTarea.REINTENTANDO
                # Re-agregar a la cola con delay
                delay = 2 ** tarea.reintentos  # Backoff exponencial
                logger.warning(f"⏳ Reintentando en {delay}s ({tarea.reintentos}/{tarea.max_reintentos})")
                time.sleep(delay)
                self.cola.agregar(tarea)
            else:
                resultado.estado = EstadoTarea.FALLIDO
                logger.error(f"❌ Tarea fallida permanentemente: {tarea_id}")

        finally:
            self.cola.registrar_resultado(resultado)

    def _enviar_simulado(self, tarea: TareaEmail) -> bool:
        """Simula el envío si no hay sender real"""
        logger.info(f"📧 [SIMULADO] Email: {tarea.asunto}")
        logger.info(f"   A: {', '.join(tarea.destinatarios)}")
        logger.info(f"   Tipo: {tarea.tipo}")
        time.sleep(0.5)  # Simular envío
        return True


# ═══════════════════════════════════════════════════════════════════════════════
# GESTOR PRINCIPAL DE EMAILS AUTOMÁTICOS
# ═══════════════════════════════════════════════════════════════════════════════

class GestorEmailAutomatico:
    """Gestor principal del sistema automático de emails"""

    _instancia = None
    _lock = threading.Lock()

    def __new__(cls):
        """Singleton thread-safe"""
        if cls._instancia is None:
            with cls._lock:
                if cls._instancia is None:
                    cls._instancia = super().__new__(cls)
        return cls._instancia

    def __init__(self):
        if hasattr(self, '_inicializado'):
            return

        self.cola = ColaEmails(max_size=100)
        self.trabajador = TrabajadorEmail(self.cola)
        self.email_sender = None
        self._inicializado = True
        logger.info("✅ GestorEmailAutomatico inicializado (Singleton)")

    def establecer_sender(self, sender: Callable):
        """Establece la función de envío de email"""
        self.email_sender = sender
        self.trabajador.email_sender = sender
        logger.info("✅ Email sender establecido")

    def iniciar(self):
        """Inicia el sistema automático de emails"""
        self.trabajador.iniciar()
        logger.info("✅ Sistema automático de emails iniciado")

    def detener(self):
        """Detiene el sistema automático"""
        self.trabajador.detener()
        logger.info("✅ Sistema automático de emails detenido")

    def enviar_reporte_diario(
        self,
        destinatarios: List[str],
        contenido: str,
        archivos: List[str] = None,
        datos: Dict = None
    ) -> str:
        """Envía un reporte diario automáticamente"""
        tarea = TareaEmail(
            tipo=TipoEmail.REPORTE_DIARIO.value,
            destinatarios=destinatarios,
            asunto=f"📊 Reporte Planning Diario - {datetime.now().strftime('%d/%m/%Y')}",
            contenido=contenido,
            archivos=archivos,
            datos=datos or {},
            html=True,
        )
        return self.cola.agregar(tarea)

    def enviar_alerta_critica(
        self,
        destinatarios: List[str],
        tipo_error: str,
        descripcion: str,
        oc: str = None,
        datos: Dict = None
    ) -> str:
        """Envía una alerta crítica de forma inmediata"""
        tarea = TareaEmail(
            tipo=TipoEmail.ALERTA_CRITICA.value,
            destinatarios=destinatarios,
            asunto=f"🚨 ALERTA CRÍTICA - {tipo_error}",
            contenido=descripcion,
            datos=datos or {'oc': oc},
            prioritario=True,  # Las alertas críticas tienen prioridad
            html=True,
        )
        tarea_id = self.cola.agregar(tarea)
        # Procesar inmediatamente si es posible
        if self.email_sender:
            try:
                self.email_sender(tarea)
            except Exception as e:
                logger.error(f"❌ Error al enviar alerta crítica: {e}")
        return tarea_id

    def enviar_validacion_oc(
        self,
        destinatarios: List[str],
        oc: str,
        resultado: str,
        detalles: str = None,
        datos: Dict = None
    ) -> str:
        """Envía resultado de validación de OC"""
        tarea = TareaEmail(
            tipo=TipoEmail.VALIDACION_OC.value,
            destinatarios=destinatarios,
            asunto=f"✅ Validación OC - {oc}",
            contenido=resultado,
            datos={'oc': oc, 'detalles': detalles, **( datos or {})},
            html=True,
        )
        return self.cola.agregar(tarea)

    def enviar_confirmacion(
        self,
        destinatarios: List[str],
        proceso: str,
        detalles: str = None,
        datos: Dict = None
    ) -> str:
        """Envía confirmación de proceso"""
        tarea = TareaEmail(
            tipo=TipoEmail.CONFIRMACION.value,
            destinatarios=destinatarios,
            asunto=f"✅ Confirmación: {proceso}",
            contenido=detalles or "Proceso completado exitosamente",
            datos=datos or {},
            html=True,
        )
        return self.cola.agregar(tarea)

    def obtener_estadisticas(self) -> Dict:
        """Obtiene estadísticas del sistema de emails"""
        return self.cola.obtener_estadisticas()

    def obtener_historial(self, tipo: str = None, limite: int = 50) -> List[Dict]:
        """Obtiene el historial de envíos"""
        historial = self.cola.obtener_historial(tipo=tipo, limite=limite)
        return [r.to_dict() for r in historial]


# ═══════════════════════════════════════════════════════════════════════════════
# INSTANCIA GLOBAL (SINGLETON)
# ═══════════════════════════════════════════════════════════════════════════════

# Crear instancia global del gestor
gestor_automatico = GestorEmailAutomatico()


# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIONES DE CONVENIENCIA
# ═══════════════════════════════════════════════════════════════════════════════

def iniciar_emails_automaticos(email_sender: Callable = None):
    """Inicia el sistema automático de emails"""
    if email_sender:
        gestor_automatico.establecer_sender(email_sender)
    gestor_automatico.iniciar()
    logger.info("✅ Sistema automático de emails en ejecución")


def detener_emails_automaticos():
    """Detiene el sistema automático de emails"""
    gestor_automatico.detener()
    logger.info("✅ Sistema automático de emails detenido")


def enviar_alerta_critica_ahora(
    destinatarios: List[str],
    tipo_error: str,
    descripcion: str,
    oc: str = None,
    datos: Dict = None
) -> str:
    """Envía una alerta crítica de forma inmediata"""
    return gestor_automatico.enviar_alerta_critica(
        destinatarios=destinatarios,
        tipo_error=tipo_error,
        descripcion=descripcion,
        oc=oc,
        datos=datos
    )


def obtener_estadisticas_emails() -> Dict:
    """Obtiene estadísticas del sistema"""
    return gestor_automatico.obtener_estadisticas()


if __name__ == '__main__':
    # Test básico
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    print("Iniciando prueba del sistema de emails automáticos...")

    iniciar_emails_automaticos()

    # Enviar algunos emails de prueba
    gestor_automatico.enviar_reporte_diario(
        destinatarios=['test@example.com'],
        contenido='<h1>Reporte de prueba</h1><p>Este es un email de prueba</p>'
    )

    gestor_automatico.enviar_alerta_critica(
        destinatarios=['critical@example.com'],
        tipo_error='TEST_ERROR',
        descripcion='Este es un error de prueba',
        oc='OC123456'
    )

    # Mostrar estadísticas
    time.sleep(3)
    print("Estadísticas:", gestor_automatico.obtener_estadisticas())

    detener_emails_automaticos()
    print("Prueba completada")
