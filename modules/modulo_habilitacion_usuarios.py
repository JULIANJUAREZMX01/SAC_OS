"""
═══════════════════════════════════════════════════════════════
MÓDULO DE HABILITACIÓN AUTOMÁTICA DE USUARIOS
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Este módulo actúa como "usuario habilitador" automático del WMS,
detectando y habilitando usuarios desconectados abruptamente
que tengan trabajo visible en el sistema.

Características:
- Operación automática de 6:00 AM a 6:00 PM (hora Cancún)
- Activo de Lunes a Sábado
- Detección de usuarios bloqueados con trabajo activo
- Habilitación instantánea
- Notificaciones a WhatsApp y Telegram
- Notificación de inicio/fin del servicio diario
- Modo dormitorio fuera de horario (ahorro de recursos)

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
═══════════════════════════════════════════════════════════════
"""

import logging
import time
import threading
import signal
import sys
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd
from pathlib import Path

# Importar pytz para manejo de zona horaria
try:
    import pytz
    PYTZ_AVAILABLE = True
except ImportError:
    PYTZ_AVAILABLE = False

# Importaciones del proyecto
try:
    from config import (
        DB_CONFIG, CEDIS, TELEGRAM_CONFIG, SYSTEM_CONFIG, PATHS,
        LOGGING_CONFIG
    )
    from modules.db_connection import DB2Connection, DB2ConnectionError, DB2QueryError
    from notificaciones_telegram import NotificadorTelegram, TipoAlerta
except ImportError as e:
    print(f"⚠️ Error importando módulos: {e}")
    DB_CONFIG = {}
    CEDIS = {'code': '427', 'name': 'CEDIS Cancún'}
    TELEGRAM_CONFIG = {}
    SYSTEM_CONFIG = {}
    PATHS = {'logs': Path('output/logs')}


# ═══════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE LOGGING
# ═══════════════════════════════════════════════════════════════

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# CONFIGURACIÓN DEL MÓDULO
# ═══════════════════════════════════════════════════════════════

# Intentar cargar configuración de .env
import os
from dotenv import load_dotenv
load_dotenv()

# Configuración de habilitación de usuarios
HABILITACION_CONFIG = {
    # Horario de operación
    'hora_inicio': int(os.getenv('HABILITACION_HORA_INICIO', 6)),      # 6:00 AM
    'hora_fin': int(os.getenv('HABILITACION_HORA_FIN', 18)),           # 6:00 PM
    'dias_operacion': os.getenv('HABILITACION_DIAS', '0,1,2,3,4,5').split(','),  # Lun-Sáb
    'timezone': os.getenv('HABILITACION_TIMEZONE', 'America/Cancun'),

    # Intervalos de chequeo
    'intervalo_chequeo_segundos': int(os.getenv('HABILITACION_INTERVALO', 30)),
    'intervalo_dormitorio_segundos': int(os.getenv('HABILITACION_INTERVALO_DORMIDO', 300)),

    # Notificaciones
    'notificar_telegram': os.getenv('HABILITACION_TELEGRAM', 'true').lower() == 'true',
    'notificar_whatsapp': os.getenv('HABILITACION_WHATSAPP', 'true').lower() == 'true',

    # WhatsApp API (Twilio o similar)
    'whatsapp_api_url': os.getenv('WHATSAPP_API_URL', ''),
    'whatsapp_api_token': os.getenv('WHATSAPP_API_TOKEN', ''),
    'whatsapp_group_id': os.getenv('WHATSAPP_GROUP_ID', ''),
    'whatsapp_phone_numbers': [
        p.strip() for p in os.getenv('WHATSAPP_PHONE_NUMBERS', '').split(',') if p.strip()
    ],

    # Control
    'enabled': os.getenv('HABILITACION_ENABLED', 'true').lower() == 'true',
    'max_habilitaciones_hora': int(os.getenv('HABILITACION_MAX_POR_HORA', 50)),
}


# ═══════════════════════════════════════════════════════════════
# ENUMERACIONES Y DATACLASSES
# ═══════════════════════════════════════════════════════════════

class EstadoUsuario(Enum):
    """Estados posibles de un usuario en WMS"""
    ACTIVO = "ACTIVO"
    BLOQUEADO = "BLOQUEADO"
    INACTIVO = "INACTIVO"
    DESCONECTADO_ABRUPTO = "DESCONECTADO_ABRUPTO"


class EstadoServicio(Enum):
    """Estados del servicio de habilitación"""
    ACTIVO = "🟢 ACTIVO"
    DORMIDO = "😴 DORMIDO"
    DETENIDO = "🔴 DETENIDO"
    ERROR = "❌ ERROR"


@dataclass
class UsuarioBloqueado:
    """Representa un usuario bloqueado detectado"""
    usuario_id: str
    nombre: str
    puesto: str
    ultima_actividad: datetime
    tarea_activa: str
    tipo_tarea: str
    ubicacion: str
    motivo_bloqueo: str
    tiempo_bloqueado_minutos: int
    datos_adicionales: Dict = field(default_factory=dict)


