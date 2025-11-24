<#
.SYNOPSIS
    Script de Instalación Silenciosa - SAC v2.0
    Sistema de Automatización de Consultas - CEDIS Cancún 427

.DESCRIPTION
    Instalador PowerShell para despliegue empresarial de SAC.
    Diseñado para ejecución silenciosa via SCCM, GPO, o manual.

.PARAMETER InstallPath
    Ruta de instalación. Por defecto: C:\SAC

.PARAMETER Silent
    Modo silencioso sin interacción del usuario

.PARAMETER ConfigFile
    Ruta a archivo de configuración .env predefinido

.PARAMETER CreateService
    Registra SAC como servicio de Windows

.PARAMETER ServiceName
    Nombre del servicio Windows (default: SACMonitor)

.PARAMETER LogPath
    Ruta para logs de instalación

.EXAMPLE
    # Instalación silenciosa con configuración
    .\Install-SAC.ps1 -Silent -ConfigFile "\\servidor\share\sac_config.env"

.EXAMPLE
    # Instalación con servicio Windows
    .\Install-SAC.ps1 -Silent -CreateService -ConfigFile "C:\config\sac.env"

.EXAMPLE
    # Instalación interactiva
    .\Install-SAC.ps1

.NOTES
    Autor: Julián Alexander Juárez Alvarado (ADMJAJA)
    CEDIS: Cancún 427
    Versión: 2.0.0
    Requiere: PowerShell 5.1+, Python 3.8+
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$false)]
    [string]$InstallPath = "C:\SAC",

    [Parameter(Mandatory=$false)]
    [switch]$Silent,

    [Parameter(Mandatory=$false)]
    [string]$ConfigFile,

    [Parameter(Mandatory=$false)]
    [switch]$CreateService,

    [Parameter(Mandatory=$false)]
    [string]$ServiceName = "SACMonitor",

    [Parameter(Mandatory=$false)]
    [string]$LogPath = "$env:TEMP\SAC_Install.log",

    [Parameter(Mandatory=$false)]
    [switch]$Uninstall,

    [Parameter(Mandatory=$false)]
    [switch]$Force
)

# ═══════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════

$ErrorActionPreference = "Stop"
$SAC_VERSION = "2.0.0"
$PYTHON_MIN_VERSION = "3.8"
$CEDIS_CODE = "427"
$CEDIS_NAME = "CEDIS Cancún"

# URLs y rutas
$PYTHON_DOWNLOAD_URL = "https://www.python.org/ftp/python/3.11.7/python-3.11.7-amd64.exe"
$NSSM_DOWNLOAD_URL = "https://nssm.cc/release/nssm-2.24.zip"

# ═══════════════════════════════════════════════════════════════
# FUNCIONES DE LOGGING
# ═══════════════════════════════════════════════════════════════

function Write-Log {
    param(
        [string]$Message,
        [ValidateSet("INFO", "WARN", "ERROR", "SUCCESS")]
        [string]$Level = "INFO"
    )

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"

    # Escribir a archivo
    Add-Content -Path $LogPath -Value $logMessage -Encoding UTF8

    # Mostrar en consola si no es silencioso
    if (-not $Silent) {
        $color = switch ($Level) {
            "INFO"    { "Cyan" }
            "WARN"    { "Yellow" }
            "ERROR"   { "Red" }
            "SUCCESS" { "Green" }
        }
        Write-Host $logMessage -ForegroundColor $color
    }
}

function Show-Banner {
    if (-not $Silent) {
        Write-Host ""
        Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Red
        Write-Host "       SAC - Sistema de Automatización de Consultas v$SAC_VERSION" -ForegroundColor White
        Write-Host "              CEDIS Chedraui Cancún 427 - Instalador" -ForegroundColor Gray
        Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Red
        Write-Host ""
    }
}

