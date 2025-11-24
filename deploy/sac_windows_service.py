#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════
SAC WINDOWS SERVICE WRAPPER
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Wrapper para ejecutar SAC como servicio de Windows usando pywin32.
Compatible con NSSM o registro nativo de servicios.

USO:
    # Instalar servicio
    python sac_windows_service.py install

    # Iniciar servicio
    python sac_windows_service.py start

    # Detener servicio
    python sac_windows_service.py stop

    # Eliminar servicio
    python sac_windows_service.py remove

    # Ejecutar en modo debug (consola)
    python sac_windows_service.py debug

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
═══════════════════════════════════════════════════════════════
"""

import os
import sys
import time
import logging
import threading
from pathlib import Path
from datetime import datetime

# Añadir directorio padre al path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_DIR))

# ═══════════════════════════════════════════════════════════════
# CONFIGURACIÓN DEL SERVICIO
# ═══════════════════════════════════════════════════════════════

SERVICE_NAME = "SACMonitor"
SERVICE_DISPLAY_NAME = "SAC Monitor - CEDIS 427"
SERVICE_DESCRIPTION = (
    "Sistema de Automatización de Consultas - Monitoreo continuo de OCs, "
    "validaciones y alertas para CEDIS Chedraui Cancún 427"
)
SERVICE_START_TYPE = "auto"  # auto, manual, disabled

# ═══════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE LOGGING
# ═══════════════════════════════════════════════════════════════

LOG_DIR = PROJECT_DIR / "output" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / f"sac_service_{datetime.now().strftime('%Y%m%d')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("SACService")

# ═══════════════════════════════════════════════════════════════
# VERIFICAR SI PYWIN32 ESTÁ DISPONIBLE
# ═══════════════════════════════════════════════════════════════

try:
    import win32serviceutil
    import win32service
    import win32event
    import servicemanager
    PYWIN32_AVAILABLE = True
except ImportError:
    PYWIN32_AVAILABLE = False
    logger.warning("pywin32 no disponible. Modo servicio Windows deshabilitado.")
    logger.info("Para habilitar: pip install pywin32")

# ═══════════════════════════════════════════════════════════════
# CLASE DEL SERVICIO WINDOWS
# ═══════════════════════════════════════════════════════════════

if PYWIN32_AVAILABLE:

    class SACWindowsService(win32serviceutil.ServiceFramework):
        """
        Servicio Windows para ejecutar SAC Monitor en background.
        """

        _svc_name_ = SERVICE_NAME
        _svc_display_name_ = SERVICE_DISPLAY_NAME
        _svc_description_ = SERVICE_DESCRIPTION

        def __init__(self, args):
            win32serviceutil.ServiceFramework.__init__(self, args)
            self.stop_event = win32event.CreateEvent(None, 0, 0, None)
            self.is_running = True
            self.monitor_thread = None

        def SvcStop(self):
            """Detiene el servicio"""
            logger.info("Recibida señal de parada del servicio")
            self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
            self.is_running = False
            win32event.SetEvent(self.stop_event)

        def SvcDoRun(self):
            """Ejecuta el servicio principal"""
            logger.info("═" * 60)
            logger.info("SAC Windows Service iniciando...")
            logger.info(f"Directorio de trabajo: {PROJECT_DIR}")
            logger.info("═" * 60)

            servicemanager.LogMsg(
                servicemanager.EVENTLOG_INFORMATION_TYPE,
                servicemanager.PYS_SERVICE_STARTED,
                (self._svc_name_, '')
            )

            try:
                self.main()
            except Exception as e:
                logger.error(f"Error fatal en servicio: {e}")
                servicemanager.LogErrorMsg(f"SAC Service Error: {e}")

        def main(self):
            """Lógica principal del servicio"""
            os.chdir(str(PROJECT_DIR))

            # Iniciar monitor en thread separado
            self.monitor_thread = threading.Thread(
                target=self.run_monitor,
                daemon=True
            )
            self.monitor_thread.start()

            # Esperar señal de parada
            while self.is_running:
                rc = win32event.WaitForSingleObject(self.stop_event, 5000)
                if rc == win32event.WAIT_OBJECT_0:
                    break

            logger.info("SAC Windows Service detenido")

        def run_monitor(self):
            """Ejecuta el monitor SAC"""
            try:
                # Importar y ejecutar el orquestador
                from maestro import Orquestador

                logger.info("Iniciando Orquestador SAC...")
                orquestador = Orquestador()

                while self.is_running:
                    try:
                        orquestador.ejecutar_ciclo()
                        time.sleep(60)  # Esperar entre ciclos
                    except Exception as e:
                        logger.error(f"Error en ciclo de monitoreo: {e}")
                        time.sleep(30)

            except ImportError as e:
                logger.error(f"Error importando módulos SAC: {e}")
                # Fallback: ejecutar main.py directamente
                self.run_main_fallback()

            except Exception as e:
                logger.error(f"Error en run_monitor: {e}")

        def run_main_fallback(self):
            """Fallback: ejecutar main.py como subproceso"""
            import subprocess

            logger.info("Usando modo fallback (subproceso)")

            main_py = PROJECT_DIR / "main.py"
            if not main_py.exists():
                logger.error("main.py no encontrado")
                return

            while self.is_running:
                try:
                    process = subprocess.Popen(
                        [sys.executable, str(main_py), "--daemon"],
                        cwd=str(PROJECT_DIR),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )

                    while self.is_running and process.poll() is None:
                        time.sleep(1)

                    if not self.is_running:
                        process.terminate()

                except Exception as e:
                    logger.error(f"Error en fallback: {e}")
                    time.sleep(30)


# ═══════════════════════════════════════════════════════════════
# MODO STANDALONE (SIN PYWIN32)
# ═══════════════════════════════════════════════════════════════

class SACStandaloneService:
    """
    Servicio standalone para sistemas sin pywin32.
    Útil para testing o ejecución en Linux/Mac.
    """

    def __init__(self):
        self.is_running = True
        self.monitor_thread = None

    def start(self):
        """Inicia el servicio en modo standalone"""
        logger.info("═" * 60)
        logger.info("SAC Standalone Service iniciando...")
        logger.info(f"Directorio de trabajo: {PROJECT_DIR}")
        logger.info("═" * 60)

        os.chdir(str(PROJECT_DIR))

        # Configurar manejo de señales
        import signal

        def signal_handler(signum, frame):
            logger.info("Señal de parada recibida")
            self.stop()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Ejecutar monitor
        self.run_monitor()

    def stop(self):
        """Detiene el servicio"""
        logger.info("Deteniendo servicio...")
        self.is_running = False

    def run_monitor(self):
        """Ejecuta el monitor SAC"""
        try:
            from maestro import Orquestador

            logger.info("Iniciando Orquestador SAC...")
            orquestador = Orquestador()

            while self.is_running:
                try:
                    orquestador.ejecutar_ciclo()
                    time.sleep(60)
                except Exception as e:
                    logger.error(f"Error en ciclo: {e}")
                    time.sleep(30)

        except ImportError as e:
            logger.error(f"Error importando módulos: {e}")
            logger.info("Ejecutando en modo básico...")

            while self.is_running:
                logger.info("SAC Service running... (modo básico)")
                time.sleep(60)

        except Exception as e:
            logger.error(f"Error fatal: {e}")


# ═══════════════════════════════════════════════════════════════
# FUNCIONES DE GESTIÓN DEL SERVICIO
# ═══════════════════════════════════════════════════════════════

def install_service():
    """Instala el servicio Windows"""
    if not PYWIN32_AVAILABLE:
        print("ERROR: pywin32 no está instalado")
        print("Ejecute: pip install pywin32")
        return False

    try:
        # Instalar servicio
        win32serviceutil.InstallService(
            SACWindowsService._svc_reg_class_,
            SERVICE_NAME,
            SERVICE_DISPLAY_NAME,
            startType=win32service.SERVICE_AUTO_START,
            description=SERVICE_DESCRIPTION
        )
        print(f"Servicio '{SERVICE_NAME}' instalado correctamente")
        return True
    except Exception as e:
        print(f"Error instalando servicio: {e}")
        return False


def remove_service():
    """Elimina el servicio Windows"""
    if not PYWIN32_AVAILABLE:
        print("ERROR: pywin32 no está instalado")
        return False

    try:
        win32serviceutil.RemoveService(SERVICE_NAME)
        print(f"Servicio '{SERVICE_NAME}' eliminado")
        return True
    except Exception as e:
        print(f"Error eliminando servicio: {e}")
        return False


def start_service():
    """Inicia el servicio Windows"""
    if not PYWIN32_AVAILABLE:
        print("ERROR: pywin32 no está instalado")
        return False

    try:
        win32serviceutil.StartService(SERVICE_NAME)
        print(f"Servicio '{SERVICE_NAME}' iniciado")
        return True
    except Exception as e:
        print(f"Error iniciando servicio: {e}")
        return False


def stop_service():
    """Detiene el servicio Windows"""
    if not PYWIN32_AVAILABLE:
        print("ERROR: pywin32 no está instalado")
        return False

    try:
        win32serviceutil.StopService(SERVICE_NAME)
        print(f"Servicio '{SERVICE_NAME}' detenido")
        return True
    except Exception as e:
        print(f"Error deteniendo servicio: {e}")
        return False


def get_service_status():
    """Obtiene el estado del servicio"""
    if not PYWIN32_AVAILABLE:
        return "UNKNOWN (pywin32 no disponible)"

    try:
        status = win32serviceutil.QueryServiceStatus(SERVICE_NAME)
        state = status[1]

        states = {
            win32service.SERVICE_STOPPED: "DETENIDO",
            win32service.SERVICE_START_PENDING: "INICIANDO",
            win32service.SERVICE_STOP_PENDING: "DETENIENDO",
            win32service.SERVICE_RUNNING: "EN EJECUCIÓN",
            win32service.SERVICE_CONTINUE_PENDING: "CONTINUANDO",
            win32service.SERVICE_PAUSE_PENDING: "PAUSANDO",
            win32service.SERVICE_PAUSED: "PAUSADO",
        }

        return states.get(state, f"DESCONOCIDO ({state})")
    except Exception as e:
        return f"ERROR: {e}"


def run_debug():
    """Ejecuta en modo debug (consola)"""
    print("═" * 60)
    print("SAC Service - Modo Debug")
    print("Presione Ctrl+C para detener")
    print("═" * 60)

    service = SACStandaloneService()
    service.start()


# ═══════════════════════════════════════════════════════════════
# PUNTO DE ENTRADA
# ═══════════════════════════════════════════════════════════════

def print_usage():
    """Muestra ayuda de uso"""
    print("""
