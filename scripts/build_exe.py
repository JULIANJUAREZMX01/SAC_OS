#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════
SCRIPT DE COMPILACIÓN - SAC Sistema de Automatización de Consultas
Chedraui CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Script automatizado para generar el ejecutable del sistema SAC.

Uso:
    python build_exe.py                # Compilación estándar
    python build_exe.py --clean        # Limpiar y recompilar
    python build_exe.py --onedir       # Generar carpeta (no archivo único)
    python build_exe.py --debug        # Compilar con información de debug

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
═══════════════════════════════════════════════════════════════
"""

import os
import sys
import shutil
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

# ═══════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════

# Directorio base del proyecto
BASE_DIR = Path(__file__).parent.absolute()

# Nombre del ejecutable
EXE_NAME = "SAC_Chedraui_427"

# Importar versión desde configuración centralizada
from config import VERSION

# Colores para la consola
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_banner():
    """Muestra el banner del compilador"""
    banner = f"""
{Colors.CYAN}═══════════════════════════════════════════════════════════════════════════════
 ██████╗██╗  ██╗███████╗██████╗ ██████╗  █████╗ ██╗   ██╗██╗
██╔════╝██║  ██║██╔════╝██╔══██╗██╔══██╗██╔══██╗██║   ██║██║
██║     ███████║█████╗  ██║  ██║██████╔╝███████║██║   ██║██║
██║     ██╔══██║██╔══╝  ██║  ██║██╔══██╗██╔══██║██║   ██║██║
╚██████╗██║  ██║███████╗██████╔╝██║  ██║██║  ██║╚██████╔╝██║
 ╚═════╝╚═╝  ╚═╝╚══════╝╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝

   SAC - Sistema de Automatización de Consultas - Compilador
   CEDIS Cancún 427 | Versión {VERSION}
═══════════════════════════════════════════════════════════════════════════════{Colors.ENDC}
"""
    print(banner)


def print_step(step_num, total_steps, message):
    """Imprime un paso del proceso"""
    print(f"\n{Colors.BLUE}[{step_num}/{total_steps}]{Colors.ENDC} {Colors.BOLD}{message}{Colors.ENDC}")


def print_success(message):
    """Imprime mensaje de éxito"""
    print(f"{Colors.GREEN}✅ {message}{Colors.ENDC}")


def print_warning(message):
    """Imprime mensaje de advertencia"""
    print(f"{Colors.WARNING}⚠️  {message}{Colors.ENDC}")


def print_error(message):
    """Imprime mensaje de error"""
    print(f"{Colors.FAIL}❌ {message}{Colors.ENDC}")


def print_info(message):
    """Imprime mensaje informativo"""
    print(f"{Colors.CYAN}ℹ️  {message}{Colors.ENDC}")


# ═══════════════════════════════════════════════════════════════
# VERIFICACIÓN DE REQUISITOS
# ═══════════════════════════════════════════════════════════════

def verificar_python():
    """Verifica la versión de Python"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print_error(f"Python 3.8+ requerido. Versión actual: {sys.version}")
        return False
    print_success(f"Python {version.major}.{version.minor}.{version.micro} detectado")
    return True


def verificar_pyinstaller():
    """Verifica que PyInstaller esté instalado"""
    try:
        import PyInstaller
        version = PyInstaller.__version__
        print_success(f"PyInstaller {version} instalado")
        return True
    except ImportError:
        print_error("PyInstaller no está instalado")
        print_info("Instalando PyInstaller...")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyinstaller>=6.0'])
            print_success("PyInstaller instalado correctamente")
            return True
        except subprocess.CalledProcessError:
            print_error("No se pudo instalar PyInstaller")
            return False


def verificar_dependencias():
    """Verifica que las dependencias principales estén instaladas"""
    dependencias_requeridas = [
        ('pandas', 'pandas'),
        ('openpyxl', 'openpyxl'),
        ('dotenv', 'python-dotenv'),
        ('colorama', 'colorama'),
    ]

    todas_instaladas = True
    for nombre_import, nombre_pip in dependencias_requeridas:
        try:
            __import__(nombre_import)
            print_success(f"{nombre_pip} instalado")
        except ImportError:
            print_warning(f"{nombre_pip} no encontrado")
            todas_instaladas = False

    if not todas_instaladas:
        print_info("Instalando dependencias faltantes...")
        try:
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install', '-r',
                str(BASE_DIR / 'requirements.txt')
            ])
            print_success("Dependencias instaladas")
        except subprocess.CalledProcessError:
            print_warning("Algunas dependencias podrían no haberse instalado correctamente")

    return True


