"""
═══════════════════════════════════════════════════════════════
API DE TIPO DE CAMBIO
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Proporciona información sobre tipos de cambio:
- MXN/USD actual e histórico
- MXN/EUR
- Variaciones diarias

Fuentes:
- Frankfurter API (gratuita, basada en BCE)
- Datos de respaldo en caso de fallo

Útil para:
- Cálculo de costos de importación
- Reportes financieros
- Análisis de variaciones

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════
"""

import logging
import urllib.request
import urllib.error
import json
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional

from ..base import BaseAPIClient, APIResponse, APIError, APIStatus, with_retry

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# CONSTANTES
# ═══════════════════════════════════════════════════════════════

# URLs de APIs gratuitas
FRANKFURTER_BASE_URL = "https://api.frankfurter.app"
EXCHANGERATE_BASE_URL = "https://open.er-api.com/v6"

# Tipos de cambio de respaldo (actualizados manualmente como fallback)
TIPOS_CAMBIO_FALLBACK = {
    'USD': 17.50,
    'EUR': 19.00,
}


# ═══════════════════════════════════════════════════════════════
# CLASES DE DATOS
# ═══════════════════════════════════════════════════════════════

@dataclass
class TipoCambio:
    """Información de tipo de cambio"""
    moneda_origen: str
    moneda_destino: str
    tasa: float
    fecha: date
    fuente: str = "frankfurter"
    variacion_diaria: Optional[float] = None
    variacion_porcentaje: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        return {
            'moneda_origen': self.moneda_origen,
            'moneda_destino': self.moneda_destino,
            'tasa': self.tasa,
            'fecha': self.fecha.isoformat(),
            'fuente': self.fuente,
            'variacion_diaria': self.variacion_diaria,
            'variacion_porcentaje': self.variacion_porcentaje,
            'timestamp': self.timestamp.isoformat(),
        }

    def __str__(self) -> str:
        return f"1 {self.moneda_origen} = {self.tasa:.4f} {self.moneda_destino}"


# ═══════════════════════════════════════════════════════════════
# CLASE PRINCIPAL
# ═══════════════════════════════════════════════════════════════

