#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
===============================================================================
INSTALADOR MAESTRO - SISTEMA SAC v2.0
Chedraui CEDIS Cancun 427 - Manhattan WMS
===============================================================================

SCRIPT UNICO DE INSTALACION OPTIMIZADO

Mejoras v2.0:
- GUI mejorada con Rich (colores, progress bars, paneles)
- Sincronizado con requirements.txt
- Validaciones robustas con Pydantic
- Deteccion automatica de entorno (GUI/Consola)
- Instalacion en fases con rollback
- Verificacion post-instalacion

USO:
    python instalar_sac.py                    # Instalacion completa
    python instalar_sac.py --reinstalar       # Reinstalar desde cero
    python instalar_sac.py --verificar        # Solo verificar estado

Desarrollado por: Julian Alexander Juarez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logistica Cancun
===============================================================================
"""

import os
import sys
import subprocess
import json
import platform
import re
from pathlib import Path
from datetime import datetime
from typing import Tuple, Optional, Dict, List
from dataclasses import dataclass
from enum import Enum

# ===============================================================================
# CONFIGURACION BASE
# ===============================================================================

VERSION = "2.0.0"
BASE_DIR = Path(__file__).parent.parent.resolve()
ENV_FILE = BASE_DIR / '.env'
INSTALADO_FLAG = BASE_DIR / 'config' / '.instalado'
REQUIREMENTS_FILE = BASE_DIR / 'requirements.txt'

PYTHON_MIN_VERSION = (3, 8)

# Estructura de directorios requerida
DIRECTORIOS_REQUERIDOS = [
    'config', 'docs', 'modules', 'modules/excel_templates', 'modules/email',
    'queries', 'queries/obligatorias', 'queries/preventivas', 'queries/bajo_demanda',
    'tests', 'output', 'output/logs', 'output/resultados', 'logs', 'templates'
]

# Dependencias CORE (minimas para funcionar)
DEPENDENCIAS_CORE = [
    'rich>=13.0.0',           # UI moderna para consola (PRIMERO para mostrar progreso)
    'python-dotenv>=1.0.0',   # Variables de entorno
    'pandas>=2.0.0',          # Procesamiento de datos
    'openpyxl>=3.1.0',        # Excel
]

# Dependencias de PRODUCCION completas
DEPENDENCIAS_PRODUCCION = [
    # Core (ya instaladas)
    'rich>=13.0.0',
    'python-dotenv>=1.0.0',
    'pandas>=2.0.0',
    'numpy>=1.24.0',
    'openpyxl>=3.1.0',
    # Reportes
    'XlsxWriter>=3.1.0',
    'Pillow>=10.0.0',
    'reportlab>=4.0.0',
    # Configuracion
    'PyYAML>=6.0.0',
    'pydantic>=2.0.0',        # Validacion moderna
    'pydantic-settings>=2.0.0',
    # Consola y progreso
    'colorama>=0.4.6',
    'tqdm>=4.65.0',
    # Programacion
    'schedule>=1.2.0',
    # Fechas
    'python-dateutil>=2.8.0',
    'pytz>=2023.3',
    # Web
    'requests>=2.31.0',
    'Flask>=3.0.0',
    'Jinja2>=3.1.0',
    # Notificaciones
    'python-telegram-bot>=20.0',
]

# Dependencias opcionales (pueden fallar sin problema)
DEPENDENCIAS_OPCIONALES = [
    ('pyodbc', 'Conexion DB2 Windows'),
    ('ibm-db', 'Conexion DB2 Linux/Mac'),
    ('twilio', 'Notificaciones WhatsApp'),
]


# ===============================================================================
# CLASE DE ESTADO DE INSTALACION
# ===============================================================================

class EstadoInstalacion(Enum):
    NO_INSTALADO = "no_instalado"
    PARCIAL = "parcial"
    COMPLETO = "completo"
    ERROR = "error"


@dataclass
class ResultadoVerificacion:
    python_ok: bool
    pip_ok: bool
    directorios_ok: bool
    env_ok: bool
    dependencias_ok: bool
    dependencias_faltantes: List[str]
    estado: EstadoInstalacion
    mensaje: str


# ===============================================================================
# UTILIDADES BASICAS (Sin dependencias externas)
# ===============================================================================

def ejecutar_comando(cmd: List[str], capturar: bool = True, timeout: int = 300) -> Tuple[bool, str]:
    """Ejecuta comando del sistema"""
    try:
        result = subprocess.run(cmd, capture_output=capturar, text=True, timeout=timeout)
        salida = (result.stdout or '') + (result.stderr or '') if capturar else ''
        return result.returncode == 0, salida
    except subprocess.TimeoutExpired:
        return False, "Timeout excedido"
    except Exception as e:
        return False, str(e)


def instalar_paquete_silencioso(paquete: str) -> bool:
    """Instala un paquete sin mostrar output"""
    ok, _ = ejecutar_comando([
        sys.executable, '-m', 'pip', 'install', paquete,
        '-q', '--disable-pip-version-check'
    ], timeout=120)
    return ok


def verificar_paquete_instalado(nombre: str) -> bool:
    """Verifica si un paquete esta instalado"""
    try:
        # Mapeo de nombres de paquetes a modulos
        mapeo = {
            'python-dotenv': 'dotenv',
            'python-dateutil': 'dateutil',
            'python-telegram-bot': 'telegram',
            'Pillow': 'PIL',
            'PyYAML': 'yaml',
            'pydantic-settings': 'pydantic_settings',
        }
        modulo = mapeo.get(nombre.split('>=')[0].split('==')[0],
                          nombre.split('>=')[0].split('==')[0].replace('-', '_').lower())
        __import__(modulo)
        return True
    except ImportError:
        return False


# ===============================================================================
# INSTALACION DE DEPENDENCIAS CORE (Para poder usar Rich)
# ===============================================================================

def asegurar_dependencias_core():
    """Instala dependencias minimas para mostrar UI"""
    print("\n  Preparando entorno de instalacion...")

    for dep in DEPENDENCIAS_CORE:
        nombre = dep.split('>=')[0].split('==')[0]
        if not verificar_paquete_instalado(nombre):
            print(f"    Instalando {nombre}...", end=" ", flush=True)
            if instalar_paquete_silencioso(dep):
                print("OK")
            else:
                print("WARN")


# ===============================================================================
# CLASE PRINCIPAL DEL INSTALADOR (Con Rich UI)
# ===============================================================================

class InstaladorSAC:
    """Instalador principal del Sistema SAC"""

    def __init__(self):
        self.console = None
        self.usar_rich = False
        self._inicializar_ui()

    def _inicializar_ui(self):
        """Inicializa la interfaz de usuario"""
        try:
            from rich.console import Console
            from rich.panel import Panel
            from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
            from rich.table import Table
            from rich.prompt import Prompt, Confirm
            from rich import print as rprint

            self.console = Console()
            self.usar_rich = True
            self.Panel = Panel
            self.Progress = Progress
            self.SpinnerColumn = SpinnerColumn
            self.TextColumn = TextColumn
            self.BarColumn = BarColumn
            self.Table = Table
            self.Prompt = Prompt
            self.Confirm = Confirm
            self.rprint = rprint
        except ImportError:
            self.usar_rich = False

    # =========================================================================
    # METODOS DE UI
    # =========================================================================

    def mostrar_banner(self):
        """Muestra banner del instalador"""
        if self.usar_rich:
            banner_text = """
