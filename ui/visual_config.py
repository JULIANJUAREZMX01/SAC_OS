#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════════════════════
SACITY VISUAL CONFIGURATION MODULE
Configuración Visual y Temas para SACITY Emulator
═══════════════════════════════════════════════════════════════════════════════

Módulo de configuración visual completo con:
- Paleta de colores Cybersecurity (rojo/negro/gris)
- Arte ASCII para banners y logos
- Mensajes tipo "ACCESSING CLASSIFIED DATA..."
- Estética hacker/Red Hat Enterprise
- Temas personalizables

FILOSOFÍA DE DISEÑO:
- 🔴 ROJO: Color principal (alertas, títulos, branding)
- 🖤 NEGRO: Fondo siempre (zero distracciones)
- ⚪ GRIS: Resaltar elementos secundarios
- 🟢🔵🟠 Verde/Azul/Naranja: Contraste y estados

"THE RED TERMINAL - Beyond Velocity, Beyond Telnet"

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Organización: SISTEMAS_427 - CEDIS Cancún 427
Tecnología: UNT (United North Team Techs)
Licencia: GNU GPL v3.0 - Open Source
═══════════════════════════════════════════════════════════════════════════════
"""

from typing import Dict, Optional
from datetime import datetime


# ═══════════════════════════════════════════════════════════════════════════════
# CÓDIGOS ANSI - COLORES PARA TERMINAL
# ═══════════════════════════════════════════════════════════════════════════════

class ANSI:
    """
    Códigos de escape ANSI para colores y estilos en terminal.

    Paleta oficial SACITY: Rojo/Negro/Gris + colores de contraste
    """

    # ═══ CONTROL ═══
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'
    BLINK = '\033[5m'
    BLINK_FAST = '\033[6m'
    REVERSE = '\033[7m'
    HIDDEN = '\033[8m'
    STRIKE = '\033[9m'

    # ═══ ROJOS (Color principal SACITY) ═══
    RED = '\033[31m'              # Rojo estándar
    RED_BRIGHT = '\033[91m'       # Rojo brillante - PRINCIPAL
    RED_BOLD = '\033[1;31m'       # Rojo negrita
    RED_BG = '\033[41m'           # Fondo rojo
    RED_BRIGHT_BG = '\033[101m'   # Fondo rojo brillante

    # ═══ NEGRO Y GRIS ═══
    BLACK = '\033[30m'
    BLACK_BG = '\033[40m'
    GRAY = '\033[90m'             # Gris (Bright Black)
    GRAY_BG = '\033[100m'

    # ═══ BLANCO ═══
    WHITE = '\033[37m'
    WHITE_BRIGHT = '\033[97m'
    WHITE_BG = '\033[47m'
    WHITE_BRIGHT_BG = '\033[107m'

    # ═══ VERDE (Estado OK) ═══
    GREEN = '\033[32m'
    GREEN_BRIGHT = '\033[92m'
    GREEN_BG = '\033[42m'

    # ═══ AZUL (Info) ═══
    BLUE = '\033[34m'
    BLUE_BRIGHT = '\033[94m'
    BLUE_BG = '\033[44m'

    # ═══ CYAN (Datos) ═══
    CYAN = '\033[36m'
    CYAN_BRIGHT = '\033[96m'
    CYAN_BG = '\033[46m'

    # ═══ AMARILLO/NARANJA (Advertencias) ═══
    YELLOW = '\033[33m'
    YELLOW_BRIGHT = '\033[93m'
    YELLOW_BG = '\033[43m'
    ORANGE = YELLOW  # ANSI no tiene naranja, usa amarillo

    # ═══ MAGENTA (Highlights) ═══
    MAGENTA = '\033[35m'
    MAGENTA_BRIGHT = '\033[95m'
    MAGENTA_BG = '\033[45m'

    @classmethod
    def rgb(cls, r: int, g: int, b: int) -> str:
        """Genera código RGB para terminales 24-bit"""
        return f'\033[38;2;{r};{g};{b}m'

    @classmethod
    def rgb_bg(cls, r: int, g: int, b: int) -> str:
        """Genera código RGB para fondo en terminales 24-bit"""
        return f'\033[48;2;{r};{g};{b}m'


# ═══════════════════════════════════════════════════════════════════════════════
# TEMAS DE COLOR
# ═══════════════════════════════════════════════════════════════════════════════

class ColorTheme:
    """Clase base para temas de color"""

    def __init__(self, name: str, colors: Dict[str, str]):
        self.name = name
        self.colors = colors

    def __getitem__(self, key: str) -> str:
        return self.colors.get(key, '#FFFFFF')


# Tema 1: RED BLOOD (Predeterminado - Sangre/Gótico)
THEME_RED_BLOOD = ColorTheme('Red Blood', {
    'bg': '#000000',           # Negro puro
    'fg': '#FF0000',           # Rojo sangre brillante
    'cursor': '#FFFFFF',       # Cursor blanco
    'status_bg': '#8B0000',    # Fondo status bar (rojo oscuro)
    'status_fg': '#FFFFFF',    # Texto status bar
    'success': '#00FF00',      # Verde neón - éxito
    'warning': '#FF8C00',      # Naranja - advertencia
    'error': '#FF0000',        # Rojo - error
    'info': '#00BFFF',         # Azul cibernético
    'highlight': '#FF00FF',    # Magenta
})

# Tema 2: CYBER RED (Rojo Cibernético)
THEME_CYBER_RED = ColorTheme('Cyber Red', {
    'bg': '#000000',
    'fg': '#E31837',           # Rojo Chedraui/SACITY
    'cursor': '#00FFFF',       # Cursor cyan
    'status_bg': '#FF0000',
    'status_fg': '#000000',
    'success': '#00FF00',
    'warning': '#FFFF00',
    'error': '#FF0000',
    'info': '#00BFFF',
    'highlight': '#00FFFF',
})

# Tema 3: DARK GOTHIC (Gótico Oscuro)
THEME_DARK_GOTHIC = ColorTheme('Dark Gothic', {
    'bg': '#0A0A0A',          # Negro suave
    'fg': '#B22222',          # Rojo ladrillo
    'cursor': '#C0C0C0',      # Cursor gris
    'status_bg': '#8B0000',
    'status_fg': '#FFFFFF',
    'success': '#00FF66',     # Verde Matrix
    'warning': '#FFD700',     # Dorado
    'error': '#FF4500',       # Naranja fuego
    'info': '#1E90FF',        # Azul eléctrico
    'highlight': '#FF1493',
})

# Tema 4: RED HAT ENTERPRISE (Inspirado en Red Hat)
THEME_RED_HAT = ColorTheme('Red Hat Enterprise', {
    'bg': '#000000',
    'fg': '#EE0000',          # Red Hat Official Red
    'cursor': '#FFFFFF',
    'status_bg': '#CC0000',
    'status_fg': '#FFFFFF',
    'success': '#92D400',     # Red Hat Green
    'warning': '#F0AB00',     # Red Hat Gold
    'error': '#A30000',
    'info': '#00B9E4',        # Red Hat Blue
    'highlight': '#EE0000',
})

# Tema activo por defecto
ACTIVE_THEME = THEME_RED_BLOOD


# ═══════════════════════════════════════════════════════════════════════════════
# ARTE ASCII - LOGOS Y BANNERS
# ═══════════════════════════════════════════════════════════════════════════════

class ASCII_ART:
    """Colección de arte ASCII para SACITY"""

    # ═══ LOGO PRINCIPAL (Grande) ═══
    LOGO_FULL = f"""{ANSI.RED_BRIGHT}
    ███████╗ █████╗  ██████╗██╗████████╗██╗   ██╗
    ██╔════╝██╔══██╗██╔════╝██║╚══██╔══╝╚██╗ ██╔╝
    ███████╗███████║██║     ██║   ██║    ╚████╔╝
    ╚════██║██╔══██║██║     ██║   ██║     ╚██╔╝
    ███████║██║  ██║╚██████╗██║   ██║      ██║
    ╚══════╝╚═╝  ╚═╝ ╚═════╝╚═╝   ╚═╝      ╚═╝
{ANSI.RESET}"""

    # ═══ LOGO COMPACTO ═══
    LOGO_COMPACT = f"""{ANSI.RED_BOLD}
   ▄████████    ▄████████  ▄████████  ▄█     ███     ▄██   ▄
  ███    ███   ███    ███ ███    ███ ███ ▀█████████▄ ███   ██▄
  ███    █▀    ███    ███ ███    █▀  ███▌   ▀███▀▀██ ███▄▄▄███
  ███          ███    ███ ███        ███▌    ███   ▀ ▀▀▀▀▀▀███
