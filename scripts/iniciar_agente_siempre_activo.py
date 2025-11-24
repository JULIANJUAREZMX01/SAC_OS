#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════════════
INICIAR AGENTE SAC SIEMPRE ACTIVO
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════════════

Script para iniciar el Agente SAC en modo background/daemon continuo.
Proporciona múltiples formas de invocación y control.

USOS:
    python iniciar_agente_siempre_activo.py
        Inicia en modo interactivo

    python iniciar_agente_siempre_activo.py --daemon
        Inicia como servicio en background

    python iniciar_agente_siempre_activo.py --estado
        Muestra estado actual del agente

    python iniciar_agente_siempre_activo.py --detener
        Detiene el agente en ejecución

    python iniciar_agente_siempre_activo.py --config nivel_autonomia=media
        Inicia con configuración personalizada

INSTALACIÓN EN WINDOWS STARTUP:
    1. Crear acceso directo a: scripts\\iniciar_agente_siempre_activo.bat
    2. Mover a: C:\\Users\\<usuario>\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Startup

INSTALACIÓN EN LINUX/MAC STARTUP:
    1. Agregar a crontab: @reboot python /ruta/scripts/iniciar_agente_siempre_activo.py --daemon
    2. O agregar a .bashrc / .zshrc: python /ruta/scripts/iniciar_agente_siempre_activo.py --daemon &

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════════════
"""

import sys
import os
import argparse
import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

# Agregar directorio padre al path para importar módulos
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_DIR))

# Imports
try:
    from modules.agente_siempre_activo import (
        AgenteSACSimpreActivo,
        obtener_agente_siempre_activo,
        ConfiguracionCopiloto,
        NivelAutonomia,
        AGENTE_SIEMPRE_ACTIVO_VERSION,
    )
except ImportError as e:
    print(f"❌ Error en importaciones: {e}")
    print("Asegúrate de estar ejecutando desde el directorio correcto del proyecto SAC.")
    sys.exit(1)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(PROJECT_DIR / 'output' / 'logs' / 'agente_siempre_activo.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════
# INFORMACIÓN DEL PROGRAMA
# ═══════════════════════════════════════════════════════════════════════

TITULO_PROGRAMA = f"""
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║     🤖 AGENTE SAC SIEMPRE ACTIVO - ASISTENTE VIRTUAL 24/7          ║
║                                                                       ║
║     Sistema de Automatización de Consultas                          ║
║     CEDIS Cancún 427 - Tiendas Chedraui S.A. de C.V.               ║
║                                                                       ║
║     Versión: {AGENTE_SIEMPRE_ACTIVO_VERSION:<43} ║
║     Modo: Background Continuo                                        ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
"""

INFORMACION_MODOS = """
┌─ MODOS DE OPERACIÓN ─────────────────────────────────────────────────┐
│                                                                       │
│ 🔄 NORMAL (Interactivo)                                             │
│    El agente funciona bajo demanda, esperando comandos del usuario  │
│    Modo recomendado para sesiones de trabajo activas               │
│                                                                       │
│ 🤖 COPILOTO (Automático)                                            │
│    Se activa después de 30 minutos sin respuesta                    │
│    Ejecuta tareas preautorizadas automáticamente                    │
│    Entra en vigor cuando el usuario se ausenta                      │
│                                                                       │
│ 🎯 DAEMON (Servicio)                                                │
│    Ejecuta en background sin interfaz interactiva                   │
│    Ideal para ejecutar como servicio del sistema                    │
│    Monitorea en segundo plano continuamente                         │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
"""


# ═══════════════════════════════════════════════════════════════════════
# FUNCIONES PRINCIPALES
# ═══════════════════════════════════════════════════════════════════════

def mostrar_presentacion():
    """Muestra la presentación del agente"""
    print(TITULO_PROGRAMA)
    print(INFORMACION_MODOS)


def mostrar_version():
    """Muestra la versión del agente"""
    print(f"Agente SAC Siempre Activo v{AGENTE_SIEMPRE_ACTIVO_VERSION}")
    print("Creador: Julián Alexander Juárez Alvarado (ADMJAJA)")
    print("Cargo: Jefe de Sistemas")
    print("CEDIS: Cancún 427 - Tiendas Chedraui")


def mostrar_estado(agente: AgenteSACSimpreActivo):
    """Muestra el estado actual del agente"""
    estado = agente.obtener_estado()

    print("\n" + "═" * 70)
    print("📊 ESTADO DEL AGENTE SAC SIEMPRE ACTIVO")
    print("═" * 70)

    print(f"\n🤖 Información General:")
    print(f"   Versión: {estado['version']}")
    print(f"   Activo: {'✅ Sí' if estado['activo'] else '❌ No'}")
    print(f"   Timestamp: {estado['timestamp']}")

    print(f"\n🔄 Modo Copiloto:")
    print(f"   Estado: {estado['estado_copiloto']}")
    print(f"   Tiempo Inactivo: {estado['tiempo_inactivo']}")
    print(f"   Tareas Pendientes: {estado['tareas_pendientes']}")

    stats = estado['estadisticas']
    print(f"\n📈 Estadísticas:")
    print(f"   Tareas Ejecutadas: {stats['total_tareas_ejecutadas']}")
    print(f"   Errores: {stats['total_errores']}")
    print(f"   Activaciones Copiloto: {stats['modo_copiloto_activaciones']}")
    print(f"   Tiempo en Copiloto: {stats['tiempo_en_copiloto_total']:.1f} segundos")

    print("\n" + "═" * 70 + "\n")


def iniciar_modo_interactivo(agente: AgenteSACSimpreActivo):
    """Inicia el agente en modo interactivo"""
    print("\n✅ Agente SAC Siempre Activo iniciado en modo interactivo")
    print("📝 Escribe 'ayuda' para ver comandos disponibles")
    print("❌ Escribe 'salir' para terminar\n")

    comandos_disponibles = {
        'ayuda': 'Muestra esta ayuda',
        'estado': 'Muestra estado actual del agente',
        'copiloto': 'Información sobre modo copiloto',
        'tareas': 'Muestra tareas pendientes',
        'eventos': 'Muestra últimos eventos registrados',
        'salir': 'Termina el programa',
    }

    while True:
        try:
            entrada = input("agente> ").strip().lower()

            if not entrada:
                continue

            if entrada == 'salir':
                print("👋 ¡Hasta luego!")
                agente._detener()
                break

            elif entrada == 'ayuda':
                print("\n📋 Comandos disponibles:")
                for cmd, desc in comandos_disponibles.items():
                    print(f"   {cmd:<15} - {desc}")
                print()

            elif entrada == 'estado':
                mostrar_estado(agente)

            elif entrada == 'copiloto':
                estado = agente.obtener_estado()
                print(f"\n🤖 Modo Copiloto: {estado['estado_copiloto']}")
                print(f"   Configuración:")
                print(f"   - Habilitado: {agente.config.habilitado}")
                print(f"   - Timeout: {agente.config.timeout_minutos} minutos")
                print(f"   - Nivel de Autonomía: {agente.config.nivel_autonomia.value}")
                print()

            elif entrada == 'tareas':
                tareas = agente.motor_tareas.tareas_pendientes
                if tareas:
                    print(f"\n📋 {len(tareas)} tarea(s) pendiente(s):")
                    for tarea in tareas:
                        print(f"   [{tarea.id}] {tarea.tipo.value} - Prioridad: {tarea.prioridad}")
                else:
                    print("\n✅ No hay tareas pendientes\n")

            elif entrada == 'eventos':
                eventos = agente.eventos[-10:]  # Últimos 10 eventos
                print(f"\n📝 Últimos {len(eventos)} eventos:")
                for evt in eventos:
                    print(f"   {evt.timestamp.strftime('%H:%M:%S')} - {evt.tipo.value} ({evt.severidad})")
                print()

            else:
                print(f"❓ Comando no reconocido: '{entrada}'")
                print("   Escribe 'ayuda' para ver comandos disponibles.\n")

        except KeyboardInterrupt:
            print("\n\n👋 ¡Hasta luego!")
            agente._detener()
            break
        except Exception as e:
            print(f"❌ Error: {e}\n")


def iniciar_modo_daemon(agente: AgenteSACSimpreActivo):
    """Inicia el agente en modo daemon (background sin interfaz)"""
    logger.info("🚀 Iniciando Agente SAC Siempre Activo en modo DAEMON")
    print("🚀 Agente iniciado en modo daemon (background)")
    print("   Ver logs en: output/logs/agente_siempre_activo.log")

    agente.iniciar()


def crear_archivo_config_ejemplo(config_path: Path):
    """Crea archivo de configuración de ejemplo"""
    config_ejemplo = {
        "copiloto": {
            "habilitado": True,
            "timeout_minutos": 30,
            "nivel_autonomia": "basica",
            "tareas_autorizadas": [
                "generacion_reporte",
                "envio_alerta",
                "notificacion",
                "verificacion_salud"
            ],
            "notificar_al_activar": True,
            "horario_inicio_no_laboral": "22:00",
            "horario_fin_no_laboral": "08:00"
        },
        "logging": {
            "nivel": "INFO",
            "archivo": "output/logs/agente_siempre_activo.log",
            "tamaño_maximo_mb": 10,
            "backup_count": 5
        }
    }

    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config_ejemplo, f, indent=2, ensure_ascii=False)

    print(f"✅ Archivo de configuración creado: {config_path}")


def parsear_argumentos():
    """Parsea argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(
        description='Agente SAC Siempre Activo - Asistente Virtual Continuo',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python iniciar_agente_siempre_activo.py
      Inicia en modo interactivo

  python iniciar_agente_siempre_activo.py --daemon
      Inicia como servicio en background

  python iniciar_agente_siempre_activo.py --estado
      Muestra estado actual

CONFIGURACIÓN:
  Crear un archivo config/agente_config.json para personalizar
        """
    )

    parser.add_argument(
        '--version', '-v',
        action='store_true',
        help='Muestra la versión'
    )

    parser.add_argument(
        '--daemon', '-d',
        action='store_true',
        help='Inicia en modo daemon (background)'
    )

    parser.add_argument(
        '--estado',
        action='store_true',
        help='Muestra el estado actual del agente'
    )

    parser.add_argument(
        '--detener',
        action='store_true',
        help='Detiene el agente en ejecución'
    )

    parser.add_argument(
        '--config-ejemplo',
        action='store_true',
        help='Crea archivo de configuración de ejemplo'
    )

    parser.add_argument(
        '--timeout-minutos',
        type=int,
        default=30,
        help='Timeout para activar copiloto (defecto: 30)'
    )

    parser.add_argument(
        '--nivel-autonomia',
        choices=['minima', 'basica', 'media', 'alta'],
        default='basica',
        help='Nivel de autonomía del agente (defecto: basica)'
    )

    parser.add_argument(
        '--sin-presentacion', '-s',
        action='store_true',
        help='No muestra la presentación'
    )

    return parser.parse_args()


# ═══════════════════════════════════════════════════════════════════════
# FUNCIÓN PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════

def main():
    """Función principal"""
    args = parsear_argumentos()

    # Mostrar presentación
    if not args.sin_presentacion and not args.version and not args.estado and not args.config_ejemplo:
        mostrar_presentacion()

    # Modo version
    if args.version:
        mostrar_version()
        return

    # Modo config ejemplo
    if args.config_ejemplo:
        config_path = PROJECT_DIR / 'config' / 'agente_config.json'
        crear_archivo_config_ejemplo(config_path)
        return

    # Crear configuración
    try:
        nivel_autonomia = NivelAutonomia(args.nivel_autonomia)
    except ValueError:
        print(f"❌ Nivel de autonomía inválido: {args.nivel_autonomia}")
        sys.exit(1)

    config = ConfiguracionCopiloto(
        timeout_minutos=args.timeout_minutos,
        nivel_autonomia=nivel_autonomia
    )

    # Crear agente
    try:
        agente = AgenteSACSimpreActivo(config)
    except Exception as e:
        print(f"❌ Error creando agente: {e}")
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)

    # Modo estado
    if args.estado:
        mostrar_estado(agente)
        return

    # Modo daemon
    if args.daemon:
        iniciar_modo_daemon(agente)
    else:
        # Modo interactivo (default)
        try:
            agente.iniciar()  # Inicia en background
            iniciar_modo_interactivo(agente)
        except KeyboardInterrupt:
            print("\n👋 ¡Hasta luego!")
            agente._detener()
        except Exception as e:
            print(f"❌ Error: {e}")
            logger.error(f"Error: {e}", exc_info=True)
            sys.exit(1)


if __name__ == "__main__":
    main()
