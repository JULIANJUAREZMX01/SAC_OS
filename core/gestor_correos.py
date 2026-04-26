"""
═══════════════════════════════════════════════════════════════
MÓDULO DE ENVÍO AUTOMÁTICO DE CORREOS - VERSIÓN EXPANDIDA
Sistema de Gestión de Órdenes de Compra - Chedraui CEDIS
═══════════════════════════════════════════════════════════════

Este módulo gestiona el envío automático de correos:
- 8 tipos de correos diferentes
- Sistema de templates profesionales
- Cola de envío con reintentos
- Programación de notificaciones
- Gestión de destinatarios

Tipos de correos soportados:
1. Reporte Planning Diario
2. Alerta Crítica
3. Validación OC
4. Programa de Recibo
5. Resumen Semanal (NUEVO)
6. Notificación de Error (NUEVO)
7. Recordatorio (NUEVO)
8. Confirmación de Proceso (NUEVO)

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
═══════════════════════════════════════════════════════════════
"""

import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
import pandas as pd

# Importar módulo de email expandido
from modules.email import (
    EmailClient,
    EmailMessage,
    EmailPriority,
    EmailTemplateEngine,
    EmailQueue,
    RecipientsManager,
    RecipientCategory
)

logger = logging.getLogger(__name__)


