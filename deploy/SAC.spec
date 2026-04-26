# -*- mode: python ; coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════
PYINSTALLER SPEC FILE - SAC Sistema de Automatización de Consultas
Chedraui CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Este archivo configura la compilación del ejecutable SAC.

Uso:
    pyinstaller SAC.spec

O usar el script de compilación:
    python build_exe.py

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
═══════════════════════════════════════════════════════════════
"""

import os
import sys
from pathlib import Path

# Directorio base del proyecto
BASE_DIR = os.path.dirname(os.path.abspath(SPEC))

# ═══════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE DATOS A INCLUIR
# ═══════════════════════════════════════════════════════════════

# Archivos y carpetas de datos que deben incluirse
datas = [
    # Queries SQL (carpeta completa)
    (os.path.join(BASE_DIR, 'queries'), 'queries'),

    # Configuración
    (os.path.join(BASE_DIR, 'config'), 'config'),

    # Archivo de configuración de plantilla
    (os.path.join(BASE_DIR, 'env'), '.'),

    # Documentación esencial
    (os.path.join(BASE_DIR, 'README.md'), '.'),
]

# Verificar existencia de archivos opcionales
docs_path = os.path.join(BASE_DIR, 'docs')
if os.path.exists(docs_path):
    datas.append((docs_path, 'docs'))

# ═══════════════════════════════════════════════════════════════
# HIDDEN IMPORTS
# ═══════════════════════════════════════════════════════════════

# Módulos que PyInstaller no detecta automáticamente
hiddenimports = [
    # Drivers de base de datos
    'pyodbc',
    'ibm_db',
    'ibm_db_dbi',

    # Pandas y sus dependencias
    'pandas',
    'pandas._libs',
    'pandas._libs.tslibs',
    'pandas._libs.tslibs.np_datetime',
    'pandas._libs.tslibs.nattype',
    'pandas._libs.tslibs.timestamps',

    # NumPy
    'numpy',
    'numpy.core._methods',
    'numpy.lib.format',

    # Excel
    'openpyxl',
    'openpyxl.cell._writer',
    'openpyxl.chart.bar_chart',
    'openpyxl.chart.pie_chart',
    'xlsxwriter',

    # Telegram
    'telegram',
    'telegram.ext',
    'telegram._bot',
    'telegram._message',

    # Flask (si se usa dashboard)
    'flask',
    'jinja2',

    # Email
    'email.mime.text',
    'email.mime.multipart',
    'email.mime.base',

    # Configuración
    'dotenv',
    'yaml',

    # Utilidades
    'colorama',
    'tqdm',
    'schedule',
    'dateutil',
    'pytz',

    # Reportlab para PDF
    'reportlab',
    'reportlab.lib.pagesizes',
    'reportlab.lib.styles',
    'reportlab.platypus',

    # Twilio para WhatsApp
    'twilio',
    'twilio.rest',

    # Pillow para imágenes
    'PIL',
    'PIL.Image',

    # Módulos del proyecto
    'modules',
    'modules.reportes_excel',
    'modules.db_connection',
    'modules.db_pool',
    'modules.db_local',
    'modules.query_builder',
    'modules.excel_styles',
    'modules.chart_generator',
    'modules.export_manager',
    'modules.exportar_pdf',
    'modules.modulo_cartones',
    'modules.modulo_lpn',
    'modules.modulo_ubicaciones',
    'modules.modulo_usuarios',
    'modules.excel_templates',
    'modules.excel_templates.base_template',
    'modules.excel_templates.report_templates',
    'modules.email',
    'modules.email.client',
    'modules.email.scheduler',
    'modules.email.recipients',
    'queries',
    'queries.query_loader',
]

# ═══════════════════════════════════════════════════════════════
# ARCHIVOS A EXCLUIR
# ═══════════════════════════════════════════════════════════════

excludes = [
    'tkinter',
    'matplotlib',
    'scipy',
    'cv2',
    'tensorflow',
    'torch',
    'jupyter',
    'IPython',
    'notebook',
    # Módulos problemáticos en algunos entornos
    'cryptography',
    'nacl',
    'bcrypt',
]

# ═══════════════════════════════════════════════════════════════
# ANÁLISIS
# ═══════════════════════════════════════════════════════════════

a = Analysis(
    ['main.py'],                    # Script principal
    pathex=[BASE_DIR],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# ═══════════════════════════════════════════════════════════════
# PYZ - Archivo comprimido de módulos Python
# ═══════════════════════════════════════════════════════════════

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=None,
)

# ═══════════════════════════════════════════════════════════════
# EJECUTABLE
# ═══════════════════════════════════════════════════════════════

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SAC_Chedraui_427',        # Nombre del ejecutable
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,                       # Compresión UPX
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,                   # Aplicación de consola
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,                      # Agregar icono: 'assets/icon.ico'
)

# ═══════════════════════════════════════════════════════════════
# NOTAS DE COMPILACIÓN
# ═══════════════════════════════════════════════════════════════
#
# Para compilar el ejecutable:
#   1. Instalar dependencias: pip install -r requirements.txt
#   2. Ejecutar: pyinstaller SAC.spec
#
# El ejecutable se generará en dist/SAC_Chedraui_427
#
# IMPORTANTE:
#   - El archivo .env NO se incluye por seguridad
#   - El usuario debe crear su propio .env basado en 'env'
#   - Los directorios output/logs y output/resultados se crean automáticamente
#
# ═══════════════════════════════════════════════════════════════
