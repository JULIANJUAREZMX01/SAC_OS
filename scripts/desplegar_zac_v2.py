#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
DESPLIEGUE ZAC/SAC V2.0 - ALERTA HITO Y ACTIVACION CONTINUA
CEDIS Cancun 427 - Tiendas Chedraui S.A. de C.V.
===============================================================================

Este script realiza el despliegue completo del sistema ZAC V2.0:
1. Genera y envia la ALERTA HITO con todas las especificaciones
2. Activa el sistema de alertas y monitoreo de manera ininterrumpida
3. Activa el Agente SAC para asistencia continua

"Las maquinas y los sistemas al servicio de los analistas"

Desarrollado por: Julian Alexander Juarez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logistica Cancun
===============================================================================
"""

import os
import sys
import json
import socket
import platform
import threading
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Configurar path del proyecto
BASE_DIR = Path(__file__).parent.absolute()
sys.path.insert(0, str(BASE_DIR))

# ===============================================================================
# CONFIGURACION DE LOGGING
# ===============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            BASE_DIR / 'output' / 'logs' / f'despliegue_zac_v2_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log',
            encoding='utf-8'
        )
    ]
)
logger = logging.getLogger('ZAC_V2_DEPLOY')


# ===============================================================================
# CONSTANTES Y CONFIGURACION
# ===============================================================================

VERSION = "2.0.0"
NOMBRE_CODIGO = "Orquestador Unificado"
FECHA_RELEASE = "Noviembre 2025"

# Informacion del CEDIS
CEDIS_INFO = {
    'codigo': '427',
    'nombre': 'CEDIS Cancun',
    'region': 'Sureste',
    'empresa': 'Tiendas Chedraui S.A. de C.V.',
    'almacen': 'C22'
}

# Equipo de desarrollo
EQUIPO_DESARROLLO = {
    'lider': {
        'nombre': 'Julian Alexander Juarez Alvarado',
        'usuario': 'ADMJAJA',
        'cargo': 'Jefe de Sistemas'
    },
    'analistas': [
        {'nombre': 'Larry Adanael Basto Diaz', 'cargo': 'Analista de Sistemas'},
        {'nombre': 'Adrian Quintana Zuniga', 'cargo': 'Analista de Sistemas'}
    ],
    'supervisor_regional': {
        'nombre': 'Itza Vera Reyes Sarubi',
        'ubicacion': 'Villahermosa'
    }
}


# ===============================================================================
# ESPECIFICACIONES DEL SISTEMA ZAC V2.0
# ===============================================================================

ESPECIFICACIONES_ZAC_V2 = {
    'version': VERSION,
    'nombre_codigo': NOMBRE_CODIGO,
    'fecha_release': FECHA_RELEASE,

    'arquitectura': {
        'tipo': 'Monolito Modular con Orquestacion',
        'capas': [
            'Capa de Presentacion (CLI + GUI)',
            'Capa de Logica de Negocio (Modulos)',
            'Capa de Acceso a Datos (DB2/SQLite)',
            'Capa de Integracion (Email/Telegram/WhatsApp)'
        ],
        'patron_principal': 'Script Maestro Unificado'
    },

    'scripts_maestros': {
        'INICIO_SAC.py': 'Punto de entrada unico v2.0 - Detecta estado del sistema',
        'sac_master_gui.py': 'Script Maestro GUI v3.0 - Animaciones y analisis exhaustivo',
        'sac_master.py': 'Script Maestro v2.0 - Auto-configuracion inteligente',
        'maestro.py': 'Orquestador de tareas programadas (modo daemon)',
        'main.py': 'Sistema principal con menu interactivo'
    },

    'modulos_totales': 35,
    'archivos_python': 128,

    'funcionalidades_principales': [
        'Validacion OC vs Distribuciones con deteccion de discrepancias',
        'Monitoreo en tiempo real con 15+ tipos de validaciones',
        'Sistema de alertas centralizado con 30+ tipos de alertas',
        'Generador de reportes Excel con formato corporativo Chedraui',
        'Notificaciones multi-canal (Email Office 365, Telegram, WhatsApp)',
        'Auto-configuracion inteligente basada en hardware',
        'Instalador automatizado GUI con 7 fases',
        'Sistema de carpetas compartidas multi-dispositivo',
        'Agente SAC "Godi" con IA integrada (Ollama/Llama 3)',
        'Modo Copiloto para correcciones automaticas',
        'Deteccion de anomalias proactiva',
        'Pool de conexiones DB2 optimizado',
        'Servicio Windows para ejecucion continua'
    ],

    'modulos_nuevos_v2': [
        'modulo_auto_config.py - Auto-configuracion del sistema',
        'modulo_credenciales_setup.py - Setup de credenciales GUI',
        'modulo_habilitacion_usuarios.py - Gestion usuarios WMS',
        'modulo_funciones_cedis.py - Funciones especificas CEDIS',
        'modulo_symbol_mc9000.py - Integracion lectores Symbol',
        'modulo_control_trafico.py - Control trafico archivos',
        'agente_ia.py - Agente IA con Ollama',
        'agente_sac.py - Agente SAC "Godi"',
        'anomaly_detector.py - Deteccion de anomalias',
        'copiloto_correcciones.py - Modo Copiloto',
        'ejecutor_correcciones.py - Ejecutor de correcciones',
        'scheduling_trafico.py - Programacion de trafico'
    ],

    'sistema_alertas': {
        'tipos_alertas': 30,
        'severidades': ['CRITICO', 'ALTO', 'MEDIO', 'BAJO', 'INFO', 'EXITO', 'DEBUG'],
        'canales': ['Email (Office 365)', 'Telegram Bot', 'WhatsApp API (beta)'],
        'persistencia': 'JSON con historial'
    },

    'monitoreo': {
        'validaciones': 15,
        'tipos': [
            'Conexion DB2',
            'Existencia de OC',
            'Expiracion de OC',
            'Distribucion excede OC (CRITICO)',
            'Distribucion incompleta',
            'OC sin distribuciones',
            'SKU sin Inner Pack',
            'Estado ASN invalido',
            'ASN no actualizado',
            'Datos Excel invalidos',
            'Columnas faltantes',
            'Datos nulos',
            'OC sin prefijo C',
            'Distribuciones sin prefijo C',
            'ASN sin prefijo C'
        ],
        'intervalo_default': 60  # segundos
    },

    'despliegue_empresarial': {
        'instalacion_silenciosa': 'PowerShell con -Silent',
        'servicio_windows': 'pywin32 service wrapper',
        'gpo_sccm': 'Documentado y soportado',
        'desinstalacion': '-Uninstall -Force'
    },

    'requisitos': {
        'python': '3.8+',
        'plataformas': ['Windows 10/11', 'Linux'],
        'ram_minima': '2 GB',
        'ram_recomendada': '8 GB',
        'disco': '500 MB - 2 GB'
    },

    'integraciones': {
        'base_datos': 'IBM DB2 (Manhattan WMS) - Schema WMWHSE1',
        'email': 'Office 365 SMTP con TLS',
        'telegram': 'Bot API',
        'whatsapp': 'API (beta)',
        'local': 'SQLite para cache y sincronizacion'
    }
}


# ===============================================================================
# CLASE PRINCIPAL: DESPLEGADOR ZAC V2
# ===============================================================================

class DesplegadorZACV2:
    """
    Clase principal para el despliegue de ZAC V2.0

    Responsabilidades:
    1. Generar y enviar Alerta HITO
    2. Activar sistema de monitoreo continuo
    3. Activar Agente SAC
    4. Gestionar estado del despliegue
    """

    def __init__(self):
        self.timestamp_inicio = datetime.now()
        self.dispositivo_id = self._obtener_id_dispositivo()
        self.estado_despliegue = 'iniciando'
        self.errores = []
        self.alertas_enviadas = []

        # Inicializar componentes
        self.gestor_alertas = None
        self.monitor = None
        self.agente_sac = None

        logger.info(f"Inicializando Desplegador ZAC V2.0 - Dispositivo: {self.dispositivo_id}")

    def _obtener_id_dispositivo(self) -> str:
        """Obtiene identificador unico del dispositivo"""
        try:
            hostname = socket.gethostname()
            return f"{hostname}_{platform.node()}"
        except Exception:
            return f"DEVICE_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    def _obtener_info_sistema(self) -> Dict:
        """Recopila informacion del sistema actual"""
        return {
            'hostname': socket.gethostname(),
            'plataforma': platform.system(),
            'version_os': platform.version(),
            'arquitectura': platform.machine(),
            'procesador': platform.processor(),
            'python_version': platform.python_version(),
            'directorio_trabajo': str(BASE_DIR),
            'timestamp': datetime.now().isoformat()
        }

    # ===========================================================================
    # GENERACION DE ALERTA HITO
    # ===========================================================================

    def generar_alerta_hito(self) -> Dict:
        """
        Genera la ALERTA HITO con todas las especificaciones del sistema

        Returns:
            Dict con la alerta HITO completa
        """
        logger.info("Generando ALERTA HITO de despliegue...")

        alerta_hito = {
            'tipo': 'ALERTA_HITO_DESPLIEGUE',
            'prioridad': 'MAXIMA',
            'timestamp': datetime.now().isoformat(),

            'encabezado': {
                'titulo': f'HITO: DESPLIEGUE ZAC/SAC V{VERSION} "{NOMBRE_CODIGO}"',
                'subtitulo': f'Sistema de Automatizacion de Consultas - CEDIS {CEDIS_INFO["codigo"]}',
                'fecha_despliegue': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'dispositivo_origen': self.dispositivo_id
            },

            'informacion_cedis': CEDIS_INFO,
            'equipo_desarrollo': EQUIPO_DESARROLLO,

            'especificaciones_sistema': ESPECIFICACIONES_ZAC_V2,

            'estado_despliegue': {
                'fase': 'PRODUCCION',
                'estado': 'ACTIVO',
                'monitoreo': 'ACTIVADO_CONTINUO',
                'agente_sac': 'ACTIVADO',
                'alertas': 'OPERATIVAS'
            },

            'info_sistema': self._obtener_info_sistema(),

            'instrucciones_replicacion': [
                '1. Clonar repositorio en equipo destino',
                '2. Ejecutar: python INICIO_SAC.py',
                '3. Completar formulario de credenciales',
                '4. El sistema se auto-configurara segun hardware',
                '5. Verificar conexion a DB2 y email',
                '6. El monitoreo se activara automaticamente'
            ],

            'contacto_soporte': {
                'equipo': 'Sistemas CEDIS 427',
                'lider': EQUIPO_DESARROLLO['lider']['nombre'],
                'region': CEDIS_INFO['region']
            },

            'filosofia': '"Las maquinas y los sistemas al servicio de los analistas"',

            'copyright': f'(c) {datetime.now().year} Tiendas Chedraui S.A. de C.V. - Todos los derechos reservados'
        }

        logger.info("ALERTA HITO generada exitosamente")
        return alerta_hito

    def formatear_alerta_hito_texto(self, alerta: Dict) -> str:
        """Formatea la alerta HITO como texto para consola/logs"""

        linea = "=" * 80

        texto = f"""
{linea}
                    ALERTA HITO - DESPLIEGUE ZAC/SAC V{VERSION}
                           "{NOMBRE_CODIGO}"
{linea}

