"""
Módulos del Sistema de Automatización de Consultas (SAC)
========================================================

Sistema desarrollado para CEDIS Cancún 427 - Tiendas Chedraui

Módulos disponibles:
-------------------
- db_connection: Conexión a IBM DB2 (Manhattan WMS)
- db_pool: Pool de conexiones avanzado
- query_builder: Constructor de queries SQL
- db_schema: Gestión de schema de base de datos
- repositories: Patrón Repository para acceso a datos
- modulo_cartones: Gestión y validación de cartones/LPN
- modulo_lpn: Procesamiento de License Plate Numbers
- modulo_ubicaciones: Gestión de ubicaciones en almacén
- modulo_usuarios: Administración de usuarios y permisos
- reportes_excel: Generación de reportes Excel profesionales
- validation_result: Clases de resultado de validación
- validators: Motor de validaciones especializadas
- rules: Motor de reglas de negocio
- anomaly_detector: Detección de anomalías en datos
- reconciliation: Reconciliación de datos entre fuentes
- modulo_alertas: Sistema centralizado de alertas y monitoreo
- modulo_auto_config: Auto-configuración y optimización del sistema
- modulo_ups_backup: Sistema UPS de respaldo y continuidad operativa
- modulo_setup: Setup inicial con animaciones de carga
- modulo_control_trafico: Control de tráfico y scheduling de citas
- modulo_habilitacion_usuarios: Habilitación automática de usuarios WMS
- agente_sac: Agente virtual inteligente con respuestas rápidas y aprendizaje
- agente_ia: Motor de IA con Ollama/Llama 3 para el Agente SAC
- modulo_symbol_mc9000: Gestión de dispositivos Symbol MC9000/MC93 series
- modulo_funciones_cedis: Funciones básicas del manual de sistemas CEDIS

Módulos de Reportes Excel (Nuevos):
-----------------------------------
- excel_styles: Estilos corporativos Chedraui para Excel
- excel_templates: Sistema de templates para reportes
- chart_generator: Generador de gráficos Excel
- pivot_generator: Generador de tablas dinámicas
- export_manager: Gestor de exportación multi-formato

Sistema Modular de APIs (Nuevo):
-------------------------------
- api: Sistema de integración de APIs externas
  - CalendarAPI: Calendario mexicano con días festivos
  - ExchangeRateAPI: Tipo de cambio MXN/USD/EUR
  - WeatherAPI: Clima para planificación logística

Autor: Julián Alexander Juárez Alvarado (ADMJAJA)
Cargo: Jefe de Sistemas - CEDIS Cancún 427
"""

# Importar versión desde configuración centralizada
try:
    from config import VERSION
    __version__ = VERSION
except ImportError:
    __version__ = "2.0.0"

__author__ = "Julián Alexander Juárez Alvarado (ADMJAJA)"
__email__ = "admjaja@chedraui.com.mx"

# Importaciones de módulos de base de datos
from .db_connection import *
from .db_pool import *
from .query_builder import *
from .db_schema import *
from .db_local import *
from .db_sync import *

# Importaciones de repositorios
from .repositories import (
    BaseRepository,
    OCRepository,
    DistributionRepository,
    ASNRepository,
)

# Importaciones de módulos de negocio
from .modulo_cartones import *
from .modulo_lpn import *
from .modulo_ubicaciones import *
from .modulo_usuarios import *
from .reportes_excel import *

# Importaciones del módulo de auto-configuración
from .modulo_auto_config import (
    AutoConfigurador,
    ejecutar_auto_configuracion,
    ResultadoConfiguracion,
    ConfiguracionOptima,
    NivelOptimizacion,
    EstadoComponente,
)

# Importaciones del módulo UPS Backup
from .modulo_ups_backup import (
    UPSBackup,
    get_ups_backup,
    iniciar_modo_respaldo,
    restaurar_modo_normal,
    EstadoUPS,
    ModoOperacion,
    TipoOperacionDML,
    NivelRiesgo,
    EstadoOperacion,
    OperacionDML,
    PlantillaDML,
    SnapshotDatos,
    EventoUPS,
    PLANTILLAS_PREDEFINIDAS,
    CODIGOS_AUTORIZACION,
)

