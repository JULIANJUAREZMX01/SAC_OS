"""
═══════════════════════════════════════════════════════════════
MÓDULO DE GESTIÓN DE UBICACIONES Y STOCK
Sistema de Gestión de Órdenes de Compra - Chedraui CEDIS
═══════════════════════════════════════════════════════════════

Este módulo maneja la gestión completa de ubicaciones:
- Consulta de ubicaciones por zona, pasillo, nivel
- Análisis de ocupación del almacén
- Validación de códigos verificadores
- Gestión de stock por ubicación
- Optimización de ubicaciones

Desarrollado por: Julián Alexander Juárez Alvarado (ADM)
═══════════════════════════════════════════════════════════════
"""

import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# Constantes del módulo
DEFAULT_ALMACEN = '427'
DEFAULT_TIENDA = '00002'
DEFAULT_DIVISION = 'SECOS'


class GestorUbicaciones:
    """
    Gestor completo de ubicaciones y stock en almacén
    """

    def __init__(self, almacen: str = DEFAULT_ALMACEN):
        self.almacen = almacen
    
    def consultar_ubicaciones(
        self,
        db_connection,
        filtros: Dict = None
    ) -> pd.DataFrame:
        """
        Consulta ubicaciones del almacén con filtros
        
        Filtros disponibles:
        - ubicacion: Código de ubicación específica
        - area: Área del almacén
        - zona: Zona específica
        - pasillo: Número de pasillo
        - nivel: Nivel de estantería
        - estado: Estado de la ubicación
        - zona_consolidacion: Zona de consolidación
        """
        if filtros is None:
            filtros = {}
        
        query = """
        SELECT DISTINCT
            ILWHSE AS ALMACEN,
            ILAREA AS AREA,
            ILZONE AS ZONA,
            ILLBCD AS UBICACION,
            ILCHKD AS DIG_VERIF,
            ILBAY AS BAHIA,
            ILAISL AS PASILLO,
            ILLEVL AS NIVEL,
            ILPOSN AS POSICION,
            OLCNZN AS ZONA_CONS,
            ILACTV AS VOL_REAL,
            ILACTW AS PESO_REAL,
            ILACTC AS CART_REAL,
            ILMAXP AS PALL_MAX,
            ILACTP AS PALL_REAL,
            ILDPIP AS PALL_DIRIG,
            ILREMP AS PALL_REST
        FROM WM260BASD.ILLOCN00
        INNER JOIN WM260BASD.OLCONS00 
            ON ILWHSE = OLWHSE
        WHERE ILWHSE = ?
        """
        
        params = [self.almacen]
        
        # Aplicar filtros
        if filtros.get('ubicacion'):
            if isinstance(filtros['ubicacion'], list):
                placeholders = ','.join(['?'] * len(filtros['ubicacion']))
                query += f" AND ILLBCD IN ({placeholders})"
                params.extend(filtros['ubicacion'])
            else:
                query += " AND ILLBCD = ?"
                params.append(filtros['ubicacion'])
        
        if filtros.get('area'):
            query += " AND ILAREA = ?"
            params.append(filtros['area'])
        
        if filtros.get('zona'):
            query += " AND ILZONE = ?"
            params.append(filtros['zona'])
        
        if filtros.get('pasillo'):
            query += " AND ILAISL = ?"
            params.append(filtros['pasillo'])
        
        if filtros.get('nivel'):
            query += " AND ILLEVL = ?"
            params.append(filtros['nivel'])
        
        logger.info(f"🔍 Consultando ubicaciones - Almacén {self.almacen}")
        
        try:
            df = pd.read_sql(query, db_connection, params=params)
            logger.info(f"✅ Se encontraron {len(df)} ubicaciones")
            return df
        except (pd.io.sql.DatabaseError, Exception) as e:
            error_type = type(e).__name__
            logger.error(f"❌ Error al consultar ubicaciones [{error_type}]: {str(e)}")
            logger.debug(f"Query fallido: {query[:100]}... params: {params}")
            return pd.DataFrame()
    
    def validar_codigo_verificador(
        self,
        db_connection,
        ubicacion: str
    ) -> Optional[str]:
        """
        Obtiene el código verificador de una ubicación
        
        El código verificador es usado para validación en RF
        """
        query = """
        SELECT 
            ILLBCD AS UBICACION, 
            ILCHKD AS DIG_VERIF 
        FROM WM260BASD.ILLOCN00
        WHERE ILLBCD = ?
        AND ILWHSE = ?
        """
        
        try:
            df = pd.read_sql(query, db_connection, params=[ubicacion, self.almacen])

            if df.empty:
                logger.warning(f"⚠️ Ubicación {ubicacion} no encontrada")
                return None

            dig_verif = df['DIG_VERIF'].iloc[0]
            logger.info(f"✅ Código verificador de {ubicacion}: {dig_verif}")
            return dig_verif

        except KeyError as e:
            logger.error(f"❌ Columna faltante en resultado: {e}")
            return None
        except (pd.io.sql.DatabaseError, Exception) as e:
            error_type = type(e).__name__
            logger.error(f"❌ Error al validar código [{error_type}]: {str(e)}")
            return None
    
    def analizar_ocupacion_almacen(
        self,
        df_ubicaciones: pd.DataFrame
    ) -> Dict:
        """
        Analiza la ocupación del almacén
        
        Calcula:
        - Porcentaje de ocupación por zona
        - Ubicaciones disponibles vs ocupadas
        - Capacidad máxima vs actual
        - Zonas con mayor/menor ocupación
        """
        analisis = {
            'total_ubicaciones': len(df_ubicaciones),
            'por_zona': {},
            'estadisticas': {},
            'recomendaciones': []
        }
        
        # Análisis por zona
        if 'ZONA' in df_ubicaciones.columns:
            for zona in df_ubicaciones['ZONA'].unique():
                df_zona = df_ubicaciones[df_ubicaciones['ZONA'] == zona]
                
                # Calcular ocupación
                pall_max = df_zona['PALL_MAX'].sum()
                pall_real = df_zona['PALL_REAL'].sum()
                
                if pall_max > 0:
                    ocupacion = (pall_real / pall_max) * 100
                else:
                    ocupacion = 0
                
                analisis['por_zona'][zona] = {
                    'ubicaciones': len(df_zona),
                    'capacidad_maxima': pall_max,
                    'ocupacion_actual': pall_real,
                    'disponible': pall_max - pall_real,
                    'porcentaje_ocupacion': round(ocupacion, 2)
                }
                
                # Detectar zonas críticas
                if ocupacion > 95:
                    analisis['recomendaciones'].append(
                        f"⚠️ Zona {zona} al {round(ocupacion, 1)}% - Considerar reubicación"
                    )
                elif ocupacion < 30:
                    analisis['recomendaciones'].append(
                        f"ℹ️ Zona {zona} con baja ocupación ({round(ocupacion, 1)}%) - Oportunidad de optimización"
                    )
        
        # Estadísticas generales
        total_pall_max = df_ubicaciones['PALL_MAX'].sum()
        total_pall_real = df_ubicaciones['PALL_REAL'].sum()
        
        analisis['estadisticas'] = {
            'capacidad_total': total_pall_max,
            'ocupacion_total': total_pall_real,
            'disponible_total': total_pall_max - total_pall_real,
            'porcentaje_ocupacion_general': round((total_pall_real / total_pall_max) * 100, 2) if total_pall_max > 0 else 0
        }
        
        return analisis
    
    def buscar_ubicaciones_disponibles(
        self,
        df_ubicaciones: pd.DataFrame,
        zona: Optional[str] = None,
        minimo_pallets: int = 1
    ) -> pd.DataFrame:
        """
        Busca ubicaciones disponibles para almacenaje
        
        Args:
            df_ubicaciones: DataFrame con ubicaciones
            zona: Zona específica (opcional)
            minimo_pallets: Mínimo de pallets disponibles
        
        Returns:
            DataFrame con ubicaciones disponibles ordenadas
        """
        # Filtrar ubicaciones con espacio
        df_disponibles = df_ubicaciones[
            (df_ubicaciones['PALL_MAX'] - df_ubicaciones['PALL_REAL']) >= minimo_pallets
        ].copy()
        
        # Filtrar por zona si se especifica
        if zona:
            df_disponibles = df_disponibles[df_disponibles['ZONA'] == zona]
        
        # Calcular espacio disponible
        df_disponibles['ESPACIO_DISPONIBLE'] = (
            df_disponibles['PALL_MAX'] - df_disponibles['PALL_REAL']
        )
        
        # Ordenar por espacio disponible (mayor primero)
        df_disponibles = df_disponibles.sort_values('ESPACIO_DISPONIBLE', ascending=False)
        
        logger.info(f"✅ Se encontraron {len(df_disponibles)} ubicaciones disponibles")
        
        return df_disponibles[['UBICACION', 'ZONA', 'PASILLO', 'NIVEL', 
                               'PALL_MAX', 'PALL_REAL', 'ESPACIO_DISPONIBLE']]
    
    def consultar_sku_por_tipo_grupo(
        self,
        db_connection,
        tipo_mercaderia: str,
        grupo_mercaderia: str,
        tienda: str = '00002'
    ) -> pd.DataFrame:
        """
        Consulta SKU dentro de un tipo y grupo de mercadería definido
        
        Útil para:
        - Identificar productos en circuitos específicos
        - Validar asignaciones de mercadería
        - Análisis de categorías
        """
        query = """
        SELECT DISTINCT
            RLLBCD AS CIRCUITO,
            STDIV AS DIVISION,
            STSTYL AS SKU,
            STSTYD AS DESCRIPCION,
            RLSEQN AS SECUENCIA,
            STMRTP || '' || STMRGP AS TPO_GPO_MERC,
            STVNDR AS ID_PROV,
            VMVNAM AS PROVEEDOR
        FROM WM260BASD.STSTYL00,
             WM260BASD.RLLOCN00,
             WM260BASD.VMVNDR00
        WHERE STMRTP = RLMRTP 
        AND STMRGP = RLMRGP 
        AND STVNDR = VMVNDR
        AND RLSTOR = ?
        AND STDIV = ?
        AND STMRTP = ?
        AND STMRGP = ?
        GROUP BY RLLBCD, RLSEQN, STMRTP, STMRGP, STVNDR, 
                 VMVNAM, STDIV, STSTYL, STSTYD
        ORDER BY RLSEQN, STSTYL
        """
        
        params = [tienda, DEFAULT_DIVISION, tipo_mercaderia, grupo_mercaderia]
        
        logger.info(f"🔍 Consultando SKU para Tipo:{tipo_mercaderia} Grupo:{grupo_mercaderia}")
        
        try:
            df = pd.read_sql(query, db_connection, params=params)
            logger.info(f"✅ Se encontraron {len(df)} SKU")
            return df
        except (pd.io.sql.DatabaseError, Exception) as e:
            error_type = type(e).__name__
            logger.error(f"❌ Error al consultar SKU [{error_type}]: {str(e)}")
            logger.debug(f"Parámetros: tipo={tipo_mercaderia}, grupo={grupo_mercaderia}")
            return pd.DataFrame()
    
    def obtener_tipo_grupo_tienda(
        self,
        db_connection,
        tienda: str
    ) -> pd.DataFrame:
        """
        Obtiene tipos y grupos de mercadería asignados a una tienda
        
        Útil para conocer qué categorías maneja cada tienda
        """
        query = """
        SELECT DISTINCT
            RLSTOR AS TIENDA,
            RLMRTP AS TIPO_MERC,
            RLMRGP AS GRUPO_MERC,
            RLLBCD AS CIRCUITO,
            RLSEQN AS SECUENCIA
        FROM WM260BASD.RLLOCN00
        WHERE RLSTOR = ?
        ORDER BY RLSEQN
        """
        
        try:
            df = pd.read_sql(query, db_connection, params=[tienda])
            logger.info(f"✅ Tienda {tienda} tiene {len(df)} tipos/grupos configurados")
            return df
        except (pd.io.sql.DatabaseError, Exception) as e:
            error_type = type(e).__name__
            logger.error(f"❌ Error al consultar tipos/grupos [{error_type}] para tienda {tienda}: {str(e)}")
            return pd.DataFrame()
    
    def generar_mapa_almacen(
        self,
        df_ubicaciones: pd.DataFrame
    ) -> Dict:
        """
        Genera un 'mapa' del almacén organizando ubicaciones
        
        Agrupa por:
        - Zona
        - Pasillo
        - Nivel
        
        Útil para visualización y planning de ubicaciones
        """
        mapa = {}
        
        if df_ubicaciones.empty:
            return mapa
        
        # Agrupar por zona y pasillo
        for zona in df_ubicaciones['ZONA'].unique():
            df_zona = df_ubicaciones[df_ubicaciones['ZONA'] == zona]
            mapa[zona] = {}
            
            for pasillo in df_zona['PASILLO'].unique():
                df_pasillo = df_zona[df_zona['PASILLO'] == pasillo]
                
                ubicaciones = df_pasillo.sort_values(['NIVEL', 'POSICION'])[
                    ['UBICACION', 'NIVEL', 'POSICION', 'PALL_REAL', 'PALL_MAX']
                ].to_dict('records')
                
                mapa[zona][pasillo] = {
                    'total_ubicaciones': len(df_pasillo),
                    'ocupacion': df_pasillo['PALL_REAL'].sum(),
                    'capacidad': df_pasillo['PALL_MAX'].sum(),
                    'ubicaciones': ubicaciones
                }
        
        return mapa
    
    def generar_reporte_ubicaciones(
        self,
        df_ubicaciones: pd.DataFrame,
        nombre_archivo: str = None
    ) -> str:
        """
        Genera reporte completo de ubicaciones en Excel
        """
        if nombre_archivo is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            nombre_archivo = f"Reporte_Ubicaciones_{timestamp}.xlsx"
        
        logger.info(f"📊 Generando reporte de ubicaciones")
        
        with pd.ExcelWriter(nombre_archivo, engine='openpyxl') as writer:
            # Hoja 1: Todas las ubicaciones
            df_ubicaciones.to_excel(writer, sheet_name='Ubicaciones', index=False)
            
            # Hoja 2: Análisis de ocupación
            analisis = self.analizar_ocupacion_almacen(df_ubicaciones)
            
            # Convertir análisis por zona a DataFrame
            if analisis['por_zona']:
                df_zonas = pd.DataFrame.from_dict(analisis['por_zona'], orient='index')
                df_zonas.index.name = 'Zona'
                df_zonas.reset_index(inplace=True)
                df_zonas.to_excel(writer, sheet_name='Por Zona', index=False)
            
            # Hoja 3: Ubicaciones disponibles
            df_disponibles = self.buscar_ubicaciones_disponibles(df_ubicaciones)
            if not df_disponibles.empty:
                df_disponibles.to_excel(writer, sheet_name='Disponibles', index=False)
            
            # Hoja 4: Estadísticas generales
            df_stats = pd.DataFrame([analisis['estadisticas']])
            df_stats.to_excel(writer, sheet_name='Estadísticas', index=False)
            
            # Hoja 5: Recomendaciones
            if analisis['recomendaciones']:
                df_recom = pd.DataFrame({'Recomendaciones': analisis['recomendaciones']})
                df_recom.to_excel(writer, sheet_name='Recomendaciones', index=False)
        
        logger.info(f"✅ Reporte generado: {nombre_archivo}")
        return nombre_archivo


