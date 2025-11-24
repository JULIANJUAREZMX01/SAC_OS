# ═══════════════════════════════════════════════════════════════════════════
# SCRIPT MAESTRO DE LIMPIEZA COMPLETA
# Sistema de Mantenimiento Windows - CEDIS Chedraui Cancún 427
# ═══════════════════════════════════════════════════════════════════════════
# Descripción: Script completo de limpieza y optimización del sistema
# Requiere: Ejecutar como Administrador
# Uso: powershell -ExecutionPolicy Bypass -File limpieza_completa.ps1
# Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
# ═══════════════════════════════════════════════════════════════════════════

# Configuración de colores y formato
$Host.UI.RawUI.WindowTitle = "Limpieza Completa del Sistema - CEDIS 427"

function Write-Banner {
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "              SCRIPT MAESTRO DE LIMPIEZA COMPLETA" -ForegroundColor Cyan
    Write-Host "                     CEDIS Chedraui Cancún 427" -ForegroundColor Cyan
    Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)" -ForegroundColor DarkGray
    Write-Host "  Jefe de Sistemas - CEDIS Chedraui Logística Cancún" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
}

function Write-Section {
    param([string]$Title)
    Write-Host ""
    Write-Host "───────────────────────────────────────────────────────────────────────────" -ForegroundColor Yellow
    Write-Host " $Title" -ForegroundColor Yellow
    Write-Host "───────────────────────────────────────────────────────────────────────────" -ForegroundColor Yellow
}

function Write-Status {
    param(
        [string]$Message,
        [string]$Type = "INFO"
    )

    switch ($Type) {
        "OK"      { Write-Host "[OK] $Message" -ForegroundColor Green }
        "ERROR"   { Write-Host "[ERROR] $Message" -ForegroundColor Red }
        "WARNING" { Write-Host "[ADVERTENCIA] $Message" -ForegroundColor Yellow }
        "PROCESS" { Write-Host "[PROCESO] $Message" -ForegroundColor Cyan }
        default   { Write-Host "[INFO] $Message" -ForegroundColor White }
    }
}

# ═══════════════════════════════════════════════════════════════════════════
# INICIO DEL SCRIPT
# ═══════════════════════════════════════════════════════════════════════════

Clear-Host
Write-Banner

Write-Host "[INFO] Fecha/Hora de inicio: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor White
Write-Host ""

# Verificar privilegios de administrador
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Status "Este script requiere privilegios de administrador." "ERROR"
    Write-Status "Por favor, ejecute PowerShell como Administrador." "INFO"
    Write-Host ""
    Read-Host "Presione Enter para salir..."
    exit 1
}

Write-Status "Privilegios de administrador verificados." "OK"
Write-Host ""

# Confirmar ejecución
Write-Host "[PREGUNTA] Este script realizará las siguientes operaciones:" -ForegroundColor Magenta
Write-Host "  1. Limpiar archivos temporales del usuario" -ForegroundColor White
Write-Host "  2. Limpiar archivos temporales del sistema" -ForegroundColor White
Write-Host "  3. Vaciar papelera de reciclaje" -ForegroundColor White
Write-Host "  4. Limpiar caché DNS" -ForegroundColor White
Write-Host "  5. Verificar integridad del sistema (SFC)" -ForegroundColor White
Write-Host ""

$confirmar = Read-Host "¿Desea continuar? (S/N)"

if ($confirmar -ne "S" -and $confirmar -ne "s") {
    Write-Host ""
    Write-Status "Operación cancelada por el usuario." "INFO"
    Read-Host "Presione Enter para salir..."
    exit 0
}

# ═══════════════════════════════════════════════════════════════════════════
# PASO 1: Limpiar archivos temporales del usuario
# ═══════════════════════════════════════════════════════════════════════════

Write-Section "PASO 1/5: Limpiando archivos temporales del usuario"

$tempPath = $env:TEMP
$itemsDeleted = 0
$spaceSaved = 0

try {
    $tempItems = Get-ChildItem -Path $tempPath -Recurse -ErrorAction SilentlyContinue
    $spaceSaved += ($tempItems | Measure-Object -Property Length -Sum).Sum

    Remove-Item -Path "$tempPath\*" -Recurse -Force -ErrorAction SilentlyContinue
    $itemsDeleted = $tempItems.Count

    Write-Status "Archivos temporales del usuario limpiados." "OK"
    Write-Status "Elementos eliminados: $itemsDeleted" "INFO"
    Write-Status "Espacio liberado aproximado: $([math]::Round($spaceSaved / 1MB, 2)) MB" "INFO"
}
catch {
    Write-Status "Error parcial al limpiar temporales del usuario: $_" "WARNING"
}

