"""
═══════════════════════════════════════════════════════════════
MÓDULO DE MONITOREO Y DETECCIÓN DE ERRORES EN TIEMPO REAL
Sistema de Gestión de Órdenes de Compra - Chedraui CEDIS
═══════════════════════════════════════════════════════════════

Este módulo detecta, informa y previene errores en tiempo real:
- Validaciones proactivas
- Alertas tempranas
- Prevención de problemas
- Notificaciones en tiempo real

Desarrollado por: Julián Alexander Juárez Alvarado (ADM)
Analista de Sistemas - CEDIS Chedraui Logística Cancún

Con cariño para todos los analistas:
"Las máquinas y los sistemas al servicio de los analistas"
- Automatización para reducir tiempos
- Más productividad, menos procesos manuales
- Tecnología que nos libera para pensar y crear

═══════════════════════════════════════════════════════════════
"""

import logging
import pandas as pd
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Niveles de severidad de errores"""
    CRITICO = "🔴 CRÍTICO"
    ALTO = "🟠 ALTO"
    MEDIO = "🟡 MEDIO"
    BAJO = "🟢 BAJO"
    INFO = "ℹ️ INFO"


@dataclass
class ErrorDetectado:
    """Clase para representar un error detectado"""
    tipo: str
    severidad: ErrorSeverity
    mensaje: str
    detalles: str
    solucion: str
    timestamp: datetime
    modulo: str
    datos_afectados: Optional[Dict] = None


class MonitorTiempoReal:
    """
    Sistema de monitoreo y detección de errores en tiempo real
    
    Detecta, informa y previene errores antes de que afecten el proceso
    """
    
    def __init__(self, email_config=None):
        self.errores_detectados: List[ErrorDetectado] = []
        self.alertas_criticas: List[ErrorDetectado] = []
        self.email_config = email_config
        
    def validar_conexion_db(self, db_connection) -> List[ErrorDetectado]:
        """
        Valida la conexión a DB2 antes de ejecutar
        
        ERRORES DETECTADOS:
        - Sin conexión al servidor
        - Credenciales incorrectas
        - Timeout de conexión
        - Permisos insuficientes
        """
        errores = []
        
        try:
            if not db_connection or not getattr(db_connection, 'connection', None):
                errores.append(ErrorDetectado(
                    tipo="CONEXION_DB",
                    severidad=ErrorSeverity.CRITICO,
                    mensaje="❌ Sin conexión a DB2",
                    detalles="No se pudo establecer conexión con el servidor DB2",
                    solucion="""
                    1. Verificar que el servidor DB2 esté accesible
                    2. Revisar credenciales en archivo .env
                    3. Validar permisos de red/firewall
                    4. Contactar a soporte de TI si persiste
                    """,
                    timestamp=datetime.now(),
                    modulo="DB_CONNECTION"
                ))
                
            # Intentar una consulta simple de prueba
            else:
                try:
                    test_query = "SELECT 1 FROM SYSIBM.SYSDUMMY1"
                    db_connection.execute_query(test_query)
                    logger.info("✅ Conexión DB2 validada correctamente")
                    
                except Exception as e:
                    errores.append(ErrorDetectado(
                        tipo="QUERY_TEST_FAILED",
                        severidad=ErrorSeverity.ALTO,
                        mensaje="❌ Error al ejecutar consulta de prueba",
                        detalles=f"Error: {str(e)}",
                        solucion="Verificar permisos del usuario en DB2",
                        timestamp=datetime.now(),
                        modulo="DB_CONNECTION"
                    ))
                    
        except Exception as e:
            errores.append(ErrorDetectado(
                tipo="VALIDATION_ERROR",
                severidad=ErrorSeverity.CRITICO,
                mensaje="❌ Error durante validación de conexión",
                detalles=f"Excepción: {str(e)}",
                solucion="Revisar logs del sistema y configuración",
                timestamp=datetime.now(),
                modulo="DB_CONNECTION"
            ))
            
        self.errores_detectados.extend(errores)
        self._procesar_alertas_criticas(errores)
        return errores
    
    def validar_oc_existente(self, df_oc: pd.DataFrame, oc_numero: str) -> List[ErrorDetectado]:
        """
        Valida que la OC exista en el sistema
        
        ERRORES DETECTADOS:
        - OC no encontrada
        - OC sin distribuciones
        - OC vencida
        - OC sin letra C en ID_CODE
        """
        errores = []
        
        if df_oc is None or df_oc.empty:
            errores.append(ErrorDetectado(
                tipo="OC_NO_ENCONTRADA",
                severidad=ErrorSeverity.ALTO,
                mensaje=f"⚠️ OC {oc_numero} no encontrada en sistema",
                detalles="La orden de compra no existe en la base de datos",
                solucion="""
                1. Verificar número de OC
                2. Confirmar que la OC esté integrada en Manhattan
                3. Revisar con el área de Planning
                """,
                timestamp=datetime.now(),
                modulo="VALIDACION_OC",
                datos_afectados={'oc': oc_numero}
            ))
            
        else:
            # Validar letra C en ID_CODE
            if 'ID_CODE' in df_oc.columns:
                sin_letra_c = df_oc[~df_oc['ID_CODE'].astype(str).str.startswith('C')]
                if not sin_letra_c.empty:
                    errores.append(ErrorDetectado(
                        tipo="OC_SIN_LETRA_C",
                        severidad=ErrorSeverity.MEDIO,
                        mensaje=f"⚠️ OC {oc_numero} sin letra 'C' en ID_CODE",
                        detalles=f"Se encontraron {len(sin_letra_c)} registros sin letra C",
                        solucion="Notificar a Planning para corrección en sistema",
                        timestamp=datetime.now(),
                        modulo="VALIDACION_OC",
                        datos_afectados={'oc': oc_numero, 'registros': len(sin_letra_c)}
                    ))
            
            # Validar vigencia de OC
            if 'VIGENCIA' in df_oc.columns:
                try:
                    df_oc['VIGENCIA'] = pd.to_datetime(df_oc['VIGENCIA'])
                    oc_vencidas = df_oc[df_oc['VIGENCIA'] < datetime.now()]
                    
                    if not oc_vencidas.empty:
                        errores.append(ErrorDetectado(
                            tipo="OC_VENCIDA",
                            severidad=ErrorSeverity.ALTO,
                            mensaje=f"⚠️ OC {oc_numero} VENCIDA",
                            detalles=f"La OC venció el {oc_vencidas['VIGENCIA'].min()}",
                            solucion="""
                            1. Contactar con proveedor
                            2. Solicitar extensión de vigencia
                            3. Evaluar cancelación si corresponde
                            """,
                            timestamp=datetime.now(),
                            modulo="VALIDACION_OC",
                            datos_afectados={'oc': oc_numero}
                        ))
                except (ValueError, TypeError) as e:
                    logger.warning(f"⚠️ No se pudo convertir fecha de vigencia para OC {oc_numero}: {e}")
                    # Si no se puede convertir fecha, continuar con siguiente registro

        self.errores_detectados.extend(errores)
        return errores

    def validar_distribuciones(self, df_oc: pd.DataFrame, df_distro: pd.DataFrame, 
                               oc_numero: str) -> List[ErrorDetectado]:
        """
        Valida consistencia entre OC y Distribuciones
        
        ERRORES DETECTADOS:
        - Distribución excedente (más distros que OC)
        - Distribución incompleta (menos distros que OC)
        - Sin distribuciones
        - SKU sin IP (Inner Pack)
        """
        errores = []
        
        if df_distro is None or df_distro.empty:
            errores.append(ErrorDetectado(
                tipo="SIN_DISTRIBUCIONES",
                severidad=ErrorSeverity.CRITICO,
                mensaje=f"🔴 OC {oc_numero} sin distribuciones",
                detalles="La OC no tiene distribuciones asignadas",
                solucion="""
                ACCIÓN INMEDIATA:
                1. Notificar a Planning URGENTE
                2. Solicitar creación de distribuciones
                3. Validar destinos de tiendas
                4. Confirmar fecha de entrega
                """,
                timestamp=datetime.now(),
                modulo="VALIDACION_DISTRO",
                datos_afectados={'oc': oc_numero}
            ))
            
        else:
            # Validar cantidades OC vs Distribuciones
            if 'TOTAL_OC' in df_oc.columns and 'TOTAL_DISTRO' in df_distro.columns:
                total_oc = df_oc['TOTAL_OC'].sum()
                total_distro = df_distro['TOTAL_DISTRO'].sum()
                diferencia = total_oc - total_distro
                
                if diferencia > 0:
                    errores.append(ErrorDetectado(
                        tipo="DISTRO_INCOMPLETA",
                        severidad=ErrorSeverity.ALTO,
                        mensaje=f"⚠️ OC {oc_numero}: Distribución INCOMPLETA",
                        detalles=f"Faltan {diferencia} unidades por distribuir",
                        solucion="""
                        1. Revisar SKU faltantes
                        2. Completar distribuciones pendientes
                        3. Validar con Planning destinos faltantes
                        """,
                        timestamp=datetime.now(),
                        modulo="VALIDACION_DISTRO",
                        datos_afectados={
                            'oc': oc_numero,
                            'total_oc': total_oc,
                            'total_distro': total_distro,
                            'diferencia': diferencia
                        }
                    ))
                    
                elif diferencia < 0:
                    errores.append(ErrorDetectado(
                        tipo="DISTRO_EXCEDENTE",
                        severidad=ErrorSeverity.CRITICO,
                        mensaje=f"🔴 OC {oc_numero}: Distribución EXCEDENTE",
                        detalles=f"Hay {abs(diferencia)} unidades DE MÁS distribuidas",
                        solucion="""
                        ⚠️ ACCIÓN URGENTE:
                        1. DETENER proceso de recibo
                        2. Notificar a Planning INMEDIATAMENTE
                        3. Corregir distribuciones excedentes
                        4. Re-validar antes de continuar
                        """,
                        timestamp=datetime.now(),
                        modulo="VALIDACION_DISTRO",
                        datos_afectados={
                            'oc': oc_numero,
                            'total_oc': total_oc,
                            'total_distro': total_distro,
                            'excedente': abs(diferencia)
                        }
                    ))
            
            # Validar SKU sin IP (Inner Pack)
            if 'IP' in df_distro.columns:
                sin_ip = df_distro[df_distro['IP'].isna() | (df_distro['IP'] == 0)]
                if not sin_ip.empty:
                    skus_sin_ip = sin_ip['SKU'].unique()
                    errores.append(ErrorDetectado(
                        tipo="SKU_SIN_IP",
                        severidad=ErrorSeverity.MEDIO,
                        mensaje=f"⚠️ OC {oc_numero}: {len(skus_sin_ip)} SKUs sin Inner Pack",
                        detalles=f"SKUs afectados: {', '.join(map(str, skus_sin_ip[:5]))}...",
                        solucion="""
                        1. Solicitar actualización de IP en sistema
                        2. Consultar con Compras el IP correcto
                        3. Actualizar en maestro de productos
                        """,
                        timestamp=datetime.now(),
                        modulo="VALIDACION_DISTRO",
                        datos_afectados={
                            'oc': oc_numero,
                            'skus_sin_ip': list(skus_sin_ip)
                        }
                    ))
        
        self.errores_detectados.extend(errores)
        self._procesar_alertas_criticas(errores)
        return errores
    
    def validar_asn_status(self, df_asn: pd.DataFrame, asn_numero: str) -> List[ErrorDetectado]:
        """
        Valida el status del ASN
        
        ERRORES DETECTADOS:
        - ASN no encontrado
        - ASN con status incorrecto
        - ASN sin actualización reciente
        """
        errores = []
        
        if df_asn is None or df_asn.empty:
            errores.append(ErrorDetectado(
                tipo="ASN_NO_ENCONTRADO",
                severidad=ErrorSeverity.ALTO,
                mensaje=f"⚠️ ASN {asn_numero} no encontrado",
                detalles="El ASN no existe en el sistema",
                solucion="""
                1. Verificar número de ASN
                2. Confirmar integración desde EDI
                3. Revisar logs de integración
                4. Contactar con proveedor
                """,
                timestamp=datetime.now(),
                modulo="VALIDACION_ASN",
                datos_afectados={'asn': asn_numero}
            ))
        
        else:
            # Validar status del ASN
            if 'STATUS' in df_asn.columns:
                status_actual = df_asn['STATUS'].iloc[0]
                
                # Status válidos: 10=Creado, 40=En proceso, 90=Recibido
                status_invalidos = df_asn[~df_asn['STATUS'].isin([10, 40, 90])]
                
                if not status_invalidos.empty:
                    errores.append(ErrorDetectado(
                        tipo="ASN_STATUS_INVALIDO",
                        severidad=ErrorSeverity.MEDIO,
                        mensaje=f"⚠️ ASN {asn_numero} con status inválido: {status_actual}",
                        detalles="El status del ASN no es reconocido por el sistema",
                        solucion="Revisar con soporte técnico el status del ASN",
                        timestamp=datetime.now(),
                        modulo="VALIDACION_ASN",
                        datos_afectados={'asn': asn_numero, 'status': status_actual}
                    ))
            
            # Validar fecha de última actualización
            if 'ULTIMA_MOD' in df_asn.columns:
                try:
                    ultima_mod = pd.to_datetime(df_asn['ULTIMA_MOD'].iloc[0])
                    dias_sin_actualizacion = (datetime.now() - ultima_mod).days
                    
                    if dias_sin_actualizacion > 7:
                        errores.append(ErrorDetectado(
                            tipo="ASN_SIN_ACTUALIZACION",
                            severidad=ErrorSeverity.BAJO,
                            mensaje=f"ℹ️ ASN {asn_numero} sin actualización hace {dias_sin_actualizacion} días",
                            detalles=f"Última modificación: {ultima_mod.strftime('%Y-%m-%d')}",
                            solucion="Verificar status con proveedor y Planning",
                            timestamp=datetime.now(),
                            modulo="VALIDACION_ASN",
                            datos_afectados={'asn': asn_numero, 'dias': dias_sin_actualizacion}
                        ))
                except (ValueError, TypeError) as e:
                    logger.warning(f"⚠️ No se pudo convertir fecha ULTIMA_MOD para ASN {asn_numero}: {e}")
                    # Si no se puede convertir fecha, continuar con siguiente registro

        self.errores_detectados.extend(errores)
        return errores

    def validar_datos_excel(self, df: pd.DataFrame, columnas_requeridas: List[str]) -> List[ErrorDetectado]:
        """
        Valida integridad de datos de Excel
        
        ERRORES DETECTADOS:
        - Columnas faltantes
        - Datos nulos
        - Formatos incorrectos
        """
        errores = []
        
        if df is None or df.empty:
            errores.append(ErrorDetectado(
                tipo="EXCEL_VACIO",
                severidad=ErrorSeverity.ALTO,
                mensaje="⚠️ Archivo Excel vacío o inválido",
                detalles="No se pudieron leer datos del archivo",
                solucion="""
                1. Verificar que el archivo no esté dañado
                2. Confirmar formato correcto
                3. Revisar permisos de lectura
                """,
                timestamp=datetime.now(),
                modulo="VALIDACION_EXCEL"
            ))
        
        else:
            # Validar columnas requeridas
            columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]
            
            if columnas_faltantes:
                errores.append(ErrorDetectado(
                    tipo="COLUMNAS_FALTANTES",
                    severidad=ErrorSeverity.ALTO,
                    mensaje="⚠️ Columnas requeridas faltantes en Excel",
                    detalles=f"Faltan: {', '.join(columnas_faltantes)}",
                    solucion="""
                    1. Verificar plantilla de Excel correcta
                    2. No modificar nombres de columnas
                    3. Usar plantilla proporcionada por el sistema
                    """,
                    timestamp=datetime.now(),
                    modulo="VALIDACION_EXCEL",
                    datos_afectados={'columnas_faltantes': columnas_faltantes}
                ))
            
            # Validar datos nulos en columnas críticas
            for col in columnas_requeridas:
                if col in df.columns:
                    nulos = df[col].isna().sum()
                    if nulos > 0:
                        errores.append(ErrorDetectado(
                            tipo="DATOS_NULOS",
                            severidad=ErrorSeverity.MEDIO,
                            mensaje=f"⚠️ {nulos} valores nulos en columna '{col}'",
                            detalles=f"Se encontraron datos faltantes en campo crítico",
                            solucion=f"Completar todos los valores en columna '{col}'",
                            timestamp=datetime.now(),
                            modulo="VALIDACION_EXCEL",
                            datos_afectados={'columna': col, 'nulos': nulos}
                        ))
        
        self.errores_detectados.extend(errores)
        return errores
    
    def _procesar_alertas_criticas(self, errores: List[ErrorDetectado]):
        """Procesa y envía alertas críticas"""
        criticos = [e for e in errores if e.severidad == ErrorSeverity.CRITICO]
        
        if criticos:
            self.alertas_criticas.extend(criticos)
            
            # Si hay email configurado, enviar alerta
            if self.email_config:
                self._enviar_alerta_critica(criticos)
    
    def _enviar_alerta_critica(self, errores: List[ErrorDetectado]):
        """Envía email con alerta crítica"""
        try:
            asunto = f"🚨 ALERTA CRÍTICA - Sistema Planning CEDIS - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            cuerpo = self._generar_html_alerta(errores)
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = asunto
            msg['From'] = self.email_config.get('user')
            msg['To'] = self.email_config.get('alert_recipients', self.email_config.get('user'))
            
            msg.attach(MIMEText(cuerpo, 'html'))
            
            with smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port']) as server:
                server.starttls()
                server.login(self.email_config['user'], self.email_config['password'])
                server.send_message(msg)
                
            logger.info(f"✅ Alerta crítica enviada: {len(errores)} errores")
            
        except Exception as e:
            logger.error(f"❌ Error al enviar alerta crítica: {str(e)}")
    
    def _generar_html_alerta(self, errores: List[ErrorDetectado]) -> str:
        """Genera HTML para email de alerta"""
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .header {{ background-color: #dc3545; color: white; padding: 20px; }}
                .error {{ border-left: 4px solid #dc3545; padding: 10px; margin: 10px 0; background-color: #f8d7da; }}
                .solucion {{ background-color: #fff3cd; padding: 10px; margin-top: 5px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🚨 ALERTA CRÍTICA - Sistema Planning</h1>
                <p>Errores detectados: {len(errores)}</p>
                <p>Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        """
        
        for error in errores:
            html += f"""
            <div class="error">
                <h3>{error.severidad.value} {error.tipo}</h3>
                <p><strong>Mensaje:</strong> {error.mensaje}</p>
                <p><strong>Detalles:</strong> {error.detalles}</p>
                <p><strong>Módulo:</strong> {error.modulo}</p>
                <div class="solucion">
                    <strong>💡 Solución:</strong>
                    <pre>{error.solucion}</pre>
                </div>
            </div>
            """
        
        html += """
            <hr>
            <p><em>Sistema desarrollado por: Julián Alexander Juárez Alvarado (ADM)</em></p>
            <p><em>Analista de Sistemas - CEDIS Chedraui Logística Cancún</em></p>
        </body>
        </html>
        """
        
        return html
    
    def generar_reporte_errores(self) -> pd.DataFrame:
        """Genera DataFrame con todos los errores detectados"""
        if not self.errores_detectados:
            return pd.DataFrame()
        
        data = []
        for error in self.errores_detectados:
            data.append({
                'Timestamp': error.timestamp,
                'Severidad': error.severidad.value,
                'Tipo': error.tipo,
                'Mensaje': error.mensaje,
                'Detalles': error.detalles,
                'Módulo': error.modulo,
                'Solución': error.solucion
            })
        
        return pd.DataFrame(data)
    
    def limpiar_errores(self):
        """Limpia el registro de errores"""
        self.errores_detectados.clear()
        self.alertas_criticas.clear()
        logger.info("🧹 Registro de errores limpiado")


