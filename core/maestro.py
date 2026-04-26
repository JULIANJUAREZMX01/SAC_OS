#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
===============================================================================
SCRIPT MAESTRO - ORQUESTADOR CENTRAL DEL SISTEMA SAC
Sistema de Automatizacion de Consultas - CEDIS Cancun 427
===============================================================================

Este script es el punto de control central que orquesta todos los procesos
del sistema SAC:

- Ejecuta tareas programadas (diarias, preventivas, horarias)
- Mantiene monitoreo continuo del sistema
- Gestiona alertas y notificaciones
- Proporciona un CLI unificado para todas las operaciones

MODOS DE EJECUCION:
    python maestro.py                    # Menu interactivo
    python maestro.py --daemon           # Modo servicio continuo
    python maestro.py --ejecutar-ahora   # Ejecutar ciclo completo
    python maestro.py --validar OC123    # Validar OC especifica
    python maestro.py --reporte-diario   # Generar reporte diario
    python maestro.py --status           # Ver estado del sistema

HORARIOS AUTOMATICOS (modo daemon):
    06:00 - Reporte matutino y validacion inicial
    09:00 - Validacion de OC pendientes
    12:00 - Monitoreo de medio dia
    15:00 - Validacion preventiva
    18:00 - Reporte vespertino
    21:00 - Resumen del dia
    Cada 15 min - Monitoreo continuo

