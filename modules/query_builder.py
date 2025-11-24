"""
===============================================================
CONSTRUCTOR DE QUERIES SQL PARA DB2
Sistema de Automatizacion de Consultas - CEDIS Cancun 427
===============================================================

Este modulo proporciona un constructor de queries SQL con:
- Interfaz fluida (method chaining)
- Validacion de parametros
- Escape de valores
- Soporte para DB2/Manhattan WMS
- Prevencion de SQL injection

Uso:
    from modules.query_builder import QueryBuilder

    # Construir query
    query = (
        QueryBuilder()
        .select('SKU', 'DESCR', 'QTY')
        .from_table('WMWHSE1.SKU')
        .where('STORERKEY = ?', 'C22')
        .order_by('SKU')
        .limit(100)
        .build()
    )

Desarrollado por: Julian Alexander Juarez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logistica Cancun
===============================================================
"""

import logging
import re
from typing import Optional, Dict, List, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd

# Importar conexion si esta disponible
try:
    from .db_connection import DB2Connection
except ImportError:
    DB2Connection = None

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
# ENUMS Y DATA CLASSES
# ===============================================================

class JoinType(Enum):
    """Tipos de JOIN soportados"""
    INNER = "INNER JOIN"
    LEFT = "LEFT JOIN"
    RIGHT = "RIGHT JOIN"
    FULL = "FULL OUTER JOIN"
    CROSS = "CROSS JOIN"


class OrderDirection(Enum):
    """Direcciones de ordenamiento"""
    ASC = "ASC"
    DESC = "DESC"


@dataclass
class QueryPart:
    """Parte de una query"""
    clause: str
    params: List[Any] = field(default_factory=list)


# ===============================================================
# EXCEPCIONES
# ===============================================================

class QueryBuilderError(Exception):
    """Error en el constructor de queries"""
    pass


class QueryValidationError(QueryBuilderError):
    """Error de validacion de query"""
    pass


# ===============================================================
# CLASE PRINCIPAL
# ===============================================================

