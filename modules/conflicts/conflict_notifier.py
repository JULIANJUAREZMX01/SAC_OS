"""
===============================================================================
MÓDULO DE NOTIFICACIONES DE CONFLICTOS - SISTEMA SAC
Sistema de Automatización de Consultas - CEDIS Cancún 427
===============================================================================

Gestiona las notificaciones y alertas relacionadas con conflictos externos,
incluyendo alertas al analista en turno y respuestas automáticas a correos.

Funcionalidades:
- Alertas de "ERROR NO DETECTADO A TIEMPO"
- Notificaciones al analista en turno
- Respuesta automática al correo original
- Envío de documentación generada
- Resumen de conflictos pendientes

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
===============================================================================
"""

import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from .conflict_storage import (
    ConflictoExterno,
    EstadoConflicto,
    TipoEvento,
    obtener_storage
)
from .conflict_analyzer import ResultadoAnalisis

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# ENUMERACIONES Y DATACLASSES
# ═══════════════════════════════════════════════════════════════

class TipoNotificacion(Enum):
    """Tipos de notificación"""
    ALERTA_ERROR_NO_DETECTADO = "ALERTA_ERROR_NO_DETECTADO"
    SOLICITUD_CONFIRMACION = "SOLICITUD_CONFIRMACION"
    CONFIRMACION_RECIBIDA = "CONFIRMACION_RECIBIDA"
    RESOLUCION_COMPLETADA = "RESOLUCION_COMPLETADA"
    RESOLUCION_FALLIDA = "RESOLUCION_FALLIDA"
    CONFLICTO_ESCALADO = "CONFLICTO_ESCALADO"
    RESPUESTA_A_REMITENTE = "RESPUESTA_A_REMITENTE"
    RESUMEN_PENDIENTES = "RESUMEN_PENDIENTES"


@dataclass
class Notificacion:
    """Representa una notificación a enviar"""
    tipo: TipoNotificacion
    destinatarios: List[str]
    asunto: str
    cuerpo_html: str
    cuerpo_texto: str
    adjuntos: List[str] = field(default_factory=list)
    prioridad: str = "normal"  # urgent, high, normal, low
    conflicto_id: Optional[str] = None
    fecha_creacion: datetime = field(default_factory=datetime.now)
    enviado: bool = False
    fecha_envio: Optional[datetime] = None
    error_envio: Optional[str] = None


# ═══════════════════════════════════════════════════════════════
# TEMPLATES DE EMAIL
# ═══════════════════════════════════════════════════════════════

ESTILOS_EMAIL = """
<style>
    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
    .container { max-width: 700px; margin: 0 auto; padding: 20px; }
    .header { background: linear-gradient(135deg, #E31837 0%, #B31530 100%);
              color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }
    .header h1 { margin: 0; font-size: 24px; }
    .header .emoji { font-size: 32px; margin-bottom: 10px; }
    .content { background: #ffffff; padding: 25px; border: 1px solid #ddd; }
    .alert-box { background: #FFF3CD; border-left: 4px solid #FFC107;
                 padding: 15px; margin: 15px 0; border-radius: 4px; }
    .critical-box { background: #F8D7DA; border-left: 4px solid #DC3545;
                    padding: 15px; margin: 15px 0; border-radius: 4px; }
    .success-box { background: #D4EDDA; border-left: 4px solid #28A745;
                   padding: 15px; margin: 15px 0; border-radius: 4px; }
    .info-box { background: #D1ECF1; border-left: 4px solid #17A2B8;
                padding: 15px; margin: 15px 0; border-radius: 4px; }
    .data-table { width: 100%; border-collapse: collapse; margin: 15px 0; }
    .data-table th, .data-table td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
    .data-table th { background: #f5f5f5; font-weight: bold; }
    .badge { display: inline-block; padding: 3px 8px; border-radius: 4px;
             font-size: 12px; font-weight: bold; }
    .badge-critical { background: #DC3545; color: white; }
    .badge-high { background: #FFC107; color: #333; }
    .badge-medium { background: #17A2B8; color: white; }
    .badge-resolved { background: #28A745; color: white; }
    .button { display: inline-block; padding: 12px 24px; background: #E31837;
              color: white; text-decoration: none; border-radius: 4px;
              font-weight: bold; margin: 10px 5px 10px 0; }
    .button-secondary { background: #6c757d; }
    .footer { background: #f5f5f5; padding: 15px; text-align: center;
              font-size: 12px; color: #666; border-radius: 0 0 8px 8px; }
    .divider { border-top: 1px solid #ddd; margin: 20px 0; }
    .highlight { background: #FFFDE7; padding: 2px 5px; border-radius: 3px; }
</style>
"""

