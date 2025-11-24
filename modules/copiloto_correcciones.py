"""
═══════════════════════════════════════════════════════════════
COPILOTO DE CORRECCIONES - SAC 2.0
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Este módulo integra la detección de anomalías con la ejecución
de correcciones, actuando como un verdadero copiloto para el
analista de Planning.

Flujo completo:
    Detectar → Analizar → Proponer → Confirmar → Ejecutar → Reportar

"Las máquinas y los sistemas al servicio de los analistas"

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
═══════════════════════════════════════════════════════════════
"""

import logging
from typing import Optional, Dict, List, Any, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
import pandas as pd

# Importaciones del SAC
try:
    from modules.ejecutor_correcciones import (
        EjecutorCorrecciones,
        PlanCorreccion,
        ResultadoEjecucion,
        TipoCorreccion,
        NivelRiesgo,
        EstadoEjecucion
    )
except ImportError:
    EjecutorCorrecciones = None

try:
    from config import CEDIS, PATHS
except ImportError:
    CEDIS = {'code': '427', 'name': 'Cancún'}
    PATHS = {}

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# TIPOS DE ANOMALÍAS SOPORTADAS
# ═══════════════════════════════════════════════════════════════

class TipoAnomalia(Enum):
    """Tipos de anomalías que el copiloto puede corregir"""
    DISTRIBUCION_EXCEDE = "distribucion_excede_oc"
    DISTRIBUCION_INCOMPLETA = "distribucion_incompleta"
    OC_SIN_CERRAR = "oc_sin_cerrar"
    ASN_ESTANCADO = "asn_estancado"
    LINEA_DUPLICADA = "linea_duplicada"
    CANTIDAD_INCORRECTA = "cantidad_incorrecta"
    STATUS_INCORRECTO = "status_incorrecto"


@dataclass
class AnomaliaDetectada:
    """Representa una anomalía detectada por el monitor"""
    tipo: TipoAnomalia
    descripcion: str
    severidad: str  # CRITICO, ALTO, MEDIO, BAJO
    df_afectados: pd.DataFrame
    contexto: Dict = field(default_factory=dict)
    fecha_deteccion: datetime = field(default_factory=datetime.now)
    corregible: bool = True

    @property
    def total_afectados(self) -> int:
        return len(self.df_afectados)


# ═══════════════════════════════════════════════════════════════
# CLASE PRINCIPAL: COPILOTO DE CORRECCIONES
# ═══════════════════════════════════════════════════════════════