▀███████████ ▀███████████ ███        ███▌    ███     ▄██   ███
         ███   ███    ███ ███    █▄  ███     ███     ███   ███
   ▄█    ███   ███    ███ ███    ███ ███     ███     ███   ███
 ▄████████▀    ███    █▀  ████████▀  █▀     ▄████▀    ▀█████▀
{ANSI.RESET}"""

    # ═══ MINI LOGO (Para líneas de estado) ═══
    LOGO_MINI = f"{ANSI.RED_BRIGHT}[█ SACITY █]{ANSI.RESET}"

    # ═══ DISPOSITIVO MC9190 ═══
    MC9190 = f"""{ANSI.GRAY}
        ╔═══════════════════╗
        ║{ANSI.BLACK_BG}{ANSI.GREEN_BRIGHT}███████████████████{ANSI.RESET}{ANSI.GRAY}║  ← Pantalla 3.7" VGA
        ║{ANSI.BLACK_BG}{ANSI.GREEN_BRIGHT}█  MANHATTAN WMS  █{ANSI.RESET}{ANSI.GRAY}║
        ║{ANSI.BLACK_BG}{ANSI.GREEN_BRIGHT}█  CEDIS C427     █{ANSI.RESET}{ANSI.GRAY}║
        ║{ANSI.BLACK_BG}{ANSI.GREEN_BRIGHT}███████████████████{ANSI.RESET}{ANSI.GRAY}║
        ╠═══════════════════╣
        ║ [1] [2] [3] [▲]  ║  ← Teclado
        ║ [4] [5] [6] [▼]  ║    43 teclas
        ║ [7] [8] [9] [◄]  ║
        ║ [*] [0] [#] [►]  ║
        ╠═══════════════════╣
        ║ [F1][F2][F3][F4] ║
        ╚═══════════════════╝
           ║   {ANSI.RED_BRIGHT}▼{ANSI.RESET}   ║  ← Escáner
           ╚═══════╝
{ANSI.RESET}"""

    # ═══ BARRAS Y SEPARADORES ═══
    SEPARATOR_THICK = f"{ANSI.RED_BRIGHT}{'═' * 80}{ANSI.RESET}"
    SEPARATOR_THIN = f"{ANSI.GRAY}{'─' * 80}{ANSI.RESET}"
    SEPARATOR_DOUBLE = f"{ANSI.RED_BRIGHT}{'╔' + '═' * 78 + '╗'}{ANSI.RESET}"


# ═══════════════════════════════════════════════════════════════════════════════
# MENSAJES CYBERSECURITY
# ═══════════════════════════════════════════════════════════════════════════════

class CyberMessages:
    """Mensajes estilo cybersecurity/hacker para SACITY"""

    # ═══ MENSAJES DE PROCESO ═══
    PROCESO = {
        'iniciando': f"{ANSI.RED_BRIGHT}[▓░░░░░░░] INICIANDO SISTEMA...{ANSI.RESET}",
        'autenticando': f"{ANSI.YELLOW_BRIGHT}[▓▓░░░░░░] SOLICITANDO CREDENCIALES...{ANSI.RESET}",
        'verificando': f"{ANSI.YELLOW}[▓▓▓░░░░░] VERIFICANDO IDENTIDAD...{ANSI.RESET}",
        'conectando': f"{ANSI.CYAN_BRIGHT}[▓▓▓▓░░░░] ESTABLECIENDO TÚNEL SEGURO...{ANSI.RESET}",
        'accesando': f"{ANSI.BLUE_BRIGHT}[▓▓▓▓▓░░░] ACCESANDO AL SISTEMA WMS...{ANSI.RESET}",
        'cargando': f"{ANSI.GREEN}[▓▓▓▓▓▓░░] CARGANDO MÓDULOS...{ANSI.RESET}",
        'monitoreando': f"{ANSI.CYAN}[▓▓▓▓▓▓▓░] SISTEMAS MONITOREANDO...{ANSI.RESET}",
        'operacional': f"{ANSI.GREEN_BRIGHT}[▓▓▓▓▓▓▓▓] SISTEMA OPERACIONAL{ANSI.RESET}",
    }

    # ═══ ALERTAS ═══
    ALERTA = {
        'critica': f"{ANSI.RED_BRIGHT}{ANSI.BLINK}[🚨 ALERTA CRÍTICA]{ANSI.RESET}",
        'alta': f"{ANSI.RED}[⚠️  ALERTA ALTA]{ANSI.RESET}",
        'media': f"{ANSI.YELLOW}[⚡ ADVERTENCIA]{ANSI.RESET}",
        'baja': f"{ANSI.YELLOW_BRIGHT}[ℹ️  AVISO]{ANSI.RESET}",
    }

    # ═══ ESTADOS DE ACCESO ═══
    ACCESO = {
        'permitido': f"{ANSI.GREEN_BRIGHT}[✓ ACCESO AUTORIZADO]{ANSI.RESET}",
        'denegado': f"{ANSI.RED_BOLD}[✖ ACCESO DENEGADO]{ANSI.RESET}",
        'validando': f"{ANSI.CYAN}[◐ VALIDANDO PERMISOS...]{ANSI.RESET}",
    }

    # ═══ SEGURIDAD ═══
    SEGURIDAD = {
        'confidencial': f"{ANSI.RED}[🔒 INFORMACIÓN CONFIDENCIAL]{ANSI.RESET}",
        'clasificado': f"{ANSI.RED_BOLD}[🔐 DATO CLASIFICADO]{ANSI.RESET}",
        'seguro': f"{ANSI.GREEN}[🛡️  CONEXIÓN SEGURA]{ANSI.RESET}",
        'encriptado': f"{ANSI.CYAN}[🔑 CANAL ENCRIPTADO]{ANSI.RESET}",
        'monitoreando': f"{ANSI.CYAN}[👁️  DEPARTAMENTO DE SISTEMAS MONITOREANDO]{ANSI.RESET}",
    }

    # ═══ ESTADOS GENERALES ═══
    ESTADO = {
        'exito': f"{ANSI.GREEN_BRIGHT}✓ OPERACIÓN EXITOSA{ANSI.RESET}",
        'error': f"{ANSI.RED_BRIGHT}✖ ERROR DE SISTEMA{ANSI.RESET}",
        'procesando': f"{ANSI.CYAN}◐ PROCESANDO...{ANSI.RESET}",
        'espera': f"{ANSI.YELLOW}⏳ EN ESPERA{ANSI.RESET}",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN VISUAL PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

class SacityVisualConfig:
    """
    Configuración visual principal para SACITY Emulator.

    Proporciona todos los elementos visuales:
    - Banners y logos
    - Barras de estado
    - Mensajes cybersecurity
    - Prompts interactivos
    - Footers y créditos
    """

    VERSION = "1.0.0"
    NOMBRE = "SACITY Emulator"
    SLOGAN = "THE RED TERMINAL - Beyond Velocity, Beyond Telnet"

    def __init__(self, theme: ColorTheme = THEME_RED_BLOOD):
        self.theme = theme
        self.ansi = ANSI
        self.ascii = ASCII_ART
        self.cyber = CyberMessages

    # ═══════════════════════════════════════════════════════════════
    # BANNERS
    # ═══════════════════════════════════════════════════════════════

    def get_banner_inicio(self) -> str:
        """Banner de inicio completo con tema cybersecurity"""
        return f"""
{ANSI.RED_BRIGHT}╔══════════════════════════════════════════════════════════════════════╗
║{ANSI.BLACK_BG}{ANSI.RED_BRIGHT}  🔴 SACITY EMULATOR v{self.VERSION} - SISTEMA DE ACCESO SEGURO          {ANSI.RESET}{ANSI.RED_BRIGHT}║
╠══════════════════════════════════════════════════════════════════════╣{ANSI.RESET}
{ANSI.GRAY}║  > INICIANDO PROTOCOLO DE AUTENTICACIÓN...                           ║
║  > VERIFICANDO CREDENCIALES DE ACCESO...                             ║
║  > ESTABLECIENDO CONEXIÓN ENCRIPTADA...                              ║{ANSI.RESET}
{ANSI.RED_BRIGHT}╠══════════════════════════════════════════════════════════════════════╣{ANSI.RESET}
{ANSI.GREEN_BRIGHT}║  ✓ ACCESO AUTORIZADO                                                 ║{ANSI.RESET}
{ANSI.BLUE_BRIGHT}║  ℹ SISTEMA: Manhattan WMS                                            ║
║  ℹ CEDIS: Cancún 427 - Almacén C22                                   ║{ANSI.RESET}
{ANSI.GRAY}║  ℹ Dispositivo: Symbol MC9190-G                                      ║{ANSI.RESET}
{ANSI.RED_BRIGHT}╠══════════════════════════════════════════════════════════════════════╣{ANSI.RESET}
{ANSI.RED}║  🔒 INFORMACIÓN CONFIDENCIAL - USO AUTORIZADO SOLAMENTE              ║{ANSI.RESET}
{ANSI.RED_BRIGHT}╚══════════════════════════════════════════════════════════════════════╝{ANSI.RESET}

{ANSI.GRAY}Diseñado por: ADMJAJA | SISTEMAS_427 | UNT (United North Team Techs){ANSI.RESET}
{ANSI.DIM}Open Source Project - GNU GPL v3.0 License{ANSI.RESET}
"""

    def get_banner_simple(self) -> str:
        """Banner simple con logo"""
        return f"""
{ASCII_ART.LOGO_FULL}
{ANSI.GRAY}          {self.SLOGAN}{ANSI.RESET}
{ANSI.BLUE_BRIGHT}      Emulador Telnet/Velocity MC9000/MC93{ANSI.RESET}
{ANSI.GRAY}    ═══════════════════════════════════════════{ANSI.RESET}
"""

    # ═══════════════════════════════════════════════════════════════
    # BARRA DE ESTADO
    # ═══════════════════════════════════════════════════════════════

    def get_status_bar(
        self,
        dispositivo: str = "MC9190",
        bateria: int = 78,
        wifi_nivel: int = 4,
        hora: str = None,
        usuario: str = "ADMJAJA"
    ) -> str:
        """
        Genera barra de estado estilo Red Hat Enterprise.

        Args:
            dispositivo: Modelo del dispositivo
            bateria: Porcentaje de batería (0-100)
            wifi_nivel: Nivel WiFi (0-5)
            hora: Hora actual (HH:MM) - si None usa hora actual
            usuario: Nombre de usuario
        """
        if hora is None:
            hora = datetime.now().strftime("%H:%M")

        # Iconos WiFi
        wifi_icons = ["░░░░░", "█░░░░", "██░░░", "███░░", "████░", "█████"]
        wifi = wifi_icons[min(wifi_nivel, 5)]

        # Color batería
        if bateria < 20:
            bat_color = ANSI.RED_BRIGHT
            bat_icon = "🔋⚠️ "
        elif bateria < 50:
            bat_color = ANSI.YELLOW
            bat_icon = "🔋"
        else:
            bat_color = ANSI.GREEN_BRIGHT
            bat_icon = "🔋"

        return f"""
{ANSI.RED_BG}{ANSI.WHITE_BRIGHT}┌─────────────────────────────────────────────────────────────────────┐{ANSI.RESET}
{ANSI.RED_BG}{ANSI.WHITE_BRIGHT}│ {ANSI.RED_BRIGHT}{ANSI.BOLD}SACITY{ANSI.RESET}{ANSI.RED_BG}{ANSI.WHITE_BRIGHT} │ {dispositivo} │ {bat_color}{bat_icon}{bateria}%{ANSI.RESET}{ANSI.RED_BG}{ANSI.WHITE_BRIGHT} │ WiFi:{ANSI.GREEN_BRIGHT}{wifi}{ANSI.RESET}{ANSI.RED_BG}{ANSI.WHITE_BRIGHT} │ {hora} │ {ANSI.CYAN_BRIGHT}USER:{usuario}{ANSI.RESET}{ANSI.RED_BG}{ANSI.WHITE_BRIGHT} │{ANSI.RESET}
{ANSI.RED_BG}{ANSI.WHITE_BRIGHT}└─────────────────────────────────────────────────────────────────────┘{ANSI.RESET}
"""

    # ═══════════════════════════════════════════════════════════════
    # PROMPTS
    # ═══════════════════════════════════════════════════════════════

    def get_prompt(self, modo: str = 'normal') -> str:
        """
        Genera prompt según modo de operación.

        Modos:
        - normal: Prompt estándar
        - root: Modo administrador
        - secure: Modo seguro
        - admin: Administración
        """
        prompts = {
            'normal': f"{ANSI.RED_BRIGHT}[SACITY]{ANSI.RESET}{ANSI.GRAY}>{ANSI.RESET} ",
            'root': f"{ANSI.RED_BOLD}[SACITY:ROOT]{ANSI.RESET}{ANSI.RED}#{ANSI.RESET} ",
            'secure': f"{ANSI.RED_BRIGHT}[🔒 SACITY]{ANSI.RESET}{ANSI.GRAY}>{ANSI.RESET} ",
            'admin': f"{ANSI.RED_BRIGHT}[SACITY]{ANSI.CYAN_BRIGHT}[ADMIN]{ANSI.RESET}{ANSI.GRAY}>{ANSI.RESET} ",
        }
        return prompts.get(modo, prompts['normal'])

    # ═══════════════════════════════════════════════════════════════
    # FOOTER
    # ═══════════════════════════════════════════════════════════════

    def get_footer(self) -> str:
        """Genera footer con créditos"""
        return f"""
{ANSI.GRAY}────────────────────────────────────────────────────────────────────{ANSI.RESET}
{ANSI.RED}  Proyecto Open Source: SACITY Emulator v{self.VERSION}{ANSI.RESET}
{ANSI.CYAN_BRIGHT}  Desarrollado por: ADMJAJA (Julián Alexander Juárez Alvarado){ANSI.RESET}
{ANSI.BLUE_BRIGHT}  Organización: SISTEMAS_427 - CEDIS Cancún 427{ANSI.RESET}
{ANSI.GREEN_BRIGHT}  Tecnología: UNT (United North Team Techs){ANSI.RESET}
{ANSI.GRAY}  Licencia: GNU GPL v3.0 - Código Abierto a la Comunidad{ANSI.RESET}
{ANSI.GRAY}────────────────────────────────────────────────────────────────────{ANSI.RESET}
"""

    # ═══════════════════════════════════════════════════════════════
    # ANIMACIONES
    # ═══════════════════════════════════════════════════════════════

    def get_frames_loading(self) -> list:
        """Frames de animación de carga estilo hacker"""
        return [
            f"{ANSI.RED_BRIGHT}[▓       ] INICIANDO...{ANSI.RESET}",
            f"{ANSI.RED_BRIGHT}[▓▓      ] CARGANDO MÓDULOS...{ANSI.RESET}",
            f"{ANSI.RED}[▓▓▓     ] VERIFICANDO INTEGRIDAD...{ANSI.RESET}",
            f"{ANSI.YELLOW}[▓▓▓▓    ] CONECTANDO AL SERVIDOR...{ANSI.RESET}",
            f"{ANSI.CYAN}[▓▓▓▓▓   ] AUTENTICANDO...{ANSI.RESET}",
            f"{ANSI.BLUE_BRIGHT}[▓▓▓▓▓▓  ] ESTABLECIENDO SESIÓN...{ANSI.RESET}",
            f"{ANSI.GREEN}[▓▓▓▓▓▓▓ ] LISTO...{ANSI.RESET}",
            f"{ANSI.GREEN_BRIGHT}[▓▓▓▓▓▓▓▓] SISTEMA OPERACIONAL{ANSI.RESET}",
        ]

    # ═══════════════════════════════════════════════════════════════
    # MENSAJES ESPECIALES
    # ═══════════════════════════════════════════════════════════════

    def mensaje_confidencial(self, texto: str) -> str:
        """Mensaje de información confidencial"""
        return f"{ANSI.RED}[🔒 CONFIDENCIAL]{ANSI.RESET} {texto}"

    def mensaje_monitoreando(self) -> str:
        """Mensaje de monitoreo activo"""
        return f"{ANSI.CYAN}[👁️  DEPARTAMENTO DE SISTEMAS MONITOREANDO...]{ANSI.RESET}"

    def mensaje_acceso_denegado(self, razon: str = "") -> str:
        """Mensaje de acceso denegado"""
        msg = f"{ANSI.RED_BOLD}[✖ ACCESO DENEGADO]{ANSI.RESET}"
        if razon:
            msg += f" - {razon}"
        return msg

    def mensaje_acceso_permitido(self, usuario: str = "") -> str:
        """Mensaje de acceso permitido"""
        msg = f"{ANSI.GREEN_BRIGHT}[✓ ACCESO AUTORIZADO]{ANSI.RESET}"
        if usuario:
            msg += f" - Usuario: {usuario}"
        return msg


# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIONES DE UTILIDAD
# ═══════════════════════════════════════════════════════════════════════════════

def limpiar_pantalla():
    """Limpia la pantalla (funciona en Windows y Linux)"""
    import os
    os.system('cls' if os.name == 'nt' else 'clear')


def centrar_texto(texto: str, ancho: int = 80) -> str:
    """Centra texto en un ancho específico"""
    # Eliminar códigos ANSI para calcular longitud real
    import re
    texto_limpio = re.sub(r'\033\[[0-9;]+m', '', texto)
    espacios = (ancho - len(texto_limpio)) // 2
    return ' ' * espacios + texto


# ═══════════════════════════════════════════════════════════════════════════════
# DEMO Y EJEMPLO DE USO
# ═══════════════════════════════════════════════════════════════════════════════

def demo():
    """Demostración de la configuración visual"""
    import time

    config = SacityVisualConfig()

    # 1. Limpiar pantalla
    limpiar_pantalla()

    # 2. Mostrar banner de inicio
    print(config.get_banner_inicio())
    time.sleep(2)

    # 3. Animación de carga
    print("\n" + ANSI.CYAN + "Iniciando sistema..." + ANSI.RESET + "\n")
    frames = config.get_frames_loading()
    for frame in frames:
        print(f"\r{frame}", end="", flush=True)
        time.sleep(0.5)
    print("\n")

    # 4. Status bar
    print(config.get_status_bar(bateria=85, wifi_nivel=5))

    # 5. Contenido de ejemplo
    print(ANSI.GRAY + "╔══════════════════════════════════════════════════════════════╗" + ANSI.RESET)
    print(ANSI.GRAY + "║" + ANSI.RESET + "  " + ANSI.CYAN_BRIGHT + "MANHATTAN WMS - TERMINAL EMULATOR" + ANSI.RESET + "                       " + ANSI.GRAY + "║" + ANSI.RESET)
    print(ANSI.GRAY + "║" + ANSI.RESET + "                                                              " + ANSI.GRAY + "║" + ANSI.RESET)
    print(ANSI.GRAY + "║" + ANSI.RESET + "  " + ANSI.WHITE_BRIGHT + "Usuario:" + ANSI.RESET + " " + ANSI.CYAN_BRIGHT + "ADMJAJA" + ANSI.RESET + "                                            " + ANSI.GRAY + "║" + ANSI.RESET)
    print(ANSI.GRAY + "║" + ANSI.RESET + "  " + ANSI.WHITE_BRIGHT + "Almacén:" + ANSI.RESET + " " + ANSI.GREEN_BRIGHT + "C22 (CEDIS CANCÚN)" + ANSI.RESET + "                             " + ANSI.GRAY + "║" + ANSI.RESET)
    print(ANSI.GRAY + "║" + ANSI.RESET + "                                                              " + ANSI.GRAY + "║" + ANSI.RESET)
    print(ANSI.GRAY + "╠══════════════════════════════════════════════════════════════╣" + ANSI.RESET)
    print(ANSI.GRAY + "║" + ANSI.RESET + "  " + ANSI.YELLOW_BRIGHT + "> ESCANEAR LPN:" + ANSI.RESET + " " + ANSI.WHITE_BRIGHT + "█" + ANSI.RESET + "                                       " + ANSI.GRAY + "║" + ANSI.RESET)
    print(ANSI.GRAY + "╠══════════════════════════════════════════════════════════════╣" + ANSI.RESET)
    print(ANSI.GRAY + "║" + ANSI.RESET + "  " + ANSI.DIM + "F1:Menu  F2:Buscar  F3:Ayuda" + ANSI.RESET + "                  " + ANSI.DIM + "ESC:Salir" + ANSI.RESET + "   " + ANSI.GRAY + "║" + ANSI.RESET)
    print(ANSI.GRAY + "╚══════════════════════════════════════════════════════════════╝" + ANSI.RESET)

    print()
    print(ANSI.CYAN_BRIGHT + "[INFO]" + ANSI.RESET + " Esperando escaneo... Use pistola o teclado")
    print()

    # 6. Prompt
    prompt = config.get_prompt('secure')
    try:
        user_input = input(prompt)
    except KeyboardInterrupt:
        print("\n")

    # 7. Footer
    print()
    print(config.get_footer())


if __name__ == "__main__":
    demo()
