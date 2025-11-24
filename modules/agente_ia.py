"""
═══════════════════════════════════════════════════════════════
MÓDULO DE INTELIGENCIA ARTIFICIAL - AGENTE SAC
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Este módulo proporciona capacidades de IA al Agente SAC mediante:
- Integración con Ollama (servidor local de LLMs)
- Soporte para modelos Llama 3, Mistral, CodeLlama
- Sistema de contexto basado en el repositorio SAC
- Respuestas inteligentes sobre el sistema y soporte técnico

REPOSITORIO DE REFERENCIA:
    https://github.com/meta-llama/llama3.git

REQUISITOS:
    - Ollama instalado: https://ollama.ai/download
    - Modelo descargado: ollama pull llama3

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════
"""

import os
import json
import logging
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Generator
from dataclasses import dataclass, field
from enum import Enum
import threading
import time

# Para requests HTTP a Ollama
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# CONSTANTES
# ═══════════════════════════════════════════════════════════════

# Repositorio de referencia para Llama 3
LLAMA3_REPO = "https://github.com/meta-llama/llama3.git"

# Configuración por defecto de Ollama
DEFAULT_OLLAMA_CONFIG = {
    'base_url': 'http://localhost:11434',
    'model': 'llama3',
    'model_fallback': 'llama2',
    'timeout': 60,
    'max_tokens': 2048,
    'temperature': 0.7,
}

# System prompt del Agente SAC
SYSTEM_PROMPT_SAC = """Eres el Agente SAC ("Godí"), el asistente virtual inteligente del CEDIS Cancún 427 de Tiendas Chedraui.

IDENTIDAD:
- Fuiste creado por Julián Alexander Juárez Alvarado (ADMJAJA), Jefe de Sistemas
- Eres parte del proyecto SAC (Sistema de Automatización de Consultas)
- Tu misión es ayudar a los colaboradores del CEDIS 427

CONOCIMIENTOS:
- Sistema SAC: Validación de OC, distribuciones, reportes Excel, alertas
- Soporte técnico: Redes, impresoras, software, configuraciones
- Manhattan WMS: Base de datos DB2, queries, operaciones de almacén
- Procesos Chedraui: Planning, recibo, expedición, inventario

FILOSOFÍA:
"Las máquinas y los sistemas al servicio de los analistas"

INSTRUCCIONES:
1. Responde siempre en español, de manera profesional y concisa
2. Si no sabes algo, admítelo y sugiere contactar a Sistemas
3. Para temas críticos, recomienda escalar al equipo de sistemas
4. Usa emojis ocasionalmente para hacer las respuestas más amigables
5. Mantén respuestas breves pero completas

EQUIPO DE SISTEMAS CEDIS 427:
- Julián Alexander Juárez Alvarado (ADMJAJA) - Jefe de Sistemas
- Larry Adanael Basto Díaz - Analista de Sistemas
- Adrian Quintana Zuñiga - Analista de Sistemas
"""

# Archivos del repositorio a indexar para contexto
ARCHIVOS_CONTEXTO = [
    'CLAUDE.md',
    'README.md',
    'config.py',
    'main.py',
    'monitor.py',
    'docs/QUICK_START.md',
    'docs/FUNCIONALIDADES_COMPLETAS.md',
]


# ═══════════════════════════════════════════════════════════════
# ENUMERACIONES
# ═══════════════════════════════════════════════════════════════

class EstadoOllama(Enum):
    """Estados de conexión con Ollama"""
    CONECTADO = "conectado"
    DESCONECTADO = "desconectado"
    ERROR = "error"
    CARGANDO_MODELO = "cargando_modelo"


class TipoConsulta(Enum):
    """Tipos de consulta al modelo"""
    GENERAL = "general"
    SOPORTE = "soporte"
    SAC = "sac"
    CODIGO = "codigo"
    DOCUMENTACION = "documentacion"


# ═══════════════════════════════════════════════════════════════
# DATACLASSES
# ═══════════════════════════════════════════════════════════════