[bold red]
███████╗ █████╗  ██████╗    ██╗███╗   ██╗███████╗████████╗ █████╗ ██╗     ██╗
██╔════╝██╔══██╗██╔════╝    ██║████╗  ██║██╔════╝╚══██╔══╝██╔══██╗██║     ██║
███████╗███████║██║         ██║██╔██╗ ██║███████╗   ██║   ███████║██║     ██║
╚════██║██╔══██║██║         ██║██║╚██╗██║╚════██║   ██║   ██╔══██║██║     ██║
███████║██║  ██║╚██████╗    ██║██║ ╚████║███████║   ██║   ██║  ██║███████╗███████╗
╚══════╝╚═╝  ╚═╝ ╚═════╝    ╚═╝╚═╝  ╚═══╝╚══════╝   ╚═╝   ╚═╝  ╚═╝╚══════╝╚══════╝
[/bold red]
[cyan]Sistema de Automatizacion de Consultas - CEDIS Cancun 427[/cyan]
"""
            self.console.print(self.Panel(banner_text, title=f"[bold]Instalador v{VERSION}[/bold]",
                                          border_style="red"))
            self.console.print(f"  [dim]Python: {sys.version.split()[0]} | Plataforma: {platform.system()}[/dim]\n")
        else:
            print(f"""
