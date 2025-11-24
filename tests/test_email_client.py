"""
═══════════════════════════════════════════════════════════════
TESTS PARA EMAIL CLIENT
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Tests unitarios para el cliente de email y componentes relacionados.

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
═══════════════════════════════════════════════════════════════
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import sys
import os

# Agregar path del proyecto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.email.email_message import EmailMessage, EmailPriority, Attachment
from modules.email.email_client import EmailClient, SendStats


# ═══════════════════════════════════════════════════════════════
# TESTS PARA EMAIL MESSAGE
# ═══════════════════════════════════════════════════════════════

class TestEmailMessage:
    """Tests para la clase EmailMessage"""

    def test_crear_mensaje_basico(self):
        """Test de creación de mensaje básico"""
        mensaje = EmailMessage(
            to=["usuario@chedraui.com.mx"],
            subject="Prueba",
            body_html="<h1>Hola</h1>"
        )

        assert mensaje.to == ["usuario@chedraui.com.mx"]
        assert mensaje.subject == "Prueba"
        assert mensaje.body_html == "<h1>Hola</h1>"
        assert mensaje.priority == EmailPriority.NORMAL

    def test_crear_mensaje_con_cc_bcc(self):
        """Test de mensaje con CC y BCC"""
        mensaje = EmailMessage(
            to=["usuario@chedraui.com.mx"],
            cc=["cc@chedraui.com.mx"],
            bcc=["bcc@chedraui.com.mx"],
            subject="Prueba",
            body_html="<h1>Hola</h1>"
        )

        assert mensaje.cc == ["cc@chedraui.com.mx"]
        assert mensaje.bcc == ["bcc@chedraui.com.mx"]
        assert mensaje.get_recipient_count() == 3

    def test_normalizar_destinatarios(self):
        """Test de normalización de destinatarios (string a lista)"""
        mensaje = EmailMessage(
            to="usuario@chedraui.com.mx",
            subject="Prueba",
            body_html="<h1>Hola</h1>"
        )

        assert isinstance(mensaje.to, list)
        assert len(mensaje.to) == 1

    def test_prioridad_alta(self):
        """Test de mensaje con prioridad alta"""
        mensaje = EmailMessage(
            to=["usuario@chedraui.com.mx"],
            subject="Urgente",
            body_html="<h1>Urgente</h1>",
            priority=EmailPriority.URGENT
        )

        headers = mensaje.priority.get_header_values()
        assert headers['X-Priority'] == '1'
        assert headers['Importance'] == 'High'

    def test_validacion_mensaje_valido(self):
        """Test de validación de mensaje válido"""
        mensaje = EmailMessage(
            to=["usuario@chedraui.com.mx"],
            subject="Prueba",
            body_html="<h1>Hola</h1>"
        )

        es_valido, errores = mensaje.validate()
        assert es_valido
        assert len(errores) == 0

    def test_validacion_mensaje_sin_destinatarios(self):
        """Test de validación - mensaje sin destinatarios"""
        mensaje = EmailMessage(
            to=[],
            subject="Prueba",
            body_html="<h1>Hola</h1>"
        )

        es_valido, errores = mensaje.validate()
        assert not es_valido
        assert any("destinatario" in e.lower() for e in errores)

    def test_validacion_mensaje_sin_asunto(self):
        """Test de validación - mensaje sin asunto"""
        mensaje = EmailMessage(
            to=["usuario@chedraui.com.mx"],
            subject="",
            body_html="<h1>Hola</h1>"
        )

        es_valido, errores = mensaje.validate()
        assert not es_valido
        assert any("asunto" in e.lower() for e in errores)

    def test_validacion_email_invalido(self):
        """Test de validación - email inválido"""
        mensaje = EmailMessage(
            to=["email_invalido"],
            subject="Prueba",
            body_html="<h1>Hola</h1>"
        )

        es_valido, errores = mensaje.validate()
        assert not es_valido
        assert any("inválido" in e.lower() for e in errores)

    def test_conversion_html_a_texto(self):
        """Test de conversión HTML a texto plano"""
        mensaje = EmailMessage(
            to=["usuario@chedraui.com.mx"],
            subject="Prueba",
            body_html="<html><body><h1>Titulo</h1><p>Contenido</p></body></html>"
        )

        assert mensaje.body_text is not None
        assert "Titulo" in mensaje.body_text
        assert "Contenido" in mensaje.body_text

    def test_obtener_todos_destinatarios(self):
        """Test de obtención de todos los destinatarios"""
        mensaje = EmailMessage(
            to=["to@chedraui.com.mx"],
            cc=["cc@chedraui.com.mx"],
            bcc=["bcc@chedraui.com.mx"],
            subject="Prueba",
            body_html="<h1>Hola</h1>"
        )

        all_recipients = mensaje.get_all_recipients()
        assert len(all_recipients) == 3
        assert "to@chedraui.com.mx" in all_recipients
        assert "cc@chedraui.com.mx" in all_recipients
        assert "bcc@chedraui.com.mx" in all_recipients

    def test_to_dict(self):
        """Test de conversión a diccionario"""
        mensaje = EmailMessage(
            to=["usuario@chedraui.com.mx"],
            subject="Prueba",
            body_html="<h1>Hola</h1>",
            priority=EmailPriority.HIGH
        )

        data = mensaje.to_dict()
        assert data['to'] == ["usuario@chedraui.com.mx"]
        assert data['subject'] == "Prueba"
        assert data['priority'] == "HIGH"


# ═══════════════════════════════════════════════════════════════
# TESTS PARA EMAIL PRIORITY
# ═══════════════════════════════════════════════════════════════

class TestEmailPriority:
    """Tests para EmailPriority"""

    def test_prioridad_baja(self):
        """Test de headers para prioridad baja"""
        headers = EmailPriority.LOW.get_header_values()
        assert headers['X-Priority'] == '5'
        assert headers['Importance'] == 'Low'

    def test_prioridad_normal(self):
        """Test de headers para prioridad normal"""
        headers = EmailPriority.NORMAL.get_header_values()
        assert headers['X-Priority'] == '3'
        assert headers['Importance'] == 'Normal'

    def test_prioridad_alta(self):
        """Test de headers para prioridad alta"""
        headers = EmailPriority.HIGH.get_header_values()
        assert headers['X-Priority'] == '2'
        assert headers['Importance'] == 'High'

    def test_prioridad_urgente(self):
        """Test de headers para prioridad urgente"""
        headers = EmailPriority.URGENT.get_header_values()
        assert headers['X-Priority'] == '1'
        assert headers['Importance'] == 'High'


# ═══════════════════════════════════════════════════════════════
# TESTS PARA SEND STATS
# ═══════════════════════════════════════════════════════════════

class TestSendStats:
    """Tests para SendStats"""

    def test_registrar_exito(self):
        """Test de registro de envío exitoso"""
        stats = SendStats()
        mensaje = EmailMessage(
            to=["usuario@chedraui.com.mx"],
            subject="Prueba",
            body_html="<h1>Hola</h1>"
        )

        stats.record_success(mensaje)

        assert stats.total_sent == 1
        assert stats.total_recipients == 1
        assert stats.last_send_time is not None

    def test_registrar_fallo(self):
        """Test de registro de fallo"""
        stats = SendStats()
        stats.record_failure("Error de conexión", "CONNECT_ERROR")

        assert stats.total_failed == 1
        assert stats.last_error == "Error de conexión"
        assert stats.errors_by_type["CONNECT_ERROR"] == 1

    def test_tasa_exito(self):
        """Test de cálculo de tasa de éxito"""
        stats = SendStats()
        stats.total_sent = 8
        stats.total_failed = 2

        assert stats.get_success_rate() == 80.0

    def test_tasa_exito_sin_envios(self):
        """Test de tasa de éxito sin envíos"""
        stats = SendStats()
        assert stats.get_success_rate() == 0.0

    def test_to_dict(self):
        """Test de conversión a diccionario"""
        stats = SendStats()
        stats.total_sent = 10
        stats.total_failed = 2

        data = stats.to_dict()
        assert data['total_sent'] == 10
        assert data['total_failed'] == 2
        assert 'success_rate' in data


# ═══════════════════════════════════════════════════════════════
# TESTS PARA EMAIL CLIENT
# ═══════════════════════════════════════════════════════════════

class TestEmailClient:
    """Tests para EmailClient"""

    @pytest.fixture
    def config(self):
        """Configuración de prueba"""
        return {
            'smtp_server': 'smtp.test.com',
            'smtp_port': 587,
            'user': 'test@test.com',
            'password': 'password',
            'from_name': 'Test System',
            'use_tls': True
        }

    @pytest.fixture
    def client(self, config):
        """Cliente de prueba"""
        return EmailClient(config)

    def test_inicializacion(self, client, config):
        """Test de inicialización del cliente"""
        assert client.smtp_server == config['smtp_server']
        assert client.smtp_port == config['smtp_port']
        assert client.user == config['user']
        assert client.from_name == config['from_name']
        assert not client.is_connected()

    @patch('smtplib.SMTP')
    def test_conexion_exitosa(self, mock_smtp, client):
        """Test de conexión exitosa"""
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server

        result = client.connect()

        assert result
        assert client.is_connected()
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once()

    @patch('smtplib.SMTP')
    def test_desconexion(self, mock_smtp, client):
        """Test de desconexión"""
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server

        client.connect()
        client.disconnect()

        assert not client.is_connected()
        mock_server.quit.assert_called_once()

    @patch('smtplib.SMTP')
    def test_envio_exitoso(self, mock_smtp, client):
        """Test de envío exitoso"""
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server

        mensaje = EmailMessage(
            to=["usuario@test.com"],
            subject="Prueba",
            body_html="<h1>Hola</h1>"
        )

        result = client.send(mensaje)

        assert result
        mock_server.send_message.assert_called_once()

    def test_envio_mensaje_invalido(self, client):
        """Test de envío con mensaje inválido"""
        mensaje = EmailMessage(
            to=[],
            subject="",
            body_html=""
        )

        result = client.send(mensaje)

        assert not result

    def test_estadisticas_iniciales(self, client):
        """Test de estadísticas iniciales"""
        stats = client.get_send_stats()

        assert stats['total_sent'] == 0
        assert stats['total_failed'] == 0

    def test_reset_estadisticas(self, client):
        """Test de reseteo de estadísticas"""
        client._stats.total_sent = 10
        client.reset_stats()

        stats = client.get_send_stats()
        assert stats['total_sent'] == 0


# ═══════════════════════════════════════════════════════════════
# TESTS PARA ATTACHMENT
# ═══════════════════════════════════════════════════════════════

class TestAttachment:
    """Tests para la clase Attachment"""

    def test_crear_attachment_basico(self, tmp_path):
        """Test de creación de adjunto básico"""
        # Crear archivo temporal
        test_file = tmp_path / "test.txt"
        test_file.write_text("contenido de prueba")

        attachment = Attachment(file_path=str(test_file))

        assert attachment.filename == "test.txt"
        assert attachment.content_type is not None

    def test_attachment_con_nombre_personalizado(self, tmp_path):
        """Test de adjunto con nombre personalizado"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("contenido")

        attachment = Attachment(
            file_path=str(test_file),
            filename="documento.txt"
        )

        assert attachment.filename == "documento.txt"

    def test_attachment_inline(self, tmp_path):
        """Test de adjunto inline"""
        test_file = tmp_path / "image.png"
        test_file.write_bytes(b'\x89PNG\r\n\x1a\n')

        attachment = Attachment(
            file_path=str(test_file),
            is_inline=True
        )

        assert attachment.is_inline
        assert attachment.content_id is not None

    def test_validacion_archivo_no_existe(self):
        """Test de validación con archivo inexistente"""
        attachment = Attachment(file_path="/ruta/inexistente/archivo.txt")

        assert not attachment.validate()


# ═══════════════════════════════════════════════════════════════
# EJECUCIÓN DE TESTS
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
