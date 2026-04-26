#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════
VERIFICAR INTEGRACIONES DE SAC 2.0
Validar Conexión a DB2 y Email Corporativo
═══════════════════════════════════════════════════════════════

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Cancún 427
═══════════════════════════════════════════════════════════════
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Tuple, Dict

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def imprimir_banner():
    """Imprime banner de inicio"""
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "  ✅ VERIFICACIÓN DE INTEGRACIONES SAC 2.0".center(78) + "║")
    print("║" + "  Base de Datos DB2 + Email Corporativo Office 365".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "═" * 78 + "╝")
    print("")


def verificar_env() -> Tuple[bool, Dict]:
    """Verifica variables de entorno"""
    print("🔍 Verificando variables de entorno...")
    print("─" * 80)

    from dotenv import load_dotenv
    load_dotenv()

    requeridas = {
        'DB_HOST': 'Servidor DB2',
        'DB_PORT': 'Puerto DB2',
        'DB_USER': 'Usuario DB2',
        'DB_PASSWORD': 'Contraseña DB2',
        'EMAIL_HOST': 'Servidor SMTP',
        'EMAIL_USER': 'Correo corporativo',
        'EMAIL_PASSWORD': 'Contraseña correo',
    }

    env_vars = {}
    faltantes = []

    for var, descripcion in requeridas.items():
        valor = os.getenv(var)
        env_vars[var] = valor

        if valor:
            # Ocultar valores sensibles
            if 'PASSWORD' in var or 'TOKEN' in var:
                valor_mostrado = '***' + valor[-4:] if len(valor) > 4 else '***'
            else:
                valor_mostrado = valor

            print(f"  ✅ {descripcion:.<30} {valor_mostrado}")
        else:
            print(f"  ❌ {descripcion:.<30} NO CONFIGURADO")
            faltantes.append(var)

    print("─" * 80)

    if faltantes:
        print(f"\n❌ FALTA CONFIGURAR: {', '.join(faltantes)}\n")
        return False, env_vars
    else:
        print(f"\n✅ Todas las variables de entorno están configuradas\n")
        return True, env_vars


