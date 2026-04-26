"""
═══════════════════════════════════════════════════════════════════════════════
SACYTY - Validador Ligero
Sistema de Automatización Chedraui - Modelo TinY
═══════════════════════════════════════════════════════════════════════════════

Validador esencial para verificación de:
- Conexión a base de datos
- Estructura de datos
- OC y distribuciones
- Estado del sistema

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
═══════════════════════════════════════════════════════════════════════════════
"""

import re
import logging
from enum import Enum
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# ENUMERACIONES
# ═══════════════════════════════════════════════════════════════════════════════

class Severity(Enum):
    """Niveles de severidad de errores"""
    CRITICAL = ("CRITICO", "red", 1)
    HIGH = ("ALTO", "orange", 2)
    MEDIUM = ("MEDIO", "yellow", 3)
    LOW = ("BAJO", "green", 4)
    INFO = ("INFO", "blue", 5)

    def __init__(self, label: str, color: str, priority: int):
        self.label = label
        self.color = color
        self.priority = priority

    def __str__(self) -> str:
        return self.label


class ValidationStatus(Enum):
    """Estados de validación"""
    PASSED = "OK"
    FAILED = "ERROR"
    WARNING = "ADVERTENCIA"
    SKIPPED = "OMITIDO"
    PENDING = "PENDIENTE"


# ═══════════════════════════════════════════════════════════════════════════════
# DATACLASSES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ValidationError:
    """Representa un error de validación"""
    code: str
    message: str
    severity: Severity
    details: str = ""
    solution: str = ""
    module: str = "SACYTY"
    timestamp: datetime = field(default_factory=datetime.now)
    affected_data: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return {
            'code': self.code,
            'message': self.message,
            'severity': self.severity.label,
            'details': self.details,
            'solution': self.solution,
            'module': self.module,
            'timestamp': self.timestamp.isoformat(),
            'affected_data': self.affected_data
        }

    def __str__(self) -> str:
        return f"[{self.severity}] {self.code}: {self.message}"


@dataclass
class ValidationResult:
    """Resultado de una validación"""
    name: str
    status: ValidationStatus
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)
    info: List[str] = field(default_factory=list)
    duration_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def is_valid(self) -> bool:
        """Verificar si la validación pasó sin errores críticos"""
        critical_errors = [e for e in self.errors if e.severity == Severity.CRITICAL]
        return len(critical_errors) == 0 and self.status != ValidationStatus.FAILED

    @property
    def has_warnings(self) -> bool:
        """Verificar si hay advertencias"""
        return len(self.warnings) > 0

    @property
    def error_count(self) -> int:
        """Contar errores"""
        return len(self.errors)

    @property
    def warning_count(self) -> int:
        """Contar advertencias"""
        return len(self.warnings)

    def add_error(self, error: ValidationError) -> None:
        """Agregar error"""
        self.errors.append(error)
        if self.status == ValidationStatus.PASSED:
            self.status = ValidationStatus.FAILED

    def add_warning(self, warning: ValidationError) -> None:
        """Agregar advertencia"""
        self.warnings.append(warning)
        if self.status == ValidationStatus.PASSED:
            self.status = ValidationStatus.WARNING

    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return {
            'name': self.name,
            'status': self.status.value,
            'is_valid': self.is_valid,
            'error_count': self.error_count,
            'warning_count': self.warning_count,
            'errors': [e.to_dict() for e in self.errors],
            'warnings': [w.to_dict() for w in self.warnings],
            'info': self.info,
            'duration_ms': self.duration_ms,
            'timestamp': self.timestamp.isoformat()
        }


# ═══════════════════════════════════════════════════════════════════════════════
# PATRONES DE VALIDACIÓN
# ═══════════════════════════════════════════════════════════════════════════════

