"""
═══════════════════════════════════════════════════════════════
QUERY LOADER - Cargador de Consultas SQL
Sistema SAC - CEDIS Chedraui Cancún 427
═══════════════════════════════════════════════════════════════

Módulo para cargar, gestionar y validar consultas SQL organizadas
para el sistema Manhattan WMS (DB2).

Funcionalidades:
- Carga de queries desde archivos SQL
- Sustitución de parámetros
- Validación de sintaxis SQL
- Caché de queries cargadas
- Soporte para templates Jinja2

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
═══════════════════════════════════════════════════════════════
"""

import os
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

# Importar versión desde configuración centralizada
from config import VERSION

# Configurar logger
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# CONSTANTES Y ENUMERACIONES
# ═══════════════════════════════════════════════════════════════

class QueryCategory(Enum):
    """Categorías de consultas SQL"""
    OBLIGATORIAS = "obligatorias"
    PREVENTIVAS = "preventivas"
    BAJO_DEMANDA = "bajo_demanda"
    TEMPLATES = "templates"
    DDL = "ddl"


class QueryType(Enum):
    """Tipos de consultas SQL"""
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    CREATE = "CREATE"
    ALTER = "ALTER"
    DROP = "DROP"
    CALL = "CALL"


@dataclass
class QueryMetadata:
    """Metadatos de una consulta SQL"""
    nombre: str
    categoria: QueryCategory
    descripcion: str = ""
    frecuencia: str = ""
    autor: str = "ADMJAJA"
    fecha: str = ""
    tablas_involucradas: List[str] = field(default_factory=list)
    parametros: List[str] = field(default_factory=list)
    query_type: QueryType = QueryType.SELECT
    archivo: str = ""
    version: str = VERSION  # Usar VERSION desde config.py


@dataclass
class QueryResult:
    """Resultado de carga de query"""
    sql: str
    metadata: QueryMetadata
    is_valid: bool
    validation_errors: List[str] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════
# EXCEPCIONES
# ═══════════════════════════════════════════════════════════════

class QueryLoaderError(Exception):
    """Error base para QueryLoader"""
    pass


class QueryNotFoundError(QueryLoaderError):
    """Query no encontrada"""
    pass


class QueryValidationError(QueryLoaderError):
    """Error de validación de query"""
    pass


class QueryTemplateError(QueryLoaderError):
    """Error en template de query"""
    pass


# ═══════════════════════════════════════════════════════════════
# CLASE PRINCIPAL: QueryLoader
# ═══════════════════════════════════════════════════════════════