def verificar_archivos_necesarios():
    """Verifica que existan los archivos necesarios para compilar"""
    archivos_requeridos = [
        'main.py',
        'config.py',
        'monitor.py',
        'gestor_correos.py',
        'modules/__init__.py',
        'queries/__init__.py',
    ]

    todos_existen = True
    for archivo in archivos_requeridos:
        ruta = BASE_DIR / archivo
        if ruta.exists():
            print_success(f"{archivo} encontrado")
        else:
            print_error(f"{archivo} NO encontrado")
            todos_existen = False

    return todos_existen


# ═══════════════════════════════════════════════════════════════
# LIMPIEZA
# ═══════════════════════════════════════════════════════════════

def limpiar_build():
    """Limpia los directorios de compilación anteriores"""
    directorios = ['build', 'dist', '__pycache__']
    archivos = [f'{EXE_NAME}.spec']

    for directorio in directorios:
        ruta = BASE_DIR / directorio
        if ruta.exists():
            print_info(f"Eliminando {directorio}/...")
            shutil.rmtree(ruta)

    # Limpiar __pycache__ en subdirectorios
    for pycache in BASE_DIR.rglob('__pycache__'):
        if pycache.exists():
            shutil.rmtree(pycache)

    # Limpiar archivos .pyc
    for pyc in BASE_DIR.rglob('*.pyc'):
        pyc.unlink()

    print_success("Limpieza completada")


# ═══════════════════════════════════════════════════════════════
# COMPILACIÓN
# ═══════════════════════════════════════════════════════════════

def compilar_ejecutable(use_spec=True, onedir=False, debug=False):
    """Compila el ejecutable usando PyInstaller"""

    if use_spec and (BASE_DIR / 'SAC.spec').exists():
        # Usar archivo .spec existente
        cmd = [
            sys.executable, '-m', 'PyInstaller',
            '--clean',
            '--noconfirm',
            str(BASE_DIR / 'SAC.spec')
        ]
        print_info("Usando archivo SAC.spec para la compilación")
    else:
        # Generar comando de PyInstaller dinámicamente
        cmd = [
            sys.executable, '-m', 'PyInstaller',
            '--clean',
            '--noconfirm',
            f'--name={EXE_NAME}',
        ]

        # Modo de salida
        if onedir:
            cmd.append('--onedir')
        else:
            cmd.append('--onefile')

        # Debug
        if debug:
            cmd.append('--debug=all')

        # Consola
        cmd.append('--console')

        # Datos a incluir
        datas = [
            ('queries', 'queries'),
            ('config', 'config'),
            ('env', '.'),
        ]
        for src, dst in datas:
            src_path = BASE_DIR / src
            if src_path.exists():
                cmd.extend(['--add-data', f'{src_path}{os.pathsep}{dst}'])

        # Hidden imports
        hidden_imports = [
            'pandas', 'numpy', 'openpyxl', 'xlsxwriter',
            'colorama', 'tqdm', 'schedule', 'yaml',
            'pyodbc', 'email.mime.text', 'email.mime.multipart',
        ]
        for imp in hidden_imports:
            cmd.extend(['--hidden-import', imp])

        # Archivo principal
        cmd.append(str(BASE_DIR / 'main.py'))

    print_info(f"Ejecutando: {' '.join(cmd[:5])}...")

    try:
        # Ejecutar PyInstaller
        proceso = subprocess.run(
            cmd,
            cwd=str(BASE_DIR),
            capture_output=False,
            text=True
        )

        if proceso.returncode == 0:
            return True
        else:
            print_error("La compilación falló")
            return False

    except subprocess.CalledProcessError as e:
        print_error(f"Error durante la compilación: {e}")
        return False
    except Exception as e:
        print_error(f"Error inesperado: {e}")
        return False


# ═══════════════════════════════════════════════════════════════
# POST-COMPILACIÓN
# ═══════════════════════════════════════════════════════════════

