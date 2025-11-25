"""
═══════════════════════════════════════════════════════════════════════════════
SACYTY - Núcleo del Sistema Ligero
Sistema de Automatización Chedraui - Modelo TinY
═══════════════════════════════════════════════════════════════════════════════

Núcleo principal de SACYTY que proporciona:
- Conexión básica a DB2
- Ejecución de queries
- Validación de datos
- Reportes básicos

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
═══════════════════════════════════════════════════════════════════════════════
"""

import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

from .sacyty_config import SACYTYConfig, get_config
from .sacyty_validator import SACYTYValidator, ValidationResult, Severity

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# CLASE PRINCIPAL SACYTY
# ═══════════════════════════════════════════════════════════════════════════════

class SACYTYCore:
    """
    Núcleo del sistema SACYTY - Modelo ligero para dispositivos.

    Características:
    - Conexión básica a DB2
    - Validaciones esenciales
    - Sin dependencias pesadas (GUI, animaciones, etc.)
    - Optimizado para recursos limitados
    """

    def __init__(self, config: Optional[SACYTYConfig] = None):
        """
        Inicializar SACYTY Core.

        Args:
            config: Configuración personalizada (opcional)
        """
        self.config = config or get_config()
        self.validator = SACYTYValidator()
        self.connection = None
        self._is_initialized = False
        self.logger = logging.getLogger(f"{__name__}.SACYTYCore")

        # Intentar importar pandas (opcional)
        try:
            import pandas as pd
            self._has_pandas = True
            self._pd = pd
        except ImportError:
            self._has_pandas = False
            self._pd = None
            self.logger.warning("pandas no disponible - funcionalidad reducida")

    # ═══════════════════════════════════════════════════════════════════════════
    # INICIALIZACIÓN
    # ═══════════════════════════════════════════════════════════════════════════

    def initialize(self) -> Tuple[bool, List[str]]:
        """
        Inicializar el sistema SACYTY.

        Returns:
            Tuple[bool, List[str]]: (éxito, lista de mensajes/errores)
        """
        messages = []

        try:
            # 1. Validar configuración
            is_valid, errors = self.config.validate()
            if not is_valid:
                messages.extend([f"Config Error: {e}" for e in errors])
                return False, messages

            messages.append("Configuración validada correctamente")

            # 2. Validar sistema
            system_result = self.validator.validate_system()
            if not system_result.is_valid:
                messages.extend([f"System Error: {e.message}" for e in system_result.errors])
                return False, messages

            messages.append("Sistema validado correctamente")

            # 3. Intentar conexión a DB2 (opcional)
            if self.config.database.is_configured():
                conn_success, conn_msg = self._connect_db()
                messages.append(conn_msg)
                if not conn_success:
                    messages.append("ADVERTENCIA: Continuando sin conexión a DB2")
            else:
                messages.append("Base de datos no configurada - modo offline")

            self._is_initialized = True
            messages.append("SACYTY inicializado correctamente")
            return True, messages

        except Exception as e:
            messages.append(f"Error inicializando SACYTY: {str(e)}")
            return False, messages

    def _connect_db(self) -> Tuple[bool, str]:
        """
        Conectar a base de datos DB2.

        Returns:
            Tuple[bool, str]: (éxito, mensaje)
        """
        try:
            # Intentar con pyodbc primero (Windows)
            try:
                import pyodbc
                conn_string = self.config.database.get_connection_string()
                self.connection = pyodbc.connect(conn_string, timeout=self.config.database.timeout)
                return True, "Conexión DB2 establecida (pyodbc)"
            except ImportError:
                pass

            # Intentar con ibm_db (Linux/Mac)
            try:
                import ibm_db
                conn_string = (
                    f"DATABASE={self.config.database.database};"
                    f"HOSTNAME={self.config.database.host};"
                    f"PORT={self.config.database.port};"
                    f"PROTOCOL=TCPIP;"
                    f"UID={self.config.database.user};"
                    f"PWD={self.config.database.password};"
                )
                self.connection = ibm_db.connect(conn_string, "", "")
                return True, "Conexión DB2 establecida (ibm_db)"
            except ImportError:
                pass

            return False, "No hay driver DB2 disponible (pyodbc/ibm_db)"

        except Exception as e:
            return False, f"Error conectando a DB2: {str(e)}"

    # ═══════════════════════════════════════════════════════════════════════════
    # EJECUCIÓN DE QUERIES
    # ═══════════════════════════════════════════════════════════════════════════

    def execute_query(self, query: str, params: Optional[Dict] = None) -> Tuple[bool, Any]:
        """
        Ejecutar query SQL.

        Args:
            query: Query SQL a ejecutar
            params: Parámetros opcionales para la query

        Returns:
            Tuple[bool, Any]: (éxito, resultado o error)
        """
        if not self.connection:
            return False, "No hay conexión a base de datos"

        try:
            start_time = datetime.now()

            # Ejecutar según el driver
            if hasattr(self.connection, 'cursor'):
                # pyodbc style
                cursor = self.connection.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)

                # Obtener resultados
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                rows = cursor.fetchall()
                cursor.close()

                # Convertir a DataFrame si pandas disponible
                if self._has_pandas and columns:
                    result = self._pd.DataFrame.from_records(rows, columns=columns)
                else:
                    result = {'columns': columns, 'rows': [list(row) for row in rows]}

            else:
                # ibm_db style
                import ibm_db
                stmt = ibm_db.exec_immediate(self.connection, query)

                columns = []
                rows = []
                row = ibm_db.fetch_assoc(stmt)
                if row:
                    columns = list(row.keys())
                    while row:
                        rows.append(row)
                        row = ibm_db.fetch_assoc(stmt)

                if self._has_pandas and columns:
                    result = self._pd.DataFrame(rows)
                else:
                    result = {'columns': columns, 'rows': rows}

            duration = (datetime.now() - start_time).total_seconds()
            self.logger.info(f"Query ejecutada en {duration:.2f}s")

            return True, result

        except Exception as e:
            self.logger.error(f"Error ejecutando query: {str(e)}")
            return False, str(e)

    def load_query_from_file(self, query_file: str) -> Optional[str]:
        """
        Cargar query desde archivo SQL.

        Args:
            query_file: Nombre del archivo de query

        Returns:
            Contenido de la query o None
        """
        # Buscar en diferentes ubicaciones
        search_paths = [
            self.config.paths.queries / "obligatorias" / query_file,
            self.config.paths.queries / "preventivas" / query_file,
            self.config.paths.queries / "bajo_demanda" / query_file,
            self.config.paths.queries / query_file,
        ]

        for path in search_paths:
            if path.exists():
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        return f.read()
                except Exception as e:
                    self.logger.error(f"Error leyendo {path}: {e}")

        self.logger.warning(f"Query no encontrada: {query_file}")
        return None

    # ═══════════════════════════════════════════════════════════════════════════
    # VALIDACIONES
    # ═══════════════════════════════════════════════════════════════════════════

    def validate_oc(self, oc_number: str) -> ValidationResult:
        """
        Validar una orden de compra.

        Args:
            oc_number: Número de OC

        Returns:
            ValidationResult con resultado de validación
        """
        # Validar formato
        format_result = self.validator.validate_oc_number(oc_number)

        if not format_result.is_valid:
            return format_result

        # Si hay conexión, validar en BD
        if self.connection:
            # Aquí se ejecutaría la query real
            # Por ahora solo validamos formato
            pass

        return format_result

    def run_health_check(self) -> Dict[str, Any]:
        """
        Ejecutar verificación de salud del sistema.

        Returns:
            Dict con estado del sistema
        """
        results = self.validator.run_all_validations(
            config=self.config,
            connection=self.connection
        )

        summary = self.validator.get_summary(results)
        summary['timestamp'] = datetime.now().isoformat()
        summary['version'] = self.config.version
        summary['cedis'] = {
            'code': self.config.cedis.code,
            'name': self.config.cedis.name
        }

        return summary

    # ═══════════════════════════════════════════════════════════════════════════
    # REPORTES BÁSICOS
    # ═══════════════════════════════════════════════════════════════════════════

    def generate_status_report(self) -> str:
        """
        Generar reporte de estado en formato texto.

        Returns:
            Reporte en formato texto
        """
        health = self.run_health_check()

        report = f"""
╔══════════════════════════════════════════════════════════════╗
║                SACYTY - Reporte de Estado                   ║
╠══════════════════════════════════════════════════════════════╣
║  Versión: {self.config.version:<48} ║
║  CEDIS: {self.config.cedis.code} - {self.config.cedis.name:<40} ║
║  Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S'):<48} ║
╠══════════════════════════════════════════════════════════════╣
║  ESTADO DEL SISTEMA                                          ║
╠══════════════════════════════════════════════════════════════╣
║  Estado General: {'OK' if health['all_passed'] else 'ERROR':<44} ║
║  Validaciones: {health['total_validations']:<46} ║
║  Errores: {health['total_errors']:<50} ║
║  Advertencias: {health['total_warnings']:<45} ║
╠══════════════════════════════════════════════════════════════╣
║  DETALLE DE VALIDACIONES                                     ║
╠══════════════════════════════════════════════════════════════╣"""

        for name, val in health['validations'].items():
            status = 'OK' if val['is_valid'] else 'ERROR'
            report += f"\n║  {name:<20}: {status:<8} (E:{val['errors']} W:{val['warnings']}){'':>12} ║"

        report += """
╚══════════════════════════════════════════════════════════════╝
"""
        return report

    def export_health_report(self, output_path: Optional[Path] = None) -> str:
        """
        Exportar reporte de salud a archivo JSON.

        Args:
            output_path: Ruta de salida (opcional)

        Returns:
            Ruta del archivo generado
        """
        health = self.run_health_check()

        if output_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = self.config.paths.output / f"sacyty_health_{timestamp}.json"

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(health, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Reporte exportado: {output_path}")
            return str(output_path)

        except Exception as e:
            self.logger.error(f"Error exportando reporte: {e}")
            return ""

    # ═══════════════════════════════════════════════════════════════════════════
    # UTILIDADES
    # ═══════════════════════════════════════════════════════════════════════════

    def get_status(self) -> Dict[str, Any]:
        """
        Obtener estado actual del sistema.

        Returns:
            Dict con estado
        """
        return {
            'initialized': self._is_initialized,
            'version': self.config.version,
            'cedis': self.config.cedis.code,
            'database_connected': self.connection is not None,
            'pandas_available': self._has_pandas,
            'timestamp': datetime.now().isoformat()
        }

    def close(self) -> None:
        """Cerrar conexiones y liberar recursos"""
        if self.connection:
            try:
                if hasattr(self.connection, 'close'):
                    self.connection.close()
                self.connection = None
                self.logger.info("Conexión DB2 cerrada")
            except Exception as e:
                self.logger.error(f"Error cerrando conexión: {e}")

        self._is_initialized = False

    def __enter__(self):
        """Context manager entry"""
        self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIONES DE CONVENIENCIA
# ═══════════════════════════════════════════════════════════════════════════════

def create_sacyty(config: Optional[SACYTYConfig] = None) -> SACYTYCore:
    """
    Crear instancia de SACYTY.

    Args:
        config: Configuración opcional

    Returns:
        Instancia de SACYTYCore
    """
    return SACYTYCore(config)


def quick_health_check() -> Dict[str, Any]:
    """
    Ejecutar verificación rápida de salud.

    Returns:
        Dict con estado del sistema
    """
    with SACYTYCore() as sacyty:
        return sacyty.run_health_check()


# ═══════════════════════════════════════════════════════════════════════════════
# EJECUCIÓN DIRECTA
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("SACYTY - Sistema Ligero - Prueba del Core")
    print("=" * 60)

    # Crear instancia
    sacyty = SACYTYCore()

    # Inicializar
    print("\n1. Inicializando SACYTY...")
    success, messages = sacyty.initialize()
    for msg in messages:
        print(f"   {msg}")

    # Obtener estado
    print("\n2. Estado del sistema:")
    status = sacyty.get_status()
    for key, value in status.items():
        print(f"   {key}: {value}")

    # Generar reporte
    print("\n3. Reporte de estado:")
    print(sacyty.generate_status_report())

    # Cerrar
    sacyty.close()
    print("SACYTY finalizado correctamente")