class QueryLoader:
    """
    Cargador de consultas SQL para el sistema SAC.

    Proporciona funcionalidades para:
    - Cargar queries desde archivos SQL organizados por categoría
    - Sustituir parámetros de forma segura
    - Validar sintaxis SQL básica
    - Cachear queries para mejor rendimiento
    - Renderizar templates Jinja2

    Ejemplo de uso:
    ```python
    loader = QueryLoader()

    # Cargar query simple
    sql = loader.load_query(QueryCategory.OBLIGATORIAS, "oc_diarias")

    # Cargar query con parámetros
    sql = loader.load_query_with_params(
        QueryCategory.BAJO_DEMANDA,
        "buscar_oc",
        {"oc_number": "C750384123456"}
    )

    # Listar queries disponibles
    queries = loader.list_queries(QueryCategory.OBLIGATORIAS)
    ```
    """

    # Directorio base de queries (relativo a este archivo)
    BASE_DIR = Path(__file__).parent

    # Schema por defecto para Manhattan WMS
    DEFAULT_SCHEMA = "WMWHSE1"

    # Extensión de archivos SQL
    SQL_EXTENSION = ".sql"

    # Extensión de templates Jinja2
    TEMPLATE_EXTENSION = ".sql.j2"

    def __init__(
        self,
        base_dir: Optional[Path] = None,
        schema: str = DEFAULT_SCHEMA,
        use_cache: bool = True
    ):
        """
        Inicializa el QueryLoader.

        Args:
            base_dir: Directorio base de queries (opcional)
            schema: Schema de base de datos (default: WMWHSE1)
            use_cache: Usar caché de queries (default: True)
        """
        self.base_dir = base_dir or self.BASE_DIR
        self.schema = schema
        self.use_cache = use_cache

        # Caché de queries cargadas
        self._cache: Dict[str, QueryResult] = {}

        # Validar estructura de directorios
        self._validate_directory_structure()

        logger.info(f"📂 QueryLoader inicializado. Base: {self.base_dir}")

    # ═══════════════════════════════════════════════════════════════
    # MÉTODOS PÚBLICOS - CARGA DE QUERIES
    # ═══════════════════════════════════════════════════════════════

    def load_query(
        self,
        category: QueryCategory,
        name: str,
        strip_comments: bool = False
    ) -> str:
        """
        Carga una consulta SQL desde archivo.

        Args:
            category: Categoría de la query (OBLIGATORIAS, PREVENTIVAS, etc.)
            name: Nombre del archivo (sin extensión .sql)
            strip_comments: Eliminar comentarios del SQL

        Returns:
            str: Consulta SQL

        Raises:
            QueryNotFoundError: Si la query no existe
            QueryLoaderError: Si hay error al cargar
        """
        cache_key = f"{category.value}/{name}"

        # Verificar caché
        if self.use_cache and cache_key in self._cache:
            logger.debug(f"📋 Query cargada desde caché: {cache_key}")
            result = self._cache[cache_key]
            return self._strip_comments(result.sql) if strip_comments else result.sql

        # Cargar desde archivo
        result = self._load_query_file(category, name)

        # Guardar en caché
        if self.use_cache:
            self._cache[cache_key] = result

        sql = result.sql
        if strip_comments:
            sql = self._strip_comments(sql)

        logger.info(f"✅ Query cargada: {cache_key}")
        return sql

    def load_query_with_params(
        self,
        category: QueryCategory,
        name: str,
        params: Dict[str, Any],
        use_placeholders: bool = False
    ) -> Tuple[str, Tuple]:
        """
        Carga una consulta SQL y sustituye parámetros.

        Soporta dos modos:
        1. Sustitución directa: Reemplaza {{param}} por valor
        2. Placeholders: Reemplaza {{param}} por ? y retorna valores

        Args:
            category: Categoría de la query
            name: Nombre del archivo
            params: Diccionario de parámetros
            use_placeholders: Usar ? placeholders para DB2

        Returns:
            Tuple[str, Tuple]: (SQL, valores de parámetros)

        Ejemplo:
            ```python
            # Modo sustitución directa
            sql, _ = loader.load_query_with_params(
                QueryCategory.BAJO_DEMANDA,
                "buscar_oc",
                {"oc_number": "C123456"}
            )
            # SQL: SELECT * FROM ORDERS WHERE ORDERKEY = 'C123456'

            # Modo placeholders
            sql, params = loader.load_query_with_params(
                QueryCategory.BAJO_DEMANDA,
                "buscar_oc",
                {"oc_number": "C123456"},
                use_placeholders=True
            )
            # SQL: SELECT * FROM ORDERS WHERE ORDERKEY = ?
            # params: ('C123456',)
            ```
        """
        sql = self.load_query(category, name)

        if use_placeholders:
            return self._replace_with_placeholders(sql, params)
        else:
            return self._replace_params(sql, params), ()

    def load_template(
        self,
        template_name: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Carga y renderiza un template Jinja2.

        Args:
            template_name: Nombre del template (sin extensión .sql.j2)
            context: Diccionario con variables del template

        Returns:
            str: SQL renderizado

        Raises:
            QueryTemplateError: Si hay error en el template
        """
        try:
            from jinja2 import Environment, FileSystemLoader, StrictUndefined

            template_dir = self.base_dir / "templates"
            env = Environment(
                loader=FileSystemLoader(str(template_dir)),
                undefined=StrictUndefined,
                trim_blocks=True,
                lstrip_blocks=True
            )

            template_file = f"{template_name}{self.TEMPLATE_EXTENSION}"
            template = env.get_template(template_file)

            # Agregar schema al contexto
            context.setdefault('schema', self.schema)

            sql = template.render(**context)
            logger.info(f"✅ Template renderizado: {template_name}")
            return sql

        except ImportError:
            raise QueryTemplateError(
                "Jinja2 no está instalado. Ejecute: pip install jinja2"
            )
        except Exception as e:
            raise QueryTemplateError(f"Error en template {template_name}: {e}")

    # ═══════════════════════════════════════════════════════════════
    # MÉTODOS PÚBLICOS - LISTADO Y METADATOS
    # ═══════════════════════════════════════════════════════════════

    def list_queries(
        self,
        category: Optional[QueryCategory] = None
    ) -> List[str]:
        """
        Lista todas las queries disponibles.

        Args:
            category: Categoría específica (None = todas)

        Returns:
            List[str]: Lista de nombres de queries
        """
        queries = []

        categories = [category] if category else list(QueryCategory)

        for cat in categories:
            if cat in (QueryCategory.TEMPLATES, QueryCategory.DDL):
                continue  # Estos tienen estructura diferente

            cat_dir = self.base_dir / cat.value
            if not cat_dir.exists():
                continue

            for file in cat_dir.glob(f"*{self.SQL_EXTENSION}"):
                if file.name != "__init__.py":
                    query_name = file.stem
                    queries.append(f"{cat.value}/{query_name}")

        return sorted(queries)

    def list_templates(self) -> List[str]:
        """Lista todos los templates disponibles."""
        templates = []
        template_dir = self.base_dir / "templates"

        if template_dir.exists():
            for file in template_dir.glob(f"*{self.TEMPLATE_EXTENSION}"):
                templates.append(file.stem.replace(".sql", ""))

        return sorted(templates)

    def get_query_metadata(
        self,
        category: QueryCategory,
        name: str
    ) -> QueryMetadata:
        """
        Obtiene los metadatos de una query.

        Args:
            category: Categoría de la query
            name: Nombre del archivo

        Returns:
            QueryMetadata: Metadatos de la query
        """
        cache_key = f"{category.value}/{name}"

        if self.use_cache and cache_key in self._cache:
            return self._cache[cache_key].metadata

        result = self._load_query_file(category, name)

        if self.use_cache:
            self._cache[cache_key] = result

        return result.metadata

    def get_all_metadata(self) -> Dict[str, QueryMetadata]:
        """
        Obtiene metadatos de todas las queries.

        Returns:
            Dict[str, QueryMetadata]: Diccionario con metadatos
        """
        metadata = {}

        for query_path in self.list_queries():
            parts = query_path.split("/")
            category = QueryCategory(parts[0])
            name = parts[1]

            try:
                metadata[query_path] = self.get_query_metadata(category, name)
            except Exception as e:
                logger.warning(f"⚠️ No se pudo cargar metadata de {query_path}: {e}")

        return metadata

    # ═══════════════════════════════════════════════════════════════
    # MÉTODOS PÚBLICOS - VALIDACIÓN
    # ═══════════════════════════════════════════════════════════════

    def validate_query(self, sql: str) -> Tuple[bool, List[str]]:
        """
        Valida la sintaxis básica de una consulta SQL.

        Args:
            sql: Consulta SQL a validar

        Returns:
            Tuple[bool, List[str]]: (es_válida, lista_errores)
        """
        errors = []
        sql_clean = self._strip_comments(sql).strip()

        if not sql_clean:
            errors.append("La consulta está vacía")
            return False, errors

        # Verificar que inicia con palabra clave válida
        keywords = ["SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "ALTER",
                    "DROP", "CALL", "WITH", "MERGE"]
        first_word = sql_clean.split()[0].upper()
        if first_word not in keywords:
            errors.append(f"Palabra clave SQL inválida: {first_word}")

        # Verificar paréntesis balanceados
        if sql_clean.count("(") != sql_clean.count(")"):
            errors.append("Paréntesis desbalanceados")

        # Verificar comillas simples balanceadas
        # (Ignorando comillas escapadas '')
        sql_no_escaped = sql_clean.replace("''", "")
        if sql_no_escaped.count("'") % 2 != 0:
            errors.append("Comillas simples desbalanceadas")

        # Verificar que SELECT tiene FROM (excepto SELECT de constantes)
        if first_word == "SELECT" and " FROM " not in sql_clean.upper():
            # Permitir SELECT de constantes como SELECT 1, SELECT CURRENT_DATE
            if not re.search(r"SELECT\s+[\d\w_()]+\s*$", sql_clean.upper()):
                if "DUAL" not in sql_clean.upper() and "SYSIBM" not in sql_clean.upper():
                    errors.append("SELECT sin cláusula FROM")

        # Verificar placeholder syntax para DB2
        if "{{" in sql_clean and "}}" in sql_clean:
            # Hay parámetros pendientes de sustitución
            params = re.findall(r"\{\{(\w+)\}\}", sql_clean)
            if params:
                errors.append(f"Parámetros sin sustituir: {params}")

        is_valid = len(errors) == 0
        return is_valid, errors

    def validate_all_queries(self) -> Dict[str, Tuple[bool, List[str]]]:
        """
        Valida todas las queries del sistema.

        Returns:
            Dict[str, Tuple[bool, List[str]]]: Resultados de validación
        """
        results = {}

        for query_path in self.list_queries():
            parts = query_path.split("/")
            category = QueryCategory(parts[0])
            name = parts[1]

            try:
                sql = self.load_query(category, name)
                results[query_path] = self.validate_query(sql)
            except Exception as e:
                results[query_path] = (False, [str(e)])

        return results

    # ═══════════════════════════════════════════════════════════════
    # MÉTODOS PÚBLICOS - UTILIDADES
    # ═══════════════════════════════════════════════════════════════

    def clear_cache(self):
        """Limpia el caché de queries."""
        self._cache.clear()
        logger.info("🗑️ Caché de queries limpiado")

    def get_cache_stats(self) -> Dict[str, int]:
        """
        Obtiene estadísticas del caché.

        Returns:
            Dict: Estadísticas del caché
        """
        return {
            "queries_cached": len(self._cache),
            "categories": len(set(k.split("/")[0] for k in self._cache.keys()))
        }

    def print_summary(self):
        """Imprime un resumen del sistema de queries."""
        print("\n" + "═" * 60)
        print("📁 SISTEMA DE CONSULTAS SQL - SAC")
        print("═" * 60)
        print(f"Directorio base: {self.base_dir}")
        print(f"Schema: {self.schema}")
        print(f"Caché habilitado: {self.use_cache}")
        print("-" * 60)

        for category in QueryCategory:
            if category in (QueryCategory.TEMPLATES, QueryCategory.DDL):
                continue
            queries = self.list_queries(category)
            print(f"\n📂 {category.value.upper()}: {len(queries)} queries")
            for q in queries:
                print(f"   • {q.split('/')[1]}")

        templates = self.list_templates()
        print(f"\n📄 TEMPLATES: {len(templates)} templates")
        for t in templates:
            print(f"   • {t}")

        print("\n" + "═" * 60)

    # ═══════════════════════════════════════════════════════════════
    # MÉTODOS PRIVADOS
    # ═══════════════════════════════════════════════════════════════

    def _validate_directory_structure(self):
        """Valida que existan los directorios necesarios."""
        for category in QueryCategory:
            cat_dir = self.base_dir / category.value
            if not cat_dir.exists():
                logger.debug(f"📁 Directorio no existe: {cat_dir}")

    def _load_query_file(
        self,
        category: QueryCategory,
        name: str
    ) -> QueryResult:
        """Carga un archivo SQL y extrae metadatos."""
        file_path = self.base_dir / category.value / f"{name}{self.SQL_EXTENSION}"

        if not file_path.exists():
            raise QueryNotFoundError(
                f"Query no encontrada: {category.value}/{name}"
            )

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extraer metadatos del encabezado
            metadata = self._extract_metadata(content, category, name, str(file_path))

            # Validar SQL
            is_valid, errors = self.validate_query(content)

            return QueryResult(
                sql=content,
                metadata=metadata,
                is_valid=is_valid,
                validation_errors=errors
            )

        except Exception as e:
            raise QueryLoaderError(f"Error cargando {file_path}: {e}")

    def _extract_metadata(
        self,
        content: str,
        category: QueryCategory,
        name: str,
        file_path: str
    ) -> QueryMetadata:
        """Extrae metadatos del encabezado de la query."""
        metadata = QueryMetadata(
            nombre=name,
            categoria=category,
            archivo=file_path
        )

        # Patrones para extraer metadatos del comentario
        patterns = {
            'descripcion': r'--\s*NOMBRE:\s*(.+)',
            'frecuencia': r'--\s*FRECUENCIA:\s*(.+)',
            'autor': r'--\s*AUTOR:\s*(.+)',
            'fecha': r'--\s*FECHA:\s*(.+)',
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                setattr(metadata, key, match.group(1).strip())

        # Extraer tablas involucradas
        tables_match = re.search(
            r'--\s*TABLAS INVOLUCRADAS:\s*\n((?:--\s*-\s*.+\n)+)',
            content,
            re.IGNORECASE
        )
        if tables_match:
            tables = re.findall(r'--\s*-\s*(\w+)', tables_match.group(1))
            metadata.tablas_involucradas = tables

        # Extraer parámetros (placeholders {{param}})
        params = re.findall(r'\{\{(\w+)\}\}', content)
        metadata.parametros = list(set(params))

        # Detectar tipo de query
        sql_clean = self._strip_comments(content).strip().upper()
        for qt in QueryType:
            if sql_clean.startswith(qt.value):
                metadata.query_type = qt
                break

        return metadata

    def _replace_params(self, sql: str, params: Dict[str, Any]) -> str:
        """Reemplaza parámetros en el SQL."""
        result = sql

        for key, value in params.items():
            placeholder = f"{{{{{key}}}}}"

            # Formatear valor según tipo
            if value is None:
                formatted_value = "NULL"
            elif isinstance(value, str):
                # Escapar comillas simples
                escaped = value.replace("'", "''")
                formatted_value = f"'{escaped}'"
            elif isinstance(value, bool):
                formatted_value = "1" if value else "0"
            elif isinstance(value, (int, float)):
                formatted_value = str(value)
            elif isinstance(value, datetime):
                formatted_value = f"'{value.strftime('%Y-%m-%d %H:%M:%S')}'"
            elif isinstance(value, list):
                # Lista para IN clause
                items = []
                for item in value:
                    if isinstance(item, str):
                        items.append(f"'{item.replace(chr(39), chr(39)+chr(39))}'")
                    else:
                        items.append(str(item))
                formatted_value = f"({', '.join(items)})"
            else:
                formatted_value = str(value)

            result = result.replace(placeholder, formatted_value)

        return result

    def _replace_with_placeholders(
        self,
        sql: str,
        params: Dict[str, Any]
    ) -> Tuple[str, Tuple]:
        """
        Reemplaza parámetros con placeholders ? para prepared statements.
        """
        result = sql
        values = []

        # Encontrar todos los placeholders en orden
        placeholders = re.findall(r'\{\{(\w+)\}\}', sql)

        for placeholder in placeholders:
            if placeholder in params:
                result = result.replace(f"{{{{{placeholder}}}}}", "?", 1)
                values.append(params[placeholder])

        return result, tuple(values)

    def _strip_comments(self, sql: str) -> str:
        """Elimina comentarios del SQL."""
        # Eliminar comentarios de línea
        result = re.sub(r'--.*$', '', sql, flags=re.MULTILINE)

        # Eliminar comentarios de bloque
        result = re.sub(r'/\*.*?\*/', '', result, flags=re.DOTALL)

        # Eliminar líneas vacías múltiples
        result = re.sub(r'\n\s*\n', '\n', result)

        return result.strip()


# ═══════════════════════════════════════════════════════════════
# FUNCIONES DE CONVENIENCIA
# ═══════════════════════════════════════════════════════════════

# Instancia global del loader
_default_loader: Optional[QueryLoader] = None


def get_default_loader() -> QueryLoader:
    """
    Obtiene la instancia global del QueryLoader.

    Returns:
        QueryLoader: Instancia del loader
    """
    global _default_loader
    if _default_loader is None:
        _default_loader = QueryLoader()
    return _default_loader


def load_query(category: str, name: str) -> str:
    """
    Carga una query usando el loader por defecto.

    Args:
        category: Categoría (obligatorias, preventivas, bajo_demanda)
        name: Nombre de la query

    Returns:
        str: SQL de la query
    """
    loader = get_default_loader()
    cat = QueryCategory(category)
    return loader.load_query(cat, name)


def load_query_with_params(
    category: str,
    name: str,
    params: Dict[str, Any]
) -> str:
    """
    Carga una query con parámetros usando el loader por defecto.

    Args:
        category: Categoría
        name: Nombre de la query
        params: Parámetros a sustituir

    Returns:
        str: SQL con parámetros sustituidos
    """
    loader = get_default_loader()
    cat = QueryCategory(category)
    sql, _ = loader.load_query_with_params(cat, name, params)
    return sql


# ═══════════════════════════════════════════════════════════════
# EJECUCIÓN DIRECTA PARA PRUEBAS
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Configurar logging para pruebas
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("\n" + "=" * 60)
    print("🔍 PRUEBA DE QUERYLOADER")
    print("=" * 60)

    # Crear loader
    loader = QueryLoader()

    # Mostrar resumen
    loader.print_summary()

    # Validar todas las queries
    print("\n📋 Validando todas las queries...")
    results = loader.validate_all_queries()

    valid_count = sum(1 for v, _ in results.values() if v)
    invalid_count = len(results) - valid_count

    print(f"\n✅ Queries válidas: {valid_count}")
    print(f"❌ Queries inválidas: {invalid_count}")

    if invalid_count > 0:
        print("\nQueries con errores:")
        for path, (is_valid, errors) in results.items():
            if not is_valid:
                print(f"  • {path}: {errors}")

    print("\n" + "=" * 60)
