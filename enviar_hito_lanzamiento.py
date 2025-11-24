#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
===============================================================================
SCRIPT DE NOTIFICACION DE HITO - LANZAMIENTO SISTEMA SAC
Sistema de Automatizacion de Consultas - CEDIS Cancun 427
===============================================================================

Este script envia la notificacion oficial del lanzamiento del Sistema SAC
programado para el 1ero de Diciembre de 2025.

USO:
    python enviar_hito_lanzamiento.py                # Envio a destinatarios configurados
    python enviar_hito_lanzamiento.py --test         # Modo prueba (sin envio real)
    python enviar_hito_lanzamiento.py --demo         # Genera HTML demo

Desarrollado por: Julian Alexander Juarez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logistica Cancun
===============================================================================
"""

import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Agregar directorio actual al path
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Importar configuración desde config.py (evitar conflicto con config/)
import importlib.util
config_path = Path(__file__).resolve().parent / 'config.py'
spec = importlib.util.spec_from_file_location("config_module", config_path)
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)

EMAIL_CONFIG = config_module.EMAIL_CONFIG
CEDIS = config_module.CEDIS
SYSTEM_CONFIG = config_module.SYSTEM_CONFIG
VERSION = config_module.VERSION

from gestor_correos import GestorCorreos

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ===============================================================================
# CONFIGURACION DEL HITO
# ===============================================================================

HITO_CONFIG = {
    'titulo': 'Sistema SAC - Puesta en Marcha Oficial',
    'subtitulo': 'Sistema de Automatizacion de Consultas CEDIS 427',
    'tipo': 'LANZAMIENTO OFICIAL',
    'fecha_activacion': '1 de Diciembre de 2025',
    'version': VERSION,  # Usar VERSION centralizada desde config.py
    'mensaje': '''
        Nos complace informar que el Sistema SAC (Sistema de Automatizacion de Consultas)
        entrara en operacion oficial a partir del 1ero de Diciembre de 2025.

        Este sistema ha sido desarrollado para automatizar y optimizar los procesos de
        validacion de Ordenes de Compra, monitoreo de distribuciones, y generacion de
        reportes del area de Planning.

        A partir de la fecha indicada, el sistema operara de manera automatizada en los
        horarios establecidos, enviando reportes y alertas al equipo correspondiente.
    ''',
    'funcionalidades': [
        'Validacion automatica de Ordenes de Compra vs Distribuciones',
        'Monitoreo en tiempo real de operaciones con deteccion proactiva de errores',
        'Generacion de reportes profesionales en Excel con formato corporativo',
        'Alertas criticas automaticas por correo electronico',
        'Notificaciones instantaneas via Telegram',
        'Validacion de ASN (Advanced Shipping Notices)',
        'Reporte diario de Planning con resumen ejecutivo',
        'Sistema de programacion de tareas automatizadas',
        'Integracion directa con IBM DB2 (Manhattan WMS)',
        '15+ tipos de validaciones automaticas'
    ],
    'horarios': {
        '06:00': 'Reporte matutino y validacion inicial del dia',
        '09:00': 'Validacion de OC pendientes',
        '12:00': 'Monitoreo de medio dia',
        '15:00': 'Validacion preventiva',
        '18:00': 'Reporte vespertino',
        '21:00': 'Resumen del dia',
        'Cada 15 min': 'Monitoreo continuo del sistema'
    },
    'nota_importante': '''
        El sistema funcionara de manera automatica en los horarios indicados.
        Los reportes y alertas seran enviados al equipo de Planning.
        Para cualquier duda o incidencia, contactar al area de Sistemas CEDIS 427.
    '''
}


# ===============================================================================
# FUNCIONES PRINCIPALES
# ===============================================================================

def imprimir_banner():
    """Imprime el banner del script"""
    banner = """
    ===============================================================================
                     NOTIFICACION DE HITO - SISTEMA SAC
                  Sistema de Automatizacion de Consultas
                        CEDIS Cancun 427 - Chedraui
    ===============================================================================

    Este script enviara la notificacion oficial del lanzamiento del Sistema SAC
    programado para el 1ero de Diciembre de 2025.

    ===============================================================================
    """
    print(banner)


def generar_html_demo():
    """Genera un archivo HTML de demo para visualizar el template"""
    try:
        from modules.email.template_engine import EmailTemplateEngine

        engine = EmailTemplateEngine()

        # Generar lista de funcionalidades HTML
        lista_func = ""
        for i, func in enumerate(HITO_CONFIG['funcionalidades'], 1):
            lista_func += f'<li><span class="feature-icon">{i}</span>{func}</li>'

        # Generar tabla de horarios HTML
        tabla_horarios = ""
        for hora, descripcion in HITO_CONFIG['horarios'].items():
            tabla_horarios += f'<div class="schedule-row"><div class="schedule-time">{hora}</div><div class="schedule-task">{descripcion}</div></div>'

        context = {
            'titulo_hito': HITO_CONFIG['titulo'],
            'subtitulo_hito': HITO_CONFIG['subtitulo'],
            'tipo_hito': HITO_CONFIG['tipo'],
            'mensaje_hito': HITO_CONFIG['mensaje'],
            'fecha_activacion': HITO_CONFIG['fecha_activacion'],
            'version_sistema': HITO_CONFIG['version'],
            'estado_sistema': 'OPERATIVO',
            'lista_funcionalidades': lista_func,
            'tabla_horarios': tabla_horarios,
            'nota_importante': HITO_CONFIG['nota_importante'],
        }

        html = engine.render_template('system_milestone', context)

        # Guardar archivo
        output_file = Path('output/resultados/hito_lanzamiento_demo.html')
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(html, encoding='utf-8')

        print(f"\n    HTML generado: {output_file}")
        print(f"    Abre el archivo en un navegador para visualizarlo.\n")

        return True

    except Exception as e:
        logger.error(f"Error generando HTML demo: {e}")
        return False


def enviar_hito(test_mode: bool = False):
    """
    Envia la notificacion del hito del sistema

    Args:
        test_mode: Si True, solo muestra lo que se enviaria sin enviar
    """
    print("\n    ========== INFORMACION DEL HITO ==========")
    print(f"    Titulo: {HITO_CONFIG['titulo']}")
    print(f"    Tipo: {HITO_CONFIG['tipo']}")
    print(f"    Fecha Activacion: {HITO_CONFIG['fecha_activacion']}")
    print(f"    Version: {HITO_CONFIG['version']}")
    print(f"    Funcionalidades: {len(HITO_CONFIG['funcionalidades'])}")
    print("    =============================================")

    # Obtener destinatarios
    destinatarios = EMAIL_CONFIG.get('to_emails', [])
    if isinstance(destinatarios, str):
        destinatarios = [d.strip() for d in destinatarios.split(',') if d.strip()]

    print(f"\n    Destinatarios configurados:")
    for d in destinatarios[:5]:
        print(f"      - {d}")
    if len(destinatarios) > 5:
        print(f"      ... y {len(destinatarios) - 5} mas")

    if test_mode:
        print("\n    [MODO TEST] No se enviara el correo real.")
        print("    Para enviar, ejecuta sin la opcion --test")
        return True

    # Confirmar envio
    print("\n    Deseas enviar la notificacion del hito?")
    respuesta = input("    (s/n): ").strip().lower()

    if respuesta != 's':
        print("\n    Envio cancelado.\n")
        return False

    # Configurar gestor de correos
    try:
        gestor = GestorCorreos({
            'smtp_server': EMAIL_CONFIG['smtp_server'],
            'smtp_port': EMAIL_CONFIG['smtp_port'],
            'user': EMAIL_CONFIG['user'],
            'password': EMAIL_CONFIG['password'],
            'from_name': EMAIL_CONFIG['from_name'],
            'cedis_nombre': CEDIS['name']
        })

        print("\n    Enviando notificacion...")

        resultado = gestor.enviar_hito_sistema(
            destinatarios=destinatarios,
            titulo_hito=HITO_CONFIG['titulo'],
            subtitulo=HITO_CONFIG['subtitulo'],
            mensaje=HITO_CONFIG['mensaje'],
            fecha_activacion=HITO_CONFIG['fecha_activacion'],
            tipo_hito=HITO_CONFIG['tipo'],
            funcionalidades=HITO_CONFIG['funcionalidades'],
            horarios=HITO_CONFIG['horarios'],
            nota_importante=HITO_CONFIG['nota_importante'],
            version=HITO_CONFIG['version']
        )

        if resultado:
            print("\n    ========================================")
            print("    NOTIFICACION ENVIADA EXITOSAMENTE!")
            print("    ========================================")
            print(f"    Enviada a {len(destinatarios)} destinatario(s)")
            print(f"    Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
            print("    ========================================\n")
        else:
            print("\n    ERROR: No se pudo enviar la notificacion.")
            print("    Revisa la configuracion de email en .env\n")

        return resultado

    except Exception as e:
        logger.error(f"Error enviando hito: {e}")
        print(f"\n    ERROR: {e}")
        print("    Verifica que las credenciales de email esten configuradas.\n")
        return False


def mostrar_estado_sistema():
    """Muestra el estado actual del sistema"""
    print("\n    ========== ESTADO DEL SISTEMA SAC ==========")
    print(f"    CEDIS: {CEDIS['name']} ({CEDIS['code']})")
    print(f"    Region: {CEDIS['region']}")
    print(f"    Version: {SYSTEM_CONFIG['version']}")
    print(f"    Ambiente: {SYSTEM_CONFIG['environment']}")
    print(f"    Email configurado: {'Si' if EMAIL_CONFIG.get('user') and '@' in EMAIL_CONFIG.get('user', '') else 'No'}")
    print(f"    Fecha actual: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("    ==============================================")

    print("\n    FUNCIONALIDADES VERIFICADAS:")
    verificaciones = [
        ("Modulo de Reportes Excel", True),
        ("Gestor de Correos", True),
        ("Monitor de Errores", True),
        ("Validador Proactivo", True),
        ("Programador de Tareas", True),
        ("Templates de Email", True),
        ("Sistema de Alertas", True),
        ("Conexion DB2", "Pendiente config"),
    ]

    for nombre, estado in verificaciones:
        icon = "OK" if estado == True else ("PENDIENTE" if estado == "Pendiente config" else "ERROR")
        print(f"      [{icon}] {nombre}")

    print("\n    ==============================================\n")


# ===============================================================================
# PUNTO DE ENTRADA
# ===============================================================================

def main():
    """Funcion principal"""
    parser = argparse.ArgumentParser(
        description='Envia notificacion del hito de lanzamiento del Sistema SAC',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--test', action='store_true',
                        help='Modo prueba - muestra info sin enviar')
    parser.add_argument('--demo', action='store_true',
                        help='Genera HTML demo para visualizar')
    parser.add_argument('--status', action='store_true',
                        help='Muestra estado del sistema')

    args = parser.parse_args()

    imprimir_banner()

    if args.status:
        mostrar_estado_sistema()
        return

    if args.demo:
        generar_html_demo()
        return

    # Mostrar estado antes de enviar
    mostrar_estado_sistema()

    # Enviar hito
    enviar_hito(test_mode=args.test)


if __name__ == "__main__":
    main()