@dataclass
class ResultadoHabilitacion:
    """Resultado de una habilitación"""
    usuario_id: str
    exitoso: bool
    mensaje: str
    timestamp: datetime
    detalles: Optional[str] = None


@dataclass
class EstadisticasServicio:
    """Estadísticas del servicio de habilitación"""
    inicio_servicio: datetime
    usuarios_habilitados_hoy: int = 0
    usuarios_habilitados_total: int = 0
    errores_hoy: int = 0
    ultimo_chequeo: Optional[datetime] = None
    ultima_habilitacion: Optional[datetime] = None
    estado: EstadoServicio = EstadoServicio.DETENIDO


# ═══════════════════════════════════════════════════════════════
# QUERIES SQL PARA MANHATTAN WMS
# ═══════════════════════════════════════════════════════════════

# Query para detectar usuarios bloqueados con trabajo activo
QUERY_USUARIOS_BLOQUEADOS = """
SELECT
    UP.USERKEY AS USUARIO_ID,
    UP.USERNAME AS NOMBRE_USUARIO,
    COALESCE(UP.FIRSTNAME || ' ' || UP.LASTNAME, UP.USERNAME) AS NOMBRE_COMPLETO,
    UP.USERGROUP AS GRUPO_USUARIO,
    UP.STATUS AS ESTADO_ACTUAL,
    UP.ADDDATE AS FECHA_CREACION,
    UP.EDITDATE AS ULTIMA_MODIFICACION,

    -- Información de tarea activa
    TD.TASKDETAILKEY AS TAREA_ID,
    TD.TASKTYPE AS TIPO_TAREA,
    TD.STATUS AS ESTADO_TAREA,
    TD.FROMLOC AS UBICACION_ORIGEN,
    TD.TOLOC AS UBICACION_DESTINO,
    TD.SKU AS SKU,
    TD.QTY AS CANTIDAD,
    TD.STARTTIME AS INICIO_TAREA,
    TD.ADDDATE AS FECHA_ASIGNACION,

    -- Calcular tiempo desde última actividad
    TIMESTAMPDIFF(MINUTE, TD.STARTTIME, CURRENT_TIMESTAMP) AS MINUTOS_DESDE_INICIO,

    -- Información de sesión
    COALESCE(US.LASTACTIVITY, TD.STARTTIME) AS ULTIMA_ACTIVIDAD,
    US.SESSIONID AS SESION_ID,
    US.TERMINALID AS TERMINAL_ID

FROM WMWHSE1.USERPROFILE UP
LEFT JOIN WMWHSE1.TASKDETAIL TD
    ON UP.USERKEY = TD.USERKEY
    AND TD.STATUS IN ('1', '2', '3')  -- Tareas activas/en progreso
LEFT JOIN WMWHSE1.USERSESSION US
    ON UP.USERKEY = US.USERKEY

WHERE
    -- Usuario bloqueado o con sesión cerrada abruptamente
    (UP.STATUS = '9'  -- Bloqueado
     OR (US.SESSIONID IS NULL AND TD.TASKDETAILKEY IS NOT NULL)  -- Sin sesión pero con tarea
     OR (US.STATUS = '0' AND TD.TASKDETAILKEY IS NOT NULL))  -- Sesión cerrada con tarea activa

    -- Con trabajo visible/activo
    AND TD.TASKDETAILKEY IS NOT NULL

    -- En las últimas 24 horas (evitar usuarios antiguos)
    AND TD.STARTTIME >= CURRENT_TIMESTAMP - 24 HOURS

ORDER BY MINUTOS_DESDE_INICIO DESC
"""

# Query para habilitar usuario
QUERY_HABILITAR_USUARIO = """
UPDATE WMWHSE1.USERPROFILE
SET
    STATUS = '1',
    EDITDATE = CURRENT_TIMESTAMP,
    EDITWHO = 'SAC_AUTO_ENABLE'
WHERE
    USERKEY = ?
    AND STATUS = '9'
"""

# Query para liberar sesión bloqueada
QUERY_LIBERAR_SESION = """
UPDATE WMWHSE1.USERSESSION
SET
    STATUS = '0',
    ENDTIME = CURRENT_TIMESTAMP,
    EDITDATE = CURRENT_TIMESTAMP
WHERE
    USERKEY = ?
    AND STATUS != '0'
"""

# Query para verificar si usuario ya está activo
QUERY_VERIFICAR_USUARIO = """
SELECT
    USERKEY,
    USERNAME,
    STATUS,
    EDITDATE
FROM WMWHSE1.USERPROFILE
WHERE USERKEY = ?
"""


# ═══════════════════════════════════════════════════════════════
# CLASE DE NOTIFICACIONES WHATSAPP
# ═══════════════════════════════════════════════════════════════

