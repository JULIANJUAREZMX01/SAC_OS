#!/usr/bin/env python3
"""
===============================================================================
SCRIPT MAESTRO DE INSTALACIÓN Y CONFIGURACIÓN DEL SISTEMA SAC
Sistema de Automatización de Consultas - CEDIS Cancún 427
===============================================================================

Este script unifica todas las operaciones de instalación, configuración y
validación del sistema SAC en un solo punto de entrada.

Operaciones disponibles:
1. Instalación completa de dependencias
2. Configuración segura de credenciales
3. Validación de módulos e interconexiones
4. Verificación de conexión a base de datos
5. Configuración de conexión nativa (como DBeaver)
6. Health check del sistema
7. Inicialización de producción

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
===============================================================================
"""

import os
import sys
import subprocess
import time
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import getpass

# ===============================================================================
# CONFIGURACIÓN BASE
# ===============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent
VERSION = "1.0.0"
PYTHON_MIN_VERSION = (3, 8)


class Colors:
    """Colores ANSI para terminal"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_banner():
    """Imprime el banner del sistema"""
    banner = f"""
{Colors.CYAN}╔════════════════════════════════════════════════════════════════════╗
║                                                                    ║
║  {Colors.RED}███████╗ █████╗  ██████╗{Colors.CYAN}  Sistema de Automatización de Consultas  ║
║  {Colors.RED}██╔════╝██╔══██╗██╔════╝{Colors.CYAN}                                          ║
║  {Colors.RED}███████╗███████║██║     {Colors.CYAN}  CEDIS Cancún 427 - Tiendas Chedraui     ║
║  {Colors.RED}╚════██║██╔══██║██║     {Colors.CYAN}                                          ║
║  {Colors.RED}███████║██║  ██║╚██████╗{Colors.CYAN}  Versión {VERSION}                         ║
║  {Colors.RED}╚══════╝╚═╝  ╚═╝ ╚═════╝{Colors.CYAN}                                          ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝{Colors.ENDC}

