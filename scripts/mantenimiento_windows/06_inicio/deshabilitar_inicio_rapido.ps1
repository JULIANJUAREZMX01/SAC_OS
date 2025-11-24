# ═══════════════════════════════════════════════════════════════════════════
# DESHABILITADOR DE INICIO RÁPIDO (FAST STARTUP)
# Sistema de Mantenimiento Windows - CEDIS Chedraui Cancún 427
# ═══════════════════════════════════════════════════════════════════════════
# Descripción: Deshabilita el inicio rápido si causa problemas
# Requiere: Ejecutar como Administrador
# Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
# ═══════════════════════════════════════════════════════════════════════════

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "            DESHABILITADOR DE INICIO RÁPIDO (FAST STARTUP)" -ForegroundColor Cyan
Write-Host "                        CEDIS Cancún 427" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "[INFO] El Inicio Rápido puede causar problemas en algunos sistemas." -ForegroundColor Yellow
Write-Host "[INFO] Deshabilitarlo puede resolver problemas de arranque/apagado." -ForegroundColor Yellow
Write-Host ""
Write-Host "[INFO] Fecha/Hora: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Yellow
Write-Host ""

# Verificar privilegios de administrador
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "[ERROR] Este script requiere privilegios de administrador." -ForegroundColor Red
    Write-Host "[INFO] Por favor, ejecute PowerShell como Administrador." -ForegroundColor Red
    Read-Host "Presione Enter para salir..."
    exit 1
}

Write-Host "[OK] Privilegios de administrador verificados." -ForegroundColor Green
Write-Host ""

# Confirmar operación
$confirmar = Read-Host "¿Desea deshabilitar el Inicio Rápido? (S/N)"

if ($confirmar -eq "S" -or $confirmar -eq "s") {
    Write-Host ""
    Write-Host "[PROCESO] Deshabilitando Inicio Rápido (Hibernación)..." -ForegroundColor Yellow

    # Deshabilitar hibernación (que también deshabilita Fast Startup)
    powercfg -h off

    Write-Host "[OK] Inicio Rápido deshabilitado." -ForegroundColor Green
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor Green
    Write-Host "[COMPLETADO] El Inicio Rápido ha sido deshabilitado." -ForegroundColor Green
    Write-Host "[INFO] Esto también deshabilita la hibernación." -ForegroundColor Green
    Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "[INFO] Operación cancelada por el usuario." -ForegroundColor Yellow
}

Write-Host ""
Read-Host "Presione Enter para continuar..."
