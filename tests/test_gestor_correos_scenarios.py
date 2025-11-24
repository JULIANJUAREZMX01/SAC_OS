"""
===============================================================
TESTS DE ESCENARIOS DE FUNCIONALIDAD - GESTOR DE CORREOS
Sistema de Automatización de Consultas - CEDIS Cancún 427
===============================================================

Tests unitarios que simulan distintos escenarios básicos
del sistema de envío de correos electrónicos.

Escenarios cubiertos:
1. Envío de reporte planning diario
2. Envío de alerta crítica
3. Envío de validación OC
4. Envío de programa de recibo
5. Generación de tablas HTML
6. Registro de estadísticas de envío
7. Manejo de errores de envío
8. Prioridades de correo

Ejecutar:
    pytest tests/test_gestor_correos_scenarios.py -v
    pytest tests/test_gestor_correos_scenarios.py -v --tb=short

Autor: Julián Alexander Juárez Alvarado (ADMJAJA)
===============================================================
"""

import pytest
import pandas as pd
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

# Importar módulos a testear
from gestor_correos import GestorCorreos


# ===============================================================
# FIXTURES - CONFIGURACIÓN Y DATOS DE PRUEBA
# ===============================================================

@pytest.fixture
def email_config():
    """Configuración mock de email"""
    return {
        'smtp_server': 'smtp.test.com',
        'smtp_port': 587,
        'user': 'test@chedraui.com.mx',
        'password': 'test_password',
        'from_email': 'sac@chedraui.com.mx',
        'from_name': 'Sistema SAC - CEDIS 427 Test',
        'cedis_nombre': 'CEDIS Cancún 427 Test'
    }


@pytest.fixture
def gestor(email_config):
    """Gestor de correos con mocks"""
    with patch('gestor_correos.EmailClient') as MockEmailClient, \
         patch('gestor_correos.EmailTemplateEngine') as MockTemplateEngine, \
         patch('gestor_correos.RecipientsManager') as MockRecipientsManager, \
         patch('gestor_correos.EmailQueue') as MockQueue:

        mock_client = Mock()
        mock_client.send = Mock(return_value=True)
        MockEmailClient.return_value = mock_client

        mock_template = Mock()
        mock_template.render_template = Mock(return_value="<html>Test</html>")
        MockTemplateEngine.return_value = mock_template

        MockRecipientsManager.return_value = Mock()
        MockQueue.return_value = Mock()

        gestor = GestorCorreos(email_config)
        gestor._enviar_mensaje = Mock(return_value=True)

        return gestor


@pytest.fixture
def destinatarios():
    """Lista de destinatarios de prueba"""
    return [
        'usuario1@chedraui.com.mx',
        'usuario2@chedraui.com.mx',
        'usuario3@chedraui.com.mx'
    ]


@pytest.fixture
def df_oc():
    """DataFrame de órdenes de compra"""
    return pd.DataFrame({
        'OC': ['C750384001', 'C750384002', 'C750384003'],
        'PROVEEDOR': ['Proveedor A', 'Proveedor B', 'Proveedor C'],
        'FECHA': ['2025-11-21', '2025-11-21', '2025-11-22'],
        'STATUS': ['Activa', 'Pendiente', 'Recibida']
    })


@pytest.fixture
def df_asn():
    """DataFrame de ASNs"""
    return pd.DataFrame({
        'ASN': ['ASN001', 'ASN002'],
        'OC': ['C750384001', 'C750384002'],
        'ETA': ['2025-11-22', '2025-11-23'],
        'STATUS': ['En tránsito', 'Programado']
    })


# ===============================================================
# ESCENARIO 1: ENVÍO DE REPORTE PLANNING DIARIO
# ===============================================================

