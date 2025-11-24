"""
═══════════════════════════════════════════════════════════════
ASISTENTE CONVERSACIONAL INTELIGENTE
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Módulo para interacción conversacional natural con el sistema
usando modelos de lenguaje para responder preguntas y guiar
a los usuarios.

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
═══════════════════════════════════════════════════════════════
"""

import logging
from typing import Optional, List, Dict, Tuple
from datetime import datetime
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class Conversacion:
    """Registro de una conversación"""
    id_conversacion: str
    usuario: str
    timestamp_inicio: datetime
    mensajes: List[Dict[str, str]] = field(default_factory=list)
    contexto: Dict = field(default_factory=dict)

    def agregar_mensaje(self, rol: str, contenido: str):
        """Agrega un mensaje a la conversación"""
        self.mensajes.append({"role": rol, "content": contenido})

    def obtener_contexto_chat(self) -> List[Dict[str, str]]:
        """Obtiene contexto para enviar a LLM"""
        return self.mensajes.copy()


class PromptTemplate:
    """Templates de prompts para diferentes contextos"""

    SISTEMA_BASE = """Eres un asistente inteligente para el Sistema SAC (Sistema de Automatización de Consultas)
de Chedraui CEDIS Cancún 427. Tu objetivo es ayudar analistas de planning a:

1. Validar Órdenes de Compra (OC)
2. Analizar distribuciones
3. Detectar problemas y anomalías
4. Generar reportes
5. Tomar decisiones basadas en datos

Mantén un tono profesional, preciso y amable. Proporciona respuestas claras y accionables.
Si necesitas información específica del usuario, solicítala de forma clara."""

    CONTEXTO_OC = """
Contexto actual - Orden de Compra:
- OC Número: {oc_numero}
- Cantidad Total: {cantidad_total:,.0f}
- Vigencia: {vigencia}
- Estado: {estado}
- Total de Tiendas: {num_tiendas}
"""

    CONTEXTO_DISTRIBUCION = """
Contexto actual - Distribuciones:
- OC Asociada: {oc_numero}
- Total de Tiendas: {total_tiendas}
- Cantidad Distribuida: {cantidad_total:,.0f}
- Equitativa: {'Sí' if {equitativa} else 'No'}
"""

    PREGUNTAS_FRECUENTES = {
        "validar oc": "¿Qué número de OC deseas validar?",
        "analizar distribucion": "¿Cuál es el número de OC para la distribución que quieres analizar?",
        "reporte": "¿Qué tipo de reporte necesitas? (diario, semanal, por OC)",
        "anomalias": "¿Deseas revisar anomalías en una OC específica o en todas?",
        "ayuda": "Puedo ayudarte con:\n1. Validación de OC\n2. Análisis de distribuciones\n3. Generación de reportes\n4. Detección de anomalías\n¿En cuál necesitas ayuda?",
    }


