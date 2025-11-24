"""
═══════════════════════════════════════════════════════════════
GENERADOR DE REPORTES EN TEXTO PLANO
Para lectores de pantalla y accesibilidad universal
═══════════════════════════════════════════════════════════════

Generador de reportes en formato texto plano (.txt) optimizado para:
- Lectores de pantalla (NVDA, JAWS, VoiceOver)
- Distribución por email
- Acceso desde cualquier dispositivo
- Compatibilidad universal

Características:
✓ Formato simple y accesible
✓ Estructura clara con separadores
✓ Emojis para facilitar escaneo visual
✓ Tablas formateadas en ASCII
✓ URLs navegables
✓ Anotaciones claras para elementos especiales

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
═══════════════════════════════════════════════════════════════
"""

import logging
from pathlib import Path
from typing import List, Tuple
from datetime import datetime
import pandas as pd

from .base import (
    AccessibleReportBase,
    ReportFormat,
    ReportMetadata,
    AccessibilitySettings,
    ReportSection,
)

logger = logging.getLogger(__name__)


class AccessibleTextReport(AccessibleReportBase):
    """
    Generador de reportes en texto plano WCAG compliant.

    Produce archivos .txt altamente accesibles que pueden ser:
    - Leídos por cualquier lector de pantalla
    - Distribuidos por email sin conversión
    - Abiertos en cualquier editor de texto
    - Analizados por scripts automatizados
    """

    # Separadores para estructura clara
    SECTION_SEP = "═" * 70
    SUBSECTION_SEP = "─" * 70
    TABLE_SEP = "─" * 70

    def __init__(
        self,
        metadata: ReportMetadata,
        accessibility: AccessibilitySettings = None,
        max_line_length: int = 80
    ):
        """Inicializa generador de texto plano accesible"""
        super().__init__(metadata, accessibility)
        self.max_line_length = max_line_length
        self.data_tables: List[Tuple[str, pd.DataFrame]] = []

    def add_table(
        self,
        df: pd.DataFrame,
        title: str,
        description: str = ""
    ) -> None:
        """Agrega una tabla al reporte"""
        if df.empty:
            logger.warning(f"⚠️ Tabla vacía: {title}")
            return

        self.data_tables.append((title, df))
        logger.info(f"✅ Tabla agregada: {title}")

    def get_format(self) -> ReportFormat:
        return ReportFormat.TEXT

    def generate(self, output_path: str) -> bool:
        """
        Genera el reporte en texto plano.

        Args:
            output_path: Ruta donde guardar el archivo .txt

        Returns:
            bool: True si fue exitoso
        """
        try:
            # Validar accesibilidad
            validation = self.validate_accessibility()
            if not all(validation.values()):
                logger.warning("⚠️ Algunas validaciones de accesibilidad fallaron")

            # Generar contenido
            text_content = self._build_text()

            # Guardar archivo
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text_content)

            logger.info(f"✅ Reporte de texto generado: {output_path}")
            return True

        except Exception as e:
            logger.error(f"❌ Error al generar texto: {e}")
            return False

    def _build_text(self) -> str:
        """Construye el contenido del archivo de texto"""
        lines = []

        # Encabezado
        lines.extend(self._build_header())

        # Índice
        if self.accessibility.include_table_of_contents:
            lines.extend(self._build_toc())

        # Información de accesibilidad
        lines.extend(self._build_accessibility_info())

        # Resumen ejecutivo
        if self.accessibility.include_summary:
            lines.extend(self._build_summary())

        # Secciones
        lines.extend(self._build_sections_text())

        # Tablas
        lines.extend(self._build_tables_text())

        # Pie de página
        lines.extend(self._build_footer_text())

        return '\n'.join(lines)

    def _build_header(self) -> List[str]:
        """Construye el encabezado del reporte"""
        lines = []

        lines.append(self.SECTION_SEP)
        lines.append("")
        lines.append(f"REPORTE: {self.metadata.title}")
        lines.append(f"DESCRIPCIÓN: {self.metadata.description}")
        lines.append("")
        lines.append(f"CEDIS: {self.metadata.cedis_name}")
        lines.append(f"CÓDIGO CEDIS: {self.metadata.cedis_code}")
        lines.append("")
        lines.append(f"GENERADO POR: {self.metadata.author}")
        lines.append(f"FECHA Y HORA: {self.metadata.created_date.strftime('%d/%m/%Y %H:%M:%S')}")
        lines.append("")
        lines.append(f"NIVEL DE ACCESIBILIDAD: {self.metadata.accessibility_level}")
        lines.append(f"VERSIÓN DE FORMATO: {self.metadata.format_version}")
        lines.append("")
        lines.append(self.SECTION_SEP)
        lines.append("")

        return lines

    def _build_toc(self) -> List[str]:
        """Construye tabla de contenidos en texto"""
        lines = []

        lines.append("TABLA DE CONTENIDOS")
        lines.append("═" * 40)
        lines.append("")

        # Secciones
        if self.sections:
            lines.append("SECCIONES:")
            for idx, section in enumerate(self.sections, 1):
                lines.append(f"  {idx}. {section.title}")
            lines.append("")

        # Tablas
        if self.data_tables:
            lines.append("TABLAS:")
            for idx, (title, _) in enumerate(self.data_tables, 1):
                lines.append(f"  {idx}. {title}")
            lines.append("")

        lines.append(self.SECTION_SEP)
        lines.append("")

        return lines

    def _build_accessibility_info(self) -> List[str]:
        """Construye información de accesibilidad"""
        lines = []

        lines.append("INFORMACIÓN DE ACCESIBILIDAD")
        lines.append("=" * 40)
        lines.append("")
        lines.append("Este reporte ha sido diseñado para ser accesible")
        lines.append("para personas con diferentes discapacidades:")
        lines.append("")
        lines.append("✓ VISUAL: Compatible con lectores de pantalla")
        lines.append("  - Texto plano sin imágenes innecesarias")
        lines.append("  - Estructura lógica clara")
        lines.append("  - Sin colores como único medio de información")
        lines.append("")
        lines.append("✓ AUDITIVO: Todo el contenido es visual")
        lines.append("  - No hay contenido exclusivamente auditivo")
        lines.append("")
        lines.append("✓ MOTÓRICO: Totalmente navegable")
        lines.append("  - Texto plano sin interacciones complejas")
        lines.append("")
        lines.append("✓ COGNITIVO: Lenguaje claro y simple")
        lines.append("  - Estructura predecible")
        lines.append("  - Términos explicados")
        lines.append("")
        lines.append(self.SECTION_SEP)
        lines.append("")

        return lines

    def _build_summary(self) -> List[str]:
        """Construye un resumen ejecutivo"""
        lines = []

        lines.append("RESUMEN EJECUTIVO")
        lines.append("=" * 40)
        lines.append("")
        lines.append(f"Total de secciones: {len(self.sections)}")
        lines.append(f"Total de tablas: {len(self.data_tables)}")

        # Contar filas en tablas
        total_rows = sum(len(df) for _, df in self.data_tables)
        lines.append(f"Total de filas en tablas: {total_rows}")

        lines.append("")
        lines.append(self.SECTION_SEP)
        lines.append("")

        return lines

    def _build_sections_text(self) -> List[str]:
        """Construye las secciones en formato texto"""
        lines = []

        for section_idx, section in enumerate(self.sections, 1):
            # Título
            prefix = "═" if section.heading_level == 1 else "─" if section.heading_level == 2 else " "
            lines.append(f"{prefix} SECCIÓN {section_idx}: {section.title.upper()}")
            lines.append(self.SUBSECTION_SEP)
            lines.append("")

            # Contenido
            if section.content:
                # Envolver texto largo
                wrapped = self._wrap_text(section.content, self.max_line_length)
                lines.append(wrapped)
            else:
                lines.append("[Sin contenido]")

            lines.append("")
            lines.append("")

        return lines

    def _build_tables_text(self) -> List[str]:
        """Construye las tablas en formato texto"""
        lines = []

        for table_idx, (title, df) in enumerate(self.data_tables, 1):
            lines.append(f"TABLA {table_idx}: {title.upper()}")
            lines.append(self.TABLE_SEP)
            lines.append("")

            # Descripción
            lines.append(f"Total de registros: {len(df)}")
            lines.append(f"Total de columnas: {len(df.columns)}")
            lines.append("")

            # Encabezados
            lines.append("COLUMNAS:")
            for col_idx, col in enumerate(df.columns, 1):
                lines.append(f"  {col_idx}. {col}")
            lines.append("")
            lines.append("")

            # Tabla ASCII formateada
            lines.append(self._format_table_as_text(df))
            lines.append("")
            lines.append(self.TABLE_SEP)
            lines.append("")

        return lines

    def _format_table_as_text(self, df: pd.DataFrame) -> str:
        """Formatea una tabla como texto ASCII"""
        if df.empty:
            return "[Tabla vacía]"

        # Convertir a string para cálculos de ancho
        df_str = df.astype(str)

        # Calcular anchos de columna
        col_widths = []
        for col in df_str.columns:
            max_width = max(
                len(str(col)),
                max(df_str[col].apply(len))
            )
            col_widths.append(min(max_width, 50))  # Máximo 50 caracteres

        # Línea de separación
        sep_line = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"

        # Construir tabla
        lines = []
        lines.append(sep_line)

        # Encabezados
        header_cells = []
        for col, width in zip(df_str.columns, col_widths):
            header_cells.append(f" {str(col).ljust(width)} ")
        lines.append("|" + "|".join(header_cells) + "|")
        lines.append(sep_line)

        # Filas
        for _, row in df_str.iterrows():
            row_cells = []
            for val, width in zip(row, col_widths):
                # Truncar valores muy largos
                val_str = str(val)
                if len(val_str) > width:
                    val_str = val_str[:width-3] + "..."
                row_cells.append(f" {val_str.ljust(width)} ")
            lines.append("|" + "|".join(row_cells) + "|")

        lines.append(sep_line)

        return '\n'.join(lines)

    def _wrap_text(self, text: str, max_length: int) -> str:
        """Envuelve texto a una longitud máxima"""
        if not text or len(text) <= max_length:
            return text

        words = text.split()
        lines = []
        current_line = []

        for word in words:
            current_length = len(' '.join(current_line + [word]))
            if current_length <= max_length:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]

        if current_line:
            lines.append(' '.join(current_line))

        return '\n'.join(lines)

    def _build_footer_text(self) -> List[str]:
        """Construye el pie de página en texto"""
        lines = []

        lines.append(self.SECTION_SEP)
        lines.append("")
        lines.append("PIE DE PÁGINA")
        lines.append("")
        lines.append(f"CEDIS: {self.metadata.cedis_name} (Código: {self.metadata.cedis_code})")
        lines.append(f"GENERADO: {self.metadata.created_date.strftime('%d/%m/%Y %H:%M:%S')}")
        lines.append(f"SISTEMA: Sistema SAC v{self.metadata.format_version}")
        lines.append("")
        lines.append("NOTAS:")
        lines.append("• Este reporte es confidencial")
        lines.append("• Está diseñado para ser accesible a personas con discapacidades")
        lines.append("• Compatible con lectores de pantalla")
        lines.append("")
        lines.append("COPYRIGHT")
        lines.append("© 2025 Tiendas Chedraui S.A. de C.V.")
        lines.append("Todos los derechos reservados.")
        lines.append("")
        lines.append(self.SECTION_SEP)

        return lines