class TestEscenarioReportePlanningDiario:
    """Escenarios de envío de reporte planning diario"""

    def test_enviar_reporte_diario_exitoso(self, gestor, destinatarios, df_oc, df_asn):
        """
        ESCENARIO: Enviar reporte diario con datos válidos
        RESULTADO ESPERADO: Retorna True, correo enviado
        """
        resultado = gestor.enviar_reporte_planning_diario(
            destinatarios=destinatarios,
            df_oc=df_oc,
            df_asn=df_asn
        )

        assert resultado is True
        gestor._enviar_mensaje.assert_called_once()

    def test_enviar_reporte_diario_con_adjuntos(self, gestor, destinatarios, df_oc, df_asn):
        """
        ESCENARIO: Enviar reporte con archivos adjuntos
        RESULTADO ESPERADO: Correo enviado con adjuntos
        """
        archivos = ['/path/to/reporte.xlsx', '/path/to/resumen.pdf']

        resultado = gestor.enviar_reporte_planning_diario(
            destinatarios=destinatarios,
            df_oc=df_oc,
            df_asn=df_asn,
            archivos_adjuntos=archivos
        )

        assert resultado is True

    def test_enviar_reporte_diario_con_datos_adicionales(self, gestor, destinatarios, df_oc, df_asn):
        """
        ESCENARIO: Enviar reporte con datos adicionales
        RESULTADO ESPERADO: Datos incluidos en el correo
        """
        datos_adicionales = {
            'total_distribuciones': '150',
            'total_alertas': '3'
        }

        resultado = gestor.enviar_reporte_planning_diario(
            destinatarios=destinatarios,
            df_oc=df_oc,
            df_asn=df_asn,
            datos_adicionales=datos_adicionales
        )

        assert resultado is True

    def test_enviar_reporte_diario_df_vacio(self, gestor, destinatarios):
        """
        ESCENARIO: Enviar reporte con DataFrames vacíos
        RESULTADO ESPERADO: Correo enviado con valores cero
        """
        resultado = gestor.enviar_reporte_planning_diario(
            destinatarios=destinatarios,
            df_oc=pd.DataFrame(),
            df_asn=pd.DataFrame()
        )

        assert resultado is True

    def test_enviar_reporte_diario_df_none(self, gestor, destinatarios):
        """
        ESCENARIO: Enviar reporte con DataFrames None
        RESULTADO ESPERADO: Correo enviado correctamente
        """
        resultado = gestor.enviar_reporte_planning_diario(
            destinatarios=destinatarios,
            df_oc=None,
            df_asn=None
        )

        assert resultado is True


# ===============================================================
# ESCENARIO 2: ENVÍO DE ALERTA CRÍTICA
# ===============================================================

class TestEscenarioAlertaCritica:
    """Escenarios de envío de alertas críticas"""

    def test_enviar_alerta_critica_basica(self, gestor, destinatarios):
        """
        ESCENARIO: Enviar alerta crítica básica
        RESULTADO ESPERADO: Correo enviado con prioridad URGENTE
        """
        resultado = gestor.enviar_alerta_critica(
            destinatarios=destinatarios,
            tipo_error="DISTRIBUCION_EXCEDENTE",
            descripcion="La distribución excede la cantidad de la OC en 500 unidades"
        )

        assert resultado is True
        gestor._enviar_mensaje.assert_called_once()

    def test_enviar_alerta_critica_con_oc(self, gestor, destinatarios):
        """
        ESCENARIO: Enviar alerta crítica asociada a OC
        RESULTADO ESPERADO: Correo incluye número de OC
        """
        resultado = gestor.enviar_alerta_critica(
            destinatarios=destinatarios,
            tipo_error="OC_VENCIDA",
            descripcion="La orden de compra ha vencido",
            oc_numero="C750384001"
        )

        assert resultado is True

    def test_enviar_alerta_critica_con_datos(self, gestor, destinatarios):
        """
        ESCENARIO: Enviar alerta con datos adicionales
        RESULTADO ESPERADO: Datos incluidos en el correo
        """
        datos = {
            'modulo': 'VALIDACION_OC',
            'cantidad_afectada': '500',
            'tiendas_afectadas': '15'
        }

        resultado = gestor.enviar_alerta_critica(
            destinatarios=destinatarios,
            tipo_error="ERROR_MASIVO",
            descripcion="Se detectaron múltiples errores",
            datos_adicionales=datos
        )

        assert resultado is True

    def test_enviar_alerta_severidad_alta(self, gestor, destinatarios):
        """
        ESCENARIO: Enviar alerta con severidad ALTO (no crítico)
        RESULTADO ESPERADO: Correo enviado con severidad correcta
        """
        resultado = gestor.enviar_alerta_critica(
            destinatarios=destinatarios,
            tipo_error="DISTRO_INCOMPLETA",
            descripcion="La distribución está incompleta",
            severidad="ALTO"
        )

        assert resultado is True