class Patterns:
    """Patrones de validación para datos de Manhattan WMS"""

    # Órdenes de Compra
    OC_CHEDRAUI = re.compile(r'^750384\d{6}$')
    OC_IMPORTACION = re.compile(r'^811117\d{6}$')
    OC_GENERAL = re.compile(r'^40[0-9]{11}$')
    OC_WITH_PREFIX = re.compile(r'^C\d{12,15}$')

    # LPN y ASN
    LPN = re.compile(r'^LPN[0-9]{7,10}$')
    ASN = re.compile(r'^ASN[0-9]{8,12}$')

    # SKU
    SKU = re.compile(r'^[A-Z0-9]{6,15}$')

    # Ubicaciones
    LOCATION = re.compile(r'^[A-Z][0-9]{2}[A-Z][0-9]{3}[A-Z0-9]{2}$')

    @classmethod
    def validate_oc(cls, oc: str) -> bool:
        """Validar formato de OC"""
        if not oc:
            return False
        return bool(
            cls.OC_CHEDRAUI.match(oc) or
            cls.OC_IMPORTACION.match(oc) or
            cls.OC_GENERAL.match(oc) or
            cls.OC_WITH_PREFIX.match(oc)
        )

    @classmethod
    def validate_lpn(cls, lpn: str) -> bool:
        """Validar formato de LPN"""
        return bool(lpn and cls.LPN.match(lpn))

    @classmethod
    def validate_asn(cls, asn: str) -> bool:
        """Validar formato de ASN"""
        return bool(asn and cls.ASN.match(asn))

    @classmethod
    def validate_sku(cls, sku: str) -> bool:
        """Validar formato de SKU"""
        return bool(sku and cls.SKU.match(sku))


# ═══════════════════════════════════════════════════════════════════════════════
# VALIDADOR PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

