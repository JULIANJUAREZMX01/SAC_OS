#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════════════════════
SACITY VISUAL DEMO - Demostración Interactiva
═══════════════════════════════════════════════════════════════════════════════

Demo interactivo completo de todas las capacidades visuales de SACITY:
- Banners y logos
- Animaciones de carga
- Barras de estado
- Mensajes cybersecurity
- Prompts interactivos
- Diferentes temas de color

Ejecuta este archivo para ver SACITY en acción:
    python demo_visual_sacity.py

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Organización: SISTEMAS_427 - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════════════════════
"""

import sys
import time
import random
from datetime import datetime

try:
    from sacity_visual_config import (
        SacityVisualConfig,
        ANSI,
        ASCII_ART,
        CyberMessages,
        THEME_RED_BLOOD,
        THEME_CYBER_RED,
        THEME_DARK_GOTHIC,
        THEME_RED_HAT,
        limpiar_pantalla,
    )
except ImportError:
    print("❌ Error: No se pudo importar sacity_visual_config.py")
    print("   Asegúrate de estar en el directorio correcto.")
    sys.exit(1)


def pausa(segundos=1.5):
    """Pausa con mensaje"""
    time.sleep(segundos)


def esperar_enter(mensaje="Presiona ENTER para continuar..."):
    """Espera a que el usuario presione ENTER"""
    try:
        input(f"\n{ANSI.GRAY}{mensaje}{ANSI.RESET}")
    except KeyboardInterrupt:
        print(f"\n{ANSI.YELLOW}Demo interrumpido{ANSI.RESET}")
        sys.exit(0)


def demo_seccion(titulo):
    """Imprime título de sección"""
    print(f"\n{ANSI.RED_BRIGHT}{'═' * 70}{ANSI.RESET}")
    print(f"{ANSI.RED_BRIGHT}  {titulo}{ANSI.RESET}")
    print(f"{ANSI.RED_BRIGHT}{'═' * 70}{ANSI.RESET}\n")


# ═══════════════════════════════════════════════════════════════════════════════
# DEMOS INDIVIDUALES
# ═══════════════════════════════════════════════════════════════════════════════

def demo_1_banners():
    """Demo 1: Banners y Logos"""
    demo_seccion("DEMO 1: BANNERS Y LOGOS")

    config = SacityVisualConfig()

    print(ANSI.CYAN + "1.1 Logo Principal (Grande)" + ANSI.RESET)
    print(ASCII_ART.LOGO_FULL)
    pausa(2)

    print(ANSI.CYAN + "\n1.2 Banner de Inicio Completo" + ANSI.RESET)
    print(config.get_banner_inicio())
    pausa(2)

    print(ANSI.CYAN + "\n1.3 Logo Mini" + ANSI.RESET)
    print(f"  {ASCII_ART.LOGO_MINI}")
    pausa(1)


def demo_2_animaciones():
    """Demo 2: Animaciones de Carga"""
    demo_seccion("DEMO 2: ANIMACIONES DE CARGA")

    config = SacityVisualConfig()

    print(ANSI.CYAN + "Animación estilo hacker..." + ANSI.RESET + "\n")

    frames = config.get_frames_loading()
    for frame in frames:
        print(f"\r{frame}", end="", flush=True)
        time.sleep(0.6)

    print("\n")
    pausa(1)


def demo_3_status_bar():
    """Demo 3: Barra de Estado"""
    demo_seccion("DEMO 3: BARRA DE ESTADO")

    config = SacityVisualConfig()

    print(ANSI.CYAN + "Simulando cambios en batería y WiFi..." + ANSI.RESET + "\n")

    for bateria in range(100, 9, -15):
        for wifi in range(5, -1, -1):
            hora = datetime.now().strftime("%H:%M:%S")
            print(config.get_status_bar(
                bateria=bateria,
                wifi_nivel=wifi,
                hora=hora
            ))
            time.sleep(0.3)
            # Limpiar las 3 líneas anteriores
            print("\033[F" * 3, end="")

    # Mostrar final
    print(config.get_status_bar(bateria=15, wifi_nivel=1))
    pausa(2)


def demo_4_mensajes_cyber():
    """Demo 4: Mensajes Cybersecurity"""
    demo_seccion("DEMO 4: MENSAJES CYBERSECURITY")

    print(ANSI.CYAN + "4.1 Mensajes de Proceso" + ANSI.RESET + "\n")
    for key, msg in CyberMessages.PROCESO.items():
        print(f"  {msg}")
        time.sleep(0.5)

    print(ANSI.CYAN + "\n4.2 Alertas" + ANSI.RESET + "\n")
    for key, msg in CyberMessages.ALERTA.items():
        print(f"  {msg}")
        time.sleep(0.4)

    print(ANSI.CYAN + "\n4.3 Estados de Acceso" + ANSI.RESET + "\n")
    for key, msg in CyberMessages.ACCESO.items():
        print(f"  {msg}")
        time.sleep(0.4)

    print(ANSI.CYAN + "\n4.4 Seguridad" + ANSI.RESET + "\n")
    for key, msg in CyberMessages.SEGURIDAD.items():
        print(f"  {msg}")
        time.sleep(0.4)

    pausa(2)


def demo_5_prompts():
    """Demo 5: Prompts Interactivos"""
    demo_seccion("DEMO 5: PROMPTS INTERACTIVOS")

    config = SacityVisualConfig()

    modos = ['normal', 'secure', 'admin', 'root']

    for modo in modos:
        prompt = config.get_prompt(modo)
        print(f"{ANSI.CYAN}Modo: {modo.upper()}{ANSI.RESET}")
        print(f"  {prompt}comando_ejemplo")
        pausa(0.8)


def demo_6_pantalla_completa():
    """Demo 6: Pantalla Completa Simulada"""
    demo_seccion("DEMO 6: INTERFAZ COMPLETA MC9190")

    config = SacityVisualConfig()

    limpiar_pantalla()

    # Status bar
    print(config.get_status_bar(bateria=78, wifi_nivel=5))

    # Área de trabajo
    print(ANSI.GRAY + "╔══════════════════════════════════════════════════════════════╗" + ANSI.RESET)
    print(ANSI.GRAY + "║" + ANSI.RESET + "  " + ANSI.CYAN_BRIGHT + "MANHATTAN WMS - TERMINAL EMULATOR" + ANSI.RESET + "                       " + ANSI.GRAY + "║" + ANSI.RESET)
    print(ANSI.GRAY + "║" + ANSI.RESET + "                                                              " + ANSI.GRAY + "║" + ANSI.RESET)
    print(ANSI.GRAY + "║" + ANSI.RESET + "  " + ANSI.WHITE_BRIGHT + "Usuario:" + ANSI.RESET + " " + ANSI.CYAN_BRIGHT + "ADMJAJA" + ANSI.RESET + "                                            " + ANSI.GRAY + "║" + ANSI.RESET)
    print(ANSI.GRAY + "║" + ANSI.RESET + "  " + ANSI.WHITE_BRIGHT + "Almacén:" + ANSI.RESET + " " + ANSI.GREEN_BRIGHT + "C22 (CEDIS CANCÚN)" + ANSI.RESET + "                             " + ANSI.GRAY + "║" + ANSI.RESET)
    print(ANSI.GRAY + "║" + ANSI.RESET + "  " + ANSI.WHITE_BRIGHT + "Sesión:" + ANSI.RESET + " " + ANSI.GREEN + "ACTIVA" + ANSI.RESET + " " + ANSI.DIM + "(conectado 02:34:12)" + ANSI.RESET + "                  " + ANSI.GRAY + "║" + ANSI.RESET)
    print(ANSI.GRAY + "║" + ANSI.RESET + "                                                              " + ANSI.GRAY + "║" + ANSI.RESET)
    print(ANSI.GRAY + "╠══════════════════════════════════════════════════════════════╣" + ANSI.RESET)
    print(ANSI.GRAY + "║" + ANSI.RESET + "  " + ANSI.RED + "[🔒 INFORMACIÓN CONFIDENCIAL]" + ANSI.RESET + "                             " + ANSI.GRAY + "║" + ANSI.RESET)
    print(ANSI.GRAY + "║" + ANSI.RESET + "                                                              " + ANSI.GRAY + "║" + ANSI.RESET)
    print(ANSI.GRAY + "║" + ANSI.RESET + "  " + ANSI.YELLOW_BRIGHT + "FUNCIÓN ACTIVA: RECEPCIÓN DE MERCANCÍA" + ANSI.RESET + "                     " + ANSI.GRAY + "║" + ANSI.RESET)
    print(ANSI.GRAY + "║" + ANSI.RESET + "                                                              " + ANSI.GRAY + "║" + ANSI.RESET)
    print(ANSI.GRAY + "║" + ANSI.RESET + "  " + ANSI.WHITE_BRIGHT + "> ESCANEAR LPN:" + ANSI.RESET + " " + ANSI.WHITE_BRIGHT + "█" + ANSI.RESET + "                                       " + ANSI.GRAY + "║" + ANSI.RESET)
    print(ANSI.GRAY + "║" + ANSI.RESET + "                                                              " + ANSI.GRAY + "║" + ANSI.RESET)
    print(ANSI.GRAY + "╠══════════════════════════════════════════════════════════════╣" + ANSI.RESET)
    print(ANSI.GRAY + "║" + ANSI.RESET + "  " + ANSI.DIM + "F1:Menu  F2:Buscar  F3:Reportes  F4:Config" + ANSI.RESET + "      " + ANSI.DIM + "ESC:Salir" + ANSI.RESET + " " + ANSI.GRAY + "║" + ANSI.RESET)
    print(ANSI.GRAY + "╚══════════════════════════════════════════════════════════════╝" + ANSI.RESET)

    print()
    print(ANSI.CYAN_BRIGHT + "[INFO]" + ANSI.RESET + " Esperando escaneo de LPN o código de barras...")
    print(ANSI.CYAN + "[👁️  SISTEMAS MONITOREANDO]" + ANSI.RESET + " Conexión estable | Tiempo respuesta: 42ms")

    pausa(3)


def demo_7_simulacion_uso():
    """Demo 7: Simulación de Uso Real"""
    demo_seccion("DEMO 7: SIMULACIÓN DE USO REAL")

    config = SacityVisualConfig()

    print(ANSI.CYAN + "Simulando flujo de recepción de mercancía..." + ANSI.RESET + "\n")

    # Paso 1: Escaneo de LPN
    print(config.get_prompt('normal') + "LPN0000123456")
    pausa(0.5)

    print(f"{ANSI.CYAN_BRIGHT}[PROCESANDO]{ANSI.RESET} Validando LPN...")
    pausa(0.8)

    print(f"{ANSI.GREEN_BRIGHT}[✓ VÁLIDO]{ANSI.RESET} LPN encontrado en sistema")
    print(f"  {ANSI.GRAY}• Orden de Compra: {ANSI.WHITE}OC750384123456{ANSI.RESET}")
    print(f"  {ANSI.GRAY}• Proveedor: {ANSI.WHITE}COCA-COLA FEMSA{ANSI.RESET}")
    print(f"  {ANSI.GRAY}• Items esperados: {ANSI.WHITE}48 cajas{ANSI.RESET}")
    pausa(1.5)

    # Paso 2: Confirmación
    print(f"\n{ANSI.YELLOW}[⚡ ACCIÓN REQUERIDA]{ANSI.RESET} ¿Confirmar recepción? (S/N)")
    print(config.get_prompt('secure') + "S")
    pausa(0.5)

    print(f"\n{ANSI.CYAN_BRIGHT}[GUARDANDO]{ANSI.RESET} Registrando en base de datos...")
    pausa(1)

    print(f"{ANSI.GREEN_BRIGHT}[✓ COMPLETADO]{ANSI.RESET} Recepción registrada exitosamente")
    print(f"  {ANSI.GRAY}• Timestamp: {ANSI.WHITE}{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{ANSI.RESET}")
    print(f"  {ANSI.GRAY}• Usuario: {ANSI.WHITE}ADMJAJA{ANSI.RESET}")
    print(f"  {ANSI.GRAY}• Ubicación: {ANSI.WHITE}ANDÉN-A01{ANSI.RESET}")

    pausa(2)


def demo_8_dispositivo_ascii():
    """Demo 8: Arte ASCII del Dispositivo"""
    demo_seccion("DEMO 8: DISPOSITIVO MC9190 ASCII ART")

    print(ASCII_ART.MC9190)

    pausa(3)


def demo_9_footer_creditos():
    """Demo 9: Footer y Créditos"""
    demo_seccion("DEMO 9: FOOTER Y CRÉDITOS")

    config = SacityVisualConfig()

    print(config.get_footer())

    pausa(2)


# ═══════════════════════════════════════════════════════════════════════════════
# MENÚ PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

def menu_principal():
    """Menú principal de demos"""

    while True:
        limpiar_pantalla()

        print(ASCII_ART.LOGO_FULL)
        print(f"{ANSI.GRAY}          {SacityVisualConfig.SLOGAN}{ANSI.RESET}")
        print(f"{ANSI.GRAY}    ═══════════════════════════════════════════{ANSI.RESET}\n")

        print(f"{ANSI.RED_BRIGHT}╔══════════════════════════════════════════════════════════════╗{ANSI.RESET}")
        print(f"{ANSI.RED_BRIGHT}║{ANSI.RESET}  {ANSI.BOLD}SACITY VISUAL DEMO - MENÚ PRINCIPAL{ANSI.RESET}                        {ANSI.RED_BRIGHT}║{ANSI.RESET}")
        print(f"{ANSI.RED_BRIGHT}╚══════════════════════════════════════════════════════════════╝{ANSI.RESET}\n")

        print(f"  {ANSI.CYAN}1.{ANSI.RESET} Banners y Logos")
        print(f"  {ANSI.CYAN}2.{ANSI.RESET} Animaciones de Carga")
        print(f"  {ANSI.CYAN}3.{ANSI.RESET} Barra de Estado")
        print(f"  {ANSI.CYAN}4.{ANSI.RESET} Mensajes Cybersecurity")
        print(f"  {ANSI.CYAN}5.{ANSI.RESET} Prompts Interactivos")
        print(f"  {ANSI.CYAN}6.{ANSI.RESET} Interfaz Completa MC9190")
        print(f"  {ANSI.CYAN}7.{ANSI.RESET} Simulación de Uso Real")
        print(f"  {ANSI.CYAN}8.{ANSI.RESET} Dispositivo MC9190 ASCII Art")
        print(f"  {ANSI.CYAN}9.{ANSI.RESET} Footer y Créditos")
        print()
        print(f"  {ANSI.GREEN_BRIGHT}0.{ANSI.RESET} Ver TODO (demo completa)")
        print(f"  {ANSI.RED}Q.{ANSI.RESET} Salir")

        print(f"\n{ANSI.GRAY}─────────────────────────────────────────────────────────────{ANSI.RESET}")

        opcion = input(f"\n{ANSI.RED_BRIGHT}[SACITY]{ANSI.RESET}{ANSI.GRAY}>{ANSI.RESET} Selecciona opción: ").strip().upper()

        if opcion == '1':
            limpiar_pantalla()
            demo_1_banners()
            esperar_enter()
        elif opcion == '2':
            limpiar_pantalla()
            demo_2_animaciones()
            esperar_enter()
        elif opcion == '3':
            limpiar_pantalla()
            demo_3_status_bar()
            esperar_enter()
        elif opcion == '4':
            limpiar_pantalla()
            demo_4_mensajes_cyber()
            esperar_enter()
        elif opcion == '5':
            limpiar_pantalla()
            demo_5_prompts()
            esperar_enter()
        elif opcion == '6':
            demo_6_pantalla_completa()
            esperar_enter()
        elif opcion == '7':
            limpiar_pantalla()
            demo_7_simulacion_uso()
            esperar_enter()
        elif opcion == '8':
            limpiar_pantalla()
            demo_8_dispositivo_ascii()
            esperar_enter()
        elif opcion == '9':
            limpiar_pantalla()
            demo_9_footer_creditos()
            esperar_enter()
        elif opcion == '0':
            # Demo completa
            demos = [
                demo_1_banners,
                demo_2_animaciones,
                demo_3_status_bar,
                demo_4_mensajes_cyber,
                demo_5_prompts,
                demo_6_pantalla_completa,
                demo_7_simulacion_uso,
                demo_8_dispositivo_ascii,
                demo_9_footer_creditos,
            ]
            for demo in demos:
                limpiar_pantalla()
                demo()
                esperar_enter()
        elif opcion == 'Q':
            limpiar_pantalla()
            print(f"\n{ANSI.RED_BRIGHT}[SACITY]{ANSI.RESET} Gracias por usar SACITY Visual Demo\n")
            print(f"{ANSI.GRAY}Diseñado por: ADMJAJA | SISTEMAS_427 | UNT{ANSI.RESET}\n")
            break
        else:
            print(f"\n{ANSI.RED}[✖ ERROR]{ANSI.RESET} Opción inválida")
            pausa(1)


# ═══════════════════════════════════════════════════════════════════════════════
# PUNTO DE ENTRADA
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Punto de entrada principal"""
    try:
        menu_principal()
    except KeyboardInterrupt:
        print(f"\n\n{ANSI.YELLOW}[⚠️  INTERRUMPIDO]{ANSI.RESET} Demo cancelada por el usuario\n")
    except Exception as e:
        print(f"\n{ANSI.RED}[✖ ERROR]{ANSI.RESET} {str(e)}\n")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()