#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════
SCRIPT DE CREACIÓN DE DISTRIBUCIÓN PORTABLE
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Crea un paquete portable del sistema SAC listo para distribución.

Uso:
    python crear_distribucion.py

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════
"""

import os
import sys
import shutil
import zipfile
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
    """Imprime el encabezado"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("╔═══════════════════════════════════════════════════════════════════╗")
    print("║   CREADOR DE DISTRIBUCIÓN PORTABLE - SISTEMA SAC v1.0            ║")
    print("║              CEDIS Cancún 427 - Tiendas Chedraui                 ║")
    print("╚═══════════════════════════════════════════════════════════════════╝")
    print(f"{Colors.ENDC}")


def print_success(msg):
    print(f"{Colors.GREEN}✓ {msg}{Colors.ENDC}")


def print_error(msg):
    print(f"{Colors.RED}✗ {msg}{Colors.ENDC}")


def print_info(msg):
    print(f"{Colors.BLUE}ℹ {msg}{Colors.ENDC}")


def crear_distribucion():
    """Crea el paquete de distribución"""

    base_dir = Path(__file__).parent
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    dist_name = f"SAC_CEDIS_427_v1.0_{timestamp}"
    dist_dir = base_dir / "dist" / dist_name

    # Limpiar distribución anterior
    if dist_dir.exists():
        shutil.rmtree(dist_dir)

    dist_dir.mkdir(parents=True, exist_ok=True)

    print_info(f"Creando distribución en: {dist_dir}")

    # Archivos y directorios a incluir
    items_to_copy = [
        # Archivos principales
        ('main.py', 'main.py'),
        ('sac_launcher.py', 'sac_launcher.py'),
        ('monitor.py', 'monitor.py'),
        ('gestor_correos.py', 'gestor_correos.py'),
        ('maestro.py', 'maestro.py'),
        ('dashboard.py', 'dashboard.py'),
        ('notificaciones_telegram.py', 'notificaciones_telegram.py'),
        ('notificaciones_whatsapp.py', 'notificaciones_whatsapp.py'),
        ('examples.py', 'examples.py'),
        ('verificar_sistema.py', 'verificar_sistema.py'),

        # Configuración
        ('config.py', 'config.py'),
        ('env', '.env.example'),
        ('requirements.txt', 'requirements.txt'),

        # Documentación
        ('README.md', 'README.md'),
        ('CLAUDE.md', 'CLAUDE.md'),

        # Directorios completos
        ('config', 'config'),
        ('modules', 'modules'),
        ('queries', 'queries'),
        ('docs', 'docs'),
    ]

    # Copiar archivos
    for src, dst in items_to_copy:
        src_path = base_dir / src
        dst_path = dist_dir / dst

        if src_path.is_file():
            shutil.copy(src_path, dst_path)
            print_success(f"Copiado: {src}")
        elif src_path.is_dir():
            shutil.copytree(
                src_path, dst_path,
                ignore=shutil.ignore_patterns(
                    '__pycache__', '*.pyc', '.git', '.pytest_cache'
                )
            )
            print_success(f"Copiado directorio: {src}/")

    # Crear directorio output
    (dist_dir / "output" / "logs").mkdir(parents=True, exist_ok=True)
    (dist_dir / "output" / "resultados").mkdir(parents=True, exist_ok=True)
    print_success("Creado: output/logs/ y output/resultados/")

    # Crear scripts de ejecución
    crear_scripts_ejecucion(dist_dir)

    # Crear README de instalación
    crear_readme_instalacion(dist_dir)

    # Crear archivo ZIP
    zip_path = base_dir / "dist" / f"{dist_name}.zip"
    print_info(f"Creando archivo ZIP: {zip_path.name}")

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in dist_dir.rglob('*'):
            if file_path.is_file():
                arcname = file_path.relative_to(dist_dir.parent)
                zipf.write(file_path, arcname)

    print_success(f"ZIP creado: {zip_path}")

    # Mostrar tamaños
    dist_size = sum(f.stat().st_size for f in dist_dir.rglob('*') if f.is_file())
    zip_size = zip_path.stat().st_size

    print(f"\n{Colors.BOLD}📊 RESUMEN:{Colors.ENDC}")
    print(f"   Tamaño carpeta: {dist_size / 1024 / 1024:.2f} MB")
    print(f"   Tamaño ZIP: {zip_size / 1024 / 1024:.2f} MB")

    return dist_dir, zip_path


