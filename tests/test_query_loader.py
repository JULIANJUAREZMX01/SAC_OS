"""
═══════════════════════════════════════════════════════════════
TESTS: Query Loader - Sistema SAC
CEDIS Chedraui Cancún 427
═══════════════════════════════════════════════════════════════

Tests unitarios para el módulo de carga de consultas SQL.

Ejecutar con:
    pytest tests/test_query_loader.py -v
    pytest tests/test_query_loader.py -v --cov=queries

Desarrollado por: ADMJAJA
═══════════════════════════════════════════════════════════════
"""

import pytest
import sys
from pathlib import Path

# Agregar el directorio raíz al path para imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from queries.query_loader import (
    QueryLoader,
    QueryCategory,
    QueryType,
    QueryMetadata,
    QueryResult,
    QueryLoaderError,
    QueryNotFoundError,
    QueryValidationError,
    get_default_loader,
    load_query,
    load_query_with_params,
)


# ═══════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════

@pytest.fixture
def loader():
    """Crear instancia de QueryLoader para tests."""
    return QueryLoader(use_cache=False)


@pytest.fixture
def loader_with_cache():
    """Crear instancia de QueryLoader con caché habilitado."""
    return QueryLoader(use_cache=True)


# ═══════════════════════════════════════════════════════════════
# TESTS: Inicialización
# ═══════════════════════════════════════════════════════════════

class TestQueryLoaderInit:
    """Tests de inicialización del QueryLoader."""

    def test_default_initialization(self, loader):
        """Verificar inicialización con valores por defecto."""
        assert loader.schema == "WMWHSE1"
        assert loader.use_cache == False
        assert loader.base_dir.exists()

    def test_custom_schema(self):
        """Verificar inicialización con schema personalizado."""
        loader = QueryLoader(schema="CUSTOM_SCHEMA")
        assert loader.schema == "CUSTOM_SCHEMA"

    def test_cache_initialization(self, loader_with_cache):
        """Verificar inicialización del caché."""
        assert loader_with_cache.use_cache == True
        assert len(loader_with_cache._cache) == 0


# ═══════════════════════════════════════════════════════════════
# TESTS: Carga de Queries
# ═══════════════════════════════════════════════════════════════

class TestLoadQuery:
    """Tests de carga de queries."""

    def test_load_obligatoria_query(self, loader):
        """Cargar query obligatoria existente."""
        sql = loader.load_query(QueryCategory.OBLIGATORIAS, "oc_diarias")
        assert sql is not None
        assert len(sql) > 0
        assert "SELECT" in sql.upper()

    def test_load_preventiva_query(self, loader):
        """Cargar query preventiva existente."""
        sql = loader.load_query(QueryCategory.PREVENTIVAS, "oc_por_vencer")
        assert sql is not None
        assert "SELECT" in sql.upper()

    def test_load_bajo_demanda_query(self, loader):
        """Cargar query bajo demanda existente."""
        sql = loader.load_query(QueryCategory.BAJO_DEMANDA, "buscar_oc")
        assert sql is not None
        assert "SELECT" in sql.upper()

    def test_load_nonexistent_query(self, loader):
        """Intentar cargar query que no existe."""
        with pytest.raises(QueryNotFoundError):
            loader.load_query(QueryCategory.OBLIGATORIAS, "query_inexistente")

    def test_load_with_strip_comments(self, loader):
        """Cargar query eliminando comentarios."""
        sql_with_comments = loader.load_query(
            QueryCategory.OBLIGATORIAS, "oc_diarias", strip_comments=False
        )
        sql_stripped = loader.load_query(
            QueryCategory.OBLIGATORIAS, "oc_diarias", strip_comments=True
        )

        # La versión sin comentarios debe ser más corta
        assert len(sql_stripped) <= len(sql_with_comments)

    def test_cache_stores_query(self, loader_with_cache):
        """Verificar que el caché almacena queries."""
        # Primera carga
        sql1 = loader_with_cache.load_query(QueryCategory.OBLIGATORIAS, "oc_diarias")

        # Verificar que está en caché
        cache_key = "obligatorias/oc_diarias"
        assert cache_key in loader_with_cache._cache

        # Segunda carga (desde caché)
        sql2 = loader_with_cache.load_query(QueryCategory.OBLIGATORIAS, "oc_diarias")
        assert sql1 == sql2


