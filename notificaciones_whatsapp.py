"""
===============================================================
MÓDULO DE NOTIFICACIONES WHATSAPP
Sistema de Automatización de Consultas - CEDIS Cancún 427
===============================================================

Envío de notificaciones y alertas vía WhatsApp usando Twilio API:
- Alertas críticas instantáneas
- Resúmenes diarios
- Notificaciones de validación
- Mensajes de estado del sistema

Configuración en .env:
    TWILIO_ACCOUNT_SID=tu_account_sid
    TWILIO_AUTH_TOKEN=tu_auth_token
    TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
    WHATSAPP_DESTINATARIOS=+521234567890,+521234567891

Uso:
    from notificaciones_whatsapp import NotificadorWhatsApp

    wa = NotificadorWhatsApp()
    wa.enviar_alerta_critica("Error en OC", "Distribución excede cantidad")

Requiere: pip install twilio

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
===============================================================
"""

import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

# Intentar importar Twilio
try:
    from twilio.rest import Client as TwilioClient
    from twilio.base.exceptions import TwilioRestException
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False

# Importar configuración
try:
    from config import CEDIS
except ImportError:
    CEDIS = {'name': 'CEDIS', 'code': '427'}

# Configurar logger
logger = logging.getLogger(__name__)


# ===============================================================
# ENUMERACIONES
# ===============================================================

class TipoMensaje(Enum):
    """Tipos de mensajes WhatsApp"""
    ALERTA_CRITICA = "alerta_critica"
    ALERTA_ALTA = "alerta_alta"
    INFORMATIVO = "informativo"
    RESUMEN_DIARIO = "resumen_diario"
    VALIDACION_OC = "validacion_oc"
    ESTADO_SISTEMA = "estado_sistema"


# ===============================================================
# DATA CLASS DE CONFIGURACIÓN
# ===============================================================

@dataclass
class ConfigWhatsApp:
    """Configuración de WhatsApp/Twilio"""
    account_sid: str = ""
    auth_token: str = ""
    whatsapp_from: str = "whatsapp:+14155238886"  # Sandbox por defecto
    destinatarios: List[str] = field(default_factory=list)
    enabled: bool = False

    @classmethod
    def from_env(cls) -> 'ConfigWhatsApp':
        """Crea configuración desde variables de entorno."""
        account_sid = os.getenv('TWILIO_ACCOUNT_SID', '')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN', '')

        # Parsear destinatarios
        dest_str = os.getenv('WHATSAPP_DESTINATARIOS', '')
        destinatarios = [d.strip() for d in dest_str.split(',') if d.strip()]

        # Agregar prefijo whatsapp: si no lo tienen
        destinatarios = [
            f"whatsapp:{d}" if not d.startswith('whatsapp:') else d
            for d in destinatarios
        ]

        return cls(
            account_sid=account_sid,
            auth_token=auth_token,
            whatsapp_from=os.getenv('TWILIO_WHATSAPP_FROM', 'whatsapp:+14155238886'),
            destinatarios=destinatarios,
            enabled=bool(account_sid and auth_token and destinatarios)
        )


# ===============================================================
# CLASE PRINCIPAL
# ===============================================================

