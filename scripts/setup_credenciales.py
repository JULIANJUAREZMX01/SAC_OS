#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════════════════════
MÓDULO DE SETUP INICIAL DE CREDENCIALES
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════════════════════

Setup interactivo para la configuración inicial del sistema con:
✅ Validación de credenciales
✅ Prueba de conexión a BD
✅ Prueba de conexión a Email
✅ Almacenamiento seguro en .env
✅ Interfaz amigable con animaciones

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
═══════════════════════════════════════════════════════════════════════════════
"""

import os
import logging
import sys
import getpass
import time
from pathlib import Path
from typing import Dict, Tuple, Optional
from dotenv import load_dotenv, set_key

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# COLORES
# ═══════════════════════════════════════════════════════════════════════════════

class Colores:
    """Códigos ANSI para colores"""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ROJO = '\033[91m'
    VERDE = '\033[92m'
    AMARILLO = '\033[93m'
    AZUL = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'

    @staticmethod
    def success(msg: str) -> str:
        return f"{Colores.VERDE}✅ {msg}{Colores.RESET}"

    @staticmethod
    def error(msg: str) -> str:
        return f"{Colores.ROJO}❌ {msg}{Colores.RESET}"

    @staticmethod
    def warning(msg: str) -> str:
        return f"{Colores.AMARILLO}⚠️  {msg}{Colores.RESET}"

    @staticmethod
    def info(msg: str) -> str:
        return f"{Colores.CYAN}ℹ️  {msg}{Colores.RESET}"


# ═══════════════════════════════════════════════════════════════════════════════
# GESTOR DE SETUP
# ═══════════════════════════════════════════════════════════════════════════════

class GestorSetupCredenciales:
    """Gestor interactivo del setup inicial"""

    def __init__(self, env_file: Path = None):
        if env_file is None:
            env_file = Path(__file__).parent / '.env'
        self.env_file = env_file
        self.configuracion = {}
        logger.info(f"GestorSetupCredenciales inicializado (env_file={env_file})")

    def mostrar_banner(self):
        """Muestra el banner de bienvenida"""
        banner = f"""
{Colores.AZUL}
╔════════════════════════════════════════════════════════════════════════╗
║                                                                        ║
║              ⚙️  SETUP INICIAL - SAC v1.0.0                          ║
║                                                                        ║
║         Sistema de Automatización de Consultas                         ║
║         CEDIS Cancún 427 - Tiendas Chedraui                          ║
║                                                                        ║
║         Este asistente le guiará a través de la                       ║
║         configuración inicial del sistema.                            ║
║                                                                        ║
╚════════════════════════════════════════════════════════════════════════╝
{Colores.RESET}
        """
        print(banner)
        logger.info("Banner de setup mostrado")

    def mostrar_seccion(self, titulo: str, numero: int = None, total: int = None):
        """Muestra el título de una sección"""
        if numero and total:
            prefijo = f"{Colores.AZUL}[{numero}/{total}]{Colores.RESET} "
        else:
            prefijo = f"{Colores.AZUL}●{Colores.RESET} "

        print(f"\n{prefijo}{Colores.BOLD}{titulo}{Colores.RESET}")
        print("─" * 70)

    def solicitar_entrada(self, prompt: str, valor_default: str = None,
                         ocultar: bool = False, requerido: bool = True) -> str:
        """Solicita una entrada al usuario"""
        while True:
            if valor_default:
                prompt_completo = f"{prompt} [{Colores.CYAN}{valor_default}{Colores.RESET}]: "
            else:
                prompt_completo = f"{prompt}: "

            try:
                if ocultar:
                    valor = getpass.getpass(prompt_completo)
                else:
                    valor = input(prompt_completo).strip()

                # Usar default si está vacío
                if not valor and valor_default:
                    return valor_default

                # Validar que no esté vacío si es requerido
                if requerido and not valor:
                    print(Colores.error("Este campo es requerido"))
                    continue

                return valor

            except KeyboardInterrupt:
                print()
                print(Colores.warning("Setup cancelado por el usuario"))
                sys.exit(1)

    def setup_base_de_datos(self) -> Dict:
        """Setup de credenciales de base de datos"""
        self.mostrar_seccion("CONFIGURACIÓN DE BASE DE DATOS", 1, 4)

        print(Colores.info("Ingrese los datos de conexión a DB2"))
        print("Por defecto, conecta a WM260BASD (Manhattan WMS)")
        print()

        host = self.solicitar_entrada(
            "Host/Servidor DB2",
            valor_default="WM260BASD",
            requerido=True
        )

        puerto = self.solicitar_entrada(
            "Puerto",
            valor_default="50000",
            requerido=True
        )

        usuario = self.solicitar_entrada(
            "Usuario DB2",
            valor_default="ADMJAJA",
            requerido=True
        )

        password = self.solicitar_entrada(
            "Password DB2",
            ocultar=True,
            requerido=True
        )

        print(Colores.success("Credenciales de BD ingresadas"))
        logger.info(f"Credenciales BD configuradas: {usuario}@{host}:{puerto}")

        return {
            'DB_HOST': host,
            'DB_PORT': puerto,
            'DB_USER': usuario,
            'DB_PASSWORD': password,
            'DB_DATABASE': 'WM260BASD',
            'DB_SCHEMA': 'WMWHSE1',
        }

    def setup_email(self) -> Dict:
        """Setup de credenciales de email"""
        self.mostrar_seccion("CONFIGURACIÓN DE EMAIL", 2, 4)

        print(Colores.info("Ingrese los datos para Office 365"))
        print()

        email_user = self.solicitar_entrada(
            "Email de envío",
            valor_default="tu_email@chedraui.com.mx",
            requerido=True
        )

        email_password = self.solicitar_entrada(
            "Password Email",
            ocultar=True,
            requerido=True
        )

        email_to = self.solicitar_entrada(
            "Destinatarios (separados por comas)",
            valor_default="planning@chedraui.com.mx",
            requerido=True
        )

        print(Colores.success("Credenciales de email ingresadas"))
        logger.info(f"Email configurado: {email_user}")

        return {
            'EMAIL_USER': email_user,
            'EMAIL_PASSWORD': email_password,
            'EMAIL_TO': email_to,
            'EMAIL_HOST': 'smtp.office365.com',
            'EMAIL_PORT': '587',
        }

    def setup_cedis(self) -> Dict:
        """Setup de información del CEDIS"""
        self.mostrar_seccion("INFORMACIÓN DEL CEDIS", 3, 4)

        print(Colores.info("Información del Centro de Distribución"))
        print()

        codigo = self.solicitar_entrada(
            "Código CEDIS",
            valor_default="427",
            requerido=True
        )

        nombre = self.solicitar_entrada(
            "Nombre del CEDIS",
            valor_default="CEDIS Cancún",
            requerido=True
        )

        region = self.solicitar_entrada(
            "Región",
            valor_default="Sureste",
            requerido=True
        )

        print(Colores.success("Información del CEDIS configurada"))
        logger.info(f"CEDIS: {codigo} - {nombre} ({region})")

        return {
            'CEDIS_CODE': codigo,
            'CEDIS_NAME': nombre,
            'CEDIS_REGION': region,
            'CEDIS_ALMACEN': 'C22',
        }

    def setup_sistema(self) -> Dict:
        """Setup de configuración general del sistema"""
        self.mostrar_seccion("CONFIGURACIÓN DEL SISTEMA", 4, 4)

        print(Colores.info("Preferencias generales"))
        print()

        debug = self.solicitar_entrada(
            "¿Habilitar modo DEBUG? (s/n)",
            valor_default="n",
            requerido=True
        )

        entorno = self.solicitar_entrada(
            "Entorno (production/development)",
            valor_default="production",
            requerido=True
        )

        print(Colores.success("Configuración del sistema completada"))
        logger.info(f"Sistema: DEBUG={debug}, ENTORNO={entorno}")

        return {
            'DEBUG': 'true' if debug.lower() == 's' else 'false',
            'ENVIRONMENT': entorno,
            'SYSTEM_VERSION': '1.0.0',
        }

    def probar_conexion_bd(self, config: Dict) -> bool:
        """Prueba la conexión a la base de datos"""
        print()
        print(Colores.loading("Probando conexión a BD2..."))
        time.sleep(1)

        try:
            # Intentar importar el módulo de conexión
            from modules.db_connection import DB2Connection

            # Crear conexión con configuración
            db_config = {
                'host': config['DB_HOST'],
                'port': int(config['DB_PORT']),
                'database': config['DB_DATABASE'],
                'user': config['DB_USER'],
                'password': config['DB_PASSWORD'],
            }

            conn = DB2Connection(db_config)
            exito = conn.probar_conexion()

            if exito:
                print(Colores.success("Conexión a BD exitosa"))
                logger.info("Conexión a BD verificada")
                return True
            else:
                print(Colores.warning("No se pudo conectar a BD (verifique credenciales)"))
                logger.warning("Error en conexión a BD")
                return False

        except Exception as e:
            print(Colores.warning(f"Advertencia: {str(e)}"))
            print(Colores.info("Continuando sin verificar BD..."))
            logger.warning(f"No se pudo verificar BD: {e}")
            return True  # Continuar de todos modos

    def probar_conexion_email(self, config: Dict) -> bool:
        """Prueba la conexión a email"""
        print()
        print(Colores.loading("Probando conexión a email..."))
        time.sleep(1)

        try:
            import smtplib

            # Intenta conectar al servidor SMTP
            with smtplib.SMTP(config['EMAIL_HOST'], int(config['EMAIL_PORT']), timeout=5) as server:
                server.starttls()
                server.login(config['EMAIL_USER'], config['EMAIL_PASSWORD'])

            print(Colores.success("Conexión a email exitosa"))
            logger.info("Conexión a email verificada")
            return True

        except Exception as e:
            print(Colores.warning(f"No se pudo conectar a email: {str(e)}"))
            print(Colores.info("Continuando sin verificar email..."))
            logger.warning(f"No se pudo verificar email: {e}")
            return True  # Continuar de todos modos

    def guardar_configuracion(self, configuracion: Dict) -> bool:
        """Guarda la configuración en .env"""
        print()
        print(Colores.loading("Guardando configuración..."))

        try:
            # Crear .env si no existe
            if not self.env_file.exists():
                self.env_file.touch()
                logger.info(f".env creado: {self.env_file}")

            # Guardar cada variable
            for clave, valor in configuracion.items():
                set_key(str(self.env_file), clave, valor)

            print(Colores.success(f"Configuración guardada en {self.env_file}"))
            logger.info(f"Configuración guardada: {list(configuracion.keys())}")
            return True

        except Exception as e:
            print(Colores.error(f"Error al guardar configuración: {e}"))
            logger.error(f"Error guardando configuración: {e}")
            return False

    def mostrar_resumen(self, configuracion: Dict):
        """Muestra un resumen de la configuración"""
        print()
        print(Colores.BOLD + "═" * 70 + Colores.RESET)
        print(Colores.BOLD + "RESUMEN DE CONFIGURACIÓN" + Colores.RESET)
        print(Colores.BOLD + "═" * 70 + Colores.RESET)
        print()

        # Agrupar variables por categoría
        categorias = {
            'Base de Datos': ['DB_HOST', 'DB_PORT', 'DB_USER', 'DB_PASSWORD', 'DB_DATABASE'],
            'Email': ['EMAIL_USER', 'EMAIL_TO', 'EMAIL_HOST', 'EMAIL_PORT'],
            'CEDIS': ['CEDIS_CODE', 'CEDIS_NAME', 'CEDIS_REGION'],
            'Sistema': ['DEBUG', 'ENVIRONMENT'],
        }

        for categoria, llaves in categorias.items():
            print(f"{Colores.CYAN}{categoria}{Colores.RESET}")
            for llave in llaves:
                if llave in configuracion:
                    valor = configuracion[llave]
                    # Ocultar passwords
                    if 'PASSWORD' in llave:
                        valor = '***' * 3
                    print(f"  {llave:<25} = {valor}")
            print()

    def ejecutar_setup_completo(self) -> bool:
        """Ejecuta el setup completo"""
        self.mostrar_banner()
        time.sleep(2)

        try:
            # Recopilar configuración en fases
            config = {}

            config.update(self.setup_base_de_datos())
            print()
            self.probar_conexion_bd(config)
            time.sleep(1)

            config.update(self.setup_email())
            print()
            self.probar_conexion_email(config)
            time.sleep(1)

            config.update(self.setup_cedis())
            time.sleep(1)

            config.update(self.setup_sistema())
            time.sleep(1)

            # Mostrar resumen
            self.mostrar_resumen(config)

            # Confirmar
            print()
            confirmacion = self.solicitar_entrada(
                "¿Guardar esta configuración?",
                valor_default="s",
                requerido=True
            )

            if confirmacion.lower() not in ['s', 'si', 'sí', 'yes', 'y']:
                print(Colores.warning("Setup cancelado"))
                logger.info("Setup cancelado por el usuario")
                return False

            # Guardar
            if self.guardar_configuracion(config):
                print()
                print(Colores.success("Setup completado exitosamente"))
                print(Colores.info(f"El sistema está listo para usar."))
                print(Colores.info(f"Ejecute: python startup.py"))
                logger.info("Setup completado exitosamente")
                return True
            else:
                print(Colores.error("Error al guardar la configuración"))
                logger.error("Error en guardado")
                return False

        except KeyboardInterrupt:
            print()
            print(Colores.warning("Setup interrumpido por el usuario"))
            logger.info("Setup interrumpido")
            return False

        except Exception as e:
            print(Colores.error(f"Error en setup: {e}"))
            logger.error(f"Error en setup: {e}", exc_info=True)
            return False


# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIONES DE CONVENIENCIA
# ═══════════════════════════════════════════════════════════════════════════════

def ejecutar_setup_interactivo():
    """Ejecuta el setup interactivo"""
    gestor = GestorSetupCredenciales()
    return gestor.ejecutar_setup_completo()


def verificar_credenciales_configuradas() -> bool:
    """Verifica si las credenciales ya están configuradas"""
    load_dotenv()

    credenciales_requeridas = [
        'DB_USER',
        'DB_PASSWORD',
        'EMAIL_USER',
        'EMAIL_PASSWORD',
    ]

    return all(os.getenv(cred) and os.getenv(cred) != 'tu_password'
               for cred in credenciales_requeridas)


if __name__ == '__main__':
    # Test
    logging.basicConfig(level=logging.INFO)
    print(Colores.info("Iniciando setup interactivo..."))
    print()

    exito = ejecutar_setup_interactivo()
    sys.exit(0 if exito else 1)
