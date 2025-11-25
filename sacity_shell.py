#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SACITY SHELL (dhell) - Main Entry Point
El shell minimalista y optimizado para MC9190.
"""

import sys
import time
import os
import msvcrt  # Solo para Windows/WinCE

# Asegurar que podemos importar módulos locales
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dhell import ui_templates
from dhell.comms import SacityComms
from dhell.wavelink_parser import WavelinkConfig
from dhell.config import get_current_config, should_disable_animations

# Configuración Global
CONFIG = get_current_config()

def main():
    # 1. Inicialización Visual
    if not should_disable_animations():
        ui_templates.banner_arranque()
        time.sleep(1.0 * CONFIG['speed_multiplier'])
    else:
        print("SACITY OS - Modo Seguro (Batería Baja)")

    # 2. Cargar Configuración de Conexión
    print("\n>>> Cargando configuración legacy...")
    wl_config = WavelinkConfig()
    
    # Intentar buscar archivos en la carpeta actual o bin
    posibles_rutas = [
        "WLTelnetCE_9000PPC.reg",
        "bin/WLTelnetCE_9000PPC.reg",
        "../bin/WLTelnetCE_9000PPC.reg"
    ]
    
    config_cargada = False
    for ruta in posibles_rutas:
        if os.path.exists(ruta):
            if wl_config.load_from_reg_file(ruta):
                print(f">>> Configuración encontrada en {ruta}")
                config_cargada = True
                break
    
    if not config_cargada:
        print(">>> No se encontró configuración Wavelink. Usando defaults.")
    
    conn_details = wl_config.get_connection_details()
    host = conn_details['host']
    port = conn_details['port']

    # 3. Iniciar Comunicaciones
    comms = SacityComms()
    
    print(f">>> Conectando a {host}:{port}...")
    if not should_disable_animations():
        ui_templates.barra_progreso(10)
    
    if comms.conectar(host, port):
        if not should_disable_animations():
            ui_templates.barra_progreso(100)
            time.sleep(0.5)
            ui_templates.limpiar_pantalla()
        
        print(f"CONECTADO A {host}")
        
        # 4. Bucle Principal del Shell
        try:
            while True:
                # 4.1 Leer del socket (No bloqueante)
                datos = comms.recibir(timeout=0.1)
                if datos:
                    # Decodificar y mostrar
                    try:
                        texto = datos.decode('utf-8', errors='replace')
                        sys.stdout.write(texto)
                        sys.stdout.flush()
                    except:
                        pass
                
                # 4.2 Leer del teclado (No bloqueante)
                if msvcrt.kbhit():
                    tecla = msvcrt.getch()
                    
                    # Manejo de teclas especiales
                    if tecla == b'\x03': # Ctrl+C
                        break
                    
                    # Enviar al host
                    comms.enviar(tecla)
                    
                    # Eco local (opcional, depende del host)
                    # sys.stdout.write(tecla.decode('utf-8', errors='ignore'))
                    # sys.stdout.flush()
                
                # 4.3 Verificar estado
                if not comms.connected:
                    ui_templates.alerta_critica()
                    print(">>> Conexión perdida. Reintentando en 3s...")
                    time.sleep(3)
                    if comms.conectar(host, port):
                        ui_templates.reconexion_exitosa()
                    else:
                        pass

        except KeyboardInterrupt:
            print("\n>>> Cerrando sesión...")
        finally:
            comms.desconectar()
    else:
        ui_templates.alerta_critica()
        print(f">>> No se pudo conectar a {host}:{port}")
        print(">>> Presione cualquier tecla para salir.")
        msvcrt.getch()

if __name__ == "__main__":
    main()
