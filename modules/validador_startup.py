"""
═══════════════════════════════════════════════════════════════
VALIDADOR DE STARTUP - SISTEMA SAC
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Módulo de validación que se ejecuta al iniciar la aplicación para
asegurar que todos los requisitos críticos estén configurados.

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
═══════════════════════════════════════════════════════════════
"""

import logging
import sys
from typing import Tuple, List, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class ValidacionError(Exception):
    """Excepción base para errores de validación"""
    pass


class ValidacionCriticaError(ValidacionError):
    """Excepción para errores críticos que impiden inicio"""
    pass


class ConfiguracionValidator:
    """Validador de configuración del sistema con niveles de severidad"""

    def __init__(self):
        self.errores_criticos = []
        self.advertencias = []
        self.info = []

    def limpiar(self):
        """Limpiar los resultados previos"""
        self.errores_criticos = []
        self.advertencias = []
        self.info = []

    def agregar_error_critico(self, mensaje: str):
        """Agregar un error crítico"""
        self.errores_criticos.append(mensaje)
        logger.critical(f"🔴 CRÍTICO: {mensaje}")

    def agregar_advertencia(self, mensaje: str):
        """Agregar una advertencia"""
        self.advertencias.append(mensaje)
        logger.warning(f"🟠 ADVERTENCIA: {mensaje}")

    def agregar_info(self, mensaje: str):
        """Agregar información"""
        self.info.append(mensaje)
        logger.info(f"ℹ️  {mensaje}")

    def validar_configuracion_critica(self, db_config: Dict, email_config: Dict) -> Tuple[bool, List[str]]:
        """
        Valida SOLO la configuración crítica requerida para operación.

        Args:
            db_config: Configuración de base de datos
            email_config: Configuración de email

        Returns:
            Tuple[bool, List[str]]: (es_valido, errores_criticos)
        """
        self.limpiar()

        # Validar DB_USER
        if self._es_valor_inseguro(db_config.get('user')):
            self.agregar_error_critico(
                "DB_USER no configurado. Configura DB_USER en archivo .env"
            )

        # Validar DB_PASSWORD
        if self._es_valor_inseguro(db_config.get('password')):
            self.agregar_error_critico(
                "DB_PASSWORD no configurado. Configura DB_PASSWORD en archivo .env"
            )

        # Validar DB_HOST
        if not db_config.get('host'):
            self.agregar_error_critico(
                "DB_HOST no configurado. Configura DB_HOST en archivo .env"
            )

        # Validar DB_PORT es número válido
        try:
            puerto = int(db_config.get('port', 50000))
            if not (1 <= puerto <= 65535):
                self.agregar_error_critico(
                    f"DB_PORT ({puerto}) fuera de rango válido (1-65535)"
                )
        except (ValueError, TypeError):
            self.agregar_error_critico(
                f"DB_PORT debe ser un número entero, got: {db_config.get('port')}"
            )

        # Validar EMAIL_USER
        if self._es_valor_inseguro(email_config.get('user')):
            self.agregar_error_critico(
                "EMAIL_USER no configurado. Configura EMAIL_USER en archivo .env"
            )

        # Validar EMAIL_PASSWORD
        if self._es_valor_inseguro(email_config.get('password')):
            self.agregar_error_critico(
                "EMAIL_PASSWORD no configurado. Configura EMAIL_PASSWORD en archivo .env"
            )

        # Validar EMAIL_PORT es número válido
        try:
            puerto_smtp = int(email_config.get('smtp_port', 587))
            if not (1 <= puerto_smtp <= 65535):
                self.agregar_error_critico(
                    f"EMAIL_PORT ({puerto_smtp}) fuera de rango válido (1-65535)"
                )
            if puerto_smtp not in {25, 465, 587, 2525}:
                self.agregar_advertencia(
                    f"EMAIL_PORT ({puerto_smtp}) no es puerto SMTP estándar. "
                    "Puertos comunes: 25 (SMTP), 465 (SMTPS), 587 (TLS), 2525"
                )
        except (ValueError, TypeError):
            self.agregar_error_critico(
                f"EMAIL_PORT debe ser un número entero, got: {email_config.get('smtp_port')}"
            )

        return len(self.errores_criticos) == 0, self.errores_criticos

    def validar_estructura_directorios(self, paths: Dict[str, Path]) -> Tuple[bool, List[str]]:
        """
        Valida que los directorios requeridos existan o puedan crearse.

        Args:
            paths: Diccionario de rutas del sistema

        Returns:
            Tuple[bool, List[str]]: (es_valido, errores)
        """
        errores_locales = []

        for nombre, ruta in paths.items():
            if nombre in ['logs', 'resultados']:
                try:
                    ruta.mkdir(parents=True, exist_ok=True)
                    self.agregar_info(f"Directorio '{nombre}' verificado: {ruta}")
                except Exception as e:
                    self.agregar_error_critico(
                        f"No se puede crear directorio '{nombre}': {e}"
                    )
                    errores_locales.append(str(e))

        return len(errores_locales) == 0, errores_locales

    def validar_dependencias_opcionales(self) -> Tuple[bool, List[str]]:
        """
        Valida disponibilidad de dependencias opcionales.

        Returns:
            Tuple[bool, List[str]]: (todas_disponibles, advertencias)
        """
        advertencias_locales = []

        # Verificar pyodbc
        try:
            import pyodbc
            self.agregar_info("✅ pyodbc disponible para conexión DB2")
        except ImportError:
            self.agregar_advertencia(
                "pyodbc no disponible. Conectividad DB2 limitada."
            )
            advertencias_locales.append("pyodbc no disponible")

        # Verificar ibm_db
        try:
            import ibm_db
            self.agregar_info("✅ ibm_db disponible para conexión DB2")
        except ImportError:
            if "pyodbc" in str(advertencias_locales):
                self.agregar_error_critico(
                    "Ningún driver DB2 disponible (pyodbc ni ibm_db). "
                    "Instala: pip install pyodbc o pip install ibm-db"
                )
                return False, advertencias_locales

        # Verificar openpyxl
        try:
            import openpyxl
            self.agregar_info("✅ openpyxl disponible para reportes Excel")
        except ImportError:
            self.agregar_advertencia(
                "openpyxl no disponible. Generación de reportes limitada."
            )
            advertencias_locales.append("openpyxl no disponible")

        # Verificar pandas
        try:
            import pandas
            self.agregar_info("✅ pandas disponible para procesamiento de datos")
        except ImportError:
            self.agregar_error_critico(
                "pandas no disponible. Instala: pip install pandas"
            )
            return False, advertencias_locales

        return True, advertencias_locales

    def mostrar_reporte(self, titulo: str = "REPORTE DE VALIDACIÓN") -> bool:
        """
        Muestra un reporte visual de los resultados de validación.

        Args:
            titulo: Título del reporte

        Returns:
            bool: True si no hay errores críticos
        """
        print("\n" + "═" * 70)
        print(f"  {titulo}")
        print("═" * 70 + "\n")

        # Mostrar errores críticos
        if self.errores_criticos:
            print("🔴 ERRORES CRÍTICOS (deben solucionarse):")
            print("-" * 70)
            for i, error in enumerate(self.errores_criticos, 1):
                print(f"  {i}. {error}")
            print()

        # Mostrar advertencias
        if self.advertencias:
            print("🟠 ADVERTENCIAS (se recomienda revisar):")
            print("-" * 70)
            for i, adv in enumerate(self.advertencias, 1):
                print(f"  {i}. {adv}")
            print()

        # Mostrar información
        if self.info:
            print("ℹ️  INFORMACIÓN:")
            print("-" * 70)
            for i, inf in enumerate(self.info, 1):
                print(f"  {i}. {inf}")
            print()

        # Resumen final
        hay_errores = len(self.errores_criticos) > 0
        if hay_errores:
            print("❌ Validación FALLIDA - Errores críticos encontrados")
            print("=" * 70)
            return False
        else:
            print("✅ Validación EXITOSA - Sistema listo para operación")
            print("=" * 70 + "\n")
            return True

    @staticmethod
    def _es_valor_inseguro(valor: Optional[str]) -> bool:
        """
        Determina si un valor de configuración es inseguro (sin configurar).

        Args:
            valor: Valor a validar

        Returns:
            bool: True si es inseguro
        """
        if not valor:
            return True

        inseguros = [
            'tu_usuario',
            'tu_password',
            'tu_email@chedraui.com.mx',
            'placeholder',
            'none',
            'null',
            '***',
        ]

        return valor.lower() in inseguros or valor.startswith('tu_')


def validar_startup(db_config: Dict, email_config: Dict, paths: Dict[str, Path]) -> bool:
    """
    Ejecuta validación completa de startup.

    Args:
        db_config: Configuración de base de datos
        email_config: Configuración de email
        paths: Diccionario de rutas

    Returns:
        bool: True si validación pasó, False si hay errores críticos

    Raises:
        ValidacionCriticaError: Si hay errores críticos
    """
    validador = ConfiguracionValidator()

    # 1. Validar configuración crítica
    config_ok, errores_config = validador.validar_configuracion_critica(db_config, email_config)

    # 2. Validar estructura de directorios
    dirs_ok, errores_dirs = validador.validar_estructura_directorios(paths)

    # 3. Validar dependencias opcionales
    deps_ok, adv_deps = validador.validar_dependencias_opcionales()

    # Mostrar reporte
    es_valido = validador.mostrar_reporte()

    if not es_valido:
        raise ValidacionCriticaError(
            f"Validación de startup falló con {len(validador.errores_criticos)} errores críticos. "
            "Por favor revisa la configuración del archivo .env"
        )

    return True