@dataclass
class RespuestaIA:
    """Respuesta del modelo de IA"""
    contenido: str
    modelo: str
    tokens_entrada: int = 0
    tokens_salida: int = 0
    tiempo_respuesta: float = 0.0
    exitosa: bool = True
    error: str = ""
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        return {
            'contenido': self.contenido,
            'modelo': self.modelo,
            'tokens_entrada': self.tokens_entrada,
            'tokens_salida': self.tokens_salida,
            'tiempo_respuesta': self.tiempo_respuesta,
            'exitosa': self.exitosa,
            'error': self.error,
            'timestamp': self.timestamp.isoformat(),
        }


@dataclass
class ContextoRepositorio:
    """Contexto del repositorio para el modelo"""
    archivos_indexados: List[str] = field(default_factory=list)
    contenido_resumido: str = ""
    total_tokens_estimados: int = 0
    fecha_indexacion: datetime = field(default_factory=datetime.now)
    hash_contenido: str = ""


@dataclass
class ConversacionIA:
    """Historial de conversación con el modelo"""
    id: str
    usuario: str
    mensajes: List[Dict] = field(default_factory=list)
    contexto: str = ""
    modelo: str = ""
    inicio: datetime = field(default_factory=datetime.now)
    tokens_usados: int = 0


# ═══════════════════════════════════════════════════════════════
# CLIENTE OLLAMA
# ═══════════════════════════════════════════════════════════════