TEMPLATE_ALERTA_NO_DETECTADO = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    {estilos}
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="emoji">⚠️🔴</div>
            <h1>ERROR NO DETECTADO A TIEMPO</h1>
            <p>Sistema SAC - CEDIS Cancún 427</p>
        </div>

        <div class="content">
            <div class="critical-box">
                <strong>⚡ ATENCIÓN REQUERIDA:</strong><br>
                Se ha identificado un conflicto que NO fue detectado por el sistema de monitoreo
                y fue reportado externamente por correo electrónico.
            </div>

            <h3>📋 Detalles del Conflicto</h3>
            <table class="data-table">
                <tr>
                    <th>ID Conflicto</th>
                    <td><span class="highlight">{conflicto_id}</span></td>
                </tr>
                <tr>
                    <th>Tipo</th>
                    <td>{tipo_conflicto}</td>
                </tr>
                <tr>
                    <th>Severidad</th>
                    <td><span class="badge badge-critical">{severidad}</span></td>
                </tr>
                <tr>
                    <th>Fecha Detección</th>
                    <td>{fecha_deteccion}</td>
                </tr>
            </table>

            <h3>📧 Correo Original</h3>
            <table class="data-table">
                <tr>
                    <th>De</th>
                    <td>{remitente_email} ({remitente_nombre})</td>
                </tr>
                <tr>
                    <th>Asunto</th>
                    <td>{correo_asunto}</td>
                </tr>
                <tr>
                    <th>Fecha</th>
                    <td>{correo_fecha}</td>
                </tr>
            </table>

            <h3>📦 Datos Afectados</h3>
            <table class="data-table">
                <tr>
                    <th>OCs</th>
                    <td>{ocs}</td>
                </tr>
                <tr>
                    <th>Tiendas</th>
                    <td>{tiendas}</td>
                </tr>
            </table>

            <div class="divider"></div>

            <h3>🔧 Acción Requerida</h3>
            <p>
                Por favor revise este conflicto y confirme la acción a tomar.
                El sistema ha generado sugerencias de resolución que requieren
                su aprobación antes de ejecutarse.
            </p>

            <p>
                <strong>Opciones:</strong>
            </p>
            <ul>
                <li>✅ <strong>APROBAR</strong> - Ejecutar la resolución sugerida</li>
                <li>❌ <strong>RECHAZAR</strong> - El conflicto no es válido</li>
                <li>✏️ <strong>MODIFICAR</strong> - Ajustar la acción antes de ejecutar</li>
                <li>⬆️ <strong>ESCALAR</strong> - Enviar a supervisor</li>
            </ul>

            <p style="text-align: center; margin-top: 20px;">
                <a href="#" class="button">Revisar Conflicto en SAC</a>
            </p>
        </div>

        <div class="footer">
            <p>
                <strong>Sistema SAC - CEDIS Cancún 427</strong><br>
                Tiendas Chedraui S.A. de C.V. - Región Sureste<br>
                Este es un mensaje automático generado por el sistema.
            </p>
        </div>
    </div>
