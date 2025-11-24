#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════
ANIMACIONES ASCII - Sistema SAC
CEDIS Chedraui Cancún 427
═══════════════════════════════════════════════════════════════

Animaciones ASCII para visualización de operaciones:
- Carga de camión CEDIS
- Barras de progreso animadas
- Efectos visuales para terminal

Uso:
    python animaciones.py
    python animaciones.py --demo

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
═══════════════════════════════════════════════════════════════
"""

import sys
import time
import os
import random
from typing import List, Optional, Callable

# ═══════════════════════════════════════════════════════════════
# UTILIDADES DE TERMINAL
# ═══════════════════════════════════════════════════════════════

def limpiar_pantalla():
    """Limpia la pantalla de la terminal."""
    os.system('cls' if os.name == 'nt' else 'clear')

def mover_cursor(x: int, y: int):
    """Mueve el cursor a una posición específica."""
    print(f"\033[{y};{x}H", end="")

def ocultar_cursor():
    """Oculta el cursor."""
    print("\033[?25l", end="")

def mostrar_cursor():
    """Muestra el cursor."""
    print("\033[?25h", end="")

def color_rojo(texto: str) -> str:
    """Retorna texto en rojo (color Chedraui)."""
    return f"\033[91m{texto}\033[0m"

def color_verde(texto: str) -> str:
    """Retorna texto en verde."""
    return f"\033[92m{texto}\033[0m"

def color_amarillo(texto: str) -> str:
    """Retorna texto en amarillo."""
    return f"\033[93m{texto}\033[0m"

def color_azul(texto: str) -> str:
    """Retorna texto en azul."""
    return f"\033[94m{texto}\033[0m"

def color_cian(texto: str) -> str:
    """Retorna texto en cian."""
    return f"\033[96m{texto}\033[0m"

def negrita(texto: str) -> str:
    """Retorna texto en negrita."""
    return f"\033[1m{texto}\033[0m"


# ═══════════════════════════════════════════════════════════════
# ARTE ASCII DEL CAMIÓN
# ═══════════════════════════════════════════════════════════════

CAMION_VACIO = r"""
                                    _______________
                                   |  CHEDRAUI    |
                                   |   CEDIS 427  |
       ___________________________|_______________|
      |                                           |
      |                                           |
      |                                           |
      |                                           |
      |___________________________________________|
         ____                              ____
        /    \                            /    \
       |  ()  |                          |  ()  |
        \____/                            \____/
