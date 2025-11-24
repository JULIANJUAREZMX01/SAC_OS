#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════
SCRIPT PRINCIPAL - SISTEMA DE AUTOMATIZACIÓN DE PLANNING
Chedraui CEDIS Cancún - Manhattan WMS
═══════════════════════════════════════════════════════════════

Este es el punto de entrada principal del sistema que integra:
- Validación de OC vs Distribuciones
- Monitoreo en tiempo real
- Generación de reportes Excel
- Envío automático de correos

Uso:
    python main.py --oc OC12345
    python main.py --reporte-diario
    python main.py --validar-todas

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Analista de Sistemas - CEDIS Chedraui Logística Cancún
═══════════════════════════════════════════════════════════════
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path
import argparse
import pandas as pd
from dotenv import load_dotenv

# Importar módulos del sistema
try:
    from config import DB_CONFIG, CEDIS, EMAIL_CONFIG, PATHS, LOGGING_CONFIG
    from monitor import MonitorTiempoReal, ValidadorProactivo, imprimir_resumen_errores
    from modules.reportes_excel import GeneradorReportesExcel
    from modules.db_connection import (
        DB2Connection,
        DB2ConnectionPool,
        DB2ConnectionError,
        get_connection_info,
        PYODBC_AVAILABLE,
        IBM_DB_AVAILABLE
    )
    from gestor_correos import GestorCorreos
    from notificaciones_telegram import (
        TipoAlerta,
        crear_notificador_desde_config
    )
    from queries import (
        load_query_with_params,
        get_default_loader
    )
    # Importar módulo de credenciales y animaciones
    from modules.modulo_credenciales_setup import (
        ejecutar_setup_credenciales,
        verificar_credenciales_configuradas,
        animar_inicio_proceso,
        animar_fin_proceso,
        animar_validacion_oc,
        animar_generacion_reporte,
        animar_envio_correo,
        animar_conexion_db,
        Colores
    )
    ANIMACIONES_DISPONIBLES = True
except ImportError as e:
    print(f"❌ Error al importar módulos: {e}")
    print("Asegúrate de estar en el directorio correcto y que todos los archivos existan.")
    print(f"Detalles del error: {e}")
    ANIMACIONES_DISPONIBLES = False
    # Definir Colores básico si no se pudo importar
    class Colores:
        RESET = '\033[0m'
        BOLD = '\033[1m'
        DIM = '\033[2m'
        RED = '\033[91m'
        GREEN = '\033[92m'
        YELLOW = '\033[93m'
        BLUE = '\033[94m'
        MAGENTA = '\033[95m'
        CYAN = '\033[96m'

# Cargar variables de entorno
load_dotenv()

# ═══════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE LOGGING
# ═══════════════════════════════════════════════════════════════