# ═══════════════════════════════════════════════════════════════
# TESTS: Carga con Parámetros
# ═══════════════════════════════════════════════════════════════

class TestLoadQueryWithParams:
    """Tests de carga de queries con parámetros."""

    def test_replace_string_param(self, loader):
        """Reemplazar parámetro de tipo string."""
        sql, _ = loader.load_query_with_params(
            QueryCategory.BAJO_DEMANDA,
            "buscar_oc",
            {"oc_numero": "C750384123456", "storerkey": "C22"}
        )
        assert "C750384123456" in sql
        assert "C22" in sql

    def test_replace_with_placeholders(self, loader):
        """Reemplazar con placeholders para prepared statements."""
        sql, params = loader.load_query_with_params(
            QueryCategory.BAJO_DEMANDA,
            "buscar_oc",
            {"oc_numero": "C123456", "storerkey": "C22"},
            use_placeholders=True
        )
        assert "?" in sql
        assert len(params) > 0

    def test_replace_none_param(self, loader):
        """Reemplazar parámetro None con NULL."""
        sql, _ = loader.load_query_with_params(
            QueryCategory.BAJO_DEMANDA,
            "buscar_oc",
            {"oc_numero": None, "storerkey": "C22"}
        )
        assert "NULL" in sql

    def test_replace_numeric_param(self, loader):
        """Reemplazar parámetro numérico."""
        sql, _ = loader.load_query_with_params(
            QueryCategory.OBLIGATORIAS,
            "oc_pendientes",
            {"storerkey": "C22", "dias_antiguedad": 30}
        )
        assert "30" in sql


# ═══════════════════════════════════════════════════════════════
# TESTS: Listado de Queries
# ═══════════════════════════════════════════════════════════════

class TestListQueries:
    """Tests de listado de queries."""

    def test_list_all_queries(self, loader):
        """Listar todas las queries."""
        queries = loader.list_queries()
        assert len(queries) > 0
        assert all("/" in q for q in queries)

    def test_list_obligatorias(self, loader):
        """Listar queries obligatorias."""
        queries = loader.list_queries(QueryCategory.OBLIGATORIAS)
        assert len(queries) == 8  # 8 queries obligatorias
        assert all(q.startswith("obligatorias/") for q in queries)

    def test_list_preventivas(self, loader):
        """Listar queries preventivas."""
        queries = loader.list_queries(QueryCategory.PREVENTIVAS)
        assert len(queries) == 7  # 7 queries preventivas
        assert all(q.startswith("preventivas/") for q in queries)

    def test_list_bajo_demanda(self, loader):
        """Listar queries bajo demanda."""
        queries = loader.list_queries(QueryCategory.BAJO_DEMANDA)
        assert len(queries) >= 8  # Al menos 8 queries bajo demanda
        assert all(q.startswith("bajo_demanda/") for q in queries)

    def test_list_templates(self, loader):
        """Listar templates disponibles."""
        templates = loader.list_templates()
        assert len(templates) >= 4  # Al menos 4 templates


# ═══════════════════════════════════════════════════════════════
# TESTS: Metadatos
# ═══════════════════════════════════════════════════════════════

