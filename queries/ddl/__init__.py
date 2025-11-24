"""
DDL - Definiciones de Vistas y Stored Procedures
=================================================

Scripts DDL para crear vistas y stored procedures
en la base de datos Manhattan WMS (DB2).

IMPORTANTE: Estos scripts deben ser ejecutados por un DBA
o administrador de BD con permisos apropiados.

Estructura:
- views/: Definiciones de vistas
- procedures/: Stored procedures

Vistas incluidas:
- v_oc_summary: Resumen de órdenes de compra
- v_distribution_totals: Totales de distribuciones
- v_asn_status: Estado de ASNs

Procedimientos incluidos:
- sp_validate_oc: Validación de OC
- sp_get_daily_report: Reporte diario automatizado
"""

__all__ = [
    'views',
    'procedures',
]
