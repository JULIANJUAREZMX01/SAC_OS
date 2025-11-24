"""
===============================================================
MÓDULO DE BASE DE DATOS LOCAL - SQLite
Sistema de Automatización de Consultas - CEDIS Cancún 427
===============================================================

Este módulo proporciona almacenamiento local con SQLite para:
- Histórico de validaciones de OC
- Registro de errores detectados
- Métricas y estadísticas
- Auditoría de operaciones
- Caché de consultas frecuentes

Uso:
    from modules.db_local import DBLocal, HistoricoOC, RegistroError

    # Crear instancia
    db = DBLocal()

    # Guardar validación
    db.guardar_validacion_oc(oc_numero, resultado, errores)

    # Consultar histórico
    historial = db.obtener_historial_oc(dias=30)

    # Obtener estadísticas
    stats = db.obtener_estadisticas()

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
===============================================================
"""

import sqlite3
import logging
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, field, asdict
from contextlib import contextmanager
from enum import Enum

# Configurar logger
logger = logging.getLogger(__name__)


# ===============================================================
# ENUMERACIONES Y CONSTANTES
# ===============================================================

class TipoOperacion(Enum):
    """Tipos de operaciones registradas"""
    VALIDACION_OC = "validacion_oc"
    REPORTE_DIARIO = "reporte_diario"
    ALERTA_ENVIADA = "alerta_enviada"
    CONSULTA_DB2 = "consulta_db2"
    ERROR_SISTEMA = "error_sistema"
    # Nuevas operaciones DML/DDL
    DML_INSERT = "dml_insert"
    DML_UPDATE = "dml_update"
    DML_DELETE = "dml_delete"
    DDL_CREATE = "ddl_create"
    DDL_ALTER = "ddl_alter"
    DDL_DROP = "ddl_drop"
    SINCRONIZACION = "sincronizacion"


class NivelConfirmacion(Enum):
    """Niveles de confirmación requeridos para operaciones"""
    NINGUNO = 0       # SELECT, consultas de lectura
    BAJO = 1          # INSERT
    MEDIO = 2         # UPDATE
    ALTO = 3          # DELETE (requiere confirmación)
    CRITICO = 4       # DROP, TRUNCATE (requiere doble confirmación)


class ResultadoValidacion(Enum):
    """Resultados posibles de validación"""
    EXITOSO = "exitoso"
    CON_ERRORES = "con_errores"
    CRITICO = "critico"
    FALLIDO = "fallido"


# ===============================================================
# DATA CLASSES
# ===============================================================

@dataclass
class HistoricoOC:
    """Registro histórico de validación de OC"""
    id: Optional[int] = None
    oc_numero: str = ""
    fecha_validacion: datetime = field(default_factory=datetime.now)
    resultado: str = ResultadoValidacion.EXITOSO.value
    total_oc: float = 0.0
    total_distro: float = 0.0
    diferencia: float = 0.0
    num_errores: int = 0
    num_criticos: int = 0
    tiempo_ejecucion: float = 0.0
    usuario: str = "SISTEMA"
    detalles_json: str = "{}"


@dataclass
class RegistroError:
    """Registro de error detectado"""
    id: Optional[int] = None
    fecha: datetime = field(default_factory=datetime.now)
    tipo_error: str = ""
    severidad: str = "MEDIO"
    mensaje: str = ""
    modulo: str = ""
    oc_relacionada: Optional[str] = None
    solucion_aplicada: Optional[str] = None
    resuelto: bool = False
    detalles_json: str = "{}"


@dataclass
class MetricaDiaria:
    """Métricas diarias del sistema"""
    id: Optional[int] = None
    fecha: datetime = field(default_factory=datetime.now)
    total_validaciones: int = 0
    validaciones_exitosas: int = 0
    validaciones_fallidas: int = 0
    total_errores: int = 0
    errores_criticos: int = 0
    tiempo_promedio: float = 0.0
    alertas_enviadas: int = 0
    reportes_generados: int = 0


# ===============================================================
# CLASE PRINCIPAL
# ===============================================================