# ═══════════════════════════════════════════════════════════════
# FUNCIONES DE UTILIDAD
# ═══════════════════════════════════════════════════════════════

def obtener_codigo_verificador_rapido(
    db_connection,
    ubicacion: str,
    almacen: str = '427'
) -> Optional[str]:
    """Función rápida para obtener código verificador"""
    gestor = GestorUbicaciones(almacen=almacen)
    return gestor.validar_codigo_verificador(db_connection, ubicacion)


def buscar_ubicacion_disponible(
    db_connection,
    zona: str,
    almacen: str = '427'
) -> Optional[str]:
    """Busca la primera ubicación disponible en una zona"""
    gestor = GestorUbicaciones(almacen=almacen)
    df_ubicaciones = gestor.consultar_ubicaciones(db_connection, filtros={'zona': zona})
    df_disponibles = gestor.buscar_ubicaciones_disponibles(df_ubicaciones)
    
    if not df_disponibles.empty:
        return df_disponibles.iloc[0]['UBICACION']
    return None


# ═══════════════════════════════════════════════════════════════
# EJEMPLO DE USO
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("""
    ═══════════════════════════════════════════════════════════════
    MÓDULO DE GESTIÓN DE UBICACIONES Y STOCK
    Chedraui CEDIS - Sistema de Automatización
    ═══════════════════════════════════════════════════════════════
    
    Funcionalidades:
    ✓ Consulta de ubicaciones con filtros
    ✓ Validación de códigos verificadores
    ✓ Análisis de ocupación del almacén
    ✓ Búsqueda de ubicaciones disponibles
    ✓ Consulta de SKU por tipo y grupo
    ✓ Mapa del almacén
    ✓ Reportes completos en Excel
    
    Estructura de Ubicaciones:
    • ZONA: Área del almacén
    • PASILLO: Corredor o aisle
    • NIVEL: Altura en estantería
    • POSICIÓN: Posición específica
    • DIG_VERIF: Código verificador para RF
    
    ═══════════════════════════════════════════════════════════════
    """)
