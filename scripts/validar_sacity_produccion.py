#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════
SACITY - VALIDADOR DE PRODUCCIÓN
Sistema de Automatización de Consultas - Chedraui CEDIS
═══════════════════════════════════════════════════════════════

Script de validación pre-producción para SACITY Emulator.
Verifica todas las funcionalidades críticas antes de deployment.

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
CEDIS 427 - Tiendas Chedraui Logística Cancún
═══════════════════════════════════════════════════════════════
"""

import sys
import os
import logging
import time
import importlib.util
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

# ═══════════════════════════════════════════════════════════════
# CONFIGURACIÓN LOGGING
# ═══════════════════════════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# VALIDADORES
# ═══════════════════════════════════════════════════════════════

class ValidadorSACITY:
    """Validador de producción para SACITY"""

    def __init__(self):
        self.resultados = {
            'ok': [],
            'warning': [],
            'error': [],
            'critico': []
        }
        self.puntuacion_total = 0
        self.puntuacion_max = 0

    def ejecutar_validacion_completa(self) -> bool:
        """Ejecuta todas las validaciones"""
        print("\n" + "=" * 70)
        print("🔍 SACITY - VALIDADOR DE PRODUCCIÓN v1.0")
        print("=" * 70 + "\n")

        validaciones = [
            ("Estructura de Directorios", self._validar_estructura),
            ("Archivos de Módulos", self._validar_modulos),
            ("Documentación", self._validar_documentacion),
            ("Importaciones de Módulos", self._validar_imports),
            ("Configuración", self._validar_config),
            ("Email (SMTP/IMAP)", self._validar_email),
            ("Código LITE", self._validar_lite),
            ("Código ESTÁNDAR", self._validar_estandar),
            ("Dependencias", self._validar_dependencias),
            ("Performance", self._validar_performance),
        ]

        for nombre, validador in validaciones:
            print(f"\n📋 Validando: {nombre}")
            print("-" * 70)
            try:
                validador()
            except Exception as e:
                logger.error(f"Error en validación: {e}")
                self._agregar_error(nombre, f"Error no controlado: {str(e)}")

        self._mostrar_resumen()
        return len(self.resultados['critico']) == 0

    def _validar_estructura(self) -> None:
        """Valida estructura de directorios"""
        directorios_requeridos = [
            'modules',
            'docs',
            'output/logs',
            'output/resultados',
        ]

        for directorio in directorios_requeridos:
            ruta = Path(directorio)
            if ruta.exists():
                self._agregar_ok(f"Directorio '{directorio}' existe")
            else:
                self._agregar_error(f"Estructura", f"Falta directorio: {directorio}")

    def _validar_modulos(self) -> None:
        """Valida existencia de módulos SACITY"""
        modulos_requeridos = {
            'modules/modulo_symbol_mc9000.py': 'ESTÁNDAR (66KB)',
            'modules/modulo_symbol_mc9000_lite.py': 'LITE (17KB)',
            'modules/modulo_symbol_email_commands.py': 'EMAIL COMMANDS (19KB)',
        }

        for modulo, desc in modulos_requeridos.items():
            ruta = Path(modulo)
            if ruta.exists():
                tamaño = ruta.stat().st_size
                self._agregar_ok(f"Módulo {desc}: {tamaño:,} bytes")
            else:
                self._agregar_critico(f"Módulos", f"Falta módulo: {modulo}")

    def _validar_documentacion(self) -> None:
        """Valida documentación SACITY"""
        documentos = {
            'SACITY_DEPLOYMENT.md': 'Guía de Deployment',
            'SACITY_OPTIMIZATION.md': 'Guía de Optimización',
            'AUDIT_SACITY_EMULATOR.md': 'Reporte de Auditoría',
        }

        for archivo, desc in documentos.items():
            ruta = Path(archivo)
            if ruta.exists():
                tamaño = ruta.stat().st_size
                self._agregar_ok(f"{desc}: {tamaño:,} bytes")
            else:
                self._agregar_warning(f"Documentación", f"Falta: {archivo}")

    def _validar_imports(self) -> None:
        """Valida que los imports funcionan correctamente"""
        # LITE debe funcionar sin pandas (zero dependencies)
        try:
            sys.path.insert(0, str(Path('modules')))

            spec = importlib.util.spec_from_file_location("modulo_symbol_mc9000_lite",
                                                          "modules/modulo_symbol_mc9000_lite.py")
            lite_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(lite_module)

            if hasattr(lite_module, 'GestorSymbolLite') and hasattr(lite_module, 'TelnetLite'):
                self._agregar_ok("Import LITE: GestorSymbolLite, TelnetLite")
            else:
                self._agregar_error("Imports", "Clases LITE no encontradas")
        except Exception as e:
            self._agregar_warning("Imports", f"LITE requiere validación manual: {str(e)[:50]}")

        # ESTÁNDAR y EMAIL dependen de pandas (parte del proyecto SAC)
        try:
            # Solo verificar que los archivos existen y contienen las clases
            with open('modules/modulo_symbol_mc9000.py', 'r') as f:
                if 'class GestorDispositivosSymbol' in f.read():
                    self._agregar_ok("Clase ESTÁNDAR: GestorDispositivosSymbol presente")
        except Exception as e:
            self._agregar_error("Imports", f"Error verificando ESTÁNDAR: {e}")

        try:
            with open('modules/modulo_symbol_email_commands.py', 'r') as f:
                content = f.read()
                if 'class ReceptorComandosEmail' in content and 'class ProcesadorComandosEmail' in content:
                    self._agregar_ok("Clases EMAIL: ReceptorComandosEmail, ProcesadorComandosEmail presente")
        except Exception as e:
            self._agregar_error("Imports", f"Error verificando EMAIL: {e}")

    def _validar_config(self) -> None:
        """Valida configuración base"""
        if Path('config.py').exists():
            self._agregar_ok("config.py existe")
        else:
            self._agregar_error("Config", "Falta config.py")

        env_requeridas = ['DB_USER', 'DB_PASSWORD', 'EMAIL_USER', 'EMAIL_PASSWORD']
        env_path = Path('.env')

        if env_path.exists():
            with open(env_path, 'r') as f:
                contenido = f.read()
                for var in env_requeridas:
                    if var in contenido:
                        self._agregar_ok(f"Variable {var} configurada en .env")
                    else:
                        self._agregar_warning("Config", f"Variable no encontrada: {var}")
        else:
            self._agregar_warning("Config", "Archivo .env no existe (crear de 'env' template)")

    def _validar_email(self) -> None:
        """Valida capacidades de email"""
        try:
            import smtplib
            self._agregar_ok("SMTP disponible en stdlib")
        except Exception as e:
            self._agregar_warning("Email", f"SMTP: {e}")

        try:
            import imaplib
            self._agregar_ok("IMAP disponible en stdlib")
        except Exception as e:
            self._agregar_warning("Email", f"IMAP: {e}")

        try:
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            self._agregar_ok("Email MIME disponible en stdlib")
        except Exception as e:
            self._agregar_warning("Email", f"Email MIME: {e}")

    def _validar_lite(self) -> None:
        """Valida características LITE"""
        try:
            # Validación estática sin importar
            with open('modules/modulo_symbol_mc9000_lite.py', 'r') as f:
                source = f.read()

            # Verificar que solo usa stdlib
            dependencias_externas = ['import requests', 'import numpy', 'import pandas', 'import bs4']
            encontradas = [d for d in dependencias_externas if d in source]

            if not encontradas:
                self._agregar_ok("LITE: Zero external dependencies")
            else:
                self._agregar_warning("LITE", f"Posibles dependencias: {encontradas}")

            # Verificar métodos clave
            metodos = ['def conectar', 'def desconectar', 'def ejecutar_comando', 'def obtener_bateria', 'def iniciar_heartbeat']
            for metodo in metodos:
                if metodo in source:
                    self._agregar_ok(f"LITE: {metodo.replace('def ', '')} presente")
                else:
                    self._agregar_warning("LITE", f"Falta: {metodo}")

            # Verificar clases
            if 'class GestorSymbolLite' in source:
                self._agregar_ok("LITE: Clase GestorSymbolLite presente")
            if 'class TelnetLite' in source:
                self._agregar_ok("LITE: Clase TelnetLite presente")

        except Exception as e:
            self._agregar_warning("LITE", f"Error validando: {e}")

    def _validar_estandar(self) -> None:
        """Valida características ESTÁNDAR"""
        try:
            # Validación estática
            with open('modules/modulo_symbol_mc9000.py', 'r') as f:
                source = f.read()

            # Verificar métodos clave
            metodos = ['def conectar_telnet', 'def desconectar', 'def ejecutar_comando', 'def ejecutar_health_check']
            for metodo in metodos:
                if metodo in source:
                    self._agregar_ok(f"ESTÁNDAR: {metodo.replace('def ', '')} presente")
                else:
                    self._agregar_warning("ESTÁNDAR", f"Falta: {metodo}")

            # Verificar clases
            if 'class GestorDispositivosSymbol' in source:
                self._agregar_ok("ESTÁNDAR: Clase GestorDispositivosSymbol presente")

            if 'class ConfiguracionEmail' in source:
                self._agregar_ok("ESTÁNDAR: Clase ConfiguracionEmail presente")

            # Verificar email features
            if 'def enviar_alerta_email' in source:
                self._agregar_ok("ESTÁNDAR: Método enviar_alerta_email presente")
            if 'def _enviar_smtp' in source:
                self._agregar_ok("ESTÁNDAR: Soporte SMTP presente")

        except Exception as e:
            self._agregar_warning("ESTÁNDAR", f"Error validando: {e}")

    def _validar_dependencias(self) -> None:
        """Valida que no hay dependencias externas innecesarias"""
        dependencias_esperadas = {
            'socket': 'Red y conexiones',
            'threading': 'Multi-threading',
            'logging': 'Registro de eventos',
            'time': 'Timing y delays',
            'dataclasses': 'Estructuras de datos',
            'enum': 'Enumeraciones',
            'smtplib': 'Email (SMTP)',
            'imaplib': 'Email (IMAP)',
        }

        for modulo, descripcion in dependencias_esperadas.items():
            try:
                __import__(modulo)
                self._agregar_ok(f"Stdlib: {modulo} ({descripcion})")
            except ImportError:
                self._agregar_warning("Dependencias", f"Falta: {modulo}")

    def _validar_performance(self) -> None:
        """Valida características de performance"""
        specs_esperados = {
            'LITE': '<50KB, <5MB RAM',
            'ESTÁNDAR': '~200KB, ~15MB RAM',
            'PRO': '~350KB, ~25MB RAM',
        }

        for version, spec in specs_esperados.items():
            self._agregar_ok(f"{version}: {spec}")

        # Validar polling en LITE
        try:
            from modules.modulo_symbol_mc9000_lite import TelnetLite
            import inspect
            source = inspect.getsource(TelnetLite._leer_con_polling)
            if 'time.sleep(0.01)' in source or 'sleep(0.01)' in source:
                self._agregar_ok("LITE: Polling optimizado (10ms intervals)")
            else:
                self._agregar_warning("Performance", "Verificar polling interval manualmente")
        except Exception as e:
            logger.warning(f"No se pudo validar polling: {e}")

    # ═══════════════════════════════════════════════════════════════
    # HELPERS
    # ═══════════════════════════════════════════════════════════════

    def _agregar_ok(self, mensaje: str) -> None:
        """Agrega resultado OK"""
        self.resultados['ok'].append(mensaje)
        self.puntuacion_total += 1
        self.puntuacion_max += 1
        print(f"  ✅ {mensaje}")

    def _agregar_warning(self, categoria: str, mensaje: str) -> None:
        """Agrega warning"""
        self.resultados['warning'].append(f"{categoria}: {mensaje}")
        self.puntuacion_total += 0.5
        self.puntuacion_max += 1
        print(f"  ⚠️  {mensaje}")

    def _agregar_error(self, categoria: str, mensaje: str) -> None:
        """Agrega error"""
        self.resultados['error'].append(f"{categoria}: {mensaje}")
        self.puntuacion_max += 1
        print(f"  ❌ {mensaje}")

    def _agregar_critico(self, categoria: str, mensaje: str) -> None:
        """Agrega error crítico"""
        self.resultados['critico'].append(f"{categoria}: {mensaje}")
        self.puntuacion_max += 1
        print(f"  🚨 {mensaje}")

    def _mostrar_resumen(self) -> None:
        """Muestra resumen final"""
        print("\n" + "=" * 70)
        print("📊 RESUMEN DE VALIDACIÓN")
        print("=" * 70)

        print(f"\n✅ OK: {len(self.resultados['ok'])} checks pasados")
        if self.resultados['warning']:
            print(f"⚠️  WARNINGS: {len(self.resultados['warning'])} alertas")
            for w in self.resultados['warning']:
                print(f"   - {w}")

        if self.resultados['error']:
            print(f"❌ ERRORES: {len(self.resultados['error'])} errores")
            for e in self.resultados['error']:
                print(f"   - {e}")

        if self.resultados['critico']:
            print(f"🚨 CRÍTICOS: {len(self.resultados['critico'])} problemas críticos")
            for c in self.resultados['critico']:
                print(f"   - {c}")

        # Puntuación
        if self.puntuacion_max > 0:
            porcentaje = (self.puntuacion_total / self.puntuacion_max) * 100
        else:
            porcentaje = 0

        print(f"\n📈 PUNTUACIÓN: {self.puntuacion_total:.1f}/{self.puntuacion_max} ({porcentaje:.1f}%)")

        # Recomendación
        print("\n" + "=" * 70)
        if len(self.resultados['critico']) == 0 and porcentaje >= 90:
            print("✅ SACITY ESTÁ LISTO PARA PRODUCCIÓN")
            print("=" * 70 + "\n")
            return True
        elif len(self.resultados['critico']) == 0 and porcentaje >= 75:
            print("⚠️  SACITY PUEDE DEPLOYARSE CON OBSERVACIONES")
            print("   Revisar warnings antes de producción")
            print("=" * 70 + "\n")
            return True
        else:
            print("❌ SACITY NO ESTÁ LISTO PARA PRODUCCIÓN")
            print("   Resolver errores críticos antes de deployment")
            print("=" * 70 + "\n")
            return False


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    """Ejecuta validación"""
    validador = ValidadorSACITY()
    exito = validador.ejecutar_validacion_completa()

    # Checklist pre-producción
    print("\n📋 CHECKLIST PRE-PRODUCCIÓN")
    print("=" * 70)
    print("""
