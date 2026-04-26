#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════
SCRIPT DE INICIO - AGENTE SAC
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Este script se ejecuta al inicio de sesión para invocar el Agente SAC.
Puede ser agregado al startup de Windows o ejecutado manualmente.

INSTALACIÓN EN STARTUP:
-----------------------
1. Crear acceso directo a este script
2. Mover a: C:\\Users\\<usuario>\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Startup

O desde GPO para toda la red (solo admin u427jd15)

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════
"""

import sys
import os
from pathlib import Path

# Agregar directorio del proyecto al path
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

# Argumentos de línea de comandos
import argparse


def main():
    """Punto de entrada principal"""
    parser = argparse.ArgumentParser(
        description='Agente SAC - Asistente Virtual CEDIS 427',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python iniciar_agente.py              # Inicia interfaz interactiva
  python iniciar_agente.py --silencioso # Inicia sin mostrar presentación
  python iniciar_agente.py --comando /ayuda  # Ejecuta un comando rápido
  python iniciar_agente.py --info       # Muestra información del agente
        """
    )

    parser.add_argument(
        '--silencioso', '-s',
        action='store_true',
        help='Inicia sin mostrar la presentación completa'
    )

    parser.add_argument(
        '--comando', '-c',
        type=str,
        help='Ejecuta un comando rápido y sale'
    )

    parser.add_argument(
        '--info', '-i',
        action='store_true',
        help='Muestra información del agente y sale'
    )

    parser.add_argument(
        '--version', '-v',
        action='store_true',
        help='Muestra la versión y sale'
    )

    parser.add_argument(
        '--notificacion', '-n',
        action='store_true',
        help='Muestra solo notificaciones (recordatorios pendientes)'
    )

    parser.add_argument(
        '--gui',
        action='store_true',
        help='Inicia en modo GUI (si está disponible)'
    )

    args = parser.parse_args()

    # Importar el módulo del agente
    try:
        from modules.agente_sac import (
            obtener_agente,
            iniciar_sesion,
            comando_rapido,
            presentar_agente,
            AGENTE_VERSION,
            AGENTE_CODENAME,
            CREADOR,
        )
    except ImportError as e:
        print(f"❌ Error importando módulo del agente: {e}")
        print("Asegúrate de estar en el directorio correcto del proyecto SAC.")
        sys.exit(1)

    # Modo versión
    if args.version:
        print(f"Agente SAC v{AGENTE_VERSION} ({AGENTE_CODENAME})")
        print(f"Creado por: {CREADOR['nombre_completo']} ({CREADOR['codigo']})")
        return

    # Obtener agente e iniciar sesión
    agente = obtener_agente()
    usuario = agente.identificar_usuario()

    # Modo info
    if args.info:
        print(presentar_agente('completo'))
        return

    # Modo comando único
    if args.comando:
        resultado = agente.procesar_comando_rapido(args.comando)
        if resultado:
            print(resultado)
        else:
            print(f"Comando '{args.comando}' no reconocido")
        return

    # Modo notificación (solo recordatorios)
    if args.notificacion:
        pendientes = agente.obtener_recordatorios_pendientes()
        if pendientes:
            print(f"\n🔔 Recordatorios pendientes ({len(pendientes)}):\n")
            for rec in pendientes:
                print(f"  [{rec.id}] {rec.mensaje}")
            print()
        else:
            print("✅ No hay recordatorios pendientes.")
        return

    # Modo GUI (placeholder para futuro)
    if args.gui:
        print("⚠️ El modo GUI aún no está implementado.")
        print("   Iniciando en modo consola...")

    # Modo silencioso
    if args.silencioso:
        print(f"🤖 Agente SAC v{AGENTE_VERSION} - ¡Listo!")
        print(f"   Usuario: {usuario.username}")
        pendientes = agente.obtener_recordatorios_pendientes()
        if pendientes:
            print(f"   🔔 {len(pendientes)} recordatorio(s) pendiente(s)")
        print("   Escribe '/' para comandos. 'salir' para terminar.\n")
    else:
        # Presentación completa
        print(presentar_agente('normal'))

        # Mostrar recordatorios pendientes
        pendientes = agente.obtener_recordatorios_pendientes()
        if pendientes:
            print(f"🔔 Tienes {len(pendientes)} recordatorio(s) pendiente(s):\n")
            for rec in pendientes:
                print(f"  • {rec.mensaje}")
            print()

        # Sugerencias personalizadas
        sugerencias = agente.obtener_sugerencias()
        if sugerencias:
            print(f"💡 Sugerencias: {', '.join(['/' + s for s in sugerencias[:3]])}\n")

    # Iniciar loop interactivo
    print("Escribe tu consulta o '/' para comandos. 'salir' para terminar.\n")

    while True:
        try:
            entrada = input(f"[{usuario.username}] > ").strip()

            if not entrada:
                continue

            if entrada.lower() in ['salir', 'exit', 'quit', 'q']:
                print("\n👋 ¡Hasta luego! - Agente SAC")
                break

            # Procesar comando rápido
            if entrada.startswith('/'):
                resultado = agente.procesar_comando_rapido(entrada)
                print(f"\n{resultado}\n")
            else:
                # Búsqueda en respuestas
                resultados = agente.buscar_respuestas(entrada)
                if resultados:
                    print(f"\n🔍 Encontré {len(resultados)} resultado(s):\n")
                    for resp in resultados[:3]:
                        print(f"  /{resp.comando} - {resp.titulo}")
                    print(f"\nEscribe /<comando> para ver el contenido.\n")
                else:
                    print(f"\n❓ No encontré respuestas para '{entrada}'.")
                    print("   Escribe / para ver comandos disponibles.\n")

        except KeyboardInterrupt:
            print("\n\n👋 ¡Hasta luego!")
            break
        except EOFError:
            break


if __name__ == "__main__":
    main()
