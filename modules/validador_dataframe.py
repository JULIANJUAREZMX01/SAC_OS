"""
═══════════════════════════════════════════════════════════════
VALIDADOR DE DATAFRAME ROBUSTO
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Módulo para validación de DataFrames con soporte para
null/NaN handling y validación de tipos de datos.

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
═══════════════════════════════════════════════════════════════
"""

import logging
import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Tuple, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class ErrorValidacionDataFrame(Exception):
    """Excepción base para errores de validación de DataFrame"""
    pass


@dataclass
class ResultadoValidacion:
    """Resultado de validación con detalles"""
    es_valido: bool
    errores: List[str]
    advertencias: List[str]
    info: List[str]

    def tiene_errores(self) -> bool:
        return len(self.errores) > 0

    def tiene_advertencias(self) -> bool:
        return len(self.advertencias) > 0

    def mostrar(self, titulo: str = "Validación DataFrame"):
        """Muestra reporte visual de validación"""
        print(f"\n{'='*70}")
        print(f"  {titulo}")
        print(f"{'='*70}\n")

        if self.errores:
            print("🔴 ERRORES:")
            for i, error in enumerate(self.errores, 1):
                print(f"  {i}. {error}")
            print()

        if self.advertencias:
            print("🟠 ADVERTENCIAS:")
            for i, adv in enumerate(self.advertencias, 1):
                print(f"  {i}. {adv}")
            print()

        if self.info:
            print("ℹ️  INFORMACIÓN:")
            for i, inf in enumerate(self.info, 1):
                print(f"  {i}. {inf}")
            print()

        estado = "❌ INVÁLIDO" if not self.es_valido else "✅ VÁLIDO"
        print(f"{estado} - {titulo}")
        print(f"{'='*70}\n")