</body>
</html>
"""

TEMPLATE_RESOLUCION_COMPLETADA = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    {estilos}
</head>
<body>
    <div class="container">
        <div class="header" style="background: linear-gradient(135deg, #28A745 0%, #1E7E34 100%);">
            <div class="emoji">✅</div>
            <h1>CONFLICTO RESUELTO</h1>
            <p>Sistema SAC - CEDIS Cancún 427</p>
        </div>

        <div class="content">
            <div class="success-box">
                <strong>✅ RESOLUCIÓN EXITOSA:</strong><br>
                El conflicto ha sido resuelto satisfactoriamente.
            </div>

            <h3>📋 Resumen de Resolución</h3>
            <table class="data-table">
                <tr>
                    <th>ID Conflicto</th>
                    <td>{conflicto_id}</td>
                </tr>
                <tr>
                    <th>Tipo</th>
                    <td>{tipo_conflicto}</td>
                </tr>
                <tr>
                    <th>Estado Final</th>
                    <td><span class="badge badge-resolved">RESUELTO</span></td>
                </tr>
                <tr>
                    <th>Resuelto Por</th>
                    <td>{resuelto_por}</td>
                </tr>
                <tr>
                    <th>Fecha Resolución</th>
                    <td>{fecha_resolucion}</td>
                </tr>
            </table>

            <h3>🔧 Acciones Ejecutadas</h3>
            <div class="info-box">
                {acciones_ejecutadas}
            </div>

            <h3>📝 Notas de Resolución</h3>
            <p>{notas_resolucion}</p>

            <div class="divider"></div>

            <p>
                Se adjunta documentación completa del ciclo de detección,
                análisis y resolución del conflicto.
            </p>
        </div>

        <div class="footer">
            <p>
                <strong>Sistema SAC - CEDIS Cancún 427</strong><br>
                Tiendas Chedraui S.A. de C.V. - Región Sureste
            </p>
        </div>
    </div>
</body>
</html>
"""

TEMPLATE_RESPUESTA_REMITENTE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    {estilos}
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="emoji">📧</div>
            <h1>RE: {asunto_original}</h1>
            <p>Sistema SAC - CEDIS Cancún 427</p>
        </div>

        <div class="content">
            <p>Estimado/a {nombre_remitente},</p>

            <p>
                Hemos recibido y procesado su reporte sobre el conflicto mencionado.
                A continuación, le informamos el estado actual:
            </p>

            <div class="{clase_estado}">
                <strong>Estado: {estado}</strong><br>
                {mensaje_estado}
            </div>

            <h3>📋 Detalles del Seguimiento</h3>
            <table class="data-table">
                <tr>
                    <th>ID de Seguimiento</th>
                    <td><span class="highlight">{conflicto_id}</span></td>
                </tr>
                <tr>
                    <th>Fecha de Recepción</th>
                    <td>{fecha_recepcion}</td>
                </tr>
                <tr>
                    <th>Fecha de Actualización</th>
                    <td>{fecha_actualizacion}</td>
                </tr>
                <tr>
                    <th>Asignado a</th>
                    <td>{asignado_a}</td>
                </tr>
            </table>

            {seccion_resolucion}

            <div class="divider"></div>

            <p>
                Si tiene alguna pregunta adicional sobre este caso, por favor
                responda a este correo incluyendo el ID de seguimiento:
                <strong>{conflicto_id}</strong>
            </p>

            <p>Atentamente,<br>
            <strong>Sistema de Automatización de Consultas (SAC)</strong><br>
            CEDIS Cancún 427 - Tiendas Chedraui</p>
        </div>

        <div class="footer">
            <p>
                Este es un mensaje automático del Sistema SAC.<br>
                Para más información, contacte al equipo de Sistemas CEDIS 427.
            </p>
        </div>
    </div>