class CopilotoCorrecciones:
    """
    Copiloto inteligente que asiste al analista en la corrección
    de anomalías detectadas en Manhattan WMS.

    Capacidades:
    - Analiza anomalías y propone correcciones
    - Genera planes de corrección masiva
    - Presenta opciones al analista de forma clara
    - Ejecuta correcciones con confirmación
    - Genera reportes de resultados

    Uso:
        copiloto = CopilotoCorrecciones(db_connection)

        # Cuando el monitor detecte anomalías
        anomalia = AnomaliaDetectada(
            tipo=TipoAnomalia.DISTRIBUCION_EXCEDE,
            descripcion="150 distribuciones exceden la OC",
            severidad="CRITICO",
            df_afectados=df_excedentes
        )

        # El copiloto analiza y propone
        plan = copiloto.analizar_y_proponer(anomalia)

        # Mostrar al analista
        copiloto.presentar_opciones(plan)

        # Ejecutar con confirmación
        resultado = copiloto.ejecutar_con_confirmacion(plan, usuario="ADMJAJA")
    """

    def __init__(self, db_connection=None, usuario_default: str = "SAC"):
        """
        Inicializa el copiloto.

        Args:
            db_connection: Conexión a Manhattan WMS (DB2)
            usuario_default: Usuario por defecto para auditoría
        """
        self.db = db_connection
        self.usuario = usuario_default
        self.ejecutor = EjecutorCorrecciones(db_connection) if EjecutorCorrecciones else None

        # Historial de sesión
        self.anomalias_procesadas: List[AnomaliaDetectada] = []
        self.planes_generados: List[PlanCorreccion] = []
        self.correcciones_ejecutadas: List[ResultadoEjecucion] = []

        # Estadísticas de sesión
        self.stats = {
            'anomalias_analizadas': 0,
            'planes_generados': 0,
            'correcciones_exitosas': 0,
            'registros_corregidos': 0,
            'tiempo_ahorrado_estimado': 0  # minutos
        }

        logger.info(f"✅ CopilotoCorrecciones inicializado para usuario {usuario_default}")

    # ═══════════════════════════════════════════════════════════════
    # ANÁLISIS Y PROPUESTA
    # ═══════════════════════════════════════════════════════════════

    def analizar_y_proponer(
        self,
        anomalia: AnomaliaDetectada
    ) -> Optional[PlanCorreccion]:
        """
        Analiza una anomalía y genera un plan de corrección.

        Args:
            anomalia: Anomalía detectada por el monitor

        Returns:
            PlanCorreccion si es corregible, None si no
        """
        self.stats['anomalias_analizadas'] += 1
        self.anomalias_procesadas.append(anomalia)

        if not anomalia.corregible:
            logger.warning(f"⚠️ Anomalía no corregible automáticamente: {anomalia.tipo.value}")
            return None

        if self.ejecutor is None:
            logger.error("❌ EjecutorCorrecciones no disponible")
            return None

        # Mapear tipo de anomalía a generador de plan
        generadores = {
            TipoAnomalia.DISTRIBUCION_EXCEDE: self._generar_plan_distribucion_excede,
            TipoAnomalia.OC_SIN_CERRAR: self._generar_plan_cierre_oc,
            TipoAnomalia.ASN_ESTANCADO: self._generar_plan_asn_estancado,
            TipoAnomalia.CANTIDAD_INCORRECTA: self._generar_plan_ajuste_cantidad,
            TipoAnomalia.LINEA_DUPLICADA: self._generar_plan_cancelar_duplicados,
        }

        generador = generadores.get(anomalia.tipo)
        if generador is None:
            logger.warning(f"⚠️ No hay generador para anomalía tipo: {anomalia.tipo.value}")
            return None

        # Generar plan
        plan = generador(anomalia)

        if plan:
            self.planes_generados.append(plan)
            self.stats['planes_generados'] += 1

            # Estimar tiempo ahorrado (2 min por registro manual vs 1 seg automático)
            tiempo_manual = anomalia.total_afectados * 2  # minutos
            self.stats['tiempo_ahorrado_estimado'] += tiempo_manual

        return plan

    def _generar_plan_distribucion_excede(
        self,
        anomalia: AnomaliaDetectada
    ) -> PlanCorreccion:
        """Genera plan para distribuciones que exceden OC"""
        oc = anomalia.contexto.get('oc_numero', 'DESCONOCIDA')

        # Calcular ajustes proporcionales si no vienen calculados
        df = anomalia.df_afectados.copy()
        if 'qty_ajustada' not in df.columns:
            # Ajuste simple: reducir proporcionalmente
            if 'qty_distribuida' in df.columns and 'qty_oc' in df.columns:
                factor = df['qty_oc'].sum() / df['qty_distribuida'].sum()
                df['qty_ajustada'] = (df['qty_distribuida'] * factor).astype(int)
            else:
                df['qty_ajustada'] = df.get('qty_distribuida', 0)

        return self.ejecutor.generar_plan_distribucion_excedente(df, oc)

    def _generar_plan_cierre_oc(
        self,
        anomalia: AnomaliaDetectada
    ) -> PlanCorreccion:
        """Genera plan para cerrar OCs pendientes"""
        return self.ejecutor.generar_plan_cambio_status(
            df_registros=anomalia.df_afectados,
            tabla="ORDERS",
            campo_status="STATUS",
            nuevo_status="5",
            campo_llave="ORDERKEY",
            descripcion=f"Cierre de {anomalia.total_afectados} OCs pendientes"
        )

    def _generar_plan_asn_estancado(
        self,
        anomalia: AnomaliaDetectada
    ) -> PlanCorreccion:
        """Genera plan para actualizar ASN estancados"""
        return self.ejecutor.generar_plan_cambio_status(
            df_registros=anomalia.df_afectados,
            tabla="RECEIPT",
            campo_status="STATUS",
            nuevo_status="9",  # Cerrar
            campo_llave="RECEIPTKEY",
            descripcion=f"Actualización de {anomalia.total_afectados} ASN estancados"
        )

    def _generar_plan_ajuste_cantidad(
        self,
        anomalia: AnomaliaDetectada
    ) -> PlanCorreccion:
        """Genera plan para ajustar cantidades incorrectas"""
        return self.ejecutor.generar_plan_ajuste_cantidades(
            df_ajustes=anomalia.df_afectados,
            tabla="ORDERDETAIL",
            campo_cantidad="OPENQTY",
            campo_llave="ORDERKEY",
            columna_valor_nuevo="qty_correcta",
            descripcion=f"Ajuste de {anomalia.total_afectados} cantidades"
        )

    def _generar_plan_cancelar_duplicados(
        self,
        anomalia: AnomaliaDetectada
    ) -> PlanCorreccion:
        """Genera plan para cancelar líneas duplicadas"""
        return self.ejecutor.generar_plan_cambio_status(
            df_registros=anomalia.df_afectados,
            tabla="ORDERDETAIL",
            campo_status="STATUS",
            nuevo_status="95",  # Cancelar
            campo_llave="ORDERKEY",
            descripcion=f"Cancelación de {anomalia.total_afectados} líneas duplicadas"
        )

    # ═══════════════════════════════════════════════════════════════
    # PRESENTACIÓN AL ANALISTA
    # ═══════════════════════════════════════════════════════════════

    def presentar_opciones(self, plan: PlanCorreccion) -> str:
        """
        Presenta las opciones de corrección al analista.

        Returns:
            String con el menú de opciones
        """
        vista = self.ejecutor.mostrar_vista_previa(plan)

        opciones = """
─────────────────────────────────────────────────────────────────
📌 OPCIONES DISPONIBLES:
─────────────────────────────────────────────────────────────────

  [1] ✅ APROBAR Y EJECUTAR
      Ejecutar todas las correcciones del plan

  [2] 📁 EXPORTAR A EXCEL
      Revisar detalladamente antes de decidir

  [3] ✏️  MODIFICAR PLAN
      Ajustar registros específicos

  [4] ❌ CANCELAR
      No realizar ninguna corrección

  [5] 📊 VER ESTADÍSTICAS
      Ver resumen de la sesión actual

─────────────────────────────────────────────────────────────────
"""
        return vista + opciones

    def menu_interactivo(
        self,
        plan: PlanCorreccion,
        usuario: str
    ) -> Optional[ResultadoEjecucion]:
        """
        Presenta menú interactivo al analista.

        Returns:
            ResultadoEjecucion si se ejecutó, None si se canceló
        """
        while True:
            print(self.presentar_opciones(plan))

            try:
                opcion = input("\n🎯 Seleccione opción (1-5): ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n⚠️ Operación cancelada")
                return None

            if opcion == '1':
                # Aprobar y ejecutar
                confirmacion = input(
                    f"\n⚠️  ¿Confirma ejecutar {plan.total_registros} correcciones? (S/N): "
                ).strip().upper()

                if confirmacion == 'S':
                    return self.ejecutar_con_confirmacion(plan, usuario)
                else:
                    print("❌ Ejecución cancelada")

            elif opcion == '2':
                # Exportar a Excel
                archivo = self.ejecutor.exportar_plan_a_excel(plan)
                print(f"\n📁 Plan exportado a: {archivo}")
                input("\nPresione Enter para continuar...")

            elif opcion == '3':
                # Modificar plan
                print("\n✏️ Funcionalidad de modificación en desarrollo...")
                input("Presione Enter para continuar...")

            elif opcion == '4':
                # Cancelar
                print("\n❌ Plan cancelado")
                plan.estado = EstadoEjecucion.CANCELADO
                return None

            elif opcion == '5':
                # Estadísticas
                print(self.resumen_sesion())
                input("\nPresione Enter para continuar...")

            else:
                print("\n⚠️ Opción no válida")

    # ═══════════════════════════════════════════════════════════════
    # EJECUCIÓN
    # ═══════════════════════════════════════════════════════════════

    def ejecutar_con_confirmacion(
        self,
        plan: PlanCorreccion,
        usuario: str
    ) -> ResultadoEjecucion:
        """
        Ejecuta un plan después de aprobación.

        Args:
            plan: Plan a ejecutar
            usuario: Usuario que autoriza

        Returns:
            ResultadoEjecucion con el detalle
        """
        # Aprobar
        plan = self.ejecutor.aprobar_plan(plan, usuario)

        # Ejecutar
        resultado = self.ejecutor.ejecutar_plan(plan, usuario)

        # Actualizar estadísticas
        if resultado.exitoso:
            self.stats['correcciones_exitosas'] += 1
            self.stats['registros_corregidos'] += resultado.registros_exitosos

        self.correcciones_ejecutadas.append(resultado)

        # Mostrar resultado
        print(self._formatear_resultado(resultado))

        return resultado

    def _formatear_resultado(self, resultado: ResultadoEjecucion) -> str:
        """Formatea el resultado de ejecución para mostrar"""
        emoji = "✅" if resultado.exitoso else "⚠️"

        return f"""
═══════════════════════════════════════════════════════════════
{emoji} RESULTADO DE EJECUCIÓN
═══════════════════════════════════════════════════════════════

  Plan ID:          {resultado.plan_id}
  Estado:           {'EXITOSO' if resultado.exitoso else 'CON ERRORES'}

  📊 ESTADÍSTICAS:
  ─────────────────────────────────────────────────────────────
  Registros procesados:  {resultado.registros_procesados}
  Registros exitosos:    {resultado.registros_exitosos}
  Registros fallidos:    {resultado.registros_fallidos}
  Porcentaje de éxito:   {resultado.porcentaje_exito:.1f}%
  Tiempo de ejecución:   {resultado.tiempo_ejecucion_segundos:.2f} segundos

  💾 BACKUP:
  {resultado.backup_path or 'No generado'}

{'  ❌ ERRORES:' if resultado.errores else ''}
{chr(10).join('  - ' + e for e in resultado.errores[:5])}
{'  ... y ' + str(len(resultado.errores) - 5) + ' errores más' if len(resultado.errores) > 5 else ''}

═══════════════════════════════════════════════════════════════
"""

    # ═══════════════════════════════════════════════════════════════
    # REPORTES Y ESTADÍSTICAS
    # ═══════════════════════════════════════════════════════════════

    def resumen_sesion(self) -> str:
        """Genera resumen de la sesión actual"""
        return f"""
═══════════════════════════════════════════════════════════════
📊 RESUMEN DE SESIÓN - COPILOTO SAC
═══════════════════════════════════════════════════════════════

  👤 Usuario:           {self.usuario}
  📅 Fecha:             {datetime.now().strftime('%Y-%m-%d %H:%M')}

  📈 ESTADÍSTICAS:
  ─────────────────────────────────────────────────────────────
  Anomalías analizadas:     {self.stats['anomalias_analizadas']}
  Planes generados:         {self.stats['planes_generados']}
  Correcciones exitosas:    {self.stats['correcciones_exitosas']}
  Registros corregidos:     {self.stats['registros_corregidos']}

  ⏱️  TIEMPO AHORRADO ESTIMADO:
  ─────────────────────────────────────────────────────────────
  Manual (estimado):        {self.stats['tiempo_ahorrado_estimado']} minutos
  Con SAC:                  ~{len(self.correcciones_ejecutadas)} minutos
  Ahorro:                   ~{self.stats['tiempo_ahorrado_estimado'] - len(self.correcciones_ejecutadas)} minutos

═══════════════════════════════════════════════════════════════
"""


