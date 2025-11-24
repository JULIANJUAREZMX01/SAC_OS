"""
═══════════════════════════════════════════════════════════════
MÓDULO DE REPORTERÍA WCAG 2.1 COMPLIANT
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Módulo para generación de reportes accesibles WCAG 2.1 AA en:
- HTML (con aria-labels, roles ARIA, navegación por teclado)
- Texto plano (para lectores de pantalla)
- PDF accesible (con etiquetas de accesibilidad)

Características:
✓ Cumple WCAG 2.1 AA
✓ Compatible con lectores de pantalla
✓ Navegación por teclado completa
✓ Alto contraste disponible
✓ Respuestas rápidas de acceso

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
═══════════════════════════════════════════════════════════════
"""

from .base import AccessibleReportBase
from .html_generator import AccessibleHTMLReport
from .text_generator import AccessibleTextReport
from .pdf_generator import AccessiblePDFReport

__all__ = [
    'AccessibleReportBase',
    'AccessibleHTMLReport',
    'AccessibleTextReport',
    'AccessiblePDFReport',
]

__version__ = "1.0.0"
__author__ = "Julián Alexander Juárez Alvarado"