class ClienteOllama:
    """
    Cliente para comunicación con el servidor Ollama

    Permite ejecutar modelos LLM locales como Llama 3, Mistral, etc.
    """

    def __init__(self, config: Dict = None):
        """
        Inicializa el cliente Ollama

        Args:
            config: Configuración del cliente (base_url, model, etc.)
        """
        self.config = config or DEFAULT_OLLAMA_CONFIG.copy()
        self.base_url = self.config.get('base_url', 'http://localhost:11434')
        self.modelo_actual = self.config.get('model', 'llama3')
        self.modelo_fallback = self.config.get('model_fallback', 'llama2')
        self.timeout = self.config.get('timeout', 60)
        self.max_tokens = self.config.get('max_tokens', 2048)
        self.temperature = self.config.get('temperature', 0.7)

        self.estado = EstadoOllama.DESCONECTADO
        self.modelos_disponibles: List[str] = []
        self.ultima_verificacion: Optional[datetime] = None

        # Verificar conexión inicial
        self._verificar_conexion()

    def _verificar_conexion(self) -> bool:
        """Verifica la conexión con el servidor Ollama"""
        if not REQUESTS_AVAILABLE:
            logger.error("❌ Módulo 'requests' no disponible. Instalar: pip install requests")
            self.estado = EstadoOllama.ERROR
            return False

        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )

            if response.status_code == 200:
                data = response.json()
                self.modelos_disponibles = [
                    m.get('name', '') for m in data.get('models', [])
                ]
                self.estado = EstadoOllama.CONECTADO
                self.ultima_verificacion = datetime.now()
                logger.info(f"✅ Conectado a Ollama. Modelos: {len(self.modelos_disponibles)}")
                return True
            else:
                self.estado = EstadoOllama.ERROR
                logger.warning(f"⚠️ Ollama respondió con código: {response.status_code}")
                return False

        except requests.exceptions.ConnectionError:
            self.estado = EstadoOllama.DESCONECTADO
            logger.warning("⚠️ No se pudo conectar a Ollama. ¿Está ejecutándose?")
            return False
        except Exception as e:
            self.estado = EstadoOllama.ERROR
            logger.error(f"❌ Error verificando Ollama: {e}")
            return False

    def esta_disponible(self) -> bool:
        """Verifica si Ollama está disponible"""
        return self.estado == EstadoOllama.CONECTADO

    def listar_modelos(self) -> List[str]:
        """Lista los modelos disponibles en Ollama"""
        self._verificar_conexion()
        return self.modelos_disponibles

    def modelo_disponible(self, modelo: str) -> bool:
        """Verifica si un modelo específico está disponible"""
        return modelo in self.modelos_disponibles or any(
            modelo in m for m in self.modelos_disponibles
        )

    def seleccionar_modelo(self) -> str:
        """Selecciona el mejor modelo disponible"""
        if self.modelo_disponible(self.modelo_actual):
            return self.modelo_actual
        elif self.modelo_disponible(self.modelo_fallback):
            logger.info(f"📦 Usando modelo fallback: {self.modelo_fallback}")
            return self.modelo_fallback
        elif self.modelos_disponibles:
            modelo = self.modelos_disponibles[0]
            logger.info(f"📦 Usando primer modelo disponible: {modelo}")
            return modelo
        else:
            raise RuntimeError("No hay modelos disponibles en Ollama")

    def generar(
        self,
        prompt: str,
        system_prompt: str = None,
        modelo: str = None,
        stream: bool = False,
        **kwargs
    ) -> RespuestaIA:
        """
        Genera una respuesta usando el modelo LLM

        Args:
            prompt: Texto de entrada del usuario
            system_prompt: Instrucciones del sistema
            modelo: Modelo a usar (opcional)
            stream: Si debe retornar en streaming
            **kwargs: Parámetros adicionales

        Returns:
            RespuestaIA con el contenido generado
        """
        if not self.esta_disponible():
            self._verificar_conexion()
            if not self.esta_disponible():
                return RespuestaIA(
                    contenido="",
                    modelo="",
                    exitosa=False,
                    error="Ollama no está disponible. Verifica que esté ejecutándose."
                )

        modelo = modelo or self.seleccionar_modelo()
        system_prompt = system_prompt or SYSTEM_PROMPT_SAC

        inicio = time.time()

        try:
            # Preparar payload
            payload = {
                'model': modelo,
                'prompt': prompt,
                'system': system_prompt,
                'stream': stream,
                'options': {
                    'temperature': kwargs.get('temperature', self.temperature),
                    'num_predict': kwargs.get('max_tokens', self.max_tokens),
                }
            }

            # Hacer request
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout,
                stream=stream
            )

            if response.status_code != 200:
                return RespuestaIA(
                    contenido="",
                    modelo=modelo,
                    exitosa=False,
                    error=f"Error HTTP {response.status_code}: {response.text}"
                )

            if stream:
                # Procesar streaming
                contenido = ""
                for line in response.iter_lines():
                    if line:
                        data = json.loads(line)
                        contenido += data.get('response', '')
                        if data.get('done', False):
                            break
            else:
                data = response.json()
                contenido = data.get('response', '')

            tiempo = time.time() - inicio

            return RespuestaIA(
                contenido=contenido.strip(),
                modelo=modelo,
                tiempo_respuesta=tiempo,
                exitosa=True,
            )

        except requests.exceptions.Timeout:
            return RespuestaIA(
                contenido="",
                modelo=modelo,
                exitosa=False,
                error=f"Timeout: La respuesta tardó más de {self.timeout} segundos"
            )
        except Exception as e:
            logger.error(f"❌ Error generando respuesta: {e}")
            return RespuestaIA(
                contenido="",
                modelo=modelo,
                exitosa=False,
                error=str(e)
            )

    def chat(
        self,
        mensajes: List[Dict],
        modelo: str = None,
        **kwargs
    ) -> RespuestaIA:
        """
        Genera respuesta en formato chat (con historial)

        Args:
            mensajes: Lista de mensajes [{role: 'user'/'assistant', content: '...'}]
            modelo: Modelo a usar
            **kwargs: Parámetros adicionales

        Returns:
            RespuestaIA con la respuesta
        """
        if not self.esta_disponible():
            self._verificar_conexion()
            if not self.esta_disponible():
                return RespuestaIA(
                    contenido="",
                    modelo="",
                    exitosa=False,
                    error="Ollama no está disponible"
                )

        modelo = modelo or self.seleccionar_modelo()
        inicio = time.time()

        try:
            payload = {
                'model': modelo,
                'messages': mensajes,
                'stream': False,
                'options': {
                    'temperature': kwargs.get('temperature', self.temperature),
                    'num_predict': kwargs.get('max_tokens', self.max_tokens),
                }
            }

            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.timeout
            )

            if response.status_code != 200:
                return RespuestaIA(
                    contenido="",
                    modelo=modelo,
                    exitosa=False,
                    error=f"Error HTTP {response.status_code}"
                )

            data = response.json()
            contenido = data.get('message', {}).get('content', '')
            tiempo = time.time() - inicio

            return RespuestaIA(
                contenido=contenido.strip(),
                modelo=modelo,
                tiempo_respuesta=tiempo,
                exitosa=True,
            )

        except Exception as e:
            logger.error(f"❌ Error en chat: {e}")
            return RespuestaIA(
                contenido="",
                modelo=modelo,
                exitosa=False,
                error=str(e)
            )