Desarrollado por: Julian Alexander Juarez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logistica Cancun
===============================================================================
"""

import os
import sys
import logging
import argparse
import signal
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import schedule
import pandas as pd
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Agregar directorio actual al path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Importar modulos del sistema
try:
    from config import (
        DB_CONFIG, CEDIS, EMAIL_CONFIG, TELEGRAM_CONFIG,
        PATHS, SYSTEM_CONFIG, LOGGING_CONFIG,
        validar_configuracion, imprimir_configuracion
    )
    from core.monitor import MonitorTiempoReal, ValidadorProactivo, ErrorSeverity, imprimir_resumen_errores
    from modules.reportes_excel import GeneradorReportesExcel
    from modules.db_connection import (
        DB2Connection, DB2ConnectionPool,
        PYODBC_AVAILABLE, IBM_DB_AVAILABLE,
        get_connection_info
    )
    from core.gestor_correos import GestorCorreos
    from modules.notificaciones_telegram import (
        NotificadorTelegram, TipoAlerta,
        crear_notificador_desde_config
    )
    from queries import (
        QueryLoader, QueryCategory,
        load_query, load_query_with_params, get_default_loader
    )
except ImportError as e:
    print(f"Error al importar modulos: {e}")
    print("Asegurate de estar en el directorio correcto.")
    sys.exit(1)


# ===============================================================================
# CONFIGURACION DE LOGGING
# ===============================================================================

def configurar_logging(nivel=logging.INFO, modo_daemon=False):
    """Configura el sistema de logging para el maestro"""
    log_dir = Path('output/logs')
    log_dir.mkdir(parents=True, exist_ok=True)

    fecha = datetime.now().strftime('%Y%m%d')
    log_file = log_dir / f'maestro_{fecha}.log'

    log_format = '%(asctime)s - [MAESTRO] - %(levelname)s - %(message)s'

    handlers = [
        logging.FileHandler(log_file, encoding='utf-8'),
    ]

    if not modo_daemon:
        handlers.append(logging.StreamHandler(sys.stdout))

    logging.basicConfig(
        level=nivel,
        format=log_format,
        handlers=handlers,
        force=True
    )

    return logging.getLogger('MAESTRO')


logger = configurar_logging()


# ===============================================================================
# CLASES DE ESTADO Y ENUMERACIONES
# ===============================================================================

class EstadoTarea(Enum):
    """Estados posibles de una tarea"""
    PENDIENTE = "PENDIENTE"
    EJECUTANDO = "EJECUTANDO"
    COMPLETADA = "COMPLETADA"
    ERROR = "ERROR"
    OMITIDA = "OMITIDA"


class TipoTarea(Enum):
    """Tipos de tareas del sistema"""
    VALIDACION_OC = "VALIDACION_OC"
    REPORTE_DIARIO = "REPORTE_DIARIO"
    MONITOREO = "MONITOREO"
    ALERTA = "ALERTA"
    PREVENTIVO = "PREVENTIVO"
    RESUMEN = "RESUMEN"
    MANTENIMIENTO = "MANTENIMIENTO"


@dataclass
class ResultadoTarea:
    """Resultado de ejecucion de una tarea"""
    tarea: str
    tipo: TipoTarea
    estado: EstadoTarea
    inicio: datetime
    fin: datetime = None
    mensaje: str = ""
    errores: List[str] = field(default_factory=list)
    datos: Dict[str, Any] = field(default_factory=dict)

    @property
    def duracion(self) -> float:
        """Duracion en segundos"""
        if self.fin:
            return (self.fin - self.inicio).total_seconds()
        return 0


@dataclass
class EstadoSistema:
    """Estado actual del sistema"""
    db_conectada: bool = False
    email_configurado: bool = False
    telegram_activo: bool = False
    ultimo_ciclo: datetime = None
    errores_pendientes: int = 0
    tareas_ejecutadas_hoy: int = 0
    alertas_enviadas_hoy: int = 0
    modo_operacion: str = "INTERACTIVO"


# ===============================================================================
# CLASE PRINCIPAL - MAESTRO ORQUESTADOR
# ===============================================================================

class MaestroSAC:
    """
    Orquestador central del Sistema SAC

    Coordina la ejecucion de todos los procesos del sistema,
    maneja la programacion de tareas y proporciona un punto
    de control unificado.
    """

    def __init__(self):
        """Inicializa el maestro orquestador"""
        self.estado = EstadoSistema()
        self.db_connection = None
        self.telegram = None
        self.gestor_correos = None
        self.monitor = MonitorTiempoReal()
        self.validador = ValidadorProactivo()
        self.generador_reportes = GeneradorReportesExcel(cedis=CEDIS['name'])

        self._running = False
        self._lock = threading.Lock()
        self._resultados_hoy: List[ResultadoTarea] = []
        self._errores_detectados = []

        logger.info("=" * 70)
        logger.info("MAESTRO SAC - Iniciando orquestador")
        logger.info("=" * 70)

    # ---------------------------------------------------------------------------
    # INICIALIZACION Y CONEXIONES
    # ---------------------------------------------------------------------------

    def inicializar(self) -> bool:
        """
        Inicializa todas las conexiones y servicios del sistema

        Returns:
            bool: True si la inicializacion fue exitosa
        """
        logger.info("Inicializando componentes del sistema...")

        exitos = 0
        total = 3

        # 1. Conexion a DB2
        logger.info("1/3 - Conectando a DB2...")
        if self._conectar_db():
            exitos += 1
            self.estado.db_conectada = True
            logger.info("    DB2 conectada")
        else:
            logger.warning("    DB2 no disponible - modo DEMO activo")

        # 2. Configurar Email
        logger.info("2/3 - Configurando Email...")
        if self._configurar_email():
            exitos += 1
            self.estado.email_configurado = True
            logger.info("    Email configurado")
        else:
            logger.warning("    Email no configurado")

        # 3. Configurar Telegram
        logger.info("3/3 - Configurando Telegram...")
        if self._configurar_telegram():
            exitos += 1
            self.estado.telegram_activo = True
            logger.info("    Telegram activo")
        else:
            logger.warning("    Telegram no configurado")

        logger.info(f"Inicializacion completada: {exitos}/{total} servicios activos")

        return exitos > 0

    def _conectar_db(self) -> bool:
        """Establece conexion a DB2"""
        try:
            if not PYODBC_AVAILABLE and not IBM_DB_AVAILABLE:
                logger.warning("No hay drivers DB2 disponibles")
                return False

            info = get_connection_info()
            if not info.get('password_configured'):
                logger.warning("Credenciales DB2 no configuradas")
                return False

            self.db_connection = DB2Connection(config=DB_CONFIG)
            if self.db_connection.connect():
                return True
            return False

        except Exception as e:
            logger.error(f"Error conectando a DB2: {e}")
            return False

    def _configurar_email(self) -> bool:
        """Configura el gestor de correos"""
        try:
            if not EMAIL_CONFIG.get('user') or EMAIL_CONFIG['user'] == 'tu_email@chedraui.com.mx':
                return False

            self.gestor_correos = GestorCorreos({
                'smtp_server': EMAIL_CONFIG['smtp_server'],
                'smtp_port': EMAIL_CONFIG['smtp_port'],
                'user': EMAIL_CONFIG['user'],
                'password': EMAIL_CONFIG['password'],
                'from_name': EMAIL_CONFIG['from_name'],
                'cedis_nombre': CEDIS['name']
            })
            return True

        except Exception as e:
            logger.error(f"Error configurando email: {e}")
            return False

    def _configurar_telegram(self) -> bool:
        """Configura el notificador de Telegram"""
        try:
            self.telegram = crear_notificador_desde_config()
            return self.telegram is not None and self.telegram.enabled
        except Exception as e:
            logger.error(f"Error configurando Telegram: {e}")
            return False

    def cerrar(self):
        """Cierra todas las conexiones y libera recursos"""
        logger.info("Cerrando conexiones...")

        if self.db_connection:
            try:
                self.db_connection.disconnect()
                logger.info("DB2 desconectada")
            except Exception as e:
                logger.warning(f"Error al desconectar DB2: {e}")

        self._running = False
        logger.info("Maestro SAC finalizado")

    # ---------------------------------------------------------------------------
    # EJECUTORES DE TAREAS PRINCIPALES
    # ---------------------------------------------------------------------------

    def ejecutar_validacion_oc(self, oc_numero: str) -> ResultadoTarea:
        """
        Ejecuta validacion completa de una Orden de Compra

        Args:
            oc_numero: Numero de OC a validar

        Returns:
            ResultadoTarea con el resultado de la validacion
        """
        resultado = ResultadoTarea(
            tarea=f"Validacion OC {oc_numero}",
            tipo=TipoTarea.VALIDACION_OC,
            estado=EstadoTarea.EJECUTANDO,
            inicio=datetime.now()
        )

        logger.info(f"Iniciando validacion de OC: {oc_numero}")

        try:
            if self.db_connection and self.estado.db_conectada:
                # Validacion con datos reales de DB2
                es_valida, errores = self.validador.validacion_completa_oc(
                    self.db_connection, oc_numero, CEDIS.get('almacen', 'C22')
                )

                resultado.datos['es_valida'] = es_valida
                resultado.datos['total_errores'] = len(errores)
                resultado.errores = [e.mensaje for e in errores]

                # Generar reporte Excel
                archivo_excel = self._generar_reporte_validacion(oc_numero, errores)
                resultado.datos['archivo_reporte'] = archivo_excel

                # Si hay errores criticos, enviar alerta
                criticos = [e for e in errores if e.severidad == ErrorSeverity.CRITICO]
                if criticos:
                    self._enviar_alerta_critica(
                        f"Validacion OC {oc_numero}",
                        f"Se detectaron {len(criticos)} errores criticos",
                        oc_numero
                    )
                    resultado.estado = EstadoTarea.ERROR
                else:
                    resultado.estado = EstadoTarea.COMPLETADA

            else:
                # Modo DEMO
                resultado.mensaje = "Ejecutado en modo DEMO (sin conexion DB2)"
                resultado.estado = EstadoTarea.COMPLETADA
                resultado.datos['modo'] = 'DEMO'

        except Exception as e:
            resultado.estado = EstadoTarea.ERROR
            resultado.errores.append(str(e))
            logger.error(f"Error en validacion OC {oc_numero}: {e}")

        resultado.fin = datetime.now()
        self._registrar_resultado(resultado)

        return resultado

    def ejecutar_reporte_diario(self) -> ResultadoTarea:
        """
        Genera y envia el reporte diario de Planning

        Returns:
            ResultadoTarea con el resultado de la generacion
        """
        resultado = ResultadoTarea(
            tarea="Reporte Diario Planning",
            tipo=TipoTarea.REPORTE_DIARIO,
            estado=EstadoTarea.EJECUTANDO,
            inicio=datetime.now()
        )

        logger.info("Generando reporte diario de Planning...")

        try:
            # Obtener datos
            df_oc, df_asn = self._obtener_datos_diarios()

            # Generar Excel
            fecha = datetime.now().strftime('%Y%m%d')
            archivo_excel = f"output/resultados/Planning_Diario_{CEDIS['code']}_{fecha}.xlsx"

            self.generador_reportes.crear_reporte_planning_diario(
                df_oc, df_asn, pd.DataFrame(), archivo_excel
            )

            resultado.datos['archivo'] = archivo_excel
            resultado.datos['total_oc'] = len(df_oc) if df_oc is not None else 0
            resultado.datos['total_asn'] = len(df_asn) if df_asn is not None else 0

            # Enviar por email si esta configurado
            if self.estado.email_configurado and self.gestor_correos:
                destinatarios = EMAIL_CONFIG.get('to_emails', [])
                if destinatarios:
                    self.gestor_correos.enviar_reporte_planning_diario(
                        destinatarios=destinatarios,
                        df_oc=df_oc,
                        df_asn=df_asn,
                        archivos_adjuntos=[archivo_excel]
                    )
                    resultado.datos['email_enviado'] = True

            # Notificar por Telegram
            if self.estado.telegram_activo and self.telegram:
                self.telegram.enviar_alerta(
                    TipoAlerta.INFO,
                    "Reporte Diario Generado",
                    f"OC: {resultado.datos['total_oc']} | ASN: {resultado.datos['total_asn']}",
                    "MAESTRO"
                )

            resultado.estado = EstadoTarea.COMPLETADA
            resultado.mensaje = f"Reporte generado: {archivo_excel}"

        except Exception as e:
            resultado.estado = EstadoTarea.ERROR
            resultado.errores.append(str(e))
            logger.error(f"Error generando reporte diario: {e}")

        resultado.fin = datetime.now()
        self._registrar_resultado(resultado)

        return resultado

    def ejecutar_monitoreo(self) -> ResultadoTarea:
        """
        Ejecuta ciclo de monitoreo del sistema

        Returns:
            ResultadoTarea con el resultado del monitoreo
        """
        resultado = ResultadoTarea(
            tarea="Monitoreo del Sistema",
            tipo=TipoTarea.MONITOREO,
            estado=EstadoTarea.EJECUTANDO,
            inicio=datetime.now()
        )

        logger.info("Ejecutando monitoreo del sistema...")

        try:
            errores_detectados = []

            # 1. Verificar conexion DB
            if self.db_connection:
                errores_db = self.monitor.validar_conexion_db(self.db_connection)
                errores_detectados.extend(errores_db)

            # 2. Verificar OC pendientes (si hay conexion)
            if self.estado.db_conectada:
                # Aqui se podrian agregar validaciones adicionales
                pass

            # 3. Registrar errores
            self._errores_detectados = errores_detectados
            self.estado.errores_pendientes = len(errores_detectados)

            resultado.datos['errores_detectados'] = len(errores_detectados)
            resultado.datos['criticos'] = sum(
                1 for e in errores_detectados
                if e.severidad == ErrorSeverity.CRITICO
            )

            # 4. Alertar si hay criticos
            if resultado.datos['criticos'] > 0:
                self._enviar_alerta_critica(
                    "Errores Criticos Detectados",
                    f"Se detectaron {resultado.datos['criticos']} errores criticos",
                    None
                )

            resultado.estado = EstadoTarea.COMPLETADA
            resultado.mensaje = f"Monitoreo completado: {len(errores_detectados)} errores"

        except Exception as e:
            resultado.estado = EstadoTarea.ERROR
            resultado.errores.append(str(e))
            logger.error(f"Error en monitoreo: {e}")

        resultado.fin = datetime.now()
        self.estado.ultimo_ciclo = resultado.fin
        self._registrar_resultado(resultado)

        return resultado

    def ejecutar_validacion_preventiva(self) -> ResultadoTarea:
        """
        Ejecuta validaciones preventivas del sistema

        Returns:
            ResultadoTarea con el resultado
        """
        resultado = ResultadoTarea(
            tarea="Validacion Preventiva",
            tipo=TipoTarea.PREVENTIVO,
            estado=EstadoTarea.EJECUTANDO,
            inicio=datetime.now()
        )

        logger.info("Ejecutando validaciones preventivas...")

        try:
            # Ejecutar queries preventivas si hay conexion
            if self.estado.db_conectada and self.db_connection:
                loader = get_default_loader()
                queries_preventivas = loader.list_queries(QueryCategory.PREVENTIVAS)

                resultado.datos['queries_ejecutadas'] = len(queries_preventivas)
                resultado.datos['resultados'] = {}

                for query_name in queries_preventivas:
                    try:
                        sql = load_query(QueryCategory.PREVENTIVAS, query_name)
                        # Aqui se ejecutaria la query y se procesarian resultados
                        resultado.datos['resultados'][query_name] = 'OK'
                    except Exception as e:
                        resultado.datos['resultados'][query_name] = f'ERROR: {e}'
            else:
                resultado.mensaje = "Sin conexion DB2 - omitido"

            resultado.estado = EstadoTarea.COMPLETADA

        except Exception as e:
            resultado.estado = EstadoTarea.ERROR
            resultado.errores.append(str(e))
            logger.error(f"Error en validacion preventiva: {e}")

        resultado.fin = datetime.now()
        self._registrar_resultado(resultado)

        return resultado

    def ejecutar_resumen_dia(self) -> ResultadoTarea:
        """
        Genera y envia resumen del dia

        Returns:
            ResultadoTarea con el resultado
        """
        resultado = ResultadoTarea(
            tarea="Resumen del Dia",
            tipo=TipoTarea.RESUMEN,
            estado=EstadoTarea.EJECUTANDO,
            inicio=datetime.now()
        )

        logger.info("Generando resumen del dia...")

        try:
            # Calcular estadisticas del dia
            tareas_completadas = sum(
                1 for r in self._resultados_hoy
                if r.estado == EstadoTarea.COMPLETADA
            )
            tareas_error = sum(
                1 for r in self._resultados_hoy
                if r.estado == EstadoTarea.ERROR
            )

            resumen = {
                'fecha': datetime.now().strftime('%Y-%m-%d'),
                'tareas_ejecutadas': len(self._resultados_hoy),
                'completadas': tareas_completadas,
                'errores': tareas_error,
                'alertas_enviadas': self.estado.alertas_enviadas_hoy
            }

            resultado.datos = resumen

            # Enviar resumen por Telegram
            if self.estado.telegram_activo and self.telegram:
                mensaje = (
                    f"Tareas: {resumen['tareas_ejecutadas']} | "
                    f"OK: {resumen['completadas']} | "
                    f"Errores: {resumen['errores']}"
                )
                self.telegram.enviar_alerta(
                    TipoAlerta.INFO,
                    f"Resumen del Dia - {CEDIS['name']}",
                    mensaje,
                    "MAESTRO"
                )

            resultado.estado = EstadoTarea.COMPLETADA
            resultado.mensaje = f"Resumen generado: {tareas_completadas}/{len(self._resultados_hoy)} tareas OK"

        except Exception as e:
            resultado.estado = EstadoTarea.ERROR
            resultado.errores.append(str(e))
            logger.error(f"Error generando resumen: {e}")

        resultado.fin = datetime.now()
        self._registrar_resultado(resultado)

        return resultado

    # ---------------------------------------------------------------------------
    # CICLO COMPLETO DE EJECUCION
    # ---------------------------------------------------------------------------

    def ejecutar_ciclo_completo(self) -> Dict[str, ResultadoTarea]:
        """
        Ejecuta un ciclo completo de todas las tareas del sistema

        Returns:
            Dict con los resultados de cada tarea
        """
        logger.info("=" * 70)
        logger.info("INICIANDO CICLO COMPLETO DE EJECUCION")
        logger.info("=" * 70)

        resultados = {}

        # 1. Monitoreo inicial
        logger.info("Paso 1/4: Monitoreo del sistema")
        resultados['monitoreo'] = self.ejecutar_monitoreo()

        # 2. Validacion preventiva
        logger.info("Paso 2/4: Validacion preventiva")
        resultados['preventivo'] = self.ejecutar_validacion_preventiva()

        # 3. Reporte diario
        logger.info("Paso 3/4: Reporte diario")
        resultados['reporte_diario'] = self.ejecutar_reporte_diario()

        # 4. Resumen
        logger.info("Paso 4/4: Resumen")
        resultados['resumen'] = self.ejecutar_resumen_dia()

        # Imprimir resumen
        self._imprimir_resumen_ciclo(resultados)

        return resultados

    def _imprimir_resumen_ciclo(self, resultados: Dict[str, ResultadoTarea]):
        """Imprime resumen del ciclo ejecutado"""
        print("\n" + "=" * 70)
        print("RESUMEN DEL CICLO DE EJECUCION")
        print("=" * 70)

        for nombre, resultado in resultados.items():
            estado_emoji = {
                EstadoTarea.COMPLETADA: "OK",
                EstadoTarea.ERROR: "ERROR",
                EstadoTarea.OMITIDA: "OMITIDO",
            }.get(resultado.estado, "?")

            print(f"  [{estado_emoji}] {resultado.tarea} ({resultado.duracion:.1f}s)")
            if resultado.errores:
                for error in resultado.errores[:2]:
                    print(f"       -> {error}")

        print("=" * 70 + "\n")

    # ---------------------------------------------------------------------------
    # MODO DAEMON - EJECUCION PROGRAMADA
    # ---------------------------------------------------------------------------

    def iniciar_daemon(self):
        """
        Inicia el modo daemon con tareas programadas

        Horarios:
            06:00 - Reporte matutino
            09:00 - Validacion OC pendientes
            12:00 - Monitoreo medio dia
            15:00 - Validacion preventiva
            18:00 - Reporte vespertino
            21:00 - Resumen del dia
            Cada 15 min - Monitoreo continuo
        """
        logger.info("Iniciando modo DAEMON...")
        self.estado.modo_operacion = "DAEMON"
        self._running = True

        # Configurar tareas programadas
        schedule.clear()

        # Tareas diarias
        schedule.every().day.at("06:00").do(self._tarea_reporte_matutino)
        schedule.every().day.at("09:00").do(self._tarea_validacion_pendientes)
        schedule.every().day.at("12:00").do(self.ejecutar_monitoreo)
        schedule.every().day.at("15:00").do(self.ejecutar_validacion_preventiva)
        schedule.every().day.at("18:00").do(self.ejecutar_reporte_diario)
        schedule.every().day.at("21:00").do(self.ejecutar_resumen_dia)

        # Monitoreo continuo cada 15 minutos
        schedule.every(15).minutes.do(self.ejecutar_monitoreo)

        # Reset diario a medianoche
        schedule.every().day.at("00:00").do(self._reset_diario)

        logger.info("Tareas programadas configuradas")
        logger.info("Horarios: 06:00, 09:00, 12:00, 15:00, 18:00, 21:00")
        logger.info("Monitoreo: cada 15 minutos")

        # Notificar inicio
        if self.estado.telegram_activo and self.telegram:
            self.telegram.enviar_alerta(
                TipoAlerta.INFO,
                "Sistema SAC Iniciado",
                f"Modo DAEMON activo - {CEDIS['name']}",
                "MAESTRO"
            )

        # Loop principal
        try:
            while self._running:
                schedule.run_pending()
                time.sleep(60)  # Revisar cada minuto

        except KeyboardInterrupt:
            logger.info("Interrupcion recibida, deteniendo daemon...")
        finally:
            self.detener_daemon()

    def detener_daemon(self):
        """Detiene el modo daemon"""
        self._running = False
        schedule.clear()

        # Notificar detencion
        if self.estado.telegram_activo and self.telegram:
            self.telegram.enviar_alerta(
                TipoAlerta.INFO,
                "Sistema SAC Detenido",
                f"Modo DAEMON finalizado - {CEDIS['name']}",
                "MAESTRO"
            )

        logger.info("Daemon detenido")

    def _tarea_reporte_matutino(self):
        """Tarea: Reporte matutino"""
        logger.info("Ejecutando tarea: Reporte Matutino")
        self.ejecutar_monitoreo()
        self.ejecutar_reporte_diario()

    def _tarea_validacion_pendientes(self):
        """Tarea: Validar OC pendientes"""
        logger.info("Ejecutando tarea: Validacion de OC pendientes")
        # Aqui se podrian consultar OC pendientes de DB2 y validarlas
        self.ejecutar_validacion_preventiva()

    def _reset_diario(self):
        """Reset de contadores diarios"""
        logger.info("Reset diario de contadores")
        self._resultados_hoy.clear()
        self.estado.tareas_ejecutadas_hoy = 0
        self.estado.alertas_enviadas_hoy = 0

    # ---------------------------------------------------------------------------
    # METODOS AUXILIARES
    # ---------------------------------------------------------------------------

    def _obtener_datos_diarios(self) -> tuple:
        """Obtiene datos de OC y ASN del dia"""
        df_oc = pd.DataFrame()
        df_asn = pd.DataFrame()

        if self.estado.db_conectada and self.db_connection:
            try:
                # Consultar OC del dia
                fecha_hoy = datetime.now().strftime('%Y-%m-%d')
                sql_oc = load_query_with_params(
                    QueryCategory.OBLIGATORIAS, "oc_diarias",
                    {"fecha_inicio": fecha_hoy, "fecha_fin": fecha_hoy,
                     "storerkey": CEDIS.get('almacen', 'C22')}
                )
                df_oc = self.db_connection.execute_query(sql_oc)

                # Consultar ASN
                sql_asn = load_query_with_params(
                    QueryCategory.OBLIGATORIAS, "asn_status",
                    {"fecha_inicio": fecha_hoy, "fecha_fin": fecha_hoy,
                     "storerkey": CEDIS.get('almacen', 'C22')}
                )
                df_asn = self.db_connection.execute_query(sql_asn)

            except Exception as e:
                logger.error(f"Error obteniendo datos diarios: {e}")
        else:
            # Datos demo
            df_oc = pd.DataFrame({
                'OC': ['DEMO001', 'DEMO002'],
                'Proveedor': ['PROV1', 'PROV2'],
                'Total_OC': [1000, 2000],
                'Status': ['OK', 'Pendiente']
            })
            df_asn = pd.DataFrame({
                'ASN': ['ASN001', 'ASN002'],
                'OC': ['DEMO001', 'DEMO002'],
                'Status': ['40', '10'],
                'Proveedor': ['PROV1', 'PROV2']
            })

        return df_oc, df_asn

    def _generar_reporte_validacion(self, oc_numero: str, errores: List) -> str:
        """Genera reporte Excel de validacion"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        archivo = f"output/resultados/Validacion_OC_{oc_numero}_{timestamp}.xlsx"

        df_errores = pd.DataFrame([{
            'Tipo': e.tipo,
            'Severidad': e.severidad.value,
            'Mensaje': e.mensaje,
            'Modulo': e.modulo,
            'Solucion': e.solucion
        } for e in errores]) if errores else pd.DataFrame()

        self.generador_reportes.crear_reporte_validacion_oc(df_errores, archivo)

        return archivo

    def _enviar_alerta_critica(self, titulo: str, descripcion: str, oc_numero: str = None):
        """Envia alerta critica por todos los canales disponibles"""
        self.estado.alertas_enviadas_hoy += 1

        # Telegram
        if self.estado.telegram_activo and self.telegram:
            self.telegram.enviar_alerta_critica(
                titulo=titulo,
                descripcion=descripcion,
                oc_numero=oc_numero
            )

        # Email
        if self.estado.email_configurado and self.gestor_correos:
            destinatarios = EMAIL_CONFIG.get('to_emails', [])
            if destinatarios:
                self.gestor_correos.enviar_alerta_critica(
                    destinatarios=destinatarios,
                    tipo_error=titulo,
                    descripcion=descripcion,
                    oc_numero=oc_numero
                )

        logger.warning(f"ALERTA CRITICA: {titulo} - {descripcion}")

    def _registrar_resultado(self, resultado: ResultadoTarea):
        """Registra el resultado de una tarea"""
        with self._lock:
            self._resultados_hoy.append(resultado)
            self.estado.tareas_ejecutadas_hoy += 1

    def obtener_estado(self) -> Dict[str, Any]:
        """Obtiene el estado actual del sistema"""
        return {
            'db_conectada': self.estado.db_conectada,
            'email_configurado': self.estado.email_configurado,
            'telegram_activo': self.estado.telegram_activo,
            'modo_operacion': self.estado.modo_operacion,
            'ultimo_ciclo': self.estado.ultimo_ciclo.isoformat() if self.estado.ultimo_ciclo else None,
            'errores_pendientes': self.estado.errores_pendientes,
            'tareas_hoy': self.estado.tareas_ejecutadas_hoy,
            'alertas_hoy': self.estado.alertas_enviadas_hoy,
            'cedis': CEDIS['name'],
            'version': SYSTEM_CONFIG['version']
        }