def crear_scripts_ejecucion(dist_dir: Path):
    """Crea los scripts de ejecución para diferentes SO"""

    # Script para Windows (BAT)
    bat_content = """@echo off
chcp 65001 >nul
title Sistema SAC - CEDIS Cancun 427

echo.
echo ╔═══════════════════════════════════════════════════════════════════╗
echo ║     SISTEMA SAC - AUTOMATIZACION DE CONSULTAS                    ║
echo ║     CEDIS Cancun 427 - Tiendas Chedraui                          ║
echo ╚═══════════════════════════════════════════════════════════════════╝
echo.

REM Verificar que Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no está instalado o no está en el PATH
    echo Por favor instale Python 3.8 o superior desde https://www.python.org
    pause
    exit /b 1
)

REM Instalar dependencias si es necesario
if not exist "venv" (
    echo Instalando dependencias por primera vez...
    pip install -r requirements.txt
)

REM Ejecutar el sistema
python sac_launcher.py %*

pause
"""
    (dist_dir / "iniciar_sac.bat").write_text(bat_content, encoding='utf-8')
    print_success("Creado: iniciar_sac.bat")

    # Script para Linux/Mac (SH)
    sh_content = """#!/bin/bash
#═══════════════════════════════════════════════════════════════════
# SISTEMA SAC - CEDIS Cancún 427
# Script de inicio para Linux/macOS
#═══════════════════════════════════════════════════════════════════

echo ""
echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║     SISTEMA SAC - AUTOMATIZACIÓN DE CONSULTAS                    ║"
echo "║     CEDIS Cancún 427 - Tiendas Chedraui                          ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo ""

# Cambiar al directorio del script
cd "$(dirname "$0")"

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 no está instalado"
    echo "Por favor instale Python 3.8 o superior"
    exit 1
fi

# Instalar dependencias si es necesario
if [ ! -d "venv" ]; then
    echo "Instalando dependencias..."
    pip3 install -r requirements.txt
fi

# Ejecutar el sistema
python3 sac_launcher.py "$@"
"""
    sh_path = dist_dir / "iniciar_sac.sh"
    sh_path.write_text(sh_content, encoding='utf-8')
    sh_path.chmod(0o755)
    print_success("Creado: iniciar_sac.sh")

    # Script de instalación de dependencias
    install_deps = """#!/bin/bash
# Instalador de dependencias para Sistema SAC

echo "Instalando dependencias del Sistema SAC..."
pip3 install -r requirements.txt

echo ""
echo "✓ Dependencias instaladas correctamente"
echo ""
echo "Para iniciar el sistema ejecute:"
echo "  ./iniciar_sac.sh"
"""
    install_path = dist_dir / "instalar_dependencias.sh"
    install_path.write_text(install_deps, encoding='utf-8')
    install_path.chmod(0o755)
    print_success("Creado: instalar_dependencias.sh")


