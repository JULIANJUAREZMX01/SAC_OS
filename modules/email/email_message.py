"""
═══════════════════════════════════════════════════════════════
MÓDULO DE MENSAJE DE EMAIL
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Clase para construir y gestionar mensajes de correo electrónico.

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
═══════════════════════════════════════════════════════════════
"""

import os
import mimetypes
import logging
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path
import uuid

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# ENUMERACIONES
# ═══════════════════════════════════════════════════════════════

class EmailPriority(Enum):
    """Niveles de prioridad para correos electrónicos"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4

    def get_header_values(self) -> Dict[str, str]:
        """Obtiene los valores de cabecera según la prioridad"""
        if self == EmailPriority.LOW:
            return {
                'X-Priority': '5',
                'X-MSMail-Priority': 'Low',
                'Importance': 'Low'
            }
        elif self == EmailPriority.HIGH:
            return {
                'X-Priority': '2',
                'X-MSMail-Priority': 'High',
                'Importance': 'High'
            }
        elif self == EmailPriority.URGENT:
            return {
                'X-Priority': '1',
                'X-MSMail-Priority': 'High',
                'Importance': 'High'
            }
        else:  # NORMAL
            return {
                'X-Priority': '3',
                'X-MSMail-Priority': 'Normal',
                'Importance': 'Normal'
            }


# ═══════════════════════════════════════════════════════════════
# CLASE ATTACHMENT
# ═══════════════════════════════════════════════════════════════

@dataclass
class Attachment:
    """
    Representa un archivo adjunto de correo electrónico

    Attributes:
        file_path: Ruta al archivo
        filename: Nombre personalizado para el adjunto (opcional)
        content_type: Tipo MIME del archivo (detectado automáticamente si no se especifica)
        content_id: ID para imágenes inline (usado en cid:)
        is_inline: Si es True, se trata como imagen inline
    """
    file_path: str
    filename: Optional[str] = None
    content_type: Optional[str] = None
    content_id: Optional[str] = None
    is_inline: bool = False
    _content: Optional[bytes] = field(default=None, repr=False)

    def __post_init__(self):
        """Inicializa valores derivados"""
        if not self.filename:
            self.filename = os.path.basename(self.file_path)

        if not self.content_type:
            self.content_type, _ = mimetypes.guess_type(self.file_path)
            if not self.content_type:
                self.content_type = 'application/octet-stream'

        if self.is_inline and not self.content_id:
            self.content_id = str(uuid.uuid4())

    @property
    def content(self) -> bytes:
        """Lee y cachea el contenido del archivo"""
        if self._content is None:
            path = Path(self.file_path)
            if not path.exists():
                raise FileNotFoundError(f"Archivo adjunto no encontrado: {self.file_path}")
            self._content = path.read_bytes()
        return self._content

    @property
    def size(self) -> int:
        """Retorna el tamaño del archivo en bytes"""
        return len(self.content)

    def validate(self) -> bool:
        """Valida que el adjunto sea accesible y válido"""
        try:
            path = Path(self.file_path)
            if not path.exists():
                logger.error(f"❌ Archivo no existe: {self.file_path}")
                return False
            if not path.is_file():
                logger.error(f"❌ No es un archivo: {self.file_path}")
                return False
            # Intentar leer el archivo
            _ = self.content
            return True
        except Exception as e:
            logger.error(f"❌ Error validando adjunto {self.file_path}: {e}")
            return False


# ═══════════════════════════════════════════════════════════════
# CLASE EMAIL MESSAGE
# ═══════════════════════════════════════════════════════════════

@dataclass
class EmailMessage:
    """
    Representa un mensaje de correo electrónico completo

    Attributes:
        to: Lista de destinatarios principales
        subject: Asunto del correo
        body_html: Cuerpo del mensaje en HTML
        body_text: Cuerpo del mensaje en texto plano (opcional)
        cc: Lista de destinatarios en copia
        bcc: Lista de destinatarios en copia oculta
        attachments: Lista de archivos adjuntos
        priority: Nivel de prioridad del mensaje
        reply_to: Dirección de respuesta
        custom_headers: Cabeceras personalizadas
        message_id: Identificador único del mensaje
        created_at: Fecha de creación
        metadata: Datos adicionales para tracking
    """
    to: List[str]
    subject: str
    body_html: str
    body_text: Optional[str] = None
    cc: List[str] = field(default_factory=list)
    bcc: List[str] = field(default_factory=list)
    attachments: List[Attachment] = field(default_factory=list)
    priority: EmailPriority = EmailPriority.NORMAL
    reply_to: Optional[str] = None
    custom_headers: Dict[str, str] = field(default_factory=dict)
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Valida y normaliza los datos del mensaje"""
        # Normalizar listas de destinatarios
        if isinstance(self.to, str):
            self.to = [self.to]
        if isinstance(self.cc, str):
            self.cc = [self.cc]
        if isinstance(self.bcc, str):
            self.bcc = [self.bcc]

        # Filtrar listas vacías
        self.to = [e.strip() for e in self.to if e and e.strip()]
        self.cc = [e.strip() for e in self.cc if e and e.strip()]
        self.bcc = [e.strip() for e in self.bcc if e and e.strip()]

        # Generar texto plano si no existe
        if not self.body_text and self.body_html:
            self.body_text = self._html_to_text(self.body_html)

    def _html_to_text(self, html: str) -> str:
        """Convierte HTML a texto plano básico"""
        import re
        # Eliminar scripts y estilos
        text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        # Reemplazar etiquetas de bloque con saltos de línea
        text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'</p>', '\n\n', text, flags=re.IGNORECASE)
        text = re.sub(r'</div>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'</tr>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'</td>', '\t', text, flags=re.IGNORECASE)
        text = re.sub(r'</li>', '\n', text, flags=re.IGNORECASE)
        # Eliminar todas las etiquetas HTML restantes
        text = re.sub(r'<[^>]+>', '', text)
        # Decodificar entidades HTML comunes
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&quot;', '"')
        # Limpiar espacios múltiples
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        return text.strip()

    def add_attachment(self, file_path: str, filename: str = None,
                       content_type: str = None) -> None:
        """
        Agrega un archivo adjunto al mensaje

        Args:
            file_path: Ruta al archivo
            filename: Nombre personalizado (opcional)
            content_type: Tipo MIME (opcional)
        """
        attachment = Attachment(
            file_path=file_path,
            filename=filename,
            content_type=content_type
        )
        if attachment.validate():
            self.attachments.append(attachment)
            logger.info(f"📎 Adjunto agregado: {attachment.filename}")
        else:
            logger.warning(f"⚠️ No se pudo agregar adjunto: {file_path}")

    def add_inline_image(self, image_path: str, content_id: str = None) -> str:
        """
        Agrega una imagen inline al mensaje

        Args:
            image_path: Ruta a la imagen
            content_id: ID para referenciar en HTML (cid:)

        Returns:
            str: Content ID para usar en HTML (ej: cid:image123)
        """
        attachment = Attachment(
            file_path=image_path,
            content_id=content_id,
            is_inline=True
        )
        if attachment.validate():
            self.attachments.append(attachment)
            logger.info(f"🖼️ Imagen inline agregada: {attachment.filename}")
            return f"cid:{attachment.content_id}"
        else:
            logger.warning(f"⚠️ No se pudo agregar imagen inline: {image_path}")
            return ""

    def get_all_recipients(self) -> List[str]:
        """Obtiene todos los destinatarios (to + cc + bcc)"""
        return list(set(self.to + self.cc + self.bcc))

    def get_recipient_count(self) -> int:
        """Obtiene el número total de destinatarios"""
        return len(self.get_all_recipients())

    def get_attachment_count(self) -> int:
        """Obtiene el número de adjuntos"""
        return len(self.attachments)

    def get_total_attachment_size(self) -> int:
        """Obtiene el tamaño total de adjuntos en bytes"""
        return sum(att.size for att in self.attachments if att.validate())

    def validate(self) -> tuple:
        """
        Valida el mensaje completo

        Returns:
            tuple: (es_valido, lista_errores)
        """
        errors = []

        # Validar destinatarios
        if not self.to:
            errors.append("❌ Se requiere al menos un destinatario")

        for email in self.to + self.cc + self.bcc:
            if not self._is_valid_email(email):
                errors.append(f"❌ Email inválido: {email}")

        # Validar asunto
        if not self.subject or not self.subject.strip():
            errors.append("❌ Se requiere un asunto")

        # Validar cuerpo
        if not self.body_html and not self.body_text:
            errors.append("❌ Se requiere un cuerpo de mensaje")

        # Validar adjuntos
        for att in self.attachments:
            if not att.validate():
                errors.append(f"❌ Adjunto inválido: {att.file_path}")

        # Validar tamaño total (límite 25MB)
        total_size = self.get_total_attachment_size()
        if total_size > 25 * 1024 * 1024:
            errors.append(f"❌ Tamaño total de adjuntos excede 25MB: {total_size / 1024 / 1024:.2f}MB")

        return len(errors) == 0, errors

    @staticmethod
    def _is_valid_email(email: str) -> bool:
        """Valida formato básico de email"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email.strip()))

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el mensaje a diccionario para serialización"""
        return {
            'message_id': self.message_id,
            'to': self.to,
            'cc': self.cc,
            'bcc': self.bcc,
            'subject': self.subject,
            'body_html': self.body_html,
            'body_text': self.body_text,
            'priority': self.priority.name,
            'reply_to': self.reply_to,
            'attachments': [att.filename for att in self.attachments],
            'created_at': self.created_at.isoformat(),
            'metadata': self.metadata
        }

    def __str__(self) -> str:
        """Representación en string del mensaje"""
        return (
            f"EmailMessage("
            f"to={self.to}, "
            f"subject='{self.subject[:30]}...', "
            f"attachments={self.get_attachment_count()}, "
            f"priority={self.priority.name})"
        )


# ═══════════════════════════════════════════════════════════════
# EJEMPLO DE USO
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("""
    ═══════════════════════════════════════════════════════════════
    MÓDULO EMAIL MESSAGE - CHEDRAUI CEDIS
    ═══════════════════════════════════════════════════════════════
    """)

    # Ejemplo de creación de mensaje
    mensaje = EmailMessage(
        to=["usuario@chedraui.com.mx"],
        cc=["supervisor@chedraui.com.mx"],
        subject="📊 Reporte Diario - CEDIS Cancún",
        body_html="<html><body><h1>Reporte</h1><p>Contenido del reporte</p></body></html>",
        priority=EmailPriority.HIGH
    )

    print(f"✅ Mensaje creado: {mensaje}")
    print(f"   Destinatarios totales: {mensaje.get_recipient_count()}")

    # Validar
    es_valido, errores = mensaje.validate()
    if es_valido:
        print("✅ Mensaje válido")
    else:
        print("❌ Errores de validación:")
        for error in errores:
            print(f"   {error}")