# ═══════════════════════════════════════════════════════════════
# GESTOR DE CONTEXTO DEL REPOSITORIO
# ═══════════════════════════════════════════════════════════════

class GestorContextoRepositorio:
    """
    Gestiona el contexto del repositorio SAC para el modelo de IA

    Indexa archivos relevantes del proyecto para proporcionar
    conocimiento específico al Agente SAC.
    """

    def __init__(self, ruta_repositorio: Path = None):
        """
        Inicializa el gestor de contexto

        Args:
            ruta_repositorio: Ruta al repositorio SAC
        """
        self.ruta_repo = ruta_repositorio or Path(__file__).parent.parent
        self.contexto: Optional[ContextoRepositorio] = None
        self.archivos_indexados: Dict[str, str] = {}

    def indexar_repositorio(self, archivos: List[str] = None) -> ContextoRepositorio:
        """
        Indexa los archivos del repositorio para contexto

        Args:
            archivos: Lista de archivos a indexar (opcional)

        Returns:
            ContextoRepositorio con el contenido indexado
        """
        archivos = archivos or ARCHIVOS_CONTEXTO
        contenido_total = []
        archivos_ok = []

        for archivo in archivos:
            ruta = self.ruta_repo / archivo
            if ruta.exists():
                try:
                    contenido = ruta.read_text(encoding='utf-8')
                    # Limitar tamaño por archivo
                    if len(contenido) > 10000:
                        contenido = contenido[:10000] + "\n...[contenido truncado]..."

                    self.archivos_indexados[archivo] = contenido
                    contenido_total.append(f"=== {archivo} ===\n{contenido}\n")
                    archivos_ok.append(archivo)
                    logger.debug(f"📄 Indexado: {archivo}")
                except Exception as e:
                    logger.warning(f"⚠️ Error indexando {archivo}: {e}")

        # Crear resumen del contexto
        resumen = "\n".join(contenido_total)

        # Calcular hash para detectar cambios
        hash_contenido = hashlib.md5(resumen.encode()).hexdigest()

        self.contexto = ContextoRepositorio(
            archivos_indexados=archivos_ok,
            contenido_resumido=resumen,
            total_tokens_estimados=len(resumen) // 4,  # Aproximación
            hash_contenido=hash_contenido,
        )

        logger.info(f"✅ Repositorio indexado: {len(archivos_ok)} archivos")
        return self.contexto

    def obtener_contexto_para_consulta(self, consulta: str, max_tokens: int = 4000) -> str:
        """
        Obtiene contexto relevante para una consulta específica

        Args:
            consulta: La pregunta del usuario
            max_tokens: Límite de tokens para el contexto

        Returns:
            Contexto relevante como string
        """
        if not self.contexto:
            self.indexar_repositorio()

        # Por ahora retornamos todo el contexto disponible
        # En el futuro se puede implementar RAG para seleccionar lo relevante
        contexto = self.contexto.contenido_resumido

        # Limitar tamaño
        if len(contexto) > max_tokens * 4:
            contexto = contexto[:max_tokens * 4]

        return contexto

    def obtener_archivo(self, nombre: str) -> Optional[str]:
        """Obtiene el contenido de un archivo indexado"""
        return self.archivos_indexados.get(nombre)


