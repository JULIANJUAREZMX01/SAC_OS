"""
═══════════════════════════════════════════════════════════════
MOTOR DE TEMPLATES DE EMAIL
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Motor de templates HTML para correos electrónicos con soporte
para variables, herencia de templates y componentes reutilizables.

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
═══════════════════════════════════════════════════════════════
"""

import os
import re
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from string import Template

logger = logging.getLogger(__name__)

# Directorio de templates por defecto
DEFAULT_TEMPLATES_DIR = Path(__file__).parent / 'templates'


class EmailTemplateEngine:
    """
    Motor de templates para correos electrónicos HTML

    Características:
    - Carga de templates desde archivos HTML
    - Variables con sintaxis {{ variable }}
    - Herencia de templates (base template)
    - Registro de templates en memoria
    - Componentes reutilizables (header, footer)
    - Variables por defecto del sistema

    Ejemplo:
        engine = EmailTemplateEngine()
        html = engine.render_template('daily_report', {
            'titulo': 'Reporte Diario',
            'fecha': '21/11/2025',
            'datos': [...]
        })
    """

    def __init__(self, templates_dir: str = None):
        """
        Inicializa el motor de templates

        Args:
            templates_dir: Directorio donde se encuentran los templates HTML
        """
        self.templates_dir = Path(templates_dir) if templates_dir else DEFAULT_TEMPLATES_DIR
        self._templates_cache: Dict[str, str] = {}
        self._registered_templates: Dict[str, str] = {}

        # Variables por defecto disponibles en todos los templates
        self._default_vars = {
            'sistema_nombre': 'Sistema SAC',
            'cedis_nombre': 'CEDIS Cancún 427',
            'cedis_codigo': '427',
            'empresa': 'Tiendas Chedraui S.A. de C.V.',
            'region': 'Sureste',
            'desarrollador': 'Julián Alexander Juárez Alvarado',
            'desarrollador_cargo': 'Jefe de Sistemas',
            'color_primario': '#E31837',
            'color_secundario': '#003DA5',
            'color_exito': '#92D050',
            'color_alerta': '#FFC000',
            'color_error': '#FF0000',
            'color_info': '#B4C7E7',
            'anio_actual': str(datetime.now().year),
            'lema': 'Las máquinas y los sistemas al servicio de los analistas'
        }

        logger.info(f"📧 EmailTemplateEngine inicializado: {self.templates_dir}")

    # ═══════════════════════════════════════════════════════════════
    # CARGA DE TEMPLATES
    # ═══════════════════════════════════════════════════════════════

    def load_template(self, name: str, use_cache: bool = True) -> str:
        """
        Carga un template desde archivo

        Args:
            name: Nombre del template (sin extensión .html)
            use_cache: Si usar caché para evitar lecturas repetidas

        Returns:
            str: Contenido HTML del template
        """
        # Verificar caché
        if use_cache and name in self._templates_cache:
            return self._templates_cache[name]

        # Verificar templates registrados en memoria
        if name in self._registered_templates:
            return self._registered_templates[name]

        # Buscar archivo
        template_path = self.templates_dir / f"{name}.html"

        if not template_path.exists():
            logger.error(f"❌ Template no encontrado: {template_path}")
            raise FileNotFoundError(f"Template '{name}' no encontrado en {self.templates_dir}")

        try:
            content = template_path.read_text(encoding='utf-8')
            if use_cache:
                self._templates_cache[name] = content
            logger.debug(f"✅ Template cargado: {name}")
            return content
        except Exception as e:
            logger.error(f"❌ Error al cargar template {name}: {e}")
            raise

    def render_template(self, name: str, context: Dict[str, Any] = None) -> str:
        """
        Renderiza un template con las variables proporcionadas

        Args:
            name: Nombre del template
            context: Diccionario con variables para el template

        Returns:
            str: HTML renderizado con las variables sustituidas
        """
        # Cargar template
        template_content = self.load_template(name)

        # Combinar variables por defecto con las proporcionadas
        vars_dict = self._default_vars.copy()
        if context:
            vars_dict.update(context)

        # Agregar variables de fecha/hora actuales
        now = datetime.now()
        vars_dict.update({
            'fecha_actual': now.strftime('%d/%m/%Y'),
            'fecha_actual_larga': now.strftime('%d de %B de %Y'),
            'hora_actual': now.strftime('%H:%M'),
            'fecha_hora_actual': now.strftime('%d/%m/%Y %H:%M:%S'),
            'timestamp': now.isoformat()
        })

        # Renderizar template
        try:
            rendered = self._render_variables(template_content, vars_dict)

            # Procesar herencia ({% extends "base" %})
            rendered = self._process_extends(rendered, vars_dict)

            # Procesar includes ({% include "component" %})
            rendered = self._process_includes(rendered, vars_dict)

            return rendered
        except Exception as e:
            logger.error(f"❌ Error al renderizar template {name}: {e}")
            raise

    def _render_variables(self, content: str, vars_dict: Dict[str, Any]) -> str:
        """
        Sustituye las variables {{ variable }} en el contenido

        Soporta:
        - {{ variable }}: Sustitución simple
        - {{ variable|default:"valor" }}: Valor por defecto
        - {{ variable|upper }}: Convertir a mayúsculas
        - {{ variable|lower }}: Convertir a minúsculas
        """
        def replace_var(match):
            full_match = match.group(1).strip()

            # Verificar si hay filtros
            if '|' in full_match:
                parts = full_match.split('|')
                var_name = parts[0].strip()
                filters = parts[1:]
            else:
                var_name = full_match
                filters = []

            # Obtener valor
            value = vars_dict.get(var_name, '')

            # Aplicar filtros
            for f in filters:
                f = f.strip()
                if f.startswith('default:'):
                    if not value:
                        value = f.split(':', 1)[1].strip('"\'')
                elif f == 'upper':
                    value = str(value).upper()
                elif f == 'lower':
                    value = str(value).lower()
                elif f == 'title':
                    value = str(value).title()

            return str(value) if value is not None else ''

        # Patrón para {{ variable }}
        pattern = r'\{\{\s*(.+?)\s*\}\}'
        return re.sub(pattern, replace_var, content)

    def _process_extends(self, content: str, vars_dict: Dict[str, Any]) -> str:
        """Procesa la herencia de templates {% extends "base" %}"""
        pattern = r'\{%\s*extends\s+"(\w+)"\s*%\}'
        match = re.search(pattern, content)

        if not match:
            return content

        base_name = match.group(1)
        content = re.sub(pattern, '', content)

        try:
            base_template = self.load_template(base_name)

            # Extraer bloques del template hijo
            blocks = self._extract_blocks(content)

            # Sustituir bloques en el template base
            for block_name, block_content in blocks.items():
                block_pattern = r'\{%\s*block\s+' + block_name + r'\s*%\}.*?\{%\s*endblock\s*%\}'
                base_template = re.sub(
                    block_pattern,
                    block_content,
                    base_template,
                    flags=re.DOTALL
                )

            return self._render_variables(base_template, vars_dict)
        except FileNotFoundError:
            logger.warning(f"⚠️ Template base '{base_name}' no encontrado")
            return content

    def _extract_blocks(self, content: str) -> Dict[str, str]:
        """Extrae bloques {% block nombre %}...{% endblock %}"""
        blocks = {}
        pattern = r'\{%\s*block\s+(\w+)\s*%\}(.*?)\{%\s*endblock\s*%\}'

        for match in re.finditer(pattern, content, re.DOTALL):
            block_name = match.group(1)
            block_content = match.group(2).strip()
            blocks[block_name] = block_content

        return blocks

    def _process_includes(self, content: str, vars_dict: Dict[str, Any]) -> str:
        """Procesa includes {% include "component" %}"""
        pattern = r'\{%\s*include\s+"(\w+)"\s*%\}'

        def replace_include(match):
            include_name = match.group(1)
            try:
                include_content = self.load_template(include_name)
                return self._render_variables(include_content, vars_dict)
            except FileNotFoundError:
                logger.warning(f"⚠️ Include '{include_name}' no encontrado")
                return ''

        return re.sub(pattern, replace_include, content)

    # ═══════════════════════════════════════════════════════════════
    # REGISTRO DE TEMPLATES
    # ═══════════════════════════════════════════════════════════════

    def register_template(self, name: str, template: str) -> None:
        """
        Registra un template en memoria

        Args:
            name: Nombre del template
            template: Contenido HTML del template
        """
        self._registered_templates[name] = template
        logger.info(f"✅ Template registrado: {name}")

    def unregister_template(self, name: str) -> bool:
        """
        Elimina un template registrado

        Args:
            name: Nombre del template

        Returns:
            bool: True si se eliminó, False si no existía
        """
        if name in self._registered_templates:
            del self._registered_templates[name]
            logger.info(f"✅ Template eliminado: {name}")
            return True
        return False

    def list_templates(self) -> List[str]:
        """
        Lista todos los templates disponibles

        Returns:
            List[str]: Lista de nombres de templates
        """
        templates = set()

        # Templates de archivos
        if self.templates_dir.exists():
            for file in self.templates_dir.glob('*.html'):
                templates.add(file.stem)

        # Templates registrados
        templates.update(self._registered_templates.keys())

        return sorted(templates)

    # ═══════════════════════════════════════════════════════════════
    # GESTIÓN DE CACHÉ
    # ═══════════════════════════════════════════════════════════════

    def clear_cache(self) -> None:
        """Limpia el caché de templates"""
        self._templates_cache.clear()
        logger.info("🗑️ Caché de templates limpiado")

    def preload_templates(self) -> int:
        """
        Precarga todos los templates en caché

        Returns:
            int: Número de templates cargados
        """
        count = 0
        for name in self.list_templates():
            try:
                self.load_template(name)
                count += 1
            except Exception as e:
                logger.warning(f"⚠️ No se pudo precargar {name}: {e}")

        logger.info(f"📦 {count} templates precargados")
        return count

    # ═══════════════════════════════════════════════════════════════
    # UTILIDADES
    # ═══════════════════════════════════════════════════════════════

    def set_default_var(self, name: str, value: Any) -> None:
        """Establece una variable por defecto"""
        self._default_vars[name] = value

    def get_default_vars(self) -> Dict[str, Any]:
        """Obtiene las variables por defecto"""
        return self._default_vars.copy()

    def render_string(self, template_string: str, context: Dict[str, Any] = None) -> str:
        """
        Renderiza una cadena de texto como template

        Args:
            template_string: Cadena con sintaxis de template
            context: Variables de contexto

        Returns:
            str: Cadena renderizada
        """
        vars_dict = self._default_vars.copy()
        if context:
            vars_dict.update(context)

        now = datetime.now()
        vars_dict.update({
            'fecha_actual': now.strftime('%d/%m/%Y'),
            'hora_actual': now.strftime('%H:%M'),
        })

        return self._render_variables(template_string, vars_dict)


# ═══════════════════════════════════════════════════════════════
# EJEMPLO DE USO
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("""
    ═══════════════════════════════════════════════════════════════
    MOTOR DE TEMPLATES DE EMAIL - CHEDRAUI CEDIS
    ═══════════════════════════════════════════════════════════════
    """)

    engine = EmailTemplateEngine()

    # Registrar un template de prueba
    engine.register_template('test', """
    <html>
    <body>
        <h1>{{ titulo }}</h1>
        <p>Fecha: {{ fecha_actual }}</p>
        <p>Sistema: {{ sistema_nombre }}</p>
        <p>CEDIS: {{ cedis_nombre }}</p>
    </body>
    </html>
    """)

    # Renderizar
    html = engine.render_template('test', {'titulo': 'Prueba de Template'})
    print("✅ Template renderizado:")
    print(html)

    print("\n📋 Templates disponibles:")
    for name in engine.list_templates():
        print(f"   - {name}")
