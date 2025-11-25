#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
===============================================================================
SACITY UI - INTERFAZ GRÁFICA ASCII ANIMADA
Sistema de Automatización para Emulador Telnet
===============================================================================

Interfaz de terminal con animaciones ASCII y paleta de colores Chedraui.

PALETA DE COLORES:
- ROJO  (#E31837) - Letras, menús estáticos, marca Chedraui
- VERDE (#00FF88) - Estados OK, conexión establecida, checks
- CYAN  (#00C8FF) - Instrucciones, límites, alertas, bloqueos
- NEGRO (fondo)   - Fondo siempre negro
- GRIS            - Elementos secundarios, sombras

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
CEDIS Cancún 427 - Tiendas Chedraui
===============================================================================
"""

from __future__ import print_function
import sys
import os
import time
import threading
from datetime import datetime

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTES DE COLOR (PALETA CHEDRAUI)
# ═══════════════════════════════════════════════════════════════════════════════

class Colores:
    """Colores corporativos Chedraui para terminal"""

    # Colores principales (RGB)
    ROJO  = '\033[38;2;227;24;55m'     # #E31837 - Marca Chedraui
    VERDE = '\033[38;2;0;255;136m'     # #00FF88 - OK/Éxito
    CYAN  = '\033[38;2;0;200;255m'     # #00C8FF - Info/Alertas

    # Fondos
    BG_NEGRO = '\033[40m'              # Fondo negro (predeterminado)

    # Grises
    GRIS_OSCURO = '\033[38;2;64;64;64m'      # #404040
    GRIS_MEDIO  = '\033[38;2;128;128;128m'   # #808080
    GRIS_CLARO  = '\033[38;2;192;192;192m'   # #C0C0C0

    # Especiales
    NEGRITA = '\033[1m'
    TENUE   = '\033[2m'
    SUBRAYADO = '\033[4m'
    PARPADEO  = '\033[5m'
    INVERSO   = '\033[7m'

    # Reset
    RESET = '\033[0m'
    CLEAR_LINE = '\033[2K'
    CLEAR_SCREEN = '\033[2J\033[H'

    # Cursor
    OCULTAR_CURSOR = '\033[?25l'
    MOSTRAR_CURSOR = '\033[?25h'

    @staticmethod
    def mover_cursor(fila, columna):
        """Mueve el cursor a posición específica"""
        return f'\033[{fila};{columna}H'

    @staticmethod
    def mover_arriba(n=1):
        """Mueve cursor n líneas arriba"""
        return f'\033[{n}A'

    @staticmethod
    def mover_abajo(n=1):
        """Mueve cursor n líneas abajo"""
        return f'\033[{n}B'

    @staticmethod
    def guardar_cursor():
        """Guarda posición del cursor"""
        return '\033[s'

    @staticmethod
    def restaurar_cursor():
        """Restaura posición del cursor"""
        return '\033[u'


# ═══════════════════════════════════════════════════════════════════════════════
# ARTE ASCII - LOGO Y BANNERS
# ═══════════════════════════════════════════════════════════════════════════════

class ArteASCII:
    """Colección de arte ASCII para la interfaz"""

    LOGO_SACITY = [
        "  ███████╗ █████╗  ██████╗██╗████████╗██╗   ██╗",
        "  ██╔════╝██╔══██╗██╔════╝██║╚══██╔══╝╚██╗ ██╔╝",
        "  ███████╗███████║██║     ██║   ██║    ╚████╔╝ ",
        "  ╚════██║██╔══██║██║     ██║   ██║     ╚██╔╝  ",
        "  ███████║██║  ██║╚██████╗██║   ██║      ██║   ",
        "  ╚══════╝╚═╝  ╚═╝ ╚═════╝╚═╝   ╚═╝      ╚═╝   ",
    ]

    LOGO_PEQUENO = [
        "  ╔═══╗ ╔═══╗ ╔═══╗ ══╗ ╔══╗ ╦   ╦",
        "  ╚═══╗ ║   ║ ║     ║ ║ ║  ║ ╚╗ ╔╝",
        "  ╚═══╝ ╚═══╝ ╚═══╝ ╩ ╩ ╩  ╩  ╚═╝ ",
    ]

    ICONO_MC9190 = [
        "  ┌────────┐",
        "  │ ▀▀▀▀▀▀ │",
        "  │ ██████ │",
        "  │ ██████ │",
        "  │ ██████ │",
        "  │ [SCAN] │",
        "  └────────┘",
    ]

    ICONO_CONECTANDO = [
        "  ⣾⣿⣿⣿⣿⣿⣿⣷",
        "  ⣿⣿⣿⣿⣿⣿⣿⣿",
        "  ⣿⣿⡿⠿⠿⢿⣿⣿",
        "  ⣿⡿      ⢿⣿",
        "  ⣿⣿⣄    ⣠⣿⣿",
        "  ⠙⠿⠿⠿⠿⠿⠿⠟⠋",
    ]

    SPINNER_FRAMES = [
        "⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"
    ]

    BARRA_PROGRESO = {
        'vacio': '░',
        'lleno': '█',
        'mitad': '▓',
    }

    CAJAS = {
        'esquina_si': '╔',
        'esquina_sd': '╗',
        'esquina_ii': '╚',
        'esquina_id': '╝',
        'horizontal': '═',
        'vertical': '║',
        't_superior': '╦',
        't_inferior': '╩',
        't_izquierda': '╠',
        't_derecha': '╣',
        'cruz': '╬',
    }

    ICONOS = {
        'ok': '✓',
        'error': '✗',
        'warning': '⚠',
        'info': 'ℹ',
        'bullet': '•',
        'flecha_derecha': '→',
        'flecha_izquierda': '←',
        'flecha_arriba': '↑',
        'flecha_abajo': '↓',
        'estrella': '★',
        'corazon': '♥',
        'rombo': '◆',
        'circulo': '●',
        'cuadrado': '■',
    }


# ═══════════════════════════════════════════════════════════════════════════════
# ANIMACIONES
# ═══════════════════════════════════════════════════════════════════════════════

class Animador:
    """Sistema de animaciones para la interfaz"""

    def __init__(self):
        self._animaciones_activas = []
        self._lock = threading.Lock()

    @staticmethod
    def efecto_escribir(texto, color=Colores.ROJO, delay=0.03):
        """Efecto de escritura carácter por carácter"""
        resultado = []
        for char in texto:
            resultado.append(char)
            sys.stdout.write(color + char + Colores.RESET)
            sys.stdout.flush()
            time.sleep(delay)
        return ''.join(resultado)

    @staticmethod
    def efecto_parpadeo(texto, color=Colores.ROJO, veces=3, delay=0.5):
        """Efecto de parpadeo"""
        for _ in range(veces):
            sys.stdout.write('\r' + color + texto + Colores.RESET)
            sys.stdout.flush()
            time.sleep(delay)
            sys.stdout.write('\r' + ' ' * len(texto))
            sys.stdout.flush()
            time.sleep(delay)
        sys.stdout.write('\r' + color + texto + Colores.RESET + '\n')
        sys.stdout.flush()

    @staticmethod
    def spinner(texto, color=Colores.CYAN, duracion=2.0):
        """Spinner animado"""
        frames = ArteASCII.SPINNER_FRAMES
        inicio = time.time()
        i = 0

        sys.stdout.write(Colores.OCULTAR_CURSOR)

        try:
            while time.time() - inicio < duracion:
                frame = frames[i % len(frames)]
                sys.stdout.write('\r' + color + frame + ' ' + texto + Colores.RESET)
                sys.stdout.flush()
                time.sleep(0.1)
                i += 1
        finally:
            sys.stdout.write('\r' + Colores.CLEAR_LINE)
            sys.stdout.write(Colores.MOSTRAR_CURSOR)
            sys.stdout.flush()

    @staticmethod
    def barra_progreso(actual, total, ancho=40, texto='', color=Colores.VERDE):
        """Barra de progreso animada"""
        porcentaje = int((actual / total) * 100)
        lleno = int((actual / total) * ancho)
        vacio = ancho - lleno

        barra = (ArteASCII.BARRA_PROGRESO['lleno'] * lleno +
                 ArteASCII.BARRA_PROGRESO['vacio'] * vacio)

        sys.stdout.write('\r' + color +
                        f'[{barra}] {porcentaje}% ' +
                        texto + Colores.RESET)
        sys.stdout.flush()

        if actual >= total:
            sys.stdout.write('\n')

    @staticmethod
    def animacion_logo(logo_lineas, color=Colores.ROJO, delay=0.1):
        """Anima logo línea por línea"""
        for linea in logo_lineas:
            print(color + linea + Colores.RESET)
            time.sleep(delay)

    @staticmethod
    def efecto_onda(texto, color=Colores.CYAN, veces=2):
        """Efecto de onda sobre el texto"""
        for _ in range(veces):
            for i in range(len(texto)):
                linea = []
                for j, char in enumerate(texto):
                    if abs(j - i) < 3:
                        linea.append(color + Colores.NEGRITA + char + Colores.RESET)
                    else:
                        linea.append(color + char + Colores.RESET)
                sys.stdout.write('\r' + ''.join(linea))
                sys.stdout.flush()
                time.sleep(0.05)
        sys.stdout.write('\n')


# ═══════════════════════════════════════════════════════════════════════════════
# COMPONENTES DE UI
# ═══════════════════════════════════════════════════════════════════════════════

class Caja:
    """Componente de caja con bordes"""

    @staticmethod
    def crear(ancho, alto, titulo='', color_borde=Colores.ROJO, color_titulo=Colores.ROJO):
        """Crea una caja con bordes"""
        c = ArteASCII.CAJAS

        # Línea superior
        if titulo:
            titulo_fmt = f' {titulo} '
            padding = (ancho - len(titulo) - 2) // 2
            linea_superior = (c['esquina_si'] + c['horizontal'] * padding +
                            color_titulo + titulo_fmt + color_borde +
                            c['horizontal'] * (ancho - padding - len(titulo) - 2) +
                            c['esquina_sd'])
        else:
            linea_superior = c['esquina_si'] + c['horizontal'] * (ancho - 2) + c['esquina_sd']

        # Líneas medias
        linea_media = c['vertical'] + ' ' * (ancho - 2) + c['vertical']

        # Línea inferior
        linea_inferior = c['esquina_ii'] + c['horizontal'] * (ancho - 2) + c['esquina_id']

        # Construir caja
        lineas = [color_borde + linea_superior + Colores.RESET]
        lineas.extend([color_borde + linea_media + Colores.RESET] * (alto - 2))
        lineas.append(color_borde + linea_inferior + Colores.RESET)

        return lineas

    @staticmethod
    def con_contenido(ancho, contenido, titulo='', color_borde=Colores.ROJO,
                     color_contenido=Colores.GRIS_CLARO, padding=2):
        """Crea caja con contenido centrado"""
        alto = len(contenido) + 2 + (padding * 2)
        caja = Caja.crear(ancho, alto, titulo, color_borde)

        # Insertar contenido
        inicio_contenido = 1 + padding
        for i, linea in enumerate(contenido):
            if inicio_contenido + i < len(caja) - 1:
                espacios_izq = (ancho - len(linea) - 2) // 2
                linea_fmt = (color_borde + ArteASCII.CAJAS['vertical'] +
                           ' ' * espacios_izq +
                           color_contenido + linea +
                           color_borde +
                           ' ' * (ancho - len(linea) - espacios_izq - 2) +
                           ArteASCII.CAJAS['vertical'] + Colores.RESET)
                caja[inicio_contenido + i] = linea_fmt

        return caja


class PanelEstado:
    """Panel de estado con información en tiempo real"""

    def __init__(self, ancho=80):
        self.ancho = ancho
        self.items = {}

    def actualizar(self, clave, valor, estado='info'):
        """Actualiza un ítem del panel"""
        self.items[clave] = {'valor': valor, 'estado': estado}

    def renderizar(self):
        """Renderiza el panel"""
        lineas = []

        # Cabecera
        lineas.append(Colores.ROJO + '═' * self.ancho + Colores.RESET)
        lineas.append(Colores.ROJO + '  ESTADO DEL SISTEMA'.center(self.ancho) + Colores.RESET)
        lineas.append(Colores.ROJO + '═' * self.ancho + Colores.RESET)

        # Items
        for clave, info in self.items.items():
            valor = info['valor']
            estado = info['estado']

            # Color según estado
            if estado == 'ok':
                color = Colores.VERDE
                icono = ArteASCII.ICONOS['ok']
            elif estado == 'error':
                color = Colores.CYAN
                icono = ArteASCII.ICONOS['error']
            elif estado == 'warning':
                color = Colores.CYAN
                icono = ArteASCII.ICONOS['warning']
            else:
                color = Colores.GRIS_CLARO
                icono = ArteASCII.ICONOS['info']

            linea = f'  {color}{icono}{Colores.RESET} {Colores.GRIS_CLARO}{clave}:{Colores.RESET} {color}{valor}{Colores.RESET}'
            lineas.append(linea)

        lineas.append(Colores.ROJO + '═' * self.ancho + Colores.RESET)

        return '\n'.join(lineas)


class Menu:
    """Menú interactivo con navegación"""

    def __init__(self, titulo, opciones, ancho=60):
        self.titulo = titulo
        self.opciones = opciones  # Lista de tuplas (clave, texto)
        self.ancho = ancho
        self.seleccion = 0

    def renderizar(self, fila_inicio=5):
        """Renderiza el menú"""
        output = []

        # Limpiar pantalla
        output.append(Colores.CLEAR_SCREEN)

        # Logo pequeño
        for i, linea in enumerate(ArteASCII.LOGO_PEQUENO):
            output.append(Colores.mover_cursor(i + 1, (80 - 50) // 2))
            output.append(Colores.ROJO + linea + Colores.RESET)

        # Título
        output.append(Colores.mover_cursor(fila_inicio, 0))
        output.append(Colores.ROJO + Colores.NEGRITA +
                     self.titulo.center(80) + Colores.RESET)
        output.append(Colores.ROJO + '═' * 80 + Colores.RESET)

        # Opciones
        for i, (clave, texto) in enumerate(self.opciones):
            fila = fila_inicio + 2 + i
            output.append(Colores.mover_cursor(fila, 10))

            if i == self.seleccion:
                # Opción seleccionada
                output.append(Colores.VERDE + Colores.NEGRITA +
                            f'  ► [{clave}] {texto}' + Colores.RESET)
            else:
                # Opción normal
                output.append(Colores.GRIS_CLARO +
                            f'    [{clave}] {texto}' + Colores.RESET)

        # Instrucciones
        fila_instrucciones = fila_inicio + 3 + len(self.opciones)
        output.append(Colores.mover_cursor(fila_instrucciones, 0))
        output.append(Colores.CYAN + '─' * 80 + Colores.RESET)
        output.append(Colores.mover_cursor(fila_instrucciones + 1, 10))
        output.append(Colores.CYAN +
                     'Presione el número de la opción o [Q] para salir' +
                     Colores.RESET)

        return ''.join(output)

    def mostrar(self):
        """Muestra el menú y espera selección"""
        print(self.renderizar())

        while True:
            try:
                entrada = input('\n' + Colores.VERDE + '  Opción: ' + Colores.RESET).strip().upper()

                if entrada == 'Q':
                    return None

                # Buscar opción
                for clave, texto in self.opciones:
                    if str(clave).upper() == entrada:
                        return clave

                print(Colores.CYAN + '  ⚠ Opción no válida' + Colores.RESET)
            except (KeyboardInterrupt, EOFError):
                return None


class Notificacion:
    """Sistema de notificaciones"""

    @staticmethod
    def exito(mensaje, ancho=60):
        """Notificación de éxito"""
        print()
        print(Colores.VERDE + '  ' + ArteASCII.ICONOS['ok'] + '  ' + mensaje + Colores.RESET)
        print(Colores.VERDE + '  ' + '─' * (ancho - 4) + Colores.RESET)
        print()

    @staticmethod
    def error(mensaje, ancho=60):
        """Notificación de error"""
        print()
        print(Colores.CYAN + '  ' + ArteASCII.ICONOS['error'] + '  ' + mensaje + Colores.RESET)
        print(Colores.CYAN + '  ' + '─' * (ancho - 4) + Colores.RESET)
        print()

    @staticmethod
    def advertencia(mensaje, ancho=60):
        """Notificación de advertencia"""
        print()
        print(Colores.CYAN + '  ' + ArteASCII.ICONOS['warning'] + '  ' + mensaje + Colores.RESET)
        print(Colores.CYAN + '  ' + '─' * (ancho - 4) + Colores.RESET)
        print()

    @staticmethod
    def info(mensaje, ancho=60):
        """Notificación informativa"""
        print()
        print(Colores.GRIS_CLARO + '  ' + ArteASCII.ICONOS['info'] + '  ' + mensaje + Colores.RESET)
        print(Colores.GRIS_CLARO + '  ' + '─' * (ancho - 4) + Colores.RESET)
        print()


# ═══════════════════════════════════════════════════════════════════════════════
# PANTALLAS PRINCIPALES
# ═══════════════════════════════════════════════════════════════════════════════

class PantallaBienvenida:
    """Pantalla de bienvenida animada"""

    @staticmethod
    def mostrar():
        """Muestra pantalla de bienvenida con animación"""
        print(Colores.CLEAR_SCREEN)
        print(Colores.OCULTAR_CURSOR)

        try:
            # Logo animado
            print('\n\n')
            Animador.animacion_logo(ArteASCII.LOGO_SACITY, Colores.ROJO, 0.08)

            print()
            Animador.efecto_escribir(
                '  Emulador Telnet/Velocity para Symbol MC9190  '.center(80),
                Colores.GRIS_CLARO,
                0.02
            )
            print()
            print()

            # Información
            info = [
                'CEDIS Cancún 427',
                'Tiendas Chedraui S.A. de C.V.',
                'Versión 1.0.0',
            ]

            for linea in info:
                print(Colores.GRIS_MEDIO + linea.center(80) + Colores.RESET)
                time.sleep(0.3)

            print('\n\n')

            # Spinner de inicialización
            Animador.spinner('Inicializando sistema', Colores.CYAN, 2.0)

            print(Colores.VERDE + '\n  ✓ Sistema listo\n' + Colores.RESET)
            time.sleep(1)

        finally:
            print(Colores.MOSTRAR_CURSOR)


class PantallaConexion:
    """Pantalla de conexión con animación"""

    @staticmethod
    def mostrar(host, puerto):
        """Muestra proceso de conexión"""
        print(Colores.CLEAR_SCREEN)

        # Cabecera
        print()
        print(Colores.ROJO + '═' * 80 + Colores.RESET)
        print(Colores.ROJO + '  CONECTANDO AL SERVIDOR WMS  '.center(80) + Colores.RESET)
        print(Colores.ROJO + '═' * 80 + Colores.RESET)
        print()

        # Información de conexión
        print(Colores.GRIS_CLARO + f'  Servidor: {host}' + Colores.RESET)
        print(Colores.GRIS_CLARO + f'  Puerto:   {puerto}' + Colores.RESET)
        print()

        # Pasos de conexión
        pasos = [
            ('Resolviendo nombre del host', 1.0),
            ('Estableciendo conexión TCP', 1.5),
            ('Negociando opciones Telnet', 1.0),
            ('Inicializando terminal VT100', 0.8),
            ('Sincronizando sesión', 0.5),
        ]

        for paso, duracion in pasos:
            Animador.spinner(paso, Colores.CYAN, duracion)
            print(Colores.VERDE + f'  ✓ {paso}' + Colores.RESET)

        print()
        Notificacion.exito('Conexión establecida correctamente')
        time.sleep(1)


class PantallaEstado:
    """Pantalla de estado del sistema"""

    def __init__(self):
        self.panel = PanelEstado(80)
        self.actualizando = False
        self._thread = None

    def iniciar(self):
        """Inicia actualización automática"""
        self.actualizando = True
        self._thread = threading.Thread(target=self._actualizar_loop)
        self._thread.daemon = True
        self._thread.start()

    def detener(self):
        """Detiene actualización"""
        self.actualizando = False

    def _actualizar_loop(self):
        """Loop de actualización"""
        while self.actualizando:
            # Actualizar datos
            self.panel.actualizar('Hora', datetime.now().strftime('%H:%M:%S'), 'info')
            self.panel.actualizar('Conexión', 'ACTIVA', 'ok')
            self.panel.actualizar('Servidor', '192.168.1.1:23', 'ok')
            self.panel.actualizar('Terminal', 'VT100', 'info')
            self.panel.actualizar('Escáner', 'HABILITADO', 'ok')

            # Mostrar
            print(Colores.CLEAR_SCREEN)
            print(self.panel.renderizar())

            time.sleep(1)

    def mostrar(self):
        """Muestra panel de estado"""
        print(Colores.CLEAR_SCREEN)
        print(self.panel.renderizar())


# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIONES DE UTILIDAD
# ═══════════════════════════════════════════════════════════════════════════════

def limpiar_pantalla():
    """Limpia la pantalla"""
    print(Colores.CLEAR_SCREEN)


def pausar(mensaje='Presione ENTER para continuar'):
    """Pausa la ejecución"""
    try:
        input('\n' + Colores.CYAN + mensaje + Colores.RESET)
    except (KeyboardInterrupt, EOFError):
        pass


def confirmar(mensaje='¿Continuar?'):
    """Pide confirmación"""
    try:
        respuesta = input(Colores.CYAN + mensaje + ' (S/N): ' + Colores.RESET).strip().upper()
        return respuesta in ('S', 'Y', 'SI', 'YES')
    except (KeyboardInterrupt, EOFError):
        return False


# ═══════════════════════════════════════════════════════════════════════════════
# DEMO / TESTING
# ═══════════════════════════════════════════════════════════════════════════════

def demo_completa():
    """Demostración completa de la interfaz"""

    # 1. Pantalla de bienvenida
    PantallaBienvenida.mostrar()

    # 2. Menú principal
    menu = Menu(
        'MENÚ PRINCIPAL',
        [
            ('1', 'Conectar al servidor WMS'),
            ('2', 'Configuración'),
            ('3', 'Estado del sistema'),
            ('4', 'Acerca de'),
            ('0', 'Salir'),
        ]
    )

    opcion = menu.mostrar()

    if opcion == '1':
        # 3. Pantalla de conexión
        PantallaConexion.mostrar('192.168.1.1', 23)

        # 4. Panel de estado
        pantalla_estado = PantallaEstado()
        pantalla_estado.mostrar()
        pausar()

    elif opcion == '3':
        # Panel de estado en tiempo real
        pantalla_estado = PantallaEstado()
        pantalla_estado.iniciar()
        time.sleep(5)
        pantalla_estado.detener()

    # 5. Notificaciones
    Notificacion.info('Esta es una notificación informativa')
    time.sleep(1)
    Notificacion.exito('Operación completada con éxito')
    time.sleep(1)
    Notificacion.advertencia('Advertencia: batería baja')
    time.sleep(1)

    # 6. Despedida
    limpiar_pantalla()
    print('\n\n')
    print(Colores.ROJO + ArteASCII.LOGO_PEQUENO[1].center(80) + Colores.RESET)
    print()
    print(Colores.GRIS_CLARO + 'Gracias por usar SACITY'.center(80) + Colores.RESET)
    print('\n\n')


if __name__ == '__main__':
    try:
        demo_completa()
    except KeyboardInterrupt:
        print('\n\n' + Colores.CYAN + 'Interrumpido por usuario' + Colores.RESET)
    finally:
        print(Colores.MOSTRAR_CURSOR)
        print(Colores.RESET)
