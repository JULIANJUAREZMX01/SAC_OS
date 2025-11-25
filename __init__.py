"""
═══════════════════════════════════════════════════════════════
SACITY - Sistema Unificado v2.0
Sistema de Automatización de Consultas + Emulador Telnet
═══════════════════════════════════════════════════════════════

SACITY es el sistema completo que integra:

📊 CORE (anteriormente SACYTY)
   - Motor principal de procesamiento
   - Validación de datos
   - Configuración del sistema

🎨 UI - Interfaz de Usuario
   - Interfaz ASCII cybersecurity
   - Colores tema Chedraui
   - Animaciones y menús interactivos

💻 TERMINAL - Emulador VT100/VT220
   - Shell emulador completo
   - Cliente para Windows CE
   - Soporte Symbol MC9000 series

🔧 INSTALLER - Suite de Instalación
   - Detección automática de dispositivos
   - Instalación de drivers
   - Optimización y despliegue

ARQUITECTURA:
=============

sacity/
├── core/           # Motor principal (ex-sacyty)
│   ├── engine.py       # SACITYCore
│   ├── config.py       # SACITYConfig
│   └── validator.py    # SACITYValidator
│
├── ui/             # Interfaz de usuario
│   ├── components.py   # Componentes UI
│   ├── visual_config.py # Paleta de colores
│   ├── main.py         # Aplicación principal
│   └── demo.py         # Demo interactivo
│
├── terminal/       # Emulador terminal
│   ├── shell.py        # Shell VT100/VT220
│   └── client_ce.py    # Cliente Windows CE
│
├── installer/      # Suite de instalación
│   └── suite.py        # Instalador maestro
│
├── tests/          # Tests
├── docs/           # Documentación
└── config/         # Configuración

USO:
====

# Modo completo (UI + Terminal + Core)
from sacity import SacityUnified
app = SacityUnified(mode='full')
app.run()

# Solo core
from sacity.core import SACITYCore
core = SACITYCore()

# Solo UI
from sacity.ui import Colores, Menu
menu = Menu()

# Solo terminal
from sacity.terminal import SacityShell
shell = SacityShell()

# Instalador
from sacity.installer import InstaladorSacity
installer = InstaladorSacity()

CONSOLIDACIÓN:
=============

Esta versión 2.0 consolida las implementaciones previas:
- ✅ SACITY (UI + Terminal)
- ✅ SACYTY (Core + Validación)

Eliminando:
- ❌ Duplicación de código
- ❌ Dependencias circulares
- ❌ Confusión de nomenclatura
- ❌ Código de baja calidad

Resultado:
- ✅ Una sola estructura unificada
- ✅ Modular y escalable
- ✅ Sin redundancias
- ✅ Documentación coherente

"Las máquinas y los sistemas al servicio de los analistas"

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún 427
═══════════════════════════════════════════════════════════════
"""

__version__ = '2.0.0'
__author__ = 'Julián Alexander Juárez Alvarado (ADMJAJA)'
__email__ = 'sistemas@chedraui.com.mx'
__status__ = 'Production'

# Core (ex-SACYTY)
from .core import (
    SACITYCore,
    SACITYConfig,
    SACITYValidator,
    ValidationResult,
    ValidationStatus,
)

# UI
try:
    from .ui import Colores, ArteASCII, Menu, PanelEstado
except ImportError:
    # UI opcional para instalaciones minimal
    Colores = None
    ArteASCII = None
    Menu = None
    PanelEstado = None

# Terminal
try:
    from .terminal import SacityShell, SacityClient
except ImportError:
    # Terminal opcional
    SacityShell = None
    SacityClient = None

# Installer
try:
    from .installer import InstaladorSacity
except ImportError:
    InstaladorSacity = None


# ═══════════════════════════════════════════════════════════════
# CLASE UNIFICADA
# ═══════════════════════════════════════════════════════════════

class SacityUnified:
    """
    Sistema SACITY unificado que integra todos los componentes.

    Modos de operación:
    - 'full': Completo (UI + Terminal + Core)
    - 'minimal': Core + UI básica
    - 'terminal': Solo terminal + Core
    - 'core': Solo core (sin UI ni terminal)

    Ejemplo:
        >>> app = SacityUnified(mode='full')
        >>> app.run()
    """

    def __init__(self, mode: str = 'full', config: dict = None):
        """
        Inicializar SACITY unificado.

        Args:
            mode: Modo de operación ('full', 'minimal', 'terminal', 'core')
            config: Configuración opcional
        """
        self.mode = mode
        self.config = config or {}

        # Siempre inicializar core
        self.core = SACITYCore()
        self.validator = SACITYValidator()

        # Componentes opcionales según modo
        self.ui = None
        self.shell = None
        self.client = None

        if mode in ['full', 'minimal']:
            if Colores and Menu:
                from .ui.components import SacityUI
                self.ui = SacityUI()

        if mode in ['full', 'terminal']:
            if SacityShell:
                self.shell = SacityShell()

        if mode == 'full':
            if SacityClient:
                self.client = SacityClient()

    def run(self):
        """Ejecutar aplicación según modo"""
        if self.mode == 'full' and self.ui:
            # Modo completo con UI
            self.ui.run()
        elif self.mode == 'terminal' and self.shell:
            # Modo terminal
            self.shell.run()
        elif self.mode in ['core', 'minimal']:
            # Modo core - CLI básico
            print(f"SACITY {__version__} - Modo {self.mode}")
            print("Core inicializado correctamente")
        else:
            raise ValueError(f"Modo '{self.mode}' no soportado o componentes faltantes")

    def __enter__(self):
        """Context manager support"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cleanup on exit"""
        if self.shell:
            self.shell.close()
        if self.client:
            self.client.disconnect()

    def __repr__(self):
        return f"SacityUnified(mode='{self.mode}', version='{__version__}')"


# ═══════════════════════════════════════════════════════════════
# EXPORTS
# ═══════════════════════════════════════════════════════════════

__all__ = [
    # Versión y metadatos
    '__version__',
    '__author__',

    # Clase principal
    'SacityUnified',

    # Core
    'SACITYCore',
    'SACITYConfig',
    'SACITYValidator',
    'ValidationResult',
    'ValidationStatus',

    # UI (opcionales)
    'Colores',
    'ArteASCII',
    'Menu',
    'PanelEstado',

    # Terminal (opcionales)
    'SacityShell',
    'SacityClient',

    # Installer (opcional)
    'InstaladorSacity',
]


# ═══════════════════════════════════════════════════════════════
# INFORMACIÓN DE MÓDULO
# ═══════════════════════════════════════════════════════════════

def get_info():
    """Obtener información del módulo"""
    return {
        'version': __version__,
        'author': __author__,
        'status': __status__,
        'components': {
            'core': True,
            'ui': Colores is not None,
            'terminal': SacityShell is not None,
            'installer': InstaladorSacity is not None,
        }
    }


if __name__ == '__main__':
    # Si se ejecuta directamente, mostrar información
    info = get_info()
    print(f"SACITY v{info['version']}")
    print(f"Autor: {info['author']}")
    print("\nComponentes disponibles:")
    for comp, available in info['components'].items():
        status = "✅" if available else "❌"
        print(f"  {status} {comp}")