# ═══════════════════════════════════════════════════════════════════════════
# PASO 2: Limpiar archivos temporales del sistema
# ═══════════════════════════════════════════════════════════════════════════

Write-Section "PASO 2/5: Limpiando archivos temporales del sistema"

$windowsTemp = "C:\Windows\Temp"
$systemItemsDeleted = 0
$systemSpaceSaved = 0

try {
    $systemTempItems = Get-ChildItem -Path $windowsTemp -Recurse -ErrorAction SilentlyContinue
    $systemSpaceSaved = ($systemTempItems | Measure-Object -Property Length -Sum).Sum

    Remove-Item -Path "$windowsTemp\*" -Recurse -Force -ErrorAction SilentlyContinue
    $systemItemsDeleted = $systemTempItems.Count

    Write-Status "Archivos temporales del sistema limpiados." "OK"
    Write-Status "Elementos eliminados: $systemItemsDeleted" "INFO"
    Write-Status "Espacio liberado aproximado: $([math]::Round($systemSpaceSaved / 1MB, 2)) MB" "INFO"
}
catch {
    Write-Status "Error parcial al limpiar temporales del sistema: $_" "WARNING"
}

# ═══════════════════════════════════════════════════════════════════════════
# PASO 3: Vaciar papelera de reciclaje
# ═══════════════════════════════════════════════════════════════════════════

Write-Section "PASO 3/5: Vaciando papelera de reciclaje"

try {
    Clear-RecycleBin -Force -ErrorAction SilentlyContinue
    Write-Status "Papelera de reciclaje vaciada." "OK"
}
catch {
    Write-Status "La papelera ya estaba vacía o error al vaciar: $_" "WARNING"
}

# ═══════════════════════════════════════════════════════════════════════════
# PASO 4: Limpiar caché DNS
# ═══════════════════════════════════════════════════════════════════════════

Write-Section "PASO 4/5: Limpiando caché DNS"

try {
    $result = ipconfig /flushdns
    Write-Status "Caché DNS limpiado correctamente." "OK"
}
catch {
    Write-Status "Error al limpiar caché DNS: $_" "WARNING"
}

# ═══════════════════════════════════════════════════════════════════════════
# PASO 5: Verificar integridad del sistema
# ═══════════════════════════════════════════════════════════════════════════

Write-Section "PASO 5/5: Verificando integridad del sistema"

Write-Status "Ejecutando System File Checker (SFC)..." "PROCESS"
Write-Status "Este proceso puede tomar varios minutos..." "INFO"
Write-Host ""

try {
    sfc /scannow
    Write-Host ""
    Write-Status "Verificación de integridad completada." "OK"
}
catch {
    Write-Status "Error durante la verificación: $_" "WARNING"
}

# ═══════════════════════════════════════════════════════════════════════════
# RESUMEN FINAL
# ═══════════════════════════════════════════════════════════════════════════

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "                    LIMPIEZA COMPLETADA CON ÉXITO" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Host "  Resumen de operaciones:" -ForegroundColor White
Write-Host "  ─────────────────────────────────────────────────────────────────────────" -ForegroundColor DarkGray
Write-Host "  [OK] Archivos temporales del usuario eliminados" -ForegroundColor Green
Write-Host "  [OK] Archivos temporales del sistema eliminados" -ForegroundColor Green
Write-Host "  [OK] Papelera de reciclaje vaciada" -ForegroundColor Green
Write-Host "  [OK] Caché DNS limpiado" -ForegroundColor Green
Write-Host "  [OK] Integridad del sistema verificada" -ForegroundColor Green
Write-Host ""
Write-Host "  Espacio total liberado: $([math]::Round(($spaceSaved + $systemSpaceSaved) / 1MB, 2)) MB" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Fecha/Hora de fin: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor White
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Host "[RECOMENDACIÓN] Se recomienda reiniciar el equipo para aplicar todos los cambios." -ForegroundColor Yellow
Write-Host ""

Read-Host "Presione Enter para salir..."