# ═══════════════════════════════════════════════════════════════
# MOTOR DE IA DEL AGENTE SAC
# ═══════════════════════════════════════════════════════════════

class MotorIAAgenteSAC:
    """
    Motor de Inteligencia Artificial para el Agente SAC

    Combina el cliente Ollama con el contexto del repositorio
    para proporcionar respuestas inteligentes y contextualizadas.
    """

    def __init__(self, config: Dict = None):
        """
        Inicializa el motor de IA

        Args:
            config: Configuración de Ollama
        """
        # Cargar configuración
        try:
            from config import OLLAMA_CONFIG
            self.config = {**OLLAMA_CONFIG, **(config or {})}
        except ImportError:
            self.config = config or DEFAULT_OLLAMA_CONFIG.copy()

        # Inicializar componentes
        self.cliente = ClienteOllama(self.config)
        self.gestor_contexto = GestorContextoRepositorio()
        self.conversaciones: Dict[str, ConversacionIA] = {}

        # System prompt personalizado
        self.system_prompt = self.config.get('system_prompt', SYSTEM_PROMPT_SAC)

        # Estado
        self.habilitado = self.config.get('enabled', True)
        self.inicializado = False

        logger.info("🧠 Motor de IA del Agente SAC inicializado")

    def inicializar(self) -> bool:
        """
        Inicializa completamente el motor de IA

        Returns:
            True si se inicializó correctamente
        """
        if not self.habilitado:
            logger.info("ℹ️ Motor de IA deshabilitado en configuración")
            return False

        # Verificar Ollama
        if not self.cliente.esta_disponible():
            logger.warning("⚠️ Ollama no disponible. Ejecutar: ollama serve")
            return False

        # Indexar repositorio
        try:
            self.gestor_contexto.indexar_repositorio()
        except Exception as e:
            logger.warning(f"⚠️ Error indexando repositorio: {e}")

        self.inicializado = True
        logger.info("✅ Motor de IA inicializado correctamente")
        return True

    def consultar(
        self,
        pregunta: str,
        usuario: str = "usuario",
        tipo: TipoConsulta = TipoConsulta.GENERAL,
        incluir_contexto: bool = True
    ) -> RespuestaIA:
        """
        Realiza una consulta al modelo de IA

        Args:
            pregunta: La pregunta del usuario
            usuario: Identificador del usuario
            tipo: Tipo de consulta
            incluir_contexto: Si debe incluir contexto del repositorio

        Returns:
            RespuestaIA con la respuesta generada
        """
        if not self.habilitado:
            return RespuestaIA(
                contenido="La IA está deshabilitada. Contacta a Sistemas para habilitarla.",
                modelo="",
                exitosa=False,
                error="IA deshabilitada"
            )

        if not self.inicializado:
            self.inicializar()

        if not self.cliente.esta_disponible():
            return RespuestaIA(
                contenido="El servicio de IA no está disponible en este momento. "
                         "Por favor, intenta más tarde o contacta a Sistemas.",
                modelo="",
                exitosa=False,
                error="Ollama no disponible"
            )

        # Construir prompt con contexto
        prompt = pregunta
        system = self.system_prompt

        if incluir_contexto and tipo in [TipoConsulta.SAC, TipoConsulta.DOCUMENTACION]:
            contexto = self.gestor_contexto.obtener_contexto_para_consulta(pregunta)
            if contexto:
                system += f"\n\nCONTEXTO DEL SISTEMA SAC:\n{contexto[:8000]}"

        # Generar respuesta
        respuesta = self.cliente.generar(
            prompt=prompt,
            system_prompt=system,
        )

        # Registrar en historial
        if respuesta.exitosa:
            self._registrar_consulta(usuario, pregunta, respuesta)

        return respuesta

    def chat(
        self,
        mensaje: str,
        usuario: str,
        conversacion_id: str = None
    ) -> Tuple[RespuestaIA, str]:
        """
        Mantiene una conversación con el usuario

        Args:
            mensaje: Mensaje del usuario
            usuario: Identificador del usuario
            conversacion_id: ID de conversación existente

        Returns:
            Tuple (RespuestaIA, conversacion_id)
        """
        # Obtener o crear conversación
        if conversacion_id and conversacion_id in self.conversaciones:
            conv = self.conversaciones[conversacion_id]
        else:
            conv_id = hashlib.md5(
                f"{usuario}{datetime.now().isoformat()}".encode()
            ).hexdigest()[:12]
            conv = ConversacionIA(
                id=conv_id,
                usuario=usuario,
                modelo=self.cliente.seleccionar_modelo() if self.cliente.esta_disponible() else "",
            )
            self.conversaciones[conv_id] = conv
            conversacion_id = conv_id

        # Agregar mensaje del sistema si es nueva conversación
        if not conv.mensajes:
            conv.mensajes.append({
                'role': 'system',
                'content': self.system_prompt
            })

        # Agregar mensaje del usuario
        conv.mensajes.append({
            'role': 'user',
            'content': mensaje
        })

        # Generar respuesta
        respuesta = self.cliente.chat(conv.mensajes)

        if respuesta.exitosa:
            conv.mensajes.append({
                'role': 'assistant',
                'content': respuesta.contenido
            })

        return respuesta, conversacion_id

    def _registrar_consulta(self, usuario: str, pregunta: str, respuesta: RespuestaIA):
        """Registra una consulta en el historial"""
        # Implementar persistencia si es necesario
        pass

    def obtener_estado(self) -> Dict:
        """Obtiene el estado actual del motor de IA"""
        return {
            'habilitado': self.habilitado,
            'inicializado': self.inicializado,
            'ollama_disponible': self.cliente.esta_disponible(),
            'ollama_estado': self.cliente.estado.value,
            'modelo_actual': self.cliente.modelo_actual,
            'modelos_disponibles': self.cliente.modelos_disponibles,
            'archivos_indexados': (
                self.gestor_contexto.contexto.archivos_indexados
                if self.gestor_contexto.contexto else []
            ),
            'conversaciones_activas': len(self.conversaciones),
        }


