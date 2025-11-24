"""
Templates SQL - Plantillas parametrizadas con Jinja2
====================================================

Templates SQL reutilizables para generar queries dinámicas.
Utilizan sintaxis Jinja2 para mayor flexibilidad.

Templates incluidos:
- base_oc_query: Template base para consultas de OC
- base_distribution_query: Template base para distribuciones
- base_asn_query: Template base para ASN
- date_range_filter: Filtro de rango de fechas reutilizable
- pagination: Paginación para queries grandes

Uso:
    from queries.query_loader import QueryLoader
    loader = QueryLoader()
    sql = loader.load_template('base_oc_query', {
        'columns': ['ORDERKEY', 'STATUS'],
        'status_filter': ['0', '1'],
        'limit': 100
    })
"""

__all__ = [
    'base_oc_query',
    'base_distribution_query',
    'base_asn_query',
    'date_range_filter',
    'pagination',
]