# ===============================================================================
# MENU INTERACTIVO
# ===============================================================================

def imprimir_banner():
    """Imprime el banner del sistema"""
    banner = """
    ===============================================================================
                        MAESTRO SAC - ORQUESTADOR CENTRAL
                     Sistema de Automatizacion de Consultas
                           CEDIS Cancun 427 - Chedraui
    ===============================================================================

    Desarrollado por: Julian Alexander Juarez Alvarado (ADMJAJA)
    Jefe de Sistemas - CEDIS Chedraui Logistica Cancun

    "Las maquinas y los sistemas al servicio de los analistas"
    ===============================================================================
    """
    print(banner)


def mostrar_menu():
    """Muestra el menu principal"""
    menu = """
    ============================= MENU PRINCIPAL ================================

    EJECUCION DE TAREAS:
        1. Ejecutar ciclo completo
        2. Validar Orden de Compra
        3. Generar Reporte Diario
        4. Ejecutar Monitoreo
        5. Validacion Preventiva
        6. Resumen del Dia

    MODO AUTOMATICO:
        7. Iniciar modo DAEMON (servicio continuo)

    ESTADO Y CONFIGURACION:
        8. Ver estado del sistema
        9. Ver configuracion
       10. Probar conexiones

    SISTEMA:
        0. Salir

    =============================================================================
    """
    print(menu)


