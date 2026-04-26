#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════
VERIFICADOR DE CONEXIÓN A BASE DE DATOS DB2
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Script para verificar la conectividad a la base de datos DB2
(Manhattan WMS) y validar la configuración del sistema SAC.

Uso:
    python verificar_conexion_db2.py
    python verificar_conexion_db2.py --test-query
    python verificar_conexion_db2.py --verbose

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════
"""

import sys
import os
import socket
import argparse
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ═══════════════════════════════════════════════════════════════
# CONSTANTES Y COLORES
# ═══════════════════════════════════════════════════════════════

class Colores:
    """Códigos ANSI para colores en terminal"""
    VERDE = '\033[92m'
    ROJO = '\033[91m'
    AMARILLO = '\033[93m'
    AZUL = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_banner():
    """Imprime el banner del verificador"""
    banner = """
═══════════════════════════════════════════════════════════════
   🔍 VERIFICADOR DE CONEXIÓN DB2 - SAC v1.0
   Sistema de Automatización de Consultas
   CEDIS Cancún 427 - Tiendas Chedraui
═══════════════════════════════════════════════════════════════
"""
    print(f"{Colores.AZUL}{banner}{Colores.RESET}")


def print_ok(mensaje: str):
    """Imprime mensaje de éxito"""
    print(f"  {Colores.VERDE}✅ {mensaje}{Colores.RESET}")


def print_error(mensaje: str):
    """Imprime mensaje de error"""
    print(f"  {Colores.ROJO}❌ {mensaje}{Colores.RESET}")


def print_warning(mensaje: str):
    """Imprime mensaje de advertencia"""
    print(f"  {Colores.AMARILLO}⚠️  {mensaje}{Colores.RESET}")


def print_info(mensaje: str):
    """Imprime mensaje informativo"""
    print(f"  {Colores.AZUL}ℹ️  {mensaje}{Colores.RESET}")


def print_section(titulo: str):
    """Imprime título de sección"""
    print(f"\n{Colores.BOLD}📋 {titulo}{Colores.RESET}")
    print("─" * 50)


# ═══════════════════════════════════════════════════════════════
# VERIFICACIONES
# ═══════════════════════════════════════════════════════════════

def verificar_archivo_env() -> tuple:
    """
    Verifica que exista el archivo .env

    Returns:
        tuple: (bool, str) - (existe, mensaje)
    """
    env_path = os.path.join(os.path.dirname(__file__), '.env')

    if os.path.exists(env_path):
        return True, f"Archivo .env encontrado: {env_path}"
    else:
        return False, "Archivo .env NO encontrado. Ejecuta: cp .env.example .env"


def verificar_configuracion() -> tuple:
    """
    Verifica la configuración de base de datos

    Returns:
        tuple: (bool, dict, list) - (es_valida, config, errores)
    """
    try:
        from config import DB_CONFIG, DB_CONNECTION_STRING, validar_configuracion_critica

        # Validación crítica
        es_valida, errores = validar_configuracion_critica()

        return es_valida, DB_CONFIG, errores
    except ImportError as e:
        return False, {}, [f"Error importando configuración: {e}"]
    except Exception as e:
        return False, {}, [f"Error inesperado: {e}"]


def verificar_red(host: str, port: int, timeout: int = 5) -> tuple:
    """
    Verifica conectividad de red al servidor DB2

    Args:
        host: Nombre del host o IP
        port: Puerto de conexión
        timeout: Timeout en segundos

    Returns:
        tuple: (bool, str) - (conectado, mensaje)
    """
    try:
        # Resolver hostname
        ip_address = socket.gethostbyname(host)
        print_info(f"Host {host} resuelto a IP: {ip_address}")

        # Intentar conexión TCP
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)

        resultado = sock.connect_ex((host, port))
        sock.close()

        if resultado == 0:
            return True, f"Puerto {port} accesible en {host}"
        else:
            return False, f"Puerto {port} NO accesible en {host} (código: {resultado})"

    except socket.gaierror:
        return False, f"No se puede resolver el hostname: {host}"
    except socket.timeout:
        return False, f"Timeout al conectar a {host}:{port}"
    except Exception as e:
        return False, f"Error de red: {e}"


def verificar_driver_ibm_db() -> tuple:
    """
    Verifica que el driver ibm_db esté instalado

    Returns:
        tuple: (bool, str) - (instalado, mensaje)
    """
    try:
        import ibm_db
        version = ibm_db.__version__ if hasattr(ibm_db, '__version__') else 'desconocida'
        return True, f"Driver ibm_db instalado (versión: {version})"
    except ImportError:
        return False, "Driver ibm_db NO instalado. Ejecuta: pip install ibm_db"


def verificar_driver_pyodbc() -> tuple:
    """
    Verifica que pyodbc esté instalado

    Returns:
        tuple: (bool, str) - (instalado, mensaje)
    """
    try:
        import pyodbc
        version = pyodbc.version
        return True, f"Driver pyodbc instalado (versión: {version})"
    except ImportError:
        return False, "Driver pyodbc NO instalado. Ejecuta: pip install pyodbc"


def verificar_conexion_db2(db_config: dict, timeout: int = 10) -> tuple:
    """
    Intenta conectar a la base de datos DB2

    Args:
        db_config: Diccionario con configuración de DB
        timeout: Timeout de conexión

    Returns:
        tuple: (bool, str, object) - (conectado, mensaje, conexion)
    """
    # Intentar con ibm_db primero
    try:
        import ibm_db

        conn_string = (
            f"DATABASE={db_config.get('database', 'WM260BASD')};"
            f"HOSTNAME={db_config.get('host', 'lg00bk.chedraui.com')};"
            f"PORT={db_config.get('port', 50000)};"
            f"PROTOCOL=TCPIP;"
            f"UID={db_config.get('user', '')};"
            f"PWD={db_config.get('password', '')};"
            f"CONNECTTIMEOUT={timeout};"
        )

        print_info("Intentando conexión con ibm_db...")
        conn = ibm_db.connect(conn_string, "", "")

        if conn:
            # Obtener información del servidor
            server_info = ibm_db.server_info(conn)
            msg = f"Conectado exitosamente a {server_info.DBMS_NAME} {server_info.DBMS_VER}"
            return True, msg, conn
        else:
            return False, "Conexión retornó None", None

    except ImportError:
        print_warning("ibm_db no disponible, intentando con pyodbc...")
    except Exception as e:
        print_warning(f"Error con ibm_db: {e}")

    # Intentar con pyodbc como fallback
    try:
        import pyodbc

        conn_string = (
            f"DRIVER={db_config.get('driver', '{IBM DB2 ODBC DRIVER}')};"
            f"HOSTNAME={db_config.get('host', 'lg00bk.chedraui.com')};"
            f"PORT={db_config.get('port', 50000)};"
            f"DATABASE={db_config.get('database', 'WM260BASD')};"
            f"UID={db_config.get('user', '')};"
            f"PWD={db_config.get('password', '')};"
            f"CONNECTTIMEOUT={timeout};"
        )

        print_info("Intentando conexión con pyodbc...")
        conn = pyodbc.connect(conn_string, timeout=timeout)

        if conn:
            return True, "Conectado exitosamente con pyodbc", conn
        else:
            return False, "Conexión retornó None", None

    except ImportError:
        return False, "Ningún driver de DB2 disponible (ibm_db o pyodbc)", None
    except Exception as e:
        return False, f"Error de conexión: {e}", None


def ejecutar_query_prueba(conn, driver_type: str = 'ibm_db') -> tuple:
    """
    Ejecuta una query de prueba

    Args:
        conn: Conexión a la base de datos
        driver_type: Tipo de driver ('ibm_db' o 'pyodbc')

    Returns:
        tuple: (bool, str, dict) - (exitoso, mensaje, resultados)
    """
    query = """
    SELECT
        CURRENT SERVER AS servidor,
        CURRENT SCHEMA AS schema_actual,
        CURRENT USER AS usuario,
        CURRENT TIMESTAMP AS timestamp
    FROM SYSIBM.SYSDUMMY1
    """

    try:
        if driver_type == 'ibm_db':
            import ibm_db
            stmt = ibm_db.exec_immediate(conn, query)
            result = ibm_db.fetch_assoc(stmt)

            if result:
                return True, "Query ejecutada exitosamente", result
            else:
                return False, "Query no retornó resultados", {}
        else:
            cursor = conn.cursor()
            cursor.execute(query)
            row = cursor.fetchone()

            if row:
                result = {
                    'servidor': row[0],
                    'schema_actual': row[1],
                    'usuario': row[2],
                    'timestamp': row[3]
                }
                return True, "Query ejecutada exitosamente", result
            else:
                return False, "Query no retornó resultados", {}

    except Exception as e:
        return False, f"Error ejecutando query: {e}", {}


def cerrar_conexion(conn, driver_type: str = 'ibm_db'):
    """Cierra la conexión de forma segura"""
    try:
        if driver_type == 'ibm_db':
            import ibm_db
            ibm_db.close(conn)
        else:
            conn.close()
    except:
        pass


# ═══════════════════════════════════════════════════════════════
# FUNCIÓN PRINCIPAL
# ═══════════════════════════════════════════════════════════════

def main():
    """Función principal del verificador"""
    parser = argparse.ArgumentParser(
        description='Verificador de conexión a DB2 - SAC v1.0'
    )
    parser.add_argument(
        '--test-query', '-t',
        action='store_true',
        help='Ejecutar query de prueba después de conectar'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Mostrar información detallada'
    )
    args = parser.parse_args()

    print_banner()
    print(f"Fecha/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    errores_totales = []
    advertencias = []
    exitos = []

    # ═══════════════════════════════════════════════════════════
    # 1. Verificar archivo .env
    # ═══════════════════════════════════════════════════════════
    print_section("1. ARCHIVO DE CONFIGURACIÓN")

    existe_env, msg_env = verificar_archivo_env()
    if existe_env:
        print_ok(msg_env)
        exitos.append("Archivo .env")
    else:
        print_error(msg_env)
        errores_totales.append(msg_env)

    # ═══════════════════════════════════════════════════════════
    # 2. Verificar configuración
    # ═══════════════════════════════════════════════════════════
    print_section("2. CONFIGURACIÓN DE BASE DE DATOS")

    config_valida, db_config, errores_config = verificar_configuracion()

    if db_config:
        print_info(f"Host: {db_config.get('host', 'N/A')}")
        print_info(f"Puerto: {db_config.get('port', 'N/A')}")
        print_info(f"Database: {db_config.get('database', 'N/A')}")
        print_info(f"Usuario: {db_config.get('user', 'N/A')}")
        print_info(f"Timeout: {db_config.get('timeout', 'N/A')}s")

    if config_valida:
        print_ok("Configuración válida")
        exitos.append("Configuración DB")
    else:
        for error in errores_config:
            print_error(error)
            errores_totales.append(error)

    # ═══════════════════════════════════════════════════════════
    # 3. Verificar conectividad de red
    # ═══════════════════════════════════════════════════════════
    print_section("3. CONECTIVIDAD DE RED")

    if db_config:
        host = db_config.get('host', 'lg00bk.chedraui.com')
        port = db_config.get('port', 50000)

        red_ok, msg_red = verificar_red(host, port)
        if red_ok:
            print_ok(msg_red)
            exitos.append("Conectividad de red")
        else:
            print_error(msg_red)
            errores_totales.append(msg_red)

    # ═══════════════════════════════════════════════════════════
    # 4. Verificar drivers
    # ═══════════════════════════════════════════════════════════
    print_section("4. DRIVERS DE BASE DE DATOS")

    driver_ibm_ok, msg_ibm = verificar_driver_ibm_db()
    if driver_ibm_ok:
        print_ok(msg_ibm)
        exitos.append("Driver ibm_db")
    else:
        print_warning(msg_ibm)
        advertencias.append(msg_ibm)

    driver_pyodbc_ok, msg_pyodbc = verificar_driver_pyodbc()
    if driver_pyodbc_ok:
        print_ok(msg_pyodbc)
        exitos.append("Driver pyodbc")
    else:
        print_warning(msg_pyodbc)
        advertencias.append(msg_pyodbc)

    if not driver_ibm_ok and not driver_pyodbc_ok:
        print_error("No hay drivers de DB2 disponibles")
        errores_totales.append("No hay drivers de DB2 disponibles")

    # ═══════════════════════════════════════════════════════════
    # 5. Intentar conexión a DB2
    # ═══════════════════════════════════════════════════════════
    print_section("5. CONEXIÓN A BASE DE DATOS DB2")

    conn = None
    driver_type = 'ibm_db' if driver_ibm_ok else 'pyodbc'

    if config_valida and (driver_ibm_ok or driver_pyodbc_ok):
        conectado, msg_conn, conn = verificar_conexion_db2(db_config)

        if conectado:
            print_ok(msg_conn)
            exitos.append("Conexión DB2")

            # Ejecutar query de prueba si se solicita
            if args.test_query and conn:
                print_section("6. QUERY DE PRUEBA")

                query_ok, msg_query, resultados = ejecutar_query_prueba(conn, driver_type)

                if query_ok:
                    print_ok(msg_query)
                    print_info(f"Servidor: {resultados.get('servidor', 'N/A')}")
                    print_info(f"Schema: {resultados.get('schema_actual', 'N/A')}")
                    print_info(f"Usuario: {resultados.get('usuario', 'N/A')}")
                    print_info(f"Timestamp: {resultados.get('timestamp', 'N/A')}")
                    exitos.append("Query de prueba")
                else:
                    print_error(msg_query)
                    errores_totales.append(msg_query)

            # Cerrar conexión
            cerrar_conexion(conn, driver_type)
            print_info("Conexión cerrada correctamente")
        else:
            print_error(msg_conn)
            errores_totales.append(msg_conn)
    else:
        print_warning("No se puede intentar conexión (configuración o drivers faltantes)")
        advertencias.append("Conexión no intentada")

    # ═══════════════════════════════════════════════════════════
    # RESUMEN FINAL
    # ═══════════════════════════════════════════════════════════
    print_section("RESUMEN DE VERIFICACIÓN")

    print(f"\n  {Colores.VERDE}✅ Exitosos: {len(exitos)}{Colores.RESET}")
    if args.verbose and exitos:
        for e in exitos:
            print(f"     • {e}")

    print(f"  {Colores.AMARILLO}⚠️  Advertencias: {len(advertencias)}{Colores.RESET}")
    if args.verbose and advertencias:
        for a in advertencias:
            print(f"     • {a}")

    print(f"  {Colores.ROJO}❌ Errores: {len(errores_totales)}{Colores.RESET}")
    if errores_totales:
        for e in errores_totales:
            print(f"     • {e}")

    # Estado final
    print("\n" + "═" * 50)
    if not errores_totales:
        print(f"{Colores.VERDE}{Colores.BOLD}")
        print("  🎉 VERIFICACIÓN EXITOSA")
        print("  La conexión a DB2 está configurada correctamente")
        print(f"{Colores.RESET}")
        return 0
    else:
        print(f"{Colores.ROJO}{Colores.BOLD}")
        print("  ⚠️  VERIFICACIÓN CON ERRORES")
        print("  Revisa los errores anteriores y corrige")
        print(f"{Colores.RESET}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
