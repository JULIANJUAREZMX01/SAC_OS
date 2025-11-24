"""
===============================================================
REPOSITORIO BASE PARA DB2
Sistema de Automatizacion de Consultas - CEDIS Cancun 427
===============================================================

Clase base abstracta que implementa operaciones CRUD genericas
para entidades de Manhattan WMS.

Uso:
    class MyRepository(BaseRepository):
        TABLE = 'MY_TABLE'
        PRIMARY_KEY = 'ID'

Desarrollado por: Julian Alexander Juarez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logistica Cancun
===============================================================
"""

import logging
from typing import Optional, Dict, List, Any, Tuple
from abc import ABC, abstractmethod
from datetime import datetime
import pandas as pd

# Importar conexion y query builder
from ..db_connection import DB2Connection, DB2QueryError
from ..query_builder import QueryBuilder

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
# EXCEPCIONES
# ===============================================================

class RepositoryError(Exception):
    """Error generico del repositorio"""
    pass


class EntityNotFoundError(RepositoryError):
    """Entidad no encontrada"""
    pass


class DuplicateEntityError(RepositoryError):
    """Entidad duplicada"""
    pass


# ===============================================================
# CLASE BASE
# ===============================================================

class BaseRepository(ABC):
    """
    Clase base abstracta para repositorios

    Proporciona operaciones CRUD genericas:
    - find_by_id(): Buscar por ID
    - find_all(): Obtener todos los registros
    - find_where(): Buscar con condiciones
    - insert(): Insertar registro
    - update(): Actualizar registro
    - delete(): Eliminar registro

    Las subclases deben definir:
    - TABLE: Nombre de la tabla
    - PRIMARY_KEY: Columna de clave primaria
    - SCHEMA: Schema de la tabla (opcional, default WMWHSE1)
    """

    # Atributos que las subclases deben definir
    TABLE: str = None
    PRIMARY_KEY: str = None
    SCHEMA: str = "WMWHSE1"

    def __init__(
        self,
        connection: Optional[DB2Connection] = None,
        config: Optional[Dict] = None
    ):
        """
        Inicializa el repositorio

        Args:
            connection: Conexion DB2 a usar (o None para crear una)
            config: Configuracion de conexion
        """
        self._connection = connection
        self._own_connection = connection is None
        self.config = config or DB_CONFIG

        # Validar configuracion
        if not self.TABLE:
            raise RepositoryError(
                f"La clase {self.__class__.__name__} debe definir TABLE"
            )

        logger.debug(f"Repositorio {self.__class__.__name__} inicializado para {self.full_table_name}")

    @property
    def full_table_name(self) -> str:
        """Nombre completo de la tabla (schema.table)"""
        return f"{self.SCHEMA}.{self.TABLE}"

    def _get_connection(self) -> DB2Connection:
        """Obtiene o crea una conexion"""
        if self._connection and self._connection.is_connected():
            return self._connection

        if self._own_connection or not self._connection:
            self._connection = DB2Connection(config=self.config, auto_connect=True)

        return self._connection

    def _ensure_connected(self) -> DB2Connection:
        """Asegura que hay una conexion activa"""
        conn = self._get_connection()
        if not conn.is_connected():
            conn.connect()
        return conn

    # ===============================================================
    # OPERACIONES DE LECTURA
    # ===============================================================

    def find_by_id(self, id_value: Any) -> Optional[Dict]:
        """
        Busca un registro por su ID

        Args:
            id_value: Valor del ID a buscar

        Returns:
            Dict con el registro o None si no existe
        """
        if not self.PRIMARY_KEY:
            raise RepositoryError(
                f"La clase {self.__class__.__name__} debe definir PRIMARY_KEY"
            )

        try:
            conn = self._ensure_connected()

            query = (
                QueryBuilder(schema=self.SCHEMA)
                .select('*')
                .from_table(self.TABLE)
                .where(f"{self.PRIMARY_KEY} = ?", id_value)
                .limit(1)
            )

            df = conn.execute_query(query.build(), query.get_params())

            if df.empty:
                return None

            return df.iloc[0].to_dict()

        except Exception as e:
            logger.error(f"Error en find_by_id({id_value}): {e}")
            raise RepositoryError(f"Error buscando por ID: {e}")

    def find_all(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[str] = None
    ) -> List[Dict]:
        """
        Obtiene todos los registros

        Args:
            limit: Numero maximo de registros
            offset: Registros a saltar
            order_by: Columna para ordenar

        Returns:
            Lista de diccionarios con los registros
        """
        try:
            conn = self._ensure_connected()

            query = (
                QueryBuilder(schema=self.SCHEMA)
                .select('*')
                .from_table(self.TABLE)
            )

            if order_by:
                query.order_by(order_by)
            elif self.PRIMARY_KEY:
                query.order_by(self.PRIMARY_KEY)

            if offset:
                query.offset(offset)

            if limit:
                query.limit(limit)

            df = conn.execute_query(query.build(), query.get_params())

            return df.to_dict('records')

        except Exception as e:
            logger.error(f"Error en find_all(): {e}")
            raise RepositoryError(f"Error obteniendo todos los registros: {e}")

    def find_where(
        self,
        conditions: Dict[str, Any],
        limit: Optional[int] = None,
        order_by: Optional[str] = None
    ) -> List[Dict]:
        """
        Busca registros que cumplan las condiciones

        Args:
            conditions: Dict de columna -> valor para filtrar
            limit: Numero maximo de registros
            order_by: Columna para ordenar

        Returns:
            Lista de diccionarios con los registros
        """
        try:
            conn = self._ensure_connected()

            query = (
                QueryBuilder(schema=self.SCHEMA)
                .select('*')
                .from_table(self.TABLE)
            )

            # Agregar condiciones
            for col, val in conditions.items():
                if val is None:
                    query.where_null(col)
                elif isinstance(val, (list, tuple)):
                    query.where_in(col, list(val))
                else:
                    query.where(f"{col} = ?", val)

            if order_by:
                query.order_by(order_by)

            if limit:
                query.limit(limit)

            df = conn.execute_query(query.build(), query.get_params())

            return df.to_dict('records')

        except Exception as e:
            logger.error(f"Error en find_where({conditions}): {e}")
            raise RepositoryError(f"Error en busqueda: {e}")

    def find_one_where(self, conditions: Dict[str, Any]) -> Optional[Dict]:
        """
        Busca un unico registro que cumpla las condiciones

        Args:
            conditions: Dict de columna -> valor

        Returns:
            Dict con el registro o None
        """
        results = self.find_where(conditions, limit=1)
        return results[0] if results else None

    def count(self, conditions: Optional[Dict[str, Any]] = None) -> int:
        """
        Cuenta registros

        Args:
            conditions: Condiciones opcionales

        Returns:
            Numero de registros
        """
        try:
            conn = self._ensure_connected()

            query = (
                QueryBuilder(schema=self.SCHEMA)
                .count()
                .from_table(self.TABLE)
            )

            if conditions:
                for col, val in conditions.items():
                    if val is None:
                        query.where_null(col)
                    elif isinstance(val, (list, tuple)):
                        query.where_in(col, list(val))
                    else:
                        query.where(f"{col} = ?", val)

            df = conn.execute_query(query.build(), query.get_params())

            return int(df.iloc[0, 0])

        except Exception as e:
            logger.error(f"Error en count(): {e}")
            return 0

    def exists(self, id_value: Any) -> bool:
        """
        Verifica si existe un registro con el ID dado

        Args:
            id_value: Valor del ID

        Returns:
            True si existe
        """
        if not self.PRIMARY_KEY:
            raise RepositoryError("PRIMARY_KEY no definido")

        return self.count({self.PRIMARY_KEY: id_value}) > 0

    # ===============================================================
    # OPERACIONES DE ESCRITURA
    # ===============================================================

    def insert(self, data: Dict[str, Any]) -> int:
        """
        Inserta un nuevo registro

        Args:
            data: Dict con columna -> valor

        Returns:
            Numero de filas afectadas (1 si exitoso)

        Raises:
            RepositoryError: Si hay error en la insercion
        """
        if not data:
            raise RepositoryError("No hay datos para insertar")

        try:
            conn = self._ensure_connected()

            columns = list(data.keys())
            values = list(data.values())

            query = QueryBuilder(schema=self.SCHEMA).insert_into(self.TABLE, *columns)
            query.values(*values)

            rows = conn.execute_non_query(query.build(), tuple(values))

            logger.info(f"Insertado en {self.TABLE}: {rows} fila(s)")
            return rows

        except Exception as e:
            logger.error(f"Error en insert(): {e}")
            raise RepositoryError(f"Error insertando registro: {e}")

    def insert_many(self, data_list: List[Dict[str, Any]]) -> int:
        """
        Inserta multiples registros

        Args:
            data_list: Lista de diccionarios

        Returns:
            Numero total de filas insertadas
        """
        if not data_list:
            return 0

        total_rows = 0
        try:
            conn = self._ensure_connected()

            with conn.transaction():
                for data in data_list:
                    total_rows += self.insert(data)

            logger.info(f"Insertados en {self.TABLE}: {total_rows} fila(s)")
            return total_rows

        except Exception as e:
            logger.error(f"Error en insert_many(): {e}")
            raise RepositoryError(f"Error insertando registros: {e}")

    def update(self, id_value: Any, data: Dict[str, Any]) -> bool:
        """
        Actualiza un registro por su ID

        Args:
            id_value: Valor del ID
            data: Dict con columna -> nuevo valor

        Returns:
            True si se actualizo al menos un registro
        """
        if not self.PRIMARY_KEY:
            raise RepositoryError("PRIMARY_KEY no definido")

        if not data:
            raise RepositoryError("No hay datos para actualizar")

        try:
            conn = self._ensure_connected()

            query = (
                QueryBuilder(schema=self.SCHEMA)
                .update(self.TABLE)
                .set_many(data)
                .where(f"{self.PRIMARY_KEY} = ?", id_value)
            )

            sql, params = query.get_sql_with_params()
            rows = conn.execute_non_query(sql, params)

            logger.info(f"Actualizado en {self.TABLE}: {rows} fila(s)")
            return rows > 0

        except Exception as e:
            logger.error(f"Error en update({id_value}): {e}")
            raise RepositoryError(f"Error actualizando registro: {e}")

    def update_where(
        self,
        conditions: Dict[str, Any],
        data: Dict[str, Any]
    ) -> int:
        """
        Actualiza registros que cumplan las condiciones

        Args:
            conditions: Condiciones para filtrar
            data: Datos a actualizar

        Returns:
            Numero de filas actualizadas
        """
        if not conditions:
            raise RepositoryError("Se requieren condiciones para update_where")

        if not data:
            raise RepositoryError("No hay datos para actualizar")

        try:
            conn = self._ensure_connected()

            query = (
                QueryBuilder(schema=self.SCHEMA)
                .update(self.TABLE)
                .set_many(data)
            )

            for col, val in conditions.items():
                query.where(f"{col} = ?", val)

            sql, params = query.get_sql_with_params()
            rows = conn.execute_non_query(sql, params)

            logger.info(f"Actualizados en {self.TABLE}: {rows} fila(s)")
            return rows

        except Exception as e:
            logger.error(f"Error en update_where(): {e}")
            raise RepositoryError(f"Error actualizando registros: {e}")

    def delete(self, id_value: Any) -> bool:
        """
        Elimina un registro por su ID

        Args:
            id_value: Valor del ID

        Returns:
            True si se elimino al menos un registro
        """
        if not self.PRIMARY_KEY:
            raise RepositoryError("PRIMARY_KEY no definido")

        try:
            conn = self._ensure_connected()

            query = (
                QueryBuilder(schema=self.SCHEMA)
                .delete_from(self.TABLE)
                .where(f"{self.PRIMARY_KEY} = ?", id_value)
            )

            rows = conn.execute_non_query(query.build(), query.get_params())

            logger.info(f"Eliminado de {self.TABLE}: {rows} fila(s)")
            return rows > 0

        except Exception as e:
            logger.error(f"Error en delete({id_value}): {e}")
            raise RepositoryError(f"Error eliminando registro: {e}")

    def delete_where(self, conditions: Dict[str, Any]) -> int:
        """
        Elimina registros que cumplan las condiciones

        Args:
            conditions: Condiciones para filtrar

        Returns:
            Numero de filas eliminadas
        """
        if not conditions:
            raise RepositoryError("Se requieren condiciones para delete_where")

        try:
            conn = self._ensure_connected()

            query = (
                QueryBuilder(schema=self.SCHEMA)
                .delete_from(self.TABLE)
            )

            for col, val in conditions.items():
                query.where(f"{col} = ?", val)

            rows = conn.execute_non_query(query.build(), query.get_params())

            logger.info(f"Eliminados de {self.TABLE}: {rows} fila(s)")
            return rows

        except Exception as e:
            logger.error(f"Error en delete_where(): {e}")
            raise RepositoryError(f"Error eliminando registros: {e}")

    # ===============================================================
    # METODOS DE CONVENIENCIA
    # ===============================================================

    def to_dataframe(self, records: List[Dict]) -> pd.DataFrame:
        """Convierte lista de registros a DataFrame"""
        return pd.DataFrame(records)

    def execute_raw(self, sql: str, params: Optional[Tuple] = None) -> pd.DataFrame:
        """
        Ejecuta una query SQL raw

        Args:
            sql: Query SQL
            params: Parametros

        Returns:
            DataFrame con resultados
        """
        conn = self._ensure_connected()
        return conn.execute_query(sql, params)

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
    'BaseRepository',
    'RepositoryError',
    'EntityNotFoundError',
    'DuplicateEntityError',
]
