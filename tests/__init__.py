"""
Tests del Sistema SAC
=====================

Módulo de pruebas unitarias y de integración
para el Sistema de Automatización de Consultas.
"""

import sys
from pathlib import Path

# Agregar el directorio raíz al path para imports correctos
root_dir = Path(__file__).parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

# Importar versión desde configuración centralizada
from config import VERSION

__version__ = VERSION