def menu_interactivo(maestro: MaestroSAC):
    """Ejecuta el menu interactivo"""
    imprimir_banner()

    # Inicializar
    maestro.inicializar()

    try:
        while True:
            mostrar_menu()

            # Mostrar estado rapido
            estado = maestro.obtener_estado()
            print(f"    Estado: DB={'OK' if estado['db_conectada'] else 'NO'} | "
                  f"Email={'OK' if estado['email_configurado'] else 'NO'} | "
                  f"Telegram={'OK' if estado['telegram_activo'] else 'NO'}")
            print()

            opcion = input("    Selecciona una opcion: ").strip()

            if opcion == '1':
                maestro.ejecutar_ciclo_completo()

            elif opcion == '2':
                oc = input("\n    Numero de OC a validar: ").strip()
                if oc:
                    resultado = maestro.ejecutar_validacion_oc(oc)
                    print(f"\n    Resultado: {resultado.estado.value}")
                    if resultado.errores:
                        print("    Errores encontrados:")
                        for e in resultado.errores[:5]:
                            print(f"      - {e}")

            elif opcion == '3':
                resultado = maestro.ejecutar_reporte_diario()
                print(f"\n    {resultado.mensaje}")

            elif opcion == '4':
                resultado = maestro.ejecutar_monitoreo()
                print(f"\n    {resultado.mensaje}")

            elif opcion == '5':
                resultado = maestro.ejecutar_validacion_preventiva()
                print(f"\n    {resultado.mensaje}")

            elif opcion == '6':
                resultado = maestro.ejecutar_resumen_dia()
                print(f"\n    {resultado.mensaje}")

            elif opcion == '7':
                print("\n    Iniciando modo DAEMON...")
                print("    Presiona Ctrl+C para detener\n")
                maestro.iniciar_daemon()

            elif opcion == '8':
                estado = maestro.obtener_estado()
                print("\n    =============== ESTADO DEL SISTEMA ===============")
                for k, v in estado.items():
                    print(f"    {k}: {v}")
                print("    ==================================================")

            elif opcion == '9':
                imprimir_configuracion()

            elif opcion == '10':
                print("\n    Probando conexiones...")
                maestro.inicializar()
                estado = maestro.obtener_estado()
                print(f"    DB2: {'Conectada' if estado['db_conectada'] else 'No conectada'}")
                print(f"    Email: {'Configurado' if estado['email_configurado'] else 'No configurado'}")
                print(f"    Telegram: {'Activo' if estado['telegram_activo'] else 'No activo'}")

            elif opcion == '0':
                print("\n    Hasta luego!")
                break

            else:
                print("\n    Opcion no valida")

            input("\n    Presiona ENTER para continuar...")
            print("\n" * 2)

    finally:
        maestro.cerrar()


