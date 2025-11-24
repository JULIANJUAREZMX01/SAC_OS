"""
═══════════════════════════════════════════════════════════════
SAC AGENT CORE - MOTOR PRINCIPAL DE AGENTE
Sistema de Automatización de Consultas - CEDIS Cancún 427
SAC VISION 3.0
═══════════════════════════════════════════════════════════════

Motor principal del Agente SAC que integra:
- Claude API (Anthropic) como cerebro de IA
- Computer Use Tools para control de computadora
- Herramientas de documentos (Excel, PDF, Word)
- Sistema de archivos y aplicaciones
- Base de datos y reportes

Este módulo es el núcleo de SAC VISION 3.0, una solución integral
e inteligente para centros de distribución y logística.

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
═══════════════════════════════════════════════════════════════
"""

import os
import sys
import json
import base64
import logging
import time
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import threading
import queue

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════

@dataclass
class SACAgentConfig:
    """Configuración del Agente SAC"""
    # Anthropic
    anthropic_api_key: str = field(default_factory=lambda: os.getenv('ANTHROPIC_API_KEY', ''))
    anthropic_model: str = field(default_factory=lambda: os.getenv('ANTHROPIC_MODEL', 'claude-sonnet-4-20250514'))
    anthropic_max_tokens: int = field(default_factory=lambda: int(os.getenv('ANTHROPIC_MAX_TOKENS', '4096')))
    anthropic_timeout: int = field(default_factory=lambda: int(os.getenv('ANTHROPIC_TIMEOUT', '120')))

    # Computer Use
    computer_use_enabled: bool = field(default_factory=lambda: os.getenv('COMPUTER_USE_ENABLED', 'true').lower() == 'true')

    # Sistema
    cedis_code: str = field(default_factory=lambda: os.getenv('CEDIS_CODE', '427'))
    cedis_name: str = field(default_factory=lambda: os.getenv('CEDIS_NAME', 'CEDIS Cancún'))

    def validate(self) -> Tuple[bool, List[str]]:
        """Valida la configuración"""
        errors = []

        if not self.anthropic_api_key:
            errors.append("ANTHROPIC_API_KEY no configurada")

        return len(errors) == 0, errors


# ═══════════════════════════════════════════════════════════════
# ENUMERACIONES
# ═══════════════════════════════════════════════════════════════

class AgentState(Enum):
    """Estados del agente"""
    IDLE = "idle"
    THINKING = "thinking"
    EXECUTING = "executing"
    WAITING_INPUT = "waiting_input"
    ERROR = "error"


class ToolType(Enum):
    """Tipos de herramientas disponibles"""
    COMPUTER = "computer"
    TEXT_EDITOR = "text_editor"
    BASH = "bash"
    FILE_MANAGER = "file_manager"
    DOCUMENT = "document"


# ═══════════════════════════════════════════════════════════════
# DATACLASSES
# ═══════════════════════════════════════════════════════════════

@dataclass
class Message:
    """Mensaje en la conversación"""
    role: str  # 'user', 'assistant', 'system'
    content: Any  # string o lista de content blocks
    timestamp: datetime = field(default_factory=datetime.now)
    tool_use_id: Optional[str] = None
    tool_name: Optional[str] = None


@dataclass
class ToolResult:
    """Resultado de ejecución de herramienta"""
    tool_use_id: str
    success: bool
    output: Any
    error: Optional[str] = None
    is_error: bool = False


@dataclass
class AgentResponse:
    """Respuesta del agente"""
    content: str
    tool_calls: List[Dict] = field(default_factory=list)
    stop_reason: str = ""
    tokens_used: int = 0
    cost_estimate: float = 0.0
    duration_ms: float = 0.0


# ═══════════════════════════════════════════════════════════════
# CLASE PRINCIPAL: SAC AGENT CORE
# ═══════════════════════════════════════════════════════════════