class AsistenteConversacional:
    """Asistente conversacional inteligente"""

    def __init__(self, cliente_llm, usuario: str = "Usuario"):
        """
        Inicializa el asistente

        Args:
            cliente_llm: Cliente LLM (IntegradorLLM)
            usuario: Nombre del usuario
        """
        self.cliente_llm = cliente_llm
        self.usuario = usuario
        self.conversacion = None
        self.contexto_actual = {}
        self.historial_conversaciones = []

        if self.cliente_llm:
            logger.info(f"✅ Asistente conversacional inicializado para {usuario}")
        else:
            logger.warning("⚠️  Asistente sin LLM configurado")

    def iniciar_conversacion(self, conversacion_id: Optional[str] = None) -> str:
        """
        Inicia una nueva conversación

        Args:
            conversacion_id: ID opcional de conversación

        Returns:
            str: ID de la conversación
        """
        if not conversacion_id:
            from datetime import datetime
            conversacion_id = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        self.conversacion = Conversacion(
            id_conversacion=conversacion_id,
            usuario=self.usuario,
            timestamp_inicio=datetime.now()
        )

        # Agregar mensaje de sistema
        self.conversacion.agregar_mensaje(
            "system",
            PromptTemplate.SISTEMA_BASE
        )

        logger.info(f"✅ Conversación iniciada: {conversacion_id}")
        return conversacion_id

    def chat(self, mensaje_usuario: str) -> str:
        """
        Procesa un mensaje del usuario y genera respuesta

        Args:
            mensaje_usuario: Mensaje del usuario

        Returns:
            str: Respuesta del asistente
        """
        if not self.conversacion:
            self.iniciar_conversacion()

        if not self.cliente_llm:
            return self._respuesta_por_defecto(mensaje_usuario)

        # Agregar mensaje del usuario
        self.conversacion.agregar_mensaje("user", mensaje_usuario)

        try:
            # Enriquecer prompt con contexto
            prompt_enriquecido = self._enriquecer_prompt(mensaje_usuario)

            # Obtener respuesta del LLM
            respuesta = self.cliente_llm.cliente.consultar_con_contexto(
                prompt=prompt_enriquecido,
                contexto=self.conversacion.obtener_contexto_chat()[:-1],  # Excluir el último mensaje ya agregado
                temperatura=0.7,
                max_tokens=1500
            )

            contenido_respuesta = respuesta.contenido

            # Agregar respuesta a la conversación
            self.conversacion.agregar_mensaje("assistant", contenido_respuesta)

            # Extraer acciones del contexto si es necesario
            self._procesar_intenciones(mensaje_usuario, contenido_respuesta)

            logger.info(f"✅ Respuesta generada ({respuesta.tokens_salida} tokens)")

            return contenido_respuesta

        except Exception as e:
            logger.error(f"❌ Error en chat: {e}")
            return self._respuesta_por_defecto(mensaje_usuario)

    def establecer_contexto(self, contexto_tipo: str, datos: Dict):
        """
        Establece contexto para la conversación

        Args:
            contexto_tipo: Tipo de contexto (oc, distribucion, etc)
            datos: Datos del contexto
        """
        self.contexto_actual = {
            "tipo": contexto_tipo,
            "datos": datos,
            "timestamp": datetime.now()
        }

        if contexto_tipo == "oc":
            self.conversacion.contexto = {
                "oc_numero": datos.get('oc_numero'),
                "cantidad_total": datos.get('cantidad_total'),
                "vigencia": datos.get('vigencia'),
                "estado": datos.get('estado'),
                "num_tiendas": datos.get('num_tiendas', 0)
            }

        logger.info(f"📍 Contexto establecido: {contexto_tipo}")

    def solicitar_analisis(self, tipo_analisis: str) -> str:
        """
        Solicita análisis específico

        Args:
            tipo_analisis: Tipo de análisis (riesgos, oportunidades, etc)

        Returns:
            str: Análisis generado
        """
        if not self.conversacion:
            return "❌ No hay conversación activa"

        mensaje = f"Por favor, realiza un análisis de {tipo_analisis} basado en el contexto actual."
        return self.chat(mensaje)

    def generar_reporte_conversacional(self, datos_oc: Dict) -> str:
        """
        Genera reporte basado en conversación

        Args:
            datos_oc: Datos de OC

        Returns:
            str: Reporte conversacional
        """
        self.establecer_contexto("oc", datos_oc)

        prompt = f"""
Basándote en la información de la OC {datos_oc.get('oc_numero')},
genera un reporte ejecutivo que incluya:

1. Resumen de la OC
2. Principales hallazgos
3. Riesgos identificados
4. Oportunidades de mejora
5. Recomendaciones de acciones

Mantén el reporte conciso pero completo.
"""

        return self.chat(prompt)

    def responder_pregunta_naturalista(self, pregunta: str) -> str:
        """
        Responde preguntas en lenguaje natural

        Args:
            pregunta: Pregunta del usuario

        Returns:
            str: Respuesta
        """
        return self.chat(pregunta)

    def obtener_asistencia_paso_a_paso(self, tarea: str) -> str:
        """
        Proporciona asistencia paso a paso

        Args:
            tarea: Tarea para la cual se necesita asistencia

        Returns:
            str: Pasos y guía
        """
        prompt = f"""
Proporciona una guía paso a paso para: {tarea}

Formatea la respuesta con:
1. Requisitos previos
2. Pasos a seguir (numerados)
3. Validaciones en cada paso
4. Troubleshooting común
5. Resultado esperado
"""

        return self.chat(prompt)

    def finalizar_conversacion(self) -> Dict:
        """
        Finaliza la conversación y retorna resumen

        Returns:
            Dict: Resumen de la conversación
        """
        if not self.conversacion:
            return {}

        resumen = {
            "id_conversacion": self.conversacion.id_conversacion,
            "usuario": self.conversacion.usuario,
            "duracion": (datetime.now() - self.conversacion.timestamp_inicio).total_seconds(),
            "total_mensajes": len(self.conversacion.mensajes),
            "total_turnos": len([m for m in self.conversacion.mensajes if m['role'] == 'user']),
        }

        self.historial_conversaciones.append(self.conversacion)
        self.conversacion = None

        logger.info(f"✅ Conversación finalizada: {resumen['total_turnos']} turnos")

        return resumen

    def obtener_historial(self) -> List[Dict]:
        """Obtiene historial de mensajes"""
        if not self.conversacion:
            return []

        return [
            {
                "timestamp": self.conversacion.timestamp_inicio,
                "rol": m['role'],
                "contenido": m['content'][:100] + "..." if len(m['content']) > 100 else m['content']
            }
            for m in self.conversacion.mensajes
        ]

    # ═══════════════════════════════════════════════════════════════
    # MÉTODOS PRIVADOS
    # ═══════════════════════════════════════════════════════════════

    def _enriquecer_prompt(self, mensaje: str) -> str:
        """Enriquece el prompt con contexto"""
        prompt = mensaje

        # Agregar contexto si existe
        if self.contexto_actual:
            if self.contexto_actual['tipo'] == "oc":
                datos = self.contexto_actual['datos']
                prompt += f"\n\nContexto actual:\n"
                prompt += f"- OC: {datos.get('oc_numero')}\n"
                prompt += f"- Cantidad: {datos.get('cantidad_total'):,.0f}\n"
                prompt += f"- Tiendas: {datos.get('num_tiendas', 0)}\n"

        return prompt

    def _procesar_intenciones(self, mensaje: str, respuesta: str):
        """Procesa intenciones del usuario desde el mensaje"""
        palabras_clave = {
            "validar": "validacion",
            "analizar": "analisis",
            "reporte": "reporte",
            "riesgos": "riesgos",
            "distribucion": "distribucion"
        }

        intencion = None
        for palabra, intent in palabras_clave.items():
            if palabra.lower() in mensaje.lower():
                intencion = intent
                break

        if intencion:
            logger.debug(f"🎯 Intención detectada: {intencion}")

    def _respuesta_por_defecto(self, mensaje: str) -> str:
        """Proporciona respuesta por defecto sin LLM"""
        # Buscar palabras clave en el mensaje
        mensaje_lower = mensaje.lower()

        for palabra_clave, respuesta in PromptTemplate.PREGUNTAS_FRECUENTES.items():
            if palabra_clave in mensaje_lower:
                return respuesta

        return """ℹ️  Asistente sin LLM configurado.
Puedo ayudarte con:
- Validación de OC (ingresa: 'validar OC')
- Análisis de distribuciones (ingresa: 'analizar distribucion')
- Reportes (ingresa: 'reporte')
- Ayuda general (ingresa: 'ayuda')

¿En qué puedo ayudarte?"""

    def _extraer_parametros(self, mensaje: str) -> Dict:
        """Extrae parámetros de un mensaje"""
        parametros = {}

        # Buscar patrones comunes
        import re

        # Buscar número de OC
        match_oc = re.search(r'(C\d{6}|OC\s*[\w\d]+)', mensaje.upper())
        if match_oc:
            parametros['oc'] = match_oc.group(1)

        return parametros


class GestorConversaciones:
    """Gestor para manejar múltiples conversaciones"""

    def __init__(self, cliente_llm):
        self.cliente_llm = cliente_llm
        self.conversaciones = {}

    def crear_asistente(self, usuario: str) -> AsistenteConversacional:
        """Crea nuevo asistente para usuario"""
        asistente = AsistenteConversacional(self.cliente_llm, usuario)
        conv_id = asistente.iniciar_conversacion()
        self.conversaciones[conv_id] = asistente
        return asistente

    def obtener_asistente(self, conversacion_id: str) -> Optional[AsistenteConversacional]:
        """Obtiene asistente existente"""
        return self.conversaciones.get(conversacion_id)

    def listar_conversaciones(self) -> List[str]:
        """Lista IDs de conversaciones activas"""
        return list(self.conversaciones.keys())

    def cerrar_conversacion(self, conversacion_id: str) -> Dict:
        """Cierra una conversación"""
        asistente = self.conversaciones.get(conversacion_id)
        if asistente:
            resumen = asistente.finalizar_conversacion()
            del self.conversaciones[conversacion_id]
            return resumen
        return {}
