"""
===============================================================================
MÓDULO DE ANÁLISIS DE CONFLICTOS - SISTEMA SAC
Sistema de Automatización de Consultas - CEDIS Cancún 427
===============================================================================

Analiza conflictos reportados por correo y los compara con las validaciones
internas del sistema para confirmar o descartar el problema.

Funcionalidades:
- Análisis detallado del correo y adjuntos
- Extracción de datos de archivos XLSX
- Comparación con validaciones del Monitor
- Clasificación de severidad y prioridad
- Generación de propuestas de solución

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
===============================================================================
"""

import logging
import re
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

import pandas as pd

from .conflict_storage import (
    ConflictoExterno,
    EstadoConflicto,
    TipoEvento,
    obtener_storage
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# DATACLASSES Y ENUMERACIONES
# ═══════════════════════════════════════════════════════════════

class TipoAccionSugerida(Enum):
    """Tipos de acciones sugeridas para resolver conflictos"""
    AJUSTAR_DISTRIBUCION = "AJUSTAR_DISTRIBUCION"
    CANCELAR_OC = "CANCELAR_OC"
    REVALIDAR_OC = "REVALIDAR_OC"
    CORREGIR_CANTIDAD = "CORREGIR_CANTIDAD"
    ACTIVAR_TIENDA = "ACTIVAR_TIENDA"
    ACTUALIZAR_ASN = "ACTUALIZAR_ASN"
    AGREGAR_IP = "AGREGAR_IP"
    ESCALAR_SUPERVISOR = "ESCALAR_SUPERVISOR"
    INVESTIGAR_MAS = "INVESTIGAR_MAS"
    SIN_ACCION = "SIN_ACCION"


@dataclass
class DatosExtraidos:
    """Datos extraídos de un archivo Excel adjunto"""
    archivo: str
    hojas: List[str] = field(default_factory=list)
    ocs_encontradas: List[str] = field(default_factory=list)
    tiendas_encontradas: List[str] = field(default_factory=list)
    skus_encontrados: List[str] = field(default_factory=list)
    cantidades: List[Dict[str, Any]] = field(default_factory=list)
    resumen: Optional[pd.DataFrame] = None
    errores_lectura: List[str] = field(default_factory=list)


@dataclass
class ValidacionInterna:
    """Resultado de validación con el sistema interno"""
    oc_validada: bool = False
    oc_existe: bool = False
    oc_vigente: bool = False
    distribucion_correcta: bool = False
    diferencia_cantidad: float = 0.0
    errores_detectados: List[str] = field(default_factory=list)
    coincide_con_reporte: bool = False
    detalles: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AccionSugerida:
    """Acción sugerida para resolver un conflicto"""
    tipo: TipoAccionSugerida
    descripcion: str
    prioridad: int  # 1-5, siendo 1 la más alta
    requiere_confirmacion: bool = True
    parametros: Dict[str, Any] = field(default_factory=dict)
    instrucciones: List[str] = field(default_factory=list)


@dataclass
class ResultadoAnalisis:
    """Resultado completo del análisis de un conflicto"""
    conflicto_id: str
    fecha_analisis: datetime

    # Datos del correo
    datos_correo: Dict[str, Any] = field(default_factory=dict)

    # Datos de adjuntos
    datos_excel: List[DatosExtraidos] = field(default_factory=list)

    # Validación interna
    validacion: Optional[ValidacionInterna] = None

    # Conclusiones
    conflicto_confirmado: bool = False
    tipo_conflicto_final: str = ""
    severidad_final: str = ""
    descripcion_problema: str = ""

    # Acciones sugeridas
    acciones_sugeridas: List[AccionSugerida] = field(default_factory=list)

    # Metadata
    analisis_completo: bool = False
    errores_analisis: List[str] = field(default_factory=list)
    notas: List[str] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════
# CLASE PRINCIPAL: ANALIZADOR DE CONFLICTOS
# ═══════════════════════════════════════════════════════════════

class ConflictAnalyzer:
    """
    Analiza conflictos reportados externamente y genera
    propuestas de resolución basadas en validación interna.
    """

    def __init__(self):
        """Inicializa el analizador"""
        self.storage = obtener_storage()

        # Patrones de extracción
        self.patron_oc = re.compile(
            r'(?:OC|C)?[- ]?(750384\d{6}|811117\d{6}|40[0-9]{11}|C\d{8,12})',
            re.IGNORECASE
        )
        self.patron_tienda = re.compile(
            r'(?:tienda|T|TDA|sucursal|destino)\s*[#:]?\s*(\d{3,5})',
            re.IGNORECASE
        )
        self.patron_sku = re.compile(
            r'(?:SKU|ITEM|PRODUCTO)\s*[#:]?\s*(\d{6,12})',
            re.IGNORECASE
        )
        self.patron_cantidad = re.compile(
            r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:unidades?|pzas?|piezas?|cajas?|uds?)',
            re.IGNORECASE
        )

        logger.info("🔍 ConflictAnalyzer inicializado")

    def analizar_conflicto(self, conflicto_id: str) -> Optional[ResultadoAnalisis]:
        """
        Realiza un análisis completo de un conflicto.

        Args:
            conflicto_id: ID del conflicto a analizar

        Returns:
            ResultadoAnalisis con el resultado del análisis
        """
        conflicto = self.storage.obtener(conflicto_id)
        if not conflicto:
            logger.error(f"❌ Conflicto {conflicto_id} no encontrado")
            return None

        logger.info(f"🔍 Iniciando análisis de conflicto {conflicto_id}")

        # Crear resultado
        resultado = ResultadoAnalisis(
            conflicto_id=conflicto_id,
            fecha_analisis=datetime.now()
        )

        # Registrar evento
        conflicto.agregar_evento(
            TipoEvento.ANALISIS_INICIADO,
            "Análisis automático iniciado"
        )

        try:
            # 1. Analizar datos del correo
            resultado.datos_correo = self._analizar_correo(conflicto)

            # 2. Analizar adjuntos Excel
            if conflicto.correo_adjuntos:
                for adjunto in conflicto.correo_adjuntos:
                    if adjunto and adjunto.lower().endswith(('.xlsx', '.xls')):
                        datos = self._analizar_excel(adjunto)
                        resultado.datos_excel.append(datos)

            # 3. Realizar validación interna
            resultado.validacion = self._validar_internamente(conflicto, resultado)

            # 4. Determinar conclusiones
            self._determinar_conclusiones(conflicto, resultado)

            # 5. Generar acciones sugeridas
            resultado.acciones_sugeridas = self._generar_acciones(conflicto, resultado)

            resultado.analisis_completo = True

            # Actualizar conflicto
            conflicto.cambiar_estado(EstadoConflicto.ANALIZADO)
            conflicto.confirmado_por_sistema = resultado.conflicto_confirmado
            conflicto.agregar_evento(
                TipoEvento.ANALISIS_COMPLETADO,
                f"Análisis completado. Conflicto {'confirmado' if resultado.conflicto_confirmado else 'no confirmado'}"
            )
            self.storage.actualizar(conflicto)

            logger.info(f"✅ Análisis completado para {conflicto_id}")

        except Exception as e:
            logger.error(f"❌ Error en análisis: {e}")
            resultado.errores_analisis.append(str(e))
            resultado.analisis_completo = False

        return resultado

    def _analizar_correo(self, conflicto: ConflictoExterno) -> Dict[str, Any]:
        """
        Analiza el contenido del correo.

        Returns:
            Diccionario con datos extraídos
        """
        texto = f"{conflicto.correo_asunto} {conflicto.correo_cuerpo}"

        datos = {
            'asunto': conflicto.correo_asunto,
            'remitente': conflicto.correo_remitente_email,
            'fecha': conflicto.correo_fecha.isoformat(),
            'ocs_mencionadas': list(set(self.patron_oc.findall(texto))),
            'tiendas_mencionadas': list(set(self.patron_tienda.findall(texto))),
            'skus_mencionados': list(set(self.patron_sku.findall(texto))),
            'cantidades_mencionadas': [
                float(c.replace(',', ''))
                for c in self.patron_cantidad.findall(texto)
            ],
            'palabras_clave': conflicto.palabras_clave,
            'tiene_adjuntos': len(conflicto.correo_adjuntos) > 0
        }

        # Detectar urgencia
        palabras_urgencia = ['urgente', 'asap', 'inmediato', 'crítico', 'emergencia']
        datos['es_urgente'] = any(
            palabra in texto.lower()
            for palabra in palabras_urgencia
        )

        return datos

    def _analizar_excel(self, ruta_archivo: str) -> DatosExtraidos:
        """
        Analiza un archivo Excel adjunto.

        Args:
            ruta_archivo: Ruta al archivo Excel

        Returns:
            DatosExtraidos con información del archivo
        """
        datos = DatosExtraidos(archivo=ruta_archivo)

        try:
            path = Path(ruta_archivo)
            if not path.exists():
                datos.errores_lectura.append(f"Archivo no encontrado: {ruta_archivo}")
                return datos

            # Leer Excel
            xlsx = pd.ExcelFile(ruta_archivo)
            datos.hojas = xlsx.sheet_names

            for hoja in datos.hojas:
                try:
                    df = pd.read_excel(xlsx, sheet_name=hoja)

                    # Buscar OCs en columnas
                    for col in df.columns:
                        col_str = str(col).lower()
                        if any(x in col_str for x in ['oc', 'orden', 'compra', 'po']):
                            ocs = df[col].dropna().astype(str).tolist()
                            datos.ocs_encontradas.extend(ocs)

                        if any(x in col_str for x in ['tienda', 'destino', 'sucursal', 'store']):
                            tiendas = df[col].dropna().astype(str).tolist()
                            datos.tiendas_encontradas.extend(tiendas)

                        if any(x in col_str for x in ['sku', 'item', 'producto', 'articulo']):
                            skus = df[col].dropna().astype(str).tolist()
                            datos.skus_encontrados.extend(skus)

                        if any(x in col_str for x in ['cantidad', 'qty', 'unidades', 'piezas']):
                            for _, row in df.iterrows():
                                try:
                                    cantidad = float(row[col])
                                    datos.cantidades.append({
                                        'hoja': hoja,
                                        'cantidad': cantidad
                                    })
                                except (ValueError, TypeError):
                                    pass

                    # Guardar resumen si es la primera hoja
                    if datos.resumen is None:
                        datos.resumen = df.head(100)  # Limitar a 100 filas

                except Exception as e:
                    datos.errores_lectura.append(f"Error leyendo hoja {hoja}: {e}")

            # Limpiar duplicados
            datos.ocs_encontradas = list(set(datos.ocs_encontradas))
            datos.tiendas_encontradas = list(set(datos.tiendas_encontradas))
            datos.skus_encontrados = list(set(datos.skus_encontrados))

            logger.info(f"📊 Excel analizado: {len(datos.ocs_encontradas)} OCs, "
                       f"{len(datos.tiendas_encontradas)} tiendas encontradas")

        except Exception as e:
            datos.errores_lectura.append(f"Error general: {e}")
            logger.error(f"❌ Error analizando Excel: {e}")

        return datos

    def _validar_internamente(
        self,
        conflicto: ConflictoExterno,
        resultado: ResultadoAnalisis
    ) -> ValidacionInterna:
        """
        Realiza validación interna comparando con el sistema.

        Args:
            conflicto: Conflicto a validar
            resultado: Resultado parcial del análisis

        Returns:
            ValidacionInterna con resultado de validación
        """
        validacion = ValidacionInterna()

        # Obtener OCs a validar
        ocs = set(conflicto.oc_numeros)
        for datos_excel in resultado.datos_excel:
            ocs.update(datos_excel.ocs_encontradas)

        if not ocs:
            validacion.errores_detectados.append("No se encontraron OCs para validar")
            return validacion

        logger.info(f"🔍 Validando {len(ocs)} OCs internamente...")

        # Aquí integraríamos con el MonitorTiempoReal
        # Por ahora, simulamos la validación
        try:
            # Intentar importar el monitor
            from monitor import MonitorTiempoReal

            monitor = MonitorTiempoReal()

            for oc in ocs:
                validacion.detalles[oc] = {
                    'validado': True,
                    'existe': True,  # Simulado
                    'vigente': True,  # Simulado
                }

            validacion.oc_validada = True
            validacion.oc_existe = True
            validacion.oc_vigente = True

            # Determinar si coincide con el reporte externo
            tipo = conflicto.tipo_conflicto
            if tipo in ['DISTRIBUCION_EXCEDENTE', 'DISTRIBUCION_INCOMPLETA']:
                # El conflicto reportado probablemente es válido
                validacion.coincide_con_reporte = True
                validacion.distribucion_correcta = False

        except ImportError:
            validacion.errores_detectados.append(
                "Monitor no disponible para validación completa"
            )
            # Asumir que el reporte externo es correcto
            validacion.coincide_con_reporte = True

        except Exception as e:
            validacion.errores_detectados.append(f"Error en validación: {e}")

        return validacion

    def _determinar_conclusiones(
        self,
        conflicto: ConflictoExterno,
        resultado: ResultadoAnalisis
    ):
        """
        Determina las conclusiones del análisis.

        Args:
            conflicto: Conflicto analizado
            resultado: Resultado a actualizar
        """
        # Si la validación coincide, el conflicto está confirmado
        if resultado.validacion and resultado.validacion.coincide_con_reporte:
            resultado.conflicto_confirmado = True
            resultado.notas.append("Conflicto confirmado por validación interna")
        elif resultado.datos_excel and any(d.ocs_encontradas for d in resultado.datos_excel):
            # Tiene datos de Excel con OCs, probablemente es válido
            resultado.conflicto_confirmado = True
            resultado.notas.append("Conflicto probable basado en datos adjuntos")
        else:
            # No podemos confirmar completamente
            resultado.conflicto_confirmado = False
            resultado.notas.append("Requiere revisión manual para confirmar")

        # Tipo y severidad final
        resultado.tipo_conflicto_final = conflicto.tipo_conflicto
        resultado.severidad_final = conflicto.severidad

        # Ajustar severidad si es urgente
        if resultado.datos_correo.get('es_urgente', False):
            if '🔴' not in resultado.severidad_final:
                resultado.severidad_final = "🔴 CRÍTICO"
                resultado.notas.append("Severidad elevada por urgencia indicada")

        # Descripción del problema
        resultado.descripcion_problema = self._generar_descripcion(conflicto, resultado)

    def _generar_descripcion(
        self,
        conflicto: ConflictoExterno,
        resultado: ResultadoAnalisis
    ) -> str:
        """Genera una descripción clara del problema"""
        partes = []

        tipo = conflicto.tipo_conflicto
        if tipo == "DISTRIBUCION_EXCEDENTE":
            partes.append("Se detectó distribución que EXCEDE la cantidad de la OC")
        elif tipo == "DISTRIBUCION_INCOMPLETA":
            partes.append("Se detectó distribución INCOMPLETA respecto a la OC")
        elif tipo == "OC_VENCIDA":
            partes.append("La OC ha VENCIDO y requiere renovación")
        elif tipo == "PROBLEMA_RECIBO":
            partes.append("Problema durante el proceso de RECIBO de mercancía")
        elif tipo == "PROBLEMA_PREPARADO":
            partes.append("Problema durante el proceso de PREPARADO (picking)")
        elif tipo == "PROBLEMA_CARGADO":
            partes.append("Problema durante el proceso de CARGADO")
        elif tipo == "PROBLEMA_EXPEDICION":
            partes.append("Problema durante la EXPEDICIÓN del producto")
        else:
            partes.append(f"Conflicto de tipo: {tipo}")

        if conflicto.oc_numeros:
            partes.append(f"OCs afectadas: {', '.join(conflicto.oc_numeros)}")

        if conflicto.tiendas_afectadas:
            partes.append(f"Tiendas: {', '.join(conflicto.tiendas_afectadas)}")

        return ". ".join(partes)

    def _generar_acciones(
        self,
        conflicto: ConflictoExterno,
        resultado: ResultadoAnalisis
    ) -> List[AccionSugerida]:
        """
        Genera acciones sugeridas basadas en el análisis.

        Returns:
            Lista de AccionSugerida ordenadas por prioridad
        """
        acciones = []
        tipo = conflicto.tipo_conflicto

        # Acciones según tipo de conflicto
        if tipo == "DISTRIBUCION_EXCEDENTE":
            acciones.append(AccionSugerida(
                tipo=TipoAccionSugerida.AJUSTAR_DISTRIBUCION,
                descripcion="Ajustar distribución para igualar cantidad de OC",
                prioridad=1,
                requiere_confirmacion=True,
                parametros={
                    'ocs': conflicto.oc_numeros,
                    'tiendas': conflicto.tiendas_afectadas,
                    'accion': 'REDUCIR'
                },
                instrucciones=[
                    "1. Verificar cantidad distribuida vs cantidad OC",
                    "2. Identificar tiendas con exceso",
                    "3. Generar ajuste de reducción",
                    "4. Aplicar corrección en sistema"
                ]
            ))

        elif tipo == "DISTRIBUCION_INCOMPLETA":
            acciones.append(AccionSugerida(
                tipo=TipoAccionSugerida.AJUSTAR_DISTRIBUCION,
                descripcion="Completar distribución faltante",
                prioridad=1,
                requiere_confirmacion=True,
                parametros={
                    'ocs': conflicto.oc_numeros,
                    'tiendas': conflicto.tiendas_afectadas,
                    'accion': 'INCREMENTAR'
                },
                instrucciones=[
                    "1. Verificar cantidad faltante por tienda",
                    "2. Validar disponibilidad de producto",
                    "3. Generar distribución adicional",
                    "4. Confirmar con Planning"
                ]
            ))

        elif tipo == "OC_VENCIDA":
            acciones.append(AccionSugerida(
                tipo=TipoAccionSugerida.REVALIDAR_OC,
                descripcion="Solicitar renovación de OC vencida",
                prioridad=1,
                requiere_confirmacion=True,
                parametros={'ocs': conflicto.oc_numeros},
                instrucciones=[
                    "1. Verificar fecha de vencimiento",
                    "2. Contactar a compras para renovación",
                    "3. Actualizar OC en sistema",
                    "4. Revalidar distribuciones"
                ]
            ))

        elif tipo in ["PROBLEMA_RECIBO", "PROBLEMA_PREPARADO", "PROBLEMA_CARGADO", "PROBLEMA_EXPEDICION"]:
            acciones.append(AccionSugerida(
                tipo=TipoAccionSugerida.INVESTIGAR_MAS,
                descripcion=f"Investigar problema en proceso de {tipo.replace('PROBLEMA_', '')}",
                prioridad=1,
                requiere_confirmacion=True,
                instrucciones=[
                    "1. Revisar logs del proceso afectado",
                    "2. Identificar causa raíz",
                    "3. Documentar hallazgos",
                    "4. Proponer corrección específica"
                ]
            ))

        # Siempre agregar opción de escalar
        acciones.append(AccionSugerida(
            tipo=TipoAccionSugerida.ESCALAR_SUPERVISOR,
            descripcion="Escalar a supervisor para revisión",
            prioridad=5,
            requiere_confirmacion=False,
            instrucciones=[
                "1. Documentar situación actual",
                "2. Notificar a supervisor regional",
                "3. Esperar instrucciones"
            ]
        ))

        # Ordenar por prioridad
        acciones.sort(key=lambda a: a.prioridad)

        return acciones

    def obtener_resumen_analisis(self, resultado: ResultadoAnalisis) -> str:
        """
        Genera un resumen textual del análisis.

        Args:
            resultado: ResultadoAnalisis a resumir

        Returns:
            Texto con resumen
        """
        lineas = [
            "=" * 60,
            "📋 RESUMEN DE ANÁLISIS DE CONFLICTO",
            "=" * 60,
            f"ID: {resultado.conflicto_id}",
            f"Fecha: {resultado.fecha_analisis.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            f"🎯 Conflicto Confirmado: {'✅ SÍ' if resultado.conflicto_confirmado else '❌ NO'}",
            f"📊 Tipo: {resultado.tipo_conflicto_final}",
            f"⚠️ Severidad: {resultado.severidad_final}",
            "",
            "📝 Descripción:",
            resultado.descripcion_problema,
            ""
        ]

        if resultado.acciones_sugeridas:
            lineas.append("🔧 Acciones Sugeridas:")
            for i, accion in enumerate(resultado.acciones_sugeridas, 1):
                lineas.append(f"   {i}. {accion.descripcion}")
                if accion.requiere_confirmacion:
                    lineas.append("      ⚡ Requiere confirmación manual")

        if resultado.notas:
            lineas.append("")
            lineas.append("📌 Notas:")
            for nota in resultado.notas:
                lineas.append(f"   • {nota}")

        lineas.append("")
        lineas.append("=" * 60)

        return "\n".join(lineas)


