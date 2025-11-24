"""
═══════════════════════════════════════════════════════════════
INTEGRACIÓN CON MODELOS DE LENGUAJE (LLM)
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Módulo para integración con APIs de modelos de lenguaje
(OpenAI GPT, Anthropic Claude, etc) para análisis inteligente.

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
═══════════════════════════════════════════════════════════════
"""

import logging
import json
from typing import Optional, Dict, List, Any, Tuple
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import os

logger = logging.getLogger(__name__)


class ProveedorLLM(Enum):
    """Proveedores disponibles de LLM"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"


class ErrorLLM(Exception):
    """Excepción base para errores de LLM"""
    pass


class ErrorConexionLLM(ErrorLLM):
    """Error al conectarse con servicio LLM"""
    pass


class ErrorRateLimitLLM(ErrorLLM):
    """Error por rate limit excedido"""
    pass


@dataclass
class RespuestaLLM:
    """Respuesta de un modelo de lenguaje"""
    contenido: str
    modelo: str
    tokens_entrada: int
    tokens_salida: int
    costo_estimado: float = 0.0
    tiempo_procesamiento: float = 0.0

    def __str__(self) -> str:
        return f"{self.contenido}\n\n[{self.modelo} | {self.tokens_entrada+self.tokens_salida} tokens | ${self.costo_estimado:.4f}]"


class ClienteLLM(ABC):
    """Interfaz abstracta para clientes de LLM"""

    def __init__(self, api_key: str, modelo: str):
        self.api_key = api_key
        self.modelo = modelo
        self.tokens_entrada = 0
        self.tokens_salida = 0

    @abstractmethod
    def consultar(
        self,
        prompt: str,
        temperatura: float = 0.7,
        max_tokens: int = 2000
    ) -> RespuestaLLM:
        """Envía consulta al modelo"""
        pass

    @abstractmethod
    def consultar_con_contexto(
        self,
        prompt: str,
        contexto: List[Dict[str, str]],
        temperatura: float = 0.7,
        max_tokens: int = 2000
    ) -> RespuestaLLM:
        """Envía consulta con historial de contexto"""
        pass


class ClienteOpenAI(ClienteLLM):
    """Cliente para API de OpenAI (GPT-3.5, GPT-4)"""

    def __init__(self, api_key: str, modelo: str = "gpt-3.5-turbo"):
        super().__init__(api_key, modelo)
        self.base_url = "https://api.openai.com/v1"

        # Precios por 1K tokens (aproximado 2024)
        self.precios = {
            "gpt-3.5-turbo": {"entrada": 0.0005, "salida": 0.0015},
            "gpt-4": {"entrada": 0.03, "salida": 0.06},
            "gpt-4-turbo": {"entrada": 0.01, "salida": 0.03},
        }

        try:
            import openai
            openai.api_key = api_key
            self.cliente_openai = openai
            logger.info("✅ Cliente OpenAI inicializado")
        except ImportError:
            logger.warning("⚠️  openai no instalado. Instala: pip install openai")
            raise ErrorLLM("OpenAI no disponible. Instala: pip install openai")

    def consultar(
        self,
        prompt: str,
        temperatura: float = 0.7,
        max_tokens: int = 2000
    ) -> RespuestaLLM:
        """Consulta a OpenAI"""
        try:
            respuesta = self.cliente_openai.ChatCompletion.create(
                model=self.modelo,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperatura,
                max_tokens=max_tokens
            )

            contenido = respuesta['choices'][0]['message']['content']
            tokens_entrada = respuesta['usage']['prompt_tokens']
            tokens_salida = respuesta['usage']['completion_tokens']

            # Calcular costo
            precio = self.precios.get(self.modelo, {"entrada": 0.001, "salida": 0.002})
            costo = (tokens_entrada * precio["entrada"] + tokens_salida * precio["salida"]) / 1000

            self.tokens_entrada += tokens_entrada
            self.tokens_salida += tokens_salida

            logger.info(f"✅ Consulta OpenAI completada ({tokens_entrada+tokens_salida} tokens, ${costo:.4f})")

            return RespuestaLLM(
                contenido=contenido,
                modelo=self.modelo,
                tokens_entrada=tokens_entrada,
                tokens_salida=tokens_salida,
                costo_estimado=costo
            )

        except self.cliente_openai.error.RateLimitError as e:
            logger.error(f"❌ Rate limit OpenAI: {e}")
            raise ErrorRateLimitLLM(f"Límite de tasa excedido: {e}")

        except Exception as e:
            logger.error(f"❌ Error OpenAI: {e}")
            raise ErrorConexionLLM(f"Error en OpenAI: {e}")

    def consultar_con_contexto(
        self,
        prompt: str,
        contexto: List[Dict[str, str]],
        temperatura: float = 0.7,
        max_tokens: int = 2000
    ) -> RespuestaLLM:
        """Consulta a OpenAI con contexto de conversación"""
        try:
            # Construir mensajes con contexto
            mensajes = contexto.copy()
            mensajes.append({"role": "user", "content": prompt})

            respuesta = self.cliente_openai.ChatCompletion.create(
                model=self.modelo,
                messages=mensajes,
                temperature=temperatura,
                max_tokens=max_tokens
            )

            contenido = respuesta['choices'][0]['message']['content']
            tokens_entrada = respuesta['usage']['prompt_tokens']
            tokens_salida = respuesta['usage']['completion_tokens']

            precio = self.precios.get(self.modelo, {"entrada": 0.001, "salida": 0.002})
            costo = (tokens_entrada * precio["entrada"] + tokens_salida * precio["salida"]) / 1000

            self.tokens_entrada += tokens_entrada
            self.tokens_salida += tokens_salida

            return RespuestaLLM(
                contenido=contenido,
                modelo=self.modelo,
                tokens_entrada=tokens_entrada,
                tokens_salida=tokens_salida,
                costo_estimado=costo
            )

        except Exception as e:
            logger.error(f"❌ Error OpenAI (contexto): {e}")
            raise ErrorConexionLLM(f"Error en OpenAI: {e}")


class ClienteAnthropic(ClienteLLM):
    """Cliente para API de Anthropic (Claude)"""

    def __init__(self, api_key: str, modelo: str = "claude-3-haiku-20240307"):
        super().__init__(api_key, modelo)

        # Precios por 1M tokens (aproximado 2024)
        self.precios = {
            "claude-3-haiku-20240307": {"entrada": 0.25, "salida": 1.25},
            "claude-3-sonnet-20240229": {"entrada": 3.0, "salida": 15.0},
            "claude-3-opus-20240229": {"entrada": 15.0, "salida": 75.0},
        }

        try:
            import anthropic
            self.cliente_anthropic = anthropic.Anthropic(api_key=api_key)
            logger.info("✅ Cliente Anthropic inicializado")
        except ImportError:
            logger.warning("⚠️  anthropic no instalado. Instala: pip install anthropic")
            raise ErrorLLM("Anthropic no disponible. Instala: pip install anthropic")

    def consultar(
        self,
        prompt: str,
        temperatura: float = 0.7,
        max_tokens: int = 2000
    ) -> RespuestaLLM:
        """Consulta a Claude"""
        try:
            respuesta = self.cliente_anthropic.messages.create(
                model=self.modelo,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperatura
            )

            contenido = respuesta.content[0].text
            tokens_entrada = respuesta.usage.input_tokens
            tokens_salida = respuesta.usage.output_tokens

            # Calcular costo
            precio = self.precios.get(self.modelo, {"entrada": 1.0, "salida": 5.0})
            costo = (tokens_entrada * precio["entrada"] + tokens_salida * precio["salida"]) / 1000000

            self.tokens_entrada += tokens_entrada
            self.tokens_salida += tokens_salida

            logger.info(f"✅ Consulta Claude completada ({tokens_entrada+tokens_salida} tokens, ${costo:.6f})")

            return RespuestaLLM(
                contenido=contenido,
                modelo=self.modelo,
                tokens_entrada=tokens_entrada,
                tokens_salida=tokens_salida,
                costo_estimado=costo
            )

        except Exception as e:
            logger.error(f"❌ Error Claude: {e}")
            raise ErrorConexionLLM(f"Error en Claude: {e}")

    def consultar_con_contexto(
        self,
        prompt: str,
        contexto: List[Dict[str, str]],
        temperatura: float = 0.7,
        max_tokens: int = 2000
    ) -> RespuestaLLM:
        """Consulta a Claude con contexto"""
        try:
            mensajes = contexto.copy()
            mensajes.append({"role": "user", "content": prompt})

            respuesta = self.cliente_anthropic.messages.create(
                model=self.modelo,
                max_tokens=max_tokens,
                messages=mensajes,
                temperature=temperatura
            )

            contenido = respuesta.content[0].text
            tokens_entrada = respuesta.usage.input_tokens
            tokens_salida = respuesta.usage.output_tokens

            precio = self.precios.get(self.modelo, {"entrada": 1.0, "salida": 5.0})
            costo = (tokens_entrada * precio["entrada"] + tokens_salida * precio["salida"]) / 1000000

            self.tokens_entrada += tokens_entrada
            self.tokens_salida += tokens_salida

            return RespuestaLLM(
                contenido=contenido,
                modelo=self.modelo,
                tokens_entrada=tokens_entrada,
                tokens_salida=tokens_salida,
                costo_estimado=costo
            )

        except Exception as e:
            logger.error(f"❌ Error Claude (contexto): {e}")
            raise ErrorConexionLLM(f"Error en Claude: {e}")


class IntegradorLLM:
    """Integrador central para trabajar con LLMs"""

    def __init__(self, proveedor: ProveedorLLM = ProveedorLLM.ANTHROPIC, modelo: Optional[str] = None):
        self.proveedor = proveedor
        self.cliente = None

        if proveedor == ProveedorLLM.OPENAI:
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ErrorLLM("OPENAI_API_KEY no configurada")
            modelo = modelo or os.getenv('OPENAI_MODELO', 'gpt-3.5-turbo')
            self.cliente = ClienteOpenAI(api_key, modelo)

        elif proveedor == ProveedorLLM.ANTHROPIC:
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if not api_key:
                raise ErrorLLM("ANTHROPIC_API_KEY no configurada")
            modelo = modelo or os.getenv('ANTHROPIC_MODELO', 'claude-3-haiku-20240307')
            self.cliente = ClienteAnthropic(api_key, modelo)

        else:
            raise ErrorLLM(f"Proveedor desconocido: {proveedor}")

    def consultar_analisis(
        self,
        datos: str,
        tipo_analisis: str = "general"
    ) -> RespuestaLLM:
        """
        Consulta con análisis específico de datos

        Args:
            datos: String con datos a analizar
            tipo_analisis: Tipo de análisis (general, riesgos, oportunidades)

        Returns:
            RespuestaLLM: Respuesta del modelo
        """
        prompt = self._construir_prompt_analisis(datos, tipo_analisis)
        return self.cliente.consultar(prompt)

    def consultar_clasificacion(
        self,
        datos: str,
        categorias: List[str]
    ) -> Tuple[str, float]:
        """
        Clasifica datos en categorías

        Args:
            datos: Datos a clasificar
            categorias: Categorías posibles

        Returns:
            Tuple[str, float]: (categoría_predicha, confianza)
        """
        prompt = f"""
