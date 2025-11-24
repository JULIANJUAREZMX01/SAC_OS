#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
===============================================================================
MODULO DE CONFIGURACION DE CREDENCIALES - SISTEMA SAC v2.0
Sistema de Automatizacion de Consultas - CEDIS Cancun 427
===============================================================================

Formulario interactivo para configurar TODAS las credenciales del sistema
durante la carga inicial. Este modulo garantiza que las credenciales se
soliciten UNA SOLA VEZ al inicio y no despues.

Incluye:
- Formulario interactivo con animaciones
- Validacion de credenciales en tiempo real
- Introduccion animada sobre funcionalidades
- Animaciones divertidas y unicas estilo ADMJAJA

USO:
    from modules.modulo_credenciales_setup import ejecutar_setup_credenciales

    resultado = ejecutar_setup_credenciales()
    if resultado['configurado']:
        # Sistema listo para operar
        pass

Desarrollado por: Julian Alexander Juarez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logistica Cancun

"Las maquinas y los sistemas al servicio de los analistas"
===============================================================================
"""

import os
import sys
import time
import random
import getpass
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# Directorio base del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent


# ===============================================================================
# COLORES Y UTILIDADES DE TERMINAL
# ===============================================================================

class Colores:
    """Codigos de colores ANSI para terminal"""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    BLINK = '\033[5m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_BLUE = '\033[44m'


def limpiar_pantalla():
    """Limpia la pantalla de la terminal."""
    os.system('cls' if os.name == 'nt' else 'clear')


def ocultar_cursor():
    """Oculta el cursor de la terminal."""
    print("\033[?25l", end="", flush=True)


def mostrar_cursor():
    """Muestra el cursor de la terminal."""
    print("\033[?25h", end="", flush=True)


def c(texto: str, color: str) -> str:
    """Aplica color al texto."""
    return f"{color}{texto}{Colores.RESET}"


# ===============================================================================
# ANIMACIONES DIVERTIDAS Y UNICAS
# ===============================================================================

# Frases motivacionales del creador
FRASES_ADMJAJA = [
    "Las maquinas y los sistemas al servicio de los analistas",
    "Automatizando lo tedioso, liberando lo creativo",
    "Cada linea de codigo es un paso hacia la eficiencia",
    "El SAC nunca duerme, siempre vigilando",
    "Hecho con amor en CEDIS Cancun 427",
    "La tecnologia al servicio del CEDIS",
    "Menos clicks, mas resultados",
    "Validando datos mientras tu tomas cafe",
]

# Emojis para animaciones
EMOJIS_CARGA = ["📦", "🚛", "📊", "🔍", "📧", "💾", "⚡", "🎯", "✨", "🔧"]
EMOJIS_EXITO = ["✅", "🎉", "🚀", "💪", "🌟", "🏆", "👏", "🙌"]
EMOJIS_ERROR = ["❌", "⚠️", "🔴", "💥"]

# Spinner divertidos
SPINNERS = {
    'camion': ["🚛💨    ", " 🚛💨   ", "  🚛💨  ", "   🚛💨 ", "    🚛💨", "     🚛"],
    'montacargas': ["🏗️⬆️ ", "🏗️⬇️ ", "🏗️➡️ ", "🏗️⬅️ "],
    'cajas': ["📦    📦", " 📦  📦 ", "  📦📦  ", " 📦  📦 "],
    'dots': ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"],
    'bars': ["▏", "▎", "▍", "▌", "▋", "▊", "▉", "█", "▉", "▊", "▋", "▌", "▍", "▎"],
    'bounce': ["⠁", "⠂", "⠄", "⡀", "⢀", "⠠", "⠐", "⠈"],
}


def animar_texto_escritura(texto: str, delay: float = 0.03):
    """Anima el texto como si se estuviera escribiendo."""
    for char in texto:
        print(char, end='', flush=True)
        time.sleep(delay)
    print()


def mostrar_barra_progreso(actual: int, total: int, ancho: int = 40, mensaje: str = ""):
    """Muestra barra de progreso animada."""
    progreso = actual / total if total > 0 else 0
    lleno = int(ancho * progreso)
    vacio = ancho - lleno

    barra = c("█" * lleno, Colores.GREEN) + c("░" * vacio, Colores.BLUE)
    porcentaje = f"{progreso * 100:5.1f}%"

    emoji = random.choice(EMOJIS_CARGA)
    print(f"\r   {emoji} [{barra}] {c(porcentaje, Colores.YELLOW)} {mensaje}    ", end='', flush=True)


def animar_spinner(mensaje: str, duracion: float = 2.0, tipo: str = 'camion'):
    """Muestra animacion de spinner."""
    try:
        ocultar_cursor()
        frames = SPINNERS.get(tipo, SPINNERS['dots'])
        inicio = time.time()
        idx = 0

        while time.time() - inicio < duracion:
            frame = frames[idx % len(frames)]
            print(f"\r   {frame} {mensaje}...    ", end='', flush=True)
            idx += 1
            time.sleep(0.1)

        print(f"\r   {c('✓', Colores.GREEN)} {mensaje}... Listo!    ")
    finally:
        mostrar_cursor()


# ===============================================================================
# INTRODUCCION ANIMADA DEL SISTEMA
# ===============================================================================

def mostrar_intro_animada():
    """
    Muestra una introduccion animada en ASCII sobre las funcionalidades del SAC.
    Esta es la primera pantalla que ve el usuario al iniciar el sistema.
    """
    try:
        ocultar_cursor()
        limpiar_pantalla()

        # Banner principal con efecto
        banner_frames = [
            f"""
{Colores.RED}
   ███████╗ █████╗  ██████╗
   ██╔════╝██╔══██╗██╔════╝
   ███████╗███████║██║
   ╚════██║██╔══██║██║
   ███████║██║  ██║╚██████╗
   ╚══════╝╚═╝  ╚═╝ ╚═════╝
{Colores.RESET}""",
        ]

        for frame in banner_frames:
            print(frame)
            time.sleep(0.2)

        # Subtitulo animado
        subtitulo = "Sistema de Automatizacion de Consultas - CEDIS Cancun 427"
        print(f"\n   {Colores.CYAN}", end='')
        animar_texto_escritura(subtitulo, 0.02)
        print(Colores.RESET)

        time.sleep(0.3)

        # Caja de funcionalidades
        print(f"""
   {Colores.YELLOW}╔═══════════════════════════════════════════════════════════════════╗
   ║                    🚛 FUNCIONALIDADES DEL SAC 🚛                  ║
   ╚═══════════════════════════════════════════════════════════════════╝{Colores.RESET}
