"""
═══════════════════════════════════════════════════════════════
PROGRAMADOR DE NOTIFICACIONES
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Sistema de programación de notificaciones con soporte para
tareas diarias, semanales y expresiones cron.

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
═══════════════════════════════════════════════════════════════
"""

import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Callable, Dict, List, Optional, Any
import uuid
import re

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# ENUMERACIONES Y CLASES DE DATOS
# ═══════════════════════════════════════════════════════════════

class ScheduleType(Enum):
    """Tipos de programación"""
    ONCE = "Una vez"
    DAILY = "Diario"
    WEEKLY = "Semanal"
    MONTHLY = "Mensual"
    CRON = "Cron"
    INTERVAL = "Intervalo"


class DayOfWeek(Enum):
    """Días de la semana"""
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6


@dataclass
class ScheduledTask:
    """
    Representa una tarea programada

    Attributes:
        task_id: Identificador único
        name: Nombre descriptivo de la tarea
        task_func: Función a ejecutar
        schedule_type: Tipo de programación
        schedule_time: Hora de ejecución (HH:MM)
        schedule_day: Día de ejecución (para semanal/mensual)
        cron_expr: Expresión cron (si aplica)
        interval_seconds: Segundos entre ejecuciones (para intervalo)
        enabled: Si la tarea está habilitada
        last_run: Última ejecución
        next_run: Próxima ejecución programada
        run_count: Número de ejecuciones
        max_runs: Máximo de ejecuciones (None = sin límite)
        on_error: Función a llamar en caso de error
        metadata: Datos adicionales
    """
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    task_func: Callable = None
    schedule_type: ScheduleType = ScheduleType.DAILY
    schedule_time: str = "09:00"  # HH:MM
    schedule_day: Optional[int] = None  # 0-6 para semana, 1-31 para mes
    cron_expr: Optional[str] = None
    interval_seconds: int = 3600
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    max_runs: Optional[int] = None
    on_error: Optional[Callable] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Calcula la próxima ejecución"""
        if self.next_run is None:
            self.next_run = self._calculate_next_run()

    def _calculate_next_run(self) -> datetime:
        """Calcula la próxima fecha/hora de ejecución"""
        now = datetime.now()
        time_parts = self.schedule_time.split(':')
        target_hour = int(time_parts[0])
        target_minute = int(time_parts[1]) if len(time_parts) > 1 else 0

        if self.schedule_type == ScheduleType.ONCE:
            target = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
            if target <= now:
                target += timedelta(days=1)
            return target

        elif self.schedule_type == ScheduleType.DAILY:
            target = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
            if target <= now:
                target += timedelta(days=1)
            return target

        elif self.schedule_type == ScheduleType.WEEKLY:
            target = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
            days_ahead = (self.schedule_day or 0) - now.weekday()
            if days_ahead < 0 or (days_ahead == 0 and target <= now):
                days_ahead += 7
            return target + timedelta(days=days_ahead)

        elif self.schedule_type == ScheduleType.MONTHLY:
            target_day = self.schedule_day or 1
            target = now.replace(day=target_day, hour=target_hour, minute=target_minute, second=0, microsecond=0)
            if target <= now:
                # Siguiente mes
                if now.month == 12:
                    target = target.replace(year=now.year + 1, month=1)
                else:
                    target = target.replace(month=now.month + 1)
            return target

        elif self.schedule_type == ScheduleType.INTERVAL:
            return now + timedelta(seconds=self.interval_seconds)

        elif self.schedule_type == ScheduleType.CRON:
            return self._parse_cron_next()

        return now + timedelta(hours=1)

    def _parse_cron_next(self) -> datetime:
        """Parsea expresión cron y calcula próxima ejecución"""
        # Implementación simplificada de cron
        # Formato: minuto hora dia_mes mes dia_semana
        if not self.cron_expr:
            return datetime.now() + timedelta(hours=1)

        parts = self.cron_expr.split()
        if len(parts) != 5:
            logger.warning(f"⚠️ Expresión cron inválida: {self.cron_expr}")
            return datetime.now() + timedelta(hours=1)

        # Por simplicidad, solo manejamos el caso básico
        # En producción, usar una librería como croniter
        minute = int(parts[0]) if parts[0] != '*' else datetime.now().minute
        hour = int(parts[1]) if parts[1] != '*' else datetime.now().hour

        now = datetime.now()
        target = now.replace(minute=minute, second=0, microsecond=0)

        if parts[1] != '*':
            target = target.replace(hour=hour)

        if target <= now:
            target += timedelta(days=1)

        return target

    def should_run(self) -> bool:
        """Verifica si la tarea debe ejecutarse ahora"""
        if not self.enabled:
            return False

        if self.max_runs and self.run_count >= self.max_runs:
            return False

        if self.next_run is None:
            return False

        return datetime.now() >= self.next_run

    def mark_executed(self):
        """Marca la tarea como ejecutada y calcula siguiente ejecución"""
        self.last_run = datetime.now()
        self.run_count += 1
        self.next_run = self._calculate_next_run()

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario"""
        return {
            'task_id': self.task_id,
            'name': self.name,
            'schedule_type': self.schedule_type.value,
            'schedule_time': self.schedule_time,
            'schedule_day': self.schedule_day,
            'cron_expr': self.cron_expr,
            'enabled': self.enabled,
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'next_run': self.next_run.isoformat() if self.next_run else None,
            'run_count': self.run_count,
            'max_runs': self.max_runs,
            'metadata': self.metadata
        }


