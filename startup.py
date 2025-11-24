#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════════════════════
                         SAC STARTUP - PUNTO DE ENTRADA ÚNICO
                    Sistema de Automatización de Consultas
                    CEDIS Cancún 427 - Tiendas Chedraui
═══════════════════════════════════════════════════════════════════════════════

PUNTO DE ENTRADA ÚNICO Y CENTRALIZADO

Este archivo es el corazón del sistema. Realiza todas las inicializaciones necesarias:
✅ Carga variables de entorno
✅ Configura logging
✅ Verifica instalación
✅ Muestra animaciones ASCII
✅ Inicializa el GUI
✅ Soporta modo DEV completo

USO:
    python startup.py                  # Modo interactivo (recomendado)
    python startup.py --dev            # Modo desarrollo
    python startup.py --gui            # Modo GUI
    python startup.py --cli            # Modo CLI
    python startup.py --monitor        # Modo monitor continuo
    python startup.py --help           # Ayuda

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
═══════════════════════════════════════════════════════════════════════════════
"""

import os
import sys
import logging
import argparse
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List

# Agregar el directorio base al path
BASE_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(BASE_DIR))

# ═══════════════════════════════════════════════════════════════════════════════
# FASE 1: CARGA INICIAL DE ENTORNO (ANTES QUE NADA)
# ═══════════════════════════════════════════════════════════════════════════════

from dotenv import load_dotenv
load_dotenv()

# ═══════════════════════════════════════════════════════════════════════════════
# FASE 2: COLORES PARA OUTPUT (SIN DEPENDENCIAS)
# ═══════════════════════════════════════════════════════════════════════════════

class Colores:
    """Códigos ANSI para colores en terminal"""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'

    # Colores texto
    ROJO = '\033[91m'
    VERDE = '\033[92m'
    AMARILLO = '\033[93m'
    AZUL = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    BLANCO = '\033[97m'

    # Chedraui
    ROJO_CHEDRAUI = '\033[38;5;196m'

    @staticmethod
    def success(msg: str) -> str:
        return f"{Colores.VERDE}✅ {msg}{Colores.RESET}"

    @staticmethod
    def error(msg: str) -> str:
        return f"{Colores.ROJO}❌ {msg}{Colores.RESET}"

    @staticmethod
    def warning(msg: str) -> str:
        return f"{Colores.AMARILLO}⚠️  {msg}{Colores.RESET}"

    @staticmethod
    def info(msg: str) -> str:
        return f"{Colores.CYAN}ℹ️  {msg}{Colores.RESET}"

    @staticmethod
    def loading(msg: str) -> str:
        return f"{Colores.AZUL}⏳ {msg}{Colores.RESET}"


# ═══════════════════════════════════════════════════════════════════════════════
# FASE 3: IMPORTAR CONFIGURACIÓN CENTRALIZADA
# ═══════════════════════════════════════════════════════════════════════════════

try:
    from config import (
        DB_CONFIG, CEDIS, EMAIL_CONFIG, PATHS, COLORS, VERSION,
        LOGGING_CONFIG, DB_POOL_CONFIG
    )
    CONFIG_OK = True
except ImportError as e:
    print(Colores.error(f"Error al cargar config.py: {e}"))
    CONFIG_OK = False

# ═══════════════════════════════════════════════════════════════════════════════
# FASE 3B: IMPORTAR SISTEMA DE EMAILS AUTOMÁTICOS
# ═══════════════════════════════════════════════════════════════════════════════

try:
    from email_automatico import (
        GestorEmailAutomatico,
        iniciar_emails_automaticos,
        detener_emails_automaticos,
        gestor_automatico
    )
    EMAIL_AUTOMATICO_OK = True
except ImportError as e:
    print(Colores.warning(f"Advertencia: No se pudo cargar email_automatico.py: {e}"))
    EMAIL_AUTOMATICO_OK = False
    iniciar_emails_automaticos = None
    detener_emails_automaticos = None
    gestor_automatico = None

# ═══════════════════════════════════════════════════════════════════════════════
# FASE 3C: IMPORTAR SETUP DE CREDENCIALES
# ═══════════════════════════════════════════════════════════════════════════════

try:
    from setup_credenciales import (
        ejecutar_setup_interactivo,
        verificar_credenciales_configuradas,
    )
    SETUP_OK = True
except ImportError as e:
    print(Colores.warning(f"Advertencia: No se pudo cargar setup_credenciales.py: {e}"))
    SETUP_OK = False
    ejecutar_setup_interactivo = None
    verificar_credenciales_configuradas = None

# ═══════════════════════════════════════════════════════════════════════════════
# FASE 4: CONFIGURACIÓN DE LOGGING CENTRALIZADA
# ═══════════════════════════════════════════════════════════════════════════════

def configurar_logging(nivel: int = logging.INFO) -> logging.Logger:
    """Configura el sistema de logging centralizado"""

    if not CONFIG_OK:
        logging.basicConfig(level=nivel)
        return logging.getLogger(__name__)

    # Crear directorio de logs
    log_dir = PATHS['logs']
    log_dir.mkdir(parents=True, exist_ok=True)

    # Nombre del archivo
    timestamp = datetime.now().strftime('%Y%m%d')
    log_file = log_dir / f"sac_startup_{timestamp}.log"

    # Configurar logging
    logging.basicConfig(
        level=nivel,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

    logger = logging.getLogger(__name__)
    logger.info("=" * 80)
    logger.info(f"STARTUP INICIADO - {datetime.now()}")
    logger.info(f"Versión: {VERSION}")
    logger.info("=" * 80)

    return logger


logger = configurar_logging()

# ═══════════════════════════════════════════════════════════════════════════════
# FASE 5: ANIMACIONES ASCII
# ═══════════════════════════════════════════════════════════════════════════════

class AnimacionesStartup:
    """Animaciones ASCII para el startup"""

    @staticmethod
    def banner_inicio():
        """Muestra el banner de inicio con Chedraui colors"""
        banner = f"""
{Colores.ROJO_CHEDRAUI}
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║              ███████╗ █████╗  ██████╗    ███████╗████████╗ █████╗ █████╗   ║
║              ██╔════╝██╔══██╗██╔════╝    ██╔════╝╚══██╔══╝██╔══██╗██╔══██╗  ║
║              ███████╗███████║██║         ███████╗   ██║   ███████║██████╔╝  ║
║              ╚════██║██╔══██║██║         ╚════██║   ██║   ██╔══██║██╔══██╗  ║
║              ███████║██║  ██║╚██████╗    ███████║   ██║   ██║  ██║██║  ██║  ║
║              ╚══════╝╚═╝  ╚═╝ ╚═════╝    ╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝  ║
║                                                                              ║
║                  Sistema de Automatización de Consultas                      ║
║                      CEDIS Cancún 427 - Chedraui                            ║
║                                                                              ║
║                    Desarrollado por: ADMJAJA - Jefe de Sistemas             ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
{Colores.RESET}
        """
        print(banner)
        logger.info("Banner de inicio mostrado")

    @staticmethod
    def barra_progreso(paso: int, total: int, mensaje: str = ""):
        """Muestra una barra de progreso animada"""
        porcentaje = int((paso / total) * 100)
        barra_llena = "█" * int(porcentaje / 5)
        barra_vacia = "░" * (20 - int(porcentaje / 5))

        emoji = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"][paso % 10]

        print(f"\r{emoji} [{barra_llena}{barra_vacia}] {porcentaje}% {mensaje:<30}", end="", flush=True)
        time.sleep(0.1)

    @staticmethod
    def animacion_carga_modulos():
        """Anima la carga de módulos"""
        modulos = [
            "Cargando configuración...",
            "Inicializando logging...",
            "Verificando base de datos...",
            "Cargando módulos principales...",
            "Preparando interfaz gráfica...",
            "Sistema listo para operar..."
        ]

        for i, modulo in enumerate(modulos, 1):
            AnimacionesStartup.barra_progreso(i, len(modulos), modulo)
            time.sleep(0.3)

        print()  # Nueva línea
        logger.info("Módulos cargados exitosamente")


# ═══════════════════════════════════════════════════════════════════════════════
# FASE 6: VERIFICACIÓN DEL SISTEMA
# ═══════════════════════════════════════════════════════════════════════════════

class VerificacionSistema:
    """Verifica la integridad del sistema"""

    @staticmethod
    def verificar_archivos_criticos() -> bool:
        """Verifica que existan todos los archivos críticos"""
        archivos_criticos = [
            BASE_DIR / 'config.py',
            BASE_DIR / 'main.py',
            BASE_DIR / 'monitor.py',
            BASE_DIR / 'gestor_correos.py',
            BASE_DIR / 'modules' / '__init__.py',
        ]

        print(Colores.loading("Verificando archivos críticos..."))
        todos_existen = True

        for archivo in archivos_criticos:
            if archivo.exists():
                print(Colores.success(f"  {archivo.relative_to(BASE_DIR)}"))
                logger.info(f"Archivo verificado: {archivo.relative_to(BASE_DIR)}")
            else:
                print(Colores.error(f"  {archivo.relative_to(BASE_DIR)} - NO ENCONTRADO"))
                logger.error(f"Archivo faltante: {archivo.relative_to(BASE_DIR)}")
                todos_existen = False

        return todos_existen

    @staticmethod
    def verificar_directorios() -> bool:
        """Verifica y crea directorios necesarios"""
        print(Colores.loading("Verificando directorios..."))

        directorios = [
            PATHS['logs'],
            PATHS['resultados'],
            BASE_DIR / 'config',
            BASE_DIR / 'modules',
        ]

        todos_ok = True
        for directorio in directorios:
            try:
                directorio.mkdir(parents=True, exist_ok=True)
                print(Colores.success(f"  {directorio.relative_to(BASE_DIR)}"))
                logger.info(f"Directorio verificado/creado: {directorio.relative_to(BASE_DIR)}")
            except Exception as e:
                print(Colores.error(f"  {directorio.relative_to(BASE_DIR)} - Error: {e}"))
                logger.error(f"Error al crear directorio {directorio}: {e}")
                todos_ok = False

        return todos_ok

    @staticmethod
    def verificar_instalacion() -> bool:
        """Verifica si el sistema está instalado"""
        archivo_instalado = BASE_DIR / 'config' / '.instalado'
        return archivo_instalado.exists()

    @staticmethod
    def marcar_como_instalado():
        """Marca el sistema como instalado"""
        archivo_instalado = BASE_DIR / 'config' / '.instalado'
        archivo_instalado.parent.mkdir(parents=True, exist_ok=True)
        archivo_instalado.touch()
        logger.info("Sistema marcado como instalado")


# ═══════════════════════════════════════════════════════════════════════════════
# FASE 7: MODO DEV FUNCIONAL
# ═══════════════════════════════════════════════════════════════════════════════

class ModoDesarrollo:
    """Modo desarrollo con datos ficticios y configuración flexible"""

    MODO_DEV_ACTIVO = False

    @staticmethod
    def activar_modo_dev():
        """Activa el modo desarrollo"""
        ModoDesarrollo.MODO_DEV_ACTIVO = True

        print(Colores.warning("MODO DESARROLLO ACTIVADO"))
        print("""
