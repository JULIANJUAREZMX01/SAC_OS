"""
===============================================================
REPOSITORIO DE ASN (Advanced Shipping Notice)
Sistema de Automatizacion de Consultas - CEDIS Cancun 427
===============================================================

Repositorio especializado para operaciones con ASN
en Manhattan WMS.

Uso:
    from modules.repositories import ASNRepository

    repo = ASNRepository()
    asn = repo.find_by_asn_number('ASN123456')
    pending = repo.find_pending_asns()

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
# REPOSITORIO DE ASN
# ===============================================================

class ASNRepository(BaseRepository):
    """
    Repositorio para ASN (Advanced Shipping Notice)

    Proporciona metodos especializados para:
    - Buscar ASN por numero
    - Obtener ASNs pendientes
    - Buscar ASNs por estado
    - Detectar ASNs sin actualizar

    Tablas utilizadas:
    - ASN: Cabecera de ASN
    - ASNDETAIL: Detalle de ASN
    - RECEIPT: Recibos relacionados
    """

    TABLE = "ASN"
    PRIMARY_KEY = "ASNKEY"
    SCHEMA = "WMWHSE1"

    # Estados de ASN en Manhattan WMS
    STATUS_NEW = '0'
    STATUS_IN_PROGRESS = '1'
    STATUS_PARTIAL = '2'
    STATUS_RECEIVED = '9'
    STATUS_CANCELLED = 'X'

    def find_by_asn_number(self, asn_number: str) -> pd.DataFrame:
        """
        Busca un ASN por su numero

        Args:
            asn_number: Numero de ASN

        Returns:
            DataFrame con informacion del ASN
        """
        try:
            conn = self._ensure_connected()

            query = """
                SELECT
                    A.ASNKEY,
                    A.EXTERNRECEIPTKEY,
                    A.STORERKEY,
                    A.STATUS,
                    A.ADDDATE,
                    A.EDITDATE,
                    A.EXPECTEDRECEIPTDATE,
                    D.ASNLINENUMBER,
                    D.SKU,
                    D.EXPECTEDQTY,
                    D.RECEIVEDQTY,
                    S.DESCR AS SKU_DESCR
                FROM {schema}.ASN A
                LEFT JOIN {schema}.ASNDETAIL D ON A.ASNKEY = D.ASNKEY
                LEFT JOIN {schema}.SKU S ON D.SKU = S.SKU AND A.STORERKEY = S.STORERKEY
                WHERE A.EXTERNRECEIPTKEY = ?
                   OR A.ASNKEY = ?
                ORDER BY D.ASNLINENUMBER
            """.format(schema=self.SCHEMA)

            df = conn.execute_query(query, (asn_number, asn_number))

            if df.empty:
                logger.warning(f"ASN {asn_number} no encontrado")

            return df

        except Exception as e:
            logger.error(f"Error buscando ASN {asn_number}: {e}")
            raise RepositoryError(f"Error buscando ASN: {e}")

    def find_pending_asns(
        self,
        storer_key: Optional[str] = None,
        days_back: int = 30
    ) -> pd.DataFrame:
        """
        Obtiene los ASNs pendientes de recibir

        Args:
            storer_key: Filtrar por almacen (opcional)
            days_back: Dias hacia atras para buscar

        Returns:
            DataFrame con ASNs pendientes
        """
        try:
            conn = self._ensure_connected()

            query = """
                SELECT
                    A.ASNKEY,
                    A.EXTERNRECEIPTKEY,
                    A.STORERKEY,
                    A.STATUS,
                    A.EXPECTEDRECEIPTDATE,
                    A.ADDDATE,
                    COUNT(DISTINCT D.SKU) AS TOTAL_SKUS,
                    SUM(D.EXPECTEDQTY) AS TOTAL_EXPECTED,
                    SUM(D.RECEIVEDQTY) AS TOTAL_RECEIVED
                FROM {schema}.ASN A
                LEFT JOIN {schema}.ASNDETAIL D ON A.ASNKEY = D.ASNKEY
                WHERE A.STATUS IN ('0', '1', '2')
                  AND A.ADDDATE >= CURRENT_DATE - ? DAYS
            """.format(schema=self.SCHEMA)

            params = [days_back]

            if storer_key:
                query += " AND A.STORERKEY = ?"
                params.append(storer_key)

            query += """
                GROUP BY A.ASNKEY, A.EXTERNRECEIPTKEY, A.STORERKEY,
                         A.STATUS, A.EXPECTEDRECEIPTDATE, A.ADDDATE
                ORDER BY A.EXPECTEDRECEIPTDATE, A.ASNKEY
            """

            df = conn.execute_query(query, tuple(params))

            logger.info(f"Encontrados {len(df)} ASNs pendientes")
            return df

        except Exception as e:
            logger.error(f"Error obteniendo ASNs pendientes: {e}")
            raise RepositoryError(f"Error obteniendo ASNs pendientes: {e}")

    def find_by_status(
        self,
        status: str,
        storer_key: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Obtiene ASNs por estado

        Args:
            status: Estado del ASN
            storer_key: Filtrar por almacen (opcional)

        Returns:
            DataFrame con ASNs
        """
        try:
            conn = self._ensure_connected()

            query = """
                SELECT
                    A.ASNKEY,
                    A.EXTERNRECEIPTKEY,
                    A.STORERKEY,
                    A.STATUS,
                    A.EXPECTEDRECEIPTDATE,
                    A.ADDDATE,
                    A.EDITDATE
                FROM {schema}.ASN A
                WHERE A.STATUS = ?
            """.format(schema=self.SCHEMA)

            params = [status]

            if storer_key:
                query += " AND A.STORERKEY = ?"
                params.append(storer_key)

            query += " ORDER BY A.ADDDATE DESC"

            df = conn.execute_query(query, tuple(params))
            return df

        except Exception as e:
            logger.error(f"Error obteniendo ASNs por estado {status}: {e}")
            raise RepositoryError(f"Error obteniendo ASNs por estado: {e}")

    def find_stale_asns(self, hours_threshold: int = 24) -> pd.DataFrame:
        """
        Encuentra ASNs sin actualizar en las ultimas horas

        Args:
            hours_threshold: Umbral de horas sin actualizar

        Returns:
            DataFrame con ASNs estancados
        """
        try:
            conn = self._ensure_connected()

            query = """
                SELECT
                    A.ASNKEY,
                    A.EXTERNRECEIPTKEY,
                    A.STORERKEY,
                    A.STATUS,
                    A.ADDDATE,
                    A.EDITDATE,
                    TIMESTAMPDIFF(2, CURRENT_TIMESTAMP - A.EDITDATE) AS HORAS_SIN_ACTUALIZAR
                FROM {schema}.ASN A
                WHERE A.STATUS IN ('0', '1', '2')
                  AND TIMESTAMPDIFF(2, CURRENT_TIMESTAMP - A.EDITDATE) > ?
                ORDER BY HORAS_SIN_ACTUALIZAR DESC
            """.format(schema=self.SCHEMA)

            df = conn.execute_query(query, (hours_threshold,))

            if not df.empty:
                logger.warning(f"Encontrados {len(df)} ASNs sin actualizar")

            return df

        except Exception as e:
            logger.error(f"Error buscando ASNs estancados: {e}")
            raise RepositoryError(f"Error buscando ASNs estancados: {e}")

    def get_asn_summary(self, asn_number: str) -> Dict[str, Any]:
        """
        Obtiene un resumen de un ASN

        Args:
            asn_number: Numero de ASN

        Returns:
            Dict con resumen del ASN
        """
        try:
            df = self.find_by_asn_number(asn_number)

            if df.empty:
                return {
                    'found': False,
                    'asn_number': asn_number,
                    'message': 'ASN no encontrado'
                }

            summary = {
                'found': True,
                'asn_number': asn_number,
                'asn_key': df['ASNKEY'].iloc[0] if 'ASNKEY' in df.columns else None,
                'extern_receipt_key': df['EXTERNRECEIPTKEY'].iloc[0] if 'EXTERNRECEIPTKEY' in df.columns else None,
                'storer_key': df['STORERKEY'].iloc[0] if 'STORERKEY' in df.columns else None,
                'status': df['STATUS'].iloc[0] if 'STATUS' in df.columns else None,
                'expected_date': str(df['EXPECTEDRECEIPTDATE'].iloc[0]) if 'EXPECTEDRECEIPTDATE' in df.columns else None,
                'total_lines': len(df),
                'total_skus': df['SKU'].nunique() if 'SKU' in df.columns else 0,
                'total_expected': df['EXPECTEDQTY'].sum() if 'EXPECTEDQTY' in df.columns else 0,
                'total_received': df['RECEIVEDQTY'].sum() if 'RECEIVEDQTY' in df.columns else 0,
            }

            # Calcular porcentaje de recepcion
            if summary['total_expected'] > 0:
                summary['reception_pct'] = round(
                    (summary['total_received'] / summary['total_expected']) * 100, 2
                )
            else:
                summary['reception_pct'] = 0

            # Estado descriptivo
            status_map = {
                '0': 'Nuevo',
                '1': 'En Proceso',
                '2': 'Parcial',
                '9': 'Completado',
                'X': 'Cancelado'
            }
            summary['status_desc'] = status_map.get(summary['status'], 'Desconocido')

            return summary

        except Exception as e:
            logger.error(f"Error obteniendo resumen de ASN {asn_number}: {e}")
            return {
                'found': False,
                'asn_number': asn_number,
                'error': str(e)
            }

    def get_asn_detail(self, asn_number: str) -> pd.DataFrame:
        """
        Obtiene el detalle de SKUs de un ASN

        Args:
            asn_number: Numero de ASN

        Returns:
            DataFrame con detalle de SKUs
        """
        return self.find_by_asn_number(asn_number)

    def get_asns_for_oc(self, oc_number: str) -> pd.DataFrame:
        """
        Obtiene los ASNs relacionados a una OC

        Args:
            oc_number: Numero de OC

        Returns:
            DataFrame con ASNs relacionados
        """
        try:
            conn = self._ensure_connected()

            if not oc_number.startswith('C'):
                oc_number = f'C{oc_number}'

            # Buscar ASNs que mencionen la OC en algun campo
            query = """
                SELECT
                    A.ASNKEY,
                    A.EXTERNRECEIPTKEY,
                    A.STORERKEY,
                    A.STATUS,
                    A.EXPECTEDRECEIPTDATE,
                    COUNT(DISTINCT D.SKU) AS TOTAL_SKUS,
                    SUM(D.EXPECTEDQTY) AS TOTAL_QTY
                FROM {schema}.ASN A
                LEFT JOIN {schema}.ASNDETAIL D ON A.ASNKEY = D.ASNKEY
                WHERE A.EXTERNRECEIPTKEY LIKE ?
                   OR A.POKEY LIKE ?
                GROUP BY A.ASNKEY, A.EXTERNRECEIPTKEY, A.STORERKEY,
                         A.STATUS, A.EXPECTEDRECEIPTDATE
                ORDER BY A.ASNKEY
            """.format(schema=self.SCHEMA)

            like_pattern = f'%{oc_number}%'
            df = conn.execute_query(query, (like_pattern, like_pattern))
            return df

        except Exception as e:
            logger.error(f"Error obteniendo ASNs para OC {oc_number}: {e}")
            raise RepositoryError(f"Error obteniendo ASNs para OC: {e}")

    def get_daily_asns(self, date: Optional[datetime] = None) -> pd.DataFrame:
        """
        Obtiene los ASNs del dia

        Args:
            date: Fecha (default: hoy)

        Returns:
            DataFrame con ASNs del dia
        """
        if date is None:
            date = datetime.now()

        try:
            conn = self._ensure_connected()

            query = """
                SELECT
                    A.ASNKEY,
                    A.EXTERNRECEIPTKEY,
                    A.STORERKEY,
                    A.STATUS,
                    A.EXPECTEDRECEIPTDATE,
                    COUNT(DISTINCT D.SKU) AS TOTAL_SKUS,
                    SUM(D.EXPECTEDQTY) AS TOTAL_QTY
                FROM {schema}.ASN A
                LEFT JOIN {schema}.ASNDETAIL D ON A.ASNKEY = D.ASNKEY
                WHERE DATE(A.ADDDATE) = ?
                GROUP BY A.ASNKEY, A.EXTERNRECEIPTKEY, A.STORERKEY,
                         A.STATUS, A.EXPECTEDRECEIPTDATE
                ORDER BY A.ASNKEY
            """.format(schema=self.SCHEMA)

            df = conn.execute_query(query, (date.strftime('%Y-%m-%d'),))
            return df

        except Exception as e:
            logger.error(f"Error obteniendo ASNs del dia: {e}")
            raise RepositoryError(f"Error obteniendo ASNs del dia: {e}")

    def get_reception_status(self, asn_number: str) -> Dict[str, Any]:
        """
        Obtiene el estado de recepcion de un ASN

        Args:
            asn_number: Numero de ASN

        Returns:
            Dict con estado de recepcion
        """
        summary = self.get_asn_summary(asn_number)

        if not summary.get('found'):
            return summary

        # Agregar analisis de recepcion
        if summary['reception_pct'] == 0:
            summary['reception_status'] = 'Sin iniciar'
            summary['reception_alert'] = 'warning'
        elif summary['reception_pct'] < 100:
            summary['reception_status'] = 'En proceso'
            summary['reception_alert'] = 'info'
        else:
            summary['reception_status'] = 'Completado'
            summary['reception_alert'] = 'success'

        return summary


# ===============================================================
# EXPORTAR
# ===============================================================

__all__ = ['ASNRepository']