Clasifica los siguientes datos en una de estas categorías: {', '.join(categorias)}

Datos:
{datos}

Responde SOLO en formato JSON:
{{
    "categoria": "...",
    "confianza": 0.95,
    "razon": "..."
}}
"""
        respuesta = self.cliente.consultar(prompt, temperatura=0.1)

        try:
            json_respuesta = json.loads(respuesta.contenido)
            return json_respuesta['categoria'], json_respuesta['confianza']
        except json.JSONDecodeError:
            logger.warning(f"⚠️  No se pudo parsear respuesta JSON: {respuesta.contenido}")
            return "desconocido", 0.0

    def consultar_resumen(self, datos: str, max_palabras: int = 200) -> str:
        """
        Genera resumen de datos

        Args:
            datos: Datos a resumir
            max_palabras: Máximo de palabras en resumen

        Returns:
            str: Resumen generado
        """
        prompt = f"""
Genera un resumen conciso en máximo {max_palabras} palabras:

{datos}

Resumen:
"""
        respuesta = self.cliente.consultar(prompt, temperatura=0.5)
        return respuesta.contenido

    def consultar_recomendaciones(
        self,
        datos: str,
        contexto: str = ""
    ) -> List[str]:
        """
        Genera recomendaciones basadas en datos

        Args:
            datos: Datos para análisis
            contexto: Contexto adicional

        Returns:
            List[str]: Lista de recomendaciones
        """
        prompt = f"""