# ═══════════════════════════════════════════════════════════════
# CLASE NOTIFICATION SCHEDULER
# ═══════════════════════════════════════════════════════════════

class NotificationScheduler:
    """
    Programador de notificaciones

    Permite programar tareas para ejecución:
    - Diaria a una hora específica
    - Semanal en un día/hora específicos
    - Mensual en un día/hora específicos
    - Por intervalo de tiempo
    - Con expresiones cron simplificadas

    Ejemplo:
        scheduler = NotificationScheduler()

        # Tarea diaria
        scheduler.schedule_daily("08:00", enviar_reporte_diario)

        # Tarea semanal
        scheduler.schedule_weekly(DayOfWeek.MONDAY, "09:00", enviar_resumen)

        # Iniciar procesamiento
        scheduler.start()
    """

    def __init__(self):
        """Inicializa el programador"""
        self._tasks: Dict[str, ScheduledTask] = {}
        self._lock = threading.RLock()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._check_interval = 60  # Segundos entre verificaciones

        logger.info("📅 NotificationScheduler inicializado")

    # ═══════════════════════════════════════════════════════════════
    # PROGRAMACIÓN DE TAREAS
    # ═══════════════════════════════════════════════════════════════

    def schedule_daily(self, time: str, task: Callable, name: str = None,
                       metadata: Dict = None) -> str:
        """
        Programa una tarea diaria

        Args:
            time: Hora de ejecución (HH:MM)
            task: Función a ejecutar
            name: Nombre descriptivo
            metadata: Datos adicionales

        Returns:
            str: ID de la tarea
        """
        scheduled = ScheduledTask(
            name=name or f"Diario {time}",
            task_func=task,
            schedule_type=ScheduleType.DAILY,
            schedule_time=time,
            metadata=metadata or {}
        )

        with self._lock:
            self._tasks[scheduled.task_id] = scheduled

        logger.info(f"📅 Tarea diaria programada: {scheduled.name} a las {time}")
        return scheduled.task_id

    def schedule_weekly(self, day: DayOfWeek, time: str, task: Callable,
                        name: str = None, metadata: Dict = None) -> str:
        """
        Programa una tarea semanal

        Args:
            day: Día de la semana (DayOfWeek)
            time: Hora de ejecución (HH:MM)
            task: Función a ejecutar
            name: Nombre descriptivo
            metadata: Datos adicionales

        Returns:
            str: ID de la tarea
        """
        scheduled = ScheduledTask(
            name=name or f"Semanal {day.name} {time}",
            task_func=task,
            schedule_type=ScheduleType.WEEKLY,
            schedule_time=time,
            schedule_day=day.value,
            metadata=metadata or {}
        )

        with self._lock:
            self._tasks[scheduled.task_id] = scheduled

        logger.info(f"📅 Tarea semanal programada: {scheduled.name} - {day.name} a las {time}")
        return scheduled.task_id

    def schedule_monthly(self, day: int, time: str, task: Callable,
                         name: str = None, metadata: Dict = None) -> str:
        """
        Programa una tarea mensual

        Args:
            day: Día del mes (1-31)
            time: Hora de ejecución (HH:MM)
            task: Función a ejecutar
            name: Nombre descriptivo
            metadata: Datos adicionales

        Returns:
            str: ID de la tarea
        """
        scheduled = ScheduledTask(
            name=name or f"Mensual día {day} {time}",
            task_func=task,
            schedule_type=ScheduleType.MONTHLY,
            schedule_time=time,
            schedule_day=min(max(day, 1), 31),
            metadata=metadata or {}
        )

        with self._lock:
            self._tasks[scheduled.task_id] = scheduled

        logger.info(f"📅 Tarea mensual programada: {scheduled.name} - día {day} a las {time}")
        return scheduled.task_id

    def schedule_interval(self, seconds: int, task: Callable,
                          name: str = None, metadata: Dict = None) -> str:
        """
        Programa una tarea por intervalo

        Args:
            seconds: Segundos entre ejecuciones
            task: Función a ejecutar
            name: Nombre descriptivo
            metadata: Datos adicionales

        Returns:
            str: ID de la tarea
        """
        scheduled = ScheduledTask(
            name=name or f"Intervalo cada {seconds}s",
            task_func=task,
            schedule_type=ScheduleType.INTERVAL,
            interval_seconds=seconds,
            metadata=metadata or {}
        )

        with self._lock:
            self._tasks[scheduled.task_id] = scheduled

        logger.info(f"📅 Tarea de intervalo programada: {scheduled.name}")
        return scheduled.task_id

    def schedule_cron(self, cron_expr: str, task: Callable,
                      name: str = None, metadata: Dict = None) -> str:
        """
        Programa una tarea con expresión cron

        Args:
            cron_expr: Expresión cron (min hora dia_mes mes dia_semana)
            task: Función a ejecutar
            name: Nombre descriptivo
            metadata: Datos adicionales

        Returns:
            str: ID de la tarea
        """
        scheduled = ScheduledTask(
            name=name or f"Cron {cron_expr}",
            task_func=task,
            schedule_type=ScheduleType.CRON,
            cron_expr=cron_expr,
            metadata=metadata or {}
        )

        with self._lock:
            self._tasks[scheduled.task_id] = scheduled

        logger.info(f"📅 Tarea cron programada: {scheduled.name}")
        return scheduled.task_id

    def schedule_once(self, at_time: datetime, task: Callable,
                      name: str = None, metadata: Dict = None) -> str:
        """
        Programa una tarea para ejecutarse una sola vez

        Args:
            at_time: Fecha y hora de ejecución
            task: Función a ejecutar
            name: Nombre descriptivo
            metadata: Datos adicionales

        Returns:
            str: ID de la tarea
        """
        scheduled = ScheduledTask(
            name=name or f"Una vez {at_time}",
            task_func=task,
            schedule_type=ScheduleType.ONCE,
            schedule_time=at_time.strftime('%H:%M'),
            max_runs=1,
            next_run=at_time,
            metadata=metadata or {}
        )

        with self._lock:
            self._tasks[scheduled.task_id] = scheduled

        logger.info(f"📅 Tarea única programada: {scheduled.name} para {at_time}")
        return scheduled.task_id

    # ═══════════════════════════════════════════════════════════════
    # GESTIÓN DE TAREAS
    # ═══════════════════════════════════════════════════════════════

    def cancel_scheduled(self, job_id: str) -> bool:
        """
        Cancela una tarea programada

        Args:
            job_id: ID de la tarea

        Returns:
            bool: True si se canceló
        """
        with self._lock:
            if job_id in self._tasks:
                del self._tasks[job_id]
                logger.info(f"🚫 Tarea cancelada: {job_id[:8]}...")
                return True
            return False

    def enable_task(self, job_id: str) -> bool:
        """Habilita una tarea"""
        with self._lock:
            if job_id in self._tasks:
                self._tasks[job_id].enabled = True
                logger.info(f"✅ Tarea habilitada: {job_id[:8]}...")
                return True
            return False

    def disable_task(self, job_id: str) -> bool:
        """Deshabilita una tarea"""
        with self._lock:
            if job_id in self._tasks:
                self._tasks[job_id].enabled = False
                logger.info(f"⏸️ Tarea deshabilitada: {job_id[:8]}...")
                return True
            return False

    def get_scheduled_jobs(self) -> List[Dict[str, Any]]:
        """
        Obtiene todas las tareas programadas

        Returns:
            List[Dict]: Lista de tareas con sus datos
        """
        with self._lock:
            return [task.to_dict() for task in self._tasks.values()]

    def get_task(self, job_id: str) -> Optional[ScheduledTask]:
        """Obtiene una tarea por ID"""
        with self._lock:
            return self._tasks.get(job_id)

    # ═══════════════════════════════════════════════════════════════
    # EJECUCIÓN
    # ═══════════════════════════════════════════════════════════════

    def run_pending(self) -> int:
        """
        Ejecuta todas las tareas pendientes

        Returns:
            int: Número de tareas ejecutadas
        """
        executed = 0

        with self._lock:
            tasks_to_run = [t for t in self._tasks.values() if t.should_run()]

        for task in tasks_to_run:
            try:
                logger.info(f"▶️ Ejecutando tarea: {task.name}")
                if task.task_func:
                    task.task_func()
                task.mark_executed()
                executed += 1
                logger.info(f"✅ Tarea completada: {task.name}")

            except Exception as e:
                logger.error(f"❌ Error en tarea {task.name}: {e}")
                if task.on_error:
                    try:
                        task.on_error(e)
                    except Exception:
                        pass

        return executed

    def start(self, blocking: bool = False):
        """
        Inicia el procesamiento de tareas

        Args:
            blocking: Si True, bloquea el hilo actual
        """
        if self._running:
            logger.warning("⚠️ El scheduler ya está ejecutándose")
            return

        self._running = True
        logger.info("▶️ Scheduler iniciado")

        if blocking:
            self._run_loop()
        else:
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()

    def stop(self):
        """Detiene el procesamiento de tareas"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("⏹️ Scheduler detenido")

    def _run_loop(self):
        """Loop principal de ejecución"""
        while self._running:
            try:
                self.run_pending()
            except Exception as e:
                logger.error(f"❌ Error en loop del scheduler: {e}")

            time.sleep(self._check_interval)

    def is_running(self) -> bool:
        """Verifica si el scheduler está ejecutándose"""
        return self._running


# ═══════════════════════════════════════════════════════════════
# EJEMPLO DE USO
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("""
    ═══════════════════════════════════════════════════════════════
    PROGRAMADOR DE NOTIFICACIONES - CHEDRAUI CEDIS
    ═══════════════════════════════════════════════════════════════
    """)

    scheduler = NotificationScheduler()

    # Función de ejemplo
    def tarea_ejemplo():
        print(f"✅ Tarea ejecutada a las {datetime.now().strftime('%H:%M:%S')}")

    # Programar tareas
    id1 = scheduler.schedule_daily("09:00", tarea_ejemplo, "Reporte matutino")
    id2 = scheduler.schedule_weekly(DayOfWeek.MONDAY, "08:00", tarea_ejemplo, "Resumen semanal")

    # Mostrar tareas
    print("\n📋 Tareas programadas:")
    for task in scheduler.get_scheduled_jobs():
        print(f"   - {task['name']}: próxima ejecución {task['next_run']}")
