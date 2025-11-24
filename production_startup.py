#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════
PRODUCTION STARTUP - INICIALIZACIÓN PARA PRODUCCIÓN
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Script que inicializa el sistema SAC en ambiente de producción.
Realiza verificaciones, prepara directorios, y valida configuración.

Uso:
    python production_startup.py              # Startup normal
    python production_startup.py --interactive # Con modo interactivo
    python production_startup.py --monitor    # Inicia con monitoreo
    python production_startup.py --check      # Solo verificaciones

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
═══════════════════════════════════════════════════════════════
"""

import os
import sys
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)

PROJECT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_DIR))


class ProductionStartup:
    """Inicializador de producción"""

    def __init__(self, interactive: bool = False):
        self.interactive = interactive
        self.startup_time = datetime.now()
        self.checks_passed = []
        self.checks_failed = []

    def imprimir_banner(self):
        """Banner de bienvenida"""
        print("""
        ╔═════════════════════════════════════════════════════╗
        ║  🚀 STARTUP DE PRODUCCIÓN - SAC v1.0               ║
        ║  Sistema de Automatización de Consultas             ║
        ║  CEDIS Cancún 427 - Tiendas Chedraui              ║
        ╚═════════════════════════════════════════════════════╝
        """)
        logger.info("="*70)
        logger.info("🚀 INICIANDO SISTEMA EN MODO PRODUCCIÓN")
        logger.info("="*70)

    def verificar_python_version(self) -> bool:
        """Verifica versión de Python"""
        logger.info("\n📌 Verificando versión de Python...")

        version_info = sys.version_info
        version_str = f"{version_info.major}.{version_info.minor}.{version_info.micro}"

        if version_info.major >= 3 and version_info.minor >= 8:
            logger.info(f"   ✅ Python {version_str} OK")
            self.checks_passed.append("Python Version")
            return True
        else:
            logger.error(f"   ❌ Python {version_str} - Requiere 3.8+")
            self.checks_failed.append("Python Version")
            return False

    def verificar_ambiente(self) -> bool:
        """Verifica ambiente (.env existe)"""
        logger.info("\n📌 Verificando configuración de ambiente...")

        env_path = PROJECT_DIR / '.env'
        if env_path.exists():
            logger.info("   ✅ Archivo .env encontrado")
            self.checks_passed.append(".env Configuration")
            return True
        else:
            logger.warning("   ⚠️  Archivo .env no encontrado")
            logger.warning("   → Ejecuta: python setup_env_seguro.py")
            self.checks_failed.append(".env Configuration")
            return False

    def cargar_configuracion(self) -> bool:
        """Carga configuración del sistema"""
        logger.info("\n📌 Cargando configuración...")

        try:
            from config import (
                VERSION, DB_CONFIG, EMAIL_CONFIG, PATHS,
                CEDIS, SYSTEM_CONFIG, validar_configuracion
            )

            logger.info(f"   ✅ SAC v{VERSION}")
            logger.info(f"   ✅ CEDIS: {CEDIS['name']}")
            logger.info(f"   ✅ Región: {CEDIS['region']}")
            logger.info(f"   ✅ Ambiente: {SYSTEM_CONFIG['environment']}")

            # Validar configuración
            es_valida, errores = validar_configuracion()
            if es_valida:
                logger.info("   ✅ Configuración válida")
                self.checks_passed.append("Configuration")
                return True
            else:
                logger.error("   ❌ Errores en configuración:")
                for error in errores:
                    logger.error(f"      - {error}")
                self.checks_failed.append("Configuration")
                return False

        except Exception as e:
            logger.error(f"   ❌ Error cargando configuración: {e}")
            self.checks_failed.append("Configuration")
            return False

    def preparar_directorios(self) -> bool:
        """Prepara directorios necesarios"""
        logger.info("\n📌 Preparando directorios...")

        try:
            from config import PATHS

            directorios = [
                PATHS['output'],
                PATHS['logs'],
                PATHS['resultados'],
            ]

            for directorio in directorios:
                directorio.mkdir(parents=True, exist_ok=True)
                logger.info(f"   ✅ {directorio.name}")

            self.checks_passed.append("Directories")
            return True

        except Exception as e:
            logger.error(f"   ❌ Error preparando directorios: {e}")
            self.checks_failed.append("Directories")
            return False

    def verificar_dependencias(self) -> bool:
        """Verifica dependencias críticas"""
        logger.info("\n📌 Verificando dependencias...")

        dependencias_criticas = [
            ('pandas', 'Procesamiento de datos'),
            ('openpyxl', 'Reportes Excel'),
            ('rich', 'UI de consola'),
            ('python_dotenv', 'Variables de entorno'),
        ]

        todos_ok = True
        for paquete, descripcion in dependencias_criticas:
            try:
                __import__(paquete.replace('-', '_'))
                logger.info(f"   ✅ {paquete} ({descripcion})")
            except ImportError:
                logger.error(f"   ❌ {paquete} NO instalado")
                todos_ok = False

        if todos_ok:
            self.checks_passed.append("Dependencies")
        else:
            self.checks_failed.append("Dependencies")
            logger.error("   → Ejecuta: pip install -r requirements.txt")

        return todos_ok

    def inicializar_logging(self) -> bool:
        """Inicializa sistema de logging"""
        logger.info("\n📌 Inicializando sistema de logging...")

        try:
            from config import PATHS, LOGGING_CONFIG
            import logging.handlers

            # Crear logger del proyecto
            proyecto_logger = logging.getLogger('SAC')
            proyecto_logger.setLevel(logging.INFO)

            # Handler de archivo
            log_file = PATHS['logs'] / 'sac_production.log'
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=10485760,  # 10MB
                backupCount=5
            )
            file_handler.setLevel(logging.INFO)

            # Formato
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)

            proyecto_logger.addHandler(file_handler)

            logger.info(f"   ✅ Logging configurado en: {log_file}")
            self.checks_passed.append("Logging")
            return True

        except Exception as e:
            logger.error(f"   ❌ Error inicializando logging: {e}")
            self.checks_failed.append("Logging")
            return False

    def mostrar_informacion_sistema(self):
        """Muestra información del sistema"""
        logger.info("\n" + "="*70)
        logger.info("📊 INFORMACIÓN DEL SISTEMA")
        logger.info("="*70)

        try:
            from config import (
                VERSION, CEDIS, SYSTEM_CONFIG, DB_CONFIG,
                EMAIL_CONFIG
            )

            logger.info(f"\n📦 Versión: {VERSION}")
            logger.info(f"🏢 CEDIS: {CEDIS['name']}")
            logger.info(f"🌍 Región: {CEDIS['region']}")
            logger.info(f"🏭 Almacén: {CEDIS['almacen']}")
            logger.info(f"⚙️  Ambiente: {SYSTEM_CONFIG['environment']}")
            logger.info(f"🕐 Timezone: {SYSTEM_CONFIG['timezone']}")
            logger.info(f"\n💾 Base de Datos:")
            logger.info(f"   Host: {DB_CONFIG['host']}")
            logger.info(f"   Puerto: {DB_CONFIG['port']}")
            logger.info(f"   Database: {DB_CONFIG['database']}")
            logger.info(f"\n📧 Email SMTP:")
            logger.info(f"   Servidor: {EMAIL_CONFIG['smtp_server']}")
            logger.info(f"   Puerto: {EMAIL_CONFIG['smtp_port']}")

        except Exception as e:
            logger.warning(f"⚠️  Error mostrando información: {e}")

    def mostrar_resumen(self):
        """Muestra resumen de startup"""
        logger.info("\n" + "="*70)
        logger.info("✅ RESUMEN DE STARTUP")
        logger.info("="*70)

        logger.info(f"\n✅ Checks Exitosos ({len(self.checks_passed)}):")
        for check in self.checks_passed:
            logger.info(f"   ✅ {check}")

        if self.checks_failed:
            logger.warning(f"\n❌ Checks Fallidos ({len(self.checks_failed)}):")
            for check in self.checks_failed:
                logger.warning(f"   ❌ {check}")
        else:
            logger.info("\n🎉 ¡Todos los checks pasaron!")

        # Tiempo de startup
        duracion = datetime.now() - self.startup_time
        logger.info(f"\n⏱️  Tiempo de startup: {duracion.total_seconds():.2f}s")

    def ejecutar_verificaciones(self) -> bool:
        """Ejecuta todas las verificaciones"""
        self.imprimir_banner()

        checks = [
            self.verificar_python_version,
            self.verificar_ambiente,
            self.preparar_directorios,
            self.verificar_dependencias,
            self.cargar_configuracion,
            self.inicializar_logging,
        ]

        for check in checks:
            try:
                if not check():
                    if check in [
                        self.verificar_python_version,
                        self.cargar_configuracion,
                        self.verificar_ambiente,
                    ]:
                        logger.error("\n⚠️  Verificación crítica fallida")
                        return False
            except Exception as e:
                logger.error(f"Error ejecutando {check.__name__}: {e}")
                return False

        self.mostrar_informacion_sistema()
        self.mostrar_resumen()

        return len(self.checks_failed) == 0

    def ejecutar(self):
        """Ejecuta startup completo"""
        exito = self.ejecutar_verificaciones()

        if exito:
            logger.info("\n" + "="*70)
            logger.info("✅ SISTEMA LISTO PARA PRODUCCIÓN")
            logger.info("="*70)
            logger.info("\n📌 Próximos pasos:")
            logger.info("   1. Ejecuta: python main.py")
            logger.info("   2. Selecciona una opción del menú")
            logger.info("   3. El sistema procesará tu solicitud\n")
            return 0
        else:
            logger.error("\n" + "="*70)
            logger.error("❌ SISTEMA NO LISTO - CORREGIR ERRORES")
            logger.error("="*70)
            logger.error("\n⚠️  Revisa los errores arriba para resolver\n")
            return 1


def main():
    """Función principal"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Production Startup del Sistema SAC'
    )
    parser.add_argument(
        '--interactive',
        action='store_true',
        help='Modo interactivo'
    )
    parser.add_argument(
        '--check',
        action='store_true',
        help='Solo verificaciones (no inicia servicios)'
    )
    parser.add_argument(
        '--monitor',
        action='store_true',
        help='Inicia con monitoreo en tiempo real'
    )

    args = parser.parse_args()

    startup = ProductionStartup(interactive=args.interactive)
    codigo_salida = startup.ejecutar()

    if codigo_salida == 0 and args.monitor:
        logger.info("\n📊 Iniciando monitoreo...")
        try:
            from monitor import MonitorTiempoReal
            monitor = MonitorTiempoReal()
            monitor.monitorear_continuamente()
        except Exception as e:
            logger.error(f"Error iniciando monitor: {e}")
            sys.exit(1)

    sys.exit(codigo_salida)


if __name__ == '__main__':
    main()