def verificar_db2(env_vars: Dict) -> bool:
    """Verifica conexión a DB2"""
    print("🗄️  Verificando Base de Datos DB2...")
    print("─" * 80)

    try:
        import pyodbc
        print(f"  ✅ Módulo pyodbc importado correctamente")
    except ImportError as e:
        print(f"  ❌ Error: No se pudo importar pyodbc: {e}")
        print(f"     Solución: pip install pyodbc")
        return False

    try:
        import ibm_db
        print(f"  ✅ Módulo ibm_db importado correctamente")
        has_ibm_db = True
    except ImportError:
        print(f"  ⚠️  Módulo ibm_db no disponible (respaldo)")
        has_ibm_db = False

    # Verificar drivers ODBC
    print("\n  📋 Verificando drivers ODBC disponibles...")

    try:
        drivers = pyodbc.drivers()
        db2_drivers = [d for d in drivers if 'DB2' in d.upper()]

        if db2_drivers:
            for driver in db2_drivers:
                print(f"     ✅ Driver disponible: {driver}")
        else:
            print(f"     ⚠️  No se encontraron drivers DB2 en el sistema")
            print(f"        Los drivers ODBC de IBM DB2 deben instalarse manualmente:")
            print(f"")
            print(f"        Windows: Descargar desde https://www.ibm.com/support/")
            print(f"        Linux: sudo apt-get install libodbc1 libodbcinst1")
            print(f"               Luego instalar drivers ODBC de IBM DB2")
            print(f"")
            print(f"        NOTA: SAC puede continuar funcionando con ibm_db")
            print(f"")

    except Exception as e:
        logger.warning(f"Error listando drivers ODBC: {e}")

    # Intentar conexión
    print("\n  🔌 Intentando conexión a DB2...")

    host = env_vars.get('DB_HOST', 'WM260BASD')
    port = int(env_vars.get('DB_PORT', 50000))
    database = env_vars.get('DB_DATABASE', 'WM260BASD')
    user = env_vars.get('DB_USER', 'ADMJAJA')
    password = env_vars.get('DB_PASSWORD', '')
    schema = env_vars.get('DB_SCHEMA', 'WMWHSE1')

    # Método 1: Probar con pyodbc
    print(f"\n     Servidor: {host}:{port}")
    print(f"     Database: {database}")
    print(f"     Schema: {schema}")
    print(f"     Usuario: {user}")
    print("")

    try:
        connection_string = (
            f"DRIVER={{IBM DB2 ODBC DRIVER}};"
            f"HOSTNAME={host};"
            f"PORT={port};"
            f"DATABASE={database};"
            f"UID={user};"
            f"PWD={password};"
        )

        conn = pyodbc.connect(connection_string, autocommit=True, timeout=10)
        cursor = conn.cursor()

        # Ejecutar simple query
        cursor.execute("SELECT COUNT(*) FROM SYSCAT.TABLES")
        resultado = cursor.fetchone()

        print(f"  ✅ CONEXIÓN A DB2 EXITOSA")
        print(f"     Tablas en sistema: {resultado[0] if resultado else 'N/A'}")
        print("")

        conn.close()
        return True

    except Exception as e:
        print(f"  ⚠️  Conexión con pyodbc fallió: {e}")

        # Intentar con ibm_db
        if has_ibm_db:
            try:
                print(f"\n     Intentando con ibm_db...")
                connection_string = (
                    f"DATABASE={database};"
                    f"HOSTNAME={host};"
                    f"PORT={port};"
                    f"PROTOCOL=TCPIP;"
                    f"UID={user};"
                    f"PWD={password};"
                )

                conn = ibm_db.connect(connection_string, "", "")
                print(f"  ✅ CONEXIÓN CON IBM_DB EXITOSA")
                print("")

                ibm_db.close(conn)
                return True

            except Exception as e2:
                print(f"  ❌ Conexión con ibm_db también fallió: {e2}")
        else:
            print(f"\n  ℹ️  Para solucionar:")
            print(f"     1. Instalar drivers ODBC de IBM DB2")
            print(f"     2. Verificar credenciales en .env")
            print(f"     3. Verificar conectividad al servidor {host}:{port}")
            print("")

        return False

    print("─" * 80)