# Importaciones del módulo de alertas
from .modulo_alertas import (
    TipoAlerta,
    SeveridadAlerta,
    EstadoSistema,
    EstadoCopiloto,
    FaseSistema,
    Alerta,
    EventoFase,
    EventoCopiloto,
    Discrepancia,
    AjusteRealizado,
    GestorAlertas,
    gestor_alertas,
    alerta_critica,
    alerta_info,
    alerta_exito,
)

# Importaciones del módulo de Control de Tráfico
from .modulo_control_trafico import (
    GestorControlTrafico,
    CitaTrafico,
    Transportista,
    Compuerta,
    EquipoOperativo,
    SlotTiempo,
    MetricasRendimiento,
    ParametrosAprendizaje,
    TipoCita,
    EstadoCita,
    EstadoCompuerta,
    PrioridadCita,
    TipoCircuito,
    MonitorVisionTrafico,
    crear_gestor_trafico,
    demo_control_trafico,
)

# Importaciones del Agente SAC
from .agente_sac import (
    AgenteSAC,
    UsuarioAgente,
    RespuestaRapida,
    Recordatorio,
    ResultadoComando,
    NivelAcceso,
    CategoriaRespuesta,
    EstadoAgente,
    TipoInteraccion,
    obtener_agente,
    iniciar_sesion,
    comando_rapido,
    presentar_agente,
    iniciar_interfaz_interactiva,
    AGENTE_VERSION,
    AGENTE_CODENAME,
    CREADOR,
    EQUIPO_SISTEMAS,
    ADMIN_USUARIO,
)

# Importaciones del Motor de IA del Agente SAC
from .agente_ia import (
    ClienteOllama,
    MotorIAAgenteSAC,
    GestorContextoRepositorio,
    RespuestaIA,
    ContextoRepositorio,
    ConversacionIA,
    EstadoOllama,
    TipoConsulta,
    obtener_motor_ia,
    consultar_ia,
    verificar_ollama_instalado,
    descargar_modelo,
    clonar_repositorio_llama3,
    LLAMA3_REPO,
)

# ═══════════════════════════════════════════════════════════════
# SAC VISION 3.0 - Nuevos Módulos de IA y Computer Use
# ═══════════════════════════════════════════════════════════════

# Importaciones del SAC Agent Core (Motor principal con Claude)
try:
    from .sac_agent_core import (
        SACAgentCore,
        SACAgentConfig,
        AgentState,
        ToolType,
        Message,
        ToolResult,
        AgentResponse,
        get_sac_agent,
        chat as sac_chat,
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).warning(f"SAC Agent Core no disponible: {e}")

# Importaciones del módulo Computer Use
try:
    from .computer_use import (
        ComputerUseTools,
        ComputerUseConfig,
        ComputerAction,
        ScreenInfo,
        ActionType,
        MouseButton,
        get_computer_tools,
        take_screenshot,
        click,
        type_text,
        press_key,
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).warning(f"Computer Use Tools no disponible: {e}")

# Importaciones del módulo Document Tools
try:
    from .document_tools import (
        DocumentTools,
        DocumentResult,
        ExcelTools,
        PDFTools,
        CSVTools,
        TextTools,
        get_document_tools,
        read_document,
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).warning(f"Document Tools no disponible: {e}")

# Importaciones del módulo de Scheduling de Tráfico
from .scheduling_trafico import (
    SchedulerTrafico,
    SlotHorario,
    Conflicto,
    ReglaScheduling,
    ResumenDia,
    TipoSlot,
    EstadoSlot,
    MotivoBloqueo,
    crear_scheduler,
    demo_scheduler,
)