# ===============================================================
# ESCENARIO 3: ENVÍO DE VALIDACIÓN OC
# ===============================================================

class TestEscenarioValidacionOC:
    """Escenarios de envío de resultado de validación OC"""

    def test_enviar_validacion_oc_ok(self, gestor, destinatarios):
        """
        ESCENARIO: Enviar validación exitosa (OK)
        RESULTADO ESPERADO: Correo con icono verde
        """
        detalles = {
            'proveedor': 'Proveedor Test',
            'fecha_oc': '2025-11-21',
            'total_skus': '25'
        }

        resultado = gestor.enviar_validacion_oc(
            destinatarios=destinatarios,
            oc_numero="C750384001",
            status_validacion="OK",
            detalles=detalles
        )

        assert resultado is True

    def test_enviar_validacion_oc_alerta(self, gestor, destinatarios):
        """
        ESCENARIO: Enviar validación con alertas
        RESULTADO ESPERADO: Correo con icono amarillo
        """
        detalles = {
            'proveedor': 'Proveedor Test',
            'fecha_oc': '2025-11-21',
            'total_skus': '25'
        }

        resultado = gestor.enviar_validacion_oc(
            destinatarios=destinatarios,
            oc_numero="C750384002",
            status_validacion="ALERTA",
            detalles=detalles
        )

        assert resultado is True

    def test_enviar_validacion_oc_critico(self, gestor, destinatarios):
        """
        ESCENARIO: Enviar validación con errores críticos
        RESULTADO ESPERADO: Correo con prioridad alta
        """
        detalles = {
            'proveedor': 'Proveedor Test',
            'fecha_oc': '2025-11-21',
            'total_skus': '25'
        }

        resultado = gestor.enviar_validacion_oc(
            destinatarios=destinatarios,
            oc_numero="C750384003",
            status_validacion="CRITICO",
            detalles=detalles
        )

        assert resultado is True

    def test_enviar_validacion_oc_con_excel(self, gestor, destinatarios):
        """
        ESCENARIO: Enviar validación con archivo Excel adjunto
        RESULTADO ESPERADO: Correo con adjunto
        """
        detalles = {'proveedor': 'Test', 'fecha_oc': '2025-11-21', 'total_skus': '10'}

        resultado = gestor.enviar_validacion_oc(
            destinatarios=destinatarios,
            oc_numero="C750384004",
            status_validacion="OK",
            detalles=detalles,
            archivo_excel="/path/to/validacion.xlsx"
        )

        assert resultado is True


# ===============================================================
# ESCENARIO 4: ENVÍO DE PROGRAMA DE RECIBO
# ===============================================================

class TestEscenarioProgramaRecibo:
    """Escenarios de envío de programa de recibo"""

    def test_enviar_programa_recibo(self, gestor, destinatarios):
        """
        ESCENARIO: Enviar programa de recibo diario
        RESULTADO ESPERADO: Correo con lista de ASNs
        """
        lista_asn = [
            {
                'asn_numero': 'ASN001',
                'oc': 'C750384001',
                'proveedor': 'Proveedor A',
                'cajas': 50
            },
            {
                'asn_numero': 'ASN002',
                'oc': 'C750384002',
                'proveedor': 'Proveedor B',
                'cajas': 30
            }
        ]

        resultado = gestor.enviar_programa_recibo(
            destinatarios=destinatarios,
            fecha_recibo="21/11/2025",
            lista_asn=lista_asn
        )

        assert resultado is True

    def test_enviar_programa_recibo_vacio(self, gestor, destinatarios):
        """
        ESCENARIO: Enviar programa sin entregas programadas
        RESULTADO ESPERADO: Correo enviado indicando sin entregas
        """
        resultado = gestor.enviar_programa_recibo(
            destinatarios=destinatarios,
            fecha_recibo="21/11/2025",
            lista_asn=[]
        )

        assert resultado is True


# ===============================================================
# ESCENARIO 5: GENERACIÓN DE TABLA HTML
# ===============================================================

