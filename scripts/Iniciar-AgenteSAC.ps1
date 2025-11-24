# ═══════════════════════════════════════════════════════════════
# AGENTE SAC - Script de Inicio PowerShell
# CEDIS Cancún 427 - Tiendas Chedraui
# ═══════════════════════════════════════════════════════════════
#
# Este script inicia el Agente SAC al iniciar sesión en Windows.
# Puede ser desplegado via GPO para toda la red.
#
# SOLO EL ADMINISTRADOR u427jd15 TIENE ACCESO COMPLETO AL AGENTE CLI
#
# Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
# ═══════════════════════════════════════════════════════════════

param(
    [switch]$Silencioso,
    [switch]$SoloNotificaciones,
    [string]$Comando,
    [switch]$Instalar,
    [switch]$Desinstalar
)

# Configuración
$SAC_DIR = "C:\SAC_V01_427_ADMJAJA"
$STARTUP_DIR = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup"
$SHORTCUT_NAME = "Agente SAC.lnk"

# Función para crear acceso directo
function New-AgentShortcut {
    $WshShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut("$STARTUP_DIR\$SHORTCUT_NAME")
    $Shortcut.TargetPath = "pythonw.exe"
    $Shortcut.Arguments = "$SAC_DIR\iniciar_agente.py --silencioso"
    $Shortcut.WorkingDirectory = $SAC_DIR
    $Shortcut.Description = "Agente SAC - Asistente Virtual CEDIS 427"
    $Shortcut.IconLocation = "$SAC_DIR\assets\icon.ico,0"
    $Shortcut.Save()

    Write-Host "✅ Agente SAC instalado en el inicio de sesión" -ForegroundColor Green
}

# Función para eliminar acceso directo
function Remove-AgentShortcut {
    $shortcutPath = "$STARTUP_DIR\$SHORTCUT_NAME"
    if (Test-Path $shortcutPath) {
        Remove-Item $shortcutPath -Force
        Write-Host "✅ Agente SAC eliminado del inicio de sesión" -ForegroundColor Yellow
    } else {
        Write-Host "ℹ️ El Agente SAC no estaba instalado en el inicio" -ForegroundColor Cyan
    }
}

# Procesar parámetros
if ($Instalar) {
    New-AgentShortcut
    exit 0
}

if ($Desinstalar) {
    Remove-AgentShortcut
    exit 0
}

# Verificar directorio
if (-not (Test-Path $SAC_DIR)) {
    Write-Host "❌ Error: No se encontró el directorio del SAC: $SAC_DIR" -ForegroundColor Red
    exit 1
}

# Cambiar al directorio
Set-Location $SAC_DIR

# Verificar Python
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Python no encontrado"
    }
} catch {
    Write-Host "❌ Error: Python no está instalado o no está en el PATH" -ForegroundColor Red
    exit 1
}

# Construir argumentos
$args = @()

if ($Silencioso) {
    $args += "--silencioso"
}

if ($SoloNotificaciones) {
    $args += "--notificacion"
}

if ($Comando) {
    $args += "--comando"
    $args += $Comando
}

# Ejecutar Agente SAC
Write-Host ""
Write-Host "════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  🤖 Iniciando Agente SAC - CEDIS 427" -ForegroundColor Cyan
Write-Host "  Tiendas Chedraui S.A. de C.V." -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Ejecutar
python iniciar_agente.py $args
