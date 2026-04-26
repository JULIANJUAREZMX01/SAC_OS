"""
═══════════════════════════════════════════════════════════════
MÓDULO DE NOTIFICACIONES TELEGRAM
Sistema de Automatización de Consultas - Chedraui CEDIS
═══════════════════════════════════════════════════════════════

Este módulo gestiona el envío de notificaciones instantáneas vía Telegram:
- Alertas críticas en tiempo real
- Resumen de reportes diarios
- Notificaciones de estado del sistema
- Envío de archivos y documentos

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
═══════════════════════════════════════════════════════════════
"""

import requests
import logging
import time
from datetime import datetime
from typing import List, Dict, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
from threading import Lock
import pandas as pd
from pathlib import Path

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# RATE LIMITER
# ═══════════════════════════════════════════════════════════════

class RateLimiter:
    """
    Rate limiter para respetar límites de Telegram API.

    Telegram tiene límites de:
    - 30 mensajes por segundo a diferentes chats
    - 1 mensaje por segundo al mismo chat
    - 20 mensajes por minuto al mismo grupo
    """

    def __init__(self, max_requests: int = 25, window_seconds: float = 1.0):
        """
        Inicializa el rate limiter.

        Args:
            max_requests: Máximo de requests permitidos en la ventana
            window_seconds: Tamaño de la ventana en segundos
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: deque = deque()
        self.lock = Lock()
        self._last_request_time: Dict[str, float] = {}  # Por chat_id
        self.min_interval_per_chat = 1.0  # 1 segundo mínimo entre mensajes al mismo chat

    def acquire(self, chat_id: str = None) -> bool:
        """
        Adquiere permiso para enviar un request.
        Espera si es necesario para respetar los límites.

        Args:
            chat_id: ID del chat destino (para límite por chat)

        Returns:
            True si se puede proceder
        """
        with self.lock:
            now = time.time()

            # Limpiar requests antiguos fuera de la ventana
            while self.requests and self.requests[0] < now - self.window_seconds:
                self.requests.popleft()

            # Verificar límite global
            if len(self.requests) >= self.max_requests:
                wait_time = self.requests[0] + self.window_seconds - now
                if wait_time > 0:
                    logger.debug(f"Rate limit global: esperando {wait_time:.2f}s")
                    time.sleep(wait_time)
                    now = time.time()
                    # Limpiar de nuevo después de esperar
                    while self.requests and self.requests[0] < now - self.window_seconds:
                        self.requests.popleft()

            # Verificar límite por chat
            if chat_id and chat_id in self._last_request_time:
                elapsed = now - self._last_request_time[chat_id]
                if elapsed < self.min_interval_per_chat:
                    wait_time = self.min_interval_per_chat - elapsed
                    logger.debug(f"Rate limit por chat {chat_id}: esperando {wait_time:.2f}s")
                    time.sleep(wait_time)
                    now = time.time()

            # Registrar este request
            self.requests.append(now)
            if chat_id:
                self._last_request_time[chat_id] = now

            return True

    def get_stats(self) -> Dict:
        """Retorna estadísticas del rate limiter"""
        with self.lock:
            now = time.time()
            active_requests = sum(1 for r in self.requests if r > now - self.window_seconds)
            return {
                'active_requests': active_requests,
                'max_requests': self.max_requests,
                'window_seconds': self.window_seconds,
                'usage_percent': (active_requests / self.max_requests) * 100
            }


# ═══════════════════════════════════════════════════════════════
# ENUMERACIONES Y DATACLASSES
# ═══════════════════════════════════════════════════════════════

class TipoAlerta(Enum):
    """Tipos de alertas para Telegram"""
    CRITICO = "🔴 CRÍTICO"
    ALTO = "🟠 ALTO"
    MEDIO = "🟡 MEDIO"
    BAJO = "🟢 BAJO"
    INFO = "ℹ️ INFO"
    EXITO = "✅ ÉXITO"


@dataclass
class MensajeTelegram:
    """Estructura para mensajes de Telegram"""
    texto: str
    tipo: TipoAlerta
    timestamp: datetime
    modulo: str
    datos_adicionales: Optional[Dict] = None


# ═══════════════════════════════════════════════════════════════
# CLASE PRINCIPAL
# ═══════════════════════════════════════════════════════════════

class NotificadorTelegram:
    """
    Gestor de notificaciones Telegram para el sistema SAC

    Permite enviar alertas instantáneas, reportes y documentos
    al equipo de Planning a través de Telegram Bot API.

    Uso:
        from .notificaciones_telegram import NotificadorTelegram

        notificador = NotificadorTelegram(config)
        notificador.enviar_alerta_critica("Error en OC123456", "Distribución excede cantidad")
    """

    # URL base de la API de Telegram
    BASE_URL = "https://api.telegram.org/bot{token}/{method}"

    def __init__(self, config: Dict):
        """
        Inicializa el notificador de Telegram

        Args:
            config: Diccionario con configuración del bot
                {
                    'bot_token': 'tu_bot_token',
                    'chat_ids': ['123456789', '-100123456789'],  # usuarios y grupos
                    'enabled': True,
                    'cedis_name': 'CEDIS Cancún 427'
                }
        """
        self.bot_token = config.get('bot_token', '')
        self.chat_ids = config.get('chat_ids', [])
        self.enabled = config.get('enabled', True)
        self.cedis_name = config.get('cedis_name', 'CEDIS 427')

        # Rate limiter para respetar límites de Telegram API
        self.rate_limiter = RateLimiter(
            max_requests=config.get('rate_limit_requests', 25),
            window_seconds=config.get('rate_limit_window', 1.0)
        )

        # Estadísticas de envío
        self.stats = {
            'mensajes_enviados': 0,
            'mensajes_fallidos': 0,
            'ultimo_envio': None
        }

        # Validar configuración
        self._validar_configuracion()

    def _validar_configuracion(self) -> bool:
        """Valida que la configuración sea correcta"""
        if not self.bot_token:
            logger.warning("⚠️ TELEGRAM_BOT_TOKEN no configurado")
            self.enabled = False
            return False

        if not self.chat_ids:
            logger.warning("⚠️ TELEGRAM_CHAT_IDS no configurado")
            self.enabled = False
            return False

        return True

    def _construir_url(self, method: str) -> str:
        """Construye la URL de la API de Telegram"""
        return self.BASE_URL.format(token=self.bot_token, method=method)

    def _enviar_request(self, method: str, data: Dict, files: Dict = None, chat_id: str = None) -> Dict:
        """
        Envía una solicitud a la API de Telegram con rate limiting.

        Args:
            method: Método de la API (sendMessage, sendDocument, etc.)
            data: Datos a enviar
            files: Archivos a adjuntar (opcional)
            chat_id: ID del chat destino para rate limiting

        Returns:
            Respuesta de la API como diccionario
        """
        # Aplicar rate limiting antes de enviar
        self.rate_limiter.acquire(chat_id=chat_id)

        url = self._construir_url(method)

        try:
            if files:
                response = requests.post(url, data=data, files=files, timeout=30)
            else:
                response = requests.post(url, json=data, timeout=30)

            response.raise_for_status()
            result = response.json()

            if not result.get('ok'):
                logger.error(f"❌ Error de Telegram API: {result.get('description', 'Error desconocido')}")
                self.stats['mensajes_fallidos'] += 1
                return {'ok': False, 'error': result.get('description')}

            # Actualizar estadísticas
            self.stats['mensajes_enviados'] += 1
            self.stats['ultimo_envio'] = datetime.now()

            return result

        except requests.exceptions.Timeout:
            logger.error("❌ Timeout al conectar con Telegram API")
            self.stats['mensajes_fallidos'] += 1
            return {'ok': False, 'error': 'Timeout'}
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error de conexión con Telegram: {str(e)}")
            self.stats['mensajes_fallidos'] += 1
            return {'ok': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"❌ Error inesperado en Telegram: {str(e)}")
            self.stats['mensajes_fallidos'] += 1
            return {'ok': False, 'error': str(e)}

    # ═══════════════════════════════════════════════════════════════
    # MÉTODOS PARA ENVIAR MENSAJES
    # ═══════════════════════════════════════════════════════════════

    def enviar_mensaje(
        self,
        texto: str,
        chat_ids: List[str] = None,
        parse_mode: str = "HTML"
    ) -> Dict[str, bool]:
        """
        Envía un mensaje de texto a uno o más chats

        Args:
            texto: Texto del mensaje (soporta HTML)
            chat_ids: Lista de IDs de chat (usa los configurados si no se especifica)
            parse_mode: Modo de parseo (HTML o Markdown)

        Returns:
            Diccionario con resultados por chat_id
        """
        if not self.enabled:
            logger.warning("⚠️ Notificaciones Telegram deshabilitadas")
            return {}

        destinos = chat_ids or self.chat_ids
        resultados = {}

        for chat_id in destinos:
            data = {
                'chat_id': chat_id,
                'text': texto,
                'parse_mode': parse_mode,
                'disable_web_page_preview': True
            }

            result = self._enviar_request('sendMessage', data)
            resultados[chat_id] = result.get('ok', False)

            if result.get('ok'):
                logger.info(f"✅ Mensaje enviado a chat {chat_id}")
            else:
                logger.error(f"❌ Error enviando a chat {chat_id}: {result.get('error')}")

        return resultados

    def enviar_documento(
        self,
        archivo_path: Union[str, Path],
        caption: str = None,
        chat_ids: List[str] = None
    ) -> Dict[str, bool]:
        """
        Envía un documento (archivo) a uno o más chats

        Args:
            archivo_path: Ruta al archivo a enviar
            caption: Texto descriptivo del archivo
            chat_ids: Lista de IDs de chat

        Returns:
            Diccionario con resultados por chat_id
        """
        if not self.enabled:
            logger.warning("⚠️ Notificaciones Telegram deshabilitadas")
            return {}

        archivo_path = Path(archivo_path)
        if not archivo_path.exists():
            logger.error(f"❌ Archivo no encontrado: {archivo_path}")
            return {}

        destinos = chat_ids or self.chat_ids
        resultados = {}

        for chat_id in destinos:
            try:
                with open(archivo_path, 'rb') as f:
                    files = {'document': (archivo_path.name, f)}
                    data = {
                        'chat_id': chat_id,
                        'caption': caption or f"📄 {archivo_path.name}"
                    }

                    result = self._enviar_request('sendDocument', data, files)
                    resultados[chat_id] = result.get('ok', False)

                    if result.get('ok'):
                        logger.info(f"✅ Documento enviado a chat {chat_id}: {archivo_path.name}")
                    else:
                        logger.error(f"❌ Error enviando documento a {chat_id}")

            except Exception as e:
                logger.error(f"❌ Error al leer archivo: {str(e)}")
                resultados[chat_id] = False

        return resultados

    # ═══════════════════════════════════════════════════════════════
    # MÉTODOS DE ALERTAS
    # ═══════════════════════════════════════════════════════════════

    def enviar_alerta_critica(
        self,
        titulo: str,
        descripcion: str,
        oc_numero: str = None,
        datos_afectados: Dict = None,
        solucion: str = None
    ) -> Dict[str, bool]:
        """
        Envía una alerta crítica que requiere atención inmediata

        Args:
            titulo: Título de la alerta
            descripcion: Descripción detallada del problema
            oc_numero: Número de OC afectada (opcional)
            datos_afectados: Datos adicionales del problema
            solucion: Solución sugerida

        Returns:
            Diccionario con resultados del envío
        """
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

        mensaje = f"""