# ═══════════════════════════════════════════════════════════════
# FUNCIONES DE UTILIDAD
# ═══════════════════════════════════════════════════════════════

def clonar_repositorio_llama3(destino: Path = None) -> Tuple[bool, str]:
    """
    Clona el repositorio de Llama 3 de Meta

    Args:
        destino: Directorio destino (opcional)

    Returns:
        Tuple (exitoso, mensaje)
    """
    if destino is None:
        destino = Path(__file__).parent.parent / 'external' / 'llama3'

    destino.parent.mkdir(parents=True, exist_ok=True)

    if destino.exists():
        return True, f"Repositorio ya existe en: {destino}"

    try:
        resultado = subprocess.run(
            ['git', 'clone', LLAMA3_REPO, str(destino)],
            capture_output=True,
            text=True,
            timeout=300
        )

        if resultado.returncode == 0:
            logger.info(f"✅ Repositorio Llama 3 clonado en: {destino}")
            return True, f"Clonado exitosamente en: {destino}"
        else:
            return False, f"Error: {resultado.stderr}"

    except subprocess.TimeoutExpired:
        return False, "Timeout: La clonación tardó demasiado"
    except Exception as e:
        return False, f"Error: {str(e)}"


def verificar_ollama_instalado() -> Tuple[bool, str]:
    """
    Verifica si Ollama está instalado y ejecutándose

    Returns:
        Tuple (instalado, mensaje)
    """
    # Verificar si el comando existe
    try:
        resultado = subprocess.run(
            ['ollama', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        version = resultado.stdout.strip() if resultado.returncode == 0 else "desconocida"
    except FileNotFoundError:
        return False, "Ollama no está instalado. Descarga desde: https://ollama.ai/download"
    except Exception as e:
        return False, f"Error verificando Ollama: {e}"

    # Verificar si está ejecutándose
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            return True, f"Ollama {version} está instalado y ejecutándose"
        else:
            return True, f"Ollama {version} instalado pero no responde correctamente"
    except:
        return True, f"Ollama {version} instalado pero no está ejecutándose. Ejecutar: ollama serve"


def descargar_modelo(modelo: str = "llama3") -> Tuple[bool, str]:
    """
    Descarga un modelo en Ollama

    Args:
        modelo: Nombre del modelo a descargar

    Returns:
        Tuple (exitoso, mensaje)
    """
    try:
        resultado = subprocess.run(
            ['ollama', 'pull', modelo],
            capture_output=True,
            text=True,
            timeout=600  # 10 minutos
        )

        if resultado.returncode == 0:
            return True, f"Modelo {modelo} descargado correctamente"
        else:
            return False, f"Error: {resultado.stderr}"

    except subprocess.TimeoutExpired:
        return False, "Timeout: La descarga tardó demasiado"
    except FileNotFoundError:
        return False, "Ollama no está instalado"
    except Exception as e:
        return False, f"Error: {str(e)}"


# ═══════════════════════════════════════════════════════════════
# INSTANCIA GLOBAL
# ═══════════════════════════════════════════════════════════════

_motor_ia_global: Optional[MotorIAAgenteSAC] = None


def obtener_motor_ia() -> MotorIAAgenteSAC:
    """Obtiene la instancia global del motor de IA"""
    global _motor_ia_global
    if _motor_ia_global is None:
        _motor_ia_global = MotorIAAgenteSAC()
    return _motor_ia_global


def consultar_ia(pregunta: str, usuario: str = "usuario") -> RespuestaIA:
    """Función de conveniencia para consultar la IA"""
    motor = obtener_motor_ia()
    return motor.consultar(pregunta, usuario)


# ═══════════════════════════════════════════════════════════════
# PUNTO DE ENTRADA
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║      🧠 MÓDULO DE INTELIGENCIA ARTIFICIAL - AGENTE SAC               ║
║      CEDIS Cancún 427 - Tiendas Chedraui                             ║
║                                                                      ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║  Verificando estado del sistema de IA...                             ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
    """)

    # Verificar Ollama
    instalado, msg = verificar_ollama_instalado()
    print(f"\n{'✅' if instalado else '❌'} {msg}")

    if instalado:
        # Inicializar motor
        motor = obtener_motor_ia()
        estado = motor.obtener_estado()

        print(f"\n📊 Estado del Motor de IA:")
        print(f"   Habilitado: {'✅' if estado['habilitado'] else '❌'}")
        print(f"   Ollama: {estado['ollama_estado']}")
        print(f"   Modelo: {estado['modelo_actual']}")
        print(f"   Modelos disponibles: {', '.join(estado['modelos_disponibles']) or 'ninguno'}")
        print(f"   Archivos indexados: {len(estado['archivos_indexados'])}")

        # Demo
        print("\n" + "="*60)
        print("DEMO: Consulta al Agente SAC con IA")
        print("="*60)

        pregunta = "¿Qué es el sistema SAC y quién lo creó?"
        print(f"\n👤 Usuario: {pregunta}")

        respuesta = motor.consultar(pregunta, tipo=TipoConsulta.SAC)

        if respuesta.exitosa:
            print(f"\n🤖 Agente SAC:\n{respuesta.contenido}")
            print(f"\n⏱️ Tiempo: {respuesta.tiempo_respuesta:.2f}s | Modelo: {respuesta.modelo}")
        else:
            print(f"\n❌ Error: {respuesta.error}")
