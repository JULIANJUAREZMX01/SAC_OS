"""
═══════════════════════════════════════════════════════════════
MÓDULO EJECUTOR DE CORRECCIONES - SAC 2.0
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Este módulo permite al SAC pasar de observador a copiloto activo,
ejecutando correcciones masivas en Manhattan WMS de manera:
- Segura (validaciones pre/post ejecución)
- Auditable (log completo de cada operación)
- Reversible (backup antes de cambios)
- Controlada (requiere confirmación del analista)

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
import json
import hashlib

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# ENUMS Y TIPOS
# ═══════════════════════════════════════════════════════════════

class TipoCorreccion(Enum):
    """Tipos de correcciones soportadas"""
    AJUSTE_CANTIDAD = "ajuste_cantidad"
    CAMBIO_STATUS = "cambio_status"
    ACTUALIZACION_CAMPO = "actualizacion_campo"
    ELIMINACION_REGISTRO = "eliminacion_registro"
    INSERCION_REGISTRO = "insercion_registro"
    CORRECCION_DISTRIBUCION = "correccion_distribucion"
    CIERRE_OC = "cierre_oc"
    CANCELACION_LINEA = "cancelacion_linea"


class EstadoEjecucion(Enum):
    """Estados de ejecución de una corrección"""
    PENDIENTE = "pendiente"
    EN_REVISION = "en_revision"
    APROBADO = "aprobado"
    EJECUTANDO = "ejecutando"
    COMPLETADO = "completado"
    ERROR = "error"
    REVERTIDO = "revertido"
    CANCELADO = "cancelado"


class NivelRiesgo(Enum):
    """Nivel de riesgo de una operación"""
    BAJO = ("🟢 BAJO", "Operación segura, cambios menores")
    MEDIO = ("🟡 MEDIO", "Revisar antes de ejecutar")
    ALTO = ("🟠 ALTO", "Requiere doble confirmación")
    CRITICO = ("🔴 CRÍTICO", "Impacto significativo, verificar cuidadosamente")

    def __init__(self, emoji: str, descripcion: str):
        self.emoji = emoji
        self.descripcion = descripcion


# ═══════════════════════════════════════════════════════════════
# DATA CLASSES
# ═══════════════════════════════════════════════════════════════

@dataclass
class RegistroAfectado:
    """Representa un registro que será modificado"""
    tabla: str
    llave_primaria: Dict[str, Any]
    campo_modificado: str
    valor_anterior: Any
    valor_nuevo: Any
    sql_generado: str = ""

    def to_dict(self) -> Dict:
        return {
            'tabla': self.tabla,
            'llave_primaria': self.llave_primaria,
            'campo': self.campo_modificado,
            'valor_anterior': str(self.valor_anterior),
            'valor_nuevo': str(self.valor_nuevo),
            'sql': self.sql_generado
        }


@dataclass
class PlanCorreccion:
    """Plan de corrección generado por SAC"""
    id_plan: str
    tipo: TipoCorreccion
    descripcion: str
    anomalia_detectada: str
    registros_afectados: List[RegistroAfectado] = field(default_factory=list)
    nivel_riesgo: NivelRiesgo = NivelRiesgo.MEDIO
    estado: EstadoEjecucion = EstadoEjecucion.PENDIENTE

    # Metadata
    fecha_creacion: datetime = field(default_factory=datetime.now)
    creado_por: str = "SAC"
    aprobado_por: Optional[str] = None
    fecha_aprobacion: Optional[datetime] = None

    # Ejecución
    fecha_ejecucion: Optional[datetime] = None
    resultado_ejecucion: Optional[str] = None
    registros_exitosos: int = 0
    registros_fallidos: int = 0

    # Backup
    backup_generado: bool = False
    ruta_backup: Optional[str] = None

    @property
    def total_registros(self) -> int:
        return len(self.registros_afectados)

    @property
    def resumen(self) -> str:
        return (
            f"Plan {self.id_plan}: {self.tipo.value}\n"
            f"  Anomalía: {self.anomalia_detectada}\n"
            f"  Registros: {self.total_registros}\n"
            f"  Riesgo: {self.nivel_riesgo.emoji}\n"
            f"  Estado: {self.estado.value}"
        )

    def generar_id(self) -> str:
        """Genera ID único para el plan"""
        contenido = f"{self.tipo.value}_{self.anomalia_detectada}_{datetime.now().isoformat()}"
        return hashlib.md5(contenido.encode()).hexdigest()[:12].upper()


@dataclass
class ResultadoEjecucion:
    """Resultado de ejecutar un plan de corrección"""
    plan_id: str
    exitoso: bool
    registros_procesados: int
    registros_exitosos: int
    registros_fallidos: int
    tiempo_ejecucion_segundos: float
    errores: List[str] = field(default_factory=list)
    log_detallado: List[Dict] = field(default_factory=list)
    backup_path: Optional[str] = None

    @property
    def porcentaje_exito(self) -> float:
        if self.registros_procesados == 0:
            return 0.0
        return (self.registros_exitosos / self.registros_procesados) * 100


# ═══════════════════════════════════════════════════════════════
# CLASE PRINCIPAL: EJECUTOR DE CORRECCIONES
# ═══════════════════════════════════════════════════════════════

class EjecutorCorrecciones:
    """
    Motor de ejecución de correcciones masivas para Manhattan WMS.

    Flujo:
    1. Recibe anomalía detectada por el monitor
    2. Genera plan de corrección con vista previa
    3. Presenta al analista para aprobación
    4. Ejecuta correcciones con validaciones
    5. Genera reporte y auditoría

    Uso:
        ejecutor = EjecutorCorrecciones(db_connection)
        plan = ejecutor.generar_plan_correccion(anomalia, df_afectados)

        # Analista revisa el plan
        ejecutor.mostrar_vista_previa(plan)

        # Analista aprueba
        plan = ejecutor.aprobar_plan(plan, usuario="ADMJAJA")

        # Ejecutar
        resultado = ejecutor.ejecutar_plan(plan)
    """

    def __init__(self, db_connection=None, config: Dict = None):
        """
        Inicializa el ejecutor de correcciones.

        Args:
            db_connection: Conexión a DB2 (Manhattan WMS)
            config: Configuración adicional
        """
        self.db = db_connection
        self.config = config or {}

        # Rutas
        self.base_path = Path(__file__).parent.parent
        self.backup_path = self.base_path / "output" / "backups"
        self.audit_path = self.base_path / "output" / "auditorias"
        self.plans_path = self.base_path / "output" / "planes_correccion"

        # Crear directorios si no existen
        for path in [self.backup_path, self.audit_path, self.plans_path]:
            path.mkdir(parents=True, exist_ok=True)

        # Historial de planes
        self.planes_activos: Dict[str, PlanCorreccion] = {}

        # Configuración de seguridad
        self.requiere_confirmacion = True
        self.generar_backup_automatico = True
        self.max_registros_sin_confirmacion = 0  # Siempre confirmar
        self.timeout_operacion = 300  # 5 minutos máximo por operación

        logger.info("✅ EjecutorCorrecciones inicializado")

    # ═══════════════════════════════════════════════════════════════
    # GENERACIÓN DE PLANES DE CORRECCIÓN
    # ═══════════════════════════════════════════════════════════════

    def generar_plan_distribucion_excedente(
        self,
        df_excedentes: pd.DataFrame,
        oc_numero: str
    ) -> PlanCorreccion:
        """
        Genera plan para corregir distribuciones que exceden la OC.

        Cuando la suma de distribuciones > cantidad de OC, genera
        los UPDATEs necesarios para ajustar proporcionalmente.
        """
        plan = PlanCorreccion(
            id_plan="",
            tipo=TipoCorreccion.CORRECCION_DISTRIBUCION,
            descripcion=f"Ajustar distribuciones excedentes de OC {oc_numero}",
            anomalia_detectada=f"Distribución total excede OC {oc_numero}",
            nivel_riesgo=NivelRiesgo.ALTO
        )
        plan.id_plan = plan.generar_id()

        for _, row in df_excedentes.iterrows():
            # Calcular nuevo valor (ajuste proporcional o específico)
            valor_anterior = row.get('qty_distribuida', 0)
            valor_nuevo = row.get('qty_ajustada', valor_anterior)

            registro = RegistroAfectado(
                tabla="WMWHSE1.ORDERDETAIL",
                llave_primaria={
                    'ORDERKEY': row.get('orderkey', ''),
                    'ORDERLINENUMBER': row.get('linea', '')
                },
                campo_modificado="OPENQTY",
                valor_anterior=valor_anterior,
                valor_nuevo=valor_nuevo
            )

            # Generar SQL
            registro.sql_generado = self._generar_sql_update(registro)
            plan.registros_afectados.append(registro)

        self.planes_activos[plan.id_plan] = plan
        logger.info(f"📋 Plan generado: {plan.id_plan} con {plan.total_registros} registros")

        return plan

    def generar_plan_cambio_status(
        self,
        df_registros: pd.DataFrame,
        tabla: str,
        campo_status: str,
        nuevo_status: str,
        campo_llave: str,
        descripcion: str
    ) -> PlanCorreccion:
        """
        Genera plan para cambiar status de múltiples registros.

        Útil para:
        - Cerrar OCs masivamente
        - Cancelar líneas
        - Actualizar status de ASN
        """
        plan = PlanCorreccion(
            id_plan="",
            tipo=TipoCorreccion.CAMBIO_STATUS,
            descripcion=descripcion,
            anomalia_detectada=f"Cambio masivo de status en {tabla}",
            nivel_riesgo=NivelRiesgo.MEDIO
        )
        plan.id_plan = plan.generar_id()

        for _, row in df_registros.iterrows():
            registro = RegistroAfectado(
                tabla=f"WMWHSE1.{tabla}",
                llave_primaria={campo_llave: row[campo_llave]},
                campo_modificado=campo_status,
                valor_anterior=row.get(campo_status, 'DESCONOCIDO'),
                valor_nuevo=nuevo_status
            )
            registro.sql_generado = self._generar_sql_update(registro)
            plan.registros_afectados.append(registro)

        self.planes_activos[plan.id_plan] = plan
        return plan

    def generar_plan_ajuste_cantidades(
        self,
        df_ajustes: pd.DataFrame,
        tabla: str,
        campo_cantidad: str,
        campo_llave: str,
        columna_valor_nuevo: str,
        descripcion: str
    ) -> PlanCorreccion:
        """
        Genera plan para ajustar cantidades en múltiples registros.

        Útil para:
        - Ajustar OPENQTY en ORDERDETAIL
        - Corregir EXPECTEDQTY en RECEIPTDETAIL
        - Actualizar inventario
        """
        plan = PlanCorreccion(
            id_plan="",
            tipo=TipoCorreccion.AJUSTE_CANTIDAD,
            descripcion=descripcion,
            anomalia_detectada=f"Ajuste de {campo_cantidad} en {tabla}",
            nivel_riesgo=NivelRiesgo.ALTO
        )
        plan.id_plan = plan.generar_id()

        for _, row in df_ajustes.iterrows():
            registro = RegistroAfectado(
                tabla=f"WMWHSE1.{tabla}",
                llave_primaria={campo_llave: row[campo_llave]},
                campo_modificado=campo_cantidad,
                valor_anterior=row.get(campo_cantidad, 0),
                valor_nuevo=row[columna_valor_nuevo]
            )
            registro.sql_generado = self._generar_sql_update(registro)
            plan.registros_afectados.append(registro)

        self.planes_activos[plan.id_plan] = plan
        return plan

    # ═══════════════════════════════════════════════════════════════
    # VISTA PREVIA Y APROBACIÓN
    # ═══════════════════════════════════════════════════════════════

    def mostrar_vista_previa(self, plan: PlanCorreccion) -> str:
        """
        Genera vista previa del plan para revisión del analista.

        Returns:
            String con la vista previa formateada
        """
        lineas = [
            "",
            "═" * 70,
            "📋 PLAN DE CORRECCIÓN - VISTA PREVIA",
            "═" * 70,
            "",
            f"  ID Plan:        {plan.id_plan}",
            f"  Tipo:           {plan.tipo.value}",
            f"  Descripción:    {plan.descripcion}",
            f"  Anomalía:       {plan.anomalia_detectada}",
            f"  Riesgo:         {plan.nivel_riesgo.emoji}",
            f"  Registros:      {plan.total_registros}",
            f"  Fecha:          {plan.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "─" * 70,
            "📊 REGISTROS A MODIFICAR:",
            "─" * 70,
        ]

        # Mostrar primeros 10 registros como muestra
        for i, reg in enumerate(plan.registros_afectados[:10]):
            lineas.append(
                f"  {i+1}. {reg.tabla} | "
                f"{reg.campo_modificado}: {reg.valor_anterior} → {reg.valor_nuevo}"
            )

        if plan.total_registros > 10:
            lineas.append(f"  ... y {plan.total_registros - 10} registros más")

        lineas.extend([
            "",
            "─" * 70,
            "⚠️  IMPORTANTE:",
            "─" * 70,
            "  • Revise cuidadosamente antes de aprobar",
            "  • Se generará backup automático antes de ejecutar",
            "  • Los cambios son permanentes una vez ejecutados",
            "  • Puede exportar a Excel para revisión detallada",
            "",
            "═" * 70,
        ])

        return "\n".join(lineas)

    def exportar_plan_a_excel(self, plan: PlanCorreccion) -> str:
        """
        Exporta el plan completo a Excel para revisión.

        Returns:
            Ruta del archivo Excel generado
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        archivo = self.plans_path / f"Plan_{plan.id_plan}_{timestamp}.xlsx"

        # Crear DataFrame con todos los registros
        datos = [reg.to_dict() for reg in plan.registros_afectados]
        df = pd.DataFrame(datos)

        # Agregar metadata
        df_meta = pd.DataFrame([{
            'ID Plan': plan.id_plan,
            'Tipo': plan.tipo.value,
            'Descripción': plan.descripcion,
            'Anomalía': plan.anomalia_detectada,
            'Riesgo': plan.nivel_riesgo.emoji,
            'Total Registros': plan.total_registros,
            'Fecha Creación': plan.fecha_creacion,
            'Estado': plan.estado.value
        }])

        with pd.ExcelWriter(archivo, engine='openpyxl') as writer:
            df_meta.to_excel(writer, sheet_name='Resumen', index=False)
            df.to_excel(writer, sheet_name='Registros', index=False)

        logger.info(f"📁 Plan exportado a: {archivo}")
        return str(archivo)

    def aprobar_plan(
        self,
        plan: PlanCorreccion,
        usuario: str,
        comentario: str = ""
    ) -> PlanCorreccion:
        """
        Marca un plan como aprobado por el analista.

        Args:
            plan: Plan a aprobar
            usuario: Usuario que aprueba (ej: ADMJAJA)
            comentario: Comentario opcional
        """
        plan.estado = EstadoEjecucion.APROBADO
        plan.aprobado_por = usuario
        plan.fecha_aprobacion = datetime.now()

        logger.info(f"✅ Plan {plan.id_plan} aprobado por {usuario}")

        # Registrar en auditoría
        self._registrar_auditoria(
            plan.id_plan,
            "APROBACION",
            usuario,
            f"Plan aprobado. {comentario}"
        )

        return plan

    # ═══════════════════════════════════════════════════════════════
    # EJECUCIÓN DE CORRECCIONES
    # ═══════════════════════════════════════════════════════════════

    def ejecutar_plan(
        self,
        plan: PlanCorreccion,
        usuario: str,
        forzar: bool = False
    ) -> ResultadoEjecucion:
        """
        Ejecuta un plan de corrección aprobado.

        Args:
            plan: Plan a ejecutar (debe estar aprobado)
            usuario: Usuario que ejecuta
            forzar: Si True, ejecuta sin verificar estado

        Returns:
            ResultadoEjecucion con el detalle de la operación
        """
        inicio = datetime.now()

        # Validar estado
        if not forzar and plan.estado != EstadoEjecucion.APROBADO:
            raise ValueError(
                f"Plan {plan.id_plan} no está aprobado. "
                f"Estado actual: {plan.estado.value}"
            )

        # Marcar como ejecutando
        plan.estado = EstadoEjecucion.EJECUTANDO
        logger.info(f"🚀 Iniciando ejecución del plan {plan.id_plan}")

        resultado = ResultadoEjecucion(
            plan_id=plan.id_plan,
            exitoso=False,
            registros_procesados=0,
            registros_exitosos=0,
            registros_fallidos=0,
            tiempo_ejecucion_segundos=0
        )

        try:
            # 1. Generar backup
            if self.generar_backup_automatico:
                backup_file = self._generar_backup(plan)
                resultado.backup_path = backup_file
                plan.backup_generado = True
                plan.ruta_backup = backup_file

            # 2. Ejecutar cada operación
            for i, registro in enumerate(plan.registros_afectados):
                resultado.registros_procesados += 1

                try:
                    exito = self._ejecutar_operacion(registro, usuario)

                    if exito:
                        resultado.registros_exitosos += 1
                        resultado.log_detallado.append({
                            'indice': i,
                            'estado': 'exitoso',
                            'sql': registro.sql_generado
                        })
                    else:
                        resultado.registros_fallidos += 1
                        resultado.log_detallado.append({
                            'indice': i,
                            'estado': 'fallido',
                            'sql': registro.sql_generado
                        })

                except Exception as e:
                    resultado.registros_fallidos += 1
                    resultado.errores.append(f"Registro {i}: {str(e)}")
                    resultado.log_detallado.append({
                        'indice': i,
                        'estado': 'error',
                        'error': str(e),
                        'sql': registro.sql_generado
                    })

            # 3. Determinar éxito general
            resultado.exitoso = (resultado.registros_fallidos == 0)
            plan.estado = (
                EstadoEjecucion.COMPLETADO if resultado.exitoso
                else EstadoEjecucion.ERROR
            )

        except Exception as e:
            logger.error(f"❌ Error en ejecución: {e}")
            resultado.errores.append(str(e))
            plan.estado = EstadoEjecucion.ERROR

        finally:
            fin = datetime.now()
            resultado.tiempo_ejecucion_segundos = (fin - inicio).total_seconds()

            # Actualizar plan
            plan.fecha_ejecucion = inicio
            plan.registros_exitosos = resultado.registros_exitosos
            plan.registros_fallidos = resultado.registros_fallidos
            plan.resultado_ejecucion = (
                "Completado exitosamente" if resultado.exitoso
                else f"Completado con {resultado.registros_fallidos} errores"
            )

            # Registrar en auditoría
            self._registrar_auditoria(
                plan.id_plan,
                "EJECUCION",
                usuario,
                f"Procesados: {resultado.registros_procesados}, "
                f"Exitosos: {resultado.registros_exitosos}, "
                f"Fallidos: {resultado.registros_fallidos}"
            )

            logger.info(
                f"{'✅' if resultado.exitoso else '⚠️'} "
                f"Plan {plan.id_plan} completado en "
                f"{resultado.tiempo_ejecucion_segundos:.2f}s - "
                f"{resultado.porcentaje_exito:.1f}% éxito"
            )

        return resultado

    def _ejecutar_operacion(
        self,
        registro: RegistroAfectado,
        usuario: str
    ) -> bool:
        """
        Ejecuta una operación individual en la base de datos.

        En modo desarrollo/demo, simula la ejecución.
        En producción, ejecuta contra DB2.
        """
        sql = registro.sql_generado

        # Si no hay conexión a DB2, simular
        if self.db is None:
            logger.debug(f"[SIMULACIÓN] Ejecutando: {sql[:100]}...")
            return True  # Simular éxito

        # Ejecutar en DB2
        try:
            # Agregar auditoría al registro de Manhattan
            # (Si la tabla tiene campos de auditoría)
            cursor = self.db.cursor()
            cursor.execute(sql)
            self.db.commit()
            return True

        except Exception as e:
            logger.error(f"Error ejecutando SQL: {e}")
            self.db.rollback()
            raise

    # ═══════════════════════════════════════════════════════════════
    # FUNCIONES AUXILIARES
    # ═══════════════════════════════════════════════════════════════

    def _generar_sql_update(self, registro: RegistroAfectado) -> str:
        """Genera SQL UPDATE para un registro"""
        # Construir WHERE con llaves primarias
        where_parts = [
            f"{k} = '{v}'" for k, v in registro.llave_primaria.items()
        ]
        where_clause = " AND ".join(where_parts)

        # Determinar si el valor necesita comillas
        valor = registro.valor_nuevo
        if isinstance(valor, str):
            valor_sql = f"'{valor}'"
        else:
            valor_sql = str(valor)

        sql = (
            f"UPDATE {registro.tabla} "
            f"SET {registro.campo_modificado} = {valor_sql} "
            f"WHERE {where_clause}"
        )

        return sql

    def _generar_backup(self, plan: PlanCorreccion) -> str:
        """
        Genera backup de los registros antes de modificarlos.

        Returns:
            Ruta del archivo de backup
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = self.backup_path / f"backup_{plan.id_plan}_{timestamp}.json"

        # Recopilar datos de backup
        backup_data = {
            'plan_id': plan.id_plan,
            'fecha_backup': timestamp,
            'tipo_correccion': plan.tipo.value,
            'registros': [reg.to_dict() for reg in plan.registros_afectados]
        }

        # Si hay conexión, obtener valores actuales de DB
        if self.db is not None:
            # Implementar SELECT de valores actuales
            valores_actuales = []
            for reg in plan.registros_afectados:
                try:
                    # Construir WHERE clause con llave primaria
                    where_conditions = []
                    for col, valor in reg.llave_primaria.items():
                        where_conditions.append(f"{col} = '{valor}'")
                    where_clause = " AND ".join(where_conditions)

                    # SELECT del registro actual
                    query = f"SELECT * FROM {reg.tabla} WHERE {where_clause}"
                    resultado = self.db.ejecutar_query(query)

                    if not resultado.empty:
                        valores_actuales.append({
                            'tabla': reg.tabla,
                            'llave_primaria': reg.llave_primaria,
                            'valores_actuales': resultado.iloc[0].to_dict()
                        })
                        logger.debug(f"✓ Valores actuales recuperados de {reg.tabla}")
                    else:
                        logger.warning(f"⚠️ Registro no encontrado en {reg.tabla}")
                except Exception as e:
                    logger.error(f"❌ Error recuperando valores de {reg.tabla}: {e}")

            backup_data['valores_db_actuales'] = valores_actuales

        # Guardar backup
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False)

        logger.info(f"💾 Backup generado: {backup_file}")
        return str(backup_file)

    def _registrar_auditoria(
        self,
        plan_id: str,
        accion: str,
        usuario: str,
        detalle: str
    ):
        """Registra una acción en el log de auditoría"""
        timestamp = datetime.now()

        audit_entry = {
            'timestamp': timestamp.isoformat(),
            'plan_id': plan_id,
            'accion': accion,
            'usuario': usuario,
            'detalle': detalle
        }

        # Archivo de auditoría diario
        fecha = timestamp.strftime('%Y%m%d')
        audit_file = self.audit_path / f"auditoria_{fecha}.json"

        # Cargar existente o crear nuevo
        try:
            with open(audit_file, 'r', encoding='utf-8') as f:
                auditorias = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            auditorias = []

        auditorias.append(audit_entry)

        with open(audit_file, 'w', encoding='utf-8') as f:
            json.dump(auditorias, f, indent=2, ensure_ascii=False)

    # ═══════════════════════════════════════════════════════════════
    # OPERACIONES DE CONVENIENCIA
    # ═══════════════════════════════════════════════════════════════

    def corregir_distribuciones_excedentes(
        self,
        df_excedentes: pd.DataFrame,
        oc_numero: str,
        usuario: str,
        auto_aprobar: bool = False
    ) -> Tuple[PlanCorreccion, Optional[ResultadoEjecucion]]:
        """
        Flujo completo para corregir distribuciones excedentes.

        Args:
            df_excedentes: DataFrame con distribuciones a corregir
            oc_numero: Número de OC
            usuario: Usuario que ejecuta
            auto_aprobar: Si True, aprueba y ejecuta automáticamente

        Returns:
            Tupla (plan, resultado) - resultado es None si no se ejecutó
        """
        # 1. Generar plan
        plan = self.generar_plan_distribucion_excedente(df_excedentes, oc_numero)

        # 2. Mostrar vista previa
        print(self.mostrar_vista_previa(plan))

        # 3. Exportar a Excel
        excel_path = self.exportar_plan_a_excel(plan)
        print(f"\n📁 Plan exportado para revisión: {excel_path}")

        if not auto_aprobar:
            return plan, None

        # 4. Aprobar y ejecutar
        plan = self.aprobar_plan(plan, usuario)
        resultado = self.ejecutar_plan(plan, usuario)

        return plan, resultado

    def cerrar_ocs_masivo(
        self,
        df_ocs: pd.DataFrame,
        usuario: str,
        auto_aprobar: bool = False
    ) -> Tuple[PlanCorreccion, Optional[ResultadoEjecucion]]:
        """
        Flujo completo para cerrar múltiples OCs.
        """
        plan = self.generar_plan_cambio_status(
            df_registros=df_ocs,
            tabla="ORDERS",
            campo_status="STATUS",
            nuevo_status="5",  # Cerrada
            campo_llave="ORDERKEY",
            descripcion=f"Cierre masivo de {len(df_ocs)} OCs"
        )

        print(self.mostrar_vista_previa(plan))
        excel_path = self.exportar_plan_a_excel(plan)
        print(f"\n📁 Plan exportado: {excel_path}")

        if not auto_aprobar:
            return plan, None

        plan = self.aprobar_plan(plan, usuario)
        resultado = self.ejecutar_plan(plan, usuario)

        return plan, resultado


# ═══════════════════════════════════════════════════════════════
# FUNCIONES DE CONVENIENCIA (API SIMPLE)
# ═══════════════════════════════════════════════════════════════

def crear_ejecutor(db_connection=None) -> EjecutorCorrecciones:
    """Crea una instancia del ejecutor con configuración por defecto"""
    return EjecutorCorrecciones(db_connection)


# ═══════════════════════════════════════════════════════════════
# EJEMPLO DE USO
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    print("""
    ═══════════════════════════════════════════════════════════════
    🚀 SAC 2.0 - EJECUTOR DE CORRECCIONES
    ═══════════════════════════════════════════════════════════════

    Este módulo permite ejecutar correcciones masivas en Manhattan WMS.

    Ejemplo de uso:

        from modules.ejecutor_correcciones import EjecutorCorrecciones

        # Crear ejecutor
        ejecutor = EjecutorCorrecciones(db_connection)

        # Cuando el monitor detecte anomalías, generar plan
        plan = ejecutor.generar_plan_distribucion_excedente(
            df_excedentes,
            oc_numero="C1234567"
        )

        # Revisar plan
        print(ejecutor.mostrar_vista_previa(plan))

        # Aprobar y ejecutar
        ejecutor.aprobar_plan(plan, usuario="ADMJAJA")
        resultado = ejecutor.ejecutar_plan(plan, usuario="ADMJAJA")

        print(f"Resultado: {resultado.porcentaje_exito}% éxito")

    ═══════════════════════════════════════════════════════════════
    """)

    # Demo con datos simulados
    print("\n📋 Generando plan de demostración...\n")

    # Crear ejecutor sin conexión (modo simulación)
    ejecutor = EjecutorCorrecciones()

    # Datos de ejemplo
    df_ejemplo = pd.DataFrame({
        'orderkey': ['C1234567', 'C1234567', 'C1234567'],
        'linea': ['001', '002', '003'],
        'sku': ['SKU001', 'SKU002', 'SKU003'],
        'qty_distribuida': [100, 200, 150],
        'qty_ajustada': [90, 180, 140]
    })

    # Generar plan
    plan = ejecutor.generar_plan_distribucion_excedente(df_ejemplo, "C1234567")

    # Mostrar vista previa
    print(ejecutor.mostrar_vista_previa(plan))

    # Exportar
    excel = ejecutor.exportar_plan_a_excel(plan)
    print(f"\n📁 Plan exportado a: {excel}")

    print("\n✅ Demo completado")
