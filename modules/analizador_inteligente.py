"""
═══════════════════════════════════════════════════════════════
ANALIZADOR INTELIGENTE DE DATOS
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Módulo para análisis inteligente de OCs, distribuciones y
detección de patrones usando modelos de lenguaje.

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
═══════════════════════════════════════════════════════════════
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


@dataclass
class AnálisisOC:
    """Resultado del análisis de una OC"""
    oc_numero: str
    resumen_ejecutivo: str
    riesgos_identificados: List[Dict[str, str]]
    oportunidades: List[Dict[str, str]]
    recomendaciones: List[str]
    puntuacion_salud: float  # 0.0 a 1.0
    es_critica: bool
    timestamp: datetime


@dataclass
class AnálisisDistribución:
    """Resultado del análisis de distribuciones"""
    oc_numero: str
    total_tiendas: int
    distribucion_equitativa: bool
    anomalias_detectadas: List[str]
    tiendas_riesgo: List[str]
    recomendaciones: List[str]
    timestamp: datetime


class AnalizadorInteligente:
    """Analizador inteligente de datos SAC"""

    def __init__(self, cliente_llm=None):
        """
        Inicializa el analizador

        Args:
            cliente_llm: Cliente LLM (IntegradorLLM)
        """
        self.cliente_llm = cliente_llm
        self.historial_analisis = []

    def analizar_oc_completa(
        self,
        df_oc: pd.DataFrame,
        df_distro: Optional[pd.DataFrame] = None
    ) -> AnálisisOC:
        """
        Realiza análisis inteligente completo de una OC

        Args:
            df_oc: DataFrame con datos de OC
            df_distro: DataFrame con distribuciones (opcional)

        Returns:
            AnálisisOC: Análisis inteligente
        """
        if df_oc.empty:
            raise ValueError("DataFrame OC está vacío")

        # Extraer información
        oc_numero = df_oc.iloc[0].get('OC', 'DESCONOCIDA')

        # Análisis numérico básico
        analisis_numerico = self._analizar_numerico(df_oc)

        # Análisis de distribuciones
        analisis_distro = {}
        if df_distro is not None and not df_distro.empty:
            analisis_distro = self._analizar_distribucion_calidad(df_distro)

        # Preparar datos para LLM
        datos_para_llm = self._preparar_datos_para_analisis(df_oc, analisis_numerico, analisis_distro)

        # Obtener análisis del LLM
        riesgos = []
        oportunidades = []
        recomendaciones = []
        resumen = "Análisis no disponible (LLM no configurado)"
        puntuacion = 0.5

        if self.cliente_llm:
            try:
                # Análisis de riesgos
                respuesta_riesgos = self.cliente_llm.consultar_analisis(
                    datos_para_llm,
                    tipo_analisis="riesgos"
                )
                riesgos = self._parsear_riesgos(respuesta_riesgos.contenido)

                # Recomendaciones
                recomendaciones = self.cliente_llm.consultar_recomendaciones(datos_para_llm)

                # Resumen
                resumen = self.cliente_llm.consultar_resumen(datos_para_llm, max_palabras=300)

                # Calcular puntuación de salud
                puntuacion = self._calcular_puntuacion_salud(
                    analisis_numerico,
                    len(riesgos),
                    analisis_distro
                )

            except Exception as e:
                logger.warning(f"⚠️  Error en análisis LLM: {e}")

        es_critica = any(r.get('severidad') == 'CRÍTICA' for r in riesgos)

        analisis = AnálisisOC(
            oc_numero=str(oc_numero),
            resumen_ejecutivo=resumen,
            riesgos_identificados=riesgos,
            oportunidades=oportunidades,
            recomendaciones=recomendaciones,
            puntuacion_salud=puntuacion,
            es_critica=es_critica,
            timestamp=datetime.now()
        )

        self.historial_analisis.append(analisis)
        logger.info(f"✅ Análisis completado: OC {oc_numero} (Salud: {puntuacion:.2f})")

        return analisis

    def analizar_distribucion_inteligente(
        self,
        df_distro: pd.DataFrame,
        oc_numero: str = ""
    ) -> AnálisisDistribución:
        """
        Análisis inteligente de distribuciones

        Args:
            df_distro: DataFrame con distribuciones
            oc_numero: Número de OC para contexto

        Returns:
            AnálisisDistribución: Análisis inteligente
        """
        if df_distro.empty:
            raise ValueError("DataFrame distribución está vacío")

        # Análisis básicos
        total_tiendas = df_distro['TIENDA'].nunique() if 'TIENDA' in df_distro.columns else 0
        total_cantidad = df_distro['CANTIDAD'].sum() if 'CANTIDAD' in df_distro.columns else 0

        # Detectar equidad
        distribucion_equitativa = self._validar_equidad_distribucion(df_distro)

        # Detectar anomalías
        anomalias = self._detectar_anomalias_distribucion(df_distro)

        # Identificar tiendas en riesgo
        tiendas_riesgo = self._identificar_tiendas_riesgo(df_distro)

        # Recomendaciones del LLM
        recomendaciones = []
        if self.cliente_llm:
            try:
                datos = self._formatear_distribucion_para_llm(df_distro, total_tiendas)
                recomendaciones = self.cliente_llm.consultar_recomendaciones(
                    datos,
                    contexto=f"Distribución de OC {oc_numero}"
                )
            except Exception as e:
                logger.warning(f"⚠️  Error en recomendaciones LLM: {e}")

        analisis = AnálisisDistribución(
            oc_numero=str(oc_numero),
            total_tiendas=total_tiendas,
            distribucion_equitativa=distribucion_equitativa,
            anomalias_detectadas=anomalias,
            tiendas_riesgo=tiendas_riesgo,
            recomendaciones=recomendaciones,
            timestamp=datetime.now()
        )

        logger.info(f"✅ Análisis distribución: {total_tiendas} tiendas, {len(anomalias)} anomalías")

        return analisis

    def detectar_anomalias_inteligentes(
        self,
        df_datos: pd.DataFrame,
        tipo_dato: str = "general"
    ) -> Dict[str, Any]:
        """
        Detecta anomalías usando LLM

        Args:
            df_datos: DataFrame con datos
            tipo_dato: Tipo de datos (oc, distribucion, general)

        Returns:
            Dict con anomalías detectadas
        """
        if df_datos.empty:
            logger.warning("⚠️  DataFrame vacío para análisis de anomalías")
            return {"anomalias": [], "es_normal": True, "confianza": 1.0}

        # Preparar descripción de datos
        descripcion = self._describir_dataframe(df_datos, tipo_dato)

        if not self.cliente_llm:
            logger.warning("⚠️  LLM no configurado, usando detección estadística")
            return self._detectar_anomalias_estadistica(df_datos)

        try:
            patrones_normales = self._describir_patrones_normales(tipo_dato)
            resultado = self.cliente_llm.consultar_deteccion_anomalias(
                descripcion,
                patrones_normales
            )
            logger.info(f"✅ Detección de anomalías completada")
            return resultado

        except Exception as e:
            logger.warning(f"⚠️  Error en detección LLM: {e}")
            return self._detectar_anomalias_estadistica(df_datos)

    def clasificar_ordenes(
        self,
        df_oc: pd.DataFrame
    ) -> Dict[str, List[str]]:
        """
        Clasifica órdenes por categorías inteligentes

        Args:
            df_oc: DataFrame con órdenes

        Returns:
            Dict: Órdenes clasificadas por categoría
        """
        clasificadas = {
            "CRÍTICAS": [],
            "ALTO_RIESGO": [],
            "NORMAL": [],
            "BAJO_RIESGO": []
        }

        if df_oc.empty or not self.cliente_llm:
            return clasificadas

        categorias = list(clasificadas.keys())

        for idx, row in df_oc.iterrows():
            try:
                # Descripción de la orden
                desc_orden = f"""
