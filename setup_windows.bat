@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

echo.
echo ═══════════════════════════════════════════════════════════════
echo              INSTALADOR SAC - CEDIS Cancún 427
echo                    Tiendas Chedraui
echo ═══════════════════════════════════════════════════════════════
echo.

:: Verificar si Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no está instalado o no está en el PATH
    echo.
    echo Por favor, instala Python desde:
    echo https://www.python.org/downloads/
    echo.
    echo IMPORTANTE: Marca la opción "Add Python to PATH" durante la instalación
    pause
    exit /b 1
)

:: Mostrar versión de Python
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [OK] Python %PYTHON_VERSION% detectado
echo.

:: Crear directorios necesarios
echo [1/5] Creando directorios necesarios...
if not exist "output" mkdir output
if not exist "output\logs" mkdir output\logs
if not exist "output\resultados" mkdir output\resultados
if not exist "output\adjuntos" mkdir output\adjuntos
if not exist "output\trafico" mkdir output\trafico
if not exist "output\trafico\scheduling" mkdir output\trafico\scheduling
if not exist "output\agente_sac" mkdir output\agente_sac
echo [OK] Directorios creados
echo.

:: Actualizar pip
echo [2/5] Actualizando pip...
python -m pip install --upgrade pip --quiet
echo [OK] pip actualizado
echo.

:: Instalar dependencias mínimas primero
echo [3/5] Instalando dependencias mínimas...
echo        (Esto puede tardar varios minutos)
echo.

:: Intentar instalación mínima primero
python -m pip install --user python-dotenv colorama rich pytz python-dateutil 2>nul
if errorlevel 1 (
    echo [ADVERTENCIA] Algunas dependencias básicas fallaron, continuando...
)

:: Instalar numpy y pandas (las más problemáticas en Python 3.13)
echo.
echo [4/5] Instalando numpy y pandas...
echo        (Estas son las dependencias más grandes)
echo.

python -m pip install --user "numpy>=2.0.0" 2>nul
if errorlevel 1 (
    echo [ADVERTENCIA] numpy falló. Intentando versión específica...
    python -m pip install --user numpy==2.1.3 2>nul
)

python -m pip install --user "pandas>=2.2.0" 2>nul
if errorlevel 1 (
    echo [ADVERTENCIA] pandas falló. Intentando versión específica...
    python -m pip install --user pandas==2.2.3 2>nul
)

:: Instalar el resto de dependencias
echo.
echo [5/5] Instalando resto de dependencias...
python -m pip install --user -r requirements-minimal.txt 2>nul
if errorlevel 1 (
    echo [ADVERTENCIA] Algunas dependencias opcionales fallaron
    echo              El sistema funcionará con funcionalidad reducida
)

:: Verificar instalación crítica
echo.
echo ═══════════════════════════════════════════════════════════════
echo                    VERIFICACIÓN
echo ═══════════════════════════════════════════════════════════════
echo.

python -c "import pandas; print(f'[OK] pandas {pandas.__version__}')" 2>nul || echo [FALTA] pandas
python -c "import numpy; print(f'[OK] numpy {numpy.__version__}')" 2>nul || echo [FALTA] numpy
python -c "import openpyxl; print(f'[OK] openpyxl {openpyxl.__version__}')" 2>nul || echo [FALTA] openpyxl
python -c "import dotenv; print('[OK] python-dotenv')" 2>nul || echo [FALTA] python-dotenv
python -c "import rich; print(f'[OK] rich {rich.__version__}')" 2>nul || echo [FALTA] rich

echo.
echo ═══════════════════════════════════════════════════════════════
echo                    CONFIGURACIÓN
echo ═══════════════════════════════════════════════════════════════
echo.

:: Crear .env si no existe
if not exist ".env" (
    if exist "config\.env.example" (
        copy "config\.env.example" ".env" >nul
        echo [OK] Archivo .env creado desde plantilla
        echo.
        echo IMPORTANTE: Edita el archivo .env con tus credenciales:
        echo   - DB_USER: Tu usuario de base de datos
        echo   - DB_PASSWORD: Tu contraseña de base de datos
        echo   - EMAIL_USER: Tu correo corporativo
        echo   - EMAIL_PASSWORD: Tu contraseña de correo
    ) else (
        echo [ADVERTENCIA] No se encontró config\.env.example
        echo              Crea el archivo .env manualmente
    )
) else (
    echo [OK] Archivo .env ya existe
)

echo.
echo ═══════════════════════════════════════════════════════════════
echo                    INSTALACIÓN COMPLETADA
echo ═══════════════════════════════════════════════════════════════
echo.
echo Próximos pasos:
echo   1. Edita el archivo .env con tus credenciales
echo   2. Ejecuta: python verificar_sistema.py
echo   3. Inicia el sistema: python main.py
echo.
echo Si tienes problemas con la instalación, consulta:
echo   docs\INSTALACION_WINDOWS.md
echo.
pause
