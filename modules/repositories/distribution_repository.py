"""
===============================================================
REPOSITORIO DE DISTRIBUCIONES
Sistema de Automatizacion de Consultas - CEDIS Cancun 427
===============================================================

Repositorio especializado para operaciones con Distribuciones
en Manhattan WMS.

Uso:
    from modules.repositories import DistributionRepository

    repo = DistributionRepository()
    distros = repo.find_by_oc('C750384123456')
    totals = repo.get_distribution_totals('C750384123456')

Desarrollado por: Julian Alexander Juarez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logistica Cancun
===============================================================
"""

import logging
from typing import Optional, Dict, List, Any
from datetime import datetime
import pandas as pd

from .base_repository import BaseRepository, RepositoryError
from ..query_builder import QueryBuilder

# ===============================================================
# CONFIGURACION DE LOGGING
# ===============================================================

logger = logging.getLogger(__name__)


# ===============================================================
# REPOSITORIO DE DISTRIBUCIONES
# ===============================================================

class DistributionRepository(BaseRepository):
    """
    Repositorio para Distribuciones

    Proporciona metodos especializados para:
    - Buscar distribuciones por OC
    - Buscar distribuciones por tienda
    - Obtener totales de distribucion
    - Detectar distribuciones excedentes

    Tablas utilizadas:
    - ORDERDETAIL: Detalle de ordenes con info de distribucion
    - STORER: Tiendas destino
    """

    TABLE = "ORDERDETAIL"
    PRIMARY_KEY = "ORDERKEY"  # Es composite con ORDERLINENUMBER
    SCHEMA = "WMWHSE1"

    def find_by_oc(self, oc_number: str) -> pd.DataFrame:
        """
        Obtiene las distribuciones de una OC

        Args:
            oc_number: Numero de OC

        Returns:
            DataFrame con distribuciones
        """
        try:
            conn = self._ensure_connected()

            # Agregar prefijo C si no lo tiene
            if not oc_number.startswith('C'):
                oc_number = f'C{oc_number}'

            query = """
                SELECT
                    D.ORDERKEY,
                    D.ORDERLINENUMBER,
                    D.SKU,
                    D.STORERKEY AS TIENDA,
                    D.ORIGINALQTY AS QTY_SOLICITADA,
                    D.OPENQTY AS QTY_PENDIENTE,
                    D.SHIPPEDQTY AS QTY_ENVIADA,
                    S.DESCR AS SKU_DESCR,
                    ST.COMPANY AS TIENDA_NOMBRE
                FROM {schema}.ORDERS O
                INNER JOIN {schema}.ORDERDETAIL D ON O.ORDERKEY = D.ORDERKEY
                LEFT JOIN {schema}.SKU S ON D.SKU = S.SKU AND D.STORERKEY = S.STORERKEY
                LEFT JOIN {schema}.STORER ST ON D.STORERKEY = ST.STORERKEY
                WHERE O.EXTERNORDERKEY = ?
                   OR O.ORDERKEY = ?
                ORDER BY D.STORERKEY, D.SKU
            """.format(schema=self.SCHEMA)

            df = conn.execute_query(query, (oc_number, oc_number))
            return df

        except Exception as e:
            logger.error(f"Error obteniendo distribuciones de OC {oc_number}: {e}")
            raise RepositoryError(f"Error obteniendo distribuciones: {e}")

    def find_by_store(
        self,
        store_key: str,
        days_back: int = 30
    ) -> pd.DataFrame:
        """
        Obtiene distribuciones para una tienda

        Args:
            store_key: Clave de la tienda
            days_back: Dias hacia atras

        Returns:
            DataFrame con distribuciones
        """
        try:
            conn = self._ensure_connected()

            query = """
                SELECT
                    O.EXTERNORDERKEY AS OC,
                    D.SKU,
                    D.ORIGINALQTY,
                    D.OPENQTY,
                    D.SHIPPEDQTY,
                    O.ORDERDATE,
                    O.STATUS
                FROM {schema}.ORDERDETAIL D
                INNER JOIN {schema}.ORDERS O ON D.ORDERKEY = O.ORDERKEY
                WHERE D.STORERKEY = ?
                  AND O.ORDERDATE >= CURRENT_DATE - ? DAYS
                ORDER BY O.ORDERDATE DESC, D.SKU
            """.format(schema=self.SCHEMA)

            df = conn.execute_query(query, (store_key, days_back))
            return df

        except Exception as e:
            logger.error(f"Error obteniendo distribuciones de tienda {store_key}: {e}")
            raise RepositoryError(f"Error obteniendo distribuciones por tienda: {e}")

    def get_distribution_totals(self, oc_number: str) -> Dict[str, Any]:
        """
        Obtiene totales de distribucion para una OC

        Args:
            oc_number: Numero de OC

        Returns:
            Dict con totales
        """
        try:
            df = self.find_by_oc(oc_number)

            if df.empty:
                return {
                    'found': False,
                    'oc_number': oc_number,
                    'message': 'No hay distribuciones'
                }

            totals = {
                'found': True,
                'oc_number': oc_number,
                'total_lines': len(df),
                'total_skus': df['SKU'].nunique() if 'SKU' in df.columns else 0,
                'total_stores': df['TIENDA'].nunique() if 'TIENDA' in df.columns else 0,
                'qty_solicitada': df['QTY_SOLICITADA'].sum() if 'QTY_SOLICITADA' in df.columns else 0,
                'qty_pendiente': df['QTY_PENDIENTE'].sum() if 'QTY_PENDIENTE' in df.columns else 0,
                'qty_enviada': df['QTY_ENVIADA'].sum() if 'QTY_ENVIADA' in df.columns else 0,
            }

            # Calcular porcentajes
            if totals['qty_solicitada'] > 0:
                totals['pct_enviado'] = round(
                    (totals['qty_enviada'] / totals['qty_solicitada']) * 100, 2
                )
                totals['pct_pendiente'] = round(
                    (totals['qty_pendiente'] / totals['qty_solicitada']) * 100, 2
                )
            else:
                totals['pct_enviado'] = 0
                totals['pct_pendiente'] = 0

            # Resumen por tienda
            if 'TIENDA' in df.columns and 'QTY_SOLICITADA' in df.columns:
                by_store = df.groupby('TIENDA').agg({
                    'QTY_SOLICITADA': 'sum',
                    'QTY_ENVIADA': 'sum'
                }).reset_index()
                totals['by_store'] = by_store.to_dict('records')

            return totals

        except Exception as e:
            logger.error(f"Error obteniendo totales de OC {oc_number}: {e}")
            return {
                'found': False,
                'oc_number': oc_number,
                'error': str(e)
            }

    def find_exceeding_distributions(self, oc_number: str) -> pd.DataFrame:
        """
        Encuentra distribuciones que exceden la OC

        Args:
            oc_number: Numero de OC

        Returns:
            DataFrame con distribuciones excedentes
        """
        try:
            conn = self._ensure_connected()

            if not oc_number.startswith('C'):
                oc_number = f'C{oc_number}'

            # Esta query compara el total distribuido vs el total de la OC
            query = """
                SELECT
                    D.SKU,
                    S.DESCR AS SKU_DESCR,
                    SUM(D.ORIGINALQTY) AS TOTAL_DISTRIBUIDO,
                    O.TOTAL_OC,
                    SUM(D.ORIGINALQTY) - O.TOTAL_OC AS EXCEDENTE
                FROM {schema}.ORDERDETAIL D
                INNER JOIN {schema}.ORDERS OD ON D.ORDERKEY = OD.ORDERKEY
                LEFT JOIN {schema}.SKU S ON D.SKU = S.SKU
                INNER JOIN (
                    SELECT ORDERKEY, SKU, SUM(ORIGINALQTY) AS TOTAL_OC
                    FROM {schema}.ORDERDETAIL
                    GROUP BY ORDERKEY, SKU
                ) O ON D.ORDERKEY = O.ORDERKEY AND D.SKU = O.SKU
                WHERE OD.EXTERNORDERKEY = ? OR OD.ORDERKEY = ?
                GROUP BY D.SKU, S.DESCR, O.TOTAL_OC
                HAVING SUM(D.ORIGINALQTY) > O.TOTAL_OC
                ORDER BY EXCEDENTE DESC
            """.format(schema=self.SCHEMA)

            df = conn.execute_query(query, (oc_number, oc_number))

            if not df.empty:
                logger.warning(f"Encontradas {len(df)} distribuciones excedentes en OC {oc_number}")

            return df

        except Exception as e:
            logger.error(f"Error buscando distribuciones excedentes: {e}")
            raise RepositoryError(f"Error buscando excedentes: {e}")

    def find_incomplete_distributions(self, oc_number: str) -> pd.DataFrame:
        """
        Encuentra distribuciones incompletas (menos que la OC)

        Args:
            oc_number: Numero de OC

        Returns:
            DataFrame con distribuciones incompletas
        """
        try:
            conn = self._ensure_connected()

            if not oc_number.startswith('C'):
                oc_number = f'C{oc_number}'

            query = """
                SELECT
                    D.SKU,
                    S.DESCR AS SKU_DESCR,
                    SUM(D.ORIGINALQTY) AS TOTAL_DISTRIBUIDO,
                    SUM(D.OPENQTY) AS PENDIENTE
                FROM {schema}.ORDERDETAIL D
                INNER JOIN {schema}.ORDERS O ON D.ORDERKEY = O.ORDERKEY
                LEFT JOIN {schema}.SKU S ON D.SKU = S.SKU
                WHERE (O.EXTERNORDERKEY = ? OR O.ORDERKEY = ?)
                  AND D.OPENQTY > 0
                GROUP BY D.SKU, S.DESCR
                ORDER BY PENDIENTE DESC
            """.format(schema=self.SCHEMA)

            df = conn.execute_query(query, (oc_number, oc_number))
            return df

        except Exception as e:
            logger.error(f"Error buscando distribuciones incompletas: {e}")
            raise RepositoryError(f"Error buscando incompletas: {e}")

    def get_distribution_by_sku(
        self,
        oc_number: str,
        sku: str
    ) -> pd.DataFrame:
        """
        Obtiene distribucion de un SKU especifico en una OC

        Args:
            oc_number: Numero de OC
            sku: Codigo de SKU

        Returns:
            DataFrame con distribucion del SKU
        """
        try:
            conn = self._ensure_connected()

            if not oc_number.startswith('C'):
                oc_number = f'C{oc_number}'

            query = """
                SELECT
                    D.STORERKEY AS TIENDA,
                    ST.COMPANY AS TIENDA_NOMBRE,
                    D.ORIGINALQTY AS QTY_SOLICITADA,
                    D.OPENQTY AS QTY_PENDIENTE,
                    D.SHIPPEDQTY AS QTY_ENVIADA
                FROM {schema}.ORDERDETAIL D
                INNER JOIN {schema}.ORDERS O ON D.ORDERKEY = O.ORDERKEY
                LEFT JOIN {schema}.STORER ST ON D.STORERKEY = ST.STORERKEY
                WHERE (O.EXTERNORDERKEY = ? OR O.ORDERKEY = ?)
                  AND D.SKU = ?
                ORDER BY D.STORERKEY
            """.format(schema=self.SCHEMA)

            df = conn.execute_query(query, (oc_number, oc_number, sku))
            return df

        except Exception as e:
            logger.error(f"Error obteniendo distribucion de SKU {sku}: {e}")
            raise RepositoryError(f"Error obteniendo distribucion por SKU: {e}")

    def get_daily_distributions(self, date: Optional[datetime] = None) -> pd.DataFrame:
        """
        Obtiene distribuciones del dia

        Args:
            date: Fecha (default: hoy)

        Returns:
            DataFrame con distribuciones del dia
        """
        if date is None:
            date = datetime.now()

        try:
            conn = self._ensure_connected()

            query = """
                SELECT
                    O.EXTERNORDERKEY AS OC,
                    D.STORERKEY AS TIENDA,
                    COUNT(DISTINCT D.SKU) AS TOTAL_SKUS,
                    SUM(D.ORIGINALQTY) AS TOTAL_QTY
                FROM {schema}.ORDERDETAIL D
                INNER JOIN {schema}.ORDERS O ON D.ORDERKEY = O.ORDERKEY
                WHERE DATE(O.ADDDATE) = ?
                GROUP BY O.EXTERNORDERKEY, D.STORERKEY
                ORDER BY O.EXTERNORDERKEY, D.STORERKEY
            """.format(schema=self.SCHEMA)

            df = conn.execute_query(query, (date.strftime('%Y-%m-%d'),))
            return df

        except Exception as e:
            logger.error(f"Error obteniendo distribuciones del dia: {e}")
            raise RepositoryError(f"Error obteniendo distribuciones del dia: {e}")


# ===============================================================
# EXPORTAR
# ===============================================================

__all__ = ['DistributionRepository']
