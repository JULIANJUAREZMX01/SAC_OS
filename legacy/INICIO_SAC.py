#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════════════════════
 ██████╗██╗  ██╗███████╗██████╗ ██████╗  █████╗ ██╗   ██╗██╗
██╔════╝██║  ██║██╔════╝██╔══██╗██╔══██╗██╔══██╗██║   ██║██║
██║     ███████║█████╗  ██║  ██║██████╔╝███████║██║   ██║██║
██║     ██╔══██║██╔══╝  ██║  ██║██╔══██╗██╔══██║██║   ██║██║
╚██████╗██║  ██║███████╗██████╔╝██║  ██║██║  ██║╚██████╔╝██║
 ╚═════╝╚═╝  ╚═╝╚══════╝╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝

    SAC - SISTEMA DE AUTOMATIZACIÓN DE CONSULTAS
    CEDIS Cancún 427 - Región Sureste

    🚀 PUNTO DE ENTRADA ÚNICO 🚀

    Este es el ÚNICO archivo que necesita ejecutar.
    El sistema detectará automáticamente si necesita instalarse
    o si ya está listo para ejecutarse.

═══════════════════════════════════════════════════════════════════════════════

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún

═══════════════════════════════════════════════════════════════════════════════
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════════════════════

VERSION = "2.0.0"
BASE_DIR = Path(__file__).parent.absolute()

# Colores ANSI para terminal
class Colores:
    ROJO = '\033[91m'
    VERDE = '\033[92m'
    AMARILLO = '\033[93m'
    AZUL = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    BLANCO = '\033[97m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

# Desactivar colores en Windows si no hay soporte
if sys.platform == 'win32':
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        # Sin soporte de colores
        for attr in dir(Colores):
            if not attr.startswith('_'):
                setattr(Colores, attr, '')

# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIONES DE UTILIDAD
# ═══════════════════════════════════════════════════════════════════════════════

def limpiar_pantalla():
    """Limpia la pantalla de la terminal"""
    os.system('cls' if sys.platform == 'win32' else 'clear')


def imprimir_banner():
    """Imprime el banner de SAC"""
    limpiar_pantalla()
    print(f"""
{Colores.ROJO}{Colores.BOLD}
═══════════════════════════════════════════════════════════════════════════════
{Colores.RESET}{Colores.ROJO}
    ███████╗ █████╗  ██████╗
    ██╔════╝██╔══██╗██╔════╝
    ███████╗███████║██║
    ╚════██║██╔══██║██║
    ███████║██║  ██║╚██████╗
    ╚══════╝╚═╝  ╚═╝ ╚═════╝
{Colores.RESET}
    {Colores.CYAN}Sistema de Automatización de Consultas{Colores.RESET}
    {Colores.AMARILLO}CEDIS Chedraui Cancún 427 - Región Sureste{Colores.RESET}

    {Colores.BLANCO}Versión: {VERSION}{Colores.RESET}
    {Colores.BLANCO}Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colores.RESET}
{Colores.ROJO}{Colores.BOLD}
═══════════════════════════════════════════════════════════════════════════════
{Colores.RESET}
""")


def imprimir_mensaje(mensaje: str, tipo: str = 'info'):
    """Imprime un mensaje con formato"""
    iconos = {
        'info': f'{Colores.CYAN}ℹ️ ',
        'exito': f'{Colores.VERDE}✅',
        'error': f'{Colores.ROJO}❌',
        'advertencia': f'{Colores.AMARILLO}⚠️ ',
        'proceso': f'{Colores.MAGENTA}🔄',
        'espera': f'{Colores.AZUL}⏳',
    }
    icono = iconos.get(tipo, '•')
    print(f"  {icono} {mensaje}{Colores.RESET}")