class QueryBuilder:
    """
    Constructor de queries SQL con interfaz fluida

    Soporta operaciones SELECT, INSERT, UPDATE, DELETE
    con validacion y parametros seguros.

    Ejemplo de uso:
        >>> query = (
        ...     QueryBuilder()
        ...     .select('SKU', 'DESCR')
        ...     .from_table('WMWHSE1.SKU')
        ...     .where('STORERKEY = ?', 'C22')
        ...     .build()
        ... )
        >>> print(query)
        SELECT SKU, DESCR FROM WMWHSE1.SKU WHERE STORERKEY = ?
    """

    # Schema por defecto (Manhattan WMS)
    DEFAULT_SCHEMA = "WMWHSE1"

    def __init__(self, schema: Optional[str] = None):
        """
        Inicializa el constructor de queries

        Args:
            schema: Schema por defecto para las tablas
        """
        self.schema = schema or self.DEFAULT_SCHEMA
        self._reset()

    def _reset(self) -> None:
        """Reinicia el estado del builder"""
        self._select_columns: List[str] = []
        self._from_table: Optional[str] = None
        self._joins: List[QueryPart] = []
        self._where_conditions: List[QueryPart] = []
        self._group_by_columns: List[str] = []
        self._having_conditions: List[QueryPart] = []
        self._order_by_columns: List[Tuple[str, OrderDirection]] = []
        self._limit_value: Optional[int] = None
        self._offset_value: Optional[int] = None
        self._params: List[Any] = []
        self._distinct: bool = False
        self._for_update: bool = False

        # Para INSERT/UPDATE/DELETE
        self._operation: str = "SELECT"
        self._insert_columns: List[str] = []
        self._insert_values: List[List[Any]] = []
        self._update_sets: Dict[str, Any] = {}
        self._delete_table: Optional[str] = None

    # ===============================================================
    # SELECT
    # ===============================================================

    def select(self, *columns: str) -> 'QueryBuilder':
        """
        Define las columnas a seleccionar

        Args:
            *columns: Nombres de columnas o expresiones

        Returns:
            Self para encadenar

        Example:
            >>> qb.select('SKU', 'DESCR', 'QTY as CANTIDAD')
        """
        self._operation = "SELECT"
        self._select_columns.extend(columns)
        return self

    def select_all(self) -> 'QueryBuilder':
        """
        Selecciona todas las columnas (*)

        Returns:
            Self para encadenar
        """
        return self.select('*')

    def distinct(self) -> 'QueryBuilder':
        """
        Agrega DISTINCT a la consulta

        Returns:
            Self para encadenar
        """
        self._distinct = True
        return self

    def count(self, column: str = '*', alias: str = 'COUNT') -> 'QueryBuilder':
        """
        Agrega COUNT a la consulta

        Args:
            column: Columna a contar
            alias: Alias para el resultado

        Returns:
            Self para encadenar
        """
        return self.select(f"COUNT({column}) AS {alias}")

    def sum(self, column: str, alias: Optional[str] = None) -> 'QueryBuilder':
        """
        Agrega SUM a la consulta

        Args:
            column: Columna a sumar
            alias: Alias para el resultado

        Returns:
            Self para encadenar
        """
        alias = alias or f"SUM_{column}"
        return self.select(f"SUM({column}) AS {alias}")

    def avg(self, column: str, alias: Optional[str] = None) -> 'QueryBuilder':
        """
        Agrega AVG a la consulta

        Args:
            column: Columna para promedio
            alias: Alias para el resultado

        Returns:
            Self para encadenar
        """
        alias = alias or f"AVG_{column}"
        return self.select(f"AVG({column}) AS {alias}")

    # ===============================================================
    # FROM
    # ===============================================================

    def from_table(self, table: str, alias: Optional[str] = None) -> 'QueryBuilder':
        """
        Define la tabla principal

        Args:
            table: Nombre de la tabla (con o sin schema)
            alias: Alias opcional para la tabla

        Returns:
            Self para encadenar
        """
        # Agregar schema si no tiene
        if '.' not in table and self.schema:
            table = f"{self.schema}.{table}"

        if alias:
            self._from_table = f"{table} {alias}"
        else:
            self._from_table = table

        return self

    # ===============================================================
    # JOIN
    # ===============================================================

    def join(
        self,
        table: str,
        on: str,
        join_type: JoinType = JoinType.INNER,
        alias: Optional[str] = None
    ) -> 'QueryBuilder':
        """
        Agrega un JOIN a la consulta

        Args:
            table: Tabla a unir
            on: Condicion del JOIN
            join_type: Tipo de JOIN
            alias: Alias para la tabla

        Returns:
            Self para encadenar

        Example:
            >>> qb.join('DISTRIBUTION', 'D.SKU = S.SKU', JoinType.LEFT, 'D')
        """
        # Agregar schema si no tiene
        if '.' not in table and self.schema:
            table = f"{self.schema}.{table}"

        if alias:
            table = f"{table} {alias}"

        self._joins.append(QueryPart(
            clause=f"{join_type.value} {table} ON {on}"
        ))
        return self

    def inner_join(self, table: str, on: str, alias: Optional[str] = None) -> 'QueryBuilder':
        """INNER JOIN"""
        return self.join(table, on, JoinType.INNER, alias)

    def left_join(self, table: str, on: str, alias: Optional[str] = None) -> 'QueryBuilder':
        """LEFT JOIN"""
        return self.join(table, on, JoinType.LEFT, alias)

    def right_join(self, table: str, on: str, alias: Optional[str] = None) -> 'QueryBuilder':
        """RIGHT JOIN"""
        return self.join(table, on, JoinType.RIGHT, alias)

    # ===============================================================
    # WHERE
    # ===============================================================

    def where(self, condition: str, *params: Any) -> 'QueryBuilder':
        """
        Agrega condicion WHERE (AND)

        Args:
            condition: Condicion SQL (usar ? para parametros)
            *params: Valores de los parametros

        Returns:
            Self para encadenar

        Example:
            >>> qb.where('SKU = ?', 'ABC123')
            >>> qb.where('QTY > ? AND QTY < ?', 10, 100)
        """
        self._where_conditions.append(QueryPart(
            clause=condition,
            params=list(params)
        ))
        return self

    def where_in(self, column: str, values: List[Any]) -> 'QueryBuilder':
        """
        Agrega condicion WHERE IN

        Args:
            column: Nombre de la columna
            values: Lista de valores

        Returns:
            Self para encadenar

        Example:
            >>> qb.where_in('STATUS', ['A', 'B', 'C'])
        """
        if not values:
            # IN vacio = siempre falso
            return self.where('1 = 0')

        placeholders = ', '.join(['?' for _ in values])
        return self.where(f"{column} IN ({placeholders})", *values)

    def where_not_in(self, column: str, values: List[Any]) -> 'QueryBuilder':
        """Agrega condicion WHERE NOT IN"""
        if not values:
            return self

        placeholders = ', '.join(['?' for _ in values])
        return self.where(f"{column} NOT IN ({placeholders})", *values)

    def where_null(self, column: str) -> 'QueryBuilder':
        """Agrega condicion WHERE IS NULL"""
        return self.where(f"{column} IS NULL")

    def where_not_null(self, column: str) -> 'QueryBuilder':
        """Agrega condicion WHERE IS NOT NULL"""
        return self.where(f"{column} IS NOT NULL")

    def where_between(self, column: str, start: Any, end: Any) -> 'QueryBuilder':
        """Agrega condicion WHERE BETWEEN"""
        return self.where(f"{column} BETWEEN ? AND ?", start, end)

    def where_like(self, column: str, pattern: str) -> 'QueryBuilder':
        """Agrega condicion WHERE LIKE"""
        return self.where(f"{column} LIKE ?", pattern)

    def or_where(self, condition: str, *params: Any) -> 'QueryBuilder':
        """
        Agrega condicion WHERE con OR

        Args:
            condition: Condicion SQL
            *params: Valores de los parametros

        Returns:
            Self para encadenar
        """
        if self._where_conditions:
            # Modificar la ultima condicion para agregar OR
            last = self._where_conditions[-1]
            self._where_conditions[-1] = QueryPart(
                clause=f"({last.clause}) OR ({condition})",
                params=last.params + list(params)
            )
        else:
            self.where(condition, *params)
        return self

    # ===============================================================
    # GROUP BY / HAVING
    # ===============================================================

    def group_by(self, *columns: str) -> 'QueryBuilder':
        """
        Agrega GROUP BY

        Args:
            *columns: Columnas para agrupar

        Returns:
            Self para encadenar
        """
        self._group_by_columns.extend(columns)
        return self

    def having(self, condition: str, *params: Any) -> 'QueryBuilder':
        """
        Agrega condicion HAVING

        Args:
            condition: Condicion SQL
            *params: Valores de los parametros

        Returns:
            Self para encadenar
        """
        self._having_conditions.append(QueryPart(
            clause=condition,
            params=list(params)
        ))
        return self

    # ===============================================================
    # ORDER BY
    # ===============================================================

    def order_by(self, *columns: str, direction: OrderDirection = OrderDirection.ASC) -> 'QueryBuilder':
        """
        Agrega ORDER BY

        Args:
            *columns: Columnas para ordenar
            direction: Direccion de orden (ASC/DESC)

        Returns:
            Self para encadenar
        """
        for col in columns:
            self._order_by_columns.append((col, direction))
        return self

    def order_by_asc(self, *columns: str) -> 'QueryBuilder':
        """ORDER BY ASC"""
        return self.order_by(*columns, direction=OrderDirection.ASC)

    def order_by_desc(self, *columns: str) -> 'QueryBuilder':
        """ORDER BY DESC"""
        return self.order_by(*columns, direction=OrderDirection.DESC)

    # ===============================================================
    # LIMIT / OFFSET (DB2 syntax)
    # ===============================================================

    def limit(self, value: int) -> 'QueryBuilder':
        """
        Limita el numero de resultados (FETCH FIRST en DB2)

        Args:
            value: Numero maximo de filas

        Returns:
            Self para encadenar
        """
        if value < 0:
            raise QueryValidationError("LIMIT debe ser >= 0")
        self._limit_value = value
        return self

    def offset(self, value: int) -> 'QueryBuilder':
        """
        Define el offset de resultados (DB2 syntax)

        Args:
            value: Numero de filas a saltar

        Returns:
            Self para encadenar
        """
        if value < 0:
            raise QueryValidationError("OFFSET debe ser >= 0")
        self._offset_value = value
        return self

    def for_update(self) -> 'QueryBuilder':
        """
        Agrega FOR UPDATE al SELECT (bloqueo de filas)

        Returns:
            Self para encadenar
        """
        self._for_update = True
        return self

    # ===============================================================
    # INSERT
    # ===============================================================

    def insert_into(self, table: str, *columns: str) -> 'QueryBuilder':
        """
        Inicia un INSERT INTO

        Args:
            table: Nombre de la tabla
            *columns: Columnas a insertar

        Returns:
            Self para encadenar
        """
        self._operation = "INSERT"

        # Agregar schema si no tiene
        if '.' not in table and self.schema:
            table = f"{self.schema}.{table}"

        self._from_table = table
        self._insert_columns = list(columns)
        return self

    def values(self, *values: Any) -> 'QueryBuilder':
        """
        Define los valores a insertar

        Args:
            *values: Valores para una fila

        Returns:
            Self para encadenar
        """
        self._insert_values.append(list(values))
        return self

    # ===============================================================
    # UPDATE
    # ===============================================================

    def update(self, table: str) -> 'QueryBuilder':
        """
        Inicia un UPDATE

        Args:
            table: Nombre de la tabla

        Returns:
            Self para encadenar
        """
        self._operation = "UPDATE"

        # Agregar schema si no tiene
        if '.' not in table and self.schema:
            table = f"{self.schema}.{table}"

        self._from_table = table
        return self

    def set(self, column: str, value: Any) -> 'QueryBuilder':
        """
        Define un valor a actualizar

        Args:
            column: Nombre de la columna
            value: Nuevo valor

        Returns:
            Self para encadenar
        """
        self._update_sets[column] = value
        return self

    def set_many(self, values: Dict[str, Any]) -> 'QueryBuilder':
        """
        Define multiples valores a actualizar

        Args:
            values: Diccionario columna -> valor

        Returns:
            Self para encadenar
        """
        self._update_sets.update(values)
        return self

    # ===============================================================
    # DELETE
    # ===============================================================

    def delete_from(self, table: str) -> 'QueryBuilder':
        """
        Inicia un DELETE FROM

        Args:
            table: Nombre de la tabla

        Returns:
            Self para encadenar
        """
        self._operation = "DELETE"

        # Agregar schema si no tiene
        if '.' not in table and self.schema:
            table = f"{self.schema}.{table}"

        self._from_table = table
        return self

    # ===============================================================
    # BUILD
    # ===============================================================

    def build(self) -> str:
        """
        Construye la query SQL

        Returns:
            String con la query SQL

        Raises:
            QueryValidationError: Si la query es invalida
        """
        if self._operation == "SELECT":
            return self._build_select()
        elif self._operation == "INSERT":
            return self._build_insert()
        elif self._operation == "UPDATE":
            return self._build_update()
        elif self._operation == "DELETE":
            return self._build_delete()
        else:
            raise QueryValidationError(f"Operacion no soportada: {self._operation}")

    def _build_select(self) -> str:
        """Construye query SELECT"""
        if not self._select_columns:
            raise QueryValidationError("SELECT requiere al menos una columna")

        if not self._from_table:
            raise QueryValidationError("SELECT requiere FROM")

        parts = []

        # SELECT
        distinct = "DISTINCT " if self._distinct else ""
        columns = ", ".join(self._select_columns)
        parts.append(f"SELECT {distinct}{columns}")

        # FROM
        parts.append(f"FROM {self._from_table}")

        # JOINs
        for join in self._joins:
            parts.append(join.clause)

        # WHERE
        if self._where_conditions:
            conditions = " AND ".join([c.clause for c in self._where_conditions])
            parts.append(f"WHERE {conditions}")
            for c in self._where_conditions:
                self._params.extend(c.params)

        # GROUP BY
        if self._group_by_columns:
            columns = ", ".join(self._group_by_columns)
            parts.append(f"GROUP BY {columns}")

        # HAVING
        if self._having_conditions:
            conditions = " AND ".join([c.clause for c in self._having_conditions])
            parts.append(f"HAVING {conditions}")
            for c in self._having_conditions:
                self._params.extend(c.params)

        # ORDER BY
        if self._order_by_columns:
            orders = [f"{col} {dir.value}" for col, dir in self._order_by_columns]
            parts.append(f"ORDER BY {', '.join(orders)}")

        # OFFSET (DB2 syntax)
        if self._offset_value:
            parts.append(f"OFFSET {self._offset_value} ROWS")

        # LIMIT (FETCH FIRST en DB2)
        if self._limit_value is not None:
            parts.append(f"FETCH FIRST {self._limit_value} ROWS ONLY")

        # FOR UPDATE
        if self._for_update:
            parts.append("FOR UPDATE")

        return " ".join(parts)

    def _build_insert(self) -> str:
        """Construye query INSERT"""
        if not self._from_table:
            raise QueryValidationError("INSERT requiere tabla")

        if not self._insert_columns:
            raise QueryValidationError("INSERT requiere columnas")

        if not self._insert_values:
            raise QueryValidationError("INSERT requiere valores")

        columns = ", ".join(self._insert_columns)

        values_list = []
        for row in self._insert_values:
            placeholders = ", ".join(["?" for _ in row])
            values_list.append(f"({placeholders})")
            self._params.extend(row)

        values = ", ".join(values_list)

        return f"INSERT INTO {self._from_table} ({columns}) VALUES {values}"

    def _build_update(self) -> str:
        """Construye query UPDATE"""
        if not self._from_table:
            raise QueryValidationError("UPDATE requiere tabla")

        if not self._update_sets:
            raise QueryValidationError("UPDATE requiere SET")

        sets = []
        for col, val in self._update_sets.items():
            sets.append(f"{col} = ?")
            self._params.append(val)

        parts = [f"UPDATE {self._from_table}", f"SET {', '.join(sets)}"]

        # WHERE
        if self._where_conditions:
            conditions = " AND ".join([c.clause for c in self._where_conditions])
            parts.append(f"WHERE {conditions}")
            for c in self._where_conditions:
                self._params.extend(c.params)

        return " ".join(parts)

    def _build_delete(self) -> str:
        """Construye query DELETE"""
        if not self._from_table:
            raise QueryValidationError("DELETE requiere tabla")

        parts = [f"DELETE FROM {self._from_table}"]

        # WHERE
        if self._where_conditions:
            conditions = " AND ".join([c.clause for c in self._where_conditions])
            parts.append(f"WHERE {conditions}")
            for c in self._where_conditions:
                self._params.extend(c.params)

        return " ".join(parts)

    def get_params(self) -> Tuple[Any, ...]:
        """
        Obtiene los parametros de la query

        Returns:
            Tupla con los parametros
        """
        # Construir para recolectar parametros si no se ha hecho
        if not self._params:
            self.build()
        return tuple(self._params)

    def get_sql_with_params(self) -> Tuple[str, Tuple[Any, ...]]:
        """
        Obtiene la query y sus parametros

        Returns:
            Tupla (sql, params)
        """
        sql = self.build()
        params = self.get_params()
        return sql, params

    # ===============================================================
    # EXECUTE
    # ===============================================================

    def execute(self, connection: Optional['DB2Connection'] = None) -> pd.DataFrame:
        """
        Ejecuta la query y retorna un DataFrame

        Args:
            connection: Conexion DB2 a usar (o None para crear una)

        Returns:
            DataFrame con los resultados
        """
        sql, params = self.get_sql_with_params()

        if connection:
            return connection.execute_query(sql, params if params else None)
        else:
            if DB2Connection is None:
                raise QueryBuilderError("DB2Connection no disponible")

            with DB2Connection() as conn:
                return conn.execute_query(sql, params if params else None)

    # ===============================================================
    # VALIDACION
    # ===============================================================

    def validate(self) -> Tuple[bool, Optional[str]]:
        """
        Valida la query sin ejecutarla

        Returns:
            Tupla (es_valida, mensaje_error)
        """
        try:
            self.build()
            return True, None
        except QueryValidationError as e:
            return False, str(e)

    # ===============================================================
    # UTILIDADES
    # ===============================================================

    def to_string(self) -> str:
        """Alias para build()"""
        return self.build()

    def __str__(self) -> str:
        """String representation"""
        try:
            return self.build()
        except (ValueError, AttributeError, KeyError) as e:
            logger.debug(f"QueryBuilder.__str__() build fallback: {e}")
            return f"<QueryBuilder: {self._operation}>"

    def __repr__(self) -> str:
        return f"QueryBuilder(operation={self._operation}, table={self._from_table})"

    def clone(self) -> 'QueryBuilder':
        """
        Crea una copia del builder

        Returns:
            Nueva instancia con la misma configuracion
        """
        import copy
        new = QueryBuilder(schema=self.schema)
        new._select_columns = copy.copy(self._select_columns)
        new._from_table = self._from_table
        new._joins = copy.copy(self._joins)
        new._where_conditions = copy.copy(self._where_conditions)
        new._group_by_columns = copy.copy(self._group_by_columns)
        new._having_conditions = copy.copy(self._having_conditions)
        new._order_by_columns = copy.copy(self._order_by_columns)
        new._limit_value = self._limit_value
        new._offset_value = self._offset_value
        new._distinct = self._distinct
        new._operation = self._operation
        return new

    def raw(self, sql: str, *params: Any) -> 'QueryBuilder':
        """
        Establece una query SQL raw

        Args:
            sql: Query SQL completa
            *params: Parametros

        Returns:
            Self para encadenar
        """
        self._raw_sql = sql
        self._params = list(params)
        return self


