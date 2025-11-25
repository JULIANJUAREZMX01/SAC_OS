"""
═══════════════════════════════════════════════════════════════════════════════
SACYTY - Instalador para Dispositivos
Sistema de Automatización Chedraui - Modelo TinY
═══════════════════════════════════════════════════════════════════════════════

Instalador ligero diseñado para:
- Despliegue rápido en dispositivos a recuperar
- Mínimas dependencias
- Configuración automatizada
- Integración con la suite SAC

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
═══════════════════════════════════════════════════════════════════════════════
"""

import os
import sys
import shutil
import subprocess
import platform
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTES
# ═══════════════════════════════════════════════════════════════════════════════

SACYTY_VERSION = "1.0.0"
SACYTY_NAME = "SACYTY"

# Dependencias mínimas requeridas
CORE_DEPENDENCIES = [
    "python-dotenv>=1.0.0",
]

# Dependencias opcionales para funcionalidad extendida
OPTIONAL_DEPENDENCIES = [
    "pandas>=2.0.0",
    "openpyxl>=3.1.0",
]

# Archivos esenciales del módulo
ESSENTIAL_FILES = [
    "__init__.py",
    "sacyty_config.py",
    "sacyty_core.py",
    "sacyty_validator.py",
    "sacyty_installer.py",
]


# ═══════════════════════════════════════════════════════════════════════════════
# CLASE INSTALADOR
# ═══════════════════════════════════════════════════════════════════════════════