def crear_readme_instalacion(dist_dir: Path):
    """Crea el README de instalación"""

    readme = f"""
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║     SISTEMA SAC - AUTOMATIZACIÓN DE CONSULTAS                            ║
║     CEDIS Cancún 427 - Tiendas Chedraui                                  ║
║     Versión 1.0.0                                                        ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝

Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Desarrollador: Julián Alexander Juárez Alvarado (ADMJAJA)
               Jefe de Sistemas - CEDIS Cancún 427

════════════════════════════════════════════════════════════════════════════
                         GUÍA DE INSTALACIÓN
════════════════════════════════════════════════════════════════════════════

REQUISITOS:
-----------
• Python 3.8 o superior
• Conexión a red corporativa (para acceso a DB2)
• Credenciales de base de datos y correo

PASO 1 - CONFIGURACIÓN:
-----------------------
1. Renombre el archivo '.env.example' a '.env'
2. Edite el archivo '.env' con sus credenciales:

   # Base de datos DB2
   DB_USER=su_usuario
   DB_PASSWORD=su_contraseña

   # Correo electrónico (Office 365)
   EMAIL_USER=su_email@chedraui.com.mx
   EMAIL_PASSWORD=su_contraseña

   # Telegram (opcional)
   TELEGRAM_BOT_TOKEN=su_token
   TELEGRAM_CHAT_IDS=chat_id1,chat_id2

PASO 2 - INSTALACIÓN DE DEPENDENCIAS:
------------------------------------
Windows:
   pip install -r requirements.txt

Linux/macOS:
   ./instalar_dependencias.sh
   o
   pip3 install -r requirements.txt

PASO 3 - EJECUTAR EL SISTEMA:
----------------------------
Windows:
   Doble clic en 'iniciar_sac.bat'
   o
   python sac_launcher.py

Linux/macOS:
   ./iniciar_sac.sh
   o
   python3 sac_launcher.py

════════════════════════════════════════════════════════════════════════════
                         COMANDOS DISPONIBLES
════════════════════════════════════════════════════════════════════════════

MENÚ INTERACTIVO:
   python sac_launcher.py --menu

VALIDACIÓN DE OC:
   python sac_launcher.py --oc OC12345

REPORTE DIARIO:
   python sac_launcher.py --reporte-diario

VERIFICAR SISTEMA:
   python sac_launcher.py --validar-sistema

EJECUTAR TESTS:
   python sac_launcher.py --tests

VER CONFIGURACIÓN:
   python sac_launcher.py --config

AYUDA:
   python sac_launcher.py --help

════════════════════════════════════════════════════════════════════════════
                              ESTRUCTURA
════════════════════════════════════════════════════════════════════════════

SAC_CEDIS_427/
├── sac_launcher.py          # Punto de entrada principal
├── main.py                  # Sistema principal
├── monitor.py               # Monitor en tiempo real
├── gestor_correos.py        # Gestión de correos
├── maestro.py               # Script maestro orquestador
├── dashboard.py             # Dashboard interactivo
├── .env.example             # Plantilla de configuración
├── requirements.txt         # Dependencias Python
├── config/                  # Configuración del sistema
├── modules/                 # Módulos del sistema
│   ├── db_connection.py     # Conexión a DB2
│   ├── reportes_excel.py    # Generación de reportes
│   ├── email/               # Sistema de correos
│   └── repositories/        # Acceso a datos
├── queries/                 # Consultas SQL
├── docs/                    # Documentación
└── output/                  # Reportes generados
    ├── logs/                # Logs del sistema
    └── resultados/          # Archivos Excel

════════════════════════════════════════════════════════════════════════════
                               SOPORTE
════════════════════════════════════════════════════════════════════════════

Para soporte técnico contacte a:

   Jefe de Sistemas: Julián Alexander Juárez Alvarado (ADMJAJA)
   CEDIS Cancún 427 - Tiendas Chedraui

   "Las máquinas y los sistemas al servicio de los analistas"

════════════════════════════════════════════════════════════════════════════
"""

    (dist_dir / "INSTALACION.txt").write_text(readme, encoding='utf-8')
    print_success("Creado: INSTALACION.txt")


def main():
    """Función principal"""
    print_header()

    print_info(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Ejecutar tests primero
    print_info("Ejecutando verificación del sistema...")
    import subprocess
    result = subprocess.run(
        [sys.executable, "verificar_sistema.py"],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).parent)
    )

    if "ERROR" in result.stdout.upper() and "0 ERROR" not in result.stdout:
        print(f"{Colors.YELLOW}⚠ Hay algunos problemas en la verificación{Colors.ENDC}")

    # Crear distribución
    print(f"\n{Colors.BOLD}📦 Creando paquete de distribución...{Colors.ENDC}\n")

    try:
        dist_dir, zip_path = crear_distribucion()

        print(f"\n{Colors.GREEN}{Colors.BOLD}")
        print("═══════════════════════════════════════════════════════════════")
        print("       ✓ DISTRIBUCIÓN CREADA EXITOSAMENTE")
        print("═══════════════════════════════════════════════════════════════")
        print(f"{Colors.ENDC}")
        print(f"\n📁 Carpeta: {dist_dir}")
        print(f"📦 ZIP: {zip_path}")
        print(f"\n💡 Para instalar en otro equipo:")
        print(f"   1. Copie el archivo ZIP al equipo destino")
        print(f"   2. Extraiga el contenido")
        print(f"   3. Siga las instrucciones en INSTALACION.txt")

    except Exception as e:
        print(f"\n{Colors.RED}✗ Error al crear distribución: {e}{Colors.ENDC}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠ Cancelado por el usuario{Colors.ENDC}")
        sys.exit(1)