class NotificadorWhatsApp:
    """
    Notificador de WhatsApp usando Twilio API.

    Proporciona métodos para enviar diferentes tipos de notificaciones
    vía WhatsApp Business API.

    Ejemplo:
        >>> wa = NotificadorWhatsApp()
        >>> if wa.enabled:
        ...     wa.enviar_alerta_critica("Título", "Descripción del error")
    """

    def __init__(self, config: ConfigWhatsApp = None):
        """
        Inicializa el notificador de WhatsApp.

        Args:
            config: Configuración personalizada (usa env por defecto)
        """
        self.config = config or ConfigWhatsApp.from_env()
        self.enabled = self.config.enabled and TWILIO_AVAILABLE
        self._client = None

        if self.enabled:
            try:
                self._client = TwilioClient(
                    self.config.account_sid,
                    self.config.auth_token
                )
                logger.info("📱 NotificadorWhatsApp inicializado correctamente")
            except Exception as e:
                logger.error(f"❌ Error inicializando Twilio: {e}")
                self.enabled = False
        else:
            if not TWILIO_AVAILABLE:
                logger.warning("⚠️  Twilio no instalado. Ejecuta: pip install twilio")
            elif not self.config.account_sid:
                logger.warning("⚠️  TWILIO_ACCOUNT_SID no configurado en .env")
            elif not self.config.destinatarios:
                logger.warning("⚠️  WHATSAPP_DESTINATARIOS no configurados en .env")

    def _enviar_mensaje(
        self,
        destinatario: str,
        mensaje: str,
        media_url: str = None
    ) -> bool:
        """
        Envía un mensaje WhatsApp a un destinatario.

        Args:
            destinatario: Número en formato whatsapp:+52...
            mensaje: Texto del mensaje
            media_url: URL de imagen/documento (opcional)

        Returns:
            True si se envió correctamente
        """
        if not self.enabled or not self._client:
            logger.warning("⚠️  WhatsApp no habilitado")
            return False

        try:
            params = {
                'from_': self.config.whatsapp_from,
                'to': destinatario,
                'body': mensaje
            }

            if media_url:
                params['media_url'] = [media_url]

            message = self._client.messages.create(**params)

            logger.info(f"✅ WhatsApp enviado a {destinatario}: {message.sid}")
            return True

        except TwilioRestException as e:
            logger.error(f"❌ Error Twilio: {e.msg}")
            return False
        except Exception as e:
            logger.error(f"❌ Error enviando WhatsApp: {e}")
            return False

    def enviar_a_todos(self, mensaje: str, media_url: str = None) -> Dict[str, bool]:
        """
        Envía mensaje a todos los destinatarios configurados.

        Args:
            mensaje: Texto del mensaje
            media_url: URL de imagen (opcional)

        Returns:
            Diccionario con resultados por destinatario
        """
        resultados = {}

        for dest in self.config.destinatarios:
            resultados[dest] = self._enviar_mensaje(dest, mensaje, media_url)

        exitosos = sum(1 for v in resultados.values() if v)
        logger.info(f"📱 WhatsApp enviado a {exitosos}/{len(resultados)} destinatarios")

        return resultados

    # ===============================================================
    # MÉTODOS DE ALERTAS
    # ===============================================================

    def enviar_alerta_critica(
        self,
        titulo: str,
        descripcion: str,
        oc_numero: str = None,
        detalles: Dict = None
    ) -> Dict[str, bool]:
        """
        Envía una alerta crítica por WhatsApp.

        Args:
            titulo: Título de la alerta
            descripcion: Descripción del problema
            oc_numero: Número de OC relacionada
            detalles: Detalles adicionales

        Returns:
            Resultados de envío
        """
        emoji_alerta = "🚨"
        cedis_info = f"{CEDIS.get('name', 'CEDIS')} ({CEDIS.get('code', '427')})"

        mensaje = f"""
{emoji_alerta} *ALERTA CRÍTICA* {emoji_alerta}

*{titulo}*

{descripcion}

📍 *CEDIS:* {cedis_info}
🕐 *Hora:* {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
"""

        if oc_numero:
            mensaje += f"📦 *OC:* {oc_numero}\n"

        if detalles:
            mensaje += "\n*Detalles:*\n"
            for key, value in detalles.items():
                mensaje += f"• {key}: {value}\n"

        mensaje += "\n⚠️ _Requiere atención inmediata_"

        return self.enviar_a_todos(mensaje.strip())

    def enviar_alerta_alta(
        self,
        titulo: str,
        descripcion: str,
        modulo: str = "SISTEMA"
    ) -> Dict[str, bool]:
        """
        Envía una alerta de prioridad alta.

        Args:
            titulo: Título de la alerta
            descripcion: Descripción
            modulo: Módulo que genera la alerta

        Returns:
            Resultados de envío
        """
        mensaje = f"""
⚠️ *ALERTA ALTA*

*{titulo}*

{descripcion}

📍 CEDIS: {CEDIS.get('code', '427')}
📁 Módulo: {modulo}
🕐 Hora: {datetime.now().strftime('%H:%M:%S')}
"""
        return self.enviar_a_todos(mensaje.strip())

    def enviar_mensaje_info(
        self,
        titulo: str,
        mensaje_texto: str
    ) -> Dict[str, bool]:
        """
        Envía un mensaje informativo.

        Args:
            titulo: Título del mensaje
            mensaje_texto: Contenido del mensaje

        Returns:
            Resultados de envío
        """
        mensaje = f"""
ℹ️ *{titulo}*

{mensaje_texto}

📍 Sistema SAC - CEDIS {CEDIS.get('code', '427')}
🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')}
"""
        return self.enviar_a_todos(mensaje.strip())

    # ===============================================================
    # MÉTODOS DE REPORTES
    # ===============================================================

    def enviar_resumen_diario(
        self,
        total_validaciones: int,
        exitosas: int,
        fallidas: int,
        errores_criticos: int,
        tiempo_promedio: float
    ) -> Dict[str, bool]:
        """
        Envía el resumen diario de operaciones.

        Args:
            total_validaciones: Total de validaciones del día
            exitosas: Validaciones exitosas
            fallidas: Validaciones fallidas
            errores_criticos: Errores críticos detectados
            tiempo_promedio: Tiempo promedio de validación

        Returns:
            Resultados de envío
        """
        tasa_exito = (exitosas / total_validaciones * 100) if total_validaciones > 0 else 0

        # Determinar emoji según resultado
        if errores_criticos > 0:
            emoji_estado = "🔴"
            estado = "Con errores críticos"
        elif fallidas > 0:
            emoji_estado = "🟡"
            estado = "Con alertas"
        else:
            emoji_estado = "🟢"
            estado = "Sin problemas"

        mensaje = f"""
📊 *RESUMEN DIARIO DE OPERACIONES*
{datetime.now().strftime('%d/%m/%Y')}

{emoji_estado} *Estado General:* {estado}

📈 *Métricas del Día:*
• Validaciones: {total_validaciones}
• Exitosas: {exitosas} ✅
• Fallidas: {fallidas} ❌
• Tasa de éxito: {tasa_exito:.1f}%

⏱️ *Rendimiento:*
• Tiempo promedio: {tiempo_promedio:.2f}s

🚨 *Errores críticos:* {errores_criticos}

📍 Sistema SAC - CEDIS {CEDIS.get('name', 'Cancún')} ({CEDIS.get('code', '427')})
"""
        return self.enviar_a_todos(mensaje.strip())

    def enviar_validacion_oc(
        self,
        oc_numero: str,
        resultado: str,
        total_oc: float,
        total_distro: float,
        errores: int = 0
    ) -> Dict[str, bool]:
        """
        Envía resultado de validación de OC.

        Args:
            oc_numero: Número de OC
            resultado: Resultado (exitoso/fallido)
            total_oc: Total de la OC
            total_distro: Total de distribuciones
            errores: Número de errores

        Returns:
            Resultados de envío
        """
        emoji = "✅" if resultado == "exitoso" else "❌"
        diferencia = total_oc - total_distro

        mensaje = f"""
{emoji} *Validación de OC Completada*

📦 *OC:* {oc_numero}
📊 *Resultado:* {resultado.upper()}

📈 *Totales:*
• Total OC: {total_oc:,.0f}
• Total Distro: {total_distro:,.0f}
• Diferencia: {diferencia:,.0f}

⚠️ *Errores detectados:* {errores}

🕐 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
"""
        return self.enviar_a_todos(mensaje.strip())

    def enviar_estado_sistema(
        self,
        db_conectada: bool,
        telegram_activo: bool,
        email_configurado: bool,
        errores_pendientes: int
    ) -> Dict[str, bool]:
        """
        Envía estado del sistema.

        Args:
            db_conectada: Estado de conexión DB2
            telegram_activo: Estado de Telegram
            email_configurado: Estado de email
            errores_pendientes: Errores sin resolver

        Returns:
            Resultados de envío
        """
        estado_db = "🟢 Conectada" if db_conectada else "🔴 Desconectada"
        estado_tg = "🟢 Activo" if telegram_activo else "⚪ Inactivo"
        estado_email = "🟢 Configurado" if email_configurado else "⚪ No config."

        mensaje = f"""
🖥️ *Estado del Sistema SAC*

📊 *Conexiones:*
• Base de datos DB2: {estado_db}
• Telegram: {estado_tg}
• Email: {estado_email}
• WhatsApp: 🟢 Activo

⚠️ *Errores pendientes:* {errores_pendientes}

📍 CEDIS {CEDIS.get('name', 'Cancún')} ({CEDIS.get('code', '427')})
🕐 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
"""
        return self.enviar_a_todos(mensaje.strip())

    # ===============================================================
    # MÉTODOS DE UTILIDAD
    # ===============================================================

    def enviar_mensaje_prueba(self) -> Dict[str, bool]:
        """
        Envía un mensaje de prueba.

        Returns:
            Resultados de envío
        """
        mensaje = f"""
🧪 *Mensaje de Prueba*

Este es un mensaje de prueba del Sistema SAC.

✅ La conexión con WhatsApp está funcionando correctamente.

📍 CEDIS {CEDIS.get('name', 'Cancún')} ({CEDIS.get('code', '427')})
🕐 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
"""
        return self.enviar_a_todos(mensaje.strip())

    def verificar_conexion(self) -> bool:
        """
        Verifica la conexión con Twilio.

        Returns:
            True si la conexión es válida
        """
        if not self.enabled or not self._client:
            return False

        try:
            # Verificar cuenta
            account = self._client.api.accounts(self.config.account_sid).fetch()
            logger.info(f"✅ Conexión Twilio verificada: {account.friendly_name}")
            return True
        except Exception as e:
            logger.error(f"❌ Error verificando Twilio: {e}")
            return False

    def obtener_info(self) -> Dict:
        """
        Obtiene información de configuración.

        Returns:
            Diccionario con información
        """
        return {
            'enabled': self.enabled,
            'twilio_available': TWILIO_AVAILABLE,
            'account_sid_configured': bool(self.config.account_sid),
            'destinatarios': len(self.config.destinatarios),
            'whatsapp_from': self.config.whatsapp_from
        }


