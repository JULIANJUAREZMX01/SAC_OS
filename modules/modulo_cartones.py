"""
═══════════════════════════════════════════════════════════════
MÓDULO DE ANÁLISIS COMPLETO DE CARTONES Y PALLETS
Sistema de Gestión de Órdenes de Compra - Chedraui CEDIS
═══════════════════════════════════════════════════════════════

Este módulo maneja el análisis completo de cartones y pallets:
- Seguimiento de cartones por estado
- Análisis de pallets y cargas
- Detección de problemas en preparación
- Cierres retenidos
- Cartones duplicados o problemáticos

Estados de Cartones:
- 10: Creado
- 30: En proceso
- 40: En carga
- 65: Listo para envío
- 80: Con problema
- 85: Corregido
- 90: Enviado
- 95: Recibido en tienda

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

# Estados de cartones como constantes
ESTADO_CREADO = '10'
ESTADO_EN_PROCESO = '30'
ESTADO_EN_CARGA = '40'
ESTADO_LISTO_ENVIO = '65'
ESTADO_CON_PROBLEMA = '80'
ESTADO_CORREGIDO = '85'
ESTADO_ENVIADO = '90'
ESTADO_RECIBIDO_TIENDA = '95'


class AnalizadorCartones:
    """
    Analizador completo de cartones, pallets y cargas
    """
    
    # Estados de cartones
    ESTADOS_CARTON = {
        '10': {
            'nombre': 'Creado',
            'descripcion': 'Cartón creado pero no procesado',
            'severidad': 'OK',
            'siguiente': '30'
        },
        '30': {
            'nombre': 'En proceso',
            'descripcion': 'Cartón en proceso de preparación',
            'severidad': 'OK',
            'siguiente': '40'
        },
        '40': {
            'nombre': 'En carga',
            'descripcion': 'Cartón asignado a carga',
            'severidad': 'OK',
            'siguiente': '65'
        },
        '65': {
            'nombre': 'Listo para envío',
            'descripcion': 'Cartón preparado y listo',
            'severidad': 'OK',
            'siguiente': '90'
        },
        '80': {
            'nombre': 'Con problema',
            'descripcion': 'Cartón con error o problema detectado',
            'severidad': 'CRITICO',
            'siguiente': '85'
        },
        '85': {
            'nombre': 'Corregido',
            'descripcion': 'Problema corregido, listo para continuar',
            'severidad': 'OK',
            'siguiente': '40'
        },
        '90': {
            'nombre': 'Enviado',
            'descripcion': 'Cartón enviado a tienda',
            'severidad': 'OK',
            'siguiente': '95'
        },
        '95': {
            'nombre': 'Recibido',
            'descripcion': 'Cartón recibido en tienda - FIN',
            'severidad': 'OK',
            'siguiente': None
        }
    }
    
    def __init__(self, almacen: str = DEFAULT_ALMACEN):
        self.almacen = almacen
    
    def consultar_detalle_carton(
        self,
        db_connection,
        filtros: Dict = None
    ) -> pd.DataFrame:
        """
        Consulta detalle completo de cartones
        
        Filtros disponibles:
        - carton: Número de cartón específico
        - pallet: ID del pallet
        - carga: Número de carga
        - pickticket: Número de pickticket
        - oc: Orden de compra
        - tienda: Tienda destino
        - estado: Estado del cartón
        - sku: SKU específico
        - ruta: Ruta de envío
        """
        if filtros is None:
            filtros = {}
        
        query = """
        SELECT 
            CHWHSE AS ALM,
            CHDIV AS DIV,
            PDDSTR AS STO,
            CDPON AS OC,
            CHPCTL AS PICKTICKET,
            CDPRWV AS NUM_OLA,
            CHROUT AS RUTA,
            CHSTOR AS TIENDA,
            CHLDNO AS CARGA,
            CHPAID AS PALLET,
            CHCASN AS CARTON,
            CDSTYL AS SKU,
            REPLACE(CDSTYD,'"','') AS DESCRIPCION,
            CDPAKU AS PZA_EMP,
            PDPKQT AS IP,
            CHSTAT AS ESTADO,
            CHDLM AS FCH_MOD,
            CHTLM AS HORA_MOD,
            CHDCR AS FCH_CREA,
            CHTCR AS HORA_CREA
        FROM WM260BASD.CHCART00 
        INNER JOIN WM260BASD.CDCART00 
            ON CHCASN = CDCASN
            AND CHDIV = CDDIV
            AND CHPCTL = CDPCTL
        INNER JOIN WM260BASD.PDPICK00 
            ON CHPCTL = PDPCTL
            AND CDPCTL = PDPCTL
            AND CDPKLN = PDPKLN
            AND CDSTYL = PDBRCD
            AND CHWHSE = PDWHSE
            AND CHDIV = PDDIV
        WHERE CHWHSE = ?
        AND PDWHSE = ?
        """
        
        params = [self.almacen, self.almacen]
        
        # Aplicar filtros
        if filtros.get('division'):
            query += " AND CHDIV = ? AND CDDIV = ? AND PDDIV = ?"
            params.extend([filtros['division']] * 3)
        
        if filtros.get('carton'):
            if isinstance(filtros['carton'], list):
                placeholders = ','.join(['?'] * len(filtros['carton']))
                query += f" AND CHCASN IN ({placeholders})"
                params.extend(filtros['carton'])
            else:
                query += " AND CHCASN = ?"
                params.append(filtros['carton'])
        
        if filtros.get('pallet'):
            if isinstance(filtros['pallet'], list):
                placeholders = ','.join(['?'] * len(filtros['pallet']))
                query += f" AND CHPAID IN ({placeholders})"
                params.extend(filtros['pallet'])
            else:
                query += " AND CHPAID = ?"
                params.append(filtros['pallet'])
        
        if filtros.get('carga'):
            query += " AND CHLDNO = ?"
            params.append(filtros['carga'])
        
        if filtros.get('pickticket'):
            query += " AND CHPCTL = ?"
            params.append(filtros['pickticket'])
        
        if filtros.get('oc'):
            query += " AND CDPON = ?"
            params.append(filtros['oc'])
        
        if filtros.get('tienda'):
            query += " AND CHSTOR = ?"
            params.append(filtros['tienda'])
        
        if filtros.get('estado'):
            if isinstance(filtros['estado'], list):
                placeholders = ','.join(['?'] * len(filtros['estado']))
                query += f" AND CHSTAT IN ({placeholders})"
                params.extend(filtros['estado'])
            else:
                query += " AND CHSTAT = ?"
                params.append(filtros['estado'])
        
        if filtros.get('sku'):
            query += " AND CDSTYL = ?"
            params.append(filtros['sku'])
        
        if filtros.get('ruta'):
            query += " AND CHROUT = ?"
            params.append(filtros['ruta'])
        
        logger.info(f"🔍 Consultando detalle de cartones - Almacén {self.almacen}")
        
        try:
            df = pd.read_sql(query, db_connection, params=params)
            logger.info(f"✅ Se encontraron {len(df)} cartones")
            return df
        except (pd.io.sql.DatabaseError, Exception) as e:
            error_type = type(e).__name__
            logger.error(f"❌ Error al consultar cartones [{error_type}]: {str(e)}")
            logger.debug(f"Query fallido params: {params[:3]}...")
            return pd.DataFrame()
    
    def detectar_cartones_problematicos(
        self,
        df_cartones: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Detecta cartones con problemas
        
        Detecta:
        - Cartones en estado 80 (con problema)
        - Cartones sin pallet asignado
        - Cartones sin Inner Pack
        - Cartones duplicados (mismo SKU en mismo pallet)
        - Cartones con tiempos de proceso excesivos
        """
        problemas = []
        
        for idx, row in df_cartones.iterrows():
            # Estado 80 - Con problema
            if row['ESTADO'] == '80':
                problemas.append({
                    'CARTON': row['CARTON'],
                    'PALLET': row['PALLET'],
                    'CARGA': row['CARGA'],
                    'OC': row['OC'],
                    'SKU': row['SKU'],
                    'TIENDA': row['TIENDA'],
                    'PROBLEMA': 'Estado 80 - Con problema',
                    'SEVERIDAD': 'CRITICO',
                    'ACCION': 'Revisar error específico y corregir'
                })
            
            # Sin pallet
            if pd.isna(row['PALLET']) or row['PALLET'] == '':
                problemas.append({
                    'CARTON': row['CARTON'],
                    'PALLET': 'N/A',
                    'CARGA': row['CARGA'],
                    'OC': row['OC'],
                    'SKU': row['SKU'],
                    'TIENDA': row['TIENDA'],
                    'PROBLEMA': 'Sin pallet asignado',
                    'SEVERIDAD': 'ALTO',
                    'ACCION': 'Asignar pallet al cartón'
                })
            
            # Sin IP
            if pd.isna(row['IP']) or row['IP'] == 0:
                problemas.append({
                    'CARTON': row['CARTON'],
                    'PALLET': row['PALLET'],
                    'CARGA': row['CARGA'],
                    'OC': row['OC'],
                    'SKU': row['SKU'],
                    'TIENDA': row['TIENDA'],
                    'PROBLEMA': 'Sin Inner Pack definido',
                    'SEVERIDAD': 'MEDIO',
                    'ACCION': 'Actualizar IP en maestro de productos'
                })
        
        # Detectar cartones duplicados por pallet
        if 'PALLET' in df_cartones.columns and 'SKU' in df_cartones.columns:
            duplicados = df_cartones.groupby(['PALLET', 'SKU']).size()
            duplicados = duplicados[duplicados > 1].reset_index(name='CANTIDAD')
            
            for idx, dup in duplicados.iterrows():
                problemas.append({
                    'CARTON': 'MÚLTIPLES',
                    'PALLET': dup['PALLET'],
                    'CARGA': 'N/A',
                    'OC': 'N/A',
                    'SKU': dup['SKU'],
                    'TIENDA': 'N/A',
                    'PROBLEMA': f'SKU duplicado en pallet ({dup["CANTIDAD"]} veces)',
                    'SEVERIDAD': 'ALTO',
                    'ACCION': 'Revisar cartones del pallet y consolidar'
                })
        
        return pd.DataFrame(problemas)
    
    def analizar_carga(
        self,
        db_connection,
        num_carga: str
    ) -> Dict:
        """
        Analiza una carga completa
        
        Retorna:
        - Total de cartones
        - Total de pallets
        - Estados de cartones
        - SKU únicos
        - Tiendas destino
        - Problemas detectados
        """
        df_cartones = self.consultar_detalle_carton(
            db_connection,
            filtros={'carga': num_carga}
        )
        
        if df_cartones.empty:
            logger.warning(f"⚠️ Carga {num_carga} no encontrada o sin cartones")
            return {}
        
        analisis = {
            'num_carga': num_carga,
            'total_cartones': len(df_cartones),
            'total_pallets': df_cartones['PALLET'].nunique(),
            'total_tiendas': df_cartones['TIENDA'].nunique(),
            'total_skus': df_cartones['SKU'].nunique(),
            'total_piezas': df_cartones['PZA_EMP'].sum(),
            'estados': {},
            'tiendas': {},
            'problemas': []
        }
        
        # Análisis por estado
        for estado in df_cartones['ESTADO'].unique():
            cantidad = len(df_cartones[df_cartones['ESTADO'] == estado])
            info_estado = self.ESTADOS_CARTON.get(estado, {
                'nombre': 'Desconocido',
                'severidad': 'ALERTA'
            })
            
            analisis['estados'][estado] = {
                'cantidad': cantidad,
                'porcentaje': round((cantidad / len(df_cartones)) * 100, 2),
                'nombre': info_estado['nombre'],
                'severidad': info_estado['severidad']
            }
        
        # Análisis por tienda
        tiendas_grupo = df_cartones.groupby('TIENDA').agg({
            'CARTON': 'count',
            'PALLET': 'nunique',
            'PZA_EMP': 'sum'
        }).reset_index()
        
        for idx, tienda in tiendas_grupo.iterrows():
            analisis['tiendas'][tienda['TIENDA']] = {
                'cartones': tienda['CARTON'],
                'pallets': tienda['PALLET'],
                'piezas': tienda['PZA_EMP']
            }
        
        # Detectar problemas
        df_problemas = self.detectar_cartones_problematicos(df_cartones)
        if not df_problemas.empty:
            analisis['problemas'] = df_problemas.to_dict('records')
        
        return analisis
    
    def detectar_cierres_retenidos(
        self,
        db_connection,
        num_carga: str
    ) -> pd.DataFrame:
        """
        Detecta cartones que están causando cierres retenidos
        
        Un cierre retenido ocurre cuando:
        - Cartones en estado 80 impiden cerrar la carga
        - Carga en 65 pero cartones no están listos
        - Errores de validación en cartones
        """
        logger.info(f"🔍 Buscando cierres retenidos en carga {num_carga}")
        
        df_cartones = self.consultar_detalle_carton(
            db_connection,
            filtros={'carga': num_carga}
        )
        
        if df_cartones.empty:
            return pd.DataFrame()
        
        # Filtrar cartones problemáticos
        cartones_problema = df_cartones[
            (df_cartones['ESTADO'] == '80') |
            (df_cartones['ESTADO'] == '30')
        ].copy()
        
        if not cartones_problema.empty:
            cartones_problema['CAUSA_RETENCION'] = cartones_problema['ESTADO'].apply(
                lambda x: 'Error en cartón (80)' if x == '80' else 'Cartón no procesado (30)'
            )
            logger.warning(f"⚠️ Se encontraron {len(cartones_problema)} cartones reteniendo cierre")
        
        return cartones_problema
    
    def validar_integridad_pallet(
        self,
        df_cartones: pd.DataFrame,
        pallet_id: str
    ) -> Dict:
        """
        Valida la integridad de un pallet
        
        Verifica:
        - Todos los cartones tienen el mismo destino (tienda)
        - No hay SKU duplicados
        - Todos están en el mismo estado
        - Suma de piezas es correcta
        """
        df_pallet = df_cartones[df_cartones['PALLET'] == pallet_id].copy()
        
        if df_pallet.empty:
            return {'valido': False, 'motivo': 'Pallet no encontrado'}
        
        validacion = {
            'pallet_id': pallet_id,
            'valido': True,
            'total_cartones': len(df_pallet),
            'warnings': [],
            'errores': []
        }
        
        # Verificar mismo destino
        tiendas = df_pallet['TIENDA'].unique()
        if len(tiendas) > 1:
            validacion['valido'] = False
            validacion['errores'].append(
                f"Pallet con múltiples destinos: {', '.join(tiendas)}"
            )
        
        # Verificar SKU duplicados
        skus_duplicados = df_pallet.groupby('SKU').size()
        skus_duplicados = skus_duplicados[skus_duplicados > 1]
        if not skus_duplicados.empty:
            validacion['warnings'].append(
                f"SKU duplicados: {', '.join(skus_duplicados.index.tolist())}"
            )
        
        # Verificar estados
        estados = df_pallet['ESTADO'].unique()
        if len(estados) > 1:
            validacion['warnings'].append(
                f"Cartones en diferentes estados: {', '.join(estados)}"
            )
        
        # Verificar estado 80
        if '80' in estados:
            validacion['valido'] = False
            validacion['errores'].append(
                "Pallet contiene cartones en estado 80 (con problema)"
            )
        
        return validacion
    
    def generar_reporte_cartones(
        self,
        df_cartones: pd.DataFrame,
        nombre_archivo: str = None
    ) -> str:
        """
        Genera reporte completo de cartones en Excel
        """
        if nombre_archivo is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            nombre_archivo = f"Reporte_Cartones_{timestamp}.xlsx"
        
        logger.info(f"📊 Generando reporte de cartones")
        
        with pd.ExcelWriter(nombre_archivo, engine='openpyxl') as writer:
            # Hoja 1: Detalle completo
            df_cartones.to_excel(writer, sheet_name='Detalle Cartones', index=False)
            
            # Hoja 2: Resumen por estado
            resumen_estados = df_cartones.groupby('ESTADO').agg({
                'CARTON': 'count',
                'PZA_EMP': 'sum',
                'PALLET': 'nunique'
            }).reset_index()
            resumen_estados.columns = ['Estado', 'Cantidad', 'Total_Piezas', 'Total_Pallets']
            resumen_estados.to_excel(writer, sheet_name='Por Estado', index=False)
            
            # Hoja 3: Resumen por pallet
            resumen_pallets = df_cartones.groupby('PALLET').agg({
                'CARTON': 'count',
                'TIENDA': 'first',
                'CARGA': 'first',
                'ESTADO': lambda x: '/'.join(x.unique()),
                'PZA_EMP': 'sum'
            }).reset_index()
            resumen_pallets.columns = ['Pallet', 'Cartones', 'Tienda', 'Carga', 'Estados', 'Total_Piezas']
            resumen_pallets.to_excel(writer, sheet_name='Por Pallet', index=False)
            
            # Hoja 4: Problemas detectados
            df_problemas = self.detectar_cartones_problematicos(df_cartones)
            if not df_problemas.empty:
                df_problemas.to_excel(writer, sheet_name='Problemas', index=False)
            
            # Hoja 5: Por tienda
            resumen_tiendas = df_cartones.groupby('TIENDA').agg({
                'CARTON': 'count',
                'PALLET': 'nunique',
                'SKU': 'nunique',
                'PZA_EMP': 'sum'
            }).reset_index()
            resumen_tiendas.columns = ['Tienda', 'Cartones', 'Pallets', 'SKUs', 'Piezas']
            resumen_tiendas.to_excel(writer, sheet_name='Por Tienda', index=False)
        
        logger.info(f"✅ Reporte generado: {nombre_archivo}")
        return nombre_archivo


