"""
===============================================================
MÓDULO DE EXPORTACIÓN A PDF
Sistema de Automatización de Consultas - CEDIS Cancún 427
===============================================================

Genera reportes PDF profesionales con formato corporativo Chedraui:
- Reportes de validación de OC
- Reportes diarios de Planning
- Reportes de errores
- Resúmenes ejecutivos

Uso:
    from modules.exportar_pdf import GeneradorPDF

    pdf = GeneradorPDF()
    archivo = pdf.crear_reporte_validacion_oc(datos, "Validacion_OC123.pdf")

Requiere: pip install reportlab

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
===============================================================
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# Intentar importar ReportLab
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, cm
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        Image, PageBreak, HRFlowable
    )
    from reportlab.graphics.shapes import Drawing, Rect
    from reportlab.graphics.charts.barcharts import VerticalBarChart
    from reportlab.graphics.charts.piecharts import Pie
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# Configurar logger
logger = logging.getLogger(__name__)

# ===============================================================
# CONSTANTES Y COLORES CORPORATIVOS
# ===============================================================

# Colores Chedraui
CHEDRAUI_RED = colors.HexColor('#E31837')
CHEDRAUI_DARK = colors.HexColor('#1a1a2e')
COLOR_HEADER = colors.HexColor('#E31837')
COLOR_SUBHEADER = colors.HexColor('#F8CBAD')
COLOR_CRITICO = colors.HexColor('#FF0000')
COLOR_ALERTA = colors.HexColor('#FFC000')
COLOR_OK = colors.HexColor('#92D050')
COLOR_INFO = colors.HexColor('#B4C7E7')

# Directorio de salida por defecto
OUTPUT_DIR = Path(__file__).parent.parent / "output" / "resultados"


# ===============================================================
# DATA CLASS PARA CONFIGURACIÓN
# ===============================================================

@dataclass
class ConfiguracionPDF:
    """Configuración para generación de PDF"""
    titulo_empresa: str = "Tiendas Chedraui S.A. de C.V."
    subtitulo: str = "CEDIS Cancún 427 - Sistema SAC"
    logo_path: Optional[str] = None
    autor: str = "Sistema SAC"
    tamano_pagina: tuple = A4
    margenes: tuple = (2*cm, 2*cm, 2*cm, 2*cm)  # izq, der, arriba, abajo


# ===============================================================
# CLASE PRINCIPAL
# ===============================================================

class GeneradorPDF:
    """
    Generador de reportes PDF profesionales.

    Proporciona métodos para crear diferentes tipos de reportes
    con formato corporativo Chedraui.

    Ejemplo:
        >>> pdf = GeneradorPDF()
        >>> archivo = pdf.crear_reporte_validacion_oc(
        ...     oc_numero="OC123456",
        ...     resultado="exitoso",
        ...     datos={'total_oc': 1000, 'total_distro': 1000}
        ... )
    """

    def __init__(self, config: ConfiguracionPDF = None, output_dir: Path = None):
        """
        Inicializa el generador de PDF.

        Args:
            config: Configuración personalizada
            output_dir: Directorio de salida
        """
        if not REPORTLAB_AVAILABLE:
            logger.warning("⚠️  ReportLab no instalado. Instala con: pip install reportlab")

        self.config = config or ConfiguracionPDF()
        self.output_dir = output_dir or OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Estilos
        self._styles = None
        if REPORTLAB_AVAILABLE:
            self._init_styles()

        logger.info(f"📄 GeneradorPDF inicializado. Salida: {self.output_dir}")

    def _init_styles(self):
        """Inicializa estilos personalizados."""
        self._styles = getSampleStyleSheet()

        # Estilo título principal
        self._styles.add(ParagraphStyle(
            name='TituloPrincipal',
            parent=self._styles['Heading1'],
            fontSize=24,
            textColor=CHEDRAUI_RED,
            alignment=TA_CENTER,
            spaceAfter=20
        ))

        # Estilo subtítulo
        self._styles.add(ParagraphStyle(
            name='Subtitulo',
            parent=self._styles['Heading2'],
            fontSize=14,
            textColor=CHEDRAUI_DARK,
            alignment=TA_CENTER,
            spaceAfter=10
        ))

        # Estilo encabezado de sección
        self._styles.add(ParagraphStyle(
            name='SeccionHeader',
            parent=self._styles['Heading2'],
            fontSize=14,
            textColor=colors.white,
            backColor=CHEDRAUI_RED,
            alignment=TA_LEFT,
            leftIndent=10,
            spaceBefore=15,
            spaceAfter=10
        ))

        # Estilo normal corporativo
        self._styles.add(ParagraphStyle(
            name='NormalCorp',
            parent=self._styles['Normal'],
            fontSize=10,
            textColor=colors.black,
            alignment=TA_LEFT
        ))

        # Estilo para datos destacados
        self._styles.add(ParagraphStyle(
            name='Destacado',
            parent=self._styles['Normal'],
            fontSize=12,
            textColor=CHEDRAUI_RED,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))

    def _crear_encabezado(self, titulo: str, subtitulo: str = None) -> List:
        """Crea el encabezado corporativo del documento."""
        elementos = []

        # Línea decorativa superior
        elementos.append(HRFlowable(
            width="100%", thickness=3, color=CHEDRAUI_RED,
            spaceBefore=0, spaceAfter=10
        ))

        # Título empresa
        elementos.append(Paragraph(
            self.config.titulo_empresa,
            self._styles['TituloPrincipal']
        ))

        # Subtítulo
        elementos.append(Paragraph(
            self.config.subtitulo,
            self._styles['Subtitulo']
        ))

        # Título del reporte
        elementos.append(Spacer(1, 10))
        elementos.append(Paragraph(
            f"<b>{titulo}</b>",
            ParagraphStyle(
                'TituloReporte',
                parent=self._styles['Heading1'],
                fontSize=18,
                textColor=CHEDRAUI_DARK,
                alignment=TA_CENTER
            )
        ))

        if subtitulo:
            elementos.append(Paragraph(
                subtitulo,
                self._styles['Subtitulo']
            ))

        # Fecha y hora
        elementos.append(Paragraph(
            f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
            ParagraphStyle(
                'Fecha',
                parent=self._styles['Normal'],
                fontSize=9,
                textColor=colors.gray,
                alignment=TA_CENTER
            )
        ))

        elementos.append(HRFlowable(
            width="100%", thickness=1, color=colors.gray,
            spaceBefore=10, spaceAfter=20
        ))

        return elementos

    def _crear_pie_pagina(self, canvas, doc):
        """Crea el pie de página."""
        canvas.saveState()

        # Línea
        canvas.setStrokeColor(CHEDRAUI_RED)
        canvas.setLineWidth(1)
        canvas.line(doc.leftMargin, 1.5*cm, doc.width + doc.leftMargin, 1.5*cm)

        # Texto
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.gray)
        canvas.drawString(
            doc.leftMargin,
            1*cm,
            f"Sistema SAC - CEDIS Chedraui Cancún 427 - {datetime.now().strftime('%d/%m/%Y')}"
        )
        canvas.drawRightString(
            doc.width + doc.leftMargin,
            1*cm,
            f"Página {doc.page}"
        )

        canvas.restoreState()

    def _crear_tabla_datos(
        self,
        datos: List[List],
        encabezados: List[str],
        anchos: List[float] = None
    ) -> Table:
        """Crea una tabla con estilo corporativo."""
        tabla_datos = [encabezados] + datos

        tabla = Table(tabla_datos, colWidths=anchos)
        tabla.setStyle(TableStyle([
            # Encabezado
            ('BACKGROUND', (0, 0), (-1, 0), CHEDRAUI_RED),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),

            # Cuerpo
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('TOPPADDING', (0, 1), (-1, -1), 6),

            # Bordes y fondo alternado
            ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, COLOR_INFO]),
        ]))

        return tabla

    def _crear_seccion(self, titulo: str) -> List:
        """Crea un encabezado de sección."""
        return [
            Spacer(1, 15),
            Paragraph(f"  {titulo}", self._styles['SeccionHeader']),
            Spacer(1, 10)
        ]

    # ===============================================================
    # MÉTODOS DE REPORTES
    # ===============================================================

    def crear_reporte_validacion_oc(
        self,
        oc_numero: str,
        resultado: str,
        datos: Dict,
        errores: List[Dict] = None,
        nombre_archivo: str = None
    ) -> str:
        """
        Crea un reporte PDF de validación de OC.

        Args:
            oc_numero: Número de la OC
            resultado: Resultado de la validación
            datos: Diccionario con datos de la validación
            errores: Lista de errores detectados
            nombre_archivo: Nombre del archivo (opcional)

        Returns:
            Ruta al archivo generado
        """
        if not REPORTLAB_AVAILABLE:
            logger.error("❌ ReportLab no disponible")
            return ""

        errores = errores or []
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        nombre_archivo = nombre_archivo or f"Validacion_OC_{oc_numero}_{timestamp}.pdf"
        ruta_archivo = self.output_dir / nombre_archivo

        doc = SimpleDocTemplate(
            str(ruta_archivo),
            pagesize=self.config.tamano_pagina,
            leftMargin=self.config.margenes[0],
            rightMargin=self.config.margenes[1],
            topMargin=self.config.margenes[2],
            bottomMargin=self.config.margenes[3]
        )

        elementos = []

        # Encabezado
        elementos.extend(self._crear_encabezado(
            f"Reporte de Validación",
            f"Orden de Compra: {oc_numero}"
        ))

        # Resultado
        color_resultado = COLOR_OK if resultado == 'exitoso' else COLOR_CRITICO
        elementos.append(Paragraph(
            f"<b>RESULTADO: {resultado.upper()}</b>",
            ParagraphStyle(
                'Resultado',
                parent=self._styles['Destacado'],
                textColor=color_resultado,
                fontSize=16
            )
        ))
        elementos.append(Spacer(1, 20))

        # Resumen de datos
        elementos.extend(self._crear_seccion("Resumen de Validación"))

        resumen_datos = [
            ['Total OC', f"{datos.get('total_oc', 0):,.0f}"],
            ['Total Distribución', f"{datos.get('total_distro', 0):,.0f}"],
            ['Diferencia', f"{datos.get('diferencia', 0):,.0f}"],
            ['Tiempo Ejecución', f"{datos.get('tiempo', 0):.2f} segundos"],
        ]

        tabla_resumen = self._crear_tabla_datos(
            resumen_datos,
            ['Concepto', 'Valor'],
            [8*cm, 6*cm]
        )
        elementos.append(tabla_resumen)

        # Errores (si hay)
        if errores:
            elementos.extend(self._crear_seccion(f"Errores Detectados ({len(errores)})"))

            errores_datos = []
            for e in errores[:20]:  # Máximo 20 errores
                errores_datos.append([
                    e.get('tipo', 'N/A'),
                    e.get('severidad', 'N/A'),
                    e.get('mensaje', '')[:50]
                ])

            tabla_errores = self._crear_tabla_datos(
                errores_datos,
                ['Tipo', 'Severidad', 'Mensaje'],
                [4*cm, 3*cm, 8*cm]
            )
            elementos.append(tabla_errores)

        # Generar PDF
        doc.build(elementos, onFirstPage=self._crear_pie_pagina, onLaterPages=self._crear_pie_pagina)

        logger.info(f"✅ PDF generado: {ruta_archivo}")
        return str(ruta_archivo)

    def crear_reporte_diario(
        self,
        datos_oc: List[Dict],
        datos_asn: List[Dict],
        estadisticas: Dict,
        nombre_archivo: str = None
    ) -> str:
        """
        Crea el reporte diario de Planning en PDF.

        Args:
            datos_oc: Lista de OCs del día
            datos_asn: Lista de ASNs
            estadisticas: Estadísticas del día
            nombre_archivo: Nombre del archivo

        Returns:
            Ruta al archivo generado
        """
        if not REPORTLAB_AVAILABLE:
            logger.error("❌ ReportLab no disponible")
            return ""

        fecha = datetime.now().strftime('%Y%m%d')
        nombre_archivo = nombre_archivo or f"Planning_Diario_{fecha}.pdf"
        ruta_archivo = self.output_dir / nombre_archivo

        doc = SimpleDocTemplate(
            str(ruta_archivo),
            pagesize=self.config.tamano_pagina,
            leftMargin=self.config.margenes[0],
            rightMargin=self.config.margenes[1],
            topMargin=self.config.margenes[2],
            bottomMargin=self.config.margenes[3]
        )

        elementos = []

        # Encabezado
        elementos.extend(self._crear_encabezado(
            "Reporte Diario de Planning",
            f"Fecha: {datetime.now().strftime('%d/%m/%Y')}"
        ))

        # Estadísticas generales
        elementos.extend(self._crear_seccion("Resumen Ejecutivo"))

        stats_datos = [
            ['Total OCs', str(estadisticas.get('total_oc', len(datos_oc)))],
            ['Total ASNs', str(estadisticas.get('total_asn', len(datos_asn)))],
            ['Validaciones Exitosas', str(estadisticas.get('exitosas', 0))],
            ['Errores Detectados', str(estadisticas.get('errores', 0))],
        ]

        tabla_stats = self._crear_tabla_datos(
            stats_datos,
            ['Métrica', 'Valor'],
            [8*cm, 6*cm]
        )
        elementos.append(tabla_stats)

        # Detalle de OCs
        if datos_oc:
            elementos.extend(self._crear_seccion(f"Órdenes de Compra ({len(datos_oc)})"))

            oc_tabla = []
            for oc in datos_oc[:15]:
                oc_tabla.append([
                    oc.get('OC', 'N/A'),
                    oc.get('Proveedor', 'N/A')[:20],
                    f"{oc.get('Total_OC', 0):,.0f}",
                    oc.get('Status', 'N/A')
                ])

            tabla_oc = self._crear_tabla_datos(
                oc_tabla,
                ['OC', 'Proveedor', 'Total', 'Status'],
                [4*cm, 5*cm, 3*cm, 3*cm]
            )
            elementos.append(tabla_oc)

        # Generar PDF
        doc.build(elementos, onFirstPage=self._crear_pie_pagina, onLaterPages=self._crear_pie_pagina)

        logger.info(f"✅ Reporte diario PDF generado: {ruta_archivo}")
        return str(ruta_archivo)

    def crear_reporte_errores(
        self,
        errores: List[Dict],
        titulo: str = "Reporte de Errores",
        nombre_archivo: str = None
    ) -> str:
        """
        Crea un reporte de errores en PDF.

        Args:
            errores: Lista de errores
            titulo: Título del reporte
            nombre_archivo: Nombre del archivo

        Returns:
            Ruta al archivo generado
        """
        if not REPORTLAB_AVAILABLE:
            logger.error("❌ ReportLab no disponible")
            return ""

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        nombre_archivo = nombre_archivo or f"Errores_{timestamp}.pdf"
        ruta_archivo = self.output_dir / nombre_archivo

        doc = SimpleDocTemplate(
            str(ruta_archivo),
            pagesize=self.config.tamano_pagina,
            leftMargin=self.config.margenes[0],
            rightMargin=self.config.margenes[1],
            topMargin=self.config.margenes[2],
            bottomMargin=self.config.margenes[3]
        )

        elementos = []

        # Encabezado
        elementos.extend(self._crear_encabezado(titulo))

        # Resumen
        criticos = sum(1 for e in errores if 'CRÍTICO' in str(e.get('severidad', '')))
        altos = sum(1 for e in errores if 'ALTO' in str(e.get('severidad', '')))

        elementos.append(Paragraph(
            f"Total de errores: <b>{len(errores)}</b> | "
            f"Críticos: <b style='color:red'>{criticos}</b> | "
            f"Altos: <b style='color:orange'>{altos}</b>",
            self._styles['NormalCorp']
        ))
        elementos.append(Spacer(1, 20))

        # Tabla de errores
        if errores:
            elementos.extend(self._crear_seccion("Detalle de Errores"))

            errores_datos = []
            for e in errores[:30]:
                errores_datos.append([
                    e.get('fecha', 'N/A')[:16] if e.get('fecha') else 'N/A',
                    e.get('tipo_error', e.get('tipo', 'N/A'))[:15],
                    e.get('severidad', 'N/A')[:10],
                    e.get('mensaje', '')[:40],
                    'Sí' if e.get('resuelto') else 'No'
                ])

            tabla = self._crear_tabla_datos(
                errores_datos,
                ['Fecha', 'Tipo', 'Severidad', 'Mensaje', 'Resuelto'],
                [3*cm, 3*cm, 2.5*cm, 6*cm, 1.5*cm]
            )
            elementos.append(tabla)

        # Generar PDF
        doc.build(elementos, onFirstPage=self._crear_pie_pagina, onLaterPages=self._crear_pie_pagina)

        logger.info(f"✅ Reporte de errores PDF generado: {ruta_archivo}")
        return str(ruta_archivo)


# ===============================================================
# FUNCIÓN DE CONVENIENCIA
# ===============================================================

_generador_pdf: Optional[GeneradorPDF] = None


def get_generador_pdf() -> GeneradorPDF:
    """Obtiene instancia global del generador PDF."""
    global _generador_pdf
    if _generador_pdf is None:
        _generador_pdf = GeneradorPDF()
    return _generador_pdf


# ===============================================================
# EXPORTAR
# ===============================================================

__all__ = [
    'GeneradorPDF',
    'get_generador_pdf',
    'ConfiguracionPDF',
    'REPORTLAB_AVAILABLE',
]


# ===============================================================
# EJECUCIÓN DIRECTA
# ===============================================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("📄 GENERADOR DE PDF - SAC CEDIS 427")
    print("=" * 60)

    if not REPORTLAB_AVAILABLE:
        print("\n❌ ReportLab no está instalado")
        print("   Ejecuta: pip install reportlab")
    else:
        print("\n✅ ReportLab disponible")

        # Crear ejemplo
        pdf = GeneradorPDF()

        # Generar reporte de prueba
        archivo = pdf.crear_reporte_validacion_oc(
            oc_numero="OC123456",
            resultado="exitoso",
            datos={
                'total_oc': 1000,
                'total_distro': 1000,
                'diferencia': 0,
                'tiempo': 1.5
            },
            errores=[]
        )

        if archivo:
            print(f"\n📄 Reporte de prueba generado: {archivo}")

    print("\n" + "=" * 60)
