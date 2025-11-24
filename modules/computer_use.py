"""
═══════════════════════════════════════════════════════════════
MÓDULO DE COMPUTER USE - SAC VISION 3.0
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Módulo que proporciona capacidades de control de computadora para
el Agente SAC, incluyendo:
- Control de mouse (click, movimiento, scroll)
- Control de teclado (escritura, teclas especiales)
- Captura de pantalla
- Operaciones con archivos
- Lanzamiento de aplicaciones

IMPORTANTE: Estas capacidades requieren supervisión y están
restringidas a usuarios con nivel ADMIN o SISTEMAS.

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
═══════════════════════════════════════════════════════════════
"""

import os
import sys
import time
import base64
import logging
import subprocess
import platform
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple, Literal
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import io

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════

class ComputerUseConfig:
    """Configuración del módulo de computer use"""

    def __init__(self):
        self.enabled = os.getenv('COMPUTER_USE_ENABLED', 'true').lower() == 'true'
        self.screen_width = int(os.getenv('SCREEN_WIDTH', '0')) or None
        self.screen_height = int(os.getenv('SCREEN_HEIGHT', '0')) or None
        self.action_delay = int(os.getenv('COMPUTER_ACTION_DELAY', '100'))
        self.allow_mouse = os.getenv('ALLOW_MOUSE_CONTROL', 'true').lower() == 'true'
        self.allow_keyboard = os.getenv('ALLOW_KEYBOARD_CONTROL', 'true').lower() == 'true'
        self.allow_screenshot = os.getenv('ALLOW_SCREEN_CAPTURE', 'true').lower() == 'true'
        self.allow_file_ops = os.getenv('ALLOW_FILE_OPERATIONS', 'true').lower() == 'true'
        self.allow_app_launch = os.getenv('ALLOW_APP_LAUNCH', 'true').lower() == 'true'
        self.timeout = int(os.getenv('COMPUTER_USE_TIMEOUT', '30'))


# ═══════════════════════════════════════════════════════════════
# ENUMERACIONES
# ═══════════════════════════════════════════════════════════════

class MouseButton(Enum):
    """Botones del mouse"""
    LEFT = "left"
    RIGHT = "right"
    MIDDLE = "middle"


class ActionType(Enum):
    """Tipos de acciones de computer use"""
    SCREENSHOT = "screenshot"
    MOUSE_MOVE = "mouse_move"
    MOUSE_CLICK = "click"
    MOUSE_DOUBLE_CLICK = "double_click"
    MOUSE_SCROLL = "scroll"
    KEYBOARD_TYPE = "type"
    KEYBOARD_KEY = "key"
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    FILE_LIST = "file_list"
    APP_LAUNCH = "app_launch"
    APP_CLOSE = "app_close"
    CURSOR_POSITION = "cursor_position"


# ═══════════════════════════════════════════════════════════════
# DATACLASSES
# ═══════════════════════════════════════════════════════════════

@dataclass
class ComputerAction:
    """Representa una acción de computer use"""
    action_type: ActionType
    params: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    success: bool = False
    result: Any = None
    error: Optional[str] = None
    duration_ms: float = 0.0


@dataclass
class ScreenInfo:
    """Información de la pantalla"""
    width: int
    height: int
    scale_factor: float = 1.0
    displays: int = 1


# ═══════════════════════════════════════════════════════════════
# CLASE PRINCIPAL: COMPUTER USE TOOLS
# ═══════════════════════════════════════════════════════════════

