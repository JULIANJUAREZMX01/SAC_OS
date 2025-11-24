# ═══════════════════════════════════════════════════════════════════════════
# VISOR DE PROCESOS POR CONSUMO DE MEMORIA
# Sistema de Mantenimiento Windows - CEDIS Chedraui Cancún 427
# ═══════════════════════════════════════════════════════════════════════════
# Descripción: Muestra los 10 procesos que más memoria consumen
# Requiere: Ejecutar como Administrador
# Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
# ═══════════════════════════════════════════════════════════════════════════

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "                 VISOR DE PROCESOS (CONSUMO MEMORIA)" -ForegroundColor Cyan
Write-Host "                        CEDIS Cancún 427" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "[INFO] Fecha/Hora: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Yellow
Write-Host ""

# Información de memoria del sistema
$totalMemory = (Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB
$freeMemory = (Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1MB
$usedMemory = $totalMemory - ($freeMemory / 1024)

Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor Yellow
Write-Host "[INFO] MEMORIA DEL SISTEMA:" -ForegroundColor Yellow
Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor Yellow
Write-Host "  Memoria Total: $([math]::Round($totalMemory, 2)) GB" -ForegroundColor White
Write-Host "  Memoria en Uso: $([math]::Round($usedMemory, 2)) GB" -ForegroundColor White
Write-Host "  Memoria Libre: $([math]::Round($freeMemory / 1024, 2)) GB" -ForegroundColor White
Write-Host ""

# Top 10 procesos por memoria
Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor Magenta
Write-Host "[INFO] TOP 10 PROCESOS POR CONSUMO DE MEMORIA:" -ForegroundColor Magenta
Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor Magenta
Write-Host ""

Get-Process | Sort-Object WS -Descending | Select-Object -First 10 | Format-Table -Property ProcessName, Id, @{Name='Memoria(MB)';Expression={[math]::Round($_.WS/1MB,2)}}, @{Name='CPU(s)';Expression={[math]::Round($_.CPU,2)}} -AutoSize

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "[COMPLETADO] Análisis de consumo de memoria finalizado." -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

Read-Host "Presione Enter para continuar..."