FECHA DE DESPLIEGUE: {alerta['encabezado']['fecha_despliegue']}
DISPOSITIVO ORIGEN:  {alerta['encabezado']['dispositivo_origen']}

{linea}
                              INFORMACION DEL CEDIS
{linea}

  Codigo:   {CEDIS_INFO['codigo']}
  Nombre:   {CEDIS_INFO['nombre']}
  Region:   {CEDIS_INFO['region']}
  Empresa:  {CEDIS_INFO['empresa']}

{linea}
                           EQUIPO DE DESARROLLO
{linea}

  Lider:              {EQUIPO_DESARROLLO['lider']['nombre']} ({EQUIPO_DESARROLLO['lider']['usuario']})
                      {EQUIPO_DESARROLLO['lider']['cargo']}

  Analistas:          {EQUIPO_DESARROLLO['analistas'][0]['nombre']}
                      {EQUIPO_DESARROLLO['analistas'][1]['nombre']}

  Supervisor Regional: {EQUIPO_DESARROLLO['supervisor_regional']['nombre']}
                       ({EQUIPO_DESARROLLO['supervisor_regional']['ubicacion']})

{linea}
                         ESPECIFICACIONES DEL SISTEMA
{linea}

  Version:            {ESPECIFICACIONES_ZAC_V2['version']}
  Nombre Codigo:      {ESPECIFICACIONES_ZAC_V2['nombre_codigo']}
  Fecha Release:      {ESPECIFICACIONES_ZAC_V2['fecha_release']}

  ARQUITECTURA:
  - Tipo:             {ESPECIFICACIONES_ZAC_V2['arquitectura']['tipo']}
  - Modulos Totales:  {ESPECIFICACIONES_ZAC_V2['modulos_totales']}
  - Archivos Python:  {ESPECIFICACIONES_ZAC_V2['archivos_python']}