# ===============================================================
# FUNCIONES DE AYUDA
# ===============================================================

def select(*columns: str) -> QueryBuilder:
    """
    Crea un QueryBuilder con SELECT

    Args:
        *columns: Columnas a seleccionar

    Returns:
        QueryBuilder configurado
    """
    return QueryBuilder().select(*columns)


def insert_into(table: str, *columns: str) -> QueryBuilder:
    """
    Crea un QueryBuilder con INSERT

    Args:
        table: Tabla destino
        *columns: Columnas a insertar

    Returns:
        QueryBuilder configurado
    """
    return QueryBuilder().insert_into(table, *columns)


def update(table: str) -> QueryBuilder:
    """
    Crea un QueryBuilder con UPDATE

    Args:
        table: Tabla a actualizar

    Returns:
        QueryBuilder configurado
    """
    return QueryBuilder().update(table)


def delete_from(table: str) -> QueryBuilder:
    """
    Crea un QueryBuilder con DELETE

    Args:
        table: Tabla a eliminar

    Returns:
        QueryBuilder configurado
    """
    return QueryBuilder().delete_from(table)


# ===============================================================
# EXPORTAR
# ===============================================================

__all__ = [
    # Clase principal
    'QueryBuilder',

    # Enums
    'JoinType',
    'OrderDirection',

    # Excepciones
    'QueryBuilderError',
    'QueryValidationError',

    # Funciones de ayuda
    'select',
    'insert_into',
    'update',
    'delete_from',
]