🚨 <b>ALERTA CRÍTICA - {self.cedis_name}</b> 🚨

<b>📋 {titulo}</b>

⏰ <b>Fecha/Hora:</b> {timestamp}
"""

        if oc_numero:
            mensaje += f"📦 <b>OC:</b> {oc_numero}\n"

        mensaje += f"""
📝 <b>Descripción:</b>
{descripcion}
"""

        if datos_afectados:
            mensaje += "\n📊 <b>Datos Afectados:</b>\n"
            for key, value in datos_afectados.items():
                mensaje += f"  • {key}: {value}\n"

        if solucion:
            mensaje += f"""
💡 <b>Solución Sugerida:</b>
{solucion}
"""

        mensaje += f"""
━━━━━━━━━━━━━━━━━━━━━━━
🔔 <i>Sistema SAC - Notificación Automática</i>
"""

        logger.warning(f"🚨 Enviando alerta crítica: {titulo}")
        return self.enviar_mensaje(mensaje)

    def enviar_alerta(
        self,
        tipo: TipoAlerta,
        titulo: str,
        descripcion: str,
        modulo: str = "SISTEMA"
    ) -> Dict[str, bool]:
        """
        Envía una alerta general con el tipo especificado

        Args:
            tipo: Tipo de alerta (TipoAlerta enum)
            titulo: Título de la alerta
            descripcion: Descripción del evento
            modulo: Módulo que genera la alerta

        Returns:
            Diccionario con resultados del envío
        """
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

        mensaje = f"""
{tipo.value} <b>{titulo}</b>

