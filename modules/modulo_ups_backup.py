"""
═══════════════════════════════════════════════════════════════
MÓDULO UPS - SISTEMA DE RESPALDO ENERGÉTICO Y CONTINUIDAD
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Este módulo actúa como un UPS (Uninterruptible Power Supply) digital
para mantener la operación del sistema durante:
- Mantenimientos programados de Manhattan WMS
- Pérdida de conexión a la base de datos DB2
- Fallos temporales de red o servidor

Funcionalidades:
- Detección automática de pérdida de conexión
- Caché inteligente de datos críticos
- Almacenamiento de operaciones pendientes (modo offline)
- Cola de DMLs para sincronización posterior
- Autorización obligatoria para sincronización a Manhattan
- DMLs predefinidos seguros y plantillas para analistas
- Validación de integridad antes de reinserción

Uso:
    from modules.modulo_ups_backup import (
        UPSBackup, get_ups_backup,
        ModoOperacion, EstadoUPS,
        OperacionDML, PlantillaDML
    )

    # Obtener instancia
    ups = get_ups_backup()

    # Verificar estado
    if ups.estado == EstadoUPS.OFFLINE:
        # Trabajar en modo offline
        ups.registrar_operacion_pendiente(...)

    # Cuando Manhattan vuelva
    ops_pendientes = ups.obtener_operaciones_pendientes()
    ups.sincronizar_con_autorizacion(analista="ADMJAJA")

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
═══════════════════════════════════════════════════════════════
"""

import logging
import json
import hashlib
import sqlite3
import threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Tuple, Callable
from dataclasses import dataclass, field, asdict
from contextlib import contextmanager
from enum import Enum
from abc import ABC, abstractmethod
import time
import pandas as pd

# Importar módulos locales
from .db_local import DBLocal, get_db_local, TipoOperacion, NivelConfirmacion
from .db_connection import DB2Connection, DB2ConnectionError, DB2QueryError

# Configurar logger
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# ENUMERACIONES Y CONSTANTES
# ═══════════════════════════════════════════════════════════════

class EstadoUPS(Enum):
    """Estados del sistema UPS"""
    ONLINE = "online"              # Conexión normal a Manhattan
    OFFLINE = "offline"            # Sin conexión, usando respaldo
    SINCRONIZANDO = "sincronizando"  # Reconectando y sincronizando
    MANTENIMIENTO = "mantenimiento"  # Modo mantenimiento programado
    ERROR = "error"                # Error crítico
    INICIANDO = "iniciando"        # Inicializando sistema


class ModoOperacion(Enum):
    """Modos de operación del sistema"""
    NORMAL = "normal"              # Operación normal con Manhattan
    SOLO_LECTURA = "solo_lectura"  # Solo consultas, sin escrituras
    RESPALDO = "respaldo"          # Usando datos de respaldo local
    EMERGENCIA = "emergencia"      # Modo emergencia - datos mínimos


class TipoOperacionDML(Enum):
    """Tipos de operaciones DML"""
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    UPSERT = "UPSERT"              # INSERT o UPDATE según exista


class NivelRiesgo(Enum):
    """Niveles de riesgo para operaciones"""
    BAJO = 1       # Operaciones seguras, auto-aprobables
    MEDIO = 2      # Requiere confirmación simple
    ALTO = 3       # Requiere autorización de analista
    CRITICO = 4    # Requiere doble autorización + código


class EstadoOperacion(Enum):
    """Estados de una operación pendiente"""
    PENDIENTE = "pendiente"
    VALIDADA = "validada"
    AUTORIZADA = "autorizada"
    EJECUTANDO = "ejecutando"
    COMPLETADA = "completada"
    FALLIDA = "fallida"
    RECHAZADA = "rechazada"
    EXPIRADA = "expirada"


# ═══════════════════════════════════════════════════════════════
# DATA CLASSES
# ═══════════════════════════════════════════════════════════════

@dataclass
class OperacionDML:
    """
    Representa una operación DML pendiente de ejecutar en Manhattan.

    Cada operación se valida y requiere autorización antes de ejecutarse
    cuando la conexión se restablezca.
    """
    id: Optional[int] = None
    tipo: str = TipoOperacionDML.INSERT.value
    tabla: str = ""
    schema: str = "WMWHSE1"
    sql: str = ""
    parametros: str = "[]"  # JSON serializado
    datos_antes: str = "{}"  # Para UPDATE/DELETE
    datos_despues: str = "{}"  # Para INSERT/UPDATE
    condicion_where: str = ""
    nivel_riesgo: int = NivelRiesgo.MEDIO.value
    estado: str = EstadoOperacion.PENDIENTE.value

    # Metadata
    creado_en: datetime = field(default_factory=datetime.now)
    creado_por: str = "SISTEMA"
    descripcion: str = ""
    justificacion: str = ""

    # Validación y autorización
    validado: bool = False
    validado_por: Optional[str] = None
    validado_en: Optional[datetime] = None
    autorizado: bool = False
    autorizado_por: Optional[str] = None
    autorizado_en: Optional[datetime] = None
    codigo_autorizacion: Optional[str] = None

    # Ejecución
    ejecutado_en: Optional[datetime] = None
    resultado: Optional[str] = None
    filas_afectadas: int = 0
    error: Optional[str] = None
    intentos: int = 0
    max_intentos: int = 3


@dataclass
class PlantillaDML:
    """
    Plantilla predefinida para operaciones DML comunes.

    Las plantillas seguras pueden ser ejecutadas automáticamente,
    las complejas requieren que el analista complete los parámetros.
    """
    id: str = ""
    nombre: str = ""
    descripcion: str = ""
    tipo: str = TipoOperacionDML.UPDATE.value
    tabla: str = ""
    schema: str = "WMWHSE1"
    sql_template: str = ""
    parametros_requeridos: str = "[]"  # JSON: lista de nombres de parámetros
    valores_default: str = "{}"  # JSON: valores por defecto
    nivel_riesgo: int = NivelRiesgo.MEDIO.value
    auto_aprobable: bool = False  # True si es segura para auto-aprobar
    requiere_validacion_manual: bool = True
    activa: bool = True
    categoria: str = "general"


@dataclass
class SnapshotDatos:
    """
    Snapshot de datos críticos para operación offline.
    """
    id: Optional[int] = None
    nombre: str = ""
    tabla_origen: str = ""
    query_origen: str = ""
    datos_json: str = "[]"
    registros: int = 0
    hash_datos: str = ""
    creado_en: datetime = field(default_factory=datetime.now)
    expira_en: Optional[datetime] = None
    version: int = 1
    es_critico: bool = False


@dataclass
class EventoUPS:
    """Evento del sistema UPS para logging/auditoría"""
    id: Optional[int] = None
    tipo: str = ""
    mensaje: str = ""
    detalles: str = "{}"
    timestamp: datetime = field(default_factory=datetime.now)
    usuario: str = "SISTEMA"
    estado_anterior: str = ""
    estado_nuevo: str = ""


# ═══════════════════════════════════════════════════════════════
# PLANTILLAS DML PREDEFINIDAS
# ═══════════════════════════════════════════════════════════════

