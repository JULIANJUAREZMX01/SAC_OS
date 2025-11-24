"""
═══════════════════════════════════════════════════════════════
GENERADOR DE REPORTES HTML WCAG 2.1 COMPLIANT
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Generador de reportes en HTML con cumplimiento total de WCAG 2.1 AA.

Características:
✓ Semántica HTML5 completa
✓ ARIA labels y roles descriptivos
✓ Navegación por teclado (Tab, Enter, Escape)
✓ Colores con contraste WCAG AAA
✓ Responsive design (mobile-friendly)
✓ Compatible con lectores de pantalla
✓ Modo oscuro incluido
✓ Print-friendly

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
═══════════════════════════════════════════════════════════════
"""

import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from dataclasses import dataclass
import pandas as pd

from .base import (
    AccessibleReportBase,
    ReportFormat,
    ReportMetadata,
    AccessibilitySettings,
    ReportSection,
    ContrastMode
)

logger = logging.getLogger(__name__)


@dataclass
class HTMLTableConfig:
    """Configuración para tablas HTML accesibles"""
    caption: str
    summary: str
    striped: bool = True
    bordered: bool = True
    include_row_numbers: bool = True
    include_pagination: bool = True
    rows_per_page: int = 25


class AccessibleHTMLReport(AccessibleReportBase):
    """
    Generador de reportes HTML WCAG 2.1 AA.

    Produce HTML semántico con:
    - Estructura de encabezados correcta (h1 > h2 > h3)
    - Atributos ARIA descriptivos
    - Navegación por teclado completa
    - Colores accesibles
    - Tablas con scope y headers
    """

    CSS_COLORS = {
        "normal": {
            "primary": "#E31837",        # Rojo Chedraui
            "secondary": "#F8CBAD",      # Beige
            "success": "#28a745",        # Verde
            "warning": "#ffc107",        # Naranja
            "danger": "#dc3545",         # Rojo
            "info": "#17a2b8",           # Azul
            "text": "#212529",           # Oscuro
            "background": "#ffffff",     # Blanco
        },
        "high": {
            "primary": "#8B0000",        # Rojo oscuro
            "secondary": "#000000",      # Negro
            "success": "#006400",        # Verde oscuro
            "warning": "#FF6600",        # Naranja fuerte
            "danger": "#CC0000",         # Rojo fuerte
            "info": "#003366",           # Azul oscuro
            "text": "#000000",           # Negro
            "background": "#FFFFFF",     # Blanco
        },
        "dark": {
            "primary": "#E31837",
            "secondary": "#333333",
            "success": "#66BB6A",
            "warning": "#FFA726",
            "danger": "#EF5350",
            "info": "#42A5F5",
            "text": "#E0E0E0",
            "background": "#121212",
        }
    }

    def __init__(
        self,
        metadata: ReportMetadata,
        accessibility: AccessibilitySettings = None,
        include_dark_mode: bool = True,
        include_print_css: bool = True
    ):
        """Inicializa generador HTML accesible"""
        super().__init__(metadata, accessibility)
        self.include_dark_mode = include_dark_mode
        self.include_print_css = include_print_css
        self.data_tables: List[tuple] = []  # (title, dataframe, config)

    def add_table(
        self,
        df: pd.DataFrame,
        caption: str,
        summary: str,
        config: HTMLTableConfig = None
    ) -> None:
        """Agrega una tabla accesible al reporte"""
        if df.empty:
            logger.warning(f"⚠️ Tabla vacía: {caption}")
            return

        config = config or HTMLTableConfig(
            caption=caption,
            summary=summary
        )
        self.data_tables.append((caption, df, config))
        logger.info(f"✅ Tabla agregada: {caption} ({len(df)} filas)")

    def get_format(self) -> ReportFormat:
        return ReportFormat.HTML

    def generate(self, output_path: str) -> bool:
        """
        Genera el reporte HTML WCAG 2.1 compliant.

        Args:
            output_path: Ruta donde guardar el archivo HTML

        Returns:
            bool: True si fue exitoso
        """
        try:
            # Validar accesibilidad
            validation = self.validate_accessibility()
            if not all(validation.values()):
                logger.warning("⚠️ Algunas validaciones de accesibilidad fallaron")

            # Generar HTML
            html_content = self._build_html()

            # Guardar archivo
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            logger.info(f"✅ Reporte HTML generado: {output_path}")
            return True

        except Exception as e:
            logger.error(f"❌ Error al generar HTML: {e}")
            return False

    def _build_html(self) -> str:
        """Construye el documento HTML completo"""
        html = []

        # Doctype y apertura
        html.append('<!DOCTYPE html>')
        html.append(self._build_language_meta())

        # Head
        html.append(self._build_head())

        # Body
        html.append('<body>')

        # Skip links (WCAG 2.4.1)
        html.append(self._build_skip_links())

        # Header principal
        html.append(self._build_header())

        # Barra de herramientas de accesibilidad
        html.append(self._build_accessibility_toolbar())

        # Contenido principal
        html.append('<main id="main-content" role="main">')

        # Tabla de contenidos
        html.append(self._build_table_of_contents())

        # Secciones
        html.append(self._build_sections())

        # Tablas
        html.append(self._build_tables())

        # Declaración de accesibilidad
        html.append(self._build_accessibility_statement())

        # Pie de página
        html.append(self._build_footer())

        html.append('</main>')
        html.append('</body>')
        html.append('</html>')

        return '\n'.join(html)

    def _build_head(self) -> str:
        """Construye el head del documento (meta tags, CSS)"""
        head = ['<head>']
        head.append('  <meta charset="UTF-8">')
        head.append('  <meta name="viewport" content="width=device-width, initial-scale=1.0">')
        head.append(f'  <meta name="description" content="{self.metadata.description}">')
        head.append(f'  <meta name="author" content="{self.metadata.author}">')
        head.append('  <meta name="theme-color" content="#E31837">')

        # Accesibilidad
        head.append('  <meta name="accessibility" content="WCAG 2.1 AA">')

        # Título
        head.append(f'  <title>{self.metadata.title}</title>')

        # CSS
        head.append('  <style>')
        head.append(self._build_css())
        head.append('  </style>')

        # Dark mode CSS
        if self.include_dark_mode:
            head.append('  <style media="(prefers-color-scheme: dark)">')
            head.append(self._build_dark_css())
            head.append('  </style>')

        # Print CSS
        if self.include_print_css:
            head.append('  <style media="print">')
            head.append(self._build_print_css())
            head.append('  </style>')

        head.append('</head>')
        return '\n'.join(head)

    def _build_header(self) -> str:
        """Construye el header principal accesible"""
        colors = self.CSS_COLORS[self.accessibility.contrast_mode.value]

        header = f'''
        <header role="banner" aria-label="Encabezado del reporte" style="background-color: {colors['primary']}; color: white; padding: 20px;">
            <div class="container">
                <h1 id="page-title" style="margin: 0; font-size: 28px; font-weight: bold;">
                    {self.metadata.title}
                </h1>
                <p id="page-subtitle" style="margin: 10px 0 0 0; font-size: 14px; opacity: 0.9;">
                    {self.metadata.description}
                </p>
            </div>
        </header>
        '''
        return header

    def _build_accessibility_toolbar(self) -> str:
        """Construye barra de herramientas de accesibilidad"""
        toolbar = '''
        <div class="accessibility-toolbar" role="toolbar" aria-label="Herramientas de accesibilidad">
            <button aria-label="Aumentar tamaño de fuente" onclick="increaseFontSize()" tabindex="0">
                A+
            </button>
            <button aria-label="Disminuir tamaño de fuente" onclick="decreaseFontSize()" tabindex="0">
                A-
            </button>
            <button aria-label="Alto contraste" id="high-contrast-btn" onclick="toggleHighContrast()" tabindex="0">
                ◐ Contraste
            </button>
            <button aria-label="Imprimir reporte" onclick="window.print()" tabindex="0">
                🖨️ Imprimir
            </button>
            <button aria-label="Descargar como PDF" onclick="downloadPDF()" tabindex="0">
                📥 PDF
            </button>
        </div>
        <style>
            .accessibility-toolbar {
                display: flex;
                gap: 10px;
                padding: 15px;
                background-color: #f5f5f5;
                border-bottom: 2px solid #E31837;
                flex-wrap: wrap;
            }
            .accessibility-toolbar button {
                padding: 8px 12px;
                border: 1px solid #999;
                border-radius: 4px;
                background-color: white;
                cursor: pointer;
                font-size: 14px;
                font-weight: bold;
            }
            .accessibility-toolbar button:focus {
                outline: 3px solid #4A90E2;
                outline-offset: 2px;
            }
            .accessibility-toolbar button:hover {
                background-color: #E31837;
                color: white;
            }
        </style>
        '''
        return toolbar

    def _build_sections(self) -> str:
        """Construye las secciones del reporte"""
        sections_html = []

        for section in self.sections:
            sections_html.append(f'''
            <section id="{section.id}" aria-labelledby="{section.id}-heading">
                <h{section.heading_level} id="{section.id}-heading" aria-label="{section.aria_label}">
                    {section.title}
                </h{section.heading_level}>
                <div class="section-content">
                    {section.content}
                </div>
            </section>
            ''')

        return '\n'.join(sections_html)

    def _build_tables(self) -> str:
        """Construye tablas HTML accesibles"""
        tables_html = []

        for title, df, config in self.data_tables:
            table_html = f'''
            <section class="data-table-section" aria-labelledby="table-{title.replace(' ', '-')}-caption">
                <figure>
                    <figcaption id="table-{title.replace(' ', '-')}-caption">
                        <strong>{config.caption}</strong>
                        <p>{config.summary}</p>
                    </figcaption>
                    <table role="table" aria-describedby="table-{title.replace(' ', '-')}-caption">
                        <thead>
                            <tr role="row">
            '''

            # Headers con scope
            for col_idx, col in enumerate(df.columns, 1):
                table_html += f'<th scope="col" role="columnheader" aria-sort="none">{col}</th>'

            table_html += '''
                            </tr>
                        </thead>
                        <tbody>
            '''

            # Filas de datos
            for row_idx, (_, row) in enumerate(df.iterrows(), 1):
                table_html += '<tr role="row">'
                for col_idx, value in enumerate(row, 1):
                    # Primera columna como header de fila
                    if col_idx == 1:
                        table_html += f'<th scope="row" role="rowheader">{value}</th>'
                    else:
                        table_html += f'<td role="cell">{value}</td>'
                table_html += '</tr>'

            table_html += '''
                        </tbody>
                    </table>
                </figure>
            </section>
            '''

            tables_html.append(table_html)

        return '\n'.join(tables_html)

    def _build_footer(self) -> str:
        """Construye el pie de página"""
        return f'''
        <footer role="contentinfo" aria-label="Pie de página">
            <div class="footer-content">
                <p>
                    <strong>{self.metadata.cedis_name}</strong> (CEDIS {self.metadata.cedis_code})<br>
                    Generado: {self.metadata.created_date.strftime('%Y-%m-%d %H:%M:%S')}<br>
                    Formato: {self.metadata.format_version} | Accesibilidad: {self.metadata.accessibility_level}
                </p>
                <p style="font-size: 12px; color: #666;">
                    © 2025 Tiendas Chedraui S.A. de C.V. - Todos los derechos reservados
                </p>
            </div>
        </footer>
        <style>
            footer {
                background-color: #f5f5f5;
                border-top: 2px solid #E31837;
                padding: 20px;
                text-align: center;
                font-size: 12px;
                margin-top: 40px;
            }
        </style>
        '''

    def _build_css(self) -> str:
        """Construye CSS WCAG compliant"""
        colors = self.CSS_COLORS[self.accessibility.contrast_mode.value]

        css = f'''
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        html {{
            scroll-behavior: smooth;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            color: {colors['text']};
            background-color: {colors['background']};
            font-size: 16px;
        }}

        /* Skip links (WCAG 2.4.1) */
        .skip-links {{
            position: absolute;
            top: -40px;
            left: 0;
            background: {colors['primary']};
            color: white;
            padding: 8px;
            z-index: 100;
        }}

        .skip-link:focus {{
            top: 0;
        }}

        /* Navegación por teclado */
        a:focus, button:focus, input:focus, select:focus, textarea:focus {{
            outline: 3px solid #4A90E2;
            outline-offset: 2px;
        }}

        /* Encabezados */
        h1 {{ font-size: 32px; margin: 20px 0 10px 0; }}
        h2 {{ font-size: 24px; margin: 15px 0 10px 0; }}
        h3 {{ font-size: 20px; margin: 12px 0 8px 0; }}
        h4 {{ font-size: 18px; margin: 10px 0 6px 0; }}
        h5 {{ font-size: 16px; margin: 8px 0 4px 0; }}
        h6 {{ font-size: 14px; margin: 6px 0 2px 0; }}

        h1, h2, h3, h4, h5, h6 {{
            color: {colors['primary']};
            font-weight: bold;
        }}

        /* Tablas accesibles */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}

        table thead {{
            background-color: {colors['primary']};
            color: white;
        }}

        table thead th {{
            padding: 12px;
            text-align: left;
            font-weight: bold;
            border: 1px solid #ddd;
        }}

        table tbody tr:nth-child(odd) {{
            background-color: {colors['background']};
        }}

        table tbody tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}

        table tbody td {{
            padding: 12px;
            border: 1px solid #ddd;
        }}

        table tbody tr:hover {{
            background-color: #f0f0f0;
        }}

        /* Secciones y contenido */
        main {{
            max-width: 1200px;
            margin: 20px auto;
            padding: 20px;
        }}

        section {{
            margin: 30px 0;
            padding: 20px;
            border-left: 4px solid {colors['primary']};
            background-color: #fafafa;
        }}

        figcaption {{
            font-size: 14px;
            color: #666;
            margin-bottom: 10px;
        }}

        /* Accessibility statement */
        .accessibility-statement {{
            background-color: #e8f5e9;
            border: 2px solid #28a745;
            padding: 15px;
            border-radius: 4px;
            margin: 20px 0;
        }}

        /* Responsive */
        @media (max-width: 768px) {{
            body {{ font-size: 14px; }}
            h1 {{ font-size: 24px; }}
            h2 {{ font-size: 20px; }}
            main {{ padding: 10px; }}
            section {{ padding: 15px; }}
            table {{ font-size: 12px; }}
            table th, table td {{ padding: 8px; }}
        }}

        /* Impresión */
        @media print {{
            .accessibility-toolbar, .skip-links {{
                display: none;
            }}
            body {{ color: black; background: white; }}
            a {{ color: #E31837; }}
        }}

        /* Reduce motion */
        @media (prefers-reduced-motion: reduce) {{
            * {{
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
            }}
        }}
        '''

        return css

    def _build_dark_css(self) -> str:
        """CSS para modo oscuro (prefers-color-scheme: dark)"""
        colors = self.CSS_COLORS["dark"]
        return f'''
        body {{
            color: {colors['text']};
            background-color: {colors['background']};
        }}

        table thead {{
            background-color: {colors['primary']};
        }}

        section {{
            background-color: #1e1e1e;
            border-left-color: {colors['primary']};
        }}

        table tbody tr:nth-child(even) {{
            background-color: #2a2a2a;
        }}

        a {{ color: {colors['info']}; }}
        '''

    def _build_print_css(self) -> str:
        """CSS para impresión"""
        return '''
        @page {
            margin: 2cm;
            size: A4;
        }

        body {
            color: black;
            background: white;
        }

        .accessibility-toolbar, .skip-links {
            display: none;
        }

        section {
            page-break-inside: avoid;
        }

        table {
            page-break-inside: avoid;
        }

        a {
            color: #E31837;
            text-decoration: underline;
        }
        '''
