"""
===============================================================
MÓDULO DE SINCRONIZACIÓN DB REMOTA <-> LOCAL
Sistema de Automatización de Consultas - CEDIS Cancún 427
===============================================================

Este módulo gestiona la sincronización entre:
- DB Remota: lg001bk.chedraui.com.mx (IBM DB2 / Manhattan WMS)
- DB Local: SQLite (respaldo e intermediario)

Funcionalidades:
- Descarga de datos desde DB2 a SQLite local
- Cola de cambios pendientes de sincronizar
- Respaldo automático antes de operaciones
- Registro de sincronizaciones realizadas
- Detección de conflictos

Uso:
    from modules.db_sync import SincronizadorDB, get_sincronizador

    sync = get_sincronizador()

    # Descargar datos de DB2 a local
    sync.descargar_tabla("ORDERS", filtro="WHERE ADDDATE > '2024-01-01'")

    # Ver cambios pendientes
    cambios = sync.obtener_cambios_pendientes()

    # Sincronizar cambios a DB2
    sync.sincronizar_cambios()

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
===============================================================
"""

import logging
import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, field, asdict
from contextlib import contextmanager
from enum import Enum
import sqlite3

# Importar módulos locales
from .db_local import DBLocal, get_db_local, TipoOperacion
from .db_connection import DB2Connection, DB2ConnectionError

# Configurar logger
logger = logging.getLogger(__name__)


# ===============================================================
# ENUMERACIONES Y CONSTANTES
# ===============================================================

class EstadoSincronizacion(Enum):
    """Estados de sincronización"""
    PENDIENTE = "pendiente"
    EN_PROCESO = "en_proceso"
    COMPLETADO = "completado"
    ERROR = "error"
    CONFLICTO = "conflicto"
    CANCELADO = "cancelado"


class DireccionSync(Enum):
    """Dirección de la sincronización"""
    REMOTA_A_LOCAL = "remota_a_local"      # DB2 -> SQLite
    LOCAL_A_REMOTA = "local_a_remota"      # SQLite -> DB2
    BIDIRECCIONAL = "bidireccional"        # Ambas direcciones


class TipoCambio(Enum):
    """Tipos de cambios a sincronizar"""
    INSERCION = "insercion"
    ACTUALIZACION = "actualizacion"
    ELIMINACION = "eliminacion"


# ===============================================================
# DATA CLASSES
# ===============================================================

@dataclass
class CambioPendiente:
    """Representa un cambio pendiente de sincronización"""
    id: Optional[int] = None
    tabla: str = ""
    tipo_cambio: str = TipoCambio.ACTUALIZACION.value
    datos_antes: str = "{}"  # JSON
    datos_despues: str = "{}"  # JSON
    clave_primaria: str = ""
    fecha_cambio: datetime = field(default_factory=datetime.now)
    usuario: str = "SISTEMA"
    estado: str = EstadoSincronizacion.PENDIENTE.value
    intentos: int = 0
    ultimo_error: Optional[str] = None
    sincronizado_en: Optional[datetime] = None


@dataclass
class RegistroSincronizacion:
    """Registro de una sincronización realizada"""
    id: Optional[int] = None
    fecha_inicio: datetime = field(default_factory=datetime.now)
    fecha_fin: Optional[datetime] = None
    direccion: str = DireccionSync.REMOTA_A_LOCAL.value
    tabla: str = ""
    registros_procesados: int = 0
    registros_exitosos: int = 0
    registros_fallidos: int = 0
    estado: str = EstadoSincronizacion.PENDIENTE.value
    detalles_json: str = "{}"


# ===============================================================
# CLASE PRINCIPAL DE SINCRONIZACIÓN
# ===============================================================

