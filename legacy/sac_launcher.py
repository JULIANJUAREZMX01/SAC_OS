#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
===============================================================================
LANZADOR DEL SISTEMA SAC v2.0
Sistema de Automatizacion de Consultas - CEDIS Cancun 427
===============================================================================

Script ejecutable principal que inicia el Sistema SAC.
Integra el modulo de setup con animaciones de carga durante el inicio.

Este archivo:
- Ejecuta la configuracion inicial con animaciones
- Verifica e instala dependencias automaticamente
- Lanza el sistema principal

Uso:
    python sac_launcher.py                    # Inicia con setup animado
    python sac_launcher.py --oc OC12345       # Validar OC especifica
    python sac_launcher.py --menu             # Menu interactivo
    python sac_launcher.py --validar-sistema  # Verificar sistema
    python sac_launcher.py --skip-setup       # Omitir animaciones
    python sac_launcher.py --forzar-setup     # Forzar re-configuracion

Desarrollado por: Julian Alexander Juarez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Cancun 427
===============================================================================
"""

import sys
import os
from pathlib import Path

# Asegurar que el directorio actual esta en el path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.chdir(BASE_DIR)


# ===============================================================================
# COLORES PARA TERMINAL (Sin dependencias)
# ===============================================================================

class Colores:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'


def color_texto(texto, color):
    return f"{color}{texto}{Colores.RESET}"


# ===============================================================================
# FUNCIONES DE SOPORTE
# ===============================================================================

def print_banner_simple():
    """Imprime un banner simple (sin animaciones)"""
    print(f"""
{Colores.RED}
    ╔═══════════════════════════════════════════════════════════════════╗
    ║                                                                   ║
    ║     🏢 SISTEMA SAC - AUTOMATIZACION DE CONSULTAS                 ║
    ║     📍 CEDIS Cancun 427 - Tiendas Chedraui                       ║
    ║     📦 Manhattan WMS - Region Sureste                            ║
    ║                                                                   ║
    ║     Version: 2.0.0                                               ║
    ║     Desarrollador: Julian Alexander Juarez Alvarado (ADMJAJA)    ║
    ║                                                                   ║
    ╚═══════════════════════════════════════════════════════════════════╝
{Colores.RESET}
    """)


def ejecutar_setup_inicial(forzar=False, silencioso=False):
    """
    Ejecuta el proceso de setup inicial con animaciones.

    Este es el PRIMER paso al iniciar el sistema.
    Verifica e instala dependencias, crea directorios, etc.
    """
    try:
        from modules.modulo_setup import ejecutar_setup_inicial as run_setup
        from modules.modulo_setup import verificar_sistema_listo

        # Si ya esta listo y no forzamos, mostrar mensaje rapido
        if verificar_sistema_listo() and not forzar:
            if not silencioso:
                print(f"\n  {Colores.GREEN}✓ Sistema SAC configurado y listo{Colores.RESET}\n")
            return True

        # Ejecutar setup completo con animaciones
        resultado = run_setup(
            verbose=not silencioso,
            mostrar_splash=not silencioso,
            forzar=forzar
        )

        return resultado.exito

    except ImportError:
        # El modulo de setup aun no esta disponible, usar fallback
        return verificar_dependencias_basico()


def verificar_dependencias_basico():
    """Verificacion basica de dependencias (fallback sin animaciones)"""
    print(f"\n  {Colores.CYAN}Verificando dependencias...{Colores.RESET}")

    dependencias = [
        ('pandas', 'pandas'),
        ('openpyxl', 'openpyxl'),
        ('dotenv', 'python-dotenv'),
    ]

    faltantes = []
    for modulo, pip_name in dependencias:
        try:
            __import__(modulo)
        except ImportError:
            faltantes.append(pip_name)

    if faltantes:
        print(f"  {Colores.YELLOW}Dependencias faltantes detectadas:{Colores.RESET}")
        for dep in faltantes:
            print(f"     - {dep}")
        print(f"\n  {Colores.CYAN}Instalando automaticamente...{Colores.RESET}")

        import subprocess
        for dep in faltantes:
            try:
                subprocess.run(
                    [sys.executable, '-m', 'pip', 'install', dep, '-q'],
                    capture_output=True,
                    timeout=60
                )
                print(f"     {Colores.GREEN}✓{Colores.RESET} {dep}")
            except:
                print(f"     {Colores.RED}✗{Colores.RESET} {dep}")
                return False

    print(f"  {Colores.GREEN}✓ Dependencias verificadas{Colores.RESET}\n")
    return True


def run_tests():
    """Ejecuta los tests del sistema"""
    print("\n🧪 Ejecutando tests del sistema...\n")
    import subprocess
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
        cwd=str(BASE_DIR)
    )
    return result.returncode == 0


def run_verification():
    """Ejecuta la verificación del sistema"""
    print("\n🔍 Verificando integridad del sistema...\n")
    import subprocess
    result = subprocess.run(
        [sys.executable, "verificar_sistema.py"],
        cwd=str(BASE_DIR)
    )
    return result.returncode == 0


def show_help():
    """Muestra la ayuda del sistema"""
    print(f"""
{Colores.BOLD}📘 AYUDA DEL SISTEMA SAC v2.0{Colores.RESET}
════════════════════════════════════════════════════════════════