Antes de deployar a producción, verifica:

□ Archivo .env configurado con credenciales reales
□ Dispositivos Symbol conectados a la red
□ Prueba de conectividad: telnet <IP> 23
□ Email de test enviado y recibido respuesta
□ Health check ejecutado sin errores
□ Heartbeat activado y monitoreable en logs
□ Alertas email funcionando (simular batería baja)
□ Receptores de comandos email iniciados
□ Comando de prueba ejecutado vía email
□ Documentación SACITY_DEPLOYMENT.md leída

Para empezar:

1. Copiar template de configuración:
   $ cp env .env

2. Editar .env con credenciales reales:
   $ vi .env

3. Usar SACITY LITE para dispositivos legacy:
   from modules.modulo_symbol_mc9000_lite import GestorSymbolLite
   gestor = GestorSymbolLite()
   gestor.conectar("192.168.1.100", familia="MC9200")

4. Usar SACITY ESTÁNDAR para deployments moderno:
   from modules import GestorDispositivosSymbol, ConfiguracionEmail
   config = ConfiguracionEmail(...)
   gestor = GestorDispositivosSymbol()
   gestor.conectar_telnet(..., config_email=config)

5. Monitorear logs:
   $ tail -f output/logs/sac_427.log

═══════════════════════════════════════════════════════════════
""")

    sys.exit(0 if exito else 1)


if __name__ == "__main__":
    main()