{Colors.BOLD}MAESTRO DE INSTALACIÓN Y CONFIGURACIÓN{Colors.ENDC}
"""
    print(banner)


def log_info(mensaje: str):
    """Log de información"""
    print(f"{Colors.BLUE}ℹ️  {mensaje}{Colors.ENDC}")


def log_success(mensaje: str):
    """Log de éxito"""
    print(f"{Colors.GREEN}✅ {mensaje}{Colors.ENDC}")


def log_warning(mensaje: str):
    """Log de advertencia"""
    print(f"{Colors.WARNING}⚠️  {mensaje}{Colors.ENDC}")


def log_error(mensaje: str):
    """Log de error"""
    print(f"{Colors.RED}❌ {mensaje}{Colors.ENDC}")


def log_step(paso: int, total: int, mensaje: str):
    """Log de paso"""
    print(f"\n{Colors.CYAN}[{paso}/{total}] {mensaje}{Colors.ENDC}")
    print("-" * 60)


# ===============================================================================
# VERIFICACIONES INICIALES
# ===============================================================================

def verificar_python() -> bool:
    """Verifica la versión de Python"""
    version = sys.version_info

    if version >= PYTHON_MIN_VERSION:
        log_success(f"Python {version.major}.{version.minor}.{version.micro} detectado")
        return True
    else:
        log_error(f"Python {PYTHON_MIN_VERSION[0]}.{PYTHON_MIN_VERSION[1]}+ requerido")
        log_error(f"Versión actual: {version.major}.{version.minor}.{version.micro}")
        return False


def verificar_pip() -> bool:
    """Verifica que pip esté disponible"""
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', '--version'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            log_success(f"pip disponible: {result.stdout.split()[1]}")
            return True
    except Exception as e:
        pass

    log_error("pip no está disponible")
    return False


def verificar_directorio_base() -> bool:
    """Verifica el directorio base del proyecto"""
    archivos_requeridos = ['config.py', 'main.py', 'requirements.txt']

    for archivo in archivos_requeridos:
        if not (BASE_DIR / archivo).exists():
            log_error(f"Archivo requerido no encontrado: {archivo}")
            log_error(f"Asegúrate de ejecutar este script desde el directorio del proyecto SAC")
            return False

    log_success(f"Directorio base verificado: {BASE_DIR}")
    return True


# ===============================================================================
# INSTALACIÓN DE DEPENDENCIAS
# ===============================================================================

def instalar_dependencias(actualizar: bool = False) -> bool:
    """
    Instala las dependencias del proyecto

    Args:
        actualizar: Si True, actualiza dependencias existentes
    """
    requirements_file = BASE_DIR / 'requirements.txt'

    if not requirements_file.exists():
        log_error("requirements.txt no encontrado")
        return False

    log_info("Instalando dependencias de requirements.txt...")

    cmd = [sys.executable, '-m', 'pip', 'install', '-r', str(requirements_file)]
    if actualizar:
        cmd.append('--upgrade')

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10 minutos máximo
        )

        if result.returncode == 0:
            log_success("Dependencias instaladas correctamente")
            return True
        else:
            log_error(f"Error instalando dependencias: {result.stderr[:200]}")
            return False

    except subprocess.TimeoutExpired:
        log_error("Timeout al instalar dependencias")
        return False
    except Exception as e:
        log_error(f"Error: {str(e)}")
        return False


def instalar_driver_db2() -> bool:
    """Instala el driver ibm-db para conexión a DB2"""
    log_info("Verificando driver DB2...")

    # Intentar importar ibm_db
    try:
        import ibm_db
        log_success(f"ibm-db ya instalado")
        return True
    except ImportError:
        pass

    # Intentar instalar ibm-db
    log_info("Instalando ibm-db (driver IBM DB2)...")

    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', 'ibm-db'],
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode == 0:
            log_success("ibm-db instalado correctamente")
            return True
        else:
            log_warning("No se pudo instalar ibm-db automáticamente")
            log_info("Alternativa: pip install pyodbc (requiere driver ODBC instalado)")
            return False

    except Exception as e:
        log_warning(f"Error instalando ibm-db: {str(e)}")
        return False


# ===============================================================================
# CONFIGURACIÓN DE CREDENCIALES
# ===============================================================================

def configurar_env_seguro() -> bool:
    """Configura el archivo .env de forma segura"""
    env_file = BASE_DIR / '.env'
    env_template = BASE_DIR / 'env'

    if env_file.exists():
        respuesta = input(f"\n{Colors.WARNING}.env ya existe. ¿Sobrescribir? (s/N): {Colors.ENDC}")
        if respuesta.lower() != 's':
            log_info("Manteniendo .env existente")
            return True

    print(f"\n{Colors.CYAN}═══════════════════════════════════════════════════════════════{Colors.ENDC}")
    print(f"{Colors.BOLD}CONFIGURACIÓN SEGURA DE CREDENCIALES{Colors.ENDC}")
    print(f"{Colors.CYAN}═══════════════════════════════════════════════════════════════{Colors.ENDC}")
    print("\nLas credenciales se almacenarán en .env (archivo local, no se sube a git)")

    # Leer template
    if env_template.exists():
        with open(env_template, 'r') as f:
            template_content = f.read()
    else:
        template_content = """# Configuración SAC - CEDIS 427
# Archivo generado por maestro_instalacion.py

# === BASE DE DATOS DB2 ===
DB_HOST=WM260BASD
DB_PORT=50000
DB_DATABASE=WM260BASD
DB_USER=
DB_PASSWORD=

# === EMAIL (Office 365) ===
EMAIL_HOST=smtp.office365.com
EMAIL_PORT=587
EMAIL_USER=
EMAIL_PASSWORD=

# === CEDIS ===
CEDIS_CODE=427
CEDIS_NAME=CEDIS Cancún
CEDIS_REGION=Sureste