OC: {row.get('OC', 'N/A')}
Cantidad: {row.get('CANTIDAD', 0)}
Vigencia: {row.get('VIGENCIA', 'N/A')}
Tiendas: {row.get('TIENDAS', 0)}
"""
                categoria, confianza = self.cliente_llm.consultar_clasificacion(
                    desc_orden,
                    categorias
                )

                if confianza > 0.6:
                    clasificadas[categoria].append(str(row.get('OC', 'DESCONOCIDA')))

            except Exception as e:
                logger.debug(f"⚠️  Error clasificando orden: {e}")
                clasificadas["NORMAL"].append(str(row.get('OC', 'DESCONOCIDA')))

        logger.info(f"✅ Clasificación completada: {sum(len(v) for v in clasificadas.values())} órdenes")

        return clasificadas

    def generar_insights(
        self,
        df_oc: pd.DataFrame,
        df_distro: Optional[pd.DataFrame] = None
    ) -> List[str]:
        """
        Genera insights inteligentes de los datos

        Args:
            df_oc: DataFrame de OCs
            df_distro: DataFrame de distribuciones (opcional)

        Returns:
            List: Lista de insights
        """
        insights = []

        if df_oc.empty or not self.cliente_llm:
            return insights

        try:
            # Compilar datos
            datos = self._compilar_datos_para_insights(df_oc, df_distro)

            # Solicitar insights
            prompt = f"""