</body>
</html>
"""


# ═══════════════════════════════════════════════════════════════
# CLASE PRINCIPAL: NOTIFICADOR DE CONFLICTOS
# ═══════════════════════════════════════════════════════════════

class ConflictNotifier:
    """
    Gestiona las notificaciones relacionadas con conflictos externos.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Inicializa el notificador.

        Args:
            config: Configuración opcional con:
                - analista_turno_email: Email del analista en turno
                - supervisor_email: Email del supervisor
                - usar_gestor_correos: Si usar GestorCorreos existente
        """
        self.config = config or {}
        self.storage = obtener_storage()

        # Obtener configuración de email
        try:
            from config import EMAIL_CONFIG
            self.email_config = EMAIL_CONFIG
        except ImportError:
            self.email_config = {}

        # Email del analista en turno
        self.analista_turno = self.config.get(
            'analista_turno_email',
            self.email_config.get('to_emails', ['planning@chedraui.com.mx'])[0]
        )

        logger.info(f"🔔 ConflictNotifier inicializado")
        logger.info(f"   Analista en turno: {self.analista_turno}")

    def _obtener_gestor_correos(self):
        """Obtiene instancia del GestorCorreos"""
        try:
            from gestor_correos import GestorCorreos
            return GestorCorreos(self.email_config)
        except ImportError:
            logger.warning("⚠️ GestorCorreos no disponible")
            return None

    def notificar_error_no_detectado(
        self,
        conflicto_id: str,
        analisis: ResultadoAnalisis = None
    ) -> bool:
        """
        Envía alerta de "ERROR NO DETECTADO A TIEMPO" al analista.

        Args:
            conflicto_id: ID del conflicto
            analisis: Resultado del análisis (opcional)

        Returns:
            True si se envió correctamente
        """
        conflicto = self.storage.obtener(conflicto_id)
        if not conflicto:
            logger.error(f"❌ Conflicto {conflicto_id} no encontrado")
            return False

        logger.info(f"🔔 Enviando alerta de error no detectado: {conflicto_id}")

        # Preparar datos
        datos = {
            'estilos': ESTILOS_EMAIL,
            'conflicto_id': conflicto.id,
            'tipo_conflicto': conflicto.tipo_conflicto,
            'severidad': conflicto.severidad,
            'fecha_deteccion': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'remitente_email': conflicto.correo_remitente_email,
            'remitente_nombre': conflicto.correo_remitente_nombre,
            'correo_asunto': conflicto.correo_asunto,
            'correo_fecha': conflicto.correo_fecha.strftime('%Y-%m-%d %H:%M'),
            'ocs': ', '.join(conflicto.oc_numeros) or 'No especificadas',
            'tiendas': ', '.join(conflicto.tiendas_afectadas) or 'No especificadas'
        }

        html = TEMPLATE_ALERTA_NO_DETECTADO.format(**datos)
        asunto = f"⚠️ ERROR NO DETECTADO - {conflicto.tipo_conflicto} - {conflicto_id}"

        # Crear notificación
        notificacion = Notificacion(
            tipo=TipoNotificacion.ALERTA_ERROR_NO_DETECTADO,
            destinatarios=[self.analista_turno],
            asunto=asunto,
            cuerpo_html=html,
            cuerpo_texto=self._html_a_texto(html),
            prioridad="urgent",
            conflicto_id=conflicto_id
        )

        # Enviar
        exito = self._enviar_notificacion(notificacion)

        if exito:
            conflicto.cambiar_estado(EstadoConflicto.NOTIFICADO)
            conflicto.agregar_evento(
                TipoEvento.NOTIFICACION_ENVIADA,
                f"Alerta enviada a {self.analista_turno}"
            )
            self.storage.actualizar(conflicto)

        return exito

    def notificar_resolucion_completada(
        self,
        conflicto_id: str,
        resuelto_por: str,
        acciones: List[str],
        notas: str = ""
    ) -> bool:
        """
        Notifica que un conflicto ha sido resuelto.

        Args:
            conflicto_id: ID del conflicto
            resuelto_por: Usuario que resolvió
            acciones: Lista de acciones ejecutadas
            notas: Notas adicionales

        Returns:
            True si se envió correctamente
        """
        conflicto = self.storage.obtener(conflicto_id)
        if not conflicto:
            return False

        logger.info(f"🔔 Notificando resolución de {conflicto_id}")

        datos = {
            'estilos': ESTILOS_EMAIL,
            'conflicto_id': conflicto.id,
            'tipo_conflicto': conflicto.tipo_conflicto,
            'resuelto_por': resuelto_por,
            'fecha_resolucion': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'acciones_ejecutadas': '<br>'.join([f'• {a}' for a in acciones]) if acciones else 'N/A',
            'notas_resolucion': notas or 'Sin notas adicionales'
        }

        html = TEMPLATE_RESOLUCION_COMPLETADA.format(**datos)
        asunto = f"✅ CONFLICTO RESUELTO - {conflicto_id}"

        notificacion = Notificacion(
            tipo=TipoNotificacion.RESOLUCION_COMPLETADA,
            destinatarios=[self.analista_turno],
            asunto=asunto,
            cuerpo_html=html,
            cuerpo_texto=self._html_a_texto(html),
            adjuntos=[conflicto.archivo_reporte] if conflicto.archivo_reporte else [],
            conflicto_id=conflicto_id
        )

        return self._enviar_notificacion(notificacion)

    def responder_a_remitente(
        self,
        conflicto_id: str,
        incluir_documentacion: bool = True
    ) -> bool:
        """
        Envía respuesta al remitente original del correo.

        Args:
            conflicto_id: ID del conflicto
            incluir_documentacion: Si adjuntar documentación

        Returns:
            True si se envió correctamente
        """
        conflicto = self.storage.obtener(conflicto_id)
        if not conflicto:
            return False

        logger.info(f"📧 Respondiendo a remitente original: {conflicto.correo_remitente_email}")

        # Determinar estado y mensaje
        if conflicto.estado == EstadoConflicto.RESUELTO:
            clase_estado = "success-box"
            estado = "RESUELTO"
            mensaje_estado = "El problema ha sido identificado y corregido exitosamente."
            seccion_resolucion = f"""
            <h3>✅ Resolución Aplicada</h3>
            <p>{conflicto.notas_resolucion or 'Se aplicaron las correcciones necesarias.'}</p>
            """
        elif conflicto.estado == EstadoConflicto.ESCALADO:
            clase_estado = "alert-box"
            estado = "ESCALADO"
            mensaje_estado = "El caso ha sido escalado a supervisión para su revisión."
            seccion_resolucion = ""
        elif conflicto.estado == EstadoConflicto.EN_RESOLUCION:
            clase_estado = "info-box"
            estado = "EN PROCESO"
            mensaje_estado = "Estamos trabajando activamente en la resolución."
            seccion_resolucion = ""
        else:
            clase_estado = "info-box"
            estado = "EN REVISIÓN"
            mensaje_estado = "Su reporte está siendo analizado por nuestro equipo."
            seccion_resolucion = ""

        datos = {
            'estilos': ESTILOS_EMAIL,
            'asunto_original': conflicto.correo_asunto,
            'nombre_remitente': conflicto.correo_remitente_nombre or 'Usuario',
            'clase_estado': clase_estado,
            'estado': estado,
            'mensaje_estado': mensaje_estado,
            'conflicto_id': conflicto.id,
            'fecha_recepcion': conflicto.correo_fecha.strftime('%Y-%m-%d %H:%M'),
            'fecha_actualizacion': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'asignado_a': conflicto.asignado_a or 'Equipo de Sistemas',
            'seccion_resolucion': seccion_resolucion
        }

        html = TEMPLATE_RESPUESTA_REMITENTE.format(**datos)
        asunto = f"RE: {conflicto.correo_asunto} [ID: {conflicto.id}]"

        adjuntos = []
        if incluir_documentacion and conflicto.archivo_reporte:
            adjuntos.append(conflicto.archivo_reporte)

        notificacion = Notificacion(
            tipo=TipoNotificacion.RESPUESTA_A_REMITENTE,
            destinatarios=[conflicto.correo_remitente_email],
            asunto=asunto,
            cuerpo_html=html,
            cuerpo_texto=self._html_a_texto(html),
            adjuntos=adjuntos,
            conflicto_id=conflicto_id
        )

        exito = self._enviar_notificacion(notificacion)

        if exito:
            conflicto.correo_respuesta_id = f"RESP-{conflicto_id}-{datetime.now().strftime('%H%M%S')}"
            conflicto.agregar_evento(
                TipoEvento.RESPUESTA_ENVIADA,
                f"Respuesta enviada a {conflicto.correo_remitente_email}"
            )
            self.storage.actualizar(conflicto)

        return exito

    def enviar_resumen_pendientes(
        self,
        destinatario: str = None
    ) -> bool:
        """
        Envía resumen de conflictos pendientes.

        Args:
            destinatario: Email destino (default: analista en turno)

        Returns:
            True si se envió
        """
        pendientes = self.storage.listar_pendientes()

        if not pendientes:
            logger.info("ℹ️ No hay conflictos pendientes para reportar")
            return True

        destinatario = destinatario or self.analista_turno

        # Construir tabla de pendientes
        filas = []
        for c in pendientes:
            filas.append(f"""
            <tr>
                <td><a href="#">{c.id}</a></td>
                <td>{c.tipo_conflicto}</td>
                <td><span class="badge badge-{'critical' if '🔴' in c.severidad else 'high'}">{c.severidad}</span></td>
                <td>{c.estado.value}</td>
                <td>{c.fecha_creacion.strftime('%Y-%m-%d %H:%M')}</td>
            </tr>
            """)

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            {ESTILOS_EMAIL}
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="emoji">📋</div>
                    <h1>CONFLICTOS PENDIENTES</h1>
                    <p>Sistema SAC - CEDIS Cancún 427</p>
                </div>

                <div class="content">
                    <div class="alert-box">
                        <strong>⚠️ Hay {len(pendientes)} conflicto(s) pendiente(s) de resolución.</strong>
                    </div>

                    <table class="data-table">
                        <tr>
                            <th>ID</th>
                            <th>Tipo</th>
                            <th>Severidad</th>
                            <th>Estado</th>
                            <th>Fecha</th>
                        </tr>
                        {''.join(filas)}
                    </table>

                    <p style="text-align: center; margin-top: 20px;">
                        <a href="#" class="button">Ver en SAC</a>
                    </p>
                </div>

                <div class="footer">
                    <p>Sistema SAC - CEDIS Cancún 427</p>
                </div>
            </div>
        </body>
        </html>
        """

        notificacion = Notificacion(
            tipo=TipoNotificacion.RESUMEN_PENDIENTES,
            destinatarios=[destinatario],
            asunto=f"📋 Resumen: {len(pendientes)} Conflictos Pendientes - SAC",
            cuerpo_html=html,
            cuerpo_texto=self._html_a_texto(html)
        )

        return self._enviar_notificacion(notificacion)

    def _enviar_notificacion(self, notificacion: Notificacion) -> bool:
        """
        Envía una notificación por correo.

        Args:
            notificacion: Notificación a enviar

        Returns:
            True si se envió correctamente
        """
        gestor = self._obtener_gestor_correos()

        if gestor:
            try:
                # Usar GestorCorreos existente
                resultado = gestor._enviar_correo(
                    destinatarios=notificacion.destinatarios,
                    asunto=notificacion.asunto,
                    cuerpo_html=notificacion.cuerpo_html,
                    archivos_adjuntos=notificacion.adjuntos if notificacion.adjuntos else None
                )

                if resultado:
                    notificacion.enviado = True
                    notificacion.fecha_envio = datetime.now()
                    logger.info(f"✅ Notificación enviada: {notificacion.tipo.value}")
                    return True
                else:
                    notificacion.error_envio = "Error al enviar"
                    logger.error(f"❌ Error enviando notificación")
                    return False

            except Exception as e:
                notificacion.error_envio = str(e)
                logger.error(f"❌ Error enviando notificación: {e}")
                return False
        else:
            # Modo simulación - solo loguear
            logger.info(f"📧 [SIMULACIÓN] Notificación preparada:")
            logger.info(f"   Tipo: {notificacion.tipo.value}")
            logger.info(f"   Para: {notificacion.destinatarios}")
            logger.info(f"   Asunto: {notificacion.asunto}")
            notificacion.enviado = True
            notificacion.fecha_envio = datetime.now()
            return True

    def _html_a_texto(self, html: str) -> str:
        """Convierte HTML a texto plano simple"""
        import re
        # Remover tags HTML
        texto = re.sub(r'<[^>]+>', '', html)
        # Limpiar espacios múltiples
        texto = re.sub(r'\s+', ' ', texto)
        # Limpiar líneas vacías múltiples
        texto = re.sub(r'\n\s*\n', '\n\n', texto)
        return texto.strip()