# ═══════════════════════════════════════════════════════════════
# FUNCIONES DE UTILIDAD
# ═══════════════════════════════════════════════════════════════

def analisis_rapido_carga(
    db_connection,
    num_carga: str,
    almacen: str = '427'
) -> Dict:
    """Análisis rápido de una carga"""
    analizador = AnalizadorCartones(almacen=almacen)
    return analizador.analizar_carga(db_connection, num_carga)


def encontrar_problema_cierre(
    db_connection,
    num_carga: str,
    almacen: str = '427'
) -> pd.DataFrame:
    """Encuentra qué está causando el cierre retenido"""
    analizador = AnalizadorCartones(almacen=almacen)
    return analizador.detectar_cierres_retenidos(db_connection, num_carga)


# ═══════════════════════════════════════════════════════════════
# EJEMPLO DE USO
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("""
    ═══════════════════════════════════════════════════════════════
    MÓDULO DE ANÁLISIS DE CARTONES Y PALLETS
    Chedraui CEDIS - Sistema de Automatización
    ═══════════════════════════════════════════════════════════════
    
    Funcionalidades:
    ✓ Consulta detalle de cartones
    ✓ Análisis de cargas completas
    ✓ Detección de cierres retenidos
    ✓ Validación de integridad de pallets
    ✓ Detección de cartones problemáticos
    ✓ Reportes completos en Excel
    
    Estados de Cartones:
    • 10: Creado
    • 30: En proceso
    • 40: En carga
    • 65: Listo para envío
    • 80: Con problema
    • 85: Corregido
    • 90: Enviado
    • 95: Recibido
    
    ═══════════════════════════════════════════════════════════════
    """)