# Importaciones del módulo de Habilitación Automática de Usuarios
from .modulo_habilitacion_usuarios import (
    ServicioHabilitacionUsuarios,
    NotificadorWhatsApp,
    UsuarioBloqueado,
    ResultadoHabilitacion,
    EstadisticasServicio,
    EstadoUsuario,
    EstadoServicio,
    crear_servicio_desde_config,
    verificar_configuracion as verificar_config_habilitacion,
    HABILITACION_CONFIG,
)

# Importaciones del sistema modular de APIs
from .api import (
    # Core
    BaseAPIClient,
    APIResponse,
    APIError,
    APIStatus,
    # Registry
    APIRegistry,
    api_registry,
    get_api,
    list_apis,
    get_api_status,
    # Configuration
    API_CONFIG,
    validate_api_config,
    # Calendar API
    CalendarAPI,
    DiaMexicano,
    TipoDia,
    # Exchange Rate API
    ExchangeRateAPI,
    TipoCambio,
    # Weather API
    WeatherAPI,
    PronosticoClima,
    CondicionClima,
)

# Importaciones del módulo de dispositivos Symbol MC9000/MC93
from .modulo_symbol_mc9000 import (
    GestorDispositivosSymbol,
    DetectorDispositivosSymbol,
    SymbolTelnetCE,
    GestorDriversCradle,
    AsistenteIASymbol,
    InfoDispositivo,
    ResultadoComando as ResultadoComandoSymbol,
    AlertaDispositivo,
    ReporteHealthCheck,
    EstadoDispositivo as EstadoDispositivoSymbol,
    TipoConexion,
    NivelBateria,
    crear_gestor_symbol,
    detectar_dispositivos_symbol,
    conectar_symbol_telnet,
    health_check_symbol,
    demo_symbol_mc9000,
    SYMBOL_VENDOR_IDS,
    MODELOS_CONOCIDOS,
    BASES_CARGA,
    COMANDOS_TELNETCE,
)

# Importaciones del módulo de Email Commands
from .modulo_symbol_email_commands import (
    EstadoComando,
    ComandoEmail,
    ReceptorComandosEmail,
    ProcesadorComandosEmail,
)

# Importaciones del módulo de Funciones Básicas CEDIS
from .modulo_funciones_cedis import (
    # Constantes
    CEDIS_CODE,
    CEDIS_NAME,
    VERSION_MODULO,
    # Enumeraciones
    TipoContacto,
    TipoEquipo,
    EstadoDispositivo as EstadoDispositivoCEDIS,
    # Dataclasses
    ExtensionTelefonica,
    ContactoImportante,
    EquipoIP,
    AtajoTeclado,
    MenuWM,
    # Datos
    DIRECTORIO_TELEFONICO,
    CONTACTOS_IMPORTANTES,
    IPS_ETIQUETADORAS,
    ATAJOS_TECLADO_WM,
    TECLAS_F_EXTENDIDAS,
    MENUS_WM,
    USUARIOS_ESPECIALES,
    OPCIONES_USUARIO_WM,
    HAND_HELD_INFO,
    ATAJOS_RF,
    # Funciones de búsqueda
    buscar_extension,
    obtener_extension,
    listar_directorio_telefonico,
    buscar_contacto,
    listar_contactos_importantes,
    obtener_ip_etiquetadora,
    listar_etiquetadoras,
    obtener_atajo_tecla_f,
    listar_atajos_teclado,
    obtener_ruta_menu,
    listar_menus_wm,
    obtener_info_usuario_especial,
    listar_usuarios_especiales,
    obtener_info_hand_held,
    # Guías
    guia_habilitar_usuario,
    guia_crear_usuario,
    guia_cambiar_contrasena,
    guia_eliminar_usuario,
    guia_verificar_errores,
    guia_imprimir_wm,
    # Ayuda
    mostrar_ayuda_sac,
    demo_funciones_cedis,
)