class ValidadorDataFrame:
    """Validador de DataFrames con métodos específicos"""

    @staticmethod
    def validar_no_vacio(
        df: pd.DataFrame,
        nombre_df: str = "DataFrame"
    ) -> ResultadoValidacion:
        """
        Valida que DataFrame no esté vacío.

        Args:
            df: DataFrame a validar
            nombre_df: Nombre para logging

        Returns:
            ResultadoValidacion: Resultado de validación
        """
        resultado = ResultadoValidacion(es_valido=True, errores=[], advertencias=[], info=[])

        if df is None:
            resultado.es_valido = False
            resultado.errores.append(f"{nombre_df} es None")
            return resultado

        if not isinstance(df, pd.DataFrame):
            resultado.es_valido = False
            resultado.errores.append(
                f"{nombre_df} no es DataFrame, got {type(df).__name__}"
            )
            return resultado

        if df.empty:
            resultado.es_valido = False
            resultado.errores.append(f"{nombre_df} está vacío (0 filas)")
            return resultado

        resultado.info.append(f"{nombre_df} contiene {len(df)} filas")
        return resultado

    @staticmethod
    def validar_columnas(
        df: pd.DataFrame,
        columnas_requeridas: List[str],
        nombre_df: str = "DataFrame",
        columnas_opcionales: Optional[List[str]] = None
    ) -> ResultadoValidacion:
        """
        Valida que DataFrame contiene columnas requeridas.

        Args:
            df: DataFrame a validar
            columnas_requeridas: Lista de columnas que DEBEN existir
            nombre_df: Nombre para logging
            columnas_opcionales: Lista de columnas que PUEDEN existir

        Returns:
            ResultadoValidacion: Resultado de validación
        """
        resultado = ResultadoValidacion(es_valido=True, errores=[], advertencias=[], info=[])

        if df is None or not isinstance(df, pd.DataFrame):
            resultado.es_valido = False
            resultado.errores.append(f"{nombre_df} no es DataFrame válido")
            return resultado

        # Verificar columnas requeridas
        columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]
        if columnas_faltantes:
            resultado.es_valido = False
            resultado.errores.append(
                f"{nombre_df} falta columnas requeridas: {columnas_faltantes}"
            )

        # Verificar columnas opcionales
        if columnas_opcionales:
            columnas_opt_faltantes = [col for col in columnas_opcionales if col not in df.columns]
            if columnas_opt_faltantes:
                resultado.advertencias.append(
                    f"{nombre_df} falta columnas opcionales: {columnas_opt_faltantes}"
                )

        # Información de columnas presentes
        resultado.info.append(f"{nombre_df} tiene {len(df.columns)} columnas")
        resultado.info.append(f"Columnas: {', '.join(df.columns.tolist())}")

        return resultado

    @staticmethod
    def validar_tipos_datos(
        df: pd.DataFrame,
        esquema: Dict[str, type],
        nombre_df: str = "DataFrame",
        permitir_conversion: bool = True
    ) -> ResultadoValidacion:
        """
        Valida que tipos de datos coincidan con esquema esperado.

        Args:
            df: DataFrame a validar
            esquema: Diccionario {columna: tipo_esperado}
            nombre_df: Nombre para logging
            permitir_conversion: Si se permite intentar conversión de tipos

        Returns:
            ResultadoValidacion: Resultado de validación
        """
        resultado = ResultadoValidacion(es_valido=True, errores=[], advertencias=[], info=[])

        if df is None or not isinstance(df, pd.DataFrame):
            resultado.es_valido = False
            resultado.errores.append(f"{nombre_df} no es DataFrame válido")
            return resultado

        # Validar cada columna en esquema
        for columna, tipo_esperado in esquema.items():
            if columna not in df.columns:
                resultado.advertencias.append(f"Columna '{columna}' no encontrada en {nombre_df}")
                continue

            # Obtener tipo actual
            tipo_actual = df[columna].dtype

            # Mapping de tipos Python a pandas dtypes
            tipo_pandas = ValidadorDataFrame._mapear_tipo_pandas(tipo_esperado)

            # Verificar compatibilidad de tipos
            if not ValidadorDataFrame._tipos_compatibles(tipo_actual, tipo_pandas):
                if permitir_conversion:
                    try:
                        df[columna] = df[columna].astype(tipo_pandas)
                        resultado.advertencias.append(
                            f"Columna '{columna}': convertida de {tipo_actual} a {tipo_pandas}"
                        )
                    except Exception as e:
                        resultado.errores.append(
                            f"Columna '{columna}': no se puede convertir a {tipo_pandas} ({e})"
                        )
                        resultado.es_valido = False
                else:
                    resultado.errores.append(
                        f"Columna '{columna}': tipo {tipo_actual} no coincide con {tipo_pandas}"
                    )
                    resultado.es_valido = False
            else:
                resultado.info.append(f"Columna '{columna}': tipo {tipo_actual} ✓")

        return resultado

    @staticmethod
    def validar_null_nan(
        df: pd.DataFrame,
        nombre_df: str = "DataFrame",
        permitir_nulos: bool = False,
        max_nulos_por_columna: float = 0.5
    ) -> ResultadoValidacion:
        """
        Valida presencia de valores null/NaN.

        Args:
            df: DataFrame a validar
            nombre_df: Nombre para logging
            permitir_nulos: Si se permiten valores nulos
            max_nulos_por_columna: Porcentaje máximo de nulos permitidos (0.0-1.0)

        Returns:
            ResultadoValidacion: Resultado de validación
        """
        resultado = ResultadoValidacion(es_valido=True, errores=[], advertencias=[], info=[])

        if df is None or not isinstance(df, pd.DataFrame):
            resultado.es_valido = False
            resultado.errores.append(f"{nombre_df} no es DataFrame válido")
            return resultado

        # Contar nulos por columna
        nulos_por_columna = df.isnull().sum()
        total_filas = len(df)

        columnas_con_nulos = nulos_por_columna[nulos_por_columna > 0]

        if not columnas_con_nulos.empty:
            if not permitir_nulos:
                resultado.errores.append(
                    f"{nombre_df} contiene valores nulos no permitidos"
                )
                resultado.es_valido = False

            for columna, cantidad_nulos in columnas_con_nulos.items():
                porcentaje = (cantidad_nulos / total_filas) * 100

                if porcentaje > (max_nulos_por_columna * 100):
                    resultado.errores.append(
                        f"Columna '{columna}': {porcentaje:.1f}% nulos "
                        f"(máximo permitido: {max_nulos_por_columna*100:.1f}%)"
                    )
                    resultado.es_valido = False
                else:
                    resultado.advertencias.append(
                        f"Columna '{columna}': {cantidad_nulos} nulos ({porcentaje:.1f}%)"
                    )
        else:
            resultado.info.append(f"{nombre_df} sin valores nulos ✓")

        # Contar infinitos
        infinitos = 0
        try:
            infinitos = np.isinf(df.select_dtypes(include=[np.number])).sum().sum()
        except:
            pass

        if infinitos > 0:
            resultado.advertencias.append(f"{nombre_df} contiene {infinitos} valores infinitos")

        return resultado

    @staticmethod
    def validar_rango_valores(
        df: pd.DataFrame,
        columnas_rango: Dict[str, Tuple[Any, Any]],
        nombre_df: str = "DataFrame"
    ) -> ResultadoValidacion:
        """
        Valida que valores estén dentro de rango esperado.

        Args:
            df: DataFrame a validar
            columnas_rango: Diccionario {columna: (minimo, maximo)}
            nombre_df: Nombre para logging

        Returns:
            ResultadoValidacion: Resultado de validación
        """
        resultado = ResultadoValidacion(es_valido=True, errores=[], advertencias=[], info=[])

        if df is None or not isinstance(df, pd.DataFrame):
            resultado.es_valido = False
            resultado.errores.append(f"{nombre_df} no es DataFrame válido")
            return resultado

        for columna, (minimo, maximo) in columnas_rango.items():
            if columna not in df.columns:
                resultado.advertencias.append(f"Columna '{columna}' no encontrada")
                continue

            try:
                # Obtener valores no-nulos
                valores = df[columna].dropna()

                if valores.empty:
                    resultado.advertencias.append(f"Columna '{columna}' está toda nula")
                    continue

                # Validar rango
                fuera_rango = (valores < minimo) | (valores > maximo)

                if fuera_rango.any():
                    cantidad_fuera = fuera_rango.sum()
                    porcentaje = (cantidad_fuera / len(valores)) * 100

                    resultado.advertencias.append(
                        f"Columna '{columna}': {cantidad_fuera} valores fuera de rango "
                        f"[{minimo}, {maximo}] ({porcentaje:.1f}%)"
                    )
                    resultado.es_valido = False
                else:
                    resultado.info.append(
                        f"Columna '{columna}': todos los valores en rango [{minimo}, {maximo}] ✓"
                    )

            except Exception as e:
                resultado.advertencias.append(
                    f"No se pudo validar rango de '{columna}': {e}"
                )

        return resultado

    @staticmethod
    def validar_cardinality(
        df: pd.DataFrame,
        columna: str,
        min_unicos: Optional[int] = None,
        max_unicos: Optional[int] = None,
        nombre_df: str = "DataFrame"
    ) -> ResultadoValidacion:
        """
        Valida cantidad de valores únicos en columna.

        Args:
            df: DataFrame a validar
            columna: Columna a validar
            min_unicos: Mínimo de valores únicos
            max_unicos: Máximo de valores únicos
            nombre_df: Nombre para logging

        Returns:
            ResultadoValidacion: Resultado de validación
        """
        resultado = ResultadoValidacion(es_valido=True, errores=[], advertencias=[], info=[])

        if df is None or not isinstance(df, pd.DataFrame):
            resultado.es_valido = False
            resultado.errores.append(f"{nombre_df} no es DataFrame válido")
            return resultado

        if columna not in df.columns:
            resultado.errores.append(f"Columna '{columna}' no encontrada en {nombre_df}")
            resultado.es_valido = False
            return resultado

        unicos = df[columna].nunique(dropna=True)

        if min_unicos and unicos < min_unicos:
            resultado.errores.append(
                f"Columna '{columna}': {unicos} valores únicos, "
                f"mínimo esperado: {min_unicos}"
            )
            resultado.es_valido = False

        if max_unicos and unicos > max_unicos:
            resultado.advertencias.append(
                f"Columna '{columna}': {unicos} valores únicos, "
                f"máximo esperado: {max_unicos}"
            )

        resultado.info.append(f"Columna '{columna}': {unicos} valores únicos")

        return resultado

    @staticmethod
    def _mapear_tipo_pandas(tipo_python: type) -> Any:
        """Mapea tipo Python a tipo pandas"""
        mapping = {
            int: 'int64',
            float: 'float64',
            str: 'object',
            bool: 'bool',
            object: 'object',
        }
        return mapping.get(tipo_python, 'object')

    @staticmethod
    def _tipos_compatibles(tipo_actual: Any, tipo_esperado: Any) -> bool:
        """Verifica si tipos son compatibles"""
        conversiones_validas = {
            'int64': ['int32', 'int16', 'int8', 'uint64', 'uint32'],
            'float64': ['float32', 'int64'],
            'object': ['object', 'str'],
        }

        tipo_actual_str = str(tipo_actual)
        tipo_esperado_str = str(tipo_esperado)

        if tipo_actual_str == tipo_esperado_str:
            return True

        return tipo_actual_str in conversiones_validas.get(tipo_esperado_str, [])


