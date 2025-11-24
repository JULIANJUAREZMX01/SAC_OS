#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════
MÓDULO DE RECEPCIÓN Y PROCESAMIENTO DE COMANDOS VÍA EMAIL
Sistema de Automatización de Consultas - Chedraui CEDIS
═══════════════════════════════════════════════════════════════

Este módulo permite recibir comandos desde email (IMAP) y ejecutarlos
en dispositivos Symbol conectados, con respuesta automática.

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún 427

Última actualización: Noviembre 2025
═══════════════════════════════════════════════════════════════
"""

import imaplib
import email
import logging
import time
import threading
from email.header import decode_header
from email.utils import parseaddr, parsedate_to_datetime
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# ENUMERACIONES Y DATACLASSES
# ═══════════════════════════════════════════════════════════════

class EstadoComando(Enum):
    """Estados del comando recibido"""
    PENDIENTE = "pendiente"
    PROCESANDO = "procesando"
    EXITOSO = "exitoso"
    FALLIDO = "fallido"
    IGNORADO = "ignorado"


@dataclass
class ComandoEmail:
    """Comando recibido vía email"""
    id_mensaje: str
    remitente_email: str
    remitente_nombre: str
    comando_texto: str
    timestamp_recepcion: datetime

    # Procesamiento
    estado: EstadoComando = EstadoComando.PENDIENTE
    comando_parseado: str = ""
    timestamp_procesamiento: Optional[datetime] = None
    resultado_ejecucion: Optional[str] = None
    error: Optional[str] = None


# ═══════════════════════════════════════════════════════════════
# RECEPTOR DE COMANDOS VÍA EMAIL (IMAP)
# ═══════════════════════════════════════════════════════════════

class ReceptorComandosEmail:
    """
    Lee comandos desde buzón IMAP y los pone en cola de ejecución.
    """

    def __init__(
        self,
        imap_host: str = "imap.office365.com",
        imap_puerto: int = 993,
        usuario: str = "",
        contraseña: str = "",
        buzones: List[str] = None,
        intervalo_polling: int = 60
    ):
        """
        Args:
            imap_host: Host IMAP (ej: imap.office365.com)
            imap_puerto: Puerto IMAP (default 993 = SSL)
            usuario: Email del usuario
            contraseña: Contraseña del email
            buzones: Buzones a monitorear (default: ["INBOX"])
            intervalo_polling: Segundos entre lecturas
        """
        self.imap_host = imap_host
        self.imap_puerto = imap_puerto
        self.usuario = usuario
        self.contraseña = contraseña
        self.buzones = buzones or ["INBOX"]
        self.intervalo_polling = intervalo_polling

        self._conectado = False
        self._imap_conn = None
        self._polling_activo = False
        self._polling_thread = None
        self._cola_comandos: List[ComandoEmail] = []
        self._procesados_recientemente: set = set()

        logger.info(f"✅ ReceptorComandosEmail inicializado para {usuario}")

    def conectar(self) -> bool:
        """Conecta al servidor IMAP"""
        try:
            self._imap_conn = imaplib.IMAP4_SSL(
                self.imap_host,
                self.imap_puerto,
                timeout=10
            )
            self._imap_conn.login(self.usuario, self.contraseña)
            self._conectado = True
            logger.info(f"✅ Conectado a IMAP: {self.imap_host}")
            return True

        except imaplib.IMAP4.error as e:
            logger.error(f"❌ Error IMAP: {e}")
            self._conectado = False
            return False
        except Exception as e:
            logger.exception(f"❌ Error conectando a IMAP: {e}")
            self._conectado = False
            return False

    def desconectar(self):
        """Desconecta del servidor IMAP"""
        if self._imap_conn:
            try:
                self._imap_conn.close()
                self._imap_conn.logout()
            except:
                pass
        self._conectado = False
        logger.info("✅ Desconectado de IMAP")

    def iniciar_polling(self) -> bool:
        """Inicia thread de polling para leer emails"""
        if self._polling_activo:
            logger.warning("⚠️ Polling ya está activo")
            return False

        if not self._conectado:
            if not self.conectar():
                return False

        self._polling_activo = True
        self._polling_thread = threading.Thread(
            target=self._loop_polling,
            daemon=True,
            name=f"PollingEmail-{self.usuario}"
        )
        self._polling_thread.start()
        logger.info(f"✅ Polling iniciado (intervalo: {self.intervalo_polling}s)")
        return True

    def detener_polling(self):
        """Detiene el thread de polling"""
        self._polling_activo = False
        if self._polling_thread:
            self._polling_thread.join(timeout=5)
        logger.info("✅ Polling detenido")

    def _loop_polling(self):
        """Loop interno de polling (ejecutado en thread separado)"""
        while self._polling_activo:
            try:
                self._leer_nuevos_emails()
                time.sleep(self.intervalo_polling)
            except Exception as e:
                logger.error(f"❌ Error en polling: {e}")
                # Intentar reconectar
                self._conectado = False
                if not self.conectar():
                    logger.error("No se pudo reconectar a IMAP")

    def _leer_nuevos_emails(self):
        """Lee nuevos emails de los buzones configurados"""
        if not self._conectado:
            return

        try:
            for buzon in self.buzones:
                # Seleccionar buzón
                status, messages = self._imap_conn.select(buzon, readonly=False)
                if status != 'OK':
                    continue

                # Buscar emails no leídos
                status, message_ids = self._imap_conn.search(None, 'UNSEEN')
                if status != 'OK':
                    continue

                message_ids = message_ids[0].split()
                if not message_ids:
                    continue

                # Procesar cada email
                for msg_id in message_ids:
                    self._procesar_email(msg_id, buzon)

        except Exception as e:
            logger.debug(f"Error leyendo emails: {e}")

    def _procesar_email(self, msg_id: bytes, buzon: str):
        """Procesa un email individual"""
        try:
            status, msg_data = self._imap_conn.fetch(msg_id, '(RFC822)')
            if status != 'OK':
                return

            email_message = email.message_from_bytes(msg_data[0][1])

            # Extraer información
            remitente_email, remitente_nombre = parseaddr(email_message['From'])
            asunto = email_message.get('Subject', '(sin asunto)')
            timestamp_email = parsedate_to_datetime(email_message['Date'])

            # Decodificar asunto si es necesario
            if isinstance(asunto, bytes):
                asunto = decode_header(asunto)[0][0]
                if isinstance(asunto, bytes):
                    asunto = asunto.decode('utf-8', errors='ignore')

            # Extraer comando del cuerpo o asunto
            comando_texto = self._extraer_comando(email_message)

            if not comando_texto:
                logger.debug(f"⚠️ Email sin comando válido de {remitente_email}")
                # Marcar como leído
                self._imap_conn.store(msg_id, '+FLAGS', '\\Seen')
                return

            # Crear comando
            comando = ComandoEmail(
                id_mensaje=msg_id.decode() if isinstance(msg_id, bytes) else msg_id,
                remitente_email=remitente_email,
                remitente_nombre=remitente_nombre or remitente_email.split('@')[0],
                comando_texto=comando_texto,
                timestamp_recepcion=timestamp_email
            )

            # Evitar duplicados recientes (últimos 5 minutos)
            hash_cmd = hash((remitente_email, comando_texto, timestamp_email.minute))
            if hash_cmd not in self._procesados_recientemente:
                self._cola_comandos.append(comando)
                self._procesados_recientemente.add(hash_cmd)
                logger.info(f"✅ Comando encolado de {remitente_email}: {comando_texto[:50]}")

            # Marcar como leído
            self._imap_conn.store(msg_id, '+FLAGS', '\\Seen')

        except Exception as e:
            logger.debug(f"Error procesando email {msg_id}: {e}")

    def _extraer_comando(self, email_message) -> str:
        """Extrae comando del email (de asunto o cuerpo)"""
        # Intentar obtener de asunto
        asunto = email_message.get('Subject', '').lower()

        palabras_clave = ['comando:', 'cmd:', 'ejecutar:', 'run:']
        for palabra in palabras_clave:
            if palabra in asunto:
                return asunto.split(palabra)[1].strip()

        # Intentar obtener del cuerpo
        try:
            if email_message.is_multipart():
                for part in email_message.walk():
                    if part.get_content_type() == 'text/plain':
                        cuerpo = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        break
            else:
                cuerpo = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')

            # Buscar línea de comando (primera línea no vacía)
            for linea in cuerpo.split('\n'):
                linea = linea.strip()
                if linea and not linea.startswith('--') and not linea.startswith('//'):
                    return linea

        except:
            pass

        return ""

    def obtener_comandos_pendientes(self) -> List[ComandoEmail]:
        """Retorna comandos pendientes de procesar"""
        pendientes = [c for c in self._cola_comandos if c.estado == EstadoComando.PENDIENTE]
        return pendientes

    def marcar_como_procesado(self, comando: ComandoEmail, exito: bool,
                             resultado: str = "", error: str = ""):
        """Marca comando como procesado"""
        comando.estado = EstadoComando.EXITOSO if exito else EstadoComando.FALLIDO
        comando.timestamp_procesamiento = datetime.now()
        comando.resultado_ejecucion = resultado
        comando.error = error
        logger.info(f"✅ Comando marcado como {comando.estado.value}: {comando.comando_parseado}")

    def limpiar_procesados(self, minutos: int = 60):
        """Limpia comandos procesados hace más de N minutos"""
        ahora = datetime.now()
        inicial = len(self._cola_comandos)

        self._cola_comandos = [
            c for c in self._cola_comandos
            if c.estado == EstadoComando.PENDIENTE or
            (c.timestamp_procesamiento and
             (ahora - c.timestamp_procesamiento).total_seconds() < minutos * 60)
        ]

        eliminados = inicial - len(self._cola_comandos)
        if eliminados > 0:
            logger.debug(f"Limpieza: {eliminados} comandos procesados eliminados")


# ═══════════════════════════════════════════════════════════════
# PROCESADOR DE COMANDOS
# ═══════════════════════════════════════════════════════════════

class ProcesadorComandosEmail:
    """
    Procesa comandos recibidos por email en dispositivos Symbol.
    """

    def __init__(self, gestor_symbol=None, receptor_email=None):
        """
        Args:
            gestor_symbol: GestorDispositivosSymbol instance
            receptor_email: ReceptorComandosEmail instance
        """
        self.gestor_symbol = gestor_symbol
        self.receptor_email = receptor_email
        self._procesando = False
        self._proceso_thread = None

        logger.info("✅ ProcesadorComandosEmail inicializado")

    def iniciar_procesamiento(self, intervalo_verificacion: int = 10) -> bool:
        """Inicia thread de procesamiento"""
        if self._procesando:
            logger.warning("⚠️ Procesamiento ya está activo")
            return False

        if not self.receptor_email:
            logger.error("❌ No hay receptor de email configurado")
            return False

        self._procesando = True
        self._proceso_thread = threading.Thread(
            target=self._loop_procesamiento,
            args=(intervalo_verificacion,),
            daemon=True,
            name="ProcesadorComandosEmail"
        )
        self._proceso_thread.start()
        logger.info(f"✅ Procesamiento iniciado (verificación cada {intervalo_verificacion}s)")
        return True

    def detener_procesamiento(self):
        """Detiene el procesamiento"""
        self._procesando = False
        if self._proceso_thread:
            self._proceso_thread.join(timeout=5)
        logger.info("✅ Procesamiento detenido")

    def _loop_procesamiento(self, intervalo: int):
        """Loop de procesamiento de comandos"""
        while self._procesando:
            try:
                comandos = self.receptor_email.obtener_comandos_pendientes()

                for comando in comandos:
                    self._procesar_comando(comando)

                # Limpiar periódicamente
                if int(time.time()) % 300 == 0:  # Cada 5 minutos
                    self.receptor_email.limpiar_procesados(minutos=60)

                time.sleep(intervalo)

            except Exception as e:
                logger.error(f"❌ Error en loop de procesamiento: {e}")

    def _procesar_comando(self, comando: ComandoEmail):
        """Procesa un comando individual"""
        try:
            logger.info(f"📨 Procesando comando de {comando.remitente_email}: {comando.comando_texto}")

            # Validar que hay gestor y conexión
            if not self.gestor_symbol or not self.gestor_symbol.telnet:
                error = "No hay dispositivo Symbol conectado"
                self.receptor_email.marcar_como_procesado(
                    comando,
                    exito=False,
                    error=error
                )
                self._enviar_respuesta_email(comando, False, error_msg=error)
                return

            # Ejecutar comando
            resultado = self.gestor_symbol.telnet.ejecutar_comando(comando.comando_texto)

            if resultado.exito:
                self.receptor_email.marcar_como_procesado(
                    comando,
                    exito=True,
                    resultado=resultado.respuesta
                )
                logger.info(f"✅ Comando exitoso: {comando.comando_texto}")

                # Enviar respuesta por email
                self.gestor_symbol.telnet.enviar_respuesta_comando_email(
                    comando.remitente_email,
                    comando.comando_texto,
                    resultado
                )
            else:
                error_msg = "; ".join(resultado.errores) if resultado.errores else "Error desconocido"
                self.receptor_email.marcar_como_procesado(
                    comando,
                    exito=False,
                    error=error_msg
                )
                logger.error(f"❌ Comando fallido: {error_msg}")
                self._enviar_respuesta_email(comando, False, error_msg=error_msg)

        except Exception as e:
            logger.exception(f"❌ Error procesando comando: {e}")
            self.receptor_email.marcar_como_procesado(
                comando,
                exito=False,
                error=str(e)
            )
            self._enviar_respuesta_email(comando, False, error_msg=str(e))

    def _enviar_respuesta_email(self, comando: ComandoEmail, exito: bool,
                               resultado_texto: str = "", error_msg: str = ""):
        """Envía respuesta por email usando configuración del gestor"""
        if not self.gestor_symbol or not self.gestor_symbol.telnet:
            return

        telnet = self.gestor_symbol.telnet

        # Construir cuerpo HTML
        estado = "✅ EXITOSO" if exito else "❌ FALLIDO"
        asunto = f"[SAC] Respuesta: {comando.comando_texto[:50]} - {estado}"

        cuerpo_html = f"""
        <html>
            <body style="font-family: Arial; color: #333;">
                <h2>📧 Respuesta a tu comando SAC</h2>
                <p>Hola {comando.remitente_nombre},</p>

                <p><b>Comando enviado:</b> <code>{comando.comando_texto}</code></p>
                <p><b>Estado:</b> <span style="color: {'green' if exito else 'red'};"><b>{estado}</b></span></p>

                {f'<h3>Resultado:</h3><pre style="background-color: #f5f5f5; padding: 10px;">{resultado_texto}</pre>' if resultado_texto else ''}

                {f'<h3 style="color: red;">Error:</h3><p>{error_msg}</p>' if error_msg else ''}

                <hr>
                <p style="color: #999; font-size: 12px;">
                    Sistema SAC - CEDIS 427 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
                    Emulador SACITY para dispositivos Symbol MC9000/MC93
                </p>
            </body>
        </html>
        """

        telnet._enviar_smtp([comando.remitente_email], asunto, cuerpo_html)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger.info("Módulo de Email Commands cargado")