# ═══════════════════════════════════════════════════════════════
# FUNCIONES DE CONVENIENCIA
# ═══════════════════════════════════════════════════════════════

def crear_copiloto(db_connection=None, usuario: str = "SAC") -> CopilotoCorrecciones:
    """Crea una instancia del copiloto"""
    return CopilotoCorrecciones(db_connection, usuario)


def corregir_anomalia_rapido(
    tipo: TipoAnomalia,
    df_afectados: pd.DataFrame,
    descripcion: str,
    usuario: str,
    db_connection=None,
    auto_ejecutar: bool = False
) -> Tuple[PlanCorreccion, Optional[ResultadoEjecucion]]:
    """
    Función de conveniencia para corrección rápida.

    Ejemplo:
        plan, resultado = corregir_anomalia_rapido(
            tipo=TipoAnomalia.DISTRIBUCION_EXCEDE,
            df_afectados=df_excedentes,
            descripcion="Distribuciones exceden OC C1234567",
            usuario="ADMJAJA"
        )
    """
    copiloto = crear_copiloto(db_connection, usuario)

    anomalia = AnomaliaDetectada(
        tipo=tipo,
        descripcion=descripcion,
        severidad="ALTO",
        df_afectados=df_afectados
    )

    plan = copiloto.analizar_y_proponer(anomalia)

    if plan is None:
        return None, None

    print(copiloto.presentar_opciones(plan))

    if auto_ejecutar:
        resultado = copiloto.ejecutar_con_confirmacion(plan, usuario)
        return plan, resultado

    return plan, None


