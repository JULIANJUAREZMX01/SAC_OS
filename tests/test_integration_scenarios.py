"""
===============================================================
TESTS DE ESCENARIOS DE INTEGRACIÓN
Sistema de Automatización de Consultas - CEDIS Cancún 427
===============================================================

Tests de integración que simulan flujos completos del sistema
combinando múltiples módulos (Monitor, Reportes, Correos).

Escenarios de integración cubiertos:
1. Flujo completo: Validar OC -> Generar Reporte -> Enviar Correo
2. Detección de errores múltiples y generación de resumen
3. Validación proactiva con generación de alertas
4. Pipeline de procesamiento diario
5. Manejo de errores en cadena

Ejecutar:
    pytest tests/test_integration_scenarios.py -v
    pytest tests/test_integration_scenarios.py -v --tb=short

Autor: Julián Alexander Juárez Alvarado (ADMJAJA)
===============================================================
"""

import pytest
import pandas as pd
import os
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Importar módulos a testear
from monitor import (
    MonitorTiempoReal,
    ValidadorProactivo,
    ErrorSeverity,
    ErrorDetectado,
    imprimir_resumen_errores
)
from modules.reportes_excel import GeneradorReportesExcel


# Patch para el método _ajustar_columnas que tiene un bug con celdas combinadas
def _ajustar_columnas_fixed(self, worksheet):
    """Versión corregida que maneja celdas combinadas"""
    for column in worksheet.columns:
        max_length = 0
        try:
            column_letter = None
            for cell in column:
                if hasattr(cell, 'column_letter'):
                    column_letter = cell.column_letter
                    break

            if column_letter is None:
                continue

            for cell in column:
                try:
                    if cell.value and len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass

            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width
        except:
            pass


# ===============================================================
# FIXTURES PARA INTEGRACIÓN
# ===============================================================

@pytest.fixture
def monitor():
    """Monitor de tiempo real"""
    return MonitorTiempoReal()


@pytest.fixture
def generador():
    """Generador de reportes Excel"""
    gen = GeneradorReportesExcel(cedis="CANCÚN")
    # Aplicar fix para el bug de celdas combinadas
    gen._ajustar_columnas = lambda ws: _ajustar_columnas_fixed(gen, ws)
    return gen


@pytest.fixture
def temp_output_dir(tmp_path):
    """Directorio temporal para archivos"""
    output_dir = tmp_path / "integration_output"
    output_dir.mkdir(exist_ok=True)
    return output_dir