# === SISTEMA ===
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
"""

    # Solicitar credenciales
    print(f"\n{Colors.BOLD}1. Credenciales de Base de Datos (DB2){Colors.ENDC}")
    print("   (Dejar vacío para usar conexión nativa/trust)")

    db_user = input("   DB_USER: ").strip()
    if db_user:
        db_password = getpass.getpass("   DB_PASSWORD: ")
    else:
        db_password = ""
        log_info("Se intentará conexión nativa (sin credenciales)")

    print(f"\n{Colors.BOLD}2. Credenciales de Email (Office 365){Colors.ENDC}")
    print("   (Opcional - para notificaciones)")

    email_user = input("   EMAIL_USER: ").strip()
    if email_user:
        email_password = getpass.getpass("   EMAIL_PASSWORD: ")
    else:
        email_password = ""
        log_info("Email no configurado - notificaciones deshabilitadas")

    # Actualizar contenido
    lines = template_content.split('\n')
    new_lines = []

    for line in lines:
        if line.startswith('DB_USER='):
            new_lines.append(f'DB_USER={db_user}')
        elif line.startswith('DB_PASSWORD='):
            new_lines.append(f'DB_PASSWORD={db_password}')
        elif line.startswith('EMAIL_USER='):
            new_lines.append(f'EMAIL_USER={email_user}')
        elif line.startswith('EMAIL_PASSWORD='):
            new_lines.append(f'EMAIL_PASSWORD={email_password}')
        else:
            new_lines.append(line)

    # Escribir archivo
    try:
        with open(env_file, 'w') as f:
            f.write('\n'.join(new_lines))

        # Establecer permisos restrictivos (solo lectura para el propietario)
        os.chmod(env_file, 0o600)

        log_success(f".env creado con permisos 600 (solo propietario)")
        return True

    except Exception as e:
        log_error(f"Error creando .env: {str(e)}")
        return False


def configurar_conexion_nativa() -> bool:
    """
    Configura el sistema para conexión nativa a DB2 (como DBeaver)

    Opciones:
    1. Trust Authentication - DB2 confía en el usuario del SO
    2. DSN (Data Source Name) - Conexión configurada en el sistema
    3. Kerberos - Autenticación empresarial
    """
    print(f"\n{Colors.CYAN}═══════════════════════════════════════════════════════════════{Colors.ENDC}")
    print(f"{Colors.BOLD}CONFIGURACIÓN DE CONEXIÓN NATIVA A DB2{Colors.ENDC}")
    print(f"{Colors.CYAN}═══════════════════════════════════════════════════════════════{Colors.ENDC}")

    print("""
Similar a DBeaver, puedes configurar conexión sin especificar credenciales.

Opciones disponibles:

1. Trust Authentication
   - El servidor DB2 confía en el usuario del sistema operativo
   - Requiere configuración en el servidor DB2
   - Más seguro para ambientes corporativos

2. DSN (Data Source Name)
   - Conexión preconfigurada en ODBC
   - Las credenciales se almacenan en el sistema
   - Similar a como DBeaver guarda conexiones

3. Variables de Entorno
   - DB2INSTANCE, DB2DBDFT, etc.
   - Configuración estándar de IBM DB2

4. Kerberos
   - Autenticación empresarial (Active Directory)
   - Requiere configuración de dominio
""")

    opcion = input("¿Deseas configurar alguna opción? (1/2/3/4/N): ").strip()

    if opcion == '1':
        return _configurar_trust_auth()
    elif opcion == '2':
        return _configurar_dsn()
    elif opcion == '3':
        return _configurar_env_db2()
    elif opcion == '4':
        return _configurar_kerberos()
    else:
        log_info("Configuración nativa omitida")
        return True


def _configurar_trust_auth() -> bool:
    """Configura trust authentication"""
    print(f"\n{Colors.BOLD}Trust Authentication{Colors.ENDC}")
    print("""
Para habilitar Trust Authentication en DB2:

1. En el servidor DB2, ejecutar:
   db2 update dbm cfg using TRUST_ALLCLNTS YES
   db2 update dbm cfg using TRUST_CLNTAUTH SERVER

2. Reiniciar la instancia DB2:
   db2stop
   db2start

3. El usuario del sistema operativo debe existir en DB2

""")

    log_info("Una vez configurado en el servidor, SAC usará automáticamente Trust Auth")
    log_info("cuando no se especifiquen credenciales en .env")

    return True


def _configurar_dsn() -> bool:
    """Configura DSN para ODBC"""
    print(f"\n{Colors.BOLD}Configuración de DSN (Data Source Name){Colors.ENDC}")

    if sys.platform == 'win32':
        print("""