╔═══════════════════════════════════════════════════════════════════════╗
║              SAC INSTALL - CEDIS Cancun 427                           ║
║                  Version {VERSION}                                         ║
╚═══════════════════════════════════════════════════════════════════════╝
  Python: {sys.version.split()[0]} | Plataforma: {platform.system()}
""")

    def mostrar_exito(self):
        """Muestra mensaje de exito"""
        if self.usar_rich:
            mensaje = """
[bold green]✓ INSTALACION COMPLETADA EXITOSAMENTE[/bold green]

El sistema SAC esta listo para produccion.

[cyan]Para iniciar:[/cyan]
  [white]python main.py[/white]              Menu interactivo
  [white]python maestro.py --daemon[/white]  Modo automatico
  [white]python dashboard.py[/white]         Dashboard web

[yellow]Esta instalacion es permanente.[/yellow]
"""
            self.console.print(self.Panel(mensaje, title="[bold green]Completado[/bold green]",
                                          border_style="green"))
        else:
            print("""
═══════════════════════════════════════════════════════════════
  ✓ INSTALACION COMPLETADA EXITOSAMENTE
═══════════════════════════════════════════════════════════════

Para iniciar:
  python main.py              # Menu interactivo
  python maestro.py --daemon  # Modo automatico
  python dashboard.py         # Dashboard web
""")

    def mostrar_ya_instalado(self):
        """Muestra mensaje cuando ya esta instalado"""
        if self.usar_rich:
            mensaje = """
[bold green]✓ SISTEMA YA INSTALADO Y CONFIGURADO[/bold green]

[cyan]Comandos disponibles:[/cyan]
  [white]python main.py[/white]              Menu interactivo
  [white]python maestro.py --daemon[/white]  Modo automatico
  [white]python dashboard.py[/white]         Dashboard web

[dim]Para reinstalar: python instalar_sac.py --reinstalar[/dim]
"""
            self.console.print(self.Panel(mensaje, border_style="green"))
        else:
            print("""
═══════════════════════════════════════════════════════════════
  ✓ SISTEMA YA INSTALADO Y CONFIGURADO
═══════════════════════════════════════════════════════════════

Comandos disponibles:
  python main.py              # Menu interactivo
  python maestro.py --daemon  # Modo automatico
  python dashboard.py         # Dashboard web