def crear_estructura_distribucion():
    """Crea la estructura de directorios necesaria para distribución"""
    dist_dir = BASE_DIR / 'dist'

    if not dist_dir.exists():
        print_warning("Directorio dist/ no encontrado")
        return False

    # Crear directorios necesarios
    directorios = [
        dist_dir / 'output' / 'logs',
        dist_dir / 'output' / 'resultados',
    ]

    for directorio in directorios:
        directorio.mkdir(parents=True, exist_ok=True)
        print_info(f"Creado: {directorio.relative_to(dist_dir)}")

    # Copiar archivo de plantilla de entorno
    env_template = BASE_DIR / 'env'
    if env_template.exists():
        shutil.copy(env_template, dist_dir / 'env.template')
        print_info("Copiado: env.template")

    # Copiar README
    readme = BASE_DIR / 'README.md'
    if readme.exists():
        shutil.copy(readme, dist_dir / 'README.md')
        print_info("Copiado: README.md")

    return True


def generar_instrucciones():
    """Genera archivo de instrucciones para el usuario final"""
    instrucciones = f"""
═══════════════════════════════════════════════════════════════════════════════
SAC - Sistema de Automatización de Consultas
CEDIS Chedraui Cancún 427 - Versión {VERSION}
═══════════════════════════════════════════════════════════════════════════════

INSTRUCCIONES DE INSTALACIÓN Y USO
══════════════════════════════════

1. CONFIGURACIÓN INICIAL
   ─────────────────────
   a) Copiar el archivo 'env.template' y renombrarlo a '.env'
   b) Editar el archivo '.env' con las credenciales correctas:
      - DB_USER: Usuario de la base de datos DB2
      - DB_PASSWORD: Contraseña de la base de datos
      - EMAIL_USER: Correo corporativo
      - EMAIL_PASSWORD: Contraseña del correo
      - TELEGRAM_TOKEN: Token del bot de Telegram (opcional)

2. EJECUCIÓN
   ──────────
   - Windows: Doble clic en SAC_Chedraui_427.exe
   - Linux/Mac: ./SAC_Chedraui_427

   Opciones de línea de comandos:
   - SAC_Chedraui_427 --oc OC12345      # Validar una OC específica
   - SAC_Chedraui_427 --reporte-diario  # Generar reporte diario
   - SAC_Chedraui_427 --menu            # Mostrar menú interactivo

3. ESTRUCTURA DE DIRECTORIOS
   ─────────────────────────
   SAC_Chedraui_427/
   ├── SAC_Chedraui_427.exe    # Ejecutable principal
   ├── .env                     # Configuración (crear desde env.template)
   ├── env.template            # Plantilla de configuración
   ├── output/
   │   ├── logs/               # Logs del sistema
   │   └── resultados/         # Reportes Excel generados
   └── README.md               # Documentación

4. REQUISITOS DEL SISTEMA
   ──────────────────────
   - Windows 10/11 o Linux
   - Conexión a red corporativa (para acceso a DB2)
   - Driver ODBC para IBM DB2 (si no está incluido)

5. SOPORTE
   ────────
   Contactar al equipo de Sistemas CEDIS 427:
   - Julián Alexander Juárez Alvarado (ADMJAJA) - Jefe de Sistemas
   - Larry Adanael Basto Díaz - Analista de Sistemas
   - Adrian Quintana Zuñiga - Analista de Sistemas

═══════════════════════════════════════════════════════════════════════════════
Compilado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Tiendas Chedraui S.A. de C.V. - Todos los derechos reservados
═══════════════════════════════════════════════════════════════════════════════
"""

    dist_dir = BASE_DIR / 'dist'
    if dist_dir.exists():
        with open(dist_dir / 'INSTRUCCIONES.txt', 'w', encoding='utf-8') as f:
            f.write(instrucciones)
        print_info("Generado: INSTRUCCIONES.txt")
        return True
    return False


