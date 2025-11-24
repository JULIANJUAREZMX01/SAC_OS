"""
═══════════════════════════════════════════════════════════════
CLASE BASE PARA REPORTES ACCESIBLES
Sistema WCAG 2.1 AA - Generación de reportes accesibles
═══════════════════════════════════════════════════════════════

Clase abstracta que define la interfaz para reportes accesibles.
Todos los generadores de reportes heredan de esta clase.

Características WCAG 2.1 soportadas:
✓ Aria-labels descriptivos
✓ Roles ARIA semánticos
✓ Navegación por teclado
✓ Alto contraste
✓ Texto alternativo
✓ Estructura semántica

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
═══════════════════════════════════════════════════════════════
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ContrastMode(Enum):
    """Modos de contraste disponibles"""
    NORMAL = "normal"  # Contraste estándar Chedraui
    HIGH = "high"      # Alto contraste (WCAG AAA)
    DARK = "dark"      # Modo oscuro
    LIGHT = "light"    # Modo claro


class ReportFormat(Enum):
    """Formatos de reporte soportados"""
    HTML = "html"      # HTML con ARIA
    TEXT = "text"      # Texto plano para lectores de pantalla
    PDF = "pdf"        # PDF accesible
    MARKDOWN = "md"    # Markdown para documentación


@dataclass
class AccessibilitySettings:
    """Configuración de accesibilidad para reportes"""
    contrast_mode: ContrastMode = ContrastMode.NORMAL
    include_aria_labels: bool = True
    include_semantic_html: bool = True
    keyboard_navigation: bool = True
    alt_text_all_images: bool = True
    skip_links_enabled: bool = True
    language_code: str = "es"  # Español por defecto
    include_text_version: bool = True
    include_summary: bool = True
    include_table_of_contents: bool = True


@dataclass
class ReportMetadata:
    """Metadata de un reporte"""
    title: str
    description: str
    author: str = "Sistema SAC"
    created_date: datetime = field(default_factory=datetime.now)
    cedis_name: str = "CEDIS Cancún 427"
    cedis_code: str = "427"
    format_version: str = "1.0"
    accessibility_level: str = "WCAG 2.1 AA"  # Nivel WCAG cumplido


@dataclass
class ReportSection:
    """Una sección dentro de un reporte"""
    id: str
    title: str
    heading_level: int = 2  # h2, h3, h4, etc (1-6)
    aria_label: str = None
    content: str = ""
    subsections: List['ReportSection'] = field(default_factory=list)

    def __post_init__(self):
        if self.aria_label is None:
            self.aria_label = self.title


class AccessibleReportBase(ABC):
    """
    Clase base abstracta para todos los generadores de reportes accesibles.

    Define la interfaz y comportamiento común para:
    - Reportes HTML WCAG 2.1 compliant
    - Reportes en texto plano
    - Reportes PDF accesibles

    Principios WCAG 2.1 implementados:
    1. Perceptible: Información accesible a todos los sentidos
    2. Operable: Navegable por teclado y otros mecanismos
    3. Comprensible: Texto legible, navegación predecible
    4. Robusto: Compatible con tecnologías de asistencia
    """

    def __init__(
        self,
        metadata: ReportMetadata,
        accessibility: AccessibilitySettings = None
    ):
        """
        Inicializa un reporte accesible.

        Args:
            metadata: Información del reporte (título, autor, etc)
            accessibility: Configuración de accesibilidad
        """
        self.metadata = metadata
        self.accessibility = accessibility or AccessibilitySettings()
        self.sections: List[ReportSection] = []
        self._logger = logging.getLogger(self.__class__.__name__)

        self._logger.info(
            f"🎯 Iniciando reporte accesible: {metadata.title}",
            extra={
                'report_type': self.__class__.__name__,
                'accessibility_level': self.accessibility.contrast_mode.value,
                'language': self.accessibility.language_code
            }
        )

    @abstractmethod
    def generate(self, output_path: str) -> bool:
        """
        Genera el reporte en el formato específico.

        Args:
            output_path: Ruta donde guardar el reporte

        Returns:
            bool: True si fue exitoso, False en caso contrario
        """
        pass

    @abstractmethod
    def get_format(self) -> ReportFormat:
        """Retorna el formato de este reporte"""
        pass

    def add_section(self, section: ReportSection) -> None:
        """Agrega una sección al reporte"""
        self._validate_section(section)
        self.sections.append(section)
        self._logger.debug(f"✅ Sección agregada: {section.title}")

    def add_sections(self, sections: List[ReportSection]) -> None:
        """Agrega múltiples secciones al reporte"""
        for section in sections:
            self.add_section(section)

    def _validate_section(self, section: ReportSection) -> None:
        """Valida que la sección sea válida"""
        if not section.id or not section.title:
            raise ValueError(
                "❌ Las secciones deben tener id y title"
            )

        if section.heading_level < 1 or section.heading_level > 6:
            raise ValueError(
                f"❌ Nivel de encabezado inválido: {section.heading_level}"
            )

    def _build_table_of_contents(self) -> str:
        """
        Construye una tabla de contenidos accesible.

        WCAG: Proporciona navegación rápida (2.4.5 Multiple Ways)
        """
        if not self.accessibility.include_table_of_contents:
            return ""

        toc_html = '<nav aria-label="Tabla de contenidos">\n'
        toc_html += '  <h2 id="toc-heading">📑 Tabla de contenidos</h2>\n'
        toc_html += '  <ul aria-labelledby="toc-heading">\n'

        for section in self.sections:
            # Link accesible con aria-label
            toc_html += (
                f'    <li><a href="#{section.id}" '
                f'aria-label="{section.title}">{section.title}</a></li>\n'
            )

        toc_html += '  </ul>\n</nav>\n'
        return toc_html

    def _build_skip_links(self) -> str:
        """
        Construye links de salto para navegación por teclado.

        WCAG: Permite saltar contenido repetitivo (2.4.1 Bypass Blocks)
        """
        if not self.accessibility.skip_links_enabled:
            return ""

        skip_html = '<div class="skip-links">\n'
        skip_html += '  <a href="#main-content" class="skip-link">⏭️ Saltar a contenido principal</a>\n'
        skip_html += '  <a href="#navigation" class="skip-link">⏭️ Saltar a navegación</a>\n'
        skip_html += '</div>\n'

        return skip_html

    def _build_language_meta(self) -> str:
        """Construye meta tags de idioma accesibles"""
        lang = self.accessibility.language_code
        return (
            f'<html lang="{lang}" '
            f'dir="{"ltr" if lang != "ar" else "rtl"}">\n'
        )

    def _get_aria_attributes(self, element_type: str) -> Dict[str, str]:
        """
        Retorna atributos ARIA apropiados para diferentes elementos.

        WCAG: Utiliza roles y propiedades ARIA (4.1.2 Name, Role, Value)
        """
        aria_attrs = {}

        if element_type == "table":
            aria_attrs = {
                "role": "table",
                "aria-label": "Tabla de datos del reporte"
            }
        elif element_type == "button":
            aria_attrs = {
                "role": "button",
                "aria-pressed": "false",
                "tabindex": "0"
            }
        elif element_type == "alert":
            aria_attrs = {
                "role": "alert",
                "aria-live": "assertive",
                "aria-atomic": "true"
            }
        elif element_type == "navigation":
            aria_attrs = {
                "role": "navigation",
                "aria-label": "Navegación principal"
            }

        return aria_attrs

    def _build_accessibility_statement(self) -> str:
        """
        Construye una declaración de accesibilidad en el reporte.

        WCAG: Informa al usuario sobre características de accesibilidad
        """
        statement = """
        <section aria-labelledby="accessibility-statement-heading" class="accessibility-statement">
            <h2 id="accessibility-statement-heading">♿ Declaración de Accesibilidad</h2>
            <p>
                Este reporte ha sido diseñado siguiendo los estándares
                <strong>WCAG 2.1 nivel AA</strong>.
                Características accesibles incluidas:
            </p>
            <ul>
                <li>✅ Navegación completa por teclado (Tab, Enter, Escape)</li>
                <li>✅ Compatible con lectores de pantalla (NVDA, JAWS, VoiceOver)</li>
                <li>✅ Estructura semántica HTML5</li>
                <li>✅ Etiquetas ARIA descriptivas</li>
                <li>✅ Contraste de color suficiente</li>
                <li>✅ Versión en texto plano disponible</li>
                <li>✅ Tablas correctamente etiquetadas</li>
            </ul>
        </section>
        """
        return statement

    def get_accessibility_level(self) -> str:
        """Retorna el nivel WCAG cumplido"""
        return self.metadata.accessibility_level

    def validate_accessibility(self) -> Dict[str, bool]:
        """
        Valida que el reporte cumpla con requisitos de accesibilidad.

        Returns:
            Dict con resultados de validación
        """
        validation_results = {
            "has_title": bool(self.metadata.title),
            "has_language": bool(self.accessibility.language_code),
            "aria_labels_enabled": self.accessibility.include_aria_labels,
            "semantic_html": self.accessibility.include_semantic_html,
            "keyboard_nav": self.accessibility.keyboard_navigation,
            "has_sections": len(self.sections) > 0,
            "text_version_available": self.accessibility.include_text_version,
        }

        all_valid = all(validation_results.values())

        if all_valid:
            self._logger.info("✅ Validación de accesibilidad EXITOSA")
        else:
            self._logger.warning(
                f"⚠️ Advertencias de accesibilidad detectadas: {validation_results}"
            )

        return validation_results

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} "
            f"format={self.get_format().value} "
            f"sections={len(self.sections)} "
            f"accessibility={self.accessibility.contrast_mode.value}>"
        )