def verificar_email(env_vars: Dict) -> bool:
    """Verifica conexión a email"""
    print("\n📧 Verificando Email Corporativo (Office 365)...")
    print("─" * 80)

    try:
        import smtplib
        import email.mime.text
        print(f"  ✅ Módulos de email importados correctamente")
    except ImportError as e:
        print(f"  ❌ Error: No se pudo importar módulos de email: {e}")
        return False

    # Intenta con aiosmtplib (asincrónico)
    try:
        import aiosmtplib
        print(f"  ✅ Módulo aiosmtplib (asincrónico) disponible")
        has_aiosmtplib = True
    except ImportError:
        print(f"  ⚠️  aiosmtplib no disponible (usaremos smtplib)")
        has_aiosmtplib = False

    # Datos de conexión
    host = env_vars.get('EMAIL_HOST', 'smtp.office365.com')
    port = int(env_vars.get('EMAIL_PORT', 587))
    user = env_vars.get('EMAIL_USER', '')
    password = env_vars.get('EMAIL_PASSWORD', '')
    protocolo = env_vars.get('EMAIL_PROTOCOL', 'TLS')

    print(f"\n  🔌 Intentando conexión a {host}:{port} ({protocolo})...")
    print(f"     Usuario: {user}")
    print("")

    try:
        # Usar SMTP de Python estándar
        smtp = smtplib.SMTP(host, port, timeout=10)
        print(f"  ✅ Conexión TCP establecida")

        # Iniciar TLS
        smtp.starttls()
        print(f"  ✅ TLS iniciado")

        # Autenticarse
        smtp.login(user, password)
        print(f"  ✅ AUTENTICACIÓN CON OFFICE 365 EXITOSA")
        print("")

        # Prueba de envío
        try:
            from_email = user
            to_email = user  # Enviar a sí mismo
            subject = "🧪 Prueba SAC 2.0 - Test de Email"
            body = f"""
Hola,

Este es un email de prueba del Sistema SAC 2.0.

Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Usuario: {user}
Servidor: {host}:{port}

✅ Si recibes este email, la configuración de email es correcta.

---
Sistema SAC - CEDIS Chedraui Cancún 427
            """

            msg = email.mime.text.MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = from_email
            msg['To'] = to_email

            smtp.send_message(msg)
            print(f"  ✅ Email de prueba enviado correctamente")
            print(f"     Revisa tu buzón: {to_email}")
            print("")

        except Exception as e:
            print(f"  ⚠️  No se pudo enviar email de prueba: {e}")

        smtp.quit()
        return True

    except smtplib.SMTPAuthenticationError as e:
        print(f"  ❌ Error de autenticación: {e}")
        print(f"     Posibles causas:")
        print(f"     • Contraseña incorrecta")
        print(f"     • Usuario incorrecto")
        print(f"     • Contraseña con caracteres especiales no escapados")
        print("")
        return False

    except smtplib.SMTPException as e:
        print(f"  ❌ Error SMTP: {e}")
        print(f"     Posibles causas:")
        print(f"     • Servidor incorrecto")
        print(f"     • Puerto incorrecto")
        print(f"     • Firewall bloqueando puerto 587")
        print("")
        return False

    except Exception as e:
        print(f"  ❌ Error de conexión: {e}")
        print(f"     Verifica:")
        print(f"     • Conectividad de red")
        print(f"     • Proxy/Firewall")
        print(f"     • Credenciales en .env")
        print("")
        return False

    print("─" * 80)


def main():
    """Función principal"""
    imprimir_banner()

    # Paso 1: Verificar variables de entorno
    env_ok, env_vars = verificar_env()

    if not env_ok:
        print("❌ No se puede continuar sin las variables de entorno requeridas")
        print("   Edita el archivo .env con tus credenciales")
        return False

    # Paso 2: Verificar DB2
    db2_ok = verificar_db2(env_vars)

    # Paso 3: Verificar Email
    email_ok = verificar_email(env_vars)

    # Resumen final
    print("\n")
    print("═" * 80)
    print("RESUMEN DE VERIFICACIÓN")
    print("═" * 80)

    estado_db2 = "✅ FUNCIONAL" if db2_ok else "⚠️  REQUIERE ATENCIÓN"
    estado_email = "✅ FUNCIONAL" if email_ok else "❌ FALLO"
    estado_env = "✅ CONFIGURADO" if env_ok else "❌ INCOMPLETO"

    print(f"\nVariables de Entorno:  {estado_env}")
    print(f"Base de Datos DB2:     {estado_db2}")
    print(f"Email Corporativo:     {estado_email}")

    if env_ok and db2_ok and email_ok:
        print("\n" + "╔" + "═" * 78 + "╗")
        print("║" + " " * 78 + "║")
        print("║" + "  ✅ SAC 2.0 ESTÁ COMPLETAMENTE OPERACIONAL".center(78) + "║")
        print("║" + "  Todas las integraciones funcionan correctamente".center(78) + "║")
        print("║" + " " * 78 + "║")
        print("╚" + "═" * 78 + "╝")
        return True

    elif env_ok and email_ok:
        print("\n⚠️  SAC 2.0 PARCIALMENTE OPERACIONAL")
        print("   Email funciona correctamente")
        print("   DB2 requiere atención (instalar drivers ODBC)")
        return False

    else:
        print("\n❌ SAC 2.0 NO ESTÁ OPERACIONAL")
        print("   Requiere corrección de errores")
        return False


if __name__ == "__main__":
    exito = main()
    sys.exit(0 if exito else 1)
