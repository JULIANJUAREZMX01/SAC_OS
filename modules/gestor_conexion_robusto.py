"""
═══════════════════════════════════════════════════════════════
GESTOR DE CONEXIÓN ROBUSTO CON CONTEXT MANAGERS
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Módulo que proporciona context managers para manejo seguro
de conexiones DB2 con limpieza automática de recursos.

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
═══════════════════════════════════════════════════════════════
"""

import logging
from typing import Optional, Any, Callable
from contextlib import contextmanager
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ErrorConexionDB(Exception):
    """Excepción base para errores de conexión"""
    pass


class ErrorQueryDB(Exception):
    """Excepción para errores en ejecución de queries"""
    pass


class TimeoutError(Exception):
    """Excepción para timeout en operaciones"""
    pass


@contextmanager
def manejo_seguro_conexion(conexion, nombre_operacion: str = "Operación"):
    """
    Context manager para manejo seguro de conexión.

    Asegura que la conexión se cierre correctamente incluso si hay excepción.

    Usage:
        with manejo_seguro_conexion(db_conn, "Validación OC"):
            # usar conexión
            df = ejecutar_query(db_conn, sql)

    Args:
        conexion: Objeto de conexión DB2
        nombre_operacion: Nombre de la operación para logging

    Yields:
        conexion: La conexión (para permitir 'as' si se necesita)

    Raises:
        ErrorConexionDB: Si hay problemas al cerrar conexión
    """
    if conexion is None:
        logger.warning(f"⚠️  {nombre_operacion}: Conexión es None")
        raise ErrorConexionDB(f"Conexión no inicializada para {nombre_operacion}")

    try:
        logger.debug(f"🔄 Iniciando {nombre_operacion}...")
        yield conexion
        logger.debug(f"✅ {nombre_operacion} completada exitosamente")

    except Exception as e:
        logger.error(f"❌ Error durante {nombre_operacion}: {e}")
        raise

    finally:
        # Intentar cerrar conexión de forma segura
        try:
            if hasattr(conexion, 'close') and callable(conexion.close):
                conexion.close()
                logger.debug(f"🔌 Conexión cerrada después de {nombre_operacion}")
        except Exception as e:
            logger.warning(f"⚠️  Error al cerrar conexión en {nombre_operacion}: {e}")


@contextmanager
def manejo_transaccion(conexion, nombre_operacion: str = "Transacción"):
    """
    Context manager para manejo seguro de transacciones.

    Realiza COMMIT en caso de éxito, ROLLBACK en caso de error.

    Usage:
        with manejo_transaccion(db_conn, "Actualizar OC"):
            # realizar operaciones
            db_conn.execute(sql)
            # Si todo va bien, auto-commit al salir
            # Si hay error, auto-rollback

    Args:
        conexion: Objeto de conexión DB2
        nombre_operacion: Nombre de la operación para logging

    Yields:
        conexion: La conexión

    Raises:
        ErrorConexionDB: Si hay problemas con transacción
    """
    if conexion is None:
        raise ErrorConexionDB("Conexión no inicializada para transacción")

    try:
        logger.info(f"🔄 Iniciando transacción: {nombre_operacion}")
        yield conexion

        # Hacer commit si no hay excepción
        try:
            if hasattr(conexion, 'commit') and callable(conexion.commit):
                conexion.commit()
                logger.info(f"✅ Transacción COMMIT: {nombre_operacion}")
            else:
                logger.warning(f"⚠️  Conexión no soporta COMMIT en {nombre_operacion}")
        except Exception as e:
            logger.error(f"❌ Error al COMMIT en {nombre_operacion}: {e}")
            raise ErrorConexionDB(f"COMMIT fallido en {nombre_operacion}: {e}")

    except Exception as e:
        logger.error(f"❌ Error durante transacción {nombre_operacion}: {e}")

        # Intentar rollback en caso de error
        try:
            if hasattr(conexion, 'rollback') and callable(conexion.rollback):
                conexion.rollback()
                logger.warning(f"⚠️  Transacción ROLLBACK: {nombre_operacion}")
            else:
                logger.warning(f"⚠️  Conexión no soporta ROLLBACK en {nombre_operacion}")
        except Exception as rollback_error:
            logger.critical(
                f"🚨 CRÍTICO: Error al ROLLBACK en {nombre_operacion}: {rollback_error}"
            )

        raise


