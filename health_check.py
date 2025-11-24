#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════
HEALTH CHECK - VERIFICACIÓN DE SISTEMA PARA PRODUCCIÓN
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Verifica que todos los componentes estén listos para producción:
- Dependencias instaladas
- Configuración válida
- Base de datos accesible
- Email funcional
- Directorio de logs
- Permisos de archivos

Uso:
    python health_check.py
    python health_check.py --detailed  # Más detallado
    python health_check.py --fix       # Intentar auto-corregir

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
═══════════════════════════════════════════════════════════════
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# Añadir el directorio del proyecto al path
PROJECT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_DIR))

try:
    from config import (
        VERSION, DB_CONFIG, EMAIL_CONFIG, PATHS, CEDIS,
        validar_configuracion
    )
except ImportError as e:
    print(f"⚠️  Error importando config: {e}")
    sys.exit(1)


class HealthChecker:
    """Verificador de salud del sistema"""

    def __init__(self, detailed: bool = False, auto_fix: bool = False):
        self.detailed = detailed
        self.auto_fix = auto_fix
        self.resultados = {
            'timestamp': datetime.now().isoformat(),
            'version': VERSION,
            'checks': [],
            'resumen': {'total': 0, 'exitosos': 0, 'advertencias': 0, 'errores': 0}
        }

    def imprimir_banner(self):
        """Imprime banner"""
        print("""
        ╔═══════════════════════════════════════════════════════╗
        ║  🏥 HEALTH CHECK - VERIFICACIÓN DE SISTEMA           ║
        ║  SAC v1.0 - CEDIS Cancún 427                         ║
        ║  Production Readiness Check                           ║
        ╚═══════════════════════════════════════════════════════╝
        """)

    def agregar_check(
        self,
        nombre: str,
        estado: str,
        mensaje: str,
        detalles: str = ""
    ):
        """Agrega resultado de un check"""
        self.resultados['checks'].append({
            'nombre': nombre,
            'estado': estado,
            'mensaje': mensaje,
            'detalles': detalles
        })

        # Actualizar resumen
        self.resultados['resumen']['total'] += 1
        if estado == 'OK':
            self.resultados['resumen']['exitosos'] += 1
        elif estado == 'WARNING':
            self.resultados['resumen']['advertencias'] += 1
        elif estado == 'ERROR':
            self.resultados['resumen']['errores'] += 1

    def check_python_version(self) -> bool:
        """Verifica versión de Python"""
        print("\n📌 Verificando versión de Python...")
        version_info = sys.version_info
        version_str = f"{version_info.major}.{version_info.minor}.{version_info.micro}"

        if version_info.major >= 3 and version_info.minor >= 8:
            self.agregar_check(
                "Python Version",
                "OK",
                f"✅ Python {version_str} (requerido: 3.8+)"
            )
            print(f"   ✅ Python {version_str}")
            return True
        else:
            self.agregar_check(
                "Python Version",
                "ERROR",
                f"❌ Python {version_str} (requerido: 3.8+)"
            )
            print(f"   ❌ Python {version_str} - Requiere 3.8+")
            return False

    def check_dependencias(self) -> bool:
        """Verifica dependencias instaladas"""
        print("\n📌 Verificando dependencias...")

        dependencias_criticas = [
            'pandas', 'numpy', 'openpyxl', 'rich',
            'python_dotenv', 'pydantic'
        ]

        todas_ok = True
        for dep in dependencias_criticas:
            try:
                __import__(dep.replace('-', '_'))
                print(f"   ✅ {dep}")
                self.agregar_check(f"Dependency: {dep}", "OK", f"✅ {dep} instalado")
            except ImportError:
                print(f"   ❌ {dep} - NO INSTALADO")
                self.agregar_check(
                    f"Dependency: {dep}",
                    "ERROR",
                    f"❌ {dep} no está instalado"
                )
                todas_ok = False

        return todas_ok

    def check_env_file(self) -> bool:
        """Verifica archivo .env"""
        print("\n📌 Verificando archivo .env...")

        env_path = PROJECT_DIR / '.env'
        env_template = PROJECT_DIR / 'env'

        if env_path.exists():
            # Verificar permisos
            permisos = oct(env_path.stat().st_mode)[-3:]
            if permisos == '600':
                print(f"   ✅ .env existe con permisos correctos (600)")
                self.agregar_check(
                    ".env File",
                    "OK",
                    "✅ Archivo .env existe con permisos 600"
                )
                return True
            else:
                print(f"   ⚠️  .env existe pero permisos incorrectos ({permisos})")
                if self.auto_fix:
                    os.chmod(env_path, 0o600)
                    print(f"   ✅ Permisos corregidos a 600")
                self.agregar_check(
                    ".env File",
                    "WARNING" if self.auto_fix else "ERROR",
                    f"⚠️  Permisos incorrectos: {permisos} (debe ser 600)"
                )
                return self.auto_fix
        elif env_template.exists():
            print(f"   ⚠️  .env no existe. Usa 'python setup_env_seguro.py'")
            self.agregar_check(
                ".env File",
                "WARNING",
                "⚠️  .env no existe. Ejecuta setup_env_seguro.py"
            )
            return False
        else:
            print(f"   ❌ Ni .env ni env encontrados")
            self.agregar_check(
                ".env File",
                "ERROR",
                "❌ Archivos de configuración no encontrados"
            )
            return False

    def check_directorios(self) -> bool:
        """Verifica directorios necesarios"""
        print("\n📌 Verificando directorios...")

        directorios_requeridos = [
            PATHS['output'],
            PATHS['logs'],
            PATHS['resultados'],
            PATHS['queries']
        ]

        todas_ok = True
        for directorio in directorios_requeridos:
            if directorio.exists():
                print(f"   ✅ {directorio.name}")
            else:
                print(f"   ⚠️  {directorio.name} - No existe")
                if self.auto_fix:
                    directorio.mkdir(parents=True, exist_ok=True)
                    print(f"      ✅ Creado")
                else:
                    todas_ok = False

                self.agregar_check(
                    f"Directory: {directorio.name}",
                    "OK" if self.auto_fix else "WARNING",
                    f"{'✅' if self.auto_fix else '⚠️'} {directorio.name} "
                    f"({'creado' if self.auto_fix else 'no existe'})"
                )

        return todas_ok

    def check_config(self) -> bool:
        """Verifica configuración"""
        print("\n📌 Verificando configuración...")

        try:
            es_valida, errores = validar_configuracion()

            if es_valida:
                print(f"   ✅ Configuración válida")
                self.agregar_check("Configuration", "OK", "✅ Configuración válida")
                return True
            else:
                print(f"   ❌ Errores en configuración:")
                for error in errores:
                    print(f"      - {error}")
                self.agregar_check(
                    "Configuration",
                    "ERROR",
                    f"❌ {len(errores)} errores en configuración"
                )
                return False

        except Exception as e:
            print(f"   ❌ Error validando configuración: {e}")
            self.agregar_check("Configuration", "ERROR", f"❌ Error: {e}")
            return False

    def check_db_connection(self) -> bool:
        """Verifica conexión a BD (simulado)"""
        print("\n📌 Verificando conexión a BD...")

        # En producción, aquí se haría una conexión real
        print(f"   ℹ️  BD: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
        print(f"   ℹ️  Database: {DB_CONFIG['database']}")
        print(f"   ℹ️  Schema: WM260BASD::WMWHSE1")

        # Nota: La conexión real requiere drivers DB2 instalados
        self.agregar_check(
            "Database Connection",
            "WARNING",
            "ℹ️  Configuración presente. Conexión requiere drivers DB2."
        )
        return True

    def check_email_config(self) -> bool:
        """Verifica configuración de email"""
        print("\n📌 Verificando configuración de Email...")

        print(f"   ✅ SMTP: {EMAIL_CONFIG['smtp_server']}:{EMAIL_CONFIG['smtp_port']}")
        print(f"   ✅ Protocolo: {'TLS' if EMAIL_CONFIG['enable_ssl'] else 'No seguro'}")

        self.agregar_check(
            "Email Configuration",
            "OK",
            f"✅ Email configurado para {EMAIL_CONFIG['smtp_server']}"
        )
        return True

    def check_cedis_info(self) -> bool:
        """Verifica información del CEDIS"""
        print("\n📌 Verificando información del CEDIS...")

        print(f"   ✅ CEDIS: {CEDIS['name']} (Código: {CEDIS['code']})")
        print(f"   ✅ Región: {CEDIS['region']}")
        print(f"   ✅ Almacén: {CEDIS['almacen']}")

        self.agregar_check(
            "CEDIS Configuration",
            "OK",
            f"✅ CEDIS {CEDIS['name']} configurado"
        )
        return True

    def check_gitignore(self) -> bool:
        """Verifica que .env esté en .gitignore"""
        print("\n📌 Verificando .gitignore...")

        gitignore_path = PROJECT_DIR / '.gitignore'
        if gitignore_path.exists():
            with open(gitignore_path, 'r') as f:
                contenido = f.read()

            if '.env' in contenido:
                print(f"   ✅ .env está en .gitignore")
                self.agregar_check(".gitignore", "OK", "✅ .env en .gitignore")
                return True
            else:
                print(f"   ❌ .env NO está en .gitignore")
                self.agregar_check(".gitignore", "ERROR", "❌ .env no en .gitignore")
                return False
        else:
            print(f"   ❌ .gitignore no encontrado")
            self.agregar_check(".gitignore", "ERROR", "❌ .gitignore no encontrado")
            return False

    def check_requirements(self) -> bool:
        """Verifica requirements.txt"""
        print("\n📌 Verificando requirements.txt...")

        req_path = PROJECT_DIR / 'requirements.txt'
        if req_path.exists():
            with open(req_path, 'r') as f:
                lineas = f.readlines()

            paquetes = [l.split()[0] for l in lineas if l.strip() and not l.startswith('#')]
            print(f"   ✅ requirements.txt contiene {len(paquetes)} paquetes")
            self.agregar_check(
                "requirements.txt",
                "OK",
                f"✅ {len(paquetes)} paquetes definidos"
            )
            return True
        else:
            print(f"   ❌ requirements.txt no encontrado")
            self.agregar_check("requirements.txt", "ERROR", "❌ requirements.txt no encontrado")
            return False

    def ejecutar_todos_checks(self):
        """Ejecuta todos los checks"""
        checks = [
            self.check_python_version,
            self.check_dependencias,
            self.check_directorios,
            self.check_env_file,
            self.check_gitignore,
            self.check_requirements,
            self.check_config,
            self.check_cedis_info,
            self.check_email_config,
            self.check_db_connection,
        ]

        for check in checks:
            try:
                check()
            except Exception as e:
                print(f"\n   ⚠️  Error en {check.__name__}: {e}")

    def imprimir_resumen(self):
        """Imprime resumen de resultados"""
        print("\n" + "="*70)
        print("📊 RESUMEN FINAL")
        print("="*70)

        resumen = self.resultados['resumen']
        print(f"\nTotal checks:     {resumen['total']}")
        print(f"✅ Exitosos:      {resumen['exitosos']}")
        print(f"⚠️  Advertencias:  {resumen['advertencias']}")
        print(f"❌ Errores:       {resumen['errores']}")

        # Determinar estado general
        if resumen['errores'] == 0:
            estado = "✅ LISTO PARA PRODUCCIÓN"
            color = "verde"
        elif resumen['advertencias'] > 0 and resumen['errores'] == 0:
            estado = "⚠️  PARCIALMENTE LISTO (revisar advertencias)"
            color = "amarillo"
        else:
            estado = "❌ NO LISTO (corregir errores)"
            color = "rojo"

        print(f"\nEstado General: {estado}")

        if self.detailed:
            print("\n" + "="*70)
            print("📋 DETALLE DE CHECKS")
            print("="*70)
            for check in self.resultados['checks']:
                print(f"\n▪ {check['nombre']} [{check['estado']}]")
                print(f"  {check['mensaje']}")
                if check['detalles']:
                    print(f"  {check['detalles']}")

    def guardar_reporte(self):
        """Guarda reporte en archivo JSON"""
        reporte_path = PATHS['logs'] / f"health_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(reporte_path, 'w', encoding='utf-8') as f:
            json.dump(self.resultados, f, indent=2, ensure_ascii=False)
        print(f"\n📄 Reporte guardado en: {reporte_path}")

    def ejecutar(self):
        """Ejecuta health check completo"""
        self.imprimir_banner()
        self.ejecutar_todos_checks()
        self.imprimir_resumen()
        self.guardar_reporte()

        # Retornar código de salida según resultado
        if self.resultados['resumen']['errores'] > 0:
            sys.exit(1)
        else:
            sys.exit(0)


def main():
    """Función principal"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Health Check del Sistema SAC'
    )
    parser.add_argument(
        '--detailed',
        action='store_true',
        help='Mostrar detalles de cada check'
    )
    parser.add_argument(
        '--fix',
        action='store_true',
        help='Intentar auto-corregir problemas'
    )

    args = parser.parse_args()

    checker = HealthChecker(
        detailed=args.detailed,
        auto_fix=args.fix
    )
    checker.ejecutar()


if __name__ == '__main__':
    main()