""")

        funcionalidades = [
            ("📊", "Validacion OC vs Distribuciones", "Compara ordenes contra distribuciones"),
            ("🔍", "Monitoreo en Tiempo Real", "Detecta errores proactivamente"),
            ("📧", "Alertas por Email y Telegram", "Notificaciones instantaneas"),
            ("📁", "Reportes Excel Corporativos", "Formato Chedraui profesional"),
            ("💾", "Integracion DB2 Manhattan", "Conexion directa al WMS"),
            ("⚡", "Automatizacion de Procesos", "Menos trabajo manual"),
        ]

        for emoji, titulo, descripcion in funcionalidades:
            time.sleep(0.15)
            print(f"   {emoji} {c(titulo, Colores.GREEN)}")
            print(f"      {c(descripcion, Colores.DIM)}")
            print()

        # Frase motivacional
        frase = random.choice(FRASES_ADMJAJA)
        print(f"\n   {Colores.MAGENTA}💡 \"{frase}\"{Colores.RESET}")

        # Creditos
        print(f"""
   {Colores.DIM}─────────────────────────────────────────────────────────────────────
   Desarrollado con ❤️ por Julian Alexander Juarez Alvarado (ADMJAJA)
   Jefe de Sistemas - CEDIS Chedraui Logistica Cancun
   ─────────────────────────────────────────────────────────────────────{Colores.RESET}