# ===============================================================
# FUNCIÓN DE CONVENIENCIA
# ===============================================================

def crear_notificador_whatsapp() -> NotificadorWhatsApp:
    """Crea un notificador WhatsApp desde configuración de entorno."""
    return NotificadorWhatsApp()


# ===============================================================
# EXPORTAR
# ===============================================================

__all__ = [
    'NotificadorWhatsApp',
    'crear_notificador_whatsapp',
    'ConfigWhatsApp',
    'TipoMensaje',
    'TWILIO_AVAILABLE',
]


# ===============================================================
# EJECUCIÓN DIRECTA
# ===============================================================

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    print("\n" + "=" * 60)
    print("📱 NOTIFICADOR WHATSAPP - SAC CEDIS 427")
    print("=" * 60)

    if not TWILIO_AVAILABLE:
        print("\n❌ Twilio no está instalado")
        print("   Ejecuta: pip install twilio")
    else:
        print("\n✅ Twilio disponible")

        wa = NotificadorWhatsApp()
        info = wa.obtener_info()

        print(f"\n📋 Configuración:")
        print(f"   • Habilitado: {'✅ Sí' if info['enabled'] else '❌ No'}")
        print(f"   • Account SID: {'✅ Configurado' if info['account_sid_configured'] else '❌ No configurado'}")
        print(f"   • Destinatarios: {info['destinatarios']}")
        print(f"   • From: {info['whatsapp_from']}")

        if wa.enabled:
            print("\n💡 Para enviar mensaje de prueba:")
            print("   wa.enviar_mensaje_prueba()")

    print("\n" + "=" * 60)