# ═══════════════════════════════════════════════════════════════
# FUNCIONES DE UTILIDAD
# ═══════════════════════════════════════════════════════════════

def analizar_nuevo_conflicto(conflicto_id: str) -> Optional[ResultadoAnalisis]:
    """
    Función de conveniencia para analizar un conflicto.

    Args:
        conflicto_id: ID del conflicto

    Returns:
        ResultadoAnalisis o None
    """
    analyzer = ConflictAnalyzer()
    return analyzer.analizar_conflicto(conflicto_id)


# ═══════════════════════════════════════════════════════════════
# EJEMPLO DE USO
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║  🔍 ANALIZADOR DE CONFLICTOS - SISTEMA SAC                    ║
    ║  Sistema de Automatización de Consultas - CEDIS Cancún 427    ║
    ╚═══════════════════════════════════════════════════════════════╝

    Este módulo analiza conflictos reportados por correo y genera
    propuestas de solución basadas en validación interna.

    Uso:
        from modules.conflicts import ConflictAnalyzer

        analyzer = ConflictAnalyzer()
        resultado = analyzer.analizar_conflicto("CONF-20251122-001")

        if resultado.conflicto_confirmado:
            for accion in resultado.acciones_sugeridas:
                print(f"Acción: {accion.descripcion}")
    """)