class GestorCorreos:
    """
    Gestor de correos electrónicos automáticos - Versión Expandida

    Envía reportes, alertas y notificaciones al equipo de Planning
    utilizando el nuevo sistema de email con templates profesionales.

    Características:
    - 8 tipos de correos diferentes
    - Templates HTML profesionales
    - Cola de envío con reintentos
    - Programación de notificaciones
    - Gestión de destinatarios por categoría
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa el gestor de correos

        Args:
            config: Diccionario con configuración SMTP
        """
        self.email_client = EmailClient(config)
        self.template_engine = EmailTemplateEngine()
        self.recipients_manager = RecipientsManager()
        self.email_queue = EmailQueue()
        self.from_name = config.get('from_name', 'Sistema SAC - CEDIS 427')
        self.cedis_nombre = config.get('cedis_nombre', 'CEDIS Cancún 427')
        self._stats = {'total_enviados': 0, 'total_fallidos': 0, 'por_tipo': {}}
        logger.info(f"✅ GestorCorreos inicializado - {self.cedis_nombre}")

    def enviar_reporte_planning_diario(
        self, destinatarios: List[str], df_oc: pd.DataFrame,
        df_asn: pd.DataFrame, archivos_adjuntos: List[str] = None,
        datos_adicionales: Dict = None
    ) -> bool:
        """Envía reporte diario de Planning"""
        try:
            fecha = datetime.now().strftime('%d/%m/%Y')
            total_oc = len(df_oc) if df_oc is not None and not df_oc.empty else 0
            total_asn = len(df_asn) if df_asn is not None and not df_asn.empty else 0

            context = {
                'titulo': 'REPORTE PLANNING DIARIO',
                'total_oc': str(total_oc),
                'total_asn': str(total_asn),
                'total_distribuciones': datos_adicionales.get('total_distribuciones', '0') if datos_adicionales else '0',
                'total_alertas': datos_adicionales.get('total_alertas', '0') if datos_adicionales else '0',
                'tabla_oc': self._generar_tabla_html(df_oc, ['OC', 'PROVEEDOR', 'FECHA', 'STATUS']) if df_oc is not None and not df_oc.empty else '',
                'tabla_asn': self._generar_tabla_html(df_asn, ['ASN', 'OC', 'ETA', 'STATUS']) if df_asn is not None and not df_asn.empty else '',
            }
            if datos_adicionales:
                context.update(datos_adicionales)

            html_body = self.template_engine.render_template('daily_report', context)
            mensaje = EmailMessage(
                to=destinatarios,
                subject=f"📊 Reporte Planning Diario - {self.cedis_nombre} - {fecha}",
                body_html=html_body, priority=EmailPriority.NORMAL
            )
            if archivos_adjuntos:
                for archivo in archivos_adjuntos:
                    mensaje.add_attachment(archivo)

            resultado = self._enviar_mensaje(mensaje)
            self._registrar_envio('reporte_planning_diario', resultado)
            if resultado:
                logger.info(f"✅ Reporte diario enviado a {len(destinatarios)} destinatarios")
            return resultado
        except Exception as e:
            logger.error(f"❌ Error al enviar reporte planning diario: {str(e)}")
            return False

    def enviar_alerta_critica(
        self, destinatarios: List[str], tipo_error: str, descripcion: str,
        oc_numero: str = None, datos_adicionales: Dict = None, severidad: str = "CRITICO"
    ) -> bool:
        """Envía alerta crítica inmediata"""
        try:
            info_oc = f"<tr><td>Orden de Compra:</td><td><strong>{oc_numero}</strong></td></tr>" if oc_numero else ""
            info_adicional = ""
            if datos_adicionales:
                for clave, valor in datos_adicionales.items():
                    info_adicional += f"<tr><td>{clave}:</td><td>{valor}</td></tr>"

            context = {
                'tipo_error': tipo_error,
                'descripcion_error': descripcion,
                'severidad': severidad,
                'severidad_clase': severidad.lower(),
                'modulo': datos_adicionales.get('modulo', 'Sistema SAC') if datos_adicionales else 'Sistema SAC',
                'info_oc': info_oc,
                'info_adicional': info_adicional,
            }
            html_body = self.template_engine.render_template('critical_alert', context)
            asunto = f"🚨 ALERTA CRÍTICA - {tipo_error}"
            if oc_numero:
                asunto += f" - OC {oc_numero}"

            mensaje = EmailMessage(to=destinatarios, subject=asunto, body_html=html_body, priority=EmailPriority.URGENT)
            resultado = self._enviar_mensaje(mensaje)
            self._registrar_envio('alerta_critica', resultado)
            if resultado:
                logger.info(f"🚨 Alerta crítica enviada: {tipo_error}")
            return resultado
        except Exception as e:
            logger.error(f"❌ Error al enviar alerta crítica: {str(e)}")
            return False

    def enviar_validacion_oc(
        self, destinatarios: List[str], oc_numero: str, status_validacion: str,
        detalles: Dict, archivo_excel: str = None
    ) -> bool:
        """Envía resultado de validación de OC"""
        try:
            status_config = {
                'OK': {'clase': 'ok', 'icono': '✅', 'mensaje': 'La orden de compra ha sido validada correctamente.'},
                'ALERTA': {'clase': 'warning', 'icono': '⚠️', 'mensaje': 'Se detectaron discrepancias que requieren revisión.'},
                'CRITICO': {'clase': 'error', 'icono': '🔴', 'mensaje': 'Se detectaron errores críticos.'}
            }
            config = status_config.get(status_validacion, status_config['ALERTA'])

            context = {
                'oc_numero': oc_numero, 'status_validacion': status_validacion,
                'status_clase': config['clase'], 'status_icono': config['icono'],
                'status_mensaje': config['mensaje'],
                'proveedor': detalles.get('proveedor', 'N/A'),
                'fecha_oc': detalles.get('fecha_oc', 'N/A'),
                'total_skus': detalles.get('total_skus', '0'),
            }
            html_body = self.template_engine.render_template('oc_validation', context)
            mensaje = EmailMessage(
                to=destinatarios,
                subject=f"{config['icono']} Validación OC {oc_numero} - {status_validacion}",
                body_html=html_body,
                priority=EmailPriority.HIGH if status_validacion == 'CRITICO' else EmailPriority.NORMAL
            )
            if archivo_excel:
                mensaje.add_attachment(archivo_excel)

            resultado = self._enviar_mensaje(mensaje)
            self._registrar_envio('validacion_oc', resultado)
            return resultado
        except Exception as e:
            logger.error(f"❌ Error al enviar validación OC: {str(e)}")
            return False

    def enviar_programa_recibo(
        self, destinatarios: List[str], fecha_recibo: str,
        lista_asn: List[Dict], archivo_excel: str = None
    ) -> bool:
        """Envía programa de recibo diario"""
        try:
            total_asn = len(lista_asn)
            proveedores = set(asn.get('proveedor', '') for asn in lista_asn)
            total_unidades = sum(asn.get('unidades', 0) for asn in lista_asn)

            tabla_asn = ""
            for asn in lista_asn:
                status_clase = 'status-confirmado' if asn.get('status') == 'CONFIRMADO' else 'status-pendiente'
                tabla_asn += f"<tr><td>{asn.get('asn', 'N/A')}</td><td>{asn.get('proveedor', 'N/A')}</td><td>{asn.get('oc', 'N/A')}</td><td>{asn.get('unidades', 0)}</td><td>{asn.get('eta', 'N/A')}</td><td><span class='status-badge {status_clase}'>{asn.get('status', 'PENDIENTE')}</span></td></tr>"

            context = {
                'fecha_recibo': fecha_recibo, 'total_asn': str(total_asn),
                'total_proveedores': str(len(proveedores)), 'total_unidades': str(total_unidades),
                'tabla_asn': tabla_asn,
            }
            html_body = self.template_engine.render_template('reception_program', context)
            mensaje = EmailMessage(to=destinatarios, subject=f"📦 Programa de Recibo - {fecha_recibo}", body_html=html_body)
            if archivo_excel:
                mensaje.add_attachment(archivo_excel)

            resultado = self._enviar_mensaje(mensaje)
            self._registrar_envio('programa_recibo', resultado)
            return resultado
        except Exception as e:
            logger.error(f"❌ Error al enviar programa de recibo: {str(e)}")
            return False

    def enviar_resumen_semanal(
        self, destinatarios: List[str], periodo: str, kpis: Dict[str, Any],
        datos_proveedores: List[Dict] = None, logros: List[str] = None, oportunidades: List[str] = None
    ) -> bool:
        """Envía resumen semanal de operaciones"""
        try:
            tabla_proveedores = ""
            if datos_proveedores:
                for i, prov in enumerate(datos_proveedores[:5], 1):
                    tabla_proveedores += f"<tr><td>{i}</td><td>{prov.get('nombre', 'N/A')}</td><td>{prov.get('oc', 0)}</td><td>{prov.get('unidades', 0)}</td><td>{prov.get('cumplimiento', 'N/A')}</td></tr>"

            logros_html = "".join(f"<li>{l}</li>" for l in (logros or []))
            oportunidades_html = "".join(f"<li>{o}</li>" for o in (oportunidades or []))

            context = {
                'periodo_semana': periodo,
                'oc_procesadas': str(kpis.get('oc_procesadas', 0)),
                'asn_recibidos': str(kpis.get('asn_recibidos', 0)),
                'unidades_procesadas': str(kpis.get('unidades_procesadas', 0)),
                'precision_pct': f"{kpis.get('precision', 0)}%",
                'cumplimiento_pct': str(kpis.get('cumplimiento', 0)),
                'cumplimiento_clase': 'good' if kpis.get('cumplimiento', 0) >= 90 else 'warning',
                'tabla_proveedores': tabla_proveedores,
                'logros_semana': logros_html,
                'oportunidades_mejora': oportunidades_html,
            }
            html_body = self.template_engine.render_template('weekly_summary', context)
            mensaje = EmailMessage(to=destinatarios, subject=f"📈 Resumen Semanal - {self.cedis_nombre} - {periodo}", body_html=html_body)
            resultado = self._enviar_mensaje(mensaje)
            self._registrar_envio('resumen_semanal', resultado)
            return resultado
        except Exception as e:
            logger.error(f"❌ Error al enviar resumen semanal: {str(e)}")
            return False

    def enviar_notificacion_error(
        self, destinatarios: List[str], tipo_error: str, mensaje_error: str,
        modulo_origen: str, severidad: str = "MEDIO", stack_trace: str = None,
        pasos_resolver: List[str] = None
    ) -> bool:
        """Envía notificación de error del sistema"""
        try:
            pasos_html = "".join(f"<li>{p}</li>" for p in (pasos_resolver or ['Revisar los logs del sistema', 'Verificar la configuración', 'Contactar a Sistemas']))
            context = {
                'tipo_error': tipo_error, 'mensaje_error': mensaje_error,
                'modulo_origen': modulo_origen, 'severidad': severidad,
                'severidad_clase': severidad.lower(),
                'error_id': f"ERR-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                'stack_trace': stack_trace or "No disponible",
                'pasos_resolver': pasos_html,
            }
            html_body = self.template_engine.render_template('error_notification', context)
            mensaje = EmailMessage(
                to=destinatarios, subject=f"⚠️ Error en Sistema - {tipo_error} [{severidad}]",
                body_html=html_body, priority=EmailPriority.HIGH if severidad == "ALTO" else EmailPriority.NORMAL
            )
            resultado = self._enviar_mensaje(mensaje)
            self._registrar_envio('notificacion_error', resultado)
            return resultado
        except Exception as e:
            logger.error(f"❌ Error al enviar notificación de error: {str(e)}")
            return False

    def enviar_recordatorio(
        self, destinatarios: List[str], titulo: str, mensaje: str,
        fecha_limite: str = None, tareas: List[Dict] = None
    ) -> bool:
        """Envía recordatorio de tareas pendientes"""
        try:
            lista_tareas = ""
            if tareas:
                for t in tareas:
                    completed = 'completed' if t.get('completada', False) else ''
                    priority = f"priority-{t.get('prioridad', 'normal').lower()}"
                    lista_tareas += f"<div class='task-item {completed}'><div class='checkbox'></div><span>{t.get('nombre', 'Tarea')}</span><span class='priority-indicator {priority}'>{t.get('prioridad', 'Normal')}</span></div>"

            context = {'titulo_recordatorio': titulo, 'mensaje_recordatorio': mensaje, 'fecha_limite': fecha_limite or "No especificada", 'lista_tareas': lista_tareas}
            html_body = self.template_engine.render_template('reminder', context)
            mensaje_email = EmailMessage(to=destinatarios, subject=f"🔔 Recordatorio: {titulo}", body_html=html_body)
            resultado = self._enviar_mensaje(mensaje_email)
            self._registrar_envio('recordatorio', resultado)
            return resultado
        except Exception as e:
            logger.error(f"❌ Error al enviar recordatorio: {str(e)}")
            return False

    def enviar_confirmacion_proceso(
        self, destinatarios: List[str], titulo: str, mensaje: str,
        numero_referencia: str, tipo_proceso: str, detalles: Dict = None,
        proximos_pasos: List[str] = None
    ) -> bool:
        """Envía confirmación de proceso completado"""
        try:
            tabla_resultados = ""
            if detalles:
                for clave, valor in detalles.items():
                    tabla_resultados += f"<tr><td style='padding: 10px; border-bottom: 1px solid #e0e0e0; font-weight: bold;'>{clave}:</td><td style='padding: 10px; border-bottom: 1px solid #e0e0e0;'>{valor}</td></tr>"

            pasos_html = "".join(f"<li>{p}</li>" for p in (proximos_pasos or []))
            context = {
                'titulo_confirmacion': titulo, 'mensaje_confirmacion': mensaje,
                'numero_referencia': numero_referencia, 'tipo_proceso': tipo_proceso,
                'fecha_fin': datetime.now().strftime('%d/%m/%Y %H:%M'),
                'tabla_resultados': tabla_resultados, 'proximos_pasos': pasos_html,
            }
            html_body = self.template_engine.render_template('confirmation', context)
            mensaje_email = EmailMessage(to=destinatarios, subject=f"✅ Confirmación: {titulo} - Ref: {numero_referencia}", body_html=html_body)
            resultado = self._enviar_mensaje(mensaje_email)
            self._registrar_envio('confirmacion_proceso', resultado)
            return resultado
        except Exception as e:
            logger.error(f"❌ Error al enviar confirmación: {str(e)}")
            return False

    def enviar_reporte_kpis(self, destinatarios: List[str], kpis: Dict[str, Any], periodo: str = "Diario") -> bool:
        """Envía reporte de KPIs"""
        return self.enviar_resumen_semanal(destinatarios=destinatarios, periodo=f"KPIs - {periodo}", kpis=kpis)

    def enviar_alerta_inventario(self, destinatarios: List[str], tipo_alerta: str, items_afectados: List[Dict], detalles: Dict = None) -> bool:
        """Envía alerta de inventario"""
        return self.enviar_alerta_critica(
            destinatarios=destinatarios, tipo_error=f"ALERTA INVENTARIO - {tipo_alerta}",
            descripcion=f"Se detectaron {len(items_afectados)} items con problemas de inventario.",
            datos_adicionales={'modulo': 'Inventario', 'items_afectados': len(items_afectados), **(detalles or {})},
            severidad="ALTO"
        )

    def enviar_hito_sistema(
        self, destinatarios: List[str], titulo_hito: str, subtitulo: str,
        mensaje: str, fecha_activacion: str, tipo_hito: str = "NUEVO HITO",
        funcionalidades: List[str] = None, horarios: Dict[str, str] = None,
        nota_importante: str = None, version: str = "1.0.0"
    ) -> bool:
        """
        Envía notificación de hito del sistema (lanzamiento, actualización, etc.)

        Args:
            destinatarios: Lista de emails
            titulo_hito: Título principal del hito
            subtitulo: Subtítulo descriptivo
            mensaje: Mensaje principal del hito
            fecha_activacion: Fecha de activación del sistema
            tipo_hito: Tipo de hito (LANZAMIENTO, ACTUALIZACION, etc.)
            funcionalidades: Lista de funcionalidades activas
            horarios: Dict con horarios de ejecución {hora: descripción}
            nota_importante: Nota importante para los usuarios
            version: Versión del sistema

        Returns:
            bool: True si el envío fue exitoso
        """
        try:
            # Generar lista de funcionalidades HTML
            lista_func = ""
            if funcionalidades:
                for i, func in enumerate(funcionalidades, 1):
                    lista_func += f'<li><span class="feature-icon">{i}</span>{func}</li>'

            # Generar tabla de horarios HTML
            tabla_horarios = ""
            if horarios:
                for hora, descripcion in horarios.items():
                    tabla_horarios += f'<div class="schedule-row"><div class="schedule-time">{hora}</div><div class="schedule-task">{descripcion}</div></div>'

            context = {
                'titulo_hito': titulo_hito,
                'subtitulo_hito': subtitulo,
                'tipo_hito': tipo_hito,
                'mensaje_hito': mensaje,
                'fecha_activacion': fecha_activacion,
                'version_sistema': version,
                'estado_sistema': 'OPERATIVO',
                'lista_funcionalidades': lista_func,
                'tabla_horarios': tabla_horarios,
                'nota_importante': nota_importante or 'El sistema funcionará de manera automática en los horarios indicados.',
            }

            html_body = self.template_engine.render_template('system_milestone', context)

            mensaje_email = EmailMessage(
                to=destinatarios,
                subject=f"🚀 {tipo_hito} - {titulo_hito}",
                body_html=html_body,
                priority=EmailPriority.HIGH
            )

            resultado = self._enviar_mensaje(mensaje_email)
            self._registrar_envio('hito_sistema', resultado)

            if resultado:
                logger.info(f"🚀 Notificación de hito enviada: {titulo_hito}")

            return resultado

        except Exception as e:
            logger.error(f"❌ Error al enviar hito del sistema: {str(e)}")
            return False

    def _enviar_mensaje(self, mensaje: EmailMessage) -> bool:
        """Envía un mensaje utilizando el cliente de email"""
        try:
            return self.email_client.send(mensaje)
        except Exception as e:
            logger.error(f"❌ Error enviando mensaje: {e}")
            return False

    def _generar_tabla_html(self, df: pd.DataFrame, columnas: List[str]) -> str:
        """Genera HTML de tabla desde DataFrame"""
        if df is None or df.empty:
            return ""
        html = ""
        for _, row in df.head(10).iterrows():
            html += "<tr>"
            for col in columnas:
                html += f"<td>{row.get(col, 'N/A')}</td>" if col in df.columns else "<td>N/A</td>"
            html += "</tr>"
        return html

    def _registrar_envio(self, tipo: str, exito: bool):
        """Registra estadísticas de envío"""
        key = 'total_enviados' if exito else 'total_fallidos'
        self._stats[key] += 1
        if tipo not in self._stats['por_tipo']:
            self._stats['por_tipo'][tipo] = {'enviados': 0, 'fallidos': 0}
        self._stats['por_tipo'][tipo]['enviados' if exito else 'fallidos'] += 1

    def obtener_estadisticas(self) -> Dict[str, Any]:
        """Obtiene estadísticas de envío"""
        total = self._stats['total_enviados'] + self._stats['total_fallidos']
        return {**self._stats, 'tasa_exito': f"{(self._stats['total_enviados'] / max(total, 1)) * 100:.1f}%"}

    def probar_conexion(self) -> bool:
        """Prueba la conexión al servidor de correo"""
        return self.email_client.test_connection()

    def obtener_destinatarios(self, categoria: RecipientCategory) -> List[str]:
        """Obtiene destinatarios por categoría"""
        return self.recipients_manager.get_recipients(categoria)


if __name__ == "__main__":
    print("""
    ═══════════════════════════════════════════════════════════════
    GESTOR DE CORREOS AUTOMÁTICOS - CHEDRAUI CEDIS
    Versión Expandida con 8 Tipos de Correos
    ═══════════════════════════════════════════════════════════════
    """)
    print("✅ Módulo de correos cargado correctamente")
    print("📧 8 tipos de correos + 2 métodos auxiliares disponibles")