def verificar_python():
    """Verifica que la versión de Python sea compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        imprimir_mensaje(f"Python {version.major}.{version.minor} no es compatible", 'error')
        imprimir_mensaje("Se requiere Python 3.8 o superior", 'info')
        return False
    return True


def verificar_instalacion_completa():
    """
    Verifica si el sistema está completamente instalado.
    Retorna: (instalado: bool, tiene_credenciales: bool, mensaje: str)
    """
    # Verificar archivos críticos
    archivos_criticos = [
        'config.py',
        'main.py',
        'monitor.py',
        'requirements.txt',
    ]

    for archivo in archivos_criticos:
        if not (BASE_DIR / archivo).exists():
            return False, False, f"Falta archivo crítico: {archivo}"

    # Verificar directorios
    directorios_criticos = [
        'modules',
        'queries',
        'output',
        'output/logs',
    ]

    for directorio in directorios_criticos:
        if not (BASE_DIR / directorio).exists():
            return False, False, f"Falta directorio: {directorio}"

    # Verificar dependencias instaladas
    try:
        import pandas
        import openpyxl
        import rich
    except ImportError as e:
        return False, False, f"Dependencia faltante: {e.name}"

    # Verificar archivo .env
    env_file = BASE_DIR / '.env'
    if not env_file.exists():
        return True, False, "Sistema instalado, falta configurar credenciales (.env)"

    # Verificar que .env tiene credenciales válidas
    try:
        contenido = env_file.read_text(encoding='utf-8')
        credenciales_requeridas = ['DB_USER=', 'DB_PASSWORD=', 'EMAIL_USER=']

        for cred in credenciales_requeridas:
            if cred not in contenido:
                return True, False, f"Falta credencial: {cred.replace('=', '')}"

            # Verificar que no esté vacío
            for linea in contenido.split('\n'):
                if linea.startswith(cred):
                    valor = linea.split('=', 1)[1].strip()
                    if not valor or valor in ['tu_usuario', 'tu_password', 'your_password']:
                        return True, False, "Credenciales no configuradas"
                    break

        return True, True, "Sistema completamente instalado y configurado"

    except Exception as e:
        return True, False, f"Error leyendo .env: {e}"


def verificar_flag_instalacion():
    """Verifica si existe el flag de instalación completada"""
    flag_file = BASE_DIR / 'config' / '.instalado'
    return flag_file.exists()


def crear_flag_instalacion():
    """Crea el flag de instalación completada"""
    flag_dir = BASE_DIR / 'config'
    flag_dir.mkdir(parents=True, exist_ok=True)
    flag_file = flag_dir / '.instalado'
    flag_file.write_text(f"Instalado: {datetime.now().isoformat()}\n")


# ═══════════════════════════════════════════════════════════════════════════════
# FLUJO PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

def ejecutar_instalador():
    """Ejecuta el instalador automatizado GUI"""
    imprimir_mensaje("Iniciando instalador automatizado...", 'proceso')
    print()

    instalador_path = BASE_DIR / 'instalador_automatico_gui.py'

    if not instalador_path.exists():
        imprimir_mensaje("No se encontró el instalador automatizado", 'error')
        imprimir_mensaje("Buscando instalador alternativo...", 'info')

        # Intentar con instalador anterior
        instalador_alt = BASE_DIR / 'instalar_sac.py'
        if instalador_alt.exists():
            instalador_path = instalador_alt
        else:
            imprimir_mensaje("No se encontró ningún instalador", 'error')
            return False

    try:
        # Ejecutar instalador
        resultado = subprocess.run(
            [sys.executable, str(instalador_path)],
            cwd=str(BASE_DIR)
        )

        if resultado.returncode == 0:
            crear_flag_instalacion()
            return True
        else:
            return False

    except Exception as e:
        imprimir_mensaje(f"Error ejecutando instalador: {e}", 'error')
        return False


def solicitar_credenciales():
    """Solicita las credenciales al usuario mediante GUI"""
    imprimir_mensaje("El sistema necesita credenciales para funcionar", 'advertencia')
    imprimir_mensaje("Abriendo formulario de configuración...", 'proceso')
    print()

    # Ejecutar solo la fase de credenciales del instalador
    instalador_path = BASE_DIR / 'instalador_automatico_gui.py'

    if instalador_path.exists():
        try:
            # Importar y ejecutar solo el formulario de credenciales
            sys.path.insert(0, str(BASE_DIR))

            import tkinter as tk
            from tkinter import ttk, messagebox

            # Crear ventana simple de credenciales
            root = tk.Tk()
            root.title("🔐 Configurar Credenciales - SAC")
            root.geometry("450x400")
            root.resizable(False, False)

            # Centrar
            root.update_idletasks()
            x = (root.winfo_screenwidth() // 2) - 225
            y = (root.winfo_screenheight() // 2) - 200
            root.geometry(f"450x400+{x}+{y}")

            # Variables
            credenciales = {
                'db_user': tk.StringVar(),
                'db_password': tk.StringVar(),
                'email_user': tk.StringVar(),
                'email_password': tk.StringVar(),
            }

            # Frame principal
            main_frame = tk.Frame(root, padx=20, pady=20)
            main_frame.pack(fill=tk.BOTH, expand=True)

            # Título
            tk.Label(
                main_frame,
                text="🔐 Configuración de Credenciales",
                font=('Segoe UI', 14, 'bold'),
                fg='#E31837'
            ).pack(pady=(0, 10))

            tk.Label(
                main_frame,
                text="SAC está instalado y esperando credenciales",
                font=('Segoe UI', 9),
                fg='gray'
            ).pack(pady=(0, 20))

            # DB
            db_frame = tk.LabelFrame(main_frame, text=" Base de Datos DB2 ", font=('Segoe UI', 10, 'bold'))
            db_frame.pack(fill=tk.X, pady=(0, 10))

            tk.Label(db_frame, text="Usuario:").grid(row=0, column=0, sticky='e', padx=5, pady=5)
            tk.Entry(db_frame, textvariable=credenciales['db_user'], width=30).grid(row=0, column=1, padx=5, pady=5)

            tk.Label(db_frame, text="Contraseña:").grid(row=1, column=0, sticky='e', padx=5, pady=5)
            tk.Entry(db_frame, textvariable=credenciales['db_password'], show='*', width=30).grid(row=1, column=1, padx=5, pady=5)

            # Email
            email_frame = tk.LabelFrame(main_frame, text=" Correo Office 365 ", font=('Segoe UI', 10, 'bold'))
            email_frame.pack(fill=tk.X, pady=(0, 15))

            tk.Label(email_frame, text="Correo:").grid(row=0, column=0, sticky='e', padx=5, pady=5)
            tk.Entry(email_frame, textvariable=credenciales['email_user'], width=30).grid(row=0, column=1, padx=5, pady=5)

            tk.Label(email_frame, text="Contraseña:").grid(row=1, column=0, sticky='e', padx=5, pady=5)
            tk.Entry(email_frame, textvariable=credenciales['email_password'], show='*', width=30).grid(row=1, column=1, padx=5, pady=5)

            credenciales_guardadas = {'valor': False}

            def guardar():
                # Validar
                if not credenciales['db_user'].get() or not credenciales['db_password'].get():
                    messagebox.showwarning("Validación", "Complete las credenciales de base de datos")
                    return

                if not credenciales['email_user'].get() or not credenciales['email_password'].get():
                    messagebox.showwarning("Validación", "Complete las credenciales de correo")
                    return

                # Guardar en .env
                env_file = BASE_DIR / '.env'
                env_template = BASE_DIR / 'env'

                try:
                    if env_template.exists():
                        contenido = env_template.read_text(encoding='utf-8')
                    elif env_file.exists():
                        contenido = env_file.read_text(encoding='utf-8')
                    else:
                        # Contenido mínimo
                        contenido = """# SAC Configuration