class NotificadorWhatsApp:
    """
    Gestor de notificaciones WhatsApp para el sistema SAC

    Soporta múltiples proveedores:
    - API genérica (configurable)
    - Twilio WhatsApp Business API
    - WhatsApp Business Cloud API (Meta)
    """

    def __init__(self, config: Dict):
        """
        Inicializa el notificador de WhatsApp

        Args:
            config: Diccionario con configuración:
                {
                    'api_url': 'URL de la API',
                    'api_token': 'Token de autenticación',
                    'group_id': 'ID del grupo',
                    'phone_numbers': ['521...', '521...']
                }
        """
        self.api_url = config.get('whatsapp_api_url', '')
        self.api_token = config.get('whatsapp_api_token', '')
        self.group_id = config.get('whatsapp_group_id', '')
        self.phone_numbers = config.get('whatsapp_phone_numbers', [])
        self.cedis_name = f"{CEDIS.get('name', 'CEDIS')} {CEDIS.get('code', '427')}"

        self.enabled = bool(self.api_url and self.api_token)

        # Estadísticas
        self.stats = {
            'mensajes_enviados': 0,
            'mensajes_fallidos': 0,
            'ultimo_envio': None
        }

        if not self.enabled:
            logger.warning("⚠️ WhatsApp no configurado - notificaciones deshabilitadas")

    def _enviar_request(self, mensaje: str, destinatarios: List[str] = None) -> Dict[str, bool]:
        """
        Envía mensaje via API de WhatsApp

        Args:
            mensaje: Texto del mensaje
            destinatarios: Lista de números o IDs de grupo

        Returns:
            Diccionario con resultados por destinatario
        """
        if not self.enabled:
            return {}

        resultados = {}
        destinos = destinatarios or self.phone_numbers

        if self.group_id:
            destinos = [self.group_id] + destinos

        headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        }

        for destino in destinos:
            try:
                payload = {
                    'to': destino,
                    'message': mensaje,
                    'type': 'text'
                }

                response = requests.post(
                    self.api_url,
                    json=payload,
                    headers=headers,
                    timeout=30
                )

                if response.status_code in [200, 201]:
                    resultados[destino] = True
                    self.stats['mensajes_enviados'] += 1
                    self.stats['ultimo_envio'] = datetime.now()
                    logger.info(f"✅ WhatsApp enviado a {destino}")
                else:
                    resultados[destino] = False
                    self.stats['mensajes_fallidos'] += 1
                    logger.error(f"❌ Error WhatsApp {destino}: {response.status_code}")

            except Exception as e:
                resultados[destino] = False
                self.stats['mensajes_fallidos'] += 1
                logger.error(f"❌ Error WhatsApp {destino}: {str(e)}")

        return resultados

    def enviar_habilitacion(
        self,
        usuario: UsuarioBloqueado,
        resultado: ResultadoHabilitacion
    ) -> Dict[str, bool]:
        """
        Envía notificación de habilitación de usuario
        """
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

        emoji = "✅" if resultado.exitoso else "❌"
        estado = "HABILITADO" if resultado.exitoso else "ERROR"

        mensaje = f"""
{emoji} *USUARIO {estado}* - {self.cedis_name}

👤 *Usuario:* {usuario.nombre}
🆔 *ID:* {usuario.usuario_id}
💼 *Puesto:* {usuario.puesto}

📋 *Tarea Activa:* {usuario.tipo_tarea}
📍 *Ubicación:* {usuario.ubicacion}
⏱️ *Tiempo Bloqueado:* {usuario.tiempo_bloqueado_minutos} min

📝 *Motivo:* {usuario.motivo_bloqueo}
⏰ *Fecha/Hora:* {timestamp}

━━━━━━━━━━━━━━━━━━━━━
🤖 _Sistema SAC - Habilitación Automática_
"""

        return self._enviar_request(mensaje)

    def enviar_inicio_servicio(self) -> Dict[str, bool]:
        """Notifica inicio del servicio de habilitación"""
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

        mensaje = f"""
🚀 *SERVICIO DE HABILITACIÓN INICIADO*

🏢 *CEDIS:* {self.cedis_name}
⏰ *Inicio:* {timestamp}
📅 *Horario:* 6:00 AM - 6:00 PM

✅ Monitoreo de usuarios activo
✅ Habilitación automática activa
✅ Notificaciones configuradas

━━━━━━━━━━━━━━━━━━━━━
🤖 _Sistema SAC v1.0.0_
"""
        return self._enviar_request(mensaje)

    def enviar_fin_servicio(self, estadisticas: EstadisticasServicio) -> Dict[str, bool]:
        """Notifica fin del servicio con resumen del día"""
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

        mensaje = f"""
😴 *SERVICIO DE HABILITACIÓN FINALIZADO*

🏢 *CEDIS:* {self.cedis_name}
⏰ *Fin:* {timestamp}

━━━━━━━━━━━━━━━━━━━━━
📊 *RESUMEN DEL DÍA*
━━━━━━━━━━━━━━━━━━━━━
👥 Usuarios habilitados: *{estadisticas.usuarios_habilitados_hoy}*
❌ Errores: *{estadisticas.errores_hoy}*

━━━━━━━━━━━━━━━━━━━━━
🌙 _Sistema entrando en modo dormitorio_
🤖 _Sistema SAC v1.0.0_
"""
        return self._enviar_request(mensaje)

    def verificar_conexion(self) -> bool:
        """Verifica si la conexión a la API está activa"""
        if not self.enabled:
            return False

        try:
            # Intentar endpoint de verificación si existe
            response = requests.get(
                f"{self.api_url}/status",
                headers={'Authorization': f'Bearer {self.api_token}'},
                timeout=10
            )
            return response.status_code == 200
        except Exception:
            return False


