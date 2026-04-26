# ═══════════════════════════════════════════════════════════════
# INSTALADOR SAC - PowerShell
# Sistema de Automatización de Consultas - CEDIS Cancún 427
# ═══════════════════════════════════════════════════════════════

$ErrorActionPreference = "Continue"
$Host.UI.RawUI.WindowTitle = "Instalador SAC - CEDIS 427"

# Colores
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

# Banner
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Red
Write-Host "              INSTALADOR SAC - CEDIS Cancún 427" -ForegroundColor White
Write-Host "                    Tiendas Chedraui" -ForegroundColor White
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Red
Write-Host ""

# Verificar Python
Write-Host "[1/6] Verificando Python..." -ForegroundColor Cyan
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[OK] $pythonVersion detectado" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python no está instalado" -ForegroundColor Red
    Write-Host ""
    Write-Host "Instala Python desde: https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "IMPORTANTE: Marca 'Add Python to PATH' durante la instalación" -ForegroundColor Yellow
    Read-Host "Presiona Enter para salir"
    exit 1
}

# Crear directorios
Write-Host ""
Write-Host "[2/6] Creando directorios..." -ForegroundColor Cyan
$dirs = @(
    "output",
    "output\logs",
    "output\resultados",
    "output\adjuntos",
    "output\trafico",
    "output\trafico\scheduling",
    "output\agente_sac"
)
foreach ($dir in $dirs) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}
Write-Host "[OK] Directorios creados" -ForegroundColor Green

# Actualizar pip
Write-Host ""
Write-Host "[3/6] Actualizando pip..." -ForegroundColor Cyan
python -m pip install --upgrade pip --quiet 2>$null
Write-Host "[OK] pip actualizado" -ForegroundColor Green

# Instalar dependencias base
Write-Host ""
Write-Host "[4/6] Instalando dependencias base..." -ForegroundColor Cyan
Write-Host "      (Esto puede tardar varios minutos)" -ForegroundColor Gray

$basePackages = @(
    "python-dotenv",
    "colorama",
    "rich",
    "pytz",
    "python-dateutil",
    "openpyxl",
    "XlsxWriter",
    "requests"
)

foreach ($pkg in $basePackages) {
    python -m pip install --user $pkg --quiet 2>$null
}
Write-Host "[OK] Dependencias base instaladas" -ForegroundColor Green

# Instalar numpy y pandas
Write-Host ""
Write-Host "[5/6] Instalando numpy y pandas..." -ForegroundColor Cyan
Write-Host "      (Las dependencias más grandes)" -ForegroundColor Gray

# Intentar numpy
try {
    python -m pip install --user "numpy>=2.0.0" --quiet 2>$null
    Write-Host "[OK] numpy instalado" -ForegroundColor Green
} catch {
    Write-Host "[WARN] numpy requiere versión específica" -ForegroundColor Yellow
    python -m pip install --user numpy==2.1.3 --quiet 2>$null
}

# Intentar pandas
try {
    python -m pip install --user "pandas>=2.2.0" --quiet 2>$null
    Write-Host "[OK] pandas instalado" -ForegroundColor Green
} catch {
    Write-Host "[WARN] pandas requiere versión específica" -ForegroundColor Yellow
    python -m pip install --user pandas==2.2.3 --quiet 2>$null
}

# Instalar resto desde requirements-minimal
Write-Host ""
Write-Host "[6/6] Completando instalación..." -ForegroundColor Cyan
python -m pip install --user -r requirements-minimal.txt --quiet 2>$null

# Verificación
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "                    VERIFICACIÓN" -ForegroundColor White
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

$packages = @{
    "pandas" = "import pandas; print(f'pandas {pandas.__version__}')"
    "numpy" = "import numpy; print(f'numpy {numpy.__version__}')"
    "openpyxl" = "import openpyxl; print(f'openpyxl {openpyxl.__version__}')"
    "dotenv" = "import dotenv; print('python-dotenv OK')"
    "rich" = "import rich; print(f'rich {rich.__version__}')"
}

foreach ($pkg in $packages.Keys) {
    try {
        $result = python -c $packages[$pkg] 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[OK] $result" -ForegroundColor Green
        } else {
            Write-Host "[FALTA] $pkg" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "[FALTA] $pkg" -ForegroundColor Yellow
    }
}

# Configuración .env
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "                    CONFIGURACIÓN" -ForegroundColor White
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

if (!(Test-Path ".env")) {
    if (Test-Path "config\.env.example") {
        Copy-Item "config\.env.example" ".env"
        Write-Host "[OK] Archivo .env creado desde plantilla" -ForegroundColor Green
        Write-Host ""
        Write-Host "IMPORTANTE: Edita el archivo .env con tus credenciales:" -ForegroundColor Yellow
        Write-Host "  - DB_USER: Tu usuario de base de datos" -ForegroundColor Gray
        Write-Host "  - DB_PASSWORD: Tu contraseña de base de datos" -ForegroundColor Gray
        Write-Host "  - EMAIL_USER: Tu correo corporativo" -ForegroundColor Gray
        Write-Host "  - EMAIL_PASSWORD: Tu contraseña de correo" -ForegroundColor Gray
    } else {
        Write-Host "[WARN] No se encontró config\.env.example" -ForegroundColor Yellow
    }
} else {
    Write-Host "[OK] Archivo .env ya existe" -ForegroundColor Green
}

# Resumen final
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "                    INSTALACIÓN COMPLETADA" -ForegroundColor White
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Host "Próximos pasos:" -ForegroundColor Cyan
Write-Host "  1. Edita el archivo .env con tus credenciales" -ForegroundColor White
Write-Host "  2. Ejecuta: python verificar_sistema.py" -ForegroundColor White
Write-Host "  3. Inicia el sistema: python main.py" -ForegroundColor White
Write-Host ""

Read-Host "Presiona Enter para continuar"
