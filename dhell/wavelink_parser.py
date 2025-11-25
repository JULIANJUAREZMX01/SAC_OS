"""
SACITY OS - Wavelink Configuration Parser
Este módulo extrae la configuración de conexión (Host, Puerto, Emulación)
de los archivos de configuración legacy de Wavelink TelnetCE.
"""

import os
import struct
import re

class WavelinkConfig:
    def __init__(self):
        self.host = "127.0.0.1"
        self.port = 23
        self.emulation = "VT100"
        self.auto_login = False
        self.username = ""
        self.password = ""

    def load_from_reg_file(self, filepath):
        """Intenta leer configuración de un archivo .reg exportado"""
        if not os.path.exists(filepath):
            return False
            
        try:
            with open(filepath, 'r', encoding='utf-16-le', errors='ignore') as f:
                content = f.read()
                
            # Buscar Host
            # "HostName"="192.168.1.100"
            host_match = re.search(r'"Host(Name|Address)"="([^"]+)"', content, re.IGNORECASE)
            if host_match:
                self.host = host_match.group(2)
                
            # Buscar Puerto
            # "TcpPort"=dword:00000017
            port_match = re.search(r'"TcpPort"=dword:([0-9a-fA-F]+)', content)
            if port_match:
                self.port = int(port_match.group(1), 16)
                
            return True
        except Exception as e:
            print(f"Error leyendo .reg: {e}")
            return False

    def load_from_bin(self, filepath):
        """
        Intenta leer configuración binaria (HostCfg.bin).
        NOTA: Esto es ingeniería inversa básica, la estructura real puede variar.
        """
        # Placeholder: En una implementación real, decodificaríamos el struct binario
        # de Wavelink. Por ahora, retornamos False para usar defaults o .reg
        return False

    def get_connection_details(self):
        return {
            'host': self.host,
            'port': self.port,
            'type': 'telnet'
        }