class SincronizadorDB:
    """
    Gestor de sincronización entre DB remota (DB2) y local (SQLite).

    Actúa como intermediario para:
    - Descargar datos de DB2 para trabajo local
    - Mantener cola de cambios pendientes
    - Sincronizar cambios de vuelta a DB2
    - Detectar y resolver conflictos

    Ejemplo:
        >>> sync = SincronizadorDB()
        >>> sync.descargar_tabla("WMWHSE1.ORDERS", limite=1000)
        >>> cambios = sync.obtener_cambios_pendientes()
        >>> sync.sincronizar_cambios()
    """

    # Tablas locales para sincronización
    TABLA_CAMBIOS = "sync_cambios_pendientes"
    TABLA_HISTORIAL = "sync_historial"
    TABLA_DATOS_CACHE = "sync_datos_cache"

    def __init__(
        self,
        db_local: Optional[DBLocal] = None,
        db2_config: Optional[Dict] = None,
        schema_remoto: str = "WMWHSE1"
    ):
        """
        Inicializa el sincronizador.

        Args:
            db_local: Instancia de DBLocal (usa singleton si no se proporciona)
            db2_config: Configuración de conexión a DB2
            schema_remoto: Schema en DB2 (default: WMWHSE1)
        """
        self.db_local = db_local or get_db_local()
        self.db2_config = db2_config
        self.schema_remoto = schema_remoto
        self._db2_connection: Optional[DB2Connection] = None

        # Inicializar tablas de sincronización
        self._inicializar_tablas_sync()

        logger.info(f"🔄 SincronizadorDB inicializado (Schema: {schema_remoto})")

    def _inicializar_tablas_sync(self):
        """Crea las tablas necesarias para sincronización."""
        with self.db_local._get_connection() as conn:
            cursor = conn.cursor()

            # Tabla de cambios pendientes
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.TABLA_CAMBIOS} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tabla TEXT NOT NULL,
                    tipo_cambio TEXT NOT NULL,
                    datos_antes TEXT DEFAULT '{{}}',
                    datos_despues TEXT DEFAULT '{{}}',
                    clave_primaria TEXT,
                    fecha_cambio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    usuario TEXT DEFAULT 'SISTEMA',
                    estado TEXT DEFAULT 'pendiente',
                    intentos INTEGER DEFAULT 0,
                    ultimo_error TEXT,
                    sincronizado_en TIMESTAMP
                )
            """)

            # Tabla de historial de sincronizaciones
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.TABLA_HISTORIAL} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha_inicio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    fecha_fin TIMESTAMP,
                    direccion TEXT NOT NULL,
                    tabla TEXT,
                    registros_procesados INTEGER DEFAULT 0,
                    registros_exitosos INTEGER DEFAULT 0,
                    registros_fallidos INTEGER DEFAULT 0,
                    estado TEXT DEFAULT 'pendiente',
                    detalles_json TEXT DEFAULT '{{}}'
                )
            """)

            # Tabla de caché de datos remotos
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.TABLA_DATOS_CACHE} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tabla_origen TEXT NOT NULL,
                    clave_primaria TEXT,
                    datos_json TEXT NOT NULL,
                    hash_datos TEXT,
                    fecha_descarga TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    fecha_expiracion TIMESTAMP,
                    version INTEGER DEFAULT 1
                )
            """)

            # Índices
            cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_cambios_estado ON {self.TABLA_CAMBIOS}(estado)")
            cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_cambios_tabla ON {self.TABLA_CAMBIOS}(tabla)")
            cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_cache_tabla ON {self.TABLA_DATOS_CACHE}(tabla_origen)")

            logger.info("✅ Tablas de sincronización verificadas/creadas")

    # ===============================================================
    # CONEXIÓN A DB2
    # ===============================================================

    def conectar_db2(self) -> bool:
        """Establece conexión a la base de datos remota DB2."""
        try:
            if self._db2_connection and self._db2_connection.is_connected:
                return True

            self._db2_connection = DB2Connection(config=self.db2_config)
            self._db2_connection.connect()
            logger.info("✅ Conectado a DB2 remota")
            return True

        except DB2ConnectionError as e:
            logger.error(f"❌ Error conectando a DB2: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error inesperado conectando a DB2: {e}")
            return False

    def desconectar_db2(self):
        """Cierra la conexión a DB2."""
        if self._db2_connection:
            self._db2_connection.disconnect()
            self._db2_connection = None
            logger.info("🔌 Desconectado de DB2")

    @property
    def db2_conectado(self) -> bool:
        """Verifica si hay conexión activa a DB2."""
        return self._db2_connection is not None and self._db2_connection.is_connected

    # ===============================================================
    # DESCARGA DE DATOS (DB2 -> LOCAL)
    # ===============================================================

    def descargar_tabla(
        self,
        tabla: str,
        columnas: List[str] = None,
        filtro: str = None,
        limite: int = 10000,
        ttl_minutos: int = 60
    ) -> Tuple[bool, int, str]:
        """
        Descarga datos de una tabla DB2 a caché local.

        Args:
            tabla: Nombre de la tabla (ej: "ORDERS" o "WMWHSE1.ORDERS")
            columnas: Lista de columnas a descargar (default: todas)
            filtro: Condición WHERE (sin la palabra WHERE)
            limite: Máximo de registros
            ttl_minutos: Tiempo de vida del caché

        Returns:
            Tuple (exito, registros_descargados, mensaje)
        """
        if not self.conectar_db2():
            return False, 0, "No se pudo conectar a DB2"

        # Preparar query
        tabla_completa = f"{self.schema_remoto}.{tabla}" if '.' not in tabla else tabla
        cols = ', '.join(columnas) if columnas else '*'
        query = f"SELECT {cols} FROM {tabla_completa}"

        if filtro:
            query += f" WHERE {filtro}"
        query += f" FETCH FIRST {limite} ROWS ONLY"

        try:
            # Registrar inicio de sincronización
            sync_id = self._registrar_inicio_sync(
                direccion=DireccionSync.REMOTA_A_LOCAL.value,
                tabla=tabla
            )

            # Ejecutar query en DB2
            logger.info(f"📥 Descargando datos de {tabla_completa}...")
            df = self._db2_connection.execute_query(query)

            if df is None or df.empty:
                self._registrar_fin_sync(sync_id, 0, 0, 0, "Sin datos")
                return True, 0, "No se encontraron datos"

            registros = len(df)
            fecha_expiracion = datetime.now() + timedelta(minutes=ttl_minutos)

            # Guardar en caché local
            with self.db_local._get_connection() as conn:
                cursor = conn.cursor()

                # Limpiar caché anterior de esta tabla
                cursor.execute(
                    f"DELETE FROM {self.TABLA_DATOS_CACHE} WHERE tabla_origen = ?",
                    (tabla,)
                )

                # Insertar nuevos datos
                for _, row in df.iterrows():
                    datos_json = json.dumps(row.to_dict(), default=str)
                    hash_datos = hashlib.md5(datos_json.encode()).hexdigest()

                    cursor.execute(f"""
                        INSERT INTO {self.TABLA_DATOS_CACHE}
                        (tabla_origen, datos_json, hash_datos, fecha_expiracion)
                        VALUES (?, ?, ?, ?)
                    """, (tabla, datos_json, hash_datos, fecha_expiracion))

            self._registrar_fin_sync(sync_id, registros, registros, 0, "Completado")
            logger.info(f"✅ {registros} registros descargados de {tabla}")
            return True, registros, f"Descargados {registros} registros"

        except Exception as e:
            logger.error(f"❌ Error descargando {tabla}: {e}")
            if 'sync_id' in locals():
                self._registrar_fin_sync(sync_id, 0, 0, 0, str(e), error=True)
            return False, 0, str(e)

    def obtener_datos_cache(
        self,
        tabla: str,
        incluir_expirados: bool = False
    ) -> List[Dict]:
        """
        Obtiene datos del caché local.

        Args:
            tabla: Nombre de la tabla
            incluir_expirados: Si incluir datos expirados

        Returns:
            Lista de diccionarios con los datos
        """
        with self.db_local._get_connection() as conn:
            cursor = conn.cursor()

            query = f"SELECT datos_json FROM {self.TABLA_DATOS_CACHE} WHERE tabla_origen = ?"
            params = [tabla]

            if not incluir_expirados:
                query += " AND (fecha_expiracion IS NULL OR fecha_expiracion > ?)"
                params.append(datetime.now())

            cursor.execute(query, params)
            rows = cursor.fetchall()

            return [json.loads(row['datos_json']) for row in rows]

    # ===============================================================
    # REGISTRO DE CAMBIOS (PARA SYNC LOCAL -> REMOTA)
    # ===============================================================

    def registrar_cambio(
        self,
        tabla: str,
        tipo_cambio: TipoCambio,
        datos_antes: Dict = None,
        datos_despues: Dict = None,
        clave_primaria: str = None,
        usuario: str = "SISTEMA"
    ) -> int:
        """
        Registra un cambio pendiente de sincronización.

        Args:
            tabla: Tabla afectada
            tipo_cambio: Tipo de cambio (INSERT, UPDATE, DELETE)
            datos_antes: Datos antes del cambio (para UPDATE/DELETE)
            datos_despues: Datos después del cambio (para INSERT/UPDATE)
            clave_primaria: Valor de la clave primaria
            usuario: Usuario que realizó el cambio

        Returns:
            ID del cambio registrado
        """
        with self.db_local._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                INSERT INTO {self.TABLA_CAMBIOS}
                (tabla, tipo_cambio, datos_antes, datos_despues, clave_primaria, usuario)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                tabla,
                tipo_cambio.value,
                json.dumps(datos_antes or {}, default=str),
                json.dumps(datos_despues or {}, default=str),
                clave_primaria,
                usuario
            ))

            cambio_id = cursor.lastrowid
            logger.info(f"📝 Cambio registrado (ID: {cambio_id}, Tabla: {tabla}, Tipo: {tipo_cambio.value})")
            return cambio_id

    def obtener_cambios_pendientes(self, tabla: str = None) -> List[Dict]:
        """
        Obtiene cambios pendientes de sincronización.

        Args:
            tabla: Filtrar por tabla específica

        Returns:
            Lista de cambios pendientes
        """
        with self.db_local._get_connection() as conn:
            cursor = conn.cursor()

            query = f"SELECT * FROM {self.TABLA_CAMBIOS} WHERE estado = 'pendiente'"
            params = []

            if tabla:
                query += " AND tabla = ?"
                params.append(tabla)

            query += " ORDER BY fecha_cambio ASC"

            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def cancelar_cambio(self, cambio_id: int, motivo: str = None) -> bool:
        """Cancela un cambio pendiente."""
        with self.db_local._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE {self.TABLA_CAMBIOS}
                SET estado = 'cancelado', ultimo_error = ?
                WHERE id = ? AND estado = 'pendiente'
            """, (motivo or "Cancelado por usuario", cambio_id))

            if cursor.rowcount > 0:
                logger.info(f"🚫 Cambio {cambio_id} cancelado")
                return True
            return False

    # ===============================================================
    # SINCRONIZACIÓN (LOCAL -> DB2)
    # ===============================================================

    def sincronizar_cambios(
        self,
        tabla: str = None,
        max_intentos: int = 3
    ) -> Tuple[int, int, List[str]]:
        """
        Sincroniza cambios pendientes a DB2.

        IMPORTANTE: Esta operación modifica la DB remota.

        Args:
            tabla: Sincronizar solo cambios de esta tabla
            max_intentos: Máximo de reintentos por cambio

        Returns:
            Tuple (exitosos, fallidos, lista_errores)
        """
        if not self.conectar_db2():
            return 0, 0, ["No se pudo conectar a DB2"]

        cambios = self.obtener_cambios_pendientes(tabla)

        if not cambios:
            logger.info("✅ No hay cambios pendientes de sincronizar")
            return 0, 0, []

        exitosos = 0
        fallidos = 0
        errores = []

        sync_id = self._registrar_inicio_sync(
            direccion=DireccionSync.LOCAL_A_REMOTA.value,
            tabla=tabla or "MÚLTIPLES"
        )

        for cambio in cambios:
            if cambio['intentos'] >= max_intentos:
                logger.warning(f"⚠️ Cambio {cambio['id']} excedió máximo de intentos")
                continue

            try:
                # Marcar como en proceso
                self._actualizar_estado_cambio(cambio['id'], EstadoSincronizacion.EN_PROCESO)

                # Ejecutar según tipo de cambio
                exito = self._ejecutar_cambio_en_db2(cambio)

                if exito:
                    self._actualizar_estado_cambio(
                        cambio['id'],
                        EstadoSincronizacion.COMPLETADO,
                        sincronizado=True
                    )
                    exitosos += 1
                else:
                    raise Exception("Falló la ejecución del cambio")

            except Exception as e:
                error_msg = f"Cambio {cambio['id']}: {str(e)}"
                errores.append(error_msg)
                self._actualizar_estado_cambio(
                    cambio['id'],
                    EstadoSincronizacion.ERROR,
                    error=str(e)
                )
                fallidos += 1
                logger.error(f"❌ {error_msg}")

        self._registrar_fin_sync(
            sync_id,
            len(cambios),
            exitosos,
            fallidos,
            f"Exitosos: {exitosos}, Fallidos: {fallidos}"
        )

        logger.info(f"🔄 Sincronización completada: {exitosos} exitosos, {fallidos} fallidos")
        return exitosos, fallidos, errores

    def _ejecutar_cambio_en_db2(self, cambio: Dict) -> bool:
        """Ejecuta un cambio individual en DB2."""
        tipo = cambio['tipo_cambio']
        tabla = f"{self.schema_remoto}.{cambio['tabla']}"
        datos_despues = json.loads(cambio['datos_despues'])
        datos_antes = json.loads(cambio['datos_antes'])

        if tipo == TipoCambio.INSERCION.value:
            columnas = ', '.join(datos_despues.keys())
            placeholders = ', '.join(['?' for _ in datos_despues])
            query = f"INSERT INTO {tabla} ({columnas}) VALUES ({placeholders})"
            params = list(datos_despues.values())

        elif tipo == TipoCambio.ACTUALIZACION.value:
            sets = ', '.join([f"{k} = ?" for k in datos_despues.keys()])
            query = f"UPDATE {tabla} SET {sets} WHERE {cambio['clave_primaria']}"
            params = list(datos_despues.values())

        elif tipo == TipoCambio.ELIMINACION.value:
            query = f"DELETE FROM {tabla} WHERE {cambio['clave_primaria']}"
            params = []

        else:
            raise ValueError(f"Tipo de cambio desconocido: {tipo}")

        # Ejecutar en DB2
        result = self._db2_connection.execute_query(query, params)
        return True  # Si no hay excepción, fue exitoso

    # ===============================================================
    # MÉTODOS AUXILIARES
    # ===============================================================

    def _registrar_inicio_sync(self, direccion: str, tabla: str) -> int:
        """Registra el inicio de una sincronización."""
        with self.db_local._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                INSERT INTO {self.TABLA_HISTORIAL}
                (direccion, tabla, estado)
                VALUES (?, ?, 'en_proceso')
            """, (direccion, tabla))
            return cursor.lastrowid

    def _registrar_fin_sync(
        self,
        sync_id: int,
        procesados: int,
        exitosos: int,
        fallidos: int,
        detalles: str,
        error: bool = False
    ):
        """Registra el fin de una sincronización."""
        estado = 'error' if error else 'completado'

        with self.db_local._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE {self.TABLA_HISTORIAL}
                SET fecha_fin = ?,
                    registros_procesados = ?,
                    registros_exitosos = ?,
                    registros_fallidos = ?,
                    estado = ?,
                    detalles_json = ?
                WHERE id = ?
            """, (
                datetime.now(),
                procesados,
                exitosos,
                fallidos,
                estado,
                json.dumps({'mensaje': detalles}),
                sync_id
            ))

    def _actualizar_estado_cambio(
        self,
        cambio_id: int,
        estado: EstadoSincronizacion,
        error: str = None,
        sincronizado: bool = False
    ):
        """Actualiza el estado de un cambio."""
        with self.db_local._get_connection() as conn:
            cursor = conn.cursor()

            updates = ["estado = ?", "intentos = intentos + 1"]
            params = [estado.value]

            if error:
                updates.append("ultimo_error = ?")
                params.append(error)

            if sincronizado:
                updates.append("sincronizado_en = ?")
                params.append(datetime.now())

            params.append(cambio_id)

            cursor.execute(
                f"UPDATE {self.TABLA_CAMBIOS} SET {', '.join(updates)} WHERE id = ?",
                params
            )

    # ===============================================================
    # ESTADÍSTICAS Y REPORTES
    # ===============================================================

    def obtener_estadisticas_sync(self, dias: int = 30) -> Dict:
        """Obtiene estadísticas de sincronización."""
        fecha_inicio = datetime.now() - timedelta(days=dias)

        with self.db_local._get_connection() as conn:
            cursor = conn.cursor()

            # Estadísticas de historial
            cursor.execute(f"""
                SELECT
                    COUNT(*) as total_syncs,
                    SUM(registros_procesados) as total_procesados,
                    SUM(registros_exitosos) as total_exitosos,
                    SUM(registros_fallidos) as total_fallidos,
                    SUM(CASE WHEN estado = 'completado' THEN 1 ELSE 0 END) as syncs_exitosas,
                    SUM(CASE WHEN estado = 'error' THEN 1 ELSE 0 END) as syncs_fallidas
                FROM {self.TABLA_HISTORIAL}
                WHERE fecha_inicio >= ?
            """, (fecha_inicio,))

            historial = dict(cursor.fetchone())

            # Cambios pendientes
            cursor.execute(f"""
                SELECT
                    COUNT(*) as total_pendientes,
                    COUNT(DISTINCT tabla) as tablas_afectadas
                FROM {self.TABLA_CAMBIOS}
                WHERE estado = 'pendiente'
            """)

            pendientes = dict(cursor.fetchone())

            # Tamaño del caché
            cursor.execute(f"SELECT COUNT(*) as registros_cache FROM {self.TABLA_DATOS_CACHE}")
            cache = dict(cursor.fetchone())

            return {
                'periodo_dias': dias,
                'historial': historial,
                'pendientes': pendientes,
                'cache': cache,
                'db2_conectado': self.db2_conectado
            }

    def limpiar_cache_expirado(self) -> int:
        """Elimina registros de caché expirados."""
        with self.db_local._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"DELETE FROM {self.TABLA_DATOS_CACHE} WHERE fecha_expiracion <= ?",
                (datetime.now(),)
            )
            eliminados = cursor.rowcount

            if eliminados > 0:
                logger.info(f"🗑️ {eliminados} registros de caché expirados eliminados")

            return eliminados

    def limpiar_historial_antiguo(self, dias: int = 90) -> int:
        """Elimina historial de sincronizaciones antiguas."""
        fecha_corte = datetime.now() - timedelta(days=dias)

        with self.db_local._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"DELETE FROM {self.TABLA_HISTORIAL} WHERE fecha_inicio < ?",
                (fecha_corte,)
            )
            eliminados = cursor.rowcount

            if eliminados > 0:
                logger.info(f"🗑️ {eliminados} registros de historial eliminados")

            return eliminados