Basándote en los siguientes datos de órdenes de compra, genera 5 insights principales
que podrían ser de interés para analistas de planning:

{datos}

Formato: Lista de insights, cada uno conciso y accionable.
"""

            respuesta = self.cliente_llm.cliente.consultar(prompt, temperatura=0.7, max_tokens=1000)
            insights = [i.strip() for i in respuesta.contenido.split('\n') if i.strip() and i.startswith('-')]

            logger.info(f"✅ {len(insights)} insights generados")

        except Exception as e:
            logger.warning(f"⚠️  Error generando insights: {e}")

        return insights

    # ═══════════════════════════════════════════════════════════════
    # MÉTODOS AUXILIARES PRIVADOS
    # ═══════════════════════════════════════════════════════════════

    def _analizar_numerico(self, df_oc: pd.DataFrame) -> Dict[str, Any]:
        """Análisis numérico básico"""
        return {
            "total_oc": df_oc['CANTIDAD'].sum() if 'CANTIDAD' in df_oc.columns else 0,
            "cantidad_promedio": df_oc['CANTIDAD'].mean() if 'CANTIDAD' in df_oc.columns else 0,
            "cantidad_min": df_oc['CANTIDAD'].min() if 'CANTIDAD' in df_oc.columns else 0,
            "cantidad_max": df_oc['CANTIDAD'].max() if 'CANTIDAD' in df_oc.columns else 0,
            "desviacion_std": df_oc['CANTIDAD'].std() if 'CANTIDAD' in df_oc.columns else 0,
        }

    def _analizar_distribucion_calidad(self, df_distro: pd.DataFrame) -> Dict[str, Any]:
        """Analiza calidad de distribuciones"""
        return {
            "total_tiendas": df_distro['TIENDA'].nunique() if 'TIENDA' in df_distro.columns else 0,
            "coeficiente_variacion": (df_distro['CANTIDAD'].std() / df_distro['CANTIDAD'].mean()
                                      if 'CANTIDAD' in df_distro.columns and df_distro['CANTIDAD'].mean() > 0
                                      else 0),
        }

    def _validar_equidad_distribucion(self, df_distro: pd.DataFrame) -> bool:
        """Valida si distribución es equitativa"""
        if 'CANTIDAD' not in df_distro.columns or df_distro.empty:
            return True

        std = df_distro['CANTIDAD'].std()
        media = df_distro['CANTIDAD'].mean()

        if media == 0:
            return True

        coef_variacion = std / media
        return coef_variacion < 0.5  # Menos del 50% de variación

    def _detectar_anomalias_distribucion(self, df_distro: pd.DataFrame) -> List[str]:
        """Detecta anomalías en distribuciones"""
        anomalias = []

        if 'CANTIDAD' not in df_distro.columns:
            return anomalias

        cantidad = df_distro['CANTIDAD']
        media = cantidad.mean()
        std = cantidad.std()

        # Detectar valores outliers (> 2 desviaciones estándar)
        outliers = cantidad[abs(cantidad - media) > 2 * std]

        if not outliers.empty:
            anomalias.append(f"Detectadas {len(outliers)} distribuciones inusualmentegrandes")

        return anomalias

    def _identificar_tiendas_riesgo(self, df_distro: pd.DataFrame) -> List[str]:
        """Identifica tiendas con riesgo de falta o exceso"""
        tiendas_riesgo = []

        if 'TIENDA' not in df_distro.columns or 'CANTIDAD' not in df_distro.columns:
            return tiendas_riesgo

        # Tiendas con cantidad muy baja
        minima = df_distro['CANTIDAD'].quantile(0.25)
        tiendas_bajas = df_distro[df_distro['CANTIDAD'] < minima]['TIENDA'].unique()

        tiendas_riesgo.extend([f"{t} (baja cantidad)" for t in tiendas_bajas[:5]])

        return tiendas_riesgo

    def _calcular_puntuacion_salud(
        self,
        analisis_numerico: Dict,
        num_riesgos: int,
        analisis_distro: Dict
    ) -> float:
        """Calcula puntuación de salud de OC"""
        puntuacion = 1.0

        # Reducir por riesgos
        puntuacion -= min(0.1 * num_riesgos, 0.5)

        # Reducir por variación en distribución
        coef_var = analisis_distro.get('coeficiente_variacion', 0)
        if coef_var > 0.5:
            puntuacion -= 0.2
        elif coef_var > 0.3:
            puntuacion -= 0.1

        return max(0.0, min(1.0, puntuacion))

    def _parsear_riesgos(self, contenido: str) -> List[Dict[str, str]]:
        """Parsea riesgos del contenido LLM"""
        riesgos = []
        try:
            lineas = contenido.split('\n')
            for linea in lineas:
                if any(sev in linea.upper() for sev in ['CRÍTICA', 'ALTA', 'MEDIA', 'BAJA']):
                    riesgos.append({"descripcion": linea.strip(), "severidad": "MEDIA"})
        except:
            pass

        return riesgos

    def _preparar_datos_para_analisis(
        self,
        df_oc: pd.DataFrame,
        analisis_numerico: Dict,
        analisis_distro: Dict
    ) -> str:
        """Prepara datos para análisis LLM"""
        return f"""
