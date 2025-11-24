#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
SAC AGENT - AGENTE DE IA PARA CENTROS DE DISTRIBUCIÓN
SAC VISION 3.0
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════════════════════

Punto de entrada principal del Agente SAC VISION 3.0

El Agente SAC es una solución integral e inteligente para centros de
distribución y logística, siendo el cerebro orquestador del departamento
de sistemas.

CAPACIDADES:
- Interacción con la PC (mouse, teclado, pantalla)
- Control y visualización de aplicaciones
- Extracción, procesamiento y edición de documentos
- Creación y envío de reportes (Excel, PDF, Word)
- Conexión a bases de datos (Manhattan WMS - DB2)
- Automatización de tareas repetitivas

ROLES SOPORTADOS:
- Analistas de Sistemas
- Analistas de Recursos Humanos
- Analistas de Control
- Analistas de Tráfico
- Analistas de Recibo
- Analistas de Preparación
- Analistas de Expedición

USO:
    python sac_agent.py              # Modo interactivo
    python sac_agent.py --chat       # Chat directo
    python sac_agent.py --status     # Ver estado del sistema
    python sac_agent.py --help       # Ayuda

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún 427
Tiendas Chedraui S.A. de C.V.

"Las máquinas y los sistemas al servicio de los analistas"
═══════════════════════════════════════════════════════════════════════════════
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

# Configurar path del proyecto
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# Cargar variables de entorno
from dotenv import load_dotenv
env_file = PROJECT_ROOT / '.env'
if env_file.exists():
    load_dotenv(env_file)
else:
    # Intentar cargar desde 'env' si .env no existe
    env_template = PROJECT_ROOT / 'env'
    if env_template.exists():
        load_dotenv(env_template)


# ═══════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE LOGGING
# ═══════════════════════════════════════════════════════════════

def setup_logging(verbose: bool = False):
    """Configura el sistema de logging"""
    level = logging.DEBUG if verbose else logging.INFO

    # Crear directorio de logs
    logs_dir = PROJECT_ROOT / 'output' / 'logs'
    logs_dir.mkdir(parents=True, exist_ok=True)

    # Configurar formato
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'

    # Handler para archivo
    log_file = logs_dir / f'sac_agent_{datetime.now().strftime("%Y%m%d")}.log'
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(log_format, date_format))

    # Handler para consola (solo warnings y errores en modo normal)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if verbose else logging.WARNING)
    console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))

    # Configurar root logger
    logging.basicConfig(
        level=level,
        handlers=[file_handler, console_handler]
    )

    return logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# CONSTANTES DEL AGENTE
# ═══════════════════════════════════════════════════════════════

AGENT_VERSION = "3.0.0"
AGENT_CODENAME = "Vision"
AGENT_BUILD = "2025-11-24"

CREATOR = {
    'nombre': 'Julián Alexander Juárez Alvarado',
    'codigo': 'ADMJAJA',
    'cargo': 'Jefe de Sistemas',
    'cedis': 'CEDIS Cancún 427',
    'organizacion': 'Tiendas Chedraui S.A. de C.V.',
    'region': 'Sureste'
}

EQUIPO = [
    {'nombre': 'Larry Adanael Basto Díaz', 'cargo': 'Analista de Sistemas'},
    {'nombre': 'Adrian Quintana Zuñiga', 'cargo': 'Analista de Sistemas'},
]

BANNER = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║      ███████╗ █████╗  ██████╗     ██╗   ██╗██╗███████╗██╗ ██████╗ ███╗   ██╗ ║
║      ██╔════╝██╔══██╗██╔════╝     ██║   ██║██║██╔════╝██║██╔═══██╗████╗  ██║ ║
║      ███████╗███████║██║          ██║   ██║██║███████╗██║██║   ██║██╔██╗ ██║ ║
║      ╚════██║██╔══██║██║          ╚██╗ ██╔╝██║╚════██║██║██║   ██║██║╚██╗██║ ║
║      ███████║██║  ██║╚██████╗      ╚████╔╝ ██║███████║██║╚██████╔╝██║ ╚████║ ║
║      ╚══════╝╚═╝  ╚═╝ ╚═════╝       ╚═══╝  ╚═╝╚══════╝╚═╝ ╚═════╝ ╚═╝  ╚═══╝ ║
║                                                                              ║
║                        Sistema de Automatización de Consultas                ║
║                              CEDIS Cancún 427 - v{AGENT_VERSION}                   ║
║                                                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Agente de IA con capacidades de Computer Use                                ║
║  Powered by Claude (Anthropic)                                               ║
║                                                                              ║
║  Creador: {CREATOR['nombre'][:40]:<40}  ║
║  {CREATOR['cargo']} - {CREATOR['cedis']:<24}                           ║
║  {CREATOR['organizacion']:<60}          ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

