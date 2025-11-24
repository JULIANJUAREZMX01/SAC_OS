# ═══════════════════════════════════════════════════════════════════════════
# VACIADOR DE PAPELERA DE RECICLAJE
# Sistema de Mantenimiento Windows - CEDIS Chedraui Cancún 427
# ═══════════════════════════════════════════════════════════════════════════
# Descripción: Vacía la papelera de reciclaje de forma segura
# Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
# ═══════════════════════════════════════════════════════════════════════════

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "                 VACIADOR DE PAPELERA DE RECICLAJE" -ForegroundColor Cyan
Write-Host "                        CEDIS Cancún 427" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "[INFO] Fecha/Hora: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Yellow
Write-Host ""

# Confirmar operación
$confirmar = Read-Host "¿Desea vaciar la papelera de reciclaje? (S/N)"

if ($confirmar -eq "S" -or $confirmar -eq "s") {
    Write-Host ""
    Write-Host "[PROCESO] Vaciando papelera de reciclaje..." -ForegroundColor Yellow

    try {
        Clear-RecycleBin -Force -ErrorAction Stop
        Write-Host "[OK] Papelera de reciclaje vaciada correctamente." -ForegroundColor Green
    }
    catch {
        Write-Host "[INFO] La papelera ya estaba vacía o no hay elementos que eliminar." -ForegroundColor Yellow
    }
} else {
    Write-Host ""
    Write-Host "[INFO] Operación cancelada por el usuario." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "[COMPLETADO] Proceso finalizado." -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

Read-Host "Presione Enter para continuar..."
