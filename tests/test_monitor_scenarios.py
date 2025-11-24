"""
===============================================================
TESTS DE ESCENARIOS DE FUNCIONALIDAD - MONITOR Y VALIDACIONES
Sistema de Automatización de Consultas - CEDIS Cancún 427
===============================================================

Tests unitarios que simulan distintos escenarios básicos
de validación de órdenes de compra, distribuciones y ASN.

Escenarios cubiertos:
1. Validación de OC existente/no existente
2. Validación de OC vencida
3. Distribución excedente (crítico)
4. Distribución incompleta
5. OC sin distribuciones
6. SKU sin Inner Pack
7. ASN con status inválido
8. ASN sin actualización reciente
9. Validación de datos Excel
10. Generación de reportes de errores

Ejecutar:
    pytest tests/test_monitor_scenarios.py -v
    pytest tests/test_monitor_scenarios.py -v --tb=short

Autor: Julián Alexander Juárez Alvarado (ADMJAJA)
===============================================================
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Importar módulos a testear
from monitor import (
    MonitorTiempoReal,
    ValidadorProactivo,
    ErrorSeverity,
    ErrorDetectado,
    imprimir_resumen_errores
)


# ===============================================================
# FIXTURES - DATOS DE PRUEBA
# ===============================================================

@pytest.fixture
def monitor():
    """Monitor sin configuración de email"""
    return MonitorTiempoReal()


@pytest.fixture
def monitor_con_email():
    """Monitor con configuración de email mock"""
    email_config = {
        'smtp_server': 'smtp.test.com',
        'smtp_port': 587,
        'user': 'test@test.com',
        'password': 'test123',
        'alert_recipients': 'alerts@test.com'
    }
    return MonitorTiempoReal(email_config=email_config)


@pytest.fixture
def validador():
    """Validador proactivo"""
    return ValidadorProactivo()


@pytest.fixture
def df_oc_valida():
    """DataFrame de OC válida"""
    return pd.DataFrame({
        'OC_NUMERO': ['C750384123456'],
        'ID_CODE': ['C750384123456'],
        'PROVEEDOR': ['PROVEEDOR TEST'],
        'TOTAL_OC': [1000],
        'VIGENCIA': [(datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')],
        'STATUS': ['ACTIVA']
    })


@pytest.fixture
def df_oc_vencida():
    """DataFrame de OC vencida"""
    return pd.DataFrame({
        'OC_NUMERO': ['C750384654321'],
        'ID_CODE': ['C750384654321'],
        'PROVEEDOR': ['PROVEEDOR VENCIDO'],
        'TOTAL_OC': [500],
        'VIGENCIA': [(datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')],
        'STATUS': ['ACTIVA']
    })


@pytest.fixture
def df_oc_sin_letra_c():
    """DataFrame de OC sin letra C en ID_CODE"""
    return pd.DataFrame({
        'OC_NUMERO': ['750384111111'],
        'ID_CODE': ['750384111111'],  # Sin prefijo C
        'PROVEEDOR': ['PROVEEDOR SIN C'],
        'TOTAL_OC': [200],
        'STATUS': ['ACTIVA']
    })


@pytest.fixture
def df_distro_completa():
    """DataFrame de distribuciones completas (match con OC)"""
    return pd.DataFrame({
        'OC': ['C750384123456'] * 3,
        'SKU': ['SKU001', 'SKU002', 'SKU003'],
        'TIENDA': ['T001', 'T002', 'T003'],
        'TOTAL_DISTRO': [400, 300, 300],
        'IP': [10, 12, 15]
    })


@pytest.fixture
def df_distro_excedente():
    """DataFrame de distribuciones excedentes (más que OC)"""
    return pd.DataFrame({
        'OC': ['C750384123456'] * 3,
        'SKU': ['SKU001', 'SKU002', 'SKU003'],
        'TIENDA': ['T001', 'T002', 'T003'],
        'TOTAL_DISTRO': [500, 400, 400],  # Total = 1300, excede 1000
        'IP': [10, 12, 15]
    })


@pytest.fixture
def df_distro_incompleta():
    """DataFrame de distribuciones incompletas (menos que OC)"""
    return pd.DataFrame({
        'OC': ['C750384123456'] * 2,
        'SKU': ['SKU001', 'SKU002'],
        'TIENDA': ['T001', 'T002'],
        'TOTAL_DISTRO': [300, 200],  # Total = 500, falta para llegar a 1000
        'IP': [10, 12]
    })


@pytest.fixture
def df_distro_sin_ip():
    """DataFrame de distribuciones con SKUs sin Inner Pack"""
    return pd.DataFrame({
        'OC': ['C750384123456'] * 3,
        'SKU': ['SKU001', 'SKU002', 'SKU003'],
        'TIENDA': ['T001', 'T002', 'T003'],
        'TOTAL_DISTRO': [400, 300, 300],
        'IP': [10, 0, None]  # SKU002 y SKU003 sin IP
    })


@pytest.fixture
def df_asn_valido():
    """DataFrame de ASN válido"""
    return pd.DataFrame({
        'ASN_NUMERO': ['ASN123456789'],
        'STATUS': [10],  # Status válido: Creado
        'ULTIMA_MOD': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
    })


@pytest.fixture
def df_asn_invalido():
    """DataFrame de ASN con status inválido"""
    return pd.DataFrame({
        'ASN_NUMERO': ['ASN987654321'],
        'STATUS': [99],  # Status no reconocido
        'ULTIMA_MOD': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
    })


@pytest.fixture
def df_asn_sin_actualizar():
    """DataFrame de ASN sin actualización reciente"""
    return pd.DataFrame({
        'ASN_NUMERO': ['ASN111111111'],
        'STATUS': [10],
        'ULTIMA_MOD': [(datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d %H:%M:%S')]
    })


# ===============================================================
# ESCENARIO 1: VALIDACIÓN DE CONEXIÓN DB
# ===============================================================

class TestEscenarioConexionDB:
    """Escenarios de validación de conexión a base de datos"""

    def test_sin_conexion_genera_error_critico(self, monitor):
        """
        ESCENARIO: Sin conexión a DB2
        RESULTADO ESPERADO: Error CRÍTICO
        """
        errores = monitor.validar_conexion_db(None)

        assert len(errores) == 1
        assert errores[0].severidad == ErrorSeverity.CRITICO
        assert errores[0].tipo == "CONEXION_DB"
        assert "Sin conexión" in errores[0].mensaje

    def test_conexion_sin_objeto_connection(self, monitor):
        """
        ESCENARIO: Objeto de conexión sin conexión activa
        RESULTADO ESPERADO: Error CRÍTICO
        """
        mock_conn = Mock()
        mock_conn.connection = None

        errores = monitor.validar_conexion_db(mock_conn)

        assert len(errores) == 1
        assert errores[0].severidad == ErrorSeverity.CRITICO

    def test_conexion_valida_sin_errores(self, monitor):
        """
        ESCENARIO: Conexión válida y funcional
        RESULTADO ESPERADO: Sin errores
        """
        mock_conn = Mock()
        mock_conn.connection = True
        mock_conn.execute_query = Mock(return_value=pd.DataFrame({'1': [1]}))

        errores = monitor.validar_conexion_db(mock_conn)

        assert len(errores) == 0

    def test_query_test_falla_genera_error_alto(self, monitor):
        """
        ESCENARIO: Conexión existe pero query de prueba falla
        RESULTADO ESPERADO: Error ALTO
        """
        mock_conn = Mock()
        mock_conn.connection = True
        mock_conn.execute_query = Mock(side_effect=Exception("Query timeout"))

        errores = monitor.validar_conexion_db(mock_conn)

        assert len(errores) == 1
        assert errores[0].severidad == ErrorSeverity.ALTO
        assert errores[0].tipo == "QUERY_TEST_FAILED"


# ===============================================================
# ESCENARIO 2: VALIDACIÓN DE OC EXISTENTE
# ===============================================================

class TestEscenarioOCExistente:
    """Escenarios de validación de existencia de OC"""

    def test_oc_no_encontrada_dataframe_vacio(self, monitor):
        """
        ESCENARIO: OC no existe (DataFrame vacío)
        RESULTADO ESPERADO: Error ALTO - OC no encontrada
        """
        df_vacio = pd.DataFrame()

        errores = monitor.validar_oc_existente(df_vacio, "C750384999999")

        assert len(errores) == 1
        assert errores[0].severidad == ErrorSeverity.ALTO
        assert errores[0].tipo == "OC_NO_ENCONTRADA"
        assert "C750384999999" in errores[0].mensaje

    def test_oc_no_encontrada_dataframe_none(self, monitor):
        """
        ESCENARIO: OC no existe (DataFrame None)
        RESULTADO ESPERADO: Error ALTO - OC no encontrada
        """
        errores = monitor.validar_oc_existente(None, "C750384888888")

        assert len(errores) == 1
        assert errores[0].severidad == ErrorSeverity.ALTO
        assert errores[0].tipo == "OC_NO_ENCONTRADA"

    def test_oc_valida_sin_errores(self, monitor, df_oc_valida):
        """
        ESCENARIO: OC válida con todos los campos correctos
        RESULTADO ESPERADO: Sin errores
        """
        errores = monitor.validar_oc_existente(df_oc_valida, "C750384123456")

        assert len(errores) == 0

    def test_oc_sin_letra_c_genera_error_medio(self, monitor, df_oc_sin_letra_c):
        """
        ESCENARIO: OC sin prefijo 'C' en ID_CODE
        RESULTADO ESPERADO: Error MEDIO
        """
        errores = monitor.validar_oc_existente(df_oc_sin_letra_c, "750384111111")

        assert len(errores) == 1
        assert errores[0].severidad == ErrorSeverity.MEDIO
        assert errores[0].tipo == "OC_SIN_LETRA_C"


# ===============================================================
# ESCENARIO 3: VALIDACIÓN DE OC VENCIDA
# ===============================================================

class TestEscenarioOCVencida:
    """Escenarios de validación de vigencia de OC"""

    def test_oc_vencida_genera_error_alto(self, monitor, df_oc_vencida):
        """
        ESCENARIO: OC con fecha de vigencia pasada
        RESULTADO ESPERADO: Error ALTO - OC vencida
        """
        errores = monitor.validar_oc_existente(df_oc_vencida, "C750384654321")

        # Debe haber al menos un error de OC vencida
        errores_vencida = [e for e in errores if e.tipo == "OC_VENCIDA"]
        assert len(errores_vencida) >= 1
        assert errores_vencida[0].severidad == ErrorSeverity.ALTO
        assert "VENCIDA" in errores_vencida[0].mensaje


# ===============================================================
# ESCENARIO 4: DISTRIBUCIÓN EXCEDENTE (CRÍTICO)
# ===============================================================

class TestEscenarioDistribucionExcedente:
    """Escenarios de distribución que excede la OC"""

    def test_distro_excedente_genera_error_critico(self, monitor, df_oc_valida, df_distro_excedente):
        """
        ESCENARIO: Total de distribuciones excede total de OC
        RESULTADO ESPERADO: Error CRÍTICO - Distribución excedente

        Este es el escenario más crítico porque puede causar
        sobreasignación de producto a tiendas.
        """
        errores = monitor.validar_distribuciones(
            df_oc_valida,
            df_distro_excedente,
            "C750384123456"
        )

        errores_excedente = [e for e in errores if e.tipo == "DISTRO_EXCEDENTE"]
        assert len(errores_excedente) >= 1
        assert errores_excedente[0].severidad == ErrorSeverity.CRITICO
        assert "EXCEDENTE" in errores_excedente[0].mensaje

        # Verificar que los datos afectados contienen la información correcta
        assert errores_excedente[0].datos_afectados is not None
        assert 'excedente' in errores_excedente[0].datos_afectados


# ===============================================================
# ESCENARIO 5: DISTRIBUCIÓN INCOMPLETA
# ===============================================================

class TestEscenarioDistribucionIncompleta:
    """Escenarios de distribución incompleta"""

    def test_distro_incompleta_genera_error_alto(self, monitor, df_oc_valida, df_distro_incompleta):
        """
        ESCENARIO: Total de distribuciones menor que total de OC
        RESULTADO ESPERADO: Error ALTO - Distribución incompleta
        """
        errores = monitor.validar_distribuciones(
            df_oc_valida,
            df_distro_incompleta,
            "C750384123456"
        )

        errores_incompleta = [e for e in errores if e.tipo == "DISTRO_INCOMPLETA"]
        assert len(errores_incompleta) >= 1
        assert errores_incompleta[0].severidad == ErrorSeverity.ALTO
        assert "INCOMPLETA" in errores_incompleta[0].mensaje


# ===============================================================
# ESCENARIO 6: OC SIN DISTRIBUCIONES
# ===============================================================

class TestEscenarioSinDistribuciones:
    """Escenarios de OC sin distribuciones asignadas"""

    def test_sin_distribuciones_genera_error_critico(self, monitor, df_oc_valida):
        """
        ESCENARIO: OC existe pero no tiene distribuciones
        RESULTADO ESPERADO: Error CRÍTICO - Sin distribuciones
        """
        df_distro_vacia = pd.DataFrame()

        errores = monitor.validar_distribuciones(
            df_oc_valida,
            df_distro_vacia,
            "C750384123456"
        )

        assert len(errores) >= 1
        errores_sin_distro = [e for e in errores if e.tipo == "SIN_DISTRIBUCIONES"]
        assert len(errores_sin_distro) == 1
        assert errores_sin_distro[0].severidad == ErrorSeverity.CRITICO

    def test_sin_distribuciones_none_genera_error_critico(self, monitor, df_oc_valida):
        """
        ESCENARIO: DataFrame de distribuciones es None
        RESULTADO ESPERADO: Error CRÍTICO - Sin distribuciones
        """
        errores = monitor.validar_distribuciones(
            df_oc_valida,
            None,
            "C750384123456"
        )

        assert len(errores) >= 1
        assert errores[0].tipo == "SIN_DISTRIBUCIONES"
        assert errores[0].severidad == ErrorSeverity.CRITICO


# ===============================================================
# ESCENARIO 7: SKU SIN INNER PACK
# ===============================================================

class TestEscenarioSKUSinIP:
    """Escenarios de SKUs sin Inner Pack definido"""

    def test_sku_sin_ip_genera_error_medio(self, monitor, df_oc_valida, df_distro_sin_ip):
        """
        ESCENARIO: Algunos SKUs no tienen Inner Pack
        RESULTADO ESPERADO: Error MEDIO - SKU sin IP
        """
        errores = monitor.validar_distribuciones(
            df_oc_valida,
            df_distro_sin_ip,
            "C750384123456"
        )

        errores_sin_ip = [e for e in errores if e.tipo == "SKU_SIN_IP"]
        assert len(errores_sin_ip) >= 1
        assert errores_sin_ip[0].severidad == ErrorSeverity.MEDIO
        assert "Inner Pack" in errores_sin_ip[0].mensaje


# ===============================================================
# ESCENARIO 8: VALIDACIÓN DE ASN
# ===============================================================

class TestEscenarioValidacionASN:
    """Escenarios de validación de ASN"""

    def test_asn_no_encontrado_genera_error_alto(self, monitor):
        """
        ESCENARIO: ASN no existe en el sistema
        RESULTADO ESPERADO: Error ALTO - ASN no encontrado
        """
        errores = monitor.validar_asn_status(pd.DataFrame(), "ASN999999999")

        assert len(errores) == 1
        assert errores[0].severidad == ErrorSeverity.ALTO
        assert errores[0].tipo == "ASN_NO_ENCONTRADO"

    def test_asn_status_invalido_genera_error_medio(self, monitor, df_asn_invalido):
        """
        ESCENARIO: ASN con status no reconocido
        RESULTADO ESPERADO: Error MEDIO - Status inválido
        """
        errores = monitor.validar_asn_status(df_asn_invalido, "ASN987654321")

        errores_invalido = [e for e in errores if e.tipo == "ASN_STATUS_INVALIDO"]
        assert len(errores_invalido) >= 1
        assert errores_invalido[0].severidad == ErrorSeverity.MEDIO

    def test_asn_sin_actualizar_genera_error_bajo(self, monitor, df_asn_sin_actualizar):
        """
        ESCENARIO: ASN sin actualización por más de 7 días
        RESULTADO ESPERADO: Error BAJO - Sin actualización
        """
        errores = monitor.validar_asn_status(df_asn_sin_actualizar, "ASN111111111")

        errores_sin_act = [e for e in errores if e.tipo == "ASN_SIN_ACTUALIZACION"]
        assert len(errores_sin_act) >= 1
        assert errores_sin_act[0].severidad == ErrorSeverity.BAJO

    def test_asn_valido_sin_errores(self, monitor, df_asn_valido):
        """
        ESCENARIO: ASN válido con status correcto y reciente
        RESULTADO ESPERADO: Sin errores
        """
        errores = monitor.validar_asn_status(df_asn_valido, "ASN123456789")

        assert len(errores) == 0


# ===============================================================
# ESCENARIO 9: VALIDACIÓN DE DATOS EXCEL
# ===============================================================

class TestEscenarioValidacionExcel:
    """Escenarios de validación de datos de Excel"""

    def test_excel_vacio_genera_error_alto(self, monitor):
        """
        ESCENARIO: Archivo Excel vacío o inválido
        RESULTADO ESPERADO: Error ALTO - Excel vacío
        """
        columnas_requeridas = ['OC', 'SKU', 'CANTIDAD']

        errores = monitor.validar_datos_excel(pd.DataFrame(), columnas_requeridas)

        assert len(errores) == 1
        assert errores[0].severidad == ErrorSeverity.ALTO
        assert errores[0].tipo == "EXCEL_VACIO"

    def test_columnas_faltantes_genera_error_alto(self, monitor):
        """
        ESCENARIO: Excel con columnas requeridas faltantes
        RESULTADO ESPERADO: Error ALTO - Columnas faltantes
        """
        df_incompleto = pd.DataFrame({
            'OC': ['C750384123456'],
            'SKU': ['SKU001']
            # Falta 'CANTIDAD'
        })
        columnas_requeridas = ['OC', 'SKU', 'CANTIDAD']

        errores = monitor.validar_datos_excel(df_incompleto, columnas_requeridas)

        errores_columnas = [e for e in errores if e.tipo == "COLUMNAS_FALTANTES"]
        assert len(errores_columnas) >= 1
        assert errores_columnas[0].severidad == ErrorSeverity.ALTO
        assert 'CANTIDAD' in str(errores_columnas[0].detalles)

    def test_datos_nulos_genera_error_medio(self, monitor):
        """
        ESCENARIO: Excel con valores nulos en columnas críticas
        RESULTADO ESPERADO: Error MEDIO por cada columna con nulos
        """
        df_con_nulos = pd.DataFrame({
            'OC': ['C750384123456', None, 'C750384789012'],
            'SKU': ['SKU001', 'SKU002', None],
            'CANTIDAD': [100, 200, 300]
        })
        columnas_requeridas = ['OC', 'SKU', 'CANTIDAD']

        errores = monitor.validar_datos_excel(df_con_nulos, columnas_requeridas)

        errores_nulos = [e for e in errores if e.tipo == "DATOS_NULOS"]
        assert len(errores_nulos) >= 2  # Nulos en OC y SKU
        assert all(e.severidad == ErrorSeverity.MEDIO for e in errores_nulos)

    def test_excel_valido_sin_errores(self, monitor):
        """
        ESCENARIO: Excel con todos los datos correctos
        RESULTADO ESPERADO: Sin errores
        """
        df_valido = pd.DataFrame({
            'OC': ['C750384123456', 'C750384789012'],
            'SKU': ['SKU001', 'SKU002'],
            'CANTIDAD': [100, 200]
        })
        columnas_requeridas = ['OC', 'SKU', 'CANTIDAD']

        errores = monitor.validar_datos_excel(df_valido, columnas_requeridas)

        assert len(errores) == 0


# ===============================================================
# ESCENARIO 10: GENERACIÓN DE REPORTE DE ERRORES
# ===============================================================

class TestEscenarioReporteErrores:
    """Escenarios de generación de reporte de errores"""

    def test_generar_reporte_errores_vacio(self, monitor):
        """
        ESCENARIO: Sin errores detectados
        RESULTADO ESPERADO: DataFrame vacío
        """
        df_reporte = monitor.generar_reporte_errores()

        assert df_reporte.empty

    def test_generar_reporte_con_errores(self, monitor, df_oc_valida, df_distro_excedente):
        """
        ESCENARIO: Varios errores detectados
        RESULTADO ESPERADO: DataFrame con los errores
        """
        # Generar algunos errores
        monitor.validar_oc_existente(pd.DataFrame(), "OC_INEXISTENTE")
        monitor.validar_distribuciones(df_oc_valida, df_distro_excedente, "C750384123456")

        df_reporte = monitor.generar_reporte_errores()

        assert not df_reporte.empty
        assert 'Severidad' in df_reporte.columns
        assert 'Tipo' in df_reporte.columns
        assert 'Mensaje' in df_reporte.columns
        assert len(df_reporte) >= 2

    def test_limpiar_errores(self, monitor):
        """
        ESCENARIO: Limpiar registro de errores
        RESULTADO ESPERADO: Listas de errores vacías
        """
        # Agregar errores
        monitor.validar_oc_existente(pd.DataFrame(), "OC_TEST")
        assert len(monitor.errores_detectados) > 0

        # Limpiar
        monitor.limpiar_errores()

        assert len(monitor.errores_detectados) == 0
        assert len(monitor.alertas_criticas) == 0


# ===============================================================
# ESCENARIO 11: PROCESAMIENTO DE ALERTAS CRÍTICAS
# ===============================================================

class TestEscenarioAlertasCriticas:
    """Escenarios de procesamiento de alertas críticas"""

    def test_alertas_criticas_se_registran(self, monitor, df_oc_valida):
        """
        ESCENARIO: Se detecta un error crítico
        RESULTADO ESPERADO: Error se agrega a alertas_criticas
        """
        # Sin distribuciones genera error crítico
        monitor.validar_distribuciones(df_oc_valida, pd.DataFrame(), "C750384123456")

        assert len(monitor.alertas_criticas) >= 1
        assert all(e.severidad == ErrorSeverity.CRITICO for e in monitor.alertas_criticas)

    def test_errores_no_criticos_no_son_alertas(self, monitor, df_oc_sin_letra_c):
        """
        ESCENARIO: Se detecta error no crítico
        RESULTADO ESPERADO: No se agrega a alertas_criticas
        """
        monitor.validar_oc_existente(df_oc_sin_letra_c, "750384111111")

        # Los errores de letra C son MEDIO, no deben ir a alertas críticas
        alertas_letra_c = [
            a for a in monitor.alertas_criticas
            if a.tipo == "OC_SIN_LETRA_C"
        ]
        assert len(alertas_letra_c) == 0


# ===============================================================
# ESCENARIO 12: VALIDADOR PROACTIVO
# ===============================================================

class TestEscenarioValidadorProactivo:
    """Escenarios del validador proactivo"""

    def test_validacion_completa_sin_conexion_falla(self, validador):
        """
        ESCENARIO: Validación completa sin conexión DB
        RESULTADO ESPERADO: Retorna False y errores
        """
        es_valida, errores = validador.validacion_completa_oc(None, "C750384123456")

        assert es_valida is False
        assert len(errores) >= 1
        # El primer error debe ser de conexión
        assert any(e.tipo == "CONEXION_DB" for e in errores)

    def test_validacion_completa_con_conexion_valida(self, validador):
        """
        ESCENARIO: Validación completa con conexión válida
        RESULTADO ESPERADO: Retorna resultado basado en datos
        """
        mock_conn = Mock()
        mock_conn.connection = True
        mock_conn.execute_query = Mock(return_value=pd.DataFrame({'1': [1]}))

        es_valida, errores = validador.validacion_completa_oc(mock_conn, "C750384123456")

        # Debe pasar la validación de conexión
        errores_conexion = [e for e in errores if e.tipo == "CONEXION_DB"]
        assert len(errores_conexion) == 0


# ===============================================================
# ESCENARIO 13: ERROR DETECTADO DATACLASS
# ===============================================================

class TestEscenarioErrorDetectado:
    """Escenarios de la clase ErrorDetectado"""

    def test_crear_error_con_datos_minimos(self):
        """
        ESCENARIO: Crear error con datos mínimos requeridos
        RESULTADO ESPERADO: Error creado correctamente
        """
        error = ErrorDetectado(
            tipo="TEST_ERROR",
            severidad=ErrorSeverity.MEDIO,
            mensaje="Error de prueba",
            detalles="Detalles del error",
            solucion="Solución propuesta",
            timestamp=datetime.now(),
            modulo="TEST_MODULE"
        )

        assert error.tipo == "TEST_ERROR"
        assert error.severidad == ErrorSeverity.MEDIO
        assert error.datos_afectados is None

    def test_crear_error_con_datos_afectados(self):
        """
        ESCENARIO: Crear error con datos afectados
        RESULTADO ESPERADO: Error con datos adicionales
        """
        datos = {'oc': 'C123', 'cantidad': 100}
        error = ErrorDetectado(
            tipo="TEST_ERROR",
            severidad=ErrorSeverity.ALTO,
            mensaje="Error con datos",
            detalles="Detalles",
            solucion="Solución",
            timestamp=datetime.now(),
            modulo="TEST",
            datos_afectados=datos
        )

        assert error.datos_afectados is not None
        assert error.datos_afectados['oc'] == 'C123'


# ===============================================================
# ESCENARIO 14: NIVELES DE SEVERIDAD
# ===============================================================

class TestEscenarioNivelesSeveridad:
    """Escenarios para validar niveles de severidad"""

    def test_severidad_critico(self):
        """Verifica valor de severidad CRITICO"""
        assert ErrorSeverity.CRITICO.value == "🔴 CRÍTICO"

    def test_severidad_alto(self):
        """Verifica valor de severidad ALTO"""
        assert ErrorSeverity.ALTO.value == "🟠 ALTO"

    def test_severidad_medio(self):
        """Verifica valor de severidad MEDIO"""
        assert ErrorSeverity.MEDIO.value == "🟡 MEDIO"

    def test_severidad_bajo(self):
        """Verifica valor de severidad BAJO"""
        assert ErrorSeverity.BAJO.value == "🟢 BAJO"

    def test_severidad_info(self):
        """Verifica valor de severidad INFO"""
        assert ErrorSeverity.INFO.value == "ℹ️ INFO"


# ===============================================================
# ESCENARIO 15: FUNCIÓN IMPRIMIR RESUMEN
# ===============================================================

class TestEscenarioImprimirResumen:
    """Escenarios de la función imprimir_resumen_errores"""

    def test_imprimir_sin_errores(self, capsys):
        """
        ESCENARIO: Imprimir resumen sin errores
        RESULTADO ESPERADO: Mensaje de sin errores
        """
        imprimir_resumen_errores([])

        captured = capsys.readouterr()
        assert "No se detectaron errores" in captured.out

    def test_imprimir_con_errores(self, capsys):
        """
        ESCENARIO: Imprimir resumen con errores
        RESULTADO ESPERADO: Resumen formateado
        """
        errores = [
            ErrorDetectado(
                tipo="ERROR_1",
                severidad=ErrorSeverity.CRITICO,
                mensaje="Error crítico de prueba",
                detalles="Detalles",
                solucion="Solución",
                timestamp=datetime.now(),
                modulo="TEST"
            ),
            ErrorDetectado(
                tipo="ERROR_2",
                severidad=ErrorSeverity.MEDIO,
                mensaje="Error medio de prueba",
                detalles="Detalles",
                solucion="Solución",
                timestamp=datetime.now(),
                modulo="TEST"
            )
        ]

        imprimir_resumen_errores(errores)

        captured = capsys.readouterr()
        assert "RESUMEN DE ERRORES DETECTADOS" in captured.out
        assert "2" in captured.out  # Total de errores


# ===============================================================
# FIN DE TESTS DE ESCENARIOS
# ===============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