# ===============================================================
# INSTANCIA GLOBAL (SINGLETON)
# ===============================================================

_sincronizador_instance: Optional[SincronizadorDB] = None


def get_sincronizador() -> SincronizadorDB:
    """Obtiene la instancia global del sincronizador."""
    global _sincronizador_instance
    if _sincronizador_instance is None:
        _sincronizador_instance = SincronizadorDB()
    return _sincronizador_instance


# ===============================================================
# EXPORTAR
# ===============================================================

__all__ = [
    'SincronizadorDB',
    'get_sincronizador',
    'EstadoSincronizacion',
    'DireccionSync',
    'TipoCambio',
    'CambioPendiente',
    'RegistroSincronizacion',
]


# ===============================================================
# EJECUCIÓN DIRECTA
# ===============================================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🔄 SINCRONIZADOR DB REMOTA <-> LOCAL")
    print("   CEDIS Cancún 427")
    print("=" * 60)

    sync = SincronizadorDB()

    # Mostrar estadísticas
    stats = sync.obtener_estadisticas_sync()
    print(f"\n📊 Estadísticas de sincronización:")
    print(f"   • DB2 conectado: {'✅' if stats['db2_conectado'] else '❌'}")
    print(f"   • Cambios pendientes: {stats['pendientes']['total_pendientes']}")
    print(f"   • Registros en caché: {stats['cache']['registros_cache']}")

    if stats['historial']['total_syncs']:
        print(f"\n📈 Últimos 30 días:")
        print(f"   • Sincronizaciones: {stats['historial']['total_syncs']}")
        print(f"   • Registros procesados: {stats['historial']['total_procesados']}")

    print("\n" + "=" * 60)