class ValidadorProactivo:
    """
    Validador proactivo que previene errores antes de que ocurran
    """
    
    def __init__(self):
        self.monitor = MonitorTiempoReal()
    
    def validacion_completa_oc(self, db_connection, oc_numero: str, storerkey: str = "C22") -> Tuple[bool, List[ErrorDetectado]]:
        """
        Realiza validación completa de una OC antes de procesarla

        Args:
            db_connection: Instancia de DB2Connection conectada
            oc_numero: Número de OC a validar
            storerkey: Código de almacén (default: C22 para Cancún)

        Returns:
            Tuple[bool, List[ErrorDetectado]]: (es_valida, lista_errores)
        """
        logger.info(f"🔍 Iniciando validación completa de OC: {oc_numero}")

        todos_errores = []

        # 1. Validar conexión DB
        errores_db = self.monitor.validar_conexion_db(db_connection)
        todos_errores.extend(errores_db)

        if any(e.severidad == ErrorSeverity.CRITICO for e in errores_db):
            return False, todos_errores

        # 2. Consultar OC desde la base de datos
        try:
            from queries import load_query_with_params, QueryCategory

            # Cargar y ejecutar query de búsqueda de OC
            sql_oc = load_query_with_params(
                QueryCategory.BAJO_DEMANDA,
                "buscar_oc",
                {"oc_numero": oc_numero, "storerkey": storerkey}
            )
            df_oc = db_connection.execute_query(sql_oc)
            logger.info(f"📊 OC {oc_numero}: {len(df_oc)} registros encontrados")

            # Validar que la OC exista
            errores_oc = self.monitor.validar_oc_existente(df_oc, oc_numero)
            todos_errores.extend(errores_oc)

            # Si la OC no existe, no continuar con validación de distribuciones
            if df_oc.empty:
                logger.warning(f"⚠️ OC {oc_numero}: No encontrada en el sistema")
                return False, todos_errores

        except Exception as e:
            logger.error(f"❌ Error consultando OC {oc_numero}: {str(e)}")
            todos_errores.append(ErrorDetectado(
                tipo="ERROR_CONSULTA_OC",
                severidad=ErrorSeverity.CRITICO,
                mensaje=f"Error al consultar OC {oc_numero}",
                detalles=str(e),
                solucion="Verificar conexión a DB2 y permisos de acceso",
                timestamp=datetime.now(),
                modulo="VALIDACION_PROACTIVA"
            ))
            return False, todos_errores

        # 3. Consultar Distribuciones asociadas a la OC
        try:
            sql_distro = load_query_with_params(
                QueryCategory.BAJO_DEMANDA,
                "detalle_distribucion",
                {"oc_referencia": oc_numero, "storerkey": storerkey, "tienda_destino": "%"}
            )
            df_distro = db_connection.execute_query(sql_distro)
            logger.info(f"📊 Distribuciones para OC {oc_numero}: {len(df_distro)} registros")

            # Validar distribuciones contra OC
            errores_distro = self.monitor.validar_distribuciones(df_oc, df_distro, oc_numero)
            todos_errores.extend(errores_distro)

        except Exception as e:
            logger.error(f"❌ Error consultando distribuciones para OC {oc_numero}: {str(e)}")
            todos_errores.append(ErrorDetectado(
                tipo="ERROR_CONSULTA_DISTRIBUCIONES",
                severidad=ErrorSeverity.ALTO,
                mensaje=f"Error al consultar distribuciones de OC {oc_numero}",
                detalles=str(e),
                solucion="Verificar conexión a DB2 y estructura de tablas",
                timestamp=datetime.now(),
                modulo="VALIDACION_PROACTIVA"
            ))

        # Determinar si es válida (sin errores críticos)
        tiene_criticos = any(e.severidad == ErrorSeverity.CRITICO for e in todos_errores)

        if tiene_criticos:
            logger.warning(f"⚠️ OC {oc_numero}: VALIDACIÓN FALLIDA - {len(todos_errores)} errores encontrados")
            return False, todos_errores
        else:
            logger.info(f"✅ OC {oc_numero}: Validación exitosa ({len(todos_errores)} advertencias)")
            return True, todos_errores


