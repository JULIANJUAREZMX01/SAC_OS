"""
═══════════════════════════════════════════════════════════════
AGENTE SAC - ASISTENTE VIRTUAL INTELIGENTE
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

El Agente SAC es un asistente virtual local con capacidades de:
- Ejecución de scripts y comandos en consola
- Integración completa con el sistema SAC
- Asistente de configuraciones y resolución de problemas
- Primera línea de defensa e intermediario del equipo de sistemas
- Sistema de respuestas rápidas con comando "/"
- Aprendizaje por usuario de red
- Inteligencia Artificial con Ollama/Llama 3

IDENTIDAD:
    Creado con orgullo por el equipo de Sistemas del CEDIS 427
    Liderado por Julián Alexander Juárez Alvarado (ADMJAJA)
    Jefe de Sistemas - CEDIS Chedraui Logística Cancún

FILOSOFÍA:
    "Las máquinas y los sistemas al servicio de los analistas"

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════
"""

import os
import json
import logging
import subprocess
import hashlib
import getpass
import socket
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
import threading
import time

# Configuración del logger
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# CONSTANTES DEL AGENTE
# ═══════════════════════════════════════════════════════════════

# Versión del Agente SAC
AGENTE_VERSION = "1.0.0"
AGENTE_CODENAME = "Godí"
AGENTE_BUILD_DATE = "2025-11-22"

# Identificadores del creador
CREADOR = {
    'nombre_completo': 'Julián Alexander Juárez Alvarado',
    'codigo': 'ADMJAJA',
    'cargo': 'Jefe de Sistemas',
    'cedis': 'CEDIS Cancún 427',
    'organizacion': 'Tiendas Chedraui S.A. de C.V.',
    'region': 'Sureste',
}

# Equipo de desarrollo
EQUIPO_SISTEMAS = {
    'lider': CREADOR,
    'analistas': [
        {'nombre': 'Larry Adanael Basto Díaz', 'cargo': 'Analista de Sistemas'},
        {'nombre': 'Adrian Quintana Zuñiga', 'cargo': 'Analista de Sistemas'},
    ],
    'supervisor_regional': {
        'nombre': 'Itza Vera Reyes Sarubí',
        'ubicacion': 'Villahermosa',
    }
}

# Usuario administrador de red con acceso completo
ADMIN_USUARIO = 'u427jd15'
ADMIN_DESCRIPCION = 'Administrador de la red GCH'

# Rutas de datos del agente
try:
    from config import PATHS, CEDIS
    AGENTE_DATA_DIR = PATHS['output'] / 'agente_sac'
except ImportError:
    AGENTE_DATA_DIR = Path(__file__).parent.parent / 'output' / 'agente_sac'
    CEDIS = {'code': '427', 'name': 'CEDIS Cancún', 'region': 'Sureste'}

# Crear directorio de datos si no existe
AGENTE_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Importar módulo de IA (carga tardía para evitar dependencias circulares)
_motor_ia = None

def _obtener_motor_ia():
    """Obtiene el motor de IA de forma tardía"""
    global _motor_ia
    if _motor_ia is None:
        try:
            from .agente_ia import obtener_motor_ia, TipoConsulta
            _motor_ia = obtener_motor_ia()
        except ImportError:
            logger.warning("⚠️ Módulo de IA no disponible")
            _motor_ia = False
    return _motor_ia if _motor_ia else None


# ═══════════════════════════════════════════════════════════════
# ENUMERACIONES
# ═══════════════════════════════════════════════════════════════

class NivelAcceso(Enum):
    """Niveles de acceso al Agente SAC"""
    ADMIN = "admin"           # Acceso completo CLI - solo u427jd15
    SISTEMAS = "sistemas"     # Equipo de sistemas - acceso avanzado
    USUARIO = "usuario"       # Usuarios de red - asistente básico
    INVITADO = "invitado"     # Acceso mínimo


class CategoriaRespuesta(Enum):
    """Categorías de respuestas rápidas"""
    SOPORTE = "soporte"
    CONFIGURACION = "configuracion"
    AYUDA = "ayuda"
    SAC = "sac"
    RECORDATORIO = "recordatorio"
    SISTEMA = "sistema"
    CUSTOM = "custom"


class EstadoAgente(Enum):
    """Estados del agente"""
    ACTIVO = "activo"
    OCUPADO = "ocupado"
    MANTENIMIENTO = "mantenimiento"
    INACTIVO = "inactivo"


class TipoInteraccion(Enum):
    """Tipos de interacción con el agente"""
    COMANDO = "comando"
    RESPUESTA_RAPIDA = "respuesta_rapida"
    CONSULTA = "consulta"
    SCRIPT = "script"
    CONFIGURACION = "configuracion"


# ═══════════════════════════════════════════════════════════════
# DATACLASSES
# ═══════════════════════════════════════════════════════════════

