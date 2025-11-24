"""
Consultas Obligatorias - Ejecución Diaria
=========================================

Consultas que se ejecutan automáticamente de forma diaria
para validación y monitoreo del sistema Manhattan WMS.

Queries incluidas:
- oc_diarias: OCs del día actual
- oc_pendientes: OCs sin procesar
- oc_vencidas: OCs expiradas
- distribuciones_dia: Distribuciones del día
- asn_pendientes: ASNs sin recibir
- asn_status: Estado de todos los ASNs
- inventario_resumen: Resumen de inventario
- recibo_programado: Programa de recibo del día
"""

__all__ = [
    'oc_diarias',
    'oc_pendientes',
    'oc_vencidas',
    'distribuciones_dia',
    'asn_pendientes',
    'asn_status',
    'inventario_resumen',
    'recibo_programado',
]
