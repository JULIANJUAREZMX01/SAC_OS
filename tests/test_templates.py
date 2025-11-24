"""
═══════════════════════════════════════════════════════════════
TESTS PARA EMAIL TEMPLATES
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Tests unitarios para el motor de templates de email.

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
═══════════════════════════════════════════════════════════════
"""

import pytest
from pathlib import Path
import sys
import os

# Agregar path del proyecto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.email.template_engine import EmailTemplateEngine


# ═══════════════════════════════════════════════════════════════
# TESTS PARA EMAIL TEMPLATE ENGINE
# ═══════════════════════════════════════════════════════════════

class TestEmailTemplateEngine:
    """Tests para EmailTemplateEngine"""

    @pytest.fixture
    def engine(self):
        """Motor de templates para testing"""
        return EmailTemplateEngine()

    def test_inicializacion(self, engine):
        """Test de inicialización del motor"""
        assert engine.templates_dir is not None
        assert engine._default_vars is not None
        assert 'sistema_nombre' in engine._default_vars

    def test_registrar_template(self, engine):
        """Test de registro de template en memoria"""
        template_content = "<html><body>{{ mensaje }}</body></html>"
        engine.register_template('test_template', template_content)

        templates = engine.list_templates()
        assert 'test_template' in templates

    def test_eliminar_template_registrado(self, engine):
        """Test de eliminación de template registrado"""
        engine.register_template('temp', "<p>Temp</p>")
        result = engine.unregister_template('temp')

        assert result
        assert 'temp' not in engine.list_templates()

    def test_eliminar_template_inexistente(self, engine):
        """Test de eliminación de template inexistente"""
        result = engine.unregister_template('no_existe')
        assert not result

    def test_render_variables_simples(self, engine):
        """Test de renderizado de variables simples"""
        engine.register_template('simple', "Hola {{ nombre }}")
        result = engine.render_template('simple', {'nombre': 'Juan'})

        assert 'Juan' in result
        assert '{{' not in result

    def test_render_variables_default(self, engine):
        """Test de variables por defecto"""
        engine.register_template('default_vars', "Sistema: {{ sistema_nombre }}")
        result = engine.render_template('default_vars', {})

        assert 'Sistema SAC' in result

    def test_render_variable_con_filtro_default(self, engine):
        """Test de filtro default para variables vacías"""
        engine.register_template('filtro', '{{ valor|default:"N/A" }}')
        result = engine.render_template('filtro', {})

        assert 'N/A' in result

    def test_render_variable_con_filtro_upper(self, engine):
        """Test de filtro upper"""
        engine.register_template('upper', '{{ texto|upper }}')
        result = engine.render_template('upper', {'texto': 'minusculas'})

        assert 'MINUSCULAS' in result

    def test_render_variable_con_filtro_lower(self, engine):
        """Test de filtro lower"""
        engine.register_template('lower', '{{ texto|lower }}')
        result = engine.render_template('lower', {'texto': 'MAYUSCULAS'})

        assert 'mayusculas' in result

    def test_render_fecha_actual(self, engine):
        """Test de variable fecha_actual automática"""
        engine.register_template('fecha', 'Fecha: {{ fecha_actual }}')
        result = engine.render_template('fecha', {})

        assert 'Fecha:' in result
        assert '/' in result  # Formato dd/mm/yyyy

    def test_render_hora_actual(self, engine):
        """Test de variable hora_actual automática"""
        engine.register_template('hora', 'Hora: {{ hora_actual }}')
        result = engine.render_template('hora', {})

        assert 'Hora:' in result
        assert ':' in result  # Formato HH:MM

    def test_render_string(self, engine):
        """Test de renderizado de string directo"""
        result = engine.render_string("Hola {{ nombre }}", {'nombre': 'Mundo'})
        assert 'Hola Mundo' in result

    def test_set_default_var(self, engine):
        """Test de establecer variable por defecto"""
        engine.set_default_var('mi_variable', 'mi_valor')
        vars_default = engine.get_default_vars()

        assert 'mi_variable' in vars_default
        assert vars_default['mi_variable'] == 'mi_valor'

    def test_limpiar_cache(self, engine):
        """Test de limpieza de caché"""
        engine._templates_cache['test'] = 'contenido'
        engine.clear_cache()

        assert len(engine._templates_cache) == 0

    def test_listar_templates(self, engine):
        """Test de listado de templates"""
        templates = engine.list_templates()

        # Debería incluir los templates HTML creados
        assert isinstance(templates, list)

    def test_template_no_encontrado(self, engine):
        """Test de template no encontrado"""
        with pytest.raises(FileNotFoundError):
            engine.load_template('template_que_no_existe_123456')


