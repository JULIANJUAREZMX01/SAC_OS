"""
===============================================================
REPOSITORIO DE ORDENES DE COMPRA (OC)
Sistema de Automatizacion de Consultas - CEDIS Cancun 427
===============================================================

Repositorio especializado para operaciones con Ordenes de Compra
en Manhattan WMS.

Uso:
    from modules.repositories import OCRepository

    repo = OCRepository()
    oc = repo.find_by_oc_number('C750384123456')
    pending = repo.find_pending_ocs()

Desarrollado por: Julian Alexander Juarez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logistica Cancun
===============================================================
"""

import logging
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
import pandas as pd

from .base_repository import BaseRepository, RepositoryError
from ..query_builder import QueryBuilder

# ===============================================================
# CONFIGURACION DE LOGGING
# ===============================================================

logger = logging.getLogger(__name__)


# ===============================================================
# REPOSITORIO DE OC
# ===============================================================

class OCRepository(BaseRepository):
    """
    Repositorio para Ordenes de Compra (OC)

    Proporciona metodos especializados para:
    - Buscar OC por numero
    - Obtener OCs pendientes
    - Obtener OCs vencidas
    - Obtener resumen de OC
    - Validar OCs

    Tablas utilizadas:
    - ORDERS: Cabecera de ordenes
    - ORDERDETAIL: Detalle de ordenes
    """

    TABLE = "ORDERS"
    PRIMARY_KEY = "ORDERKEY"
    SCHEMA = "WMWHSE1"

    # Estados de OC en Manhattan WMS
    STATUS_OPEN = '0'
    STATUS_IN_PROGRESS = '1'
    STATUS_PARTIAL = '2'
    STATUS_COMPLETE = '9'

    def find_by_oc_number(self, oc_number: str) -> pd.DataFrame:
        """
        Busca una OC por su numero

        Args:
            oc_number: Numero de OC (ej: 'C750384123456')

        Returns:
            DataFrame con la informacion de la OC
        """
        try:
            conn = self._ensure_connected()

            # Agregar prefijo C si no lo tiene
            if not oc_number.startswith('C'):
                oc_number = f'C{oc_number}'

            query = """
                SELECT
                    O.ORDERKEY,
                    O.EXTERNORDERKEY,
                    O.STORERKEY,
                    O.STATUS,
                    O.ORDERDATE,
                    O.DELIVERYDATE,
                    O.ADDDATE,
                    O.EDITDATE,
                    D.ORDERLINENUMBER,
                    D.SKU,
                    D.OPENQTY,
                    D.SHIPPEDQTY,
                    D.ORIGINALQTY,
                    S.DESCR AS SKU_DESCR
                FROM {schema}.ORDERS O
                LEFT JOIN {schema}.ORDERDETAIL D ON O.ORDERKEY = D.ORDERKEY
                LEFT JOIN {schema}.SKU S ON D.SKU = S.SKU AND D.STORERKEY = S.STORERKEY
                WHERE O.EXTERNORDERKEY = ?
                   OR O.ORDERKEY = ?
                ORDER BY D.ORDERLINENUMBER
            """.format(schema=self.SCHEMA)

            df = conn.execute_query(query, (oc_number, oc_number))

            if df.empty:
                logger.warning(f"OC {oc_number} no encontrada")

            return df

        except Exception as e:
            logger.error(f"Error buscando OC {oc_number}: {e}")
            raise RepositoryError(f"Error buscando OC: {e}")

    def find_pending_ocs(
        self,
        storer_key: Optional[str] = None,
        days_back: int = 30
    ) -> pd.DataFrame:
        """
        Obtiene las OCs pendientes de recibir

        Args:
            storer_key: Filtrar por almacen (opcional)
            days_back: Dias hacia atras para buscar

        Returns:
            DataFrame con OCs pendientes
        """
        try:
            conn = self._ensure_connected()

            query = """
                SELECT
                    O.ORDERKEY,
                    O.EXTERNORDERKEY,
                    O.STORERKEY,
                    O.STATUS,
                    O.ORDERDATE,
                    O.DELIVERYDATE,
                    COUNT(DISTINCT D.SKU) AS TOTAL_SKUS,
                    SUM(D.OPENQTY) AS TOTAL_OPEN_QTY,
                    SUM(D.SHIPPEDQTY) AS TOTAL_SHIPPED_QTY
                FROM {schema}.ORDERS O
                LEFT JOIN {schema}.ORDERDETAIL D ON O.ORDERKEY = D.ORDERKEY
                WHERE O.STATUS IN ('0', '1', '2')
                  AND O.ORDERDATE >= CURRENT_DATE - ? DAYS
            """.format(schema=self.SCHEMA)

            params = [days_back]

            if storer_key:
                query += " AND O.STORERKEY = ?"
                params.append(storer_key)

            query += """
                GROUP BY O.ORDERKEY, O.EXTERNORDERKEY, O.STORERKEY,
                         O.STATUS, O.ORDERDATE, O.DELIVERYDATE
                ORDER BY O.DELIVERYDATE, O.ORDERKEY
            """

            df = conn.execute_query(query, tuple(params))

            logger.info(f"Encontradas {len(df)} OCs pendientes")
            return df

        except Exception as e:
            logger.error(f"Error obteniendo OCs pendientes: {e}")
            raise RepositoryError(f"Error obteniendo OCs pendientes: {e}")

    def find_expired_ocs(
        self,
        storer_key: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Obtiene las OCs vencidas (fecha de entrega pasada)

        Args:
            storer_key: Filtrar por almacen (opcional)

        Returns:
            DataFrame con OCs vencidas
        """
        try:
            conn = self._ensure_connected()

            query = """
                SELECT
                    O.ORDERKEY,
                    O.EXTERNORDERKEY,
                    O.STORERKEY,
                    O.STATUS,
                    O.ORDERDATE,
                    O.DELIVERYDATE,
                    DAYS(CURRENT_DATE) - DAYS(O.DELIVERYDATE) AS DIAS_VENCIDA,
                    SUM(D.OPENQTY) AS QTY_PENDIENTE
                FROM {schema}.ORDERS O
                LEFT JOIN {schema}.ORDERDETAIL D ON O.ORDERKEY = D.ORDERKEY
                WHERE O.STATUS IN ('0', '1', '2')
                  AND O.DELIVERYDATE < CURRENT_DATE
                  AND D.OPENQTY > 0
            """.format(schema=self.SCHEMA)

            params = []

            if storer_key:
                query += " AND O.STORERKEY = ?"
                params.append(storer_key)

            query += """
                GROUP BY O.ORDERKEY, O.EXTERNORDERKEY, O.STORERKEY,
                         O.STATUS, O.ORDERDATE, O.DELIVERYDATE
                ORDER BY DIAS_VENCIDA DESC
            """

            df = conn.execute_query(query, tuple(params) if params else None)

            logger.info(f"Encontradas {len(df)} OCs vencidas")
            return df

        except Exception as e:
            logger.error(f"Error obteniendo OCs vencidas: {e}")
            raise RepositoryError(f"Error obteniendo OCs vencidas: {e}")

    def find_ocs_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        storer_key: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Obtiene OCs en un rango de fechas

        Args:
            start_date: Fecha inicio
            end_date: Fecha fin
            storer_key: Filtrar por almacen (opcional)

        Returns:
            DataFrame con OCs
        """
        try:
            conn = self._ensure_connected()

            query = """
                SELECT
                    O.ORDERKEY,
                    O.EXTERNORDERKEY,
                    O.STORERKEY,
                    O.STATUS,
                    O.ORDERDATE,
                    O.DELIVERYDATE,
                    COUNT(DISTINCT D.SKU) AS TOTAL_SKUS,
                    SUM(D.ORIGINALQTY) AS TOTAL_QTY
                FROM {schema}.ORDERS O
                LEFT JOIN {schema}.ORDERDETAIL D ON O.ORDERKEY = D.ORDERKEY
                WHERE O.ORDERDATE BETWEEN ? AND ?
            """.format(schema=self.SCHEMA)

            params = [start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')]

            if storer_key:
                query += " AND O.STORERKEY = ?"
                params.append(storer_key)

            query += """
                GROUP BY O.ORDERKEY, O.EXTERNORDERKEY, O.STORERKEY,
                         O.STATUS, O.ORDERDATE, O.DELIVERYDATE
                ORDER BY O.ORDERDATE DESC
            """

            df = conn.execute_query(query, tuple(params))
            return df

        except Exception as e:
            logger.error(f"Error obteniendo OCs por fecha: {e}")
            raise RepositoryError(f"Error obteniendo OCs por fecha: {e}")

    def get_oc_summary(self, oc_number: str) -> Dict[str, Any]:
        """
        Obtiene un resumen de una OC

        Args:
            oc_number: Numero de OC

        Returns:
            Dict con resumen de la OC
        """
        try:
            df = self.find_by_oc_number(oc_number)

            if df.empty:
                return {
                    'found': False,
                    'oc_number': oc_number,
                    'message': 'OC no encontrada'
                }

            # Calcular resumen
            summary = {
                'found': True,
                'oc_number': oc_number,
                'order_key': df['ORDERKEY'].iloc[0] if 'ORDERKEY' in df.columns else None,
                'extern_order_key': df['EXTERNORDERKEY'].iloc[0] if 'EXTERNORDERKEY' in df.columns else None,
                'storer_key': df['STORERKEY'].iloc[0] if 'STORERKEY' in df.columns else None,
                'status': df['STATUS'].iloc[0] if 'STATUS' in df.columns else None,
                'order_date': str(df['ORDERDATE'].iloc[0]) if 'ORDERDATE' in df.columns else None,
                'delivery_date': str(df['DELIVERYDATE'].iloc[0]) if 'DELIVERYDATE' in df.columns else None,
                'total_lines': len(df),
                'total_skus': df['SKU'].nunique() if 'SKU' in df.columns else 0,
                'total_open_qty': df['OPENQTY'].sum() if 'OPENQTY' in df.columns else 0,
                'total_shipped_qty': df['SHIPPEDQTY'].sum() if 'SHIPPEDQTY' in df.columns else 0,
                'total_original_qty': df['ORIGINALQTY'].sum() if 'ORIGINALQTY' in df.columns else 0,
            }

            # Calcular porcentaje de completitud
            if summary['total_original_qty'] > 0:
                summary['completion_pct'] = round(
                    (summary['total_shipped_qty'] / summary['total_original_qty']) * 100, 2
                )
            else:
                summary['completion_pct'] = 0

            return summary

        except Exception as e:
            logger.error(f"Error obteniendo resumen de OC {oc_number}: {e}")
            return {
                'found': False,
                'oc_number': oc_number,
                'error': str(e)
            }

    def get_oc_detail(self, oc_number: str) -> pd.DataFrame:
        """
        Obtiene el detalle de SKUs de una OC

        Args:
            oc_number: Numero de OC

        Returns:
            DataFrame con detalle de SKUs
        """
        return self.find_by_oc_number(oc_number)

    def get_ocs_about_to_expire(self, days_ahead: int = 3) -> pd.DataFrame:
        """
        Obtiene OCs proximas a vencer

        Args:
            days_ahead: Dias por adelantado para alertar

        Returns:
            DataFrame con OCs proximas a vencer
        """
        try:
            conn = self._ensure_connected()

            query = """
                SELECT
                    O.ORDERKEY,
                    O.EXTERNORDERKEY,
                    O.STORERKEY,
                    O.STATUS,
                    O.DELIVERYDATE,
                    DAYS(O.DELIVERYDATE) - DAYS(CURRENT_DATE) AS DIAS_PARA_VENCER,
                    SUM(D.OPENQTY) AS QTY_PENDIENTE
                FROM {schema}.ORDERS O
                LEFT JOIN {schema}.ORDERDETAIL D ON O.ORDERKEY = D.ORDERKEY
                WHERE O.STATUS IN ('0', '1', '2')
                  AND O.DELIVERYDATE BETWEEN CURRENT_DATE AND CURRENT_DATE + ? DAYS
                  AND D.OPENQTY > 0
                GROUP BY O.ORDERKEY, O.EXTERNORDERKEY, O.STORERKEY,
                         O.STATUS, O.DELIVERYDATE
                ORDER BY DIAS_PARA_VENCER
            """.format(schema=self.SCHEMA)

            df = conn.execute_query(query, (days_ahead,))
            return df

        except Exception as e:
            logger.error(f"Error obteniendo OCs por vencer: {e}")
            raise RepositoryError(f"Error obteniendo OCs por vencer: {e}")

    def get_daily_ocs(self, date: Optional[datetime] = None) -> pd.DataFrame:
        """
        Obtiene las OCs del dia

        Args:
            date: Fecha (default: hoy)

        Returns:
            DataFrame con OCs del dia
        """
        if date is None:
            date = datetime.now()

        try:
            conn = self._ensure_connected()

            query = """
                SELECT
                    O.ORDERKEY,
                    O.EXTERNORDERKEY,
                    O.STORERKEY,
                    O.STATUS,
                    O.ORDERDATE,
                    O.DELIVERYDATE,
                    COUNT(DISTINCT D.SKU) AS TOTAL_SKUS,
                    SUM(D.ORIGINALQTY) AS TOTAL_QTY
                FROM {schema}.ORDERS O
                LEFT JOIN {schema}.ORDERDETAIL D ON O.ORDERKEY = D.ORDERKEY
                WHERE DATE(O.ADDDATE) = ?
                GROUP BY O.ORDERKEY, O.EXTERNORDERKEY, O.STORERKEY,
                         O.STATUS, O.ORDERDATE, O.DELIVERYDATE
                ORDER BY O.ORDERKEY
            """.format(schema=self.SCHEMA)

            df = conn.execute_query(query, (date.strftime('%Y-%m-%d'),))
            return df

        except Exception as e:
            logger.error(f"Error obteniendo OCs del dia: {e}")
            raise RepositoryError(f"Error obteniendo OCs del dia: {e}")


# ===============================================================
# EXPORTAR
# ===============================================================

__all__ = ['OCRepository']
