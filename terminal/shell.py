#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
===============================================================================
SACITY SHELL - EMULADOR DE TERMINAL VT100/VT220
Sistema de Automatización para Emulador Telnet
===============================================================================

Shell completo con emulación VT100/VT220, manejo de sesión telnet,
integración de escáner y reconexión automática.

CARACTERÍSTICAS:
- Emulación completa VT100/VT220
- Buffer de pantalla con procesamiento de escape sequences
- Manejo de teclado y escáner de códigos de barras
- Reconexión automática con backoff exponencial
- Heartbeat para mantener sesión activa
- Integración con interfaz gráfica ASCII

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
CEDIS Cancún 427 - Tiendas Chedraui
===============================================================================
"""

from __future__ import print_function
import sys
import os
import time
import socket
import threading
import json
from datetime import datetime
from collections import deque

try:
    from sacity_ui import Colores, ArteASCII, Animador, Notificacion
except ImportError:
    # Fallback si no está disponible
    class Colores:
        RESET = '\033[0m'
        ROJO = '\033[31m'
        VERDE = '\033[32m'
        CYAN = '\033[36m'
        CLEAR_SCREEN = '\033[2J\033[H'
        OCULTAR_CURSOR = '\033[?25l'
        MOSTRAR_CURSOR = '\033[?25h'


# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTES
# ═══════════════════════════════════════════════════════════════════════════════

VERSION = "1.0.0"

# Códigos de control VT100
ESC = '\x1b'
CSI = ESC + '['
OSC = ESC + ']'
BEL = '\x07'
BS = '\x08'
HT = '\x09'
LF = '\x0a'
VT = '\x0b'
FF = '\x0c'
CR = '\x0d'

# Teclas especiales
KEY_UP = '\x1b[A'
KEY_DOWN = '\x1b[B'
KEY_RIGHT = '\x1b[C'
KEY_LEFT = '\x1b[D'
KEY_HOME = '\x1b[H'
KEY_END = '\x1b[F'
KEY_PGUP = '\x1b[5~'
KEY_PGDN = '\x1b[6~'
KEY_INSERT = '\x1b[2~'
KEY_DELETE = '\x1b[3~'
KEY_F1 = '\x1bOP'
KEY_F2 = '\x1bOQ'
KEY_F3 = '\x1bOR'
KEY_F4 = '\x1bOS'


# ═══════════════════════════════════════════════════════════════════════════════
# BUFFER DE PANTALLA VT100
# ═══════════════════════════════════════════════════════════════════════════════

class BufferPantalla:
    """
    Buffer de pantalla con soporte completo VT100/VT220.

    Mantiene una matriz de caracteres y atributos, procesa secuencias
    de escape, y maneja el cursor.
    """

    def __init__(self, filas=24, columnas=80):
        self.filas = filas
        self.columnas = columnas

        # Buffer de caracteres
        self.buffer = [[' ' for _ in range(columnas)] for _ in range(filas)]

        # Atributos por celda (color, negrita, etc.)
        self.atributos = [[{} for _ in range(columnas)] for _ in range(filas)]

        # Estado del cursor
        self.cursor_fila = 0
        self.cursor_columna = 0
        self.cursor_visible = True

        # Atributos actuales del texto
        self.attr_negrita = False
        self.attr_tenue = False
        self.attr_subrayado = False
        self.attr_parpadeo = False
        self.attr_inverso = False
        self.attr_color_fg = 37  # Blanco por defecto
        self.attr_color_bg = 40  # Negro por defecto

        # Modo de inserción
        self.modo_insercion = False

        # Regiones de scroll
        self.scroll_top = 0
        self.scroll_bottom = filas - 1

        # Buffer de secuencias de escape
        self._escape_buffer = []
        self._en_escape = False

        # Bandera de actualización
        self.actualizado = True

        # Lock para thread safety
        self._lock = threading.Lock()

    def escribir(self, data):
        """Escribe datos al buffer procesando secuencias VT100"""
        with self._lock:
            if isinstance(data, bytes):
                try:
                    data = data.decode('utf-8', errors='ignore')
                except:
                    data = data.decode('latin-1', errors='ignore')

            for char in data:
                self._procesar_caracter(char)

            self.actualizado = True

    def _procesar_caracter(self, char):
        """Procesa un carácter individual"""
        if self._en_escape:
            self._procesar_escape(char)
            return

        # Caracteres de control
        if char == ESC:
            self._en_escape = True
            self._escape_buffer = []
            return
        elif char == CR:
            self.cursor_columna = 0
            return
        elif char == LF or char == VT or char == FF:
            self._nueva_linea()
            return
        elif char == BS:
            if self.cursor_columna > 0:
                self.cursor_columna -= 1
            return
        elif char == HT:
            # Tab: mover a siguiente múltiplo de 8
            self.cursor_columna = ((self.cursor_columna // 8) + 1) * 8
            if self.cursor_columna >= self.columnas:
                self.cursor_columna = self.columnas - 1
            return
        elif char == BEL:
            # Beep (ignorar por ahora)
            return

        # Carácter imprimible
        if ord(char) >= 32:
            self._poner_caracter(char)

    def _procesar_escape(self, char):
        """Procesa secuencia de escape"""
        self._escape_buffer.append(char)

        # CSI sequence
        if len(self._escape_buffer) == 1:
            if char == '[':
                return  # Continuar acumulando
            elif char == ']':
                return  # OSC sequence
            else:
                # Secuencia simple
                self._ejecutar_escape_simple(char)
                self._en_escape = False
                self._escape_buffer = []
                return

        # OSC sequence
        if self._escape_buffer[0] == ']':
            # Esperar BEL o ESC\
            if char == BEL or (char == '\\' and len(self._escape_buffer) > 1 and
                              self._escape_buffer[-2] == ESC):
                self._ejecutar_osc()
                self._en_escape = False
                self._escape_buffer = []
            return

        # CSI sequence continuación
        if self._escape_buffer[0] == '[':
            # Verificar si es comando final
            if char.isalpha() or char in '@`':
                self._ejecutar_csi()
                self._en_escape = False
                self._escape_buffer = []
            elif len(self._escape_buffer) > 32:
                # Secuencia muy larga, abortar
                self._en_escape = False
                self._escape_buffer = []

    def _ejecutar_escape_simple(self, char):
        """Ejecuta secuencia de escape simple"""
        if char == 'M':  # Reverse Index (scroll down)
            if self.cursor_fila == self.scroll_top:
                self._scroll_down()
            else:
                self.cursor_fila = max(0, self.cursor_fila - 1)
        elif char == 'D':  # Index (scroll up)
            if self.cursor_fila == self.scroll_bottom:
                self._scroll_up()
            else:
                self.cursor_fila = min(self.filas - 1, self.cursor_fila + 1)
        elif char == 'E':  # Next Line
            self._nueva_linea()
        elif char == 'c':  # Reset
            self.resetear()
        elif char == '7':  # Save cursor
            self._cursor_guardado = (self.cursor_fila, self.cursor_columna)
        elif char == '8':  # Restore cursor
            if hasattr(self, '_cursor_guardado'):
                self.cursor_fila, self.cursor_columna = self._cursor_guardado

    def _ejecutar_csi(self):
        """Ejecuta secuencia CSI"""
        if len(self._escape_buffer) < 2:
            return

        # Parsear secuencia
        secuencia = ''.join(self._escape_buffer[1:])
        comando = secuencia[-1]
        params_str = secuencia[:-1]

        # Parsear parámetros
        if params_str:
            try:
                params = [int(p) if p else 0 for p in params_str.split(';')]
            except ValueError:
                params = []
        else:
            params = []

        # Ejecutar comando
        if comando == 'H' or comando == 'f':  # Cursor Position
            fila = (params[0] if params else 1) - 1
            col = (params[1] if len(params) > 1 else 1) - 1
            self.cursor_fila = max(0, min(fila, self.filas - 1))
            self.cursor_columna = max(0, min(col, self.columnas - 1))

        elif comando == 'A':  # Cursor Up
            n = params[0] if params else 1
            self.cursor_fila = max(0, self.cursor_fila - n)

        elif comando == 'B':  # Cursor Down
            n = params[0] if params else 1
            self.cursor_fila = min(self.filas - 1, self.cursor_fila + n)

        elif comando == 'C':  # Cursor Forward
            n = params[0] if params else 1
            self.cursor_columna = min(self.columnas - 1, self.cursor_columna + n)

        elif comando == 'D':  # Cursor Back
            n = params[0] if params else 1
            self.cursor_columna = max(0, self.cursor_columna - n)

        elif comando == 'J':  # Erase Display
            modo = params[0] if params else 0
            if modo == 0:  # Cursor to end
                self._borrar_desde_cursor_hasta_fin()
            elif modo == 1:  # Beginning to cursor
                self._borrar_desde_inicio_hasta_cursor()
            elif modo == 2:  # Entire screen
                self.limpiar()

        elif comando == 'K':  # Erase Line
            modo = params[0] if params else 0
            if modo == 0:  # Cursor to end of line
                for c in range(self.cursor_columna, self.columnas):
                    self.buffer[self.cursor_fila][c] = ' '
            elif modo == 1:  # Start to cursor
                for c in range(0, self.cursor_columna + 1):
                    self.buffer[self.cursor_fila][c] = ' '
            elif modo == 2:  # Entire line
                self.buffer[self.cursor_fila] = [' '] * self.columnas

        elif comando == 'm':  # Select Graphic Rendition (SGR)
            if not params:
                params = [0]
            self._procesar_sgr(params)

        elif comando == 'r':  # Set Scrolling Region
            top = (params[0] if params else 1) - 1
            bottom = (params[1] if len(params) > 1 else self.filas) - 1
            self.scroll_top = max(0, min(top, self.filas - 1))
            self.scroll_bottom = max(self.scroll_top, min(bottom, self.filas - 1))

        elif comando == 's':  # Save cursor position
            self._cursor_guardado = (self.cursor_fila, self.cursor_columna)

        elif comando == 'u':  # Restore cursor position
            if hasattr(self, '_cursor_guardado'):
                self.cursor_fila, self.cursor_columna = self._cursor_guardado

        elif comando == 'l':  # Reset Mode
            if params == [25]:
                self.cursor_visible = False

        elif comando == 'h':  # Set Mode
            if params == [25]:
                self.cursor_visible = True

    def _procesar_sgr(self, params):
        """Procesa parámetros SGR (colores y atributos)"""
        i = 0
        while i < len(params):
            param = params[i]

            if param == 0:  # Reset
                self.attr_negrita = False
                self.attr_tenue = False
                self.attr_subrayado = False
                self.attr_parpadeo = False
                self.attr_inverso = False
                self.attr_color_fg = 37
                self.attr_color_bg = 40
            elif param == 1:  # Negrita
                self.attr_negrita = True
            elif param == 2:  # Tenue
                self.attr_tenue = True
            elif param == 4:  # Subrayado
                self.attr_subrayado = True
            elif param == 5:  # Parpadeo
                self.attr_parpadeo = True
            elif param == 7:  # Inverso
                self.attr_inverso = True
            elif param == 22:  # No negrita/tenue
                self.attr_negrita = False
                self.attr_tenue = False
            elif param == 24:  # No subrayado
                self.attr_subrayado = False
            elif param == 25:  # No parpadeo
                self.attr_parpadeo = False
            elif param == 27:  # No inverso
                self.attr_inverso = False
            elif 30 <= param <= 37:  # Foreground color
                self.attr_color_fg = param
            elif 40 <= param <= 47:  # Background color
                self.attr_color_bg = param
            elif param == 39:  # Default foreground
                self.attr_color_fg = 37
            elif param == 49:  # Default background
                self.attr_color_bg = 40
            elif param == 38:  # Extended foreground color
                if i + 2 < len(params) and params[i + 1] == 5:
                    # 256 color
                    self.attr_color_fg = 30 + (params[i + 2] % 8)
                    i += 2
            elif param == 48:  # Extended background color
                if i + 2 < len(params) and params[i + 1] == 5:
                    # 256 color
                    self.attr_color_bg = 40 + (params[i + 2] % 8)
                    i += 2

            i += 1

    def _ejecutar_osc(self):
        """Ejecuta secuencia OSC (Operating System Command)"""
        # Por ahora ignoramos OSC sequences (cambio de título, etc.)
        pass

    def _poner_caracter(self, char):
        """Coloca un carácter en la posición del cursor"""
        if self.cursor_fila >= self.filas or self.cursor_columna >= self.columnas:
            return

        self.buffer[self.cursor_fila][self.cursor_columna] = char

        # Guardar atributos
        self.atributos[self.cursor_fila][self.cursor_columna] = {
            'negrita': self.attr_negrita,
            'tenue': self.attr_tenue,
            'subrayado': self.attr_subrayado,
            'parpadeo': self.attr_parpadeo,
            'inverso': self.attr_inverso,
            'fg': self.attr_color_fg,
            'bg': self.attr_color_bg,
        }

        # Avanzar cursor
        self.cursor_columna += 1

        # Wrap automático
        if self.cursor_columna >= self.columnas:
            self.cursor_columna = 0
            self._nueva_linea()

    def _nueva_linea(self):
        """Procesa nueva línea con scroll si es necesario"""
        self.cursor_fila += 1

        if self.cursor_fila > self.scroll_bottom:
            self._scroll_up()
            self.cursor_fila = self.scroll_bottom

    def _scroll_up(self):
        """Scroll hacia arriba (contenido sube)"""
        # Eliminar primera línea de región
        self.buffer.pop(self.scroll_top)
        self.atributos.pop(self.scroll_top)

        # Agregar línea vacía al final de región
        self.buffer.insert(self.scroll_bottom, [' '] * self.columnas)
        self.atributos.insert(self.scroll_bottom, [{} for _ in range(self.columnas)])

    def _scroll_down(self):
        """Scroll hacia abajo (contenido baja)"""
        # Eliminar última línea de región
        self.buffer.pop(self.scroll_bottom)
        self.atributos.pop(self.scroll_bottom)

        # Agregar línea vacía al inicio de región
        self.buffer.insert(self.scroll_top, [' '] * self.columnas)
        self.atributos.insert(self.scroll_top, [{} for _ in range(self.columnas)])

    def _borrar_desde_cursor_hasta_fin(self):
        """Borra desde cursor hasta fin de pantalla"""
        # Línea actual desde cursor
        for c in range(self.cursor_columna, self.columnas):
            self.buffer[self.cursor_fila][c] = ' '

        # Líneas siguientes
        for f in range(self.cursor_fila + 1, self.filas):
            self.buffer[f] = [' '] * self.columnas

    def _borrar_desde_inicio_hasta_cursor(self):
        """Borra desde inicio hasta cursor"""
        # Líneas anteriores
        for f in range(0, self.cursor_fila):
            self.buffer[f] = [' '] * self.columnas

        # Línea actual hasta cursor
        for c in range(0, self.cursor_columna + 1):
            self.buffer[self.cursor_fila][c] = ' '

    def limpiar(self):
        """Limpia el buffer completo"""
        with self._lock:
            self.buffer = [[' ' for _ in range(self.columnas)] for _ in range(self.filas)]
            self.atributos = [[{} for _ in range(self.columnas)] for _ in range(self.filas)]
            self.cursor_fila = 0
            self.cursor_columna = 0
            self.actualizado = True

    def resetear(self):
        """Resetea el buffer al estado inicial"""
        self.limpiar()
        self.attr_negrita = False
        self.attr_tenue = False
        self.attr_subrayado = False
        self.attr_parpadeo = False
        self.attr_inverso = False
        self.attr_color_fg = 37
        self.attr_color_bg = 40
        self.cursor_visible = True
        self.scroll_top = 0
        self.scroll_bottom = self.filas - 1

    def obtener_linea(self, fila):
        """Obtiene una línea como string"""
        with self._lock:
            if 0 <= fila < self.filas:
                return ''.join(self.buffer[fila])
            return ''

    def obtener_pantalla(self):
        """Obtiene toda la pantalla como string"""
        with self._lock:
            lineas = [''.join(fila) for fila in self.buffer]
            return '\n'.join(lineas)

    def obtener_pantalla_con_cursor(self):
        """Obtiene pantalla con indicador de cursor"""
        with self._lock:
            lineas = []
            for f in range(self.filas):
                linea = []
                for c in range(self.columnas):
                    char = self.buffer[f][c]

                    # Marcar posición del cursor
                    if f == self.cursor_fila and c == self.cursor_columna and self.cursor_visible:
                        linea.append(Colores.VERDE + Colores.NEGRITA + char + Colores.RESET)
                    else:
                        linea.append(char)

                lineas.append(''.join(linea))

            return '\n'.join(lineas)


# ═══════════════════════════════════════════════════════════════════════════════
# GESTOR DE SESIÓN TELNET
# ═══════════════════════════════════════════════════════════════════════════════

class GestorSesionTelnet:
    """
    Gestor completo de sesión Telnet con reconexión automática
    """

    def __init__(self, host, puerto, timeout=30):
        self.host = host
        self.puerto = puerto
        self.timeout = timeout

        self.socket = None
        self.conectado = False

        # Estadísticas
        self.intentos_conexion = 0
        self.ultima_actividad = None
        self.bytes_enviados = 0
        self.bytes_recibidos = 0

        # Opciones Telnet (RFC 854)
        self.IAC = 255
        self.DONT = 254
        self.DO = 253
        self.WONT = 252
        self.WILL = 251
        self.SB = 250
        self.SE = 240

        # Opciones comunes
        self.ECHO = 1
        self.SGA = 3
        self.TTYPE = 24
        self.NAWS = 31
        self.LINEMODE = 34

        # Lock
        self._lock = threading.Lock()

    def conectar(self, reintentos=3):
        """Conecta al servidor con reintentos"""
        for intento in range(reintentos):
            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.settimeout(self.timeout)
                self.socket.connect((self.host, self.puerto))

                self.conectado = True
                self.intentos_conexion += 1
                self.ultima_actividad = time.time()

                # Negociar opciones
                self._negociar_opciones()

                return True

            except Exception as e:
                if intento < reintentos - 1:
                    delay = 2 ** intento  # Backoff exponencial
                    time.sleep(delay)
                else:
                    return False

        return False

    def desconectar(self):
        """Desconecta del servidor"""
        try:
            if self.socket:
                self.socket.close()
        except:
            pass

        self.socket = None
        self.conectado = False

    def _negociar_opciones(self):
        """Negocia opciones Telnet"""
        try:
            # WILL TTYPE (indicar que soportamos tipo de terminal)
            self._enviar_comando([self.IAC, self.WILL, self.TTYPE])

            # DO SGA (solicitar Suppress Go Ahead)
            self._enviar_comando([self.IAC, self.DO, self.SGA])

            # WILL NAWS (indicar que soportamos tamaño de ventana)
            self._enviar_comando([self.IAC, self.WILL, self.NAWS])

            # Enviar tamaño de ventana (24x80)
            self._enviar_naws(80, 24)

        except:
            pass

    def _enviar_comando(self, bytes_comando):
        """Envía comando Telnet"""
        if self.socket:
            try:
                self.socket.send(bytearray(bytes_comando))
            except:
                pass

    def _enviar_naws(self, ancho, alto):
        """Envía tamaño de ventana"""
        comando = [
            self.IAC, self.SB, self.NAWS,
            (ancho >> 8) & 0xFF, ancho & 0xFF,
            (alto >> 8) & 0xFF, alto & 0xFF,
            self.IAC, self.SE
        ]
        self._enviar_comando(comando)

    def enviar(self, datos):
        """Envía datos al servidor"""
        if not self.conectado or not self.socket:
            return False

        try:
            with self._lock:
                if isinstance(datos, str):
                    datos = datos.encode('utf-8', errors='ignore')

                self.socket.sendall(datos)
                self.bytes_enviados += len(datos)
                self.ultima_actividad = time.time()

            return True

        except Exception as e:
            self.conectado = False
            return False

    def recibir(self, timeout=0.1):
        """Recibe datos del servidor"""
        if not self.conectado or not self.socket:
            return None

        try:
            self.socket.settimeout(timeout)
            datos = self.socket.recv(4096)

            if datos:
                self.bytes_recibidos += len(datos)
                self.ultima_actividad = time.time()

                # Filtrar comandos Telnet
                datos_filtrados = self._filtrar_comandos_telnet(datos)
                return datos_filtrados

            return b''

        except socket.timeout:
            return b''

        except Exception as e:
            self.conectado = False
            return None

    def _filtrar_comandos_telnet(self, datos):
        """Filtra comandos Telnet de los datos"""
        resultado = bytearray()
        i = 0

        while i < len(datos):
            if datos[i] == self.IAC and i + 1 < len(datos):
                cmd = datos[i + 1]

                if cmd == self.IAC:
                    # IAC IAC = literal IAC
                    resultado.append(self.IAC)
                    i += 2

                elif cmd in (self.DO, self.DONT, self.WILL, self.WONT):
                    # Comando de 3 bytes
                    if i + 2 < len(datos):
                        opt = datos[i + 2]
                        self._responder_opcion(cmd, opt)
                        i += 3
                    else:
                        i += 2

                elif cmd == self.SB:
                    # Subnegociación - buscar SE
                    se_pos = datos.find(bytes([self.IAC, self.SE]), i)
                    if se_pos != -1:
                        self._procesar_subnegociacion(datos[i+2:se_pos])
                        i = se_pos + 2
                    else:
                        i += 2

                else:
                    # Otro comando
                    i += 2

            else:
                resultado.append(datos[i])
                i += 1

        return bytes(resultado)

    def _responder_opcion(self, cmd, opt):
        """Responde a solicitud de opción"""
        try:
            if cmd == self.DO:
                # Servidor solicita que hagamos algo
                if opt in (self.TTYPE, self.NAWS, self.SGA):
                    self._enviar_comando([self.IAC, self.WILL, opt])
                else:
                    self._enviar_comando([self.IAC, self.WONT, opt])

            elif cmd == self.WILL:
                # Servidor hará algo
                if opt in (self.ECHO, self.SGA):
                    self._enviar_comando([self.IAC, self.DO, opt])
                else:
                    self._enviar_comando([self.IAC, self.DONT, opt])

        except:
            pass

    def _procesar_subnegociacion(self, datos):
        """Procesa subnegociación"""
        if len(datos) >= 1:
            opt = datos[0]

            if opt == self.TTYPE and len(datos) >= 2 and datos[1] == 1:
                # Enviar tipo de terminal
                ttype = b'VT100'
                respuesta = [self.IAC, self.SB, self.TTYPE, 0] + list(ttype) + [self.IAC, self.SE]
                self._enviar_comando(respuesta)

    def esta_activo(self):
        """Verifica si la conexión está activa"""
        if not self.conectado:
            return False

        # Verificar timeout de actividad
        if self.ultima_actividad:
            tiempo_inactivo = time.time() - self.ultima_actividad
            if tiempo_inactivo > self.timeout:
                return False

        return True


# ═══════════════════════════════════════════════════════════════════════════════
# SHELL PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

class SacityShell:
    """
    Shell completo de emulación con integración de todos los componentes
    """

    def __init__(self, config):
        self.config = config

        # Componentes
        self.buffer = BufferPantalla(
            filas=config.get('filas', 24),
            columnas=config.get('columnas', 80)
        )

        self.sesion = GestorSesionTelnet(
            host=config.get('host', '192.168.1.1'),
            puerto=config.get('puerto', 23),
            timeout=config.get('timeout', 30)
        )

        # Estado
        self.ejecutando = False
        self.modo_local = False  # Modo local vs remoto

        # Threads
        self._thread_recepcion = None
        self._thread_heartbeat = None
        self._thread_renderizado = None

        # Cola de entrada
        self._cola_entrada = deque()
        self._lock_entrada = threading.Lock()

        # Configuración de escáner
        self.escaner_habilitado = config.get('escaner_habilitado', True)
        self.escaner_sufijo = config.get('escaner_sufijo', '\r')

        # Configuración de reconexión
        self.reconexion_auto = config.get('reconexion_auto', True)
        self.heartbeat_intervalo = config.get('heartbeat_intervalo', 30)

    def conectar(self):
        """Conecta al servidor"""
        print(Colores.CYAN + '\n  Conectando a {}:{}...\n'.format(
            self.config['host'], self.config['puerto']) + Colores.RESET)

        if self.sesion.conectar(reintentos=3):
            print(Colores.VERDE + '  ✓ Conectado correctamente\n' + Colores.RESET)
            return True
        else:
            print(Colores.CYAN + '  ✗ Error de conexión\n' + Colores.RESET)
            return False

    def desconectar(self):
        """Desconecta del servidor"""
        self.ejecutando = False
        self.sesion.desconectar()

    def iniciar(self):
        """Inicia el shell"""
        if not self.sesion.conectado:
            if not self.conectar():
                return False

        self.ejecutando = True

        # Iniciar threads
        self._thread_recepcion = threading.Thread(target=self._loop_recepcion)
        self._thread_recepcion.daemon = True
        self._thread_recepcion.start()

        if self.heartbeat_intervalo > 0:
            self._thread_heartbeat = threading.Thread(target=self._loop_heartbeat)
            self._thread_heartbeat.daemon = True
            self._thread_heartbeat.start()

        self._thread_renderizado = threading.Thread(target=self._loop_renderizado)
        self._thread_renderizado.daemon = True
        self._thread_renderizado.start()

        return True

    def detener(self):
        """Detiene el shell"""
        self.ejecutando = False
        self.desconectar()

        # Esperar threads
        if self._thread_recepcion:
            self._thread_recepcion.join(timeout=2)
        if self._thread_heartbeat:
            self._thread_heartbeat.join(timeout=2)
        if self._thread_renderizado:
            self._thread_renderizado.join(timeout=2)

    def _loop_recepcion(self):
        """Loop de recepción de datos del servidor"""
        while self.ejecutando and self.sesion.conectado:
            try:
                datos = self.sesion.recibir(timeout=0.1)

                if datos is None:
                    # Error de conexión
                    break

                if datos:
                    # Escribir al buffer
                    self.buffer.escribir(datos)

            except Exception as e:
                break

        # Reconexión automática
        if self.ejecutando and self.reconexion_auto:
            self._reconectar()

    def _loop_heartbeat(self):
        """Loop de heartbeat para mantener conexión activa"""
        while self.ejecutando and self.sesion.conectado:
            time.sleep(self.heartbeat_intervalo)

            if self.ejecutando:
                # Enviar NUL como heartbeat
                self.sesion.enviar(b'\x00')

    def _loop_renderizado(self):
        """Loop de renderizado de pantalla"""
        ultimo_renderizado = ''

        while self.ejecutando:
            if self.buffer.actualizado:
                contenido = self.buffer.obtener_pantalla_con_cursor()

                if contenido != ultimo_renderizado:
                    # Limpiar y mostrar
                    print(Colores.CLEAR_SCREEN)
                    print(contenido)

                    ultimo_renderizado = contenido
                    self.buffer.actualizado = False

            time.sleep(0.05)  # 20 FPS

    def _reconectar(self):
        """Reconexión automática con backoff exponencial"""
        delay = 2

        while self.ejecutando:
            print(Colores.CYAN + '\n  Reconectando en {} segundos...\n'.format(delay) + Colores.RESET)
            time.sleep(delay)

            if self.conectar():
                # Reiniciar thread de recepción
                self._thread_recepcion = threading.Thread(target=self._loop_recepcion)
                self._thread_recepcion.daemon = True
                self._thread_recepcion.start()
                break

            delay = min(delay * 2, 60)  # Máximo 60 segundos

    def enviar_tecla(self, tecla):
        """Envía una tecla al servidor"""
        if isinstance(tecla, str):
            self.sesion.enviar(tecla.encode('utf-8'))
        else:
            self.sesion.enviar(tecla)

    def enviar_escaneo(self, codigo):
        """Envía código de barras escaneado"""
        datos = codigo + self.escaner_sufijo
        self.sesion.enviar(datos.encode('utf-8'))

    def ejecutar_interactivo(self):
        """Ejecuta shell en modo interactivo"""
        if not self.iniciar():
            return

        print(Colores.OCULTAR_CURSOR)

        try:
            while self.ejecutando:
                # Leer entrada del usuario
                try:
                    # Nota: En producción, usar msvcrt (Windows) o termios (Linux)
                    # para leer teclas sin esperar Enter
                    entrada = input()

                    if entrada.upper() == 'QUIT':
                        break

                    # Enviar al servidor
                    self.enviar_tecla(entrada + '\r')

                except EOFError:
                    break

        except KeyboardInterrupt:
            print(Colores.CYAN + '\n\nInterrumpido por usuario\n' + Colores.RESET)

        finally:
            print(Colores.MOSTRAR_CURSOR)
            self.detener()


# ═══════════════════════════════════════════════════════════════════════════════
# DEMO / TESTING
# ═══════════════════════════════════════════════════════════════════════════════

def demo_shell():
    """Demostración del shell"""
    config = {
        'host': '192.168.1.1',
        'puerto': 23,
        'timeout': 30,
        'filas': 24,
        'columnas': 80,
        'escaner_habilitado': True,
        'escaner_sufijo': '\r',
        'reconexion_auto': True,
        'heartbeat_intervalo': 30,
    }

    shell = SacityShell(config)
    shell.ejecutar_interactivo()


if __name__ == '__main__':
    try:
        demo_shell()
    except Exception as e:
        print(f'\nError: {e}')
    finally:
        print(Colores.RESET)