"""

CAMION_FRAME = [
    "                                    _______________",
    "                                   |  CHEDRAUI    |",
    "                                   |   CEDIS 427  |",
    "       ___________________________|_______________|",
    "      |{interior}|",
    "      |{interior}|",
    "      |{interior}|",
    "      |{interior}|",
    "      |___________________________________________|",
    "         ____                              ____",
    "        /    \\                            /    \\",
    "       |  ()  |                          |  ()  |",
    "        \\____/                            \\____/",
]

# Cajas/pallets ASCII
CAJA = "█"
CAJA_OUTLINE = "▓"
PALLET = "▒"
ESPACIO = " "

# Montacargas ASCII frames
MONTACARGAS_FRAMES = [
    # Frame 1 - Montacargas bajado
    [
        "    ┌──┐",
        "    │██│",
        " ┌──┴──┴──┐",
        " │FORKLIFT│",
        " └─┬────┬─┘",
        "  (●)  (●)",
    ],
    # Frame 2 - Montacargas subiendo
    [
        "    ┌──┐",
        "    │██│ ↑",
        " ┌──┴──┴──┐",
        " │FORKLIFT│",
        " └─┬────┬─┘",
        "  (●)  (●)",
    ],
    # Frame 3 - Montacargas arriba
    [
        "    ┌──┐ ▓▓",
        "    │██│ ▓▓",
        " ┌──┴──┴──┐",
        " │FORKLIFT│",
        " └─┬────┬─┘",
        "  (●)  (●)",
    ],
]


# ═══════════════════════════════════════════════════════════════
# ANIMACIÓN DE CARGA DE CAMIÓN
# ═══════════════════════════════════════════════════════════════

class AnimacionCargaCamion:
    """
    Animación ASCII de carga de camión CEDIS Chedraui.
    Muestra pallets/cajas siendo cargados con barras de progreso.
    """

    def __init__(self, total_items: int = 10, velocidad: float = 0.15):
        """
        Inicializa la animación.

        Args:
            total_items: Número total de items a cargar
            velocidad: Velocidad de la animación (segundos entre frames)
        """
        self.total_items = total_items
        self.velocidad = velocidad
        self.items_cargados = 0
        self.ancho_interior = 41  # Ancho del interior del camión
        self.alto_interior = 4    # Alto del interior del camión
        self.carga_actual = []    # Estado actual de la carga

        # Inicializar matriz de carga vacía
        for _ in range(self.alto_interior):
            self.carga_actual.append([ESPACIO] * self.ancho_interior)

    def _dibujar_camion(self, mensaje: str = "", progreso: float = 0) -> List[str]:
        """Dibuja el camión con el estado actual de carga."""
        lineas = []

        # Header
        lineas.append("")
        lineas.append(color_rojo("  ╔══════════════════════════════════════════════════════════════╗"))
        lineas.append(color_rojo("  ║") + negrita("        🚛 SISTEMA DE CARGA - CEDIS CHEDRAUI 427 🚛          ") + color_rojo("║"))
        lineas.append(color_rojo("  ╚══════════════════════════════════════════════════════════════╝"))
        lineas.append("")

        # Barra de progreso principal
        barra_ancho = 50
        completado = int(barra_ancho * progreso)
        barra = color_verde("█" * completado) + color_azul("░" * (barra_ancho - completado))
        porcentaje = f"{progreso * 100:5.1f}%"
        lineas.append(f"   Progreso de carga: [{barra}] {color_amarillo(porcentaje)}")
        lineas.append(f"   Items: {color_cian(str(self.items_cargados))}/{self.total_items}")
        lineas.append("")

        # Cabina del camión
        lineas.append("                                         " + color_rojo("_______________"))
        lineas.append("                                        " + color_rojo("|") + negrita("  CHEDRAUI    ") + color_rojo("|"))
        lineas.append("                                        " + color_rojo("|") + negrita("   CEDIS 427  ") + color_rojo("|"))
        lineas.append("        " + color_azul("____________________________") + color_rojo("|_______________|"))

        # Interior del camión con carga
        for fila in self.carga_actual:
            interior = "".join(fila)
            lineas.append("       " + color_azul("|") + color_amarillo(interior) + color_azul("|"))

        # Parte inferior del camión
        lineas.append("       " + color_azul("|_________________________________________|"))
        lineas.append("          " + color_azul("____") + "                              " + color_azul("____"))
        lineas.append("         " + color_azul("/    \\") + "                            " + color_azul("/    \\"))
        lineas.append("        " + color_azul("|") + "  " + color_rojo("()") + "  " + color_azul("|") + "                          " + color_azul("|") + "  " + color_rojo("()") + "  " + color_azul("|"))
        lineas.append("         " + color_azul("\\____/") + "                            " + color_azul("\\____/"))

        # Mensaje de estado
        lineas.append("")
        if mensaje:
            lineas.append(f"   {mensaje}")
        lineas.append("")

        return lineas

    def _dibujar_montacargas(self, posicion_x: int, tiene_carga: bool = True, elevado: bool = False) -> List[str]:
        """Dibuja el montacargas en una posición."""
        if tiene_carga:
            if elevado:
                return [
                    "   ┌──┐ " + color_amarillo("▓▓"),
                    "   │" + color_verde("██") + "│ " + color_amarillo("▓▓"),
                    "┌──┴──┴──┐",
                    "│" + color_rojo("FORKLIFT") + "│",
                    "└─┬────┬─┘",
                    " (" + color_azul("●") + ")  (" + color_azul("●") + ")",
                ]
            else:
                return [
                    "   ┌──┐",
                    "   │" + color_verde("██") + "│ " + color_amarillo("▓▓"),
                    "┌──┴──┴──┐ " + color_amarillo("▓▓"),
                    "│" + color_rojo("FORKLIFT") + "│",
                    "└─┬────┬─┘",
                    " (" + color_azul("●") + ")  (" + color_azul("●") + ")",
                ]
        else:
            return [
                "   ┌──┐",
                "   │" + color_verde("██") + "│",
                "┌──┴──┴──┐",
                "│" + color_rojo("FORKLIFT") + "│",
                "└─┬────┬─┘",
                " (" + color_azul("●") + ")  (" + color_azul("●") + ")",
            ]

    def _agregar_item_carga(self):
        """Agrega un item a la carga del camión."""
        # Buscar espacio disponible (de derecha a izquierda, de abajo a arriba)
        ancho_item = 4  # Ancho de cada item

        for fila in range(self.alto_interior - 1, -1, -1):
            for col in range(self.ancho_interior - ancho_item, -1, -ancho_item):
                # Verificar si hay espacio
                espacio_libre = all(
                    self.carga_actual[fila][col + i] == ESPACIO
                    for i in range(ancho_item)
                )
                if espacio_libre:
                    # Agregar item
                    patron = random.choice([
                        ["▓", "▓", "▓", "▓"],
                        ["█", "█", "█", "█"],
                        ["▒", "▒", "▒", "▒"],
                        ["▓", "█", "█", "▓"],
                    ])
                    for i, char in enumerate(patron):
                        self.carga_actual[fila][col + i] = char
                    return True
        return False

    def _animar_entrada_pallet(self):
        """Anima la entrada de un pallet al camión."""
        posiciones_montacargas = [0, 5, 10, 15, 20]

        for i, pos in enumerate(posiciones_montacargas):
            limpiar_pantalla()

            # Dibujar camión
            lineas_camion = self._dibujar_camion(
                f"📦 Cargando pallet {self.items_cargados + 1}/{self.total_items}...",
                self.items_cargados / self.total_items
            )

            # Insertar montacargas
            montacargas = self._dibujar_montacargas(pos, tiene_carga=True, elevado=(i >= 3))

            # Imprimir escena completa
            for linea in lineas_camion:
                print(linea)

            # Dibujar montacargas debajo
            if pos < 20:
                espacios = " " * pos
                for linea_mk in montacargas:
                    print(espacios + linea_mk)

            time.sleep(self.velocidad)

    def ejecutar(self, callback: Optional[Callable[[int, int], None]] = None):
        """
        Ejecuta la animación completa de carga.

        Args:
            callback: Función opcional llamada después de cargar cada item
        """
        try:
            ocultar_cursor()
            limpiar_pantalla()

            # Animación inicial
            print("\n" * 3)
            print(color_rojo("  ╔══════════════════════════════════════════════════════════════╗"))
            print(color_rojo("  ║") + negrita("       🚛 INICIANDO PROCESO DE CARGA - CEDIS 427 🚛           ") + color_rojo("║"))
            print(color_rojo("  ╚══════════════════════════════════════════════════════════════╝"))
            print("\n")

            # Cuenta regresiva
            for i in range(3, 0, -1):
                print(f"\r   Iniciando en {color_amarillo(str(i))}...", end="")
                time.sleep(0.5)

            # Cargar items uno por uno
            for item in range(self.total_items):
                self._animar_entrada_pallet()
                self._agregar_item_carga()
                self.items_cargados += 1

                if callback:
                    callback(self.items_cargados, self.total_items)

                # Mostrar progreso
                limpiar_pantalla()
                lineas = self._dibujar_camion(
                    f"✅ Pallet {self.items_cargados} cargado exitosamente",
                    self.items_cargados / self.total_items
                )
                for linea in lineas:
                    print(linea)

                time.sleep(self.velocidad * 2)

            # Animación final
            self._mostrar_carga_completa()

        except KeyboardInterrupt:
            pass
        finally:
            mostrar_cursor()

    def _mostrar_carga_completa(self):
        """Muestra la animación de carga completa."""
        limpiar_pantalla()

        lineas = self._dibujar_camion(
            color_verde("✅ ¡CARGA COMPLETA! Camión listo para salida"),
            1.0
        )
        for linea in lineas:
            print(linea)

        # Animación de celebración
        celebracion = ["🎉", "🚛", "📦", "✅", "🎊"]
        print()
        for _ in range(3):
            for emoji in celebracion:
                print(f"\r   {' '.join(celebracion)}  ¡LISTO PARA DESPACHO!  {' '.join(celebracion[::-1])}", end="")
                time.sleep(0.2)
        print()


# ═══════════════════════════════════════════════════════════════
# BARRA DE PROGRESO ANIMADA
# ═══════════════════════════════════════════════════════════════

class BarraProgresoCarga:
    """Barra de progreso animada estilo carga de camión."""

    def __init__(self, total: int = 100, ancho: int = 40, titulo: str = "Procesando"):
        self.total = total
        self.ancho = ancho
        self.titulo = titulo
        self.actual = 0

        # Caracteres de animación
        self.chars_carga = ["▓", "▒", "░", "▒"]
        self.frame = 0

    def actualizar(self, valor: int, mensaje: str = ""):
        """Actualiza la barra de progreso."""
        self.actual = min(valor, self.total)
        self.frame = (self.frame + 1) % len(self.chars_carga)

        progreso = self.actual / self.total
        completado = int(self.ancho * progreso)
        restante = self.ancho - completado

        # Construir barra
        barra_llena = color_verde("█" * completado)
        char_animado = color_amarillo(self.chars_carga[self.frame]) if restante > 0 else ""
        barra_vacia = color_azul("░" * max(0, restante - 1))

        barra = f"{barra_llena}{char_animado}{barra_vacia}"
        porcentaje = f"{progreso * 100:5.1f}%"

        # Camión pequeño que avanza
        pos_camion = int(self.ancho * progreso)
        camion = "🚛"

        # Imprimir
        linea = f"\r   {color_rojo(self.titulo)}: [{barra}] {color_cian(porcentaje)} {camion}"
        if mensaje:
            linea += f" - {mensaje}"

        print(linea + "    ", end="", flush=True)

    def completar(self, mensaje: str = "¡Completado!"):
        """Marca la barra como completa."""
        self.actualizar(self.total, color_verde(mensaje))
        print()


# ═══════════════════════════════════════════════════════════════
# ANIMACIÓN DE VALIDACIÓN DE OC
# ═══════════════════════════════════════════════════════════════

def animar_validacion_oc(oc_numero: str, pasos: List[str] = None):
    """
    Animación para validación de OC con camión.

    Args:
        oc_numero: Número de la OC
        pasos: Lista de pasos a mostrar
    """
    if pasos is None:
        pasos = [
            "Conectando a DB2...",
            "Consultando OC...",
            "Obteniendo distribuciones...",
            "Validando cantidades...",
            "Verificando SKUs...",
            "Generando reporte...",
        ]

    try:
        ocultar_cursor()
        print()
        print(color_rojo("  ╔══════════════════════════════════════════════════════════════╗"))
        print(color_rojo("  ║") + negrita(f"        🔍 VALIDANDO OC: {oc_numero:^20}              ") + color_rojo("║"))
        print(color_rojo("  ╚══════════════════════════════════════════════════════════════╝"))
        print()

        # Animación de camión moviéndose
        camion_frames = [
            "🚛💨    ",
            " 🚛💨   ",
            "  🚛💨  ",
            "   🚛💨 ",
            "    🚛💨",
            "     🚛💨",
        ]

        barra = BarraProgresoCarga(len(pasos), ancho=45, titulo="Validando")

        for i, paso in enumerate(pasos):
            # Animación de camión
            for frame in camion_frames:
                print(f"\r   {frame} {paso}", end="", flush=True)
                time.sleep(0.08)

            barra.actualizar(i + 1, paso)
            time.sleep(0.3)

        barra.completar("✅ Validación completada")
        print()

    finally:
        mostrar_cursor()


# ═══════════════════════════════════════════════════════════════
# SPLASH SCREEN
# ═══════════════════════════════════════════════════════════════

def mostrar_splash_screen():
    """Muestra la pantalla de inicio con animación."""

    splash = r"""

     ██████╗██╗  ██╗███████╗██████╗ ██████╗  █████╗ ██╗   ██╗██╗
    ██╔════╝██║  ██║██╔════╝██╔══██╗██╔══██╗██╔══██╗██║   ██║██║
    ██║     ███████║█████╗  ██║  ██║██████╔╝███████║██║   ██║██║
    ██║     ██╔══██║██╔══╝  ██║  ██║██╔══██╗██╔══██║██║   ██║██║
    ╚██████╗██║  ██║███████╗██████╔╝██║  ██║██║  ██║╚██████╔╝██║
     ╚═════╝╚═╝  ╚═╝╚══════╝╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝

        ╔═══════════════════════════════════════════════════╗
        ║     🚛  SISTEMA DE AUTOMATIZACIÓN DE CONSULTAS    ║
        ║              CEDIS CANCÚN 427 - SAC               ║
        ╚═══════════════════════════════════════════════════╝

    """

    try:
        ocultar_cursor()
        limpiar_pantalla()

        # Mostrar splash línea por línea
        for linea in splash.split('\n'):
            print(color_rojo(linea))
            time.sleep(0.05)

        print()

        # Barra de carga
        barra = BarraProgresoCarga(100, ancho=50, titulo="Cargando sistema")
        for i in range(101):
            barra.actualizar(i)
            time.sleep(0.02)

        barra.completar("Sistema listo")
        print()
        time.sleep(0.5)

    finally:
        mostrar_cursor()


# ═══════════════════════════════════════════════════════════════
# ANIMACIÓN DE PROCESAMIENTO
# ═══════════════════════════════════════════════════════════════

def animar_procesamiento(mensaje: str = "Procesando", duracion: float = 3.0):
    """
    Muestra una animación de procesamiento con camión.

    Args:
        mensaje: Mensaje a mostrar
        duracion: Duración en segundos
    """
    frames = [
        "🚛💨      📦📦📦",
        " 🚛💨     📦📦📦",
        "  🚛💨    📦📦📦",
        "   🚛💨   📦📦📦",
        "    🚛💨  📦📦📦",
        "     🚛💨 📦📦📦",
        "      🚛💨📦📦📦",
        "       🚛📦📦📦",
        "        🚛📦📦",
        "         🚛📦",
        "          🚛",
    ]

    spinner = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    try:
        ocultar_cursor()
        start_time = time.time()
        frame_idx = 0
        spin_idx = 0

        while time.time() - start_time < duracion:
            frame = frames[frame_idx % len(frames)]
            spin = spinner[spin_idx % len(spinner)]

            print(f"\r   {color_amarillo(spin)} {mensaje}... {frame}    ", end="", flush=True)

            frame_idx += 1
            spin_idx += 1
            time.sleep(0.1)

        print(f"\r   {color_verde('✅')} {mensaje}... ¡Completado!           ")

    finally:
        mostrar_cursor()


# ═══════════════════════════════════════════════════════════════
# DEMO Y PUNTO DE ENTRADA
# ═══════════════════════════════════════════════════════════════

def demo_animaciones():
    """Ejecuta una demostración de todas las animaciones."""

    print("\n" + "=" * 60)
    print("  🎬 DEMO DE ANIMACIONES - SAC CEDIS 427")
    print("=" * 60)
    print("\n  Presiona Ctrl+C para saltar cualquier animación\n")
    input("  Presiona Enter para comenzar...")

    try:
        # 1. Splash screen
        print("\n  📺 1. Splash Screen")
        input("  Presiona Enter...")
        mostrar_splash_screen()

        # 2. Animación de validación
        print("\n  📺 2. Animación de Validación de OC")
        input("  Presiona Enter...")
        animar_validacion_oc("C7503840012345")

        # 3. Animación de procesamiento
        print("\n  📺 3. Animación de Procesamiento")
        input("  Presiona Enter...")
        animar_procesamiento("Generando reporte", 3.0)

        # 4. Carga de camión completa
        print("\n  📺 4. Animación de Carga de Camión")
        input("  Presiona Enter...")
        animacion = AnimacionCargaCamion(total_items=8, velocidad=0.1)
        animacion.ejecutar()

    except KeyboardInterrupt:
        mostrar_cursor()
        print("\n\n  Demo interrumpida por el usuario")

    print("\n" + "=" * 60)
    print("  ✅ Demo completada")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Animaciones ASCII - SAC CEDIS 427')
    parser.add_argument('--demo', action='store_true', help='Ejecutar demostración')
    parser.add_argument('--splash', action='store_true', help='Mostrar splash screen')
    parser.add_argument('--carga', type=int, default=0, help='Ejecutar animación de carga con N items')
    parser.add_argument('--validar', type=str, help='Animar validación de OC')

    args = parser.parse_args()

    if args.demo:
        demo_animaciones()
    elif args.splash:
        mostrar_splash_screen()
    elif args.carga > 0:
        animacion = AnimacionCargaCamion(total_items=args.carga)
        animacion.ejecutar()
    elif args.validar:
        animar_validacion_oc(args.validar)
    else:
        # Por defecto, ejecutar demo
        demo_animaciones()