""")

        # Animacion de camion
        print(f"   {Colores.CYAN}Preparando el sistema...{Colores.RESET}")
        for i in range(6):
            frames = ["🚛💨      ", " 🚛💨     ", "  🚛💨    ", "   🚛💨   ", "    🚛💨  ", "     🚛💨 "]
            print(f"\r   {frames[i]}                    ", end='', flush=True)
            time.sleep(0.2)
        print(f"\r   {c('✅ Sistema cargado!', Colores.GREEN)}            ")

        time.sleep(0.5)

    finally:
        mostrar_cursor()


# ===============================================================================
# FORMULARIO DE CONFIGURACION DE CREDENCIALES
# ===============================================================================

@dataclass
class ConfiguracionCredenciales:
    """Estructura para almacenar todas las credenciales configuradas."""
    # Base de Datos DB2
    db_user: str = ""
    db_password: str = ""
    db_host: str = "WM260BASD"
    db_port: int = 50000
    db_database: str = "WM260BASD"

    # Email SMTP
    email_user: str = ""
    email_password: str = ""
    email_host: str = "smtp.office365.com"
    email_port: int = 587

    # Telegram (Opcional)
    telegram_token: str = ""
    telegram_chat_ids: str = ""
    telegram_enabled: bool = False

    # CEDIS Info
    cedis_code: str = "427"
    cedis_name: str = "CEDIS Cancun"
    cedis_region: str = "Sureste"


class FormularioCredenciales:
    """
    Formulario interactivo para configurar TODAS las credenciales del sistema.

    Este formulario se ejecuta durante la carga inicial y garantiza que
    todas las credenciales necesarias esten configuradas antes de operar.
    """

    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.config = ConfiguracionCredenciales()
        self.env_file = BASE_DIR / '.env'
        self.env_template = BASE_DIR / 'env'

    def _verificar_env_existente(self) -> Dict[str, str]:
        """Verifica si ya existe un archivo .env y lee sus valores."""
        valores = {}

        if self.env_file.exists():
            try:
                with open(self.env_file, 'r', encoding='utf-8') as f:
                    for linea in f:
                        linea = linea.strip()
                        if '=' in linea and not linea.startswith('#'):
                            key, value = linea.split('=', 1)
                            valores[key.strip()] = value.strip()
            except Exception:
                pass

        return valores

    def _es_credencial_valida(self, valor: str) -> bool:
        """Verifica si una credencial es valida (no es placeholder)."""
        valores_invalidos = {
            '', 'tu_usuario', 'tu_password', 'tu_email@chedraui.com.mx',
            'your_password', 'password', 'admin', 'root', 'test',
            'changeme', 'default', 'secret', '123456', 'qwerty',
            'your_token', 'bot_token_here'
        }
        return valor.lower().strip() not in valores_invalidos

    def _necesita_configuracion(self) -> Tuple[bool, List[str]]:
        """Determina si se necesita configurar credenciales."""
        valores = self._verificar_env_existente()
        faltantes = []

        # Credenciales obligatorias
        obligatorias = {
            'DB_USER': 'Usuario de Base de Datos',
            'DB_PASSWORD': 'Contrasena de Base de Datos',
            'EMAIL_USER': 'Correo electronico',
            'EMAIL_PASSWORD': 'Contrasena de correo',
        }

        for key, descripcion in obligatorias.items():
            valor = valores.get(key, '')
            if not self._es_credencial_valida(valor):
                faltantes.append(descripcion)

        return len(faltantes) > 0, faltantes

    def _mostrar_seccion(self, titulo: str, icono: str = "📝"):
        """Muestra un encabezado de seccion."""
        print(f"\n   {Colores.YELLOW}{'═' * 60}{Colores.RESET}")
        print(f"   {icono} {c(titulo, Colores.BOLD + Colores.CYAN)}")
        print(f"   {Colores.YELLOW}{'═' * 60}{Colores.RESET}\n")

    def _input_con_animacion(self, prompt: str, default: str = "", es_password: bool = False) -> str:
        """Solicita input con animacion."""
        if default and not es_password:
            texto_prompt = f"   {prompt} [{c(default, Colores.DIM)}]: "
        else:
            texto_prompt = f"   {prompt}: "

        try:
            if es_password:
                valor = getpass.getpass(texto_prompt)
            else:
                valor = input(texto_prompt)

            if not valor and default:
                valor = default

            return valor.strip()
        except KeyboardInterrupt:
            print(f"\n   {c('Operacion cancelada', Colores.YELLOW)}")
            return default

    def _validar_email(self, email: str) -> bool:
        """Valida formato basico de email."""
        return '@' in email and '.' in email.split('@')[-1]

    def _animar_guardado(self):
        """Animacion de guardado de configuracion."""
        print()
        frames_guardado = [
            "💾 Guardando configuracion",
            "💾 Guardando configuracion.",
            "💾 Guardando configuracion..",
            "💾 Guardando configuracion...",
        ]

        for _ in range(2):
            for frame in frames_guardado:
                print(f"\r   {c(frame, Colores.CYAN)}    ", end='', flush=True)
                time.sleep(0.15)

        print(f"\r   {c('✅ Configuracion guardada exitosamente!', Colores.GREEN)}         ")

    def solicitar_credenciales_db(self, valores_actuales: Dict[str, str]) -> None:
        """Solicita credenciales de base de datos."""
        self._mostrar_seccion("CONFIGURACION DE BASE DE DATOS DB2", "💾")

        print(f"   {c('Servidor:', Colores.DIM)} WM260BASD (Manhattan WMS)")
        print(f"   {c('Puerto:', Colores.DIM)} 50000")
        print(f"   {c('Base de datos:', Colores.DIM)} WM260BASD")
        print()

        # Usuario
        default_user = valores_actuales.get('DB_USER', '')
        if not self._es_credencial_valida(default_user):
            default_user = 'ADMJAJA'

        self.config.db_user = self._input_con_animacion(
            "Usuario DB2",
            default_user
        )

        # Password
        self.config.db_password = self._input_con_animacion(
            "Contrasena DB2",
            es_password=True
        )

        if self.config.db_user and self.config.db_password:
            animar_spinner("Verificando conexion DB2", 1.5, 'dots')

    def solicitar_credenciales_email(self, valores_actuales: Dict[str, str]) -> None:
        """Solicita credenciales de correo electronico."""
        self._mostrar_seccion("CONFIGURACION DE CORREO ELECTRONICO", "📧")

        print(f"   {c('Servidor SMTP:', Colores.DIM)} smtp.office365.com")
        print(f"   {c('Puerto:', Colores.DIM)} 587 (TLS)")
        print()

        # Email
        default_email = valores_actuales.get('EMAIL_USER', '')
        if not self._es_credencial_valida(default_email):
            default_email = ''

        while True:
            self.config.email_user = self._input_con_animacion(
                "Correo electronico (@chedraui.com.mx)",
                default_email
            )

            if self._validar_email(self.config.email_user):
                break
            else:
                print(f"   {c('⚠️ Formato de email invalido. Intenta de nuevo.', Colores.YELLOW)}")

        # Password
        self.config.email_password = self._input_con_animacion(
            "Contrasena del correo",
            es_password=True
        )

        if self.config.email_user and self.config.email_password:
            animar_spinner("Verificando configuracion de email", 1.0, 'dots')

    def solicitar_credenciales_telegram(self, valores_actuales: Dict[str, str]) -> None:
        """Solicita credenciales de Telegram (opcional)."""
        self._mostrar_seccion("CONFIGURACION DE TELEGRAM (OPCIONAL)", "📱")

        print(f"   {c('Telegram permite enviar alertas instantaneas al celular.', Colores.DIM)}")
        print(f"   {c('Si no tienes un bot, puedes omitir esta seccion.', Colores.DIM)}")
        print()

        configurar = self._input_con_animacion(
            "Deseas configurar Telegram? (s/n)",
            "n"
        ).lower()

        if configurar in ['s', 'si', 'yes', 'y']:
            self.config.telegram_enabled = True

            print()
            print(f"   {c('Para obtener un token:', Colores.CYAN)}")
            print(f"   {c('1. Busca @BotFather en Telegram', Colores.DIM)}")
            print(f"   {c('2. Usa /newbot y sigue las instrucciones', Colores.DIM)}")
            print(f"   {c('3. Copia el token que te proporciona', Colores.DIM)}")
            print()

            default_token = valores_actuales.get('TELEGRAM_BOT_TOKEN', '')
            self.config.telegram_token = self._input_con_animacion(
                "Token del Bot",
                default_token if self._es_credencial_valida(default_token) else ''
            )

            print()
            print(f"   {c('Para obtener tu Chat ID:', Colores.CYAN)}")
            print(f"   {c('1. Inicia chat con tu bot', Colores.DIM)}")
            print(f"   {c('2. Envia cualquier mensaje', Colores.DIM)}")
            print(f"   {c('3. Visita: api.telegram.org/bot<TOKEN>/getUpdates', Colores.DIM)}")
            print()

            default_chat = valores_actuales.get('TELEGRAM_CHAT_IDS', '')
            self.config.telegram_chat_ids = self._input_con_animacion(
                "Chat IDs (separados por coma)",
                default_chat
            )

            if self.config.telegram_token:
                animar_spinner("Verificando configuracion de Telegram", 1.0, 'dots')
        else:
            self.config.telegram_enabled = False
            print(f"\n   {c('ℹ️ Telegram omitido. Puedes configurarlo despues.', Colores.DIM)}")

    def solicitar_info_cedis(self, valores_actuales: Dict[str, str]) -> None:
        """Solicita informacion del CEDIS."""
        self._mostrar_seccion("INFORMACION DEL CEDIS", "🏢")

        self.config.cedis_code = self._input_con_animacion(
            "Codigo CEDIS",
            valores_actuales.get('CEDIS_CODE', '427')
        )

        self.config.cedis_name = self._input_con_animacion(
            "Nombre CEDIS",
            valores_actuales.get('CEDIS_NAME', 'CEDIS Cancun')
        )

        self.config.cedis_region = self._input_con_animacion(
            "Region",
            valores_actuales.get('CEDIS_REGION', 'Sureste')
        )

    def guardar_configuracion(self) -> bool:
        """Guarda la configuracion en el archivo .env"""
        try:
            # Leer template si existe
            contenido_base = ""
            if self.env_template.exists():
                with open(self.env_template, 'r', encoding='utf-8') as f:
                    contenido_base = f.read()

            # Crear contenido del .env
            contenido = f"""# ===============================================================================