# ═══════════════════════════════════════════════════════════════
# VALIDADOR AVANZADO CON 10+ VALIDACIONES ADICIONALES
# ═══════════════════════════════════════════════════════════════

class ValidadorAvanzado:
    """
    Validador avanzado con 10+ validaciones adicionales
    para el sistema de Planning de Chedraui CEDIS
    """

    def __init__(self, email_config=None):
        self.errores_detectados: List[ErrorDetectado] = []
        self.email_config = email_config

    def validar_secuencia_oc(self, df_oc: pd.DataFrame,
                            oc_col: str = 'OC_NUMERO') -> List[ErrorDetectado]:
        """Valida la secuencia de números de OC (detecta gaps)"""
        errores = []
        if df_oc is None or df_oc.empty or oc_col not in df_oc.columns:
            return errores
        try:
            numeros = df_oc[oc_col].astype(str).str.extract(r'(\d+)')[0]
            numeros = pd.to_numeric(numeros, errors='coerce').dropna().astype(int)
            if len(numeros) > 1:
                numeros_sorted = sorted(numeros.unique())
                gaps = [(numeros_sorted[i-1], numeros_sorted[i])
                       for i in range(1, len(numeros_sorted))
                       if numeros_sorted[i] - numeros_sorted[i-1] > 1]
                if gaps:
                    errores.append(ErrorDetectado(
                        tipo="SECUENCIA_OC_GAPS", severidad=ErrorSeverity.BAJO,
                        mensaje=f"ℹ️ {len(gaps)} gaps en secuencia de OC",
                        detalles=f"Gaps: {gaps[:5]}...",
                        solucion="Verificar OC faltantes", timestamp=datetime.now(),
                        modulo="VALIDACION_SECUENCIA"))
        except Exception as e:
            logger.warning(f"Error validando secuencia: {e}")
        self.errores_detectados.extend(errores)
        return errores

    def validar_proveedor_activo(self, df_proveedores: pd.DataFrame,
                                proveedor_id: str) -> List[ErrorDetectado]:
        """Valida que el proveedor esté activo"""
        errores = []
        if df_proveedores is None or df_proveedores.empty:
            return errores
        if 'STATUS' in df_proveedores.columns:
            prov = df_proveedores[df_proveedores['ID'] == proveedor_id]
            if not prov.empty:
                status = prov['STATUS'].iloc[0]
                if str(status).upper() not in ['ACTIVO', 'ACTIVE', '1', 'A']:
                    errores.append(ErrorDetectado(
                        tipo="PROVEEDOR_INACTIVO", severidad=ErrorSeverity.ALTO,
                        mensaje=f"⚠️ Proveedor {proveedor_id} no está activo",
                        detalles=f"Status: {status}",
                        solucion="Verificar con Compras", timestamp=datetime.now(),
                        modulo="VALIDACION_PROVEEDOR"))
        self.errores_detectados.extend(errores)
        return errores

    def validar_tienda_activa(self, df_tiendas: pd.DataFrame, tienda_id: str) -> List[ErrorDetectado]:
        """Valida que la tienda esté activa"""
        errores = []
        if df_tiendas is None or df_tiendas.empty:
            return errores
        tienda = df_tiendas[df_tiendas['TIENDA'] == tienda_id]
        if tienda.empty:
            errores.append(ErrorDetectado(
                tipo="TIENDA_NO_ENCONTRADA", severidad=ErrorSeverity.ALTO,
                mensaje=f"⚠️ Tienda {tienda_id} no existe",
                detalles="Tienda no registrada", solucion="Verificar código",
                timestamp=datetime.now(), modulo="VALIDACION_TIENDA"))
        elif 'STATUS' in df_tiendas.columns:
            status = tienda['STATUS'].iloc[0]
            if str(status).upper() not in ['ACTIVA', 'ACTIVE', '1', 'A']:
                errores.append(ErrorDetectado(
                    tipo="TIENDA_INACTIVA", severidad=ErrorSeverity.CRITICO,
                    mensaje=f"🔴 Tienda {tienda_id} inactiva",
                    detalles=f"Status: {status}", solucion="Remover de distribuciones",
                    timestamp=datetime.now(), modulo="VALIDACION_TIENDA"))
        self.errores_detectados.extend(errores)
        return errores

    def validar_ruta_entrega(self, df_rutas: pd.DataFrame, tienda_id: str) -> List[ErrorDetectado]:
        """Valida ruta de entrega para la tienda"""
        errores = []
        if df_rutas is None or df_rutas.empty:
            return errores
        rutas = df_rutas[df_rutas['TIENDA'] == tienda_id]
        if rutas.empty:
            errores.append(ErrorDetectado(
                tipo="SIN_RUTA_ENTREGA", severidad=ErrorSeverity.ALTO,
                mensaje=f"⚠️ Sin ruta para tienda {tienda_id}",
                detalles="No hay ruta configurada", solucion="Asignar ruta",
                timestamp=datetime.now(), modulo="VALIDACION_RUTA"))
        self.errores_detectados.extend(errores)
        return errores

    def validar_capacidad_almacen(self, inv_actual: float, entrada: float,
                                  capacidad_max: float) -> List[ErrorDetectado]:
        """Valida capacidad de almacén"""
        errores = []
        if (inv_actual + entrada) > capacidad_max:
            excedente = (inv_actual + entrada) - capacidad_max
            errores.append(ErrorDetectado(
                tipo="CAPACIDAD_EXCEDIDA", severidad=ErrorSeverity.CRITICO,
                mensaje="🔴 Capacidad será excedida",
                detalles=f"Actual:{inv_actual:,.0f} +Entrada:{entrada:,.0f} > Cap:{capacidad_max:,.0f}",
                solucion="Coordinar salidas antes de recibir",
                timestamp=datetime.now(), modulo="VALIDACION_CAPACIDAD"))
        self.errores_detectados.extend(errores)
        return errores

    def validar_horario_recibo(self, hora: int = None,
                              hora_inicio: int = 6, hora_fin: int = 22) -> List[ErrorDetectado]:
        """Valida horario de recibo"""
        errores = []
        if hora is None:
            hora = datetime.now().hour
        if hora < hora_inicio or hora >= hora_fin:
            errores.append(ErrorDetectado(
                tipo="FUERA_HORARIO_RECIBO", severidad=ErrorSeverity.MEDIO,
                mensaje=f"⚠️ Hora {hora}:00 fuera de operación",
                detalles=f"Horario: {hora_inicio}:00-{hora_fin}:00",
                solucion="Reprogramar", timestamp=datetime.now(), modulo="VALIDACION_HORARIO"))
        self.errores_detectados.extend(errores)
        return errores

    def validar_documentacion_completa(self, docs_presentes: List[str],
                                       docs_requeridos: List[str] = None) -> List[ErrorDetectado]:
        """Valida documentación completa"""
        errores = []
        if docs_requeridos is None:
            docs_requeridos = ['FACTURA', 'REMISION', 'OC']
        faltantes = [d for d in docs_requeridos if d.upper() not in [p.upper() for p in docs_presentes]]
        if faltantes:
            errores.append(ErrorDetectado(
                tipo="DOCUMENTOS_FALTANTES", severidad=ErrorSeverity.ALTO,
                mensaje=f"⚠️ Documentos faltantes: {', '.join(faltantes)}",
                detalles=f"Presentes: {docs_presentes}", solucion="Completar documentación",
                timestamp=datetime.now(), modulo="VALIDACION_DOCS"))
        self.errores_detectados.extend(errores)
        return errores

    def validar_aprobaciones(self, aprobaciones_actuales: int,
                            aprobaciones_requeridas: int = 1) -> List[ErrorDetectado]:
        """Valida aprobaciones completas"""
        errores = []
        if aprobaciones_actuales < aprobaciones_requeridas:
            errores.append(ErrorDetectado(
                tipo="APROBACIONES_INCOMPLETAS", severidad=ErrorSeverity.ALTO,
                mensaje=f"⚠️ Aprobaciones: {aprobaciones_actuales}/{aprobaciones_requeridas}",
                detalles="Faltan aprobaciones", solucion="Solicitar aprobaciones",
                timestamp=datetime.now(), modulo="VALIDACION_APROBACIONES"))
        self.errores_detectados.extend(errores)
        return errores

    def validar_presupuesto(self, monto_oc: float, disponible: float) -> List[ErrorDetectado]:
        """Valida presupuesto disponible"""
        errores = []
        if monto_oc > disponible:
            errores.append(ErrorDetectado(
                tipo="PRESUPUESTO_EXCEDIDO", severidad=ErrorSeverity.CRITICO,
                mensaje="🔴 Monto excede presupuesto",
                detalles=f"OC:${monto_oc:,.2f} > Disp:${disponible:,.2f}",
                solucion="Solicitar ampliación", timestamp=datetime.now(),
                modulo="VALIDACION_PRESUPUESTO"))
        self.errores_detectados.extend(errores)
        return errores

    def validar_prioridad(self, df_oc: pd.DataFrame) -> List[ErrorDetectado]:
        """Alerta sobre OC de alta prioridad"""
        errores = []
        if df_oc is None or df_oc.empty or 'PRIORIDAD' not in df_oc.columns:
            return errores
        alta = df_oc[df_oc['PRIORIDAD'].isin(['ALTA', 'URGENTE', 'CRITICA', 1])]
        if not alta.empty:
            errores.append(ErrorDetectado(
                tipo="OC_ALTA_PRIORIDAD", severidad=ErrorSeverity.INFO,
                mensaje=f"ℹ️ {len(alta)} OC(s) con alta prioridad",
                detalles="Requieren atención prioritaria", solucion="Procesar primero",
                timestamp=datetime.now(), modulo="VALIDACION_PRIORIDAD"))
        self.errores_detectados.extend(errores)
        return errores

    def generar_reporte_errores(self) -> pd.DataFrame:
        """Genera DataFrame con errores detectados"""
        if not self.errores_detectados:
            return pd.DataFrame()
        return pd.DataFrame([{
            'Timestamp': e.timestamp, 'Severidad': e.severidad.value,
            'Tipo': e.tipo, 'Mensaje': e.mensaje, 'Detalles': e.detalles,
            'Módulo': e.modulo, 'Solución': e.solucion
        } for e in self.errores_detectados])

    def limpiar_errores(self):
        """Limpia errores detectados"""
        self.errores_detectados.clear()