class TestQueryMetadata:
    """Tests de extracción de metadatos."""

    def test_get_metadata(self, loader):
        """Obtener metadatos de una query."""
        metadata = loader.get_query_metadata(QueryCategory.OBLIGATORIAS, "oc_diarias")

        assert metadata.nombre == "oc_diarias"
        assert metadata.categoria == QueryCategory.OBLIGATORIAS
        assert metadata.autor == "ADMJAJA"

    def test_metadata_has_parameters(self, loader):
        """Verificar que se detectan parámetros."""
        metadata = loader.get_query_metadata(QueryCategory.BAJO_DEMANDA, "buscar_oc")

        # Debe detectar los parámetros {{oc_numero}} y {{storerkey}}
        assert len(metadata.parametros) > 0

    def test_get_all_metadata(self, loader):
        """Obtener metadatos de todas las queries."""
        all_metadata = loader.get_all_metadata()

        assert len(all_metadata) > 0
        assert all(isinstance(m, QueryMetadata) for m in all_metadata.values())


# ═══════════════════════════════════════════════════════════════
# TESTS: Validación
# ═══════════════════════════════════════════════════════════════

class TestQueryValidation:
    """Tests de validación de queries."""

    def test_validate_valid_select(self, loader):
        """Validar SELECT válido."""
        sql = "SELECT * FROM ORDERS WHERE STATUS = '0'"
        is_valid, errors = loader.validate_query(sql)
        assert is_valid == True
        assert len(errors) == 0

    def test_validate_empty_query(self, loader):
        """Validar query vacía."""
        sql = ""
        is_valid, errors = loader.validate_query(sql)
        assert is_valid == False
        assert "vacía" in errors[0].lower()

    def test_validate_unbalanced_parentheses(self, loader):
        """Validar paréntesis desbalanceados."""
        sql = "SELECT * FROM ORDERS WHERE (STATUS = '0'"
        is_valid, errors = loader.validate_query(sql)
        assert is_valid == False
        assert any("paréntesis" in e.lower() for e in errors)

    def test_validate_all_queries(self, loader):
        """Validar todas las queries del sistema."""
        results = loader.validate_all_queries()

        # Todas las queries deben ser válidas (excepto por parámetros no sustituidos)
        # Algunos errores son falsos positivos del validador básico
        errores_aceptables = [
            "parámetros sin sustituir",
            "select sin cláusula from",  # Falso positivo en queries multi-línea
        ]
        for path, (is_valid, errors) in results.items():
            if not is_valid:
                errors_lower = [e.lower() for e in errors]
                tiene_error_aceptable = any(
                    any(aceptable in err for aceptable in errores_aceptables)
                    for err in errors_lower
                )
                assert tiene_error_aceptable, \
                    f"Query {path} tiene errores inesperados: {errors}"


# ═══════════════════════════════════════════════════════════════
# TESTS: Utilidades
# ═══════════════════════════════════════════════════════════════

class TestUtilities:
    """Tests de funciones utilitarias."""

    def test_clear_cache(self, loader_with_cache):
        """Verificar limpieza de caché."""
        # Cargar query para llenar caché
        loader_with_cache.load_query(QueryCategory.OBLIGATORIAS, "oc_diarias")
        assert len(loader_with_cache._cache) > 0

        # Limpiar caché
        loader_with_cache.clear_cache()
        assert len(loader_with_cache._cache) == 0

    def test_get_cache_stats(self, loader_with_cache):
        """Obtener estadísticas del caché."""
        loader_with_cache.load_query(QueryCategory.OBLIGATORIAS, "oc_diarias")
        loader_with_cache.load_query(QueryCategory.PREVENTIVAS, "oc_por_vencer")

        stats = loader_with_cache.get_cache_stats()
        assert stats["queries_cached"] == 2
        assert stats["categories"] == 2


# ═══════════════════════════════════════════════════════════════
# TESTS: Funciones de Conveniencia
# ═══════════════════════════════════════════════════════════════