🏢 <b>CEDIS:</b> {self.cedis_name}
📍 <b>Módulo:</b> {modulo}
⏰ <b>Fecha/Hora:</b> {timestamp}

📝 {descripcion}

━━━━━━━━━━━━━━━━━━━━━━━
🔔 <i>Sistema SAC</i>
"""

        logger.info(f"{tipo.value} Enviando alerta: {titulo}")
        return self.enviar_mensaje(mensaje)

    # ═══════════════════════════════════════════════════════════════
    # MÉTODOS DE REPORTES
    # ═══════════════════════════════════════════════════════════════

    def enviar_resumen_diario(
        self,
        total_oc: int,
        oc_validadas: int,
        oc_con_errores: int,
        errores_criticos: int,
        errores_altos: int,
        archivo_reporte: str = None
    ) -> Dict[str, bool]:
        """
        Envía el resumen diario de Planning

        Args:
            total_oc: Total de OC procesadas
            oc_validadas: OC validadas correctamente
            oc_con_errores: OC con errores detectados
            errores_criticos: Cantidad de errores críticos
            errores_altos: Cantidad de errores altos
            archivo_reporte: Ruta al archivo Excel del reporte (opcional)

        Returns:
            Diccionario con resultados del envío
        """
        fecha = datetime.now().strftime('%d/%m/%Y')
        hora = datetime.now().strftime('%H:%M')

        # Calcular porcentaje de éxito
        pct_exito = (oc_validadas / total_oc * 100) if total_oc > 0 else 0

        # Determinar emoji según resultado
        if pct_exito >= 95:
            estado_emoji = "🟢"
            estado_texto = "EXCELENTE"
        elif pct_exito >= 80:
            estado_emoji = "🟡"
            estado_texto = "BUENO"
        elif pct_exito >= 60:
            estado_emoji = "🟠"
            estado_texto = "REGULAR"
        else:
            estado_emoji = "🔴"
            estado_texto = "CRÍTICO"

        mensaje = f"""
