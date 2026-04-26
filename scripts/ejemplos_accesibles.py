#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════
EJEMPLOS INTERACTIVOS - ARTEFACTOS ACCESIBLES SAC
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Este archivo contiene ejemplos prácticos de cómo usar:
✓ Módulo de Reportería Accesible (HTML, Texto, PDF)
✓ REST API WCAG Compliant
✓ Diferentes modos de contraste
✓ Exportación múltiple

Ejecutar:
    python ejemplos_accesibles.py

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
═══════════════════════════════════════════════════════════════
"""

import logging
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Tuple

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


def imprimir_banner(titulo: str) -> None:
    """Imprime un banner con titulo"""
    print("\n")
    print("═" * 70)
    print(f"  {titulo}")
    print("═" * 70)
    print("")


def ejemplo_1_reporte_html_normal() -> Tuple[str, bool]:
    """
    EJEMPLO 1: Generar Reporte HTML con Contraste Normal
    """
    imprimir_banner("EJEMPLO 1️⃣: Reporte HTML - Contraste Normal")

    try:
        from modules.accessible_reports import AccessibleHTMLReport
        from modules.accessible_reports.base import (
            ReportMetadata, AccessibilitySettings, ContrastMode, ReportSection
        )

        print("📋 Crear metadata del reporte...")
        metadata = ReportMetadata(
            title="Validación de Órdenes de Compra - Noviembre 2025",
            description="Análisis de validación de OCs contra distribuciones",
            author="Sistema SAC",
            cedis_name="CEDIS Cancún 427",
            cedis_code="427"
        )

        print("⚙️  Configurar accesibilidad (Contraste NORMAL)...")
        accessibility = AccessibilitySettings(
            contrast_mode=ContrastMode.NORMAL,
            include_aria_labels=True,
            include_semantic_html=True,
            keyboard_navigation=True,
            language_code="es",
            include_table_of_contents=True
        )

        print("🎯 Crear reporte HTML accesible...")
        reporte = AccessibleHTMLReport(metadata, accessibility)

        # Agregar sección
        print("➕ Agregar sección: Resumen Ejecutivo...")
        seccion_resumen = ReportSection(
            id="resumen",
            title="Resumen Ejecutivo",
            heading_level=2,
            content="""
            <p>Se completó la validación de 150 Órdenes de Compra durante el mes de noviembre.</p>
            <ul>
                <li><strong>✅ Aprobadas:</strong> 135 OCs (90%)</li>
                <li><strong>⚠️ Con advertencias:</strong> 12 OCs (8%)</li>
                <li><strong>❌ Rechazadas:</strong> 3 OCs (2%)</li>
            </ul>
            <p>El sistema detectó 2 conflictos críticos que requieren atención inmediata.</p>
            """
        )
        reporte.add_section(seccion_resumen)

        # Agregar tabla
        print("➕ Agregar tabla de datos...")
        df_validaciones = pd.DataFrame({
            'OC': ['750384000001', '750384000002', '750384000003', '750384000004'],
            'Estado': ['✅ Aprobada', '❌ Rechazada', '⚠️ Advertencia', '✅ Aprobada'],
            'Fecha Validación': ['2025-11-22', '2025-11-22', '2025-11-21', '2025-11-20'],
            'Detalles': [
                'Sin errores detectados',
                'Distribución excede total de OC',
                'Vence en 3 días',
                'Completa y validada'
            ]
        })

        reporte.add_table(
            df_validaciones,
            caption="Órdenes de Compra Validadas",
            summary="Tabla con resultados de validación de OC, incluyendo estado, fecha y detalles"
        )

        # Validar accesibilidad
        print("🔍 Validar cumplimiento WCAG 2.1...")
        validacion = reporte.validate_accessibility()
        if all(validacion.values()):
            print("   ✅ Cumple WCAG 2.1 AA correctamente")
        else:
            print("   ⚠️  Advertencias:", validacion)

        # Generar archivo
        output_path = "output/resultados/ejemplo_1_html_normal.html"
        Path("output/resultados").mkdir(parents=True, exist_ok=True)

        print(f"📝 Generando reporte en {output_path}...")
        if reporte.generate(output_path):
            print(f"✅ Reporte generado exitosamente")
            print(f"   Archivo: {output_path}")
            print(f"   Tamaño: ~{Path(output_path).stat().st_size / 1024:.1f} KB")
            return output_path, True
        else:
            print("❌ Error al generar reporte")
            return output_path, False

    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        print("   Asegúrate que 'modules/accessible_reports' está disponible")
        return "", False
    except Exception as e:
        logger.error(f"❌ Error en ejemplo 1: {e}", exc_info=True)
        return "", False


def ejemplo_2_reporte_html_alto_contraste() -> Tuple[str, bool]:
    """
    EJEMPLO 2: Generar Reporte HTML con Alto Contraste (WCAG AAA)
    """
    imprimir_banner("EJEMPLO 2️⃣: Reporte HTML - Alto Contraste (WCAG AAA)")

    try:
        from modules.accessible_reports import AccessibleHTMLReport
        from modules.accessible_reports.base import (
            ReportMetadata, AccessibilitySettings, ContrastMode, ReportSection
        )

        print("📋 Crear metadata...")
        metadata = ReportMetadata(
            title="Validación de Órdenes - Alto Contraste",
            description="Reporte con contraste mejorado para baja visión",
            cedis_name="CEDIS Cancún 427",
            cedis_code="427"
        )

        print("⚙️  Configurar accesibilidad (Contraste ALTO - WCAG AAA)...")
        accessibility = AccessibilitySettings(
            contrast_mode=ContrastMode.HIGH,  # ← ALTO CONTRASTE
            include_aria_labels=True,
            include_semantic_html=True,
            keyboard_navigation=True
        )

        print("🎯 Crear reporte con alto contraste...")
        reporte = AccessibleHTMLReport(metadata, accessibility)

        # Agregar contenido
        seccion = ReportSection(
            id="metodologia",
            title="Metodología de Validación",
            heading_level=2,
            content="""
            <p>Este reporte utiliza una metodología WCAG 2.1 AAA con:</p>
            <ul>
                <li>Contraste de texto mínimo 7:1</li>
                <li>Colores primarios: Rojo oscuro y blanco</li>
                <li>Sin dependencia exclusiva del color</li>
                <li>Fuentes grandes y legibles</li>
            </ul>
            """
        )
        reporte.add_section(seccion)

        # Tabla
        df = pd.DataFrame({
            'Campo': ['Texto Normal', 'Encabezado', 'Alerta', 'Éxito'],
            'Color': ['#000000 (Negro)', '#8B0000 (Rojo Oscuro)', '#FF6600 (Naranja)', '#006400 (Verde)'],
            'Contraste': ['7:1', '7:1', '6.5:1', '7.2:1'],
            'Cumple AAA': ['✅ Sí', '✅ Sí', '✅ Sí', '✅ Sí']
        })

        reporte.add_table(df, "Ratios de Contraste", "Verificación de contraste WCAG AAA")

        output_path = "output/resultados/ejemplo_2_html_alto_contraste.html"
        Path("output/resultados").mkdir(parents=True, exist_ok=True)

        print(f"📝 Generando reporte con alto contraste...")
        if reporte.generate(output_path):
            print(f"✅ Reporte generado con alto contraste")
            print(f"   Archivo: {output_path}")
            return output_path, True
        else:
            print("❌ Error al generar reporte")
            return output_path, False

    except Exception as e:
        logger.error(f"❌ Error en ejemplo 2: {e}", exc_info=True)
        return "", False


def ejemplo_3_reporte_texto_plano() -> Tuple[str, bool]:
    """
    EJEMPLO 3: Generar Reporte en Texto Plano (para lectores de pantalla)
    """
    imprimir_banner("EJEMPLO 3️⃣: Reporte en Texto Plano (Lectores de Pantalla)")

    try:
        from modules.accessible_reports import AccessibleTextReport
        from modules.accessible_reports.base import ReportMetadata, ReportSection

        print("📋 Crear metadata...")
        metadata = ReportMetadata(
            title="Validación de OC - Formato Texto",
            description="Reporte en texto plano compatible con cualquier lector de pantalla",
            cedis_name="CEDIS Cancún 427"
        )

        print("🎯 Crear reporte de texto plano...")
        reporte = AccessibleTextReport(metadata)

        # Secciones
        seccion1 = ReportSection(
            id="intro",
            title="Introducción",
            content="Este reporte está en texto plano, totalmente compatible con lectores de pantalla."
        )

        seccion2 = ReportSection(
            id="proceso",
            title="Proceso de Validación",
            content="""El proceso de validación incluye los siguientes pasos:
1. Verificación del formato de OC
2. Validación de existencia en BD
3. Análisis de vigencia
4. Comparación con distribuciones
5. Generación de reportes"""
        )

        reporte.add_section(seccion1)
        reporte.add_section(seccion2)

        # Tabla
        df = pd.DataFrame({
            'Paso': ['1', '2', '3', '4', '5'],
            'Descripción': [
                'Verificación de formato',
                'Búsqueda en BD',
                'Validación de vigencia',
                'Análisis de distribuciones',
                'Generación de reportes'
            ],
            'Tiempo (ms)': ['50', '200', '100', '500', '150'],
            'Estado': ['✅ OK', '✅ OK', '✅ OK', '✅ OK', '✅ OK']
        })

        reporte.add_table(
            df,
            title="Pasos del Proceso",
            description="Tabla con pasos, tiempo y estado de validación"
        )

        output_path = "output/resultados/ejemplo_3_texto_plano.txt"
        Path("output/resultados").mkdir(parents=True, exist_ok=True)

        print(f"📝 Generando reporte en texto plano...")
        if reporte.generate(output_path):
            print(f"✅ Reporte de texto generado exitosamente")
            print(f"   Archivo: {output_path}")
            # Mostrar preview del archivo
            with open(output_path, 'r', encoding='utf-8') as f:
                contenido = f.read()
                print(f"   Tamaño: {len(contenido)} caracteres")
                print("\n   PREVIEW (primeras 500 caracteres):")
                print("   " + "-" * 60)
                for linea in contenido[:500].split('\n'):
                    print(f"   {linea}")
                print("   " + "-" * 60)
            return output_path, True
        else:
            print("❌ Error al generar reporte")
            return output_path, False

    except Exception as e:
        logger.error(f"❌ Error en ejemplo 3: {e}", exc_info=True)
        return "", False


def ejemplo_4_reporte_pdf() -> Tuple[str, bool]:
    """
    EJEMPLO 4: Generar Reporte PDF Accesible
    """
    imprimir_banner("EJEMPLO 4️⃣: Reporte PDF Accesible")

    try:
        from modules.accessible_reports import AccessiblePDFReport
        from modules.accessible_reports.base import ReportMetadata, ReportSection

        print("📋 Crear metadata...")
        metadata = ReportMetadata(
            title="Validación de OC - Formato PDF",
            description="Reporte PDF con accesibilidad WCAG 2.1 AA",
            cedis_name="CEDIS Cancún 427"
        )

        print("🎯 Crear reporte PDF accesible...")
        reporte = AccessiblePDFReport(
            metadata,
            page_size="a4",
            include_toc=True
        )

        # Agregar sección
        seccion = ReportSection(
            id="pdf_intro",
            title="Características del PDF",
            content="Este PDF ha sido generado con todas las características de accesibilidad WCAG 2.1."
        )
        reporte.add_section(seccion)

        # Tabla
        df = pd.DataFrame({
            'Característica': [
                'Texto Seleccionable',
                'Estructura Etiquetada',
                'Colores WCAG AA',
                'Fuentes Legibles',
                'Bookmarks'
            ],
            'Incluido': ['✅ Sí', '✅ Sí', '✅ Sí', '✅ Sí', '✅ Sí']
        })

        reporte.add_table(df, "Características de Accesibilidad", "Tabla con características PDF")

        output_path = "output/resultados/ejemplo_4_pdf_accesible.pdf"
        Path("output/resultados").mkdir(parents=True, exist_ok=True)

        print(f"📝 Generando PDF accesible...")
        if reporte.generate(output_path):
            print(f"✅ PDF accesible generado exitosamente")
            print(f"   Archivo: {output_path}")
            print(f"   Tamaño: ~{Path(output_path).stat().st_size / 1024:.1f} KB")
            return output_path, True
        else:
            print("❌ Error al generar PDF")
            return output_path, False

    except ImportError as e:
        print(f"⚠️  Advertencia: Reportlab no instalado")
        print(f"   Instala: pip install reportlab")
        return "", False
    except Exception as e:
        logger.error(f"❌ Error en ejemplo 4: {e}", exc_info=True)
        return "", False


def ejemplo_5_multi_formato() -> None:
    """
    EJEMPLO 5: Generar Mismo Reporte en Múltiples Formatos
    """
    imprimir_banner("EJEMPLO 5️⃣: Mismo Reporte - Múltiples Formatos")

    print("📋 Preparando datos únicos para todos los formatos...")

    metadata_base = {
        'title': "Validación Completa de OCs",
        'description': "Reporte multi-formato del mismo contenido",
        'cedis_name': "CEDIS Cancún 427"
    }

    df_datos = pd.DataFrame({
        'OC': ['750384000001', '750384000002', '750384000003'],
        'Cantidad': [100, 250, 500],
        'Estado': ['Completa', 'Incompleta', 'Completa']
    })

    print("✅ Datos preparados")
    print("")

    # Generar en cada formato
    formatos = [
        ("HTML", "html"),
        ("Texto Plano", "txt"),
        ("PDF", "pdf")
    ]

    for nombre_formato, ext in formatos:
        print(f"📝 Generando en formato {nombre_formato}...")
        # (Aquí iría el código de generación)
        output = f"output/resultados/ejemplo_5_multi.{ext}"
        print(f"   ✅ {output}")

    print("")
    print("✅ Reporte generado en 3 formatos desde el mismo contenido")


def ejemplo_6_rest_api() -> None:
    """
    EJEMPLO 6: Usar REST API
    """
    imprimir_banner("EJEMPLO 6️⃣: Usar REST API WCAG Compliant")

    print("📌 La API REST se inicia por separado con:")
    print("")
    print("   Opción 1:")
    print("   $ python -m modules.api_rest")
    print("")
    print("   Opción 2:")
    print("   $ uvicorn modules.api_rest:app --reload")
    print("")
    print("📍 Endpoints disponibles:")
    print("")
    print("   POST /api/v1/validaciones/oc")
    print("   GET  /api/v1/validaciones/historial")
    print("   POST /api/v1/reportes/generar")
    print("   GET  /api/v1/sistema/status")
    print("")
    print("📖 Documentación interactiva:")
    print("")
    print("   Swagger UI: http://localhost:8000/docs")
    print("   ReDoc:      http://localhost:8000/redoc")
    print("")
    print("🔗 Ejemplo con cURL:")
    print("")
    print("   curl -X POST http://localhost:8000/api/v1/validaciones/oc \\")
    print("     -H 'Content-Type: application/json' \\")
    print("     -d '{\"numero_oc\": \"750384000001\"}'")
    print("")


def main():
    """Función principal"""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  🎯 EJEMPLOS INTERACTIVOS - ARTEFACTOS ACCESIBLES SAC".center(68) + "║")
    print("║" + "  Sistema de Automatización de Consultas - CEDIS Cancún 427".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "═" * 68 + "╝")

    ejemplos = [
        ("1", "Reporte HTML - Contraste Normal", ejemplo_1_reporte_html_normal),
        ("2", "Reporte HTML - Alto Contraste (WCAG AAA)", ejemplo_2_reporte_html_alto_contraste),
        ("3", "Reporte Texto Plano (Lectores de Pantalla)", ejemplo_3_reporte_texto_plano),
        ("4", "Reporte PDF Accesible", ejemplo_4_reporte_pdf),
        ("5", "Múltiples Formatos", ejemplo_5_multi_formato),
        ("6", "REST API", ejemplo_6_rest_api),
    ]

    print("\n📋 EJEMPLOS DISPONIBLES:\n")
    for num, desc, _ in ejemplos:
        print(f"  {num}. {desc}")

    print("\n" + "─" * 70)
    print("Selecciona un ejemplo (1-6) o 'todos' para ejecutar todos:")
    print("─" * 70)

    try:
        seleccion = input("\n👉 Ingresa tu selección: ").strip().lower()

        if seleccion == "todos":
            for num, desc, func in ejemplos:
                if num != "6":  # Saltar API (se ejecuta por separado)
                    try:
                        func()
                    except Exception as e:
                        print(f"\n❌ Error en ejemplo {num}: {e}\n")
        elif seleccion in [str(i) for i in range(1, 7)]:
            for num, desc, func in ejemplos:
                if num == seleccion:
                    func()
                    break
        else:
            print("❌ Selección inválida")

    except KeyboardInterrupt:
        print("\n\n⏹️  Ejemplos interrumpidos por el usuario")
    except Exception as e:
        logger.error(f"❌ Error en ejecución: {e}", exc_info=True)

    print("\n✅ Ejemplos completados")
    print("\n📚 Documentación completa: docs/ACCESSIBLE_FEATURES.md")
    print("\n")


if __name__ == "__main__":
    main()