class ComputerUseTools:
    """
    Herramientas de control de computadora para SAC VISION 3.0

    Proporciona capacidades de:
    - Captura de pantalla
    - Control de mouse
    - Control de teclado
    - Operaciones con archivos
    - Lanzamiento de aplicaciones
    """

    def __init__(self, config: ComputerUseConfig = None):
        """
        Inicializa las herramientas de computer use

        Args:
            config: Configuración personalizada (opcional)
        """
        self.config = config or ComputerUseConfig()
        self.platform = platform.system().lower()
        self.history: List[ComputerAction] = []

        # Verificar dependencias
        self._pyautogui = None
        self._pil = None
        self._screen_info: Optional[ScreenInfo] = None

        self._init_dependencies()

        logger.info(f"🖥️ ComputerUseTools inicializado - Platform: {self.platform}")

    def _init_dependencies(self):
        """Inicializa las dependencias necesarias"""
        # PyAutoGUI para control de mouse y teclado
        try:
            import pyautogui
            pyautogui.FAILSAFE = True  # Mover mouse a esquina superior izquierda para abortar
            pyautogui.PAUSE = self.config.action_delay / 1000.0  # Convertir ms a segundos
            self._pyautogui = pyautogui
            logger.info("✅ PyAutoGUI disponible")
        except ImportError:
            logger.warning("⚠️ PyAutoGUI no instalado. Instala: pip install pyautogui")

        # Pillow para capturas de pantalla
        try:
            from PIL import Image, ImageGrab
            self._pil = {'Image': Image, 'ImageGrab': ImageGrab}
            logger.info("✅ Pillow disponible")
        except ImportError:
            logger.warning("⚠️ Pillow no instalado. Instala: pip install pillow")

        # Detectar información de pantalla
        self._detect_screen_info()

    def _detect_screen_info(self):
        """Detecta información de la pantalla"""
        try:
            if self._pyautogui:
                size = self._pyautogui.size()
                self._screen_info = ScreenInfo(
                    width=self.config.screen_width or size.width,
                    height=self.config.screen_height or size.height,
                )
            else:
                # Valores por defecto
                self._screen_info = ScreenInfo(
                    width=self.config.screen_width or 1920,
                    height=self.config.screen_height or 1080,
                )

            logger.info(f"📐 Pantalla detectada: {self._screen_info.width}x{self._screen_info.height}")

        except Exception as e:
            logger.error(f"❌ Error detectando pantalla: {e}")
            self._screen_info = ScreenInfo(width=1920, height=1080)

    # ═══════════════════════════════════════════════════════════
    # CAPTURA DE PANTALLA
    # ═══════════════════════════════════════════════════════════

    def screenshot(self, region: Optional[Tuple[int, int, int, int]] = None) -> ComputerAction:
        """
        Captura la pantalla completa o una región específica

        Args:
            region: Tupla (x, y, width, height) para capturar región específica

        Returns:
            ComputerAction con imagen en base64 como resultado
        """
        action = ComputerAction(
            action_type=ActionType.SCREENSHOT,
            params={'region': region}
        )

        if not self.config.allow_screenshot:
            action.error = "Captura de pantalla no permitida"
            return self._finish_action(action)

        start_time = time.time()

        try:
            if self._pil:
                # Usar Pillow
                if region:
                    img = self._pil['ImageGrab'].grab(bbox=region)
                else:
                    img = self._pil['ImageGrab'].grab()

                # Convertir a base64
                buffer = io.BytesIO()
                img.save(buffer, format='PNG')
                img_base64 = base64.standard_b64encode(buffer.getvalue()).decode('utf-8')

                action.success = True
                action.result = {
                    'image_base64': img_base64,
                    'width': img.width,
                    'height': img.height,
                    'format': 'png'
                }

            elif self._pyautogui:
                # Usar PyAutoGUI como fallback
                if region:
                    img = self._pyautogui.screenshot(region=region)
                else:
                    img = self._pyautogui.screenshot()

                buffer = io.BytesIO()
                img.save(buffer, format='PNG')
                img_base64 = base64.standard_b64encode(buffer.getvalue()).decode('utf-8')

                action.success = True
                action.result = {
                    'image_base64': img_base64,
                    'width': img.width,
                    'height': img.height,
                    'format': 'png'
                }
            else:
                action.error = "No hay librería de captura disponible"

        except Exception as e:
            action.error = f"Error capturando pantalla: {str(e)}"
            logger.error(f"❌ {action.error}")

        return self._finish_action(action, start_time)

    # ═══════════════════════════════════════════════════════════
    # CONTROL DE MOUSE
    # ═══════════════════════════════════════════════════════════

    def mouse_move(self, x: int, y: int, duration: float = 0.5) -> ComputerAction:
        """
        Mueve el mouse a una posición específica

        Args:
            x: Coordenada X
            y: Coordenada Y
            duration: Duración del movimiento en segundos

        Returns:
            ComputerAction con resultado
        """
        action = ComputerAction(
            action_type=ActionType.MOUSE_MOVE,
            params={'x': x, 'y': y, 'duration': duration}
        )

        if not self.config.allow_mouse:
            action.error = "Control de mouse no permitido"
            return self._finish_action(action)

        if not self._pyautogui:
            action.error = "PyAutoGUI no disponible"
            return self._finish_action(action)

        start_time = time.time()

        try:
            self._pyautogui.moveTo(x, y, duration=duration)
            action.success = True
            action.result = {'final_position': (x, y)}

        except Exception as e:
            action.error = f"Error moviendo mouse: {str(e)}"
            logger.error(f"❌ {action.error}")

        return self._finish_action(action, start_time)

    def mouse_click(
        self,
        x: Optional[int] = None,
        y: Optional[int] = None,
        button: str = "left",
        clicks: int = 1
    ) -> ComputerAction:
        """
        Realiza click del mouse

        Args:
            x: Coordenada X (None para posición actual)
            y: Coordenada Y (None para posición actual)
            button: 'left', 'right', 'middle'
            clicks: Número de clicks

        Returns:
            ComputerAction con resultado
        """
        action = ComputerAction(
            action_type=ActionType.MOUSE_CLICK if clicks == 1 else ActionType.MOUSE_DOUBLE_CLICK,
            params={'x': x, 'y': y, 'button': button, 'clicks': clicks}
        )

        if not self.config.allow_mouse:
            action.error = "Control de mouse no permitido"
            return self._finish_action(action)

        if not self._pyautogui:
            action.error = "PyAutoGUI no disponible"
            return self._finish_action(action)

        start_time = time.time()

        try:
            if x is not None and y is not None:
                self._pyautogui.click(x, y, clicks=clicks, button=button)
            else:
                self._pyautogui.click(clicks=clicks, button=button)

            action.success = True
            action.result = {
                'clicked_at': (x, y) if x and y else self._pyautogui.position(),
                'button': button,
                'clicks': clicks
            }

        except Exception as e:
            action.error = f"Error haciendo click: {str(e)}"
            logger.error(f"❌ {action.error}")

        return self._finish_action(action, start_time)

    def mouse_scroll(self, clicks: int, x: Optional[int] = None, y: Optional[int] = None) -> ComputerAction:
        """
        Realiza scroll del mouse

        Args:
            clicks: Cantidad de scroll (positivo = arriba, negativo = abajo)
            x: Coordenada X (opcional)
            y: Coordenada Y (opcional)

        Returns:
            ComputerAction con resultado
        """
        action = ComputerAction(
            action_type=ActionType.MOUSE_SCROLL,
            params={'clicks': clicks, 'x': x, 'y': y}
        )

        if not self.config.allow_mouse:
            action.error = "Control de mouse no permitido"
            return self._finish_action(action)

        if not self._pyautogui:
            action.error = "PyAutoGUI no disponible"
            return self._finish_action(action)

        start_time = time.time()

        try:
            if x is not None and y is not None:
                self._pyautogui.scroll(clicks, x, y)
            else:
                self._pyautogui.scroll(clicks)

            action.success = True
            action.result = {'scrolled': clicks}

        except Exception as e:
            action.error = f"Error haciendo scroll: {str(e)}"
            logger.error(f"❌ {action.error}")

        return self._finish_action(action, start_time)

    def get_cursor_position(self) -> ComputerAction:
        """
        Obtiene la posición actual del cursor

        Returns:
            ComputerAction con posición (x, y)
        """
        action = ComputerAction(action_type=ActionType.CURSOR_POSITION)

        if not self._pyautogui:
            action.error = "PyAutoGUI no disponible"
            return self._finish_action(action)

        start_time = time.time()

        try:
            pos = self._pyautogui.position()
            action.success = True
            action.result = {'x': pos.x, 'y': pos.y}

        except Exception as e:
            action.error = f"Error obteniendo posición: {str(e)}"

        return self._finish_action(action, start_time)

    # ═══════════════════════════════════════════════════════════
    # CONTROL DE TECLADO
    # ═══════════════════════════════════════════════════════════

    def keyboard_type(self, text: str, interval: float = 0.05) -> ComputerAction:
        """
        Escribe texto usando el teclado

        Args:
            text: Texto a escribir
            interval: Intervalo entre teclas (segundos)

        Returns:
            ComputerAction con resultado
        """
        action = ComputerAction(
            action_type=ActionType.KEYBOARD_TYPE,
            params={'text': text[:100] + '...' if len(text) > 100 else text, 'interval': interval}
        )

        if not self.config.allow_keyboard:
            action.error = "Control de teclado no permitido"
            return self._finish_action(action)

        if not self._pyautogui:
            action.error = "PyAutoGUI no disponible"
            return self._finish_action(action)

        start_time = time.time()

        try:
            self._pyautogui.typewrite(text, interval=interval)
            action.success = True
            action.result = {'typed_length': len(text)}

        except Exception as e:
            # Intentar con write si typewrite falla (para caracteres especiales)
            try:
                self._pyautogui.write(text)
                action.success = True
                action.result = {'typed_length': len(text)}
            except Exception as e2:
                action.error = f"Error escribiendo texto: {str(e2)}"
                logger.error(f"❌ {action.error}")

        return self._finish_action(action, start_time)

    def keyboard_key(self, key: str, modifiers: List[str] = None) -> ComputerAction:
        """
        Presiona una tecla o combinación de teclas

        Args:
            key: Tecla a presionar (ej: 'enter', 'tab', 'a', 'f1')
            modifiers: Lista de modificadores ['ctrl', 'alt', 'shift', 'win']

        Returns:
            ComputerAction con resultado
        """
        action = ComputerAction(
            action_type=ActionType.KEYBOARD_KEY,
            params={'key': key, 'modifiers': modifiers or []}
        )

        if not self.config.allow_keyboard:
            action.error = "Control de teclado no permitido"
            return self._finish_action(action)

        if not self._pyautogui:
            action.error = "PyAutoGUI no disponible"
            return self._finish_action(action)

        start_time = time.time()

        try:
            if modifiers:
                # Combinación de teclas (ej: Ctrl+C)
                keys = modifiers + [key]
                self._pyautogui.hotkey(*keys)
            else:
                # Tecla simple
                self._pyautogui.press(key)

            action.success = True
            action.result = {'key_pressed': key, 'modifiers': modifiers or []}

        except Exception as e:
            action.error = f"Error presionando tecla: {str(e)}"
            logger.error(f"❌ {action.error}")

        return self._finish_action(action, start_time)

    # ═══════════════════════════════════════════════════════════
    # OPERACIONES CON ARCHIVOS
    # ═══════════════════════════════════════════════════════════

    def file_read(self, path: str, encoding: str = 'utf-8') -> ComputerAction:
        """
        Lee el contenido de un archivo

        Args:
            path: Ruta del archivo
            encoding: Codificación del archivo

        Returns:
            ComputerAction con contenido del archivo
        """
        action = ComputerAction(
            action_type=ActionType.FILE_READ,
            params={'path': path, 'encoding': encoding}
        )

        if not self.config.allow_file_ops:
            action.error = "Operaciones de archivo no permitidas"
            return self._finish_action(action)

        start_time = time.time()

        try:
            file_path = Path(path)

            if not file_path.exists():
                action.error = f"Archivo no encontrado: {path}"
                return self._finish_action(action, start_time)

            # Verificar tamaño (máximo 10MB)
            if file_path.stat().st_size > 10 * 1024 * 1024:
                action.error = "Archivo demasiado grande (máximo 10MB)"
                return self._finish_action(action, start_time)

            # Leer archivo
            content = file_path.read_text(encoding=encoding)

            action.success = True
            action.result = {
                'content': content,
                'path': str(file_path.absolute()),
                'size': len(content),
                'lines': content.count('\n') + 1
            }

        except Exception as e:
            action.error = f"Error leyendo archivo: {str(e)}"
            logger.error(f"❌ {action.error}")

        return self._finish_action(action, start_time)

    def file_write(self, path: str, content: str, encoding: str = 'utf-8') -> ComputerAction:
        """
        Escribe contenido a un archivo

        Args:
            path: Ruta del archivo
            content: Contenido a escribir
            encoding: Codificación del archivo

        Returns:
            ComputerAction con resultado
        """
        action = ComputerAction(
            action_type=ActionType.FILE_WRITE,
            params={'path': path, 'size': len(content)}
        )

        if not self.config.allow_file_ops:
            action.error = "Operaciones de archivo no permitidas"
            return self._finish_action(action)

        start_time = time.time()

        try:
            file_path = Path(path)

            # Crear directorio si no existe
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Escribir archivo
            file_path.write_text(content, encoding=encoding)

            action.success = True
            action.result = {
                'path': str(file_path.absolute()),
                'size': len(content),
                'lines': content.count('\n') + 1
            }

        except Exception as e:
            action.error = f"Error escribiendo archivo: {str(e)}"
            logger.error(f"❌ {action.error}")

        return self._finish_action(action, start_time)

    def file_list(self, directory: str, pattern: str = '*') -> ComputerAction:
        """
        Lista archivos en un directorio

        Args:
            directory: Ruta del directorio
            pattern: Patrón glob para filtrar archivos

        Returns:
            ComputerAction con lista de archivos
        """
        action = ComputerAction(
            action_type=ActionType.FILE_LIST,
            params={'directory': directory, 'pattern': pattern}
        )

        if not self.config.allow_file_ops:
            action.error = "Operaciones de archivo no permitidas"
            return self._finish_action(action)

        start_time = time.time()

        try:
            dir_path = Path(directory)

            if not dir_path.exists():
                action.error = f"Directorio no encontrado: {directory}"
                return self._finish_action(action, start_time)

            if not dir_path.is_dir():
                action.error = f"No es un directorio: {directory}"
                return self._finish_action(action, start_time)

            # Listar archivos
            files = []
            for f in dir_path.glob(pattern):
                stat = f.stat()
                files.append({
                    'name': f.name,
                    'path': str(f.absolute()),
                    'is_dir': f.is_dir(),
                    'size': stat.st_size if f.is_file() else 0,
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                })

            action.success = True
            action.result = {
                'directory': str(dir_path.absolute()),
                'pattern': pattern,
                'files': files,
                'total': len(files)
            }

        except Exception as e:
            action.error = f"Error listando directorio: {str(e)}"
            logger.error(f"❌ {action.error}")

        return self._finish_action(action, start_time)

    # ═══════════════════════════════════════════════════════════
    # LANZAMIENTO DE APLICACIONES
    # ═══════════════════════════════════════════════════════════

    def app_launch(self, app_path: str, args: List[str] = None) -> ComputerAction:
        """
        Lanza una aplicación

        Args:
            app_path: Ruta o nombre de la aplicación
            args: Argumentos para la aplicación

        Returns:
            ComputerAction con resultado
        """
        action = ComputerAction(
            action_type=ActionType.APP_LAUNCH,
            params={'app_path': app_path, 'args': args or []}
        )

        if not self.config.allow_app_launch:
            action.error = "Lanzamiento de aplicaciones no permitido"
            return self._finish_action(action)

        start_time = time.time()

        try:
            cmd = [app_path] + (args or [])

            # Lanzar en segundo plano
            if self.platform == 'windows':
                process = subprocess.Popen(
                    cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
            else:
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    start_new_session=True
                )

            action.success = True
            action.result = {
                'app': app_path,
                'pid': process.pid,
                'args': args or []
            }

        except Exception as e:
            action.error = f"Error lanzando aplicación: {str(e)}"
            logger.error(f"❌ {action.error}")

        return self._finish_action(action, start_time)

    # ═══════════════════════════════════════════════════════════
    # UTILIDADES
    # ═══════════════════════════════════════════════════════════

    def _finish_action(self, action: ComputerAction, start_time: float = None) -> ComputerAction:
        """Finaliza una acción y la registra en el historial"""
        if start_time:
            action.duration_ms = (time.time() - start_time) * 1000

        self.history.append(action)

        # Mantener solo las últimas 100 acciones
        if len(self.history) > 100:
            self.history = self.history[-100:]

        if action.success:
            logger.info(f"✅ {action.action_type.value} completado en {action.duration_ms:.0f}ms")
        else:
            logger.warning(f"⚠️ {action.action_type.value} falló: {action.error}")

        return action

    def get_screen_info(self) -> ScreenInfo:
        """Obtiene información de la pantalla"""
        return self._screen_info

    def get_history(self, limit: int = 10) -> List[ComputerAction]:
        """Obtiene el historial de acciones recientes"""
        return self.history[-limit:]

    def is_available(self) -> Dict[str, bool]:
        """Verifica qué capacidades están disponibles"""
        return {
            'enabled': self.config.enabled,
            'screenshot': self._pil is not None or self._pyautogui is not None,
            'mouse': self._pyautogui is not None and self.config.allow_mouse,
            'keyboard': self._pyautogui is not None and self.config.allow_keyboard,
            'file_operations': self.config.allow_file_ops,
            'app_launch': self.config.allow_app_launch
        }