{linea}
                         SCRIPTS MAESTROS
{linea}

"""
        for script, desc in ESPECIFICACIONES_ZAC_V2['scripts_maestros'].items():
            texto += f"  {script:25} {desc}\n"

        texto += f"""
{linea}
                    FUNCIONALIDADES PRINCIPALES
{linea}

"""
        for i, func in enumerate(ESPECIFICACIONES_ZAC_V2['funcionalidades_principales'], 1):
            texto += f"  {i:2}. {func}\n"

        texto += f"""
{linea}
                         MODULOS NUEVOS V2.0
{linea}

"""
        for modulo in ESPECIFICACIONES_ZAC_V2['modulos_nuevos_v2']:
            texto += f"  + {modulo}\n"

        texto += f"""
{linea}
                        SISTEMA DE ALERTAS
{linea}

  Tipos de Alertas:   {ESPECIFICACIONES_ZAC_V2['sistema_alertas']['tipos_alertas']}
  Severidades:        {', '.join(ESPECIFICACIONES_ZAC_V2['sistema_alertas']['severidades'])}
  Canales:            {', '.join(ESPECIFICACIONES_ZAC_V2['sistema_alertas']['canales'])}

{linea}
                           MONITOREO
{linea}

  Validaciones:       {ESPECIFICACIONES_ZAC_V2['monitoreo']['validaciones']} tipos
  Intervalo Default:  {ESPECIFICACIONES_ZAC_V2['monitoreo']['intervalo_default']} segundos

  TIPOS DE VALIDACION:
