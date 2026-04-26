#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
#  SAC - Sistema de Automatización de Consultas
#  CEDIS Chedraui Cancún 427 - Región Sureste
#
#  EJECUTAR ESTE ARCHIVO PARA INICIAR SAC
#  La instalación es completamente automática
# ═══════════════════════════════════════════════════════════════════════════════

# Colores
ROJO='\033[0;31m'
VERDE='\033[0;32m'
AMARILLO='\033[0;33m'
CYAN='\033[0;36m'
RESET='\033[0m'

# Cambiar al directorio del script
cd "$(dirname "$0")"

echo ""
echo "═══════════════════════════════════════════════════════════════════════════════"
echo -e "  ${CYAN}SAC - Sistema de Automatización de Consultas${RESET}"
echo -e "  ${AMARILLO}CEDIS Chedraui Cancún 427 - Región Sureste${RESET}"
echo "═══════════════════════════════════════════════════════════════════════════════"
echo ""

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo -e "${ROJO}ERROR: Python 3 no está instalado${RESET}"
    echo ""
    echo "Por favor instale Python 3.8 o superior:"
    echo "  Ubuntu/Debian: sudo apt install python3 python3-pip python3-tk"
    echo "  CentOS/RHEL:   sudo yum install python3 python3-pip python3-tkinter"
    echo "  macOS:         brew install python3 python-tk"
    echo ""
    exit 1
fi

# Verificar versión de Python
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
    echo -e "${ROJO}ERROR: Se requiere Python 3.8 o superior${RESET}"
    echo "Versión actual: Python $PYTHON_VERSION"
    exit 1
fi

echo -e "${VERDE}✓ Python $PYTHON_VERSION detectado${RESET}"
echo ""

# Ejecutar SAC
python3 SAC.py

# Código de salida
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo -e "${ROJO}SAC terminó con errores (código: $EXIT_CODE)${RESET}"
    echo "Presione Enter para cerrar..."
    read
fi

exit $EXIT_CODE