En Windows:
1. Abre "Administrador de orígenes de datos ODBC"
2. Ve a "DSN de sistema" o "DSN de usuario"
3. Clic en "Agregar"
4. Selecciona "IBM DB2 ODBC DRIVER"
5. Configura:
   - Nombre del origen de datos: WM260BASD
   - Descripción: Manhattan WMS DB2
   - Servidor: WM260BASD
   - Puerto: 50000
   - Base de datos: WM260BASD
6. Guarda las credenciales si deseas (marca "Guardar contraseña")
""")
    else:
        print("""
En Linux/macOS:
1. Editar /etc/odbc.ini o ~/.odbc.ini:

[WM260BASD]
Description=Manhattan WMS DB2
Driver=IBM DB2 ODBC DRIVER
Database=WM260BASD
Hostname=WM260BASD
Port=50000
Protocol=TCPIP

2. Editar /etc/odbcinst.ini para el driver:

[IBM DB2 ODBC DRIVER]
Description=IBM DB2 ODBC Driver
Driver=/opt/ibm/db2/clidriver/lib/libdb2o.so
""")

    dsn_name = input("\nNombre del DSN configurado (o Enter para omitir): ").strip()

    if dsn_name:
        # Agregar al .env
        env_file = BASE_DIR / '.env'
        if env_file.exists():
            with open(env_file, 'a') as f:
                f.write(f"\n# DSN para conexión ODBC\nDB_DSN={dsn_name}\n")
            log_success(f"DSN '{dsn_name}' agregado a .env")

    return True


def _configurar_env_db2() -> bool:
    """Configura variables de entorno DB2"""
    print(f"\n{Colors.BOLD}Variables de Entorno DB2{Colors.ENDC}")
    print("""
Variables de entorno estándar de IBM DB2:

DB2INSTANCE - Nombre de la instancia DB2
DB2DBDFT    - Base de datos predeterminada
DB2PATH     - Ruta de instalación DB2

Estas variables se pueden configurar en:
- Linux/macOS: ~/.bashrc o ~/.profile
- Windows: Variables de entorno del sistema

export DB2INSTANCE=db2inst1
export DB2DBDFT=WM260BASD
""")

    return True


def _configurar_kerberos() -> bool:
    """Información sobre configuración Kerberos"""
    print(f"\n{Colors.BOLD}Autenticación Kerberos{Colors.ENDC}")
    print("""
Para usar Kerberos con DB2:

1. Requisitos:
   - Dominio Active Directory configurado
   - Cliente Kerberos instalado
   - krb5.conf configurado

2. En el servidor DB2:
   db2 update dbm cfg using AUTHENTICATION KERBEROS
   db2 update dbm cfg using SRVCON_GSSPLUGIN_LIST IBMkrb5

3. Obtener ticket Kerberos:
   kinit usuario@DOMINIO.COM

4. SAC detectará automáticamente Kerberos cuando:
   - No hay credenciales en .env
   - Hay un ticket Kerberos válido