PLANTILLAS_PREDEFINIDAS: List[PlantillaDML] = [
    # === PLANTILLAS DE BAJO RIESGO (Auto-aprobables) ===
    PlantillaDML(
        id="TPL_001",
        nombre="Actualizar estado de recepción ASN",
        descripcion="Actualiza el estado de una recepción ASN a completado",
        tipo=TipoOperacionDML.UPDATE.value,
        tabla="ASN",
        sql_template="""
            UPDATE {schema}.ASN
            SET STATUS = '9',
                EDITDATE = CURRENT_TIMESTAMP,
                EDITWHO = '{usuario}'
            WHERE ASNKEY = '{asnkey}'
              AND WHSEID = '{whseid}'
        """,
        parametros_requeridos='["asnkey", "whseid", "usuario"]',
        valores_default='{"whseid": "WM260BASD"}',
        nivel_riesgo=NivelRiesgo.BAJO.value,
        auto_aprobable=True,
        requiere_validacion_manual=False,
        categoria="recepciones"
    ),
    PlantillaDML(
        id="TPL_002",
        nombre="Actualizar ubicación de LPN",
        descripcion="Mueve un LPN a una nueva ubicación (putaway)",
        tipo=TipoOperacionDML.UPDATE.value,
        tabla="LPNDETAIL",
        sql_template="""
            UPDATE {schema}.LPNDETAIL
            SET LOC = '{nueva_ubicacion}',
                EDITDATE = CURRENT_TIMESTAMP,
                EDITWHO = '{usuario}'
            WHERE LPNKEY = '{lpnkey}'
        """,
        parametros_requeridos='["lpnkey", "nueva_ubicacion", "usuario"]',
        nivel_riesgo=NivelRiesgo.BAJO.value,
        auto_aprobable=True,
        requiere_validacion_manual=False,
        categoria="ubicaciones"
    ),

    # === PLANTILLAS DE RIESGO MEDIO (Requieren confirmación) ===
    PlantillaDML(
        id="TPL_003",
        nombre="Ajustar inventario por conteo",
        descripcion="Ajusta la cantidad de inventario después de un conteo físico",
        tipo=TipoOperacionDML.UPDATE.value,
        tabla="LOTXLOCXID",
        sql_template="""
            UPDATE {schema}.LOTXLOCXID
            SET QTY = {nueva_cantidad},
                EDITDATE = CURRENT_TIMESTAMP,
                EDITWHO = '{usuario}'
            WHERE LOC = '{ubicacion}'
              AND SKU = '{sku}'
              AND LOT = '{lote}'
              AND ID = '{id_inventario}'
        """,
        parametros_requeridos='["ubicacion", "sku", "lote", "id_inventario", "nueva_cantidad", "usuario"]',
        nivel_riesgo=NivelRiesgo.MEDIO.value,
        auto_aprobable=False,
        requiere_validacion_manual=True,
        categoria="inventario"
    ),
    PlantillaDML(
        id="TPL_004",
        nombre="Cerrar orden de compra",
        descripcion="Cierra una OC y actualiza su estado a completado",
        tipo=TipoOperacionDML.UPDATE.value,
        tabla="RECEIPTDETAIL",
        sql_template="""
            UPDATE {schema}.RECEIPTDETAIL
            SET STATUS = 'C',
                CLOSEDDATE = CURRENT_DATE,
                EDITDATE = CURRENT_TIMESTAMP,
                EDITWHO = '{usuario}'
            WHERE RECEIPTKEY = '{receiptkey}'
        """,
        parametros_requeridos='["receiptkey", "usuario"]',
        nivel_riesgo=NivelRiesgo.MEDIO.value,
        auto_aprobable=False,
        requiere_validacion_manual=True,
        categoria="ordenes"
    ),

    # === PLANTILLAS DE ALTO RIESGO (Requieren autorización) ===
    PlantillaDML(
        id="TPL_005",
        nombre="Eliminar LPN vacío",
        descripcion="Elimina un LPN que ya no tiene contenido",
        tipo=TipoOperacionDML.DELETE.value,
        tabla="LPN",
        sql_template="""
            DELETE FROM {schema}.LPN
            WHERE LPNKEY = '{lpnkey}'
              AND NOT EXISTS (
                  SELECT 1 FROM {schema}.LPNDETAIL
                  WHERE LPNKEY = '{lpnkey}' AND QTY > 0
              )
        """,
        parametros_requeridos='["lpnkey"]',
        nivel_riesgo=NivelRiesgo.ALTO.value,
        auto_aprobable=False,
        requiere_validacion_manual=True,
        categoria="lpn"
    ),
    PlantillaDML(
        id="TPL_006",
        nombre="Reversar recepción",
        descripcion="Revierte una recepción parcial o completa",
        tipo=TipoOperacionDML.UPDATE.value,
        tabla="RECEIPTDETAIL",
        sql_template="""
            UPDATE {schema}.RECEIPTDETAIL
            SET QTYRECEIVED = QTYRECEIVED - {cantidad_reversar},
                STATUS = CASE WHEN QTYRECEIVED - {cantidad_reversar} <= 0 THEN 'N' ELSE STATUS END,
                EDITDATE = CURRENT_TIMESTAMP,
                EDITWHO = '{usuario}'
            WHERE RECEIPTKEY = '{receiptkey}'
              AND RECEIPTLINENUMBER = '{linea}'
              AND QTYRECEIVED >= {cantidad_reversar}
        """,
        parametros_requeridos='["receiptkey", "linea", "cantidad_reversar", "usuario"]',
        nivel_riesgo=NivelRiesgo.ALTO.value,
        auto_aprobable=False,
        requiere_validacion_manual=True,
        categoria="recepciones"
    ),

    # === PLANTILLAS CRÍTICAS (Requieren doble autorización) ===
    PlantillaDML(
        id="TPL_007",
        nombre="Eliminar distribución errónea",
        descripcion="Elimina una línea de distribución que fue creada por error",
        tipo=TipoOperacionDML.DELETE.value,
        tabla="ORDERDETAIL",
        sql_template="""
            -- OPERACIÓN CRÍTICA: Eliminar distribución
            -- Requiere autorización de Jefe de Sistemas
            DELETE FROM {schema}.ORDERDETAIL
            WHERE ORDERKEY = '{orderkey}'
              AND ORDERLINENUMBER = '{linea}'
              AND STATUS = '0'  -- Solo si no está en proceso
        """,
        parametros_requeridos='["orderkey", "linea"]',
        nivel_riesgo=NivelRiesgo.CRITICO.value,
        auto_aprobable=False,
        requiere_validacion_manual=True,
        categoria="distribuciones"
    ),
    PlantillaDML(
        id="TPL_008",
        nombre="Purgar histórico antiguo",
        descripcion="Elimina registros históricos anteriores a fecha especificada",
        tipo=TipoOperacionDML.DELETE.value,
        tabla="TRANSACTIONLOG",
        sql_template="""
            -- OPERACIÓN CRÍTICA: Purga de histórico
            -- Esto NO puede deshacerse
            DELETE FROM {schema}.TRANSACTIONLOG
            WHERE ADDDATE < '{fecha_corte}'
              AND TRANSACTIONTYPE IN ('INFO', 'DEBUG')
        """,
        parametros_requeridos='["fecha_corte"]',
        nivel_riesgo=NivelRiesgo.CRITICO.value,
        auto_aprobable=False,
        requiere_validacion_manual=True,
        categoria="mantenimiento"
    ),
]

# Códigos de autorización para operaciones críticas
CODIGOS_AUTORIZACION = {
    NivelRiesgo.ALTO: "AUTH-SAC-427",
    NivelRiesgo.CRITICO: "AUTH-CRITICO-CEDIS427-CONFIRMAR",
}


# ═══════════════════════════════════════════════════════════════
# CLASE PRINCIPAL UPS BACKUP
# ═══════════════════════════════════════════════════════════════