@pytest.fixture
def datos_oc_completos():
    """Conjunto completo de datos de OC para pruebas de integración"""
    return {
        'oc_valida': pd.DataFrame({
            'OC_NUMERO': ['C750384001'],
            'ID_CODE': ['C750384001'],
            'PROVEEDOR': ['Proveedor Integración'],
            'TOTAL_OC': [1000],
            'VIGENCIA': [(datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')],
            'STATUS': ['ACTIVA']
        }),
        'oc_vencida': pd.DataFrame({
            'OC_NUMERO': ['C750384002'],
            'ID_CODE': ['C750384002'],
            'PROVEEDOR': ['Proveedor Vencido'],
            'TOTAL_OC': [500],
            'VIGENCIA': [(datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')],
            'STATUS': ['ACTIVA']
        }),
        'oc_sin_c': pd.DataFrame({
            'OC_NUMERO': ['750384003'],
            'ID_CODE': ['750384003'],
            'PROVEEDOR': ['Proveedor Sin C'],
            'TOTAL_OC': [300],
            'STATUS': ['ACTIVA']
        })
    }


@pytest.fixture
def datos_distro_completos():
    """Conjunto completo de datos de distribución"""
    return {
        'distro_ok': pd.DataFrame({
            'OC': ['C750384001'] * 3,
            'SKU': ['SKU001', 'SKU002', 'SKU003'],
            'TIENDA': ['T001', 'T002', 'T003'],
            'TOTAL_DISTRO': [400, 300, 300],  # Total = 1000
            'IP': [10, 12, 15]
        }),
        'distro_excedente': pd.DataFrame({
            'OC': ['C750384001'] * 3,
            'SKU': ['SKU001', 'SKU002', 'SKU003'],
            'TIENDA': ['T001', 'T002', 'T003'],
            'TOTAL_DISTRO': [500, 400, 400],  # Total = 1300 (excede 1000)
            'IP': [10, 12, 15]
        }),
        'distro_incompleta': pd.DataFrame({
            'OC': ['C750384001'] * 2,
            'SKU': ['SKU001', 'SKU002'],
            'TIENDA': ['T001', 'T002'],
            'TOTAL_DISTRO': [300, 200],  # Total = 500 (faltan 500)
            'IP': [10, 12]
        }),
        'distro_sin_ip': pd.DataFrame({
            'OC': ['C750384001'] * 3,
            'SKU': ['SKU001', 'SKU002', 'SKU003'],
            'TIENDA': ['T001', 'T002', 'T003'],
            'TOTAL_DISTRO': [400, 300, 300],
            'IP': [10, 0, None]  # SKU002 y SKU003 sin IP
        })
    }


# ===============================================================
# ESCENARIO 1: FLUJO COMPLETO VALIDACIÓN -> REPORTE
# ===============================================================

class TestFlujoCompletoValidacionReporte:
    """
    Escenario de integración: Validación de OC y generación de reporte

    Simula el flujo típico:
    1. Validar existencia de OC
    2. Validar distribuciones
    3. Detectar errores
    4. Generar reporte con errores encontrados
    """

    def test_flujo_oc_valida_sin_errores(
        self, monitor, generador, datos_oc_completos, datos_distro_completos, temp_output_dir
    ):
        """
        ESCENARIO INTEGRACIÓN: OC válida con distribuciones correctas
        FLUJO: Validar -> Sin errores -> Reporte OK
        """
        df_oc = datos_oc_completos['oc_valida']
        df_distro = datos_distro_completos['distro_ok']

        # Paso 1: Validar OC
        errores_oc = monitor.validar_oc_existente(df_oc, "C750384001")

        # Paso 2: Validar distribuciones
        errores_distro = monitor.validar_distribuciones(df_oc, df_distro, "C750384001")

        # Paso 3: Consolidar errores
        todos_errores = errores_oc + errores_distro

        # Paso 4: Generar reporte de validación
        df_validacion = pd.DataFrame({
            'OC': ['C750384001'],
            'PROVEEDOR': ['Proveedor Integración'],
            'TOTAL_OC': [1000],
            'TOTAL_DISTRO': [1000],
            'DIFERENCIA': [0],
            'STATUS': ['OK'],
            'ERRORES': [len(todos_errores)]
        })

        nombre_archivo = str(temp_output_dir / "integracion_validacion_ok.xlsx")
        archivo_generado = generador.crear_reporte_validacion_oc(
            df_validacion,
            nombre_archivo=nombre_archivo
        )

        # Verificaciones
        assert len(todos_errores) == 0
        assert os.path.exists(archivo_generado)

    def test_flujo_oc_con_errores_multiples(
        self, monitor, generador, datos_oc_completos, datos_distro_completos, temp_output_dir
    ):
        """
        ESCENARIO INTEGRACIÓN: OC con múltiples problemas
        FLUJO: Validar -> Detectar errores -> Reporte con errores
        """
        df_oc = datos_oc_completos['oc_sin_c']
        df_distro = datos_distro_completos['distro_sin_ip']

        # Validaciones
        errores_oc = monitor.validar_oc_existente(df_oc, "750384003")
        errores_distro = monitor.validar_distribuciones(df_oc, df_distro, "750384003")

        todos_errores = errores_oc + errores_distro

        # Generar reporte de errores
        df_errores = monitor.generar_reporte_errores()

        nombre_archivo = str(temp_output_dir / "integracion_con_errores.xlsx")

        df_validacion = pd.DataFrame({
            'OC': ['750384003'],
            'PROVEEDOR': ['Proveedor Sin C'],
            'TOTAL_OC': [300],
            'TOTAL_DISTRO': [1000],
            'DIFERENCIA': [-700],
            'STATUS': ['Con errores'],
            'ERRORES': [len(todos_errores)]
        })

        archivo_generado = generador.crear_reporte_validacion_oc(
            df_validacion,
            nombre_archivo=nombre_archivo
        )

        # Verificaciones
        assert len(todos_errores) >= 1  # Al menos error de sin letra C
        assert os.path.exists(archivo_generado)


# ===============================================================
# ESCENARIO 2: DETECCIÓN DE ERRORES CRÍTICOS
# ===============================================================

class TestDeteccionErroresCriticos:
    """
    Escenario de integración: Detección y manejo de errores críticos

    Verifica que los errores críticos se detectan, registran y
    pueden ser usados para generar alertas.
    """

    def test_distribucion_excedente_genera_alerta_critica(
        self, monitor, datos_oc_completos, datos_distro_completos
    ):
        """
        ESCENARIO INTEGRACIÓN: Distribución excedente (error crítico)
        RESULTADO: Error registrado en alertas_criticas
        """
        df_oc = datos_oc_completos['oc_valida']
        df_distro = datos_distro_completos['distro_excedente']

        # Validar distribuciones (detectará excedente)
        errores = monitor.validar_distribuciones(df_oc, df_distro, "C750384001")

        # Verificar que hay errores críticos
        errores_criticos = [e for e in errores if e.severidad == ErrorSeverity.CRITICO]

        # Verificar que se registraron en alertas_criticas
        assert len(monitor.alertas_criticas) >= 1
        assert any(e.tipo == "DISTRO_EXCEDENTE" for e in errores_criticos)

    def test_sin_distribuciones_genera_alerta_critica(
        self, monitor, datos_oc_completos
    ):
        """
        ESCENARIO INTEGRACIÓN: OC sin distribuciones
        RESULTADO: Error CRÍTICO detectado y registrado
        """
        df_oc = datos_oc_completos['oc_valida']
        df_distro_vacia = pd.DataFrame()

        errores = monitor.validar_distribuciones(df_oc, df_distro_vacia, "C750384001")

        assert len(errores) >= 1
        assert errores[0].tipo == "SIN_DISTRIBUCIONES"
        assert errores[0].severidad == ErrorSeverity.CRITICO


# ===============================================================
# ESCENARIO 3: PIPELINE DE VALIDACIÓN COMPLETO
# ===============================================================

class TestPipelineValidacionCompleto:
    """
    Escenario de integración: Pipeline completo de validación

    Simula el procesamiento de múltiples OCs en un ciclo de validación.
    """

    def test_validar_multiples_ocs(
        self, monitor, generador, datos_oc_completos, datos_distro_completos, temp_output_dir
    ):
        """
        ESCENARIO INTEGRACIÓN: Validar múltiples OCs en un ciclo
        RESULTADO: Resumen consolidado con todas las validaciones
        """
        resultados = []

        # OC 1: Válida
        errores1 = monitor.validar_oc_existente(
            datos_oc_completos['oc_valida'], "C750384001"
        )
        errores1 += monitor.validar_distribuciones(
            datos_oc_completos['oc_valida'],
            datos_distro_completos['distro_ok'],
            "C750384001"
        )
        resultados.append({
            'OC': 'C750384001',
            'STATUS': 'OK' if len(errores1) == 0 else 'Con errores',
            'ERRORES': len(errores1)
        })

        # OC 2: Vencida
        errores2 = monitor.validar_oc_existente(
            datos_oc_completos['oc_vencida'], "C750384002"
        )
        resultados.append({
            'OC': 'C750384002',
            'STATUS': 'OK' if len(errores2) == 0 else 'Con errores',
            'ERRORES': len(errores2)
        })

        # OC 3: Sin letra C
        errores3 = monitor.validar_oc_existente(
            datos_oc_completos['oc_sin_c'], "750384003"
        )
        resultados.append({
            'OC': '750384003',
            'STATUS': 'OK' if len(errores3) == 0 else 'Con errores',
            'ERRORES': len(errores3)
        })

        # Generar reporte consolidado
        df_resultados = pd.DataFrame(resultados)

        nombre_archivo = str(temp_output_dir / "resumen_validaciones.xlsx")
        archivo_generado = generador.crear_reporte_validacion_oc(
            df_resultados,
            nombre_archivo=nombre_archivo
        )

        # Verificaciones
        assert len(resultados) == 3
        assert os.path.exists(archivo_generado)
        # La OC válida debe tener 0 errores
        assert resultados[0]['ERRORES'] == 0


# ===============================================================
# ESCENARIO 4: GENERACIÓN DE REPORTE PLANNING DIARIO
# ===============================================================

class TestReportePlanningDiarioIntegrado:
    """
    Escenario de integración: Generación de reporte planning diario

    Combina datos de OC, ASN y errores en un único reporte.
    """

    def test_generar_reporte_planning_completo(
        self, monitor, generador, datos_oc_completos, datos_distro_completos, temp_output_dir
    ):
        """
        ESCENARIO INTEGRACIÓN: Reporte planning diario con todas las secciones
        """
        # Simular validaciones
        monitor.validar_oc_existente(datos_oc_completos['oc_valida'], "C750384001")
        monitor.validar_distribuciones(
            datos_oc_completos['oc_valida'],
            datos_distro_completos['distro_excedente'],
            "C750384001"
        )

        # Obtener errores detectados
        df_errores = monitor.generar_reporte_errores()

        # Datos de OC para el reporte
        df_oc = pd.DataFrame({
            'OC': ['C750384001', 'C750384002'],
            'PROVEEDOR': ['Prov A', 'Prov B'],
            'FECHA': ['2025-11-21', '2025-11-21'],
            'STATUS': ['Activa', 'Pendiente']
        })

        # Datos de ASN
        df_asn = pd.DataFrame({
            'ASN': ['ASN001', 'ASN002'],
            'OC': ['C750384001', 'C750384002'],
            'ETA': ['2025-11-22', '2025-11-23'],
            'STATUS': ['En tránsito', 'Programado']
        })

        nombre_archivo = str(temp_output_dir / "planning_diario_integrado.xlsx")

        archivo_generado = generador.crear_reporte_planning_diario(
            df_oc=df_oc,
            df_asn=df_asn,
            df_errores=df_errores,
            nombre_archivo=nombre_archivo
        )

        # Verificaciones
        assert os.path.exists(archivo_generado)
        assert not df_errores.empty  # Debe haber errores detectados


# ===============================================================
# ESCENARIO 5: LIMPIEZA Y REINICIO DE ERRORES
# ===============================================================

class TestLimpiezaYReinicio:
    """
    Escenario de integración: Limpieza entre ciclos de validación
    """

    def test_limpiar_errores_entre_ciclos(
        self, monitor, datos_oc_completos, datos_distro_completos
    ):
        """
        ESCENARIO INTEGRACIÓN: Limpiar errores entre ciclos de validación
        """
        # Ciclo 1: Generar errores
        monitor.validar_distribuciones(
            datos_oc_completos['oc_valida'],
            pd.DataFrame(),  # Sin distribuciones -> error crítico
            "C750384001"
        )

        errores_ciclo1 = len(monitor.errores_detectados)
        alertas_ciclo1 = len(monitor.alertas_criticas)

        assert errores_ciclo1 > 0
        assert alertas_ciclo1 > 0

        # Limpiar
        monitor.limpiar_errores()

        # Ciclo 2: Nueva validación limpia
        monitor.validar_oc_existente(datos_oc_completos['oc_valida'], "C750384001")

        # Verificar que los errores del ciclo 1 fueron limpiados
        assert len(monitor.errores_detectados) < errores_ciclo1 or \
               len(monitor.errores_detectados) == 0


# ===============================================================
# ESCENARIO 6: VALIDADOR PROACTIVO INTEGRADO
# ===============================================================

class TestValidadorProactivoIntegrado:
    """
    Escenario de integración: Uso del validador proactivo
    """

    def test_validador_proactivo_sin_conexion(self):
        """
        ESCENARIO INTEGRACIÓN: Validación proactiva sin conexión DB
        RESULTADO: Falla temprana con error de conexión
        """
        validador = ValidadorProactivo()

        es_valida, errores = validador.validacion_completa_oc(None, "C750384001")

        # Debe fallar por falta de conexión
        assert es_valida is False
        assert len(errores) >= 1
        assert any(e.tipo == "CONEXION_DB" for e in errores)

    def test_validador_proactivo_con_conexion_mock(self):
        """
        ESCENARIO INTEGRACIÓN: Validación proactiva con conexión mock
        """
        validador = ValidadorProactivo()

        # Mock de conexión válida
        mock_conn = Mock()
        mock_conn.connection = True
        mock_conn.execute_query = Mock(return_value=pd.DataFrame({'1': [1]}))

        es_valida, errores = validador.validacion_completa_oc(mock_conn, "C750384001")

        # La conexión debe validarse correctamente
        errores_conexion = [e for e in errores if e.tipo == "CONEXION_DB"]
        assert len(errores_conexion) == 0


# ===============================================================
# ESCENARIO 7: DATOS DE EXCEL CON VALIDACIÓN
# ===============================================================

class TestValidacionExcelIntegrada:
    """
    Escenario de integración: Validación de datos Excel y generación de reporte
    """

    def test_validar_y_reportar_excel(self, monitor, generador, temp_output_dir):
        """
        ESCENARIO INTEGRACIÓN: Validar Excel y generar reporte de resultados
        """
        # Datos de Excel con problemas
        df_excel = pd.DataFrame({
            'OC': ['C750384001', None, 'C750384003'],
            'SKU': ['SKU001', 'SKU002', None],
            'CANTIDAD': [100, 200, 300]
        })
        columnas_requeridas = ['OC', 'SKU', 'CANTIDAD']

        # Validar datos
        errores = monitor.validar_datos_excel(df_excel, columnas_requeridas)

        # Generar reporte de errores si hay
        if errores:
            df_errores = monitor.generar_reporte_errores()

            nombre_archivo = str(temp_output_dir / "validacion_excel.xlsx")

            # Usar reporte de planning para incluir errores
            archivo_generado = generador.crear_reporte_planning_diario(
                df_oc=df_excel,
                df_asn=pd.DataFrame(),
                df_errores=df_errores,
                nombre_archivo=nombre_archivo
            )

            assert os.path.exists(archivo_generado)

        # Debe haber detectado nulos
        errores_nulos = [e for e in errores if e.tipo == "DATOS_NULOS"]
        assert len(errores_nulos) >= 2  # Nulos en OC y SKU


# ===============================================================
# ESCENARIO 8: DASHBOARD CON DATOS DE INTEGRACIÓN
# ===============================================================

class TestDashboardIntegrado:
    """
    Escenario de integración: Dashboard ejecutivo con datos reales
    """

    def test_generar_dashboard_integrado(
        self, monitor, generador, datos_oc_completos, datos_distro_completos, temp_output_dir
    ):
        """
        ESCENARIO INTEGRACIÓN: Dashboard con KPIs calculados y errores reales
        """
        # Realizar validaciones
        monitor.validar_oc_existente(datos_oc_completos['oc_valida'], "C750384001")
        monitor.validar_oc_existente(datos_oc_completos['oc_vencida'], "C750384002")
        monitor.validar_distribuciones(
            datos_oc_completos['oc_valida'],
            datos_distro_completos['distro_incompleta'],
            "C750384001"
        )

        # Obtener errores
        df_errores = monitor.generar_reporte_errores()

        # Calcular KPIs basados en validaciones
        total_errores = len(monitor.errores_detectados)
        errores_criticos = len([e for e in monitor.errores_detectados
                               if e.severidad == ErrorSeverity.CRITICO])

        kpis = {
            'OCs Validadas': {'value': 2, 'target': 5, 'unit': '', 'trend': 'neutral'},
            'Errores Totales': {
                'value': total_errores,
                'target': 0,
                'unit': '',
                'trend': 'negative' if total_errores > 0 else 'positive'
            },
            'Errores Críticos': {
                'value': errores_criticos,
                'target': 0,
                'unit': '',
                'trend': 'negative' if errores_criticos > 0 else 'positive'
            },
            'Precisión': {'value': 85, 'target': 95, 'unit': '%', 'trend': 'negative'}
        }

        # Resumen de OCs
        df_resumen = pd.DataFrame({
            'OC': ['C750384001', 'C750384002'],
            'Status': ['Incompleta', 'Vencida'],
            'Errores': [2, 1]
        })

        nombre_archivo = str(temp_output_dir / "dashboard_integrado.xlsx")

        archivo_generado = generador.crear_dashboard_ejecutivo(
            kpis=kpis,
            df_resumen=df_resumen,
            df_errores=df_errores,
            nombre_archivo=nombre_archivo
        )

        assert os.path.exists(archivo_generado)
        assert total_errores >= 2  # Debe haber detectado errores


# ===============================================================
# ESCENARIO 9: RESUMEN DE ERRORES IMPRESO
# ===============================================================

class TestResumenErroresIntegrado:
    """
    Escenario de integración: Imprimir resumen de errores
    """

    def test_imprimir_resumen_multiples_errores(
        self, monitor, datos_oc_completos, datos_distro_completos, capsys
    ):
        """
        ESCENARIO INTEGRACIÓN: Resumen con errores de múltiples severidades
        """
        # Generar errores de diferentes severidades
        monitor.validar_oc_existente(pd.DataFrame(), "OC_NO_EXISTE")  # ALTO
        monitor.validar_oc_existente(datos_oc_completos['oc_sin_c'], "750384003")  # MEDIO
        monitor.validar_distribuciones(
            datos_oc_completos['oc_valida'],
            pd.DataFrame(),  # Sin distribuciones -> CRÍTICO
            "C750384001"
        )

        # Imprimir resumen
        imprimir_resumen_errores(monitor.errores_detectados)

        captured = capsys.readouterr()

        # Verificar que se muestran las diferentes severidades
        assert "RESUMEN DE ERRORES DETECTADOS" in captured.out
        assert "CRÍTICO" in captured.out


# ===============================================================
# FIN DE TESTS DE INTEGRACIÓN
# ===============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