📊 <b>RESUMEN DIARIO - {self.cedis_name}</b>

📅 <b>Fecha:</b> {fecha}
⏰ <b>Generado:</b> {hora}

━━━━━━━━━━━━━━━━━━━━━━━
<b>📦 ÓRDENES DE COMPRA</b>
━━━━━━━━━━━━━━━━━━━━━━━
  📋 Total procesadas: <b>{total_oc}</b>
  ✅ Validadas OK: <b>{oc_validadas}</b>
  ❌ Con errores: <b>{oc_con_errores}</b>
  📈 Tasa de éxito: <b>{pct_exito:.1f}%</b>

━━━━━━━━━━━━━━━━━━━━━━━
<b>⚠️ ERRORES DETECTADOS</b>
━━━━━━━━━━━━━━━━━━━━━━━
  🔴 Críticos: <b>{errores_criticos}</b>
  🟠 Altos: <b>{errores_altos}</b>

━━━━━━━━━━━━━━━━━━━━━━━
{estado_emoji} <b>ESTADO GENERAL: {estado_texto}</b>
━━━━━━━━━━━━━━━━━━━━━━━

🔔 <i>Sistema SAC - Reporte Automático</i>
"""

        logger.info(f"📊 Enviando resumen diario: {total_oc} OC, {pct_exito:.1f}% éxito")
        resultados = self.enviar_mensaje(mensaje)

        # Enviar archivo si se proporciona
        if archivo_reporte and Path(archivo_reporte).exists():
            self.enviar_documento(
                archivo_reporte,
                caption=f"📊 Reporte Planning {fecha} - {self.cedis_name}"
            )

        return resultados

    def enviar_resumen_errores(
        self,
        errores: List[Dict],
        titulo: str = "Resumen de Errores"
    ) -> Dict[str, bool]:
        """
        Envía un resumen de errores detectados

        Args:
            errores: Lista de diccionarios con errores
                [{'tipo': str, 'severidad': str, 'mensaje': str, 'oc': str}, ...]
            titulo: Título del resumen

        Returns:
            Diccionario con resultados del envío
        """
        if not errores:
            return self.enviar_alerta(
                TipoAlerta.EXITO,
                "Sin Errores Detectados",
                "No se encontraron errores en la validación",
                "MONITOR"
            )

        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

        # Agrupar errores por severidad
        criticos = [e for e in errores if 'CRÍTICO' in str(e.get('severidad', ''))]
        altos = [e for e in errores if 'ALTO' in str(e.get('severidad', ''))]
        otros = [e for e in errores if e not in criticos and e not in altos]

        mensaje = f"""