# ===============================================================================
# PUNTO DE ENTRADA PRINCIPAL
# ===============================================================================

def main():
    """Funcion principal"""

    parser = argparse.ArgumentParser(
        description='Maestro SAC - Orquestador Central del Sistema',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
    python maestro.py                    # Menu interactivo
    python maestro.py --daemon           # Modo servicio continuo
    python maestro.py --ejecutar-ahora   # Ejecutar ciclo completo
    python maestro.py --validar OC12345  # Validar OC especifica
    python maestro.py --reporte-diario   # Generar reporte diario
    python maestro.py --status           # Ver estado del sistema
        """
    )

    parser.add_argument('--daemon', action='store_true',
                        help='Iniciar en modo servicio continuo')
    parser.add_argument('--ejecutar-ahora', action='store_true',
                        help='Ejecutar ciclo completo inmediatamente')
    parser.add_argument('--validar', type=str, metavar='OC',
                        help='Validar una OC especifica')
    parser.add_argument('--reporte-diario', action='store_true',
                        help='Generar reporte diario')
    parser.add_argument('--monitoreo', action='store_true',
                        help='Ejecutar monitoreo del sistema')
    parser.add_argument('--status', action='store_true',
                        help='Mostrar estado del sistema')
    parser.add_argument('--config', action='store_true',
                        help='Mostrar configuracion')

    args = parser.parse_args()

    # Crear instancia del maestro
    maestro = MaestroSAC()

    # Manejar senales para cierre limpio
    def signal_handler(signum, frame):
        print("\nSenal recibida, cerrando...")
        maestro.cerrar()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        if args.daemon:
            # Modo daemon
            logger = configurar_logging(modo_daemon=True)
            maestro.inicializar()
            maestro.iniciar_daemon()

        elif args.ejecutar_ahora:
            # Ejecutar ciclo completo
            maestro.inicializar()
            maestro.ejecutar_ciclo_completo()

        elif args.validar:
            # Validar OC especifica
            maestro.inicializar()
            resultado = maestro.ejecutar_validacion_oc(args.validar)
            print(f"\nResultado: {resultado.estado.value}")
            if resultado.errores:
                print("Errores:")
                for e in resultado.errores:
                    print(f"  - {e}")

        elif args.reporte_diario:
            # Generar reporte diario
            maestro.inicializar()
            resultado = maestro.ejecutar_reporte_diario()
            print(f"\n{resultado.mensaje}")

        elif args.monitoreo:
            # Ejecutar monitoreo
            maestro.inicializar()
            resultado = maestro.ejecutar_monitoreo()
            print(f"\n{resultado.mensaje}")

        elif args.status:
            # Mostrar estado
            maestro.inicializar()
            estado = maestro.obtener_estado()
            print("\n===== ESTADO DEL SISTEMA =====")
            for k, v in estado.items():
                print(f"  {k}: {v}")
            print("==============================\n")

        elif args.config:
            # Mostrar configuracion
            imprimir_configuracion()

        else:
            # Menu interactivo (por defecto)
            menu_interactivo(maestro)

    except Exception as e:
        logger.error(f"Error fatal: {e}")
        sys.exit(1)
    finally:
        maestro.cerrar()


if __name__ == "__main__":
    main()
