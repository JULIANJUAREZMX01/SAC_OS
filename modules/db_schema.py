"""
===============================================================
GESTOR DE SCHEMA PARA DB2
Sistema de Automatizacion de Consultas - CEDIS Cancun 427
===============================================================

Este modulo proporciona gestion del schema de base de datos:
- Verificacion de schema y tablas
- Informacion de tablas y columnas
- Listado de objetos de base de datos
- Validacion de estructura esperada

Uso:
    from modules.db_schema import SchemaManager

    # Crear manager
    schema_mgr = SchemaManager()

    # Verificar schema
    errores = schema_mgr.verify_schema()

    # Obtener info de tabla
    info = schema_mgr.get_table_info('ORDERS')

Desarrollado por: Julian Alexander Juarez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logistica Cancun
===============================================================
"""

import logging
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
from datetime import datetime
import pandas as pd

# Importar conexion
from .db_connection import DB2Connection, DB2QueryError

# Importar configuracion
try:
    from config import DB_CONFIG
except ImportError:
    DB_CONFIG = {}

# ===============================================================
# CONFIGURACION DE LOGGING
# ===============================================================

logger = logging.getLogger(__name__)


# ===============================================================
# DATA CLASSES
# ===============================================================

@dataclass
class ColumnInfo:
    """Informacion de una columna"""
    name: str
    data_type: str
    length: Optional[int] = None
    scale: Optional[int] = None
    nullable: bool = True
    default: Optional[str] = None
    position: int = 0


@dataclass
class TableInfo:
    """Informacion de una tabla"""
    name: str
    schema: str
    type: str  # TABLE, VIEW, ALIAS, etc.
    columns: List[ColumnInfo] = field(default_factory=list)
    row_count: Optional[int] = None
    created: Optional[datetime] = None
    last_modified: Optional[datetime] = None


@dataclass
class IndexInfo:
    """Informacion de un indice"""
    name: str
    table_name: str
    columns: List[str] = field(default_factory=list)
    unique: bool = False
    clustered: bool = False


# ===============================================================
# EXCEPCIONES
# ===============================================================

class SchemaError(Exception):
    """Error de schema"""
    pass


class TableNotFoundError(SchemaError):
    """Tabla no encontrada"""
    pass


# ===============================================================
# DEFINICION DE SCHEMA ESPERADO (Manhattan WMS)
# ===============================================================

# Tablas criticas de Manhattan WMS para el sistema SAC
EXPECTED_TABLES = {
    'ORDERDETAIL': {
        'description': 'Detalle de ordenes de compra',
        'critical_columns': ['ORDERKEY', 'ORDERLINENUMBER', 'SKU', 'OPENQTY', 'SHIPPEDQTY']
    },
    'ORDERS': {
        'description': 'Cabecera de ordenes',
        'critical_columns': ['ORDERKEY', 'STORERKEY', 'STATUS', 'ORDERDATE']
    },
    'SKU': {
        'description': 'Maestro de SKUs',
        'critical_columns': ['STORERKEY', 'SKU', 'DESCR', 'INNERPACK']
    },
    'RECEIPT': {
        'description': 'Recibo de mercancia',
        'critical_columns': ['RECEIPTKEY', 'EXTERNRECEIPTKEY', 'STATUS']
    },
    'RECEIPTDETAIL': {
        'description': 'Detalle de recibo',
        'critical_columns': ['RECEIPTKEY', 'RECEIPTLINENUMBER', 'SKU', 'QTYRECEIVED']
    },
    'ASN': {
        'description': 'Advanced Shipping Notice',
        'critical_columns': ['ASNKEY', 'EXTERNRECEIPTKEY', 'STATUS']
    },
    'ASNDETAIL': {
        'description': 'Detalle de ASN',
        'critical_columns': ['ASNKEY', 'ASNLINENUMBER', 'SKU', 'EXPECTEDQTY']
    },
    'LPN': {
        'description': 'License Plate Numbers',
        'critical_columns': ['LPNKEY', 'LPN', 'STATUS']
    },
    'LOC': {
        'description': 'Ubicaciones',
        'critical_columns': ['LOC', 'LOCATIONTYPE', 'STATUS']
    },
    'STORER': {
        'description': 'Almacenes/Tiendas',
        'critical_columns': ['STORERKEY', 'COMPANY', 'TYPE']
    },
}