⚠️ <b>{titulo} - {self.cedis_name}</b>

⏰ <b>Fecha/Hora:</b> {timestamp}
📊 <b>Total Errores:</b> {len(errores)}

━━━━━━━━━━━━━━━━━━━━━━━
"""

        if criticos:
            mensaje += f"\n🔴 <b>CRÍTICOS ({len(criticos)})</b>\n"
            for err in criticos[:5]:  # Máximo 5 por categoría
                oc = err.get('oc', 'N/A')
                msg = err.get('mensaje', 'Sin descripción')[:100]
                mensaje += f"  • OC {oc}: {msg}\n"
            if len(criticos) > 5:
                mensaje += f"  ... y {len(criticos) - 5} más\n"

        if altos:
            mensaje += f"\n🟠 <b>ALTOS ({len(altos)})</b>\n"
            for err in altos[:5]:
                oc = err.get('oc', 'N/A')
                msg = err.get('mensaje', 'Sin descripción')[:100]
                mensaje += f"  • OC {oc}: {msg}\n"
            if len(altos) > 5:
                mensaje += f"  ... y {len(altos) - 5} más\n"

        if otros:
            mensaje += f"\n🟡 <b>OTROS ({len(otros)})</b>\n"
            mensaje += f"  Ver reporte completo para detalles\n"

        mensaje += f"""
━━━━━━━━━━━━━━━━━━━━━━━
💡 <i>Revisa el reporte Excel para más detalles</i>
🔔 <i>Sistema SAC</i>
"""

        logger.warning(f"⚠️ Enviando resumen de {len(errores)} errores")
        return self.enviar_mensaje(mensaje)

    # ═══════════════════════════════════════════════════════════════
    # MÉTODOS DE ESTADO DEL SISTEMA
    # ═══════════════════════════════════════════════════════════════

    def enviar_estado_sistema(
        self,
        db_conectada: bool,
        email_configurado: bool,
        ultimo_reporte: str = None,
        errores_pendientes: int = 0
    ) -> Dict[str, bool]:
        """
        Envía el estado actual del sistema

        Args:
            db_conectada: Si la conexión a DB2 está activa
            email_configurado: Si el email está configurado
            ultimo_reporte: Fecha/hora del último reporte
            errores_pendientes: Cantidad de errores pendientes

        Returns:
            Diccionario con resultados del envío
        """
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

        db_estado = "✅ Conectada" if db_conectada else "❌ Desconectada"
        email_estado = "✅ Configurado" if email_configurado else "⚠️ No configurado"

        mensaje = f"""
🖥️ <b>ESTADO DEL SISTEMA - {self.cedis_name}</b>

⏰ <b>Verificación:</b> {timestamp}

━━━━━━━━━━━━━━━━━━━━━━━
<b>🔌 CONEXIONES</b>
━━━━━━━━━━━━━━━━━━━━━━━
  💾 Base de Datos: {db_estado}
  📧 Email: {email_estado}
  📱 Telegram: ✅ Activo