# ═══════════════════════════════════════════════════════════════
# EJEMPLO DE USO / DEMO
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    print("""
    ═══════════════════════════════════════════════════════════════
    🤖 SAC 2.0 - COPILOTO DE CORRECCIONES
    ═══════════════════════════════════════════════════════════════

    "Las máquinas y los sistemas al servicio de los analistas"

    Este módulo actúa como copiloto inteligente que:

    1. Recibe anomalías detectadas por el monitor
    2. Analiza y propone planes de corrección
    3. Presenta opciones claras al analista
    4. Ejecuta correcciones masivas con confirmación
    5. Genera reportes y estadísticas

    ═══════════════════════════════════════════════════════════════
    """)

    # Demo
    print("\n📋 Ejecutando demostración...\n")

    # Crear copiloto
    copiloto = crear_copiloto(usuario="ADMJAJA")

    # Simular anomalía detectada
    df_ejemplo = pd.DataFrame({
        'orderkey': ['C1234567'] * 5,
        'linea': ['001', '002', '003', '004', '005'],
        'sku': ['SKU001', 'SKU002', 'SKU003', 'SKU004', 'SKU005'],
        'qty_distribuida': [100, 200, 150, 80, 120],
        'qty_oc': [90, 180, 140, 75, 110],
        'qty_ajustada': [90, 180, 140, 75, 110]
    })

    anomalia = AnomaliaDetectada(
        tipo=TipoAnomalia.DISTRIBUCION_EXCEDE,
        descripcion="5 líneas de distribución exceden la OC C1234567",
        severidad="CRITICO",
        df_afectados=df_ejemplo,
        contexto={'oc_numero': 'C1234567'}
    )

    # Analizar y proponer
    plan = copiloto.analizar_y_proponer(anomalia)

    if plan:
        # Mostrar opciones
        print(copiloto.presentar_opciones(plan))

        # Mostrar resumen
        print(copiloto.resumen_sesion())

    print("\n✅ Demo completado")
    print("\nPara usar en producción:")
    print("  from modules.copiloto_correcciones import CopilotoCorrecciones")
    print("  copiloto = CopilotoCorrecciones(db_connection, 'ADMJAJA')")