def validar_dataframe_completo(
    df: pd.DataFrame,
    nombre_df: str = "DataFrame",
    columnas_requeridas: Optional[List[str]] = None,
    esquema: Optional[Dict[str, type]] = None,
    permitir_nulos: bool = False
) -> ResultadoValidacion:
    """
    Valida DataFrame completamente.

    Args:
        df: DataFrame a validar
        nombre_df: Nombre para logging
        columnas_requeridas: Columnas que deben existir
        esquema: Esquema de tipos esperados
        permitir_nulos: Si se permiten valores nulos

    Returns:
        ResultadoValidacion: Resultado consolidado
    """
    # Validación no-vacío
    resultado = ValidadorDataFrame.validar_no_vacio(df, nombre_df)
    if not resultado.es_valido:
        return resultado

    # Validación de columnas
    if columnas_requeridas:
        resultado_cols = ValidadorDataFrame.validar_columnas(
            df, columnas_requeridas, nombre_df
        )
        resultado.errores.extend(resultado_cols.errores)
        resultado.advertencias.extend(resultado_cols.advertencias)
        resultado.info.extend(resultado_cols.info)
        resultado.es_valido = resultado.es_valido and resultado_cols.es_valido

    # Validación de tipos
    if esquema:
        resultado_tipos = ValidadorDataFrame.validar_tipos_datos(
            df, esquema, nombre_df
        )
        resultado.errores.extend(resultado_tipos.errores)
        resultado.advertencias.extend(resultado_tipos.advertencias)
        resultado.info.extend(resultado_tipos.info)
        resultado.es_valido = resultado.es_valido and resultado_tipos.es_valido

    # Validación null/NaN
    resultado_nulos = ValidadorDataFrame.validar_null_nan(
        df, nombre_df, permitir_nulos
    )
    resultado.errores.extend(resultado_nulos.errores)
    resultado.advertencias.extend(resultado_nulos.advertencias)
    resultado.info.extend(resultado_nulos.info)
    resultado.es_valido = resultado.es_valido and resultado_nulos.es_valido

    return resultado