{Colores.CYAN}INICIO Y CONFIGURACION:{Colores.RESET}
─────────────────────────────────────────────────────────────────
  python sac_launcher.py                    # Inicia con setup animado
  python sac_launcher.py --skip-setup       # Omitir animaciones de inicio
  python sac_launcher.py --forzar-setup     # Forzar re-configuracion
  python sac_launcher.py --quiet            # Modo silencioso

{Colores.CYAN}MENU INTERACTIVO:{Colores.RESET}
─────────────────────────────────────────────────────────────────
  python sac_launcher.py --menu             # Menu principal

{Colores.CYAN}VALIDACION DE OC:{Colores.RESET}
─────────────────────────────────────────────────────────────────
  python sac_launcher.py --oc OC12345       # Validar OC especifica
  python sac_launcher.py --oc OC12345 --excel  # Con reporte Excel

{Colores.CYAN}REPORTES:{Colores.RESET}
─────────────────────────────────────────────────────────────────
  python sac_launcher.py --reporte-diario   # Generar reporte diario
  python sac_launcher.py --dashboard        # Abrir dashboard

{Colores.CYAN}MONITOREO:{Colores.RESET}
─────────────────────────────────────────────────────────────────
  python sac_launcher.py --monitor          # Monitor en tiempo real

{Colores.CYAN}UTILIDADES:{Colores.RESET}
─────────────────────────────────────────────────────────────────
  python sac_launcher.py --validar-sistema  # Verificar integridad
  python sac_launcher.py --tests            # Ejecutar tests
  python sac_launcher.py --config           # Ver configuracion
  python sac_launcher.py --help             # Esta ayuda

{Colores.CYAN}CONFIGURACION INICIAL:{Colores.RESET}
─────────────────────────────────────────────────────────────────
  La primera vez que ejecutes el sistema, se mostrara una
  animacion de carga mientras se:
  - Verifican dependencias
  - Crean directorios necesarios
  - Verifica configuracion .env

  Para configurar credenciales:
    python instalar_sac.py

════════════════════════════════════════════════════════════════
    """)


def main():
    """
    Funcion principal del lanzador.

    Flujo:
    1. Ejecutar setup inicial con animaciones (configuracion, dependencias)
    2. Procesar argumentos especiales
    3. Lanzar sistema principal
    """
    # Procesar argumentos
    args = sys.argv[1:]

    # Detectar modos especiales
    skip_setup = '--skip-setup' in args or '-s' in args
    forzar_setup = '--forzar-setup' in args or '-f' in args
    silencioso = '--quiet' in args or '-q' in args

    # Limpiar argumentos especiales del lanzador
    args_limpios = [a for a in args if a not in [
        '--skip-setup', '-s', '--forzar-setup', '-f', '--quiet', '-q'
    ]]

    # Ayuda
    if '--help' in args or '-h' in args:
        show_help()
        sys.exit(0)

    # ===========================================================================
    # PASO 1: SETUP INICIAL CON ANIMACIONES
    # ===========================================================================
    if not skip_setup:
        setup_ok = ejecutar_setup_inicial(
            forzar=forzar_setup,
            silencioso=silencioso
        )

        if not setup_ok:
            print(f"\n{Colores.RED}Error durante la configuracion inicial{Colores.RESET}")
            print(f"Ejecuta: {Colores.CYAN}python instalar_sac.py{Colores.RESET} para configurar\n")
            sys.exit(1)
    else:
        # Solo banner simple si se omite setup
        if not silencioso:
            print_banner_simple()

    # ===========================================================================
    # PASO 2: COMANDOS ESPECIALES
    # ===========================================================================
    if '--validar-sistema' in args_limpios:
        success = run_verification()
        sys.exit(0 if success else 1)

    if '--tests' in args_limpios:
        success = run_tests()
        sys.exit(0 if success else 1)

    if '--config' in args_limpios:
        try:
            from config import imprimir_configuracion
            imprimir_configuracion()
        except Exception as e:
            print(f"{Colores.RED}Error al cargar configuracion: {e}{Colores.RESET}")
        sys.exit(0)

    # ===========================================================================
    # PASO 3: EJECUTAR SISTEMA PRINCIPAL
    # ===========================================================================
    if not silencioso:
        print(f"  {Colores.CYAN}🚀 Iniciando Sistema SAC...{Colores.RESET}\n")

    try:
        # Priorizar script maestro GUI
        master_gui_path = BASE_DIR / 'sac_master_gui.py'

        if master_gui_path.exists():
            # Usar el nuevo script maestro GUI unificado
            if not silencioso:
                print(f"  {Colores.CYAN}Usando Script Maestro GUI v3.0{Colores.RESET}\n")

            import sac_master_gui
            sac_master_gui.main()
        else:
            # Fallback a main.py
            import main as sac_main

            # Si no hay argumentos, mostrar menu
            if not args_limpios:
                args_limpios = ['--menu']

            # Reconstruir sys.argv para main
            sys.argv = ['sac_launcher.py'] + args_limpios

            # Llamar al main del sistema
            if hasattr(sac_main, 'main'):
                sac_main.main()
            else:
                print(f"{Colores.RED}Error: Funcion main() no encontrada{Colores.RESET}")
                sys.exit(1)

    except KeyboardInterrupt:
        print(f"\n\n{Colores.YELLOW}Sistema interrumpido por el usuario{Colores.RESET}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colores.RED}Error al iniciar el sistema: {e}{Colores.RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