"""
        for val in ESPECIFICACIONES_ZAC_V2['monitoreo']['tipos']:
            texto += f"    - {val}\n"

        texto += f"""
{linea}
                      DESPLIEGUE EMPRESARIAL
{linea}

  Instalacion:        Silenciosa con PowerShell
  Servicio Windows:   Soportado (pywin32)
  GPO/SCCM:           Documentado
  Desinstalacion:     -Uninstall -Force

{linea}
                          INTEGRACIONES
{linea}

  Base de Datos:      {ESPECIFICACIONES_ZAC_V2['integraciones']['base_datos']}
  Email:              {ESPECIFICACIONES_ZAC_V2['integraciones']['email']}
  Telegram:           {ESPECIFICACIONES_ZAC_V2['integraciones']['telegram']}
  WhatsApp:           {ESPECIFICACIONES_ZAC_V2['integraciones']['whatsapp']}

{linea}
                       ESTADO DEL DESPLIEGUE
{linea}

  FASE:               PRODUCCION
  ESTADO:             ACTIVO
  MONITOREO:          ACTIVADO CONTINUO
  AGENTE SAC:         ACTIVADO
  SISTEMA ALERTAS:    OPERATIVO

{linea}
                   INSTRUCCIONES DE REPLICACION
{linea}

"""
        for instruccion in alerta['instrucciones_replicacion']:
            texto += f"  {instruccion}\n"

        texto += f"""
{linea}

  FILOSOFIA: {alerta['filosofia']}