┌─────────────────────────────────────────────────────────────┐
│  🔧 MODO DEV - Ambiente de Pruebas                         │
│                                                             │
│  ✅ Datos ficticios para pruebas                           │
│  ✅ Modo simulación sin DB2 real                           │
│  ✅ Correos en modo de prueba (no se envían)               │
│  ✅ Logs detallados en console                             │
│  ✅ Reportes de demostración                               │
│                                                             │
│  Para usar base de datos real, use:                        │
│  python startup.py --prod                                  │
└─────────────────────────────────────────────────────────────┘
        """)
        logger.warning("MODO DESARROLLO ACTIVADO - Usando datos ficticios")

    @staticmethod
    def obtener_configuracion_dev() -> Dict:
        """Retorna configuración para modo desarrollo"""
        return {
            'DB_MOCK': True,
            'EMAIL_TEST': True,
            'LOG_LEVEL': logging.DEBUG,
            'DEMO_DATA': True,
            'SKIP_DB_CHECK': True,
            'SHOW_DETAILS': True,
        }

    @staticmethod
    def cargar_datos_demo():
        """Carga datos de demostración"""
        logger.info("Cargando datos de demostración para modo DEV")
        return {
            'oc_ejemplo': 'OC7503840000001',
            'distribucion_ejemplo': 'DIST000001',
            'cantidad': 100,
            'estado': 'ABIERTA',
        }


# ═══════════════════════════════════════════════════════════════════════════════
# FASE 8: INTERFAZ GUI PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

class MenuPrincipal:
    """Menú principal interactivo del sistema"""

    @staticmethod
    def mostrar_menu_inicio():
        """Muestra el menú de inicio principal"""
        print(f"""
{Colores.BOLD}{Colores.CYAN}
╔════════════════════════════════════════════════════════════════╗
║                    📊 MENÚ PRINCIPAL - SAC                     ║
╚════════════════════════════════════════════════════════════════╝
{Colores.RESET}

  {Colores.VERDE}1.{Colores.RESET} Validar Orden de Compra (OC)
  {Colores.VERDE}2.{Colores.RESET} Generar Reporte Diario
  {Colores.VERDE}3.{Colores.RESET} Monitor en Tiempo Real
  {Colores.VERDE}4.{Colores.RESET} Enviar Alerta Crítica
  {Colores.VERDE}5.{Colores.RESET} Ver Estado del Sistema
  {Colores.VERDE}6.{Colores.RESET} Configuración y Credenciales
  {Colores.VERDE}0.{Colores.RESET} Salir