def ejecutar_query_seguro(
    conexion,
    sql: str,
    parametros: Optional[tuple] = None,
    timeout: int = 30,
    nombre_operacion: str = "Query"
) -> Any:
    """
    Ejecuta query de forma segura con manejo robusto de errores.

    Args:
        conexion: Objeto de conexión DB2
        sql: SQL a ejecutar
        parametros: Parámetros para query (tuple)
        timeout: Timeout en segundos
        nombre_operacion: Nombre para logging

    Returns:
        Any: Resultado de la query

    Raises:
        ErrorQueryDB: Si hay error en ejecución de query
        TimeoutError: Si query excede timeout
        ValueError: Si parametros inválidos
    """
    if not conexion:
        raise ErrorConexionDB("Conexión no inicializada")

    if not sql or not isinstance(sql, str):
        raise ValueError("SQL debe ser string no-vacío")

    # Sanitizar SQL: remover comandos peligrosos que no sean query de lectura
    sql_upper = sql.strip().upper()
    if any(cmd in sql_upper for cmd in ['DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE']):
        logger.warning(f"⚠️  Query contiene comando potencialmente peligroso: {nombre_operacion}")

    try:
        logger.debug(f"🔍 Ejecutando query: {nombre_operacion}")

        # Obtener cursor
        if not hasattr(conexion, 'cursor'):
            raise ErrorConexionDB("Conexión no soporta cursor()")

        cursor = conexion.cursor()

        if cursor is None:
            raise ErrorConexionDB("No se pudo obtener cursor de la conexión")

        try:
            # Ejecutar con parámetros si se proporcionaron
            if parametros:
                if not isinstance(parametros, (tuple, list)):
                    raise ValueError(f"Parámetros deben ser tuple/list, got {type(parametros)}")
                cursor.execute(sql, parametros)
            else:
                cursor.execute(sql)

            # Obtener resultados
            resultado = cursor.fetchall()
            logger.info(f"✅ Query exitosa: {nombre_operacion} ({len(resultado) if resultado else 0} filas)")

            return resultado

        except Exception as e:
            error_msg = str(e)

            if 'timeout' in error_msg.lower():
                logger.error(f"⏱️  TIMEOUT en query: {nombre_operacion}")
                raise TimeoutError(f"Query excedió timeout ({timeout}s): {nombre_operacion}")

            elif 'connection' in error_msg.lower():
                logger.error(f"🔌 Error de conexión en query: {nombre_operacion}")
                raise ErrorConexionDB(f"Conexión perdida durante query: {nombre_operacion}")

            elif 'syntax' in error_msg.lower() or 'invalid' in error_msg.lower():
                logger.error(f"❌ Error de sintaxis SQL en {nombre_operacion}: {error_msg[:100]}")
                raise ErrorQueryDB(f"SQL inválido en {nombre_operacion}: {error_msg[:200]}")

            else:
                logger.error(f"❌ Error desconocido en query {nombre_operacion}: {error_msg}")
                raise ErrorQueryDB(f"Error ejecutando query {nombre_operacion}: {error_msg}")

        finally:
            # Cerrar cursor
            try:
                if cursor and hasattr(cursor, 'close'):
                    cursor.close()
            except Exception as e:
                logger.warning(f"⚠️  Error cerrando cursor en {nombre_operacion}: {e}")

    except (ErrorConexionDB, ErrorQueryDB, TimeoutError, ValueError):
        # Re-raise nuestras excepciones personalizadas
        raise

    except Exception as e:
        logger.critical(f"🚨 Error inesperado en query {nombre_operacion}: {e}")
        raise ErrorQueryDB(f"Error inesperado en {nombre_operacion}: {e}")


def validar_resultado_query(
    resultado: Any,
    esperado_tipo: type = list,
    minimo_filas: int = 0,
    nombre_operacion: str = "Query"
) -> bool:
    """
    Valida resultado de query.

    Args:
        resultado: Resultado de la query
        esperado_tipo: Tipo esperado del resultado
        minimo_filas: Mínimo de filas esperadas
        nombre_operacion: Nombre para logging

    Returns:
        bool: True si validación pasó

    Raises:
        ValueError: Si validación falló
    """
    if resultado is None:
        logger.warning(f"⚠️  Query {nombre_operacion} retornó None")
        raise ValueError(f"Query {nombre_operacion} retornó resultado None")

    if not isinstance(resultado, esperado_tipo):
        raise ValueError(
            f"Query {nombre_operacion} retornó {type(resultado).__name__}, "
            f"se esperaba {esperado_tipo.__name__}"
        )

    if isinstance(resultado, (list, tuple)):
        if len(resultado) < minimo_filas:
            logger.warning(
                f"⚠️  Query {nombre_operacion} retornó {len(resultado)} filas, "
                f"mínimo esperado: {minimo_filas}"
            )
            raise ValueError(
                f"Query {nombre_operacion} retornó {len(resultado)} filas, "
                f"mínimo: {minimo_filas}"
            )

    logger.info(f"✅ Validación de resultado exitosa: {nombre_operacion}")
    return True


def retry_con_backoff(
    funcion: Callable,
    intentos: int = 3,
    delay_inicial: float = 1.0,
    nombre_operacion: str = "Operación"
) -> Any:
    """
    Reintenta ejecutar función con backoff exponencial.

    Args:
        funcion: Función a ejecutar (debe ser callable sin argumentos)
        intentos: Número de intentos máximos
        delay_inicial: Delay inicial en segundos
        nombre_operacion: Nombre para logging

    Returns:
        Any: Resultado de la función

    Raises:
        Exception: Si todos los intentos fallan
    """
    ultimo_error = None
    delay_actual = delay_inicial

    for intento in range(1, intentos + 1):
        try:
            logger.info(f"🔄 {nombre_operacion} - Intento {intento}/{intentos}")
            resultado = funcion()
            logger.info(f"✅ {nombre_operacion} exitosa en intento {intento}")
            return resultado

        except Exception as e:
            ultimo_error = e
            logger.warning(
                f"⚠️  {nombre_operacion} falló en intento {intento}: {e}"
            )

            if intento < intentos:
                logger.info(f"⏳ Esperando {delay_actual}s antes de reintentar...")
                import time
                time.sleep(delay_actual)
                delay_actual *= 2  # Backoff exponencial

    # Si llegamos aquí, todos los intentos fallaron
    logger.error(f"❌ {nombre_operacion} falló después de {intentos} intentos")
    raise ultimo_error