def configurar_logging(nivel=logging.INFO):
    """Configura el sistema de logging usando PATHS desde config.py"""

    # Usar directorio de logs desde configuración centralizada
    log_dir = PATHS['logs']
    log_dir.mkdir(parents=True, exist_ok=True)

    # Nombre del archivo de log
    fecha = datetime.now().strftime('%Y%m%d')
    log_file = log_dir / f'planning_automation_{fecha}.log'

    # Usar formato desde configuración centralizada
    log_format = LOGGING_CONFIG.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Configurar handlers
    logging.basicConfig(
        level=nivel,
        format=log_format,
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

    return logging.getLogger(__name__)


logger = configurar_logging()


# ═══════════════════════════════════════════════════════════════
# FUNCIONES PRINCIPALES
# ═══════════════════════════════════════════════════════════════

def imprimir_banner():
    """Imprime el banner del sistema"""
    banner = """
    ═══════════════════════════════════════════════════════════════
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║        SISTEMA DE AUTOMATIZACIÓN DE PLANNING             ║
    ║              Chedraui CEDIS Cancún                        ║
    ║                                                           ║
    ║        Manhattan WMS - DB2 Integration                    ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    
    Desarrollado con ❤️  por:
    Julián Alexander Juárez Alvarado (ADM)
    Analista de Sistemas - CEDIS Chedraui Logística Cancún
    
    "Las máquinas y los sistemas al servicio de los analistas"
    ═══════════════════════════════════════════════════════════════
    """
    print(banner)


def conectar_db(use_pool: bool = False):
    """
    Conecta a la base de datos DB2 de Manhattan WMS

    Esta función establece una conexión real a IBM DB2 utilizando
    el módulo db_connection con soporte para:
    - Retry automático con backoff exponencial
    - Connection pooling (opcional)
    - Manejo de errores y logging

    Args:
        use_pool: Si es True, utiliza el pool de conexiones

    Returns:
        DB2Connection o DB2ConnectionPool si la conexión es exitosa
        None si hay error de configuración o conexión
    """
    logger.info("🔌 Conectando a DB2...")

    # Verificar disponibilidad de drivers
    if not PYODBC_AVAILABLE and not IBM_DB_AVAILABLE:
        logger.error("❌ No hay drivers DB2 disponibles")
        logger.error("   Instala uno de: pip install pyodbc  o  pip install ibm-db")
        return None

    # Mostrar información de conexión
    info = get_connection_info()
    logger.info(f"   📍 Host: {info['host']}")
    logger.info(f"   📍 Database: {info['database']}")
    logger.info(f"   📍 Usuario: {info['user']}")

    # Verificar credenciales configuradas
    if not info['password_configured']:
        logger.warning("⚠️  Credenciales DB2 no configuradas en .env")
        logger.warning("   Configura DB_USER y DB_PASSWORD para conectar")
        logger.warning("   Ejecutando en modo DEMO sin conexión real")
        return None

    try:
        if use_pool:
            # Usar pool de conexiones para múltiples operaciones
            logger.info("🏊 Inicializando pool de conexiones...")
            pool = DB2ConnectionPool(
                config=DB_CONFIG,
                min_connections=1,
                max_connections=5,
                connection_timeout=30.0
            )
            logger.info("✅ Pool de conexiones DB2 inicializado")
            return pool
        else:
            # Conexión simple
            connection = DB2Connection(config=DB_CONFIG)

            if connection.connect():
                logger.info("✅ Conexión a DB2 establecida exitosamente")
                return connection
            else:
                logger.error("❌ No se pudo establecer conexión a DB2")
                return None

    except DB2ConnectionError as e:
        logger.error(f"❌ Error de conexión DB2: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"❌ Error inesperado al conectar: {str(e)}")
        return None


def desconectar_db(connection):
    """
    Cierra la conexión a la base de datos DB2

    Args:
        connection: Objeto DB2Connection o DB2ConnectionPool
    """
    if connection is None:
        return

    try:
        if isinstance(connection, DB2ConnectionPool):
            connection.close_all()
            logger.info("🔌 Pool de conexiones cerrado")
        elif isinstance(connection, DB2Connection):
            connection.disconnect()
            logger.info("🔌 Conexión DB2 cerrada")
    except Exception as e:
        logger.error(f"⚠️  Error al cerrar conexión: {str(e)}")


# ═══════════════════════════════════════════════════════════════
# FUNCIONES DE CONSULTA A DB2
# ═══════════════════════════════════════════════════════════════

def consultar_oc_desde_db(oc_numero: str, db_connection) -> pd.DataFrame:
    """
    Consulta una Orden de Compra desde DB2 Manhattan WMS.

    Args:
        oc_numero: Número de la OC a buscar
        db_connection: Conexión activa a DB2

    Returns:
        DataFrame con los datos de la OC
    """
    if db_connection is None:
        logger.warning("⚠️  Sin conexión DB2, retornando DataFrame vacío")
        return pd.DataFrame()

    try:
        # Cargar query con parámetros
        loader = get_default_loader()
        sql = load_query_with_params(
            "bajo_demanda",
            "buscar_oc",
            {
                "oc_numero": oc_numero,
                "storerkey": CEDIS.get('almacen', 'C22')
            }
        )

        logger.info(f"🔍 Consultando OC {oc_numero} en DB2...")

        # Ejecutar query
        if isinstance(db_connection, DB2ConnectionPool):
            with db_connection.get_connection() as conn:
                df = conn.execute_query(sql)
        else:
            df = db_connection.execute_query(sql)

        logger.info(f"✅ OC consultada: {len(df)} registros encontrados")
        return df

    except Exception as e:
        logger.error(f"❌ Error consultando OC desde DB2: {str(e)}")
        return pd.DataFrame()


def consultar_distribuciones_desde_db(oc_numero: str, db_connection) -> pd.DataFrame:
    """
    Consulta las distribuciones de una OC desde DB2 Manhattan WMS.

    Args:
        oc_numero: Número de la OC de referencia
        db_connection: Conexión activa a DB2

    Returns:
        DataFrame con las distribuciones
    """
    if db_connection is None:
        logger.warning("⚠️  Sin conexión DB2, retornando DataFrame vacío")
        return pd.DataFrame()

    try:
        # Cargar query con parámetros
        sql = load_query_with_params(
            "bajo_demanda",
            "detalle_distribucion",
            {
                "oc_referencia": oc_numero,
                "storerkey": CEDIS.get('almacen', 'C22'),
                "tienda_destino": "%"  # Todas las tiendas
            }
        )

        logger.info(f"🔍 Consultando distribuciones de OC {oc_numero}...")

        # Ejecutar query
        if isinstance(db_connection, DB2ConnectionPool):
            with db_connection.get_connection() as conn:
                df = conn.execute_query(sql)
        else:
            df = db_connection.execute_query(sql)

        logger.info(f"✅ Distribuciones consultadas: {len(df)} registros")
        return df

    except Exception as e:
        logger.error(f"❌ Error consultando distribuciones: {str(e)}")
        return pd.DataFrame()


def consultar_oc_diarias(db_connection, fecha: datetime = None) -> pd.DataFrame:
    """
    Consulta las OC del día actual desde DB2.

    Args:
        db_connection: Conexión activa a DB2
        fecha: Fecha a consultar (default: hoy)

    Returns:
        DataFrame con las OC del día
    """
    if db_connection is None:
        logger.warning("⚠️  Sin conexión DB2, retornando DataFrame vacío")
        return pd.DataFrame()

    try:
        fecha = fecha or datetime.now()
        fecha_str = fecha.strftime('%Y-%m-%d')

        sql = load_query_with_params(
            "obligatorias",
            "oc_diarias",
            {
                "fecha_inicio": fecha_str,
                "fecha_fin": fecha_str,
                "storerkey": CEDIS.get('almacen', 'C22')
            }
        )

        logger.info(f"🔍 Consultando OC del día {fecha_str}...")

        if isinstance(db_connection, DB2ConnectionPool):
            with db_connection.get_connection() as conn:
                df = conn.execute_query(sql)
        else:
            df = db_connection.execute_query(sql)

        logger.info(f"✅ OC diarias: {len(df)} registros")
        return df

    except Exception as e:
        logger.error(f"❌ Error consultando OC diarias: {str(e)}")
        return pd.DataFrame()


def consultar_asn_status(db_connection, fecha: datetime = None) -> pd.DataFrame:
    """
    Consulta el status de ASN desde DB2.

    Args:
        db_connection: Conexión activa a DB2
        fecha: Fecha a consultar (default: últimos 30 días)

    Returns:
        DataFrame con status de ASN
    """
    if db_connection is None:
        logger.warning("⚠️  Sin conexión DB2, retornando DataFrame vacío")
        return pd.DataFrame()

    try:
        fecha_fin = fecha or datetime.now()
        fecha_inicio = datetime(fecha_fin.year, fecha_fin.month, 1)  # Primer día del mes

        sql = load_query_with_params(
            "obligatorias",
            "asn_status",
            {
                "fecha_inicio": fecha_inicio.strftime('%Y-%m-%d'),
                "fecha_fin": fecha_fin.strftime('%Y-%m-%d'),
                "storerkey": CEDIS.get('almacen', 'C22')
            }
        )

        logger.info(f"🔍 Consultando status de ASN...")

        if isinstance(db_connection, DB2ConnectionPool):
            with db_connection.get_connection() as conn:
                df = conn.execute_query(sql)
        else:
            df = db_connection.execute_query(sql)

        logger.info(f"✅ ASN status: {len(df)} registros")
        return df

    except Exception as e:
        logger.error(f"❌ Error consultando ASN status: {str(e)}")
        return pd.DataFrame()


def generar_datos_demo_oc(oc_numero: str) -> tuple:
    """
    Genera datos de demostración para OC cuando no hay conexión DB2.

    ADVERTENCIA: Estos datos son FICTICIOS y solo para propósitos de demostración.
    NO deben usarse para decisiones de negocio reales.

    Args:
        oc_numero: Número de OC

    Returns:
        Tuple con (df_oc, df_distro) - DataFrames con datos de ejemplo
    """
    logger.warning("⚠️ MODO DEMO ACTIVO: Los datos mostrados son FICTICIOS")
    logger.info("📊 Generando datos de demostración (modo DEMO)...")
    print("\n" + "="*60)
    print("⚠️  ADVERTENCIA: DATOS DE DEMOSTRACIÓN")
    print("   Los siguientes datos NO son reales.")
    print("   Para datos reales, configure la conexión a DB2.")
    print("="*60 + "\n")

    df_oc = pd.DataFrame({
        'OC': [oc_numero],
        'TOTAL_OC': [1000],
        'VIGENCIA': [datetime.now()],
        'ID_CODE': ['C123'],
        'STATUS': ['0'],
        'STATUS_DESC': ['Abierta'],
        '_ES_DEMO': [True]  # Flag para identificar datos demo
    })

    df_distro = pd.DataFrame({
        'OC': [oc_numero, oc_numero, oc_numero],
        'TOTAL_DISTRO': [300, 400, 300],
        'TIENDA': ['001', '002', '003'],
        'SKU': ['SKU001', 'SKU002', 'SKU003'],
        'DISTR_QTY': [300, 400, 300],
        'IP': [10, 10, 10],
        '_ES_DEMO': [True, True, True]  # Flag para identificar datos demo
    })

    return df_oc, df_distro


def generar_datos_demo_diario() -> tuple:
    """
    Genera datos de demostración para reporte diario.

    ADVERTENCIA: Estos datos son FICTICIOS y solo para propósitos de demostración.
    NO deben usarse para decisiones de negocio reales.

    Returns:
        Tuple con (df_oc, df_asn, df_errores) - DataFrames con datos de ejemplo
    """
    logger.warning("⚠️ MODO DEMO ACTIVO: Los datos del reporte diario son FICTICIOS")
    logger.info("📊 Generando datos de demostración para reporte diario (modo DEMO)...")
    print("\n" + "="*60)
    print("⚠️  ADVERTENCIA: DATOS DE DEMOSTRACIÓN - REPORTE DIARIO")
    print("   Los siguientes datos NO son reales.")
    print("   Para datos reales, configure la conexión a DB2.")
    print("="*60 + "\n")

    df_oc = pd.DataFrame({
        'OC': ['OC001', 'OC002', 'OC003'],
        'Proveedor': ['PROV1', 'PROV2', 'PROV3'],
        'Total_OC': [1000, 2000, 1500],
        'Status': ['OK', 'OK', 'Pendiente'],
        '_ES_DEMO': [True, True, True]
    })

    df_asn = pd.DataFrame({
        'ASN': ['ASN001', 'ASN002', 'ASN003'],
        'OC': ['OC001', 'OC002', 'OC003'],
        'Status': ['40', '40', '10'],
        'Proveedor': ['PROV1', 'PROV2', 'PROV3'],
        '_ES_DEMO': [True, True, True]
    })

    df_errores = pd.DataFrame()

    return df_oc, df_asn, df_errores


def validar_orden_compra(oc_numero: str, db_connection=None):
    """
    Valida una Orden de Compra completa

    Args:
        oc_numero: Número de la OC a validar
        db_connection: Conexión a DB2 (opcional)
    """
    # Animación de inicio si está disponible
    if ANIMACIONES_DISPONIBLES:
        animar_inicio_proceso(f"VALIDACIÓN DE OC: {oc_numero}")
        animar_validacion_oc(oc_numero)
    else:
        logger.info(f"\n{'='*70}")
        logger.info(f"🔍 INICIANDO VALIDACIÓN DE OC: {oc_numero}")
        logger.info(f"{'='*70}\n")
    
    # Inicializar validador
    validador = ValidadorProactivo()
    monitor = MonitorTiempoReal()
    
    # 1. Validar conexión DB (si existe)
    if db_connection:
        logger.info("📊 Paso 1/4: Validando conexión a DB2...")
        errores_db = monitor.validar_conexion_db(db_connection)
        
        if any(e.severidad.value == '🔴 CRÍTICO' for e in errores_db):
            logger.error("❌ Error crítico en conexión DB2. Abortando validación.")
            imprimir_resumen_errores(errores_db)
            return False
    
    # 2. Consultar datos de OC
    logger.info(f"📊 Paso 2/4: Consultando datos de OC {oc_numero}...")

    # Intentar consulta real a DB2, si no hay conexión usar datos demo
    if db_connection:
        df_oc = consultar_oc_desde_db(oc_numero, db_connection)
        df_distro = consultar_distribuciones_desde_db(oc_numero, db_connection)

        # Si no se encontraron datos, advertir
        if df_oc.empty:
            logger.warning(f"⚠️  No se encontró OC {oc_numero} en DB2")
    else:
        # Modo DEMO - usar datos de ejemplo
        logger.info("⚠️  Modo DEMO: Usando datos de ejemplo")
        df_oc, df_distro = generar_datos_demo_oc(oc_numero)

    # Adaptar columnas si vienen de DB2 real
    if not df_oc.empty and 'qty_original' in df_oc.columns:
        # Mapear columnas de DB2 a formato esperado
        df_oc = df_oc.rename(columns={
            'oc_numero': 'OC',
            'qty_original': 'TOTAL_OC',
            'fecha_entrega': 'VIGENCIA'
        })
        # Agregar TOTAL_OC si no existe
        if 'TOTAL_OC' not in df_oc.columns:
            df_oc['TOTAL_OC'] = df_oc.groupby('OC')['qty_original'].transform('sum') if 'qty_original' in df_oc.columns else 0

    if not df_distro.empty and 'qty_asignada' in df_distro.columns:
        df_distro = df_distro.rename(columns={
            'oc_referencia': 'OC',
            'qty_asignada': 'DISTR_QTY',
            'codigo_tienda': 'TIENDA',
            'sku': 'SKU',
            'inner_pack': 'IP'
        })
    
    # 3. Validar OC
    logger.info("📊 Paso 3/4: Validando datos de OC...")
    errores_oc = monitor.validar_oc_existente(df_oc, oc_numero)
    
    # 4. Validar Distribuciones
    logger.info("📊 Paso 4/4: Validando distribuciones...")
    errores_distro = monitor.validar_distribuciones(df_oc, df_distro, oc_numero)
    
    # Consolidar errores
    todos_errores = errores_oc + errores_distro
    
    # Mostrar resumen
    print("\n")
    imprimir_resumen_errores(todos_errores)
    
    # 5. Generar reporte Excel
    if ANIMACIONES_DISPONIBLES:
        animar_generacion_reporte("Validación OC")
    else:
        logger.info("\n📄 Generando reporte de validación...")

    generador = GeneradorReportesExcel(cedis="CANCÚN")

    # Calcular totales con validación defensiva
    total_oc = df_oc['TOTAL_OC'].sum() if not df_oc.empty and 'TOTAL_OC' in df_oc.columns else 0
    total_distro = df_distro['DISTR_QTY'].sum() if not df_distro.empty and 'DISTR_QTY' in df_distro.columns else 0
    diferencia = total_oc - total_distro

    # Crear DataFrame de validación
    df_validacion = pd.DataFrame({
        'OC': [oc_numero],
        'Total_OC': total_oc,
        'Total_Distro': total_distro,
        'Diferencia': diferencia,
        'STATUS': 'OK' if total_oc == total_distro else 'Revisar'
    })
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    archivo_excel = f"Validacion_OC_{oc_numero}_{timestamp}.xlsx"
    
    generador.crear_reporte_validacion_oc(df_validacion, archivo_excel)
    logger.info(f"✅ Reporte generado: {archivo_excel}")
    
    # 6. Enviar correo (opcional)
    if input("\n📧 ¿Deseas enviar el reporte por correo? (s/n): ").lower() == 's':
        enviar_reporte_validacion(oc_numero, todos_errores, archivo_excel)
    
    # Resultado final
    tiene_criticos = any(e.severidad.value == '🔴 CRÍTICO' for e in todos_errores)

    if tiene_criticos:
        if ANIMACIONES_DISPONIBLES:
            animar_fin_proceso(False, f"OC {oc_numero}: Se detectaron problemas")
        else:
            logger.warning(f"\n⚠️  VALIDACIÓN DE OC {oc_numero}: PROBLEMAS DETECTADOS")
        return False
    else:
        if ANIMACIONES_DISPONIBLES:
            animar_fin_proceso(True, f"OC {oc_numero}: Validación exitosa")
        else:
            logger.info(f"\n✅ VALIDACIÓN DE OC {oc_numero}: EXITOSA")
        return True


def generar_reporte_diario(db_connection=None):
    """
    Genera y envía el reporte diario de Planning

    Args:
        db_connection: Conexión a DB2 (opcional, usa modo DEMO si es None)
    """
    if ANIMACIONES_DISPONIBLES:
        animar_inicio_proceso("REPORTE DIARIO DE PLANNING")
    else:
        logger.info("\n" + "="*70)
        logger.info("📊 GENERANDO REPORTE DIARIO DE PLANNING")
        logger.info("="*70 + "\n")

    # Consultar datos desde DB2 o usar datos demo
    if db_connection:
        logger.info("🔍 Consultando datos desde DB2...")
        df_oc = consultar_oc_diarias(db_connection)
        df_asn = consultar_asn_status(db_connection)
        df_errores = pd.DataFrame()

        # Adaptar columnas de DB2 si es necesario
        if not df_oc.empty:
            df_oc = df_oc.rename(columns={
                'oc_numero': 'OC',
                'qty_original_total': 'Total_OC',
                'status_descripcion': 'Status'
            })
            # Asegurar columna Proveedor
            if 'Proveedor' not in df_oc.columns:
                df_oc['Proveedor'] = df_oc.get('storerkey', 'N/A')

        if not df_asn.empty:
            df_asn = df_asn.rename(columns={
                'status_code': 'Status',
                'status_descripcion': 'Status_Desc'
            })
            # Asegurar columnas necesarias
            if 'ASN' not in df_asn.columns:
                df_asn['ASN'] = df_asn.index.map(lambda x: f'ASN{x:04d}')
            if 'OC' not in df_asn.columns:
                df_asn['OC'] = 'N/A'
            if 'Proveedor' not in df_asn.columns:
                df_asn['Proveedor'] = 'N/A'
    else:
        # Modo DEMO - usar datos de ejemplo
        logger.info("⚠️  Modo DEMO: Usando datos de ejemplo")
        df_oc, df_asn, df_errores = generar_datos_demo_diario()
    
    # Generar reporte Excel
    if ANIMACIONES_DISPONIBLES:
        animar_generacion_reporte("Planning Diario")
    else:
        logger.info("📄 Generando reporte Excel...")

    generador = GeneradorReportesExcel(cedis="CANCÚN")

    fecha = datetime.now().strftime('%Y%m%d')
    archivo_excel = f"Planning_Diario_Cancun_{fecha}.xlsx"

    generador.crear_reporte_planning_diario(df_oc, df_asn, df_errores, archivo_excel)

    if ANIMACIONES_DISPONIBLES:
        animar_fin_proceso(True, f"Reporte generado: {archivo_excel}")
    else:
        logger.info(f"✅ Reporte generado: {archivo_excel}")
    
    # Enviar por correo
    if input("\n📧 ¿Enviar reporte por correo? (s/n): ").lower() == 's':
        destinatarios = input("Destinatarios (separados por coma): ").split(',')
        destinatarios = [d.strip() for d in destinatarios]
        
        enviar_reporte_diario(destinatarios, df_oc, df_asn, archivo_excel)


def enviar_reporte_diario(destinatarios, df_oc, df_asn, archivo_excel):
    """Envía el reporte diario por correo"""
    try:
        if ANIMACIONES_DISPONIBLES:
            animar_envio_correo()
        else:
            logger.info("\n📧 Enviando reporte por correo...")
        
        # Configurar gestor de correos
        email_config = {
            'smtp_server': os.getenv('EMAIL_SMTP_SERVER', 'smtp.office365.com'),
            'smtp_port': int(os.getenv('EMAIL_SMTP_PORT', '587')),
            'user': os.getenv('EMAIL_USER'),
            'password': os.getenv('EMAIL_PASSWORD'),
            'from_name': 'Sistema Planning CEDIS'
        }
        
        # Validar configuración
        if not email_config['user'] or not email_config['password']:
            logger.error("❌ Credenciales de correo no configuradas en .env")
            return False
        
        gestor = GestorCorreos(email_config)
        
        # Enviar correo
        resultado = gestor.enviar_reporte_planning_diario(
            destinatarios=destinatarios,
            df_oc=df_oc,
            df_asn=df_asn,
            archivos_adjuntos=[archivo_excel]
        )
        
        if resultado:
            logger.info("✅ Reporte enviado exitosamente")
            return True
        else:
            logger.error("❌ Error al enviar reporte")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error al enviar correo: {str(e)}")
        return False


def enviar_reporte_validacion(oc_numero, errores, archivo_excel):
    """Envía reporte de validación de OC"""
    try:
        destinatarios = input("Destinatarios (separados por coma): ").split(',')
        destinatarios = [d.strip() for d in destinatarios]
        
        # Determinar status
        tiene_criticos = any(e.severidad.value == '🔴 CRÍTICO' for e in errores)
        tiene_alertas = any(e.severidad.value == '🟠 ALTO' for e in errores)
        
        if tiene_criticos:
            status = 'CRITICO'
        elif tiene_alertas:
            status = 'ALERTA'
        else:
            status = 'OK'
        
        # Preparar detalles
        detalles = {
            'Total Errores': len(errores),
            'Errores Críticos': sum(1 for e in errores if e.severidad.value == '🔴 CRÍTICO'),
            'Alertas': sum(1 for e in errores if e.severidad.value == '🟠 ALTO')
        }
        
        # Configurar y enviar
        email_config = {
            'smtp_server': os.getenv('EMAIL_SMTP_SERVER', 'smtp.office365.com'),
            'smtp_port': int(os.getenv('EMAIL_SMTP_PORT', '587')),
            'user': os.getenv('EMAIL_USER'),
            'password': os.getenv('EMAIL_PASSWORD'),
            'from_name': 'Sistema Planning CEDIS'
        }
        
        gestor = GestorCorreos(email_config)
        
        resultado = gestor.enviar_validacion_oc(
            destinatarios=destinatarios,
            oc_numero=oc_numero,
            status_validacion=status,
            detalles=detalles,
            archivo_excel=archivo_excel
        )
        
        if resultado:
            logger.info("✅ Reporte de validación enviado")
        
    except Exception as e:
        logger.error(f"❌ Error al enviar reporte de validación: {str(e)}")


# ═══════════════════════════════════════════════════════════════
# MENÚ INTERACTIVO
# ═══════════════════════════════════════════════════════════════

def mostrar_menu():
    """Muestra el menú principal del sistema"""
    menu = """
    ╔═══════════════════════════════════════════════════════════╗
    ║                    MENÚ PRINCIPAL                         ║
    ╚═══════════════════════════════════════════════════════════╝

    1️⃣  Validar Orden de Compra
    2️⃣  Generar Reporte Diario
    3️⃣  Enviar Alerta Crítica
    4️⃣  Validar Múltiples OC
    5️⃣  Programa de Recibo

    ───────────────────────────────────────────────────────────
    📧 GESTIÓN DE CONFLICTOS EXTERNOS
    ───────────────────────────────────────────────────────────
    A️⃣  Buscar Conflictos en Correo
    B️⃣  Ver Conflictos Pendientes
    C️⃣  Resolver Conflicto
    D️⃣  Generar Documentación de Conflicto

    ───────────────────────────────────────────────────────────
    📱 TELEGRAM
    ───────────────────────────────────────────────────────────
    6️⃣  Probar Conexión Telegram
    7️⃣  Enviar Mensaje de Prueba
    8️⃣  Enviar Resumen del Sistema

    ───────────────────────────────────────────────────────────
    🔌 BASE DE DATOS
    ───────────────────────────────────────────────────────────
    9️⃣  Probar/Reconectar DB2
    🔟  Ver Estadísticas de Conexión

    ───────────────────────────────────────────────────────────
    ⚙️  CONFIGURACIÓN
    ───────────────────────────────────────────────────────────
    R️⃣  Reconfigurar Credenciales

    0️⃣  Salir

    ───────────────────────────────────────────────────────────
    """
    print(menu)


def menu_interactivo():
    """Ejecuta el menú interactivo con setup de credenciales al inicio"""

    db_connection = None
    telegram_notificador = None

    # ═══════════════════════════════════════════════════════════════
    # PASO 1: SETUP DE CREDENCIALES (si es necesario)
    # Solicita TODAS las credenciales durante la carga inicial
    # ═══════════════════════════════════════════════════════════════

    if ANIMACIONES_DISPONIBLES:
        # Ejecutar setup de credenciales con introducción animada
        resultado_setup = ejecutar_setup_credenciales(
            mostrar_intro=True,
            forzar=False,
            verbose=True
        )

        if not resultado_setup['configurado']:
            print(f"\n{Colores.YELLOW}⚠️  Sistema ejecutando sin configuración completa{Colores.RESET}")
            print(f"{Colores.DIM}   Algunas funciones pueden no estar disponibles{Colores.RESET}\n")
    else:
        # Fallback al banner simple si no hay animaciones
        imprimir_banner()

    # ═══════════════════════════════════════════════════════════════
    # PASO 2: CONEXIÓN A DB2
    # ═══════════════════════════════════════════════════════════════

    print(f"\n{Colores.CYAN}{'═' * 55}{Colores.RESET}")
    print(f"   🔌 {Colores.BOLD}VERIFICANDO CONEXIONES{Colores.RESET}")
    print(f"{Colores.CYAN}{'═' * 55}{Colores.RESET}\n")

    # Animación de conexión a DB2
    if ANIMACIONES_DISPONIBLES:
        animar_conexion_db()

    db_connection = conectar_db()

    if db_connection is None:
        print(f"   {Colores.YELLOW}⚠️  Modo DEMO activo (sin conexión a DB2){Colores.RESET}")
        print(f"   {Colores.DIM}   Las credenciales se configuraron pero el servidor no responde{Colores.RESET}")
    else:
        print(f"   {Colores.GREEN}✅ Conexión a DB2 establecida{Colores.RESET}")

    # ═══════════════════════════════════════════════════════════════
    # PASO 3: INICIALIZACIÓN DE TELEGRAM
    # ═══════════════════════════════════════════════════════════════

    print(f"\n   📱 Verificando Telegram...")
    telegram_notificador = crear_notificador_desde_config()
    if telegram_notificador and telegram_notificador.enabled:
        print(f"   {Colores.GREEN}✅ Telegram configurado y activo{Colores.RESET}")
    else:
        print(f"   {Colores.DIM}ℹ️  Telegram no configurado (opcional){Colores.RESET}")

    try:
        while True:
            mostrar_menu()

            # Mostrar estado de conexiones
            if db_connection:
                print("   📊 Estado DB2: ✅ Conectado")
            else:
                print("   📊 Estado DB2: ⚠️  Modo DEMO")

            if telegram_notificador and telegram_notificador.enabled:
                print("   📱 Estado Telegram: ✅ Activo")
            else:
                print("   📱 Estado Telegram: ⚠️  No configurado")

            opcion = input("\nSelecciona una opción: ").strip()

            if opcion == '1':
                oc_numero = input("\nIngresa el número de OC: ").strip()
                if oc_numero:
                    validar_orden_compra(oc_numero, db_connection)
                else:
                    print("❌ Número de OC inválido")

            elif opcion == '2':
                generar_reporte_diario(db_connection)

            elif opcion == '3':
                print("\n🚨 Enviar Alerta Crítica por Telegram")
                if telegram_notificador and telegram_notificador.enabled:
                    titulo = input("Título de la alerta: ").strip()
                    descripcion = input("Descripción: ").strip()
                    oc = input("Número de OC (opcional, Enter para omitir): ").strip() or None

                    resultado = telegram_notificador.enviar_alerta_critica(
                        titulo=titulo,
                        descripcion=descripcion,
                        oc_numero=oc
                    )
                    if any(resultado.values()):
                        print("✅ Alerta enviada por Telegram")
                    else:
                        print("❌ Error al enviar alerta")
                else:
                    print("⚠️  Telegram no está configurado. Configura TELEGRAM_BOT_TOKEN en .env")

            elif opcion == '4':
                print("\n📊 Validación de múltiples OC")
                ocs = input("Ingresa los números de OC separados por coma: ").strip()
                if ocs:
                    lista_ocs = [oc.strip() for oc in ocs.split(',')]
                    for oc in lista_ocs:
                        validar_orden_compra(oc, db_connection)
                        print("\n" + "-"*70 + "\n")

            elif opcion == '5':
                print("\n📦 Programa de Recibo")
                print("Función en desarrollo")

            elif opcion.upper() == 'A':
                # Buscar Conflictos en Correo
                print("\n📧 BUSCAR CONFLICTOS EN CORREO")
                print("="*50)
                try:
                    from modules.email.email_receiver import EmailReceiver
                    from modules.conflicts import ConflictStorage, ConflictAnalyzer, ConflictNotifier
                    from modules.conflicts.conflict_storage import crear_conflicto_desde_correo
                    from config import IMAP_CONFIG, CONFLICT_CONFIG

                    dias = int(input(f"Días a buscar (default {CONFLICT_CONFIG['dias_busqueda_correos']}): ").strip() or CONFLICT_CONFIG['dias_busqueda_correos'])

                    print(f"\n🔍 Buscando correos de los últimos {dias} días...")

                    receiver = EmailReceiver(IMAP_CONFIG)
                    with receiver:
                        correos = receiver.buscar_correos_conflicto(dias_atras=dias)

                    if not correos:
                        print("✅ No se encontraron correos con conflictos")
                    else:
                        print(f"\n📧 Se encontraron {len(correos)} correos con posibles conflictos:\n")

                        storage = ConflictStorage()
                        analyzer = ConflictAnalyzer()
                        notifier = ConflictNotifier()

                        for i, correo in enumerate(correos, 1):
                            print(f"{i}. [{correo.severidad_detectada.value if correo.severidad_detectada else 'N/A'}]")
                            print(f"   De: {correo.remitente_email}")
                            print(f"   Asunto: {correo.asunto[:60]}...")
                            print(f"   Tipo: {correo.tipo_conflicto_detectado.value if correo.tipo_conflicto_detectado else 'OTRO'}")
                            print(f"   OCs: {', '.join(correo.oc_numeros) if correo.oc_numeros else 'N/A'}")
                            print()

                        procesar = input("¿Procesar estos conflictos? (s/n): ").lower()
                        if procesar == 's':
                            for correo in correos:
                                # Crear conflicto
                                conflicto = crear_conflicto_desde_correo(correo)
                                storage.crear(conflicto)
                                print(f"✅ Conflicto {conflicto.id} creado")

                                # Analizar
                                if CONFLICT_CONFIG['auto_analizar']:
                                    analyzer.analizar_conflicto(conflicto.id)
                                    print(f"   🔍 Analizado")

                                # Notificar
                                if CONFLICT_CONFIG['auto_notificar']:
                                    notifier.notificar_error_no_detectado(conflicto.id)
                                    print(f"   📧 Notificación enviada")

                            print(f"\n✅ {len(correos)} conflictos procesados")

                except ImportError as e:
                    print(f"⚠️ Módulos de conflictos no disponibles: {e}")
                except Exception as e:
                    print(f"❌ Error: {e}")

            elif opcion.upper() == 'B':
                # Ver Conflictos Pendientes
                print("\n📋 CONFLICTOS PENDIENTES")
                print("="*50)
                try:
                    from modules.conflicts import ConflictStorage

                    storage = ConflictStorage()
                    pendientes = storage.listar_pendientes()

                    if not pendientes:
                        print("✅ No hay conflictos pendientes")
                    else:
                        print(f"\n📋 {len(pendientes)} conflictos pendientes:\n")
                        for c in pendientes:
                            print(f"  {c.id} | {c.severidad} | {c.tipo_conflicto}")
                            print(f"         Estado: {c.estado.value}")
                            print(f"         OCs: {', '.join(c.oc_numeros) if c.oc_numeros else 'N/A'}")
                            print(f"         De: {c.correo_remitente_email}")
                            print()

                        # Mostrar estadísticas
                        stats = storage.obtener_estadisticas()
                        print(f"\n📊 Estadísticas:")
                        print(f"   Total: {stats['total']}")
                        print(f"   Pendientes: {stats['pendientes']}")
                        print(f"   Resueltos: {stats['resueltos']}")

                except ImportError as e:
                    print(f"⚠️ Módulos de conflictos no disponibles: {e}")
                except Exception as e:
                    print(f"❌ Error: {e}")

            elif opcion.upper() == 'C':
                # Resolver Conflicto
                print("\n🔧 RESOLVER CONFLICTO")
                print("="*50)
                try:
                    from modules.conflicts import ConflictStorage, ConflictResolver
                    from modules.conflicts.conflict_resolver import solicitar_confirmacion_cli

                    storage = ConflictStorage()
                    pendientes = storage.listar_pendientes()

                    if not pendientes:
                        print("✅ No hay conflictos pendientes para resolver")
                    else:
                        print(f"\n📋 Conflictos disponibles:")
                        for c in pendientes:
                            print(f"  • {c.id}: {c.tipo_conflicto} - {c.correo_asunto[:40]}...")

                        conflicto_id = input("\nIngresa ID del conflicto a resolver: ").strip()

                        if conflicto_id:
                            decision = solicitar_confirmacion_cli(conflicto_id)
                            if decision:
                                resolver = ConflictResolver()
                                resultado = resolver.procesar_decision(conflicto_id, decision)
                                print(resolver.obtener_resumen_resolucion(resultado))

                                # Generar documentación
                                if resultado.exito:
                                    doc = input("\n¿Generar documentación? (s/n): ").lower()
                                    if doc == 's':
                                        ruta = resolver.generar_documentacion(conflicto_id)
                                        if ruta:
                                            print(f"✅ Documentación: {ruta}")

                except ImportError as e:
                    print(f"⚠️ Módulos de conflictos no disponibles: {e}")
                except Exception as e:
                    print(f"❌ Error: {e}")

            elif opcion.upper() == 'D':
                # Generar Documentación de Conflicto
                print("\n📄 GENERAR DOCUMENTACIÓN")
                print("="*50)
                try:
                    from modules.conflicts import ConflictStorage, ConflictResolver, ConflictNotifier

                    storage = ConflictStorage()
                    conflicto_id = input("ID del conflicto: ").strip()

                    if conflicto_id:
                        conflicto = storage.obtener(conflicto_id)
                        if conflicto:
                            resolver = ConflictResolver()
                            ruta = resolver.generar_documentacion(conflicto_id)

                            if ruta:
                                print(f"✅ Documentación generada: {ruta}")

                                responder = input("\n¿Responder al remitente original? (s/n): ").lower()
                                if responder == 's':
                                    notifier = ConflictNotifier()
                                    if notifier.responder_a_remitente(conflicto_id):
                                        print("✅ Respuesta enviada")
                                    else:
                                        print("⚠️ No se pudo enviar respuesta")
                            else:
                                print("❌ Error generando documentación")
                        else:
                            print(f"❌ Conflicto {conflicto_id} no encontrado")

                except ImportError as e:
                    print(f"⚠️ Módulos de conflictos no disponibles: {e}")
                except Exception as e:
                    print(f"❌ Error: {e}")

            elif opcion == '6':
                # Probar Conexión Telegram
                print("\n📱 Probando conexión a Telegram...")
                if telegram_notificador:
                    if telegram_notificador.verificar_conexion():
                        print("✅ Conexión a Telegram verificada")
                    else:
                        print("❌ No se pudo verificar la conexión")
                        print("   Verifica TELEGRAM_BOT_TOKEN en .env")
                else:
                    print("⚠️  Telegram no configurado")
                    print("\n💡 Para configurar Telegram:")
                    print("   1. Crea un bot con @BotFather en Telegram")
                    print("   2. Copia el token del bot")
                    print("   3. Agrega en .env:")
                    print("      TELEGRAM_BOT_TOKEN=tu_token")
                    print("      TELEGRAM_CHAT_IDS=tu_chat_id")

            elif opcion == '7':
                # Enviar Mensaje de Prueba
                print("\n📱 Enviar Mensaje de Prueba por Telegram")
                if telegram_notificador and telegram_notificador.enabled:
                    mensaje = input("Mensaje (Enter para mensaje por defecto): ").strip()
                    if not mensaje:
                        mensaje = f"🧪 Mensaje de prueba desde SAC - {CEDIS['name']} {CEDIS['code']}"

                    resultado = telegram_notificador.enviar_alerta(
                        TipoAlerta.INFO,
                        "Mensaje de Prueba",
                        mensaje,
                        "SISTEMA"
                    )
                    if any(resultado.values()):
                        print("✅ Mensaje enviado exitosamente")
                    else:
                        print("❌ Error al enviar mensaje")
                else:
                    print("⚠️  Telegram no está configurado")

            elif opcion == '8':
                # Enviar Resumen del Sistema
                print("\n📊 Enviando Resumen del Sistema por Telegram...")
                if telegram_notificador and telegram_notificador.enabled:
                    # Datos de ejemplo para el resumen
                    resultado = telegram_notificador.enviar_estado_sistema(
                        db_conectada=db_connection is not None,
                        email_configurado=bool(EMAIL_CONFIG.get('user')),
                        ultimo_reporte=datetime.now().strftime('%d/%m/%Y %H:%M'),
                        errores_pendientes=0
                    )
                    if any(resultado.values()):
                        print("✅ Resumen enviado")
                    else:
                        print("❌ Error al enviar resumen")
                else:
                    print("⚠️  Telegram no está configurado")

            elif opcion == '9':
                # Probar/Reconectar DB2
                print("\n🔌 Probando conexión a DB2...")
                if db_connection:
                    desconectar_db(db_connection)
                db_connection = conectar_db()
                if db_connection:
                    print("✅ Conexión establecida")
                else:
                    print("⚠️  No se pudo conectar - modo DEMO activo")

            elif opcion == '10':
                # Ver estadísticas de conexión
                if db_connection and hasattr(db_connection, 'print_stats'):
                    db_connection.print_stats()
                elif db_connection and hasattr(db_connection, 'get_pool_stats'):
                    stats = db_connection.get_pool_stats()
                    print("\n📊 Estadísticas del Pool:")
                    for key, value in stats.items():
                        print(f"   {key}: {value}")
                else:
                    print("\n⚠️  No hay estadísticas disponibles (modo DEMO)")

            elif opcion.upper() == 'R':
                # Reconfigurar Credenciales
                print(f"\n   {Colores.YELLOW}⚙️  RECONFIGURAR CREDENCIALES{Colores.RESET}")
                print(f"   {'─' * 50}")
                confirmar = input("\n   ¿Deseas reconfigurar las credenciales del sistema? (s/n): ").lower()

                if confirmar in ['s', 'si', 'yes', 'y']:
                    if ANIMACIONES_DISPONIBLES:
                        resultado_reconfig = ejecutar_setup_credenciales(
                            mostrar_intro=False,
                            forzar=True,
                            verbose=True
                        )

                        if resultado_reconfig['configurado']:
                            print(f"\n   {Colores.GREEN}✅ Credenciales actualizadas{Colores.RESET}")
                            print(f"   {Colores.DIM}ℹ️  Reinicia el sistema para aplicar los cambios{Colores.RESET}")
                        else:
                            print(f"\n   {Colores.YELLOW}⚠️  Configuración no completada{Colores.RESET}")
                    else:
                        print("\n   ⚠️  Módulo de configuración no disponible")
                else:
                    print(f"\n   {Colores.DIM}ℹ️  Operación cancelada{Colores.RESET}")

            elif opcion == '0':
                # Notificar cierre del sistema si Telegram está activo
                if telegram_notificador and telegram_notificador.enabled:
                    respuesta = input("\n¿Enviar notificación de cierre por Telegram? (s/n): ").lower()
                    if respuesta == 's':
                        telegram_notificador.enviar_alerta(
                            TipoAlerta.INFO,
                            "Sistema Detenido",
                            "El sistema SAC ha sido detenido manualmente",
                            "SISTEMA"
                        )

                # Mensaje de despedida animado
                if ANIMACIONES_DISPONIBLES:
                    print(f"\n   {Colores.CYAN}{'═' * 55}{Colores.RESET}")
                    print(f"   👋 {Colores.BOLD}¡Hasta pronto!{Colores.RESET}")
                    print(f"   {Colores.DIM}Sistema desarrollado con ❤️ por ADMJAJA{Colores.RESET}")
                    print(f"   {Colores.MAGENTA}\"Las máquinas y los sistemas al servicio de los analistas\"{Colores.RESET}")
                    print(f"   {Colores.CYAN}{'═' * 55}{Colores.RESET}\n")
                else:
                    print("\n👋 ¡Hasta luego!")
                    print("Sistema desarrollado con ❤️  por ADM\n")
                break

            else:
                print(f"\n   {Colores.RED}❌ Opción no válida. Intenta de nuevo.{Colores.RESET}\n")

            input("\nPresiona ENTER para continuar...")
            print("\n" * 2)

    finally:
        # Asegurar cierre de conexión al salir
        if db_connection:
            desconectar_db(db_connection)


# ═══════════════════════════════════════════════════════════════
# MAIN - PUNTO DE ENTRADA
# ═══════════════════════════════════════════════════════════════

def main():
    """Función principal"""
    
    # Configurar argumentos de línea de comandos
    parser = argparse.ArgumentParser(
        description='Sistema de Automatización de Planning - Chedraui CEDIS'
    )
    
    parser.add_argument('--oc', type=str, help='Número de OC a validar')
    parser.add_argument('--reporte-diario', action='store_true', 
                       help='Generar reporte diario')
    parser.add_argument('--menu', action='store_true',
                       help='Mostrar menú interactivo')
    
    args = parser.parse_args()
    
    # Ejecutar según argumentos
    if args.oc:
        imprimir_banner()
        validar_orden_compra(args.oc)
    
    elif args.reporte_diario:
        imprimir_banner()
        db_connection = conectar_db()
        try:
            generar_reporte_diario(db_connection)
        finally:
            desconectar_db(db_connection)
    
    else:
        # Si no hay argumentos, mostrar menú interactivo
        menu_interactivo()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Proceso interrumpido por el usuario")
        print("Sistema desarrollado con ❤️  por ADM\n")
        sys.exit(0)
    except Exception as e:
        logger.error(f"\n❌ Error fatal: {str(e)}", exc_info=True)
        sys.exit(1)