class SACYTYInstaller:
    """
    Instalador ligero de SACYTY para dispositivos.

    Características:
    - Verificación de requisitos mínimos
    - Instalación de dependencias básicas
    - Configuración automática
    - Verificación post-instalación
    """

    def __init__(self, target_path: Optional[Path] = None):
        """
        Inicializar instalador.

        Args:
            target_path: Ruta de instalación (opcional)
        """
        self.source_path = Path(__file__).parent
        self.target_path = target_path or self._get_default_target()
        self.log_messages: List[str] = []
        self.errors: List[str] = []

        # Configurar logging básico
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def _get_default_target(self) -> Path:
        """Obtener ruta de instalación por defecto"""
        if platform.system() == "Windows":
            return Path(os.environ.get('LOCALAPPDATA', 'C:\\')) / "SACYTY"
        else:
            return Path.home() / ".sacyty"

    def _log(self, message: str, level: str = "INFO") -> None:
        """Registrar mensaje"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        formatted = f"[{timestamp}] [{level}] {message}"
        self.log_messages.append(formatted)

        if level == "ERROR":
            self.errors.append(message)
            self.logger.error(message)
        elif level == "WARNING":
            self.logger.warning(message)
        else:
            self.logger.info(message)

    # ═══════════════════════════════════════════════════════════════════════════
    # VERIFICACIONES
    # ═══════════════════════════════════════════════════════════════════════════

    def check_python_version(self) -> Tuple[bool, str]:
        """
        Verificar versión de Python.

        Returns:
            Tuple[bool, str]: (compatible, mensaje)
        """
        version = sys.version_info
        version_str = f"{version.major}.{version.minor}.{version.micro}"

        if version.major < 3 or (version.major == 3 and version.minor < 8):
            return False, f"Python {version_str} no compatible. Se requiere 3.8+"

        return True, f"Python {version_str} compatible"

    def check_pip_available(self) -> Tuple[bool, str]:
        """
        Verificar disponibilidad de pip.

        Returns:
            Tuple[bool, str]: (disponible, mensaje)
        """
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "--version"],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                return True, f"pip disponible: {result.stdout.strip()}"
            return False, "pip no disponible"
        except Exception as e:
            return False, f"Error verificando pip: {str(e)}"

    def check_disk_space(self, required_mb: int = 50) -> Tuple[bool, str]:
        """
        Verificar espacio en disco.

        Args:
            required_mb: Espacio requerido en MB

        Returns:
            Tuple[bool, str]: (suficiente, mensaje)
        """
        try:
            if platform.system() == "Windows":
                import ctypes
                free_bytes = ctypes.c_ulonglong(0)
                ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                    ctypes.c_wchar_p(str(self.target_path.parent)),
                    None, None, ctypes.pointer(free_bytes)
                )
                free_mb = free_bytes.value / (1024 * 1024)
            else:
                stat = os.statvfs(self.target_path.parent if self.target_path.parent.exists() else Path.home())
                free_mb = (stat.f_bavail * stat.f_frsize) / (1024 * 1024)

            if free_mb >= required_mb:
                return True, f"Espacio disponible: {free_mb:.0f} MB"
            return False, f"Espacio insuficiente: {free_mb:.0f} MB (requerido: {required_mb} MB)"

        except Exception as e:
            return True, f"No se pudo verificar espacio: {str(e)}"

    def check_write_permissions(self) -> Tuple[bool, str]:
        """
        Verificar permisos de escritura.

        Returns:
            Tuple[bool, str]: (tiene_permisos, mensaje)
        """
        try:
            test_dir = self.target_path.parent
            if not test_dir.exists():
                test_dir = Path.home()

            test_file = test_dir / ".sacyty_test"
            test_file.touch()
            test_file.unlink()
            return True, "Permisos de escritura verificados"

        except PermissionError:
            return False, "Sin permisos de escritura en directorio destino"
        except Exception as e:
            return False, f"Error verificando permisos: {str(e)}"

    def run_preflight_checks(self) -> Tuple[bool, List[str]]:
        """
        Ejecutar todas las verificaciones previas.

        Returns:
            Tuple[bool, List[str]]: (todo_ok, lista_de_resultados)
        """
        results = []
        all_ok = True

        checks = [
            ("Python", self.check_python_version),
            ("pip", self.check_pip_available),
            ("Espacio en disco", self.check_disk_space),
            ("Permisos", self.check_write_permissions),
        ]

        for name, check_func in checks:
            try:
                ok, msg = check_func()
                status = "OK" if ok else "ERROR"
                results.append(f"[{status}] {name}: {msg}")
                if not ok:
                    all_ok = False
            except Exception as e:
                results.append(f"[ERROR] {name}: {str(e)}")
                all_ok = False

        return all_ok, results

    # ═══════════════════════════════════════════════════════════════════════════
    # INSTALACIÓN
    # ═══════════════════════════════════════════════════════════════════════════

    def install_dependencies(self, include_optional: bool = False) -> Tuple[bool, List[str]]:
        """
        Instalar dependencias.

        Args:
            include_optional: Incluir dependencias opcionales

        Returns:
            Tuple[bool, List[str]]: (éxito, mensajes)
        """
        messages = []
        deps = CORE_DEPENDENCIES.copy()

        if include_optional:
            deps.extend(OPTIONAL_DEPENDENCIES)

        for dep in deps:
            try:
                self._log(f"Instalando {dep}...")
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", dep, "--quiet"],
                    capture_output=True,
                    text=True,
                    timeout=120
                )

                if result.returncode == 0:
                    messages.append(f"OK: {dep}")
                else:
                    messages.append(f"ERROR: {dep} - {result.stderr}")
                    self._log(f"Error instalando {dep}", "WARNING")

            except subprocess.TimeoutExpired:
                messages.append(f"TIMEOUT: {dep}")
            except Exception as e:
                messages.append(f"ERROR: {dep} - {str(e)}")

        success = not any("ERROR" in m for m in messages)
        return success, messages

    def copy_files(self) -> Tuple[bool, List[str]]:
        """
        Copiar archivos de SACYTY al destino.

        Returns:
            Tuple[bool, List[str]]: (éxito, mensajes)
        """
        messages = []

        try:
            # Crear directorio destino
            self.target_path.mkdir(parents=True, exist_ok=True)
            messages.append(f"Directorio creado: {self.target_path}")

            # Copiar archivos esenciales
            for filename in ESSENTIAL_FILES:
                source = self.source_path / filename
                dest = self.target_path / filename

                if source.exists():
                    shutil.copy2(source, dest)
                    messages.append(f"Copiado: {filename}")
                else:
                    messages.append(f"ADVERTENCIA: No encontrado: {filename}")

            return True, messages

        except Exception as e:
            messages.append(f"ERROR: {str(e)}")
            return False, messages

    def create_env_template(self) -> Tuple[bool, str]:
        """
        Crear plantilla de archivo .env.

        Returns:
            Tuple[bool, str]: (éxito, mensaje)
        """
        env_template = """# ═══════════════════════════════════════════════════════════════════════════════
# SACYTY - Configuración de Entorno
# Sistema de Automatización Chedraui - Modelo TinY
# ═══════════════════════════════════════════════════════════════════════════════

# Base de Datos DB2 (Manhattan WMS)
DB_HOST=WM260BASD
DB_PORT=50000
DB_DATABASE=WM260BASD
DB_SCHEMA=WMWHSE1
DB_USER=tu_usuario
DB_PASSWORD=tu_password
DB_TIMEOUT=30

# CEDIS
CEDIS_CODE=427
CEDIS_NAME=CEDIS Cancún
CEDIS_REGION=Sureste
CEDIS_ALMACEN=C22
TIMEZONE=America/Cancun

# Email (Opcional)
EMAIL_HOST=smtp.office365.com
EMAIL_PORT=587
EMAIL_USER=
EMAIL_PASSWORD=
EMAIL_USE_TLS=true