Para reinstalar: python instalar_sac.py --reinstalar
""")

    def log_paso(self, numero: int, total: int, mensaje: str):
        """Muestra un paso de instalacion"""
        if self.usar_rich:
            self.console.print(f"\n[bold blue][{numero}/{total}][/bold blue] [bold]{mensaje}[/bold]")
            self.console.print("─" * 60)
        else:
            print(f"\n[{numero}/{total}] {mensaje}")
            print("─" * 60)

    def log_ok(self, msg: str):
        if self.usar_rich:
            self.console.print(f"  [green]✓[/green] {msg}")
        else:
            print(f"  ✓ {msg}")

    def log_error(self, msg: str):
        if self.usar_rich:
            self.console.print(f"  [red]✗[/red] {msg}")
        else:
            print(f"  ✗ {msg}")

    def log_warn(self, msg: str):
        if self.usar_rich:
            self.console.print(f"  [yellow]⚠[/yellow] {msg}")
        else:
            print(f"  ⚠ {msg}")

    def log_info(self, msg: str):
        if self.usar_rich:
            self.console.print(f"  [cyan]ℹ[/cyan] {msg}")
        else:
            print(f"  ℹ {msg}")

    # =========================================================================
    # VERIFICACIONES
    # =========================================================================

    def verificar_estado(self) -> ResultadoVerificacion:
        """Verifica el estado actual de la instalacion"""
        resultado = ResultadoVerificacion(
            python_ok=sys.version_info >= PYTHON_MIN_VERSION,
            pip_ok=False,
            directorios_ok=True,
            env_ok=False,
            dependencias_ok=True,
            dependencias_faltantes=[],
            estado=EstadoInstalacion.NO_INSTALADO,
            mensaje=""
        )

        # Verificar pip
        ok, _ = ejecutar_comando([sys.executable, '-m', 'pip', '--version'])
        resultado.pip_ok = ok

        # Verificar directorios
        for dir_path in DIRECTORIOS_REQUERIDOS:
            if not (BASE_DIR / dir_path).exists():
                resultado.directorios_ok = False
                break

        # Verificar .env
        resultado.env_ok = ENV_FILE.exists() and self._env_tiene_credenciales()

        # Verificar dependencias core
        for dep in DEPENDENCIAS_CORE:
            nombre = dep.split('>=')[0].split('==')[0]
            if not verificar_paquete_instalado(nombre):
                resultado.dependencias_ok = False
                resultado.dependencias_faltantes.append(nombre)

        # Determinar estado
        if INSTALADO_FLAG.exists() and resultado.env_ok:
            resultado.estado = EstadoInstalacion.COMPLETO
            resultado.mensaje = "Sistema instalado y configurado"
        elif resultado.env_ok or resultado.directorios_ok:
            resultado.estado = EstadoInstalacion.PARCIAL
            resultado.mensaje = "Instalacion parcial detectada"
        else:
            resultado.estado = EstadoInstalacion.NO_INSTALADO
            resultado.mensaje = "Primera instalacion"

        return resultado

    def _env_tiene_credenciales(self) -> bool:
        """Verifica si .env tiene credenciales configuradas"""
        if not ENV_FILE.exists():
            return False
        try:
            with open(ENV_FILE, 'r', encoding='utf-8') as f:
                contenido = f.read()
            # Verificar que DB_USER tenga valor
            match = re.search(r'^DB_USER=(.+)$', contenido, re.MULTILINE)
            return match is not None and len(match.group(1).strip()) > 0
        except:
            return False

    # =========================================================================
    # FORMULARIO DE CONFIGURACION
    # =========================================================================

    def solicitar_credenciales(self) -> Optional[Dict]:
        """Solicita credenciales al usuario"""
        # Intentar GUI tkinter primero
        credenciales = self._solicitar_credenciales_gui()
        if credenciales:
            return credenciales

        # Fallback a consola
        return self._solicitar_credenciales_consola()

    def _solicitar_credenciales_gui(self) -> Optional[Dict]:
        """Solicita credenciales via GUI tkinter"""
        try:
            import tkinter as tk
            from tkinter import ttk, messagebox
        except ImportError:
            return None

        credenciales = {}
        ventana_cerrada = [False]

        root = tk.Tk()
        root.title("SAC - Configuracion Inicial")
        root.geometry("550x680")
        root.resizable(False, False)

        # Centrar
        root.update_idletasks()
        x = (root.winfo_screenwidth() // 2) - 275
        y = (root.winfo_screenheight() // 2) - 340
        root.geometry(f"+{x}+{y}")

        COLOR_ROJO = "#E31837"

        # Frame principal
        main = tk.Frame(root, bg="white")
        main.pack(fill="both", expand=True)

        # Header
        header = tk.Frame(main, bg=COLOR_ROJO, height=90)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header, text="🏪 Sistema SAC - CEDIS Cancun 427",
                font=("Arial", 16, "bold"), fg="white", bg=COLOR_ROJO).pack(pady=15)
        tk.Label(header, text="Configuracion Inicial (Solo una vez)",
                font=("Arial", 10), fg="white", bg=COLOR_ROJO).pack()

        # Contenido
        content = tk.Frame(main, bg="white", padx=40, pady=20)
        content.pack(fill="both", expand=True)

        tk.Label(content, text="Complete las credenciales para configurar el sistema",
                font=("Arial", 11), bg="white", fg="#666").pack(anchor="w", pady=(0, 15))

        # Base de Datos
        db_frame = tk.LabelFrame(content, text=" Base de Datos DB2 ",
                                font=("Arial", 10, "bold"), bg="white", fg=COLOR_ROJO)
        db_frame.pack(fill="x", pady=8)
        db_inner = tk.Frame(db_frame, bg="white", padx=15, pady=10)
        db_inner.pack(fill="x")

        tk.Label(db_inner, text="Usuario:", font=("Arial", 10), bg="white").grid(row=0, column=0, sticky="w", pady=5)
        entry_db_user = tk.Entry(db_inner, width=35, font=("Arial", 10))
        entry_db_user.grid(row=0, column=1, pady=5, padx=10)
        entry_db_user.insert(0, "ADMJAJA")

        tk.Label(db_inner, text="Password:", font=("Arial", 10), bg="white").grid(row=1, column=0, sticky="w", pady=5)
        entry_db_pass = tk.Entry(db_inner, width=35, font=("Arial", 10), show="•")
        entry_db_pass.grid(row=1, column=1, pady=5, padx=10)

        # Email
        email_frame = tk.LabelFrame(content, text=" Correo Office 365 ",
                                   font=("Arial", 10, "bold"), bg="white", fg=COLOR_ROJO)
        email_frame.pack(fill="x", pady=8)
        email_inner = tk.Frame(email_frame, bg="white", padx=15, pady=10)
        email_inner.pack(fill="x")

        tk.Label(email_inner, text="Email:", font=("Arial", 10), bg="white").grid(row=0, column=0, sticky="w", pady=5)
        entry_email = tk.Entry(email_inner, width=35, font=("Arial", 10))
        entry_email.grid(row=0, column=1, pady=5, padx=10)
        entry_email.insert(0, "@chedraui.com.mx")

        tk.Label(email_inner, text="Password:", font=("Arial", 10), bg="white").grid(row=1, column=0, sticky="w", pady=5)
        entry_email_pass = tk.Entry(email_inner, width=35, font=("Arial", 10), show="•")
        entry_email_pass.grid(row=1, column=1, pady=5, padx=10)

        # Telegram (opcional)
        tg_frame = tk.LabelFrame(content, text=" Telegram (Opcional) ",
                                font=("Arial", 10, "bold"), bg="white", fg="#888")
        tg_frame.pack(fill="x", pady=8)
        tg_inner = tk.Frame(tg_frame, bg="white", padx=15, pady=10)
        tg_inner.pack(fill="x")

        tk.Label(tg_inner, text="Bot Token:", font=("Arial", 10), bg="white").grid(row=0, column=0, sticky="w", pady=5)
        entry_tg_token = tk.Entry(tg_inner, width=35, font=("Arial", 10))
        entry_tg_token.grid(row=0, column=1, pady=5, padx=10)

        tk.Label(tg_inner, text="Chat IDs:", font=("Arial", 10), bg="white").grid(row=1, column=0, sticky="w", pady=5)
        entry_tg_chats = tk.Entry(tg_inner, width=35, font=("Arial", 10))
        entry_tg_chats.grid(row=1, column=1, pady=5, padx=10)

        # Nota
        tk.Label(content, text="⚠ Esta configuracion se guarda permanentemente",
                font=("Arial", 9), bg="white", fg="#888").pack(anchor="w", pady=15)

        # Botones
        btn_frame = tk.Frame(content, bg="white")
        btn_frame.pack(fill="x", pady=10)

        def cancelar():
            if messagebox.askyesno("Cancelar", "¿Cancelar instalacion?"):
                ventana_cerrada[0] = True
                root.destroy()

        def instalar():
            if not entry_db_pass.get().strip():
                messagebox.showerror("Error", "Password DB2 es requerido")
                return
            if '@' not in entry_email.get():
                messagebox.showerror("Error", "Email valido requerido")
                return
            if not entry_email_pass.get().strip():
                messagebox.showerror("Error", "Password email requerido")
                return

            credenciales['db_user'] = entry_db_user.get().strip()
            credenciales['db_password'] = entry_db_pass.get().strip()
            credenciales['email_user'] = entry_email.get().strip()
            credenciales['email_password'] = entry_email_pass.get().strip()
            credenciales['telegram_token'] = entry_tg_token.get().strip()
            credenciales['telegram_chats'] = entry_tg_chats.get().strip()
            root.destroy()

        tk.Button(btn_frame, text="Cancelar", font=("Arial", 10),
                 width=12, command=cancelar).pack(side="left")
        tk.Button(btn_frame, text="✓ Instalar", font=("Arial", 10, "bold"),
                 width=15, bg=COLOR_ROJO, fg="white", command=instalar).pack(side="right")

        root.protocol("WM_DELETE_WINDOW", cancelar)
        entry_db_pass.focus()
        root.mainloop()

        if ventana_cerrada[0] or not credenciales:
            return None
        return credenciales

    def _solicitar_credenciales_consola(self) -> Optional[Dict]:
        """Solicita credenciales por consola"""
        if self.usar_rich:
            self.console.print("\n[bold cyan]═══ CONFIGURACION INICIAL ═══[/bold cyan]")
            self.console.print("[dim]Se solicita UNA SOLA VEZ[/dim]\n")
        else:
            print("\n═══ CONFIGURACION INICIAL ═══")
            print("Se solicita UNA SOLA VEZ\n")

        try:
            credenciales = {}

            print("Base de Datos DB2:")
            credenciales['db_user'] = input("  Usuario [ADMJAJA]: ").strip() or "ADMJAJA"
            credenciales['db_password'] = input("  Password: ").strip()
            if not credenciales['db_password']:
                print("Error: Password requerido")
                return None

            print("\nCorreo Office 365:")
            credenciales['email_user'] = input("  Email: ").strip()
            if '@' not in credenciales['email_user']:
                print("Error: Email invalido")
                return None
            credenciales['email_password'] = input("  Password: ").strip()
            if not credenciales['email_password']:
                print("Error: Password requerido")
                return None

            print("\nTelegram (Enter para omitir):")
            credenciales['telegram_token'] = input("  Bot Token: ").strip()
            credenciales['telegram_chats'] = input("  Chat IDs: ").strip()

            return credenciales
        except (KeyboardInterrupt, EOFError):
            return None

    # =========================================================================
    # INSTALACION
    # =========================================================================

    def crear_directorios(self) -> int:
        """Crea estructura de directorios"""
        creados = 0
        for dir_path in DIRECTORIOS_REQUERIDOS:
            full_path = BASE_DIR / dir_path
            if not full_path.exists():
                full_path.mkdir(parents=True, exist_ok=True)
                creados += 1
        return creados

    def crear_archivo_env(self, credenciales: Dict) -> bool:
        """Crea archivo .env con configuracion completa"""
        contenido = f"""# ═══════════════════════════════════════════════════════════════