DB_USER=
DB_PASSWORD=
EMAIL_USER=
EMAIL_PASSWORD=
DB_HOST=WM260BASD
DB_PORT=50000
DB_DATABASE=WM260BASD
DB_SCHEMA=WMWHSE1
EMAIL_HOST=smtp.office365.com
EMAIL_PORT=587
"""

                    # Reemplazar
                    lineas = contenido.split('\n')
                    nuevas = []
                    for linea in lineas:
                        if linea.startswith('DB_USER='):
                            nuevas.append(f"DB_USER={credenciales['db_user'].get()}")
                        elif linea.startswith('DB_PASSWORD='):
                            nuevas.append(f"DB_PASSWORD={credenciales['db_password'].get()}")
                        elif linea.startswith('EMAIL_USER='):
                            nuevas.append(f"EMAIL_USER={credenciales['email_user'].get()}")
                        elif linea.startswith('EMAIL_PASSWORD='):
                            nuevas.append(f"EMAIL_PASSWORD={credenciales['email_password'].get()}")
                        elif linea.startswith('EMAIL_FROM='):
                            nuevas.append(f"EMAIL_FROM={credenciales['email_user'].get()}")
                        else:
                            nuevas.append(linea)

                    env_file.write_text('\n'.join(nuevas), encoding='utf-8')
                    credenciales_guardadas['valor'] = True
                    messagebox.showinfo("Éxito", "✅ Credenciales guardadas correctamente")
                    root.destroy()

                except Exception as e:
                    messagebox.showerror("Error", f"Error guardando credenciales:\n{e}")

            def cancelar():
                root.destroy()

            # Botones
            btn_frame = tk.Frame(main_frame)
            btn_frame.pack(fill=tk.X, pady=20)

            tk.Button(btn_frame, text="Cancelar", command=cancelar, width=15).pack(side=tk.LEFT)
            tk.Button(
                btn_frame, text="💾 Guardar", command=guardar,
                bg='#E31837', fg='white', font=('Segoe UI', 10, 'bold'), width=15
            ).pack(side=tk.RIGHT)

            root.mainloop()

            return credenciales_guardadas['valor']

        except Exception as e:
            imprimir_mensaje(f"Error en formulario: {e}", 'error')
            return False
    else:
        imprimir_mensaje("No se encontró el instalador para credenciales", 'error')
        return False


def ejecutar_sac():
    """Ejecuta el sistema SAC principal via Script Maestro GUI"""
    imprimir_mensaje("Iniciando SAC via Script Maestro GUI...", 'proceso')
    print()

    # Priorizar el nuevo script maestro GUI
    master_gui_path = BASE_DIR / 'sac_master_gui.py'
    master_path = BASE_DIR / 'sac_master.py'
    main_path = BASE_DIR / 'main.py'

    # Determinar cual ejecutar en orden de prioridad
    if master_gui_path.exists():
        script_a_ejecutar = master_gui_path
        imprimir_mensaje("Usando Script Maestro GUI v3.0", 'info')
    elif master_path.exists():
        script_a_ejecutar = master_path
        imprimir_mensaje("Usando Script Maestro v2.0", 'info')
    elif main_path.exists():
        script_a_ejecutar = main_path
        imprimir_mensaje("Usando main.py (modo basico)", 'info')
    else:
        imprimir_mensaje("No se encontro ningun punto de entrada", 'error')
        return False

    try:
        # Ejecutar SAC
        resultado = subprocess.run(
            [sys.executable, str(script_a_ejecutar)],
            cwd=str(BASE_DIR)
        )
        return resultado.returncode == 0

    except KeyboardInterrupt:
        print()
        imprimir_mensaje("SAC finalizado por el usuario", 'info')
        return True
    except Exception as e:
        imprimir_mensaje(f"Error ejecutando SAC: {e}", 'error')
        return False


def menu_espera_credenciales():
    """Muestra un menú cuando el sistema espera credenciales"""
    while True:
        imprimir_banner()
        print(f"""
  {Colores.AMARILLO}╔══════════════════════════════════════════════════════════════╗
  ║  ⏳ SAC INSTALADO - ESPERANDO CONFIGURACIÓN DE CREDENCIALES  ║
  ╚══════════════════════════════════════════════════════════════╝{Colores.RESET}

  El sistema está instalado y listo, pero necesita credenciales
  para conectarse a la base de datos y enviar correos.

  {Colores.CYAN}Opciones disponibles:{Colores.RESET}

    {Colores.VERDE}[1]{Colores.RESET} 🔐 Configurar credenciales ahora
    {Colores.VERDE}[2]{Colores.RESET} 📝 Editar archivo .env manualmente
    {Colores.VERDE}[3]{Colores.RESET} ✅ Verificar estado del sistema
    {Colores.VERDE}[4]{Colores.RESET} 🚀 Intentar ejecutar SAC (sin credenciales completas)
    {Colores.VERDE}[0]{Colores.RESET} ❌ Salir