# CONFIGURACION DEL SISTEMA SAC - CEDIS {self.config.cedis_code}
# Generado automaticamente por el asistente de configuracion
# Fecha: {time.strftime('%Y-%m-%d %H:%M:%S')}
# ===============================================================================

# CREDENCIALES DE BASE DE DATOS DB2 (Manhattan WMS)
DB_HOST={self.config.db_host}
DB_PORT={self.config.db_port}
DB_DATABASE={self.config.db_database}
DB_USER={self.config.db_user}
DB_PASSWORD={self.config.db_password}
DB_SCHEMA=WMWHSE1
DB_DRIVER={{IBM DB2 ODBC DRIVER}}
DB_TIMEOUT=30

# CREDENCIALES DE CORREO ELECTRONICO (Office 365)
EMAIL_HOST={self.config.email_host}
EMAIL_PORT={self.config.email_port}
EMAIL_USER={self.config.email_user}
EMAIL_PASSWORD={self.config.email_password}
EMAIL_FROM={self.config.email_user}
EMAIL_PROTOCOL=TLS

# CONFIGURACION DE TELEGRAM
TELEGRAM_BOT_TOKEN={self.config.telegram_token}
TELEGRAM_CHAT_IDS={self.config.telegram_chat_ids}
TELEGRAM_ENABLED={'true' if self.config.telegram_enabled else 'false'}