# ═══════════════════════════════════════════════════════════════
# FUNCIONES DE CONVENIENCIA
# ═══════════════════════════════════════════════════════════════

_computer_tools: Optional[ComputerUseTools] = None


def get_computer_tools() -> ComputerUseTools:
    """Obtiene la instancia global de ComputerUseTools"""
    global _computer_tools
    if _computer_tools is None:
        _computer_tools = ComputerUseTools()
    return _computer_tools


def take_screenshot(region: Optional[Tuple[int, int, int, int]] = None) -> Dict:
    """Toma una captura de pantalla"""
    tools = get_computer_tools()
    action = tools.screenshot(region)
    if action.success:
        return action.result
    raise Exception(action.error)


def click(x: int, y: int, button: str = "left") -> bool:
    """Realiza un click"""
    tools = get_computer_tools()
    action = tools.mouse_click(x, y, button)
    return action.success


def type_text(text: str) -> bool:
    """Escribe texto"""
    tools = get_computer_tools()
    action = tools.keyboard_type(text)
    return action.success


def press_key(key: str, modifiers: List[str] = None) -> bool:
    """Presiona una tecla"""
    tools = get_computer_tools()
    action = tools.keyboard_key(key, modifiers)
    return action.success


# ═══════════════════════════════════════════════════════════════
# PUNTO DE ENTRADA PARA PRUEBAS
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║  🖥️ MÓDULO DE COMPUTER USE - SAC VISION 3.0                         ║
║  Prueba de capacidades                                                ║
╚══════════════════════════════════════════════════════════════════════╝
    """)

    # Inicializar herramientas
    tools = ComputerUseTools()

    # Mostrar capacidades disponibles
    print("📋 Capacidades disponibles:")
    caps = tools.is_available()
    for cap, available in caps.items():
        status = "✅" if available else "❌"
        print(f"  {status} {cap}")

    # Mostrar información de pantalla
    print(f"\n📐 Pantalla: {tools.get_screen_info().width}x{tools.get_screen_info().height}")

    # Tomar captura de pantalla
    print("\n📸 Tomando captura de pantalla...")
    screenshot_action = tools.screenshot()
    if screenshot_action.success:
        print(f"  ✅ Captura exitosa: {screenshot_action.result['width']}x{screenshot_action.result['height']}")
    else:
        print(f"  ❌ Error: {screenshot_action.error}")

    print("\n✅ Prueba completada")
