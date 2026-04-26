# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller Specification File
Sistema de Automatizacion de Consultas - SAC
CEDIS Cancun 427 - Tiendas Chedraui
"""

import sys
from pathlib import Path

block_cipher = None

# Obtener ruta base del proyecto
base_path = Path.cwd()

# Archivos de datos a incluir
datas = [
    ('config', 'config'),
    ('queries', 'queries'),
    ('docs', 'docs'),
    ('modules', 'modules'),
    ('env', '.'),
    ('README.md', '.'),
    ('CLAUDE.md', '.'),
]

# Imports ocultos necesarios
hiddenimports = [
    'config',
    'monitor',
    'gestor_correos',
    'notificaciones_telegram',
    'notificaciones_whatsapp',
    'dashboard',
    'maestro',
    'modules',
    'modules.db_connection',
    'modules.db_pool',
    'modules.db_local',
    'modules.db_schema',
    'modules.reportes_excel',
    'modules.chart_generator',
    'modules.excel_styles',
    'modules.excel_templates',
    'modules.export_manager',
    'modules.exportar_pdf',
    'modules.modulo_cartones',
    'modules.modulo_lpn',
    'modules.modulo_ubicaciones',
    'modules.modulo_usuarios',
    'modules.pivot_generator',
    'modules.query_builder',
    'modules.email',
    'modules.email.email_client',
    'modules.email.email_message',
    'modules.email.queue',
    'modules.email.recipients',
    'modules.email.scheduler',
    'modules.email.template_engine',
    'modules.repositories',
    'modules.repositories.base_repository',
    'modules.repositories.oc_repository',
    'modules.repositories.distribution_repository',
    'modules.repositories.asn_repository',
    'queries',
    'queries.query_loader',
    'pandas',
    'openpyxl',
    'dotenv',
    'smtplib',
    'email',
    'sqlite3',
]

a = Analysis(
    ['main.py'],
    pathex=[str(base_path)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SAC_CEDIS_427',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Agregar icono si existe: 'assets/sac_icon.ico'
)
