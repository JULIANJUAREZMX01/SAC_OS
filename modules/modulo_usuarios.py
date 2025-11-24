"""
═══════════════════════════════════════════════════════════════
MÓDULO DE ANÁLISIS DE USUARIOS Y ACTIVIDADES
Sistema de Gestión de Órdenes de Compra - Chedraui CEDIS
═══════════════════════════════════════════════════════════════

Este módulo maneja el análisis de usuarios y actividades:
- Seguimiento de usuarios activos en WMS
- Análisis de productividad
- Actividades por usuario
- Detección de usuarios inactivos
- Reportes de rendimiento

Desarrollado por: Julián Alexander Juárez Alvarado (ADM)
═══════════════════════════════════════════════════════════════
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# Constantes del módulo
DEFAULT_ALMACEN = '427'
DATE_FORMAT = '%Y%m%d'
INACTIVITY_THRESHOLD_DAYS = 30
ESTADO_ACTIVO = 'ACTIVO'
ESTADO_INACTIVO = 'INACTIVO'


class AnalizadorUsuarios:
    """
    Analizador completo de usuarios y sus actividades en WMS
    """

    def __init__(self, almacen: str = DEFAULT_ALMACEN):
        self.almacen = almacen
    
    def consultar_usuarios_activos(
        self,
        db_connection
    ) -> pd.DataFrame:
        """
        Consulta todos los usuarios activos del almacén
        
        Retorna información de:
        - Usuario ID
        - Nombre
        - División
        - Puesto/perfil
        - Fecha de creación
        - Última modificación
        - Estado
        """
        query = """
        SELECT 
            WHSE AS ALMACEN,
            USRID AS USUARIO,
            NOMBRE,
            DIV AS DIVISION,
            KRONOS AS MATRICULA,
            TIPO_USUARIO,
            PUESTO,
            FCH_CREACION,
            FCH_MODIFICACION,
            ESTADO
        FROM WM260BASD.USUARIOS
        WHERE WHSE = ?
        AND ESTADO = 'ACTIVO'
        ORDER BY NOMBRE
        """
        
        logger.info(f"🔍 Consultando usuarios activos - Almacén {self.almacen}")
        
        try:
            # Nota: Esta consulta es conceptual - ajustar según tabla real
            df = pd.read_sql(query, db_connection, params=[self.almacen])
            logger.info(f"✅ Se encontraron {len(df)} usuarios activos")
            return df
        except (pd.io.sql.DatabaseError, Exception) as e:
            error_type = type(e).__name__
            logger.error(f"❌ Error al consultar usuarios [{error_type}]: {str(e)}")
            return pd.DataFrame()
    
    def analizar_actividad_usuario(
        self,
        db_connection,
        usuario: str,
        fecha_inicio: Optional[str] = None,
        fecha_fin: Optional[str] = None
    ) -> Dict:
        """
        Analiza la actividad de un usuario específico
        
        Args:
            usuario: ID del usuario
            fecha_inicio: Fecha inicio análisis (YYYYMMDD)
            fecha_fin: Fecha fin análisis (YYYYMMDD)
        
        Returns:
            Dict con métricas de actividad:
            - Total de transacciones
            - LPN procesados
            - Cartones manejados
            - Errores cometidos
            - Tiempo promedio por operación
        """
        if fecha_inicio is None:
            fecha_inicio = (datetime.now() - timedelta(days=7)).strftime('%Y%m%d')
        
        if fecha_fin is None:
            fecha_fin = datetime.now().strftime('%Y%m%d')
        
        analisis = {
            'usuario': usuario,
            'periodo': f"{fecha_inicio} - {fecha_fin}",
            'metricas': {},
            'actividades': []
        }
        
        # Consultar actividades del usuario
        query_actividades = """
        SELECT 
            FECHA,
            HORA,
            TIPO_ACTIVIDAD,
            OBJETO,
            CANTIDAD,
            ESTADO
        FROM WM260BASD.LOG_ACTIVIDADES
        WHERE USUARIO = ?
        AND FECHA BETWEEN ? AND ?
        ORDER BY FECHA DESC, HORA DESC
        """
        
        try:
            df_actividades = pd.read_sql(
                query_actividades,
                db_connection,
                params=[usuario, fecha_inicio, fecha_fin]
            )
            
            if not df_actividades.empty:
                # Calcular métricas
                analisis['metricas'] = {
                    'total_transacciones': len(df_actividades),
                    'lpn_procesados': len(df_actividades[
                        df_actividades['TIPO_ACTIVIDAD'] == 'LPN'
                    ]),
                    'cartones_manejados': len(df_actividades[
                        df_actividades['TIPO_ACTIVIDAD'] == 'CARTON'
                    ]),
                    'errores': len(df_actividades[
                        df_actividades['ESTADO'] == 'ERROR'
                    ]),
                    'tasa_error': 0
                }
                
                # Calcular tasa de error
                if analisis['metricas']['total_transacciones'] > 0:
                    analisis['metricas']['tasa_error'] = round(
                        (analisis['metricas']['errores'] / 
                         analisis['metricas']['total_transacciones']) * 100,
                        2
                    )
                
                analisis['actividades'] = df_actividades.to_dict('records')
            
            logger.info(f"✅ Análisis completado para usuario {usuario}")

        except (pd.io.sql.DatabaseError, KeyError) as e:
            error_type = type(e).__name__
            logger.error(f"❌ Error al analizar actividad [{error_type}]: {str(e)}")
        except Exception as e:
            error_type = type(e).__name__
            logger.error(f"❌ Error inesperado al analizar actividad [{error_type}]: {str(e)}")

        return analisis
    
    def generar_reporte_productividad(
        self,
        db_connection,
        fecha: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Genera reporte de productividad de todos los usuarios
        
        Métricas incluidas:
        - Transacciones por usuario
        - Tiempo promedio por transacción
        - Tasa de error
        - Ranking de productividad
        """
        if fecha is None:
            fecha = datetime.now().strftime('%Y%m%d')
        
        logger.info(f"📊 Generando reporte de productividad - Fecha: {fecha}")
        
        query = """
        SELECT 
            USUARIO,
            COUNT(*) AS TOTAL_TRANSACCIONES,
            COUNT(DISTINCT OBJETO) AS OBJETOS_UNICOS,
            SUM(CASE WHEN ESTADO = 'ERROR' THEN 1 ELSE 0 END) AS ERRORES,
            AVG(TIEMPO_PROCESO) AS TIEMPO_PROMEDIO
        FROM WM260BASD.LOG_ACTIVIDADES
        WHERE FECHA = ?
        GROUP BY USUARIO
        ORDER BY TOTAL_TRANSACCIONES DESC
        """
        
        try:
            df = pd.read_sql(query, db_connection, params=[fecha])
            
            if not df.empty:
                # Calcular tasa de error
                df['TASA_ERROR'] = round(
                    (df['ERRORES'] / df['TOTAL_TRANSACCIONES']) * 100,
                    2
                )
                
                # Calcular ranking
                df['RANKING'] = df['TOTAL_TRANSACCIONES'].rank(
                    ascending=False,
                    method='min'
                ).astype(int)
                
                logger.info(f"✅ Reporte generado con {len(df)} usuarios")

            return df

        except (pd.io.sql.DatabaseError, Exception) as e:
            error_type = type(e).__name__
            logger.error(f"❌ Error al generar reporte [{error_type}]: {str(e)}")
            return pd.DataFrame()
    
    def detectar_usuarios_inactivos(
        self,
        db_connection,
        dias_inactividad: int = 30
    ) -> pd.DataFrame:
        """
        Detecta usuarios que no han tenido actividad reciente
        
        Args:
            dias_inactividad: Días sin actividad para considerarse inactivo
        
        Returns:
            DataFrame con usuarios inactivos
        """
        fecha_limite = (datetime.now() - timedelta(days=dias_inactividad)).strftime('%Y%m%d')
        
        logger.info(f"🔍 Buscando usuarios inactivos (>{dias_inactividad} días)")
        
        query = """
        SELECT 
            U.USUARIO,
            U.NOMBRE,
            U.PUESTO,
            MAX(A.FECHA) AS ULTIMA_ACTIVIDAD,
            ? AS FECHA_LIMITE
        FROM WM260BASD.USUARIOS U
        LEFT JOIN WM260BASD.LOG_ACTIVIDADES A 
            ON U.USUARIO = A.USUARIO
        WHERE U.WHSE = ?
        AND U.ESTADO = 'ACTIVO'
        GROUP BY U.USUARIO, U.NOMBRE, U.PUESTO
        HAVING MAX(A.FECHA) < ? OR MAX(A.FECHA) IS NULL
        """
        
        try:
            df = pd.read_sql(
                query,
                db_connection,
                params=[fecha_limite, self.almacen, fecha_limite]
            )
            
            if not df.empty:
                logger.warning(f"⚠️ Se encontraron {len(df)} usuarios inactivos")
            else:
                logger.info("✅ No se encontraron usuarios inactivos")
            
            return df

        except (pd.io.sql.DatabaseError, Exception) as e:
            error_type = type(e).__name__
            logger.error(f"❌ Error al detectar inactivos [{error_type}]: {str(e)}")
            return pd.DataFrame()

    def analizar_errores_por_usuario(
        self,
        db_connection,
        fecha_inicio: str,
        fecha_fin: str
    ) -> pd.DataFrame:
        """
        Analiza errores cometidos por cada usuario
        
        Útil para:
        - Identificar usuarios que necesitan capacitación
        - Detectar patrones de errores
        - Mejoras en procesos
        """
        query = """
        SELECT 
            USUARIO,
            TIPO_ERROR,
            COUNT(*) AS CANTIDAD,
            FECHA
        FROM WM260BASD.LOG_ERRORES
        WHERE FECHA BETWEEN ? AND ?
        AND ALMACEN = ?
        GROUP BY USUARIO, TIPO_ERROR, FECHA
        ORDER BY CANTIDAD DESC
        """
        
        logger.info(f"🔍 Analizando errores por usuario")
        
        try:
            df = pd.read_sql(
                query,
                db_connection,
                params=[fecha_inicio, fecha_fin, self.almacen]
            )
            
            logger.info(f"✅ Análisis completado - {len(df)} registros de errores")
            return df

        except (pd.io.sql.DatabaseError, Exception) as e:
            error_type = type(e).__name__
            logger.error(f"❌ Error al analizar errores [{error_type}]: {str(e)}")
            return pd.DataFrame()

    def generar_dashboard_usuarios(
        self,
        db_connection,
        fecha: Optional[str] = None
    ) -> Dict:
        """
        Genera dashboard completo de usuarios
        
        Incluye:
        - Total de usuarios activos
        - Usuarios más productivos
        - Usuarios con más errores
        - Distribución de actividades
        - Recomendaciones
        """
        if fecha is None:
            fecha = datetime.now().strftime('%Y%m%d')
        
        dashboard = {
            'fecha': fecha,
            'usuarios_activos': 0,
            'top_productivos': [],
            'usuarios_con_errores': [],
            'estadisticas': {},
            'recomendaciones': []
        }
        
        # Obtener usuarios activos
        df_usuarios = self.consultar_usuarios_activos(db_connection)
        dashboard['usuarios_activos'] = len(df_usuarios)
        
        # Obtener reporte de productividad
        df_productividad = self.generar_reporte_productividad(db_connection, fecha)
        
        if not df_productividad.empty:
            # Top 5 más productivos
            dashboard['top_productivos'] = df_productividad.head(5).to_dict('records')
            
            # Usuarios con alta tasa de error
            df_errores = df_productividad[df_productividad['TASA_ERROR'] > 5]
            if not df_errores.empty:
                dashboard['usuarios_con_errores'] = df_errores.to_dict('records')
                dashboard['recomendaciones'].append(
                    f"⚠️ {len(df_errores)} usuarios con tasa de error > 5%"
                )
            
            # Estadísticas generales
            dashboard['estadisticas'] = {
                'total_transacciones': df_productividad['TOTAL_TRANSACCIONES'].sum(),
                'promedio_por_usuario': round(
                    df_productividad['TOTAL_TRANSACCIONES'].mean(),
                    2
                ),
                'total_errores': df_productividad['ERRORES'].sum(),
                'tasa_error_general': round(
                    (df_productividad['ERRORES'].sum() / 
                     df_productividad['TOTAL_TRANSACCIONES'].sum()) * 100,
                    2
                ) if df_productividad['TOTAL_TRANSACCIONES'].sum() > 0 else 0
            }
        
        return dashboard
    
    def generar_reporte_usuarios(
        self,
        df_usuarios: pd.DataFrame,
        df_productividad: Optional[pd.DataFrame] = None,
        nombre_archivo: str = None
    ) -> str:
        """
        Genera reporte completo de usuarios en Excel
        """
        if nombre_archivo is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            nombre_archivo = f"Reporte_Usuarios_{timestamp}.xlsx"
        
        logger.info(f"📊 Generando reporte de usuarios")
        
        with pd.ExcelWriter(nombre_archivo, engine='openpyxl') as writer:
            # Hoja 1: Usuarios activos
            df_usuarios.to_excel(writer, sheet_name='Usuarios Activos', index=False)
            
            # Hoja 2: Productividad (si se proporciona)
            if df_productividad is not None and not df_productividad.empty:
                df_productividad.to_excel(writer, sheet_name='Productividad', index=False)
            
            # Hoja 3: Resumen por puesto
            if 'PUESTO' in df_usuarios.columns:
                resumen_puesto = df_usuarios.groupby('PUESTO').size().reset_index(name='CANTIDAD')
                resumen_puesto.to_excel(writer, sheet_name='Por Puesto', index=False)
            
            # Hoja 4: Resumen por división
            if 'DIVISION' in df_usuarios.columns:
                resumen_div = df_usuarios.groupby('DIVISION').size().reset_index(name='CANTIDAD')
                resumen_div.to_excel(writer, sheet_name='Por División', index=False)
        
        logger.info(f"✅ Reporte generado: {nombre_archivo}")
        return nombre_archivo