# ===============================================================
# EJECUTAR AL IMPORTAR
# ===============================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print(" QUERY BUILDER - SAC CEDIS 427")
    print("="*60)

    # Ejemplo SELECT
    print("\n Ejemplo SELECT:")
    query = (
        QueryBuilder()
        .select('SKU', 'DESCR', 'QTY')
        .from_table('SKU')
        .where('STORERKEY = ?', 'C22')
        .where('STATUS = ?', 'A')
        .order_by('SKU')
        .limit(10)
    )
    print(f"   {query.build()}")
    print(f"   Params: {query.get_params()}")

    # Ejemplo JOIN
    print("\n Ejemplo JOIN:")
    query = (
        QueryBuilder()
        .select('O.ORDERKEY', 'O.STATUS', 'D.SKU', 'D.QTY')
        .from_table('ORDERS', 'O')
        .left_join('ORDERDETAIL', 'D.ORDERKEY = O.ORDERKEY', 'D')
        .where('O.STATUS = ?', 'OPEN')
        .order_by_desc('O.ORDERKEY')
    )
    print(f"   {query.build()}")

    # Ejemplo INSERT
    print("\n Ejemplo INSERT:")
    query = (
        QueryBuilder()
        .insert_into('AUDITLOG', 'ACTION', 'USER', 'TIMESTAMP')
        .values('LOGIN', 'ADMJAJA', '2025-01-21')
    )
    print(f"   {query.build()}")
    print(f"   Params: {query.get_params()}")

    # Ejemplo UPDATE
    print("\n Ejemplo UPDATE:")
    query = (
        QueryBuilder()
        .update('SKU')
        .set('STATUS', 'I')
        .set('EDITDATE', '2025-01-21')
        .where('SKU = ?', 'ABC123')
    )
    print(f"   {query.build()}")
    print(f"   Params: {query.get_params()}")

    print("\n" + "="*60 + "\n")