HELP_TEXT = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                           COMANDOS DISPONIBLES                               ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  COMANDOS ESPECIALES (durante la conversación):                              ║
║  ─────────────────────────────────────────────────────────────────────────── ║
║  /ayuda      - Muestra esta ayuda                                            ║
║  /limpiar    - Limpia el historial de conversación                           ║
║  /estado     - Muestra el estado del sistema                                 ║
║  /stats      - Muestra estadísticas de la sesión                             ║
║  /screenshot - Toma una captura de pantalla                                  ║
║  /info       - Información del agente                                        ║
║  /salir      - Termina la sesión                                             ║
║                                                                              ║
║  EJEMPLOS DE USO:                                                            ║
║  ─────────────────────────────────────────────────────────────────────────── ║
║  > Abre Excel y crea una tabla con las ventas del mes                        ║
║  > Toma una captura de pantalla y describe lo que ves                        ║
║  > Lee el archivo report.xlsx y resume los datos                             ║
║  > Ejecuta el comando 'dir' y muéstrame los resultados                       ║
║  > Ayúdame a validar la OC 750384123456                                      ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""


# ═══════════════════════════════════════════════════════════════
# CLASE PRINCIPAL: SAC AGENT CLI
# ═══════════════════════════════════════════════════════════════

class SACAgentCLI:
    """
    Interfaz de línea de comandos para el Agente SAC

    Proporciona:
    - Modo interactivo de chat
    - Comandos especiales con /
    - Visualización de estado
    - Gestión de sesión
    """

    def __init__(self, verbose: bool = False):
        """Inicializa la CLI del agente"""
        self.verbose = verbose
        self.logger = setup_logging(verbose)
        self.agent = None
        self.running = False

        # Inicializar agente
        self._init_agent()

    def _init_agent(self):
        """Inicializa el motor del agente"""
        try:
            from modules.sac_agent_core import SACAgentCore
            self.agent = SACAgentCore()
            self.logger.info("✅ Agente SAC inicializado")
        except ImportError as e:
            self.logger.error(f"❌ Error importando módulos: {e}")
            print(f"\n❌ Error: No se pudo cargar el módulo del agente.")
            print(f"   Detalle: {e}")
            print(f"\n   Asegúrate de que todas las dependencias estén instaladas:")
            print(f"   pip install anthropic pyautogui pillow pandas openpyxl")
        except Exception as e:
            self.logger.error(f"❌ Error inicializando agente: {e}")
            print(f"\n❌ Error inicializando agente: {e}")

    def show_banner(self):
        """Muestra el banner de inicio"""
        print(BANNER)

    def show_status(self):
        """Muestra el estado del sistema"""
        print("\n" + "═" * 70)
        print(" 📊 ESTADO DEL SISTEMA")
        print("═" * 70)

        # Verificar API Key
        api_key = os.getenv('ANTHROPIC_API_KEY', '')
        api_status = "✅ Configurada" if api_key else "❌ No configurada"
        print(f"\n  🔑 ANTHROPIC_API_KEY: {api_status}")

        if api_key:
            print(f"     (****{api_key[-4:]})")

        # Modelo
        model = os.getenv('ANTHROPIC_MODEL', 'claude-sonnet-4-20250514')
        print(f"  🤖 Modelo: {model}")

        # Computer Use
        cu_enabled = os.getenv('COMPUTER_USE_ENABLED', 'true').lower() == 'true'
        cu_status = "✅ Habilitado" if cu_enabled else "❌ Deshabilitado"
        print(f"  🖥️  Computer Use: {cu_status}")

        # Verificar dependencias
        print("\n  📦 Dependencias:")

        deps = [
            ('anthropic', 'API de Claude'),
            ('pyautogui', 'Control de mouse/teclado'),
            ('PIL', 'Captura de pantalla'),
            ('pandas', 'Procesamiento de datos'),
            ('openpyxl', 'Archivos Excel'),
        ]

        for module, description in deps:
            try:
                __import__(module)
                print(f"     ✅ {module}: {description}")
            except ImportError:
                print(f"     ❌ {module}: {description} (no instalado)")

        # Estado del agente
        if self.agent:
            ready, msg = self.agent.is_ready()
            status = "✅ Listo" if ready else f"⚠️ {msg}"
            print(f"\n  🤖 Estado del Agente: {status}")

            if ready:
                stats = self.agent.get_stats()
                print(f"     Sesión iniciada: {stats['session_start'].strftime('%H:%M:%S')}")

        print("\n" + "═" * 70)

    def show_help(self):
        """Muestra la ayuda"""
        print(HELP_TEXT)

    def show_info(self):
        """Muestra información del agente"""
        print("\n" + "═" * 70)
        print(" 🤖 INFORMACIÓN DEL AGENTE SAC")
        print("═" * 70)
        print(f"""
  Nombre:        SAC Agent (Sistema de Automatización de Consultas)
  Versión:       {AGENT_VERSION}
  Codename:      {AGENT_CODENAME}
  Build:         {AGENT_BUILD}

  Creador:       {CREATOR['nombre']}
  Código:        {CREATOR['codigo']}
  Cargo:         {CREATOR['cargo']}
  CEDIS:         {CREATOR['cedis']}
  Organización:  {CREATOR['organizacion']}
  Región:        {CREATOR['region']}

  Equipo de Desarrollo:
  • Larry Adanael Basto Díaz - Analista de Sistemas
  • Adrian Quintana Zuñiga - Analista de Sistemas

  Supervisor Regional:
  • Itza Vera Reyes Sarubí (Villahermosa)

  Filosofía:
  "Las máquinas y los sistemas al servicio de los analistas"
""")
        print("═" * 70)

    def show_stats(self):
        """Muestra estadísticas de la sesión"""
        if not self.agent:
            print("\n⚠️ Agente no inicializado")
            return

        stats = self.agent.get_stats()
        print("\n" + "═" * 70)
        print(" 📈 ESTADÍSTICAS DE SESIÓN")
        print("═" * 70)
        print(f"""
  Sesión iniciada:     {stats['session_start'].strftime('%Y-%m-%d %H:%M:%S')}
  Duración:            {stats['session_duration']}
  Mensajes enviados:   {stats['messages_sent']}
  Tokens utilizados:   {stats['tokens_used']}
  Herramientas usadas: {stats['tools_executed']}
  Errores:             {stats['errors']}
  Longitud historial:  {stats['conversation_length']}
  Estado actual:       {stats['state']}
""")
        print("═" * 70)

    def process_special_command(self, command: str) -> bool:
        """
        Procesa comandos especiales

        Args:
            command: Comando a procesar

        Returns:
            True si fue un comando especial, False si no
        """
        cmd = command.lower().strip()

        if cmd in ['/ayuda', '/help', '/?']:
            self.show_help()
            return True

        elif cmd in ['/limpiar', '/clear', '/cls']:
            if self.agent:
                self.agent.clear_history()
            print("\n🧹 Historial limpiado\n")
            return True

        elif cmd in ['/estado', '/status']:
            self.show_status()
            return True

        elif cmd in ['/stats', '/estadisticas']:
            self.show_stats()
            return True

        elif cmd in ['/info', '/about', '/acerca']:
            self.show_info()
            return True

        elif cmd in ['/screenshot', '/captura']:
            self._take_screenshot()
            return True

        elif cmd in ['/salir', '/exit', '/quit', '/q']:
            self.running = False
            return True

        return False

    def _take_screenshot(self):
        """Toma una captura de pantalla"""
        print("\n📸 Tomando captura de pantalla...")

        try:
            from modules.computer_use import get_computer_tools
            tools = get_computer_tools()
            result = tools.screenshot()

            if result.success:
                # Guardar captura
                output_dir = PROJECT_ROOT / 'output' / 'screenshots'
                output_dir.mkdir(parents=True, exist_ok=True)

                import base64
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = output_dir / f'screenshot_{timestamp}.png'

                img_data = base64.b64decode(result.result['image_base64'])
                with open(filename, 'wb') as f:
                    f.write(img_data)

                print(f"✅ Captura guardada: {filename}")
                print(f"   Dimensiones: {result.result['width']}x{result.result['height']}")
            else:
                print(f"❌ Error: {result.error}")

        except Exception as e:
            print(f"❌ Error tomando captura: {e}")

    def run_interactive(self):
        """Ejecuta el modo interactivo"""
        self.show_banner()

        # Verificar que el agente está listo
        if not self.agent:
            print("\n❌ El agente no pudo inicializarse.")
            print("   Verifica tu configuración y dependencias.")
            return

        ready, msg = self.agent.is_ready()
        if not ready:
            print(f"\n⚠️ Advertencia: {msg}")
            print("   Algunas funciones pueden no estar disponibles.")

        print("\n💬 Escribe tu mensaje o /ayuda para ver comandos disponibles.")
        print("   Escribe /salir para terminar.\n")

        self.running = True

        while self.running:
            try:
                # Prompt
                user_input = input("\n[Usuario] > ").strip()

                if not user_input:
                    continue

                # Procesar comandos especiales
                if user_input.startswith('/'):
                    if self.process_special_command(user_input):
                        continue

                # Enviar al agente
                print("\n[SAC Agent] Procesando...")

                response = self.agent.chat(user_input)

                print(f"\n[SAC Agent] {response}")

            except KeyboardInterrupt:
                print("\n\n⚠️ Interrumpido por el usuario")
                self.running = False

            except EOFError:
                self.running = False

            except Exception as e:
                self.logger.error(f"Error en loop interactivo: {e}")
                print(f"\n❌ Error: {e}")

        # Despedida
        self._show_goodbye()

    def _show_goodbye(self):
        """Muestra mensaje de despedida"""
        print(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║  👋 ¡Hasta luego!                                                            ║
║                                                                              ║
║  Gracias por usar SAC VISION 3.0                                             ║
║                                                                              ║
║  Este sistema fue desarrollado con dedicación por:                           ║
║  {CREATOR['nombre']:<60}          ║
║  {CREATOR['cargo']} - {CREATOR['cedis']:<24}                           ║
║                                                                              ║
║  "Las máquinas y los sistemas al servicio de los analistas"                  ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
        """)


# ═══════════════════════════════════════════════════════════════
# PUNTO DE ENTRADA
# ═══════════════════════════════════════════════════════════════

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description='SAC Agent - Agente de IA para Centros de Distribución',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Ejemplos:
  python sac_agent.py              # Modo interactivo
  python sac_agent.py --status     # Ver estado del sistema
  python sac_agent.py --info       # Información del agente
  python sac_agent.py -v           # Modo verbose

SAC VISION 3.0 - CEDIS Cancún 427
Desarrollado por: {CREATOR['nombre']} ({CREATOR['codigo']})
        """
    )

    parser.add_argument(
        '--status', '-s',
        action='store_true',
        help='Muestra el estado del sistema'
    )

    parser.add_argument(
        '--info', '-i',
        action='store_true',
        help='Muestra información del agente'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Modo verbose (más información en logs)'
    )

    parser.add_argument(
        '--version',
        action='store_true',
        help='Muestra la versión'
    )

    parser.add_argument(
        '--check',
        action='store_true',
        help='Verifica dependencias y configuración'
    )

    args = parser.parse_args()

    # Versión
    if args.version:
        print(f"SAC Agent v{AGENT_VERSION} ({AGENT_CODENAME})")
        print(f"Build: {AGENT_BUILD}")
        print(f"Creador: {CREATOR['nombre']} ({CREATOR['codigo']})")
        return

    # Inicializar CLI
    cli = SACAgentCLI(verbose=args.verbose)

    # Modo status
    if args.status or args.check:
        cli.show_status()
        return

    # Modo info
    if args.info:
        cli.show_info()
        return

    # Modo interactivo (default)
    cli.run_interactive()


if __name__ == "__main__":
    main()
