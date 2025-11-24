# ═══════════════════════════════════════════════════════════════════════════
# VISOR DE PROCESOS POR CONSUMO DE CPU
# Sistema de Mantenimiento Windows - CEDIS Chedraui Cancún 427
# ═══════════════════════════════════════════════════════════════════════════
# Descripción: Muestra los 10 procesos que más CPU consumen
# Requiere: Ejecutar como Administrador
# Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
# ═══════════════════════════════════════════════════════════════════════════

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "                  VISOR DE PROCESOS (CONSUMO CPU)" -ForegroundColor Cyan
Write-Host "                        CEDIS Cancún 427" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "[INFO] Fecha/Hora: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Yellow
Write-Host ""

# Top 10 procesos por CPU
Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor Red
Write-Host "[INFO] TOP 10 PROCESOS POR CONSUMO DE CPU:" -ForegroundColor Red
Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor Red
Write-Host ""

Get-Process | Sort-Object CPU -Descending | Select-Object -First 10 | Format-Table -Property ProcessName, Id, @{Name='CPU(s)';Expression={[math]::Round($_.CPU,2)}}, @{Name='Memoria(MB)';Expression={[math]::Round($_.WS/1MB,2)}} -AutoSize

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "[COMPLETADO] Análisis de consumo de CPU finalizado." -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

Read-Host "Presione Enter para continuar..."