# Sistema
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
"""
        try:
            env_file = self.target_path / "env.template"
            with open(env_file, 'w', encoding='utf-8') as f:
                f.write(env_template)
            return True, f"Plantilla creada: {env_file}"
        except Exception as e:
            return False, f"Error creando plantilla: {str(e)}"

    def create_launcher(self) -> Tuple[bool, str]:
        """
        Crear script de lanzamiento.

        Returns:
            Tuple[bool, str]: (éxito, mensaje)
        """
        if platform.system() == "Windows":
            # Script batch para Windows
            launcher_content = f"""@echo off
title SACYTY - Sistema Ligero
cd /d "{self.target_path}"
python -c "from sacyty_core import SACYTYCore; s = SACYTYCore(); print(s.generate_status_report())"
pause
"""
            launcher_file = self.target_path / "SACYTY.bat"
        else:
            # Script bash para Linux/Mac
            launcher_content = f"""#!/bin/bash
cd "{self.target_path}"
python3 -c "from sacyty_core import SACYTYCore; s = SACYTYCore(); print(s.generate_status_report())"
"""
            launcher_file = self.target_path / "sacyty.sh"

        try:
            with open(launcher_file, 'w', encoding='utf-8') as f:
                f.write(launcher_content)

            if platform.system() != "Windows":
                os.chmod(launcher_file, 0o755)

            return True, f"Lanzador creado: {launcher_file}"
        except Exception as e:
            return False, f"Error creando lanzador: {str(e)}"

    # ═══════════════════════════════════════════════════════════════════════════
    # INSTALACIÓN COMPLETA
    # ═══════════════════════════════════════════════════════════════════════════

    def install(self, include_optional: bool = False,
                skip_deps: bool = False) -> Dict[str, Any]:
        """
        Ejecutar instalación completa de SACYTY.

        Args:
            include_optional: Incluir dependencias opcionales
            skip_deps: Omitir instalación de dependencias

        Returns:
            Dict con resultado de instalación
        """
        result = {
            'success': False,
            'version': SACYTY_VERSION,
            'target_path': str(self.target_path),
            'timestamp': datetime.now().isoformat(),
            'steps': [],
            'errors': []
        }

        print(f"""
╔══════════════════════════════════════════════════════════════╗
║        SACYTY - Instalador de Sistema Ligero                ║
║        Version {SACYTY_VERSION}                                         ║
╠══════════════════════════════════════════════════════════════╣
║  Destino: {str(self.target_path)[:47]:<47} ║
╚══════════════════════════════════════════════════════════════╝
""")

        # Paso 1: Verificaciones previas
        print("\n[1/5] Ejecutando verificaciones previas...")
        ok, checks = self.run_preflight_checks()
        result['steps'].append({'name': 'Verificaciones', 'status': 'OK' if ok else 'ERROR', 'details': checks})
        for check in checks:
            print(f"  {check}")

        if not ok:
            result['errors'].append("Verificaciones previas fallidas")
            print("\nERROR: Las verificaciones previas no pasaron.")
            return result

        # Paso 2: Instalar dependencias
        if not skip_deps:
            print("\n[2/5] Instalando dependencias...")
            ok, deps = self.install_dependencies(include_optional)
            result['steps'].append({'name': 'Dependencias', 'status': 'OK' if ok else 'WARNING', 'details': deps})
            for dep in deps:
                print(f"  {dep}")
        else:
            print("\n[2/5] Omitiendo instalación de dependencias...")
            result['steps'].append({'name': 'Dependencias', 'status': 'SKIPPED', 'details': []})

        # Paso 3: Copiar archivos
        print("\n[3/5] Copiando archivos...")
        ok, files = self.copy_files()
        result['steps'].append({'name': 'Archivos', 'status': 'OK' if ok else 'ERROR', 'details': files})
        for f in files:
            print(f"  {f}")

        if not ok:
            result['errors'].append("Error copiando archivos")
            return result

        # Paso 4: Crear plantilla de configuración
        print("\n[4/5] Creando configuración...")
        ok, msg = self.create_env_template()
        result['steps'].append({'name': 'Configuración', 'status': 'OK' if ok else 'ERROR', 'details': [msg]})
        print(f"  {msg}")

        # Paso 5: Crear lanzador
        print("\n[5/5] Creando lanzador...")
        ok, msg = self.create_launcher()
        result['steps'].append({'name': 'Lanzador', 'status': 'OK' if ok else 'ERROR', 'details': [msg]})
        print(f"  {msg}")

        # Resultado final
        result['success'] = len(result['errors']) == 0

        if result['success']:
            print(f"""
