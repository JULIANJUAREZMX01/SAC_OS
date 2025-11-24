# Consultas SQL - Sistema SAC

Sistema completo de consultas SQL para Manhattan WMS (DB2).

## Estructura

```
queries/
├── query_loader.py          # Cargador principal de queries
├── obligatorias/            # 8 queries de ejecución diaria
├── preventivas/             # 7 queries de monitoreo proactivo
├── bajo_demanda/            # 8 queries específicas
├── templates/               # 5 templates Jinja2
└── ddl/                     # Vistas y Stored Procedures
    ├── views/               # 3 vistas
    └── procedures/          # 2 stored procedures
```

## Queries Obligatorias (8)

Ejecutadas diariamente de forma automática:

| Query | Descripción |
|-------|-------------|
| `oc_diarias` | OCs del día actual |
| `oc_pendientes` | OCs sin procesar |
| `oc_vencidas` | OCs expiradas |
| `distribuciones_dia` | Distribuciones del día |
| `asn_pendientes` | ASNs sin recibir |
| `asn_status` | Estado de todos los ASNs |
| `inventario_resumen` | Resumen de inventario |
| `recibo_programado` | Programa de recibo del día |

## Queries Preventivas (7)

Monitoreo proactivo para prevenir problemas:

| Query | Descripción | Prioridad |
|-------|-------------|-----------|
| `oc_por_vencer` | OCs próximas a vencer (3 días) | Alta |
| `distribuciones_excedentes` | Distribuciones > OC | **CRÍTICA** |
| `distribuciones_incompletas` | Distribuciones < OC | Media |
| `sku_sin_innerpack` | SKUs sin Inner Pack | Media |
| `asn_sin_actualizar` | ASNs estancados | Alta |
| `ubicaciones_llenas` | Ubicaciones al límite | Media |
| `usuarios_inactivos` | Usuarios sin actividad | Baja |

## Queries Bajo Demanda (8)

Consultas específicas según necesidad:

| Query | Descripción |
|-------|-------------|
| `buscar_oc` | Búsqueda por número OC |
| `buscar_sku` | Búsqueda por SKU |
| `buscar_lpn` | Búsqueda por LPN |
| `buscar_asn` | Búsqueda por ASN |
| `historial_oc` | Historial completo de OC |
| `detalle_distribucion` | Detalle por tienda |
| `movimientos_lpn` | Trazabilidad de LPN |
| `auditoria_usuario` | Actividad de usuario |

## Uso del Query Loader

### Carga Simple

```python
from queries import QueryLoader, QueryCategory

loader = QueryLoader()

# Cargar query
sql = loader.load_query(QueryCategory.OBLIGATORIAS, "oc_diarias")
```

### Con Parámetros

```python
# Sustitución directa
sql, _ = loader.load_query_with_params(
    QueryCategory.BAJO_DEMANDA,
    "buscar_oc",
    {"oc_numero": "C750384123456", "storerkey": "C22"}
)

# Con placeholders para prepared statements
sql, params = loader.load_query_with_params(
    QueryCategory.BAJO_DEMANDA,
    "buscar_oc",
    {"oc_numero": "C123456", "storerkey": "C22"},
    use_placeholders=True
)
```

### Funciones de Conveniencia

```python
from queries import load_query, load_query_with_params

sql = load_query("obligatorias", "oc_diarias")
sql = load_query_with_params("bajo_demanda", "buscar_oc", {"oc_numero": "C123"})
```

### Listar Queries

```python
# Listar todas
queries = loader.list_queries()

# Por categoría
obligatorias = loader.list_queries(QueryCategory.OBLIGATORIAS)

# Templates
templates = loader.list_templates()
```

### Validación

```python
# Validar una query
is_valid, errors = loader.validate_query(sql)

# Validar todas
results = loader.validate_all_queries()
```

## Templates Jinja2

Templates parametrizados para queries dinámicas:

| Template | Descripción |
|----------|-------------|
| `base_oc_query` | Query base para OCs |
| `base_distribution_query` | Query base para distribuciones |
| `base_asn_query` | Query base para ASN |
| `date_range_filter` | Filtro de rango de fechas |
| `pagination` | Paginación para queries grandes |

### Uso de Templates

```python
sql = loader.load_template('base_oc_query', {
    'storerkey': 'C22',
    'status_filter': ['0', '1'],
    'include_detail': True,
    'limit': 100
})
```

## DDL - Vistas y Stored Procedures

### Vistas

| Vista | Descripción |
|-------|-------------|
| `v_oc_summary` | Resumen consolidado de OCs |
| `v_distribution_totals` | Totales de distribuciones |
| `v_asn_status` | Estado de ASNs con métricas |

### Stored Procedures

| Procedimiento | Descripción |
|---------------|-------------|
| `sp_validate_oc` | Validación OC vs Distribuciones |
| `sp_get_daily_report` | Reporte diario automatizado |

## Formato de Archivos SQL

Cada archivo SQL sigue este formato:

```sql
-- ============================================
-- NOMBRE: Descripción de la consulta
-- CATEGORÍA: obligatoria / preventiva / bajo_demanda
-- FRECUENCIA: Diaria / Semanal / Bajo demanda
-- AUTOR: ADMJAJA
-- FECHA: YYYY-MM-DD
-- VERSION: 1.0.0
-- ============================================

-- DESCRIPCIÓN:
-- Explicación detallada

-- TABLAS INVOLUCRADAS:
-- - TABLA1
-- - TABLA2

-- PARAMETROS:
-- {{param1}} - Descripción
-- {{param2}} - Descripción

SELECT ...
```

## Tests

Ejecutar tests de validación:

```bash
# Todos los tests
pytest tests/test_query_loader.py -v

# Con coverage
pytest tests/test_query_loader.py -v --cov=queries
```

## Estadísticas

- **Total queries SQL**: 23
- **Templates Jinja2**: 5
- **Vistas DDL**: 3
- **Stored Procedures**: 2
- **Total archivos**: 33+

---

**Desarrollado por:** Julián Alexander Juárez Alvarado (ADMJAJA)
**CEDIS Cancún 427** - Tiendas Chedraui S.A. de C.V.
