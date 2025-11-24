"""
Consultas Preventivas - Monitoreo Proactivo
============================================

Consultas de monitoreo proactivo para detectar problemas
potenciales antes de que se conviertan en críticos.

Queries incluidas:
- oc_por_vencer: OCs próximas a vencer (3 días)
- distribuciones_excedentes: Distribuciones que exceden OC
- distribuciones_incompletas: Distribuciones menores que OC
- sku_sin_innerpack: SKUs sin Inner Pack configurado
- asn_sin_actualizar: ASNs estancados sin movimiento
- ubicaciones_llenas: Ubicaciones al límite de capacidad
- usuarios_inactivos: Usuarios sin actividad reciente
"""

__all__ = [
    'oc_por_vencer',
    'distribuciones_excedentes',
    'distribuciones_incompletas',
    'sku_sin_innerpack',
    'asn_sin_actualizar',
    'ubicaciones_llenas',
    'usuarios_inactivos',
]