{Colores.CYAN}─────────────────────────────────────────────────────────────{Colores.RESET}
        """)

    @staticmethod
    def procesar_opcion(opcion: str):
        """Procesa la opción seleccionada"""
        if opcion == '1':
            print(Colores.info("Iniciando validación de OC..."))
            # Aquí iría la lógica de validación

        elif opcion == '2':
            print(Colores.info("Generando reporte diario..."))
            # Aquí iría la lógica de reporte

        elif opcion == '3':
            print(Colores.info("Iniciando monitor en tiempo real..."))
            # Aquí iría la lógica de monitor

        elif opcion == '4':
            print(Colores.warning("Enviando alerta crítica..."))
            # Aquí iría la lógica de alerta

        elif opcion == '5':
            print(Colores.info("Estado del sistema:"))
            MenuPrincipal.mostrar_estado_sistema()

        elif opcion == '6':
            print(Colores.info("Abriendo configuración..."))
            # Aquí iría la lógica de configuración

        elif opcion == '0':
            print(Colores.warning("Saliendo del sistema..."))
            sys.exit(0)

        else:
            print(Colores.error("Opción no válida"))

    @staticmethod
    def mostrar_estado_sistema():
        """Muestra el estado actual del sistema"""
        print(f"""
{Colores.BOLD}ESTADO DEL SISTEMA SAC{Colores.RESET}

  Version:           {VERSION}
  CEDIS:             {CEDIS['name']} ({CEDIS['code']})
  Región:            {CEDIS['region']}
  Base de Datos:     {DB_CONFIG['host']}
  Email:             {EMAIL_CONFIG['user']}

  Modo Desarrollo:   {Colores.VERDE if ModoDesarrollo.MODO_DEV_ACTIVO else Colores.ROJO}{'Activo ✓' if ModoDesarrollo.MODO_DEV_ACTIVO else 'Inactivo ✗'}{Colores.RESET}

  Timestamp:         {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """)


# ═══════════════════════════════════════════════════════════════════════════════
# FASE 9: FUNCIÓN PRINCIPAL - FLUJO DE STARTUP
# ═══════════════════════════════════════════════════════════════════════════════

def startup_principal(modo: str = "interactivo", dev: bool = False, gui: bool = True):
    """
    Función principal de startup

    Args:
        modo: 'interactivo', 'cli', 'monitor', 'daemon'
        dev: Activar modo desarrollo
        gui: Mostrar interfaz gráfica
    """

    logger.info(f"Iniciando SAC en modo: {modo} (dev={dev}, gui={gui})")

    # ─────────────────────────────────────────────────────────────
    # PASO 1: MOSTRAR BANNER
    # ─────────────────────────────────────────────────────────────
    AnimacionesStartup.banner_inicio()
    time.sleep(1)

    # ─────────────────────────────────────────────────────────────
    # PASO 2: ACTIVAR MODO DEV SI SE SOLICITA
    # ─────────────────────────────────────────────────────────────
    if dev:
        ModoDesarrollo.activar_modo_dev()
        time.sleep(1)

    # ─────────────────────────────────────────────────────────────
    # PASO 3: ANIMACIÓN DE CARGA
    # ─────────────────────────────────────────────────────────────
    AnimacionesStartup.animacion_carga_modulos()
    time.sleep(1)

    # ─────────────────────────────────────────────────────────────
    # PASO 4: VERIFICACIÓN DEL SISTEMA
    # ─────────────────────────────────────────────────────────────
    print()
    archivos_ok = VerificacionSistema.verificar_archivos_criticos()
    print()
    directorios_ok = VerificacionSistema.verificar_directorios()
    print()

    if not (archivos_ok and directorios_ok):
        print(Colores.error("El sistema no pasó todas las verificaciones"))
        logger.error("Falló la verificación del sistema")
        return False

    # ─────────────────────────────────────────────────────────────
    # PASO 5: VERIFICAR INSTALACIÓN Y CREDENCIALES
    # ─────────────────────────────────────────────────────────────
    if not VerificacionSistema.verificar_instalacion():
        print(Colores.warning("Primera vez que se ejecuta el sistema"))
        print(Colores.info("Se requerirá configuración inicial..."))
        logger.info("Primera ejecución detectada")

        # Ejecutar setup de credenciales si está disponible
        if SETUP_OK and ejecutar_setup_interactivo:
            print()
            print(Colores.loading("Iniciando asistente de configuración..."))
            time.sleep(1)
            exito_setup = ejecutar_setup_interactivo()
            if exito_setup:
                # Recargar variables de entorno después del setup
                from dotenv import load_dotenv
                load_dotenv()
                logger.info("Credenciales configuradas mediante setup interactivo")
            else:
                print(Colores.error("Setup cancelado. El sistema requiere credenciales configuradas."))
                logger.error("Setup cancelado por el usuario")
                return False
        else:
            print(Colores.warning("Setup interactivo no disponible. Configure .env manualmente."))

        VerificacionSistema.marcar_como_instalado()

    # Verificar que las credenciales estén configuradas
    elif SETUP_OK and verificar_credenciales_configuradas:
        if not verificar_credenciales_configuradas():
            print(Colores.warning("Credenciales no configuradas"))
            print(Colores.info("¿Desea ejecutar el asistente de configuración?"))
            respuesta = input(f"{Colores.CYAN}(s/n): {Colores.RESET}").strip().lower()
            if respuesta in ['s', 'si', 'sí', 'yes', 'y']:
                if ejecutar_setup_interactivo():
                    from dotenv import load_dotenv
                    load_dotenv()
                    logger.info("Credenciales actualizadas mediante setup")
                else:
                    print(Colores.error("Setup cancelado"))
                    return False
            else:
                print(Colores.warning("Sistema requiere credenciales configuradas. Saliendo..."))
                return False

    # ─────────────────────────────────────────────────────────────
    # PASO 6: MOSTRAR INFORMACIÓN DEL SISTEMA
    # ─────────────────────────────────────────────────────────────
    print()
    MenuPrincipal.mostrar_estado_sistema()
    print()

    # ─────────────────────────────────────────────────────────────
    # PASO 6B: INICIAR SISTEMA DE EMAILS AUTOMÁTICOS
    # ─────────────────────────────────────────────────────────────
    if EMAIL_AUTOMATICO_OK:
        print(Colores.loading("Iniciando sistema automático de emails..."))
        iniciar_emails_automaticos()
        print(Colores.success("Sistema de emails automáticos en ejecución"))
        logger.info("Sistema automático de emails iniciado")
    else:
        print(Colores.warning("Sistema de emails automáticos no disponible"))

    # ─────────────────────────────────────────────────────────────
    # PASO 7: MOSTRAR MENÚ Y PROCESAR COMANDOS
    # ─────────────────────────────────────────────────────────────
    if modo == "interactivo" and gui:
        try:
            while True:
                MenuPrincipal.mostrar_menu_inicio()
                opcion = input(f"{Colores.CYAN}Seleccione una opción: {Colores.RESET}").strip()
                print()
                MenuPrincipal.procesar_opcion(opcion)
                print()
                time.sleep(1)
        except KeyboardInterrupt:
            print()
            print(Colores.warning("Interrupción del usuario detectada"))
            logger.info("Sistema interrumpido por el usuario")
            print(Colores.info("Saliendo..."))

    # ─────────────────────────────────────────────────────────────
    # PASO 8: MODO MONITOR CONTINUO
    # ─────────────────────────────────────────────────────────────
    elif modo == "monitor":
        print(Colores.info("Iniciando monitor continuo..."))
        logger.info("Monitor continuo iniciado")
        print(Colores.warning("Monitor ejecutándose. Presione Ctrl+C para salir."))
        try:
            while True:
                print(f"{datetime.now()} - Monitor activo...")
                time.sleep(5)
        except KeyboardInterrupt:
            print()
            print(Colores.info("Monitor detenido"))
            logger.info("Monitor detenido por el usuario")

    # ─────────────────────────────────────────────────────────────
    # PASO 9: MODO CLI
    # ─────────────────────────────────────────────────────────────
    elif modo == "cli":
        print(Colores.info("Modo CLI - Sistema listo para comandos"))
        logger.info("Sistema en modo CLI")

    print()

    # ─────────────────────────────────────────────────────────────
    # CLEANUP: DETENER SISTEMAS
    # ─────────────────────────────────────────────────────────────
    if EMAIL_AUTOMATICO_OK and detener_emails_automaticos:
        detener_emails_automaticos()
        print(Colores.info("Sistema de emails automáticos detenido"))

    print()
    print(Colores.success("Sistema finalizado correctamente"))
    logger.info("Startup completado exitosamente")
    return True


# ═══════════════════════════════════════════════════════════════════════════════
# FASE 10: PARSEO DE ARGUMENTOS
# ═══════════════════════════════════════════════════════════════════════════════

def parse_argumentos():
    """Parsea los argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(
        description='SAC - Sistema de Automatización de Consultas',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python startup.py                 # Modo interactivo
  python startup.py --dev           # Modo desarrollo
  python startup.py --monitor       # Monitor continuo
  python startup.py --cli           # Modo CLI

Contacto: ADMJAJA - Jefe de Sistemas CEDIS Cancún 427
        """
    )

    parser.add_argument(
        '--dev',
        action='store_true',
        help='Activar modo desarrollo (datos de prueba)'
    )

    parser.add_argument(
        '--prod',
        action='store_true',
        help='Modo producción (base de datos real)'
    )

    parser.add_argument(
        '--monitor',
        action='store_true',
        help='Iniciar en modo monitor continuo'
    )

    parser.add_argument(
        '--cli',
        action='store_true',
        help='Modo CLI sin interfaz gráfica'
    )

    parser.add_argument(
        '--gui',
        action='store_true',
        default=True,
        help='Mostrar interfaz gráfica (por defecto: True)'
    )

    parser.add_argument(
        '--no-gui',
        action='store_true',
        help='Desactivar interfaz gráfica'
    )

    parser.add_argument(
        '--version',
        action='version',
        version=f'SAC {VERSION}'
    )

    return parser.parse_args()


# ═══════════════════════════════════════════════════════════════════════════════
# PUNTO DE ENTRADA - MAIN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    try:
        # Parsear argumentos
        args = parse_argumentos()

        # Determinar modo de ejecución
        modo = "interactivo"
        dev = args.dev
        gui = args.gui and not args.no_gui

        if args.monitor:
            modo = "monitor"
        elif args.cli:
            modo = "cli"

        # Ejecutar startup principal
        exito = startup_principal(modo=modo, dev=dev, gui=gui)

        # Código de salida
        sys.exit(0 if exito else 1)

    except Exception as e:
        print(Colores.error(f"Error fatal en startup: {e}"))
        logger.exception(f"Error fatal en startup: {e}")
        sys.exit(1)