# INFORMACION DEL CEDIS
CEDIS_CODE={self.config.cedis_code}
CEDIS_NAME={self.config.cedis_name}
CEDIS_REGION={self.config.cedis_region}
CEDIS_ALMACEN=C22

# CONFIGURACION DEL SISTEMA
SYSTEM_VERSION=2.0.0
ENVIRONMENT=production
DEBUG=false
TIMEZONE=America/Cancun
LOG_LEVEL=INFO

# ===============================================================================
# Configurado por: Sistema SAC
# Desarrollado por: Julian Alexander Juarez Alvarado (ADMJAJA)
# ===============================================================================
"""

            # Guardar archivo
            with open(self.env_file, 'w', encoding='utf-8') as f:
                f.write(contenido)

            self._animar_guardado()
            return True

        except Exception as e:
            print(f"\n   {c(f'Error guardando configuracion: {e}', Colores.RED)}")
            return False

    def mostrar_resumen(self) -> None:
        """Muestra resumen de la configuracion."""
        print(f"\n   {Colores.GREEN}{'═' * 60}{Colores.RESET}")
        print(f"   {c('RESUMEN DE CONFIGURACION', Colores.BOLD + Colores.GREEN)}")
        print(f"   {Colores.GREEN}{'═' * 60}{Colores.RESET}\n")

        # DB2
        print(f"   {c('Base de Datos DB2:', Colores.CYAN)}")
        print(f"      Usuario: {self.config.db_user}")
        print(f"      Servidor: {self.config.db_host}:{self.config.db_port}")
        print()

        # Email
        print(f"   {c('Correo Electronico:', Colores.CYAN)}")
        print(f"      Email: {self.config.email_user}")
        print(f"      Servidor: {self.config.email_host}:{self.config.email_port}")
        print()

        # Telegram
        print(f"   {c('Telegram:', Colores.CYAN)}")
        if self.config.telegram_enabled:
            print(f"      Estado: {c('Configurado', Colores.GREEN)}")
            print(f"      Chat IDs: {self.config.telegram_chat_ids or 'N/A'}")
        else:
            print(f"      Estado: {c('No configurado', Colores.YELLOW)}")
        print()

        # CEDIS
        print(f"   {c('CEDIS:', Colores.CYAN)}")
        print(f"      Codigo: {self.config.cedis_code}")
        print(f"      Nombre: {self.config.cedis_name}")
        print(f"      Region: {self.config.cedis_region}")
        print()

    def ejecutar(self, forzar: bool = False) -> Dict:
        """
        Ejecuta el formulario de configuracion de credenciales.

        Args:
            forzar: Si True, ejecuta el formulario aunque ya exista configuracion

        Returns:
            Dict con el resultado de la configuracion
        """
        resultado = {
            'configurado': False,
            'mensaje': '',
            'nuevas_credenciales': False,
        }

        try:
            # Verificar si necesita configuracion
            necesita, faltantes = self._necesita_configuracion()
            valores_actuales = self._verificar_env_existente()

            if not necesita and not forzar:
                # Ya esta configurado
                if self.verbose:
                    print(f"\n   {c('✅ Credenciales ya configuradas', Colores.GREEN)}")

                resultado['configurado'] = True
                resultado['mensaje'] = 'Credenciales ya configuradas'
                return resultado

            # Mostrar que falta
            if faltantes and self.verbose:
                print(f"\n   {c('⚠️ Faltan credenciales por configurar:', Colores.YELLOW)}")
                for faltante in faltantes:
                    print(f"      - {faltante}")
                print()

            # Ejecutar formulario
            if self.verbose:
                print(f"\n   {c('Iniciando asistente de configuracion...', Colores.CYAN)}")
                time.sleep(0.5)

            # 1. Credenciales DB2
            self.solicitar_credenciales_db(valores_actuales)

            # 2. Credenciales Email
            self.solicitar_credenciales_email(valores_actuales)

            # 3. Telegram (Opcional)
            self.solicitar_credenciales_telegram(valores_actuales)

            # 4. Info CEDIS
            self.solicitar_info_cedis(valores_actuales)

            # Guardar configuracion
            if self.guardar_configuracion():
                self.mostrar_resumen()
                resultado['configurado'] = True
                resultado['nuevas_credenciales'] = True
                resultado['mensaje'] = 'Configuracion completada exitosamente'
            else:
                resultado['mensaje'] = 'Error al guardar configuracion'

        except KeyboardInterrupt:
            print(f"\n\n   {c('⚠️ Configuracion cancelada por el usuario', Colores.YELLOW)}")
            resultado['mensaje'] = 'Cancelado por el usuario'

        return resultado


# ===============================================================================
# ANIMACIONES DURANTE PROCESOS DEL SAC
# ===============================================================================

def animar_inicio_proceso(nombre_proceso: str):
    """Animacion al iniciar un proceso del SAC."""
    print()
    print(f"   {Colores.CYAN}{'─' * 55}{Colores.RESET}")

    emoji = random.choice(EMOJIS_CARGA)
    print(f"   {emoji} {c(nombre_proceso, Colores.BOLD + Colores.CYAN)}")

    print(f"   {Colores.CYAN}{'─' * 55}{Colores.RESET}")

    # Animacion de camion
    for i in range(4):
        frames = ["🚛    ", " 🚛   ", "  🚛  ", "   🚛 "]
        print(f"\r   {frames[i]}                    ", end='', flush=True)
        time.sleep(0.1)
    print("\r                              ", end='')
    print()


def animar_fin_proceso(exito: bool, mensaje: str = ""):
    """Animacion al finalizar un proceso."""
    if exito:
        emoji = random.choice(EMOJIS_EXITO)
        color = Colores.GREEN
        estado = "COMPLETADO"
    else:
        emoji = random.choice(EMOJIS_ERROR)
        color = Colores.RED
        estado = "ERROR"

    print()
    print(f"   {c('─' * 55, color)}")
    print(f"   {emoji} {c(estado, Colores.BOLD + color)}")

    if mensaje:
        print(f"   {c(mensaje, Colores.DIM)}")

    print(f"   {c('─' * 55, color)}")
    print()


def animar_validacion_oc(oc_numero: str, pasos: List[str] = None):
    """Animacion especial para validacion de OC."""
    if pasos is None:
        pasos = [
            "Conectando a DB2...",
            "Consultando OC...",
            "Obteniendo distribuciones...",
            "Validando cantidades...",
            "Verificando SKUs...",
            "Generando reporte...",
        ]

    try:
        ocultar_cursor()

        print()
        print(f"   {Colores.YELLOW}╔{'═' * 53}╗{Colores.RESET}")
        print(f"   {Colores.YELLOW}║{Colores.RESET} 🔍 {c(f'VALIDANDO OC: {oc_numero:^20}', Colores.BOLD)} 📊       {Colores.YELLOW}║{Colores.RESET}")
        print(f"   {Colores.YELLOW}╚{'═' * 53}╝{Colores.RESET}")
        print()

        for i, paso in enumerate(pasos):
            # Barra de progreso
            mostrar_barra_progreso(i + 1, len(pasos), 35, paso[:25])
            time.sleep(0.4)

        # Completado
        print(f"\r   {c('✅', Colores.GREEN)} [{c('█' * 35, Colores.GREEN)}] 100.0% Completado!           ")
        print()

    finally:
        mostrar_cursor()


def animar_generacion_reporte(tipo_reporte: str = "Excel"):
    """Animacion para generacion de reportes."""
    try:
        ocultar_cursor()

        etapas = [
            ("📊", "Preparando datos..."),
            ("🎨", "Aplicando formato corporativo..."),
            ("📝", "Generando hojas..."),
            ("💾", "Guardando archivo..."),
        ]

        print()
        print(f"   {c(f'Generando Reporte {tipo_reporte}', Colores.CYAN)}")
        print()

        for i, (emoji, etapa) in enumerate(etapas):
            mostrar_barra_progreso(i + 1, len(etapas), 40, f"{emoji} {etapa[:20]}")
            time.sleep(0.5)

        print(f"\r   {c('✅', Colores.GREEN)} Reporte generado exitosamente!                              ")
        print()

    finally:
        mostrar_cursor()


def animar_envio_correo():
    """Animacion para envio de correo."""
    try:
        ocultar_cursor()

        print()
        frames = [
            "📧       ➡️",
            " 📧      ➡️",
            "  📧     ➡️",
            "   📧    ➡️",
            "    📧   ➡️",
            "     📧  ➡️",
            "      📧 ➡️",
            "       📧➡️",
            "        ✅",
        ]

        for frame in frames:
            print(f"\r   {c('Enviando correo... ', Colores.CYAN)}{frame}    ", end='', flush=True)
            time.sleep(0.15)

        print(f"\r   {c('✅ Correo enviado exitosamente!', Colores.GREEN)}                    ")
        print()

    finally:
        mostrar_cursor()


def animar_conexion_db():
    """Animacion para conexion a base de datos."""
    try:
        ocultar_cursor()

        print()
        estados = [
            ("🔌", "Estableciendo conexion..."),
            ("🔐", "Autenticando..."),
            ("🔗", "Conectando a WM260BASD..."),
            ("✅", "Conexion establecida!"),
        ]

        for i, (emoji, estado) in enumerate(estados):
            print(f"\r   {emoji} {c(estado, Colores.CYAN)}                    ", end='', flush=True)
            time.sleep(0.4)

        print()

    finally:
        mostrar_cursor()


# ===============================================================================
# FUNCIONES PRINCIPALES DE EXPORTACION
# ===============================================================================

def ejecutar_setup_credenciales(
    mostrar_intro: bool = True,
    forzar: bool = False,
    verbose: bool = True
) -> Dict:
    """
    Ejecuta el proceso completo de setup de credenciales.

    Esta funcion debe llamarse al inicio del sistema para garantizar
    que todas las credenciales esten configuradas.

    Args:
        mostrar_intro: Si True, muestra la introduccion animada
        forzar: Si True, fuerza la reconfiguracion
        verbose: Si True, muestra mensajes y animaciones

    Returns:
        Dict con el resultado del proceso:
        {
            'configurado': bool,
            'mensaje': str,
            'nuevas_credenciales': bool
        }
    """
    try:
        # Mostrar introduccion animada
        if mostrar_intro and verbose:
            mostrar_intro_animada()
            time.sleep(0.3)

        # Ejecutar formulario de credenciales
        formulario = FormularioCredenciales(verbose=verbose)
        resultado = formulario.ejecutar(forzar=forzar)

        # Mensaje final
        if resultado['configurado'] and verbose:
            print()
            print(f"   {Colores.GREEN}{'═' * 55}{Colores.RESET}")
            print(f"   {c('🚀 SISTEMA SAC LISTO PARA OPERAR', Colores.BOLD + Colores.GREEN)}")
            print(f"   {Colores.GREEN}{'═' * 55}{Colores.RESET}")
            print()

            # Frase final
            frase = random.choice(FRASES_ADMJAJA)
            print(f"   {Colores.MAGENTA}💡 \"{frase}\"{Colores.RESET}")
            print()

        return resultado

    except Exception as e:
        return {
            'configurado': False,
            'mensaje': f'Error: {str(e)}',
            'nuevas_credenciales': False
        }


def verificar_credenciales_configuradas() -> bool:
    """
    Verifica rapidamente si las credenciales estan configuradas.

    Returns:
        True si las credenciales criticas estan configuradas
    """
    formulario = FormularioCredenciales(verbose=False)
    necesita, _ = formulario._necesita_configuracion()
    return not necesita


# ===============================================================================
# EXPORTAR
# ===============================================================================

__all__ = [
    # Funciones principales
    'ejecutar_setup_credenciales',
    'verificar_credenciales_configuradas',
    'mostrar_intro_animada',

    # Animaciones de procesos
    'animar_inicio_proceso',
    'animar_fin_proceso',
    'animar_validacion_oc',
    'animar_generacion_reporte',
    'animar_envio_correo',
    'animar_conexion_db',

    # Utilidades
    'animar_spinner',
    'mostrar_barra_progreso',
    'animar_texto_escritura',

    # Clases
    'FormularioCredenciales',
    'ConfiguracionCredenciales',
    'Colores',
]


# ===============================================================================
# EJECUCION DIRECTA
# ===============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description='Configuracion de Credenciales - Sistema SAC'
    )
    parser.add_argument('--forzar', '-f', action='store_true',
                       help='Forzar reconfiguracion')
    parser.add_argument('--sin-intro', action='store_true',
                       help='Omitir introduccion animada')
    parser.add_argument('--verificar', '-v', action='store_true',
                       help='Solo verificar si esta configurado')

    args = parser.parse_args()

    if args.verificar:
        configurado = verificar_credenciales_configuradas()
        if configurado:
            print(f"   {Colores.GREEN}✅ Credenciales configuradas{Colores.RESET}")
        else:
            print(f"   {Colores.YELLOW}⚠️ Credenciales pendientes{Colores.RESET}")
        sys.exit(0 if configurado else 1)

    resultado = ejecutar_setup_credenciales(
        mostrar_intro=not args.sin_intro,
        forzar=args.forzar
    )

    sys.exit(0 if resultado['configurado'] else 1)
