"""
═══════════════════════════════════════════════════════════════
MÓDULO DE ANÁLISIS COMPLETO DE LPN
Sistema de Gestión de Órdenes de Compra - Chedraui CEDIS
═══════════════════════════════════════════════════════════════

Este módulo maneja todo el análisis de LPN (License Plate Number):
- Seguimiento completo de LPN en inventario
- Estados y transiciones (01, 10, 65, 90, 95)
- Historial de movimientos
- Análisis de ubicaciones
- Detección de LPN problemáticos

Estados de LPN:
- 01: Mercancía no ingresada
- 10: Recibo no almacenado (en inventario, requiere liberación)
- 65: Pendiente por repartir (listo para preparación)
- 90: En repartición (en proceso de distribución)
- 95: Consumido (distribuido en tiendas - FIN)

Desarrollado por: Julián Alexander Juárez Alvarado (ADM)
═══════════════════════════════════════════════════════════════
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class AnalizadorLPN:
    """
    Analizador completo de LPN con seguimiento y estados
    """

    # Constantes de estados LPN para evitar strings hardcodeados
    ESTADO_NO_INGRESADO = '01'
    ESTADO_RECIBO_NO_ALMACENADO = '10'
    ESTADO_EN_PROCESO = '30'
    ESTADO_PENDIENTE_REPARTIR = '65'
    ESTADO_CON_PROBLEMA = '80'
    ESTADO_EN_REPARTICION = '90'
    ESTADO_CONSUMIDO = '95'

    # Definición de estados de LPN
    ESTADOS_LPN = {
        '01': {
            'nombre': 'No ingresada',
            'descripcion': 'La mercancía no está ingresada por parte del área de recibo',
            'severidad': 'ALTO',
            'accion': 'Revisar con área de recibo'
        },
        '10': {
            'nombre': 'Recibo no almacenado',
            'descripcion': 'Mercancía recibida y en inventario, necesita ser liberado por Gestión',
            'severidad': 'MEDIO',
            'accion': 'Solicitar liberación a Gestión'
        },
        '65': {
            'nombre': 'Pendiente por repartir',
            'descripcion': 'Mercancía en slot de recibo lista para ser preparada',
            'severidad': 'OK',
            'accion': 'Listo para preparación'
        },
        '90': {
            'nombre': 'En repartición',
            'descripcion': 'Mercancía en proceso de distribución, confirmada en tienda',
            'severidad': 'OK',
            'accion': 'En proceso normal'
        },
        '95': {
            'nombre': 'Consumido',
            'descripcion': 'Mercancía ya distribuida en tiendas - FIN',
            'severidad': 'OK',
            'accion': 'Proceso completado'
        },
        '30': {
            'nombre': 'En proceso',
            'descripcion': 'LPN en proceso de manejo',
            'severidad': 'OK',
            'accion': 'Monitorear progreso'
        },
        '80': {
            'nombre': 'Con problema',
            'descripcion': 'LPN con problema, requiere corrección',
            'severidad': 'CRITICO',
            'accion': 'Revisar y corregir inmediatamente'
        },
        '85': {
            'nombre': 'Corregido',
            'descripcion': 'Problema ya corregido',
            'severidad': 'OK',
            'accion': 'Continuar proceso'
        }
    }
    
    def __init__(self, almacen: str = '427'):
        self.almacen = almacen
    
    def consultar_lpn_inventario(
        self,
        db_connection,
        filtros: Dict = None
    ) -> pd.DataFrame:
        """
        Consulta LPN en inventario con múltiples filtros
        
        Filtros disponibles:
        - oc: Orden de compra
        - asn: ASN
        - lpn: LPN específico
        - estado: Estado del LPN
        - division: División
        - sku: SKU específico
        - fecha_recibo: Fecha de recibo
        - rango_fechas: Tupla (fecha_inicio, fecha_fin)
        """
        if filtros is None:
            filtros = {}
        
        query = """
        SELECT 
            IDPON AS OC,
            IDSHMT AS ASN,
            IDCASN AS LPN,
            IDSA1,
            IDSTOR AS TIENDA,
            IDSTYL AS SKU,
            CASE SUBSTR(STSTYD,1,1)
                WHEN '"' THEN SUBSTR(STSTYD,2,34)
                ELSE STSTYD 
            END AS DESC_SKU,
            IDIPQT AS IP,
            IDOQTY AS PZAS_ORIG,
            IDQTY AS PZAS_REST,
            INT(IDOQTY/IDIPQT) AS CJS_ORIG,
            REAL(IDQTY/IDIPQT) AS CJS_REALES,
            IDSTAT AS ESTADO,
            IDRQTP AS NEC_INM,
            IDDCR AS FCH_CREA,
            IDDLM AS FCH_ULT_MOD,
            IDRCDT AS FCHA_REC,
            IDTCR AS HR_CREA
        FROM WM260BASD.IDCASE00  
        INNER JOIN WM260BASD.STSTYL00 ON STSTYL = IDSTYL
        WHERE IDWHSE = ?
        """
        
        params = [self.almacen]
        
        # Aplicar filtros
        if filtros.get('division'):
            query += " AND IDDIV = ?"
            params.append(filtros['division'])
        
        if filtros.get('oc'):
            query += " AND IDPON IN (?)"
            params.append(filtros['oc'])
        
        if filtros.get('asn'):
            query += " AND IDSHMT IN (?)"
            params.append(filtros['asn'])
        
        if filtros.get('lpn'):
            query += " AND IDCASN IN (?)"
            params.append(filtros['lpn'])
        
        if filtros.get('estado'):
            if isinstance(filtros['estado'], list):
                placeholders = ','.join(['?'] * len(filtros['estado']))
                query += f" AND IDSTAT IN ({placeholders})"
                params.extend(filtros['estado'])
            else:
                query += " AND IDSTAT = ?"
                params.append(filtros['estado'])
        
        if filtros.get('sku'):
            query += " AND IDSTYL = ?"
            params.append(filtros['sku'])
        
        if filtros.get('fecha_recibo'):
            query += " AND IDRCDT = ?"
            params.append(filtros['fecha_recibo'])
        
        if filtros.get('rango_fechas'):
            fecha_inicio, fecha_fin = filtros['rango_fechas']
            query += " AND IDDCR BETWEEN ? AND ?"
            params.extend([fecha_inicio, fecha_fin])
        
        query += " ORDER BY IDPON ASC"
        
        logger.info(f"🔍 Consultando LPN en inventario - Almacén {self.almacen}")
        
        try:
            # Ejecutar consulta
            df = pd.read_sql(query, db_connection, params=params)
            logger.info(f"✅ Se encontraron {len(df)} LPN")
            return df
        except Exception as e:
            logger.error(f"❌ Error al consultar LPN: {str(e)}")
            return pd.DataFrame()
    
    def analizar_estado_lpn(self, estado: str) -> Dict:
        """Obtiene información detallada del estado de un LPN"""
        return self.ESTADOS_LPN.get(estado, {
            'nombre': 'Desconocido',
            'descripcion': 'Estado no documentado',
            'severidad': 'ALERTA',
            'accion': 'Consultar con soporte técnico'
        })
    
    def detectar_lpn_problematicos(self, df_lpn: pd.DataFrame) -> pd.DataFrame:
        """
        Detecta LPN con problemas o situaciones anómalas
        
        Detecta:
        - LPN en estado 10 por más de 24 horas
        - LPN en estado 01 (no ingresados)
        - LPN en estado 80 (con problema)
        - LPN sin Inner Pack
        - LPN con fechas antiguas sin movimiento
        """
        problemas = []
        
        for idx, row in df_lpn.iterrows():
            # Estado 01 - No ingresado
            if row['ESTADO'] == self.ESTADO_NO_INGRESADO:
                problemas.append({
                    'LPN': row['LPN'],
                    'OC': row['OC'],
                    'ASN': row['ASN'],
                    'SKU': row['SKU'],
                    'PROBLEMA': 'No ingresado',
                    'SEVERIDAD': 'ALTO',
                    'DESCRIPCION': 'Mercancía no ingresada por recibo',
                    'ACCION': 'Contactar área de recibo urgente'
                })
            
            # Estado 10 - Más de 24 horas
            if row['ESTADO'] == self.ESTADO_RECIBO_NO_ALMACENADO:
                try:
                    fecha_ult_mod = pd.to_datetime(row['FCH_ULT_MOD'], format='%Y%m%d')
                    dias_sin_movimiento = (datetime.now() - fecha_ult_mod).days
                    
                    if dias_sin_movimiento > 1:
                        problemas.append({
                            'LPN': row['LPN'],
                            'OC': row['OC'],
                            'ASN': row['ASN'],
                            'SKU': row['SKU'],
                            'PROBLEMA': f'Estado 10 hace {dias_sin_movimiento} días',
                            'SEVERIDAD': 'MEDIO',
                            'DESCRIPCION': 'LPN sin liberar por más de 24 horas',
                            'ACCION': 'Solicitar liberación urgente a Gestión'
                        })
                except (ValueError, TypeError) as e:
                    logger.warning(f"⚠️ No se pudo calcular días sin movimiento para LPN {row['LPN']}: {e}")

            # Estado 80 - Con problema
            if row['ESTADO'] == self.ESTADO_CON_PROBLEMA:
                problemas.append({
                    'LPN': row['LPN'],
                    'OC': row['OC'],
                    'ASN': row['ASN'],
                    'SKU': row['SKU'],
                    'PROBLEMA': 'Estado 80 - Con problema',
                    'SEVERIDAD': 'CRITICO',
                    'DESCRIPCION': 'LPN marcado con problema en sistema',
                    'ACCION': 'Revisar y corregir inmediatamente'
                })
            
            # Sin Inner Pack
            if pd.isna(row['IP']) or row['IP'] == 0:
                problemas.append({
                    'LPN': row['LPN'],
                    'OC': row['OC'],
                    'ASN': row['ASN'],
                    'SKU': row['SKU'],
                    'PROBLEMA': 'Sin Inner Pack',
                    'SEVERIDAD': 'MEDIO',
                    'DESCRIPCION': 'SKU sin IP definido',
                    'ACCION': 'Actualizar IP en maestro de productos'
                })
        
        return pd.DataFrame(problemas)
    
    def generar_reporte_seguimiento_lpn(
        self,
        df_lpn: pd.DataFrame,
        nombre_archivo: str = None
    ) -> str:
        """
        Genera reporte completo de seguimiento de LPN
        """
        if nombre_archivo is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            nombre_archivo = f"Seguimiento_LPN_{timestamp}.xlsx"
        
        logger.info(f"📊 Generando reporte de seguimiento de LPN")
        
        with pd.ExcelWriter(nombre_archivo, engine='openpyxl') as writer:
            # Hoja 1: Todos los LPN
            df_lpn.to_excel(writer, sheet_name='LPN Inventario', index=False)
            
            # Hoja 2: Resumen por estado
            resumen_estados = df_lpn.groupby('ESTADO').agg({
                'LPN': 'count',
                'PZAS_REST': 'sum',
                'CJS_REALES': 'sum'
            }).reset_index()
            resumen_estados.columns = ['Estado', 'Cantidad_LPN', 'Total_Piezas', 'Total_Cajas']
            
            # Agregar descripción de estados
            resumen_estados['Descripcion'] = resumen_estados['Estado'].apply(
                lambda x: self.analizar_estado_lpn(x)['nombre']
            )
            
            resumen_estados.to_excel(writer, sheet_name='Resumen por Estado', index=False)
            
            # Hoja 3: LPN Problemáticos
            df_problemas = self.detectar_lpn_problematicos(df_lpn)
            if not df_problemas.empty:
                df_problemas.to_excel(writer, sheet_name='LPN Problemáticos', index=False)
            
            # Hoja 4: Resumen por OC
            resumen_oc = df_lpn.groupby('OC').agg({
                'LPN': 'count',
                'ASN': 'nunique',
                'SKU': 'nunique',
                'PZAS_REST': 'sum'
            }).reset_index()
            resumen_oc.columns = ['OC', 'Cantidad_LPN', 'Total_ASN', 'Total_SKU', 'Total_Piezas']
            resumen_oc.to_excel(writer, sheet_name='Resumen por OC', index=False)
            
            # Hoja 5: Resumen por División (si aplica)
            if 'DIVISION' in df_lpn.columns:
                resumen_div = df_lpn.groupby('DIVISION').agg({
                    'LPN': 'count',
                    'PZAS_REST': 'sum'
                }).reset_index()
                resumen_div.to_excel(writer, sheet_name='Resumen por División', index=False)
        
        logger.info(f"✅ Reporte generado: {nombre_archivo}")
        return nombre_archivo
    
    def rastrear_movimientos_lpn(
        self,
        db_connection,
        lpn: str
    ) -> pd.DataFrame:
        """
        Obtiene el historial completo de movimientos de un LPN específico
        
        Muestra:
        - Cambios de estado
        - Movimientos de ubicación
        - Transiciones temporales
        - Usuario que realizó cada movimiento
        """
        query = """
        SELECT 
            FECHA,
            HORA,
            ESTADO_ANTERIOR,
            ESTADO_NUEVO,
            UBICACION,
            USUARIO,
            ACCION,
            DETALLES
        FROM WM260BASD.HISTORIAL_LPN
        WHERE LPN = ?
        ORDER BY FECHA DESC, HORA DESC
        """
        
        logger.info(f"📊 Rastreando movimientos del LPN: {lpn}")
        
        try:
            df = pd.read_sql(query, db_connection, params=[lpn])
            logger.info(f"✅ Se encontraron {len(df)} movimientos")
            return df
        except Exception as e:
            logger.error(f"❌ Error al rastrear movimientos: {str(e)}")
            return pd.DataFrame()
    
    def analizar_flujo_lpn(self, df_lpn: pd.DataFrame) -> Dict:
        """
        Analiza el flujo completo de LPN y detecta cuellos de botella
        """
        analisis = {
            'total_lpn': len(df_lpn),
            'por_estado': {},
            'tiempo_promedio_por_estado': {},
            'cuellos_de_botella': [],
            'recomendaciones': []
        }
        
        # Análisis por estado
        for estado in df_lpn['ESTADO'].unique():
            cantidad = len(df_lpn[df_lpn['ESTADO'] == estado])
            porcentaje = (cantidad / len(df_lpn)) * 100
            
            info_estado = self.analizar_estado_lpn(estado)
            
            analisis['por_estado'][estado] = {
                'cantidad': cantidad,
                'porcentaje': round(porcentaje, 2),
                'nombre': info_estado['nombre'],
                'severidad': info_estado['severidad']
            }
            
            # Detectar cuellos de botella
            if estado in ['10', '01'] and porcentaje > 30:
                analisis['cuellos_de_botella'].append({
                    'estado': estado,
                    'problema': f"{porcentaje}% de LPN en estado {info_estado['nombre']}",
                    'impacto': 'ALTO'
                })
        
        # Generar recomendaciones
        if analisis['cuellos_de_botella']:
            analisis['recomendaciones'].append(
                "Priorizar liberación de LPN en estado 10"
            )
            analisis['recomendaciones'].append(
                "Revisar proceso de ingreso con área de recibo"
            )
        
        return analisis


# ═══════════════════════════════════════════════════════════════
# FUNCIONES DE UTILIDAD
# ═══════════════════════════════════════════════════════════════

def obtener_lpn_por_estado(
    db_connection,
    estado: str,
    almacen: str = '427'
) -> pd.DataFrame:
    """
    Función rápida para obtener todos los LPN en un estado específico
    """
    analizador = AnalizadorLPN(almacen=almacen)
    return analizador.consultar_lpn_inventario(
        db_connection,
        filtros={'estado': estado}
    )


def analizar_lpn_oc(
    db_connection,
    oc: str,
    almacen: str = '427'
) -> Tuple[pd.DataFrame, Dict]:
    """
    Analiza todos los LPN de una OC específica
    """
    analizador = AnalizadorLPN(almacen=almacen)
    
    df_lpn = analizador.consultar_lpn_inventario(
        db_connection,
        filtros={'oc': oc}
    )
    
    analisis = analizador.analizar_flujo_lpn(df_lpn)
    
    return df_lpn, analisis


# ═══════════════════════════════════════════════════════════════
# EJEMPLO DE USO
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("""
    ═══════════════════════════════════════════════════════════════
    MÓDULO DE ANÁLISIS COMPLETO DE LPN
    Chedraui CEDIS - Sistema de Automatización
    ═══════════════════════════════════════════════════════════════
    
    Estados de LPN:
    • 01: No ingresada
    • 10: Recibo no almacenado
    • 65: Pendiente por repartir
    • 90: En repartición
    • 95: Consumido
    • 30: En proceso
    • 80: Con problema
    • 85: Corregido
    
    Funcionalidades:
    ✓ Consulta de LPN con filtros múltiples
    ✓ Análisis de estados
    ✓ Detección de problemas
    ✓ Seguimiento de movimientos
    ✓ Análisis de flujo
    ✓ Reportes completos
    
    ═══════════════════════════════════════════════════════════════
    """)
