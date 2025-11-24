# ═══════════════════════════════════════════════════════════════════════════
# VISOR DE SERVICIOS EN EJECUCIÓN
# Sistema de Mantenimiento Windows - CEDIS Chedraui Cancún 427
# ═══════════════════════════════════════════════════════════════════════════
# Descripción: Muestra servicios en ejecución ordenados por nombre
# Requiere: Ejecutar como Administrador
# Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
# ═══════════════════════════════════════════════════════════════════════════

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "                    VISOR DE SERVICIOS EN EJECUCIÓN" -ForegroundColor Cyan
Write-Host "                        CEDIS Cancún 427" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "[INFO] Fecha/Hora: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Yellow
Write-Host ""

# Mostrar servicios en ejecución
Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "[INFO] SERVICIOS EN EJECUCIÓN:" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""

Get-Service | Where-Object {$_.Status -eq "Running"} | Sort-Object -Property DisplayName | Format-Table -Property DisplayName, Name, Status -AutoSize

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "[INFO] TOTAL DE SERVICIOS EN EJECUCIÓN: $((Get-Service | Where-Object {$_.Status -eq 'Running'}).Count)" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""

Read-Host "Presione Enter para continuar..."
