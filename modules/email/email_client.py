"""
═══════════════════════════════════════════════════════════════
CLIENTE DE EMAIL SMTP
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Cliente SMTP robusto con soporte para Office 365, TLS y gestión
de conexiones.

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
═══════════════════════════════════════════════════════════════
"""

import smtplib
import ssl
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email import encoders
from email.utils import formataddr, formatdate, make_msgid
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
import time
import threading

from .email_message import EmailMessage, EmailPriority, Attachment

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# ESTADÍSTICAS DE ENVÍO
# ═══════════════════════════════════════════════════════════════

@dataclass
class SendStats:
    """Estadísticas de envío de correos"""
    total_sent: int = 0
    total_failed: int = 0
    total_recipients: int = 0
    total_attachments: int = 0
    total_bytes_sent: int = 0
    last_send_time: Optional[datetime] = None
    last_error: Optional[str] = None
    errors_by_type: Dict[str, int] = field(default_factory=dict)

    def record_success(self, message: EmailMessage):
        """Registra un envío exitoso"""
        self.total_sent += 1
        self.total_recipients += message.get_recipient_count()
        self.total_attachments += message.get_attachment_count()
        self.total_bytes_sent += message.get_total_attachment_size()
        self.last_send_time = datetime.now()

    def record_failure(self, error: str, error_type: str = "UNKNOWN"):
        """Registra un fallo de envío"""
        self.total_failed += 1
        self.last_error = error
        self.errors_by_type[error_type] = self.errors_by_type.get(error_type, 0) + 1

    def get_success_rate(self) -> float:
        """Calcula la tasa de éxito"""
        total = self.total_sent + self.total_failed
        if total == 0:
            return 0.0
        return (self.total_sent / total) * 100

    def to_dict(self) -> Dict[str, Any]:
        """Convierte las estadísticas a diccionario"""
        return {
            'total_sent': self.total_sent,
            'total_failed': self.total_failed,
            'total_recipients': self.total_recipients,
            'total_attachments': self.total_attachments,
            'total_bytes_sent': self.total_bytes_sent,
            'success_rate': f"{self.get_success_rate():.1f}%",
            'last_send_time': self.last_send_time.isoformat() if self.last_send_time else None,
            'last_error': self.last_error,
            'errors_by_type': self.errors_by_type
        }


# ═══════════════════════════════════════════════════════════════
# CLIENTE DE EMAIL
# ═══════════════════════════════════════════════════════════════

