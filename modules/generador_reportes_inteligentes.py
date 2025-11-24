"""
═══════════════════════════════════════════════════════════════
GENERADOR DE REPORTES INTELIGENTES
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Módulo para generación inteligente de reportes con análisis,
recomendaciones y insights automáticos usando LLMs.

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
═══════════════════════════════════════════════════════════════
"""

import logging
import pandas as pd
from typing import Optional, Dict, List, Any
from datetime import datetime
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)


@dataclass
class ReporteInteligente:
    """Estructura de un reporte inteligente"""
    titulo: str
    fecha_generacion: datetime
    periodo: str
    resumen_ejecutivo: str
    datos_principales: Dict[str, Any]
    analisis_llm: str
    recomendaciones: List[str]
    alertas_criticas: List[str]
    metricas_clave: Dict[str, float]
    proximos_pasos: List[str]
    confianza: float  # Confianza del análisis LLM


class GeneradorReportesInteligentes:
    """Generador de reportes inteligentes con análisis LLM"""

    def __init__(self, cliente_llm=None, generador_excel=None):
        """
        Inicializa el generador

        Args:
            cliente_llm: Cliente LLM (IntegradorLLM)
            generador_excel: Generador de reportes Excel
        """
        self.cliente_llm = cliente_llm
        self.generador_excel = generador_excel
        self.historial_reportes = []

    def generar_reporte_planning_inteligente(
        self,
        df_oc: pd.DataFrame,
        df_distro: Optional[pd.DataFrame] = None,
        periodo: str = "Diario"
    ) -> ReporteInteligente:
        """
        Genera reporte inteligente de planning

        Args:
            df_oc: DataFrame con OCs
            df_distro: DataFrame con distribuciones
            periodo: Periodo del reporte

        Returns:
            ReporteInteligente: Reporte generado
        """
        logger.info(f"📊 Generando reporte inteligente {periodo}...")

        # Compilar datos
        datos_principales = self._compilar_datos_principales(df_oc, df_distro)

        # Calcular métricas
        metricas = self._calcular_metricas_clave(df_oc, df_distro)

        # Análisis LLM
        analisis_llm = ""
        recomendaciones = []
        alertas = []
        confianza = 0.5

        if self.cliente_llm:
            try:
                # Análisis general
                analisis_llm = self._generar_analisis_general(datos_principales)

                # Recomendaciones
                recomendaciones = self._generar_recomendaciones(datos_principales)

                # Alertas críticas
                alertas = self._generar_alertas(datos_principales)

                confianza = 0.9

            except Exception as e:
                logger.warning(f"⚠️  Error en análisis LLM: {e}")
                confianza = 0.5

        # Próximos pasos
        proximos_pasos = self._generar_proximos_pasos(recomendaciones)

        reporte = ReporteInteligente(
            titulo=f"Reporte de Planning - {periodo}",
            fecha_generacion=datetime.now(),
            periodo=periodo,
            resumen_ejecutivo=self._generar_resumen_ejecutivo(datos_principales),
            datos_principales=datos_principales,
            analisis_llm=analisis_llm,
            recomendaciones=recomendaciones,
            alertas_criticas=alertas,
            metricas_clave=metricas,
            proximos_pasos=proximos_pasos,
            confianza=confianza
        )

        self.historial_reportes.append(reporte)
        logger.info(f"✅ Reporte generado exitosamente")

        return reporte

    def generar_reporte_anomalias_inteligente(
        self,
        df_datos: pd.DataFrame,
        anomalias_detectadas: List[Dict]
    ) -> ReporteInteligente:
        """
        Genera reporte inteligente de anomalías

        Args:
            df_datos: DataFrame con datos
            anomalias_detectadas: Anomalías encontradas

        Returns:
            ReporteInteligente: Reporte de anomalías
        """
        logger.info("🚨 Generando reporte de anomalías inteligente...")

        datos_principales = {
            "total_registros": len(df_datos),
            "anomalias_detectadas": len(anomalias_detectadas),
            "severidad_distribucion": self._analizar_severidad(anomalias_detectadas),
            "anomalias": anomalias_detectadas[:10]  # Primeras 10
        }

        metricas = {
            "porcentaje_anomalias": (len(anomalias_detectadas) / len(df_datos) * 100)
            if len(df_datos) > 0 else 0,
            "anomalias_criticas": sum(1 for a in anomalias_detectadas
                                       if a.get('severidad') == 'CRÍTICA'),
            "anomalias_altas": sum(1 for a in anomalias_detectadas
                                    if a.get('severidad') == 'ALTA'),
        }

        analisis_llm = ""
        recomendaciones = []
        alertas = []

        if self.cliente_llm:
            try:
                # Análisis de anomalías
                datos_para_llm = json.dumps(datos_principales, indent=2)
                respuesta = self.cliente_llm.cliente.consultar(
                    f"Analiza estas anomalías y proporciona recomendaciones:\n{datos_para_llm}",
                    temperatura=0.6
                )
                analisis_llm = respuesta.contenido

                # Recomendaciones
                recomendaciones = self.cliente_llm.consultar_recomendaciones(
                    datos_para_llm,
                    contexto="Detección de anomalías"
                )

                # Alertas
                alertas = [f"⚠️  {a['descripcion']}" for a in anomalias_detectadas
                          if a.get('severidad') == 'CRÍTICA']

            except Exception as e:
                logger.warning(f"⚠️  Error en análisis LLM de anomalías: {e}")

        reporte = ReporteInteligente(
            titulo="Reporte de Anomalías Detectadas",
            fecha_generacion=datetime.now(),
            periodo="Análisis Puntual",
            resumen_ejecutivo=f"Se detectaron {len(anomalias_detectadas)} anomalías",
            datos_principales=datos_principales,
            analisis_llm=analisis_llm,
            recomendaciones=recomendaciones,
            alertas_criticas=alertas,
            metricas_clave=metricas,
            proximos_pasos=self._generar_proximos_pasos(recomendaciones),
            confianza=0.85
        )

        return reporte

    def generar_reporte_oc_inteligente(
        self,
        df_oc: pd.DataFrame,
        df_distro: Optional[pd.DataFrame] = None,
        oc_numero: str = ""
    ) -> ReporteInteligente:
        """
        Genera reporte inteligente de una OC específica

        Args:
            df_oc: DataFrame con datos de OC
            df_distro: DataFrame con distribuciones
            oc_numero: Número de OC

        Returns:
            ReporteInteligente: Reporte de OC
        """
        logger.info(f"📋 Generando reporte inteligente de OC {oc_numero}...")

        datos_principales = self._compilar_datos_oc(df_oc, df_distro, oc_numero)
        metricas = self._calcular_metricas_oc(df_oc, df_distro)

        analisis_llm = ""
        recomendaciones = []
        alertas = []
        confianza = 0.5

        if self.cliente_llm:
            try:
                # Análisis de OC
                datos_para_llm = json.dumps(datos_principales, indent=2, default=str)
                analisis_llm = self._generar_analisis_oc(datos_para_llm)

                # Recomendaciones
                recomendaciones = self.cliente_llm.consultar_recomendaciones(
                    datos_para_llm,
                    contexto=f"Análisis de OC {oc_numero}"
                )

                # Alertas
                if metricas.get('distribucion_equitativa', True) == False:
                    alertas.append("⚠️  Distribución inequitativa detectada")

                confianza = 0.9

            except Exception as e:
                logger.warning(f"⚠️  Error en análisis OC: {e}")

        reporte = ReporteInteligente(
            titulo=f"Reporte Inteligente - OC {oc_numero}",
            fecha_generacion=datetime.now(),
            periodo="Puntual",
            resumen_ejecutivo=self._generar_resumen_oc(datos_principales),
            datos_principales=datos_principales,
            analisis_llm=analisis_llm,
            recomendaciones=recomendaciones,
            alertas_criticas=alertas,
            metricas_clave=metricas,
            proximos_pasos=self._generar_proximos_pasos(recomendaciones),
            confianza=confianza
        )

        return reporte

    def exportar_reporte_completo(
        self,
        reporte: ReporteInteligente,
        formato: str = "excel"
    ) -> str:
        """
        Exporta reporte completo en formato especificado

        Args:
            reporte: Reporte a exportar
            formato: Formato de exportación (excel, pdf, json)

        Returns:
            str: Ruta del archivo generado
        """
        if formato == "json":
            return self._exportar_json(reporte)
        elif formato == "excel" and self.generador_excel:
            return self._exportar_excel(reporte)
        else:
            logger.warning(f"⚠️  Formato no soportado: {formato}")
            return self._exportar_json(reporte)

    def generar_resumen_conversacional(self, reporte: ReporteInteligente) -> str:
        """
        Genera resumen conversacional del reporte

        Args:
            reporte: Reporte a resumir

        Returns:
            str: Resumen en formato conversacional
        """
        resumen = f"""
📊 **{reporte.titulo}**
_Generado: {reporte.fecha_generacion.strftime('%Y-%m-%d %H:%M:%S')}_

**Resumen Ejecutivo:**
{reporte.resumen_ejecutivo}

**Métricas Clave:**
"""

        for metrica, valor in reporte.metricas_clave.items():
            resumen += f"\n- {metrica}: {valor}"

        if reporte.alertas_criticas:
            resumen += "\n\n🚨 **Alertas Críticas:**\n"
            for alerta in reporte.alertas_criticas:
                resumen += f"\n- {alerta}"

        if reporte.recomendaciones:
            resumen += "\n\n💡 **Recomendaciones:**\n"
            for i, rec in enumerate(reporte.recomendaciones[:5], 1):
                resumen += f"\n{i}. {rec}"

        if reporte.proximos_pasos:
            resumen += "\n\n📋 **Próximos Pasos:**\n"
            for paso in reporte.proximos_pasos:
                resumen += f"\n- {paso}"

        resumen += f"\n\n_Confianza del análisis: {reporte.confianza:.0%}_"

        return resumen

    # ═══════════════════════════════════════════════════════════════
    # MÉTODOS PRIVADOS
    # ═══════════════════════════════════════════════════════════════

    def _compilar_datos_principales(
        self,
        df_oc: pd.DataFrame,
        df_distro: Optional[pd.DataFrame] = None
    ) -> Dict[str, Any]:
        """Compila datos principales"""
        datos = {
            "total_oc": len(df_oc),
            "cantidad_total": df_oc['CANTIDAD'].sum() if 'CANTIDAD' in df_oc.columns else 0,
            "cantidad_promedio": df_oc['CANTIDAD'].mean() if 'CANTIDAD' in df_oc.columns else 0,
        }

        if df_distro is not None and not df_distro.empty:
            datos['total_tiendas'] = df_distro['TIENDA'].nunique() if 'TIENDA' in df_distro.columns else 0
            datos['cantidad_distribuida'] = df_distro['CANTIDAD'].sum() if 'CANTIDAD' in df_distro.columns else 0

        return datos

    def _calcular_metricas_clave(
        self,
        df_oc: pd.DataFrame,
        df_distro: Optional[pd.DataFrame] = None
    ) -> Dict[str, float]:
        """Calcula métricas clave"""
        metricas = {
            "total_oc_procesadas": len(df_oc),
            "cantidad_total_procesada": df_oc['CANTIDAD'].sum() if 'CANTIDAD' in df_oc.columns else 0,
        }

        if df_distro is not None and not df_distro.empty:
            total_oc = df_oc['CANTIDAD'].sum() if 'CANTIDAD' in df_oc.columns else 0
            total_dist = df_distro['CANTIDAD'].sum() if 'CANTIDAD' in df_distro.columns else 0

            metricas['porcentaje_distribuido'] = (total_dist / total_oc * 100) if total_oc > 0 else 0
            metricas['distribucion_equitativa'] = (
                df_distro['CANTIDAD'].std() / df_distro['CANTIDAD'].mean() < 0.5
                if 'CANTIDAD' in df_distro.columns and df_distro['CANTIDAD'].mean() > 0
                else True
            )

        return metricas

    def _generar_analisis_general(self, datos_principales: Dict) -> str:
        """Genera análisis general usando LLM"""
        if not self.cliente_llm:
            return "Análisis no disponible"

        prompt = f"""
Genera un análisis profesional de los siguientes datos de planning:

{json.dumps(datos_principales, indent=2)}

Incluye:
1. Interpretación de los números principales
2. Patrones identificados
3. Desviaciones de lo normal
4. Implicaciones operacionales
"""

        try:
            respuesta = self.cliente_llm.cliente.consultar(prompt, temperatura=0.6, max_tokens=800)
            return respuesta.contenido
        except Exception as e:
            logger.warning(f"⚠️  Error generando análisis: {e}")
            return "Análisis no disponible"

    def _generar_recomendaciones(self, datos_principales: Dict) -> List[str]:
        """Genera recomendaciones"""
        if not self.cliente_llm:
            return []

        return self.cliente_llm.consultar_recomendaciones(
            json.dumps(datos_principales, indent=2)
        )

    def _generar_alertas(self, datos_principales: Dict) -> List[str]:
        """Genera alertas críticas"""
        alertas = []

        # Alertas basadas en datos
        total_oc = datos_principales.get('total_oc', 0)
        if total_oc == 0:
            alertas.append("⚠️  Sin órdenes de compra procesadas")

        porcentaje_dist = datos_principales.get('porcentaje_distribuido', 100)
        if porcentaje_dist < 70:
            alertas.append(f"⚠️  Solo {porcentaje_dist:.0f}% distribuido")

        return alertas

    def _compilar_datos_oc(
        self,
        df_oc: pd.DataFrame,
        df_distro: Optional[pd.DataFrame],
        oc_numero: str
    ) -> Dict[str, Any]:
        """Compila datos de OC específica"""
        datos = {
            "oc_numero": oc_numero,
            "cantidad_total": df_oc['CANTIDAD'].sum() if 'CANTIDAD' in df_oc.columns else 0,
        }

        if df_distro is not None and not df_distro.empty:
            datos['num_tiendas'] = df_distro['TIENDA'].nunique() if 'TIENDA' in df_distro.columns else 0
            datos['cantidad_distribuida'] = df_distro['CANTIDAD'].sum() if 'CANTIDAD' in df_distro.columns else 0

        return datos

    def _calcular_metricas_oc(
        self,
        df_oc: pd.DataFrame,
        df_distro: Optional[pd.DataFrame] = None
    ) -> Dict[str, float]:
        """Calcula métricas de OC"""
        metricas = {
            "cantidad_total": df_oc['CANTIDAD'].sum() if 'CANTIDAD' in df_oc.columns else 0,
        }

        if df_distro is not None and not df_distro.empty:
            metricas['distribucion_equitativa'] = (
                df_distro['CANTIDAD'].std() / df_distro['CANTIDAD'].mean() < 0.5
                if 'CANTIDAD' in df_distro.columns and df_distro['CANTIDAD'].mean() > 0
                else True
            )

        return metricas

    def _generar_analisis_oc(self, datos_json: str) -> str:
        """Genera análisis detallado de OC"""
        if not self.cliente_llm:
            return "Análisis no disponible"

        prompt = f"""
Analiza esta OC en detalle:

{datos_json}

Proporciona análisis sobre:
- Viabilidad de la distribución
- Riesgos potenciales
- Oportunidades de optimización
"""

        try:
            respuesta = self.cliente_llm.cliente.consultar(prompt, temperatura=0.6, max_tokens=1000)
            return respuesta.contenido
        except Exception as e:
            logger.warning(f"⚠️  Error en análisis OC: {e}")
            return "Análisis no disponible"

    def _generar_resumen_ejecutivo(self, datos: Dict) -> str:
        """Genera resumen ejecutivo"""
        total_oc = datos.get('total_oc', 0)
        cantidad = datos.get('cantidad_total', 0)
        tiendas = datos.get('total_tiendas', 0)

        return (f"Se procesaron {total_oc} órdenes de compra por una cantidad total de "
                f"{cantidad:,.0f} unidades, distribuidas en {tiendas} tiendas.")

    def _generar_resumen_oc(self, datos: Dict) -> str:
        """Genera resumen de OC"""
        oc = datos.get('oc_numero', 'DESCONOCIDA')
        cantidad = datos.get('cantidad_total', 0)
        tiendas = datos.get('num_tiendas', 0)

        return (f"OC {oc} con cantidad total de {cantidad:,.0f} unidades distribuidas "
                f"en {tiendas} tiendas.")

    def _generar_proximos_pasos(self, recomendaciones: List[str]) -> List[str]:
        """Genera próximos pasos basado en recomendaciones"""
        pasos = []

        if recomendaciones:
            pasos.append("Implementar las recomendaciones generadas")

        pasos.append("Monitorear métricas clave")
        pasos.append("Revisar avances en próximo reporte")

        return pasos

    def _analizar_severidad(self, anomalias: List[Dict]) -> Dict[str, int]:
        """Analiza distribución de severidad"""
        severidades = {}

        for anomalia in anomalias:
            sev = anomalia.get('severidad', 'DESCONOCIDA')
            severidades[sev] = severidades.get(sev, 0) + 1

        return severidades

    def _exportar_json(self, reporte: ReporteInteligente) -> str:
        """Exporta reporte a JSON"""
        reporte_dict = {
            "titulo": reporte.titulo,
            "fecha": reporte.fecha_generacion.isoformat(),
            "periodo": reporte.periodo,
            "resumen_ejecutivo": reporte.resumen_ejecutivo,
            "datos_principales": reporte.datos_principales,
            "analisis_llm": reporte.analisis_llm,
            "recomendaciones": reporte.recomendaciones,
            "alertas": reporte.alertas_criticas,
            "metricas": reporte.metricas_clave,
            "confianza": reporte.confianza,
        }

        archivo = f"/tmp/reporte_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(archivo, 'w') as f:
            json.dump(reporte_dict, f, indent=2, default=str)

        logger.info(f"✅ Reporte exportado a JSON: {archivo}")
        return archivo

    def _exportar_excel(self, reporte: ReporteInteligente) -> str:
        """Exporta reporte a Excel (si generador disponible)"""
        if not self.generador_excel:
            logger.warning("⚠️  Generador Excel no disponible")
            return self._exportar_json(reporte)

        try:
            # Crear DataFrame con datos del reporte
            datos_para_excel = {
                "Métrica": list(reporte.metricas_clave.keys()),
                "Valor": list(reporte.metricas_clave.values()),
            }

            df = pd.DataFrame(datos_para_excel)

            # Usar generador Excel
            archivo = self.generador_excel.crear_reporte_validacion_oc(
                df,
                nombre_archivo=f"Reporte_Inteligente_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            )

            logger.info(f"✅ Reporte exportado a Excel: {archivo}")
            return archivo

        except Exception as e:
            logger.warning(f"⚠️  Error exportando a Excel: {e}")
            return self._exportar_json(reporte)