Basándote en los siguientes datos, genera 5 recomendaciones accionables:

Datos:
{datos}

{f'Contexto: {contexto}' if contexto else ''}

Responde en formato JSON:
{{
    "recomendaciones": [
        {{"prioridad": "ALTA", "recomendacion": "..."}},
        {{"prioridad": "MEDIA", "recomendacion": "..."}}
    ]
}}
"""
        respuesta = self.cliente.consultar(prompt, temperatura=0.6)

        try:
            json_respuesta = json.loads(respuesta.contenido)
            return [f"[{r['prioridad']}] {r['recomendacion']}" for r in json_respuesta.get('recomendaciones', [])]
        except json.JSONDecodeError:
            logger.warning(f"⚠️  No se pudo parsear recomendaciones: {respuesta.contenido}")
            return []

    def consultar_deteccion_anomalias(
        self,
        datos: str,
        patrones_normales: str = ""
    ) -> Dict[str, Any]:
        """
        Detecta anomalías en datos

        Args:
            datos: Datos a analizar
            patrones_normales: Descripción de patrones normales

        Returns:
            Dict con anomalías detectadas
        """
        prompt = f"""
Analiza los siguientes datos y detecta anomalías:

Datos:
{datos}

{f'Patrones Normales: {patrones_normales}' if patrones_normales else ''}