# ═══════════════════════════════════════════════════════════════
# CLASE PRINCIPAL: SERVICIO DE HABILITACIÓN
# ═══════════════════════════════════════════════════════════════

class ServicioHabilitacionUsuarios:
    """
    Servicio de habilitación automática de usuarios para Manhattan WMS

    Características:
    - Monitoreo continuo de usuarios bloqueados
    - Habilitación automática cuando detecta trabajo activo
    - Notificaciones instantáneas (Telegram + WhatsApp)
    - Operación en horario definido (6AM-6PM Lun-Sáb)
    - Modo dormitorio fuera de horario

    Uso:
        servicio = ServicioHabilitacionUsuarios()
        servicio.iniciar()  # Inicia en segundo plano
        # ...
        servicio.detener()  # Detiene el servicio
    """

    def __init__(self, config: Dict = None):
        """
        Inicializa el servicio de habilitación

        Args:
            config: Configuración personalizada (usa HABILITACION_CONFIG por defecto)
        """
        self.config = config or HABILITACION_CONFIG

        # Estado del servicio
        self.estadisticas = EstadisticasServicio(
            inicio_servicio=datetime.now(),
            estado=EstadoServicio.DETENIDO
        )

        # Control de hilos
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        # Conexión a DB
        self.db: Optional[DB2Connection] = None

        # Notificadores
        self._inicializar_notificadores()

        # Zona horaria
        if PYTZ_AVAILABLE:
            self.tz = pytz.timezone(self.config.get('timezone', 'America/Cancun'))
        else:
            self.tz = None
            logger.warning("⚠️ pytz no disponible - usando hora local")

        # Registro de usuarios habilitados (evitar duplicados)
        self._usuarios_habilitados_sesion: set = set()

        # Contadores por hora (para límite)
        self._habilitaciones_hora: Dict[int, int] = {}

        logger.info(f"🔧 ServicioHabilitacionUsuarios inicializado")
        logger.info(f"   Horario: {self.config['hora_inicio']}:00 - {self.config['hora_fin']}:00")
        logger.info(f"   Días: Lun-Sáb")
        logger.info(f"   Intervalo: {self.config['intervalo_chequeo_segundos']}s")

    def _inicializar_notificadores(self) -> None:
        """Inicializa los servicios de notificación"""
        # Telegram
        if self.config.get('notificar_telegram', True):
            try:
                telegram_config = {
                    'bot_token': TELEGRAM_CONFIG.get('bot_token', ''),
                    'chat_ids': TELEGRAM_CONFIG.get('chat_ids', []),
                    'enabled': TELEGRAM_CONFIG.get('enabled', True),
                    'cedis_name': f"{CEDIS.get('name', 'CEDIS')} {CEDIS.get('code', '427')}"
                }
                self.notificador_telegram = NotificadorTelegram(telegram_config)
                logger.info("✅ Notificador Telegram inicializado")
            except Exception as e:
                logger.warning(f"⚠️ Error inicializando Telegram: {e}")
                self.notificador_telegram = None
        else:
            self.notificador_telegram = None

        # WhatsApp
        if self.config.get('notificar_whatsapp', True):
            try:
                self.notificador_whatsapp = NotificadorWhatsApp(self.config)
                logger.info("✅ Notificador WhatsApp inicializado")
            except Exception as e:
                logger.warning(f"⚠️ Error inicializando WhatsApp: {e}")
                self.notificador_whatsapp = None
        else:
            self.notificador_whatsapp = None

    def _obtener_hora_actual(self) -> datetime:
        """Obtiene la hora actual en la zona horaria configurada"""
        if self.tz:
            return datetime.now(self.tz)
        return datetime.now()

    def _esta_en_horario_operacion(self) -> bool:
        """
        Verifica si estamos dentro del horario de operación

        Returns:
            True si estamos en horario de operación
        """
        ahora = self._obtener_hora_actual()

        # Verificar día de la semana (0=Lunes, 6=Domingo)
        dia_semana = str(ahora.weekday())
        dias_operacion = self.config.get('dias_operacion', ['0', '1', '2', '3', '4', '5'])

        if dia_semana not in dias_operacion:
            return False

        # Verificar hora
        hora_actual = ahora.hour
        hora_inicio = self.config.get('hora_inicio', 6)
        hora_fin = self.config.get('hora_fin', 18)

        return hora_inicio <= hora_actual < hora_fin

    def _conectar_db(self) -> bool:
        """
        Establece conexión a la base de datos

        Returns:
            True si la conexión fue exitosa
        """
        try:
            if self.db and self.db.is_connected():
                return True

            self.db = DB2Connection(config=DB_CONFIG)
            self.db.connect()
            logger.info("✅ Conexión a DB2 establecida")
            return True

        except Exception as e:
            logger.error(f"❌ Error conectando a DB2: {str(e)}")
            self.estadisticas.estado = EstadoServicio.ERROR
            return False

    def _desconectar_db(self) -> None:
        """Cierra la conexión a la base de datos"""
        if self.db:
            try:
                self.db.disconnect()
                logger.info("🔌 Conexión a DB2 cerrada")
            except Exception as e:
                logger.warning(f"⚠️ Error cerrando conexión: {e}")
            self.db = None

    def detectar_usuarios_bloqueados(self) -> List[UsuarioBloqueado]:
        """
        Detecta usuarios bloqueados con trabajo activo

        Returns:
            Lista de usuarios bloqueados detectados
        """
        usuarios = []

        try:
            if not self._conectar_db():
                return usuarios

            df = self.db.execute_query(QUERY_USUARIOS_BLOQUEADOS)

            if df.empty:
                logger.debug("✅ No se detectaron usuarios bloqueados")
                return usuarios

            for _, row in df.iterrows():
                usuario_id = str(row.get('USUARIO_ID', ''))

                # Evitar procesar el mismo usuario múltiples veces en la sesión
                if usuario_id in self._usuarios_habilitados_sesion:
                    continue

                usuario = UsuarioBloqueado(
                    usuario_id=usuario_id,
                    nombre=str(row.get('NOMBRE_COMPLETO', row.get('NOMBRE_USUARIO', 'N/A'))),
                    puesto=str(row.get('GRUPO_USUARIO', 'N/A')),
                    ultima_actividad=row.get('ULTIMA_ACTIVIDAD', datetime.now()),
                    tarea_activa=str(row.get('TAREA_ID', 'N/A')),
                    tipo_tarea=str(row.get('TIPO_TAREA', 'N/A')),
                    ubicacion=str(row.get('UBICACION_ORIGEN', 'N/A')),
                    motivo_bloqueo="Desconexión abrupta con trabajo activo",
                    tiempo_bloqueado_minutos=int(row.get('MINUTOS_DESDE_INICIO', 0)),
                    datos_adicionales={
                        'sku': str(row.get('SKU', '')),
                        'cantidad': int(row.get('CANTIDAD', 0)),
                        'ubicacion_destino': str(row.get('UBICACION_DESTINO', '')),
                        'terminal': str(row.get('TERMINAL_ID', '')),
                        'sesion': str(row.get('SESION_ID', ''))
                    }
                )
                usuarios.append(usuario)

            if usuarios:
                logger.info(f"🔍 Detectados {len(usuarios)} usuarios bloqueados con trabajo activo")

        except Exception as e:
            logger.error(f"❌ Error detectando usuarios bloqueados: {str(e)}")
            self.estadisticas.errores_hoy += 1

        return usuarios

    def habilitar_usuario(self, usuario: UsuarioBloqueado) -> ResultadoHabilitacion:
        """
        Habilita un usuario bloqueado

        Args:
            usuario: Usuario a habilitar

        Returns:
            Resultado de la operación
        """
        resultado = ResultadoHabilitacion(
            usuario_id=usuario.usuario_id,
            exitoso=False,
            mensaje="",
            timestamp=datetime.now()
        )

        try:
            # Verificar límite por hora
            hora_actual = self._obtener_hora_actual().hour
            habilitaciones_esta_hora = self._habilitaciones_hora.get(hora_actual, 0)
            max_por_hora = self.config.get('max_habilitaciones_hora', 50)

            if habilitaciones_esta_hora >= max_por_hora:
                resultado.mensaje = f"Límite de habilitaciones por hora alcanzado ({max_por_hora})"
                logger.warning(f"⚠️ {resultado.mensaje}")
                return resultado

            if not self._conectar_db():
                resultado.mensaje = "Error de conexión a base de datos"
                return resultado

            # Habilitar el usuario
            with self.db.transaction():
                # Actualizar estado del usuario
                rows_affected = self.db.execute_non_query(
                    QUERY_HABILITAR_USUARIO,
                    params=(usuario.usuario_id,),
                    auto_commit=False
                )

                # Liberar sesión si existe
                self.db.execute_non_query(
                    QUERY_LIBERAR_SESION,
                    params=(usuario.usuario_id,),
                    auto_commit=False
                )

            if rows_affected > 0:
                resultado.exitoso = True
                resultado.mensaje = f"Usuario {usuario.nombre} habilitado exitosamente"
                resultado.detalles = f"Tarea activa: {usuario.tipo_tarea}, Ubicación: {usuario.ubicacion}"

                # Actualizar estadísticas
                self.estadisticas.usuarios_habilitados_hoy += 1
                self.estadisticas.usuarios_habilitados_total += 1
                self.estadisticas.ultima_habilitacion = datetime.now()

                # Actualizar contadores
                self._habilitaciones_hora[hora_actual] = habilitaciones_esta_hora + 1
                self._usuarios_habilitados_sesion.add(usuario.usuario_id)

                logger.info(f"✅ {resultado.mensaje}")
            else:
                resultado.mensaje = f"Usuario {usuario.usuario_id} no encontrado o ya activo"
                logger.warning(f"⚠️ {resultado.mensaje}")

        except Exception as e:
            resultado.mensaje = f"Error habilitando usuario: {str(e)}"
            resultado.detalles = str(e)
            self.estadisticas.errores_hoy += 1
            logger.error(f"❌ {resultado.mensaje}")

        return resultado

    def _notificar_habilitacion(
        self,
        usuario: UsuarioBloqueado,
        resultado: ResultadoHabilitacion
    ) -> None:
        """
        Envía notificaciones de habilitación por todos los canales

        Args:
            usuario: Usuario habilitado
            resultado: Resultado de la habilitación
        """
        # Telegram
        if self.notificador_telegram:
            try:
                timestamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
                emoji = "✅" if resultado.exitoso else "❌"
                estado = "HABILITADO" if resultado.exitoso else "ERROR"

                mensaje = f"""
{emoji} <b>USUARIO {estado}</b> - {self.notificador_telegram.cedis_name}

👤 <b>Usuario:</b> {usuario.nombre}
🆔 <b>ID:</b> {usuario.usuario_id}
💼 <b>Puesto:</b> {usuario.puesto}

📋 <b>Tarea Activa:</b> {usuario.tipo_tarea}
📍 <b>Ubicación:</b> {usuario.ubicacion}
⏱️ <b>Tiempo Bloqueado:</b> {usuario.tiempo_bloqueado_minutos} min

📝 <b>Motivo:</b> {usuario.motivo_bloqueo}
⏰ <b>Fecha/Hora:</b> {timestamp}

━━━━━━━━━━━━━━━━━━━━━
🤖 <i>Sistema SAC - Habilitación Automática</i>
"""
                self.notificador_telegram.enviar_mensaje(mensaje)
            except Exception as e:
                logger.error(f"❌ Error enviando a Telegram: {e}")

        # WhatsApp
        if self.notificador_whatsapp:
            try:
                self.notificador_whatsapp.enviar_habilitacion(usuario, resultado)
            except Exception as e:
                logger.error(f"❌ Error enviando a WhatsApp: {e}")

    def _notificar_inicio_servicio(self) -> None:
        """Notifica el inicio del servicio por todos los canales"""
        logger.info("📢 Notificando inicio del servicio...")

        # Telegram
        if self.notificador_telegram:
            try:
                timestamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
                mensaje = f"""
🚀 <b>SERVICIO DE HABILITACIÓN INICIADO</b>

🏢 <b>CEDIS:</b> {self.notificador_telegram.cedis_name}
⏰ <b>Inicio:</b> {timestamp}
📅 <b>Horario:</b> {self.config['hora_inicio']}:00 - {self.config['hora_fin']}:00

✅ Monitoreo de usuarios activo
✅ Habilitación automática activa
✅ Notificaciones configuradas

━━━━━━━━━━━━━━━━━━━━━
🤖 <i>Sistema SAC v1.0.0</i>
"""
                self.notificador_telegram.enviar_mensaje(mensaje)
            except Exception as e:
                logger.error(f"❌ Error notificando inicio a Telegram: {e}")

        # WhatsApp
        if self.notificador_whatsapp:
            try:
                self.notificador_whatsapp.enviar_inicio_servicio()
            except Exception as e:
                logger.error(f"❌ Error notificando inicio a WhatsApp: {e}")

    def _notificar_fin_servicio(self) -> None:
        """Notifica el fin del servicio con resumen del día"""
        logger.info("📢 Notificando fin del servicio...")

        # Telegram
        if self.notificador_telegram:
            try:
                timestamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
                mensaje = f"""
😴 <b>SERVICIO DE HABILITACIÓN FINALIZADO</b>

🏢 <b>CEDIS:</b> {self.notificador_telegram.cedis_name}
⏰ <b>Fin:</b> {timestamp}

━━━━━━━━━━━━━━━━━━━━━
📊 <b>RESUMEN DEL DÍA</b>
━━━━━━━━━━━━━━━━━━━━━
👥 Usuarios habilitados: <b>{self.estadisticas.usuarios_habilitados_hoy}</b>
❌ Errores: <b>{self.estadisticas.errores_hoy}</b>

━━━━━━━━━━━━━━━━━━━━━
🌙 <i>Sistema entrando en modo dormitorio</i>
🤖 <i>Sistema SAC v1.0.0</i>
"""
                self.notificador_telegram.enviar_mensaje(mensaje)
            except Exception as e:
                logger.error(f"❌ Error notificando fin a Telegram: {e}")

        # WhatsApp
        if self.notificador_whatsapp:
            try:
                self.notificador_whatsapp.enviar_fin_servicio(self.estadisticas)
            except Exception as e:
                logger.error(f"❌ Error notificando fin a WhatsApp: {e}")

    def _resetear_estadisticas_diarias(self) -> None:
        """Resetea las estadísticas diarias"""
        self.estadisticas.usuarios_habilitados_hoy = 0
        self.estadisticas.errores_hoy = 0
        self._usuarios_habilitados_sesion.clear()
        self._habilitaciones_hora.clear()
        logger.info("📊 Estadísticas diarias reseteadas")

    def _ciclo_monitoreo(self) -> None:
        """
        Ciclo principal de monitoreo
        Se ejecuta mientras el servicio esté activo
        """
        ultimo_estado_horario = None

        while self._running:
            try:
                en_horario = self._esta_en_horario_operacion()

                # Detectar cambio de estado (entrada/salida de horario)
                if ultimo_estado_horario is not None and en_horario != ultimo_estado_horario:
                    if en_horario:
                        # Entrando en horario de operación
                        logger.info("🌅 Entrando en horario de operación")
                        self._resetear_estadisticas_diarias()
                        self._notificar_inicio_servicio()
                        self.estadisticas.estado = EstadoServicio.ACTIVO
                    else:
                        # Saliendo del horario de operación
                        logger.info("🌙 Saliendo del horario de operación")
                        self._notificar_fin_servicio()
                        self._desconectar_db()
                        self.estadisticas.estado = EstadoServicio.DORMIDO

                ultimo_estado_horario = en_horario

                if en_horario:
                    # Modo activo: monitorear y habilitar
                    self.estadisticas.estado = EstadoServicio.ACTIVO
                    self.estadisticas.ultimo_chequeo = datetime.now()

                    # Detectar usuarios bloqueados
                    usuarios_bloqueados = self.detectar_usuarios_bloqueados()

                    # Habilitar cada usuario detectado
                    for usuario in usuarios_bloqueados:
                        resultado = self.habilitar_usuario(usuario)

                        # Notificar (solo si fue exitoso o si hubo error importante)
                        if resultado.exitoso or "Error" in resultado.mensaje:
                            self._notificar_habilitacion(usuario, resultado)

                        # Pequeña pausa entre habilitaciones
                        time.sleep(0.5)

                    # Esperar intervalo normal
                    intervalo = self.config.get('intervalo_chequeo_segundos', 30)

                else:
                    # Modo dormitorio: esperar con intervalo largo
                    self.estadisticas.estado = EstadoServicio.DORMIDO
                    intervalo = self.config.get('intervalo_dormitorio_segundos', 300)

                # Esperar el intervalo correspondiente
                for _ in range(intervalo):
                    if not self._running:
                        break
                    time.sleep(1)

            except Exception as e:
                logger.error(f"❌ Error en ciclo de monitoreo: {str(e)}")
                self.estadisticas.estado = EstadoServicio.ERROR
                self.estadisticas.errores_hoy += 1
                time.sleep(60)  # Esperar un minuto antes de reintentar

    def iniciar(self, en_segundo_plano: bool = True) -> bool:
        """
        Inicia el servicio de habilitación

        Args:
            en_segundo_plano: Si True, ejecuta en hilo separado

        Returns:
            True si inició correctamente
        """
        if self._running:
            logger.warning("⚠️ El servicio ya está en ejecución")
            return False

        if not self.config.get('enabled', True):
            logger.warning("⚠️ El servicio está deshabilitado en la configuración")
            return False

        logger.info("🚀 Iniciando servicio de habilitación de usuarios...")

        self._running = True
        self.estadisticas.inicio_servicio = datetime.now()

        # Verificar si estamos en horario y notificar
        if self._esta_en_horario_operacion():
            self._notificar_inicio_servicio()
            self.estadisticas.estado = EstadoServicio.ACTIVO
        else:
            self.estadisticas.estado = EstadoServicio.DORMIDO
            logger.info("😴 Fuera de horario de operación - iniciando en modo dormitorio")

        if en_segundo_plano:
            self._thread = threading.Thread(
                target=self._ciclo_monitoreo,
                daemon=True,
                name="ServicioHabilitacion"
            )
            self._thread.start()
            logger.info("✅ Servicio iniciado en segundo plano")
        else:
            logger.info("✅ Servicio iniciado en primer plano")
            self._ciclo_monitoreo()

        return True

    def detener(self) -> None:
        """Detiene el servicio de habilitación"""
        logger.info("🛑 Deteniendo servicio de habilitación...")

        self._running = False

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=10)

        # Notificar fin si estábamos en horario
        if self.estadisticas.estado == EstadoServicio.ACTIVO:
            self._notificar_fin_servicio()

        self._desconectar_db()
        self.estadisticas.estado = EstadoServicio.DETENIDO

        logger.info("✅ Servicio detenido")

    def obtener_estadisticas(self) -> Dict:
        """
        Obtiene las estadísticas actuales del servicio

        Returns:
            Diccionario con estadísticas
        """
        return {
            'estado': self.estadisticas.estado.value,
            'inicio_servicio': str(self.estadisticas.inicio_servicio),
            'usuarios_habilitados_hoy': self.estadisticas.usuarios_habilitados_hoy,
            'usuarios_habilitados_total': self.estadisticas.usuarios_habilitados_total,
            'errores_hoy': self.estadisticas.errores_hoy,
            'ultimo_chequeo': str(self.estadisticas.ultimo_chequeo) if self.estadisticas.ultimo_chequeo else None,
            'ultima_habilitacion': str(self.estadisticas.ultima_habilitacion) if self.estadisticas.ultima_habilitacion else None,
            'en_horario_operacion': self._esta_en_horario_operacion(),
            'configuracion': {
                'hora_inicio': self.config.get('hora_inicio'),
                'hora_fin': self.config.get('hora_fin'),
                'intervalo_segundos': self.config.get('intervalo_chequeo_segundos'),
                'telegram_habilitado': self.notificador_telegram is not None,
                'whatsapp_habilitado': self.notificador_whatsapp is not None and self.notificador_whatsapp.enabled
            }
        }

    def forzar_chequeo(self) -> List[ResultadoHabilitacion]:
        """
        Fuerza un chequeo inmediato (útil para pruebas)

        Returns:
            Lista de resultados de habilitación
        """
        logger.info("🔍 Forzando chequeo de usuarios bloqueados...")

        resultados = []
        usuarios_bloqueados = self.detectar_usuarios_bloqueados()

        for usuario in usuarios_bloqueados:
            resultado = self.habilitar_usuario(usuario)
            resultados.append(resultado)

            if resultado.exitoso:
                self._notificar_habilitacion(usuario, resultado)

        return resultados