""")

    return True


# ===============================================================================
# VALIDACIÓN DEL SISTEMA
# ===============================================================================

def ejecutar_validacion() -> bool:
    """Ejecuta la validación completa del sistema"""
    log_info("Ejecutando validación del sistema...")

    try:
        from validador_conexiones import ValidadorConexiones

        validador = ValidadorConexiones(
            modo_verbose=True,
            intentar_conexion_nativa=True
        )

        reporte = validador.ejecutar_validacion_completa()
        validador.guardar_reporte()

        return reporte.fallidos == 0

    except ImportError:
        log_error("No se pudo importar validador_conexiones")
        log_info("Ejecutando validación básica...")
        return _validacion_basica()
    except Exception as e:
        log_error(f"Error en validación: {str(e)}")
        return False


def _validacion_basica() -> bool:
    """Validación básica cuando el validador no está disponible"""
    errores = 0

    # Verificar imports básicos
    modulos = ['config', 'monitor', 'pandas', 'openpyxl']

    for modulo in modulos:
        try:
            __import__(modulo)
            log_success(f"Módulo {modulo} disponible")
        except ImportError:
            log_error(f"Módulo {modulo} no disponible")
            errores += 1

    return errores == 0


# ===============================================================================
# HEALTH CHECK
# ===============================================================================

def ejecutar_health_check() -> bool:
    """Ejecuta health check del sistema"""
    log_info("Ejecutando health check...")

    try:
        # Verificar si existe health_check.py
        health_check_file = BASE_DIR / 'health_check.py'
        if health_check_file.exists():
            result = subprocess.run(
                [sys.executable, str(health_check_file), '--detailed'],
                capture_output=True,
                text=True,
                timeout=120
            )
            print(result.stdout)
            return result.returncode == 0
        else:
            log_warning("health_check.py no encontrado")
            return _health_check_basico()

    except Exception as e:
        log_error(f"Error en health check: {str(e)}")
        return False


def _health_check_basico() -> bool:
    """Health check básico"""
    checks_ok = 0
    total_checks = 4

    # 1. Verificar configuración
    try:
        from config import validar_configuracion
        es_valida, _ = validar_configuracion()
        if es_valida:
            log_success("Configuración válida")
            checks_ok += 1
        else:
            log_warning("Configuración con advertencias")
    except Exception as e:
        log_error(f"Error verificando configuración: {str(e)}")

    # 2. Verificar módulos
    try:
        from modules import DB2Connection
        log_success("Módulo DB2Connection disponible")
        checks_ok += 1
    except Exception as e:
        log_error(f"Error importando módulos: {str(e)}")

    # 3. Verificar directorios
    dirs = [BASE_DIR / 'output' / 'logs', BASE_DIR / 'output' / 'resultados']
    dirs_ok = all(d.exists() for d in dirs)
    if dirs_ok:
        log_success("Directorios de salida verificados")
        checks_ok += 1
    else:
        log_warning("Algunos directorios no existen")

    # 4. Verificar espacio en disco
    try:
        import shutil
        total, used, free = shutil.disk_usage(BASE_DIR)
        free_gb = free / (1024**3)
        if free_gb > 1:
            log_success(f"Espacio disponible: {free_gb:.1f} GB")
            checks_ok += 1
        else:
            log_warning(f"Espacio bajo: {free_gb:.2f} GB")
    except Exception:
        pass

    log_info(f"Health check: {checks_ok}/{total_checks} verificaciones exitosas")
    return checks_ok >= 3


# ===============================================================================
# MENÚ INTERACTIVO
# ===============================================================================

def menu_interactivo():
    """Muestra el menú interactivo de opciones"""
    while True:
        print(f"\n{Colors.CYAN}═══════════════════════════════════════════════════════════════{Colors.ENDC}")
        print(f"{Colors.BOLD}MENÚ PRINCIPAL{Colors.ENDC}")
        print(f"{Colors.CYAN}═══════════════════════════════════════════════════════════════{Colors.ENDC}")
        print("""