""")
        try:
            opcion = input(f"  {Colores.CYAN}Seleccione una opción: {Colores.RESET}").strip()

            if opcion == '1':
                if solicitar_credenciales():
                    imprimir_mensaje("Credenciales configuradas", 'exito')
                    input(f"\n  {Colores.CYAN}Presione Enter para continuar...{Colores.RESET}")
                    return True  # Continuar a ejecutar SAC

            elif opcion == '2':
                env_file = BASE_DIR / '.env'
                if not env_file.exists():
                    # Crear desde template
                    env_template = BASE_DIR / 'env'
                    if env_template.exists():
                        import shutil
                        shutil.copy(env_template, env_file)
                        imprimir_mensaje(f"Archivo .env creado desde template", 'exito')
                    else:
                        imprimir_mensaje("No se encontró template de .env", 'error')
                        continue

                imprimir_mensaje(f"Archivo .env ubicado en:", 'info')
                print(f"    {env_file}")
                imprimir_mensaje("Edite el archivo con sus credenciales y vuelva a ejecutar", 'info')
                input(f"\n  {Colores.CYAN}Presione Enter para continuar...{Colores.RESET}")

            elif opcion == '3':
                instalado, tiene_creds, mensaje = verificar_instalacion_completa()
                print()
                imprimir_mensaje(f"Estado: {mensaje}", 'exito' if tiene_creds else 'advertencia')
                imprimir_mensaje(f"Instalado: {'Sí' if instalado else 'No'}", 'info')
                imprimir_mensaje(f"Credenciales: {'Configuradas' if tiene_creds else 'Pendientes'}", 'info')
                input(f"\n  {Colores.CYAN}Presione Enter para continuar...{Colores.RESET}")

            elif opcion == '4':
                imprimir_mensaje("Intentando ejecutar SAC...", 'proceso')
                ejecutar_sac()
                input(f"\n  {Colores.CYAN}Presione Enter para continuar...{Colores.RESET}")

            elif opcion == '0':
                imprimir_mensaje("Hasta pronto. SAC sigue instalado y esperando credenciales.", 'info')
                return False

        except KeyboardInterrupt:
            print()
            return False


def main():
    """Punto de entrada principal de SAC"""
    imprimir_banner()

    # Verificar Python
    if not verificar_python():
        sys.exit(1)

    imprimir_mensaje("Verificando estado del sistema...", 'proceso')
    print()

    # Verificar estado de instalación
    instalado, tiene_credenciales, mensaje = verificar_instalacion_completa()

    if not instalado:
        # Sistema NO instalado - Ejecutar instalador automatizado
        imprimir_mensaje(mensaje, 'advertencia')
        print()
        imprimir_mensaje("Iniciando instalación automatizada completa...", 'proceso')
        print()

        print(f"""
  {Colores.CYAN}╔══════════════════════════════════════════════════════════════╗
  ║           🚀 INSTALACIÓN AUTOMATIZADA DE SAC                 ║
  ╠══════════════════════════════════════════════════════════════╣
  ║                                                              ║
  ║  El sistema ejecutará automáticamente:                       ║
  ║                                                              ║
  ║   1. ✅ Verificación de requisitos                           ║
  ║   2. ✅ Actualización de herramientas                        ║
  ║   3. ✅ Instalación de dependencias                          ║
  ║   4. ✅ Creación de estructura                               ║
  ║   5. ✅ Verificación del sistema                             ║
  ║   6. ✅ Compilación de ejecutable                            ║
  ║   7. 🔐 Configuración de credenciales (AL FINAL)             ║
  ║                                                              ║
  ║  No se requiere intervención hasta el paso final.            ║
  ║                                                              ║
  ╚══════════════════════════════════════════════════════════════╝
{Colores.RESET}
""")

        try:
            input(f"  {Colores.CYAN}Presione Enter para iniciar la instalación...{Colores.RESET}")
        except KeyboardInterrupt:
            print()
            imprimir_mensaje("Instalación cancelada", 'advertencia')
            sys.exit(0)

        # Ejecutar instalador
        if ejecutar_instalador():
            imprimir_mensaje("Instalación completada", 'exito')

            # Re-verificar
            instalado, tiene_credenciales, mensaje = verificar_instalacion_completa()
        else:
            imprimir_mensaje("La instalación no se completó correctamente", 'error')
            sys.exit(1)

    # Sistema instalado pero sin credenciales
    if instalado and not tiene_credenciales:
        imprimir_mensaje("Sistema instalado - Esperando credenciales", 'espera')
        print()

        if menu_espera_credenciales():
            # Re-verificar después de configurar credenciales
            _, tiene_credenciales, _ = verificar_instalacion_completa()

    # Sistema completamente listo
    if instalado and tiene_credenciales:
        imprimir_mensaje("Sistema completamente configurado", 'exito')
        print()

        print(f"""
  {Colores.VERDE}╔══════════════════════════════════════════════════════════════╗
  ║              ✅ SAC LISTO PARA EJECUTAR                      ║
  ╚══════════════════════════════════════════════════════════════╝{Colores.RESET}
""")

        try:
            input(f"  {Colores.CYAN}Presione Enter para iniciar SAC...{Colores.RESET}")
        except KeyboardInterrupt:
            print()
            imprimir_mensaje("Hasta pronto", 'info')
            sys.exit(0)

        # Ejecutar SAC
        ejecutar_sac()

    print()
    imprimir_mensaje("Sesión de SAC finalizada", 'info')


# ═══════════════════════════════════════════════════════════════════════════════
# EJECUCIÓN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print()
        print(f"\n  {Colores.AMARILLO}👋 Hasta pronto - SAC{Colores.RESET}\n")
    except Exception as e:
        print(f"\n  {Colores.ROJO}❌ Error inesperado: {e}{Colores.RESET}\n")
        sys.exit(1)