# ═══════════════════════════════════════════════════════════════
# FUNCIONES DE UTILIDAD
# ═══════════════════════════════════════════════════════════════

def obtener_actividad_usuario_rapido(
    db_connection,
    usuario: str,
    almacen: str = '427'
) -> Dict:
    """Obtiene actividad rápida de un usuario (últimos 7 días)"""
    analizador = AnalizadorUsuarios(almacen=almacen)
    return analizador.analizar_actividad_usuario(db_connection, usuario)


def verificar_usuarios_inactivos(
    db_connection,
    almacen: str = '427',
    dias: int = 30
) -> pd.DataFrame:
    """Verifica usuarios inactivos rápidamente"""
    analizador = AnalizadorUsuarios(almacen=almacen)
    return analizador.detectar_usuarios_inactivos(db_connection, dias)


# ═══════════════════════════════════════════════════════════════
# EJEMPLO DE USO
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("""
    ═══════════════════════════════════════════════════════════════
    MÓDULO DE ANÁLISIS DE USUARIOS Y ACTIVIDADES
    Chedraui CEDIS - Sistema de Automatización
    ═══════════════════════════════════════════════════════════════
    
    Funcionalidades:
    ✓ Consulta de usuarios activos
    ✓ Análisis de actividad por usuario
    ✓ Reporte de productividad
    ✓ Detección de usuarios inactivos
    ✓ Análisis de errores por usuario
    ✓ Dashboard completo de usuarios
    ✓ Reportes en Excel
    
    Métricas de Productividad:
    • Total de transacciones
    • Objetos únicos procesados
    • Tasa de error
    • Tiempo promedio por operación
    • Ranking de productividad
    
    Usos:
    • Identificar usuarios top performers
    • Detectar necesidades de capacitación
    • Optimizar asignación de tareas
    • Reconocer desempeño destacado
    
    ═══════════════════════════════════════════════════════════════
    """)