# ===============================================================
# CLASE PRINCIPAL
# ===============================================================

class SchemaManager:
    """
    Gestor de schema para IBM DB2 (Manhattan WMS)

    Proporciona funcionalidades para:
    - Verificar existencia y estructura de tablas
    - Obtener informacion de columnas e indices
    - Validar schema esperado
    - Listar objetos de base de datos

    Ejemplo de uso:
        >>> schema_mgr = SchemaManager()
        >>> errors = schema_mgr.verify_schema()
        >>> if errors:
        ...     print("Errores encontrados:", errors)
        >>> info = schema_mgr.get_table_info('ORDERS')
        >>> print(info)
    """

    DEFAULT_SCHEMA = "WMWHSE1"

    def __init__(
        self,
        connection: Optional[DB2Connection] = None,
        schema: Optional[str] = None,
        config: Optional[Dict] = None
    ):
        """
        Inicializa el gestor de schema

        Args:
            connection: Conexion DB2 a usar (o None para crear una)
            schema: Nombre del schema (default: WMWHSE1)
            config: Configuracion de conexion
        """
        self._connection = connection
        self._own_connection = connection is None
        self.schema = schema or self.DEFAULT_SCHEMA
        self.config = config or DB_CONFIG
        self._table_cache: Dict[str, TableInfo] = {}

        logger.info(f"SchemaManager inicializado para schema: {self.schema}")

    def _get_connection(self) -> DB2Connection:
        """Obtiene o crea una conexion"""
        if self._connection and self._connection.is_connected():
            return self._connection

        if self._own_connection:
            self._connection = DB2Connection(config=self.config, auto_connect=True)

        return self._connection

    def _ensure_connected(self) -> DB2Connection:
        """Asegura que hay una conexion activa"""
        conn = self._get_connection()
        if not conn or not conn.is_connected():
            conn = DB2Connection(config=self.config, auto_connect=True)
            self._connection = conn
        return conn

    # ===============================================================
    # VERIFICACION DE SCHEMA
    # ===============================================================

    def verify_schema(self, expected_tables: Optional[Dict] = None) -> List[str]:
        """
        Verifica el schema contra la estructura esperada

        Args:
            expected_tables: Dict de tablas esperadas (usa EXPECTED_TABLES por defecto)

        Returns:
            Lista de errores encontrados (vacia si todo OK)
        """
        expected = expected_tables or EXPECTED_TABLES
        errors = []

        logger.info(f"Verificando schema {self.schema}...")

        try:
            conn = self._ensure_connected()

            # Verificar cada tabla esperada
            for table_name, table_spec in expected.items():
                logger.debug(f"  Verificando tabla {table_name}...")

                # Verificar existencia
                if not self.table_exists(table_name):
                    errors.append(f"Tabla {self.schema}.{table_name} no existe")
                    continue

                # Verificar columnas criticas
                table_info = self.get_table_info(table_name)
                existing_columns = {col.name.upper() for col in table_info.columns}

                for col in table_spec.get('critical_columns', []):
                    if col.upper() not in existing_columns:
                        errors.append(
                            f"Columna {col} no existe en {self.schema}.{table_name}"
                        )

            # Resumen
            if errors:
                logger.warning(f"Verificacion completada con {len(errors)} errores")
            else:
                logger.info("Verificacion completada sin errores")

        except Exception as e:
            errors.append(f"Error durante verificacion: {str(e)}")
            logger.error(f"Error verificando schema: {e}")

        return errors

    def table_exists(self, table_name: str) -> bool:
        """
        Verifica si una tabla existe

        Args:
            table_name: Nombre de la tabla

        Returns:
            True si la tabla existe
        """
        try:
            conn = self._ensure_connected()

            query = """
                SELECT COUNT(*)
                FROM SYSCAT.TABLES
                WHERE TABSCHEMA = ?
                AND TABNAME = ?
            """
            df = conn.execute_query(query, (self.schema.upper(), table_name.upper()))
            return df.iloc[0, 0] > 0

        except Exception as e:
            logger.error(f"Error verificando existencia de tabla {table_name}: {e}")
            return False

    # ===============================================================
    # INFORMACION DE TABLAS
    # ===============================================================

    def get_table_info(self, table_name: str, use_cache: bool = True) -> TableInfo:
        """
        Obtiene informacion detallada de una tabla

        Args:
            table_name: Nombre de la tabla
            use_cache: Usar cache si esta disponible

        Returns:
            TableInfo con la informacion

        Raises:
            TableNotFoundError: Si la tabla no existe
        """
        cache_key = f"{self.schema}.{table_name}".upper()

        # Verificar cache
        if use_cache and cache_key in self._table_cache:
            return self._table_cache[cache_key]

        try:
            conn = self._ensure_connected()

            # Obtener informacion basica de la tabla
            table_query = """
                SELECT TABNAME, TABSCHEMA, TYPE, CREATE_TIME, ALTER_TIME, CARD
                FROM SYSCAT.TABLES
                WHERE TABSCHEMA = ?
                AND TABNAME = ?
            """
            df_table = conn.execute_query(
                table_query,
                (self.schema.upper(), table_name.upper())
            )

            if df_table.empty:
                raise TableNotFoundError(f"Tabla {self.schema}.{table_name} no encontrada")

            row = df_table.iloc[0]

            # Obtener columnas
            columns = self._get_columns(table_name)

            # Crear TableInfo
            info = TableInfo(
                name=row['TABNAME'] if 'TABNAME' in df_table.columns else table_name,
                schema=row['TABSCHEMA'] if 'TABSCHEMA' in df_table.columns else self.schema,
                type=row['TYPE'] if 'TYPE' in df_table.columns else 'T',
                columns=columns,
                row_count=int(row['CARD']) if 'CARD' in df_table.columns and pd.notna(row['CARD']) else None,
                created=row['CREATE_TIME'] if 'CREATE_TIME' in df_table.columns else None,
                last_modified=row['ALTER_TIME'] if 'ALTER_TIME' in df_table.columns else None
            )

            # Guardar en cache
            self._table_cache[cache_key] = info

            return info

        except TableNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error obteniendo info de tabla {table_name}: {e}")
            raise SchemaError(f"Error obteniendo info de tabla: {e}")

    def _get_columns(self, table_name: str) -> List[ColumnInfo]:
        """Obtiene las columnas de una tabla"""
        conn = self._ensure_connected()

        query = """
            SELECT COLNAME, TYPENAME, LENGTH, SCALE, NULLS, DEFAULT, COLNO
            FROM SYSCAT.COLUMNS
            WHERE TABSCHEMA = ?
            AND TABNAME = ?
            ORDER BY COLNO
        """
        df = conn.execute_query(query, (self.schema.upper(), table_name.upper()))

        columns = []
        for _, row in df.iterrows():
            columns.append(ColumnInfo(
                name=row['COLNAME'],
                data_type=row['TYPENAME'],
                length=int(row['LENGTH']) if pd.notna(row.get('LENGTH')) else None,
                scale=int(row['SCALE']) if pd.notna(row.get('SCALE')) else None,
                nullable=row.get('NULLS', 'Y') == 'Y',
                default=row.get('DEFAULT'),
                position=int(row['COLNO']) if pd.notna(row.get('COLNO')) else 0
            ))

        return columns

    def get_column_info(self, table_name: str, column_name: str) -> Optional[ColumnInfo]:
        """
        Obtiene informacion de una columna especifica

        Args:
            table_name: Nombre de la tabla
            column_name: Nombre de la columna

        Returns:
            ColumnInfo o None si no existe
        """
        table_info = self.get_table_info(table_name)

        for col in table_info.columns:
            if col.name.upper() == column_name.upper():
                return col

        return None

    def describe_table(self, table_name: str) -> pd.DataFrame:
        """
        Describe una tabla (similar a DESCRIBE en SQL)

        Args:
            table_name: Nombre de la tabla

        Returns:
            DataFrame con la descripcion de columnas
        """
        table_info = self.get_table_info(table_name)

        data = []
        for col in table_info.columns:
            data.append({
                'Columna': col.name,
                'Tipo': col.data_type,
                'Longitud': col.length,
                'Escala': col.scale,
                'Nullable': 'Si' if col.nullable else 'No',
                'Default': col.default
            })

        return pd.DataFrame(data)

    # ===============================================================
    # LISTADO DE OBJETOS
    # ===============================================================

    def list_tables(self, pattern: Optional[str] = None) -> List[str]:
        """
        Lista las tablas del schema

        Args:
            pattern: Patron LIKE para filtrar (opcional)

        Returns:
            Lista de nombres de tablas
        """
        try:
            conn = self._ensure_connected()

            if pattern:
                query = """
                    SELECT TABNAME
                    FROM SYSCAT.TABLES
                    WHERE TABSCHEMA = ?
                    AND TYPE = 'T'
                    AND TABNAME LIKE ?
                    ORDER BY TABNAME
                """
                df = conn.execute_query(query, (self.schema.upper(), pattern.upper()))
            else:
                query = """
                    SELECT TABNAME
                    FROM SYSCAT.TABLES
                    WHERE TABSCHEMA = ?
                    AND TYPE = 'T'
                    ORDER BY TABNAME
                """
                df = conn.execute_query(query, (self.schema.upper(),))

            return df['TABNAME'].tolist() if not df.empty else []

        except Exception as e:
            logger.error(f"Error listando tablas: {e}")
            return []

    def list_views(self, pattern: Optional[str] = None) -> List[str]:
        """
        Lista las vistas del schema

        Args:
            pattern: Patron LIKE para filtrar (opcional)

        Returns:
            Lista de nombres de vistas
        """
        try:
            conn = self._ensure_connected()

            if pattern:
                query = """
                    SELECT VIEWNAME
                    FROM SYSCAT.VIEWS
                    WHERE VIEWSCHEMA = ?
                    AND VIEWNAME LIKE ?
                    ORDER BY VIEWNAME
                """
                df = conn.execute_query(query, (self.schema.upper(), pattern.upper()))
            else:
                query = """
                    SELECT VIEWNAME
                    FROM SYSCAT.VIEWS
                    WHERE VIEWSCHEMA = ?
                    ORDER BY VIEWNAME
                """
                df = conn.execute_query(query, (self.schema.upper(),))

            return df['VIEWNAME'].tolist() if not df.empty else []

        except Exception as e:
            logger.error(f"Error listando vistas: {e}")
            return []

    def list_indexes(self, table_name: Optional[str] = None) -> List[IndexInfo]:
        """
        Lista los indices del schema o de una tabla especifica

        Args:
            table_name: Nombre de tabla para filtrar (opcional)

        Returns:
            Lista de IndexInfo
        """
        try:
            conn = self._ensure_connected()

            if table_name:
                query = """
                    SELECT INDNAME, TABNAME, UNIQUERULE, INDEXTYPE,
                           COLNAMES
                    FROM SYSCAT.INDEXES
                    WHERE TABSCHEMA = ?
                    AND TABNAME = ?
                    ORDER BY INDNAME
                """
                df = conn.execute_query(query, (self.schema.upper(), table_name.upper()))
            else:
                query = """
                    SELECT INDNAME, TABNAME, UNIQUERULE, INDEXTYPE,
                           COLNAMES
                    FROM SYSCAT.INDEXES
                    WHERE TABSCHEMA = ?
                    ORDER BY TABNAME, INDNAME
                """
                df = conn.execute_query(query, (self.schema.upper(),))

            indexes = []
            for _, row in df.iterrows():
                # Parsear columnas (formato: +COL1+COL2 o -COL1-COL2)
                colnames = row.get('COLNAMES', '')
                if colnames:
                    columns = [c.strip('+-') for c in colnames.split('+') if c.strip('+-')]
                else:
                    columns = []

                indexes.append(IndexInfo(
                    name=row['INDNAME'],
                    table_name=row['TABNAME'],
                    columns=columns,
                    unique=row.get('UNIQUERULE', 'D') in ('U', 'P'),
                    clustered=row.get('INDEXTYPE', '') == 'CLUS'
                ))

            return indexes

        except Exception as e:
            logger.error(f"Error listando indices: {e}")
            return []

    # ===============================================================
    # UTILIDADES
    # ===============================================================

    def get_row_count(self, table_name: str, where: Optional[str] = None) -> int:
        """
        Obtiene el conteo de filas de una tabla

        Args:
            table_name: Nombre de la tabla
            where: Condicion WHERE opcional

        Returns:
            Numero de filas
        """
        try:
            conn = self._ensure_connected()

            if where:
                query = f"SELECT COUNT(*) FROM {self.schema}.{table_name} WHERE {where}"
            else:
                query = f"SELECT COUNT(*) FROM {self.schema}.{table_name}"

            df = conn.execute_query(query)
            return int(df.iloc[0, 0])

        except Exception as e:
            logger.error(f"Error obteniendo conteo de {table_name}: {e}")
            return -1

    def clear_cache(self) -> None:
        """Limpia el cache de tablas"""
        self._table_cache.clear()
        logger.debug("Cache de tablas limpiado")

    def print_schema_summary(self) -> None:
        """Imprime un resumen del schema"""
        print("\n" + "="*55)
        print(f" SCHEMA SUMMARY: {self.schema}")
        print("="*55)

        tables = self.list_tables()
        views = self.list_views()

        print(f"\n   Tablas: {len(tables)}")
        print(f"   Vistas: {len(views)}")

        print("\n   Tablas principales:")
        for table in tables[:10]:
            try:
                info = self.get_table_info(table)
                print(f"      {table}: {len(info.columns)} columnas, ~{info.row_count or '?'} filas")
            except Exception:
                print(f"      {table}: (info no disponible)")

        if len(tables) > 10:
            print(f"      ... y {len(tables) - 10} mas")

        print("="*55 + "\n")

    def close(self) -> None:
        """Cierra la conexion si es propia"""
        if self._own_connection and self._connection:
            self._connection.disconnect()
            self._connection = None

    def __enter__(self):
        """Entrada al context manager"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Salida del context manager"""
        self.close()
        return False


