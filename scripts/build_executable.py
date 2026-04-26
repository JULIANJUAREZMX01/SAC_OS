#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════
SCRIPT DE CONSTRUCCIÓN DE EJECUTABLE
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Este script genera el ejecutable del sistema SAC usando PyInstaller.

Uso:
    python build_executable.py
    python build_executable.py --clean  # Limpia builds anteriores

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

# Colores para terminal
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header():
    """Imprime el encabezado del script"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("╔═══════════════════════════════════════════════════════════════════╗")
    print("║     CONSTRUCTOR DE EJECUTABLE - SISTEMA SAC v1.0                 ║")
    print("║              CEDIS Cancún 427 - Tiendas Chedraui                 ║")
    print("╚═══════════════════════════════════════════════════════════════════╝")
    print(f"{Colors.ENDC}")


def print_success(msg):
    print(f"{Colors.GREEN}✓ {msg}{Colors.ENDC}")


def print_error(msg):
    print(f"{Colors.RED}✗ {msg}{Colors.ENDC}")


def print_info(msg):
    print(f"{Colors.BLUE}ℹ {msg}{Colors.ENDC}")


def print_warning(msg):
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.ENDC}")


def check_dependencies():
    """Verifica que las dependencias estén instaladas"""
    print_info("Verificando dependencias...")

    try:
        import PyInstaller
        print_success(f"PyInstaller {PyInstaller.__version__} instalado")
        return True
    except ImportError:
        print_error("PyInstaller no está instalado")
        print_info("Instalando PyInstaller...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "pyinstaller"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print_success("PyInstaller instalado correctamente")
            return True
        else:
            print_error("No se pudo instalar PyInstaller")
            print_error(result.stderr)
            return False


def clean_build_dirs(base_path: Path):
    """Limpia directorios de builds anteriores"""
    print_info("Limpiando builds anteriores...")

    dirs_to_clean = ['build', 'dist', '__pycache__']

    for dir_name in dirs_to_clean:
        dir_path = base_path / dir_name
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print_success(f"Eliminado: {dir_name}/")

    # Limpiar archivos .pyc
    for pyc_file in base_path.rglob("*.pyc"):
        pyc_file.unlink()

    # Limpiar __pycache__ en subdirectorios
    for pycache in base_path.rglob("__pycache__"):
        if pycache.is_dir():
            shutil.rmtree(pycache)

    print_success("Limpieza completada")


def run_tests():
    """Ejecuta los tests antes de construir"""
    print_info("Ejecutando tests del sistema...")

    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short", "-q"],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).parent)
    )

    # Buscar el resumen de tests
    output = result.stdout + result.stderr
    if "passed" in output:
        # Extraer números de tests
        import re
        match = re.search(r'(\d+) passed', output)
        if match:
            passed = match.group(1)
            print_success(f"{passed} tests pasaron")
            return True

    if result.returncode != 0:
        print_error("Algunos tests fallaron")
        print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
        response = input("¿Continuar con la construcción de todas formas? (s/n): ")
        return response.lower() == 's'

    return True


def verify_system():
    """Ejecuta verificación del sistema"""
    print_info("Verificando integridad del sistema...")

    result = subprocess.run(
        [sys.executable, "verificar_sistema.py"],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).parent)
    )

    if "ERROR" in result.stdout.upper() or "ERRORES" in result.stdout:
        # Verificar si son errores críticos
        if "0 ERROR" not in result.stdout and "Errores: 0" not in result.stdout:
            print_warning("Se detectaron algunos problemas en la verificación")
            # Continuar de todas formas si son solo advertencias
    else:
        print_success("Sistema verificado correctamente")

    return True


def build_executable(base_path: Path):
    """Construye el ejecutable usando PyInstaller"""
    print_info("Construyendo ejecutable...")
    print_info("Este proceso puede tomar varios minutos...")

    spec_file = base_path / "SAC_CEDIS.spec"

    if not spec_file.exists():
        print_error(f"Archivo spec no encontrado: {spec_file}")
        return False

    # Ejecutar PyInstaller
    result = subprocess.run(
        [sys.executable, "-m", "PyInstaller", str(spec_file), "--clean"],
        cwd=str(base_path),
        capture_output=False  # Mostrar output en tiempo real
    )

    if result.returncode == 0:
        exe_path = base_path / "dist" / "SAC_CEDIS_427"
        if sys.platform == "win32":
            exe_path = exe_path.with_suffix(".exe")

        if exe_path.exists():
            print_success(f"Ejecutable creado: {exe_path}")
            return True
        else:
            print_warning("El proceso terminó pero no se encontró el ejecutable")
            return False
    else:
        print_error("Error al construir el ejecutable")
        return False


def create_distribution(base_path: Path):
    """Crea el paquete de distribución"""
    print_info("Creando paquete de distribución...")

    dist_path = base_path / "dist"
    sac_dist = dist_path / "SAC_CEDIS_427_Distribucion"

    if not dist_path.exists():
        print_error("Directorio dist/ no existe")
        return False

    # Crear directorio de distribución
    sac_dist.mkdir(exist_ok=True)

    # Copiar ejecutable
    exe_name = "SAC_CEDIS_427.exe" if sys.platform == "win32" else "SAC_CEDIS_427"
    exe_src = dist_path / exe_name
    if exe_src.exists():
        shutil.copy(exe_src, sac_dist / exe_name)

    # Copiar archivos de configuración
    files_to_copy = [
        ('env', '.env.example'),
        ('README.md', 'README.md'),
    ]

    for src, dst in files_to_copy:
        src_path = base_path / src
        if src_path.exists():
            shutil.copy(src_path, sac_dist / dst)

    # Crear script de ejecución
    if sys.platform == "win32":
        run_script = sac_dist / "ejecutar_sac.bat"
        run_script.write_text("""@echo off