class UPSBackup:
    """
    Sistema UPS de Respaldo Energético para Manhattan WMS.

    Actúa como intermediario entre la aplicación y Manhattan,
    manteniendo la operación durante interrupciones de servicio.

    Características:
    - Detección automática de fallos de conexión
    - Caché de datos críticos actualizado
    - Cola de operaciones pendientes
    - Sincronización controlada con autorización
    - DMLs predefinidos y plantillas seguras
    - Auditoría completa de operaciones

    Ejemplo:
        >>> ups = UPSBackup()
        >>>
        >>> # Verificar estado
        >>> if ups.esta_online():
        ...     # Operación normal
        ...     datos = ups.obtener_datos_tabla("ORDERS")
        ... else:
        ...     # Usar datos de respaldo
        ...     datos = ups.obtener_datos_respaldo("ORDERS")
        ...     # Registrar operación para después
        ...     ups.registrar_operacion_pendiente(...)
        >>>
        >>> # Sincronizar cuando Manhattan vuelva
        >>> if ups.verificar_conexion_manhattan():
        ...     resultado = ups.sincronizar_con_autorizacion(
        ...         analista="ADMJAJA",
        ...         codigo="AUTH-SAC-427"
        ...     )
    """

    # Constantes
    TABLA_OPERACIONES = "ups_operaciones_pendientes"
    TABLA_SNAPSHOTS = "ups_snapshots_datos"
    TABLA_PLANTILLAS = "ups_plantillas_dml"
    TABLA_EVENTOS = "ups_eventos"
    TABLA_CONFIG = "ups_configuracion"

    # Intervalo de health check (segundos)
    HEALTH_CHECK_INTERVAL = 30

    # TTL default para snapshots (minutos)
    DEFAULT_SNAPSHOT_TTL = 60

    def __init__(
        self,
        db_local: Optional[DBLocal] = None,
        db2_config: Optional[Dict] = None,
        auto_start: bool = True,
        health_check_enabled: bool = True
    ):
        """
        Inicializa el sistema UPS de respaldo.

        Args:
            db_local: Instancia de base de datos local
            db2_config: Configuración de conexión a DB2
            auto_start: Iniciar monitoreo automático
            health_check_enabled: Habilitar verificación periódica
        """
        self.db_local = db_local or get_db_local()
        self.db2_config = db2_config
        self._db2_connection: Optional[DB2Connection] = None

        # Estado del sistema
        self._estado = EstadoUPS.INICIANDO
        self._modo_operacion = ModoOperacion.NORMAL
        self._ultimo_health_check: Optional[datetime] = None
        self._ultima_sincronizacion: Optional[datetime] = None
        self._errores_consecutivos = 0
        self._max_errores_offline = 3

        # Threading para health check
        self._health_check_enabled = health_check_enabled
        self._health_check_thread: Optional[threading.Thread] = None
        self._stop_health_check = threading.Event()
        self._lock = threading.Lock()

        # Inicializar tablas
        self._inicializar_tablas()

        # Cargar plantillas predefinidas
        self._cargar_plantillas_predefinidas()

        logger.info("🔋 UPS Backup inicializado")

        # Verificar conexión inicial
        if auto_start:
            self._verificar_estado_inicial()
            if health_check_enabled:
                self._iniciar_health_check()

    # ═══════════════════════════════════════════════════════════════
    # INICIALIZACIÓN Y CONFIGURACIÓN
    # ═══════════════════════════════════════════════════════════════

    def _inicializar_tablas(self):
        """Crea las tablas necesarias para el sistema UPS."""
        with self.db_local._get_connection() as conn:
            cursor = conn.cursor()

            # Tabla de operaciones pendientes
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.TABLA_OPERACIONES} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo TEXT NOT NULL,
                    tabla TEXT NOT NULL,
                    schema TEXT DEFAULT 'WMWHSE1',
                    sql TEXT NOT NULL,
                    parametros TEXT DEFAULT '[]',
                    datos_antes TEXT DEFAULT '{{}}',
                    datos_despues TEXT DEFAULT '{{}}',
                    condicion_where TEXT,
                    nivel_riesgo INTEGER DEFAULT 2,
                    estado TEXT DEFAULT 'pendiente',

                    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    creado_por TEXT DEFAULT 'SISTEMA',
                    descripcion TEXT,
                    justificacion TEXT,

                    validado INTEGER DEFAULT 0,
                    validado_por TEXT,
                    validado_en TIMESTAMP,
                    autorizado INTEGER DEFAULT 0,
                    autorizado_por TEXT,
                    autorizado_en TIMESTAMP,
                    codigo_autorizacion TEXT,

                    ejecutado_en TIMESTAMP,
                    resultado TEXT,
                    filas_afectadas INTEGER DEFAULT 0,
                    error TEXT,
                    intentos INTEGER DEFAULT 0,
                    max_intentos INTEGER DEFAULT 3
                )
            """)

            # Tabla de snapshots de datos
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.TABLA_SNAPSHOTS} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    tabla_origen TEXT NOT NULL,
                    query_origen TEXT,
                    datos_json TEXT NOT NULL,
                    registros INTEGER DEFAULT 0,
                    hash_datos TEXT,
                    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expira_en TIMESTAMP,
                    version INTEGER DEFAULT 1,
                    es_critico INTEGER DEFAULT 0
                )
            """)

            # Tabla de plantillas DML
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.TABLA_PLANTILLAS} (
                    id TEXT PRIMARY KEY,
                    nombre TEXT NOT NULL,
                    descripcion TEXT,
                    tipo TEXT NOT NULL,
                    tabla TEXT NOT NULL,
                    schema TEXT DEFAULT 'WMWHSE1',
                    sql_template TEXT NOT NULL,
                    parametros_requeridos TEXT DEFAULT '[]',
                    valores_default TEXT DEFAULT '{{}}',
                    nivel_riesgo INTEGER DEFAULT 2,
                    auto_aprobable INTEGER DEFAULT 0,
                    requiere_validacion_manual INTEGER DEFAULT 1,
                    activa INTEGER DEFAULT 1,
                    categoria TEXT DEFAULT 'general'
                )
            """)

            # Tabla de eventos
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.TABLA_EVENTOS} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo TEXT NOT NULL,
                    mensaje TEXT,
                    detalles TEXT DEFAULT '{{}}',
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    usuario TEXT DEFAULT 'SISTEMA',
                    estado_anterior TEXT,
                    estado_nuevo TEXT
                )
            """)

            # Tabla de configuración
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.TABLA_CONFIG} (
                    clave TEXT PRIMARY KEY,
                    valor TEXT,
                    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Índices
            cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_ops_estado ON {self.TABLA_OPERACIONES}(estado)")
            cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_ops_nivel ON {self.TABLA_OPERACIONES}(nivel_riesgo)")
            cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_snap_tabla ON {self.TABLA_SNAPSHOTS}(tabla_origen)")
            cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_eventos_tipo ON {self.TABLA_EVENTOS}(tipo)")

            logger.info("✅ Tablas UPS inicializadas")

    def _cargar_plantillas_predefinidas(self):
        """Carga las plantillas DML predefinidas en la base de datos."""
        with self.db_local._get_connection() as conn:
            cursor = conn.cursor()

            for plantilla in PLANTILLAS_PREDEFINIDAS:
                cursor.execute(f"""
                    INSERT OR REPLACE INTO {self.TABLA_PLANTILLAS}
                    (id, nombre, descripcion, tipo, tabla, schema, sql_template,
                     parametros_requeridos, valores_default, nivel_riesgo,
                     auto_aprobable, requiere_validacion_manual, activa, categoria)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    plantilla.id,
                    plantilla.nombre,
                    plantilla.descripcion,
                    plantilla.tipo,
                    plantilla.tabla,
                    plantilla.schema,
                    plantilla.sql_template,
                    plantilla.parametros_requeridos,
                    plantilla.valores_default,
                    plantilla.nivel_riesgo,
                    1 if plantilla.auto_aprobable else 0,
                    1 if plantilla.requiere_validacion_manual else 0,
                    1 if plantilla.activa else 0,
                    plantilla.categoria
                ))

            logger.info(f"✅ {len(PLANTILLAS_PREDEFINIDAS)} plantillas DML cargadas")

    def _verificar_estado_inicial(self):
        """Verifica el estado inicial de conexión a Manhattan."""
        if self.verificar_conexion_manhattan():
            self._cambiar_estado(EstadoUPS.ONLINE)
            self._modo_operacion = ModoOperacion.NORMAL
            logger.info("🟢 UPS: Conexión a Manhattan establecida - Modo ONLINE")
        else:
            self._cambiar_estado(EstadoUPS.OFFLINE)
            self._modo_operacion = ModoOperacion.RESPALDO
            logger.warning("🔴 UPS: Sin conexión a Manhattan - Modo OFFLINE (usando respaldo)")

    # ═══════════════════════════════════════════════════════════════
    # PROPIEDADES Y ESTADO
    # ═══════════════════════════════════════════════════════════════

    @property
    def estado(self) -> EstadoUPS:
        """Estado actual del sistema UPS."""
        return self._estado

    @property
    def modo_operacion(self) -> ModoOperacion:
        """Modo de operación actual."""
        return self._modo_operacion

    def esta_online(self) -> bool:
        """Verifica si el sistema está online (conectado a Manhattan)."""
        return self._estado == EstadoUPS.ONLINE

    def esta_offline(self) -> bool:
        """Verifica si el sistema está offline (usando respaldo)."""
        return self._estado in [EstadoUPS.OFFLINE, EstadoUPS.MANTENIMIENTO]

    def _cambiar_estado(self, nuevo_estado: EstadoUPS, motivo: str = ""):
        """Cambia el estado del sistema y registra el evento."""
        estado_anterior = self._estado
        self._estado = nuevo_estado

        self._registrar_evento(
            tipo="CAMBIO_ESTADO",
            mensaje=f"Estado cambiado: {estado_anterior.value} -> {nuevo_estado.value}",
            detalles={"motivo": motivo},
            estado_anterior=estado_anterior.value,
            estado_nuevo=nuevo_estado.value
        )

        # Notificar cambio crítico
        if nuevo_estado == EstadoUPS.OFFLINE and estado_anterior == EstadoUPS.ONLINE:
            logger.warning(f"🔴 UPS: Sistema cambiado a OFFLINE - {motivo}")
        elif nuevo_estado == EstadoUPS.ONLINE and estado_anterior != EstadoUPS.ONLINE:
            logger.info(f"🟢 UPS: Sistema restaurado a ONLINE - {motivo}")

    def _registrar_evento(
        self,
        tipo: str,
        mensaje: str,
        detalles: Dict = None,
        usuario: str = "SISTEMA",
        estado_anterior: str = "",
        estado_nuevo: str = ""
    ):
        """Registra un evento en el log del sistema."""
        with self.db_local._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                INSERT INTO {self.TABLA_EVENTOS}
                (tipo, mensaje, detalles, usuario, estado_anterior, estado_nuevo)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                tipo,
                mensaje,
                json.dumps(detalles or {}, default=str),
                usuario,
                estado_anterior,
                estado_nuevo
            ))

    # ═══════════════════════════════════════════════════════════════
    # CONEXIÓN Y HEALTH CHECK
    # ═══════════════════════════════════════════════════════════════

    def verificar_conexion_manhattan(self) -> bool:
        """
        Verifica si hay conexión activa a Manhattan WMS.

        Returns:
            True si la conexión está disponible
        """
        try:
            if self._db2_connection is None:
                self._db2_connection = DB2Connection(config=self.db2_config)

            # Intentar conexión si no está conectado
            if not self._db2_connection.is_connected():
                self._db2_connection.connect()

            # Health check con query simple
            result = self._db2_connection.execute_scalar(
                "SELECT 1 FROM SYSIBM.SYSDUMMY1"
            )

            self._ultimo_health_check = datetime.now()
            self._errores_consecutivos = 0

            return result == 1

        except Exception as e:
            self._errores_consecutivos += 1
            logger.warning(f"⚠️ Health check fallido ({self._errores_consecutivos}): {e}")

            if self._errores_consecutivos >= self._max_errores_offline:
                if self._estado == EstadoUPS.ONLINE:
                    self._cambiar_estado(
                        EstadoUPS.OFFLINE,
                        f"Pérdida de conexión después de {self._errores_consecutivos} intentos"
                    )
                    self._modo_operacion = ModoOperacion.RESPALDO

            return False

    def _iniciar_health_check(self):
        """Inicia el thread de health check periódico."""
        if self._health_check_thread and self._health_check_thread.is_alive():
            return

        self._stop_health_check.clear()
        self._health_check_thread = threading.Thread(
            target=self._health_check_loop,
            daemon=True,
            name="UPS-HealthCheck"
        )
        self._health_check_thread.start()
        logger.info("🔄 Health check iniciado")

    def _health_check_loop(self):
        """Loop principal de health check."""
        while not self._stop_health_check.is_set():
            try:
                with self._lock:
                    conexion_ok = self.verificar_conexion_manhattan()

                    if conexion_ok and self._estado != EstadoUPS.ONLINE:
                        # Conexión restaurada
                        self._cambiar_estado(
                            EstadoUPS.ONLINE,
                            "Conexión restaurada automáticamente"
                        )
                        self._modo_operacion = ModoOperacion.NORMAL

            except Exception as e:
                logger.error(f"❌ Error en health check: {e}")

            # Esperar intervalo
            self._stop_health_check.wait(self.HEALTH_CHECK_INTERVAL)

    def detener_health_check(self):
        """Detiene el thread de health check."""
        self._stop_health_check.set()
        if self._health_check_thread:
            self._health_check_thread.join(timeout=5)
        logger.info("🛑 Health check detenido")

    def activar_modo_mantenimiento(self, duracion_minutos: int = 60, motivo: str = ""):
        """
        Activa el modo mantenimiento programado.

        Args:
            duracion_minutos: Duración estimada del mantenimiento
            motivo: Motivo del mantenimiento
        """
        self._cambiar_estado(
            EstadoUPS.MANTENIMIENTO,
            f"Mantenimiento programado: {motivo} ({duracion_minutos} min)"
        )
        self._modo_operacion = ModoOperacion.RESPALDO

        # Guardar configuración
        self._guardar_config("mantenimiento_inicio", datetime.now().isoformat())
        self._guardar_config("mantenimiento_duracion", str(duracion_minutos))
        self._guardar_config("mantenimiento_motivo", motivo)

        logger.info(f"🔧 Modo mantenimiento activado: {motivo}")

    def desactivar_modo_mantenimiento(self):
        """Desactiva el modo mantenimiento."""
        if self._estado == EstadoUPS.MANTENIMIENTO:
            # Verificar conexión antes de cambiar estado
            if self.verificar_conexion_manhattan():
                self._cambiar_estado(EstadoUPS.ONLINE, "Fin de mantenimiento")
                self._modo_operacion = ModoOperacion.NORMAL
            else:
                self._cambiar_estado(EstadoUPS.OFFLINE, "Fin de mantenimiento (sin conexión)")
                self._modo_operacion = ModoOperacion.RESPALDO

            logger.info("✅ Modo mantenimiento desactivado")

    def _guardar_config(self, clave: str, valor: str):
        """Guarda una configuración en la base de datos."""
        with self.db_local._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                INSERT OR REPLACE INTO {self.TABLA_CONFIG}
                (clave, valor, actualizado_en)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (clave, valor))

    def _obtener_config(self, clave: str) -> Optional[str]:
        """Obtiene una configuración de la base de datos."""
        with self.db_local._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT valor FROM {self.TABLA_CONFIG} WHERE clave = ?",
                (clave,)
            )
            row = cursor.fetchone()
            return row['valor'] if row else None

    # ═══════════════════════════════════════════════════════════════
    # GESTIÓN DE SNAPSHOTS (CACHÉ DE DATOS)
    # ═══════════════════════════════════════════════════════════════

    def crear_snapshot(
        self,
        nombre: str,
        tabla: str,
        query: str = None,
        ttl_minutos: int = None,
        es_critico: bool = False
    ) -> int:
        """
        Crea un snapshot de datos para uso offline.

        Args:
            nombre: Nombre identificador del snapshot
            tabla: Tabla de origen
            query: Query personalizada (default: SELECT * FROM tabla)
            ttl_minutos: Tiempo de vida en minutos
            es_critico: Si es crítico para operación offline

        Returns:
            ID del snapshot creado
        """
        if not self.esta_online():
            logger.warning("⚠️ No se puede crear snapshot en modo offline")
            return -1

        ttl = ttl_minutos or self.DEFAULT_SNAPSHOT_TTL
        query = query or f"SELECT * FROM WMWHSE1.{tabla} FETCH FIRST 10000 ROWS ONLY"

        try:
            # Ejecutar query en Manhattan
            df = self._db2_connection.execute_query(query)

            if df is None or df.empty:
                logger.warning(f"⚠️ Snapshot vacío para {nombre}")
                datos_json = "[]"
                registros = 0
            else:
                datos_json = df.to_json(orient='records', date_format='iso')
                registros = len(df)

            # Calcular hash
            hash_datos = hashlib.md5(datos_json.encode()).hexdigest()
            expira_en = datetime.now() + timedelta(minutes=ttl)

            # Obtener versión anterior
            version = 1
            with self.db_local._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    f"SELECT MAX(version) FROM {self.TABLA_SNAPSHOTS} WHERE nombre = ?",
                    (nombre,)
                )
                row = cursor.fetchone()
                if row[0]:
                    version = row[0] + 1

            # Guardar snapshot
            with self.db_local._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"""
                    INSERT INTO {self.TABLA_SNAPSHOTS}
                    (nombre, tabla_origen, query_origen, datos_json, registros,
                     hash_datos, expira_en, version, es_critico)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    nombre, tabla, query, datos_json, registros,
                    hash_datos, expira_en, version, 1 if es_critico else 0
                ))

                snapshot_id = cursor.lastrowid

            logger.info(f"📸 Snapshot creado: {nombre} ({registros} registros, v{version})")
            return snapshot_id

        except Exception as e:
            logger.error(f"❌ Error creando snapshot {nombre}: {e}")
            return -1

    def obtener_snapshot(
        self,
        nombre: str,
        incluir_expirados: bool = False
    ) -> Optional[pd.DataFrame]:
        """
        Obtiene datos de un snapshot.

        Args:
            nombre: Nombre del snapshot
            incluir_expirados: Incluir snapshots expirados

        Returns:
            DataFrame con los datos o None
        """
        with self.db_local._get_connection() as conn:
            cursor = conn.cursor()

            if incluir_expirados:
                cursor.execute(f"""
                    SELECT datos_json FROM {self.TABLA_SNAPSHOTS}
                    WHERE nombre = ?
                    ORDER BY version DESC
                    LIMIT 1
                """, (nombre,))
            else:
                cursor.execute(f"""
                    SELECT datos_json FROM {self.TABLA_SNAPSHOTS}
                    WHERE nombre = ?
                      AND (expira_en IS NULL OR expira_en > ?)
                    ORDER BY version DESC
                    LIMIT 1
                """, (nombre, datetime.now()))

            row = cursor.fetchone()

            if row:
                datos = json.loads(row['datos_json'])
                return pd.DataFrame(datos)

            return None

    def actualizar_snapshots_criticos(self):
        """Actualiza todos los snapshots marcados como críticos."""
        if not self.esta_online():
            logger.warning("⚠️ No se pueden actualizar snapshots en modo offline")
            return

        with self.db_local._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT DISTINCT nombre, tabla_origen, query_origen
                FROM {self.TABLA_SNAPSHOTS}
                WHERE es_critico = 1
            """)

            criticos = cursor.fetchall()

        for snap in criticos:
            self.crear_snapshot(
                nombre=snap['nombre'],
                tabla=snap['tabla_origen'],
                query=snap['query_origen'],
                es_critico=True
            )

        logger.info(f"✅ {len(criticos)} snapshots críticos actualizados")

    def limpiar_snapshots_expirados(self) -> int:
        """Elimina snapshots expirados (excepto críticos)."""
        with self.db_local._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                DELETE FROM {self.TABLA_SNAPSHOTS}
                WHERE expira_en < ?
                  AND es_critico = 0
            """, (datetime.now(),))

            eliminados = cursor.rowcount

        if eliminados > 0:
            logger.info(f"🗑️ {eliminados} snapshots expirados eliminados")

        return eliminados

    # ═══════════════════════════════════════════════════════════════
    # GESTIÓN DE OPERACIONES PENDIENTES
    # ═══════════════════════════════════════════════════════════════

    def registrar_operacion_pendiente(
        self,
        tipo: TipoOperacionDML,
        tabla: str,
        sql: str,
        parametros: List = None,
        descripcion: str = "",
        justificacion: str = "",
        creado_por: str = "SISTEMA",
        nivel_riesgo: NivelRiesgo = NivelRiesgo.MEDIO,
        datos_antes: Dict = None,
        datos_despues: Dict = None,
        condicion_where: str = ""
    ) -> int:
        """
        Registra una operación pendiente para ejecutar cuando Manhattan vuelva.

        Args:
            tipo: Tipo de operación (INSERT, UPDATE, DELETE)
            tabla: Tabla destino
            sql: Consulta SQL
            parametros: Parámetros de la consulta
            descripcion: Descripción de la operación
            justificacion: Justificación de por qué se necesita
            creado_por: Usuario que registra la operación
            nivel_riesgo: Nivel de riesgo de la operación
            datos_antes: Datos antes del cambio (para auditoría)
            datos_despues: Datos después del cambio
            condicion_where: Condición WHERE (para UPDATE/DELETE)

        Returns:
            ID de la operación registrada
        """
        with self.db_local._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                INSERT INTO {self.TABLA_OPERACIONES}
                (tipo, tabla, sql, parametros, datos_antes, datos_despues,
                 condicion_where, nivel_riesgo, descripcion, justificacion, creado_por)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                tipo.value,
                tabla,
                sql,
                json.dumps(parametros or [], default=str),
                json.dumps(datos_antes or {}, default=str),
                json.dumps(datos_despues or {}, default=str),
                condicion_where,
                nivel_riesgo.value,
                descripcion,
                justificacion,
                creado_por
            ))

            op_id = cursor.lastrowid

        logger.info(f"📝 Operación pendiente registrada (ID: {op_id}, Tipo: {tipo.value})")

        self._registrar_evento(
            tipo="OPERACION_REGISTRADA",
            mensaje=f"Nueva operación pendiente: {descripcion}",
            detalles={"operacion_id": op_id, "tipo": tipo.value, "tabla": tabla},
            usuario=creado_por
        )

        return op_id

    def registrar_desde_plantilla(
        self,
        plantilla_id: str,
        parametros: Dict,
        creado_por: str = "SISTEMA",
        justificacion: str = ""
    ) -> int:
        """
        Registra una operación pendiente usando una plantilla predefinida.

        Args:
            plantilla_id: ID de la plantilla a usar
            parametros: Valores para los parámetros de la plantilla
            creado_por: Usuario que registra
            justificacion: Justificación de la operación

        Returns:
            ID de la operación registrada
        """
        plantilla = self.obtener_plantilla(plantilla_id)
        if not plantilla:
            raise ValueError(f"Plantilla no encontrada: {plantilla_id}")

        # Verificar parámetros requeridos
        params_requeridos = json.loads(plantilla['parametros_requeridos'])
        valores_default = json.loads(plantilla['valores_default'])

        # Combinar defaults con parámetros proporcionados
        params_completos = {**valores_default, **parametros}

        # Verificar que están todos los requeridos
        faltantes = [p for p in params_requeridos if p not in params_completos]
        if faltantes:
            raise ValueError(f"Parámetros faltantes: {', '.join(faltantes)}")

        # Formatear SQL con parámetros
        sql_formateado = plantilla['sql_template'].format(
            schema=plantilla['schema'],
            **params_completos
        )

        return self.registrar_operacion_pendiente(
            tipo=TipoOperacionDML(plantilla['tipo']),
            tabla=plantilla['tabla'],
            sql=sql_formateado,
            parametros=list(params_completos.values()),
            descripcion=f"[{plantilla_id}] {plantilla['nombre']}",
            justificacion=justificacion,
            creado_por=creado_por,
            nivel_riesgo=NivelRiesgo(plantilla['nivel_riesgo']),
            datos_despues=params_completos
        )

    def obtener_operaciones_pendientes(
        self,
        estado: EstadoOperacion = None,
        nivel_riesgo: NivelRiesgo = None,
        limite: int = 100
    ) -> List[Dict]:
        """
        Obtiene operaciones pendientes de sincronización.

        Args:
            estado: Filtrar por estado específico
            nivel_riesgo: Filtrar por nivel de riesgo
            limite: Máximo de resultados

        Returns:
            Lista de operaciones pendientes
        """
        with self.db_local._get_connection() as conn:
            cursor = conn.cursor()

            query = f"SELECT * FROM {self.TABLA_OPERACIONES} WHERE 1=1"
            params = []

            if estado:
                query += " AND estado = ?"
                params.append(estado.value)
            else:
                # Por defecto, excluir completadas y rechazadas
                query += " AND estado NOT IN ('completada', 'rechazada', 'expirada')"

            if nivel_riesgo:
                query += " AND nivel_riesgo = ?"
                params.append(nivel_riesgo.value)

            query += " ORDER BY creado_en ASC LIMIT ?"
            params.append(limite)

            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def validar_operacion(
        self,
        operacion_id: int,
        validado_por: str
    ) -> Tuple[bool, str]:
        """
        Valida una operación pendiente (paso 1 de autorización).

        Args:
            operacion_id: ID de la operación
            validado_por: Usuario que valida

        Returns:
            Tuple (exito, mensaje)
        """
        op = self._obtener_operacion(operacion_id)
        if not op:
            return False, "Operación no encontrada"

        if op['estado'] != EstadoOperacion.PENDIENTE.value:
            return False, f"Estado inválido: {op['estado']}"

        # Validar SQL básico
        sql_upper = op['sql'].strip().upper()
        if not any(sql_upper.startswith(t) for t in ['INSERT', 'UPDATE', 'DELETE']):
            return False, "SQL no válido para operación DML"

        # Actualizar estado
        with self.db_local._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE {self.TABLA_OPERACIONES}
                SET estado = 'validada',
                    validado = 1,
                    validado_por = ?,
                    validado_en = ?
                WHERE id = ?
            """, (validado_por, datetime.now(), operacion_id))

        logger.info(f"✅ Operación {operacion_id} validada por {validado_por}")
        return True, "Operación validada correctamente"

    def autorizar_operacion(
        self,
        operacion_id: int,
        autorizado_por: str,
        codigo_autorizacion: str = None
    ) -> Tuple[bool, str]:
        """
        Autoriza una operación validada (paso 2 de autorización).

        Args:
            operacion_id: ID de la operación
            autorizado_por: Usuario que autoriza
            codigo_autorizacion: Código requerido para operaciones de alto riesgo

        Returns:
            Tuple (exito, mensaje)
        """
        op = self._obtener_operacion(operacion_id)
        if not op:
            return False, "Operación no encontrada"

        if op['estado'] != EstadoOperacion.VALIDADA.value:
            return False, f"La operación debe estar validada primero (estado actual: {op['estado']})"

        nivel = NivelRiesgo(op['nivel_riesgo'])

        # Verificar código de autorización para operaciones de alto riesgo
        if nivel in [NivelRiesgo.ALTO, NivelRiesgo.CRITICO]:
            codigo_esperado = CODIGOS_AUTORIZACION.get(nivel)
            if codigo_autorizacion != codigo_esperado:
                return False, f"Código de autorización incorrecto para nivel {nivel.name}"

        # Actualizar estado
        with self.db_local._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE {self.TABLA_OPERACIONES}
                SET estado = 'autorizada',
                    autorizado = 1,
                    autorizado_por = ?,
                    autorizado_en = ?,
                    codigo_autorizacion = ?
                WHERE id = ?
            """, (autorizado_por, datetime.now(), codigo_autorizacion, operacion_id))

        logger.info(f"✅ Operación {operacion_id} autorizada por {autorizado_por}")
        return True, "Operación autorizada correctamente"

    def rechazar_operacion(
        self,
        operacion_id: int,
        rechazado_por: str,
        motivo: str
    ) -> bool:
        """
        Rechaza una operación pendiente.

        Args:
            operacion_id: ID de la operación
            rechazado_por: Usuario que rechaza
            motivo: Motivo del rechazo

        Returns:
            True si se rechazó correctamente
        """
        with self.db_local._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE {self.TABLA_OPERACIONES}
                SET estado = 'rechazada',
                    error = ?,
                    validado_por = ?
                WHERE id = ?
                  AND estado IN ('pendiente', 'validada')
            """, (f"Rechazado: {motivo}", rechazado_por, operacion_id))

            if cursor.rowcount > 0:
                logger.info(f"🚫 Operación {operacion_id} rechazada: {motivo}")
                return True

        return False

    def _obtener_operacion(self, operacion_id: int) -> Optional[Dict]:
        """Obtiene una operación por su ID."""
        with self.db_local._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT * FROM {self.TABLA_OPERACIONES} WHERE id = ?",
                (operacion_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    # ═══════════════════════════════════════════════════════════════
    # SINCRONIZACIÓN CON MANHATTAN
    # ═══════════════════════════════════════════════════════════════

    def sincronizar_con_autorizacion(
        self,
        analista: str,
        codigo: str = None,
        solo_auto_aprobables: bool = False,
        max_operaciones: int = 100
    ) -> Dict:
        """
        Sincroniza operaciones pendientes con Manhattan WMS.

        IMPORTANTE: Requiere que Manhattan esté disponible y que las
        operaciones estén autorizadas.

        Args:
            analista: Usuario que ejecuta la sincronización
            codigo: Código de autorización (requerido para ops de alto riesgo)
            solo_auto_aprobables: Solo sincronizar operaciones auto-aprobables
            max_operaciones: Máximo de operaciones a procesar

        Returns:
            Diccionario con resultados de la sincronización
        """
        resultado = {
            'inicio': datetime.now().isoformat(),
            'analista': analista,
            'total_procesadas': 0,
            'exitosas': 0,
            'fallidas': 0,
            'omitidas': 0,
            'errores': [],
            'operaciones': []
        }

        # Verificar conexión
        if not self.verificar_conexion_manhattan():
            resultado['error'] = "Manhattan no disponible"
            logger.error("❌ No se puede sincronizar: Manhattan no disponible")
            return resultado

        # Cambiar estado a sincronizando
        self._cambiar_estado(EstadoUPS.SINCRONIZANDO, f"Sincronización por {analista}")

        try:
            # Obtener operaciones autorizadas
            operaciones = self._obtener_operaciones_para_sync(
                solo_auto_aprobables,
                max_operaciones
            )

            for op in operaciones:
                resultado['total_procesadas'] += 1

                try:
                    exito, mensaje = self._ejecutar_operacion_manhattan(op, analista)

                    if exito:
                        resultado['exitosas'] += 1
                        resultado['operaciones'].append({
                            'id': op['id'],
                            'tipo': op['tipo'],
                            'estado': 'completada',
                            'mensaje': mensaje
                        })
                    else:
                        resultado['fallidas'] += 1
                        resultado['errores'].append({
                            'id': op['id'],
                            'error': mensaje
                        })
                        resultado['operaciones'].append({
                            'id': op['id'],
                            'tipo': op['tipo'],
                            'estado': 'fallida',
                            'error': mensaje
                        })

                except Exception as e:
                    resultado['fallidas'] += 1
                    error_msg = str(e)
                    resultado['errores'].append({
                        'id': op['id'],
                        'error': error_msg
                    })

                    # Actualizar estado de la operación
                    self._actualizar_estado_operacion(
                        op['id'],
                        EstadoOperacion.FALLIDA,
                        error=error_msg
                    )

            resultado['fin'] = datetime.now().isoformat()

            # Restaurar estado
            self._cambiar_estado(EstadoUPS.ONLINE, "Sincronización completada")
            self._ultima_sincronizacion = datetime.now()

            logger.info(
                f"✅ Sincronización completada: "
                f"{resultado['exitosas']}/{resultado['total_procesadas']} exitosas"
            )

            self._registrar_evento(
                tipo="SINCRONIZACION_COMPLETADA",
                mensaje=f"Sincronización: {resultado['exitosas']} exitosas, {resultado['fallidas']} fallidas",
                detalles=resultado,
                usuario=analista
            )

        except Exception as e:
            resultado['error'] = str(e)
            logger.error(f"❌ Error en sincronización: {e}")
            self._cambiar_estado(EstadoUPS.ERROR, str(e))

        return resultado

    def _obtener_operaciones_para_sync(
        self,
        solo_auto_aprobables: bool,
        limite: int
    ) -> List[Dict]:
        """Obtiene operaciones listas para sincronización."""
        with self.db_local._get_connection() as conn:
            cursor = conn.cursor()

            if solo_auto_aprobables:
                cursor.execute(f"""
                    SELECT * FROM {self.TABLA_OPERACIONES}
                    WHERE estado = 'pendiente'
                      AND nivel_riesgo = 1
                    ORDER BY creado_en ASC
                    LIMIT ?
                """, (limite,))
            else:
                cursor.execute(f"""
                    SELECT * FROM {self.TABLA_OPERACIONES}
                    WHERE estado = 'autorizada'
                    ORDER BY creado_en ASC
                    LIMIT ?
                """, (limite,))

            return [dict(row) for row in cursor.fetchall()]

    def _ejecutar_operacion_manhattan(
        self,
        operacion: Dict,
        ejecutado_por: str
    ) -> Tuple[bool, str]:
        """
        Ejecuta una operación en Manhattan WMS.

        Args:
            operacion: Diccionario con datos de la operación
            ejecutado_por: Usuario que ejecuta

        Returns:
            Tuple (exito, mensaje)
        """
        op_id = operacion['id']

        # Actualizar estado a ejecutando
        self._actualizar_estado_operacion(op_id, EstadoOperacion.EJECUTANDO)

        try:
            # Ejecutar SQL en Manhattan
            sql = operacion['sql']
            filas = self._db2_connection.execute_non_query(sql)

            # Actualizar como completada
            with self.db_local._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"""
                    UPDATE {self.TABLA_OPERACIONES}
                    SET estado = 'completada',
                        ejecutado_en = ?,
                        filas_afectadas = ?,
                        resultado = 'OK'
                    WHERE id = ?
                """, (datetime.now(), filas, op_id))

            logger.info(f"✅ Operación {op_id} ejecutada: {filas} filas afectadas")
            return True, f"Ejecutada: {filas} filas afectadas"

        except Exception as e:
            error_msg = str(e)

            # Incrementar intentos
            with self.db_local._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"""
                    UPDATE {self.TABLA_OPERACIONES}
                    SET intentos = intentos + 1,
                        error = ?,
                        estado = CASE
                            WHEN intentos >= max_intentos - 1 THEN 'fallida'
                            ELSE 'autorizada'
                        END
                    WHERE id = ?
                """, (error_msg, op_id))

            logger.error(f"❌ Error ejecutando operación {op_id}: {error_msg}")
            return False, error_msg

    def _actualizar_estado_operacion(
        self,
        operacion_id: int,
        estado: EstadoOperacion,
        error: str = None
    ):
        """Actualiza el estado de una operación."""
        with self.db_local._get_connection() as conn:
            cursor = conn.cursor()

            if error:
                cursor.execute(f"""
                    UPDATE {self.TABLA_OPERACIONES}
                    SET estado = ?, error = ?
                    WHERE id = ?
                """, (estado.value, error, operacion_id))
            else:
                cursor.execute(f"""
                    UPDATE {self.TABLA_OPERACIONES}
                    SET estado = ?
                    WHERE id = ?
                """, (estado.value, operacion_id))

    # ═══════════════════════════════════════════════════════════════
    # GESTIÓN DE PLANTILLAS DML
    # ═══════════════════════════════════════════════════════════════

    def obtener_plantillas(
        self,
        categoria: str = None,
        activas_solo: bool = True
    ) -> List[Dict]:
        """
        Obtiene plantillas DML disponibles.

        Args:
            categoria: Filtrar por categoría
            activas_solo: Solo plantillas activas

        Returns:
            Lista de plantillas
        """
        with self.db_local._get_connection() as conn:
            cursor = conn.cursor()

            query = f"SELECT * FROM {self.TABLA_PLANTILLAS} WHERE 1=1"
            params = []

            if activas_solo:
                query += " AND activa = 1"

            if categoria:
                query += " AND categoria = ?"
                params.append(categoria)

            query += " ORDER BY categoria, nombre"

            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def obtener_plantilla(self, plantilla_id: str) -> Optional[Dict]:
        """Obtiene una plantilla por ID."""
        with self.db_local._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT * FROM {self.TABLA_PLANTILLAS} WHERE id = ?",
                (plantilla_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def agregar_plantilla_personalizada(
        self,
        id: str,
        nombre: str,
        tipo: TipoOperacionDML,
        tabla: str,
        sql_template: str,
        parametros_requeridos: List[str],
        descripcion: str = "",
        nivel_riesgo: NivelRiesgo = NivelRiesgo.ALTO,
        categoria: str = "personalizada"
    ) -> bool:
        """
        Agrega una nueva plantilla DML personalizada.

        Las plantillas personalizadas siempre requieren validación manual
        y no son auto-aprobables por seguridad.

        Args:
            id: ID único de la plantilla
            nombre: Nombre descriptivo
            tipo: Tipo de operación
            tabla: Tabla destino
            sql_template: Template SQL con placeholders
            parametros_requeridos: Lista de parámetros requeridos
            descripcion: Descripción de la operación
            nivel_riesgo: Nivel de riesgo
            categoria: Categoría para organización

        Returns:
            True si se agregó correctamente
        """
        with self.db_local._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                INSERT INTO {self.TABLA_PLANTILLAS}
                (id, nombre, descripcion, tipo, tabla, sql_template,
                 parametros_requeridos, nivel_riesgo, auto_aprobable,
                 requiere_validacion_manual, activa, categoria)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 1, 1, ?)
            """, (
                id,
                nombre,
                descripcion,
                tipo.value,
                tabla,
                sql_template,
                json.dumps(parametros_requeridos),
                nivel_riesgo.value,
                categoria
            ))

            if cursor.rowcount > 0:
                logger.info(f"✅ Plantilla personalizada agregada: {id}")
                return True

        return False

    # ═══════════════════════════════════════════════════════════════
    # ESTADÍSTICAS Y REPORTES
    # ═══════════════════════════════════════════════════════════════

    def obtener_estadisticas(self) -> Dict:
        """
        Obtiene estadísticas del sistema UPS.

        Returns:
            Diccionario con estadísticas completas
        """
        with self.db_local._get_connection() as conn:
            cursor = conn.cursor()

            # Operaciones por estado
            cursor.execute(f"""
                SELECT estado, COUNT(*) as total
                FROM {self.TABLA_OPERACIONES}
                GROUP BY estado
            """)
            ops_por_estado = {row['estado']: row['total'] for row in cursor.fetchall()}

            # Operaciones por nivel de riesgo
            cursor.execute(f"""
                SELECT nivel_riesgo, COUNT(*) as total
                FROM {self.TABLA_OPERACIONES}
                WHERE estado NOT IN ('completada', 'rechazada', 'expirada')
                GROUP BY nivel_riesgo
            """)
            ops_por_riesgo = {str(row['nivel_riesgo']): row['total'] for row in cursor.fetchall()}

            # Snapshots
            cursor.execute(f"""
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN es_critico = 1 THEN 1 ELSE 0 END) as criticos,
                       SUM(CASE WHEN expira_en < CURRENT_TIMESTAMP THEN 1 ELSE 0 END) as expirados
                FROM {self.TABLA_SNAPSHOTS}
            """)
            snap_stats = dict(cursor.fetchone())

            # Eventos recientes
            cursor.execute(f"""
                SELECT tipo, COUNT(*) as total
                FROM {self.TABLA_EVENTOS}
                WHERE timestamp > datetime('now', '-24 hours')
                GROUP BY tipo
            """)
            eventos_24h = {row['tipo']: row['total'] for row in cursor.fetchall()}

        return {
            'estado_actual': self._estado.value,
            'modo_operacion': self._modo_operacion.value,
            'ultimo_health_check': self._ultimo_health_check.isoformat() if self._ultimo_health_check else None,
            'ultima_sincronizacion': self._ultima_sincronizacion.isoformat() if self._ultima_sincronizacion else None,
            'errores_consecutivos': self._errores_consecutivos,
            'operaciones': {
                'por_estado': ops_por_estado,
                'por_riesgo': ops_por_riesgo,
                'pendientes_total': sum(
                    v for k, v in ops_por_estado.items()
                    if k in ['pendiente', 'validada', 'autorizada']
                )
            },
            'snapshots': snap_stats,
            'eventos_24h': eventos_24h
        }

    def obtener_resumen_operaciones_pendientes(self) -> str:
        """
        Genera un resumen legible de operaciones pendientes.

        Returns:
            Texto formateado con el resumen
        """
        ops = self.obtener_operaciones_pendientes()

        if not ops:
            return "✅ No hay operaciones pendientes de sincronización"

        lineas = [
            "═" * 60,
            "📋 OPERACIONES PENDIENTES DE SINCRONIZACIÓN",
            "═" * 60,
            ""
        ]

        for i, op in enumerate(ops, 1):
            nivel = NivelRiesgo(op['nivel_riesgo'])
            icono = {
                NivelRiesgo.BAJO: "🟢",
                NivelRiesgo.MEDIO: "🟡",
                NivelRiesgo.ALTO: "🟠",
                NivelRiesgo.CRITICO: "🔴"
            }.get(nivel, "⚪")

            lineas.append(f"{i}. [{op['id']}] {icono} {nivel.name}")
            lineas.append(f"   Tipo: {op['tipo']} | Tabla: {op['tabla']}")
            lineas.append(f"   Estado: {op['estado']}")
            lineas.append(f"   Descripción: {op['descripcion'] or 'N/A'}")
            lineas.append(f"   Creado: {op['creado_en']} por {op['creado_por']}")

            if op['validado']:
                lineas.append(f"   Validado: ✅ por {op['validado_por']}")
            if op['autorizado']:
                lineas.append(f"   Autorizado: ✅ por {op['autorizado_por']}")

            lineas.append("")

        lineas.append("═" * 60)
        lineas.append(f"Total: {len(ops)} operaciones pendientes")

        return "\n".join(lineas)

    def imprimir_estado(self):
        """Imprime el estado actual del sistema UPS."""
        stats = self.obtener_estadisticas()

        estado_icono = {
            EstadoUPS.ONLINE: "🟢",
            EstadoUPS.OFFLINE: "🔴",
            EstadoUPS.SINCRONIZANDO: "🔄",
            EstadoUPS.MANTENIMIENTO: "🔧",
            EstadoUPS.ERROR: "❌",
            EstadoUPS.INICIANDO: "⏳"
        }.get(self._estado, "⚪")

        print("\n" + "═" * 60)
        print(f"🔋 SISTEMA UPS - ESTADO ACTUAL")
        print("═" * 60)
        print(f"\n   {estado_icono} Estado: {stats['estado_actual'].upper()}")
        print(f"   📊 Modo: {stats['modo_operacion']}")
        print(f"   🔍 Último health check: {stats['ultimo_health_check'] or 'N/A'}")
        print(f"   🔄 Última sincronización: {stats['ultima_sincronizacion'] or 'N/A'}")

        print(f"\n📝 OPERACIONES PENDIENTES:")
        for estado, total in stats['operaciones']['por_estado'].items():
            print(f"   • {estado}: {total}")

        print(f"\n📸 SNAPSHOTS:")
        print(f"   • Total: {stats['snapshots']['total']}")
        print(f"   • Críticos: {stats['snapshots']['criticos']}")
        print(f"   • Expirados: {stats['snapshots']['expirados']}")

        print("\n" + "═" * 60)

    # ═══════════════════════════════════════════════════════════════
    # CLEANUP Y DESTRUCTOR
    # ═══════════════════════════════════════════════════════════════

    def cleanup(self):
        """Limpia recursos y detiene procesos."""
        self.detener_health_check()

        if self._db2_connection:
            try:
                self._db2_connection.disconnect()
            except Exception:
                pass

        logger.info("🧹 UPS Backup limpiado")

    def __del__(self):
        """Destructor."""
        try:
            self.cleanup()
        except Exception:
            pass

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()
        return False