def mostrar_resumen(exito):
    """Muestra el resumen final de la compilación"""
    print(f"\n{Colors.CYAN}═══════════════════════════════════════════════════════════════{Colors.ENDC}")

    if exito:
        dist_dir = BASE_DIR / 'dist'
        exe_path = dist_dir / f'{EXE_NAME}.exe' if sys.platform == 'win32' else dist_dir / EXE_NAME

        # Calcular tamaño
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print_success(f"COMPILACIÓN EXITOSA")
            print(f"\n{Colors.GREEN}Ejecutable generado:{Colors.ENDC}")
            print(f"   📁 {exe_path}")
            print(f"   📊 Tamaño: {size_mb:.2f} MB")
        else:
            # Buscar en subdirectorio onedir
            onedir_path = dist_dir / EXE_NAME
            if onedir_path.exists():
                print_success(f"COMPILACIÓN EXITOSA (modo onedir)")
                print(f"\n{Colors.GREEN}Directorio generado:{Colors.ENDC}")
                print(f"   📁 {onedir_path}")

        print(f"\n{Colors.CYAN}Próximos pasos:{Colors.ENDC}")
        print("   1. Revisar la carpeta 'dist/'")
        print("   2. Crear archivo '.env' desde 'env.template'")
        print("   3. Configurar credenciales")
        print("   4. Ejecutar SAC_Chedraui_427")
    else:
        print_error("COMPILACIÓN FALLIDA")
        print(f"\n{Colors.WARNING}Sugerencias:{Colors.ENDC}")
        print("   1. Verificar que todas las dependencias estén instaladas")
        print("   2. Revisar los logs de PyInstaller")
        print("   3. Ejecutar: pip install -r requirements.txt")
        print("   4. Intentar: python build_exe.py --clean")

    print(f"\n{Colors.CYAN}═══════════════════════════════════════════════════════════════{Colors.ENDC}")


# ═══════════════════════════════════════════════════════════════
# FUNCIÓN PRINCIPAL
# ═══════════════════════════════════════════════════════════════

def main():
    """Función principal del compilador"""
    # Parsear argumentos
    parser = argparse.ArgumentParser(
        description='Compilador de SAC - Sistema de Automatización de Consultas'
    )
    parser.add_argument('--clean', action='store_true',
                        help='Limpiar compilaciones anteriores antes de compilar')
    parser.add_argument('--onedir', action='store_true',
                        help='Generar carpeta en lugar de archivo único')
    parser.add_argument('--debug', action='store_true',
                        help='Compilar con información de debug')
    parser.add_argument('--no-spec', action='store_true',
                        help='No usar archivo .spec, generar comando dinámicamente')
    parser.add_argument('--clean-only', action='store_true',
                        help='Solo limpiar, no compilar')

    args = parser.parse_args()

    # Mostrar banner
    print_banner()

    total_steps = 7 if not args.clean_only else 1
    current_step = 0

    # Paso 1: Limpiar (si se solicita)
    if args.clean or args.clean_only:
        current_step += 1
        print_step(current_step, total_steps, "Limpiando compilaciones anteriores...")
        limpiar_build()

        if args.clean_only:
            print_success("Limpieza completada")
            return 0

    # Paso 2: Verificar Python
    current_step += 1
    print_step(current_step, total_steps, "Verificando versión de Python...")
    if not verificar_python():
        return 1

    # Paso 3: Verificar PyInstaller
    current_step += 1
    print_step(current_step, total_steps, "Verificando PyInstaller...")
    if not verificar_pyinstaller():
        return 1

    # Paso 4: Verificar dependencias
    current_step += 1
    print_step(current_step, total_steps, "Verificando dependencias...")
    verificar_dependencias()

    # Paso 5: Verificar archivos
    current_step += 1
    print_step(current_step, total_steps, "Verificando archivos del proyecto...")
    if not verificar_archivos_necesarios():
        print_error("Faltan archivos necesarios para la compilación")
        return 1

    # Paso 6: Compilar
    current_step += 1
    print_step(current_step, total_steps, "Compilando ejecutable...")
    print_info("Este proceso puede tomar varios minutos...")

    exito = compilar_ejecutable(
        use_spec=not args.no_spec,
        onedir=args.onedir,
        debug=args.debug
    )

    if exito:
        # Paso 7: Post-compilación
        current_step += 1
        print_step(current_step, total_steps, "Configurando distribución...")
        crear_estructura_distribucion()
        generar_instrucciones()

    # Mostrar resumen
    mostrar_resumen(exito)

    return 0 if exito else 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Compilación cancelada por el usuario{Colors.ENDC}")
        sys.exit(130)
    except Exception as e:
        print(f"\n{Colors.FAIL}Error inesperado: {e}{Colors.ENDC}")
        sys.exit(1)