@dataclass
class UsuarioAgente:
    """Representa un usuario del Agente SAC"""
    username: str
    nivel_acceso: NivelAcceso
    nombre_display: str = ""
    area: str = ""
    ultimo_acceso: Optional[datetime] = None
    total_interacciones: int = 0
    respuestas_favoritas: List[str] = field(default_factory=list)
    preferencias: Dict[str, Any] = field(default_factory=dict)
    historial_consultas: List[Dict] = field(default_factory=list)
    fecha_registro: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        """Convierte a diccionario para serialización"""
        return {
            'username': self.username,
            'nivel_acceso': self.nivel_acceso.value,
            'nombre_display': self.nombre_display,
            'area': self.area,
            'ultimo_acceso': self.ultimo_acceso.isoformat() if self.ultimo_acceso else None,
            'total_interacciones': self.total_interacciones,
            'respuestas_favoritas': self.respuestas_favoritas,
            'preferencias': self.preferencias,
            'fecha_registro': self.fecha_registro.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'UsuarioAgente':
        """Crea instancia desde diccionario"""
        return cls(
            username=data['username'],
            nivel_acceso=NivelAcceso(data['nivel_acceso']),
            nombre_display=data.get('nombre_display', ''),
            area=data.get('area', ''),
            ultimo_acceso=datetime.fromisoformat(data['ultimo_acceso']) if data.get('ultimo_acceso') else None,
            total_interacciones=data.get('total_interacciones', 0),
            respuestas_favoritas=data.get('respuestas_favoritas', []),
            preferencias=data.get('preferencias', {}),
            fecha_registro=datetime.fromisoformat(data['fecha_registro']) if data.get('fecha_registro') else datetime.now(),
        )


@dataclass
class RespuestaRapida:
    """Respuesta rápida para el baúl de comandos /"""
    comando: str
    titulo: str
    contenido: str
    categoria: CategoriaRespuesta
    palabras_clave: List[str] = field(default_factory=list)
    uso_count: int = 0
    creado_por: str = "sistema"
    fecha_creacion: datetime = field(default_factory=datetime.now)
    activo: bool = True

    def to_dict(self) -> Dict:
        """Convierte a diccionario"""
        return {
            'comando': self.comando,
            'titulo': self.titulo,
            'contenido': self.contenido,
            'categoria': self.categoria.value,
            'palabras_clave': self.palabras_clave,
            'uso_count': self.uso_count,
            'creado_por': self.creado_por,
            'fecha_creacion': self.fecha_creacion.isoformat(),
            'activo': self.activo,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'RespuestaRapida':
        """Crea instancia desde diccionario"""
        return cls(
            comando=data['comando'],
            titulo=data['titulo'],
            contenido=data['contenido'],
            categoria=CategoriaRespuesta(data['categoria']),
            palabras_clave=data.get('palabras_clave', []),
            uso_count=data.get('uso_count', 0),
            creado_por=data.get('creado_por', 'sistema'),
            fecha_creacion=datetime.fromisoformat(data['fecha_creacion']) if data.get('fecha_creacion') else datetime.now(),
            activo=data.get('activo', True),
        )


@dataclass
class Recordatorio:
    """Recordatorio para usuarios"""
    id: str
    usuario: str
    mensaje: str
    fecha_hora: datetime
    repetir: bool = False
    intervalo_dias: int = 0
    completado: bool = False
    creado: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'usuario': self.usuario,
            'mensaje': self.mensaje,
            'fecha_hora': self.fecha_hora.isoformat(),
            'repetir': self.repetir,
            'intervalo_dias': self.intervalo_dias,
            'completado': self.completado,
            'creado': self.creado.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Recordatorio':
        return cls(
            id=data['id'],
            usuario=data['usuario'],
            mensaje=data['mensaje'],
            fecha_hora=datetime.fromisoformat(data['fecha_hora']),
            repetir=data.get('repetir', False),
            intervalo_dias=data.get('intervalo_dias', 0),
            completado=data.get('completado', False),
            creado=datetime.fromisoformat(data['creado']) if data.get('creado') else datetime.now(),
        )


@dataclass
class ResultadoComando:
    """Resultado de ejecución de comando/script"""
    exito: bool
    salida: str
    error: str = ""
    codigo_retorno: int = 0
    tiempo_ejecucion: float = 0.0
    comando: str = ""
    timestamp: datetime = field(default_factory=datetime.now)


# ═══════════════════════════════════════════════════════════════
# RESPUESTAS RÁPIDAS PREDEFINIDAS
# ═══════════════════════════════════════════════════════════════

RESPUESTAS_PREDEFINIDAS: List[Dict] = [
    # Soporte técnico
    {
        'comando': 'limpiar_cache',
        'titulo': 'Limpiar caché del navegador',
        'contenido': '''🧹 **Limpiar Caché del Navegador**

**Chrome/Edge:**
1. Presiona Ctrl + Shift + Delete
2. Selecciona "Todo el tiempo"
3. Marca "Imágenes y archivos en caché"
4. Clic en "Borrar datos"

**Alternativa rápida:** Ctrl + F5 para recargar sin caché''',
        'categoria': 'soporte',
        'palabras_clave': ['cache', 'lento', 'navegador', 'limpiar'],
    },
    {
        'comando': 'reiniciar_impresora',
        'titulo': 'Reiniciar cola de impresión',
        'contenido': '''🖨️ **Reiniciar Cola de Impresión**

1. Presiona Win + R
2. Escribe: services.msc
3. Busca "Cola de impresión"
4. Clic derecho → Reiniciar

**O desde CMD como admin:**
```
net stop spooler && net start spooler
```''',
        'categoria': 'soporte',
        'palabras_clave': ['impresora', 'cola', 'atascado', 'imprimir'],
    },
    {
        'comando': 'red_diagnostico',
        'titulo': 'Diagnóstico de red',
        'contenido': '''🌐 **Diagnóstico Rápido de Red**

**Verificar conectividad:**
```
ping google.com
ping WM260BASD
```

**Ver IP actual:**
```
ipconfig
```

**Renovar IP:**
```
ipconfig /release
ipconfig /renew
```

**Si persiste el problema, contacta a Sistemas.**''',
        'categoria': 'soporte',
        'palabras_clave': ['red', 'internet', 'conexion', 'ip'],
    },

    # SAC
    {
        'comando': 'sac_ayuda',
        'titulo': 'Ayuda del Sistema SAC',
        'contenido': '''📊 **Sistema SAC - Ayuda Rápida**

**¿Qué es el SAC?**
Sistema de Automatización de Consultas para el departamento de Planning.

**Funciones principales:**
- ✅ Validación de Órdenes de Compra
- 📋 Validación de Distribuciones
- 📈 Generación de reportes Excel
- 📧 Envío de alertas por correo
- 🔍 Monitoreo en tiempo real

**Comandos disponibles:**
- /sac_validar - Validar OC
- /sac_reporte - Generar reporte
- /sac_estado - Estado del sistema''',
        'categoria': 'sac',
        'palabras_clave': ['sac', 'ayuda', 'planning', 'sistema'],
    },
    {
        'comando': 'sac_validar',
        'titulo': 'Validar Orden de Compra',
        'contenido': '''✅ **Validar Orden de Compra en SAC**

**Desde línea de comandos:**
```
python main.py --oc OC12345
```

**Desde menú interactivo:**
1. Ejecuta: python main.py
2. Selecciona opción 1
3. Ingresa número de OC

**Resultado esperado:**
- Validación de existencia
- Comparación con distribuciones
- Detección de discrepancias''',
        'categoria': 'sac',
        'palabras_clave': ['validar', 'oc', 'orden', 'compra'],
    },
    {
        'comando': 'sac_reporte',
        'titulo': 'Generar reporte diario',
        'contenido': '''📈 **Generar Reporte Diario SAC**

**Comando:**
```
python main.py --reporte-diario
```

**El reporte incluye:**
- Resumen ejecutivo
- OC procesadas
- Distribuciones validadas
- Errores detectados
- Estadísticas del día

**Ubicación:** output/resultados/''',
        'categoria': 'sac',
        'palabras_clave': ['reporte', 'diario', 'excel', 'generar'],
    },

    # Configuración
    {
        'comando': 'config_env',
        'titulo': 'Configurar archivo .env',
        'contenido': '''⚙️ **Configurar Variables de Entorno**

1. Copia el archivo plantilla:
   ```
   cp env .env
   ```

2. Edita .env con tus credenciales:
   ```
   DB_USER=tu_usuario
   DB_PASSWORD=tu_password
   EMAIL_USER=tu_email@chedraui.com.mx
   EMAIL_PASSWORD=tu_password_email
   ```

3. Verifica la configuración:
   ```
   python config.py
   ```

⚠️ **NUNCA compartas el archivo .env**''',
        'categoria': 'configuracion',
        'palabras_clave': ['env', 'configurar', 'credenciales', 'variables'],
    },
    {
        'comando': 'verificar_sistema',
        'titulo': 'Verificar estado del sistema',
        'contenido': '''🔍 **Verificar Estado del Sistema SAC**

**Ejecuta:**
```
python verificar_sistema.py
```

**Verifica:**
- ✅ Dependencias instaladas
- ✅ Configuración válida
- ✅ Conectividad a BD
- ✅ Configuración de email
- ✅ Directorios necesarios

**Si hay errores, contacta a Sistemas del 427.**''',
        'categoria': 'configuracion',
        'palabras_clave': ['verificar', 'estado', 'sistema', 'check'],
    },

    # Ayuda general
    {
        'comando': 'contacto_sistemas',
        'titulo': 'Contacto del equipo de Sistemas',
        'contenido': '''📞 **Contacto - Equipo de Sistemas CEDIS 427**

**Jefe de Sistemas:**
👤 Julián Alexander Juárez Alvarado (ADMJAJA)
📧 admjaja@chedraui.com.mx

**Analistas de Sistemas:**
👤 Larry Adanael Basto Díaz
👤 Adrian Quintana Zuñiga

**Supervisor Regional:**
👤 Itza Vera Reyes Sarubí (Villahermosa)

**Horario de atención:**
🕐 Lunes a Viernes: 8:00 - 18:00
🕐 Sábados: 8:00 - 14:00''',
        'categoria': 'ayuda',
        'palabras_clave': ['contacto', 'sistemas', 'soporte', 'telefono'],
    },
    {
        'comando': 'acerca',
        'titulo': 'Acerca del Agente SAC',
        'contenido': '''🤖 **Agente SAC - "Godí"**

**Versión:** {version}
**Build:** {build_date}

Soy el Agente SAC, tu asistente virtual del CEDIS 427.
Fui creado con orgullo por el equipo de Sistemas.

**Mi creador:**
👨‍💻 Julián Alexander Juárez Alvarado (ADMJAJA)
🏢 Jefe de Sistemas - CEDIS Cancún 427
🏪 Tiendas Chedraui S.A. de C.V.

**Mi misión:**
Servir como primera línea de defensa y guía para todos
los colaboradores, haciendo su trabajo más fácil.

**Filosofía:**
"Las máquinas y los sistemas al servicio de los analistas"

**Comandos:** Escribe / para ver respuestas rápidas''',
        'categoria': 'sistema',
        'palabras_clave': ['acerca', 'agente', 'sac', 'godi', 'quien'],
    },
    {
        'comando': 'comandos',
        'titulo': 'Lista de comandos disponibles',
        'contenido': '''📋 **Comandos Disponibles**

**Soporte:**
/limpiar_cache - Limpiar caché del navegador
/reiniciar_impresora - Reiniciar cola de impresión
/red_diagnostico - Diagnóstico de red

**SAC:**
/sac_ayuda - Ayuda del sistema SAC
/sac_validar - Validar Orden de Compra
/sac_reporte - Generar reporte diario

**Configuración:**
/config_env - Configurar archivo .env
/verificar_sistema - Verificar estado

**Ayuda:**
/contacto_sistemas - Contacto del equipo
/acerca - Acerca del Agente SAC
/comandos - Esta lista

Escribe / seguido del comando para ejecutar.''',
        'categoria': 'ayuda',
        'palabras_clave': ['comandos', 'lista', 'ayuda', 'menu'],
    },
]


# ═══════════════════════════════════════════════════════════════
# CLASE PRINCIPAL: AGENTE SAC
# ═══════════════════════════════════════════════════════════════

class AgenteSAC:
    """
    Agente SAC - Asistente Virtual Inteligente del CEDIS 427

    Creado con orgullo por el equipo de Sistemas del almacén 427,
    liderado por Julián Alexander Juárez Alvarado (ADMJAJA).

    Características:
    - Ejecución de scripts y comandos (solo admin)
    - Sistema de respuestas rápidas con "/"
    - Aprendizaje por usuario
    - Recordatorios
    - Integración con SAC
    """

    def __init__(self, data_dir: Path = None):
        """
        Inicializa el Agente SAC

        Args:
            data_dir: Directorio para almacenar datos del agente
        """
        self.data_dir = data_dir or AGENTE_DATA_DIR
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Archivos de datos
        self.usuarios_file = self.data_dir / 'usuarios.json'
        self.respuestas_file = self.data_dir / 'respuestas.json'
        self.recordatorios_file = self.data_dir / 'recordatorios.json'
        self.aprendizaje_file = self.data_dir / 'aprendizaje.json'
        self.log_file = self.data_dir / 'agente.log'

        # Estado del agente
        self.estado = EstadoAgente.ACTIVO
        self.usuario_actual: Optional[UsuarioAgente] = None
        self.sesion_inicio: datetime = datetime.now()

        # Cargar datos
        self.usuarios: Dict[str, UsuarioAgente] = {}
        self.respuestas: Dict[str, RespuestaRapida] = {}
        self.recordatorios: List[Recordatorio] = []
        self.aprendizaje: Dict[str, Dict] = {}

        # Inicializar
        self._cargar_datos()
        self._inicializar_respuestas_predefinidas()

        logger.info(f"🤖 Agente SAC v{AGENTE_VERSION} inicializado")

    # ═══════════════════════════════════════════════════════════
    # IDENTIDAD Y PRESENTACIÓN
    # ═══════════════════════════════════════════════════════════

    def obtener_identidad(self) -> Dict:
        """Retorna la identidad completa del agente"""
        return {
            'nombre': 'Agente SAC',
            'codename': AGENTE_CODENAME,
            'version': AGENTE_VERSION,
            'build_date': AGENTE_BUILD_DATE,
            'creador': CREADOR,
            'equipo': EQUIPO_SISTEMAS,
            'cedis': CEDIS,
            'filosofia': 'Las máquinas y los sistemas al servicio de los analistas',
            'estado': self.estado.value,
        }

    def presentarse(self, nivel_detalle: str = 'normal') -> str:
        """
        Genera una presentación del agente

        Args:
            nivel_detalle: 'breve', 'normal', 'completo'
        """
        if nivel_detalle == 'breve':
            return f"🤖 Soy el Agente SAC ({AGENTE_CODENAME}), tu asistente del CEDIS 427."

        elif nivel_detalle == 'normal':
            return f"""
╔══════════════════════════════════════════════════════════════╗
║  🤖 AGENTE SAC - "{AGENTE_CODENAME}"                         ║
║  Asistente Virtual del CEDIS 427                             ║
╠══════════════════════════════════════════════════════════════╣
║  Versión: {AGENTE_VERSION}                                   ║
║  Estado: {self.estado.value.upper()}                         ║
║                                                              ║
║  Creado por: {CREADOR['nombre_completo']}                    ║
║  ({CREADOR['codigo']}) - {CREADOR['cargo']}                  ║
║                                                              ║
║  Escribe "/" para ver comandos disponibles                   ║
╚══════════════════════════════════════════════════════════════╝
"""

        else:  # completo
            return f"""
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║      🤖 AGENTE SAC - "{AGENTE_CODENAME}"                             ║
║      Sistema de Asistencia Virtual Inteligente                       ║
║                                                                      ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║  📋 INFORMACIÓN DEL SISTEMA                                          ║
║  ─────────────────────────────────────────────────────────────────── ║
║  Versión:      {AGENTE_VERSION}                                      ║
║  Build:        {AGENTE_BUILD_DATE}                                   ║
║  Estado:       {self.estado.value.upper()}                           ║
║  Ubicación:    {CEDIS.get('name', 'CEDIS 427')}                      ║
║  Región:       {CEDIS.get('region', 'Sureste')}                      ║
║                                                                      ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║  👨‍💻 CREADOR                                                         ║
║  ─────────────────────────────────────────────────────────────────── ║
║  {CREADOR['nombre_completo']}                                        ║
║  Código: {CREADOR['codigo']}                                         ║
║  Cargo:  {CREADOR['cargo']}                                          ║
║  CEDIS:  {CREADOR['cedis']}                                          ║
║  Org:    {CREADOR['organizacion']}                                   ║
║                                                                      ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║  👥 EQUIPO DE SISTEMAS                                               ║
║  ─────────────────────────────────────────────────────────────────── ║
║  • Larry Adanael Basto Díaz      - Analista de Sistemas              ║
║  • Adrian Quintana Zuñiga        - Analista de Sistemas              ║
║  • Itza Vera Reyes Sarubí        - Supervisor Regional               ║
║                                                                      ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║  💡 FILOSOFÍA                                                        ║
║  "Las máquinas y los sistemas al servicio de los analistas"         ║
║                                                                      ║
║  🎯 MISIÓN                                                           ║
║  Servir como primera línea de defensa, guía y asistente para        ║
║  todos los colaboradores del CEDIS 427, facilitando su trabajo      ║
║  diario y resolviendo dudas de manera eficiente.                    ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝

Escribe "/" seguido de un comando para acceder a respuestas rápidas.
Escribe "/comandos" para ver la lista completa.
"""

    def agradecer_creador(self) -> str:
        """Mensaje de agradecimiento al creador"""
        return f"""
🙏 Este sistema fue desarrollado con dedicación por:

   👨‍💻 {CREADOR['nombre_completo']} ({CREADOR['codigo']})
   📍 {CREADOR['cargo']} - {CREADOR['cedis']}
   🏪 {CREADOR['organizacion']}

   Con el apoyo del equipo de Sistemas:
   • Larry Adanael Basto Díaz
   • Adrian Quintana Zuñiga

   Y la supervisión de:
   • Itza Vera Reyes Sarubí (Regional Villahermosa)

"Cada función, validación y reporte fue diseñado para hacer
el trabajo más fácil y eficiente para todos los analistas."

¡Gracias por usar el Agente SAC! 🚀
"""

    # ═══════════════════════════════════════════════════════════
    # GESTIÓN DE USUARIOS Y ACCESO
    # ═══════════════════════════════════════════════════════════

    def identificar_usuario(self, username: str = None) -> UsuarioAgente:
        """
        Identifica al usuario actual y determina su nivel de acceso

        Args:
            username: Nombre de usuario (si None, detecta automáticamente)

        Returns:
            UsuarioAgente con el nivel de acceso correspondiente
        """
        if username is None:
            username = getpass.getuser().lower()
        else:
            username = username.lower()

        # Determinar nivel de acceso
        if username == ADMIN_USUARIO.lower():
            nivel = NivelAcceso.ADMIN
            logger.info(f"🔑 Usuario administrador identificado: {username}")
        elif username.startswith('adm') or username in ['larry', 'adrian']:
            nivel = NivelAcceso.SISTEMAS
            logger.info(f"💻 Usuario de sistemas identificado: {username}")
        else:
            nivel = NivelAcceso.USUARIO
            logger.info(f"👤 Usuario de red identificado: {username}")

        # Buscar o crear usuario
        if username in self.usuarios:
            usuario = self.usuarios[username]
            usuario.ultimo_acceso = datetime.now()
            usuario.total_interacciones += 1
        else:
            usuario = UsuarioAgente(
                username=username,
                nivel_acceso=nivel,
                ultimo_acceso=datetime.now(),
                total_interacciones=1,
            )
            self.usuarios[username] = usuario
            logger.info(f"📝 Nuevo usuario registrado: {username}")

        self.usuario_actual = usuario
        self._guardar_usuarios()

        return usuario

    def verificar_permiso(self, accion: str) -> Tuple[bool, str]:
        """
        Verifica si el usuario actual tiene permiso para una acción

        Args:
            accion: Tipo de acción a verificar

        Returns:
            Tuple (tiene_permiso, mensaje)
        """
        if self.usuario_actual is None:
            return False, "❌ Usuario no identificado. Ejecuta identificar_usuario() primero."

        nivel = self.usuario_actual.nivel_acceso

        # Acciones por nivel
        permisos = {
            'ejecutar_script': [NivelAcceso.ADMIN],
            'ejecutar_comando': [NivelAcceso.ADMIN],
            'configurar_sistema': [NivelAcceso.ADMIN, NivelAcceso.SISTEMAS],
            'ver_logs': [NivelAcceso.ADMIN, NivelAcceso.SISTEMAS],
            'crear_respuesta': [NivelAcceso.ADMIN, NivelAcceso.SISTEMAS],
            'eliminar_respuesta': [NivelAcceso.ADMIN],
            'ver_usuarios': [NivelAcceso.ADMIN, NivelAcceso.SISTEMAS],
            'usar_respuestas': [NivelAcceso.ADMIN, NivelAcceso.SISTEMAS, NivelAcceso.USUARIO],
            'crear_recordatorio': [NivelAcceso.ADMIN, NivelAcceso.SISTEMAS, NivelAcceso.USUARIO],
            'consultar': [NivelAcceso.ADMIN, NivelAcceso.SISTEMAS, NivelAcceso.USUARIO, NivelAcceso.INVITADO],
        }

        niveles_permitidos = permisos.get(accion, [])

        if nivel in niveles_permitidos:
            return True, f"✅ Permiso concedido para: {accion}"
        else:
            return False, f"🚫 Sin permiso para: {accion}. Requiere: {[n.value for n in niveles_permitidos]}"

    def es_admin(self) -> bool:
        """Verifica si el usuario actual es administrador"""
        return self.usuario_actual and self.usuario_actual.nivel_acceso == NivelAcceso.ADMIN

    def es_sistemas(self) -> bool:
        """Verifica si el usuario actual es del equipo de sistemas"""
        return self.usuario_actual and self.usuario_actual.nivel_acceso in [NivelAcceso.ADMIN, NivelAcceso.SISTEMAS]

    # ═══════════════════════════════════════════════════════════
    # SISTEMA DE RESPUESTAS RÁPIDAS (/)
    # ═══════════════════════════════════════════════════════════

    def _inicializar_respuestas_predefinidas(self):
        """Inicializa las respuestas rápidas predefinidas"""
        for resp_data in RESPUESTAS_PREDEFINIDAS:
            comando = resp_data['comando']
            if comando not in self.respuestas:
                # Reemplazar variables en contenido
                contenido = resp_data['contenido'].format(
                    version=AGENTE_VERSION,
                    build_date=AGENTE_BUILD_DATE,
                )

                self.respuestas[comando] = RespuestaRapida(
                    comando=comando,
                    titulo=resp_data['titulo'],
                    contenido=contenido,
                    categoria=CategoriaRespuesta(resp_data['categoria']),
                    palabras_clave=resp_data.get('palabras_clave', []),
                )

        self._guardar_respuestas()

    def procesar_comando_rapido(self, entrada: str) -> Optional[str]:
        """
        Procesa un comando rápido que inicia con "/"

        Args:
            entrada: Texto ingresado por el usuario

        Returns:
            Contenido de la respuesta o None si no es comando
        """
        if not entrada.startswith('/'):
            return None

        comando = entrada[1:].strip().lower()

        # Comando vacío - mostrar lista
        if not comando:
            return self._listar_comandos()

        # Buscar comando exacto
        if comando in self.respuestas:
            respuesta = self.respuestas[comando]
            respuesta.uso_count += 1
            self._guardar_respuestas()

            # Registrar en aprendizaje
            self._registrar_uso(comando)

            return respuesta.contenido

        # Buscar por palabras clave
        for cmd, resp in self.respuestas.items():
            if comando in resp.palabras_clave or any(kw in comando for kw in resp.palabras_clave):
                resp.uso_count += 1
                self._guardar_respuestas()
                return f"🔍 Encontré: /{cmd}\n\n{resp.contenido}"

        # No encontrado
        return f"❌ Comando '/{comando}' no encontrado.\n\nEscribe / para ver comandos disponibles."

    def _listar_comandos(self) -> str:
        """Lista todos los comandos disponibles"""
        lineas = ["📋 **Comandos Disponibles**\n"]

        # Agrupar por categoría
        por_categoria: Dict[str, List[RespuestaRapida]] = {}
        for resp in self.respuestas.values():
            if resp.activo:
                cat = resp.categoria.value.title()
                if cat not in por_categoria:
                    por_categoria[cat] = []
                por_categoria[cat].append(resp)

        for categoria, respuestas in sorted(por_categoria.items()):
            lineas.append(f"\n**{categoria}:**")
            for resp in sorted(respuestas, key=lambda x: x.comando):
                lineas.append(f"  /{resp.comando} - {resp.titulo}")

        lineas.append("\n💡 Escribe /<comando> para ver el contenido.")

        return '\n'.join(lineas)

    def agregar_respuesta(
        self,
        comando: str,
        titulo: str,
        contenido: str,
        categoria: str = 'custom',
        palabras_clave: List[str] = None
    ) -> Tuple[bool, str]:
        """
        Agrega una nueva respuesta rápida

        Solo disponible para administrador y equipo de sistemas
        """
        permitido, msg = self.verificar_permiso('crear_respuesta')
        if not permitido:
            return False, msg

        comando = comando.lower().strip()

        if comando in self.respuestas:
            return False, f"❌ El comando '/{comando}' ya existe."

        self.respuestas[comando] = RespuestaRapida(
            comando=comando,
            titulo=titulo,
            contenido=contenido,
            categoria=CategoriaRespuesta(categoria),
            palabras_clave=palabras_clave or [],
            creado_por=self.usuario_actual.username if self.usuario_actual else 'sistema',
        )

        self._guardar_respuestas()

        return True, f"✅ Respuesta /{comando} agregada correctamente."

    def buscar_respuestas(self, termino: str) -> List[RespuestaRapida]:
        """Busca respuestas que coincidan con el término"""
        termino = termino.lower()
        resultados = []

        for resp in self.respuestas.values():
            if (termino in resp.comando or
                termino in resp.titulo.lower() or
                termino in resp.contenido.lower() or
                any(termino in kw for kw in resp.palabras_clave)):
                resultados.append(resp)

        return resultados

    # ═══════════════════════════════════════════════════════════
    # INTELIGENCIA ARTIFICIAL (OLLAMA/LLAMA)
    # ═══════════════════════════════════════════════════════════

    def consultar_ia(self, pregunta: str, incluir_contexto: bool = True) -> str:
        """
        Realiza una consulta al motor de IA

        Usa Ollama con modelos Llama 3 para responder preguntas
        complejas que no están en las respuestas rápidas.

        Args:
            pregunta: La pregunta del usuario
            incluir_contexto: Si debe incluir contexto del repositorio SAC

        Returns:
            Respuesta generada por la IA o mensaje de error
        """
        motor = _obtener_motor_ia()

        if motor is None:
            return ("🤖 La IA no está disponible en este momento.\n\n"
                   "Para habilitarla:\n"
                   "1. Instala Ollama: https://ollama.ai/download\n"
                   "2. Ejecuta: ollama serve\n"
                   "3. Descarga un modelo: ollama pull llama3\n\n"
                   "Mientras tanto, puedes usar /comandos para ver las respuestas rápidas.")

        try:
            from .agente_ia import TipoConsulta

            # Determinar tipo de consulta
            pregunta_lower = pregunta.lower()
            if any(kw in pregunta_lower for kw in ['sac', 'validar', 'oc', 'distribución', 'reporte']):
                tipo = TipoConsulta.SAC
            elif any(kw in pregunta_lower for kw in ['código', 'python', 'script', 'función']):
                tipo = TipoConsulta.CODIGO
            elif any(kw in pregunta_lower for kw in ['ayuda', 'soporte', 'error', 'problema']):
                tipo = TipoConsulta.SOPORTE
            else:
                tipo = TipoConsulta.GENERAL

            # Consultar IA
            respuesta = motor.consultar(
                pregunta=pregunta,
                usuario=self.usuario_actual.username if self.usuario_actual else "anonimo",
                tipo=tipo,
                incluir_contexto=incluir_contexto
            )

            if respuesta.exitosa:
                return f"🧠 **Respuesta IA** (Modelo: {respuesta.modelo})\n\n{respuesta.contenido}"
            else:
                return f"❌ Error de IA: {respuesta.error}\n\nIntenta con /comandos para respuestas rápidas."

        except Exception as e:
            logger.error(f"❌ Error consultando IA: {e}")
            return f"❌ Error al consultar la IA: {str(e)}"

    def chat_ia(self, mensaje: str) -> str:
        """
        Mantiene una conversación con la IA

        Args:
            mensaje: Mensaje del usuario

        Returns:
            Respuesta de la IA
        """
        motor = _obtener_motor_ia()

        if motor is None:
            return "🤖 La IA no está disponible. Instala Ollama primero."

        try:
            usuario = self.usuario_actual.username if self.usuario_actual else "anonimo"

            # Obtener o crear ID de conversación
            conv_id = getattr(self, '_conv_id_actual', None)

            respuesta, conv_id = motor.chat(mensaje, usuario, conv_id)

            # Guardar ID de conversación
            self._conv_id_actual = conv_id

            if respuesta.exitosa:
                return respuesta.contenido
            else:
                return f"❌ Error: {respuesta.error}"

        except Exception as e:
            logger.error(f"❌ Error en chat IA: {e}")
            return f"❌ Error: {str(e)}"

    def obtener_estado_ia(self) -> Dict:
        """Obtiene el estado del motor de IA"""
        motor = _obtener_motor_ia()

        if motor is None:
            return {
                'disponible': False,
                'mensaje': 'Motor de IA no inicializado. Instala Ollama.'
            }

        return motor.obtener_estado()

    # ═══════════════════════════════════════════════════════════
    # EJECUCIÓN DE COMANDOS Y SCRIPTS (SOLO ADMIN)
    # ═══════════════════════════════════════════════════════════

    def ejecutar_comando(self, comando: str, timeout: int = 30) -> ResultadoComando:
        """
        Ejecuta un comando en la consola

        SOLO DISPONIBLE PARA ADMINISTRADOR (u427jd15)

        Args:
            comando: Comando a ejecutar
            timeout: Tiempo máximo en segundos

        Returns:
            ResultadoComando con el resultado
        """
        permitido, msg = self.verificar_permiso('ejecutar_comando')
        if not permitido:
            logger.warning(f"🚫 Intento de ejecutar comando sin permiso: {self.usuario_actual}")
            return ResultadoComando(
                exito=False,
                salida='',
                error=msg,
                comando=comando,
            )

        logger.info(f"⚡ Ejecutando comando: {comando}")
        inicio = time.time()

        try:
            resultado = subprocess.run(
                comando,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            tiempo = time.time() - inicio

            return ResultadoComando(
                exito=resultado.returncode == 0,
                salida=resultado.stdout,
                error=resultado.stderr,
                codigo_retorno=resultado.returncode,
                tiempo_ejecucion=tiempo,
                comando=comando,
            )

        except subprocess.TimeoutExpired:
            return ResultadoComando(
                exito=False,
                salida='',
                error=f'Timeout: El comando excedió {timeout} segundos',
                comando=comando,
            )
        except Exception as e:
            logger.error(f"❌ Error ejecutando comando: {e}")
            return ResultadoComando(
                exito=False,
                salida='',
                error=str(e),
                comando=comando,
            )

    def ejecutar_script(self, ruta_script: str, argumentos: List[str] = None) -> ResultadoComando:
        """
        Ejecuta un script Python

        SOLO DISPONIBLE PARA ADMINISTRADOR (u427jd15)

        Args:
            ruta_script: Ruta al archivo Python
            argumentos: Lista de argumentos

        Returns:
            ResultadoComando con el resultado
        """
        permitido, msg = self.verificar_permiso('ejecutar_script')
        if not permitido:
            logger.warning(f"🚫 Intento de ejecutar script sin permiso")
            return ResultadoComando(
                exito=False,
                salida='',
                error=msg,
                comando=f"python {ruta_script}",
            )

        if not Path(ruta_script).exists():
            return ResultadoComando(
                exito=False,
                salida='',
                error=f'Script no encontrado: {ruta_script}',
                comando=f"python {ruta_script}",
            )

        comando = f"python {ruta_script}"
        if argumentos:
            comando += ' ' + ' '.join(argumentos)

        return self.ejecutar_comando(comando)

    def ejecutar_sac(self, accion: str, **kwargs) -> ResultadoComando:
        """
        Ejecuta una acción del sistema SAC

        Acciones disponibles:
        - 'validar_oc': Validar orden de compra
        - 'reporte_diario': Generar reporte diario
        - 'verificar': Verificar sistema
        - 'menu': Abrir menú interactivo

        Args:
            accion: Acción a ejecutar
            **kwargs: Argumentos adicionales
        """
        acciones = {
            'validar_oc': 'python main.py --oc {oc}',
            'reporte_diario': 'python main.py --reporte-diario',
            'verificar': 'python verificar_sistema.py',
            'menu': 'python main.py --menu',
        }

        if accion not in acciones:
            return ResultadoComando(
                exito=False,
                salida='',
                error=f"Acción desconocida: {accion}. Disponibles: {list(acciones.keys())}",
                comando='',
            )

        comando = acciones[accion].format(**kwargs)
        return self.ejecutar_comando(comando)

    # ═══════════════════════════════════════════════════════════
    # SISTEMA DE RECORDATORIOS
    # ═══════════════════════════════════════════════════════════

    def crear_recordatorio(
        self,
        mensaje: str,
        fecha_hora: datetime,
        repetir: bool = False,
        intervalo_dias: int = 0
    ) -> Tuple[bool, str]:
        """
        Crea un recordatorio para el usuario actual

        Args:
            mensaje: Mensaje del recordatorio
            fecha_hora: Fecha y hora del recordatorio
            repetir: Si debe repetirse
            intervalo_dias: Días entre repeticiones
        """
        if not self.usuario_actual:
            return False, "❌ Usuario no identificado"

        # Generar ID único
        id_recordatorio = hashlib.md5(
            f"{self.usuario_actual.username}{mensaje}{fecha_hora}".encode()
        ).hexdigest()[:8]

        recordatorio = Recordatorio(
            id=id_recordatorio,
            usuario=self.usuario_actual.username,
            mensaje=mensaje,
            fecha_hora=fecha_hora,
            repetir=repetir,
            intervalo_dias=intervalo_dias,
        )

        self.recordatorios.append(recordatorio)
        self._guardar_recordatorios()

        fecha_str = fecha_hora.strftime('%d/%m/%Y %H:%M')
        return True, f"✅ Recordatorio creado (ID: {id_recordatorio})\n📅 {fecha_str}\n💬 {mensaje}"

    def obtener_recordatorios_pendientes(self, usuario: str = None) -> List[Recordatorio]:
        """Obtiene recordatorios pendientes para un usuario"""
        if usuario is None and self.usuario_actual:
            usuario = self.usuario_actual.username

        ahora = datetime.now()
        pendientes = []

        for rec in self.recordatorios:
            if rec.usuario == usuario and not rec.completado:
                if rec.fecha_hora <= ahora:
                    pendientes.append(rec)

        return pendientes

    def completar_recordatorio(self, id_recordatorio: str) -> Tuple[bool, str]:
        """Marca un recordatorio como completado"""
        for rec in self.recordatorios:
            if rec.id == id_recordatorio:
                if rec.repetir and rec.intervalo_dias > 0:
                    # Programar siguiente ocurrencia
                    rec.fecha_hora += timedelta(days=rec.intervalo_dias)
                else:
                    rec.completado = True

                self._guardar_recordatorios()
                return True, f"✅ Recordatorio {id_recordatorio} completado"

        return False, f"❌ Recordatorio {id_recordatorio} no encontrado"

    # ═══════════════════════════════════════════════════════════
    # SISTEMA DE APRENDIZAJE
    # ═══════════════════════════════════════════════════════════

    def _registrar_uso(self, comando: str):
        """Registra el uso de un comando para aprendizaje"""
        if not self.usuario_actual:
            return

        username = self.usuario_actual.username

        if username not in self.aprendizaje:
            self.aprendizaje[username] = {
                'comandos_usados': {},
                'consultas': [],
                'patrones': {},
            }

        datos = self.aprendizaje[username]

        # Incrementar contador de comando
        if comando not in datos['comandos_usados']:
            datos['comandos_usados'][comando] = 0
        datos['comandos_usados'][comando] += 1

        # Agregar a favoritos si se usa frecuentemente
        if datos['comandos_usados'][comando] >= 3:
            if comando not in self.usuario_actual.respuestas_favoritas:
                self.usuario_actual.respuestas_favoritas.append(comando)
                self._guardar_usuarios()

        self._guardar_aprendizaje()

    def obtener_sugerencias(self) -> List[str]:
        """Obtiene sugerencias personalizadas para el usuario actual"""
        if not self.usuario_actual:
            return []

        username = self.usuario_actual.username

        if username not in self.aprendizaje:
            # Usuario nuevo - sugerencias generales
            return ['comandos', 'acerca', 'contacto_sistemas']

        datos = self.aprendizaje[username]

        # Ordenar comandos por uso
        comandos_ordenados = sorted(
            datos['comandos_usados'].items(),
            key=lambda x: x[1],
            reverse=True
        )

        # Retornar top 5
        return [cmd for cmd, count in comandos_ordenados[:5]]

    # ═══════════════════════════════════════════════════════════
    # PERSISTENCIA DE DATOS
    # ═══════════════════════════════════════════════════════════

    def _cargar_datos(self):
        """Carga todos los datos persistidos"""
        self._cargar_usuarios()
        self._cargar_respuestas()
        self._cargar_recordatorios()
        self._cargar_aprendizaje()

    def _cargar_usuarios(self):
        """Carga usuarios desde archivo"""
        if self.usuarios_file.exists():
            try:
                with open(self.usuarios_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.usuarios = {
                        k: UsuarioAgente.from_dict(v) for k, v in data.items()
                    }
            except Exception as e:
                logger.error(f"Error cargando usuarios: {e}")

    def _guardar_usuarios(self):
        """Guarda usuarios a archivo"""
        try:
            with open(self.usuarios_file, 'w', encoding='utf-8') as f:
                data = {k: v.to_dict() for k, v in self.usuarios.items()}
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error guardando usuarios: {e}")

    def _cargar_respuestas(self):
        """Carga respuestas desde archivo"""
        if self.respuestas_file.exists():
            try:
                with open(self.respuestas_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.respuestas = {
                        k: RespuestaRapida.from_dict(v) for k, v in data.items()
                    }
            except Exception as e:
                logger.error(f"Error cargando respuestas: {e}")

    def _guardar_respuestas(self):
        """Guarda respuestas a archivo"""
        try:
            with open(self.respuestas_file, 'w', encoding='utf-8') as f:
                data = {k: v.to_dict() for k, v in self.respuestas.items()}
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error guardando respuestas: {e}")

    def _cargar_recordatorios(self):
        """Carga recordatorios desde archivo"""
        if self.recordatorios_file.exists():
            try:
                with open(self.recordatorios_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.recordatorios = [Recordatorio.from_dict(r) for r in data]
            except Exception as e:
                logger.error(f"Error cargando recordatorios: {e}")

    def _guardar_recordatorios(self):
        """Guarda recordatorios a archivo"""
        try:
            with open(self.recordatorios_file, 'w', encoding='utf-8') as f:
                data = [r.to_dict() for r in self.recordatorios]
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error guardando recordatorios: {e}")

    def _cargar_aprendizaje(self):
        """Carga datos de aprendizaje"""
        if self.aprendizaje_file.exists():
            try:
                with open(self.aprendizaje_file, 'r', encoding='utf-8') as f:
                    self.aprendizaje = json.load(f)
            except Exception as e:
                logger.error(f"Error cargando aprendizaje: {e}")

    def _guardar_aprendizaje(self):
        """Guarda datos de aprendizaje"""
        try:
            with open(self.aprendizaje_file, 'w', encoding='utf-8') as f:
                json.dump(self.aprendizaje, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error guardando aprendizaje: {e}")


# ═══════════════════════════════════════════════════════════════
# FUNCIONES DE CONVENIENCIA
# ═══════════════════════════════════════════════════════════════

# Instancia global del agente
_agente_global: Optional[AgenteSAC] = None


def obtener_agente() -> AgenteSAC:
    """Obtiene la instancia global del Agente SAC"""
    global _agente_global
    if _agente_global is None:
        _agente_global = AgenteSAC()
    return _agente_global


def iniciar_sesion(username: str = None) -> UsuarioAgente:
    """Inicia sesión con el agente"""
    agente = obtener_agente()
    return agente.identificar_usuario(username)


def comando_rapido(entrada: str) -> Optional[str]:
    """Procesa un comando rápido"""
    agente = obtener_agente()
    return agente.procesar_comando_rapido(entrada)


def presentar_agente(nivel: str = 'normal') -> str:
    """Obtiene la presentación del agente"""
    agente = obtener_agente()
    return agente.presentarse(nivel)


# ═══════════════════════════════════════════════════════════════
# INTERFAZ INTERACTIVA
# ═══════════════════════════════════════════════════════════════

def iniciar_interfaz_interactiva():
    """
    Inicia la interfaz interactiva del Agente SAC

    Esta función se ejecuta cuando el usuario inicia una sesión
    """
    agente = obtener_agente()

    # Identificar usuario
    usuario = agente.identificar_usuario()

    # Mostrar presentación
    print(agente.presentarse('normal'))

    # Verificar recordatorios pendientes
    pendientes = agente.obtener_recordatorios_pendientes()
    if pendientes:
        print(f"\n🔔 Tienes {len(pendientes)} recordatorio(s) pendiente(s):\n")
        for rec in pendientes:
            print(f"  • {rec.mensaje}")
        print()

    # Sugerencias personalizadas
    sugerencias = agente.obtener_sugerencias()
    if sugerencias:
        print(f"💡 Sugerencias para ti: {', '.join(['/' + s for s in sugerencias])}\n")

    # Loop interactivo
    print("Escribe tu consulta o '/' para comandos. 'salir' para terminar.\n")

    while True:
        try:
            entrada = input(f"[{usuario.username}] > ").strip()

            if not entrada:
                continue

            if entrada.lower() in ['salir', 'exit', 'quit']:
                print("\n" + agente.agradecer_creador())
                break

            # Procesar comando rápido
            if entrada.startswith('/'):
                respuesta = agente.procesar_comando_rapido(entrada)
                print(f"\n{respuesta}\n")
            else:
                # Búsqueda en respuestas
                resultados = agente.buscar_respuestas(entrada)
                if resultados:
                    print(f"\n🔍 Encontré {len(resultados)} resultado(s) relacionados:\n")
                    for resp in resultados[:3]:
                        print(f"  /{resp.comando} - {resp.titulo}")
                    print(f"\nEscribe /<comando> para ver el contenido.\n")
                else:
                    print(f"\nNo encontré respuestas para '{entrada}'.")
                    print(f"Escribe / para ver comandos disponibles.\n")

        except KeyboardInterrupt:
            print("\n\n👋 ¡Hasta luego!")
            break
        except EOFError:
            break


# ═══════════════════════════════════════════════════════════════
# PUNTO DE ENTRADA
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║      🤖 AGENTE SAC - Sistema de Asistencia Virtual                   ║
║      CEDIS Cancún 427 - Tiendas Chedraui                             ║
║                                                                      ║
║      Creado por: Julián Alexander Juárez Alvarado (ADMJAJA)          ║
║      Jefe de Sistemas - CEDIS Cancún 427                             ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
    """)

    # Iniciar interfaz interactiva
    iniciar_interfaz_interactiva()