class SACYTYValidator:
    """
    Validador ligero para SACYTY.
    Implementa validaciones esenciales sin dependencias pesadas.
    """

    def __init__(self):
        """Inicializar validador"""
        self.logger = logging.getLogger(f"{__name__}.SACYTYValidator")

    # ═══════════════════════════════════════════════════════════════════════════
    # VALIDACIONES DE SISTEMA
    # ═══════════════════════════════════════════════════════════════════════════

    def validate_system(self) -> ValidationResult:
        """
        Validar estado del sistema.

        Returns:
            ValidationResult con estado del sistema
        """
        start_time = datetime.now()
        result = ValidationResult(name="Sistema SACYTY", status=ValidationStatus.PASSED)

        try:
            # Validar Python
            import sys
            if sys.version_info < (3, 8):
                result.add_warning(ValidationError(
                    code="PYTHON_VERSION",
                    message=f"Python {sys.version_info.major}.{sys.version_info.minor} detectado",
                    severity=Severity.MEDIUM,
                    details="Se recomienda Python 3.8 o superior",
                    solution="Actualizar Python a versión 3.8+"
                ))
            else:
                result.info.append(f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

            # Validar módulos esenciales
            essential_modules = ['json', 'logging', 'pathlib', 'datetime', 're']
            for module in essential_modules:
                try:
                    __import__(module)
                except ImportError:
                    result.add_error(ValidationError(
                        code="MISSING_MODULE",
                        message=f"Módulo esencial '{module}' no disponible",
                        severity=Severity.CRITICAL,
                        solution="Reinstalar Python estándar"
                    ))

            # Validar módulos opcionales
            optional_modules = ['pandas', 'openpyxl']
            for module in optional_modules:
                try:
                    __import__(module)
                    result.info.append(f"Módulo {module} disponible")
                except ImportError:
                    result.add_warning(ValidationError(
                        code="OPTIONAL_MODULE",
                        message=f"Módulo '{module}' no instalado",
                        severity=Severity.LOW,
                        details="Funcionalidad reducida sin este módulo",
                        solution=f"pip install {module}"
                    ))

        except Exception as e:
            result.add_error(ValidationError(
                code="SYSTEM_ERROR",
                message=f"Error validando sistema: {str(e)}",
                severity=Severity.HIGH
            ))

        result.duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        return result

    def validate_config(self, config: Any) -> ValidationResult:
        """
        Validar configuración SACYTY.

        Args:
            config: Instancia de SACYTYConfig

        Returns:
            ValidationResult con estado de configuración
        """
        start_time = datetime.now()
        result = ValidationResult(name="Configuración", status=ValidationStatus.PASSED)

        try:
            # Validar configuración de base de datos
            if not config.database.is_configured():
                result.add_error(ValidationError(
                    code="DB_NOT_CONFIGURED",
                    message="Credenciales de base de datos no configuradas",
                    severity=Severity.CRITICAL,
                    details="DB_USER y DB_PASSWORD son requeridos",
                    solution="Configurar variables en archivo .env"
                ))
            else:
                result.info.append("Base de datos configurada")

            # Validar host de base de datos
            if not config.database.host:
                result.add_error(ValidationError(
                    code="DB_HOST_MISSING",
                    message="Host de base de datos no especificado",
                    severity=Severity.CRITICAL,
                    solution="Configurar DB_HOST en .env"
                ))

            # Validar CEDIS
            if not config.cedis.code:
                result.add_warning(ValidationError(
                    code="CEDIS_NOT_SET",
                    message="Código de CEDIS no configurado",
                    severity=Severity.MEDIUM,
                    solution="Configurar CEDIS_CODE en .env"
                ))
            else:
                result.info.append(f"CEDIS: {config.cedis.code} - {config.cedis.name}")

            # Validar rutas
            if not config.paths.base.exists():
                result.add_error(ValidationError(
                    code="PATH_NOT_EXISTS",
                    message=f"Ruta base no existe: {config.paths.base}",
                    severity=Severity.HIGH,
                    solution="Verificar instalación del sistema"
                ))

            # Validar email (opcional)
            if not config.email.is_configured():
                result.add_warning(ValidationError(
                    code="EMAIL_NOT_CONFIGURED",
                    message="Email no configurado",
                    severity=Severity.LOW,
                    details="Notificaciones por email deshabilitadas",
                    solution="Configurar EMAIL_USER y EMAIL_PASSWORD en .env"
                ))

        except Exception as e:
            result.add_error(ValidationError(
                code="CONFIG_ERROR",
                message=f"Error validando configuración: {str(e)}",
                severity=Severity.HIGH
            ))

        result.duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        return result

    # ═══════════════════════════════════════════════════════════════════════════
    # VALIDACIONES DE CONEXIÓN
    # ═══════════════════════════════════════════════════════════════════════════

    def validate_db_connection(self, connection: Any) -> ValidationResult:
        """
        Validar conexión a base de datos.

        Args:
            connection: Objeto de conexión a DB2

        Returns:
            ValidationResult con estado de conexión
        """
        start_time = datetime.now()
        result = ValidationResult(name="Conexión DB2", status=ValidationStatus.PASSED)

        try:
            if connection is None:
                result.add_error(ValidationError(
                    code="NO_CONNECTION",
                    message="No hay conexión a base de datos",
                    severity=Severity.CRITICAL,
                    solution="Verificar credenciales y conectividad de red"
                ))
                return result

            # Intentar ejecutar query simple
            try:
                # Esto depende del driver usado
                if hasattr(connection, 'cursor'):
                    cursor = connection.cursor()
                    cursor.execute("SELECT 1 FROM SYSIBM.SYSDUMMY1")
                    cursor.close()
                    result.info.append("Conexión DB2 activa")
                else:
                    result.info.append("Conexión disponible (no verificada)")
            except Exception as e:
                result.add_error(ValidationError(
                    code="DB_QUERY_FAILED",
                    message="Error ejecutando query de prueba",
                    severity=Severity.HIGH,
                    details=str(e),
                    solution="Verificar permisos de usuario en DB2"
                ))

        except Exception as e:
            result.add_error(ValidationError(
                code="CONNECTION_ERROR",
                message=f"Error validando conexión: {str(e)}",
                severity=Severity.CRITICAL
            ))

        result.duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        return result

    # ═══════════════════════════════════════════════════════════════════════════
    # VALIDACIONES DE DATOS
    # ═══════════════════════════════════════════════════════════════════════════

    def validate_oc_number(self, oc: str) -> ValidationResult:
        """
        Validar formato de número de OC.

        Args:
            oc: Número de orden de compra

        Returns:
            ValidationResult con resultado de validación
        """
        result = ValidationResult(name=f"OC {oc}", status=ValidationStatus.PASSED)

        if not oc:
            result.add_error(ValidationError(
                code="OC_EMPTY",
                message="Número de OC vacío",
                severity=Severity.HIGH
            ))
            return result

        # Limpiar OC
        oc_clean = oc.strip().upper()

        # Validar formato
        if not Patterns.validate_oc(oc_clean):
            result.add_warning(ValidationError(
                code="OC_FORMAT",
                message=f"Formato de OC '{oc}' no estándar",
                severity=Severity.MEDIUM,
                details="Formatos esperados: 750384XXXXXX, 811117XXXXXX, 40XXXXXXXXXXX, CXXXXXXXXXXXX",
                solution="Verificar número de OC en Manhattan"
            ))
        else:
            result.info.append(f"Formato de OC válido: {oc_clean}")

        return result

    def validate_dataframe(self, df: Any, required_columns: List[str],
                           name: str = "DataFrame") -> ValidationResult:
        """
        Validar estructura de DataFrame.

        Args:
            df: pandas DataFrame a validar
            required_columns: Lista de columnas requeridas
            name: Nombre descriptivo

        Returns:
            ValidationResult con resultado de validación
        """
        start_time = datetime.now()
        result = ValidationResult(name=name, status=ValidationStatus.PASSED)

        try:
            # Verificar si es DataFrame
            if df is None:
                result.add_error(ValidationError(
                    code="DF_NULL",
                    message="DataFrame es None",
                    severity=Severity.HIGH
                ))
                return result

            # Verificar si tiene el atributo columns (es DataFrame-like)
            if not hasattr(df, 'columns'):
                result.add_error(ValidationError(
                    code="NOT_DATAFRAME",
                    message="Objeto no es un DataFrame válido",
                    severity=Severity.HIGH
                ))
                return result

            # Verificar columnas requeridas
            df_columns = [str(c).upper() for c in df.columns]
            missing_columns = []

            for col in required_columns:
                if col.upper() not in df_columns:
                    missing_columns.append(col)

            if missing_columns:
                result.add_error(ValidationError(
                    code="MISSING_COLUMNS",
                    message=f"Columnas faltantes: {', '.join(missing_columns)}",
                    severity=Severity.HIGH,
                    details=f"Columnas disponibles: {', '.join(df.columns[:10])}...",
                    affected_data={'missing': missing_columns}
                ))

            # Verificar si está vacío
            if hasattr(df, 'empty') and df.empty:
                result.add_warning(ValidationError(
                    code="DF_EMPTY",
                    message="DataFrame sin datos",
                    severity=Severity.MEDIUM
                ))
            else:
                row_count = len(df) if hasattr(df, '__len__') else 0
                result.info.append(f"Registros: {row_count}")

            # Verificar valores nulos en columnas críticas
            if hasattr(df, 'isnull'):
                null_counts = df.isnull().sum()
                cols_with_nulls = null_counts[null_counts > 0]
                if len(cols_with_nulls) > 0:
                    for col, count in cols_with_nulls.items():
                        if col.upper() in [c.upper() for c in required_columns]:
                            result.add_warning(ValidationError(
                                code="NULL_VALUES",
                                message=f"Columna '{col}' tiene {count} valores nulos",
                                severity=Severity.MEDIUM,
                                affected_data={'column': col, 'null_count': int(count)}
                            ))

        except Exception as e:
            result.add_error(ValidationError(
                code="DF_VALIDATION_ERROR",
                message=f"Error validando DataFrame: {str(e)}",
                severity=Severity.HIGH
            ))

        result.duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        return result

    def validate_oc_vs_distributions(self, oc_total: float,
                                     dist_total: float,
                                     oc_number: str) -> ValidationResult:
        """
        Validar OC contra distribuciones.

        Args:
            oc_total: Total de la OC
            dist_total: Total de distribuciones
            oc_number: Número de OC

        Returns:
            ValidationResult con resultado de comparación
        """
        result = ValidationResult(name=f"OC vs Distro {oc_number}", status=ValidationStatus.PASSED)

        try:
            difference = dist_total - oc_total
            percentage = (difference / oc_total * 100) if oc_total > 0 else 0

            if dist_total > oc_total:
                # Distribución excede OC - CRÍTICO
                result.add_error(ValidationError(
                    code="DIST_EXCEEDS_OC",
                    message=f"Distribución EXCEDE OC por {difference:,.0f} unidades ({percentage:,.1f}%)",
                    severity=Severity.CRITICAL,
                    details=f"OC Total: {oc_total:,.0f} | Distro Total: {dist_total:,.0f}",
                    solution="Ajustar distribución o aumentar cantidad en OC",
                    affected_data={
                        'oc_total': oc_total,
                        'dist_total': dist_total,
                        'difference': difference,
                        'percentage': percentage
                    }
                ))

            elif dist_total < oc_total:
                # Distribución incompleta - Advertencia
                completion = (dist_total / oc_total * 100) if oc_total > 0 else 0
                if completion < 90:
                    severity = Severity.MEDIUM
                else:
                    severity = Severity.LOW

                result.add_warning(ValidationError(
                    code="DIST_INCOMPLETE",
                    message=f"Distribución incompleta: {completion:,.1f}% completada",
                    severity=severity,
                    details=f"OC Total: {oc_total:,.0f} | Distro Total: {dist_total:,.0f} | Pendiente: {oc_total - dist_total:,.0f}",
                    solution="Completar distribución a tiendas",
                    affected_data={
                        'oc_total': oc_total,
                        'dist_total': dist_total,
                        'pending': oc_total - dist_total,
                        'completion': completion
                    }
                ))
            else:
                # Coinciden exactamente
                result.info.append(f"OC y Distribución coinciden: {oc_total:,.0f} unidades")

        except Exception as e:
            result.add_error(ValidationError(
                code="COMPARISON_ERROR",
                message=f"Error comparando OC vs Distribución: {str(e)}",
                severity=Severity.HIGH
            ))

        return result

    # ═══════════════════════════════════════════════════════════════════════════
    # VALIDACIÓN COMPLETA
    # ═══════════════════════════════════════════════════════════════════════════

    def run_all_validations(self, config: Any = None,
                            connection: Any = None) -> Dict[str, ValidationResult]:
        """
        Ejecutar todas las validaciones disponibles.

        Args:
            config: Configuración SACYTY (opcional)
            connection: Conexión a DB2 (opcional)

        Returns:
            Dict con resultados de todas las validaciones
        """
        results = {}

        # Validar sistema
        results['system'] = self.validate_system()

        # Validar configuración si está disponible
        if config:
            results['config'] = self.validate_config(config)

        # Validar conexión si está disponible
        if connection:
            results['database'] = self.validate_db_connection(connection)

        return results

    def get_summary(self, results: Dict[str, ValidationResult]) -> Dict[str, Any]:
        """
        Obtener resumen de validaciones.

        Args:
            results: Diccionario de resultados

        Returns:
            Dict con resumen
        """
        total_errors = sum(r.error_count for r in results.values())
        total_warnings = sum(r.warning_count for r in results.values())
        all_passed = all(r.is_valid for r in results.values())

        return {
            'all_passed': all_passed,
            'total_validations': len(results),
            'total_errors': total_errors,
            'total_warnings': total_warnings,
            'validations': {
                name: {
                    'status': result.status.value,
                    'is_valid': result.is_valid,
                    'errors': result.error_count,
                    'warnings': result.warning_count
                }
                for name, result in results.items()
            }
        }


# ═══════════════════════════════════════════════════════════════════════════════
# EJECUCIÓN DIRECTA
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Test del validador
    validator = SACYTYValidator()

    print("\n" + "=" * 60)
    print("SACYTY - Prueba de Validador Ligero")
    print("=" * 60)

    # Validar sistema
    print("\n1. Validando sistema...")
    result = validator.validate_system()
    print(f"   Estado: {result.status.value}")
    print(f"   Errores: {result.error_count} | Advertencias: {result.warning_count}")
    for info in result.info:
        print(f"   + {info}")

    # Validar formato de OC
    print("\n2. Validando formatos de OC...")
    test_ocs = ["750384123456", "C750384123456", "INVALID", "40123456789012"]
    for oc in test_ocs:
        result = validator.validate_oc_number(oc)
        print(f"   OC '{oc}': {result.status.value}")

    # Validar comparación OC vs Distro
    print("\n3. Validando OC vs Distribución...")
    test_cases = [
        (1000, 1000, "OC_IGUAL"),
        (1000, 1200, "OC_EXCEDE"),
        (1000, 800, "OC_INCOMPLETA")
    ]
    for oc_total, dist_total, name in test_cases:
        result = validator.validate_oc_vs_distributions(oc_total, dist_total, name)
        print(f"   {name}: {result.status.value}")
        for err in result.errors:
            print(f"      ERROR: {err.message}")
        for warn in result.warnings:
            print(f"      WARN: {warn.message}")

    print("\n" + "=" * 60)
    print("Validación completada")
    print("=" * 60)
# Alias for compatibility
SACITYValidator = SACYTYValidator