class DBLocal:
    """
    Gestor de base de datos local SQLite para el sistema SAC.

    Proporciona:
    - Almacenamiento persistente de históricos
    - Registro de errores y auditoría
    - Métricas y estadísticas
    - Consultas optimizadas con índices

    Ejemplo:
        >>> db = DBLocal()
        >>> db.guardar_validacion_oc("OC123", "exitoso", [])
        >>> historial = db.obtener_historial_oc(dias=7)
    """

    # Ruta por defecto de la base de datos
    DEFAULT_DB_PATH = Path(__file__).parent.parent / "output" / "sac_historico.db"

    def __init__(self, db_path: Optional[Path] = None):
        """
        Inicializa la conexión a la base de datos local.

        Args:
            db_path: Ruta al archivo SQLite (opcional)
        """
        self.db_path = db_path or self.DEFAULT_DB_PATH

        # Asegurar que el directorio existe
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Inicializar base de datos
        self._inicializar_db()

        logger.info(f"💾 Base de datos local inicializada: {self.db_path}")

    @contextmanager
    def _get_connection(self):
        """Context manager para conexiones a SQLite."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Error en transacción SQLite: {e}")
            raise
        finally:
            conn.close()

    def _inicializar_db(self):
        """Crea las tablas si no existen."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Tabla de histórico de OC
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS historico_oc (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    oc_numero TEXT NOT NULL,
                    fecha_validacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resultado TEXT NOT NULL,
                    total_oc REAL DEFAULT 0,
                    total_distro REAL DEFAULT 0,
                    diferencia REAL DEFAULT 0,
                    num_errores INTEGER DEFAULT 0,
                    num_criticos INTEGER DEFAULT 0,
                    tiempo_ejecucion REAL DEFAULT 0,
                    usuario TEXT DEFAULT 'SISTEMA',
                    detalles_json TEXT DEFAULT '{}'
                )
            """)

            # Tabla de errores
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS registro_errores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    tipo_error TEXT NOT NULL,
                    severidad TEXT DEFAULT 'MEDIO',
                    mensaje TEXT,
                    modulo TEXT,
                    oc_relacionada TEXT,
                    solucion_aplicada TEXT,
                    resuelto INTEGER DEFAULT 0,
                    detalles_json TEXT DEFAULT '{}'
                )
            """)

            # Tabla de métricas diarias
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metricas_diarias (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha DATE UNIQUE NOT NULL,
                    total_validaciones INTEGER DEFAULT 0,
                    validaciones_exitosas INTEGER DEFAULT 0,
                    validaciones_fallidas INTEGER DEFAULT 0,
                    total_errores INTEGER DEFAULT 0,
                    errores_criticos INTEGER DEFAULT 0,
                    tiempo_promedio REAL DEFAULT 0,
                    alertas_enviadas INTEGER DEFAULT 0,
                    reportes_generados INTEGER DEFAULT 0
                )
            """)

            # Tabla de auditoría
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS auditoria (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    tipo_operacion TEXT NOT NULL,
                    usuario TEXT DEFAULT 'SISTEMA',
                    descripcion TEXT,
                    ip_origen TEXT,
                    detalles_json TEXT DEFAULT '{}'
                )
            """)

            # Tabla de caché de consultas
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cache_consultas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    clave TEXT UNIQUE NOT NULL,
                    valor_json TEXT NOT NULL,
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    fecha_expiracion TIMESTAMP,
                    hits INTEGER DEFAULT 0
                )
            """)

            # Crear índices para optimización
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_historico_oc_numero ON historico_oc(oc_numero)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_historico_fecha ON historico_oc(fecha_validacion)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_errores_fecha ON registro_errores(fecha)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_errores_severidad ON registro_errores(severidad)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_metricas_fecha ON metricas_diarias(fecha)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_cache_clave ON cache_consultas(clave)")

            logger.info("✅ Tablas de base de datos local verificadas/creadas")

    # ===============================================================
    # MÉTODOS DE HISTÓRICO DE OC
    # ===============================================================

    def guardar_validacion_oc(
        self,
        oc_numero: str,
        resultado: str,
        errores: List[Any] = None,
        total_oc: float = 0,
        total_distro: float = 0,
        tiempo_ejecucion: float = 0,
        usuario: str = "SISTEMA",
        detalles: Dict = None
    ) -> int:
        """
        Guarda el resultado de una validación de OC.

        Args:
            oc_numero: Número de la OC validada
            resultado: Resultado de la validación
            errores: Lista de errores detectados
            total_oc: Total de la OC
            total_distro: Total de distribuciones
            tiempo_ejecucion: Tiempo de ejecución en segundos
            usuario: Usuario que ejecutó la validación
            detalles: Detalles adicionales

        Returns:
            ID del registro creado
        """
        errores = errores or []
        detalles = detalles or {}

        num_errores = len(errores)
        num_criticos = sum(1 for e in errores if hasattr(e, 'severidad') and 'CRÍTICO' in str(e.severidad))

        # Serializar errores para JSON
        errores_serializados = []
        for e in errores:
            if hasattr(e, '__dict__'):
                errores_serializados.append({
                    'tipo': getattr(e, 'tipo', 'DESCONOCIDO'),
                    'severidad': str(getattr(e, 'severidad', 'MEDIO')),
                    'mensaje': getattr(e, 'mensaje', str(e))
                })
            else:
                errores_serializados.append(str(e))

        detalles['errores'] = errores_serializados

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO historico_oc
                (oc_numero, resultado, total_oc, total_distro, diferencia,
                 num_errores, num_criticos, tiempo_ejecucion, usuario, detalles_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                oc_numero,
                resultado,
                total_oc,
                total_distro,
                total_oc - total_distro,
                num_errores,
                num_criticos,
                tiempo_ejecucion,
                usuario,
                json.dumps(detalles, default=str)
            ))

            record_id = cursor.lastrowid

            # Actualizar métricas diarias
            self._actualizar_metricas_validacion(
                exitoso=(resultado == ResultadoValidacion.EXITOSO.value),
                num_errores=num_errores,
                num_criticos=num_criticos,
                tiempo=tiempo_ejecucion
            )

            logger.info(f"💾 Validación de OC {oc_numero} guardada (ID: {record_id})")
            return record_id

    def obtener_historial_oc(
        self,
        oc_numero: Optional[str] = None,
        dias: int = 30,
        limite: int = 100
    ) -> List[Dict]:
        """
        Obtiene el historial de validaciones de OC.

        Args:
            oc_numero: Filtrar por OC específica
            dias: Número de días hacia atrás
            limite: Máximo de registros

        Returns:
            Lista de registros históricos
        """
        fecha_inicio = datetime.now() - timedelta(days=dias)

        with self._get_connection() as conn:
            cursor = conn.cursor()

            if oc_numero:
                cursor.execute("""
                    SELECT * FROM historico_oc
                    WHERE oc_numero = ? AND fecha_validacion >= ?
                    ORDER BY fecha_validacion DESC
                    LIMIT ?
                """, (oc_numero, fecha_inicio, limite))
            else:
                cursor.execute("""
                    SELECT * FROM historico_oc
                    WHERE fecha_validacion >= ?
                    ORDER BY fecha_validacion DESC
                    LIMIT ?
                """, (fecha_inicio, limite))

            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def obtener_ultima_validacion_oc(self, oc_numero: str) -> Optional[Dict]:
        """Obtiene la última validación de una OC específica."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM historico_oc
                WHERE oc_numero = ?
                ORDER BY fecha_validacion DESC
                LIMIT 1
            """, (oc_numero,))

            row = cursor.fetchone()
            return dict(row) if row else None

    # ===============================================================
    # MÉTODOS DE REGISTRO DE ERRORES
    # ===============================================================

    def registrar_error(
        self,
        tipo_error: str,
        severidad: str,
        mensaje: str,
        modulo: str = "SISTEMA",
        oc_relacionada: Optional[str] = None,
        detalles: Dict = None
    ) -> int:
        """
        Registra un error en la base de datos.

        Args:
            tipo_error: Tipo de error
            severidad: Nivel de severidad
            mensaje: Mensaje descriptivo
            modulo: Módulo donde ocurrió
            oc_relacionada: OC relacionada (si aplica)
            detalles: Detalles adicionales

        Returns:
            ID del registro
        """
        detalles = detalles or {}

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO registro_errores
                (tipo_error, severidad, mensaje, modulo, oc_relacionada, detalles_json)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                tipo_error,
                severidad,
                mensaje,
                modulo,
                oc_relacionada,
                json.dumps(detalles, default=str)
            ))

            record_id = cursor.lastrowid
            logger.info(f"💾 Error registrado (ID: {record_id}, Tipo: {tipo_error})")
            return record_id

    def obtener_errores(
        self,
        severidad: Optional[str] = None,
        no_resueltos: bool = False,
        dias: int = 7,
        limite: int = 100
    ) -> List[Dict]:
        """
        Obtiene errores registrados.

        Args:
            severidad: Filtrar por severidad
            no_resueltos: Solo errores no resueltos
            dias: Días hacia atrás
            limite: Máximo de registros

        Returns:
            Lista de errores
        """
        fecha_inicio = datetime.now() - timedelta(days=dias)

        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM registro_errores WHERE fecha >= ?"
            params = [fecha_inicio]

            if severidad:
                query += " AND severidad = ?"
                params.append(severidad)

            if no_resueltos:
                query += " AND resuelto = 0"

            query += " ORDER BY fecha DESC LIMIT ?"
            params.append(limite)

            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def marcar_error_resuelto(self, error_id: int, solucion: str = None) -> bool:
        """Marca un error como resuelto."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE registro_errores
                SET resuelto = 1, solucion_aplicada = ?
                WHERE id = ?
            """, (solucion, error_id))

            return cursor.rowcount > 0

    # ===============================================================
    # MÉTODOS DE MÉTRICAS
    # ===============================================================

    def _actualizar_metricas_validacion(
        self,
        exitoso: bool,
        num_errores: int,
        num_criticos: int,
        tiempo: float
    ):
        """Actualiza métricas diarias con una validación."""
        fecha_hoy = datetime.now().date()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Verificar si existe registro para hoy
            cursor.execute(
                "SELECT id, total_validaciones, tiempo_promedio FROM metricas_diarias WHERE fecha = ?",
                (fecha_hoy,)
            )
            row = cursor.fetchone()

            if row:
                # Actualizar registro existente
                total_prev = row['total_validaciones']
                tiempo_prev = row['tiempo_promedio']
                nuevo_promedio = ((tiempo_prev * total_prev) + tiempo) / (total_prev + 1)

                cursor.execute("""
                    UPDATE metricas_diarias SET
                        total_validaciones = total_validaciones + 1,
                        validaciones_exitosas = validaciones_exitosas + ?,
                        validaciones_fallidas = validaciones_fallidas + ?,
                        total_errores = total_errores + ?,
                        errores_criticos = errores_criticos + ?,
                        tiempo_promedio = ?
                    WHERE fecha = ?
                """, (
                    1 if exitoso else 0,
                    0 if exitoso else 1,
                    num_errores,
                    num_criticos,
                    nuevo_promedio,
                    fecha_hoy
                ))
            else:
                # Crear nuevo registro
                cursor.execute("""
                    INSERT INTO metricas_diarias
                    (fecha, total_validaciones, validaciones_exitosas, validaciones_fallidas,
                     total_errores, errores_criticos, tiempo_promedio)
                    VALUES (?, 1, ?, ?, ?, ?, ?)
                """, (
                    fecha_hoy,
                    1 if exitoso else 0,
                    0 if exitoso else 1,
                    num_errores,
                    num_criticos,
                    tiempo
                ))

    def obtener_metricas_diarias(self, dias: int = 30) -> List[Dict]:
        """Obtiene métricas de los últimos N días."""
        fecha_inicio = datetime.now().date() - timedelta(days=dias)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM metricas_diarias
                WHERE fecha >= ?
                ORDER BY fecha DESC
            """, (fecha_inicio,))

            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def obtener_estadisticas(self, dias: int = 30) -> Dict:
        """
        Obtiene estadísticas agregadas del sistema.

        Args:
            dias: Período de análisis

        Returns:
            Diccionario con estadísticas
        """
        fecha_inicio = datetime.now() - timedelta(days=dias)

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Estadísticas de validaciones
            cursor.execute("""
                SELECT
                    COUNT(*) as total_validaciones,
                    SUM(CASE WHEN resultado = 'exitoso' THEN 1 ELSE 0 END) as exitosas,
                    SUM(CASE WHEN resultado != 'exitoso' THEN 1 ELSE 0 END) as fallidas,
                    AVG(tiempo_ejecucion) as tiempo_promedio,
                    SUM(num_errores) as total_errores,
                    SUM(num_criticos) as total_criticos,
                    COUNT(DISTINCT oc_numero) as oc_unicas
                FROM historico_oc
                WHERE fecha_validacion >= ?
            """, (fecha_inicio,))

            validaciones = dict(cursor.fetchone())

            # Estadísticas de errores
            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN severidad LIKE '%CRÍTICO%' THEN 1 ELSE 0 END) as criticos,
                    SUM(CASE WHEN severidad LIKE '%ALTO%' THEN 1 ELSE 0 END) as altos,
                    SUM(CASE WHEN resuelto = 0 THEN 1 ELSE 0 END) as no_resueltos
                FROM registro_errores
                WHERE fecha >= ?
            """, (fecha_inicio,))

            errores = dict(cursor.fetchone())

            # Top OCs con más problemas
            cursor.execute("""
                SELECT oc_numero, COUNT(*) as validaciones, SUM(num_errores) as errores
                FROM historico_oc
                WHERE fecha_validacion >= ? AND num_errores > 0
                GROUP BY oc_numero
                ORDER BY errores DESC
                LIMIT 10
            """, (fecha_inicio,))

            top_problematicas = [dict(row) for row in cursor.fetchall()]

            return {
                'periodo_dias': dias,
                'validaciones': validaciones,
                'errores': errores,
                'top_oc_problematicas': top_problematicas,
                'tasa_exito': (
                    (validaciones['exitosas'] / validaciones['total_validaciones'] * 100)
                    if validaciones['total_validaciones'] > 0 else 0
                )
            }

    # ===============================================================
    # MÉTODOS DE AUDITORÍA
    # ===============================================================

    def registrar_auditoria(
        self,
        tipo_operacion: str,
        descripcion: str,
        usuario: str = "SISTEMA",
        detalles: Dict = None
    ) -> int:
        """Registra una operación en auditoría."""
        detalles = detalles or {}

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO auditoria (tipo_operacion, usuario, descripcion, detalles_json)
                VALUES (?, ?, ?, ?)
            """, (tipo_operacion, usuario, descripcion, json.dumps(detalles, default=str)))

            return cursor.lastrowid

    def obtener_auditoria(self, dias: int = 7, limite: int = 100) -> List[Dict]:
        """Obtiene registros de auditoría."""
        fecha_inicio = datetime.now() - timedelta(days=dias)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM auditoria
                WHERE fecha >= ?
                ORDER BY fecha DESC
                LIMIT ?
            """, (fecha_inicio, limite))

            return [dict(row) for row in cursor.fetchall()]

    # ===============================================================
    # MÉTODOS DE CACHÉ
    # ===============================================================

    def guardar_cache(self, clave: str, valor: Any, ttl_minutos: int = 60) -> bool:
        """
        Guarda un valor en caché.

        Args:
            clave: Clave única
            valor: Valor a guardar (serializable a JSON)
            ttl_minutos: Tiempo de vida en minutos

        Returns:
            True si se guardó correctamente
        """
        expiracion = datetime.now() + timedelta(minutes=ttl_minutos)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO cache_consultas (clave, valor_json, fecha_expiracion, hits)
                VALUES (?, ?, ?, COALESCE((SELECT hits FROM cache_consultas WHERE clave = ?), 0))
            """, (clave, json.dumps(valor, default=str), expiracion, clave))

            return cursor.rowcount > 0

    def obtener_cache(self, clave: str) -> Optional[Any]:
        """
        Obtiene un valor del caché.

        Args:
            clave: Clave a buscar

        Returns:
            Valor guardado o None si expiró/no existe
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT valor_json FROM cache_consultas
                WHERE clave = ? AND fecha_expiracion > ?
            """, (clave, datetime.now()))

            row = cursor.fetchone()
            if row:
                # Incrementar hits
                cursor.execute(
                    "UPDATE cache_consultas SET hits = hits + 1 WHERE clave = ?",
                    (clave,)
                )
                return json.loads(row['valor_json'])

            return None

    def limpiar_cache_expirado(self) -> int:
        """Elimina entradas de caché expiradas."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM cache_consultas WHERE fecha_expiracion <= ?",
                (datetime.now(),)
            )
            eliminados = cursor.rowcount
            logger.info(f"🗑️ Cache limpiado: {eliminados} entradas eliminadas")
            return eliminados

    # ===============================================================
    # MÉTODOS DE UTILIDAD
    # ===============================================================

    def ejecutar_query(self, query: str, params: Tuple = ()) -> List[Dict]:
        """Ejecuta una consulta SQL personalizada."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def obtener_info_db(self) -> Dict:
        """Obtiene información sobre la base de datos."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Contar registros por tabla
            tablas = ['historico_oc', 'registro_errores', 'metricas_diarias', 'auditoria', 'cache_consultas']
            conteos = {}

            for tabla in tablas:
                cursor.execute(f"SELECT COUNT(*) FROM {tabla}")
                conteos[tabla] = cursor.fetchone()[0]

            # Tamaño del archivo
            import os
            tamanio_bytes = os.path.getsize(self.db_path) if self.db_path.exists() else 0

            return {
                'ruta': str(self.db_path),
                'tamanio_mb': round(tamanio_bytes / (1024 * 1024), 2),
                'registros': conteos,
                'total_registros': sum(conteos.values())
            }

    def vaciar_tabla(self, tabla: str) -> bool:
        """Vacía una tabla específica (usar con precaución)."""
        tablas_validas = ['historico_oc', 'registro_errores', 'metricas_diarias', 'auditoria', 'cache_consultas']

        if tabla not in tablas_validas:
            logger.error(f"❌ Tabla no válida: {tabla}")
            return False

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM {tabla}")
            logger.warning(f"⚠️ Tabla {tabla} vaciada")
            return True

    def limpiar_historial_antiguo(self, dias: int = 90) -> Dict[str, int]:
        """
        Elimina registros más antiguos que N días.

        Args:
            dias: Días a mantener (elimina registros anteriores)

        Returns:
            Diccionario con conteos de registros eliminados por tabla
        """
        fecha_limite = datetime.now() - timedelta(days=dias)
        eliminados = {}

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Limpiar histórico de OC
            cursor.execute(
                "DELETE FROM historico_oc WHERE fecha_validacion < ?",
                (fecha_limite,)
            )
            eliminados['historico_oc'] = cursor.rowcount

            # Limpiar errores resueltos antiguos
            cursor.execute(
                "DELETE FROM registro_errores WHERE fecha < ? AND resuelto = 1",
                (fecha_limite,)
            )
            eliminados['registro_errores'] = cursor.rowcount

            # Limpiar métricas antiguas
            cursor.execute(
                "DELETE FROM metricas_diarias WHERE fecha < ?",
                (fecha_limite.date(),)
            )
            eliminados['metricas_diarias'] = cursor.rowcount

            # Limpiar auditoría antigua
            cursor.execute(
                "DELETE FROM auditoria WHERE fecha < ?",
                (fecha_limite,)
            )
            eliminados['auditoria'] = cursor.rowcount

            # Limpiar caché expirado
            cursor.execute(
                "DELETE FROM cache_consultas WHERE fecha_expiracion < ?",
                (datetime.now(),)
            )
            eliminados['cache_consultas'] = cursor.rowcount

        total = sum(eliminados.values())
        logger.info(f"🗑️ Limpieza completada: {total} registros eliminados")
        for tabla, count in eliminados.items():
            if count > 0:
                logger.info(f"   • {tabla}: {count} registros")

        return eliminados

    def exportar_a_json(self, archivo: str = None) -> str:
        """Exporta toda la base de datos a JSON."""
        archivo = archivo or f"sac_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        datos = {
            'exportado_en': datetime.now().isoformat(),
            'historico_oc': self.obtener_historial_oc(dias=365, limite=10000),
            'errores': self.obtener_errores(dias=365, limite=10000),
            'metricas': self.obtener_metricas_diarias(dias=365),
            'auditoria': self.obtener_auditoria(dias=365, limite=10000)
        }

        ruta_archivo = self.db_path.parent / archivo
        with open(ruta_archivo, 'w', encoding='utf-8') as f:
            json.dump(datos, f, indent=2, default=str, ensure_ascii=False)

        logger.info(f"💾 Base de datos exportada a: {ruta_archivo}")
        return str(ruta_archivo)


# ===============================================================
# CLASE DE SEGURIDAD PARA OPERACIONES DML/DDL
# ===============================================================

class OperacionPendiente:
    """Representa una operación DML/DDL pendiente de confirmación"""

    def __init__(
        self,
        sql: str,
        tipo: TipoOperacion,
        nivel_confirmacion: NivelConfirmacion,
        descripcion: str,
        usuario: str = "SISTEMA",
        datos_afectados: Dict = None
    ):
        self.id = datetime.now().strftime('%Y%m%d%H%M%S%f')
        self.sql = sql
        self.tipo = tipo
        self.nivel_confirmacion = nivel_confirmacion
        self.descripcion = descripcion
        self.usuario = usuario
        self.datos_afectados = datos_afectados or {}
        self.creada_en = datetime.now()
        self.confirmada = False
        self.ejecutada = False
        self.resultado = None


class GestorOperacionesSeguras:
    """
    Gestor de operaciones DML/DDL con confirmación obligatoria.

    REGLAS DE SEGURIDAD:
    - SELECT: Sin confirmación
    - INSERT: Confirmación simple (nivel BAJO)
    - UPDATE: Confirmación con preview de datos afectados (nivel MEDIO)
    - DELETE: Confirmación obligatoria con código de seguridad (nivel ALTO)
    - DROP/TRUNCATE: Doble confirmación + código de seguridad (nivel CRITICO)

    Ejemplo:
        >>> gestor = GestorOperacionesSeguras(db)
        >>> op = gestor.preparar_delete("DELETE FROM tabla WHERE id = 1")
        >>> print(op.descripcion)  # Muestra qué se va a borrar
        >>> gestor.confirmar_operacion(op.id, codigo_confirmacion="CONFIRMAR-DELETE")
    """

    # Código de confirmación para operaciones destructivas
    CODIGO_DELETE = "CONFIRMAR-DELETE"
    CODIGO_DROP = "CONFIRMAR-DROP-PERMANENTE"

    def __init__(self, db_local: 'DBLocal'):
        self.db = db_local
        self._operaciones_pendientes: Dict[str, OperacionPendiente] = {}
        self._historial_operaciones: List[OperacionPendiente] = []
        logger.info("🔒 GestorOperacionesSeguras inicializado")

    def _detectar_tipo_operacion(self, sql: str) -> Tuple[TipoOperacion, NivelConfirmacion]:
        """Detecta el tipo de operación SQL y su nivel de confirmación requerido."""
        sql_upper = sql.strip().upper()

        if sql_upper.startswith('SELECT'):
            return None, NivelConfirmacion.NINGUNO
        elif sql_upper.startswith('INSERT'):
            return TipoOperacion.DML_INSERT, NivelConfirmacion.BAJO
        elif sql_upper.startswith('UPDATE'):
            return TipoOperacion.DML_UPDATE, NivelConfirmacion.MEDIO
        elif sql_upper.startswith('DELETE'):
            return TipoOperacion.DML_DELETE, NivelConfirmacion.ALTO
        elif sql_upper.startswith('CREATE'):
            return TipoOperacion.DDL_CREATE, NivelConfirmacion.BAJO
        elif sql_upper.startswith('ALTER'):
            return TipoOperacion.DDL_ALTER, NivelConfirmacion.MEDIO
        elif sql_upper.startswith('DROP') or sql_upper.startswith('TRUNCATE'):
            return TipoOperacion.DDL_DROP, NivelConfirmacion.CRITICO
        else:
            return None, NivelConfirmacion.NINGUNO

    def _obtener_preview_datos(self, sql: str) -> Dict:
        """Obtiene preview de los datos que serán afectados por la operación."""
        sql_upper = sql.strip().upper()
        preview = {'registros_afectados': 0, 'muestra': []}

        try:
            # Para DELETE, obtener los registros que se eliminarán
            if sql_upper.startswith('DELETE'):
                # Convertir DELETE a SELECT para preview
                # DELETE FROM tabla WHERE condicion -> SELECT * FROM tabla WHERE condicion
                partes = sql_upper.split('WHERE')
                if len(partes) > 1:
                    tabla = sql_upper.split('FROM')[1].split('WHERE')[0].strip()
                    condicion = sql.split('WHERE')[1] if 'WHERE' in sql.upper() else '1=1'
                    select_sql = f"SELECT * FROM {tabla} WHERE {condicion} LIMIT 10"
                    preview['muestra'] = self.db.ejecutar_query(select_sql)
                    # Contar total
                    count_sql = f"SELECT COUNT(*) as total FROM {tabla} WHERE {condicion}"
                    result = self.db.ejecutar_query(count_sql)
                    preview['registros_afectados'] = result[0]['total'] if result else 0

            # Para UPDATE, mostrar registros que se modificarán
            elif sql_upper.startswith('UPDATE'):
                partes = sql_upper.split('SET')
                if len(partes) > 1:
                    tabla = partes[0].replace('UPDATE', '').strip()
                    condicion = sql.split('WHERE')[1] if 'WHERE' in sql.upper() else '1=1'
                    select_sql = f"SELECT * FROM {tabla} WHERE {condicion} LIMIT 10"
                    preview['muestra'] = self.db.ejecutar_query(select_sql)
                    count_sql = f"SELECT COUNT(*) as total FROM {tabla} WHERE {condicion}"
                    result = self.db.ejecutar_query(count_sql)
                    preview['registros_afectados'] = result[0]['total'] if result else 0

        except Exception as e:
            logger.warning(f"⚠️ No se pudo obtener preview: {e}")
            preview['error'] = str(e)

        return preview

    def preparar_operacion(
        self,
        sql: str,
        usuario: str = "SISTEMA",
        descripcion: str = None
    ) -> Optional[OperacionPendiente]:
        """
        Prepara una operación DML/DDL para confirmación.

        Args:
            sql: Consulta SQL a ejecutar
            usuario: Usuario que solicita la operación
            descripcion: Descripción opcional

        Returns:
            OperacionPendiente si requiere confirmación, None si es SELECT
        """
        tipo, nivel = self._detectar_tipo_operacion(sql)

        # SELECT no requiere confirmación
        if nivel == NivelConfirmacion.NINGUNO:
            return None

        # Obtener preview de datos afectados
        preview = self._obtener_preview_datos(sql)

        # Crear descripción automática si no se proporciona
        if not descripcion:
            descripcion = f"Operación {tipo.value if tipo else 'desconocida'}"
            if preview['registros_afectados'] > 0:
                descripcion += f" - {preview['registros_afectados']} registros afectados"

        operacion = OperacionPendiente(
            sql=sql,
            tipo=tipo,
            nivel_confirmacion=nivel,
            descripcion=descripcion,
            usuario=usuario,
            datos_afectados=preview
        )

        self._operaciones_pendientes[operacion.id] = operacion

        # Log según nivel
        if nivel == NivelConfirmacion.CRITICO:
            logger.warning(f"🚨 OPERACIÓN CRÍTICA PENDIENTE: {descripcion}")
            logger.warning(f"   ID: {operacion.id}")
            logger.warning(f"   Requiere código: {self.CODIGO_DROP}")
        elif nivel == NivelConfirmacion.ALTO:
            logger.warning(f"⚠️ OPERACIÓN DE BORRADO PENDIENTE: {descripcion}")
            logger.warning(f"   ID: {operacion.id}")
            logger.warning(f"   Requiere código: {self.CODIGO_DELETE}")
        else:
            logger.info(f"📝 Operación pendiente: {descripcion} (ID: {operacion.id})")

        return operacion

    def confirmar_operacion(
        self,
        operacion_id: str,
        codigo_confirmacion: str = None,
        confirmacion_adicional: bool = False
    ) -> Tuple[bool, str, Any]:
        """
        Confirma y ejecuta una operación pendiente.

        Args:
            operacion_id: ID de la operación a confirmar
            codigo_confirmacion: Código requerido para DELETE/DROP
            confirmacion_adicional: Segunda confirmación para operaciones CRITICAS

        Returns:
            Tuple (exito, mensaje, resultado)
        """
        if operacion_id not in self._operaciones_pendientes:
            return False, "Operación no encontrada o ya ejecutada", None

        op = self._operaciones_pendientes[operacion_id]

        # Verificar código de confirmación según nivel
        if op.nivel_confirmacion == NivelConfirmacion.ALTO:
            if codigo_confirmacion != self.CODIGO_DELETE:
                return False, f"Código de confirmación incorrecto. Use: {self.CODIGO_DELETE}", None

        elif op.nivel_confirmacion == NivelConfirmacion.CRITICO:
            if codigo_confirmacion != self.CODIGO_DROP:
                return False, f"Código de confirmación incorrecto. Use: {self.CODIGO_DROP}", None
            if not confirmacion_adicional:
                return False, "Operación CRÍTICA requiere confirmacion_adicional=True", None

        # Ejecutar la operación
        try:
            op.confirmada = True

            with self.db._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(op.sql)
                filas_afectadas = cursor.rowcount

            op.ejecutada = True
            op.resultado = {'filas_afectadas': filas_afectadas}

            # Registrar en auditoría
            self.db.registrar_auditoria(
                tipo_operacion=op.tipo.value if op.tipo else "DML",
                descripcion=op.descripcion,
                usuario=op.usuario,
                detalles={
                    'sql': op.sql,
                    'filas_afectadas': filas_afectadas,
                    'nivel_confirmacion': op.nivel_confirmacion.name,
                    'operacion_id': op.id
                }
            )

            # Mover a historial
            self._historial_operaciones.append(op)
            del self._operaciones_pendientes[operacion_id]

            logger.info(f"✅ Operación {operacion_id} ejecutada: {filas_afectadas} filas afectadas")
            return True, f"Operación ejecutada correctamente ({filas_afectadas} filas)", op.resultado

        except Exception as e:
            logger.error(f"❌ Error ejecutando operación {operacion_id}: {e}")
            return False, f"Error: {str(e)}", None

    def cancelar_operacion(self, operacion_id: str) -> bool:
        """Cancela una operación pendiente."""
        if operacion_id in self._operaciones_pendientes:
            op = self._operaciones_pendientes[operacion_id]
            del self._operaciones_pendientes[operacion_id]
            logger.info(f"🚫 Operación {operacion_id} cancelada: {op.descripcion}")
            return True
        return False

    def listar_operaciones_pendientes(self) -> List[Dict]:
        """Lista todas las operaciones pendientes de confirmación."""
        return [
            {
                'id': op.id,
                'tipo': op.tipo.value if op.tipo else None,
                'nivel': op.nivel_confirmacion.name,
                'descripcion': op.descripcion,
                'usuario': op.usuario,
                'creada_en': op.creada_en.isoformat(),
                'registros_afectados': op.datos_afectados.get('registros_afectados', 0)
            }
            for op in self._operaciones_pendientes.values()
        ]

    def ejecutar_select(self, sql: str) -> List[Dict]:
        """Ejecuta consulta SELECT directamente (sin confirmación)."""
        if not sql.strip().upper().startswith('SELECT'):
            raise ValueError("Solo se permiten consultas SELECT con este método")
        return self.db.ejecutar_query(sql)

    def limpiar_pendientes_expiradas(self, minutos: int = 30) -> int:
        """Limpia operaciones pendientes más antiguas que N minutos."""
        ahora = datetime.now()
        expiradas = [
            op_id for op_id, op in self._operaciones_pendientes.items()
            if (ahora - op.creada_en).total_seconds() > minutos * 60
        ]

        for op_id in expiradas:
            del self._operaciones_pendientes[op_id]

        if expiradas:
            logger.info(f"🗑️ {len(expiradas)} operaciones pendientes expiradas eliminadas")

        return len(expiradas)


# ===============================================================
# INSTANCIA GLOBAL (SINGLETON)
# ===============================================================

_db_instance: Optional[DBLocal] = None
_gestor_seguro: Optional[GestorOperacionesSeguras] = None


def get_db_local() -> DBLocal:
    """Obtiene la instancia global de la base de datos local."""
    global _db_instance
    if _db_instance is None:
        _db_instance = DBLocal()
    return _db_instance


def get_gestor_operaciones() -> GestorOperacionesSeguras:
    """Obtiene la instancia global del gestor de operaciones seguras."""
    global _gestor_seguro
    if _gestor_seguro is None:
        _gestor_seguro = GestorOperacionesSeguras(get_db_local())
    return _gestor_seguro


# ===============================================================
# EXPORTAR
# ===============================================================

__all__ = [
    # Base de datos local
    'DBLocal',
    'get_db_local',
    # Gestor de operaciones seguras
    'GestorOperacionesSeguras',
    'get_gestor_operaciones',
    'OperacionPendiente',
    'NivelConfirmacion',
    # Data classes
    'HistoricoOC',
    'RegistroError',
    'MetricaDiaria',
    # Enums
    'TipoOperacion',
    'ResultadoValidacion',
]


# ===============================================================
# EJECUCIÓN DIRECTA
# ===============================================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("💾 BASE DE DATOS LOCAL - SAC CEDIS 427")
    print("=" * 60)

    # Crear instancia
    db = DBLocal()

    # Mostrar información
    info = db.obtener_info_db()
    print(f"\n📁 Ruta: {info['ruta']}")
    print(f"📊 Tamaño: {info['tamanio_mb']} MB")
    print(f"\n📋 Registros por tabla:")
    for tabla, conteo in info['registros'].items():
        print(f"   • {tabla}: {conteo}")

    print(f"\n   Total: {info['total_registros']} registros")

    # Mostrar estadísticas si hay datos
    stats = db.obtener_estadisticas()
    if stats['validaciones']['total_validaciones']:
        print(f"\n📈 Estadísticas (últimos 30 días):")
        print(f"   • Validaciones: {stats['validaciones']['total_validaciones']}")
        print(f"   • Tasa de éxito: {stats['tasa_exito']:.1f}%")

    print("\n" + "=" * 60)