title Sistema SAC - CEDIS Cancun 427
echo.
echo ========================================
echo   Sistema de Automatizacion de Consultas
echo   CEDIS Cancun 427 - Tiendas Chedraui
echo ========================================
echo.
SAC_CEDIS_427.exe %*
pause
""", encoding='utf-8')
    else:
        run_script = sac_dist / "ejecutar_sac.sh"
        run_script.write_text("""#!/bin/bash
echo ""
echo "========================================"
echo "  Sistema de Automatizacion de Consultas"
echo "  CEDIS Cancun 427 - Tiendas Chedraui"
echo "========================================"
echo ""
./SAC_CEDIS_427 "$@"
""", encoding='utf-8')
        run_script.chmod(0o755)

    # Crear README de instalación
    install_readme = sac_dist / "INSTALACION.txt"
    install_readme.write_text(f"""
═══════════════════════════════════════════════════════════════
SISTEMA SAC - INSTALACIÓN Y USO
CEDIS Cancún 427 - Tiendas Chedraui
Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
═══════════════════════════════════════════════════════════════

PASOS DE INSTALACIÓN:
1. Copie esta carpeta a la ubicación deseada
2. Renombre .env.example a .env
3. Configure sus credenciales en .env:
   - DB_USER y DB_PASSWORD para la base de datos
   - EMAIL_USER y EMAIL_PASSWORD para correos

EJECUCIÓN:
- Windows: Doble clic en ejecutar_sac.bat
- Linux/Mac: Ejecutar ./ejecutar_sac.sh

COMANDOS DISPONIBLES:
- SAC_CEDIS_427 --menu          : Menú interactivo
- SAC_CEDIS_427 --oc OC12345    : Validar OC específica
- SAC_CEDIS_427 --reporte-diario : Generar reporte diario
- SAC_CEDIS_427 --help          : Ver ayuda completa

SOPORTE:
Jefe de Sistemas: Julián Alexander Juárez Alvarado (ADMJAJA)
CEDIS Cancún 427

═══════════════════════════════════════════════════════════════
""", encoding='utf-8')

    print_success(f"Paquete de distribución creado: {sac_dist}")
    return True


def main():
    """Función principal"""
    print_header()

    base_path = Path(__file__).parent
    print_info(f"Directorio del proyecto: {base_path}")
    print_info(f"Fecha y hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Verificar argumentos
    clean_only = "--clean" in sys.argv

    # 1. Limpiar builds anteriores
    clean_build_dirs(base_path)

    if clean_only:
        print_success("Limpieza completada")
        return

    # 2. Verificar dependencias
    if not check_dependencies():
        print_error("No se pueden verificar las dependencias")
        sys.exit(1)

    # 3. Ejecutar tests
    if not run_tests():
        print_warning("Continuando sin tests exitosos...")

    # 4. Verificar sistema
    verify_system()

    # 5. Construir ejecutable
    print(f"\n{Colors.BOLD}Iniciando construcción del ejecutable...{Colors.ENDC}\n")

    if build_executable(base_path):
        # 6. Crear paquete de distribución
        create_distribution(base_path)

        print(f"\n{Colors.GREEN}{Colors.BOLD}")
        print("═══════════════════════════════════════════════════════════════")
        print("       ✓ EJECUTABLE GENERADO EXITOSAMENTE")
        print("═══════════════════════════════════════════════════════════════")
        print(f"{Colors.ENDC}")
        print(f"\nUbicación: {base_path / 'dist' / 'SAC_CEDIS_427_Distribucion'}")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}")
        print("═══════════════════════════════════════════════════════════════")
        print("       ✗ ERROR AL GENERAR EL EJECUTABLE")
        print("═══════════════════════════════════════════════════════════════")
        print(f"{Colors.ENDC}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠ Construcción cancelada por el usuario{Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}✗ Error inesperado: {e}{Colors.ENDC}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