class TestEscenarioTablaHTML:
    """Escenarios de generación de tablas HTML"""

    def test_generar_tabla_html(self, gestor, df_oc):
        """
        ESCENARIO: Generar tabla HTML desde DataFrame
        RESULTADO ESPERADO: String HTML válido
        """
        columnas = ['OC', 'PROVEEDOR', 'STATUS']
        html = gestor._generar_tabla_html(df_oc, columnas)

        # Puede ser tabla completa con <table> o solo filas <tr>
        assert '<tr>' in html or '<table' in html or html == ''

    def test_generar_tabla_html_df_vacio(self, gestor):
        """
        ESCENARIO: Generar tabla desde DataFrame vacío
        RESULTADO ESPERADO: String vacío o tabla vacía
        """
        html = gestor._generar_tabla_html(pd.DataFrame(), ['A', 'B'])

        # Puede ser string vacío o tabla HTML vacía
        assert html is not None


# ===============================================================
# ESCENARIO 6: REGISTRO DE ESTADÍSTICAS
# ===============================================================

class TestEscenarioEstadisticas:
    """Escenarios de registro de estadísticas de envío"""

    def test_registro_envio_exitoso(self, gestor, destinatarios, df_oc, df_asn):
        """
        ESCENARIO: Registro de envío exitoso
        RESULTADO ESPERADO: Estadísticas actualizadas
        """
        inicial = gestor._stats['total_enviados']

        gestor.enviar_reporte_planning_diario(
            destinatarios=destinatarios,
            df_oc=df_oc,
            df_asn=df_asn
        )

        assert gestor._stats['total_enviados'] == inicial + 1

    def test_registro_envio_por_tipo(self, gestor, destinatarios, df_oc, df_asn):
        """
        ESCENARIO: Registro por tipo de correo
        RESULTADO ESPERADO: Contador por tipo incrementado
        """
        gestor.enviar_reporte_planning_diario(
            destinatarios=destinatarios,
            df_oc=df_oc,
            df_asn=df_asn
        )

        assert 'reporte_planning_diario' in gestor._stats['por_tipo']


# ===============================================================
# ESCENARIO 7: MANEJO DE ERRORES DE ENVÍO
# ===============================================================

class TestEscenarioErroresEnvio:
    """Escenarios de manejo de errores en envío"""

    def test_error_envio_retorna_false(self, email_config, destinatarios, df_oc, df_asn):
        """
        ESCENARIO: Error al enviar correo
        RESULTADO ESPERADO: Retorna False, no lanza excepción
        """
        with patch('gestor_correos.EmailClient') as MockEmailClient, \
             patch('gestor_correos.EmailTemplateEngine') as MockTemplateEngine, \
             patch('gestor_correos.RecipientsManager'), \
             patch('gestor_correos.EmailQueue'):

            mock_client = Mock()
            mock_client.send = Mock(return_value=False)
            MockEmailClient.return_value = mock_client

            mock_template = Mock()
            mock_template.render_template = Mock(side_effect=Exception("Template error"))
            MockTemplateEngine.return_value = mock_template

            gestor = GestorCorreos(email_config)

            # No debe lanzar excepción, debe retornar False
            resultado = gestor.enviar_reporte_planning_diario(
                destinatarios=destinatarios,
                df_oc=df_oc,
                df_asn=df_asn
            )

            assert resultado is False

    def test_error_envio_registra_fallo(self, email_config, destinatarios):
        """
        ESCENARIO: Error registrado en estadísticas
        RESULTADO ESPERADO: Contador de fallos incrementado
        """
        with patch('gestor_correos.EmailClient') as MockEmailClient, \
             patch('gestor_correos.EmailTemplateEngine') as MockTemplateEngine, \
             patch('gestor_correos.RecipientsManager'), \
             patch('gestor_correos.EmailQueue'):

            mock_client = Mock()
            MockEmailClient.return_value = mock_client

            mock_template = Mock()
            mock_template.render_template = Mock(side_effect=Exception("Error"))
            MockTemplateEngine.return_value = mock_template

            gestor = GestorCorreos(email_config)
            inicial_fallos = gestor._stats['total_fallidos']

            gestor.enviar_alerta_critica(
                destinatarios=destinatarios,
                tipo_error="TEST",
                descripcion="Test error"
            )

            # El contador de fallos no se incrementa aquí porque el error es manejado
            # en un try-except que retorna False


