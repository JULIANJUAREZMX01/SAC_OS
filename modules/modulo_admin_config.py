#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════
MÓDULO DE CONFIGURACIÓN ADMINISTRATIVA SAC
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Este módulo gestiona la configuración administrativa para el
despliegue empresarial de SAC en el entorno del CEDIS 427.

Características:
- Configuración centralizada de despliegue
- Gestión de permisos y roles
- Registro de equipos autorizados
- Auditoría de accesos
- Configuración de políticas

IMPORTANTE: Este módulo opera bajo el principio de mínimo
privilegio. SAC no requiere ni solicita permisos administrativos
del sistema operativo para su funcionamiento normal.

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
═══════════════════════════════════════════════════════════════
"""

import os
import json
import socket
import hashlib
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum

# Configuración de logging
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# ENUMERACIONES Y CONSTANTES
# ═══════════════════════════════════════════════════════════════

class RolUsuario(Enum):
    """Roles disponibles en SAC"""
    ADMINISTRADOR = "administrador"     # Acceso completo
    ANALISTA = "analista"               # Operaciones normales
    SUPERVISOR = "supervisor"           # Lectura + reportes
    CONSULTA = "consulta"               # Solo lectura
    SERVICIO = "servicio"               # Cuenta de servicio


class EstadoEquipo(Enum):
    """Estados de equipos registrados"""
    ACTIVO = "activo"
    INACTIVO = "inactivo"
    PENDIENTE = "pendiente"
    BLOQUEADO = "bloqueado"


class NivelLog(Enum):
    """Niveles de auditoría"""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    AUDIT = "AUDIT"


# ═══════════════════════════════════════════════════════════════
# ESTRUCTURAS DE DATOS
# ═══════════════════════════════════════════════════════════════

@dataclass
class EquipoRegistrado:
    """Representa un equipo autorizado para ejecutar SAC"""
    hostname: str
    ip_address: str
    mac_address: str = ""
    usuario_registro: str = ""
    fecha_registro: str = ""
    estado: str = "activo"
    rol_asignado: str = "consulta"
    ubicacion: str = "CEDIS 427"
    descripcion: str = ""
    ultima_conexion: str = ""

    def __post_init__(self):
        if not self.fecha_registro:
            self.fecha_registro = datetime.now().isoformat()


@dataclass
class ConfiguracionDespliegue:
    """Configuración de despliegue empresarial"""
    # Información del CEDIS
    cedis_code: str = "427"
    cedis_name: str = "CEDIS Cancún"
    cedis_region: str = "Sureste"

    # Rutas de instalación
    install_base_path: str = "C:\\SAC"
    shared_config_path: str = ""  # UNC path para config compartida
    log_server_path: str = ""     # Servidor de logs centralizado

    # Configuración de servicio
    service_name: str = "SACMonitor"
    service_auto_start: bool = True
    service_restart_on_failure: bool = True
    service_restart_delay_seconds: int = 60

    # Políticas de seguridad
    require_domain_auth: bool = True
    allowed_domains: List[str] = field(default_factory=lambda: ["gcch.com"])
    session_timeout_minutes: int = 480  # 8 horas

    # Políticas de actualización
    auto_update_enabled: bool = False
    update_server_url: str = ""
    update_check_interval_hours: int = 24

    # Notificaciones
    notify_on_install: bool = True
    notify_on_error: bool = True
    admin_email: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'ConfiguracionDespliegue':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class RegistroAuditoria:
    """Registro de auditoría de accesos y operaciones"""
    timestamp: str = ""
    hostname: str = ""
    usuario: str = ""
    accion: str = ""
    modulo: str = ""
    resultado: str = ""
    detalles: str = ""
    nivel: str = "INFO"

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


# ═══════════════════════════════════════════════════════════════
# CLASE PRINCIPAL DE ADMINISTRACIÓN
# ═══════════════════════════════════════════════════════════════

class AdministradorSAC:
    """
    Gestor de configuración administrativa para SAC.

    Esta clase maneja:
    - Registro y autorización de equipos
    - Configuración de despliegue
    - Auditoría de accesos
    - Políticas de seguridad

    NOTA: Este módulo NO otorga ni requiere privilegios
    administrativos del sistema operativo.
    """

    def __init__(self, config_dir: Optional[Path] = None):
        """
        Inicializa el administrador SAC.

        Args:
            config_dir: Directorio de configuración. Si no se especifica,
                       usa el directorio por defecto del proyecto.
        """
        self.config_dir = config_dir or self._get_default_config_dir()
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Archivos de configuración
        self.equipos_file = self.config_dir / "equipos_registrados.json"
        self.config_file = self.config_dir / "deploy_config.json"
        self.audit_file = self.config_dir / "audit_log.json"

        # Cargar configuraciones
        self.equipos: Dict[str, EquipoRegistrado] = {}
        self.config: ConfiguracionDespliegue = ConfiguracionDespliegue()

        self._cargar_configuraciones()

        logger.info(f"AdministradorSAC inicializado. Config dir: {self.config_dir}")

    def _get_default_config_dir(self) -> Path:
        """Obtiene el directorio de configuración por defecto"""
        # Buscar directorio del proyecto
        current = Path(__file__).resolve().parent.parent
        return current / "config" / "admin"

    def _cargar_configuraciones(self):
        """Carga todas las configuraciones desde archivos"""
        self._cargar_equipos()
        self._cargar_config_despliegue()

    def _cargar_equipos(self):
        """Carga equipos registrados desde archivo JSON"""
        if self.equipos_file.exists():
            try:
                with open(self.equipos_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.equipos = {
                        k: EquipoRegistrado(**v) for k, v in data.items()
                    }
                logger.info(f"Cargados {len(self.equipos)} equipos registrados")
            except Exception as e:
                logger.error(f"Error cargando equipos: {e}")
                self.equipos = {}

    def _cargar_config_despliegue(self):
        """Carga configuración de despliegue"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.config = ConfiguracionDespliegue.from_dict(data)
                logger.info("Configuración de despliegue cargada")
            except Exception as e:
                logger.error(f"Error cargando configuración: {e}")
                self.config = ConfiguracionDespliegue()

    def _guardar_equipos(self):
        """Guarda equipos registrados a archivo"""
        try:
            data = {k: asdict(v) for k, v in self.equipos.items()}
            with open(self.equipos_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.debug("Equipos guardados correctamente")
        except Exception as e:
            logger.error(f"Error guardando equipos: {e}")

    def _guardar_config(self):
        """Guarda configuración de despliegue"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config.to_dict(), f, indent=2, ensure_ascii=False)
            logger.debug("Configuración guardada correctamente")
        except Exception as e:
            logger.error(f"Error guardando configuración: {e}")

    # ═══════════════════════════════════════════════════════════
    # GESTIÓN DE EQUIPOS
    # ═══════════════════════════════════════════════════════════

    def registrar_equipo_actual(self, rol: RolUsuario = RolUsuario.CONSULTA) -> EquipoRegistrado:
        """
        Registra el equipo actual en el sistema.

        Args:
            rol: Rol a asignar al equipo

        Returns:
            EquipoRegistrado con la información del equipo
        """
        hostname = socket.gethostname()
        ip_address = self._obtener_ip_local()

        equipo = EquipoRegistrado(
            hostname=hostname,
            ip_address=ip_address,
            usuario_registro=os.environ.get('USERNAME', 'unknown'),
            rol_asignado=rol.value,
            descripcion=f"Auto-registrado desde {hostname}"
        )

        self.equipos[hostname] = equipo
        self._guardar_equipos()

        self._registrar_auditoria(
            accion="REGISTRO_EQUIPO",
            modulo="admin_config",
            resultado="OK",
            detalles=f"Equipo {hostname} registrado con rol {rol.value}"
        )

        logger.info(f"Equipo registrado: {hostname} ({ip_address})")
        return equipo

    def obtener_equipo(self, hostname: str) -> Optional[EquipoRegistrado]:
        """Obtiene información de un equipo registrado"""
        return self.equipos.get(hostname)

    def listar_equipos(self, solo_activos: bool = False) -> List[EquipoRegistrado]:
        """
        Lista todos los equipos registrados.

        Args:
            solo_activos: Si es True, solo devuelve equipos activos

        Returns:
            Lista de equipos registrados
        """
        equipos = list(self.equipos.values())

        if solo_activos:
            equipos = [e for e in equipos if e.estado == EstadoEquipo.ACTIVO.value]

        return equipos

    def actualizar_estado_equipo(self, hostname: str, estado: EstadoEquipo) -> bool:
        """Actualiza el estado de un equipo"""
        if hostname in self.equipos:
            self.equipos[hostname].estado = estado.value
            self._guardar_equipos()

            self._registrar_auditoria(
                accion="ACTUALIZAR_ESTADO",
                modulo="admin_config",
                resultado="OK",
                detalles=f"Equipo {hostname} -> {estado.value}"
            )
            return True
        return False

    def verificar_equipo_autorizado(self) -> bool:
        """
        Verifica si el equipo actual está autorizado.

        Returns:
            True si el equipo está autorizado y activo
        """
        hostname = socket.gethostname()
        equipo = self.equipos.get(hostname)

        if equipo and equipo.estado == EstadoEquipo.ACTIVO.value:
            # Actualizar última conexión
            equipo.ultima_conexion = datetime.now().isoformat()
            self._guardar_equipos()
            return True

        return False

    def _obtener_ip_local(self) -> str:
        """Obtiene la IP local del equipo"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    # ═══════════════════════════════════════════════════════════
    # CONFIGURACIÓN DE DESPLIEGUE
    # ═══════════════════════════════════════════════════════════

    def obtener_config_despliegue(self) -> ConfiguracionDespliegue:
        """Obtiene la configuración de despliegue actual"""
        return self.config

    def actualizar_config_despliegue(self, **kwargs) -> bool:
        """
        Actualiza la configuración de despliegue.

        Args:
            **kwargs: Campos a actualizar

        Returns:
            True si se actualizó correctamente
        """
        try:
            for key, value in kwargs.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)

            self._guardar_config()

            self._registrar_auditoria(
                accion="ACTUALIZAR_CONFIG",
                modulo="admin_config",
                resultado="OK",
                detalles=f"Campos actualizados: {list(kwargs.keys())}"
            )

            return True
        except Exception as e:
            logger.error(f"Error actualizando configuración: {e}")
            return False

    def generar_script_despliegue(self, destino: Path) -> bool:
        """
        Genera un script de despliegue personalizado.

        Args:
            destino: Ruta donde guardar el script

        Returns:
            True si se generó correctamente
        """
        try:
            script_content = self._crear_contenido_script()

            with open(destino, 'w', encoding='utf-8') as f:
                f.write(script_content)

            logger.info(f"Script de despliegue generado: {destino}")
            return True
        except Exception as e:
            logger.error(f"Error generando script: {e}")
            return False

    def _crear_contenido_script(self) -> str:
        """Crea el contenido del script de despliegue"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        service_cmd = "python deploy\\sac_windows_service.py install" if self.config.service_auto_start else "REM Servicio no configurado"

        return f'''@echo off
REM ═══════════════════════════════════════════════════════════════
REM Script de Despliegue SAC - CEDIS {self.config.cedis_code}
REM Generado: {timestamp}
REM ═══════════════════════════════════════════════════════════════

echo Instalando SAC en {self.config.install_base_path}...

REM Crear directorio de instalación
if not exist "{self.config.install_base_path}" mkdir "{self.config.install_base_path}"

REM Copiar archivos (ajustar ruta de origen)
REM xcopy /E /I /Y "\\\\servidor\\\\share\\\\SAC" "{self.config.install_base_path}"

REM Instalar dependencias
cd /d "{self.config.install_base_path}"
python -m pip install -r requirements.txt --quiet

REM Configurar servicio (si está habilitado)
{service_cmd}

echo Instalación completada.
pause
'''

    # ═══════════════════════════════════════════════════════════
    # AUDITORÍA
    # ═══════════════════════════════════════════════════════════

    def _registrar_auditoria(
        self,
        accion: str,
        modulo: str,
        resultado: str,
        detalles: str = "",
        nivel: str = "INFO"
    ):
        """Registra una entrada de auditoría"""
        registro = RegistroAuditoria(
            hostname=socket.gethostname(),
            usuario=os.environ.get('USERNAME', 'unknown'),
            accion=accion,
            modulo=modulo,
            resultado=resultado,
            detalles=detalles,
            nivel=nivel
        )

        # Cargar registros existentes
        registros = []
        if self.audit_file.exists():
            try:
                with open(self.audit_file, 'r', encoding='utf-8') as f:
                    registros = json.load(f)
            except Exception:
                registros = []

        # Añadir nuevo registro
        registros.append(asdict(registro))

        # Mantener solo últimos 1000 registros
        if len(registros) > 1000:
            registros = registros[-1000:]

        # Guardar
        try:
            with open(self.audit_file, 'w', encoding='utf-8') as f:
                json.dump(registros, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error guardando auditoría: {e}")

    def obtener_logs_auditoria(
        self,
        limite: int = 100,
        nivel_minimo: Optional[str] = None
    ) -> List[Dict]:
        """
        Obtiene los registros de auditoría.

        Args:
            limite: Número máximo de registros a devolver
            nivel_minimo: Filtrar por nivel mínimo

        Returns:
            Lista de registros de auditoría
        """
        if not self.audit_file.exists():
            return []

        try:
            with open(self.audit_file, 'r', encoding='utf-8') as f:
                registros = json.load(f)

            if nivel_minimo:
                niveles = ["INFO", "WARNING", "ERROR", "CRITICAL", "AUDIT"]
                idx = niveles.index(nivel_minimo) if nivel_minimo in niveles else 0
                registros = [r for r in registros if niveles.index(r.get('nivel', 'INFO')) >= idx]

            return registros[-limite:]
        except Exception as e:
            logger.error(f"Error leyendo auditoría: {e}")
            return []

    # ═══════════════════════════════════════════════════════════
    # UTILIDADES
    # ═══════════════════════════════════════════════════════════

    def generar_reporte_estado(self) -> Dict[str, Any]:
        """
        Genera un reporte del estado actual del sistema.

        Returns:
            Diccionario con el estado del sistema
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "cedis": {
                "codigo": self.config.cedis_code,
                "nombre": self.config.cedis_name,
                "region": self.config.cedis_region
            },
            "equipo_actual": {
                "hostname": socket.gethostname(),
                "ip": self._obtener_ip_local(),
                "autorizado": self.verificar_equipo_autorizado()
            },
            "equipos_registrados": {
                "total": len(self.equipos),
                "activos": len([e for e in self.equipos.values() if e.estado == "activo"]),
                "inactivos": len([e for e in self.equipos.values() if e.estado != "activo"])
            },
            "configuracion": {
                "ruta_instalacion": self.config.install_base_path,
                "servicio": self.config.service_name,
                "auto_start": self.config.service_auto_start
            }
        }

    def exportar_configuracion(self, destino: Path) -> bool:
        """
        Exporta toda la configuración a un archivo.

        Args:
            destino: Ruta del archivo de destino

        Returns:
            True si se exportó correctamente
        """
        try:
            export_data = {
                "version": "2.0.0",
                "exportado": datetime.now().isoformat(),
                "configuracion": self.config.to_dict(),
                "equipos": {k: asdict(v) for k, v in self.equipos.items()}
            }

            with open(destino, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Configuración exportada a: {destino}")
            return True
        except Exception as e:
            logger.error(f"Error exportando: {e}")
            return False

    def importar_configuracion(self, origen: Path) -> bool:
        """
        Importa configuración desde un archivo.

        Args:
            origen: Ruta del archivo de origen

        Returns:
            True si se importó correctamente
        """
        try:
            with open(origen, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if "configuracion" in data:
                self.config = ConfiguracionDespliegue.from_dict(data["configuracion"])
                self._guardar_config()

            if "equipos" in data:
                self.equipos = {
                    k: EquipoRegistrado(**v)
                    for k, v in data["equipos"].items()
                }
                self._guardar_equipos()

            logger.info(f"Configuración importada desde: {origen}")
            return True
        except Exception as e:
            logger.error(f"Error importando: {e}")
            return False


# ═══════════════════════════════════════════════════════════════
# FUNCIONES DE CONVENIENCIA
# ═══════════════════════════════════════════════════════════════

def obtener_administrador() -> AdministradorSAC:
    """Obtiene una instancia del administrador SAC"""
    return AdministradorSAC()


def verificar_autorizacion() -> bool:
    """Verifica si el equipo actual está autorizado"""
    admin = AdministradorSAC()
    return admin.verificar_equipo_autorizado()


def registrar_equipo_actual(rol: str = "consulta") -> bool:
    """Registra el equipo actual con el rol especificado"""
    admin = AdministradorSAC()
    try:
        rol_enum = RolUsuario(rol)
        admin.registrar_equipo_actual(rol_enum)
        return True
    except ValueError:
        logger.error(f"Rol inválido: {rol}")
        return False


# ═══════════════════════════════════════════════════════════════
# PUNTO DE ENTRADA
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    print("═" * 60)
    print("SAC - Módulo de Configuración Administrativa")
    print("═" * 60)

    admin = AdministradorSAC()

    # Mostrar estado actual
    reporte = admin.generar_reporte_estado()

    print(f"\nCEDIS: {reporte['cedis']['nombre']} ({reporte['cedis']['codigo']})")
    print(f"Equipo: {reporte['equipo_actual']['hostname']}")
    print(f"IP: {reporte['equipo_actual']['ip']}")
    print(f"Autorizado: {'✓' if reporte['equipo_actual']['autorizado'] else '✗'}")
    print(f"\nEquipos registrados: {reporte['equipos_registrados']['total']}")
    print(f"  - Activos: {reporte['equipos_registrados']['activos']}")
    print(f"  - Inactivos: {reporte['equipos_registrados']['inactivos']}")

    # Si no está registrado, registrar
    if not reporte['equipo_actual']['autorizado']:
        print("\nRegistrando equipo actual...")
        admin.registrar_equipo_actual(RolUsuario.ADMINISTRADOR)
        print("Equipo registrado correctamente")

    print("\n" + "═" * 60)