# ═══════════════════════════════════════════════════════════════
# FUNCIONES DE UTILIDAD
# ═══════════════════════════════════════════════════════════════

def alertar_conflicto_no_detectado(conflicto_id: str) -> bool:
    """
    Función de conveniencia para alertar un conflicto.

    Args:
        conflicto_id: ID del conflicto

    Returns:
        True si se alertó correctamente
    """
    notifier = ConflictNotifier()
    return notifier.notificar_error_no_detectado(conflicto_id)


# ═══════════════════════════════════════════════════════════════
# EJEMPLO DE USO
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║  🔔 NOTIFICADOR DE CONFLICTOS - SISTEMA SAC                   ║
    ║  Sistema de Automatización de Consultas - CEDIS Cancún 427    ║
    ╚═══════════════════════════════════════════════════════════════╝

    Este módulo gestiona las notificaciones de conflictos:
    - Alertas "ERROR NO DETECTADO A TIEMPO"
    - Notificaciones al analista en turno
    - Respuestas automáticas al remitente
    - Resúmenes de conflictos pendientes

    Uso:
        from modules.conflicts import ConflictNotifier

        notifier = ConflictNotifier()

        # Alertar conflicto
        notifier.notificar_error_no_detectado("CONF-20251122-001")

        # Responder al remitente
        notifier.responder_a_remitente("CONF-20251122-001")

        # Enviar resumen
        notifier.enviar_resumen_pendientes()
    """)