Responde en JSON:
{{
    "anomalias_detectadas": [
        {{"tipo": "...", "severidad": "ALTA/MEDIA/BAJA", "descripcion": "..."}}
    ],
    "es_normal": true/false,
    "confianza": 0.95
}}
"""
        respuesta = self.cliente.consultar(prompt, temperatura=0.3)

        try:
            return json.loads(respuesta.contenido)
        except json.JSONDecodeError:
            logger.warning(f"⚠️  No se pudo parsear anomalías: {respuesta.contenido}")
            return {"anomalias_detectadas": [], "es_normal": True, "confianza": 0.5}

    @staticmethod
    def _construir_prompt_analisis(datos: str, tipo_analisis: str) -> str:
        """Construye prompt para análisis específico"""
        prompts = {
            "general": f"""
Analiza los siguientes datos de OC/Distribución y proporciona un análisis detallado:

{datos}

Incluye:
1. Resumen ejecutivo
2. Principales hallazgos
3. Riesgos identificados
4. Oportunidades
5. Recomendaciones
""",
            "riesgos": f"""
Identifica todos los riesgos potenciales en estos datos:

{datos}

Para cada riesgo, proporciona:
- Descripción
- Severidad (CRÍTICA, ALTA, MEDIA, BAJA)
- Probabilidad de ocurrencia
- Impacto potencial
- Mitigación recomendada
""",
            "oportunidades": f"""
Identifica oportunidades de mejora en estos datos:

{datos}

Para cada oportunidad:
- Descripción
- Beneficio esperado
- Esfuerzo estimado
- Impacto potencial
""",
        }

        return prompts.get(tipo_analisis, prompts["general"])

    def obtener_estadisticas(self) -> Dict[str, Any]:
        """Obtiene estadísticas de uso"""
        return {
            "proveedor": self.proveedor.value,
            "modelo": self.cliente.modelo,
            "tokens_entrada": self.cliente.tokens_entrada,
            "tokens_salida": self.cliente.tokens_salida,
            "total_tokens": self.cliente.tokens_entrada + self.cliente.tokens_salida,
        }