class EmailClient:
    """
    Cliente SMTP para envío de correos electrónicos

    Soporta:
    - Office 365 con TLS
    - Reconexión automática
    - Estadísticas de envío
    - Envío en lotes
    - Gestión de adjuntos e imágenes inline

    Ejemplo de uso:
        config = {
            'smtp_server': 'smtp.office365.com',
            'smtp_port': 587,
            'user': 'correo@chedraui.com.mx',
            'password': 'password',
            'from_name': 'Sistema SAC',
            'use_tls': True
        }

        client = EmailClient(config)
        if client.connect():
            client.send(mensaje)
            client.disconnect()
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa el cliente de email

        Args:
            config: Diccionario de configuración con:
                - smtp_server: Servidor SMTP
                - smtp_port: Puerto SMTP
                - user: Usuario/email de autenticación
                - password: Contraseña
                - from_name: Nombre del remitente (opcional)
                - from_email: Email del remitente (opcional, usa user si no se especifica)
                - use_tls: Usar TLS (default True)
                - timeout: Timeout de conexión en segundos (default 30)
        """
        self.smtp_server = config.get('smtp_server', 'smtp.office365.com')
        self.smtp_port = config.get('smtp_port', 587)
        self.user = config.get('user', '')
        self.password = config.get('password', '')
        self.from_name = config.get('from_name', 'Sistema SAC - CEDIS 427')
        self.from_email = config.get('from_email', self.user)
        self.use_tls = config.get('use_tls', True)
        self.timeout = config.get('timeout', 30)

        self._server: Optional[smtplib.SMTP] = None
        self._connected = False
        self._lock = threading.Lock()
        self._stats = SendStats()

        logger.info(f"📧 EmailClient inicializado: {self.smtp_server}:{self.smtp_port}")

    # ═══════════════════════════════════════════════════════════════
    # GESTIÓN DE CONEXIÓN
    # ═══════════════════════════════════════════════════════════════

    def connect(self) -> bool:
        """
        Establece conexión con el servidor SMTP

        Returns:
            bool: True si la conexión fue exitosa
        """
        with self._lock:
            try:
                if self._connected and self._server:
                    # Verificar si la conexión sigue activa
                    try:
                        self._server.noop()
                        return True
                    except Exception:
                        self._connected = False

                logger.info(f"📧 Conectando a {self.smtp_server}:{self.smtp_port}...")

                # Crear conexión
                self._server = smtplib.SMTP(
                    self.smtp_server,
                    self.smtp_port,
                    timeout=self.timeout
                )

                # Habilitar modo debug si está configurado
                # self._server.set_debuglevel(1)

                # EHLO
                self._server.ehlo()

                # Iniciar TLS si está habilitado
                if self.use_tls:
                    context = ssl.create_default_context()
                    self._server.starttls(context=context)
                    self._server.ehlo()

                # Autenticar
                self._server.login(self.user, self.password)

                self._connected = True
                logger.info(f"✅ Conectado exitosamente a {self.smtp_server}")
                return True

            except smtplib.SMTPAuthenticationError as e:
                logger.error(f"❌ Error de autenticación SMTP: {e}")
                self._stats.record_failure(str(e), "AUTH_ERROR")
                self._connected = False
                return False

            except smtplib.SMTPConnectError as e:
                logger.error(f"❌ Error de conexión SMTP: {e}")
                self._stats.record_failure(str(e), "CONNECT_ERROR")
                self._connected = False
                return False

            except Exception as e:
                logger.error(f"❌ Error inesperado al conectar: {e}")
                self._stats.record_failure(str(e), "UNKNOWN_ERROR")
                self._connected = False
                return False

    def disconnect(self) -> None:
        """Cierra la conexión SMTP"""
        with self._lock:
            if self._server:
                try:
                    self._server.quit()
                    logger.info("✅ Desconectado del servidor SMTP")
                except Exception as e:
                    logger.warning(f"⚠️ Error al desconectar: {e}")
                finally:
                    self._server = None
                    self._connected = False

    def is_connected(self) -> bool:
        """Verifica si hay una conexión activa"""
        return self._connected and self._server is not None

    def test_connection(self) -> bool:
        """
        Prueba la conexión al servidor SMTP

        Returns:
            bool: True si la conexión funciona correctamente
        """
        try:
            was_connected = self._connected

            if not self._connected:
                if not self.connect():
                    return False

            # Probar con NOOP
            self._server.noop()

            if not was_connected:
                self.disconnect()

            logger.info("✅ Prueba de conexión exitosa")
            return True

        except Exception as e:
            logger.error(f"❌ Prueba de conexión fallida: {e}")
            return False

    # ═══════════════════════════════════════════════════════════════
    # ENVÍO DE CORREOS
    # ═══════════════════════════════════════════════════════════════

    def send(self, message: EmailMessage, retry_count: int = 3,
             retry_delay: float = 2.0) -> bool:
        """
        Envía un mensaje de correo electrónico

        Args:
            message: Objeto EmailMessage a enviar
            retry_count: Número de reintentos en caso de fallo
            retry_delay: Segundos entre reintentos

        Returns:
            bool: True si el envío fue exitoso
        """
        # Validar mensaje
        is_valid, errors = message.validate()
        if not is_valid:
            logger.error(f"❌ Mensaje inválido: {errors}")
            self._stats.record_failure(str(errors), "VALIDATION_ERROR")
            return False

        for attempt in range(retry_count):
            try:
                # Asegurar conexión
                if not self._connected:
                    if not self.connect():
                        continue

                # Construir mensaje MIME
                mime_message = self._build_mime_message(message)

                # Obtener todos los destinatarios
                all_recipients = message.get_all_recipients()

                # Enviar
                with self._lock:
                    self._server.send_message(
                        mime_message,
                        from_addr=self.from_email,
                        to_addrs=all_recipients
                    )

                # Registrar éxito
                self._stats.record_success(message)
                logger.info(
                    f"✅ Correo enviado exitosamente: "
                    f"'{message.subject[:40]}...' a {len(all_recipients)} destinatario(s)"
                )
                return True

            except smtplib.SMTPServerDisconnected:
                logger.warning(f"⚠️ Servidor desconectado, reintentando... ({attempt + 1}/{retry_count})")
                self._connected = False
                time.sleep(retry_delay)

            except smtplib.SMTPRecipientsRefused as e:
                logger.error(f"❌ Destinatarios rechazados: {e}")
                self._stats.record_failure(str(e), "RECIPIENTS_REFUSED")
                return False

            except smtplib.SMTPDataError as e:
                logger.error(f"❌ Error de datos SMTP: {e}")
                self._stats.record_failure(str(e), "DATA_ERROR")
                if attempt < retry_count - 1:
                    time.sleep(retry_delay)

            except Exception as e:
                logger.error(f"❌ Error al enviar correo: {e}")
                self._stats.record_failure(str(e), "UNKNOWN_ERROR")
                if attempt < retry_count - 1:
                    time.sleep(retry_delay)

        logger.error(f"❌ Falló el envío después de {retry_count} intentos")
        return False

    def send_batch(self, messages: List[EmailMessage],
                   continue_on_error: bool = True) -> Dict[str, bool]:
        """
        Envía múltiples mensajes en lote

        Args:
            messages: Lista de mensajes a enviar
            continue_on_error: Si continuar enviando tras un error

        Returns:
            Dict[str, bool]: Diccionario {message_id: resultado}
        """
        results = {}

        if not messages:
            logger.warning("⚠️ Lista de mensajes vacía")
            return results

        logger.info(f"📧 Iniciando envío en lote de {len(messages)} correos...")

        # Conectar una vez para todo el lote
        if not self._connected:
            if not self.connect():
                logger.error("❌ No se pudo establecer conexión para envío en lote")
                return {msg.message_id: False for msg in messages}

        for i, message in enumerate(messages, 1):
            try:
                success = self.send(message, retry_count=2)
                results[message.message_id] = success

                if not success and not continue_on_error:
                    logger.warning(f"⚠️ Deteniendo envío en lote tras fallo en mensaje {i}")
                    break

                # Pequeña pausa entre envíos para evitar rate limiting
                if i < len(messages):
                    time.sleep(0.5)

            except Exception as e:
                logger.error(f"❌ Error en mensaje {i}: {e}")
                results[message.message_id] = False
                if not continue_on_error:
                    break

        # Resumen
        sent = sum(1 for v in results.values() if v)
        failed = len(results) - sent
        logger.info(f"📊 Envío en lote completado: {sent} exitosos, {failed} fallidos")

        return results

    # ═══════════════════════════════════════════════════════════════
    # CONSTRUCCIÓN DE MENSAJE MIME
    # ═══════════════════════════════════════════════════════════════

    def _build_mime_message(self, message: EmailMessage) -> MIMEMultipart:
        """
        Construye el mensaje MIME completo

        Args:
            message: EmailMessage a convertir

        Returns:
            MIMEMultipart: Mensaje MIME listo para enviar
        """
        # Determinar tipo de mensaje
        has_inline = any(att.is_inline for att in message.attachments)
        has_attachments = any(not att.is_inline for att in message.attachments)

        if has_inline or has_attachments:
            mime_msg = MIMEMultipart('mixed')
        else:
            mime_msg = MIMEMultipart('alternative')

        # Cabeceras básicas
        mime_msg['From'] = formataddr((self.from_name, self.from_email))
        mime_msg['To'] = ', '.join(message.to)
        if message.cc:
            mime_msg['Cc'] = ', '.join(message.cc)
        mime_msg['Subject'] = message.subject
        mime_msg['Date'] = formatdate(localtime=True)
        mime_msg['Message-ID'] = make_msgid(domain=self.from_email.split('@')[-1])

        # Reply-To
        if message.reply_to:
            mime_msg['Reply-To'] = message.reply_to

        # Cabeceras de prioridad
        priority_headers = message.priority.get_header_values()
        for header, value in priority_headers.items():
            mime_msg[header] = value

        # Cabeceras personalizadas
        for header, value in message.custom_headers.items():
            mime_msg[header] = value

        # Cuerpo del mensaje
        if has_inline:
            # Crear parte relacionada para imágenes inline
            related = MIMEMultipart('related')
            alternative = MIMEMultipart('alternative')

            if message.body_text:
                text_part = MIMEText(message.body_text, 'plain', 'utf-8')
                alternative.attach(text_part)

            html_part = MIMEText(message.body_html, 'html', 'utf-8')
            alternative.attach(html_part)
            related.attach(alternative)

            # Agregar imágenes inline
            for att in message.attachments:
                if att.is_inline:
                    img = MIMEImage(att.content)
                    img.add_header('Content-ID', f'<{att.content_id}>')
                    img.add_header('Content-Disposition', 'inline',
                                   filename=att.filename)
                    related.attach(img)

            mime_msg.attach(related)
        else:
            # Sin imágenes inline
            alternative = MIMEMultipart('alternative')

            if message.body_text:
                text_part = MIMEText(message.body_text, 'plain', 'utf-8')
                alternative.attach(text_part)

            html_part = MIMEText(message.body_html, 'html', 'utf-8')
            alternative.attach(html_part)

            if has_attachments:
                mime_msg.attach(alternative)
            else:
                return alternative  # Retornar solo alternative si no hay adjuntos

        # Agregar adjuntos regulares
        for att in message.attachments:
            if not att.is_inline:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(att.content)
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename="{att.filename}"'
                )
                if att.content_type:
                    part.set_type(att.content_type)
                mime_msg.attach(part)

        return mime_msg

    # ═══════════════════════════════════════════════════════════════
    # ESTADÍSTICAS
    # ═══════════════════════════════════════════════════════════════

    def get_send_stats(self) -> Dict[str, Any]:
        """
        Obtiene las estadísticas de envío

        Returns:
            Dict: Estadísticas de envío
        """
        return self._stats.to_dict()

    def reset_stats(self) -> None:
        """Reinicia las estadísticas de envío"""
        self._stats = SendStats()
        logger.info("📊 Estadísticas de envío reiniciadas")

    # ═══════════════════════════════════════════════════════════════
    # CONTEXT MANAGER
    # ═══════════════════════════════════════════════════════════════

    def __enter__(self):
        """Soporte para context manager"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cierra conexión al salir del context"""
        self.disconnect()
        return False


# ═══════════════════════════════════════════════════════════════
# EJEMPLO DE USO
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("""
    ═══════════════════════════════════════════════════════════════
    CLIENTE DE EMAIL SMTP - CHEDRAUI CEDIS
    ═══════════════════════════════════════════════════════════════
    """)

    # Configuración de ejemplo
    config = {
        'smtp_server': 'smtp.office365.com',
        'smtp_port': 587,
        'user': 'ejemplo@chedraui.com.mx',
        'password': 'password',
        'from_name': 'Sistema SAC - CEDIS 427',
        'use_tls': True
    }

    print("✅ Módulo EmailClient cargado correctamente\n")
    print("📧 Uso con context manager:")
    print("""
    with EmailClient(config) as client:
        mensaje = EmailMessage(
            to=["usuario@chedraui.com.mx"],
            subject="Prueba",
            body_html="<h1>Hola</h1>"
        )
        client.send(mensaje)
    """)
