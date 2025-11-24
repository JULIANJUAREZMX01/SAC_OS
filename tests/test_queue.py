"""
═══════════════════════════════════════════════════════════════
TESTS PARA EMAIL QUEUE
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Tests unitarios para la cola de emails y scheduler.

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
═══════════════════════════════════════════════════════════════
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import sys
import os

# Agregar path del proyecto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.email.email_message import EmailMessage, EmailPriority
from modules.email.queue import EmailQueue, QueuedEmail, QueueStatus, QueueFullError
from modules.email.scheduler import NotificationScheduler, ScheduledTask, ScheduleType, DayOfWeek
from modules.email.recipients import RecipientsManager, RecipientCategory


# ═══════════════════════════════════════════════════════════════
# TESTS PARA EMAIL QUEUE
# ═══════════════════════════════════════════════════════════════

class TestEmailQueue:
    """Tests para EmailQueue"""

    @pytest.fixture
    def queue(self):
        """Cola de emails para testing"""
        return EmailQueue(max_queue_size=100)

    @pytest.fixture
    def mensaje(self):
        """Mensaje de prueba"""
        return EmailMessage(
            to=["usuario@chedraui.com.mx"],
            subject="Prueba",
            body_html="<h1>Hola</h1>"
        )

    def test_agregar_mensaje(self, queue, mensaje):
        """Test de agregar mensaje a la cola"""
        queue_id = queue.add(mensaje)

        assert queue_id is not None
        assert len(queue.get_pending()) == 1

    def test_agregar_con_prioridad(self, queue, mensaje):
        """Test de agregar con prioridad"""
        queue.add(mensaje, priority=1)
        queue.add(mensaje, priority=10)

        pending = queue.get_pending()
        assert pending[0].priority <= pending[-1].priority

    def test_agregar_programado(self, queue, mensaje):
        """Test de agregar mensaje programado"""
        future = datetime.now() + timedelta(hours=1)
        queue_id = queue.add(mensaje, scheduled_at=future)

        queued = queue.get_by_id(queue_id)
        assert queued.scheduled_at == future

    def test_eliminar_mensaje(self, queue, mensaje):
        """Test de eliminar mensaje"""
        queue_id = queue.add(mensaje)
        result = queue.remove(queue_id)

        assert result
        assert len(queue.get_pending()) == 0

    def test_eliminar_mensaje_inexistente(self, queue):
        """Test de eliminar mensaje inexistente"""
        result = queue.remove("id_inexistente")
        assert not result

    def test_limpiar_cola(self, queue, mensaje):
        """Test de limpiar cola"""
        queue.add(mensaje)
        queue.add(mensaje)
        queue.add(mensaje)

        count = queue.clear_queue()

        assert count == 3
        assert len(queue.get_pending()) == 0

    def test_cola_llena(self):
        """Test de cola llena"""
        queue = EmailQueue(max_queue_size=2)
        mensaje = EmailMessage(
            to=["usuario@test.com"],
            subject="Test",
            body_html="<p>Test</p>"
        )

        queue.add(mensaje)
        queue.add(mensaje)

        with pytest.raises(QueueFullError):
            queue.add(mensaje)

    def test_procesar_cola(self, queue, mensaje):
        """Test de procesamiento de cola"""
        queue.add(mensaje)

        # Mock de función de envío
        send_func = Mock(return_value=True)
        results = queue.process_queue(send_func)

        assert len(results) == 1
        assert all(results.values())
        send_func.assert_called_once()

    def test_procesar_cola_con_fallo(self, queue, mensaje):
        """Test de procesamiento con fallo"""
        queue.add(mensaje, max_retries=1)

        send_func = Mock(return_value=False)
        results = queue.process_queue(send_func)

        assert not all(results.values())

    def test_estadisticas_cola(self, queue, mensaje):
        """Test de estadísticas de cola"""
        queue.add(mensaje)
        queue.add(mensaje, scheduled_at=datetime.now() + timedelta(hours=1))

        stats = queue.get_queue_stats()

        assert stats['total_in_queue'] == 2
        assert stats['scheduled'] == 1
        assert stats['ready_to_send'] == 1


# ═══════════════════════════════════════════════════════════════
# TESTS PARA QUEUED EMAIL
# ═══════════════════════════════════════════════════════════════

class TestQueuedEmail:
    """Tests para QueuedEmail"""

    @pytest.fixture
    def mensaje(self):
        return EmailMessage(
            to=["usuario@test.com"],
            subject="Test",
            body_html="<p>Test</p>"
        )

    def test_crear_queued_email(self, mensaje):
        """Test de creación de QueuedEmail"""
        queued = QueuedEmail(email=mensaje)

        assert queued.email == mensaje
        assert queued.status == QueueStatus.PENDING
        assert queued.retry_count == 0

    def test_puede_reintentar(self, mensaje):
        """Test de verificación de reintento"""
        queued = QueuedEmail(email=mensaje, max_retries=3)

        assert queued.can_retry()

        queued.retry_count = 3
        assert not queued.can_retry()

    def test_incrementar_reintento(self, mensaje):
        """Test de incremento de reintento"""
        queued = QueuedEmail(email=mensaje)
        queued.increment_retry()

        assert queued.retry_count == 1
        assert queued.last_attempt is not None

    def test_comparacion_prioridad(self, mensaje):
        """Test de comparación por prioridad"""
        queued1 = QueuedEmail(email=mensaje, priority=1)
        queued2 = QueuedEmail(email=mensaje, priority=5)

        assert queued1 < queued2

    def test_to_dict(self, mensaje):
        """Test de conversión a diccionario"""
        queued = QueuedEmail(email=mensaje, priority=3)
        data = queued.to_dict()

        assert data['priority'] == 3
        assert data['status'] == QueueStatus.PENDING.value


# ═══════════════════════════════════════════════════════════════
# TESTS PARA NOTIFICATION SCHEDULER
# ═══════════════════════════════════════════════════════════════

class TestNotificationScheduler:
    """Tests para NotificationScheduler"""

    @pytest.fixture
    def scheduler(self):
        return NotificationScheduler()

    def test_programar_tarea_diaria(self, scheduler):
        """Test de programación diaria"""
        task_func = Mock()
        task_id = scheduler.schedule_daily("09:00", task_func, "Tarea diaria")

        assert task_id is not None
        jobs = scheduler.get_scheduled_jobs()
        assert len(jobs) == 1
        assert jobs[0]['schedule_type'] == ScheduleType.DAILY.value

    def test_programar_tarea_semanal(self, scheduler):
        """Test de programación semanal"""
        task_func = Mock()
        task_id = scheduler.schedule_weekly(
            DayOfWeek.MONDAY, "10:00", task_func, "Tarea semanal"
        )

        assert task_id is not None
        jobs = scheduler.get_scheduled_jobs()
        assert jobs[0]['schedule_type'] == ScheduleType.WEEKLY.value

    def test_programar_tarea_mensual(self, scheduler):
        """Test de programación mensual"""
        task_func = Mock()
        task_id = scheduler.schedule_monthly(1, "08:00", task_func, "Tarea mensual")

        assert task_id is not None

    def test_programar_tarea_intervalo(self, scheduler):
        """Test de programación por intervalo"""
        task_func = Mock()
        task_id = scheduler.schedule_interval(3600, task_func, "Cada hora")

        jobs = scheduler.get_scheduled_jobs()
        assert jobs[0]['schedule_type'] == ScheduleType.INTERVAL.value

    def test_cancelar_tarea(self, scheduler):
        """Test de cancelación de tarea"""
        task_func = Mock()
        task_id = scheduler.schedule_daily("09:00", task_func)

        result = scheduler.cancel_scheduled(task_id)

        assert result
        assert len(scheduler.get_scheduled_jobs()) == 0

    def test_habilitar_deshabilitar_tarea(self, scheduler):
        """Test de habilitar/deshabilitar tarea"""
        task_func = Mock()
        task_id = scheduler.schedule_daily("09:00", task_func)

        scheduler.disable_task(task_id)
        task = scheduler.get_task(task_id)
        assert not task.enabled

        scheduler.enable_task(task_id)
        task = scheduler.get_task(task_id)
        assert task.enabled

    def test_ejecutar_pendientes(self, scheduler):
        """Test de ejecución de tareas pendientes"""
        task_func = Mock()

        # Programar tarea para ahora
        scheduler.schedule_once(
            datetime.now() - timedelta(seconds=1),
            task_func,
            "Tarea inmediata"
        )

        executed = scheduler.run_pending()

        assert executed == 1
        task_func.assert_called_once()


# ═══════════════════════════════════════════════════════════════
# TESTS PARA SCHEDULED TASK
# ═══════════════════════════════════════════════════════════════

class TestScheduledTask:
    """Tests para ScheduledTask"""

    def test_crear_tarea_diaria(self):
        """Test de creación de tarea diaria"""
        task = ScheduledTask(
            name="Test diario",
            task_func=lambda: None,
            schedule_type=ScheduleType.DAILY,
            schedule_time="08:00"
        )

        assert task.name == "Test diario"
        assert task.schedule_type == ScheduleType.DAILY
        assert task.next_run is not None

    def test_should_run(self):
        """Test de verificación si debe ejecutarse"""
        task = ScheduledTask(
            name="Test",
            task_func=lambda: None,
            schedule_type=ScheduleType.ONCE,
            next_run=datetime.now() - timedelta(minutes=1)
        )

        assert task.should_run()

    def test_should_not_run_disabled(self):
        """Test de tarea deshabilitada"""
        task = ScheduledTask(
            name="Test",
            task_func=lambda: None,
            enabled=False,
            next_run=datetime.now() - timedelta(minutes=1)
        )

        assert not task.should_run()

    def test_mark_executed(self):
        """Test de marcar como ejecutada"""
        task = ScheduledTask(
            name="Test",
            task_func=lambda: None,
            schedule_type=ScheduleType.DAILY,
            schedule_time="08:00"
        )

        task.mark_executed()

        assert task.run_count == 1
        assert task.last_run is not None
        # Verificamos que next_run esté calculado (puede ser el mismo día u otro)
        assert task.next_run is not None


# ═══════════════════════════════════════════════════════════════
# TESTS PARA RECIPIENTS MANAGER
# ═══════════════════════════════════════════════════════════════

class TestRecipientsManager:
    """Tests para RecipientsManager"""

    @pytest.fixture
    def manager(self):
        return RecipientsManager()

    def test_agregar_destinatario(self, manager):
        """Test de agregar destinatario"""
        result = manager.add_recipient(
            "usuario@chedraui.com.mx",
            name="Usuario Test",
            categories=[RecipientCategory.PLANNING]
        )

        assert result
        recipients = manager.get_recipients(RecipientCategory.PLANNING)
        assert "usuario@chedraui.com.mx" in recipients

    def test_agregar_email_invalido(self, manager):
        """Test de agregar email inválido"""
        result = manager.add_recipient("email_invalido")
        assert not result

    def test_eliminar_destinatario(self, manager):
        """Test de eliminar destinatario"""
        manager.add_recipient("usuario@test.com")
        result = manager.remove_recipient("usuario@test.com")

        assert result
        assert "usuario@test.com" not in manager.get_all_emails()

    def test_obtener_por_categoria(self, manager):
        """Test de obtener destinatarios por categoría"""
        manager.add_recipient(
            "planning@test.com",
            categories=[RecipientCategory.PLANNING]
        )
        manager.add_recipient(
            "sistemas@test.com",
            categories=[RecipientCategory.SYSTEMS]
        )

        planning = manager.get_recipients(RecipientCategory.PLANNING)
        sistemas = manager.get_recipients(RecipientCategory.SYSTEMS)

        assert "planning@test.com" in planning
        assert "sistemas@test.com" in sistemas
        assert "sistemas@test.com" not in planning

    def test_validar_email(self):
        """Test de validación de email"""
        assert RecipientsManager.validate_email("usuario@chedraui.com.mx")
        assert RecipientsManager.validate_email("user.name@domain.co")
        assert not RecipientsManager.validate_email("invalido")
        assert not RecipientsManager.validate_email("@domain.com")
        assert not RecipientsManager.validate_email("user@")

    def test_crear_lista_distribucion(self, manager):
        """Test de crear lista de distribución"""
        result = manager.create_distribution_list(
            "test_list",
            description="Lista de prueba",
            emails=["user1@test.com", "user2@test.com"]
        )

        assert result
        assert "test_list" in manager.list_distribution_lists()

    def test_obtener_lista_distribucion(self, manager):
        """Test de obtener lista de distribución"""
        manager.create_distribution_list(
            "mi_lista",
            emails=["a@test.com", "b@test.com"]
        )

        emails = manager.get_distribution_list("mi_lista")
        assert len(emails) == 2

    def test_estadisticas(self, manager):
        """Test de estadísticas"""
        manager.add_recipient(
            "user1@test.com",
            categories=[RecipientCategory.PLANNING]
        )
        manager.add_recipient(
            "user2@test.com",
            categories=[RecipientCategory.SYSTEMS]
        )

        stats = manager.get_stats()

        assert stats['total_recipients'] == 2
        assert stats['enabled'] == 2


# ═══════════════════════════════════════════════════════════════
# EJECUCIÓN DE TESTS
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