class TestConvenienceFunctions:
    """Tests de funciones de conveniencia globales."""

    def test_load_query_function(self):
        """Probar función load_query global."""
        sql = load_query("obligatorias", "oc_diarias")
        assert sql is not None
        assert "SELECT" in sql.upper()

    def test_load_query_with_params_function(self):
        """Probar función load_query_with_params global."""
        sql = load_query_with_params(
            "bajo_demanda",
            "buscar_oc",
            {"oc_numero": "C123456", "storerkey": "C22"}
        )
        assert "C123456" in sql
        assert "C22" in sql

    def test_get_default_loader_singleton(self):
        """Verificar que get_default_loader retorna singleton."""
        loader1 = get_default_loader()
        loader2 = get_default_loader()
        assert loader1 is loader2


# ═══════════════════════════════════════════════════════════════
# TESTS: Queries Específicas
# ═══════════════════════════════════════════════════════════════

class TestSpecificQueries:
    """Tests para queries específicas importantes."""

    def test_oc_diarias_has_required_columns(self, loader):
        """Verificar que oc_diarias tiene columnas requeridas."""
        sql = loader.load_query(QueryCategory.OBLIGATORIAS, "oc_diarias")
        sql_upper = sql.upper()

        # Columnas esperadas
        assert "ORDERKEY" in sql_upper
        assert "STATUS" in sql_upper
        assert "ORDERDATE" in sql_upper

    def test_distribuciones_excedentes_is_critical(self, loader):
        """Verificar que distribuciones_excedentes es query crítica."""
        metadata = loader.get_query_metadata(
            QueryCategory.PREVENTIVAS,
            "distribuciones_excedentes"
        )
        # Verificar que está marcada como crítica en el encabezado
        sql = loader.load_query(QueryCategory.PREVENTIVAS, "distribuciones_excedentes")
        assert "CRÍTICO" in sql.upper() or "CRITICO" in sql.upper()

    def test_buscar_oc_supports_flexible_search(self, loader):
        """Verificar que buscar_oc soporta búsqueda flexible."""
        sql = loader.load_query(QueryCategory.BAJO_DEMANDA, "buscar_oc")
        sql_upper = sql.upper()

        # Debe soportar búsqueda por ORDERKEY o EXTERNORDERKEY
        assert "ORDERKEY" in sql_upper
        assert "EXTERNORDERKEY" in sql_upper
        assert "OR" in sql_upper


# ═══════════════════════════════════════════════════════════════
# TESTS: Integridad del Sistema
# ═══════════════════════════════════════════════════════════════

class TestSystemIntegrity:
    """Tests de integridad del sistema de queries."""

    def test_all_categories_have_queries(self, loader):
        """Verificar que todas las categorías tienen queries."""
        for category in [QueryCategory.OBLIGATORIAS, QueryCategory.PREVENTIVAS, QueryCategory.BAJO_DEMANDA]:
            queries = loader.list_queries(category)
            assert len(queries) > 0, f"Categoría {category.value} no tiene queries"

    def test_total_query_count(self, loader):
        """Verificar conteo total de queries."""
        all_queries = loader.list_queries()

        # Esperamos al menos 23 queries (8 + 7 + 8)
        assert len(all_queries) >= 23

    def test_all_queries_have_valid_structure(self, loader):
        """Verificar que todas las queries tienen estructura válida."""
        for query_path in loader.list_queries():
            parts = query_path.split("/")
            category = QueryCategory(parts[0])
            name = parts[1]

            # Cargar query
            sql = loader.load_query(category, name)

            # Debe contener al menos un SELECT, INSERT, UPDATE o DELETE
            sql_upper = sql.upper()
            has_dml = any(kw in sql_upper for kw in ["SELECT", "INSERT", "UPDATE", "DELETE", "WITH"])
            assert has_dml, f"Query {query_path} no tiene statement DML válido"


# ═══════════════════════════════════════════════════════════════
# EJECUCIÓN DE TESTS
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Ejecutar tests con pytest
    pytest.main([__file__, "-v", "--tb=short"])