# ═══════════════════════════════════════════════════════════════
# TESTS PARA TEMPLATES HTML
# ═══════════════════════════════════════════════════════════════

class TestHTMLTemplates:
    """Tests para los templates HTML del sistema"""

    @pytest.fixture
    def engine(self):
        """Motor de templates"""
        return EmailTemplateEngine()

    def test_template_daily_report_existe(self, engine):
        """Test de existencia de template daily_report"""
        templates = engine.list_templates()
        assert 'daily_report' in templates

    def test_template_critical_alert_existe(self, engine):
        """Test de existencia de template critical_alert"""
        templates = engine.list_templates()
        assert 'critical_alert' in templates

    def test_template_oc_validation_existe(self, engine):
        """Test de existencia de template oc_validation"""
        templates = engine.list_templates()
        assert 'oc_validation' in templates

    def test_template_reception_program_existe(self, engine):
        """Test de existencia de template reception_program"""
        templates = engine.list_templates()
        assert 'reception_program' in templates

    def test_template_weekly_summary_existe(self, engine):
        """Test de existencia de template weekly_summary"""
        templates = engine.list_templates()
        assert 'weekly_summary' in templates

    def test_template_error_notification_existe(self, engine):
        """Test de existencia de template error_notification"""
        templates = engine.list_templates()
        assert 'error_notification' in templates

    def test_template_reminder_existe(self, engine):
        """Test de existencia de template reminder"""
        templates = engine.list_templates()
        assert 'reminder' in templates

    def test_template_confirmation_existe(self, engine):
        """Test de existencia de template confirmation"""
        templates = engine.list_templates()
        assert 'confirmation' in templates

    def test_render_daily_report(self, engine):
        """Test de renderizado de daily_report"""
        context = {
            'total_oc': '10',
            'total_asn': '5',
            'total_distribuciones': '100',
            'total_alertas': '2'
        }
        result = engine.render_template('daily_report', context)

        assert '10' in result
        assert '5' in result
        assert 'CEDIS' in result
        assert '<html' in result.lower()

    def test_render_critical_alert(self, engine):
        """Test de renderizado de critical_alert"""
        context = {
            'tipo_error': 'ERROR DE PRUEBA',
            'descripcion_error': 'Descripción del error',
            'severidad': 'CRITICO'
        }
        result = engine.render_template('critical_alert', context)

        assert 'ERROR DE PRUEBA' in result
        assert 'CRITICO' in result
        assert '<html' in result.lower()

    def test_render_oc_validation(self, engine):
        """Test de renderizado de oc_validation"""
        context = {
            'oc_numero': 'OC123456',
            'status_validacion': 'OK',
            'status_clase': 'ok',
            'proveedor': 'Proveedor Test'
        }
        result = engine.render_template('oc_validation', context)

        assert 'OC123456' in result
        assert 'OK' in result
        assert '<html' in result.lower()


# ═══════════════════════════════════════════════════════════════
# TESTS PARA VARIABLES DE CONTEXTO
# ═══════════════════════════════════════════════════════════════

class TestContextVariables:
    """Tests para variables de contexto"""

    @pytest.fixture
    def engine(self):
        return EmailTemplateEngine()

    def test_variables_cedis(self, engine):
        """Test de variables de CEDIS"""
        defaults = engine.get_default_vars()

        assert defaults['cedis_nombre'] == 'CEDIS Cancún 427'
        assert defaults['cedis_codigo'] == '427'
        assert defaults['region'] == 'Sureste'

    def test_variables_empresa(self, engine):
        """Test de variables de empresa"""
        defaults = engine.get_default_vars()

        assert 'Chedraui' in defaults['empresa']

    def test_variables_desarrollador(self, engine):
        """Test de variables de desarrollador"""
        defaults = engine.get_default_vars()

        assert 'Julián' in defaults['desarrollador']
        assert defaults['desarrollador_cargo'] == 'Jefe de Sistemas'

    def test_variables_colores(self, engine):
        """Test de variables de colores"""
        defaults = engine.get_default_vars()

        assert defaults['color_primario'] == '#E31837'
        assert defaults['color_secundario'] == '#003DA5'

    def test_variable_lema(self, engine):
        """Test de variable lema"""
        defaults = engine.get_default_vars()

        assert 'máquinas' in defaults['lema'].lower()
        assert 'sistemas' in defaults['lema'].lower()


# ═══════════════════════════════════════════════════════════════
# EJECUCIÓN DE TESTS
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