ORDEN DE COMPRA (OC):
- Cantidad total: {analisis_numerico['total_oc']:,.0f}
- Cantidad promedio: {analisis_numerico['cantidad_promedio']:,.0f}
- Rango: {analisis_numerico['cantidad_min']:,.0f} - {analisis_numerico['cantidad_max']:,.0f}
- Desviación estándar: {analisis_numerico['desviacion_std']:,.0f}

DISTRIBUCIONES:
- Total de tiendas: {analisis_distro.get('total_tiendas', 'N/A')}
- Coeficiente de variación: {analisis_distro.get('coeficiente_variacion', 'N/A'):.2%}

DATOS ADICIONALES:
{df_oc.to_string(max_rows=10)}
"""

    def _describir_dataframe(self, df: pd.DataFrame, tipo: str) -> str:
        """Describe un DataFrame para análisis"""
        desc = f"DataFrame tipo '{tipo}':\n"
        desc += f"- Filas: {len(df)}\n"
        desc += f"- Columnas: {', '.join(df.columns.tolist())}\n"
        desc += f"\n{df.describe().to_string()}\n"
        return desc

    def _describir_patrones_normales(self, tipo_dato: str) -> str:
        """Describe patrones normales por tipo"""
        patrones = {
            "oc": "OCs normales tienen distribuciones relativamente equitativas entre tiendas",
            "distribucion": "Distribuciones normales varían menos del 50% entre tiendas",
            "general": "Sin patrones específicos"
        }
        return patrones.get(tipo_dato, patrones["general"])

    def _detectar_anomalias_estadistica(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detección de anomalías usando métodos estadísticos"""
        anomalias = []

        for columna in df.select_dtypes(include=[np.number]).columns:
            serie = df[columna]
            media = serie.mean()
            std = serie.std()

            outliers = serie[abs(serie - media) > 3 * std]

            if not outliers.empty:
                anomalias.append({
                    "tipo": f"Outliers en {columna}",
                    "severidad": "MEDIA",
                    "descripcion": f"{len(outliers)} valores anómalos detectados"
                })

        return {
            "anomalias_detectadas": anomalias,
            "es_normal": len(anomalias) == 0,
            "confianza": 0.7
        }

    def _formatear_distribucion_para_llm(self, df_distro: pd.DataFrame, total_tiendas: int) -> str:
        """Formatea distribuciones para análisis LLM"""
        return f"""
DISTRIBUCIÓN:
- Total de tiendas: {total_tiendas}
- Total de cantidad distribuida: {df_distro['CANTIDAD'].sum():,.0f}
- Cantidad por tienda (promedio): {df_distro['CANTIDAD'].mean():,.0f}
- Variación: {df_distro['CANTIDAD'].std()/df_distro['CANTIDAD'].mean():.1%}

Primeras 10 tiendas:
{df_distro.head(10).to_string()}
"""

    def _compilar_datos_para_insights(
        self,
        df_oc: pd.DataFrame,
        df_distro: Optional[pd.DataFrame]
    ) -> str:
        """Compila datos para generación de insights"""
        datos = f"OCs procesadas: {len(df_oc)}\n"

        if 'CANTIDAD' in df_oc.columns:
            datos += f"Cantidad total: {df_oc['CANTIDAD'].sum():,.0f}\n"

        if df_distro is not None and not df_distro.empty:
            datos += f"Tiendas alcanzadas: {df_distro['TIENDA'].nunique()}\n"

        datos += f"\nResumen de datos:\n{df_oc.describe().to_string()}"

        return datos