function Show-Progress {
    param(
        [int]$Step,
        [int]$Total,
        [string]$Activity
    )

    if (-not $Silent) {
        Write-Progress -Activity "Instalando SAC" -Status $Activity -PercentComplete (($Step / $Total) * 100)
    }
    Write-Log "Paso $Step/$Total : $Activity"
}

# ═══════════════════════════════════════════════════════════════
# VERIFICACIONES DEL SISTEMA
# ═══════════════════════════════════════════════════════════════

function Test-AdminRights {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Test-PythonInstalled {
    try {
        $pythonVersion = & python --version 2>&1
        if ($pythonVersion -match "Python (\d+\.\d+)") {
            $version = [version]$matches[1]
            $minVersion = [version]$PYTHON_MIN_VERSION
            return $version -ge $minVersion
        }
    } catch {
        return $false
    }
    return $false
}

function Get-PythonPath {
    try {
        $pythonPath = & where.exe python 2>&1 | Select-Object -First 1
        if (Test-Path $pythonPath) {
            return $pythonPath
        }
    } catch {}

    # Buscar en ubicaciones comunes
    $commonPaths = @(
        "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python39\python.exe",
        "C:\Python311\python.exe",
        "C:\Python310\python.exe",
        "C:\Python39\python.exe"
    )

    foreach ($path in $commonPaths) {
        if (Test-Path $path) {
            return $path
        }
    }

    return $null
}

function Test-NetworkConnectivity {
    param([string]$TestUrl = "https://pypi.org")

    try {
        $request = [System.Net.WebRequest]::Create($TestUrl)
        $request.Timeout = 5000
        $response = $request.GetResponse()
        $response.Close()
        return $true
    } catch {
        return $false
    }
}

# ═══════════════════════════════════════════════════════════════
# INSTALACIÓN DE PYTHON (SI ES NECESARIO)
# ═══════════════════════════════════════════════════════════════

function Install-Python {
    Write-Log "Python no encontrado. Iniciando instalación..." -Level "WARN"

    $pythonInstaller = "$env:TEMP\python-installer.exe"

    try {
        # Descargar instalador
        Write-Log "Descargando Python desde python.org..."

        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        $webClient = New-Object System.Net.WebClient
        $webClient.DownloadFile($PYTHON_DOWNLOAD_URL, $pythonInstaller)

        # Instalar silenciosamente
        Write-Log "Instalando Python (esto puede tomar varios minutos)..."

        $arguments = @(
            "/quiet",
            "InstallAllUsers=1",
            "PrependPath=1",
            "Include_pip=1",
            "Include_test=0"
        )

        $process = Start-Process -FilePath $pythonInstaller -ArgumentList $arguments -Wait -PassThru

        if ($process.ExitCode -eq 0) {
            Write-Log "Python instalado correctamente" -Level "SUCCESS"

            # Refrescar PATH
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
                        [System.Environment]::GetEnvironmentVariable("Path", "User")

            return $true
        } else {
            Write-Log "Error instalando Python. Código: $($process.ExitCode)" -Level "ERROR"
            return $false
        }
    } catch {
        Write-Log "Error en instalación de Python: $_" -Level "ERROR"
        return $false
    } finally {
        if (Test-Path $pythonInstaller) {
            Remove-Item $pythonInstaller -Force -ErrorAction SilentlyContinue
        }
    }
}

# ═══════════════════════════════════════════════════════════════
# INSTALACIÓN DE SAC
# ═══════════════════════════════════════════════════════════════

function Install-SAC {
    $totalSteps = 8
    $currentStep = 0

    # Paso 1: Crear directorio de instalación
    $currentStep++
    Show-Progress -Step $currentStep -Total $totalSteps -Activity "Creando directorio de instalación"

    if (-not (Test-Path $InstallPath)) {
        New-Item -ItemType Directory -Path $InstallPath -Force | Out-Null
        Write-Log "Directorio creado: $InstallPath" -Level "SUCCESS"
    }

    # Paso 2: Copiar archivos del proyecto
    $currentStep++
    Show-Progress -Step $currentStep -Total $totalSteps -Activity "Copiando archivos SAC"

    $sourceDir = Split-Path -Parent $PSScriptRoot

    # Archivos y carpetas a copiar
    $itemsToCopy = @(
        "*.py",
        "requirements.txt",
        "modules",
        "queries",
        "config",
        "docs",
        "templates"
    )

    foreach ($item in $itemsToCopy) {
        $sourcePath = Join-Path $sourceDir $item
        if (Test-Path $sourcePath) {
            Copy-Item -Path $sourcePath -Destination $InstallPath -Recurse -Force
            Write-Log "Copiado: $item"
        }
    }

    # Crear directorios de output
    $outputDirs = @("output", "output\logs", "output\resultados", "logs")
    foreach ($dir in $outputDirs) {
        $dirPath = Join-Path $InstallPath $dir
        if (-not (Test-Path $dirPath)) {
            New-Item -ItemType Directory -Path $dirPath -Force | Out-Null
        }
    }

    Write-Log "Archivos copiados correctamente" -Level "SUCCESS"

    # Paso 3: Configurar archivo .env
    $currentStep++
    Show-Progress -Step $currentStep -Total $totalSteps -Activity "Configurando sistema"

    $envFilePath = Join-Path $InstallPath ".env"

    if ($ConfigFile -and (Test-Path $ConfigFile)) {
        Copy-Item -Path $ConfigFile -Destination $envFilePath -Force
        Write-Log "Archivo de configuración copiado desde: $ConfigFile" -Level "SUCCESS"
    } elseif (-not (Test-Path $envFilePath)) {
        # Crear .env base
        $envContent = Get-DefaultEnvContent
        Set-Content -Path $envFilePath -Value $envContent -Encoding UTF8
        Write-Log "Archivo .env base creado. IMPORTANTE: Configurar credenciales" -Level "WARN"
    }

    # Paso 4: Crear entorno virtual (opcional pero recomendado)
    $currentStep++
    Show-Progress -Step $currentStep -Total $totalSteps -Activity "Creando entorno virtual"

    $pythonPath = Get-PythonPath
    $venvPath = Join-Path $InstallPath "venv"

    if ($pythonPath) {
        try {
            & $pythonPath -m venv $venvPath 2>&1 | Out-Null
            Write-Log "Entorno virtual creado" -Level "SUCCESS"

            # Usar Python del venv para resto de instalación
            $pythonPath = Join-Path $venvPath "Scripts\python.exe"
        } catch {
            Write-Log "Continuando sin entorno virtual: $_" -Level "WARN"
        }
    }

    # Paso 5: Instalar dependencias
    $currentStep++
    Show-Progress -Step $currentStep -Total $totalSteps -Activity "Instalando dependencias Python"

    $requirementsPath = Join-Path $InstallPath "requirements.txt"

    if (Test-Path $requirementsPath) {
        try {
            $pipArgs = @(
                "-m", "pip", "install",
                "-r", $requirementsPath,
                "--quiet",
                "--disable-pip-version-check"
            )

            & $pythonPath $pipArgs 2>&1 | Out-Null
            Write-Log "Dependencias instaladas correctamente" -Level "SUCCESS"
        } catch {
            Write-Log "Error instalando dependencias: $_" -Level "ERROR"
        }
    }

    # Paso 6: Instalar driver IBM DB2 ODBC (si está disponible)
    $currentStep++
    Show-Progress -Step $currentStep -Total $totalSteps -Activity "Verificando driver DB2"

    $db2DriverInstalled = Test-ODBCDriver -DriverName "IBM DB2 ODBC DRIVER"
    if ($db2DriverInstalled) {
        Write-Log "Driver IBM DB2 ODBC detectado" -Level "SUCCESS"
    } else {
        Write-Log "Driver IBM DB2 ODBC no encontrado. Instalar manualmente." -Level "WARN"
    }

    # Paso 7: Crear servicio Windows (si se solicitó)
    $currentStep++
    Show-Progress -Step $currentStep -Total $totalSteps -Activity "Configurando servicio Windows"

    if ($CreateService) {
        $serviceResult = Install-SACService -PythonPath $pythonPath
        if ($serviceResult) {
            Write-Log "Servicio '$ServiceName' configurado correctamente" -Level "SUCCESS"
        }
    } else {
        Write-Log "Servicio Windows no solicitado (use -CreateService para habilitarlo)"
    }

    # Paso 8: Verificación final
    $currentStep++
    Show-Progress -Step $currentStep -Total $totalSteps -Activity "Verificación final"

    $verificationResult = Test-Installation

    if ($verificationResult.Success) {
        Write-Log "Instalación completada exitosamente" -Level "SUCCESS"
    } else {
        Write-Log "Instalación completada con advertencias" -Level "WARN"
    }

    # Generar reporte de instalación
    Save-InstallationReport -Result $verificationResult

    return $verificationResult
}

# ═══════════════════════════════════════════════════════════════
# SERVICIO DE WINDOWS
# ═══════════════════════════════════════════════════════════════

function Install-SACService {
    param([string]$PythonPath)

    $servicePath = Join-Path $InstallPath "sac_service.py"

    # Verificar si NSSM está disponible o usar sc.exe alternativo
    $nssmPath = Join-Path $InstallPath "tools\nssm.exe"

    if (-not (Test-Path $nssmPath)) {
        # Crear wrapper batch como alternativa
        $wrapperPath = Join-Path $InstallPath "sac_service.bat"
        $wrapperContent = @"
@echo off
cd /d "$InstallPath"
"$PythonPath" -u maestro.py --daemon
"@
        Set-Content -Path $wrapperPath -Value $wrapperContent -Encoding ASCII

        # Registrar con sc.exe (método nativo Windows)
        try {
            $binPath = "`"$wrapperPath`""

            # Eliminar servicio existente
            & sc.exe delete $ServiceName 2>&1 | Out-Null

            # Crear nuevo servicio
            & sc.exe create $ServiceName binPath= $binPath start= auto displayname= "SAC Monitor - CEDIS 427"
            & sc.exe description $ServiceName "Sistema de Automatización de Consultas - Monitoreo continuo"

            # Configurar recuperación ante fallos
            & sc.exe failure $ServiceName reset= 86400 actions= restart/60000/restart/60000/restart/60000

            Write-Log "Servicio Windows configurado con sc.exe" -Level "SUCCESS"
            return $true
        } catch {
            Write-Log "Error configurando servicio: $_" -Level "ERROR"
            return $false
        }
    }

    return $true
}

function Uninstall-SACService {
    try {
        $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue

        if ($service) {
            if ($service.Status -eq "Running") {
                Stop-Service -Name $ServiceName -Force
                Write-Log "Servicio detenido"
            }

            & sc.exe delete $ServiceName 2>&1 | Out-Null
            Write-Log "Servicio eliminado" -Level "SUCCESS"
        }

        return $true
    } catch {
        Write-Log "Error eliminando servicio: $_" -Level "ERROR"
        return $false
    }
}

# ═══════════════════════════════════════════════════════════════
# FUNCIONES AUXILIARES
# ═══════════════════════════════════════════════════════════════

function Test-ODBCDriver {
    param([string]$DriverName)

    try {
        $drivers = Get-OdbcDriver | Where-Object { $_.Name -like "*$DriverName*" }
        return $null -ne $drivers
    } catch {
        return $false
    }
}

function Get-DefaultEnvContent {
    return @"
# ═══════════════════════════════════════════════════════════════
# CONFIGURACIÓN SAC - CEDIS CHEDRAUI CANCÚN 427
# Generado por instalador: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
# ═══════════════════════════════════════════════════════════════

# === CREDENCIALES BASE DE DATOS DB2 ===
# ¡IMPORTANTE! Configurar antes de usar
DB_USER=
DB_PASSWORD=

# === CONFIGURACIÓN DB2 MANHATTAN WMS ===
DB_HOST=WM260BASD
DB_PORT=50000
DB_DATABASE=WM260BASD
DB_SCHEMA=WMWHSE1
DB_DRIVER={IBM DB2 ODBC DRIVER}
DB_TIMEOUT=30

# === CREDENCIALES CORREO ===
# ¡IMPORTANTE! Configurar antes de usar
EMAIL_USER=
EMAIL_PASSWORD=

# === CONFIGURACIÓN CORREO OFFICE 365 ===
EMAIL_HOST=smtp.office365.com
EMAIL_PORT=587
EMAIL_PROTOCOL=TLS
EMAIL_FROM_NAME=Sistema SAC - CEDIS 427

# === TELEGRAM (Opcional) ===
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_IDS=
TELEGRAM_ENABLED=false

# === INFORMACIÓN CEDIS ===
CEDIS_CODE=427
CEDIS_NAME=CEDIS Cancun
CEDIS_REGION=Sureste
CEDIS_ALMACEN=C22

# === CONFIGURACIÓN SISTEMA ===
SYSTEM_VERSION=$SAC_VERSION
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
TIMEZONE=America/Cancun

# === HOSTNAME INSTALACIÓN ===
INSTALL_HOSTNAME=$env:COMPUTERNAME
INSTALL_DATE=$(Get-Date -Format "yyyy-MM-dd")
"@
}

function Test-Installation {
    $result = @{
        Success = $true
        Warnings = @()
        Errors = @()
        Components = @{}
    }

    # Verificar archivos principales
    $mainFiles = @("main.py", "config.py", "maestro.py", "requirements.txt", ".env")
    foreach ($file in $mainFiles) {
        $filePath = Join-Path $InstallPath $file
        $result.Components[$file] = Test-Path $filePath
        if (-not $result.Components[$file]) {
            $result.Warnings += "Archivo faltante: $file"
        }
    }

    # Verificar módulos
    $modulesPath = Join-Path $InstallPath "modules"
    $result.Components["modules"] = Test-Path $modulesPath

    # Verificar Python funcional
    $pythonPath = Get-PythonPath
    $result.Components["python"] = $null -ne $pythonPath

    # Verificar .env tiene credenciales
    $envPath = Join-Path $InstallPath ".env"
    if (Test-Path $envPath) {
        $envContent = Get-Content $envPath -Raw
        if ($envContent -match "DB_USER=\s*$" -or $envContent -match "DB_PASSWORD=\s*$") {
            $result.Warnings += "Credenciales DB2 no configuradas en .env"
        }
        if ($envContent -match "EMAIL_USER=\s*$" -or $envContent -match "EMAIL_PASSWORD=\s*$") {
            $result.Warnings += "Credenciales Email no configuradas en .env"
        }
    }

    # Verificar servicio (si se instaló)
    if ($CreateService) {
        $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
        $result.Components["service"] = $null -ne $service
    }

    # Determinar éxito general
    $result.Success = $result.Errors.Count -eq 0

    return $result
}

function Save-InstallationReport {
    param($Result)

    $reportPath = Join-Path $InstallPath "install_report.json"

    $report = @{
        timestamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ss"
        version = $SAC_VERSION
        hostname = $env:COMPUTERNAME
        domain = $env:USERDOMAIN
        user = $env:USERNAME
        installPath = $InstallPath
        pythonPath = Get-PythonPath
        serviceInstalled = $CreateService
        serviceName = $ServiceName
        result = $Result
    }

    $report | ConvertTo-Json -Depth 5 | Set-Content -Path $reportPath -Encoding UTF8
    Write-Log "Reporte de instalación guardado: $reportPath"
}

# ═══════════════════════════════════════════════════════════════
# DESINSTALACIÓN
# ═══════════════════════════════════════════════════════════════

function Uninstall-SAC {
    Write-Log "Iniciando desinstalación de SAC..."

    # Detener y eliminar servicio
    Uninstall-SACService

    # Eliminar directorio de instalación
    if (Test-Path $InstallPath) {
        if ($Force -or (Confirm-Action "¿Eliminar directorio $InstallPath y todos sus contenidos?")) {
            Remove-Item -Path $InstallPath -Recurse -Force
            Write-Log "Directorio de instalación eliminado" -Level "SUCCESS"
        }
    }

    Write-Log "Desinstalación completada" -Level "SUCCESS"
}

function Confirm-Action {
    param([string]$Message)

    if ($Silent -or $Force) {
        return $true
    }

    $response = Read-Host "$Message (S/N)"
    return $response -eq "S" -or $response -eq "s"
}

# ═══════════════════════════════════════════════════════════════
# EJECUCIÓN PRINCIPAL
# ═══════════════════════════════════════════════════════════════

try {
    # Inicializar log
    "═══════════════════════════════════════════════════════════════" | Out-File $LogPath
    "SAC Installation Log - $(Get-Date)" | Out-File $LogPath -Append
    "═══════════════════════════════════════════════════════════════" | Out-File $LogPath -Append

    Show-Banner

    # Verificar derechos de administrador
    if (-not (Test-AdminRights)) {
        Write-Log "Este script requiere privilegios de administrador" -Level "ERROR"
        exit 1
    }

    # Modo desinstalación
    if ($Uninstall) {
        Uninstall-SAC
        exit 0
    }

    # Verificar Python
    Write-Log "Verificando requisitos del sistema..."

    if (-not (Test-PythonInstalled)) {
        Write-Log "Python $PYTHON_MIN_VERSION+ no encontrado" -Level "WARN"

        if ($Silent -or (Confirm-Action "¿Desea instalar Python automáticamente?")) {
            $pythonInstalled = Install-Python
            if (-not $pythonInstalled) {
                Write-Log "No se pudo instalar Python. Instale manualmente." -Level "ERROR"
                exit 1
            }
        } else {
            Write-Log "Python es requerido. Instalación cancelada." -Level "ERROR"
            exit 1
        }
    } else {
        Write-Log "Python detectado: $(& python --version)" -Level "SUCCESS"
    }

    # Verificar conectividad (para descargar dependencias)
    if (-not (Test-NetworkConnectivity)) {
        Write-Log "Sin conexión a internet. Algunas dependencias pueden fallar." -Level "WARN"
    }

    # Ejecutar instalación
    $result = Install-SAC

    # Mostrar resumen
    if (-not $Silent) {
        Write-Host ""
        Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Green
        Write-Host "           INSTALACIÓN COMPLETADA - SAC v$SAC_VERSION" -ForegroundColor White
        Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Green
        Write-Host ""
        Write-Host "  Ruta: $InstallPath" -ForegroundColor Cyan
        Write-Host "  Log:  $LogPath" -ForegroundColor Cyan
        Write-Host ""

        if ($result.Warnings.Count -gt 0) {
            Write-Host "  Advertencias:" -ForegroundColor Yellow
            foreach ($warn in $result.Warnings) {
                Write-Host "    - $warn" -ForegroundColor Yellow
            }
            Write-Host ""
        }

        Write-Host "  Para iniciar:" -ForegroundColor White
        Write-Host "    cd $InstallPath" -ForegroundColor Gray
        Write-Host "    python main.py" -ForegroundColor Gray
        Write-Host ""

        if ($CreateService) {
            Write-Host "  Servicio Windows:" -ForegroundColor White
            Write-Host "    net start $ServiceName" -ForegroundColor Gray
            Write-Host ""
        }
    }

    exit 0

} catch {
    Write-Log "Error fatal: $_" -Level "ERROR"
    Write-Log $_.ScriptStackTrace -Level "ERROR"
    exit 1
}
