"""
═══════════════════════════════════════════════════════════════
MÓDULO DE EMAIL - SISTEMA SAC
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Sistema completo de notificaciones por correo electrónico.

Componentes:
- EmailClient: Cliente SMTP con gestión de conexiones
- EmailMessage: Clase para construir mensajes de email
- EmailTemplateEngine: Motor de templates HTML
- EmailQueue: Cola de emails con reintentos
- NotificationScheduler: Programador de notificaciones
- RecipientsManager: Gestión de destinatarios
- EmailReceiver: Receptor de correos IMAP para detección de conflictos

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
═══════════════════════════════════════════════════════════════
"""

from .email_message import EmailMessage, EmailPriority, Attachment
from .email_client import EmailClient
from .template_engine import EmailTemplateEngine
from .queue import EmailQueue, QueuedEmail
from .scheduler import NotificationScheduler, ScheduledTask
from .recipients import RecipientsManager, RecipientCategory
from .email_receiver import (
    EmailReceiver,
    CorreoRecibido,
    AdjuntoCorreo,
    TipoConflictoCorreo,
    SeveridadConflicto
)

__all__ = [
    # Email Message
    'EmailMessage',
    'EmailPriority',
    'Attachment',

    # Email Client
    'EmailClient',

    # Template Engine
    'EmailTemplateEngine',

    # Queue
    'EmailQueue',
    'QueuedEmail',

    # Scheduler
    'NotificationScheduler',
    'ScheduledTask',

    # Recipients
    'RecipientsManager',
    'RecipientCategory',

    # Email Receiver (IMAP)
    'EmailReceiver',
    'CorreoRecibido',
    'AdjuntoCorreo',
    'TipoConflictoCorreo',
    'SeveridadConflicto',
]