class ExchangeRateAPI(BaseAPIClient):
    """
    API de Tipo de Cambio.

    Proporciona tipos de cambio actuales e históricos
    usando APIs públicas gratuitas.
    """

    API_NAME = "ExchangeRateAPI"
    API_VERSION = "1.0"
    API_DESCRIPTION = "Tipo de cambio MXN/USD/EUR desde fuentes públicas"

    def __init__(
        self,
        moneda_base: str = "MXN",
        timeout_seconds: int = 10,
        **kwargs
    ):
        """
        Inicializa la API de tipo de cambio.

        Args:
            moneda_base: Moneda base (default MXN)
            timeout_seconds: Timeout para requests
        """
        super().__init__(
            cache_ttl_seconds=3600,  # Cache 1 hora
            timeout_seconds=timeout_seconds,
            **kwargs
        )
        self._moneda_base = moneda_base.upper()
        self._ultima_actualizacion: Optional[datetime] = None

    def _hacer_request(self, url: str) -> Dict:
        """
        Realiza una request HTTP GET.

        Args:
            url: URL a consultar

        Returns:
            Dict con la respuesta JSON
        """
        try:
            req = urllib.request.Request(
                url,
                headers={'User-Agent': 'SAC-CEDIS/1.0'}
            )
            with urllib.request.urlopen(req, timeout=self._timeout) as response:
                return json.loads(response.read().decode())
        except urllib.error.URLError as e:
            logger.error(f"❌ Error de conexión: {e}")
            raise APIError(
                codigo="CONNECTION_ERROR",
                mensaje=f"Error conectando a API: {e}",
                api_nombre=self.API_NAME,
            )
        except json.JSONDecodeError as e:
            logger.error(f"❌ Error parseando JSON: {e}")
            raise APIError(
                codigo="PARSE_ERROR",
                mensaje="Respuesta inválida de API",
                api_nombre=self.API_NAME,
            )

    @with_retry(max_retries=2)
    def _obtener_tasa_frankfurter(
        self,
        moneda_origen: str,
        moneda_destino: str,
        fecha: Optional[date] = None
    ) -> TipoCambio:
        """
        Obtiene tipo de cambio desde Frankfurter API.

        Args:
            moneda_origen: Moneda de origen
            moneda_destino: Moneda de destino
            fecha: Fecha opcional (None = actual)

        Returns:
            TipoCambio
        """
        import time
        start_time = time.time()

        if fecha:
            url = f"{FRANKFURTER_BASE_URL}/{fecha.isoformat()}"
        else:
            url = f"{FRANKFURTER_BASE_URL}/latest"

        url += f"?from={moneda_origen}&to={moneda_destino}"

        try:
            data = self._hacer_request(url)

            tasa = data.get('rates', {}).get(moneda_destino)
            if tasa is None:
                raise APIError(
                    codigo="NO_RATE",
                    mensaje=f"No se encontró tasa para {moneda_destino}",
                    api_nombre=self.API_NAME,
                )

            fecha_resp = datetime.strptime(data.get('date', ''), '%Y-%m-%d').date()

            response_time = (time.time() - start_time) * 1000
            self._record_request(True, response_time)

            return TipoCambio(
                moneda_origen=moneda_origen,
                moneda_destino=moneda_destino,
                tasa=float(tasa),
                fecha=fecha_resp,
                fuente="frankfurter",
            )

        except APIError:
            raise
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self._record_request(False, response_time, str(e))
            raise APIError(
                codigo="API_ERROR",
                mensaje=str(e),
                api_nombre=self.API_NAME,
            )

    def _obtener_tasa_fallback(
        self,
        moneda_origen: str,
        moneda_destino: str
    ) -> TipoCambio:
        """
        Obtiene tipo de cambio desde datos de respaldo.

        Args:
            moneda_origen: Moneda de origen
            moneda_destino: Moneda de destino

        Returns:
            TipoCambio con datos de fallback
        """
        logger.warning(f"⚠️  Usando tipo de cambio de respaldo para {moneda_destino}")

        # Si origen es MXN, retornar tasa directa
        if moneda_origen == "MXN":
            tasa = 1 / TIPOS_CAMBIO_FALLBACK.get(moneda_destino, 1)
        elif moneda_destino == "MXN":
            tasa = TIPOS_CAMBIO_FALLBACK.get(moneda_origen, 17.50)
        else:
            # Conversión cruzada via MXN
            tasa_origen = TIPOS_CAMBIO_FALLBACK.get(moneda_origen, 1)
            tasa_destino = TIPOS_CAMBIO_FALLBACK.get(moneda_destino, 1)
            tasa = tasa_origen / tasa_destino

        return TipoCambio(
            moneda_origen=moneda_origen,
            moneda_destino=moneda_destino,
            tasa=tasa,
            fecha=date.today(),
            fuente="fallback",
        )

    # ═══════════════════════════════════════════════════════════
    # MÉTODOS PRINCIPALES
    # ═══════════════════════════════════════════════════════════

    def obtener_tipo_cambio(
        self,
        moneda_destino: str = "USD",
        moneda_origen: Optional[str] = None,
        fecha: Optional[date] = None,
        usar_fallback: bool = True
    ) -> TipoCambio:
        """
        Obtiene el tipo de cambio actual o histórico.

        Args:
            moneda_destino: Moneda a convertir
            moneda_origen: Moneda base (default: configurada)
            fecha: Fecha para histórico
            usar_fallback: Usar datos de respaldo si falla API

        Returns:
            TipoCambio
        """
        moneda_origen = moneda_origen or self._moneda_base
        moneda_destino = moneda_destino.upper()
        moneda_origen = moneda_origen.upper()

        # Verificar cache
        cache_key = f"{moneda_origen}_{moneda_destino}_{fecha or 'latest'}"
        cached = self._get_from_cache(cache_key)
        if cached:
            self._metrics.cache_hits += 1
            return cached

        self._metrics.cache_misses += 1

        try:
            tipo_cambio = self._obtener_tasa_frankfurter(
                moneda_origen, moneda_destino, fecha
            )

            # Calcular variación diaria si es tasa actual
            if not fecha:
                try:
                    ayer = date.today() - timedelta(days=1)
                    tipo_ayer = self._obtener_tasa_frankfurter(
                        moneda_origen, moneda_destino, ayer
                    )
                    tipo_cambio.variacion_diaria = tipo_cambio.tasa - tipo_ayer.tasa
                    tipo_cambio.variacion_porcentaje = (
                        (tipo_cambio.variacion_diaria / tipo_ayer.tasa) * 100
                    )
                except Exception:
                    pass  # Ignorar si falla obtener variación

            self._set_cache(cache_key, tipo_cambio)
            self._ultima_actualizacion = datetime.now()
            return tipo_cambio

        except APIError as e:
            if usar_fallback:
                return self._obtener_tasa_fallback(moneda_origen, moneda_destino)
            raise

    def obtener_usd_mxn(self) -> TipoCambio:
        """Atajo para obtener USD/MXN"""
        return self.obtener_tipo_cambio("MXN", "USD")

    def obtener_mxn_usd(self) -> TipoCambio:
        """Atajo para obtener MXN/USD"""
        return self.obtener_tipo_cambio("USD", "MXN")

    def convertir(
        self,
        cantidad: float,
        moneda_origen: str,
        moneda_destino: str
    ) -> float:
        """
        Convierte una cantidad entre monedas.

        Args:
            cantidad: Cantidad a convertir
            moneda_origen: Moneda de origen
            moneda_destino: Moneda de destino

        Returns:
            Cantidad convertida
        """
        tipo_cambio = self.obtener_tipo_cambio(moneda_destino, moneda_origen)
        return cantidad * tipo_cambio.tasa

    def obtener_historico(
        self,
        moneda_destino: str = "USD",
        dias: int = 30,
        moneda_origen: Optional[str] = None
    ) -> List[TipoCambio]:
        """
        Obtiene el histórico de tipos de cambio.

        Args:
            moneda_destino: Moneda destino
            dias: Número de días hacia atrás
            moneda_origen: Moneda origen

        Returns:
            Lista de TipoCambio
        """
        moneda_origen = moneda_origen or self._moneda_base
        resultados = []

        for i in range(dias):
            fecha = date.today() - timedelta(days=i)
            # Solo días hábiles (aproximado)
            if fecha.weekday() < 5:
                try:
                    tc = self.obtener_tipo_cambio(
                        moneda_destino,
                        moneda_origen,
                        fecha,
                        usar_fallback=False
                    )
                    resultados.append(tc)
                except APIError:
                    continue

        return sorted(resultados, key=lambda x: x.fecha)

    def obtener_resumen(self) -> Dict:
        """
        Obtiene un resumen de tipos de cambio principales.

        Returns:
            Dict con resumen
        """
        resultado = {
            'fecha': date.today().isoformat(),
            'moneda_base': self._moneda_base,
            'tipos_cambio': {},
            'ultima_actualizacion': (
                self._ultima_actualizacion.isoformat()
                if self._ultima_actualizacion else None
            ),
        }

        for moneda in ['USD', 'EUR']:
            try:
                tc = self.obtener_tipo_cambio(moneda)
                resultado['tipos_cambio'][moneda] = tc.to_dict()
            except APIError as e:
                resultado['tipos_cambio'][moneda] = {'error': str(e)}

        return resultado

    # ═══════════════════════════════════════════════════════════
    # MÉTODOS DE BaseAPIClient
    # ═══════════════════════════════════════════════════════════

    def health_check(self) -> bool:
        """Verifica que la API funcione correctamente"""
        try:
            tc = self.obtener_tipo_cambio("USD", usar_fallback=False)
            return tc is not None and tc.tasa > 0
        except Exception as e:
            logger.warning(f"⚠️  Health check con fallback: {e}")
            # Aún consideramos healthy si el fallback funciona
            try:
                tc = self._obtener_tasa_fallback("MXN", "USD")
                self.set_status(APIStatus.LIMITADA)
                return True
            except Exception:
                return False

    def get_info(self) -> Dict:
        """Obtiene información de la API"""
        return {
            'nombre': self.API_NAME,
            'version': self.API_VERSION,
            'descripcion': self.API_DESCRIPTION,
            'moneda_base': self._moneda_base,
            'fuentes': ['Frankfurter (BCE)', 'Fallback local'],
            'ultima_actualizacion': (
                self._ultima_actualizacion.isoformat()
                if self._ultima_actualizacion else None
            ),
            'monedas_soportadas': ['USD', 'EUR', 'GBP', 'CAD', 'JPY'],
        }
