"""
═══════════════════════════════════════════════════════════════
COLA DE EMAILS CON REINTENTOS
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Sistema de cola para gestión de envío de correos con reintentos
automáticos, priorización y persistencia.

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
═══════════════════════════════════════════════════════════════
"""

import json
import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from queue import PriorityQueue
import uuid

from .email_message import EmailMessage, EmailPriority

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# ENUMERACIONES Y CLASES DE DATOS
# ═══════════════════════════════════════════════════════════════

class QueueStatus(Enum):
    """Estados de un email en la cola"""
    PENDING = "PENDIENTE"
    PROCESSING = "PROCESANDO"
    SENT = "ENVIADO"
    FAILED = "FALLIDO"
    RETRY = "REINTENTANDO"


@dataclass
class QueuedEmail:
    """
    Representa un email en la cola de envío

    Attributes:
        email: Mensaje de email
        priority: Prioridad en la cola (menor = más prioritario)
        queue_id: Identificador único en la cola
        status: Estado actual del email
        retry_count: Número de reintentos realizados
        max_retries: Número máximo de reintentos
        created_at: Fecha de creación
        scheduled_at: Fecha programada de envío
        last_attempt: Fecha del último intento
        last_error: Último error registrado
        metadata: Datos adicionales
    """
    email: EmailMessage
    priority: int = 5
    queue_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: QueueStatus = QueueStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = field(default_factory=datetime.now)
    scheduled_at: Optional[datetime] = None
    last_attempt: Optional[datetime] = None
    last_error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __lt__(self, other):
        """Comparación para PriorityQueue (menor prioridad = más prioritario)"""
        if self.priority != other.priority:
            return self.priority < other.priority
        return self.created_at < other.created_at

    def can_retry(self) -> bool:
        """Verifica si se puede reintentar el envío"""
        return self.retry_count < self.max_retries

    def increment_retry(self):
        """Incrementa el contador de reintentos"""
        self.retry_count += 1
        self.last_attempt = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para serialización"""
        return {
            'queue_id': self.queue_id,
            'message_id': self.email.message_id,
            'subject': self.email.subject,
            'to': self.email.to,
            'priority': self.priority,
            'status': self.status.value,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'created_at': self.created_at.isoformat(),
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'last_attempt': self.last_attempt.isoformat() if self.last_attempt else None,
            'last_error': self.last_error,
            'metadata': self.metadata
        }


# ═══════════════════════════════════════════════════════════════
# CLASE EMAIL QUEUE
# ═══════════════════════════════════════════════════════════════

class EmailQueue:
    """
    Cola de emails con gestión de reintentos y priorización

    Características:
    - Priorización de envíos
    - Reintentos automáticos con backoff exponencial
    - Persistencia opcional en archivo
    - Estadísticas de la cola
    - Procesamiento en segundo plano

    Ejemplo:
        queue = EmailQueue()
        queue.add(email_message, priority=1)
        results = queue.process_queue(send_function)
    """

    def __init__(self, persistence_file: str = None, max_queue_size: int = 1000):
        """
        Inicializa la cola de emails

        Args:
            persistence_file: Archivo para persistir la cola (opcional)
            max_queue_size: Tamaño máximo de la cola
        """
        self._queue: List[QueuedEmail] = []
        self._processing: Dict[str, QueuedEmail] = {}
        self._completed: List[QueuedEmail] = []
        self._failed: List[QueuedEmail] = []
        self._lock = threading.RLock()
        self._max_size = max_queue_size
        self._persistence_file = Path(persistence_file) if persistence_file else None
        self._is_processing = False

        # Cargar cola persistida si existe
        if self._persistence_file and self._persistence_file.exists():
            self._load_from_file()

        logger.info(f"📧 EmailQueue inicializada (max_size={max_queue_size})")

    # ═══════════════════════════════════════════════════════════════
    # GESTIÓN DE COLA
    # ═══════════════════════════════════════════════════════════════

    def add(self, message: EmailMessage, priority: int = 5,
            scheduled_at: datetime = None, max_retries: int = 3,
            metadata: Dict = None) -> str:
        """
        Agrega un email a la cola

        Args:
            message: Mensaje de email
            priority: Prioridad (1-10, menor = más prioritario)
            scheduled_at: Fecha programada de envío
            max_retries: Número máximo de reintentos
            metadata: Datos adicionales

        Returns:
            str: ID del email en la cola
        """
        with self._lock:
            if len(self._queue) >= self._max_size:
                logger.warning(f"⚠️ Cola llena ({self._max_size}), no se puede agregar email")
                raise QueueFullError(f"Cola llena (max={self._max_size})")

            queued = QueuedEmail(
                email=message,
                priority=min(max(priority, 1), 10),  # Limitar 1-10
                scheduled_at=scheduled_at,
                max_retries=max_retries,
                metadata=metadata or {}
            )

            self._queue.append(queued)
            self._queue.sort()  # Ordenar por prioridad

            if self._persistence_file:
                self._save_to_file()

            logger.info(
                f"📥 Email agregado a cola: {queued.queue_id[:8]}... "
                f"(priority={priority}, scheduled={scheduled_at})"
            )
            return queued.queue_id

    def get_pending(self) -> List[QueuedEmail]:
        """
        Obtiene todos los emails pendientes

        Returns:
            List[QueuedEmail]: Emails pendientes ordenados por prioridad
        """
        with self._lock:
            return [q for q in self._queue if q.status == QueueStatus.PENDING]

    def get_by_id(self, queue_id: str) -> Optional[QueuedEmail]:
        """
        Obtiene un email por su ID de cola

        Args:
            queue_id: ID del email en la cola

        Returns:
            QueuedEmail o None si no se encuentra
        """
        with self._lock:
            for q in self._queue + self._completed + self._failed:
                if q.queue_id == queue_id:
                    return q
            return self._processing.get(queue_id)

    def remove(self, queue_id: str) -> bool:
        """
        Elimina un email de la cola

        Args:
            queue_id: ID del email

        Returns:
            bool: True si se eliminó
        """
        with self._lock:
            for i, q in enumerate(self._queue):
                if q.queue_id == queue_id:
                    del self._queue[i]
                    if self._persistence_file:
                        self._save_to_file()
                    logger.info(f"🗑️ Email eliminado de cola: {queue_id[:8]}...")
                    return True
            return False

    def clear_queue(self) -> int:
        """
        Limpia la cola de emails pendientes

        Returns:
            int: Número de emails eliminados
        """
        with self._lock:
            count = len(self._queue)
            self._queue.clear()
            if self._persistence_file:
                self._save_to_file()
            logger.info(f"🗑️ Cola limpiada: {count} emails eliminados")
            return count

    # ═══════════════════════════════════════════════════════════════
    # PROCESAMIENTO DE COLA
    # ═══════════════════════════════════════════════════════════════

    def process_queue(self, send_function: Callable[[EmailMessage], bool],
                      batch_size: int = 10, delay_between: float = 0.5) -> Dict[str, bool]:
        """
        Procesa la cola de emails

        Args:
            send_function: Función para enviar emails (recibe EmailMessage, retorna bool)
            batch_size: Número máximo de emails a procesar
            delay_between: Segundos de espera entre envíos

        Returns:
            Dict[str, bool]: Resultados {queue_id: éxito}
        """
        results = {}

        with self._lock:
            if self._is_processing:
                logger.warning("⚠️ La cola ya está siendo procesada")
                return results

            self._is_processing = True

        try:
            now = datetime.now()
            to_process = []

            with self._lock:
                for q in self._queue[:]:
                    if q.status != QueueStatus.PENDING:
                        continue

                    # Verificar si está programado
                    if q.scheduled_at and q.scheduled_at > now:
                        continue

                    to_process.append(q)
                    if len(to_process) >= batch_size:
                        break

            logger.info(f"📤 Procesando {len(to_process)} emails...")

            for queued in to_process:
                try:
                    with self._lock:
                        queued.status = QueueStatus.PROCESSING
                        self._processing[queued.queue_id] = queued

                    # Intentar enviar
                    success = send_function(queued.email)

                    with self._lock:
                        if success:
                            queued.status = QueueStatus.SENT
                            self._completed.append(queued)
                            self._queue.remove(queued)
                            logger.info(f"✅ Email enviado: {queued.queue_id[:8]}...")
                        else:
                            self._handle_failed(queued, "Envío fallido")

                        del self._processing[queued.queue_id]
                        results[queued.queue_id] = success

                except Exception as e:
                    logger.error(f"❌ Error procesando {queued.queue_id[:8]}...: {e}")
                    with self._lock:
                        self._handle_failed(queued, str(e))
                        if queued.queue_id in self._processing:
                            del self._processing[queued.queue_id]
                        results[queued.queue_id] = False

                # Pausa entre envíos
                if delay_between > 0:
                    time.sleep(delay_between)

            if self._persistence_file:
                self._save_to_file()

        finally:
            with self._lock:
                self._is_processing = False

        # Resumen
        sent = sum(1 for v in results.values() if v)
        failed = len(results) - sent
        logger.info(f"📊 Procesamiento completado: {sent} enviados, {failed} fallidos")

        return results

    def _handle_failed(self, queued: QueuedEmail, error: str):
        """Maneja un email fallido"""
        queued.last_error = error
        queued.increment_retry()

        if queued.can_retry():
            queued.status = QueueStatus.RETRY
            # Backoff exponencial: 2^retry * 30 segundos
            delay = (2 ** queued.retry_count) * 30
            queued.scheduled_at = datetime.now() + timedelta(seconds=delay)
            queued.status = QueueStatus.PENDING
            logger.warning(
                f"⚠️ Reintento programado para {queued.queue_id[:8]}... "
                f"({queued.retry_count}/{queued.max_retries}) en {delay}s"
            )
        else:
            queued.status = QueueStatus.FAILED
            self._failed.append(queued)
            if queued in self._queue:
                self._queue.remove(queued)
            logger.error(f"❌ Email fallido permanentemente: {queued.queue_id[:8]}...")

    def retry_failed(self, send_function: Callable[[EmailMessage], bool]) -> int:
        """
        Reintenta enviar los emails fallidos

        Args:
            send_function: Función para enviar emails

        Returns:
            int: Número de emails reenviados exitosamente
        """
        with self._lock:
            to_retry = self._failed[:]
            self._failed.clear()

        success_count = 0
        for queued in to_retry:
            queued.status = QueueStatus.PENDING
            queued.retry_count = 0
            queued.scheduled_at = None

            with self._lock:
                self._queue.append(queued)

        if to_retry:
            results = self.process_queue(send_function)
            success_count = sum(1 for v in results.values() if v)

        logger.info(f"🔄 Reintento de fallidos: {success_count}/{len(to_retry)} exitosos")
        return success_count

    # ═══════════════════════════════════════════════════════════════
    # ESTADÍSTICAS
    # ═══════════════════════════════════════════════════════════════

    def get_queue_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de la cola

        Returns:
            Dict: Estadísticas de la cola
        """
        with self._lock:
            pending = [q for q in self._queue if q.status == QueueStatus.PENDING]
            scheduled = [q for q in pending if q.scheduled_at and q.scheduled_at > datetime.now()]
            ready = [q for q in pending if not q.scheduled_at or q.scheduled_at <= datetime.now()]

            return {
                'total_in_queue': len(self._queue),
                'pending': len(pending),
                'scheduled': len(scheduled),
                'ready_to_send': len(ready),
                'processing': len(self._processing),
                'completed': len(self._completed),
                'failed': len(self._failed),
                'max_queue_size': self._max_size,
                'queue_utilization': f"{(len(self._queue) / self._max_size) * 100:.1f}%",
                'is_processing': self._is_processing
            }

    # ═══════════════════════════════════════════════════════════════
    # PERSISTENCIA
    # ═══════════════════════════════════════════════════════════════

    def _save_to_file(self):
        """Guarda la cola en archivo"""
        if not self._persistence_file:
            return

        try:
            data = {
                'queue': [q.to_dict() for q in self._queue],
                'failed': [q.to_dict() for q in self._failed],
                'saved_at': datetime.now().isoformat()
            }
            self._persistence_file.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding='utf-8'
            )
        except Exception as e:
            logger.error(f"❌ Error guardando cola: {e}")

    def _load_from_file(self):
        """Carga la cola desde archivo"""
        if not self._persistence_file or not self._persistence_file.exists():
            return

        try:
            data = json.loads(self._persistence_file.read_text(encoding='utf-8'))
            logger.info(f"📂 Cola cargada desde {self._persistence_file}")
            # Nota: La reconstrucción completa requeriría serialización de EmailMessage
        except Exception as e:
            logger.error(f"❌ Error cargando cola: {e}")


# ═══════════════════════════════════════════════════════════════
# EXCEPCIONES
# ═══════════════════════════════════════════════════════════════

class QueueFullError(Exception):
    """Excepción cuando la cola está llena"""
    pass


# ═══════════════════════════════════════════════════════════════
# EJEMPLO DE USO
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("""
    ═══════════════════════════════════════════════════════════════
    COLA DE EMAILS - CHEDRAUI CEDIS
    ═══════════════════════════════════════════════════════════════
    """)

    queue = EmailQueue()

    # Crear mensaje de prueba
    mensaje = EmailMessage(
        to=["usuario@chedraui.com.mx"],
        subject="Prueba de Cola",
        body_html="<h1>Prueba</h1>"
    )

    # Agregar a la cola
    queue_id = queue.add(mensaje, priority=1)
    print(f"✅ Email agregado con ID: {queue_id}")

    # Mostrar estadísticas
    stats = queue.get_queue_stats()
    print(f"\n📊 Estadísticas de cola:")
    for key, value in stats.items():
        print(f"   {key}: {value}")
