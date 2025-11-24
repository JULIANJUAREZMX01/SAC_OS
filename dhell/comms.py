import socket
import select
import time
import sys

class SacityComms:
    """
    Módulo de comunicaciones ligero y resiliente para SACITY OS.
    Maneja conexiones TCP/Telnet crudas con bajo consumo de recursos.
    """
    def __init__(self):
        self.sock = None
        self.host = None
        self.port = 23
        self.timeout = 5.0
        self.connected = False
        self.buffer_size = 4096

    def conectar(self, host, port=23, timeout=5.0):
        """Establece conexión optimizada con el host"""
        self.host = host
        self.port = port
        self.timeout = timeout
        
        try:
            # Crear socket TCP IPv4
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Opciones para mantener viva la conexión y baja latencia
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            self.sock.settimeout(self.timeout)
            
            self.sock.connect((self.host, self.port))
            self.connected = True
            return True
        except Exception as e:
            self.connected = False
            return f"Error de conexión: {str(e)}"

    def desconectar(self):
        """Cierra la conexión y libera recursos"""
        if self.sock:
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
                self.sock.close()
            except:
                pass
        self.sock = None
        self.connected = False

    def enviar(self, datos):
        """Envía datos crudos al host"""
        if not self.connected or not self.sock:
            return False
        try:
            if isinstance(datos, str):
                datos = datos.encode('utf-8') # O 'ascii'/'latin-1' según el host legacy
            self.sock.sendall(datos)
            return True
        except Exception:
            self.desconectar()
            return False

    def recibir(self, timeout=0.1):
        """
        Lee datos del socket de forma no bloqueante (o con timeout corto).
        Retorna bytes crudos o None si no hay datos/timeout.
        """
        if not self.connected or not self.sock:
            return None
            
        try:
            # Usar select para verificar si hay datos disponibles sin bloquear
            # Esto es más eficiente que settimeout para loops rápidos
            ready_to_read, _, _ = select.select([self.sock], [], [], timeout)
            
            if ready_to_read:
                data = self.sock.recv(self.buffer_size)
                if not data:
                    # Conexión cerrada por el remoto
                    self.desconectar()
                    return None
                return data
            else:
                return b'' # Timeout, no hay datos
        except Exception:
            self.desconectar()
            return None

    def estado(self):
        return {
            "host": self.host,
            "port": self.port,
            "connected": self.connected
        }
