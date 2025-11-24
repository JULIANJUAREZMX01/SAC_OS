"""
═══════════════════════════════════════════════════════════════
MÓDULO DE CONSULTAS SQL - Sistema SAC
CEDIS Chedraui Cancún 427
═══════════════════════════════════════════════════════════════

Contiene todas las consultas SQL optimizadas para validación
y monitoreo del sistema Manhattan WMS (DB2).

Estructura del módulo:
---------------------
queries/
├── __init__.py              # Este archivo
├── query_loader.py          # Cargador principal de queries
├── obligatorias/            # Queries de ejecución diaria
│   ├── oc_diarias.sql
│   ├── oc_pendientes.sql
│   ├── oc_vencidas.sql
│   ├── distribuciones_dia.sql
│   ├── asn_pendientes.sql
│   ├── asn_status.sql
│   ├── inventario_resumen.sql
│   └── recibo_programado.sql
├── preventivas/             # Monitoreo proactivo
│   ├── oc_por_vencer.sql
│   ├── distribuciones_excedentes.sql
│   ├── distribuciones_incompletas.sql
│   ├── sku_sin_innerpack.sql
│   ├── asn_sin_actualizar.sql
│   ├── ubicaciones_llenas.sql
│   └── usuarios_inactivos.sql
├── bajo_demanda/            # Consultas específicas
│   ├── buscar_oc.sql
│   ├── buscar_sku.sql
│   ├── buscar_lpn.sql
│   ├── buscar_asn.sql
│   ├── historial_oc.sql
│   ├── detalle_distribucion.sql
│   ├── movimientos_lpn.sql
│   └── auditoria_usuario.sql
├── templates/               # Templates Jinja2
│   ├── base_oc_query.sql.j2
│   ├── base_distribution_query.sql.j2
│   ├── base_asn_query.sql.j2
│   ├── date_range_filter.sql.j2
│   └── pagination.sql.j2
└── ddl/                     # Vistas y Stored Procedures
    ├── views/
    │   ├── v_oc_summary.sql
    │   ├── v_distribution_totals.sql
    │   └── v_asn_status.sql
    └── procedures/
        ├── sp_validate_oc.sql
        └── sp_get_daily_report.sql

Uso básico:
----------
    from queries.query_loader import QueryLoader, QueryCategory

    # Crear loader
    loader = QueryLoader()

    # Cargar query simple
    sql = loader.load_query(QueryCategory.OBLIGATORIAS, "oc_diarias")

    # Cargar query con parámetros
    sql, params = loader.load_query_with_params(
        QueryCategory.BAJO_DEMANDA,
        "buscar_oc",
        {"oc_numero": "C750384123456", "storerkey": "C22"},
        use_placeholders=True
    )

    # Listar queries disponibles
    queries = loader.list_queries()

    # Validar todas las queries
    results = loader.validate_all_queries()

Funciones de conveniencia:
-------------------------
    from queries import load_query, load_query_with_params

    sql = load_query("obligatorias", "oc_diarias")
    sql = load_query_with_params("bajo_demanda", "buscar_oc", {"oc_numero": "C123"})

Base de datos: DB2 - Manhattan WMS (WM260BASD)
Schema: WMWHSE1
CEDIS: Cancún 427

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
═══════════════════════════════════════════════════════════════
"""

# Importar versión desde configuración centralizada
from config import VERSION, __author__, __author_code__

__version__ = VERSION
__date__ = "2025-11-21"

# Importar clases y funciones principales
from .query_loader import (
    QueryLoader,
    QueryCategory,
    QueryType,
    QueryMetadata,
    QueryResult,
    QueryLoaderError,
    QueryNotFoundError,
    QueryValidationError,
    QueryTemplateError,
    get_default_loader,
    load_query,
    load_query_with_params,
)

# Definir exports públicos
__all__ = [
    # Clases principales
    'QueryLoader',
    'QueryCategory',
    'QueryType',
    'QueryMetadata',
    'QueryResult',

    # Excepciones
    'QueryLoaderError',
    'QueryNotFoundError',
    'QueryValidationError',
    'QueryTemplateError',

    # Funciones de conveniencia
    'get_default_loader',
    'load_query',
    'load_query_with_params',

    # Categorías como constantes de conveniencia
    'OBLIGATORIAS',
    'PREVENTIVAS',
    'BAJO_DEMANDA',
]

# Constantes de categorías para acceso fácil
OBLIGATORIAS = QueryCategory.OBLIGATORIAS
PREVENTIVAS = QueryCategory.PREVENTIVAS
BAJO_DEMANDA = QueryCategory.BAJO_DEMANDA


def get_summary() -> str:
    """
    Retorna un resumen del módulo de queries.

    Returns:
        str: Resumen formateado
    """
    loader = get_default_loader()

    summary_lines = [
        "",
        "=" * 60,
        "MÓDULO DE CONSULTAS SQL - Sistema SAC",
        "=" * 60,
        f"Versión: {__version__}",
        f"Schema: WMWHSE1",
        f"CEDIS: Cancún 427",
        "-" * 60,
    ]

    for category in [QueryCategory.OBLIGATORIAS, QueryCategory.PREVENTIVAS, QueryCategory.BAJO_DEMANDA]:
        queries = loader.list_queries(category)
        summary_lines.append(f"\n{category.value.upper()}: {len(queries)} queries")
        for q in queries:
            summary_lines.append(f"  - {q.split('/')[1]}")

    templates = loader.list_templates()
    summary_lines.append(f"\nTEMPLATES: {len(templates)} templates")
    for t in templates:
        summary_lines.append(f"  - {t}")

    summary_lines.append("")
    summary_lines.append("=" * 60)

    return "\n".join(summary_lines)


# Mostrar información al importar (si se ejecuta como script)
if __name__ == "__main__":
    print(get_summary())