# ═══════════════════════════════════════════════════════════════
# FUNCIONES DE UTILIDAD
# ═══════════════════════════════════════════════════════════════

def crear_servicio_desde_config() -> Optional[ServicioHabilitacionUsuarios]:
    """
    Crea un servicio de habilitación usando la configuración del sistema

    Returns:
        Servicio configurado o None si falla
    """
    try:
        return ServicioHabilitacionUsuarios(HABILITACION_CONFIG)
    except Exception as e:
        logger.error(f"❌ Error creando servicio: {str(e)}")
        return None


def verificar_configuracion() -> Dict:
    """
    Verifica la configuración del módulo de habilitación

    Returns:
        Diccionario con estado de la configuración
    """
    config_status = {
        'habilitacion_enabled': HABILITACION_CONFIG.get('enabled', False),
        'db_configured': bool(DB_CONFIG.get('user') and DB_CONFIG.get('password')),
        'telegram_configured': bool(TELEGRAM_CONFIG.get('bot_token')),
        'whatsapp_configured': bool(
            HABILITACION_CONFIG.get('whatsapp_api_url') and
            HABILITACION_CONFIG.get('whatsapp_api_token')
        ),
        'horario': f"{HABILITACION_CONFIG.get('hora_inicio', 6)}:00 - {HABILITACION_CONFIG.get('hora_fin', 18)}:00",
        'timezone': HABILITACION_CONFIG.get('timezone', 'America/Cancun'),
        'pytz_available': PYTZ_AVAILABLE
    }

    return config_status


