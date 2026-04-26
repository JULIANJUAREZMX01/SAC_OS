#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
===============================================================================
SACITY CLIENT - CLIENTE EMULADOR PARA WINDOWS CE
===============================================================================

Cliente ligero de emulación telnet que corre EN el dispositivo MC9190.
Diseñado para máxima compatibilidad con Windows CE y recursos limitados.

CARACTERÍSTICAS:
- Emulación VT100/VT220 para Manhattan WMS
- Soporte completo de escáner de códigos de barras
- Reconexión automática
- Auto-inicio con el dispositivo
- Bajo consumo de memoria (<2MB)
- Compatible con Python 2.7 y 3.x (para máxima compatibilidad CE)

ARQUITECTURA:
- TelnetClient: Conexión al servidor WMS
- ScreenBuffer: Buffer de pantalla VT100
- ScannerHandler: Integración con escáner
- KeyboardHandler: Mapeo de teclas

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
CEDIS Cancún 427 - Tiendas Chedraui
===============================================================================
"""

from __future__ import print_function  # Compatibilidad Python 2.7

import os
import sys
import socket
import time
import json
import threading
import re

# Intentar importar configuración
try:
    from sacity_config import CONFIG
except ImportError:
    CONFIG = None


# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTES
# ═══════════════════════════════════════════════════════════════════════════════

VERSION = "1.0.0"
NOMBRE = "SACITY Client CE"

# Códigos de escape VT100
ESC = '\x1b'
CSI = ESC + '['

# Secuencias VT100 comunes
VT100_CLEAR = CSI + '2J'
VT100_HOME = CSI + 'H'
VT100_CURSOR_POS = CSI + '{};{}H'

# Colores VT100 (Manhattan WMS usa estos)
VT100_COLORS = {
    'black': 30,
    'red': 31,
    'green': 32,
    'yellow': 33,
    'blue': 34,
    'magenta': 35,
    'cyan': 36,
    'white': 37
}

# Mapeo de teclas especiales MC9190 -> VT100
KEY_MAP = {
    '\x1b[A': 'UP',
    '\x1b[B': 'DOWN',
    '\x1b[C': 'RIGHT',
    '\x1b[D': 'LEFT',
    '\x0d': 'ENTER',
    '\x09': 'TAB',
    '\x1b': 'ESC',
    '\x7f': 'BACKSPACE',
    '\x08': 'BACKSPACE'
}

# Configuración por defecto
DEFAULT_CONFIG = {
    'server': {
        'host': '192.168.1.1',
        'port': 23,
        'timeout': 30
    },
    'display': {
        'rows': 24,
        'cols': 80
    },
    'scanner': {
        'enabled': True,
        'suffix': '\r'
    },
    'session': {
        'reconnect': True,
        'reconnect_delay': 5,
        'heartbeat': 30
    }
}


# ═══════════════════════════════════════════════════════════════════════════════
# CLIENTE TELNET
# ═══════════════════════════════════════════════════════════════════════════════

class TelnetClient:
    """
    Cliente Telnet ligero para Windows CE.

    Implementa protocolo Telnet RFC 854 con soporte VT100.
    """

    def __init__(self, host, port, timeout=30):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.socket = None
        self.connected = False
        self._lock = threading.Lock()

        # Opciones Telnet
        self.IAC = 255  # Interpret As Command
        self.DONT = 254
        self.DO = 253
        self.WONT = 252
        self.WILL = 251
        self.SB = 250
        self.SE = 240
        self.ECHO = 1
        self.SGA = 3  # Suppress Go Ahead
        self.NAWS = 31  # Negotiate About Window Size
        self.TTYPE = 24  # Terminal Type

    def connect(self, retries=3):
        """Conecta al servidor con reintentos"""
        for attempt in range(retries):
            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.settimeout(self.timeout)
                self.socket.connect((self.host, self.port))
                self.connected = True
                self._negotiate_options()
                return True
            except Exception as e:
                if attempt < retries - 1:
                    delay = 2 ** attempt
                    time.sleep(delay)
                else:
                    return False
        return False

    def disconnect(self):
        """Desconecta del servidor"""
        try:
            if self.socket:
                self.socket.close()
        except:
            pass
        self.socket = None
        self.connected = False

    def _negotiate_options(self):
        """Negocia opciones Telnet"""
        # Enviar terminal type
        try:
            # WILL TTYPE
            self.socket.send(bytes([self.IAC, self.WILL, self.TTYPE]))
            # DO SGA
            self.socket.send(bytes([self.IAC, self.DO, self.SGA]))
            # WILL NAWS
            self.socket.send(bytes([self.IAC, self.WILL, self.NAWS]))
        except:
            pass

    def send(self, data):
        """Envía datos al servidor"""
        if not self.connected:
            return False
        try:
            with self._lock:
                if isinstance(data, str):
                    data = data.encode('ascii', errors='ignore')
                self.socket.send(data)
            return True
        except:
            self.connected = False
            return False

    def receive(self, timeout=0.1):
        """Recibe datos del servidor"""
        if not self.connected:
            return None
        try:
            self.socket.settimeout(timeout)
            data = self.socket.recv(4096)
            if data:
                # Filtrar comandos Telnet
                return self._filter_telnet_commands(data)
            return data
        except socket.timeout:
            return b''
        except:
            self.connected = False
            return None

    def _filter_telnet_commands(self, data):
        """Filtra comandos Telnet de los datos"""
        result = []
        i = 0
        while i < len(data):
            if data[i] == self.IAC and i + 2 < len(data):
                cmd = data[i + 1]
                if cmd in (self.DO, self.DONT, self.WILL, self.WONT):
                    # Responder a opciones
                    opt = data[i + 2]
                    self._respond_to_option(cmd, opt)
                    i += 3
                    continue
                elif cmd == self.SB:
                    # Subnegociación - buscar SE
                    se_pos = data.find(bytes([self.IAC, self.SE]), i)
                    if se_pos != -1:
                        i = se_pos + 2
                        continue
            result.append(data[i])
            i += 1
        return bytes(result)

    def _respond_to_option(self, cmd, opt):
        """Responde a solicitudes de opciones Telnet"""
        try:
            if cmd == self.DO:
                # Responder WILL o WONT
                if opt in (self.TTYPE, self.NAWS, self.SGA):
                    self.socket.send(bytes([self.IAC, self.WILL, opt]))
                else:
                    self.socket.send(bytes([self.IAC, self.WONT, opt]))
            elif cmd == self.WILL:
                # Responder DO o DONT
                if opt in (self.ECHO, self.SGA):
                    self.socket.send(bytes([self.IAC, self.DO, opt]))
                else:
                    self.socket.send(bytes([self.IAC, self.DONT, opt]))
        except:
            pass


# ═══════════════════════════════════════════════════════════════════════════════
# BUFFER DE PANTALLA
# ═══════════════════════════════════════════════════════════════════════════════

class ScreenBuffer:
    """
    Buffer de pantalla con soporte VT100.

    Mantiene el estado de la pantalla y procesa secuencias de escape.
    """

    def __init__(self, rows=24, cols=80):
        self.rows = rows
        self.cols = cols
        self.cursor_row = 0
        self.cursor_col = 0
        self.buffer = [[' ' for _ in range(cols)] for _ in range(rows)]
        self.dirty = True
        self._escape_buffer = ''
        self._in_escape = False

    def write(self, data):
        """Escribe datos al buffer procesando secuencias VT100"""
        if isinstance(data, bytes):
            data = data.decode('ascii', errors='ignore')

        for char in data:
            if self._in_escape:
                self._process_escape(char)
            elif char == '\x1b':
                self._in_escape = True
                self._escape_buffer = ''
            elif char == '\r':
                self.cursor_col = 0
            elif char == '\n':
                self._newline()
            elif char == '\b':
                if self.cursor_col > 0:
                    self.cursor_col -= 1
            elif char >= ' ':
                self._put_char(char)

        self.dirty = True

    def _put_char(self, char):
        """Coloca un caracter en la posición actual"""
        if 0 <= self.cursor_row < self.rows and 0 <= self.cursor_col < self.cols:
            self.buffer[self.cursor_row][self.cursor_col] = char
            self.cursor_col += 1
            if self.cursor_col >= self.cols:
                self.cursor_col = 0
                self._newline()

    def _newline(self):
        """Procesa nueva línea"""
        self.cursor_row += 1
        if self.cursor_row >= self.rows:
            # Scroll up
            self.buffer.pop(0)
            self.buffer.append([' ' for _ in range(self.cols)])
            self.cursor_row = self.rows - 1

    def _process_escape(self, char):
        """Procesa secuencia de escape"""
        self._escape_buffer += char

        # CSI sequences
        if self._escape_buffer.startswith('['):
            # Verificar si secuencia completa
            if char.isalpha():
                self._execute_csi(self._escape_buffer)
                self._in_escape = False
                self._escape_buffer = ''
            elif len(self._escape_buffer) > 20:
                # Secuencia muy larga, abortar
                self._in_escape = False
                self._escape_buffer = ''
        elif char == '[':
            pass  # Continuar acumulando
        else:
            # Secuencia simple de escape
            self._in_escape = False
            self._escape_buffer = ''

    def _execute_csi(self, seq):
        """Ejecuta secuencia CSI"""
        # Parsear parámetros
        match = re.match(r'\[(\d*(?:;\d*)*)([A-Za-z])', seq)
        if not match:
            return

        params_str = match.group(1)
        cmd = match.group(2)

        params = [int(p) if p else 0 for p in params_str.split(';')] if params_str else []

        if cmd == 'H' or cmd == 'f':  # Cursor Position
            row = params[0] - 1 if params else 0
            col = params[1] - 1 if len(params) > 1 else 0
            self.cursor_row = max(0, min(row, self.rows - 1))
            self.cursor_col = max(0, min(col, self.cols - 1))

        elif cmd == 'J':  # Erase Display
            mode = params[0] if params else 0
            if mode == 2:  # Clear entire screen
                self.buffer = [[' ' for _ in range(self.cols)] for _ in range(self.rows)]
                self.cursor_row = 0
                self.cursor_col = 0

        elif cmd == 'K':  # Erase Line
            mode = params[0] if params else 0
            if mode == 0:  # Cursor to end
                for i in range(self.cursor_col, self.cols):
                    self.buffer[self.cursor_row][i] = ' '
            elif mode == 2:  # Entire line
                self.buffer[self.cursor_row] = [' ' for _ in range(self.cols)]

        elif cmd == 'A':  # Cursor Up
            n = params[0] if params else 1
            self.cursor_row = max(0, self.cursor_row - n)

        elif cmd == 'B':  # Cursor Down
            n = params[0] if params else 1
            self.cursor_row = min(self.rows - 1, self.cursor_row + n)

        elif cmd == 'C':  # Cursor Forward
            n = params[0] if params else 1
            self.cursor_col = min(self.cols - 1, self.cursor_col + n)

        elif cmd == 'D':  # Cursor Back
            n = params[0] if params else 1
            self.cursor_col = max(0, self.cursor_col - n)

    def get_display(self):
        """Obtiene el contenido del buffer como string"""
        lines = [''.join(row) for row in self.buffer]
        return '\n'.join(lines)

    def clear(self):
        """Limpia el buffer"""
        self.buffer = [[' ' for _ in range(self.cols)] for _ in range(self.rows)]
        self.cursor_row = 0
        self.cursor_col = 0
        self.dirty = True


# ═══════════════════════════════════════════════════════════════════════════════
# MANEJADOR DE ESCÁNER
# ═══════════════════════════════════════════════════════════════════════════════

class ScannerHandler:
    """
    Manejador del escáner de códigos de barras.

    En Windows CE, el escáner funciona como entrada de teclado
    o a través del API de Symbol.
    """

    def __init__(self, suffix='\r'):
        self.suffix = suffix
        self.enabled = True
        self.last_scan = ''
        self.callback = None

    def process_input(self, data):
        """
        Procesa entrada que podría ser del escáner.

        Los escaneos típicamente llegan como texto rápido seguido del sufijo.
        """
        if not self.enabled:
            return data, None

        # Detectar escaneo (entrada rápida + sufijo)
        if self.suffix and data.endswith(self.suffix):
            # Posible escaneo
            scan_data = data[:-len(self.suffix)]
            if len(scan_data) >= 8:  # Códigos típicos tienen 8+ caracteres
                self.last_scan = scan_data
                if self.callback:
                    self.callback(scan_data)
                return '', scan_data

        return data, None

    def set_callback(self, callback):
        """Establece callback para escaneos"""
        self.callback = callback


# ═══════════════════════════════════════════════════════════════════════════════
# CLIENTE SACITY PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

class SacityClient:
    """
    Cliente SACITY principal.

    Integra todos los componentes para emulación completa.
    """

    def __init__(self, config=None):
        self.config = config or DEFAULT_CONFIG

        # Componentes
        self.telnet = TelnetClient(
            host=self.config['server']['host'],
            port=self.config['server']['port'],
            timeout=self.config['server'].get('timeout', 30)
        )

        self.screen = ScreenBuffer(
            rows=self.config['display']['rows'],
            cols=self.config['display']['cols']
        )

        self.scanner = ScannerHandler(
            suffix=self.config['scanner'].get('suffix', '\r')
        )

        # Estado
        self.running = False
        self._receive_thread = None
        self._heartbeat_thread = None

    def connect(self):
        """Conecta al servidor"""
        print("Conectando a {}:{}...".format(
            self.config['server']['host'],
            self.config['server']['port']
        ))

        if self.telnet.connect():
            print("Conectado!")
            self._start_threads()
            return True
        else:
            print("Error de conexion")
            return False

    def disconnect(self):
        """Desconecta del servidor"""
        self.running = False
        self.telnet.disconnect()

    def _start_threads(self):
        """Inicia threads de recepción y heartbeat"""
        self.running = True

        self._receive_thread = threading.Thread(target=self._receive_loop)
        self._receive_thread.daemon = True
        self._receive_thread.start()

        if self.config['session'].get('heartbeat'):
            self._heartbeat_thread = threading.Thread(target=self._heartbeat_loop)
            self._heartbeat_thread.daemon = True
            self._heartbeat_thread.start()

    def _receive_loop(self):
        """Loop de recepción de datos"""
        while self.running and self.telnet.connected:
            try:
                data = self.telnet.receive(timeout=0.1)
                if data:
                    self.screen.write(data)
            except:
                break

        # Reconexión automática
        if self.running and self.config['session'].get('reconnect'):
            self._auto_reconnect()

    def _heartbeat_loop(self):
        """Loop de heartbeat"""
        interval = self.config['session'].get('heartbeat', 30)
        while self.running and self.telnet.connected:
            time.sleep(interval)
            if not self.telnet.send(b'\x00'):  # NUL como heartbeat
                break

    def _auto_reconnect(self):
        """Reconexión automática"""
        delay = self.config['session'].get('reconnect_delay', 5)
        while self.running:
            print("Reconectando en {} segundos...".format(delay))
            time.sleep(delay)
            if self.connect():
                break
            delay = min(delay * 2, 60)  # Max 60 segundos

    def send_key(self, key):
        """Envía tecla al servidor"""
        self.telnet.send(key)

    def send_scan(self, barcode):
        """Envía código de barras al servidor"""
        data = barcode + self.scanner.suffix
        self.telnet.send(data.encode('ascii'))

    def get_screen(self):
        """Obtiene contenido de pantalla"""
        return self.screen.get_display()

    def run_console(self):
        """Ejecuta en modo consola (para testing)"""
        if not self.connect():
            return

        print("\nSACITY Client CE v{}".format(VERSION))
        print("Escriba 'quit' para salir\n")

        try:
            while self.running:
                # Mostrar pantalla
                if self.screen.dirty:
                    os.system('cls' if os.name == 'nt' else 'clear')
                    print(self.get_screen())
                    print("\n" + "-" * self.config['display']['cols'])
                    self.screen.dirty = False

                # Leer entrada
                try:
                    user_input = input()
                    if user_input.lower() == 'quit':
                        break

                    # Verificar si es escaneo
                    processed, scan = self.scanner.process_input(user_input)
                    if scan:
                        self.send_scan(scan)
                    elif processed:
                        self.telnet.send((processed + '\r').encode('ascii'))
                except EOFError:
                    break

        except KeyboardInterrupt:
            print("\nInterrumpido")
        finally:
            self.disconnect()
            print("Desconectado")


# ═══════════════════════════════════════════════════════════════════════════════
# PUNTO DE ENTRADA
# ═══════════════════════════════════════════════════════════════════════════════

def load_config():
    """Carga configuración desde archivo"""
    config_paths = [
        'sacity_config.json',
        '\\Application\\sacity_config.json',
        '\\Program Files\\SACITY\\config.json'
    ]

    for path in config_paths:
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except:
            pass

    return DEFAULT_CONFIG


def main():
    """Punto de entrada principal"""
    print("\n" + "=" * 50)
    print("  SACITY Client CE v{}".format(VERSION))
    print("  Emulador Telnet para Manhattan WMS")
    print("  CEDIS Cancun 427")
    print("=" * 50 + "\n")

    # Cargar configuración
    config = load_config()

    # Parsear argumentos (si disponibles)
    if len(sys.argv) > 1:
        if sys.argv[1] == '--host' and len(sys.argv) > 2:
            config['server']['host'] = sys.argv[2]
        elif sys.argv[1] == '--help':
            print("Uso: sacity_client_ce.py [--host IP] [--port PORT]")
            return

    if len(sys.argv) > 3 and sys.argv[3] == '--port':
        config['server']['port'] = int(sys.argv[4])

    # Crear y ejecutar cliente
    client = SacityClient(config)
    client.run_console()


if __name__ == "__main__":
    main()