# ═══════════════════════════════════════════════════════════════
# FUNCIONES DE UTILIDAD
# ═══════════════════════════════════════════════════════════════

def imprimir_resumen_errores(errores: List[ErrorDetectado]):
    """Imprime un resumen de errores en consola"""
    if not errores:
        print("\n✅ No se detectaron errores\n")
        return
    
    print("\n" + "="*70)
    print(f"📊 RESUMEN DE ERRORES DETECTADOS: {len(errores)}")
    print("="*70 + "\n")
    
    # Agrupar por severidad
    por_severidad = {}
    for error in errores:
        severidad = error.severidad.value
        if severidad not in por_severidad:
            por_severidad[severidad] = []
        por_severidad[severidad].append(error)
    
    # Mostrar por severidad
    for severidad in [ErrorSeverity.CRITICO, ErrorSeverity.ALTO, ErrorSeverity.MEDIO, 
                      ErrorSeverity.BAJO, ErrorSeverity.INFO]:
        sev_str = severidad.value
        if sev_str in por_severidad:
            print(f"\n{sev_str} ({len(por_severidad[sev_str])} errores):")
            print("-" * 70)
            for error in por_severidad[sev_str]:
                print(f"\n  • {error.mensaje}")
                print(f"    Módulo: {error.modulo}")
                print(f"    {error.detalles}")
    
    print("\n" + "="*70 + "\n")


# ═══════════════════════════════════════════════════════════════
# EJEMPLO DE USO
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("""
    ═══════════════════════════════════════════════════════════════
    SISTEMA DE MONITOREO Y DETECCIÓN DE ERRORES EN TIEMPO REAL
    Chedraui CEDIS - Automatización de Planning
    ═══════════════════════════════════════════════════════════════
    
    Desarrollado con ❤️ por:
    Julián Alexander Juárez Alvarado (ADM)
    Analista de Sistemas - CEDIS Chedraui Logística Cancún
    
    "Las máquinas y los sistemas al servicio de los analistas"
    
    ═══════════════════════════════════════════════════════════════
    """)
    
    # Ejemplo de uso
    monitor = MonitorTiempoReal()
    
    print("\n🔍 Iniciando validaciones de ejemplo...\n")
    
    # Simular validaciones
    print("1. Validando conexión DB2...")
    # errores = monitor.validar_conexion_db(None)  # Simular sin conexión
    
    print("2. Validando OC...")
    # errores = monitor.validar_oc_existente(pd.DataFrame(), "OC12345")
    
    print("\n✅ Demo completada\n")