class SACAgentCore:
    """
    Motor principal del Agente SAC - SAC VISION 3.0

    Integra Claude (Anthropic) con capacidades de:
    - Computer Use (mouse, teclado, pantalla)
    - Edición de archivos y documentos
    - Ejecución de comandos
    - Gestión de aplicaciones
    """

    # Información del agente
    VERSION = "3.0.0"
    CODENAME = "Vision"
    BUILD_DATE = "2025-11-24"

    # Información del creador
    CREATOR = {
        'nombre': 'Julián Alexander Juárez Alvarado',
        'codigo': 'ADMJAJA',
        'cargo': 'Jefe de Sistemas',
        'cedis': 'CEDIS Cancún 427',
        'organizacion': 'Tiendas Chedraui S.A. de C.V.'
    }

    def __init__(self, config: SACAgentConfig = None):
        """
        Inicializa el Agente SAC

        Args:
            config: Configuración personalizada (opcional)
        """
        self.config = config or SACAgentConfig()
        self.state = AgentState.IDLE
        self.conversation_history: List[Message] = []
        self.tool_results: List[ToolResult] = []

        # Cliente de Anthropic
        self._anthropic_client = None

        # Herramientas
        self._computer_tools = None
        self._document_tools = None

        # Sistema de prompts
        self._system_prompt = self._build_system_prompt()

        # Estadísticas
        self.stats = {
            'messages_sent': 0,
            'tokens_used': 0,
            'tools_executed': 0,
            'errors': 0,
            'session_start': datetime.now()
        }

        # Inicializar componentes
        self._init_components()

        logger.info(f"🤖 SAC Agent Core v{self.VERSION} ({self.CODENAME}) inicializado")

    def _init_components(self):
        """Inicializa los componentes del agente"""
        # Inicializar cliente Anthropic
        if self.config.anthropic_api_key:
            try:
                import anthropic
                self._anthropic_client = anthropic.Anthropic(
                    api_key=self.config.anthropic_api_key
                )
                logger.info("✅ Cliente Anthropic inicializado")
            except ImportError:
                logger.error("❌ anthropic no instalado. Instala: pip install anthropic")
            except Exception as e:
                logger.error(f"❌ Error inicializando Anthropic: {e}")
        else:
            logger.warning("⚠️ ANTHROPIC_API_KEY no configurada")

        # Inicializar Computer Use Tools
        if self.config.computer_use_enabled:
            try:
                from .computer_use import ComputerUseTools
                self._computer_tools = ComputerUseTools()
                logger.info("✅ Computer Use Tools inicializado")
            except ImportError as e:
                logger.warning(f"⚠️ Computer Use Tools no disponible: {e}")

    def _build_system_prompt(self) -> str:
        """Construye el prompt del sistema"""
        return f"""Eres el Agente SAC (Sistema de Automatización de Consultas) versión {self.VERSION},
nombre código "{self.CODENAME}".

IDENTIDAD:
- Fuiste creado por {self.CREATOR['nombre']} ({self.CREATOR['codigo']})
- {self.CREATOR['cargo']} del {self.CREATOR['cedis']}
- {self.CREATOR['organizacion']}
- Build: {self.BUILD_DATE}

UBICACIÓN:
- CEDIS: {self.config.cedis_name} (Código: {self.config.cedis_code})
- Sistema: SAC VISION 3.0

CAPACIDADES:
1. Control de Computadora (Computer Use):
   - Captura de pantalla para ver el contenido
   - Control de mouse (click, movimiento, scroll)
   - Control de teclado (escribir, teclas especiales)
   - Gestión de archivos

2. Documentos y Reportes:
   - Crear y editar archivos Excel
   - Leer y procesar PDFs
   - Editar documentos de texto
   - Generar reportes automáticos

3. Operaciones de Sistema:
   - Ejecutar comandos de terminal
   - Lanzar aplicaciones
   - Gestionar archivos y carpetas

4. Base de Datos:
   - Consultas a Manhattan WMS (DB2)
   - Validación de OC y distribuciones
   - Generación de reportes

INSTRUCCIONES:
1. Siempre responde en español de manera profesional y concisa
2. Cuando necesites ver la pantalla, toma una captura primero
3. Para operaciones complejas, describe paso a paso lo que harás
4. Si hay errores, explica qué sucedió y sugiere soluciones
5. Prioriza la seguridad - no ejecutes comandos peligrosos sin confirmación

FILOSOFÍA:
"Las máquinas y los sistemas al servicio de los analistas"

Estás listo para ayudar a los analistas de:
- Sistemas
- Recursos Humanos
- Control
- Tráfico
- Recibo
- Preparación
- Expedición"""

    # ═══════════════════════════════════════════════════════════
    # DEFINICIÓN DE HERRAMIENTAS
    # ═══════════════════════════════════════════════════════════

    def _get_tools_definition(self) -> List[Dict]:
        """Retorna la definición de herramientas para Claude"""
        tools = []

        # Computer Use Tool
        if self._computer_tools:
            tools.append({
                "type": "computer_20241022",
                "name": "computer",
                "display_width_px": self._computer_tools.get_screen_info().width,
                "display_height_px": self._computer_tools.get_screen_info().height,
                "display_number": 1
            })

        # Text Editor Tool
        tools.append({
            "type": "text_editor_20241022",
            "name": "str_replace_editor"
        })

        # Bash Tool
        tools.append({
            "type": "bash_20241022",
            "name": "bash"
        })

        return tools

    # ═══════════════════════════════════════════════════════════
    # EJECUCIÓN DE HERRAMIENTAS
    # ═══════════════════════════════════════════════════════════

    def _execute_tool(self, tool_name: str, tool_input: Dict, tool_use_id: str) -> ToolResult:
        """
        Ejecuta una herramienta y retorna el resultado

        Args:
            tool_name: Nombre de la herramienta
            tool_input: Parámetros de entrada
            tool_use_id: ID del uso de herramienta

        Returns:
            ToolResult con el resultado
        """
        self.state = AgentState.EXECUTING
        self.stats['tools_executed'] += 1

        logger.info(f"🔧 Ejecutando herramienta: {tool_name}")
        logger.debug(f"   Input: {json.dumps(tool_input, default=str)[:200]}")

        try:
            if tool_name == "computer":
                return self._execute_computer_tool(tool_input, tool_use_id)
            elif tool_name == "str_replace_editor":
                return self._execute_text_editor_tool(tool_input, tool_use_id)
            elif tool_name == "bash":
                return self._execute_bash_tool(tool_input, tool_use_id)
            else:
                return ToolResult(
                    tool_use_id=tool_use_id,
                    success=False,
                    output=None,
                    error=f"Herramienta desconocida: {tool_name}",
                    is_error=True
                )

        except Exception as e:
            logger.error(f"❌ Error ejecutando {tool_name}: {e}")
            self.stats['errors'] += 1
            return ToolResult(
                tool_use_id=tool_use_id,
                success=False,
                output=None,
                error=str(e),
                is_error=True
            )

        finally:
            self.state = AgentState.IDLE

    def _execute_computer_tool(self, tool_input: Dict, tool_use_id: str) -> ToolResult:
        """Ejecuta acciones de computer use"""
        if not self._computer_tools:
            return ToolResult(
                tool_use_id=tool_use_id,
                success=False,
                output=None,
                error="Computer Use Tools no disponible",
                is_error=True
            )

        action = tool_input.get("action")
        result_content = []

        if action == "screenshot":
            # Captura de pantalla
            screenshot = self._computer_tools.screenshot()
            if screenshot.success:
                result_content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": screenshot.result['image_base64']
                    }
                })
                return ToolResult(
                    tool_use_id=tool_use_id,
                    success=True,
                    output=result_content
                )
            else:
                return ToolResult(
                    tool_use_id=tool_use_id,
                    success=False,
                    output=None,
                    error=screenshot.error,
                    is_error=True
                )

        elif action == "mouse_move":
            # Mover mouse
            coordinate = tool_input.get("coordinate", [0, 0])
            result = self._computer_tools.mouse_move(coordinate[0], coordinate[1])
            return ToolResult(
                tool_use_id=tool_use_id,
                success=result.success,
                output=f"Mouse movido a ({coordinate[0]}, {coordinate[1]})" if result.success else None,
                error=result.error,
                is_error=not result.success
            )

        elif action in ["left_click", "click"]:
            # Click izquierdo
            coordinate = tool_input.get("coordinate")
            if coordinate:
                result = self._computer_tools.mouse_click(coordinate[0], coordinate[1], "left")
            else:
                result = self._computer_tools.mouse_click(button="left")
            return ToolResult(
                tool_use_id=tool_use_id,
                success=result.success,
                output=f"Click realizado" if result.success else None,
                error=result.error,
                is_error=not result.success
            )

        elif action == "right_click":
            # Click derecho
            coordinate = tool_input.get("coordinate")
            if coordinate:
                result = self._computer_tools.mouse_click(coordinate[0], coordinate[1], "right")
            else:
                result = self._computer_tools.mouse_click(button="right")
            return ToolResult(
                tool_use_id=tool_use_id,
                success=result.success,
                output=f"Click derecho realizado" if result.success else None,
                error=result.error,
                is_error=not result.success
            )

        elif action == "double_click":
            # Doble click
            coordinate = tool_input.get("coordinate")
            if coordinate:
                result = self._computer_tools.mouse_click(coordinate[0], coordinate[1], "left", clicks=2)
            else:
                result = self._computer_tools.mouse_click(button="left", clicks=2)
            return ToolResult(
                tool_use_id=tool_use_id,
                success=result.success,
                output=f"Doble click realizado" if result.success else None,
                error=result.error,
                is_error=not result.success
            )

        elif action == "scroll":
            # Scroll
            coordinate = tool_input.get("coordinate")
            direction = tool_input.get("direction", "down")
            amount = tool_input.get("amount", 3)
            scroll_amount = -amount if direction == "down" else amount

            if coordinate:
                result = self._computer_tools.mouse_scroll(scroll_amount, coordinate[0], coordinate[1])
            else:
                result = self._computer_tools.mouse_scroll(scroll_amount)

            return ToolResult(
                tool_use_id=tool_use_id,
                success=result.success,
                output=f"Scroll {direction} realizado" if result.success else None,
                error=result.error,
                is_error=not result.success
            )

        elif action == "type":
            # Escribir texto
            text = tool_input.get("text", "")
            result = self._computer_tools.keyboard_type(text)
            return ToolResult(
                tool_use_id=tool_use_id,
                success=result.success,
                output=f"Texto escrito: {text[:50]}..." if result.success else None,
                error=result.error,
                is_error=not result.success
            )

        elif action == "key":
            # Presionar tecla
            key = tool_input.get("key", "")
            # Mapear nombres de teclas
            key_mapping = {
                "Return": "enter",
                "BackSpace": "backspace",
                "Tab": "tab",
                "Escape": "escape",
                "space": "space",
                "Delete": "delete",
                "Home": "home",
                "End": "end",
                "Page_Up": "pageup",
                "Page_Down": "pagedown",
                "Up": "up",
                "Down": "down",
                "Left": "left",
                "Right": "right",
            }
            mapped_key = key_mapping.get(key, key.lower())

            # Verificar si hay modificadores
            modifiers = []
            if "ctrl+" in key.lower() or "control+" in key.lower():
                modifiers.append("ctrl")
                key = key.lower().replace("ctrl+", "").replace("control+", "")
            if "alt+" in key.lower():
                modifiers.append("alt")
                key = key.lower().replace("alt+", "")
            if "shift+" in key.lower():
                modifiers.append("shift")
                key = key.lower().replace("shift+", "")

            result = self._computer_tools.keyboard_key(mapped_key, modifiers if modifiers else None)
            return ToolResult(
                tool_use_id=tool_use_id,
                success=result.success,
                output=f"Tecla presionada: {key}" if result.success else None,
                error=result.error,
                is_error=not result.success
            )

        elif action == "cursor_position":
            # Obtener posición del cursor
            result = self._computer_tools.get_cursor_position()
            if result.success:
                return ToolResult(
                    tool_use_id=tool_use_id,
                    success=True,
                    output=f"Posición del cursor: ({result.result['x']}, {result.result['y']})"
                )
            return ToolResult(
                tool_use_id=tool_use_id,
                success=False,
                output=None,
                error=result.error,
                is_error=True
            )

        else:
            return ToolResult(
                tool_use_id=tool_use_id,
                success=False,
                output=None,
                error=f"Acción de computer use desconocida: {action}",
                is_error=True
            )

    def _execute_text_editor_tool(self, tool_input: Dict, tool_use_id: str) -> ToolResult:
        """Ejecuta acciones del editor de texto"""
        command = tool_input.get("command")
        path = tool_input.get("path")

        if command == "view":
            # Ver archivo
            try:
                file_path = Path(path)
                if not file_path.exists():
                    return ToolResult(
                        tool_use_id=tool_use_id,
                        success=False,
                        output=None,
                        error=f"Archivo no encontrado: {path}",
                        is_error=True
                    )

                content = file_path.read_text(encoding='utf-8')

                # Limitar contenido muy largo
                if len(content) > 100000:
                    content = content[:100000] + "\n\n[... contenido truncado ...]"

                return ToolResult(
                    tool_use_id=tool_use_id,
                    success=True,
                    output=content
                )

            except Exception as e:
                return ToolResult(
                    tool_use_id=tool_use_id,
                    success=False,
                    output=None,
                    error=str(e),
                    is_error=True
                )

        elif command == "create":
            # Crear archivo
            try:
                file_content = tool_input.get("file_text", "")
                file_path = Path(path)
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(file_content, encoding='utf-8')

                return ToolResult(
                    tool_use_id=tool_use_id,
                    success=True,
                    output=f"Archivo creado: {path}"
                )

            except Exception as e:
                return ToolResult(
                    tool_use_id=tool_use_id,
                    success=False,
                    output=None,
                    error=str(e),
                    is_error=True
                )

        elif command == "str_replace":
            # Reemplazar texto
            try:
                file_path = Path(path)
                if not file_path.exists():
                    return ToolResult(
                        tool_use_id=tool_use_id,
                        success=False,
                        output=None,
                        error=f"Archivo no encontrado: {path}",
                        is_error=True
                    )

                old_str = tool_input.get("old_str", "")
                new_str = tool_input.get("new_str", "")

                content = file_path.read_text(encoding='utf-8')

                if old_str not in content:
                    return ToolResult(
                        tool_use_id=tool_use_id,
                        success=False,
                        output=None,
                        error=f"Texto no encontrado en el archivo: {old_str[:50]}...",
                        is_error=True
                    )

                new_content = content.replace(old_str, new_str, 1)
                file_path.write_text(new_content, encoding='utf-8')

                return ToolResult(
                    tool_use_id=tool_use_id,
                    success=True,
                    output=f"Reemplazo realizado en {path}"
                )

            except Exception as e:
                return ToolResult(
                    tool_use_id=tool_use_id,
                    success=False,
                    output=None,
                    error=str(e),
                    is_error=True
                )

        elif command == "insert":
            # Insertar texto
            try:
                file_path = Path(path)
                if not file_path.exists():
                    return ToolResult(
                        tool_use_id=tool_use_id,
                        success=False,
                        output=None,
                        error=f"Archivo no encontrado: {path}",
                        is_error=True
                    )

                insert_line = tool_input.get("insert_line", 0)
                new_str = tool_input.get("new_str", "")

                lines = file_path.read_text(encoding='utf-8').split('\n')
                lines.insert(insert_line, new_str)
                file_path.write_text('\n'.join(lines), encoding='utf-8')

                return ToolResult(
                    tool_use_id=tool_use_id,
                    success=True,
                    output=f"Texto insertado en línea {insert_line}"
                )

            except Exception as e:
                return ToolResult(
                    tool_use_id=tool_use_id,
                    success=False,
                    output=None,
                    error=str(e),
                    is_error=True
                )

        else:
            return ToolResult(
                tool_use_id=tool_use_id,
                success=False,
                output=None,
                error=f"Comando de editor desconocido: {command}",
                is_error=True
            )

    def _execute_bash_tool(self, tool_input: Dict, tool_use_id: str) -> ToolResult:
        """Ejecuta comandos bash"""
        import subprocess

        command = tool_input.get("command", "")
        restart = tool_input.get("restart", False)

        if not command:
            return ToolResult(
                tool_use_id=tool_use_id,
                success=False,
                output=None,
                error="Comando vacío",
                is_error=True
            )

        # Lista de comandos peligrosos que requieren confirmación
        dangerous_commands = ['rm -rf', 'format', 'mkfs', 'dd if=', '> /dev/', 'shutdown', 'reboot']
        is_dangerous = any(dc in command.lower() for dc in dangerous_commands)

        if is_dangerous:
            logger.warning(f"⚠️ Comando potencialmente peligroso detectado: {command}")
            # En producción, aquí se solicitaría confirmación al usuario

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.config.anthropic_timeout
            )

            output = result.stdout
            if result.stderr:
                output += f"\n[stderr]: {result.stderr}"

            # Limitar output muy largo
            if len(output) > 50000:
                output = output[:50000] + "\n\n[... output truncado ...]"

            return ToolResult(
                tool_use_id=tool_use_id,
                success=result.returncode == 0,
                output=output if output else "(sin output)",
                error=result.stderr if result.returncode != 0 else None,
                is_error=result.returncode != 0
            )

        except subprocess.TimeoutExpired:
            return ToolResult(
                tool_use_id=tool_use_id,
                success=False,
                output=None,
                error=f"Timeout: El comando excedió {self.config.anthropic_timeout} segundos",
                is_error=True
            )

        except Exception as e:
            return ToolResult(
                tool_use_id=tool_use_id,
                success=False,
                output=None,
                error=str(e),
                is_error=True
            )

    # ═══════════════════════════════════════════════════════════
    # COMUNICACIÓN CON CLAUDE
    # ═══════════════════════════════════════════════════════════

    def chat(self, user_message: str, max_iterations: int = 10) -> str:
        """
        Envía un mensaje al agente y procesa la respuesta

        Args:
            user_message: Mensaje del usuario
            max_iterations: Máximo de iteraciones de herramientas

        Returns:
            Respuesta final del agente
        """
        if not self._anthropic_client:
            return "❌ Error: Cliente Anthropic no inicializado. Verifica tu ANTHROPIC_API_KEY."

        self.state = AgentState.THINKING

        # Agregar mensaje del usuario
        self.conversation_history.append(Message(role="user", content=user_message))

        try:
            iteration = 0
            final_response = ""

            while iteration < max_iterations:
                iteration += 1
                logger.info(f"🔄 Iteración {iteration}/{max_iterations}")

                # Construir mensajes para la API
                messages = self._build_api_messages()

                # Llamar a Claude
                start_time = time.time()

                response = self._anthropic_client.messages.create(
                    model=self.config.anthropic_model,
                    max_tokens=self.config.anthropic_max_tokens,
                    system=self._system_prompt,
                    tools=self._get_tools_definition(),
                    messages=messages
                )

                duration_ms = (time.time() - start_time) * 1000

                # Actualizar estadísticas
                self.stats['messages_sent'] += 1
                self.stats['tokens_used'] += response.usage.input_tokens + response.usage.output_tokens

                logger.info(f"✅ Respuesta recibida en {duration_ms:.0f}ms (tokens: {response.usage.input_tokens}+{response.usage.output_tokens})")

                # Procesar respuesta
                text_content = ""
                tool_uses = []

                for block in response.content:
                    if block.type == "text":
                        text_content += block.text
                    elif block.type == "tool_use":
                        tool_uses.append({
                            'id': block.id,
                            'name': block.name,
                            'input': block.input
                        })

                # Agregar respuesta del asistente al historial
                self.conversation_history.append(Message(
                    role="assistant",
                    content=response.content
                ))

                # Si no hay tool_uses, terminamos
                if not tool_uses or response.stop_reason == "end_turn":
                    final_response = text_content
                    break

                # Ejecutar herramientas
                tool_results = []
                for tool_use in tool_uses:
                    result = self._execute_tool(
                        tool_use['name'],
                        tool_use['input'],
                        tool_use['id']
                    )
                    tool_results.append(result)

                # Agregar resultados de herramientas al historial
                tool_result_content = []
                for result in tool_results:
                    if isinstance(result.output, list):
                        # Para screenshots, el output ya es una lista de content blocks
                        tool_result_content.append({
                            "type": "tool_result",
                            "tool_use_id": result.tool_use_id,
                            "content": result.output,
                            "is_error": result.is_error
                        })
                    else:
                        tool_result_content.append({
                            "type": "tool_result",
                            "tool_use_id": result.tool_use_id,
                            "content": str(result.output) if result.output else str(result.error),
                            "is_error": result.is_error
                        })

                self.conversation_history.append(Message(
                    role="user",
                    content=tool_result_content
                ))

            self.state = AgentState.IDLE
            return final_response

        except Exception as e:
            self.state = AgentState.ERROR
            self.stats['errors'] += 1
            logger.error(f"❌ Error en chat: {e}")
            return f"❌ Error: {str(e)}"

    def _build_api_messages(self) -> List[Dict]:
        """Construye la lista de mensajes para la API"""
        messages = []

        for msg in self.conversation_history:
            if isinstance(msg.content, str):
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            else:
                # Content blocks (tool_use, tool_result, etc.)
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })

        return messages

    # ═══════════════════════════════════════════════════════════
    # UTILIDADES
    # ═══════════════════════════════════════════════════════════

    def clear_history(self):
        """Limpia el historial de conversación"""
        self.conversation_history = []
        self.tool_results = []
        logger.info("🧹 Historial limpiado")

    def get_stats(self) -> Dict:
        """Obtiene estadísticas de la sesión"""
        return {
            **self.stats,
            'session_duration': str(datetime.now() - self.stats['session_start']),
            'conversation_length': len(self.conversation_history),
            'state': self.state.value
        }

    def get_identity(self) -> Dict:
        """Retorna la identidad del agente"""
        return {
            'name': 'SAC Agent',
            'version': self.VERSION,
            'codename': self.CODENAME,
            'build_date': self.BUILD_DATE,
            'creator': self.CREATOR,
            'cedis': {
                'code': self.config.cedis_code,
                'name': self.config.cedis_name
            }
        }

    def is_ready(self) -> Tuple[bool, str]:
        """Verifica si el agente está listo para operar"""
        if not self._anthropic_client:
            return False, "Cliente Anthropic no inicializado"

        valid, errors = self.config.validate()
        if not valid:
            return False, ", ".join(errors)

        return True, "Agente listo"