╔══════════════════════════════════════════════════════════════╗
║          INSTALACIÓN COMPLETADA EXITOSAMENTE                ║
╠══════════════════════════════════════════════════════════════╣
║  Ubicación: {str(self.target_path)[:45]:<45} ║
║                                                              ║
║  Próximos pasos:                                             ║
║  1. Copiar env.template a .env                               ║
║  2. Configurar credenciales en .env                          ║
║  3. Ejecutar SACYTY.bat (Windows) o sacyty.sh (Linux)        ║
╚══════════════════════════════════════════════════════════════╝
""")
        else:
            print(f"""
╔══════════════════════════════════════════════════════════════╗
║            INSTALACIÓN COMPLETADA CON ERRORES               ║
╠══════════════════════════════════════════════════════════════╣
║  Errores encontrados:                                        ║""")
            for err in result['errors']:
                print(f"║    - {err[:52]:<52} ║")
            print("╚══════════════════════════════════════════════════════════════╝")

        return result

    # ═══════════════════════════════════════════════════════════════════════════
    # DESINSTALACIÓN
    # ═══════════════════════════════════════════════════════════════════════════

    def uninstall(self, remove_config: bool = False) -> Tuple[bool, str]:
        """
        Desinstalar SACYTY.

        Args:
            remove_config: Eliminar archivos de configuración

        Returns:
            Tuple[bool, str]: (éxito, mensaje)
        """
        try:
            if not self.target_path.exists():
                return True, "SACYTY no está instalado en esta ubicación"

            if remove_config:
                shutil.rmtree(self.target_path)
                return True, f"SACYTY desinstalado completamente de {self.target_path}"
            else:
                # Solo eliminar archivos de código, mantener configuración
                for filename in ESSENTIAL_FILES:
                    file_path = self.target_path / filename
                    if file_path.exists():
                        file_path.unlink()

                return True, f"Archivos de SACYTY eliminados (configuración mantenida)"

        except Exception as e:
            return False, f"Error desinstalando: {str(e)}"


# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIONES DE CONVENIENCIA
# ═══════════════════════════════════════════════════════════════════════════════

def install_sacyty(target_path: Optional[str] = None,
                   include_optional: bool = False) -> Dict[str, Any]:
    """
    Instalar SACYTY en ubicación especificada.

    Args:
        target_path: Ruta de instalación
        include_optional: Incluir dependencias opcionales

    Returns:
        Dict con resultado de instalación
    """
    path = Path(target_path) if target_path else None
    installer = SACYTYInstaller(path)
    return installer.install(include_optional=include_optional)


def uninstall_sacyty(target_path: Optional[str] = None,
                     remove_config: bool = False) -> Tuple[bool, str]:
    """
    Desinstalar SACYTY.

    Args:
        target_path: Ruta de instalación
        remove_config: Eliminar configuración

    Returns:
        Tuple[bool, str]: (éxito, mensaje)
    """
    path = Path(target_path) if target_path else None
    installer = SACYTYInstaller(path)
    return installer.uninstall(remove_config)


# ═══════════════════════════════════════════════════════════════════════════════
# EJECUCIÓN DIRECTA
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="SACYTY - Instalador de Sistema Ligero",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python sacyty_installer.py --install
  python sacyty_installer.py --install --path /opt/sacyty
  python sacyty_installer.py --install --optional
  python sacyty_installer.py --uninstall
  python sacyty_installer.py --check
        """
    )

    parser.add_argument('--install', action='store_true',
                        help='Instalar SACYTY')
    parser.add_argument('--uninstall', action='store_true',
                        help='Desinstalar SACYTY')
    parser.add_argument('--check', action='store_true',
                        help='Solo ejecutar verificaciones')
    parser.add_argument('--path', type=str,
                        help='Ruta de instalación')
    parser.add_argument('--optional', action='store_true',
                        help='Incluir dependencias opcionales')
    parser.add_argument('--skip-deps', action='store_true',
                        help='Omitir instalación de dependencias')
    parser.add_argument('--remove-config', action='store_true',
                        help='Eliminar configuración al desinstalar')

    args = parser.parse_args()

    # Si no se especifica ninguna acción, mostrar ayuda
    if not (args.install or args.uninstall or args.check):
        parser.print_help()
        sys.exit(0)

    path = Path(args.path) if args.path else None
    installer = SACYTYInstaller(path)

    if args.check:
        print("\nEjecutando verificaciones del sistema...")
        ok, results = installer.run_preflight_checks()
        for r in results:
            print(f"  {r}")
        sys.exit(0 if ok else 1)

    elif args.install:
        result = installer.install(
            include_optional=args.optional,
            skip_deps=args.skip_deps
        )
        sys.exit(0 if result['success'] else 1)

    elif args.uninstall:
        ok, msg = installer.uninstall(remove_config=args.remove_config)
        print(msg)
        sys.exit(0 if ok else 1)