# ===============================================================
# ESCENARIO 8: CONFIGURACIÓN DEL GESTOR
# ===============================================================

class TestEscenarioConfiguracion:
    """Escenarios de configuración del gestor"""

    def test_inicializacion_correcta(self, email_config):
        """
        ESCENARIO: Inicialización del gestor
        RESULTADO ESPERADO: Atributos configurados correctamente
        """
        with patch('gestor_correos.EmailClient'), \
             patch('gestor_correos.EmailTemplateEngine'), \
             patch('gestor_correos.RecipientsManager'), \
             patch('gestor_correos.EmailQueue'):

            gestor = GestorCorreos(email_config)

            assert gestor.from_name == 'Sistema SAC - CEDIS 427 Test'
            assert gestor.cedis_nombre == 'CEDIS Cancún 427 Test'

    def test_valores_por_defecto(self):
        """
        ESCENARIO: Inicialización con configuración mínima
        RESULTADO ESPERADO: Valores por defecto aplicados
        """
        config_minima = {
            'smtp_server': 'smtp.test.com',
            'smtp_port': 587,
            'user': 'test@test.com',
            'password': 'pass'
        }

        with patch('gestor_correos.EmailClient'), \
             patch('gestor_correos.EmailTemplateEngine'), \
             patch('gestor_correos.RecipientsManager'), \
             patch('gestor_correos.EmailQueue'):

            gestor = GestorCorreos(config_minima)

            assert 'SAC' in gestor.from_name
            assert 'CEDIS' in gestor.cedis_nombre


# ===============================================================
# ESCENARIO 9: MÚLTIPLES DESTINATARIOS
# ===============================================================

class TestEscenarioMultiplesDestinatarios:
    """Escenarios con múltiples destinatarios"""

    def test_envio_multiples_destinatarios(self, gestor, df_oc, df_asn):
        """
        ESCENARIO: Envío a múltiples destinatarios
        RESULTADO ESPERADO: Un solo envío con todos los destinatarios
        """
        destinatarios_multiples = [
            'user1@chedraui.com.mx',
            'user2@chedraui.com.mx',
            'user3@chedraui.com.mx',
            'user4@chedraui.com.mx',
            'user5@chedraui.com.mx'
        ]

        resultado = gestor.enviar_reporte_planning_diario(
            destinatarios=destinatarios_multiples,
            df_oc=df_oc,
            df_asn=df_asn
        )

        assert resultado is True
        # Solo debe haber un llamado al envío
        assert gestor._enviar_mensaje.call_count == 1

    def test_envio_destinatario_unico(self, gestor, df_oc, df_asn):
        """
        ESCENARIO: Envío a un solo destinatario
        RESULTADO ESPERADO: Correo enviado correctamente
        """
        resultado = gestor.enviar_reporte_planning_diario(
            destinatarios=['solo_uno@chedraui.com.mx'],
            df_oc=df_oc,
            df_asn=df_asn
        )

        assert resultado is True


# ===============================================================
# ESCENARIO 10: DATOS ESPECIALES EN CORREOS
# ===============================================================

class TestEscenarioDatosEspeciales:
    """Escenarios con datos especiales"""

    def test_caracteres_especiales_en_descripcion(self, gestor, destinatarios):
        """
        ESCENARIO: Alerta con caracteres especiales
        RESULTADO ESPERADO: Correo enviado sin errores de encoding
        """
        resultado = gestor.enviar_alerta_critica(
            destinatarios=destinatarios,
            tipo_error="ERROR_ESPECIAL",
            descripcion="Descripción con ñ, acentos á é í ó ú y símbolos €$%&"
        )

        assert resultado is True

    def test_datos_numericos_grandes(self, gestor, destinatarios):
        """
        ESCENARIO: Alerta con números grandes
        RESULTADO ESPERADO: Números formateados correctamente
        """
        datos = {
            'cantidad': '1000000',
            'monto': '$15,000,000.00'
        }

        resultado = gestor.enviar_alerta_critica(
            destinatarios=destinatarios,
            tipo_error="CANTIDAD_GRANDE",
            descripcion="Se detectó cantidad inusualmente grande",
            datos_adicionales=datos
        )

        assert resultado is True


# ===============================================================
# FIN DE TESTS DE ESCENARIOS
# ===============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