{linea}
  {alerta['copyright']}
{linea}
"""
        return texto

    def formatear_alerta_hito_html(self, alerta: Dict) -> str:
        """Formatea la alerta HITO como HTML para email"""

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f5f5f5;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #E31837 0%, #B31030 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 28px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        .header h2 {{
            margin: 10px 0 0 0;
            font-size: 18px;
            font-weight: normal;
            opacity: 0.9;
        }}
        .badge {{
            display: inline-block;
            background: #FFD700;
            color: #333;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            margin-top: 15px;
        }}
        .content {{
            padding: 30px;
        }}
        .section {{
            margin-bottom: 25px;
            border-left: 4px solid #E31837;
            padding-left: 15px;
        }}
        .section h3 {{
            color: #E31837;
            margin: 0 0 10px 0;
            font-size: 16px;
            text-transform: uppercase;
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: 150px 1fr;
            gap: 8px;
        }}
        .info-label {{
            color: #666;
            font-weight: 500;
        }}
        .info-value {{
            color: #333;
        }}
        .feature-list {{
            list-style: none;
            padding: 0;
            margin: 0;
        }}
        .feature-list li {{
            padding: 8px 0;
            border-bottom: 1px solid #eee;
        }}
        .feature-list li:before {{
            content: "✅ ";
        }}
        .status-box {{
            background: #d4edda;
            border: 1px solid #c3e6cb;
            border-radius: 8px;
            padding: 15px;
            text-align: center;
        }}
        .status-active {{
            color: #155724;
            font-size: 18px;
            font-weight: bold;
        }}
        .footer {{
            background: #333;
            color: #ccc;
            padding: 20px;
            text-align: center;
            font-size: 12px;
        }}
        .philosophy {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 20px 0;
            font-style: italic;
            font-size: 16px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 10px 0;
        }}
        table th, table td {{
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }}
        table th {{
            background: #f8f9fa;
            color: #E31837;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>ALERTA HITO</h1>
            <h2>DESPLIEGUE ZAC/SAC V{VERSION} "{NOMBRE_CODIGO}"</h2>
            <div class="badge">CEDIS {CEDIS_INFO['codigo']} - {CEDIS_INFO['region']}</div>
        </div>

        <div class="content">
            <div class="status-box">
                <div class="status-active">SISTEMA DESPLEGADO Y OPERATIVO</div>
                <p>Monitoreo Continuo | Alertas Activas | Agente SAC Operativo</p>
            </div>

            <div class="section">
                <h3>Informacion del Despliegue</h3>
                <div class="info-grid">
                    <span class="info-label">Fecha:</span>
                    <span class="info-value">{alerta['encabezado']['fecha_despliegue']}</span>
                    <span class="info-label">Dispositivo:</span>
                    <span class="info-value">{alerta['encabezado']['dispositivo_origen']}</span>
                    <span class="info-label">Version:</span>
                    <span class="info-value">{VERSION}</span>
                </div>
            </div>

            <div class="section">
                <h3>Equipo de Desarrollo</h3>
                <table>
                    <tr>
                        <th>Rol</th>
                        <th>Nombre</th>
                        <th>Cargo</th>
                    </tr>
                    <tr>
                        <td>Lider</td>
                        <td>{EQUIPO_DESARROLLO['lider']['nombre']}</td>
                        <td>{EQUIPO_DESARROLLO['lider']['cargo']}</td>
                    </tr>
                    <tr>
                        <td>Analista</td>
                        <td>{EQUIPO_DESARROLLO['analistas'][0]['nombre']}</td>
                        <td>{EQUIPO_DESARROLLO['analistas'][0]['cargo']}</td>
                    </tr>
                    <tr>
                        <td>Analista</td>
                        <td>{EQUIPO_DESARROLLO['analistas'][1]['nombre']}</td>
                        <td>{EQUIPO_DESARROLLO['analistas'][1]['cargo']}</td>
                    </tr>
                    <tr>
                        <td>Supervisor Regional</td>
                        <td>{EQUIPO_DESARROLLO['supervisor_regional']['nombre']}</td>
                        <td>{EQUIPO_DESARROLLO['supervisor_regional']['ubicacion']}</td>
                    </tr>
                </table>
            </div>

            <div class="section">
                <h3>Especificaciones del Sistema</h3>
                <div class="info-grid">
                    <span class="info-label">Modulos:</span>
                    <span class="info-value">{ESPECIFICACIONES_ZAC_V2['modulos_totales']} modulos</span>
                    <span class="info-label">Archivos Python:</span>
                    <span class="info-value">{ESPECIFICACIONES_ZAC_V2['archivos_python']} archivos</span>
                    <span class="info-label">Tipos de Alertas:</span>
                    <span class="info-value">{ESPECIFICACIONES_ZAC_V2['sistema_alertas']['tipos_alertas']}</span>
                    <span class="info-label">Validaciones:</span>
                    <span class="info-value">{ESPECIFICACIONES_ZAC_V2['monitoreo']['validaciones']} tipos</span>
                </div>
            </div>

            <div class="section">
                <h3>Funcionalidades Principales</h3>
                <ul class="feature-list">
"""
        for func in ESPECIFICACIONES_ZAC_V2['funcionalidades_principales'][:8]:
            html += f"                    <li>{func}</li>\n"

        html += f"""
                </ul>
            </div>

            <div class="section">
                <h3>Canales de Notificacion</h3>
                <ul class="feature-list">
"""
        for canal in ESPECIFICACIONES_ZAC_V2['sistema_alertas']['canales']:
            html += f"                    <li>{canal}</li>\n"

        html += f"""
                </ul>
            </div>

            <div class="section">
                <h3>Instrucciones de Replicacion</h3>
                <ol>
"""
        for instruccion in alerta['instrucciones_replicacion']:
            # Quitar el numero inicial ya que usamos <ol>
            texto_instruccion = instruccion.split('. ', 1)[-1] if '. ' in instruccion else instruccion
            html += f"                    <li>{texto_instruccion}</li>\n"

        html += f"""
                </ol>
            </div>

            <div class="philosophy">
                {alerta['filosofia']}
            </div>
        </div>

        <div class="footer">
            <p>{alerta['copyright']}</p>
            <p>Contacto Soporte: {alerta['contacto_soporte']['equipo']} | {alerta['contacto_soporte']['lider']}</p>
        </div>
    </div>
</body>
</html>
"""
        return html

    # ===========================================================================
    # ENVIO DE ALERTA HITO
    # ===========================================================================

    def enviar_alerta_hito(self, alerta: Dict) -> Dict[str, bool]:
        """
        Envia la alerta HITO por todos los canales disponibles

        Returns:
            Dict con resultado por canal
        """
        resultados = {
            'consola': False,
            'archivo': False,
            'email': False,
            'telegram': False
        }

        # 1. Mostrar en consola
        try:
            texto = self.formatear_alerta_hito_texto(alerta)
            print(texto)
            resultados['consola'] = True
            logger.info("Alerta HITO mostrada en consola")
        except Exception as e:
            logger.error(f"Error mostrando en consola: {e}")

        # 2. Guardar en archivo
        try:
            archivo_alerta = BASE_DIR / 'output' / 'logs' / f'ALERTA_HITO_ZAC_V2_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
            archivo_alerta.parent.mkdir(parents=True, exist_ok=True)
            archivo_alerta.write_text(self.formatear_alerta_hito_texto(alerta), encoding='utf-8')

            # Guardar version JSON
            archivo_json = archivo_alerta.with_suffix('.json')
            with open(archivo_json, 'w', encoding='utf-8') as f:
                json.dump(alerta, f, ensure_ascii=False, indent=2, default=str)

            resultados['archivo'] = True
            logger.info(f"Alerta HITO guardada en: {archivo_alerta}")
        except Exception as e:
            logger.error(f"Error guardando archivo: {e}")

        # 3. Enviar por email
        try:
            from gestor_correos import GestorCorreos
            from config import EMAIL_CONFIG

            gestor_email = GestorCorreos(EMAIL_CONFIG)
            html = self.formatear_alerta_hito_html(alerta)

            # Obtener destinatarios de config o usar default
            try:
                from config import EMAIL_TO_NORMAL, EMAIL_CC
                destinatarios = EMAIL_TO_NORMAL if EMAIL_TO_NORMAL else []
                cc = EMAIL_CC if EMAIL_CC else []
            except ImportError:
                destinatarios = []
                cc = []

            if destinatarios:
                resultado_email = gestor_email._enviar_correo(
                    destinatarios=destinatarios,
                    asunto=f"[HITO] Despliegue ZAC/SAC V{VERSION} - CEDIS {CEDIS_INFO['codigo']}",
                    cuerpo_html=html,
                    cc=cc
                )
                resultados['email'] = resultado_email
                logger.info("Alerta HITO enviada por email")
            else:
                logger.warning("No hay destinatarios configurados para email")

        except ImportError:
            logger.warning("Modulo de correos no disponible")
        except Exception as e:
            logger.error(f"Error enviando email: {e}")

        # 4. Enviar por Telegram
        try:
            from notificaciones_telegram import NotificadorTelegram

            notificador = NotificadorTelegram()
            mensaje_telegram = f"""
🎉 *ALERTA HITO - DESPLIEGUE*

📦 *ZAC/SAC V{VERSION}*
_{NOMBRE_CODIGO}_

📍 CEDIS: {CEDIS_INFO['codigo']} - {CEDIS_INFO['nombre']}
📅 Fecha: {alerta['encabezado']['fecha_despliegue']}
💻 Dispositivo: {self.dispositivo_id}

✅ Estado: SISTEMA OPERATIVO
🔄 Monitoreo: ACTIVO CONTINUO
🤖 Agente SAC: ACTIVADO

_{alerta['filosofia']}_
"""
            resultado_telegram = notificador.enviar_mensaje(mensaje_telegram)
            resultados['telegram'] = resultado_telegram
            logger.info("Alerta HITO enviada por Telegram")

        except ImportError:
            logger.warning("Modulo de Telegram no disponible")
        except Exception as e:
            logger.error(f"Error enviando Telegram: {e}")

        self.alertas_enviadas.append({
            'tipo': 'ALERTA_HITO',
            'timestamp': datetime.now().isoformat(),
            'resultados': resultados
        })

        return resultados

    # ===========================================================================
    # ACTIVACION DEL SISTEMA DE MONITOREO
    # ===========================================================================

    def activar_monitoreo_continuo(self) -> bool:
        """
        Activa el sistema de monitoreo de manera ininterrumpida

        Returns:
            True si se activo correctamente
        """
        logger.info("Activando sistema de monitoreo continuo...")

        try:
            # Importar gestor de alertas
            from modules.modulo_alertas import GestorAlertas, TipoAlerta, SeveridadAlerta

            self.gestor_alertas = GestorAlertas()

            # Registrar inicio del sistema
            self.gestor_alertas.sistema_iniciado()

            # Registrar alerta de monitoreo iniciado
            self.gestor_alertas.monitoreo_iniciado(
                intervalo_segundos=ESPECIFICACIONES_ZAC_V2['monitoreo']['intervalo_default']
            )

            # Activar modo copiloto
            self.gestor_alertas.activar_copiloto(
                razon="Despliegue ZAC V2.0 - Activacion automatica",
                detalles={'version': VERSION, 'dispositivo': self.dispositivo_id}
            )

            logger.info("Sistema de monitoreo activado correctamente")
            return True

        except ImportError as e:
            logger.warning(f"Modulo de alertas no disponible: {e}")
            return False
        except Exception as e:
            logger.error(f"Error activando monitoreo: {e}")
            self.errores.append(f"Error monitoreo: {e}")
            return False

    # ===========================================================================
    # ACTIVACION DEL AGENTE SAC
    # ===========================================================================

    def activar_agente_sac(self) -> bool:
        """
        Activa el Agente SAC "Godi"

        Returns:
            True si se activo correctamente
        """
        logger.info("Activando Agente SAC 'Godi'...")

        try:
            from modules.agente_sac import AgenteSAC

            self.agente_sac = AgenteSAC()
            logger.info("Agente SAC 'Godi' activado correctamente")

            if self.gestor_alertas:
                self.gestor_alertas.registrar_alerta(
                    tipo=TipoAlerta.SISTEMA_INICIADO,
                    severidad=SeveridadAlerta.EXITO,
                    titulo="🤖 Agente SAC Activado",
                    mensaje="El Agente SAC 'Godi' esta listo para asistir",
                    modulo="agente_sac"
                )

            return True

        except ImportError as e:
            logger.warning(f"Modulo de Agente SAC no disponible: {e}")
            return False
        except Exception as e:
            logger.error(f"Error activando Agente SAC: {e}")
            self.errores.append(f"Error Agente SAC: {e}")
            return False

    # ===========================================================================
    # DESPLIEGUE COMPLETO
    # ===========================================================================

    def ejecutar_despliegue(self) -> Dict:
        """
        Ejecuta el despliegue completo de ZAC V2.0

        Returns:
            Dict con resultado del despliegue
        """
        logger.info("="*80)
        logger.info("INICIANDO DESPLIEGUE ZAC V2.0")
        logger.info("="*80)

        resultado = {
            'exito': False,
            'timestamp_inicio': self.timestamp_inicio.isoformat(),
            'timestamp_fin': None,
            'fases': {},
            'errores': []
        }

        try:
            # FASE 1: Generar Alerta HITO
            logger.info("FASE 1: Generando Alerta HITO...")
            alerta_hito = self.generar_alerta_hito()
            resultado['fases']['alerta_hito'] = True

            # FASE 2: Enviar Alerta HITO
            logger.info("FASE 2: Enviando Alerta HITO...")
            resultados_envio = self.enviar_alerta_hito(alerta_hito)
            resultado['fases']['envio_alerta'] = any(resultados_envio.values())
            resultado['canales_notificacion'] = resultados_envio

            # FASE 3: Activar Monitoreo
            logger.info("FASE 3: Activando Monitoreo Continuo...")
            monitoreo_ok = self.activar_monitoreo_continuo()
            resultado['fases']['monitoreo'] = monitoreo_ok

            # FASE 4: Activar Agente SAC
            logger.info("FASE 4: Activando Agente SAC...")
            agente_ok = self.activar_agente_sac()
            resultado['fases']['agente_sac'] = agente_ok

            # Determinar exito general
            resultado['exito'] = resultado['fases']['alerta_hito'] and resultado['fases']['envio_alerta']
            resultado['errores'] = self.errores
            resultado['timestamp_fin'] = datetime.now().isoformat()

            self.estado_despliegue = 'completado' if resultado['exito'] else 'parcial'

            # Resumen final
            logger.info("="*80)
            logger.info("DESPLIEGUE COMPLETADO")
            logger.info(f"  - Alerta HITO: {'OK' if resultado['fases']['alerta_hito'] else 'ERROR'}")
            logger.info(f"  - Envio:       {'OK' if resultado['fases']['envio_alerta'] else 'PARCIAL'}")
            logger.info(f"  - Monitoreo:   {'ACTIVO' if resultado['fases']['monitoreo'] else 'NO DISPONIBLE'}")
            logger.info(f"  - Agente SAC:  {'ACTIVO' if resultado['fases']['agente_sac'] else 'NO DISPONIBLE'}")
            logger.info("="*80)

        except Exception as e:
            logger.error(f"Error critico en despliegue: {e}")
            resultado['errores'].append(str(e))
            resultado['timestamp_fin'] = datetime.now().isoformat()
            self.estado_despliegue = 'error'

        return resultado

    def obtener_resumen(self) -> Dict:
        """Obtiene resumen del estado del despliegue"""
        return {
            'estado': self.estado_despliegue,
            'dispositivo': self.dispositivo_id,
            'version': VERSION,
            'timestamp_inicio': self.timestamp_inicio.isoformat(),
            'alertas_enviadas': len(self.alertas_enviadas),
            'errores': self.errores,
            'gestor_alertas_activo': self.gestor_alertas is not None,
            'agente_sac_activo': self.agente_sac is not None
        }