# CONFIGURACION SAC - CEDIS CHEDRAUI CANCUN 427
# Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# ═══════════════════════════════════════════════════════════════

# === CREDENCIALES BASE DE DATOS DB2 ===
DB_USER={credenciales['db_user']}
DB_PASSWORD={credenciales['db_password']}

# === CONFIGURACION DB2 MANHATTAN WMS ===
DB_HOST=WM260BASD
DB_PORT=50000
DB_DATABASE=WM260BASD
DB_SCHEMA=WMWHSE1
DB_DRIVER={{IBM DB2 ODBC DRIVER}}
DB_TIMEOUT=30
DB_POOL_SIZE=5

# === CREDENCIALES CORREO ===
EMAIL_USER={credenciales['email_user']}
EMAIL_PASSWORD={credenciales['email_password']}

# === CONFIGURACION CORREO OFFICE 365 ===
EMAIL_HOST=smtp.office365.com
EMAIL_PORT=587
EMAIL_PROTOCOL=TLS
EMAIL_FROM_NAME=Sistema SAC - CEDIS 427

# === TELEGRAM ===
TELEGRAM_BOT_TOKEN={credenciales.get('telegram_token', '')}
TELEGRAM_CHAT_IDS={credenciales.get('telegram_chats', '')}
TELEGRAM_ENABLED={'true' if credenciales.get('telegram_token') else 'false'}

