#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
===============================================================================
SACITY - EMULADOR TELNET/VELOCITY PARA SYMBOL MC9190
===============================================================================

Aplicación principal que integra todos los componentes:
- Interfaz gráfica ASCII con colores Chedraui
- Shell emulador VT100/VT220
- Cliente Telnet con reconexión automática
- Soporte de escáner de códigos de barras

PALETA DE COLORES CHEDRAUI:
- ROJO  (#E31837) - Marca, menús, cabeceras
- VERDE (#00FF88) - Estados OK, conexiones establecidas
- CYAN  (#00C8FF) - Alertas, instrucciones, límites
- NEGRO (fondo)   - Fondo siempre negro
- GRIS            - Elementos secundarios

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún 427
===============================================================================
"""

from __future__ import print_function
import sys
import os
import time
import json
import threading
from datetime import datetime

# Importar componentes SACITY
try:
    from sacity_ui import (
        Colores, ArteASCII, Animador, Caja, Menu, PanelEstado,
        Notificacion, PantallaBienvenida, PantallaConexion, PantallaEstado,
        limpiar_pantalla, pausar, confirmar
    )
    from sacity_shell import SacityShell, BufferPantalla, GestorSesionTelnet
except ImportError:
    print("Error: No se pueden importar componentes SACITY")
    print("Asegúrese de que sacity_ui.py y sacity_shell.py están en el mismo directorio")
    sys.exit(1)


# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTES
# ═══════════════════════════════════════════════════════════════════════════════

VERSION = "1.0.0"
NOMBRE_APP = "SACITY"
CEDIS = "CEDIS Cancún 427"
EMPRESA = "Tiendas Chedraui S.A. de C.V."

# Rutas de configuración
RUTAS_CONFIG = [
    'sacity_config.json',
    '/Application/sacity_config.json',
    '/Program Files/SACITY/config.json',
    '\\Application\\sacity_config.json',
    '\\Program Files\\SACITY\\config.json',
]

# Configuración por defecto
CONFIG_DEFECTO = {
    'version': VERSION,
    'servidor': {
        'host': '192.168.1.1',
        'puerto': 23,
        'timeout': 30,
    },
    'terminal': {
        'filas': 24,
        'columnas': 80,
        'tipo': 'VT100',
    },
    'escaner': {
        'habilitado': True,
        'sufijo': '\r',
        'beep': True,
    },
    'sesion': {
        'reconexion_auto': True,
        'reconexion_intentos': 5,
        'reconexion_delay': 5,
        'heartbeat_intervalo': 30,
    },
    'interfaz': {
        'animaciones': True,
        'pantalla_completa': True,
        'mostrar_estado': True,
    }
}


# ═══════════════════════════════════════════════════════════════════════════════
# GESTOR DE CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════════════════════

class GestorConfiguracion:
    """Gestiona la configuración de la aplicación"""

    def __init__(self):
        self.config = CONFIG_DEFECTO.copy()
        self.archivo_config = None

    def cargar(self):
        """Carga configuración desde archivo"""
        for ruta in RUTAS_CONFIG:
            try:
                with open(ruta, 'r') as f:
                    config_archivo = json.load(f)
                    self._fusionar_config(config_archivo)
                    self.archivo_config = ruta
                    return True
            except:
                continue

        # No se encontró archivo, usar configuración por defecto
        return False

    def guardar(self, ruta=None):
        """Guarda configuración a archivo"""
        ruta = ruta or self.archivo_config or RUTAS_CONFIG[0]

        try:
            # Crear directorio si no existe
            directorio = os.path.dirname(ruta)
            if directorio and not os.path.exists(directorio):
                os.makedirs(directorio)

            with open(ruta, 'w') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)

            self.archivo_config = ruta
            return True

        except Exception as e:
            return False

    def _fusionar_config(self, config_nueva):
        """Fusiona configuración nueva con la existente"""
        def fusionar_dict(dest, src):
            for key, value in src.items():
                if key in dest and isinstance(dest[key], dict) and isinstance(value, dict):
                    fusionar_dict(dest[key], value)
                else:
                    dest[key] = value

        fusionar_dict(self.config, config_nueva)

    def obtener(self, ruta, defecto=None):
        """Obtiene valor de configuración por ruta (e.g., 'servidor.host')"""
        partes = ruta.split('.')
        valor = self.config

        for parte in partes:
            if isinstance(valor, dict) and parte in valor:
                valor = valor[parte]
            else:
                return defecto

        return valor

    def establecer(self, ruta, valor):
        """Establece valor de configuración por ruta"""
        partes = ruta.split('.')
        config = self.config

        for i, parte in enumerate(partes[:-1]):
            if parte not in config:
                config[parte] = {}
            config = config[parte]

        config[partes[-1]] = valor


# ═══════════════════════════════════════════════════════════════════════════════
# APLICACIÓN PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

class AplicacionSacity:
    """Aplicación principal SACITY"""

    def __init__(self):
        self.gestor_config = GestorConfiguracion()
        self.shell = None
        self.ejecutando = False

    def iniciar(self):
        """Inicia la aplicación"""
        # Cargar configuración
        self.gestor_config.cargar()

        # Mostrar pantalla de bienvenida
        if self.gestor_config.obtener('interfaz.animaciones', True):
            PantallaBienvenida.mostrar()

        # Mostrar menú principal
        self._menu_principal()

    def _menu_principal(self):
        """Menú principal de la aplicación"""
        while True:
            menu = Menu(
                'MENÚ PRINCIPAL - SACITY',
                [
                    ('1', 'Conectar al servidor WMS'),
                    ('2', 'Configuración'),
                    ('3', 'Estado del sistema'),
                    ('4', 'Prueba de conexión'),
                    ('5', 'Acerca de'),
                    ('0', 'Salir'),
                ]
            )

            opcion = menu.mostrar()

            if opcion == '1':
                self._conectar_servidor()
            elif opcion == '2':
                self._menu_configuracion()
            elif opcion == '3':
                self._mostrar_estado()
            elif opcion == '4':
                self._probar_conexion()
            elif opcion == '5':
                self._acerca_de()
            elif opcion == '0' or opcion is None:
                if confirmar('¿Seguro que desea salir?'):
                    break

        # Despedida
        self._despedida()

    def _conectar_servidor(self):
        """Conecta al servidor WMS y ejecuta shell"""
        limpiar_pantalla()

        # Obtener configuración
        host = self.gestor_config.obtener('servidor.host')
        puerto = self.gestor_config.obtener('servidor.puerto')
        timeout = self.gestor_config.obtener('servidor.timeout')

        # Mostrar pantalla de conexión
        PantallaConexion.mostrar(host, puerto)

        # Crear shell
        config_shell = {
            'host': host,
            'puerto': puerto,
            'timeout': timeout,
            'filas': self.gestor_config.obtener('terminal.filas'),
            'columnas': self.gestor_config.obtener('terminal.columnas'),
            'escaner_habilitado': self.gestor_config.obtener('escaner.habilitado'),
            'escaner_sufijo': self.gestor_config.obtener('escaner.sufijo'),
            'reconexion_auto': self.gestor_config.obtener('sesion.reconexion_auto'),
            'heartbeat_intervalo': self.gestor_config.obtener('sesion.heartbeat_intervalo'),
        }

        self.shell = SacityShell(config_shell)

        # Ejecutar shell
        try:
            self.shell.ejecutar_interactivo()
        except Exception as e:
            Notificacion.error(f'Error en shell: {e}')
            pausar()

    def _menu_configuracion(self):
        """Menú de configuración"""
        while True:
            limpiar_pantalla()

            print()
            print(Colores.ROJO + '═' * 80 + Colores.RESET)
            print(Colores.ROJO + '  CONFIGURACIÓN  '.center(80) + Colores.RESET)
            print(Colores.ROJO + '═' * 80 + Colores.RESET)
            print()

            # Mostrar configuración actual
            print(Colores.GRIS_CLARO + '  Servidor WMS:'.ljust(30) +
                  Colores.VERDE + self.gestor_config.obtener('servidor.host') + Colores.RESET)
            print(Colores.GRIS_CLARO + '  Puerto:'.ljust(30) +
                  Colores.VERDE + str(self.gestor_config.obtener('servidor.puerto')) + Colores.RESET)
            print(Colores.GRIS_CLARO + '  Terminal:'.ljust(30) +
                  Colores.VERDE + self.gestor_config.obtener('terminal.tipo') + Colores.RESET)
            print(Colores.GRIS_CLARO + '  Escáner:'.ljust(30) +
                  Colores.VERDE + ('HABILITADO' if self.gestor_config.obtener('escaner.habilitado') else 'DESHABILITADO') +
                  Colores.RESET)
            print(Colores.GRIS_CLARO + '  Reconexión automática:'.ljust(30) +
                  Colores.VERDE + ('SÍ' if self.gestor_config.obtener('sesion.reconexion_auto') else 'NO') +
                  Colores.RESET)

            print()
            print(Colores.CYAN + '─' * 80 + Colores.RESET)
            print()

            menu = Menu(
                '',
                [
                    ('1', 'Cambiar servidor WMS'),
                    ('2', 'Cambiar puerto'),
                    ('3', 'Configurar escáner'),
                    ('4', 'Opciones de sesión'),
                    ('5', 'Guardar configuración'),
                    ('0', 'Volver'),
                ],
                ancho=80
            )

            opcion = menu.mostrar()

            if opcion == '1':
                self._cambiar_servidor()
            elif opcion == '2':
                self._cambiar_puerto()
            elif opcion == '3':
                self._configurar_escaner()
            elif opcion == '4':
                self._opciones_sesion()
            elif opcion == '5':
                if self.gestor_config.guardar():
                    Notificacion.exito('Configuración guardada correctamente')
                else:
                    Notificacion.error('Error al guardar configuración')
                pausar()
            elif opcion == '0' or opcion is None:
                break

    def _cambiar_servidor(self):
        """Cambia servidor WMS"""
        limpiar_pantalla()

        print()
        print(Colores.ROJO + '  CONFIGURAR SERVIDOR WMS  ' + Colores.RESET)
        print(Colores.CYAN + '─' * 80 + Colores.RESET)
        print()

        actual = self.gestor_config.obtener('servidor.host')
        print(Colores.GRIS_CLARO + f'  Servidor actual: {actual}' + Colores.RESET)
        print()

        try:
            nuevo = input(Colores.VERDE + '  Nuevo servidor (Enter para cancelar): ' + Colores.RESET).strip()

            if nuevo:
                self.gestor_config.establecer('servidor.host', nuevo)
                Notificacion.exito(f'Servidor cambiado a: {nuevo}')
            else:
                Notificacion.info('Cambio cancelado')

        except (KeyboardInterrupt, EOFError):
            Notificacion.info('Cambio cancelado')

        pausar()

    def _cambiar_puerto(self):
        """Cambia puerto"""
        limpiar_pantalla()

        print()
        print(Colores.ROJO + '  CONFIGURAR PUERTO  ' + Colores.RESET)
        print(Colores.CYAN + '─' * 80 + Colores.RESET)
        print()

        actual = self.gestor_config.obtener('servidor.puerto')
        print(Colores.GRIS_CLARO + f'  Puerto actual: {actual}' + Colores.RESET)
        print()

        try:
            nuevo = input(Colores.VERDE + '  Nuevo puerto (Enter para cancelar): ' + Colores.RESET).strip()

            if nuevo:
                try:
                    puerto = int(nuevo)
                    if 1 <= puerto <= 65535:
                        self.gestor_config.establecer('servidor.puerto', puerto)
                        Notificacion.exito(f'Puerto cambiado a: {puerto}')
                    else:
                        Notificacion.error('Puerto inválido (debe estar entre 1 y 65535)')
                except ValueError:
                    Notificacion.error('Puerto inválido (debe ser un número)')
            else:
                Notificacion.info('Cambio cancelado')

        except (KeyboardInterrupt, EOFError):
            Notificacion.info('Cambio cancelado')

        pausar()

    def _configurar_escaner(self):
        """Configura escáner"""
        limpiar_pantalla()

        print()
        print(Colores.ROJO + '  CONFIGURAR ESCÁNER  ' + Colores.RESET)
        print(Colores.CYAN + '─' * 80 + Colores.RESET)
        print()

        habilitado = self.gestor_config.obtener('escaner.habilitado')
        print(Colores.GRIS_CLARO + '  Estado actual: ' + Colores.VERDE +
              ('HABILITADO' if habilitado else 'DESHABILITADO') + Colores.RESET)
        print()

        if confirmar('¿Cambiar estado del escáner?'):
            self.gestor_config.establecer('escaner.habilitado', not habilitado)
            Notificacion.exito('Estado del escáner cambiado')
        else:
            Notificacion.info('Cambio cancelado')

        pausar()

    def _opciones_sesion(self):
        """Configura opciones de sesión"""
        limpiar_pantalla()

        print()
        print(Colores.ROJO + '  OPCIONES DE SESIÓN  ' + Colores.RESET)
        print(Colores.CYAN + '─' * 80 + Colores.RESET)
        print()

        reconexion = self.gestor_config.obtener('sesion.reconexion_auto')
        heartbeat = self.gestor_config.obtener('sesion.heartbeat_intervalo')

        print(Colores.GRIS_CLARO + '  Reconexión automática: ' + Colores.VERDE +
              ('SÍ' if reconexion else 'NO') + Colores.RESET)
        print(Colores.GRIS_CLARO + f'  Intervalo heartbeat: {heartbeat}s' + Colores.RESET)
        print()

        if confirmar('¿Cambiar reconexión automática?'):
            self.gestor_config.establecer('sesion.reconexion_auto', not reconexion)
            Notificacion.exito('Reconexión automática cambiada')

        pausar()

    def _mostrar_estado(self):
        """Muestra estado del sistema"""
        pantalla_estado = PantallaEstado()
        pantalla_estado.iniciar()

        print()
        pausar('Presione ENTER para volver al menú')

        pantalla_estado.detener()

    def _probar_conexion(self):
        """Prueba conexión al servidor"""
        limpiar_pantalla()

        print()
        print(Colores.ROJO + '═' * 80 + Colores.RESET)
        print(Colores.ROJO + '  PRUEBA DE CONEXIÓN  '.center(80) + Colores.RESET)
        print(Colores.ROJO + '═' * 80 + Colores.RESET)
        print()

        host = self.gestor_config.obtener('servidor.host')
        puerto = self.gestor_config.obtener('servidor.puerto')
        timeout = self.gestor_config.obtener('servidor.timeout')

        print(Colores.GRIS_CLARO + f'  Servidor: {host}' + Colores.RESET)
        print(Colores.GRIS_CLARO + f'  Puerto:   {puerto}' + Colores.RESET)
        print()

        # Probar conexión
        Animador.spinner('Probando conexión', Colores.CYAN, 2.0)

        sesion = GestorSesionTelnet(host, puerto, timeout)

        if sesion.conectar(reintentos=1):
            Notificacion.exito('Conexión exitosa')
            sesion.desconectar()
        else:
            Notificacion.error('No se pudo conectar al servidor')

        pausar()

    def _acerca_de(self):
        """Muestra información acerca de"""
        limpiar_pantalla()

        print()
        print()

        # Logo
        for linea in ArteASCII.LOGO_SACITY:
            print(Colores.ROJO + linea.center(80) + Colores.RESET)

        print()
        print(Colores.GRIS_CLARO + f'Versión {VERSION}'.center(80) + Colores.RESET)
        print()
        print()

        # Información
        info = [
            '',
            'Emulador Telnet/Velocity para Symbol MC9190',
            '',
            CEDIS,
            EMPRESA,
            '',
            'Desarrollado por:',
            'Julián Alexander Juárez Alvarado (ADMJAJA)',
            'Jefe de Sistemas',
            '',
            '© 2025 Tiendas Chedraui S.A. de C.V.',
            'Todos los derechos reservados',
            '',
        ]

        for linea in info:
            print(Colores.GRIS_MEDIO + linea.center(80) + Colores.RESET)

        print()
        print()

        pausar()

    def _despedida(self):
        """Muestra pantalla de despedida"""
        limpiar_pantalla()

        print()
        print()
        print()

        for linea in ArteASCII.LOGO_PEQUENO:
            print(Colores.ROJO + linea.center(80) + Colores.RESET)
            time.sleep(0.1)

        print()
        print()
        print(Colores.GRIS_CLARO + 'Gracias por usar SACITY'.center(80) + Colores.RESET)
        print(Colores.GRIS_MEDIO + f'{CEDIS} - {EMPRESA}'.center(80) + Colores.RESET)
        print()
        print()


# ═══════════════════════════════════════════════════════════════════════════════
# PUNTO DE ENTRADA
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Punto de entrada principal"""
    try:
        app = AplicacionSacity()
        app.iniciar()

    except KeyboardInterrupt:
        print()
        print(Colores.CYAN + '\n  Interrumpido por usuario\n' + Colores.RESET)

    except Exception as e:
        print()
        print(Colores.CYAN + f'\n  Error: {e}\n' + Colores.RESET)

    finally:
        print(Colores.MOSTRAR_CURSOR)
        print(Colores.RESET)


if __name__ == '__main__':
    main()