# ═══════════════════════════════════════════════════════════════
# MANEJADOR DE SEÑALES
# ═══════════════════════════════════════════════════════════════

_servicio_global: Optional[ServicioHabilitacionUsuarios] = None

def _manejador_señal(signum, frame):
    """Manejador de señales para detener el servicio graciosamente"""
    global _servicio_global

    logger.info(f"🛑 Señal recibida ({signum}), deteniendo servicio...")

    if _servicio_global:
        _servicio_global.detener()

    sys.exit(0)


# ═══════════════════════════════════════════════════════════════
# EJECUCIÓN PRINCIPAL
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    print("\n" + "="*60)
    print("🔧 MÓDULO DE HABILITACIÓN AUTOMÁTICA DE USUARIOS")
    print("   Sistema SAC - CEDIS Cancún 427")
    print("="*60)

    # Verificar configuración
    config_status = verificar_configuracion()

    print("\n📋 Estado de Configuración:")
    print(f"   • Habilitación: {'✅ Activo' if config_status['habilitacion_enabled'] else '❌ Inactivo'}")
    print(f"   • Base de Datos: {'✅ Configurada' if config_status['db_configured'] else '❌ Sin configurar'}")
    print(f"   • Telegram: {'✅ Configurado' if config_status['telegram_configured'] else '⚠️ Sin configurar'}")
    print(f"   • WhatsApp: {'✅ Configurado' if config_status['whatsapp_configured'] else '⚠️ Sin configurar'}")
    print(f"   • Horario: {config_status['horario']}")
    print(f"   • Zona Horaria: {config_status['timezone']}")
    print(f"   • pytz: {'✅ Disponible' if config_status['pytz_available'] else '⚠️ No disponible'}")

    print("\n" + "="*60)
    print("💡 Uso:")
    print("   from modules.modulo_habilitacion_usuarios import ServicioHabilitacionUsuarios")
    print("   ")
    print("   servicio = ServicioHabilitacionUsuarios()")
    print("   servicio.iniciar()  # Inicia en segundo plano")
    print("   ")
    print("   # Para detener:")
    print("   servicio.detener()")
    print("="*60)

    # Preguntar si iniciar el servicio
    respuesta = input("\n¿Iniciar servicio de habilitación? (s/n): ").strip().lower()

    if respuesta == 's':
        # Registrar manejador de señales
        signal.signal(signal.SIGINT, _manejador_señal)
        signal.signal(signal.SIGTERM, _manejador_señal)

        # Crear e iniciar servicio
        _servicio_global = ServicioHabilitacionUsuarios()

        print("\n🚀 Iniciando servicio...")
        print("   Presiona Ctrl+C para detener\n")

        # Iniciar en primer plano para pruebas
        _servicio_global.iniciar(en_segundo_plano=False)
    else:
        print("\n✅ Módulo cargado. Usa las clases para implementar el servicio.")