# ═══════════════════════════════════════════════════════════════
# INSTANCIA GLOBAL (SINGLETON)
# ═══════════════════════════════════════════════════════════════

_ups_instance: Optional[UPSBackup] = None


def get_ups_backup(
    auto_start: bool = True,
    health_check_enabled: bool = True
) -> UPSBackup:
    """
    Obtiene la instancia global del sistema UPS.

    Args:
        auto_start: Iniciar monitoreo automático
        health_check_enabled: Habilitar verificación periódica

    Returns:
        Instancia de UPSBackup
    """
    global _ups_instance
    if _ups_instance is None:
        _ups_instance = UPSBackup(
            auto_start=auto_start,
            health_check_enabled=health_check_enabled
        )
    return _ups_instance


def iniciar_modo_respaldo(motivo: str = "Mantenimiento programado"):
    """
    Función de conveniencia para activar modo respaldo.

    Args:
        motivo: Motivo del modo respaldo
    """
    ups = get_ups_backup()
    ups.activar_modo_mantenimiento(motivo=motivo)


def restaurar_modo_normal():
    """Función de conveniencia para restaurar modo normal."""
    ups = get_ups_backup()
    ups.desactivar_modo_mantenimiento()


# ═══════════════════════════════════════════════════════════════
# EXPORTAR
# ═══════════════════════════════════════════════════════════════