1. 📦 Instalación completa (dependencias + configuración)
2. 🔧 Solo instalar dependencias
3. 🔑 Configurar credenciales (.env)
4. 🔗 Configurar conexión nativa (sin credenciales)
5. ✅ Validar sistema completo
6. 💚 Health check rápido
7. 🚀 Iniciar sistema (main.py)
8. 📊 Ver configuración actual
9. ❓ Ayuda
0. 🚪 Salir
""")

        opcion = input(f"{Colors.CYAN}Selecciona una opción: {Colors.ENDC}").strip()

        if opcion == '1':
            instalacion_completa()
        elif opcion == '2':
            instalar_dependencias()
            instalar_driver_db2()
        elif opcion == '3':
            configurar_env_seguro()
        elif opcion == '4':
            configurar_conexion_nativa()
        elif opcion == '5':
            ejecutar_validacion()
        elif opcion == '6':
            ejecutar_health_check()
        elif opcion == '7':
            iniciar_sistema()
        elif opcion == '8':
            mostrar_configuracion()
        elif opcion == '9':
            mostrar_ayuda()
        elif opcion == '0':
            print(f"\n{Colors.GREEN}¡Hasta pronto!{Colors.ENDC}\n")
            break
        else:
            log_warning("Opción no válida")


def instalacion_completa():
    """Ejecuta la instalación completa"""
    total_pasos = 6

    log_step(1, total_pasos, "Verificando requisitos previos")
    if not verificar_python() or not verificar_pip():
        return False

    log_step(2, total_pasos, "Instalando dependencias")
    if not instalar_dependencias():
        log_warning("Algunas dependencias no se instalaron correctamente")

    log_step(3, total_pasos, "Instalando driver DB2")
    instalar_driver_db2()

    log_step(4, total_pasos, "Configurando credenciales")
    configurar_env_seguro()

    log_step(5, total_pasos, "Validando sistema")
    ejecutar_validacion()

    log_step(6, total_pasos, "Health check final")
    ejecutar_health_check()

    print(f"\n{Colors.GREEN}{'='*60}{Colors.ENDC}")
    log_success("INSTALACIÓN COMPLETA")
    print(f"{Colors.GREEN}{'='*60}{Colors.ENDC}")
    print(f"\nPara iniciar el sistema ejecuta: {Colors.CYAN}python main.py{Colors.ENDC}")

    return True


def iniciar_sistema():
    """Inicia el sistema principal"""
    log_info("Iniciando sistema SAC...")

    main_file = BASE_DIR / 'main.py'
    if main_file.exists():
        subprocess.run([sys.executable, str(main_file)])
    else:
        log_error("main.py no encontrado")


def mostrar_configuracion():
    """Muestra la configuración actual"""
    try:
        from config import imprimir_configuracion
        imprimir_configuracion()
    except Exception as e:
        log_error(f"Error mostrando configuración: {str(e)}")


def mostrar_ayuda():
    """Muestra información de ayuda"""
    print(f"""
{Colors.BOLD}AYUDA - MAESTRO DE INSTALACIÓN SAC{Colors.ENDC}

Este script unifica todas las operaciones de configuración del sistema SAC.

{Colors.BOLD}Uso desde línea de comandos:{Colors.ENDC}
  python maestro_instalacion.py [opción]

{Colors.BOLD}Opciones:{Colors.ENDC}
  --install        Instalación completa
  --deps           Solo instalar dependencias
  --config         Solo configurar credenciales
  --native         Configurar conexión nativa DB2
  --validate       Validar sistema
  --health         Health check
  --start          Iniciar sistema
  --help           Mostrar esta ayuda

{Colors.BOLD}Ejemplos:{Colors.ENDC}
  python maestro_instalacion.py --install
  python maestro_instalacion.py --validate
  python maestro_instalacion.py (modo interactivo)

{Colors.BOLD}Documentación:{Colors.ENDC}
  - CLAUDE.md         Guía completa del sistema
  - docs/QUICK_START.md  Inicio rápido
  - docs/README.md    Documentación detallada

{Colors.BOLD}Soporte:{Colors.ENDC}
  Julián Alexander Juárez Alvarado (ADMJAJA)
  Jefe de Sistemas - CEDIS Cancún 427
""")


# ===============================================================================
# PUNTO DE ENTRADA
# ===============================================================================

def main():
    """Función principal"""
    print_banner()

    # Verificaciones iniciales
    if not verificar_directorio_base():
        return 1

    # Procesar argumentos de línea de comandos
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()

        if arg in ['--install', '-i']:
            return 0 if instalacion_completa() else 1
        elif arg in ['--deps', '-d']:
            return 0 if instalar_dependencias() else 1
        elif arg in ['--config', '-c']:
            return 0 if configurar_env_seguro() else 1
        elif arg in ['--native', '-n']:
            return 0 if configurar_conexion_nativa() else 1
        elif arg in ['--validate', '-v']:
            return 0 if ejecutar_validacion() else 1
        elif arg in ['--health', '-h']:
            return 0 if ejecutar_health_check() else 1
        elif arg in ['--start', '-s']:
            iniciar_sistema()
            return 0
        elif arg in ['--help', '-?']:
            mostrar_ayuda()
            return 0
        else:
            log_error(f"Opción desconocida: {arg}")
            mostrar_ayuda()
            return 1

    # Modo interactivo
    menu_interactivo()
    return 0


if __name__ == "__main__":
    sys.exit(main())