# ===============================================================
# EXPORTAR
# ===============================================================

__all__ = [
    # Clase principal
    'SchemaManager',

    # Data classes
    'TableInfo',
    'ColumnInfo',
    'IndexInfo',

    # Excepciones
    'SchemaError',
    'TableNotFoundError',

    # Constantes
    'EXPECTED_TABLES',
]


# ===============================================================
# EJECUTAR AL IMPORTAR
# ===============================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print(" SCHEMA MANAGER - SAC CEDIS 427")
    print("="*60)

    print("\n Este modulo proporciona gestion del schema de DB2.")
    print("\n Uso basico:")
    print("   from modules.db_schema import SchemaManager")
    print("   ")
    print("   schema_mgr = SchemaManager()")
    print("   ")
    print("   # Verificar schema")
    print("   errors = schema_mgr.verify_schema()")
    print("   ")
    print("   # Obtener info de tabla")
    print("   info = schema_mgr.get_table_info('ORDERS')")
    print("   print(info)")
    print("   ")
    print("   # Describir tabla")
    print("   df = schema_mgr.describe_table('ORDERS')")
    print("   print(df)")

    print("\n Tablas esperadas en Manhattan WMS:")
    for table, spec in EXPECTED_TABLES.items():
        print(f"   {table}: {spec['description']}")

    print("\n" + "="*60 + "\n")