__all__ = [
    # Clase principal
    'UPSBackup',
    'get_ups_backup',

    # Funciones de conveniencia
    'iniciar_modo_respaldo',
    'restaurar_modo_normal',

    # Enums
    'EstadoUPS',
    'ModoOperacion',
    'TipoOperacionDML',
    'NivelRiesgo',
    'EstadoOperacion',

    # Data classes
    'OperacionDML',
    'PlantillaDML',
    'SnapshotDatos',
    'EventoUPS',

    # Constantes
    'PLANTILLAS_PREDEFINIDAS',
    'CODIGOS_AUTORIZACION',
]


# ═══════════════════════════════════════════════════════════════
# EJECUCIÓN DIRECTA
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n" + "═" * 60)
    print("🔋 MÓDULO UPS BACKUP - SAC CEDIS 427")
    print("   Sistema de Respaldo y Continuidad Operativa")
    print("═" * 60)

    # Crear instancia sin health check automático para demo
    ups = UPSBackup(auto_start=True, health_check_enabled=False)

    # Mostrar estado
    ups.imprimir_estado()

    # Mostrar plantillas disponibles
    print("\n📋 PLANTILLAS DML DISPONIBLES:")
    for plantilla in ups.obtener_plantillas():
        nivel = NivelRiesgo(plantilla['nivel_riesgo'])
        auto = "✅" if plantilla['auto_aprobable'] else "❌"
        print(f"   [{plantilla['id']}] {plantilla['nombre']}")
        print(f"       Riesgo: {nivel.name} | Auto-aprobable: {auto}")
        print(f"       Categoría: {plantilla['categoria']}")

    print("\n" + "═" * 60)
    print("✅ Módulo UPS Backup cargado correctamente")
    print("═" * 60 + "\n")