# ═══════════════════════════════════════════════════════════════
# FUNCIONES DE CONVENIENCIA
# ═══════════════════════════════════════════════════════════════

_sac_agent: Optional[SACAgentCore] = None


def get_sac_agent() -> SACAgentCore:
    """Obtiene la instancia global del agente SAC"""
    global _sac_agent
    if _sac_agent is None:
        _sac_agent = SACAgentCore()
    return _sac_agent


def chat(message: str) -> str:
    """Función rápida para chatear con el agente"""
    agent = get_sac_agent()
    return agent.chat(message)


# ═══════════════════════════════════════════════════════════════
# PUNTO DE ENTRADA PARA PRUEBAS
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print(f"""
╔══════════════════════════════════════════════════════════════════════╗
║  🤖 SAC AGENT CORE - SAC VISION 3.0                                  ║
║  Motor Principal del Agente SAC                                       ║
╠══════════════════════════════════════════════════════════════════════╣
║  Versión: {SACAgentCore.VERSION}                                              ║
║  Codename: {SACAgentCore.CODENAME}                                          ║
║  Build: {SACAgentCore.BUILD_DATE}                                          ║
║                                                                      ║
║  Creador: {SACAgentCore.CREATOR['nombre']}                  ║
║  {SACAgentCore.CREATOR['cargo']} - {SACAgentCore.CREATOR['cedis']}                ║
╚══════════════════════════════════════════════════════════════════════╝
    """)

    # Verificar estado
    agent = SACAgentCore()
    ready, message = agent.is_ready()

    if ready:
        print(f"✅ {message}")
        print(f"📊 Modelo: {agent.config.anthropic_model}")

        # Modo interactivo simple
        print("\n💬 Escribe tu mensaje (o 'salir' para terminar):\n")

        while True:
            try:
                user_input = input("[Usuario] > ").strip()

                if not user_input:
                    continue

                if user_input.lower() in ['salir', 'exit', 'quit']:
                    print("\n👋 ¡Hasta luego!")
                    break

                response = agent.chat(user_input)
                print(f"\n[SAC Agent] {response}\n")

            except KeyboardInterrupt:
                print("\n\n👋 ¡Hasta luego!")
                break
    else:
        print(f"❌ {message}")
        print("\nPara configurar el agente:")
        print("1. Copia 'env' a '.env'")
        print("2. Configura tu ANTHROPIC_API_KEY")
        print("3. Ejecuta nuevamente")