━━━━━━━━━━━━━━━━━━━━━━━
<b>📊 INFORMACIÓN</b>
━━━━━━━━━━━━━━━━━━━━━━━
  📄 Último Reporte: {ultimo_reporte or 'N/A'}
  ⚠️ Errores Pendientes: {errores_pendientes}

━━━━━━━━━━━━━━━━━━━━━━━
🔔 <i>Sistema SAC - Heartbeat</i>
"""

        logger.info("🖥️ Enviando estado del sistema")
        return self.enviar_mensaje(mensaje)

    def enviar_inicio_sistema(self) -> Dict[str, bool]:
        """Notifica que el sistema ha iniciado"""
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

        mensaje = f"""
🚀 <b>SISTEMA SAC INICIADO</b>

🏢 <b>CEDIS:</b> {self.cedis_name}
⏰ <b>Inicio:</b> {timestamp}

✅ Monitoreo activo
✅ Alertas habilitadas
✅ Notificaciones Telegram activas

━━━━━━━━━━━━━━━━━━━━━━━
🔔 <i>Sistema SAC v1.0.0</i>
"""

        logger.info("🚀 Notificando inicio del sistema")
        return self.enviar_mensaje(mensaje)

    # ═══════════════════════════════════════════════════════════════
    # MÉTODOS DE VALIDACIÓN DE OC
    # ═══════════════════════════════════════════════════════════════

    def enviar_validacion_oc(
        self,
        oc_numero: str,
        es_valida: bool,
        total_oc: float,
        total_distro: float,
        diferencia: float = 0,
        errores: List[str] = None
    ) -> Dict[str, bool]:
        """
        Envía el resultado de validación de una OC

        Args:
            oc_numero: Número de la OC validada
            es_valida: Si la OC pasó la validación
            total_oc: Total de piezas en OC
            total_distro: Total de piezas distribuidas
            diferencia: Diferencia entre OC y distribución
            errores: Lista de errores encontrados

        Returns:
            Diccionario con resultados del envío
        """
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

        if es_valida:
            estado_emoji = "✅"
            estado_texto = "VALIDACIÓN EXITOSA"
        else:
            estado_emoji = "❌"
            estado_texto = "VALIDACIÓN FALLIDA"

        mensaje = f"""
{estado_emoji} <b>{estado_texto}</b>

🏢 <b>CEDIS:</b> {self.cedis_name}
📦 <b>OC:</b> {oc_numero}
⏰ <b>Validada:</b> {timestamp}

━━━━━━━━━━━━━━━━━━━━━━━
<b>📊 CANTIDADES</b>
━━━━━━━━━━━━━━━━━━━━━━━
  📋 Total OC: <b>{total_oc:,.0f}</b> pzas
  📤 Total Distro: <b>{total_distro:,.0f}</b> pzas
  📐 Diferencia: <b>{diferencia:+,.0f}</b> pzas
"""

        if errores:
            mensaje += f"""
━━━━━━━━━━━━━━━━━━━━━━━
<b>⚠️ ERRORES ({len(errores)})</b>
━━━━━━━━━━━━━━━━━━━━━━━
"""
            for err in errores[:5]:
                mensaje += f"  • {err[:80]}\n"
            if len(errores) > 5:
                mensaje += f"  ... y {len(errores) - 5} más\n"

        mensaje += f"""
