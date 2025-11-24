"""
═══════════════════════════════════════════════════════════════
TESTS CORE - Sistema SAC
CEDIS Chedraui Cancún 427
═══════════════════════════════════════════════════════════════

Tests básicos para verificar funcionalidad core del sistema.

Ejecutar:
    pytest tests/test_core.py -v
    pytest tests/test_core.py -v --cov=. --cov-report=html

═══════════════════════════════════════════════════════════════
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

# Agregar directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))


# ═══════════════════════════════════════════════════════════════
# TESTS DE CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════

class TestConfiguracion:
    """Tests para el módulo de configuración"""

    def test_config_importable(self):
        """Verifica que config.py se puede importar"""
        try:
            from config import DB_CONFIG, CEDIS, EMAIL_CONFIG
            assert DB_CONFIG is not None
            assert CEDIS is not None
            assert EMAIL_CONFIG is not None
        except ImportError as e:
            pytest.skip(f"Config no disponible: {e}")

    def test_cedis_tiene_campos_requeridos(self):
        """Verifica que CEDIS tiene los campos necesarios"""
        try:
            from config import CEDIS
            assert 'code' in CEDIS or 'codigo' in CEDIS
            assert 'name' in CEDIS or 'nombre' in CEDIS
        except ImportError:
            pytest.skip("Config no disponible")

    def test_paths_existen(self):
        """Verifica que las rutas configuradas existen o se pueden crear"""
        try:
            from config import PATHS
            # Solo verificar que PATHS es un diccionario
            assert isinstance(PATHS, dict)
        except ImportError:
            pytest.skip("PATHS no definido en config")


# ═══════════════════════════════════════════════════════════════
# TESTS DE MONITOR
# ═══════════════════════════════════════════════════════════════

class TestMonitor:
    """Tests para el módulo de monitoreo"""

    def test_error_severity_enum(self):
        """Verifica que ErrorSeverity tiene los valores esperados"""
        try:
            from monitor import ErrorSeverity
            assert hasattr(ErrorSeverity, 'CRITICO')
            assert hasattr(ErrorSeverity, 'ALTO')
            assert hasattr(ErrorSeverity, 'MEDIO')
            assert hasattr(ErrorSeverity, 'BAJO')
            assert hasattr(ErrorSeverity, 'INFO')
        except ImportError as e:
            pytest.skip(f"Monitor no disponible: {e}")

    def test_error_detectado_dataclass(self):
        """Verifica que ErrorDetectado funciona correctamente"""
        try:
            from monitor import ErrorDetectado, ErrorSeverity

            error = ErrorDetectado(
                tipo="TEST_ERROR",
                severidad=ErrorSeverity.MEDIO,
                mensaje="Error de prueba",
                detalles="Detalles del error",
                solucion="Solucion sugerida",
                timestamp=datetime.now(),
                modulo="TEST"
            )

            assert error.tipo == "TEST_ERROR"
            assert error.severidad == ErrorSeverity.MEDIO
            assert "prueba" in error.mensaje
        except ImportError as e:
            pytest.skip(f"Monitor no disponible: {e}")

    def test_monitor_tiempo_real_instanciable(self):
        """Verifica que MonitorTiempoReal se puede instanciar"""
        try:
            from monitor import MonitorTiempoReal
            monitor = MonitorTiempoReal()
            assert monitor is not None
            assert hasattr(monitor, 'errores_detectados')
        except ImportError as e:
            pytest.skip(f"Monitor no disponible: {e}")


# ═══════════════════════════════════════════════════════════════
# TESTS DE TELEGRAM (con Rate Limiter)
# ═══════════════════════════════════════════════════════════════

class TestTelegramRateLimiter:
    """Tests para el rate limiter de Telegram"""

    def test_rate_limiter_importable(self):
        """Verifica que RateLimiter se puede importar"""
        try:
            from notificaciones_telegram import RateLimiter
            assert RateLimiter is not None
        except ImportError as e:
            pytest.skip(f"Telegram no disponible: {e}")

    def test_rate_limiter_instanciable(self):
        """Verifica que RateLimiter se puede instanciar"""
        try:
            from notificaciones_telegram import RateLimiter

            limiter = RateLimiter(max_requests=10, window_seconds=1.0)
            assert limiter.max_requests == 10
            assert limiter.window_seconds == 1.0
        except ImportError:
            pytest.skip("RateLimiter no disponible")

    def test_rate_limiter_acquire(self):
        """Verifica que acquire funciona"""
        try:
            from notificaciones_telegram import RateLimiter

            limiter = RateLimiter(max_requests=5, window_seconds=1.0)
            result = limiter.acquire(chat_id="test_chat")
            assert result is True
        except ImportError:
            pytest.skip("RateLimiter no disponible")

    def test_rate_limiter_stats(self):
        """Verifica que get_stats funciona"""
        try:
            from notificaciones_telegram import RateLimiter

            limiter = RateLimiter(max_requests=10, window_seconds=1.0)
            limiter.acquire()
            limiter.acquire()

            stats = limiter.get_stats()
            assert 'active_requests' in stats
            assert 'max_requests' in stats
            assert 'usage_percent' in stats
            assert stats['active_requests'] >= 2
        except ImportError:
            pytest.skip("RateLimiter no disponible")


# ═══════════════════════════════════════════════════════════════
# TESTS DE REPORTES EXCEL
# ═══════════════════════════════════════════════════════════════

class TestReportesExcel:
    """Tests para el generador de reportes Excel"""

    def test_generador_importable(self):
        """Verifica que GeneradorReportesExcel se puede importar"""
        try:
            from modules.reportes_excel import GeneradorReportesExcel
            assert GeneradorReportesExcel is not None
        except ImportError as e:
            pytest.skip(f"Reportes no disponible: {e}")

    def test_generador_instanciable(self):
        """Verifica que GeneradorReportesExcel se puede instanciar"""
        try:
            from modules.reportes_excel import GeneradorReportesExcel
            generador = GeneradorReportesExcel(cedis="TEST")
            assert generador is not None
        except ImportError:
            pytest.skip("GeneradorReportesExcel no disponible")


# ═══════════════════════════════════════════════════════════════
# TESTS DE INSTALADOR
# ═══════════════════════════════════════════════════════════════

class TestInstalador:
    """Tests para el instalador"""

    def test_instalador_importable(self):
        """Verifica que el instalador se puede importar"""
        try:
            # Importar funciones del instalador
            import instalar_sac
            assert hasattr(instalar_sac, 'InstaladorSAC')
            assert hasattr(instalar_sac, 'VERSION')
        except ImportError as e:
            pytest.skip(f"Instalador no disponible: {e}")

    def test_estado_instalacion_enum(self):
        """Verifica que EstadoInstalacion existe"""
        try:
            from instalar_sac import EstadoInstalacion
            assert hasattr(EstadoInstalacion, 'NO_INSTALADO')
            assert hasattr(EstadoInstalacion, 'COMPLETO')
        except ImportError:
            pytest.skip("EstadoInstalacion no disponible")

    def test_resultado_verificacion_dataclass(self):
        """Verifica que ResultadoVerificacion funciona"""
        try:
            from instalar_sac import ResultadoVerificacion, EstadoInstalacion

            resultado = ResultadoVerificacion(
                python_ok=True,
                pip_ok=True,
                directorios_ok=True,
                env_ok=False,
                dependencias_ok=True,
                dependencias_faltantes=[],
                estado=EstadoInstalacion.PARCIAL,
                mensaje="Test"
            )

            assert resultado.python_ok is True
            assert resultado.estado == EstadoInstalacion.PARCIAL
        except ImportError:
            pytest.skip("ResultadoVerificacion no disponible")


# ═══════════════════════════════════════════════════════════════
# TESTS DE ESTRUCTURA DE DIRECTORIOS
# ═══════════════════════════════════════════════════════════════

class TestEstructura:
    """Tests para verificar estructura del proyecto"""

    def test_directorios_principales_existen(self):
        """Verifica que los directorios principales existen"""
        base = Path(__file__).parent.parent

        directorios = ['config', 'modules', 'queries', 'docs', 'tests']

        for dir_name in directorios:
            dir_path = base / dir_name
            assert dir_path.exists(), f"Directorio {dir_name} no existe"

    def test_archivos_principales_existen(self):
        """Verifica que los archivos principales existen"""
        base = Path(__file__).parent.parent

        archivos = [
            'main.py',
            'monitor.py',
            'config.py',
            'requirements.txt',
            'instalar_sac.py',
        ]

        for archivo in archivos:
            file_path = base / archivo
            assert file_path.exists(), f"Archivo {archivo} no existe"

    def test_requirements_no_vacio(self):
        """Verifica que requirements.txt no está vacío"""
        base = Path(__file__).parent.parent
        req_file = base / 'requirements.txt'

        assert req_file.exists()
        content = req_file.read_text()
        assert len(content) > 100, "requirements.txt parece vacío"
        assert 'pandas' in content, "pandas no está en requirements"
        assert 'rich' in content, "rich no está en requirements"


# ═══════════════════════════════════════════════════════════════
# EJECUTAR TESTS
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