__all__ = [
    # Módulos de base de datos
    'db_connection',
    'db_pool',
    'query_builder',
    'db_schema',
    'db_local',
    'db_sync',
    # Repositorios
    'repositories',
    'BaseRepository',
    'OCRepository',
    'DistributionRepository',
    'ASNRepository',
    # Módulos de negocio
    'modulo_cartones',
    'modulo_lpn',
    'modulo_ubicaciones',
    'modulo_usuarios',
    'reportes_excel',
    # Módulo de auto-configuración
    'modulo_auto_config',
    'AutoConfigurador',
    'ejecutar_auto_configuracion',
    'ResultadoConfiguracion',
    'ConfiguracionOptima',
    'NivelOptimizacion',
    'EstadoComponente',
    # Módulo de alertas
    'modulo_alertas',
    'TipoAlerta',
    'SeveridadAlerta',
    'EstadoSistema',
    'EstadoCopiloto',
    'FaseSistema',
    'Alerta',
    'EventoFase',
    'EventoCopiloto',
    'Discrepancia',
    'AjusteRealizado',
    'GestorAlertas',
    'gestor_alertas',
    'alerta_critica',
    'alerta_info',
    'alerta_exito',
    # Módulo UPS Backup
    'modulo_ups_backup',
    'UPSBackup',
    'get_ups_backup',
    'iniciar_modo_respaldo',
    'restaurar_modo_normal',
    'EstadoUPS',
    'ModoOperacion',
    'TipoOperacionDML',
    'NivelRiesgo',
    'EstadoOperacion',
    'OperacionDML',
    'PlantillaDML',
    'SnapshotDatos',
    'EventoUPS',
    'PLANTILLAS_PREDEFINIDAS',
    'CODIGOS_AUTORIZACION',
    # Módulo Control de Tráfico
    'modulo_control_trafico',
    'GestorControlTrafico',
    'CitaTrafico',
    'Transportista',
    'Compuerta',
    'EquipoOperativo',
    'SlotTiempo',
    'MetricasRendimiento',
    'ParametrosAprendizaje',
    'TipoCita',
    'EstadoCita',
    'EstadoCompuerta',
    'PrioridadCita',
    'TipoCircuito',
    'MonitorVisionTrafico',
    'crear_gestor_trafico',
    # Módulo Scheduling de Tráfico
    'scheduling_trafico',
    'SchedulerTrafico',
    'SlotHorario',
    'Conflicto',
    'ReglaScheduling',
    'ResumenDia',
    'TipoSlot',
    'EstadoSlot',
    'MotivoBloqueo',
    'crear_scheduler',
    # Módulo Habilitación Automática de Usuarios
    'modulo_habilitacion_usuarios',
    'ServicioHabilitacionUsuarios',
    'NotificadorWhatsApp',
    'UsuarioBloqueado',
    'ResultadoHabilitacion',
    'EstadisticasServicio',
    'EstadoUsuario',
    'EstadoServicio',
    'crear_servicio_desde_config',
    'verificar_config_habilitacion',
    'HABILITACION_CONFIG',
    # Agente SAC
    'agente_sac',
    'AgenteSAC',
    'UsuarioAgente',
    'RespuestaRapida',
    'Recordatorio',
    'ResultadoComando',
    'NivelAcceso',
    'CategoriaRespuesta',
    'EstadoAgente',
    'TipoInteraccion',
    'obtener_agente',
    'iniciar_sesion',
    'comando_rapido',
    'presentar_agente',
    'iniciar_interfaz_interactiva',
    'AGENTE_VERSION',
    'AGENTE_CODENAME',
    'CREADOR',
    'EQUIPO_SISTEMAS',
    'ADMIN_USUARIO',
    # Motor de IA del Agente SAC
    'agente_ia',
    'ClienteOllama',
    'MotorIAAgenteSAC',
    'GestorContextoRepositorio',
    'RespuestaIA',
    'ContextoRepositorio',
    'ConversacionIA',
    'EstadoOllama',
    'TipoConsulta',
    'obtener_motor_ia',
    'consultar_ia',
    'verificar_ollama_instalado',
    'descargar_modelo',
    'clonar_repositorio_llama3',
    'LLAMA3_REPO',
    # Sistema modular de APIs
    'api',
    'BaseAPIClient',
    'APIResponse',
    'APIError',
    'APIStatus',
    'APIRegistry',
    'api_registry',
    'get_api',
    'list_apis',
    'get_api_status',
    'API_CONFIG',
    'validate_api_config',
    'CalendarAPI',
    'DiaMexicano',
    'TipoDia',
    'ExchangeRateAPI',
    'TipoCambio',
    'WeatherAPI',
    'PronosticoClima',
    'CondicionClima',
    # Módulo de dispositivos Symbol MC9000/MC93
    'modulo_symbol_mc9000',
    'GestorDispositivosSymbol',
    'DetectorDispositivosSymbol',
    'SymbolTelnetCE',
    'GestorDriversCradle',
    'AsistenteIASymbol',
    'InfoDispositivo',
    'ResultadoComandoSymbol',
    'AlertaDispositivo',
    'ReporteHealthCheck',
    'EstadoDispositivoSymbol',
    'TipoConexion',
    'NivelBateria',
    'crear_gestor_symbol',
    'detectar_dispositivos_symbol',
    'conectar_symbol_telnet',
    'health_check_symbol',
    'demo_symbol_mc9000',
    'SYMBOL_VENDOR_IDS',
    'MODELOS_CONOCIDOS',
    'BASES_CARGA',
    'COMANDOS_TELNETCE',
    # Módulo de Email Commands
    'modulo_symbol_email_commands',
    'EstadoComando',
    'ComandoEmail',
    'ReceptorComandosEmail',
    'ProcesadorComandosEmail',
    # Módulo de Funciones Básicas CEDIS
    'modulo_funciones_cedis',
    'CEDIS_CODE',
    'CEDIS_NAME',
    'VERSION_MODULO',
    'TipoContacto',
    'TipoEquipo',
    'EstadoDispositivoCEDIS',
    'ExtensionTelefonica',
    'ContactoImportante',
    'EquipoIP',
    'AtajoTeclado',
    'MenuWM',
    'DIRECTORIO_TELEFONICO',
    'CONTACTOS_IMPORTANTES',
    'IPS_ETIQUETADORAS',
    'ATAJOS_TECLADO_WM',
    'TECLAS_F_EXTENDIDAS',
    'MENUS_WM',
    'USUARIOS_ESPECIALES',
    'OPCIONES_USUARIO_WM',
    'HAND_HELD_INFO',
    'ATAJOS_RF',
    'buscar_extension',
    'obtener_extension',
    'listar_directorio_telefonico',
    'buscar_contacto',
    'listar_contactos_importantes',
    'obtener_ip_etiquetadora',
    'listar_etiquetadoras',
    'obtener_atajo_tecla_f',
    'listar_atajos_teclado',
    'obtener_ruta_menu',
    'listar_menus_wm',
    'obtener_info_usuario_especial',
    'listar_usuarios_especiales',
    'obtener_info_hand_held',
    'guia_habilitar_usuario',
    'guia_crear_usuario',
    'guia_cambiar_contrasena',
    'guia_eliminar_usuario',
    'guia_verificar_errores',
    'guia_imprimir_wm',
    'mostrar_ayuda_sac',
    'demo_funciones_cedis',
    # SAC VISION 3.0 - SAC Agent Core
    'sac_agent_core',
    'SACAgentCore',
    'SACAgentConfig',
    'AgentState',
    'ToolType',
    'Message',
    'ToolResult',
    'AgentResponse',
    'get_sac_agent',
    'sac_chat',
    # SAC VISION 3.0 - Computer Use Tools
    'computer_use',
    'ComputerUseTools',
    'ComputerUseConfig',
    'ComputerAction',
    'ScreenInfo',
    'ActionType',
    'MouseButton',
    'get_computer_tools',
    'take_screenshot',
    'click',
    'type_text',
    'press_key',
    # SAC VISION 3.0 - Document Tools
    'document_tools',
    'DocumentTools',
    'DocumentResult',
    'ExcelTools',
    'PDFTools',
    'CSVTools',
    'TextTools',
    'get_document_tools',
    'read_document',
]