━━━━━━━━━━━━━━━━━━━━━━━
🔔 <i>Sistema SAC</i>
"""

        logger.info(f"📦 Enviando validación OC {oc_numero}: {'OK' if es_valida else 'ERROR'}")
        return self.enviar_mensaje(mensaje)

    # ═══════════════════════════════════════════════════════════════
    # MÉTODOS UTILITARIOS
    # ═══════════════════════════════════════════════════════════════

    def verificar_conexion(self) -> bool:
        """
        Verifica la conexión con la API de Telegram

        Returns:
            True si la conexión es exitosa
        """
        if not self.bot_token:
            logger.error("❌ Bot token no configurado")
            return False

        try:
            url = self._construir_url('getMe')
            response = requests.get(url, timeout=10)
            result = response.json()

            if result.get('ok'):
                bot_info = result.get('result', {})
                bot_name = bot_info.get('first_name', 'Unknown')
                bot_username = bot_info.get('username', 'unknown')
                logger.info(f"✅ Conectado a Telegram Bot: @{bot_username} ({bot_name})")
                return True
            else:
                logger.error(f"❌ Error de autenticación: {result.get('description')}")
                return False

        except Exception as e:
            logger.error(f"❌ Error verificando conexión: {str(e)}")
            return False

    def obtener_actualizaciones(self, limit: int = 10) -> List[Dict]:
        """
        Obtiene las últimas actualizaciones (mensajes) recibidos

        Útil para obtener chat_ids de nuevos usuarios/grupos

        Args:
            limit: Número máximo de actualizaciones

        Returns:
            Lista de actualizaciones
        """
        if not self.bot_token:
            return []

        try:
            data = {'limit': limit, 'timeout': 0}
            result = self._enviar_request('getUpdates', data)

            if result.get('ok'):
                updates = result.get('result', [])
                logger.info(f"📬 {len(updates)} actualizaciones recibidas")
                return updates
            return []

        except Exception as e:
            logger.error(f"❌ Error obteniendo actualizaciones: {str(e)}")
            return []


# ═══════════════════════════════════════════════════════════════
# FUNCIONES DE UTILIDAD
# ═══════════════════════════════════════════════════════════════

def crear_notificador_desde_config() -> Optional[NotificadorTelegram]:
    """
    Crea un NotificadorTelegram usando la configuración del sistema

    Returns:
        NotificadorTelegram configurado o None si falla
    """
    try:
        from config import TELEGRAM_CONFIG, CEDIS

        config = {
            'bot_token': TELEGRAM_CONFIG.get('bot_token', ''),
            'chat_ids': TELEGRAM_CONFIG.get('chat_ids', []),
            'enabled': TELEGRAM_CONFIG.get('enabled', True),
            'cedis_name': f"{CEDIS['name']} {CEDIS['code']}"
        }

        return NotificadorTelegram(config)

    except ImportError:
        logger.warning("⚠️ TELEGRAM_CONFIG no encontrado en config.py")
        return None
    except Exception as e:
        logger.error(f"❌ Error creando notificador: {str(e)}")
        return None


def enviar_alerta_rapida(
    mensaje: str,
    tipo: TipoAlerta = TipoAlerta.INFO
) -> bool:
    """
    Función de conveniencia para enviar alertas rápidas

    Args:
        mensaje: Texto del mensaje
        tipo: Tipo de alerta

    Returns:
        True si se envió correctamente
    """
    notificador = crear_notificador_desde_config()
    if notificador:
        resultados = notificador.enviar_alerta(tipo, "Alerta SAC", mensaje, "SISTEMA")
        return any(resultados.values())
    return False


# ═══════════════════════════════════════════════════════════════
# EJECUCIÓN PRINCIPAL (PRUEBAS)
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Configuración de logging para pruebas
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("\n" + "="*60)
    print("📱 MÓDULO DE NOTIFICACIONES TELEGRAM")
    print("="*60)

    # Intentar crear notificador desde config
    notificador = crear_notificador_desde_config()

    if notificador:
        print("\n✅ Notificador creado desde configuración")

        # Verificar conexión
        if notificador.verificar_conexion():
            print("✅ Conexión con Telegram verificada")
        else:
            print("❌ No se pudo verificar la conexión")
    else:
        print("\n⚠️ No se encontró configuración de Telegram")
        print("\n💡 Para configurar Telegram:")
        print("   1. Crea un bot con @BotFather en Telegram")
        print("   2. Obtén el token del bot")
        print("   3. Agrega las variables en .env:")
        print("      TELEGRAM_BOT_TOKEN=tu_token")
        print("      TELEGRAM_CHAT_IDS=123456789,987654321")
        print("   4. Agrega TELEGRAM_CONFIG en config.py")

    print("\n" + "="*60)
    print("✅ Módulo cargado correctamente")
    print("="*60 + "\n")
