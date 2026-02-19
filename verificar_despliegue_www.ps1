# Script para verificar que el despliegue se completó en producción

Write-Host ""
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host "  VERIFICACION POST-DESPLIEGUE" -ForegroundColor Cyan
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host ""

$API_BASE = "https://api.masasestacion.cl"

Write-Host "Esperando 90 segundos para que complete el despliegue..." -ForegroundColor Yellow
Start-Sleep -Seconds 90

Write-Host ""
Write-Host "Probando deteccion en produccion..." -ForegroundColor Yellow
Write-Host ""

$testCases = @(
    @{hostname="masasestacion.cl"; descripcion="Sin www"},
    @{hostname="www.masasestacion.cl"; descripcion="Con www (FIX)"},
    @{hostname="admin.masasestacion.cl"; descripcion="Backoffice"}
)

foreach ($test in $testCases) {
    Write-Host "Probando: $($test.hostname)" -ForegroundColor Cyan
    Write-Host "  $($test.descripcion)" -ForegroundColor Gray
    
    try {
        $response = Invoke-RestMethod `
            -Uri "$API_BASE/api/config/landing" `
            -Headers @{
                "X-Forwarded-Host" = $test.hostname
            } `
            -TimeoutSec 10
        
        Write-Host "  EXITO: Tenant $($response.tenant.nombre) detectado" -ForegroundColor Green
    } catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        Write-Host "  ERROR: Status $statusCode" -ForegroundColor Red
    }
    Write-Host ""
}

Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host "  Ahora prueba en tu navegador: www.masasestacion.cl" -ForegroundColor Cyan
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host ""