═══════════════════════════════════════════════════════════════
SAC Windows Service - Comandos disponibles
═══════════════════════════════════════════════════════════════

  install     - Instala el servicio Windows
  remove      - Elimina el servicio Windows
  start       - Inicia el servicio
  stop        - Detiene el servicio
  restart     - Reinicia el servicio
  status      - Muestra el estado del servicio
  debug       - Ejecuta en modo consola (debug)

Ejemplos:
  python sac_windows_service.py install
  python sac_windows_service.py start
  python sac_windows_service.py status

Nota: Los comandos install/remove/start/stop requieren
      privilegios de administrador.
═══════════════════════════════════════════════════════════════
""")


def main():
    """Punto de entrada principal"""
    if len(sys.argv) < 2:
        print_usage()
        return

    command = sys.argv[1].lower()

    if command == "install":
        install_service()

    elif command == "remove":
        remove_service()

    elif command == "start":
        start_service()

    elif command == "stop":
        stop_service()

    elif command == "restart":
        stop_service()
        time.sleep(2)
        start_service()

    elif command == "status":
        status = get_service_status()
        print(f"Estado del servicio '{SERVICE_NAME}': {status}")

    elif command == "debug":
        run_debug()

    elif command in ("help", "-h", "--help"):
        print_usage()

    else:
        # Intentar manejar con win32serviceutil
        if PYWIN32_AVAILABLE:
            win32serviceutil.HandleCommandLine(SACWindowsService)
        else:
            print(f"Comando desconocido: {command}")
            print_usage()


if __name__ == "__main__":
    main()