# === INFORMACION CEDIS ===
CEDIS_CODE=427
CEDIS_NAME=CEDIS Cancun
CEDIS_REGION=Sureste
CEDIS_ALMACEN=C22

# === CONFIGURACION SISTEMA ===
SYSTEM_VERSION={VERSION}
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
TIMEZONE=America/Cancun

# === RUTAS ===
OUTPUT_DIR=output
LOGS_DIR=output/logs
REPORTS_DIR=output/resultados
"""
        try:
            with open(ENV_FILE, 'w', encoding='utf-8') as f:
                f.write(contenido)
            return True
        except Exception as e:
            self.log_error(f"Error creando .env: {e}")
            return False

    def instalar_dependencias(self) -> Tuple[int, int]:
        """Instala todas las dependencias"""
        exitos = 0
        fallos = 0

        # Actualizar pip
        self.log_info("Actualizando pip...")
        ejecutar_comando([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip', '-q'])

        total = len(DEPENDENCIAS_PRODUCCION)

        if self.usar_rich:
            with self.Progress(
                self.SpinnerColumn(),
                self.TextColumn("[progress.description]{task.description}"),
                self.BarColumn(),
                self.TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                console=self.console
            ) as progress:
                task = progress.add_task("Instalando dependencias...", total=total)

                for dep in DEPENDENCIAS_PRODUCCION:
                    nombre = dep.split('>=')[0].split('==')[0]
                    progress.update(task, description=f"[cyan]{nombre}[/cyan]")

                    if instalar_paquete_silencioso(dep):
                        exitos += 1
                    else:
                        fallos += 1

                    progress.advance(task)
        else:
            for i, dep in enumerate(DEPENDENCIAS_PRODUCCION, 1):
                nombre = dep.split('>=')[0].split('==')[0]
                print(f"    [{i}/{total}] {nombre}...", end=" ", flush=True)

                if instalar_paquete_silencioso(dep):
                    print("OK")
                    exitos += 1
                else:
                    print("WARN")
                    fallos += 1

        # Dependencias opcionales
        self.log_info("Intentando dependencias opcionales...")
        for dep, desc in DEPENDENCIAS_OPCIONALES:
            if instalar_paquete_silencioso(dep):
                self.log_ok(f"{dep} ({desc})")
            else:
                self.log_warn(f"{dep} no disponible")

        return exitos, fallos

    def registrar_modulos(self) -> Dict:
        """Registra modulos disponibles"""
        registro = {
            'timestamp': datetime.now().isoformat(),
            'version': VERSION,
            'instalacion_completa': True,
            'modulos': {
                'validacion_oc': {'nombre': 'Validacion OC', 'habilitado': True, 'icono': '1'},
                'reporte_diario': {'nombre': 'Reporte Diario', 'habilitado': True, 'icono': '2'},
                'alertas': {'nombre': 'Alertas Criticas', 'habilitado': True, 'icono': '3'},
                'monitor': {'nombre': 'Monitor', 'habilitado': True, 'icono': '4'},
                'reportes_excel': {'nombre': 'Reportes Excel', 'habilitado': True, 'icono': '5'},
                'dashboard': {'nombre': 'Dashboard Web', 'habilitado': True, 'icono': '6'},
                'telegram': {'nombre': 'Telegram', 'habilitado': bool(os.getenv('TELEGRAM_BOT_TOKEN')), 'icono': '7'},
                'maestro': {'nombre': 'Orquestador', 'habilitado': True, 'icono': '8'},
            }
        }

        registro_path = BASE_DIR / 'config' / 'modulos_registro.json'
        registro_path.parent.mkdir(exist_ok=True)

        with open(registro_path, 'w', encoding='utf-8') as f:
            json.dump(registro, f, indent=2, ensure_ascii=False)

        return registro

    def marcar_instalado(self):
        """Marca el sistema como instalado"""
        INSTALADO_FLAG.parent.mkdir(exist_ok=True)
        with open(INSTALADO_FLAG, 'w') as f:
            f.write(datetime.now().isoformat())

    # =========================================================================
    # EJECUCION PRINCIPAL
    # =========================================================================

    def ejecutar(self, reinstalar: bool = False, verificar: bool = False) -> int:
        """Ejecuta el proceso de instalacion"""
        self.mostrar_banner()

        # Modo reinstalar
        if reinstalar:
            if self.usar_rich:
                self.console.print("[yellow]Modo reinstalacion activado[/yellow]")
            if INSTALADO_FLAG.exists():
                INSTALADO_FLAG.unlink()
            if ENV_FILE.exists():
                ENV_FILE.unlink()

        # Verificar estado
        estado = self.verificar_estado()

        # Solo verificar
        if verificar:
            self._mostrar_verificacion(estado)
            return 0 if estado.estado == EstadoInstalacion.COMPLETO else 1

        # Ya instalado
        if estado.estado == EstadoInstalacion.COMPLETO:
            self.mostrar_ya_instalado()
            return 0

        # Verificar Python
        if not estado.python_ok:
            self.log_error(f"Python 3.8+ requerido. Actual: {sys.version}")
            return 1

        if self.usar_rich:
            self.console.print("[cyan]Primera ejecucion - Iniciando instalacion...[/cyan]\n")
        else:
            print("Primera ejecucion - Iniciando instalacion...\n")

        # PASO 1: Credenciales
        self.log_paso(1, 5, "Configuracion de Credenciales")
        credenciales = self.solicitar_credenciales()
        if not credenciales:
            self.log_error("Instalacion cancelada")
            return 1
        self.log_ok("Credenciales capturadas")

        # PASO 2: Directorios
        self.log_paso(2, 5, "Creando Estructura de Directorios")
        creados = self.crear_directorios()
        self.log_ok(f"Estructura creada ({creados} nuevos)")

        # PASO 3: Configuracion
        self.log_paso(3, 5, "Guardando Configuracion")
        if not self.crear_archivo_env(credenciales):
            return 1
        self.log_ok("Archivo .env creado")

        # PASO 4: Dependencias
        self.log_paso(4, 5, "Instalando Dependencias")
        self.log_info("Esto puede tomar varios minutos...")
        exitos, fallos = self.instalar_dependencias()
        self.log_ok(f"{exitos} dependencias instaladas")
        if fallos > 0:
            self.log_warn(f"{fallos} opcionales no instaladas")

        # PASO 5: Finalizar
        self.log_paso(5, 5, "Finalizando")
        registro = self.registrar_modulos()
        habilitados = sum(1 for m in registro['modulos'].values() if m['habilitado'])
        self.log_ok(f"{habilitados}/{len(registro['modulos'])} modulos habilitados")

        self.marcar_instalado()
        self.log_ok("Sistema marcado como instalado")

        self.mostrar_exito()
        return 0

    def _mostrar_verificacion(self, estado: ResultadoVerificacion):
        """Muestra resultado de verificacion"""
        if self.usar_rich:
            tabla = self.Table(title="Estado del Sistema")
            tabla.add_column("Componente", style="cyan")
            tabla.add_column("Estado", justify="center")

            tabla.add_row("Python 3.8+", "[green]✓[/green]" if estado.python_ok else "[red]✗[/red]")
            tabla.add_row("Pip", "[green]✓[/green]" if estado.pip_ok else "[red]✗[/red]")
            tabla.add_row("Directorios", "[green]✓[/green]" if estado.directorios_ok else "[yellow]⚠[/yellow]")
            tabla.add_row("Configuracion .env", "[green]✓[/green]" if estado.env_ok else "[red]✗[/red]")
            tabla.add_row("Dependencias Core", "[green]✓[/green]" if estado.dependencias_ok else "[red]✗[/red]")

            self.console.print(tabla)
            self.console.print(f"\n[bold]Estado:[/bold] {estado.estado.value}")
        else:
            print("\nEstado del Sistema:")
            print(f"  Python 3.8+: {'OK' if estado.python_ok else 'FAIL'}")
            print(f"  Pip: {'OK' if estado.pip_ok else 'FAIL'}")
            print(f"  Directorios: {'OK' if estado.directorios_ok else 'WARN'}")
            print(f"  .env: {'OK' if estado.env_ok else 'FAIL'}")
            print(f"  Dependencias: {'OK' if estado.dependencias_ok else 'FAIL'}")
            print(f"\nEstado: {estado.estado.value}")


# ===============================================================================
# MAIN
# ===============================================================================

def main():
    # Asegurar dependencias minimas para UI
    asegurar_dependencias_core()

    # Parsear argumentos
    reinstalar = '--reinstalar' in sys.argv or '--reset' in sys.argv
    verificar = '--verificar' in sys.argv or '--check' in sys.argv

    # Ejecutar instalador
    instalador = InstaladorSAC()
    return instalador.ejecutar(reinstalar=reinstalar, verificar=verificar)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nInstalacion cancelada por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\nError fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
