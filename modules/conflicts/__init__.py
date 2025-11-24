"""
===============================================================================
MÓDULO DE GESTIÓN DE CONFLICTOS EXTERNOS - SISTEMA SAC
Sistema de Automatización de Consultas - CEDIS Cancún 427
===============================================================================

Sistema completo para la detección, análisis, almacenamiento y resolución
de conflictos reportados externamente por correo electrónico.

Componentes:
- ConflictStorage: Almacenamiento persistente de conflictos
- ConflictAnalyzer: Análisis y clasificación de conflictos
- ConflictResolver: Flujo de resolución con confirmación manual
- ConflictNotifier: Alertas y notificaciones al analista en turno

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
===============================================================================
"""

from .conflict_storage import (
    ConflictStorage,
    ConflictoExterno,
    EstadoConflicto,
    EventoConflicto,
)
from .conflict_analyzer import (
    ConflictAnalyzer,
    ResultadoAnalisis,
)
from .conflict_resolver import (
    ConflictResolver,
    AccionResolucion,
    ResultadoResolucion,
)
from .conflict_notifier import (
    ConflictNotifier,
    TipoNotificacion,
)

__all__ = [
    # Storage
    'ConflictStorage',
    'ConflictoExterno',
    'EstadoConflicto',
    'EventoConflicto',

    # Analyzer
    'ConflictAnalyzer',
    'ResultadoAnalisis',

    # Resolver
    'ConflictResolver',
    'AccionResolucion',
    'ResultadoResolucion',

    # Notifier
    'ConflictNotifier',
    'TipoNotificacion',
]