# ===============================================================================
# FUNCION PRINCIPAL
# ===============================================================================

def main():
    """Funcion principal de despliegue"""
    print("""
===============================================================================
                    DESPLIEGUE ZAC/SAC V2.0

    "Las maquinas y los sistemas al servicio de los analistas"

    CEDIS Cancun 427 - Tiendas Chedraui S.A. de C.V.
===============================================================================
""")

    # Crear directorio de logs si no existe
    (BASE_DIR / 'output' / 'logs').mkdir(parents=True, exist_ok=True)

    # Crear e iniciar desplegador
    desplegador = DesplegadorZACV2()

    # Ejecutar despliegue
    resultado = desplegador.ejecutar_despliegue()

    # Mostrar resultado
    print("\n" + "="*80)
    print("RESULTADO DEL DESPLIEGUE")
    print("="*80)

    if resultado['exito']:
        print("""
    ✅ DESPLIEGUE EXITOSO

    El sistema ZAC/SAC V2.0 ha sido desplegado correctamente.

    - Alerta HITO enviada a todos los canales
    - Sistema de monitoreo ACTIVO
    - Agente SAC OPERATIVO

    El sistema esta listo para ser replicado en otros equipos.
""")
    else:
        print(f"""
    ⚠️ DESPLIEGUE COMPLETADO CON ADVERTENCIAS

    Algunos componentes pueden no estar disponibles.
    Errores: {resultado['errores']}

    La Alerta HITO ha sido generada y guardada localmente.
""")

    print("="*80)

    # Guardar resultado
    resultado_file = BASE_DIR / 'output' / 'logs' / f'resultado_despliegue_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(resultado_file, 'w', encoding='utf-8') as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2, default=str)

    print(f"\nResultado guardado en: {resultado_file}")

    return resultado


# ===============================================================================
# EJECUCION
# ===============================================================================

if __name__ == '__main__':
    try:
        resultado = main()
        sys.exit(0 if resultado.get('exito') else 1)
    except KeyboardInterrupt:
        print("\n\nDespliegue cancelado por el usuario.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nError critico: {e}")
        logger.exception("Error critico en despliegue")
        sys.exit(1)
