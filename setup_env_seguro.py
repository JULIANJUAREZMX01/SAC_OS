#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════
SETUP SEGURO DE VARIABLES DE ENTORNO
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Script seguro para configurar credenciales sin exponerlas en Git.
Crea el archivo .env de forma interactiva con validaciones.

Uso:
    python setup_env_seguro.py

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
═══════════════════════════════════════════════════════════════
"""

import os
import sys
import json
import getpass
from pathlib import Path
from datetime import datetime


class ConfiguradorSeguro:
    """Configurador seguro de variables de entorno"""

    def __init__(self):
        self.ruta_proyecto = Path(__file__).resolve().parent
        self.ruta_env = self.ruta_proyecto / '.env'
        self.ruta_env_template = self.ruta_proyecto / 'env'
        self.credenciales = {}

    def imprimir_banner(self):
        """Imprime banner de bienvenida"""
        print("""
        ╔════════════════════════════════════════════════════════╗
        ║  🔐 CONFIGURADOR SEGURO DE VARIABLES DE ENTORNO       ║
        ║  SAC v1.0 - CEDIS Cancún 427                          ║
        ╚════════════════════════════════════════════════════════╝
        """)

    def validar_credenciales_db(self, usuario: str, contraseña: str) -> bool:
        """Valida credenciales DB2"""
        if not usuario or len(usuario) < 3:
            print("❌ Usuario DB2 inválido (mínimo 3 caracteres)")
            return False
        if not contraseña or len(contraseña) < 6:
            print("❌ Contraseña DB2 inválida (mínimo 6 caracteres)")
            return False
        return True

    def validar_email(self, email: str) -> bool:
        """Valida formato de email"""
        if '@chedraui.com.mx' not in email:
            print("❌ Email debe ser corporativo (@chedraui.com.mx)")
            return False
        if not email or len(email) < 10:
            print("❌ Email inválido")
            return False
        return True

    def solicitar_credenciales_db(self):
        """Solicita credenciales de DB2"""
        print("\n" + "="*60)
        print("📊 CONFIGURACIÓN BASE DE DATOS DB2 (MANHATTAN WMS)")
        print("="*60)

        while True:
            usuario = input("\n👤 Usuario DB2: ").strip()
            if self.validar_credenciales_db(usuario, "placeholder"):
                break
            print("   Intenta de nuevo...")

        while True:
            contraseña = getpass.getpass("🔐 Contraseña DB2 (no visible): ")
            if self.validar_credenciales_db(usuario, contraseña):
                break
            print("   Intenta de nuevo...")

        self.credenciales['DB_USER'] = usuario
        self.credenciales['DB_PASSWORD'] = contraseña
        print("✅ Credenciales DB2 guardadas")

    def solicitar_credenciales_email(self):
        """Solicita credenciales de Email"""
        print("\n" + "="*60)
        print("📧 CONFIGURACIÓN EMAIL (OFFICE 365)")
        print("="*60)

        while True:
            email = input("\n📧 Email corporativo (@chedraui.com.mx): ").strip()
            if self.validar_email(email):
                break
            print("   Intenta de nuevo...")

        contraseña = getpass.getpass("🔐 Contraseña Email (no visible): ")

        self.credenciales['EMAIL_USER'] = email
        self.credenciales['EMAIL_PASSWORD'] = contraseña
        print("✅ Credenciales Email guardadas")

    def solicitar_configuracion_adicional(self):
        """Solicita configuración adicional opcional"""
        print("\n" + "="*60)
        print("⚙️  CONFIGURACIÓN ADICIONAL (OPCIONAL)")
        print("="*60)

        # Telegram
        usar_telegram = input("\n¿Deseas configurar Telegram para alertas? (s/n): ").strip().lower()
        if usar_telegram == 's':
            token = input("Token del Bot de Telegram: ").strip()
            chat_ids = input("Chat IDs (separados por comas): ").strip()
            if token:
                self.credenciales['TELEGRAM_BOT_TOKEN'] = token
                self.credenciales['TELEGRAM_CHAT_IDS'] = chat_ids
                print("✅ Telegram configurado")

        # Debug
        debug = input("\n¿Habilitar modo DEBUG? (s/n): ").strip().lower()
        self.credenciales['DEBUG'] = 'true' if debug == 's' else 'false'

    def crear_archivo_env(self):
        """Crea archivo .env con las credenciales"""
        if self.ruta_env.exists():
            respuesta = input(
                "\n⚠️  Archivo .env ya existe. ¿Deseas sobrescribir? (s/n): "
            ).strip().lower()
            if respuesta != 's':
                print("Operación cancelada")
                return False

        try:
            # Leer template env
            with open(self.ruta_env_template, 'r', encoding='utf-8') as f:
                contenido = f.read()

            # Reemplazar credenciales en el contenido
            for clave, valor in self.credenciales.items():
                # Buscar en el contenido y reemplazar
                contenido = contenido.replace(
                    f"{clave}=your_",
                    f"{clave}={valor}"
                )
                contenido = contenido.replace(
                    f"{clave}=",
                    f"{clave}={valor}",
                    1
                )

            # Escribir archivo .env con permisos restringidos
            with open(self.ruta_env, 'w', encoding='utf-8') as f:
                f.write(contenido)

            # Establecer permisos restrictivos (600 = -rw-------)
            os.chmod(self.ruta_env, 0o600)

            print(f"\n✅ Archivo .env creado exitosamente en: {self.ruta_env}")
            print(f"🔒 Permisos configurados: -rw------- (600)")
            return True

        except Exception as e:
            print(f"\n❌ Error al crear archivo .env: {e}")
            return False

    def verificar_instalacion(self):
        """Verifica que el setup sea correcto"""
        print("\n" + "="*60)
        print("🔍 VERIFICANDO INSTALACIÓN")
        print("="*60)

        checks = []

        # Check: .env existe
        check1 = self.ruta_env.exists()
        status1 = "✅" if check1 else "❌"
        checks.append(check1)
        print(f"\n{status1} Archivo .env existe: {check1}")

        # Check: permisos correctos
        if check1:
            permisos = oct(self.ruta_env.stat().st_mode)[-3:]
            check2 = permisos == '600'
            status2 = "✅" if check2 else "⚠️"
            checks.append(check2)
            print(f"{status2} Permisos .env correctos (600): {check2} (actuales: {permisos})")
        else:
            checks.append(False)

        # Check: variables requeridas
        requeridas = ['DB_USER', 'DB_PASSWORD', 'EMAIL_USER', 'EMAIL_PASSWORD']
        check3 = all(var in self.credenciales for var in requeridas)
        status3 = "✅" if check3 else "❌"
        checks.append(check3)
        print(f"{status3} Variables requeridas configuradas: {check3}")

        # Check: Git ignore
        if (self.ruta_proyecto / '.gitignore').exists():
            with open(self.ruta_proyecto / '.gitignore', 'r') as f:
                contenido_git = f.read()
                check4 = '.env' in contenido_git
                status4 = "✅" if check4 else "⚠️"
                checks.append(check4)
                print(f"{status4} .env en .gitignore: {check4}")
        else:
            checks.append(False)

        if all(checks):
            print("\n✅ ¡Verificación completada exitosamente!")
            print("\n📌 PRÓXIMOS PASOS:")
            print("   1. Ejecuta: python main.py")
            print("   2. Selecciona una opción del menú")
            print("   3. El sistema usará tus credenciales de .env")
            return True
        else:
            print("\n⚠️  Algunos checks fallaron. Verifica la configuración.")
            return False

    def ejecutar(self):
        """Ejecuta el flujo completo de setup"""
        self.imprimir_banner()

        try:
            self.solicitar_credenciales_db()
            self.solicitar_credenciales_email()
            self.solicitar_configuracion_adicional()

            # Resumen
            print("\n" + "="*60)
            print("📋 RESUMEN DE CONFIGURACIÓN")
            print("="*60)
            for clave, valor in self.credenciales.items():
                valor_oculto = valor[0] + '*'*(len(valor)-2) if len(valor) > 2 else '***'
                print(f"   {clave}: {valor_oculto}")

            confirmacion = input("\n¿Confirmas estas credenciales? (s/n): ").strip().lower()
            if confirmacion != 's':
                print("Operación cancelada")
                return False

            if self.crear_archivo_env():
                return self.verificar_instalacion()

        except KeyboardInterrupt:
            print("\n\n⚠️  Configuración cancelada por el usuario")
            return False
        except Exception as e:
            print(f"\n❌ Error durante la configuración: {e}")
            return False

        return False


def main():
    """Función principal"""
    configurador = ConfiguradorSeguro()
    exitoso = configurador.ejecutar()

    if exitoso:
        print("\n🎉 ¡Configuración completada exitosamente!")
        sys.exit(0)
    else:
        print("\n⚠️  La configuración no se completó")
        sys.exit(1)


if __name__ == '__main__':
    main()
